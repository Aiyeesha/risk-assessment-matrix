"""
Export d'un registre vérifié (commande « risk-export ») : JSON ou CSV.

  - JSON : registre complet, enrichi de ce que calcule la méthode (niveau de chaque note, liens
    ATT&CK et playbooks, avertissements à la date de référence). Format stable, versionné par
    « schema_version », destiné à l'interface web et à d'autres outils ;
  - CSV  : un fichier des risques et, avec --measures, un fichier des mesures, pour un tableur.
    Chaque cellule est protégée contre l'injection de formules (voir tabular.py).

Un registre invalide n'est jamais exporté : ses erreurs sont affichées (code de retour 1).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from risk_matrix import __version__
from risk_matrix.check import load_register
from risk_matrix.cli import add_common_options, methods_dirs, missing_paths, write_output
from risk_matrix.console import setup_streams
from risk_matrix.method import Method, Text
from risk_matrix.references import ANNEX_A, PLAYBOOKS, annex_a_theme, attack_url, playbook_url
from risk_matrix.register import Register, Score
from risk_matrix.tabular import MEASURE_COLUMNS, RISK_COLUMNS, measure_rows, risk_rows, write_csv

SCHEMA_VERSION = 1  # à augmenter à chaque changement incompatible du JSON


# ─────────────────────────────────────────────────────────────
# 1. Registre → JSON
# ─────────────────────────────────────────────────────────────
def _day(value: date | None) -> str | None:
    return value.isoformat() if value else None


def _method(method: Method, lang: str) -> dict:
    def axis(a) -> dict:
        return {
            "name": a.name.get(lang),
            "levels": [{"value": lv.value, "label": lv.label.get(lang), "description": lv.description.get(lang)}
                       for lv in a.levels],
        }  # fmt: skip

    return {
        "id": method.id,
        "name": method.name.get(lang),
        "references": list(method.references),
        "likelihood": axis(method.likelihood),
        "impact": axis(method.impact),
        "levels": [
            {
                "id": lv.id,
                "label": lv.label.get(lang),
                "color": lv.color,
                "review_months": lv.review_months,
                "guidance": lv.guidance.get(lang),
            }
            for lv in method.levels
        ],  # fmt: skip
        "grid": [list(row) for row in method.grid],  # grid[vraisemblance - 1][impact - 1]
        "appetite": method.appetite,
        "authorities": [
            {"level": a.level, "by": a.by.get(lang), "max_months": a.max_months} for a in method.authorities
        ],  # fmt: skip
    }


def _score(method: Method, score: Score) -> dict:
    return {
        "likelihood": score.likelihood,
        "impact": score.impact,
        "level": method.level_of(score.likelihood, score.impact).id,
    }


def _controls(controls: tuple[str, ...], lang: str) -> list[dict]:
    themes: dict[int, Text] = {theme: name for theme, (_count, name) in ANNEX_A.items()}
    return [{"id": c, "theme": themes[annex_a_theme(c)].get(lang)} for c in controls]


def to_json(register: Register, warnings: list[str], today: date) -> dict:
    lang, method = register.lang, register.method
    risks = []
    for risk in register.risks:
        a = risk.acceptance
        risks.append({
            "id": risk.id,
            "title": risk.title,
            "description": risk.description,
            "category": risk.category,
            "owner": risk.owner,
            "status": risk.status,
            "assets": list(risk.assets),
            "threat": risk.threat,
            "vulnerability": risk.vulnerability,
            "gdpr": risk.gdpr,
            "nis2": risk.nis2,
            "inherent": _score(method, risk.inherent),
            "existing_controls": list(risk.existing_controls),
            "measures": [
                {"title": m.title, "owner": m.owner, "due": _day(m.due), "status": m.status,
                 "iso27001": _controls(m.iso27001, lang)}
                for m in risk.measures
            ],
            "residual": {**_score(method, risk.residual), "justification": risk.residual_justification},
            "treatment": risk.treatment,
            "transfer_to": risk.transfer_to,
            "acceptance": None if a is None else {
                "by": a.by, "role": a.role, "on": _day(a.on), "until": _day(a.until), "rationale": a.rationale,
            },
            "review": {"last": _day(risk.review.last), "next": _day(risk.review.next)},
            "history": [{"on": _day(h.on), "by": h.by, "change": h.change} for h in risk.history],
            "iso27001": _controls(risk.iso27001, lang),
            "attack": [{"id": t, "url": attack_url(t)} for t in risk.attack],
            "playbooks": [{"id": p, "title": PLAYBOOKS[p][0].get(lang), "url": playbook_url(p, lang)}
                          for p in risk.playbooks],
        })  # fmt: skip
    return {
        "schema_version": SCHEMA_VERSION,
        "generator": f"risk-assessment-matrix {__version__}",
        "as_of": today.isoformat(),  # date de référence des avertissements
        "register": {
            "organisation": register.organisation,
            "lang": lang,
            "assessed_on": _day(register.assessed_on),
            "assessor": register.assessor,
        },
        "method": _method(method, lang),
        "risks": risks,
        "warnings": warnings,
    }


# ─────────────────────────────────────────────────────────────
# 2. Ligne de commande
# ─────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    setup_streams()
    parser = argparse.ArgumentParser(
        prog="risk-export",
        description="Exporte un registre vérifié en JSON ou en CSV (protégé contre l'injection de formules).",
    )
    parser.add_argument("register", type=Path, help="registre à exporter (fichier TOML)")
    parser.add_argument("--format", choices=("json", "csv"), default="json", help="format de sortie (défaut : json)")
    parser.add_argument("-o", "--output", type=Path, help="fichier de sortie (défaut : sortie standard)")
    parser.add_argument("--measures", type=Path, metavar="FICHIER", help="CSV : fichier des mesures, en plus")
    parser.add_argument(
        "--delimiter", choices=(";", ","), help="CSV : séparateur (défaut : « ; » en français, « , » en anglais)"
    )
    parser.add_argument("--force", action="store_true", help="remplace les fichiers de sortie existants")
    add_common_options(parser)
    args = parser.parse_args(argv)
    if args.measures and args.format != "csv":
        parser.error("--measures ne s'utilise qu'avec --format csv")

    root = Path.cwd()
    if missing_paths([args.register, *(args.methods or [])]):
        return 2
    today = args.today or date.today()
    register, problems = load_register(args.register, methods_dirs(args, root), today)
    if register is None:
        for problem in problems:
            print(problem.render(root), file=sys.stderr)
        print("Export impossible : corriger d'abord le registre (risk-check).", file=sys.stderr)
        return 1
    warnings = [p.message for p in problems if p.warning]

    if args.format == "json":
        text = json.dumps(to_json(register, warnings, today), ensure_ascii=False, indent=2) + "\n"
        return 0 if write_output(args.output, text, args.force) else 2

    delimiter = args.delimiter or (";" if register.lang == "fr" else ",")
    to_file = args.output is not None  # BOM pour Excel dans un fichier, pas sur la sortie standard
    if not write_output(args.output, write_csv(risk_rows(register), RISK_COLUMNS, delimiter), args.force, to_file):
        return 2
    if args.measures:
        text = write_csv(measure_rows(register), MEASURE_COLUMNS, delimiter)
        if not write_output(args.measures, text, args.force, bom=True):
            return 2
    return 0
