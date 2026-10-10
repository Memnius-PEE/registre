# 0014 — Un registre par projet, fait de cartes, et un super-registre (socle v2)

- Date : 2026-10-10
- Origine : [humain] « chaque depot de projet doit avoir son propre registre, ils doivent tous avoir une structure identique (regle). Le "super" registre permet lui d'avoir une vue generale et pointe vers les different depot de projets. Les registres doivent contenir des "cartes" qui synthetise le contenue (carte pour decisions, code, données, source) et dire qui a fait quoi et ou trouver. a partir de ces cartes, un script genere un index » ; [agent] format des cartes et emplacement de l'index proposés dans la pull request du kit, à valider par le comité
- Décidé par : Romain (comité du socle)
- Options écartées : un registre central unique tenu à la main ; un index sans cartes, déduit seulement de Git
- Source : projet Claude « Memnius », message de Romain du 2026-10-10 ; dépôt de travail Pwouette/Memnius
- Remplace : —

Socle v2 : règle C11 (registre du projet tenu à jour) et garde A7 (registre du projet).

- Chaque projet a un dossier `registre/` de structure identique : `code/`, `donnees/`, `sources/`,
  `README.md`, et l'index généré `INDEX.md` et `index.json`.
- Une carte est un fichier Markdown dont l'en-tête YAML donne au moins `titre`, `resume`, `ou`
  (où le trouver), `auteurs` (qui l'a fait) et `date` (`schema/carte.schema.json`).
- Les cartes de décision sont les entrées du journal `decisions/`, lues par l'index sans recopie.
- `outils/memnius.py index` génère l'index ; il est commité avec les cartes et la garde A7 refuse un
  index périmé, une carte mal formée ou un emplacement qui n'existe pas.
- Le super-registre de ce dépôt lit chaque nuit la fiche et l'index de chaque projet et publie la vue
  générale (`REGISTRE.md`, `CARTES.md`, `registre.json`) sur sa branche `super-registre`.
