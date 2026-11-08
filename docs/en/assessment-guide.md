# Risk assessment guide

🇫🇷 [Version française](../fr/guide-evaluation.md)

This guide walks through a complete assessment, from the first meeting to the next review, with
the repository's tools. It is meant for the CISO of a small or mid-sized organisation, the CIO who
plays that role, or anyone who must produce a risk register that stands up in front of management
or an auditor.

Running example: **Atelier Lumen**, a fictional company whose full registers are in
[`examples/en/`](../../examples/en/) — 5×5 method and EBIOS Risk Manager variant.

## Contents

1. [The process at a glance](#1-the-process-at-a-glance)
2. [Prepare: scope, participants, method](#2-prepare-scope-participants-method)
3. [Identify risks](#3-identify-risks)
4. [Analyse: score the inherent risk](#4-analyse-score-the-inherent-risk)
5. [Evaluate: compare with the appetite](#5-evaluate-compare-with-the-appetite)
6. [Treat: choose and plan](#6-treat-choose-and-plan)
7. [Formally accept the residual risk](#7-formally-accept-the-residual-risk)
8. [Monitor and review](#8-monitor-and-review)
9. [Report](#9-report)
10. [Common mistakes](#10-common-mistakes)
11. [Mapping to the frameworks](#11-mapping-to-the-frameworks)

## 1. The process at a glance

| Step | Question | What you produce | Tool |
|---|---|---|---|
| Prepare | What, with whom, under which rules? | Scope, approved method | `methods/*.toml`, `risk-check` |
| Identify | What can go wrong? | List of described risks | TOML register or spreadsheet + `risk-import` |
| Analyse | How likely, and how severe? | Inherent risk | `inherent` |
| Evaluate | Is it acceptable as is? | Priorities | The method's grid and appetite |
| Treat | What do we do, who, by when? | Action plan, residual risk | `measures`, `residual`, `treatment` |
| Accept | Who owns what remains? | Signed acceptances | `acceptance` |
| Monitor | Is it still true? | Reviews, history, alerts | `review`, `history`, `risk-check --strict` |
| Report | What does management need to know? | Report | `risk-report` |

This cycle repeats: **at least once a year**, and at every significant change (new activity,
migration, incident, exercise revealing a weakness). ISO/IEC 27001:2022 requires the risk
assessment to be performed at planned intervals and when significant changes occur (8.2).

## 2. Prepare: scope, participants, method

### 2.1 Set the scope

Write in one sentence what is covered and what is not. For Atelier Lumen: *"the whole information
system of the head office, the warehouse and the online shop; manufacturing, which is outsourced,
is out of scope, but the dependence on suppliers is in."*

### 2.2 Bring the right people together

A register written by IT alone underestimates business risks, and vice versa.

| Role | Contribution |
|---|---|
| CISO or CIO | Threats, vulnerabilities, technical measures; runs the process |
| Management (or its representative) | Appetite, trade-offs, acceptances |
| Business owners (finance, sales, logistics, HR) | What really matters, what an outage would cost |
| DPO | Personal data, GDPR obligations |
| Key providers (managed services, hosting) | What they cover, and above all what they do not |

### 2.3 Choose the method

The repository provides two presets ([`methods/`](../../methods/)):

| | `iso27005-5x5` | `ebios-rm-4x4` |
|---|---|---|
| Scales | Likelihood 1–5 × impact 1–5 | Likelihood V1–V4 × severity G1–G4 |
| Levels | Low, moderate, high, critical | Acceptable, tolerable, unacceptable |
| Suits | A first assessment; a "classic" register expected by an ISO/IEC 27001 auditor | An organisation following EBIOS RM (security accreditation, public sector, regulated entities and their providers) |
| Granularity | Finer (25 cells) | Sharper (16 cells, three decision zones) |

> 💡 **An even scale has no middle.** With four levels, you cannot score everything "3 out of 5"
> to play safe: you have to decide. That is one of the strengths of the EBIOS RM scales.

### 2.4 Adapt, then approve the method

The presets are starting points. Copy one, then read each description again with management:
*"For us, what is a major impact?"* Amounts, outage durations and frequencies must make sense for
**your** organisation.

```powershell
Copy-Item methods\iso27005-5x5.toml methods\lumen-5x5.toml
# Change id = "lumen-5x5", the descriptions, the grid, the appetite and the authorities, then:
risk-check methods
```

`risk-check` rejects an inconsistent method: non-monotonic grid (a cell less severe than its more
likely neighbour), unused level, missing authority above the appetite, less frequent review for a
more severe risk… The approved method is part of the **risk criteria** required by ISO/IEC 27001
(6.1.2): keep a record of its approval (date, by whom).

## 3. Identify risks

### 3.1 Where to look

- **Activities and what they depend on**: for each essential activity (selling online, shipping,
  paying suppliers), which information, which systems, which providers?
- **Past incidents**, yours and your sector's.
- **Exercises**: Atelier Lumen's [tabletop exercise](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/docs/D06-tabletop-exercise.md)
  revealed two weaknesses — VPN without MFA, backup NAS reachable — on which risk R01 is built.
- **Audits, penetration tests, vulnerability scans**.
- **ISO/IEC 27001:2022 Annex A**, read the other way round: for each theme, *"what would happen if
  we had nothing?"*

ISO/IEC 27005:2022 describes two complementary ways of identifying risks: **event-based**
(scenarios: *"ransomware halts shipping"*) and **asset-based** (*"the file server: which threats,
which vulnerabilities?"*). EBIOS RM starts from **risk origins** and their **target objectives**
(workshop 2), then builds strategic scenarios (workshop 3) and operational scenarios (workshop 4).

### 3.2 Describe a risk well

A well-written risk fits in one **cause → event → consequence** sentence:

> *An attacker gets in through the VPN with a stolen password* (cause), *encrypts the file server
> and the backups* (event); *shipping stops for several days* (consequence).

In the register:

| Field | Content | Example (R01) |
|---|---|---|
| `title` | The feared event, short | Ransomware encrypting the file server and the backups |
| `description` | The cause → event → consequence sentence | … |
| `assets` | What is affected | File server, backup NAS, Active Directory |
| `threat` | Who or what | Criminal group, with double extortion |
| `vulnerability` | What makes it possible | VPN without MFA; NAS reachable from the office network |
| `owner` | **One** person accountable for the risk | Julien Morel, CIO |
| `gdpr`, `nis2` | Personal data at stake? Incident reportable under NIS 2? | `true`, `false` |

> ⚠️ **"Cyber risk" is not a risk.** Too vague to be scored or treated. Conversely, a list of 200
> technical vulnerabilities is not a risk register: group them by scenario. A useful register often
> holds between 10 and 40 risks.

### 3.3 Start from a spreadsheet

If the workshop runs in Excel, start from the CSV export of an example register, fill it in, then
convert it:

```powershell
risk-export examples\en\atelier-lumen.toml --format csv -o risks.csv --measures measures.csv
# … work in Excel, save as "CSV UTF-8" …
risk-import risks.csv --measures measures.csv -o private-registers\lumen.private.toml `
    --lang en --method lumen-5x5 --organisation "Atelier Lumen" --assessed-on 2026-09-15 --assessor "Risk committee"
```

`risk-import` lists what is still missing; complete the TOML file until `risk-check` reports no
more errors.

## 4. Analyse: score the inherent risk

### 4.1 What "inherent" means here

In this repository, the **inherent risk** is the risk **as it stands today**, with the controls
already in place (`existing_controls`), **before** the measures you plan to add. The **residual
risk** is what will remain **once the planned measures are done**.

> ⚠️ **Definitions vary.** Some methods call "inherent" the risk with *no* control at all, not even
> existing ones. That choice is rarely useful (nobody pictures a company without antivirus) and
> produces artificially high scores. Whatever convention you pick, write it into the method and
> stick to it.

### 4.2 Score

For each risk, choose a **likelihood** level and an **impact** level by reading the method's
descriptions — not by gut feeling. Score as a group, each person alone first, then compare: the
gaps reveal information not everyone has.

| Good practice | Why |
|---|---|
| Score the impact of the **most severe realistic scenario**, not the worst imaginable | Otherwise everything becomes "critical" and nothing is a priority any more |
| Back the likelihood with facts (incidents, exposure, attractiveness) | A score must be defensible in front of an auditor |
| Score the impact on **every** dimension: operations, finances, legal, reputation, people | A data breach "with no outage" can cost a lot |
| Beware of the middle of the scale | A default "3 out of 5" decides nothing |

The risk level is **not computed** by the register: it is **read from the method's grid**. A
method can thus decide that a critical impact stays critical even when it is rare.

## 5. Evaluate: compare with the appetite

The **appetite** is the highest level the organisation accepts without a specific decision ("Low"
in the 5×5 method, "Acceptable" in EBIOS RM). Every risk above it calls for treatment, or for a
formal acceptance by the designated authority.

The report sorts risks from the most to the least severe and shows both **heat maps**: the inherent
risk shows where you start, the residual risk where the planned measures will take you.

## 6. Treat: choose and plan

### 6.1 The four options

| `treatment` | Meaning | Requires | Atelier Lumen |
|---|---|---|---|
| `reduce` | Lower the likelihood or the impact with measures | At least one measure | R01 (MFA, immutable backups, EDR, segmentation) |
| `transfer` | Have a third party bear all or part of the consequences | `transfer.to`: to whom | R05 (hosting commitment, cyber insurance) |
| `avoid` | Remove the activity or asset causing the risk | — | R08 (warehouse servers removed: risk closed) |
| `accept` | Keep the risk as is, knowingly | Formal acceptance if above the appetite | R04 of the EBIOS RM variant |

> 💡 **Transferring does not erase the risk.** Insurance pays out; it restores neither the data nor
> the customers' trust. The residual risk of a transfer often stays above the appetite: it must then
> be formally accepted (R05).

### 6.2 Plan the measures

Each measure has an **actionable title**, **one owner**, a **due date** and a **status**
(`planned`, `in-progress`, `done`). Link it to the ISO/IEC 27001:2022 Annex A controls it implements
(`iso27001 = ["8.5"]`): the [Statement of Applicability](#11-mapping-to-the-frameworks) will be
easier to maintain.

### 6.3 Score the residual risk

Score the risk again **as if every planned measure were done**. The residual risk cannot exceed the
inherent risk without a `justification` (for example, exposure rising during a project):
`risk-check` rejects it.

### 6.4 Link to the response plan

Record the scenario's MITRE ATT&CK techniques (`attack`) and the **playbook** to apply if it
materialises (`playbooks`, P01 to P07 of the incident response repository). Risk R01 thus points to
playbook P02, the one the tabletop exercise put to the test.

## 7. Formally accept the residual risk

A residual risk above the appetite must be **formally accepted** as soon as nothing is under way to
reduce it any more (treatment `accept`, or every measure done). This is the risk owners' approval of
residual risks required by ISO/IEC 27001 (6.1.3).

```toml
acceptance = { by = "Nadia Ferrand", role = "Risk owner", on = 2026-10-01, until = 2027-10-01, rationale = "…" }
```

- `role` must be **exactly** the authority set by the method for that level, in the register's
  language — a high risk is not accepted at the level of a moderate one.
- `until` cannot exceed the method's maximum duration (12 months for a moderate risk, 3 for a
  critical one in the 5×5 method; 6 months for an unacceptable risk in EBIOS RM).
- `rationale` says **why**: disproportionate cost, measure impossible before a given date, risk
  covered otherwise. *"Accepted"* alone protects nobody.

> ⚠️ **An acceptance expires.** After `until`, `risk-check` warns: renew the acceptance (new
> decision, new date) or resume treatment.

## 8. Monitor and review

### 8.1 The next review date

Each risk has a review (`review.last`, `review.next`). The maximum interval depends on the residual
level (in the 5×5 method: 12 months for a low risk, 1 month for a critical one). Reviewing a risk
means checking that its description, scores and measures are still true.

Review **outside the cycle** after an incident, a significant change (migration, new provider), or
an exercise or audit that reveals something.

### 8.2 The history

Record every decision in `[[risks.history]]`: creation, re-scoring, measure completed, acceptance,
closure. The history is the register's memory — what an auditor, or your successor, will ask for.

### 8.3 Let the tool keep watch

```powershell
risk-check                    # errors: blocking; passed deadlines: warnings
risk-check --strict           # warnings become blocking too (exit code 1)
```

In continuous integration or a scheduled task, `--strict` turns any overdue measure, passed review
or expired acceptance into a visible alert.

> 🔒 **A real register is never published.** It describes the organisation's weaknesses precisely.
> Keep it in `private-registers/` or name it `*.private.toml` (excluded from Git), and restrict
> access to it like sensitive internal information.

## 9. Report

```powershell
risk-report private-registers\lumen.private.toml --format html -o reports\risks.html
```

The self-contained, printable HTML report supports the management committee: summary, heat maps,
risks above the appetite and their status, action plan, upcoming reviews. The ISO/IEC 27001
management review (9.3) expects, among other things, the results of the risk assessment and the
status of the risk treatment plan.

Generated report examples: [5×5](../../examples/en/atelier-lumen.md) ·
[EBIOS RM](../../examples/en/atelier-lumen-ebios.md) (HTML and JSON versions in the same folder).

## 10. Common mistakes

| Mistake | Consequence | Remedy |
|---|---|---|
| Scoring everything "critical" | No priority left | Score the realistic scenario, not the worst imaginable |
| A committee as risk owner | Nobody acts | One named person per risk |
| Measures without a due date | The plan does not move | A due date and an owner for each |
| Residual risk scored as if measures were done… when they are not | False sense of security | Residual risk is a **target**; the report shows open measures |
| An acceptance with no reason and no end | The risk is forgotten | `rationale` and `until`, then renewal |
| A register reviewed once a year only | It no longer describes reality | Reviews by level, and outside the cycle after every change |

## 11. Mapping to the frameworks

| This repository | ISO/IEC 27001:2022 | ISO/IEC 27005:2022 | EBIOS Risk Manager |
|---|---|---|---|
| Method (`methods/`) | Risk criteria (6.1.2) | Context establishment, criteria | Workshop 1: scope and security baseline |
| `threat`, `assets`, `description` | Identification (6.1.2) | Identification, event-based or asset-based | Workshops 2 to 4: risk origins, strategic and operational scenarios |
| `inherent` | Analysis (6.1.2) | Analysis: likelihood and consequences | Severity and likelihood assessment |
| Grid, appetite | Evaluation (6.1.2) | Evaluation against the criteria | Risk map and acceptance grid |
| `treatment`, `measures`, `residual` | Treatment (6.1.3), implementation (8.3) | Treatment: options, controls, plan | Workshop 5: treatment strategy, measures |
| `iso27001` | Annex A, Statement of Applicability (6.1.3 d) | — | Security baseline |
| `acceptance` | Approval of residual risks (6.1.3) | Risk acceptance | Security accreditation (accepted residual risks) |
| `review`, `history` | Assessment at planned intervals (8.2), management review (9.3) | Monitoring and review | Strategic and operational cycles |

> ℹ️ **References.** ISO/IEC 27001:2022 and ISO/IEC 27005:2022 are paid standards: this guide cites
> their requirements without reproducing them. EBIOS Risk Manager is published free of charge by
> ANSSI (version 1.5, 2024) on [cyber.gouv.fr](https://cyber.gouv.fr/).
