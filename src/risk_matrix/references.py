"""
Référentiels liés aux risques : mesures de l'annexe A d'ISO/IEC 27001:2022, techniques MITRE ATT&CK
et playbooks de réponse aux incidents.

Seuls des IDENTIFIANTS sont conservés ici :
  - annexe A : le texte des mesures est protégé par le droit d'auteur de l'ISO ; seuls leur numéro
    et le nom des quatre thèmes (organisationnel, humain, physique, technologique) sont repris ;
  - ATT&CK : le format de l'identifiant est vérifié (T1234 ou T1234.001), pas son existence, qui
    supposerait d'embarquer et de tenir à jour le référentiel complet (à vérifier sur attack.mitre.org) ;
  - playbooks : les sept playbooks du dépôt incident-response-playbook, avec leur titre.
"""

from __future__ import annotations

import re

from risk_matrix.method import Text

# ─────────────────────────────────────────────────────────────
# 1. ISO/IEC 27001:2022, annexe A : 93 mesures en quatre thèmes
# ─────────────────────────────────────────────────────────────
# Thème → (nombre de mesures, nom du thème). Les mesures sont numérotées 5.1 à 5.37, 6.1 à 6.8, etc.
ANNEX_A: dict[int, tuple[int, Text]] = {
    5: (37, Text("Mesures organisationnelles", "Organisational controls")),
    6: (8, Text("Mesures liées aux personnes", "People controls")),
    7: (14, Text("Mesures physiques", "Physical controls")),
    8: (34, Text("Mesures technologiques", "Technological controls")),
}
_ANNEX_A = re.compile(r"^(?P<theme>[5-8])\.(?P<number>[1-9][0-9]?)$")


def annex_a_theme(control: str) -> int | None:
    """Thème (5 à 8) d'une mesure de l'annexe A existante, ou None si le numéro n'existe pas."""
    match = _ANNEX_A.match(control)
    if not match:
        return None
    theme, number = int(match["theme"]), int(match["number"])
    return theme if number <= ANNEX_A[theme][0] else None


# ─────────────────────────────────────────────────────────────
# 2. MITRE ATT&CK : techniques et sous-techniques
# ─────────────────────────────────────────────────────────────
_ATTACK = re.compile(r"^T[0-9]{4}(?:\.[0-9]{3})?$")
ATTACK_URL = "https://attack.mitre.org/techniques/{path}/"


def is_attack_id(value: str) -> bool:
    return bool(_ATTACK.match(value))


def attack_url(technique: str) -> str:
    """Lien vers la fiche ATT&CK : T1566.001 → …/techniques/T1566/001/."""
    return ATTACK_URL.format(path=technique.replace(".", "/"))


# ─────────────────────────────────────────────────────────────
# 3. Playbooks de réponse aux incidents (dépôt incident-response-playbook)
# ─────────────────────────────────────────────────────────────
PLAYBOOK_REPO = "https://github.com/Aiyeesha/incident-response-playbook"
# Identifiant → (titre, nom du fichier en français, nom du fichier en anglais)
PLAYBOOKS: dict[str, tuple[Text, str, str]] = {
    "P01": (Text("Infection par logiciel malveillant", "Malware infection"), "P01-logiciel-malveillant", "P01-malware"),
    "P02": (Text("Attaque par rançongiciel", "Ransomware attack"), "P02-rancongiciel", "P02-ransomware"),
    "P03": (Text("Fuite de données", "Data breach"), "P03-fuite-de-donnees", "P03-data-breach"),
    "P04": (Text("Hameçonnage", "Phishing"), "P04-hameconnage", "P04-phishing"),
    "P05": (Text("Accès non autorisé", "Unauthorised access"), "P05-acces-non-autorise", "P05-unauthorised-access"),
    "P06": (Text("Déni de service", "Denial of service"), "P06-deni-de-service", "P06-denial-of-service"),
    "P07": (
        Text("Compte compromis et fraude au virement", "Compromised account and payment fraud"),
        "P07-compte-compromis",
        "P07-compromised-account",
    ),
}


def playbook_url(playbook: str, lang: str) -> str:
    """Lien vers le playbook dans la langue du registre."""
    _title, fr_file, en_file = PLAYBOOKS[playbook]
    return f"{PLAYBOOK_REPO}/blob/main/{lang}/playbooks/{fr_file if lang == 'fr' else en_file}.md"
