"""
Tests de « risk-check » : lecture des fichiers, syntaxe TOML, ligne de commande.

Chaque test construit ses fichiers dans un dossier temporaire (tmp_path).
"""

from datetime import date
from importlib.metadata import version
from pathlib import Path

import pytest

import risk_matrix
from risk_matrix.check import MAX_BYTES, iter_toml, load_toml, main, run_checks

# Méthode valide de référence : le préréglage 5×5 du dépôt
METHODE = (Path(__file__).parents[1] / "methods" / "iso27005-5x5.toml").read_text(encoding="utf-8")
# Registre valide et sans avertissement au 2026-11-08
REGISTRE = (Path(__file__).parent / "data" / "registre-valide.toml").read_text(encoding="utf-8")
JOUR = "2026-11-08"


def write(root: Path, relative: str, content: str | bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


# ── Paquet ──────────────────────────────────────────────────
def test_version_coherente():
    assert version("risk-assessment-matrix") == risk_matrix.__version__


def test_option_version(capsys):
    with pytest.raises(SystemExit) as fin:
        main(["--version"])
    assert fin.value.code == 0
    assert capsys.readouterr().out.strip() == f"risk-check {risk_matrix.__version__}"


# ── Lecture d'un fichier ────────────────────────────────────
def test_toml_valide(tmp_path):
    data, problems = load_toml(write(tmp_path, "m.toml", 'nom = "Méthode 5×5"\n[seuils]\nacceptable = 6\n'))
    assert problems == []
    assert data == {"nom": "Méthode 5×5", "seuils": {"acceptable": 6}}


def test_erreur_de_syntaxe_avec_numero_de_ligne(tmp_path):
    path = write(tmp_path, "m.toml", 'nom = "ok"\n\ncle = = 3\n')
    data, (problem,) = load_toml(path)
    assert data is None
    assert problem.line == 3
    assert problem.message.startswith("syntaxe TOML : ")
    assert "line" not in problem.message  # la position n'est pas répétée dans le texte


def test_cle_en_double(tmp_path):
    _data, (problem,) = load_toml(write(tmp_path, "m.toml", "a = 1\na = 2\n"))
    assert problem.line == 2


def test_encodage_invalide(tmp_path):
    _data, (problem,) = load_toml(write(tmp_path, "m.toml", "nom = 'caf\xe9'\n".encode("latin-1")))
    assert problem.message.startswith("encodage invalide : UTF-8 attendu")


def test_fichier_trop_volumineux(tmp_path):
    _data, (problem,) = load_toml(write(tmp_path, "m.toml", b"#" * (MAX_BYTES + 1)))
    assert problem.message.startswith("fichier trop volumineux")


# ── Fichiers parcourus ──────────────────────────────────────
def test_parcours_trie_et_dossiers_ignores(tmp_path):
    write(tmp_path, "b.toml", "")
    write(tmp_path, "sous/a.toml", "")
    write(tmp_path, "node_modules/x.toml", "")
    write(tmp_path, ".venv/y.toml", "")
    write(tmp_path, "notes.md", "")
    assert [p.relative_to(tmp_path).as_posix() for p in iter_toml([tmp_path])] == ["b.toml", "sous/a.toml"]


def test_fichier_designe_directement(tmp_path):
    path = write(tmp_path, "registre.toml", "")
    assert iter_toml([path]) == [path]


def test_plusieurs_problemes(tmp_path):
    write(tmp_path, "a.toml", "x = \n")
    write(tmp_path, "b.toml", METHODE)
    write(tmp_path, "c.toml", "[t\n")
    count, problems = run_checks([tmp_path])
    assert count == 3
    assert [p.path.name for p in problems] == ["a.toml", "c.toml"]


# ── Ligne de commande ───────────────────────────────────────
@pytest.fixture
def depot(tmp_path, monkeypatch):
    """Dossier de travail avec les dossiers vérifiés par défaut."""
    write(tmp_path, "methods/5x5.toml", METHODE)
    write(tmp_path, "examples/fr/registre.toml", REGISTRE)
    write(tmp_path, "pyproject.toml", "[project\n")  # hors des dossiers vérifiés : ignoré
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_dossiers_par_defaut(depot, capsys):
    assert main(["--today", JOUR]) == 0
    assert capsys.readouterr().out.strip() == "2 fichier(s) vérifié(s) — OK"


def test_probleme_au_format_editeur(depot, capsys):
    write(depot, "methods/casse.toml", "a = 1\n\nb = \n")
    assert main(["--today", JOUR]) == 1
    sortie = capsys.readouterr().out.splitlines()
    assert sortie[0].startswith("methods/casse.toml:3: syntaxe TOML : ")
    assert sortie[-1] == "3 fichier(s) vérifié(s) — 1 problème(s)"


def test_chemin_introuvable(depot, capsys):
    assert main(["absent.toml"]) == 2
    assert "introuvable : absent.toml" in capsys.readouterr().err


def test_chemin_explicite(depot, capsys):
    assert main([str(depot / "methods")]) == 0
    assert "1 fichier(s) vérifié(s) — OK" in capsys.readouterr().out


# ── Type de fichier et méthodes ─────────────────────────────
def test_type_de_fichier_obligatoire(tmp_path):
    write(tmp_path, "m.toml", 'nom = "sans type"\n')
    _count, (problem,) = run_checks([tmp_path])
    assert problem.message == "kind : « method » ou « register » attendu en tête de fichier"


def test_methode_invalide_signalee_avec_le_chemin_du_champ(tmp_path):
    write(tmp_path, "m.toml", METHODE.replace('appetite = "low"', 'appetite = "inconnu"'))
    _count, problems = run_checks([tmp_path])
    assert [p.message for p in problems] == ["acceptance.appetite : niveau inconnu « inconnu »"]


def test_identifiant_de_methode_en_double(tmp_path):
    write(tmp_path, "a.toml", METHODE)
    write(tmp_path, "b.toml", METHODE)
    _count, problems = run_checks([tmp_path])
    assert [(p.path.name, p.message) for p in problems] == [("b.toml", "id : « iso27005-5x5 » déjà utilisé par a.toml")]


def test_preréglages_du_depot_valides():
    count, problems = run_checks([Path(__file__).parents[1] / "methods"])
    assert count == 2
    assert problems == []


# ── Registres ───────────────────────────────────────────────
def test_registre_verifie_avec_sa_methode(tmp_path):
    write(tmp_path, "methods/5x5.toml", METHODE)
    write(tmp_path, "r.toml", REGISTRE.replace('role = "Responsable du risque"', 'role = "Stagiaire"'))
    _count, problems = run_checks([tmp_path], today=date(2026, 11, 8))
    assert [p.message.split(" : ")[0] for p in problems] == ["R02.acceptance.role"]


def test_methode_lue_dans_le_dossier_des_methodes(tmp_path):
    """Seul le registre est vérifié ; sa méthode vient de --methods, sans être recomptée."""
    write(tmp_path, "methodes/5x5.toml", METHODE)
    registre = write(tmp_path, "r.toml", REGISTRE)
    count, problems = run_checks([registre], [tmp_path / "methodes"], date(2026, 11, 8))
    assert (count, problems) == (1, [])


def test_methode_absente(tmp_path):
    registre = write(tmp_path, "r.toml", REGISTRE)
    _count, (problem,) = run_checks([registre], today=date(2026, 11, 8))
    assert problem.message == "method : méthode « iso27005-5x5 » introuvable (disponibles : aucune)"


def test_avertissements_n_echouent_pas(depot, capsys):
    assert main(["--today", "2027-01-15"]) == 0
    sortie = capsys.readouterr().out.splitlines()
    assert sortie[0] == "examples/fr/registre.toml: attention : R01.review : revue en retard (prévue le 2027-01-01)"
    assert sortie[-1] == "2 fichier(s) vérifié(s) — OK, 1 avertissement(s)"


def test_mode_strict(depot, capsys):
    assert main(["--today", "2027-01-15", "--strict"]) == 1


def test_erreurs_et_avertissements_comptes_a_part(depot, capsys):
    write(depot, "methods/casse.toml", "b = \n")
    assert main(["--today", "2027-01-15"]) == 1
    assert capsys.readouterr().out.splitlines()[-1] == "3 fichier(s) vérifié(s) — 1 problème(s), 1 avertissement(s)"


def test_registre_designe_seul_utilise_le_dossier_methods(depot, capsys):
    assert main(["examples/fr/registre.toml", "--today", JOUR]) == 0
    assert capsys.readouterr().out.strip() == "1 fichier(s) vérifié(s) — OK"


def test_date_de_reference_invalide(depot, capsys):
    with pytest.raises(SystemExit) as fin:
        main(["--today", "08/11/2026"])
    assert fin.value.code == 2
    assert "date invalide « 08/11/2026 » (format AAAA-MM-JJ)" in capsys.readouterr().err


def test_dossier_de_methodes_introuvable(depot, capsys):
    assert main(["--methods", "absent"]) == 2
