"""
Tests de la méthode d'évaluation (kind = "method").

Chaque test part d'un PRÉRÉGLAGE réel du dépôt, lu en dictionnaire, et y casse une seule chose :
on vérifie ainsi que la règle visée, et elle seule, est signalée.
"""

import copy
import tomllib
from pathlib import Path

import pytest

from risk_matrix.method import parse_method

METHODS = Path(__file__).parents[1] / "methods"


def preset(name: str = "iso27005-5x5") -> dict:
    with (METHODS / f"{name}.toml").open("rb") as f:
        return tomllib.load(f)


def errors(data: dict) -> list[str]:
    method, found = parse_method(data)
    assert (method is None) == bool(found)  # une méthode n'est rendue que si elle est valide
    return found


# ── Préréglages ─────────────────────────────────────────────
@pytest.mark.parametrize("name", ["iso27005-5x5", "ebios-rm-4x4"])
def test_preréglages_valides(name):
    method, found = parse_method(preset(name))
    assert found == []
    assert method is not None
    assert method.id == name


def test_grille_5x5_conforme_a_la_regle_du_produit():
    method, _ = parse_method(preset())
    seuils = {"low": range(1, 5), "moderate": range(5, 10), "high": range(10, 17), "critical": range(17, 26)}
    for vraisemblance in range(1, 6):
        for impact in range(1, 6):
            niveau = method.level_of(vraisemblance, impact).id
            assert vraisemblance * impact in seuils[niveau], (vraisemblance, impact, niveau)


def test_ebios_libelles_et_acceptation():
    method, _ = parse_method(preset("ebios-rm-4x4"))
    assert [lvl.label.fr.split(" — ")[0] for lvl in method.impact.levels] == ["G1", "G2", "G3", "G4"]
    assert method.impact.levels[3].label.fr == "G4 — Critique"
    assert method.level_of(4, 4).id == "unacceptable"
    assert method.level_of(1, 1).id == "acceptable"
    assert not method.needs_acceptance("acceptable")
    assert method.needs_acceptance("tolerable")
    assert method.authority("unacceptable").max_months == 6


def test_aides_du_modele():
    method, _ = parse_method(preset())
    assert method.rank("low") == 0
    assert method.rank("critical") == 3
    assert method.level("high").label.en == "High"
    assert method.authority("low") is None  # sous l'appétence : pas d'acceptation formelle


# ── Structure générale ──────────────────────────────────────
def test_cle_inconnue_signalee():
    data = preset()
    data["appetit"] = "low"
    assert errors(data) == ["appetit : clé inconnue"]


def test_version_du_format():
    data = preset()
    data["format"] = 2
    assert errors(data) == ["format : 1 attendu (version du format de fichier)"]


def test_identifiant_invalide():
    data = preset()
    data["id"] = "Méthode 5x5"
    assert errors(data) == ["id : identifiant invalide « Méthode 5x5 » (minuscules, chiffres et tirets)"]


@pytest.mark.parametrize(
    ("valeur", "attendu"),
    [
        ({"fr": "Nom"}, ["name.en : texte non vide attendu"]),
        ({"fr": "Nom", "en": "  "}, ["name.en : texte non vide attendu"]),
        ({"fr": "Nom", "en": "Name", "de": "Name"}, ["name.de : langue inconnue (fr et en seulement)"]),
        ("Nom", ["name : table attendue", "name.fr : texte non vide attendu", "name.en : texte non vide attendu"]),
    ],
)
def test_textes_bilingues(valeur, attendu):
    data = preset()
    data["name"] = valeur
    assert errors(data) == attendu


# ── Axes ────────────────────────────────────────────────────
def test_niveaux_d_axe_numerotes_dans_l_ordre():
    data = preset()
    data["likelihood"]["levels"][1]["value"] = 3
    assert errors(data) == ["likelihood.levels[1].value : 2 attendu (niveaux numérotés 1, 2, 3… dans l'ordre)"]


def test_taille_d_axe_bornee():
    data = preset()
    data["impact"]["levels"] = data["impact"]["levels"][:2]
    found = errors(data)
    assert "impact.levels : de 3 à 7 niveaux attendus (2)" in found


def test_un_booleen_n_est_pas_un_entier():
    data = preset()
    data["likelihood"]["levels"][0]["value"] = True
    assert "likelihood.levels[0].value : entier supérieur ou égal à 1 attendu" in errors(data)


