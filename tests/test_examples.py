"""
Tests des registres d'exemple (Atelier Lumen) : validité, avertissement voulu, parallélisme des
versions française et anglaise, et fraîcheur des sorties générées (rapports, JSON).
"""

import importlib.util
import tomllib
from pathlib import Path

import pytest

from risk_matrix.check import load_register

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "examples"
NAMES = ["atelier-lumen", "atelier-lumen-ebios"]

# Le script de génération n'est pas dans le paquet : on le charge depuis son chemin
_spec = importlib.util.spec_from_file_location("build_examples", ROOT / "scripts" / "build_examples.py")
build_examples = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_examples)


@pytest.mark.parametrize("lang", ["fr", "en"])
@pytest.mark.parametrize("name", NAMES)
def test_exemples_valides(lang, name):
    register, problems = load_register(EXAMPLES / lang / f"{name}.toml", [ROOT / "methods"], build_examples.AS_OF)
    assert register is not None, [p.message for p in problems]
    assert register.lang == lang
    warnings = [p.message.split(" : ")[0] for p in problems if p.warning]
    # Seul avertissement voulu : le test d'intrusion en retard du registre 5×5 (montré dans les rapports)
    assert warnings == (["R03.measures[1]"] if name == "atelier-lumen" else [])


def _structure(data: dict) -> list:
    """Tout ce qui ne dépend pas de la langue : identifiants, notes, dates, états, références."""
    keys = ("id", "status", "gdpr", "nis2", "inherent", "residual", "treatment", "review", "iso27001", "attack",
            "playbooks")  # fmt: skip
    risks = []
    for r in data["risks"]:
        acceptance = r.get("acceptance", {})
        risks.append((
            {k: r.get(k) for k in keys},
            [(m["due"], m["status"], m.get("iso27001")) for m in r.get("measures", [])],
            [h["on"] for h in r.get("history", [])],
            (acceptance.get("on"), acceptance.get("until")),
            len(r.get("assets", [])), len(r.get("existing_controls", [])),
        ))  # fmt: skip
    return [data["method"], data["assessed_on"], risks]


@pytest.mark.parametrize("name", NAMES)
def test_versions_francaise_et_anglaise_paralleles(name):
    versions = {}
    for lang in ("fr", "en"):
        with (EXAMPLES / lang / f"{name}.toml").open("rb") as f:
            versions[lang] = tomllib.load(f)
    assert _structure(versions["fr"]) == _structure(versions["en"])


def test_sorties_d_exemple_a_jour(capsys):
    """Les rapports et exports d'exemple doivent correspondre aux registres (sinon : régénérer)."""
    assert build_examples.main(["--check"]) == 0, capsys.readouterr().err
