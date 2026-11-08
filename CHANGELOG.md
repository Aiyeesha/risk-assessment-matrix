# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versionnage [sémantique](https://semver.org/lang/fr/).

Ce dépôt remplace deux anciens dépôts, archivés en privé : `risk-assessment-matrix` (version
anglaise d'origine, renommée `archive-risk-assessment-matrix`) et `matrice-risques` (reconstruction
française, renommée `archive-matrice-risques`).

## [Non publié]

### Modifié
- Dépôt rendu public : règles de protection de `main` (Pull Request obligatoire, 7 vérifications
  requises, ni suppression ni réécriture de l'historique), analyse des secrets et protection à
  l'envoi, alertes et correctifs Dependabot, signalement privé des vulnérabilités ; interface web
  publiée sur GitHub Pages.

## [1.1.0] — 2026-11-08

### Ajouté
- **Interface web** ([`web/`](web/)), publiée sur GitHub Pages : chargement des registres d'exemple
  ou d'un export JSON local (lu dans le navigateur, jamais envoyé), synthèse, cartographies du risque
  inhérent et résiduel cliquables, liste filtrable et fiche détaillée, plan d'action, calendrier des
  revues ; français et anglais, thème clair ou sombre, clavier et mobile.
- Sécurité de l'interface : validation complète de l'export (types, dates, couleurs, cohérence avec
  la grille), texte inséré avec `textContent`, liens limités à attack.mitre.org et au dépôt des
  playbooks, CSP stricte, seule la langue mémorisable (sur demande).
- CI : job « Interface web · Node 24 » (typage, 24 tests sur les exports d'exemple, construction) ;
  workflow Pages (publication dès que le dépôt est public) ; Dependabot pour npm.

## [1.0.0] — 2026-11-08

Première version complète de l'outillage en ligne de commande.

### Ajouté
- **Guide d'évaluation** en français ([`docs/fr/guide-evaluation.md`](docs/fr/guide-evaluation.md))
  et en anglais ([`docs/en/assessment-guide.md`](docs/en/assessment-guide.md)) : préparation,
  identification, analyse, évaluation, traitement, acceptation formelle, suivi et revue, compte rendu,
  erreurs fréquentes, correspondances ISO/IEC 27001:2022, ISO/IEC 27005:2022 et EBIOS RM.
- **Registres d'exemple** d'Atelier Lumen (entreprise fictive), en français et en anglais : 8 risques
  avec la méthode 5×5, 4 scénarios stratégiques avec EBIOS RM 4×4 ; versions françaises et anglaises
  vérifiées comme strictement parallèles par les tests.
- **Sorties d'exemple** (rapports Markdown et HTML, export JSON) générées à date fixe par
  `scripts/build_examples.py` ; la CI vérifie qu'elles restent à jour.
- Captures du rapport HTML (clair en français, sombre en anglais) dans les README.
- Ossature du projet : paquet Python `risk_matrix` sans dépendance d'exécution, commande `risk-check`
  qui vérifie la syntaxe des fichiers TOML de `methods/` et `examples/` (ou des chemins donnés) et
  affiche les erreurs au format `fichier:ligne: message`.
- Protections : fichiers de plus de 1 Mio refusés, encodage UTF-8 exigé, registres réels exclus de Git
  (`registres-prives/`, `private-registers/`, `*.prive.toml`, `*.private.toml`).
- CI : tests sous Linux et Windows avec Python 3.11 et 3.14, analyse Ruff, vérification des fichiers
  TOML du dépôt ; Dependabot pour les actions GitHub et les outils Python.
- README en français et en anglais, politique de sécurité, licence MIT.
- **Méthode d'évaluation** (`kind = "method"`, module `method.py`) : axes de vraisemblance et d'impact,
  niveaux de risque, grille explicite case par case, appétence et autorités d'acceptation, textes en
  français et en anglais. `risk-check` vérifie clés, textes, dimensions et monotonie de la grille,
  cohérence des fréquences de revue et des durées d'acceptation, autorités au regard de l'appétence ;
  chaque fichier doit déclarer son type (`kind`), et deux méthodes ne peuvent pas partager un `id`.
- Préréglages `iso27005-5x5` (vraisemblance × impact, règle du produit) et `ebios-rm-4x4` (échelles
  d'EBIOS Risk Manager 1.5, grille d'acceptation à trois zones donnée en exemple).
- **Registre de risques** (`kind = "register"`, module `register.py`) : identification (actifs,
  menace, vulnérabilité, RGPD, NIS 2), risque inhérent et résiduel, mesures prévues (responsable,
  échéance, état), traitement (réduire, accepter, transférer, éviter), acceptation formelle, revue et
  historique. `risk-check` vérifie chaque registre avec la méthode qu'il désigne : notes dans les
  échelles, résiduel justifié s'il dépasse l'inhérent, acceptation exigée au-dessus de l'appétence
  (autorité et durée maximale prévues par la méthode), fréquence de revue, historique chronologique.
- **Avertissements** distincts des erreurs pour ce qui est échu (mesure ou revue en retard,
  acceptation expirée) ; options `--today` (date de référence), `--strict` (les avertissements font
  échouer) et `--methods` (dossier des méthodes, `methods/` par défaut).
- **Références** (module `references.py`) : mesures de l'annexe A d'ISO/IEC 27001:2022 (numéros
  5.1 à 8.34 vérifiés, sans le texte des mesures), techniques MITRE ATT&CK (format vérifié, lien vers
  la fiche) et playbooks P01 à P07 du dépôt incident-response-playbook, sur chaque risque
  (`iso27001`, `attack`, `playbooks`) et sur chaque mesure (`iso27001`).
- **`risk-export`** : export d'un registre valide en JSON (`schema_version` 1 : niveaux calculés,
  liens, avertissements) ou en CSV (risques et mesures, séparateur adapté à la langue, UTF-8 avec
  BOM pour Excel).
- **`risk-import`** : création d'un registre TOML depuis les mêmes CSV (aller-retour avec un tableur),
  cellules typées et vérifiées, registre obtenu vérifié comme par `risk-check`.
- Sécurité des CSV : protection contre l'injection de formules (CWE-1236) à l'export, apostrophe de
  protection retirée à l'import ; fichiers limités à 1 Mio et 5 000 lignes, UTF-8 exigé ; aucun
  fichier existant écrasé sans `--force`.
- **`risk-report`** : rapport Markdown ou HTML dans la langue du registre — synthèse, cartographies
  du risque inhérent et résiduel, risques par niveau, risques au-dessus de l'appétence et leurs
  acceptations, plan d'action, calendrier des revues, références (annexe A, playbooks, ATT&CK),
  risques clos et avertissements. HTML autonome et imprimable, sans script ni ressource externe,
  texte échappé, CSP limitée à la feuille de style intégrée (empreinte SHA-256), mode sombre.

### Corrigé
- `description` et `category` d'un risque sont bien facultatives, comme l'indique la documentation.
- Orange du niveau « élevé » / « tolérable » assombri (`#b85300`) dans les deux préréglages : le
  texte blanc y atteint le contraste WCAG AA (4,91:1 au lieu de 4,42:1).
