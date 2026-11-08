# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/),
versionnage [sémantique](https://semver.org/lang/fr/).

Ce dépôt remplace deux anciens dépôts, archivés en privé : `risk-assessment-matrix` (version
anglaise d'origine, renommée `archive-risk-assessment-matrix`) et `matrice-risques` (reconstruction
française, renommée `archive-matrice-risques`).

## [Non publié]

### Ajouté
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
