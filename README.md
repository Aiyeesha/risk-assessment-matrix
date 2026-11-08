# Risk Assessment Matrix

🇫🇷 [Version française](README.fr.md)

A **methodical risk register** for small and mid-sized organisations: identify, analyse, evaluate,
treat, accept and review every risk, following a written and verifiable method. Aligned with
**ISO/IEC 27005:2022** and **EBIOS Risk Manager** (ANSSI, version 1.5 of March 2024).

> 🚧 **Work in progress** (v0.1.0). The method is in place; the register lands in step 3.

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
| 2 | Method: TOML format, 5×5 and EBIOS RM 4×4 presets | ✅ |
| 3 | Register: data model, consistency rules, `risk-check` | ⏳ |
| 4 | References (ISO/IEC 27001, ATT&CK, playbooks), safe CSV import and export | ⏳ |
| 5 | Markdown and HTML reports: `risk-report` | ⏳ |
| 6 | Assessment guide and example registers FR/EN → **v1.0.0** | ⏳ |
| 7 | Web interface on GitHub Pages → **v1.1.0** | ⏳ |
| 8 | Public repository and protections | ⏳ |

## The method

A method is a TOML file (`kind = "method"`) that describes, **in French and English**:

- the two **axes**: likelihood and impact ("severity" in EBIOS RM), 3 to 7 levels each,
  numbered from 1;
- the **risk levels**, from least to most severe, with their colour, review frequency and what the
  organisation does with them;
- the **grid** `[grid]`: the level of every cell, written explicitly. A "likelihood × impact"
  formula could not represent the EBIOS RM zones;
- the **risk appetite** and the **acceptance authorities**: who may accept a risk above the
  appetite, and for how many months at most.

`risk-check` rejects an inconsistent method and points to the faulty field by its path
(`grid.rows[4][2] : …`):

- unknown keys (a typo never goes unnoticed), text missing in one language;
- incomplete grid, unknown or unused level;
- **non-monotonic** grid: a risk can never become less severe when its likelihood or impact
  increases;
- a more severe risk reviewed less often, or accepted for longer, than a less severe one;
- an acceptance authority missing (or useless) given the appetite.

### Presets

**[`iso27005-5x5`](methods/iso27005-5x5.toml)** — compatible with the ISO/IEC 27005:2022 approach, which
lets every organisation define its scales. Appetite: *Low*.

| Likelihood ↓ / Impact → | Negligible | Minor | Moderate | Major | Critical |
|---|---|---|---|---|---|
| Almost certain | Moderate | High | High | Critical | Critical |
| Likely | Low | Moderate | High | High | Critical |
| Possible | Low | Moderate | Moderate | High | High |
| Unlikely | Low | Low | Moderate | Moderate | High |
| Rare | Low | Low | Low | Low | Moderate |

**[`ebios-rm-4x4`](methods/ebios-rm-4x4.toml)** — EBIOS Risk Manager scales (severity G1 to G4,
likelihood V1 to V4) and a three-zone acceptance grid. Appetite: *Acceptable as is*.

| Likelihood ↓ / Severity → | G1 — Minor | G2 — Significant | G3 — Severe | G4 — Critical |
|---|---|---|---|---|
| V4 — Almost certain | Tolerable under control | Unacceptable | Unacceptable | Unacceptable |
| V3 — Very likely | Tolerable under control | Tolerable under control | Unacceptable | Unacceptable |
| V2 — Likely | Acceptable as is | Tolerable under control | Tolerable under control | Unacceptable |
| V1 — Unlikely | Acceptable as is | Acceptable as is | Tolerable under control | Tolerable under control |

> ⚙️ **Adapt it.** Both presets are realistic starting points. Copy one, adjust descriptions, grid
> and authorities to your organisation, then have management approve the result: the method is part
> of the risk criteria required by ISO/IEC 27001 (6.1.2).

## Usage

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
risk-check              # checks methods/ and examples/
risk-check my-register.private.toml
pytest -v
```

Errors are printed as `file:line: message`, understood by editors and CI.
Exit code: `0` when everything is valid, `1` on problems, `2` on misuse.

> 🔒 **A real register is never published.** It describes the organisation's weaknesses. Name it
> `*.private.toml` or keep it in `private-registers/`: these files are excluded from Git.

## License

[MIT](LICENSE) — © 2026 Aïcha Imène Dahoumane.
