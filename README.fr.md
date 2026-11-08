# Matrice d'évaluation des risques

🇬🇧 [English version](README.md)

Un **registre de risques méthodique** pour une PME ou une ETI : identifier, analyser, évaluer,
traiter, accepter et revoir chaque risque, selon une méthode écrite et vérifiable. Aligné sur
**ISO/IEC 27005:2022** et sur **EBIOS Risk Manager** (ANSSI, version 1.5 de mars 2024).

> 🚧 **En cours de construction** (v0.1.0 — ossature). La méthode arrive à l'étape 2, le registre
> à l'étape 3.

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
| 2 | Méthode : format TOML, préréglages 5×5 et EBIOS RM 4×4 | ⏳ |
| 3 | Registre : modèle, règles de cohérence, `risk-check` | ⏳ |
| 4 | Références (ISO/IEC 27001, ATT&CK, playbooks), import et export CSV sûrs | ⏳ |
| 5 | Rapports Markdown et HTML : `risk-report` | ⏳ |
| 6 | Guide d'évaluation et registres d'exemple FR/EN → **v1.0.0** | ⏳ |
| 7 | Interface web sur GitHub Pages → **v1.1.0** | ⏳ |
| 8 | Dépôt public et protections | ⏳ |

## Utilisation (étape 1)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
risk-check              # vérifie methods/ et examples/ (syntaxe TOML pour l'instant)
risk-check mon-registre.prive.toml
pytest -v
```

Les erreurs s'affichent au format `fichier:ligne: message`, reconnu par les éditeurs et la CI.
Code de retour : `0` si tout est valide, `1` en cas de problème, `2` en cas de mauvais usage.

> 🔒 **Un vrai registre ne se publie pas.** Il décrit les faiblesses de l'organisation. Nommez-le
> `*.prive.toml` ou rangez-le dans `registres-prives/` : ces fichiers sont exclus de Git.

## Licence

[MIT](LICENSE) — © 2026 Aïcha Imène Dahoumane.
