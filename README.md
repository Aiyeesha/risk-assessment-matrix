# Risk Assessment Matrix

🇫🇷 [Version française](README.fr.md)

A **methodical risk register** for small and mid-sized organisations: identify, analyse, evaluate,
treat, accept and review every risk, following a written and verifiable method. Aligned with
**ISO/IEC 27005:2022** and **EBIOS Risk Manager** (ANSSI, version 1.5 of March 2024).

> 🚧 **Work in progress** (v0.1.0 — scaffold). The method lands in step 2, the register in step 3.

## What the repository will contain

| Item | Content |
|---|---|
| **Configurable method** | Scales, thresholds and acceptance rules described in a validated TOML file. Two presets: **5×5** (likelihood × impact) and **EBIOS RM 4×4** (severity G1–G4 × likelihood V1–V4). |
| **Inherent and residual risk** | Score before and after the measures, both visible on the matrix. |
| **Treatment and acceptance** | Reduce, accept, transfer or avoid; formal acceptance (who, when, why, until when) when the residual risk stays above the risk appetite. |
| **Reviews and history** | Next review, overdue reviews and measures, change log. |
| **Links** | Assets, threats and vulnerabilities, ISO/IEC 27001:2022 Annex A controls, MITRE ATT&CK techniques, and the [incident response](https://github.com/Aiyeesha/incident-response-playbook) playbook to apply if the risk materialises. |
| **Tools** | `risk-check` (validation), `risk-report` (Markdown and HTML reports), `risk-export` (JSON, CSV protected against formula injection), web interface. |

## Roadmap

| Step | Content | Status |
|---|---|---|
| 1 | Repository, layout, TOML syntax check, CI | ✅ |
| 2 | Method: TOML format, 5×5 and EBIOS RM 4×4 presets | ⏳ |
| 3 | Register: data model, consistency rules, `risk-check` | ⏳ |
| 4 | References (ISO/IEC 27001, ATT&CK, playbooks), safe CSV import and export | ⏳ |
| 5 | Markdown and HTML reports: `risk-report` | ⏳ |
| 6 | Assessment guide and example registers FR/EN → **v1.0.0** | ⏳ |
| 7 | Web interface on GitHub Pages → **v1.1.0** | ⏳ |
| 8 | Public repository and protections | ⏳ |

## Usage (step 1)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
risk-check              # checks methods/ and examples/ (TOML syntax for now)
risk-check my-register.private.toml
pytest -v
```

Errors are printed as `file:line: message`, understood by editors and CI.
Exit code: `0` when everything is valid, `1` on problems, `2` on misuse.

> 🔒 **A real register is never published.** It describes the organisation's weaknesses. Name it
> `*.private.toml` or keep it in `private-registers/`: these files are excluded from Git.

## License

[MIT](LICENSE) — © 2026 Aïcha Imène Dahoumane.
