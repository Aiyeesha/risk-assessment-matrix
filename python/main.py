from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from python.risk_matrix import RiskRegister, get_level, get_color
from python.report import generate_html_report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Risk Assessment Matrix — CLI")
    sub = p.add_subparsers(dest="command")

    # report command
    report = sub.add_parser("report", help="Generate HTML report from JSON risk register")
    report.add_argument("--input", required=True, help="Path to risk register JSON")
    report.add_argument("--output", default="report.html", help="Output HTML path")

    # eval command
    ev = sub.add_parser("eval", help="Evaluate a single risk score")
    ev.add_argument("--risk", required=True, help="Risk title")
    ev.add_argument("--likelihood", type=int, required=True, choices=range(1, 6))
    ev.add_argument("--impact", type=int, required=True, choices=range(1, 6))

    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.command == "report":
        data = json.loads(Path(args.input).read_text())
        register = RiskRegister.from_dict(data)
        generate_html_report(register, args.output)

    elif args.command == "eval":
        score = args.likelihood * args.impact
        level = get_level(score)
        color = get_color(level)
        print(f"\nRisk: {args.risk}")
        print(f"  Likelihood : {args.likelihood}/5")
        print(f"  Impact     : {args.impact}/5")
        print(f"  Score      : {score}/25")
        print(f"  Level      : {level.upper()}")
        print()

    else:
        print("Usage: python -m python.main report --input data/sample_risks.json")
        print("       python -m python.main eval --risk 'SQL injection' --likelihood 4 --impact 5")
        sys.exit(1)


if __name__ == "__main__":
    main()
