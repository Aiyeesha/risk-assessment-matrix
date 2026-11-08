"""
Options et sorties communes aux commandes (risk-check, risk-export, risk-import, risk-report).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from risk_matrix import __version__

DEFAULT_METHODS = "methods"  # dossier des méthodes mises à disposition des registres


def day_arg(value: str) -> date:
    """Type argparse : date AAAA-MM-JJ."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide « {value} » (format AAAA-MM-JJ)") from None


def add_common_options(parser: argparse.ArgumentParser) -> None:
    """--methods, --today et --version, avec le même sens pour toutes les commandes."""
    parser.add_argument(
        "--methods",
        type=Path,
        action="append",
        metavar="DOSSIER",
        help=f"dossier de méthodes disponibles pour les registres (répétable ; défaut : {DEFAULT_METHODS})",
    )
    parser.add_argument(
        "--today", type=day_arg, metavar="AAAA-MM-JJ", help="date de référence des échéances (défaut : aujourd'hui)"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")


def methods_dirs(args: argparse.Namespace, root: Path) -> list[Path]:
    return args.methods or [root / DEFAULT_METHODS]


def missing_paths(paths: list[Path]) -> bool:
    """Signale les chemins introuvables (code 2 : mauvais usage) ; vrai s'il en manque."""
    missing = [p for p in paths if not p.exists()]
    if missing:
        print(f"Erreur : introuvable : {', '.join(map(str, missing))}", file=sys.stderr)
    return bool(missing)


def write_output(path: Path | None, text: str, force: bool, bom: bool = False) -> bool:
    """
    Écrit « text » dans « path », ou sur la sortie standard si path est None.
    N'écrase jamais un fichier existant sans --force ; renvoie faux si l'écriture est refusée.
    bom : ajoute la marque UTF-8 attendue par Excel pour reconnaître l'encodage d'un CSV.
    """
    if path is None:
        sys.stdout.write(text)
        return True
    if path.exists() and not force:
        print(f"Erreur : {path} existe déjà (--force pour le remplacer)", file=sys.stderr)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" : les fins de ligne du texte sont écrites telles quelles (CRLF du CSV compris)
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as f:
        f.write(text)
    return True
