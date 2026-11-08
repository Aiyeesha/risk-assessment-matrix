"""
Tests de l'import et de l'export CSV : protection contre l'injection de formules, lecture sûre,
conversion des cellules, et commandes risk-export / risk-import (y compris l'aller-retour).
"""

import csv
import dataclasses
import io
import json
import tomllib
from datetime import date
from pathlib import Path

import pytest

from risk_matrix import export, importer
from risk_matrix.check import load_methods, load_register
from risk_matrix.tabular import (
    MAX_BYTES,
    MAX_ROWS,
    MEASURE_COLUMNS,
    RISK_COLUMNS,
    CsvError,
    neutralize,
    read_csv,
    restore,
    rows_to_register,
    write_csv,
)
from risk_matrix.toml_writer import dump_register, value

ROOT = Path(__file__).parents[1]
REGISTRE = ROOT / "tests" / "data" / "registre-valide.toml"
METHODS = ["--methods", str(ROOT / "methods")]
JOUR = ["--today", "2026-11-08"]
TODAY = date(2026, 11, 8)
HEADER = {"method": "iso27005-5x5", "lang": "fr", "organisation": "Test", "assessed_on": date(2026, 9, 1),
          "assessor": "Équipe sécurité"}  # fmt: skip
IMPORT = ["--method", "iso27005-5x5", "--organisation", "Organisation de test", "--assessed-on", "2026-09-01",
          "--assessor", "Équipe sécurité", *METHODS, *JOUR]  # fmt: skip


def write(path: Path, content: str | bytes) -> Path:
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


# ── 1. Injection de formules ────────────────────────────────
@pytest.mark.parametrize(
    "dangereux",
    ["=1+1", "+33 1 23", "-2+3", "@SUM(A1)", "\t=1", "\r=1", '=HYPERLINK("http://exemple.invalid","clic")'],
)
def test_cellule_dangereuse_neutralisee_puis_restauree(dangereux):
    assert neutralize(dangereux) == "'" + dangereux
    assert restore(neutralize(dangereux)) == dangereux


@pytest.mark.parametrize("anodin", ["R01", "Sauvegardes", "2026-09-01", "'apostrophe d'origine", "", "8.13"])
def test_cellule_anodine_inchangee(anodin):
    assert neutralize(anodin) == anodin
    assert restore(anodin) == anodin


def test_toutes_les_cellules_exportees_sont_protegees():
    rows = [{"id": "R01", "title": "=cmd|' /C calc'!A0", "owner": "@moi"}]
    text = write_csv(rows, ("id", "title", "owner"), ";")
    cells = list(csv.reader(io.StringIO(text), delimiter=";"))[1]
    assert cells == ["R01", "'=cmd|' /C calc'!A0", "'@moi"]
    assert not any(cell.startswith(("=", "+", "-", "@")) for cell in cells)


# ── 2. Lecture sûre d'un CSV ────────────────────────────────
def test_lecture_point_virgule_et_bom(tmp_path):
    path = write(tmp_path / "r.csv", '\ufeffid;title\r\nR01;"Titre ; avec point-virgule"\r\n'.encode())
    assert read_csv(path, RISK_COLUMNS) == [(2, {"id": "R01", "title": "Titre ; avec point-virgule"})]


def test_lecture_virgule_detectee(tmp_path):
    path = write(tmp_path / "r.csv", "id,title\nR01,Titre\n\n")
    assert read_csv(path, RISK_COLUMNS) == [(2, {"id": "R01", "title": "Titre"})]


@pytest.mark.parametrize(
    ("contenu", "message", "ligne"),
    [
        ("", "fichier vide : une ligne d'en-tête est attendue", 1),
        ("id;titre\n", "colonne(s) inconnue(s) : titre", 1),
        ("id;title;title\n", "colonne(s) en double : title", 1),
        ("title\nTitre\n", "colonne « id » obligatoire", 1),
        ("id;title\nR01\n", "1 cellules pour 2 colonnes", 2),
        ('id;title\nR01;"non fermé\n', "structure CSV invalide", 2),
    ],
)
def test_csv_inutilisable(tmp_path, contenu, message, ligne):
    with pytest.raises(CsvError) as err:
        read_csv(write(tmp_path / "r.csv", contenu), RISK_COLUMNS)
    assert err.value.message.startswith(message)
    assert err.value.line == ligne


def test_encodage_d_excel_refuse_avec_conseil(tmp_path):
    with pytest.raises(CsvError) as err:
        read_csv(write(tmp_path / "r.csv", "id;title\nR01;Sécurité\n".encode("cp1252")), RISK_COLUMNS)
    assert "enregistrer le fichier au format « CSV UTF-8 »" in err.value.message


def test_limites_de_taille(tmp_path):
    with pytest.raises(CsvError, match="trop volumineux"):
        read_csv(write(tmp_path / "gros.csv", b"id\n" + b"R" * MAX_BYTES), RISK_COLUMNS)
    lignes = "id\n" + "".join(f"R{i}\n" for i in range(MAX_ROWS + 1))
    with pytest.raises(CsvError, match=f"plus de {MAX_ROWS} lignes"):
        read_csv(write(tmp_path / "long.csv", lignes), RISK_COLUMNS)


