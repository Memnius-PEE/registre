# 0013 — Fusionner les dépôts regles et registre

- Date : 2026-10-10
- Origine : [humain] « on garde l'idée du depot de registre et on le fusionne avec celui de regles » ; « il existe deja un depot d'orgaisation github sur lequel les projet du groupe d'étude existe, nous allons y ajouter le depot de registre/regles » ; [choix] nom `registre`, choisi par Romain parmi memnius, registre et socle
- Décidé par : Romain (comité du socle)
- Options écartées : garder deux dépôts séparés ; nommer le dépôt commun memnius ou socle ; créer une nouvelle organisation (Memnius-PEE reste un banc d'essai)
- Source : projet Claude « Memnius », message de Romain du 2026-10-10
- Remplace : —

Un seul dépôt commun, `registre`, réunit les règles, les gardes, l'outil `memnius.py` et le
super-registre. Il est ajouté à l'organisation GitHub existante du groupe d'étude, à côté des projets.
Les projets n'ont plus qu'un dépôt à cloner pour leurs gardes (workflow réutilisable
`registre/.github/workflows/gardes.yml@v2`). Les décisions 0001 à 0011 du dépôt `regles` sont reprises
telles quelles, sans modification. Le vocabulaire « sujet » devient « projet » (topic `memnius-projet`).
