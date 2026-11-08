"""
Import d'un registre depuis un tableur (commande « risk-import ») : CSV → fichier TOML.

Usage typique : reprendre un registre tenu jusque-là dans Excel. Les colonnes sont celles de
« risk-export --format csv » (un export modifié dans un tableur se réimporte donc tel quel).

Déroulé :
  1. lecture sûre des CSV (taille, encodage, en-tête, structure — voir tabular.py) ;
  2. conversion des cellules (entiers, dates, oui/non, listes « a | b ») ;
  3. écriture du fichier TOML, jamais par-dessus un fichier existant sans --force ;
  4. vérification du registre obtenu, comme risk-check : ce qui reste à compléter est listé.

Codes de retour : 0 = registre écrit et valide ; 1 = CSV inutilisable (rien n'est écrit) ou registre
écrit mais à compléter ; 2 = mauvais usage.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from datetime import date
from pathlib import Path

from risk_matrix.check import Problem, load_methods
from risk_matrix.cli import add_common_options, day_arg, methods_dirs, missing_paths, write_output
from risk_matrix.console import setup_streams
from risk_matrix.register import parse_register
from risk_matrix.tabular import MEASURE_COLUMNS, RISK_COLUMNS, CsvError, read_csv, rows_to_register
from risk_matrix.toml_writer import dump_register


def main(argv: list[str] | None = None) -> int:
    setup_streams()
    parser = argparse.ArgumentParser(
        prog="risk-import",
        description="Crée un registre TOML à partir d'un fichier CSV des risques (et, au besoin, des mesures).",
    )
    parser.add_argument("risks", type=Path, help="CSV des risques (colonnes de risk-export --format csv)")
    parser.add_argument("-o", "--output", type=Path, required=True, help="registre TOML à créer")
    parser.add_argument("--measures", type=Path, metavar="FICHIER", help="CSV des mesures (colonne risk_id)")
    parser.add_argument("--method", required=True, help="identifiant de la méthode (ex. iso27005-5x5)")
    parser.add_argument("--lang", choices=("fr", "en"), default="fr", help="langue du registre (défaut : fr)")
    parser.add_argument("--organisation", required=True, help="organisation évaluée")
    parser.add_argument("--assessed-on", type=day_arg, required=True, metavar="AAAA-MM-JJ", help="date d'évaluation")
    parser.add_argument("--assessor", required=True, help="auteur de l'évaluation")
    parser.add_argument("--delimiter", choices=(";", ","), help="séparateur (défaut : détecté sur l'en-tête)")
    parser.add_argument("--force", action="store_true", help="remplace le registre s'il existe déjà")
    add_common_options(parser)
    args = parser.parse_args(argv)

    root = Path.cwd()
    if missing_paths([args.risks, *([args.measures] if args.measures else []), *(args.methods or [])]):
        return 2

    # ── 1-2. Lecture et conversion ──────────────────────────
    problems: list[Problem] = []
    rows: dict[str, list] = {"risks": [], "measures": []}
    for key, path, columns in (("risks", args.risks, RISK_COLUMNS), ("measures", args.measures, MEASURE_COLUMNS)):
        if path is None:
            continue
        try:
            rows[key] = read_csv(path, columns, args.delimiter)
        except CsvError as exc:
            problems.append(Problem(path, exc.message, exc.line))
    if not problems:
        header = {
            "method": args.method,
            "lang": args.lang,
            "organisation": args.organisation,
            "assessed_on": args.assessed_on,
            "assessor": args.assessor,
        }
        data, errors = rows_to_register(header, rows["risks"], rows["measures"])
        source = {"risks": args.risks, "measures": args.measures}
        problems += [Problem(source[kind], message, line) for kind, line, message in errors]
    if problems:
        for problem in problems:
            print(problem.render(root), file=sys.stderr)
        print("Import impossible : rien n'a été écrit.", file=sys.stderr)
        return 1

    # ── 3. Écriture ─────────────────────────────────────────
    comment = (
        f"Registre importé de {args.risks.name}{f' et {args.measures.name}' if args.measures else ''} "
        f"par risk-import.\nÀ compléter (historique, champs manquants), puis à vérifier avec risk-check."
    )
    text = dump_register(data, comment)
    tomllib.loads(text)  # garde-fou : le fichier écrit doit toujours être du TOML valide
    if not write_output(args.output, text, args.force):
        return 2

    # ── 4. Vérification du registre obtenu ──────────────────
    _register, findings = parse_register(
        tomllib.loads(text), load_methods(methods_dirs(args, root)), args.today or date.today()
    )
    for message in findings.errors:
        print(Problem(args.output, message).render(root))
    for message in findings.warnings:
        print(Problem(args.output, message, warning=True).render(root))
    count = len(data["risks"])
    if findings.errors:
        print(f"{args.output.name} écrit ({count} risque(s)) — {len(findings.errors)} point(s) à compléter")
        return 1
    print(f"{args.output.name} écrit ({count} risque(s)) — registre valide")
    return 0
