"""
Génère les sorties d'exemple de chaque registre de examples/ : rapport Markdown, rapport HTML et
export JSON, écrits à côté du registre (atelier-lumen.toml → atelier-lumen.md, .html, .json).

La date de référence est FIXE (AS_OF) : les sorties ne changent que si le registre, la méthode
ou l'outil changent, jamais avec le temps qui passe.

Usage, depuis la racine du dépôt :
    python scripts/build_examples.py           # régénère les sorties
    python scripts/build_examples.py --check   # vérifie qu'elles sont à jour (CI) ; code 1 sinon
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from risk_matrix.check import load_register
from risk_matrix.console import setup_streams
from risk_matrix.export import to_json
from risk_matrix.report import build_report, render_html, render_markdown

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
METHODS = [ROOT / "methods"]
AS_OF = date(2026, 11, 8)  # « situation au » des sorties d'exemple


def outputs(register_path: Path) -> dict[Path, str]:
    """Contenu attendu de chaque sortie d'un registre d'exemple."""
    register, problems = load_register(register_path, METHODS, AS_OF)
    if register is None:
        messages = "\n".join(p.render(ROOT) for p in problems)
        raise SystemExit(f"Registre d'exemple invalide :\n{messages}")
    warnings = [p.message for p in problems if p.warning]
    report = build_report(register, warnings, AS_OF)
    stem = register_path.with_suffix("")
    return {
        stem.with_suffix(".md"): render_markdown(report),
        stem.with_suffix(".html"): render_html(report, register.method),
        stem.with_suffix(".json"): json.dumps(to_json(register, warnings, AS_OF), ensure_ascii=False, indent=2) + "\n",
    }


def main(argv: list[str] | None = None) -> int:
    setup_streams()  # accents corrects dans la console Windows
    parser = argparse.ArgumentParser(description="Génère ou vérifie les sorties des registres d'exemple.")
    parser.add_argument("--check", action="store_true", help="vérifie sans écrire (code 1 si une sortie est périmée)")
    args = parser.parse_args(argv)

    stale = []
    for register_path in sorted(EXAMPLES.rglob("*.toml")):
        for path, content in outputs(register_path).items():
            current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else None
            if current == content:
                continue
            if args.check:
                stale.append(path.relative_to(ROOT).as_posix())
            else:
                path.write_text(content, encoding="utf-8", newline="\n")
                print(f"écrit : {path.relative_to(ROOT).as_posix()}")
    if stale:
        print("Sorties d'exemple périmées (lancer « python scripts/build_examples.py ») :", file=sys.stderr)
        print("\n".join(f"  - {p}" for p in stale), file=sys.stderr)
        return 1
    if args.check:
        print("Sorties d'exemple à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
