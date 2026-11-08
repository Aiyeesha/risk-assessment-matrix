# Politique de sécurité

## Signaler un problème

Merci de **ne pas ouvrir d'issue publique** pour une faille de l'outillage.

Utilisez le signalement privé de GitHub : onglet **Security** du dépôt → **Report a vulnerability**
(disponible une fois le dépôt public).

## Ce qui est concerné

- une faiblesse des outils (`risk-check`, puis `risk-report` et `risk-export`) : lecture de fichiers
  hors du dossier demandé, injection dans un rapport HTML ou un export CSV, etc. ;
- une erreur de méthode qui ferait sous-estimer un risque (calcul de score, seuil d'acceptation).

## Données sensibles

Ce dépôt ne contient que des **exemples fictifs**. Le registre de risques d'une vraie organisation
décrit ses faiblesses, ses actifs critiques et ses mesures manquantes : **ne le publiez jamais**.
Le fichier `.gitignore` exclut par précaution les dossiers `registres-prives/` et `private-registers/`
ainsi que les fichiers `*.prive.toml` et `*.private.toml`.

## Délais

Projet personnel maintenu sur le temps libre : accusé de réception visé sous 7 jours.
