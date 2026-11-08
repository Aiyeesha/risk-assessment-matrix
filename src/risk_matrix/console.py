"""Réglages communs des commandes en ligne (risk-check, puis risk-report et risk-export)."""

from __future__ import annotations

import sys
from typing import TextIO


def use_utf8(stream: TextIO) -> None:
    """
    Force l'UTF-8 quand la sortie est redirigée (fichier, tube, autre programme).

    Sous Windows, une sortie redirigée utilise sinon l'encodage régional (cp1252) :
    les accents arrivent abîmés dans PowerShell, et certains caractères (—, …) peuvent
    faire échouer l'affichage. Dans une vraie console, Python gère déjà l'Unicode.
    Même réglage que dans le projet port-scanner.
    """
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None and not stream.isatty():
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


def setup_streams() -> None:
    """Applique use_utf8 à la sortie standard et à la sortie d'erreur."""
    use_utf8(sys.stdout)
    use_utf8(sys.stderr)
