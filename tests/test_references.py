"""Tests des référentiels : numéros de l'annexe A, format ATT&CK, playbooks."""

import pytest

from risk_matrix.references import ANNEX_A, PLAYBOOKS, annex_a_theme, attack_url, is_attack_id, playbook_url


def test_annexe_a_93_mesures():
    assert sum(count for count, _name in ANNEX_A.values()) == 93
    valides = [f"{t}.{n}" for t, (count, _name) in ANNEX_A.items() for n in range(1, count + 1)]
    assert len(valides) == 93
    assert all(annex_a_theme(c) is not None for c in valides)


@pytest.mark.parametrize(("mesure", "theme"), [("5.1", 5), ("5.37", 5), ("6.8", 6), ("7.14", 7), ("8.34", 8)])
def test_bornes_de_l_annexe_a(mesure, theme):
    assert annex_a_theme(mesure) == theme


@pytest.mark.parametrize("mesure", ["5.0", "5.38", "6.9", "7.15", "8.35", "4.1", "9.1", "8.01", "A.5.1", "8", ""])
def test_numeros_hors_annexe_a(mesure):
    assert annex_a_theme(mesure) is None


@pytest.mark.parametrize(("technique", "valide"), [
    ("T1486", True), ("T1566.001", True), ("T148", False), ("T1566.1", False), ("t1486", False), ("TA0040", False),
])  # fmt: skip
def test_format_att_ck(technique, valide):
    assert is_attack_id(technique) is valide


def test_liens():
    assert attack_url("T1566.001") == "https://attack.mitre.org/techniques/T1566/001/"
    assert attack_url("T1486") == "https://attack.mitre.org/techniques/T1486/"
    assert playbook_url("P02", "fr").endswith("/blob/main/fr/playbooks/P02-rancongiciel.md")
    assert playbook_url("P02", "en").endswith("/blob/main/en/playbooks/P02-ransomware.md")


def test_sept_playbooks():
    assert list(PLAYBOOKS) == [f"P0{i}" for i in range(1, 8)]
    assert PLAYBOOKS["P07"][0].en == "Compromised account and payment fraud"
