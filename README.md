# Risk Assessment Matrix

🇫🇷 [Version française](README.fr.md)

A **methodical risk register** for small and mid-sized organisations: identify, analyse, evaluate,
treat, accept and review every risk, following a written and verifiable method. Aligned with
**ISO/IEC 27005:2022** and **EBIOS Risk Manager** (ANSSI, version 1.5 of March 2024).

> 🚧 **Work in progress** (v0.1.0). Method, register, references and import/export are in place; reports land in step 5.

## What the repository will contain

| Item | Content |
|---|---|
| **Configurable method** | Scales, thresholds and acceptance rules described in a validated TOML file. Two presets: **5×5** (likelihood × impact) and **EBIOS RM 4×4** (severity G1–G4 × likelihood V1–V4). |
| **Inherent and residual risk** | Score before and after the measures, both visible on the matrix. |
| **Treatment and acceptance** | Reduce, accept, transfer or avoid; formal acceptance (who, when, why, until when) when the residual risk stays above the risk appetite. |
| **Reviews and history** | Next review, overdue reviews and measures, change log. |
| **Links** | Assets, threats and vulnerabilities, ISO/IEC 27001:2022 Annex A controls, MITRE ATT&CK techniques, and the [incident response](https://github.com/Aiyeesha/incident-response-playbook) playbook to apply if the risk materialises. |
| **Tools** | `risk-check` (validation), `risk-report` (Markdown and HTML reports), `risk-export` and `risk-import` (JSON, CSV protected against formula injection), web interface. |

## Roadmap

| Step | Content | Status |
|---|---|---|
| 1 | Repository, layout, TOML syntax check, CI | ✅ |
| 2 | Method: TOML format, 5×5 and EBIOS RM 4×4 presets | ✅ |
| 3 | Register: data model, consistency rules, `risk-check` | ✅ |
| 4 | References (ISO/IEC 27001, ATT&CK, playbooks), safe CSV import and export | ✅ |
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

## The register

A register (`kind = "register"`) names its method by identifier, then describes each risk.
Abridged example (a complete register is in [`tests/data/`](tests/data/registre-valide.toml)):

```toml
kind = "register"
format = 1
method = "iso27005-5x5"         # scales, grid and authorities come from the method
lang = "en"                     # language of the texts, hence of the expected acceptance roles
organisation = "Atelier Lumen"
assessed_on = 2026-09-01        # TOML dates, without quotes
assessor = "Security team"

[[risks]]
id = "R02"
title = "Phishing targeting accounting"
owner = "Chief financial officer"
assets = ["Email", "Bank transfers"]
threat = "Fraudster impersonating a supplier"
vulnerability = "Bank details changed without a call-back"
gdpr = false                    # personal data involved?
nis2 = false                    # incident reportable under NIS 2?
inherent = { likelihood = 4, impact = 3 }   # before the planned measures
residual = { likelihood = 2, impact = 3 }   # after
treatment = "reduce"            # reduce, accept, transfer or avoid
review = { last = 2026-09-15, next = 2027-03-15 }
acceptance = { by = "Claire Martin", role = "Risk owner", on = 2026-09-15, until = 2027-09-15, rationale = "…" }

[[risks.measures]]
title = "Mandatory call-back before any change of bank details"
owner = "Chief financial officer"
due = 2026-09-10
status = "done"                 # planned, in-progress or done
```

Optional fields: `description`, `category`, `existing_controls`, `status` (`active` by default,
`closed` for a risk that no longer exists), `transfer = { to = "…" }`, `residual.justification`, and
`[[risks.history]]` (`on`, `by`, `change`).

`risk-check` reports two kinds of messages (written in French).

**Errors** — the register is invalid or inconsistent (exit code `1`):
- unknown method, score outside the method's scales, unknown key, badly written date;
- residual risk higher than the inherent risk without a `justification`;
- `reduce` without a measure, `transfer` without a recipient;
- **missing formal acceptance** when the residual risk stays above the appetite and nothing is under
  way to reduce it any more (treatment `accept`, or all measures done) — this is the risk owners'
  acceptance of residual risks required by ISO/IEC 27001 (6.1.3 f);
- acceptance signed by another authority than the one set by the method, or longer than the
  maximum allowed duration;
- next review further away than the review frequency of the residual risk level;
- history out of chronological order, future dates.

**Warnings** — the file is valid, but a deadline has passed (exit code `0`, or `1` with `--strict`):
overdue measure, overdue review, expired acceptance. The reference date is today, or the one given
with `--today`.

```text
register.private.toml: attention : R01.review : revue en retard (prévue le 2027-01-01)
1 fichier(s) vérifié(s) — OK, 1 avertissement(s)
```

## References

Each risk — and each measure, for Annex A — can point to three frameworks:

```toml
iso27001 = ["8.7", "8.13"]    # ISO/IEC 27001:2022 Annex A controls
attack = ["T1486", "T1490"]   # MITRE ATT&CK techniques of the scenario
playbooks = ["P02"]           # playbook to apply if the risk materialises
```

| Framework | What `risk-check` checks |
|---|---|
| **ISO/IEC 27001:2022, Annex A** | The number exists: 5.1 to 5.37 (organisational), 6.1 to 6.8 (people), 7.1 to 7.14 (physical), 8.1 to 8.34 (technological). Only the numbers are in the repository: the text of the controls belongs to ISO. |
| **MITRE ATT&CK** | The format: technique `T1234` or sub-technique `T1234.001`. The export adds the link to the [attack.mitre.org](https://attack.mitre.org/) page. |
| **Playbooks** | The playbook is one of P01 to P07 of the [incident-response-playbook](https://github.com/Aiyeesha/incident-response-playbook) repository; the export gives its title and link in the register's language. |

A duplicate identifier within a list is reported.

> ⚠️ **Whether an ATT&CK technique exists is not checked.** The framework holds several hundred
> techniques and changes twice a year: embedding it would mean keeping it up to date. Only the
> format is checked; verify the identifier on attack.mitre.org.

## Import and export

```powershell
risk-export register.private.toml -o register.json                     # full JSON (default)
risk-export register.private.toml --format csv -o risks.csv --measures measures.csv
risk-import risks.csv --measures measures.csv -o register.private.toml `
    --lang en --method iso27005-5x5 --organisation "Atelier Lumen" --assessed-on 2026-09-01 --assessor "Security team"
```

- **`risk-export`** only exports a **valid** register (otherwise it prints its errors, exit code `1`).
  - **JSON** (`schema_version` 1): the full register, method included, with the level of each score,
    ATT&CK and playbook links, and the warnings at the reference date.
  - **CSV**: a risks file (one row per risk, with computed levels and the number of open measures)
    and, with `--measures`, a measures file. Separator `;` for a French register (French Excel), `,`
    for an English one; option `--delimiter`. UTF-8 with BOM, recognised by Excel. Lists are written
    `Email | Bank transfers`.
- **`risk-import`** creates a TOML register from the same columns: an export edited in a spreadsheet
  imports back as is. Badly written cells (date, integer, yes/no) are reported with their line and
  nothing is written; otherwise the register is written, then checked, and what remains to complete
  is listed (exit code `1`). History has no column: complete it in the TOML file.
- Neither command overwrites an existing file without `--force`.

> 🛡️ **Formula injection (CWE-1236).** A spreadsheet executes a cell starting with `=`, `+`, `-` or
> `@`. On export, such cells are prefixed with an apostrophe, which makes them display as text (OWASP
> recommendation); on import, that apostrophe is removed and the value stays plain text in the TOML
> file. Imported files are limited to 1 MiB and 5,000 rows, UTF-8 required (in Excel: *Save as →
> CSV UTF-8*).

## Usage

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
risk-check              # checks methods/ and examples/
risk-check my-register.private.toml
risk-check --strict --today 2027-01-15   # warnings fail too, at a given date
pytest -v
```

Errors are printed as `file:line: message`, understood by editors and CI.
Exit code: `0` when everything is valid, `1` on errors (or warnings with `--strict`), `2` on misuse.
Methods are read from `methods/` (use `--methods` for another folder).

> 🔒 **A real register is never published.** It describes the organisation's weaknesses. Name it
> `*.private.toml` or keep it in `private-registers/`: these files are excluded from Git.

## License

[MIT](LICENSE) — © 2026 Aïcha Imène Dahoumane.
