# 0019 — La CI pousse l'index avec une clé de déploiement, et un projet se publie depuis n'importe quel dossier

- Date : 2026-10-11
- Origine : [humain] « ok maintenant il faut tester tout ca en créant un nouveau depot qui obeis a ces regles » ; [choix] « oui et oui » de Romain au bilan du test (corriger les frictions relevées, publier la page en ligne)
- Décidé par : Romain (comité du socle)
- Options écartées : garder la relance par `workflow_dispatch` et approuver à la main chaque exécution en attente ; une GitHub App par organisation pour pousser l'index (plus de réglages pour un seul usage) ; revenir à un index commité par le contributeur (contraire à la décision 0017)
- Source : projet Claude « Memnius », essai du projet horloge-hello dans Memnius-PEE le 2026-10-11 (pull request horloge-hello#1)
- Remplace : —

L'essai d'un projet neuf a montré que l'index écrit par la CI (décision 0017) bloquait la fusion : le commit
poussé avec le jeton du workflow laissait l'exécution `pull_request` « en attente d'approbation », et la
relance par `workflow_dispatch` ne compte pas pour le ruleset. Chaque projet reçoit donc une clé de
déploiement en écriture, dont la clé privée est le secret `MEMNIUS_INDEX_CLE` du projet ; la CI pousse l'index
avec elle, ce qui relance normalement les gardes. Sans ce secret, la CI ne commite rien et demande l'index.
Le workflow d'un projet passe `secrets: inherit` et n'a plus besoin que de `contents: read`.

`publier-projet.sh` publie un projet depuis n'importe quel dossier préparé par `memnius.py init` (le nom du
dépôt est le champ `id`), règle un dépôt existant sans dossier local (`--regler`) et pose la clé. `init`
ajoute CONTRIBUTING.md, que A3 recommande. Les gardes lancées sur un dossier rangé dans un autre dépôt Git
le lisent comme un simple dossier.