# ── 3. Conversion des cellules ──────────────────────────────
def test_conversion_typee():
    row = {"id": "R01", "assets": "A | B |", "gdpr": "Oui", "nis2": "no", "inherent_likelihood": "3",
           "inherent_impact": "4", "review_last": "2026-10-01", "inherent_level": "ignoré",
           "transfer_to": ""}  # fmt: skip
    data, errors = rows_to_register(HEADER, [(2, row)])
    assert errors == []
    assert data["risks"] == [{
        "id": "R01", "assets": ["A", "B"], "gdpr": True, "nis2": False,
        "inherent": {"likelihood": 3, "impact": 4}, "review": {"last": date(2026, 10, 1)},
    }]  # fmt: skip


@pytest.mark.parametrize(
    ("colonne", "cellule", "message"),
    [
        ("inherent_impact", "4,5", "colonne « inherent_impact » : entier attendu (« 4,5 »)"),
        ("review_next", "01/03/2027", "colonne « review_next » : date AAAA-MM-JJ attendue (« 01/03/2027 »)"),
        ("review_next", "2027-02-30", "colonne « review_next » : date AAAA-MM-JJ attendue (« 2027-02-30 »)"),
        ("review_next", "20270301", "colonne « review_next » : date AAAA-MM-JJ attendue (« 20270301 »)"),
        ("gdpr", "peut-être", "colonne « gdpr » : oui ou non attendu (« peut-être »)"),
    ],
)
def test_cellule_mal_ecrite(colonne, cellule, message):
    _data, errors = rows_to_register(HEADER, [(5, {"id": "R01", colonne: cellule})])
    assert errors == [("risks", 5, message)]


def test_mesure_d_un_risque_absent():
    _data, errors = rows_to_register(HEADER, [(2, {"id": "R01"})], [(3, {"risk_id": "R09", "title": "x"})])
    assert errors == [("measures", 3, "risque « R09 » absent du fichier des risques")]


def test_identifiant_en_double_dans_le_csv():
    _data, errors = rows_to_register(HEADER, [(2, {"id": "R01"}), (3, {"id": "R01"})])
    assert errors == [("risks", 3, "identifiant « R01 » en double")]


# ── 4. Écriture TOML ────────────────────────────────────────
@pytest.mark.parametrize(
    "texte", ['guillemet " et barre \\', "ligne 1\nligne 2", "tab\tcontrôle\x01\x7f", "émoji 🛡️", "'''", '"""']
)
def test_chaines_toml_echappees(texte):
    assert tomllib.loads(f"x = {value(texte)}")["x"] == texte


def test_registre_reecrit_a_l_identique():
    """Lire le registre de référence, le réécrire, le relire : mêmes données (historique compris)."""
    with REGISTRE.open("rb") as f:
        data = tomllib.load(f)
    assert tomllib.loads(dump_register(data, "commentaire\nsur deux lignes")) == data


def test_type_non_pris_en_charge():
    with pytest.raises(TypeError):
        value(1.5)


# ── 5. risk-export ──────────────────────────────────────────
def test_export_json(capsys):
    assert export.main([str(REGISTRE), *METHODS, *JOUR]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["schema_version"] == 1
    assert data["as_of"] == "2026-11-08"
    assert data["method"]["id"] == "iso27005-5x5"
    assert len(data["method"]["grid"]) == 5
    r01 = data["risks"][0]
    assert r01["inherent"] == {"likelihood": 4, "impact": 5, "level": "critical"}
    assert r01["residual"]["level"] == "high"
    assert r01["iso27001"][1] == {"id": "8.13", "theme": "Mesures technologiques"}
    assert r01["attack"][0] == {"id": "T1486", "url": "https://attack.mitre.org/techniques/T1486/"}
    assert r01["playbooks"][0]["title"] == "Attaque par rançongiciel"
    assert data["risks"][1]["acceptance"]["until"] == "2027-09-15"
    assert data["warnings"] == []


def test_export_json_avec_avertissements(capsys):
    assert export.main([str(REGISTRE), *METHODS, "--today", "2027-01-15"]) == 0
    assert json.loads(capsys.readouterr().out)["warnings"] == ["R01.review : revue en retard (prévue le 2027-01-01)"]


def test_export_csv_pour_excel(tmp_path):
    risques, mesures = tmp_path / "risques.csv", tmp_path / "mesures.csv"
    assert export.main([str(REGISTRE), "--format", "csv", "-o", str(risques), "--measures", str(mesures),
                        *METHODS, *JOUR]) == 0  # fmt: skip
    raw = risques.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # BOM : Excel reconnaît l'UTF-8
    assert b"\r\n" in raw
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), delimiter=";"))
    assert [r["id"] for r in rows] == ["R01", "R02", "R03"]
    assert rows[0]["inherent_level"] == "Critique"
    assert rows[0]["assets"] == "Serveur de fichiers | Sauvegardes"
    assert rows[0]["gdpr"] == "oui"
    assert (rows[0]["measures_open"], rows[0]["measures_total"]) == ("1", "2")
    assert mesures.read_text(encoding="utf-8-sig").splitlines()[0] == ";".join(MEASURE_COLUMNS)


