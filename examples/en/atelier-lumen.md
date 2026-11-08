# Risk report — Atelier Lumen (fictional company)

- Method: 5×5 matrix — likelihood × impact
- Assessment: 2026-09-15, by Risk committee (CISO, CIO, CFO, DPO)
- Status as of: 2026-11-08

## Summary

- 7 active risk(s), 1 closed
- 5 above the appetite (“Low”)
- 4 open measure(s), 1 overdue
- 1 warning(s) to address

| Residual level | Risks |
|---|---|
| Critical | 0 |
| High | 1 |
| Moderate | 4 |
| Low | 2 |

## Heat map — inherent risk

| Likelihood ↓ / Impact → | Negligible | Minor | Moderate | Major | Critical |
|---|---|---|---|---|---|
| Almost certain | Moderate | High | High | Critical | Critical |
| Likely | Low | Moderate | High · **R04** | High · **R02** | Critical · **R01** |
| Possible | Low | Moderate | Moderate · **R05, R06** | High · **R03** | High |
| Unlikely | Low | Low | Moderate | Moderate · **R07** | High |
| Rare | Low | Low | Low | Low | Moderate |

## Heat map — residual risk

| Likelihood ↓ / Impact → | Negligible | Minor | Moderate | Major | Critical |
|---|---|---|---|---|---|
| Almost certain | Moderate | High | High | Critical | Critical |
| Likely | Low | Moderate | High | High | Critical |
| Possible | Low · **R06** | Moderate · **R05** | Moderate | High · **R01** | High |
| Unlikely | Low | Low | Moderate · **R04** | Moderate · **R02, R03** | High |
| Rare | Low | Low | Low | Low · **R07** | Moderate |

Each cell shows its level and the active risks it holds.

## Risks by residual level

| ID | Risk | Owner | Inherent | Residual | Treatment | Next review |
|---|---|---|---|---|---|---|
| R01 | Ransomware encrypting the file server and the backups | Julien Morel, CIO | Critical | High | Reduce | 2027-01-15 |
| R02 | Payment fraud through supplier impersonation | Nadia Ferrand, CFO | High | Moderate | Reduce | 2027-03-15 |
| R03 | Breach of the online shop's customer data | Camille Roy, e-commerce manager | High | Moderate | Reduce | 2027-03-15 |
| R04 | Microsoft 365 accounts compromised through phishing | Julien Morel, CIO | High | Moderate | Reduce | 2027-04-01 |
| R05 | Prolonged outage of the online shop | Camille Roy, e-commerce manager | Moderate | Moderate | Transfer | 2027-03-15 |
| R06 | Theft or loss of a laptop | Julien Morel, CIO | Moderate | Low | Reduce | 2027-09-15 |
| R07 | Access kept after an employee leaves or a service contract ends | Human resources manager | Moderate | Low | Reduce | 2027-09-15 |

## Above the appetite

| ID | Risk | Residual | Status |
|---|---|---|---|
| R01 | Ransomware encrypting the file server and the backups | High | Reduction under way (2 open measure(s)) |
| R02 | Payment fraud through supplier impersonation | Moderate | Accepted by Nadia Ferrand (Risk owner) until 2027-10-01 |
| R03 | Breach of the online shop's customer data | Moderate | Reduction under way (1 open measure(s)) |
| R04 | Microsoft 365 accounts compromised through phishing | Moderate | Accepted by Julien Morel (Risk owner) until 2027-10-01 |
| R05 | Prolonged outage of the online shop | Moderate | Accepted by Camille Roy (Risk owner) until 2027-09-15 |

## Action plan

| Due | ID | Measure | Owner | Status |
|---|---|---|---|---|
| **2026-10-31** | R03 | Penetration test of the shop and fixing of the flaws found | Camille Roy | **Overdue** |
| 2026-12-15 | R01 | EDR on all workstations and servers, monitored 24/7 | Managed service provider | In progress |
| 2027-01-31 | R01 | Move the backup NAS to a dedicated network | Julien Morel, CIO | Planned |
| 2027-03-31 | R07 | Leaver procedure shared by HR and IT, and quarterly account review | Human resources manager | Planned |

## Review schedule

| Date | ID | Risk | Residual |
|---|---|---|---|
| 2027-01-15 | R01 | Ransomware encrypting the file server and the backups | High |
| 2027-03-15 | R02 | Payment fraud through supplier impersonation | Moderate |
| 2027-03-15 | R03 | Breach of the online shop's customer data | Moderate |
| 2027-03-15 | R05 | Prolonged outage of the online shop | Moderate |
| 2027-04-01 | R04 | Microsoft 365 accounts compromised through phishing | Moderate |
| 2027-09-15 | R06 | Theft or loss of a laptop | Low |
| 2027-09-15 | R07 | Access kept after an employee leaves or a service contract ends | Low |

## References

### ISO/IEC 27001:2022, Annex A

| Theme | Controls cited |
|---|---|
| 5 — Organisational controls | 5.14, 5.15, 5.17, 5.18, 5.20, 5.23, 5.30 |
| 6 — People controls | 6.3, 6.5 |
| 7 — Physical controls | 7.9 |
| 8 — Technological controls | 8.1, 8.2, 8.5, 8.7, 8.8, 8.13, 8.16, 8.20, 8.22, 8.24, 8.26, 8.28, 8.29 |

### Incident response playbooks

| Playbook | Risks |
|---|---|
| [P01 — Malware infection](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P01-malware.md) | R01 |
| [P02 — Ransomware attack](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P02-ransomware.md) | R01 |
| [P03 — Data breach](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P03-data-breach.md) | R03 |
| [P04 — Phishing](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P04-phishing.md) | R02, R04 |
| [P05 — Unauthorised access](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P05-unauthorised-access.md) | R07 |
| [P06 — Denial of service](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P06-denial-of-service.md) | R05 |
| [P07 — Compromised account and payment fraud](https://github.com/Aiyeesha/incident-response-playbook/blob/main/en/playbooks/P07-compromised-account.md) | R02, R04 |

### MITRE ATT&CK techniques

| Technique | Risks |
|---|---|
| [T1078](https://attack.mitre.org/techniques/T1078/) | R01, R07 |
| [T1078.004](https://attack.mitre.org/techniques/T1078/004/) | R04 |
| [T1133](https://attack.mitre.org/techniques/T1133/) | R01 |
| [T1190](https://attack.mitre.org/techniques/T1190/) | R03 |
| [T1486](https://attack.mitre.org/techniques/T1486/) | R01 |
| [T1490](https://attack.mitre.org/techniques/T1490/) | R01 |
| [T1498](https://attack.mitre.org/techniques/T1498/) | R05 |
| [T1566](https://attack.mitre.org/techniques/T1566/) | R02 |
| [T1566.002](https://attack.mitre.org/techniques/T1566/002/) | R04 |
| [T1656](https://attack.mitre.org/techniques/T1656/) | R02 |

## Closed risks

| ID | Risk |
|---|---|
| R08 | Disaster in the warehouse server room |

## Warnings

- R03.measures\[1\] : mesure en retard (échéance 2026-10-31) — « Penetration test of the shop and fixing of the flaws found »

---

*Generated by risk-assessment-matrix 1.0.0 on 2026-11-08.*
