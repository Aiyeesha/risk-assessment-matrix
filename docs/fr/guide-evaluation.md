# Guide d'évaluation des risques

🇬🇧 [English version](../en/assessment-guide.md)

Ce guide accompagne une évaluation complète, de la première réunion à la revue suivante, avec les
outils du dépôt. Il s'adresse au RSSI d'une PME ou d'une ETI, au DSI qui en tient le rôle, ou à
quiconque doit produire un registre de risques défendable devant une direction ou un auditeur.

Fil rouge : **Atelier Lumen**, entreprise fictive dont les registres complets sont dans
[`examples/fr/`](../../examples/fr/) — méthode 5×5 et variante EBIOS Risk Manager.

## Sommaire

1. [La démarche en un coup d'œil](#1-la-démarche-en-un-coup-dœil)
2. [Préparer : périmètre, participants, méthode](#2-préparer--périmètre-participants-méthode)
3. [Identifier les risques](#3-identifier-les-risques)
4. [Analyser : coter le risque inhérent](#4-analyser--coter-le-risque-inhérent)
5. [Évaluer : comparer à l'appétence](#5-évaluer--comparer-à-lappétence)
6. [Traiter : choisir et planifier](#6-traiter--choisir-et-planifier)
7. [Accepter formellement le risque résiduel](#7-accepter-formellement-le-risque-résiduel)
8. [Suivre et revoir](#8-suivre-et-revoir)
9. [Rendre compte](#9-rendre-compte)
10. [Erreurs fréquentes](#10-erreurs-fréquentes)
11. [Correspondances avec les référentiels](#11-correspondances-avec-les-référentiels)

## 1. La démarche en un coup d'œil

| Étape | Question | Ce que l'on produit | Outil |
|---|---|---|---|
| Préparer | Quoi, avec qui, selon quelles règles ? | Périmètre, méthode validée | `methods/*.toml`, `risk-check` |
| Identifier | Qu'est-ce qui peut mal tourner ? | Liste de risques décrits | Registre TOML ou tableur + `risk-import` |
| Analyser | À quel point est-ce probable, et grave ? | Risque inhérent | `inherent` |
| Évaluer | Est-ce acceptable en l'état ? | Priorités | Grille et appétence de la méthode |
| Traiter | Que fait-on, qui, pour quand ? | Plan d'action, risque résiduel | `measures`, `residual`, `treatment` |
| Accepter | Qui assume ce qui reste ? | Acceptations signées | `acceptance` |
| Suivre | Est-ce toujours vrai ? | Revues, historique, alertes | `review`, `history`, `risk-check --strict` |
| Rendre compte | Que doit savoir la direction ? | Rapport | `risk-report` |

Ce cycle se répète : **au moins une fois par an**, et à chaque changement important (nouvelle
activité, migration, incident, exercice révélant une faiblesse). ISO/IEC 27001:2022 exige que
l'appréciation des risques soit refaite à intervalles planifiés et lors de changements importants
(8.2).

## 2. Préparer : périmètre, participants, méthode

### 2.1 Fixer le périmètre

Écrivez en une phrase ce qui est couvert et ce qui ne l'est pas. Pour Atelier Lumen : *« tout le
système d'information du siège, de l'entrepôt et de la boutique en ligne ; la fabrication,
sous-traitée, est hors périmètre, mais la dépendance aux fournisseurs y est. »*

### 2.2 Réunir les bonnes personnes

Un registre écrit seul par l'informatique sous-estime les risques métier, et inversement.

| Rôle | Apport |
|---|---|
| RSSI ou DSI | Menaces, vulnérabilités, mesures techniques ; anime la démarche |
| Direction (ou son représentant) | Appétence, arbitrages, acceptations |
| Responsables métier (finance, commerce, logistique, RH) | Ce qui compte vraiment, ce que coûterait un arrêt |
| DPO | Données personnelles, obligations du RGPD |
| Prestataires clés (infogérance, hébergeur) | Ce qu'ils couvrent, et surtout ce qu'ils ne couvrent pas |

### 2.3 Choisir la méthode

Le dépôt fournit deux préréglages ([`methods/`](../../methods/)) :

| | `iso27005-5x5` | `ebios-rm-4x4` |
|---|---|---|
| Échelles | Vraisemblance 1–5 × impact 1–5 | Vraisemblance V1–V4 × gravité G1–G4 |
| Niveaux | Faible, modéré, élevé, critique | Acceptable, tolérable, inacceptable |
| Convient à | Une première évaluation ; un registre « classique » attendu par un auditeur ISO/IEC 27001 | Une organisation qui suit EBIOS RM (homologation, secteur public, entités régulées et leurs prestataires) |
| Grain | Plus fin (25 cases) | Plus tranché (16 cases, trois zones de décision) |

> 💡 **Une échelle paire n'a pas de milieu.** Avec quatre niveaux, impossible de tout coter « 3 sur
> 5 » par prudence : il faut trancher. C'est l'un des intérêts des échelles d'EBIOS RM.

### 2.4 Adapter puis faire valider la méthode

Les préréglages sont des points de départ. Copiez-en un, puis relisez chaque description avec la
direction : *« Pour nous, un impact majeur, c'est quoi ? »*. Les montants, durées d'arrêt et
fréquences doivent parler à **votre** organisation.

```powershell
Copy-Item methods\iso27005-5x5.toml methods\lumen-5x5.toml
# Modifier id = "lumen-5x5", les descriptions, la grille, l'appétence et les autorités, puis :
risk-check methods
```

`risk-check` refuse une méthode incohérente : grille non monotone (une case moins grave que sa
voisine plus probable), niveau jamais utilisé, autorité manquante au-dessus de l'appétence, revue
moins fréquente pour un risque plus grave… La méthode validée fait partie des **critères de
risque** qu'exige ISO/IEC 27001 (6.1.2) : conservez la trace de sa validation (date, qui).

## 3. Identifier les risques

### 3.1 Où chercher

- **Les activités et ce dont elles dépendent** : pour chaque activité essentielle (vendre en ligne,
  expédier, payer les fournisseurs), quelles informations, quels systèmes, quels prestataires ?
- **Les incidents passés**, chez vous et dans votre secteur.
- **Les exercices** : l'[exercice sur table](https://github.com/Aiyeesha/incident-response-playbook/blob/main/fr/docs/D06-exercice-sur-table.md)
  d'Atelier Lumen a révélé deux faiblesses — VPN sans MFA, NAS de sauvegarde joignable — qui
  fondent le risque R01.
- **Les audits, tests d'intrusion, scans de vulnérabilités**.
- **L'annexe A d'ISO/IEC 27001:2022**, lue à l'envers : pour chaque thème, *« que se passerait-il si
  nous n'avions rien ? »*

ISO/IEC 27005:2022 décrit deux façons d'identifier les risques, complémentaires : **par les
événements** (scénarios : *« un rançongiciel paralyse l'expédition »*) et **par les actifs**
(*« le serveur de fichiers : quelles menaces, quelles vulnérabilités ? »*). EBIOS RM part des
**sources de risque** et de leurs **objectifs visés** (atelier 2), puis construit des scénarios
stratégiques (atelier 3) et opérationnels (atelier 4).

### 3.2 Bien décrire un risque

Un risque bien écrit tient en une phrase **cause → événement → conséquence** :

> *Un attaquant entre par le VPN avec un mot de passe volé* (cause), *chiffre le serveur de
> fichiers et les sauvegardes* (événement) ; *l'expédition s'arrête plusieurs jours* (conséquence).

Dans le registre :

| Champ | Contenu | Exemple (R01) |
|---|---|---|
| `title` | L'événement redouté, court | Rançongiciel chiffrant le serveur de fichiers et les sauvegardes |
| `description` | La phrase cause → événement → conséquence | … |
| `assets` | Ce qui est touché | Serveur de fichiers, NAS de sauvegarde, Active Directory |
| `threat` | Qui ou quoi | Groupe criminel, avec double extorsion |
| `vulnerability` | Ce qui le permet | VPN sans MFA ; NAS joignable depuis le réseau bureautique |
| `owner` | **Une** personne qui répond du risque | Julien Morel, DSI |
| `gdpr`, `nis2` | Données personnelles en jeu ? Incident à notifier au titre de NIS 2 ? | `true`, `false` |

> ⚠️ **« Le risque cyber » n'est pas un risque.** Trop vague pour être coté ou traité. À
> l'inverse, une liste de 200 vulnérabilités techniques n'est pas un registre de risques : regroupez
> par scénario. Un registre utile tient souvent entre 10 et 40 risques.

### 3.3 Démarrer depuis un tableur

Si l'atelier se fait dans Excel, partez de l'export CSV d'un registre d'exemple, remplissez-le,
puis convertissez-le :

```powershell
risk-export examples\fr\atelier-lumen.toml --format csv -o risques.csv --measures mesures.csv
# … travail dans Excel, enregistrement au format « CSV UTF-8 » …
risk-import risques.csv --measures mesures.csv -o registres-prives\lumen.prive.toml `
    --method lumen-5x5 --organisation "Atelier Lumen" --assessed-on 2026-09-15 --assessor "Comité des risques"
```

`risk-import` liste ce qui manque encore ; complétez le fichier TOML jusqu'à ce que `risk-check`
ne signale plus d'erreur.

## 4. Analyser : coter le risque inhérent

### 4.1 Ce que « inhérent » veut dire ici

Dans ce dépôt, le **risque inhérent** est le risque **tel qu'il est aujourd'hui**, avec les mesures
déjà en place (`existing_controls`), **avant** les mesures que l'on prévoit d'ajouter. Le **risque
résiduel** est celui qui restera **une fois les mesures prévues réalisées**.

> ⚠️ **Définitions variables.** Certaines méthodes appellent « inhérent » le risque sans *aucune*
> mesure, même existante. Ce choix est rarement utile (personne n'imagine une entreprise sans
> antivirus) et produit des cotes artificiellement hautes. Quelle que soit la convention retenue,
> écrivez-la dans la méthode et tenez-vous-y.

### 4.2 Coter

Pour chaque risque, choisissez un niveau de **vraisemblance** et un niveau d'**impact** en lisant
les descriptions de la méthode — pas au jugé. Coter à plusieurs, chacun d'abord seul, puis
confronter : les écarts révèlent des informations que tous n'ont pas.

| Bonne pratique | Pourquoi |
|---|---|
| Coter l'impact du **scénario réaliste le plus grave**, pas du pire imaginable | Sinon tout devient « critique » et plus rien n'est prioritaire |
| Justifier la vraisemblance par des faits (incidents, exposition, attractivité) | Une cote se défend devant un auditeur |
| Coter l'impact sur **toutes** les dimensions : activité, finances, juridique, image, personnes | Une fuite de données « sans arrêt de service » peut coûter très cher |
| Se méfier du milieu de l'échelle | « 3 sur 5 » par défaut ne décide rien |

Le niveau de risque n'est **pas calculé** par le registre : il est **lu dans la grille** de la
méthode. Ainsi une méthode peut juger qu'un impact critique reste critique même s'il est rare.

## 5. Évaluer : comparer à l'appétence

L'**appétence** est le niveau le plus élevé que l'organisation accepte sans décision particulière
(« Faible » dans le 5×5, « Acceptable » dans EBIOS RM). Tout risque au-dessus appelle un
traitement, ou une acceptation formelle par l'autorité prévue.

Le rapport classe les risques du plus grave au moins grave et affiche les deux **cartographies** :
le risque inhérent montre où l'on part, le risque résiduel où les mesures prévues mèneront.

## 6. Traiter : choisir et planifier

### 6.1 Les quatre options

| `treatment` | Sens | Exige | Atelier Lumen |
|---|---|---|---|
| `reduce` | Réduire la vraisemblance ou l'impact par des mesures | Au moins une mesure | R01 (MFA, sauvegardes immuables, EDR, segmentation) |
| `transfer` | Faire porter tout ou partie des conséquences par un tiers | `transfer.to` : à qui | R05 (engagement de l'hébergeur, assurance cyber) |
| `avoid` | Supprimer l'activité ou l'actif à l'origine du risque | — | R08 (serveurs de l'entrepôt retirés : risque clos) |
| `accept` | Garder le risque en l'état, en connaissance de cause | Acceptation formelle s'il dépasse l'appétence | R04 de la variante EBIOS RM |

> 💡 **Transférer n'efface pas le risque.** Une assurance rembourse ; elle ne restaure ni les
> données, ni la confiance des clients. Le risque résiduel d'un transfert reste souvent au-dessus de
> l'appétence : il faut alors l'accepter formellement (R05).

### 6.2 Planifier les mesures

Chaque mesure a un **intitulé actionnable**, **un responsable**, une **échéance** et un **état**
(`planned`, `in-progress`, `done`). Rattachez-la aux mesures de l'annexe A d'ISO/IEC 27001:2022 qu'elle
met en œuvre (`iso27001 = ["8.5"]`) : la [déclaration d'applicabilité](#11-correspondances-avec-les-référentiels)
en sera plus simple à tenir.

### 6.3 Coter le risque résiduel

Recotez le risque **comme si toutes les mesures prévues étaient faites**. Le résiduel ne peut pas
dépasser l'inhérent sans `justification` (par exemple, une exposition qui augmente pendant un
projet) : `risk-check` le refuse.

### 6.4 Relier au plan de réponse

Indiquez les techniques MITRE ATT&CK du scénario (`attack`) et le **playbook** à appliquer s'il se
réalise (`playbooks`, P01 à P07 du dépôt de réponse aux incidents). Le risque R01 renvoie ainsi au
playbook P02, celui que l'exercice sur table a mis à l'épreuve.

## 7. Accepter formellement le risque résiduel

Un risque résiduel au-dessus de l'appétence doit être **accepté formellement** dès que plus rien
n'est en cours pour le réduire (traitement `accept`, ou toutes les mesures terminées). C'est
l'approbation des risques résiduels par leurs propriétaires qu'exige ISO/IEC 27001 (6.1.3).

```toml
acceptance = { by = "Nadia Ferrand", role = "Responsable du risque", on = 2026-10-01, until = 2027-10-01, rationale = "…" }
```

- `role` doit être **exactement** l'autorité prévue par la méthode pour ce niveau, dans la langue du
  registre — un risque élevé ne s'accepte pas à l'échelon d'un risque modéré.
- `until` ne peut dépasser la durée maximale de la méthode (12 mois pour un risque modéré, 3 pour un
  critique dans le 5×5 ; 6 mois pour un risque inacceptable dans EBIOS RM).
- `rationale` dit **pourquoi** : coût disproportionné, mesure impossible avant une date, risque
  couvert autrement. *« Accepté »* seul ne protège personne.

> ⚠️ **Une acceptation expire.** Passé `until`, `risk-check` avertit : il faut renouveler
> l'acceptation (nouvelle décision, nouvelle date) ou reprendre le traitement.

## 8. Suivre et revoir

### 8.1 La date de prochaine revue

Chaque risque a une revue (`review.last`, `review.next`). L'intervalle maximal dépend du niveau
résiduel (dans le 5×5 : 12 mois pour un risque faible, 1 mois pour un critique). Revoir un risque,
c'est vérifier que sa description, ses cotes et ses mesures sont toujours vraies.

Revoyez **hors cycle** après un incident, un changement important (migration, nouveau prestataire),
un exercice ou un audit qui révèle quelque chose.

### 8.2 L'historique

Notez chaque décision dans `[[risks.history]]` : création, recotation, mesure terminée, acceptation,
clôture. L'historique est la mémoire du registre — ce que demandera un auditeur, ou votre
successeur.

### 8.3 Laisser l'outil surveiller

```powershell
risk-check                    # erreurs : bloquantes ; échéances dépassées : avertissements
risk-check --strict           # les avertissements deviennent bloquants (code 1)
```

Dans une intégration continue ou une tâche planifiée, `--strict` transforme toute mesure en retard,
revue dépassée ou acceptation expirée en alerte visible.

> 🔒 **Un vrai registre ne se publie pas.** Il décrit précisément les faiblesses de l'organisation.
> Rangez-le dans `registres-prives/` ou nommez-le `*.prive.toml` (exclus de Git), et limitez son
> accès comme une information interne sensible.

## 9. Rendre compte

```powershell
risk-report registres-prives\lumen.prive.toml --format html -o rapports\risques.html
```

Le rapport HTML, autonome et imprimable, sert de support au comité de direction : synthèse,
cartographies, risques au-dessus de l'appétence et leur situation, plan d'action, revues à venir. La
revue de direction d'ISO/IEC 27001 (9.3) attend notamment les résultats de l'appréciation des
risques et l'état du plan de traitement.

Exemples de rapports générés : [5×5](../../examples/fr/atelier-lumen.md) ·
[EBIOS RM](../../examples/fr/atelier-lumen-ebios.md) (versions HTML et JSON dans le même dossier).

## 10. Erreurs fréquentes

| Erreur | Conséquence | Remède |
|---|---|---|
| Tout coter « critique » | Plus de priorité | Coter le scénario réaliste, pas le pire imaginable |
| Un comité comme responsable du risque | Personne n'agit | Une personne nommée par risque |
| Des mesures sans échéance | Le plan n'avance pas | Échéance et responsable pour chacune |
| Le résiduel coté comme si les mesures étaient déjà faites… alors qu'elles ne le sont pas | Fausse impression de sécurité | Le résiduel est un **objectif** ; le rapport montre les mesures ouvertes |
| Une acceptation sans motif ni fin | Le risque est oublié | `rationale` et `until`, puis renouvellement |
| Un registre revu une fois par an seulement | Il ne décrit plus la réalité | Revues selon le niveau, et hors cycle après chaque changement |

## 11. Correspondances avec les référentiels

| Ce dépôt | ISO/IEC 27001:2022 | ISO/IEC 27005:2022 | EBIOS Risk Manager |
|---|---|---|---|
| Méthode (`methods/`) | Critères de risque (6.1.2) | Établissement du contexte, critères | Atelier 1 : cadrage, socle de sécurité |
| `threat`, `assets`, `description` | Identification (6.1.2) | Identification, par événements ou par actifs | Ateliers 2 à 4 : sources de risque, scénarios stratégiques et opérationnels |
| `inherent` | Analyse (6.1.2) | Analyse : vraisemblance et conséquences | Évaluation de la gravité et de la vraisemblance |
| Grille, appétence | Évaluation (6.1.2) | Évaluation, comparaison aux critères | Cartographie et grille d'acceptation |
| `treatment`, `measures`, `residual` | Traitement (6.1.3), mise en œuvre (8.3) | Traitement : options, mesures, plan | Atelier 5 : stratégie de traitement, mesures |
| `iso27001` | Annexe A, déclaration d'applicabilité (6.1.3 d) | — | Socle de sécurité |
| `acceptance` | Approbation des risques résiduels (6.1.3) | Acceptation des risques | Homologation (risques résiduels acceptés) |
| `review`, `history` | Appréciation à intervalles planifiés (8.2), revue de direction (9.3) | Surveillance et revue | Cycles stratégique et opérationnel |

> ℹ️ **Références.** ISO/IEC 27001:2022 et ISO/IEC 27005:2022 sont des normes payantes : ce guide
> en cite les exigences sans les reproduire. EBIOS Risk Manager est publié gratuitement par l'ANSSI
> (version 1.5, 2024) sur [cyber.gouv.fr](https://cyber.gouv.fr/).
