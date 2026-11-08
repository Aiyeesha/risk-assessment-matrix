"""
Vérification des méthodes d'évaluation et des registres de risques (commande « risk-check »).

Chaque fichier TOML est lu et sa SYNTAXE vérifiée (message « fichier:ligne: message »,
reconnu par les éditeurs et par la CI), puis son CONTENU selon son type :
  - kind = "method"   : méthode d'évaluation (échelles, niveaux, grille, acceptation) ;
  - kind = "register" : registre de risques (contrôles de contenu ajoutés à l'étape 3).

Codes de retour : 0 = tout est valide, 1 = au moins un problème, 2 = mauvais usage.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from risk_matrix import __version__
from risk_matrix.console import setup_streams
from risk_matrix.method import Method, parse_method

# ─────────────────────────────────────────────────────────────
# 1. Réglages
# ─────────────────────────────────────────────────────────────
# Dossiers vérifiés par défaut, depuis la racine du dépôt
DEFAULT_FOLDERS = ("methods", "examples")
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

    def render(self, root: Path) -> str:
        """Format « chemin:ligne: message », chemin relatif à la racine quand c'est possible."""
        try:
            shown = self.path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            shown = self.path.as_posix()
        where = f"{shown}:{self.line}" if self.line else shown
        return f"{where}: {self.message}"


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


def check_file(path: Path) -> tuple[Method | None, list[Problem]]:
    """Syntaxe, puis contenu selon le type ; renvoie la méthode lue s'il s'agit d'une méthode valide."""
    data, problems = load_toml(path)
    if data is None:
        return None, problems
    kind = data.get("kind")
    if kind not in KINDS:
        return None, [Problem(path, f"kind : « {' » ou « '.join(KINDS)} » attendu en tête de fichier")]
    if kind == "method":
        method, errors = parse_method(data)
        return method, [Problem(path, message) for message in errors]
    return None, []  # registre : contrôles de contenu à l'étape 3


def run_checks(paths: Iterable[Path]) -> tuple[int, list[Problem]]:
    """Vérifie chaque fichier ; renvoie (nombre de fichiers lus, problèmes)."""
    files = iter_toml(paths)
    problems: list[Problem] = []
    seen: dict[str, Path] = {}
    for path in files:
        method, found = check_file(path)
        problems.extend(found)
        # Deux méthodes ne peuvent pas porter le même identifiant : un registre ne saurait laquelle utiliser
        if method is not None:
            if method.id in seen:
                problems.append(Problem(path, f"id : « {method.id} » déjà utilisé par {seen[method.id].name}"))
            seen.setdefault(method.id, path)
    return len(files), problems


# ─────────────────────────────────────────────────────────────
# 4. Ligne de commande
# ─────────────────────────────────────────────────────────────
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
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args(argv)

    root = Path.cwd()
    if args.paths:
        missing = [p for p in args.paths if not p.exists()]
        if missing:
            print(f"Erreur : introuvable : {', '.join(map(str, missing))}", file=sys.stderr)
            return 2
        targets = list(args.paths)
    else:
        targets = [root / folder for folder in DEFAULT_FOLDERS if (root / folder).is_dir()]

    count, problems = run_checks(targets)
    for problem in problems:
        print(problem.render(root))
    status = "OK" if not problems else f"{len(problems)} problème(s)"
    print(f"{count} fichier(s) vérifié(s) — {status}")
    return 1 if problems else 0
