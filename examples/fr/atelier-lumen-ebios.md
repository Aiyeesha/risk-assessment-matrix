# Rapport de risques — Atelier Lumen (entreprise fictive)

- Méthode : EBIOS Risk Manager — vraisemblance V1–V4 × gravité G1–G4
- Évaluation : 15/09/2026, par Comité des risques (RSSI, DSI, DAF, DPO)
- Situation au : 08/11/2026

## Synthèse

- 4 risque(s) actif(s), 0 clos
- 4 au-dessus de l'appétence (« Acceptable en l'état »)
- 2 mesure(s) ouverte(s), dont 0 en retard
- 0 avertissement(s) à traiter

| Niveau résiduel | Risques |
|---|---|
| Inacceptable | 1 |
| Tolérable sous contrôle | 3 |
| Acceptable en l'état | 0 |

## Cartographie — risque inhérent

| Vraisemblance ↓ / Gravité → | G1 — Mineure | G2 — Significative | G3 — Grave | G4 — Critique |
|---|---|---|---|---|
| V4 — Quasi certain | Tolérable sous contrôle | Inacceptable | Inacceptable | Inacceptable |
| V3 — Très vraisemblable | Tolérable sous contrôle | Tolérable sous contrôle | Inacceptable · **R02** | Inacceptable · **R01** |
| V2 — Vraisemblable | Acceptable en l'état | Tolérable sous contrôle | Tolérable sous contrôle | Inacceptable · **R04, R03** |
| V1 — Peu vraisemblable | Acceptable en l'état | Acceptable en l'état | Tolérable sous contrôle | Tolérable sous contrôle |

## Cartographie — risque résiduel

| Vraisemblance ↓ / Gravité → | G1 — Mineure | G2 — Significative | G3 — Grave | G4 — Critique |
|---|---|---|---|---|
| V4 — Quasi certain | Tolérable sous contrôle | Inacceptable | Inacceptable | Inacceptable |
| V3 — Très vraisemblable | Tolérable sous contrôle | Tolérable sous contrôle | Inacceptable | Inacceptable |
| V2 — Vraisemblable | Acceptable en l'état | Tolérable sous contrôle | Tolérable sous contrôle · **R01** | Inacceptable · **R04** |
| V1 — Peu vraisemblable | Acceptable en l'état | Acceptable en l'état | Tolérable sous contrôle · **R02** | Tolérable sous contrôle · **R03** |

Chaque case indique son niveau et les risques actifs qui s'y trouvent.

## Risques par niveau résiduel

| ID | Risque | Responsable | Inhérent | Résiduel | Traitement | Prochaine revue |
|---|---|---|---|---|---|---|
| R04 | Dépendance à un prestataire de paiement unique | Camille Roy, responsable du commerce en ligne | Inacceptable | Inacceptable | Accepter | 01/01/2027 |
| R01 | Arrêt de l'activité par un rançongiciel | Julien Morel, DSI | Inacceptable | Tolérable sous contrôle | Réduire | 15/04/2027 |
| R02 | Détournement de paiements fournisseurs | Nadia Ferrand, DAF | Inacceptable | Tolérable sous contrôle | Réduire | 01/04/2027 |
| R03 | Vol des données clients de la boutique en ligne | Camille Roy, responsable du commerce en ligne | Inacceptable | Tolérable sous contrôle | Réduire | 15/03/2027 |

## Au-dessus de l'appétence

| ID | Risque | Résiduel | Situation |
|---|---|---|---|
| R04 | Dépendance à un prestataire de paiement unique | Inacceptable | Accepté par Hélène Bastide (Direction générale (homologation)) jusqu'au 01/04/2027 |
| R01 | Arrêt de l'activité par un rançongiciel | Tolérable sous contrôle | Réduction en cours (1 mesure(s) ouverte(s)) |
| R02 | Détournement de paiements fournisseurs | Tolérable sous contrôle | Accepté par Nadia Ferrand (Responsable du risque, après avis du RSSI) jusqu'au 01/10/2027 |
| R03 | Vol des données clients de la boutique en ligne | Tolérable sous contrôle | Réduction en cours (1 mesure(s) ouverte(s)) |

## Plan d'action

| Échéance | ID | Mesure | Responsable | État |
|---|---|---|---|---|
| 31/12/2026 | R03 | Test d'intrusion de la boutique et correction des failles trouvées | Camille Roy | En cours |
| 31/01/2027 | R01 | Sauvegardes immuables et isolement du NAS | Julien Morel, DSI | En cours |

## Calendrier des revues

| Date | ID | Risque | Résiduel |
|---|---|---|---|
| 01/01/2027 | R04 | Dépendance à un prestataire de paiement unique | Inacceptable |
| 15/03/2027 | R03 | Vol des données clients de la boutique en ligne | Tolérable sous contrôle |
| 01/04/2027 | R02 | Détournement de paiements fournisseurs | Tolérable sous contrôle |
| 15/04/2027 | R01 | Arrêt de l'activité par un rançongiciel | Tolérable sous contrôle |

## Références

### ISO/IEC 27001:2022, annexe A

| Thème | Mesures citées |
|---|---|
| 5 — Mesures organisationnelles | 5.14, 5.17, 5.19, 5.21, 5.30 |
| 6 — Mesures liées aux personnes | 6.3 |
| 7 — Mesures physiques | · |
| 8 — Mesures technologiques | 8.5, 8.7, 8.8, 8.13, 8.22, 8.26, 8.29 |

### Playbooks de réponse aux incidents

| Playbook | Risques |
|---|---|
| [P02 — Attaque par rançongiciel](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P02-rancongiciel.md) | R01 |
| [P03 — Fuite de données](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P03-fuite-de-donnees.md) | R03 |
| [P06 — Déni de service](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P06-deni-de-service.md) | R04 |
| [P07 — Compte compromis et fraude au virement](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P07-compte-compromis.md) | R02 |

### Techniques MITRE ATT&CK

| Technique | Risques |
|---|---|
| [T1133](https://attack.mitre.org/techniques/T1133/) | R01 |
| [T1190](https://attack.mitre.org/techniques/T1190/) | R03 |
| [T1486](https://attack.mitre.org/techniques/T1486/) | R01 |
| [T1490](https://attack.mitre.org/techniques/T1490/) | R01 |
| [T1566](https://attack.mitre.org/techniques/T1566/) | R02 |
| [T1656](https://attack.mitre.org/techniques/T1656/) | R02 |

---

*Généré par risk-assessment-matrix 1.0.0 le 08/11/2026.*
