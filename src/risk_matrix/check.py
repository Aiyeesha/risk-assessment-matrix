"""
Vérification des méthodes d'évaluation et des registres de risques (commande « risk-check »).

Chaque fichier TOML est lu et sa SYNTAXE vérifiée (message « fichier:ligne: message »,
reconnu par les éditeurs et par la CI), puis son CONTENU selon son type :
  - kind = "method"   : méthode d'évaluation (échelles, niveaux, grille, acceptation) ;
  - kind = "register" : registre de risques, vérifié avec la méthode qu'il désigne.

Deux sortes de messages :
  - les ERREURS (donnée invalide ou incohérente) ;
  - les AVERTISSEMENTS (« attention : »), pour ce qui est échu à la date du jour : revue,
    mesure ou acceptation dépassée. Ils n'échouent qu'avec --strict.

Codes de retour : 0 = valide, 1 = au moins une erreur (ou un avertissement avec --strict),
2 = mauvais usage.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from risk_matrix import __version__
from risk_matrix.console import setup_streams
from risk_matrix.method import Method, parse_method
from risk_matrix.register import parse_register

# ─────────────────────────────────────────────────────────────
# 1. Réglages
# ─────────────────────────────────────────────────────────────
# Dossiers vérifiés par défaut, depuis la racine du dépôt
DEFAULT_FOLDERS = ("methods", "examples")
# Dossier des méthodes mises à disposition des registres, même quand on ne vérifie qu'un registre
DEFAULT_METHODS = "methods"
# Un registre réel tient en quelques centaines de Ko : au-delà, on refuse de lire
# (protection contre un fichier démesuré, volontaire ou non)
MAX_BYTES = 1_048_576
# Dossiers jamais parcourus (environnements, caches, dépendances)
SKIP_DIRS = {".git", ".venv", "node_modules", "build", "dist", ".pytest_cache", ".ruff_cache", "__pycache__"}
# Types de fichiers reconnus (clé « kind » en tête de fichier)
KINDS = ("method", "register")
# Python 3.11 à 3.13 indiquent la position dans le message : « … (at line 3, column 7) »
_POSITION = re.compile(r"\(at line (?P<line>\d+), column \d+\)")


@dataclass(frozen=True)
class Problem:
    """Un problème détecté, rattaché à un fichier (et à une ligne si possible)."""

    path: Path
    message: str
    line: int | None = None
    warning: bool = False  # avertissement : à traiter, mais le fichier reste valide

    def render(self, root: Path) -> str:
        """Format « chemin:ligne: message », chemin relatif à la racine quand c'est possible."""
        try:
            shown = self.path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            shown = self.path.as_posix()
        where = f"{shown}:{self.line}" if self.line else shown
        return f"{where}: {'attention : ' if self.warning else ''}{self.message}"


# ─────────────────────────────────────────────────────────────
# 2. Lecture d'un fichier TOML
# ─────────────────────────────────────────────────────────────
def load_toml(path: Path) -> tuple[dict | None, list[Problem]]:
    """Lit un fichier TOML : (données, []) s'il est valide, (None, [problème]) sinon."""
    try:
        size = path.stat().st_size
        if size > MAX_BYTES:
            return None, [Problem(path, f"fichier trop volumineux ({size} octets, maximum {MAX_BYTES})")]
        raw = path.read_bytes()
    except OSError as exc:
        return None, [Problem(path, f"lecture impossible : {exc.strerror or exc}")]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, [Problem(path, f"encodage invalide : UTF-8 attendu (octet {exc.start})")]
    try:
        return tomllib.loads(text), []
    except tomllib.TOMLDecodeError as exc:
        # Python 3.14 fournit « lineno » ; avant, la position est dans le message
        line = getattr(exc, "lineno", None)
        message = str(exc)
        match = _POSITION.search(message)
        if line is None and match:
            line = int(match.group("line"))
        message = _POSITION.sub("", getattr(exc, "msg", message)).strip()
        return None, [Problem(path, f"syntaxe TOML : {message}", line)]


# ─────────────────────────────────────────────────────────────
# 3. Fichiers à vérifier
# ─────────────────────────────────────────────────────────────
def iter_toml(targets: Iterable[Path]) -> list[Path]:
    """Fichiers .toml désignés : un fichier tel quel, un dossier parcouru récursivement (trié)."""
    found: list[Path] = []
    for target in targets:
        if target.is_file():
            found.append(target)
            continue
        for path in sorted(target.rglob("*.toml")):
            if not SKIP_DIRS.intersection(part for part in path.relative_to(target).parts[:-1]):
                found.append(path)
    return found


