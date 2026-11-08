# Rapport de risques — Atelier Lumen (entreprise fictive)

- Méthode : Matrice 5×5 — vraisemblance × impact
- Évaluation : 15/09/2026, par Comité des risques (RSSI, DSI, DAF, DPO)
- Situation au : 08/11/2026

## Synthèse

- 7 risque(s) actif(s), 1 clos
- 5 au-dessus de l'appétence (« Faible »)
- 4 mesure(s) ouverte(s), dont 1 en retard
- 1 avertissement(s) à traiter

| Niveau résiduel | Risques |
|---|---|
| Critique | 0 |
| Élevé | 1 |
| Modéré | 4 |
| Faible | 2 |

## Cartographie — risque inhérent

| Vraisemblance ↓ / Impact → | Négligeable | Mineur | Modéré | Majeur | Critique |
|---|---|---|---|---|---|
| Quasi certain | Modéré | Élevé | Élevé | Critique | Critique |
| Probable | Faible | Modéré | Élevé · **R04** | Élevé · **R02** | Critique · **R01** |
| Possible | Faible | Modéré | Modéré · **R05, R06** | Élevé · **R03** | Élevé |
| Peu probable | Faible | Faible | Modéré | Modéré · **R07** | Élevé |
| Rare | Faible | Faible | Faible | Faible | Modéré |

## Cartographie — risque résiduel

| Vraisemblance ↓ / Impact → | Négligeable | Mineur | Modéré | Majeur | Critique |
|---|---|---|---|---|---|
| Quasi certain | Modéré | Élevé | Élevé | Critique | Critique |
| Probable | Faible | Modéré | Élevé | Élevé | Critique |
| Possible | Faible · **R06** | Modéré · **R05** | Modéré | Élevé · **R01** | Élevé |
| Peu probable | Faible | Faible | Modéré · **R04** | Modéré · **R02, R03** | Élevé |
| Rare | Faible | Faible | Faible | Faible · **R07** | Modéré |

Chaque case indique son niveau et les risques actifs qui s'y trouvent.

## Risques par niveau résiduel

| ID | Risque | Responsable | Inhérent | Résiduel | Traitement | Prochaine revue |
|---|---|---|---|---|---|---|
| R01 | Rançongiciel chiffrant le serveur de fichiers et les sauvegardes | Julien Morel, DSI | Critique | Élevé | Réduire | 15/01/2027 |
| R02 | Fraude au virement par usurpation d'un fournisseur | Nadia Ferrand, DAF | Élevé | Modéré | Réduire | 15/03/2027 |
| R03 | Fuite des données clients de la boutique en ligne | Camille Roy, responsable du commerce en ligne | Élevé | Modéré | Réduire | 15/03/2027 |
| R04 | Compromission de comptes Microsoft 365 par hameçonnage | Julien Morel, DSI | Élevé | Modéré | Réduire | 01/04/2027 |
| R05 | Indisponibilité prolongée de la boutique en ligne | Camille Roy, responsable du commerce en ligne | Modéré | Modéré | Transférer | 15/03/2027 |
| R06 | Vol ou perte d'un ordinateur portable | Julien Morel, DSI | Modéré | Faible | Réduire | 15/09/2027 |
| R07 | Accès conservés après un départ ou la fin d'un contrat de prestation | Responsable des ressources humaines | Modéré | Faible | Réduire | 15/09/2027 |

## Au-dessus de l'appétence

| ID | Risque | Résiduel | Situation |
|---|---|---|---|
| R01 | Rançongiciel chiffrant le serveur de fichiers et les sauvegardes | Élevé | Réduction en cours (2 mesure(s) ouverte(s)) |
| R02 | Fraude au virement par usurpation d'un fournisseur | Modéré | Accepté par Nadia Ferrand (Responsable du risque) jusqu'au 01/10/2027 |
| R03 | Fuite des données clients de la boutique en ligne | Modéré | Réduction en cours (1 mesure(s) ouverte(s)) |
| R04 | Compromission de comptes Microsoft 365 par hameçonnage | Modéré | Accepté par Julien Morel (Responsable du risque) jusqu'au 01/10/2027 |
| R05 | Indisponibilité prolongée de la boutique en ligne | Modéré | Accepté par Camille Roy (Responsable du risque) jusqu'au 15/09/2027 |

## Plan d'action

| Échéance | ID | Mesure | Responsable | État |
|---|---|---|---|---|
| **31/10/2026** | R03 | Test d'intrusion de la boutique et correction des failles trouvées | Camille Roy | **En retard** |
| 15/12/2026 | R01 | EDR sur tous les postes et serveurs, supervisé 24 h/24 | Prestataire d'infogérance | En cours |
| 31/01/2027 | R01 | Isoler le NAS de sauvegarde dans un réseau dédié | Julien Morel, DSI | Prévue |
| 31/03/2027 | R07 | Procédure de départ commune RH / informatique et revue trimestrielle des comptes | Responsable des ressources humaines | Prévue |

## Calendrier des revues

| Date | ID | Risque | Résiduel |
|---|---|---|---|
| 15/01/2027 | R01 | Rançongiciel chiffrant le serveur de fichiers et les sauvegardes | Élevé |
| 15/03/2027 | R02 | Fraude au virement par usurpation d'un fournisseur | Modéré |
| 15/03/2027 | R03 | Fuite des données clients de la boutique en ligne | Modéré |
| 15/03/2027 | R05 | Indisponibilité prolongée de la boutique en ligne | Modéré |
| 01/04/2027 | R04 | Compromission de comptes Microsoft 365 par hameçonnage | Modéré |
| 15/09/2027 | R06 | Vol ou perte d'un ordinateur portable | Faible |
| 15/09/2027 | R07 | Accès conservés après un départ ou la fin d'un contrat de prestation | Faible |

## Références

### ISO/IEC 27001:2022, annexe A

| Thème | Mesures citées |
|---|---|
| 5 — Mesures organisationnelles | 5.14, 5.15, 5.17, 5.18, 5.20, 5.23, 5.30 |
| 6 — Mesures liées aux personnes | 6.3, 6.5 |
| 7 — Mesures physiques | 7.9 |
| 8 — Mesures technologiques | 8.1, 8.2, 8.5, 8.7, 8.8, 8.13, 8.16, 8.20, 8.22, 8.24, 8.26, 8.28, 8.29 |

### Playbooks de réponse aux incidents

| Playbook | Risques |
|---|---|
| [P01 — Infection par logiciel malveillant](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P01-logiciel-malveillant.md) | R01 |
| [P02 — Attaque par rançongiciel](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P02-rancongiciel.md) | R01 |
| [P03 — Fuite de données](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P03-fuite-de-donnees.md) | R03 |
| [P04 — Hameçonnage](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P04-hameconnage.md) | R02, R04 |
| [P05 — Accès non autorisé](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P05-acces-non-autorise.md) | R07 |
| [P06 — Déni de service](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P06-deni-de-service.md) | R05 |
| [P07 — Compte compromis et fraude au virement](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/playbooks/P07-compte-compromis.md) | R02, R04 |

### Techniques MITRE ATT&CK

| Technique | Risques |
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

## Risques clos

| ID | Risque |
|---|---|
| R08 | Sinistre dans la salle serveur de l'entrepôt |

## Avertissements

- R03.measures\[1\] : mesure en retard (échéance 2026-10-31) — « Test d'intrusion de la boutique et correction des failles trouvées »

---

*Généré par risk-assessment-matrix 1.1.0 le 08/11/2026.*