# ── Niveaux de risque ───────────────────────────────────────
def test_couleur_invalide():
    data = preset()
    data["levels"][0]["color"] = "vert"
    assert errors(data) == ["levels[0].color : couleur « vert » invalide (format #RRVVBB)"]


def test_identifiant_de_niveau_en_double():
    data = preset()
    data["levels"][1]["id"] = "low"
    assert "levels : identifiant « low » en double" in errors(data)


def test_risque_plus_grave_revu_moins_souvent():
    data = preset()
    data["levels"][2]["review_months"] = 12  # « high » revu tous les 12 mois, « moderate » tous les 6
    assert errors(data) == ["levels : « high » revu moins souvent (12 mois) que « moderate »"]


# ── Grille ──────────────────────────────────────────────────
def test_grille_mal_dimensionnee():
    data = preset()
    data["grid"]["rows"] = data["grid"]["rows"][:4]
    assert errors(data) == ["grid.rows : 5 lignes attendues, une par niveau de vraisemblance (4)"]


def test_case_manquante():
    data = preset()
    data["grid"]["rows"][2] = data["grid"]["rows"][2][:4]
    assert errors(data) == ["grid.rows[2] : 5 cases attendues, une par niveau d'impact (4)"]


def test_niveau_inconnu_dans_la_grille():
    data = preset()
    data["grid"]["rows"][0][0] = "faible"
    assert errors(data) == ["grid.rows[0][0] : niveau inconnu « faible »"]


def test_grille_non_monotone_en_impact():
    data = preset()
    # Ligne 5 : « moderate, critical, high… » — « high » est moins grave que la case à sa gauche,
    # mais pas que celle du dessus (« high ») : une seule erreur attendue
    data["grid"]["rows"][4][1] = "critical"
    assert errors(data) == ["grid.rows[4][2] : « high » moins grave que la case à sa gauche (« critical »)"]


def test_deux_voisins_plus_graves_deux_erreurs():
    data = preset()
    data["grid"]["rows"][4][4] = "high"  # moins grave que la case de gauche ET que celle du dessus
    assert len(errors(data)) == 2


def test_grille_non_monotone_en_vraisemblance():
    data = preset()
    data["grid"]["rows"][3][0] = "moderate"  # puis la ligne suivante a « moderate » : OK ; on casse la ligne 4
    data["grid"]["rows"][4][0] = "low"
    assert errors(data) == ["grid.rows[4][0] : « low » moins grave que la case de la ligne précédente (« moderate »)"]


def test_niveau_jamais_utilise():
    data = preset("ebios-rm-4x4")
    grille = data["grid"]["rows"]
    data["grid"]["rows"] = [[("tolerable" if c == "unacceptable" else c) for c in row] for row in grille]
    found = errors(data)
    assert "grid.rows : niveau « unacceptable » jamais utilisé dans la grille" in found


def test_grille_ecrite_au_mauvais_endroit():
    """Le piège TOML : une clé écrite après [[levels]] appartient au dernier niveau."""
    data = preset()
    rows = data.pop("grid")["rows"]
    data["levels"][-1]["grid"] = rows
    found = errors(data)
    assert found[0] == "levels[3].grid : clé inconnue"
    assert "grid : table attendue" in found


# ── Appétence et acceptation ────────────────────────────────
def test_autorite_manquante_au_dessus_de_l_appetence():
    data = preset()
    data["acceptance"]["authorities"].pop()  # plus d'autorité pour « critical »
    assert errors(data) == [
        "acceptance.authorities : une autorité attendue pour le niveau « critical » (au-dessus de l'appétence)"
    ]


def test_autorite_inutile_sous_l_appetence():
    data = preset()
    data["acceptance"]["appetite"] = "moderate"
    assert errors(data) == [
        "acceptance.authorities : « moderate » n'est pas au-dessus de l'appétence : aucune autorité à déclarer"
    ]


def test_acceptation_plus_longue_pour_un_risque_plus_grave():
    data = preset()
    data["acceptance"]["authorities"][2]["max_months"] = 12  # critique accepté 12 mois, élevé 6
    assert errors(data) == ["acceptance.authorities : acceptation de « critical » plus longue que celle de « high »"]


def test_toutes_les_erreurs_sont_collectees():
    data = copy.deepcopy(preset())
    data["format"] = 0
    data["levels"][0]["color"] = "rouge"
    data["acceptance"]["appetite"] = "inconnu"
    assert len(errors(data)) == 3
