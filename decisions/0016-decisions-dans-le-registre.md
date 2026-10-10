# 0016 — Le journal des décisions passe dans le registre, et les cartes deviennent cliquables

- Date : 2026-10-10
- Origine : [humain] « j'aimerai que les carte de decisions ne soient plus isolé du reste des registre (tout dans le dossier registre) » ; [humain] « quand une carte reference un fichier du depot il faut que l'on puisse y acceder en cliquant dessus (lien) »
- Décidé par : Romain (comité du socle)
- Options écartées : recopier chaque décision en carte dans `registre/` (deux textes à tenir) ; demander aux auteurs d'écrire les liens à la main dans le texte de la carte (ils divergent de l'en-tête)
- Source : projet Claude « Memnius », message de Romain du 2026-10-10
- Remplace : —

Dans un projet, le journal passe de `decisions/` à `registre/decisions/` : tout ce qui décrit le projet est
dans `registre/`, qui compte désormais quatre dossiers (`decisions/`, `code/`, `donnees/`, `sources/`).
Les règles du journal ne changent pas (C2, garde A4) ; un projet le déplace avec `git mv decisions
registre/decisions`, déplacement que A4 accepte. Le dépôt commun, qui n'est pas un projet, garde son
journal dans `decisions/`.

GitHub affiche l'en-tête YAML d'une carte en tableau, sans liens. `memnius.py index` écrit donc, juste
sous l'en-tête, un bloc dérivé où chaque fichier ou adresse de `ou`, `url` et `doi`, et chaque carte de
`liens`, est un lien cliquable. A7 refuse un bloc périmé ou retouché à la main, comme un index périmé.
Les entrées du journal ne sont jamais réécrites. `CARTES.md` du super-registre gagne une colonne « Où »
cliquable.

Le socle reste en v2 : il n'est encore publié que dans l'organisation d'essai.
