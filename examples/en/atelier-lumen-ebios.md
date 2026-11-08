# Risk report — Atelier Lumen (fictional company)

- Method: EBIOS Risk Manager — likelihood V1–V4 × severity G1–G4
- Assessment: 2026-09-15, by Risk committee (CISO, CIO, CFO, DPO)
- Status as of: 2026-11-08

## Summary

- 4 active risk(s), 0 closed
- 4 above the appetite (“Acceptable as is”)
- 2 open measure(s), 0 overdue
- 0 warning(s) to address

| Residual level | Risks |
|---|---|
| Unacceptable | 1 |
| Tolerable under control | 3 |
| Acceptable as is | 0 |

## Heat map — inherent risk

| Likelihood ↓ / Severity → | G1 — Minor | G2 — Significant | G3 — Severe | G4 — Critical |
|---|---|---|---|---|
| V4 — Almost certain | Tolerable under control | Unacceptable | Unacceptable | Unacceptable |
| V3 — Very likely | Tolerable under control | Tolerable under control | Unacceptable · **R02** | Unacceptable · **R01** |
| V2 — Likely | Acceptable as is | Tolerable under control | Tolerable under control | Unacceptable · **R04, R03** |
| V1 — Unlikely | Acceptable as is | Acceptable as is | Tolerable under control | Tolerable under control |

## Heat map — residual risk

| Likelihood ↓ / Severity → | G1 — Minor | G2 — Significant | G3 — Severe | G4 — Critical |
|---|---|---|---|---|
| V4 — Almost certain | Tolerable under control | Unacceptable | Unacceptable | Unacceptable |
| V3 — Very likely | Tolerable under control | Tolerable under control | Unacceptable | Unacceptable |
| V2 — Likely | Acceptable as is | Tolerable under control | Tolerable under control · **R01** | Unacceptable · **R04** |
| V1 — Unlikely | Acceptable as is | Acceptable as is | Tolerable under control · **R02** | Tolerable under control · **R03** |

Each cell shows its level and the active risks it holds.

## Risks by residual level

| ID | Risk | Owner | Inherent | Residual | Treatment | Next review |
|---|---|---|---|---|---|---|
| R04 | Dependence on a single payment provider | Camille Roy, e-commerce manager | Unacceptable | Unacceptable | Accept | 2027-01-01 |
| R01 | Business halted by ransomware | Julien Morel, CIO | Unacceptable | Tolerable under control | Reduce | 2027-04-15 |
| R02 | Diversion of supplier payments | Nadia Ferrand, CFO | Unacceptable | Tolerable under control | Reduce | 2027-04-01 |
| R03 | Theft of the online shop's customer data | Camille Roy, e-commerce manager | Unacceptable | Tolerable under control | Reduce | 2027-03-15 |

## Above the appetite

| ID | Risk | Residual | Status |
|---|---|---|---|
| R04 | Dependence on a single payment provider | Unacceptable | Accepted by Hélène Bastide (Executive management (security accreditation)) until 2027-04-01 |
| R01 | Business halted by ransomware | Tolerable under control | Reduction under way (1 open measure(s)) |
| R02 | Diversion of supplier payments | Tolerable under control | Accepted by Nadia Ferrand (Risk owner, after the CISO's opinion) until 2027-10-01 |
| R03 | Theft of the online shop's customer data | Tolerable under control | Reduction under way (1 open measure(s)) |

## Action plan

| Due | ID | Measure | Owner | Status |
|---|---|---|---|---|
| 2026-12-31 | R03 | Penetration test of the shop and fixing of the flaws found | Camille Roy | In progress |
| 2027-01-31 | R01 | Immutable backups and isolation of the NAS | Julien Morel, CIO | In progress |

## Review schedule

| Date | ID | Risk | Residual |
|---|---|---|---|
| 2027-01-01 | R04 | Dependence on a single payment provider | Unacceptable |
| 2027-03-15 | R03 | Theft of the online shop's customer data | Tolerable under control |
| 2027-04-01 | R02 | Diversion of supplier payments | Tolerable under control |
| 2027-04-15 | R01 | Business halted by ransomware | Tolerable under control |

## References

### ISO/IEC 27001:2022, Annex A

| Theme | Controls cited |
|---|---|
| 5 — Organisational controls | 5.14, 5.17, 5.19, 5.21, 5.30 |
| 6 — People controls | 6.3 |
| 7 — Physical controls | · |
| 8 — Technological controls | 8.5, 8.7, 8.8, 8.13, 8.22, 8.26, 8.29 |

### Incident response playbooks

| Playbook | Risks |
|---|---|
| [P02 — Ransomware attack](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P02-ransomware.md) | R01 |
| [P03 — Data breach](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P03-data-breach.md) | R03 |
| [P06 — Denial of service](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P06-denial-of-service.md) | R04 |
| [P07 — Compromised account and payment fraud](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P07-compromised-account.md) | R02 |

### MITRE ATT&CK techniques

| Technique | Risks |
|---|---|
| [T1133](https://attack.mitre.org/techniques/T1133/) | R01 |
| [T1190](https://attack.mitre.org/techniques/T1190/) | R03 |
| [T1486](https://attack.mitre.org/techniques/T1486/) | R01 |
| [T1490](https://attack.mitre.org/techniques/T1490/) | R01 |
| [T1566](https://attack.mitre.org/techniques/T1566/) | R02 |
| [T1656](https://attack.mitre.org/techniques/T1656/) | R02 |

---

*Generated by risk-assessment-matrix 1.0.0 on 2026-11-08.*
