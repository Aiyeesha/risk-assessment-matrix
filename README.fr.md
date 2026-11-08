# Matrice d'évaluation des risques

🇬🇧 [English version](README.md)

Un **registre de risques méthodique** pour une PME ou une ETI : identifier, analyser, évaluer,
traiter, accepter et revoir chaque risque, selon une méthode écrite et vérifiable. Aligné sur
**ISO/IEC 27005:2022** et sur **EBIOS Risk Manager** (ANSSI, version 1.5 de mars 2024).

> 🚧 **En cours de construction** (v0.1.0). La méthode est en place ; le registre arrive à l'étape 3.

## Ce que contiendra le dépôt

| Élément | Contenu |
|---|---|
| **Méthode configurable** | Échelles, seuils et règles d'acceptation décrits dans un fichier TOML vérifié. Deux préréglages : **5×5** (vraisemblance × impact) et **EBIOS RM 4×4** (gravité G1–G4 × vraisemblance V1–V4). |
| **Risque inhérent et résiduel** | Score avant et après les mesures, les deux visibles sur la matrice. |
| **Traitement et acceptation** | Réduire, accepter, transférer ou éviter ; acceptation formelle (qui, quand, pourquoi, jusqu'à quand) lorsque le risque résiduel reste au-dessus de l'appétence. |
| **Revues et historique** | Prochaine revue, revues et mesures en retard, journal des modifications. |
| **Liens** | Actifs, menaces et vulnérabilités, mesures de l'annexe A d'ISO/IEC 27001:2022, techniques MITRE ATT&CK, et playbook de [réponse aux incidents](https://github.com/Aiyeesha/incident-response-playbook) à appliquer si le risque se réalise. |
| **Outils** | `risk-check` (vérification), `risk-report` (rapports Markdown et HTML), `risk-export` (JSON, CSV protégé contre l'injection de formules), interface web. |

## Feuille de route

| Étape | Contenu | État |
|---|---|---|
| 1 | Dépôt, structure, vérification de la syntaxe TOML, CI | ✅ |
| 2 | Méthode : format TOML, préréglages 5×5 et EBIOS RM 4×4 | ✅ |
| 3 | Registre : modèle, règles de cohérence, `risk-check` | ⏳ |
| 4 | Références (ISO/IEC 27001, ATT&CK, playbooks), import et export CSV sûrs | ⏳ |
| 5 | Rapports Markdown et HTML : `risk-report` | ⏳ |
| 6 | Guide d'évaluation et registres d'exemple FR/EN → **v1.0.0** | ⏳ |
| 7 | Interface web sur GitHub Pages → **v1.1.0** | ⏳ |
| 8 | Dépôt public et protections | ⏳ |

## La méthode

Une méthode est un fichier TOML (`kind = "method"`) qui décrit, **en français et en anglais** :

- les deux **axes** : la vraisemblance et l'impact (la « gravité » dans EBIOS RM), de 3 à 7 niveaux
  chacun, numérotés à partir de 1 ;
- les **niveaux de risque**, du moins grave au plus grave, avec leur couleur, leur fréquence de revue
  et ce que l'organisation en fait ;
- la **grille** `[grid]` : le niveau de chaque case, écrit explicitement. Une formule
  « vraisemblance × impact » ne permettrait pas de représenter les zones d'EBIOS RM ;
- l'**appétence** au risque et les **autorités d'acceptation** : qui peut accepter un risque
  au-dessus de l'appétence, et pour combien de mois au plus.

`risk-check` refuse une méthode incohérente et désigne le champ fautif par son chemin
(`grid.rows[4][2] : …`) :

- clés inconnues (une faute de frappe ne passe jamais en silence), textes manquants dans une langue ;
- grille incomplète, niveau inconnu ou jamais utilisé ;
- grille **non monotone** : un risque ne peut pas devenir moins grave quand sa vraisemblance ou son
  impact augmente ;
- un risque plus grave revu moins souvent, ou accepté plus longtemps, qu'un risque moins grave ;
- une autorité d'acceptation manquante (ou inutile) au regard de l'appétence.

### Préréglages

**[`iso27005-5x5`](methods/iso27005-5x5.toml)** — compatible avec la démarche d'ISO/IEC 27005:2022, qui
laisse chaque organisation définir ses échelles. Appétence : *Faible*.

| Vraisemblance ↓ / Impact → | Négligeable | Mineur | Modéré | Majeur | Critique |
|---|---|---|---|---|---|
| Quasi certain | Modéré | Élevé | Élevé | Critique | Critique |
| Probable | Faible | Modéré | Élevé | Élevé | Critique |
| Possible | Faible | Modéré | Modéré | Élevé | Élevé |
| Peu probable | Faible | Faible | Modéré | Modéré | Élevé |
| Rare | Faible | Faible | Faible | Faible | Modéré |

**[`ebios-rm-4x4`](methods/ebios-rm-4x4.toml)** — échelles d'EBIOS Risk Manager (gravité G1 à G4,
vraisemblance V1 à V4) et grille d'acceptation à trois zones. Appétence : *Acceptable en l'état*.

| Vraisemblance ↓ / Gravité → | G1 — Mineure | G2 — Significative | G3 — Grave | G4 — Critique |
|---|---|---|---|---|
| V4 — Quasi certain | Tolérable sous contrôle | Inacceptable | Inacceptable | Inacceptable |
| V3 — Très vraisemblable | Tolérable sous contrôle | Tolérable sous contrôle | Inacceptable | Inacceptable |
| V2 — Vraisemblable | Acceptable en l'état | Tolérable sous contrôle | Tolérable sous contrôle | Inacceptable |
| V1 — Peu vraisemblable | Acceptable en l'état | Acceptable en l'état | Tolérable sous contrôle | Tolérable sous contrôle |

> ⚙️ **À adapter.** Les deux préréglages sont des points de départ réalistes. Copiez-en un, ajustez
> descriptions, grille et autorités à votre organisation, puis faites valider le résultat par la
> direction : la méthode fait partie des critères de risque exigés par ISO/IEC 27001 (6.1.2).

## Utilisation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
risk-check              # vérifie methods/ et examples/
risk-check mon-registre.prive.toml
pytest -v
```

Les erreurs s'affichent au format `fichier:ligne: message`, reconnu par les éditeurs et la CI.
Code de retour : `0` si tout est valide, `1` en cas de problème, `2` en cas de mauvais usage.

> 🔒 **Un vrai registre ne se publie pas.** Il décrit les faiblesses de l'organisation. Nommez-le
> `*.prive.toml` ou rangez-le dans `registres-prives/` : ces fichiers sont exclus de Git.

## Licence

[MIT](LICENSE) — © 2026 Aïcha Imène Dahoumane.
