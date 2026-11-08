"""
Tests du registre de risques (kind = "register").

Chaque test part du registre de référence « data/registre-valide.toml » (valide et sans
avertissement au 2026-11-08), y casse une seule chose, et vérifie le message obtenu.
"""

import tomllib
from datetime import date
from pathlib import Path

import pytest

from risk_matrix.method import parse_method
from risk_matrix.register import add_months, parse_register

ROOT = Path(__file__).parents[1]
TODAY = date(2026, 11, 8)


def load(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


# Méthodes disponibles : les deux préréglages du dépôt
METHODS = {m.id: m for m in (parse_method(load(p))[0] for p in sorted((ROOT / "methods").glob("*.toml")))}


@pytest.fixture
def data() -> dict:
    """Copie neuve du registre de référence (chaque test peut la modifier)."""
    return load(ROOT / "tests" / "data" / "registre-valide.toml")


def risk(data: dict, risk_id: str) -> dict:
    return next(r for r in data["risks"] if r["id"] == risk_id)


def check(data: dict, today: date = TODAY):
    register, findings = parse_register(data, METHODS, today)
    assert (register is None) == bool(findings.errors)  # un registre n'est rendu que s'il est valide
    return findings


def errors(data: dict, today: date = TODAY) -> list[str]:
    return check(data, today).errors


# ── Registre de référence ───────────────────────────────────
def test_registre_de_reference_valide(data):
    register, findings = parse_register(data, METHODS, TODAY)
    assert findings.errors == []
    assert findings.warnings == []
    assert [r.id for r in register.risks] == ["R01", "R02", "R03"]
    r01, r02, r03 = register.risks
    assert (register.inherent_level(r01), register.residual_level(r01)) == ("critical", "high")
    assert (register.inherent_level(r02), register.residual_level(r02)) == ("high", "moderate")
    assert register.residual_level(r03) == "low"
    assert r01.gdpr and not r03.gdpr  # absent : false par défaut
    assert r03.transfer_to == "Assureur (contrat multirisque)"
    assert r02.acceptance.until == date(2027, 9, 15)


@pytest.mark.parametrize(
    ("start", "months", "expected"),
    [
        (date(2026, 9, 15), 12, date(2027, 9, 15)),
        (date(2027, 1, 31), 1, date(2027, 2, 28)),  # pas de 31 février : dernier jour du mois
        (date(2027, 8, 31), 6, date(2028, 2, 29)),  # année bissextile
        (date(2026, 11, 30), 3, date(2027, 2, 28)),
    ],
)
def test_ajout_de_mois(start, months, expected):
    assert add_months(start, months) == expected


# ── En-tête du registre ─────────────────────────────────────
def test_methode_introuvable(data):
    data["method"] = "maison-3x3"
    assert errors(data) == ["method : méthode « maison-3x3 » introuvable (disponibles : ebios-rm-4x4, iso27005-5x5)"]


def test_version_et_langue(data):
    data["format"] = 2
    data["lang"] = "de"
    assert errors(data) == ["format : 1 attendu (version du format de fichier)", "lang : « fr », « en » attendu"]


def test_evaluation_datee_dans_le_futur(data):
    data["assessed_on"] = date(2026, 12, 1)
    assert errors(data) == ["assessed_on : date future (2026-12-01)"]


def test_date_entre_guillemets_refusee(data):
    data["assessed_on"] = "2026-09-01"  # chaîne, pas une date TOML
    assert errors(data) == ["assessed_on : date attendue au format AAAA-MM-JJ, sans guillemets"]


def test_cle_inconnue_dans_un_risque(data):
    risk(data, "R01")["owners"] = "faute de frappe"
    assert errors(data) == ["R01.owners : clé inconnue"]


def test_identifiant_en_double(data):
    risk(data, "R03")["id"] = "R01"
    assert "risks : identifiant « R01 » en double" in errors(data)


def test_identifiant_de_risque_invalide(data):
    risk(data, "R03")["id"] = "r 3"
    assert errors(data)[0] == "risks[2].id : identifiant « r 3 » invalide (majuscules, chiffres et tirets, ex. R01)"


def test_registre_sans_risque(data):
    data["risks"] = []
    assert errors(data) == ["risks : au moins un risque attendu"]


# ── Notes de risque ─────────────────────────────────────────
def test_note_hors_echelle(data):
    risk(data, "R01")["inherent"]["impact"] = 6
    assert errors(data) == ["R01.inherent.impact : 6 hors échelle (1 à 5 dans la méthode « iso27005-5x5 »)"]


def test_echelle_de_la_methode_choisie(data):
    data["method"] = "ebios-rm-4x4"  # 4×4 : l'impact 5 de R01 n'existe plus
    assert "R01.inherent.impact : 5 hors échelle (1 à 4 dans la méthode « ebios-rm-4x4 »)" in errors(data)


def test_residuel_superieur_a_l_inherent(data):
    risk(data, "R03")["residual"] = {"likelihood": 1, "impact": 3}  # impact 3 > impact inhérent 2
    assert errors(data) == ["R03.residual : supérieur au risque inhérent sur un axe : ajouter « justification »"]


def test_residuel_superieur_justifie(data):
    r03 = risk(data, "R03")
    r03["residual"] = {"likelihood": 4, "impact": 1, "justification": "Usage nomade en forte hausse."}
    assert errors(data) == []


def test_justification_reservee_au_residuel(data):
    risk(data, "R01")["inherent"]["justification"] = "sans objet"
    assert errors(data) == ["R01.inherent.justification : clé inconnue"]


# ── Traitement ──────────────────────────────────────────────
def test_reduction_sans_mesure(data):
    del risk(data, "R01")["measures"]
    found = errors(data)
    assert found[0] == "R01.measures : traitement « reduce » sans aucune mesure de réduction"


def test_transfert_sans_destinataire(data):
    del risk(data, "R03")["transfer"]
    assert errors(data) == [
        "R03.transfer.to : traitement « transfer » : préciser à qui le risque est transféré (assureur, prestataire…)"
    ]


def test_transfert_renseigne_pour_un_autre_traitement(data):
    risk(data, "R03")["treatment"] = "accept"
    assert errors(data) == ["R03.transfer : renseigné alors que le traitement n'est pas « transfer »"]


def test_traitement_inconnu(data):
    risk(data, "R01")["treatment"] = "ignore"
    assert errors(data) == ["R01.treatment : « reduce », « accept », « transfer », « avoid » attendu"]


# ── Acceptation formelle ────────────────────────────────────
def test_acceptation_requise_apres_reduction_terminee(data):
    del risk(data, "R02")["acceptance"]
    assert errors(data) == [
        "R02.acceptance : risque résiduel « moderate » au-dessus de l'appétence : acceptation formelle requise"
    ]


def test_acceptation_requise_quand_le_traitement_est_d_accepter(data):
    risk(data, "R01")["treatment"] = "accept"  # mesures en cours, mais le choix est d'accepter
    assert errors(data) == [
        "R01.acceptance : risque résiduel « high » au-dessus de l'appétence : acceptation formelle requise"
    ]


def test_pas_d_acceptation_pour_un_risque_clos(data):
    r02 = risk(data, "R02")
    r02["status"] = "closed"
    del r02["acceptance"]
    assert errors(data) == []


def test_mauvaise_autorite(data):
    risk(data, "R02")["acceptance"]["role"] = "Stagiaire"
    assert errors(data) == [
        "R02.acceptance.role : « Responsable du risque » attendu pour un risque « moderate » (méthode « iso27005-5x5 »)"
    ]


def test_autorite_dans_la_langue_du_registre(data):
    data["lang"] = "en"  # le rôle doit alors être écrit en anglais
    assert errors(data) == [
        "R02.acceptance.role : « Risk owner » attendu pour un risque « moderate » (méthode « iso27005-5x5 »)"
    ]


def test_acceptation_trop_longue(data):
    risk(data, "R02")["acceptance"]["until"] = date(2027, 9, 16)
    assert errors(data) == [
        "R02.acceptance.until : au-delà de 12 mois pour un risque « moderate » (au plus tard 2027-09-15)"
    ]


def test_fin_d_acceptation_avant_son_debut(data):
    risk(data, "R02")["acceptance"]["until"] = date(2026, 9, 1)
    assert errors(data) == ["R02.acceptance.until : doit être postérieure à la date d'acceptation (« on »)"]


def test_acceptation_incomplete(data):
    del risk(data, "R02")["acceptance"]["rationale"]
    assert errors(data) == ["R02.acceptance.rationale : texte non vide attendu"]


# ── Revue ───────────────────────────────────────────────────
def test_revue_trop_eloignee(data):
    risk(data, "R01")["review"]["next"] = date(2027, 1, 2)  # « high » : 3 mois au plus
    assert errors(data) == ["R01.review.next : trop éloignée : un risque « high » se revoit tous les 3 mois au plus"]


def test_revue_suivante_avant_la_derniere(data):
    risk(data, "R03")["review"]["next"] = date(2026, 5, 1)
    assert "R03.review.next : doit être postérieure à la dernière revue (« last »)" in errors(data)


def test_revue_obligatoire(data):
    del risk(data, "R03")["review"]
    assert errors(data)[0] == "R03.review : table attendue"


# ── Historique ──────────────────────────────────────────────
def test_historique_chronologique(data):
    risk(data, "R01")["history"].reverse()
    assert errors(data) == ["R01.history[1].on : historique à tenir dans l'ordre chronologique"]


def test_historique_sans_date_future(data):
    risk(data, "R01")["history"][1]["on"] = date(2026, 12, 25)
    assert errors(data) == ["R01.history[1].on : date future (2026-12-25)"]


# ── Avertissements : ce qui est échu à la date du jour ──────
def test_avertissements_a_une_date_ulterieure(data):
    findings = check(data, today=date(2027, 10, 1))
    assert findings.errors == []  # le fichier reste valide
    assert findings.warnings == [
        "R01.measures[1] : mesure en retard (échéance 2027-01-31) — « EDR sur tous les postes »",
        "R01.review : revue en retard (prévue le 2027-01-01)",
        "R02.acceptance : acceptation expirée le 2027-09-15 — à renouveler ou à traiter",
        "R02.review : revue en retard (prévue le 2027-03-15)",
        "R03.review : revue en retard (prévue le 2027-06-01)",
    ]


def test_echeance_du_jour_pas_encore_en_retard(data):
    assert check(data, today=date(2027, 1, 1)).warnings == []  # revue de R01 prévue ce jour-là


def test_mesure_terminee_jamais_en_retard(data):
    risk(data, "R01")["measures"][1]["status"] = "done"
    risk(data, "R01")["acceptance"] = {
        "by": "Paul Durand",
        "role": "Direction",
        "on": date(2026, 11, 1),
        "until": date(2027, 5, 1),
        "rationale": "EDR déployé ; risque résiduel élevé accepté le temps de la segmentation réseau.",
    }
    findings = check(data, today=date(2027, 2, 1))
    assert findings.errors == []
    assert [w for w in findings.warnings if "measures" in w] == []


def test_risque_clos_sans_avertissement(data):
    for r in data["risks"]:
        r["status"] = "closed"
    assert check(data, today=date(2030, 1, 1)).warnings == []


# ── Toutes les erreurs sont collectées ──────────────────────
def test_toutes_les_erreurs_sont_collectees(data):
    data["lang"] = "es"
    risk(data, "R01")["owner"] = ""
    risk(data, "R03")["gdpr"] = "oui"
    assert len(errors(data)) == 3
