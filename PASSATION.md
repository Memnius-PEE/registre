# Passation — 2026-10-10 — rédigée par un agent (Claude), vérifiée par : —

## 0. En une phrase *
Socle v2 prêt à publier : dépôts `regles` et `registre` fusionnés, registre par projet (cartes et index, garde A7) et super-registre ; aucune étiquette v2 posée tant que le dépôt n'est pas dans l'organisation.

## 1. État mesuré *
Tests lancés hors GitHub, dans le kit (dépôt de travail Pwouette/Memnius), le 2026-10-10 :
`python3 -m unittest discover -s tests` → 53 tests, OK.
À re-mesurer après la publication avec `python3 -m unittest discover -s tests -v`.

## 3. Décisions prises (numéros du journal)
0001 à 0011 : socle v1 (2026-09-26 et 2026-10-01).
0012 : archiviste abandonné jusqu'à nouvel ordre. 0013 : fusion de `regles` et `registre`. 0014 : registre par projet, cartes, index et super-registre (socle v2). 0015 : plus de dépôt gabarit, des modèles de cartes et `memnius.py init`.

## 5. Ce qui reste dû ou en cours *
1. Publier ce dépôt dans l'organisation GitHub du groupe (nom à confirmer) et poser l'étiquette v2.
2. Faire valider par le comité le format des cartes proposé dans 0014.
3. Faire entrer les projets existants de l'organisation (fiche, registre, workflow, topic `memnius-projet`).
4. Ajouter un ou deux membres au comité du socle (0004).

## 7. Ce qui n'a PAS été vérifié *
- Les workflows GitHub Actions (gardes, gitleaks, tests, super-registre) n'ont pas tourné sur GitHub en v2.
- La publication du super-registre sur la branche `super-registre` n'a été essayée que contre un dépôt Git local.
- La garde A5 ne vérifie que les renvois nommés (C3, R5…), pas les phrases qui comptent les règles.
