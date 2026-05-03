# Risk Assessment Matrix

Interactive risk assessment tool combining a **browser-based matrix** (HTML/JS) and a **Python CLI** for batch processing and report generation.

## Features

- Likelihood × Impact matrix (5×5) with automatic risk scoring
- Risk register with categories, owners, mitigations, and due dates
- Color-coded heat map (Critical / High / Medium / Low)
- Export to JSON and CSV
- Python CLI for bulk risk imports and HTML report generation

## Quick Start

### Browser App (no install required)

```bash
# Just open in any browser
open index.html
```

### Python CLI

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r python/requirements.txt

# Generate HTML report from JSON risk register
python python/main.py --input data/sample_risks.json --output report.html

# Evaluate a single risk
python python/main.py --risk "SQL injection on login form" --likelihood 4 --impact 5
```

## Risk Scoring

```
Risk Score = Likelihood (1–5) × Impact (1–5)
```

| Score | Level | Action |
|-------|-------|--------|
| 20–25 | Critical | Immediate remediation required |
| 12–19 | High | Remediate within 30 days |
| 6–11 | Medium | Remediate within 90 days |
| 1–5 | Low | Accept or monitor |

## Project Structure

```
.
├── index.html              # Standalone browser app
├── src/
│   ├── risk_matrix.js      # Matrix logic + scoring
│   └── export.js           # JSON / CSV export
├── styles/
│   └── main.css
├── data/
│   ├── risk_categories.json
│   └── sample_risks.json
└── python/
    ├── main.py
    ├── risk_matrix.py
    ├── report.py
    └── requirements.txt
```

## License

MIT