def test_export_refuse_un_registre_invalide(tmp_path, capsys):
    casse = write(tmp_path / "r.toml", REGISTRE.read_text(encoding="utf-8").replace('treatment = "transfer"\n', ""))
    assert export.main([str(casse), *METHODS, *JOUR]) == 1
    err = capsys.readouterr().err
    assert "R03.treatment" in err
    assert "Export impossible" in err


def test_export_n_ecrase_pas_sans_force(tmp_path, capsys):
    sortie = write(tmp_path / "r.json", "ancien")
    assert export.main([str(REGISTRE), "-o", str(sortie), *METHODS, *JOUR]) == 2
    assert sortie.read_text(encoding="utf-8") == "ancien"
    assert export.main([str(REGISTRE), "-o", str(sortie), "--force", *METHODS, *JOUR]) == 0
    assert json.loads(sortie.read_text(encoding="utf-8"))["schema_version"] == 1


def test_export_mesures_reserve_au_csv():
    with pytest.raises(SystemExit) as fin:
        export.main([str(REGISTRE), "--measures", "m.csv"])
    assert fin.value.code == 2


# ── 6. risk-import et aller-retour ──────────────────────────
@pytest.fixture
def csv_exportes(tmp_path):
    risques, mesures = tmp_path / "risques.csv", tmp_path / "mesures.csv"
    export.main([str(REGISTRE), "--format", "csv", "-o", str(risques), "--measures", str(mesures), *METHODS, *JOUR])
    return risques, mesures


def test_aller_retour_export_puis_import(tmp_path, csv_exportes, capsys):
    risques, mesures = csv_exportes
    sortie = tmp_path / "importe.toml"
    assert importer.main([str(risques), "--measures", str(mesures), "-o", str(sortie), *IMPORT]) == 0
    assert "importe.toml écrit (3 risque(s)) — registre valide" in capsys.readouterr().out
    methods = [ROOT / "methods"]
    original, _ = load_register(REGISTRE, methods, TODAY)
    importe, problems = load_register(sortie, methods, TODAY)
    assert problems == []
    # Tout est conservé, sauf l'historique, qui n'a pas de colonne dans le CSV
    sans_historique = [dataclasses.replace(r, history=()) for r in original.risks]
    assert list(importe.risks) == sans_historique


def test_formule_importee_reste_du_texte(tmp_path, capsys):
    risques = write(tmp_path / "r.csv", 'id;title;owner\nR01;"=HYPERLINK(""http://exemple.invalid"")";\'@moi\n')
    sortie = tmp_path / "r.toml"
    assert importer.main([str(risques), "-o", str(sortie), *IMPORT]) == 1  # registre à compléter
    data = tomllib.loads(sortie.read_text(encoding="utf-8"))
    assert data["risks"][0]["title"] == '=HYPERLINK("http://exemple.invalid")'  # simple texte dans le TOML
    assert data["risks"][0]["owner"] == "@moi"  # apostrophe de protection retirée
    # …et redevient inoffensive à l'export suivant
    assert neutralize(data["risks"][0]["title"]).startswith("'=")


def test_import_liste_ce_qui_reste_a_completer(tmp_path, capsys):
    risques = write(tmp_path / "r.csv", "id;title;treatment\nR01;Vol de portable;reduce\n")
    assert importer.main([str(risques), "-o", str(tmp_path / "r.toml"), *IMPORT]) == 1
    out = capsys.readouterr().out
    assert "r.toml: R01.owner : texte non vide attendu" in out
    assert "r.toml: R01.measures : traitement « reduce » sans aucune mesure de réduction" in out
    assert out.splitlines()[-1].startswith("r.toml écrit (1 risque(s)) — ")


def test_import_cellule_invalide_rien_n_est_ecrit(tmp_path, capsys):
    risques = write(tmp_path / "r.csv", "id;review_next\nR01;01/03/2027\n")
    sortie = tmp_path / "r.toml"
    assert importer.main([str(risques), "-o", str(sortie), *IMPORT]) == 1
    err = capsys.readouterr().err
    assert "r.csv:2: colonne « review_next » : date AAAA-MM-JJ attendue" in err
    assert "rien n'a été écrit" in err
    assert not sortie.exists()


def test_import_n_ecrase_pas_sans_force(tmp_path, csv_exportes):
    risques, _ = csv_exportes
    sortie = write(tmp_path / "existant.toml", "# registre à conserver\n")
    assert importer.main([str(risques), "-o", str(sortie), *IMPORT]) == 2
    assert sortie.read_text(encoding="utf-8") == "# registre à conserver\n"


def test_methodes_chargees_pour_l_import():
    assert set(load_methods([ROOT / "methods"])) == {"iso27005-5x5", "ebios-rm-4x4"}