def _same(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def run_checks(
    paths: Iterable[Path], methods_dirs: Iterable[Path] = (), today: date | None = None
) -> tuple[int, list[Problem]]:
    """
    Vérifie chaque fichier ; renvoie (nombre de fichiers vérifiés, problèmes et avertissements).

    Ordre : toutes les MÉTHODES d'abord (celles des chemins vérifiés, puis celles de « methods_dirs »,
    lues sans être signalées), puis les REGISTRES, qui ont besoin d'elles.
    """
    today = today or date.today()
    files = iter_toml(paths)
    problems: list[Problem] = []
    methods: dict[str, Method] = {}
    origin: dict[str, Path] = {}
    registers: list[tuple[Path, dict]] = []

    # ── 1. Lecture, type de fichier et méthodes ─────────────
    for path in files:
        data, found = load_toml(path)
        problems.extend(found)
        if data is None:
            continue
        kind = data.get("kind")
        if kind not in KINDS:
            problems.append(Problem(path, f"kind : « {' » ou « '.join(KINDS)} » attendu en tête de fichier"))
        elif kind == "register":
            registers.append((path, data))
        else:
            method, errors = parse_method(data)
            problems.extend(Problem(path, message) for message in errors)
            if method is None:
                continue
            # Deux méthodes ne peuvent pas porter le même identifiant : un registre ne saurait laquelle utiliser
            if method.id in origin:
                problems.append(Problem(path, f"id : « {method.id} » déjà utilisé par {origin[method.id].name}"))
                continue
            methods[method.id], origin[method.id] = method, path

    # ── 2. Méthodes mises à disposition (non vérifiées ici) ─
    for path in iter_toml(d for d in methods_dirs if d.is_dir()):
        if any(_same(path, f) for f in files):
            continue
        data, _ = load_toml(path)
        if data is not None and data.get("kind") == "method":
            method, _ = parse_method(data)
            if method is not None:
                methods.setdefault(method.id, method)

    # ── 3. Registres ────────────────────────────────────────
    for path, data in registers:
        _register, findings = parse_register(data, methods, today)
        problems.extend(Problem(path, message) for message in findings.errors)
        problems.extend(Problem(path, message, warning=True) for message in findings.warnings)
    problems.sort(key=lambda p: files.index(p.path))  # dans l'ordre des fichiers, erreurs puis avertissements
    return len(files), problems


# ─────────────────────────────────────────────────────────────
# 4. Ligne de commande
# ─────────────────────────────────────────────────────────────
def _day(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"date invalide « {value} » (format AAAA-MM-JJ)") from None


def summary(count: int, problems: list[Problem]) -> str:
    errors = sum(not p.warning for p in problems)
    warnings = len(problems) - errors
    parts = [f"{errors} problème(s)" if errors else "OK"]
    if warnings:
        parts.append(f"{warnings} avertissement(s)")
    return f"{count} fichier(s) vérifié(s) — {', '.join(parts)}"


def main(argv: list[str] | None = None) -> int:
    setup_streams()
    parser = argparse.ArgumentParser(
        prog="risk-check",
        description="Vérifie les méthodes d'évaluation et les registres de risques (fichiers TOML).",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help=f"fichiers ou dossiers à vérifier (défaut : {', '.join(DEFAULT_FOLDERS)} du dossier courant)",
    )
    parser.add_argument(
        "--methods",
        type=Path,
        action="append",
        metavar="DOSSIER",
        help=f"dossier de méthodes disponibles pour les registres (répétable ; défaut : {DEFAULT_METHODS})",
    )
    parser.add_argument(
        "--today", type=_day, metavar="AAAA-MM-JJ", help="date de référence des échéances (défaut : aujourd'hui)"
    )
    parser.add_argument("--strict", action="store_true", help="les avertissements font aussi échouer (code 1)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    root = Path.cwd()
    asked = list(args.paths) + list(args.methods or [])
    missing = [p for p in asked if not p.exists()]
    if missing:
        print(f"Erreur : introuvable : {', '.join(map(str, missing))}", file=sys.stderr)
        return 2
    if args.paths:
        targets = list(args.paths)
    else:
        targets = [root / folder for folder in DEFAULT_FOLDERS if (root / folder).is_dir()]
    methods_dirs = args.methods or [root / DEFAULT_METHODS]

    count, problems = run_checks(targets, methods_dirs, args.today)
    for problem in problems:
        print(problem.render(root))
    print(summary(count, problems))
    failed = any(not p.warning for p in problems) or (args.strict and bool(problems))
    return 1 if failed else 0
