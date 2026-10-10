# Toutes les cartes des projets Memnius

_Généré le 2026-10-10T21:43:10+00:00 à partir du `registre/index.json` de chaque projet. Ne pas éditer. Vue par projet : [REGISTRE.md](REGISTRE.md)._

## Décisions (4)

| Projet | Carte | Résumé | Qui |
|---|---|---|---|
| optique-ondulatoire | [0001 — Adopter le socle commun Memnius v1](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0001-adopter-le-socle.md) | Le sujet suit les règles C1–C10 et les gardes A1–A6 du socle v1, au niveau `recommande` : des agents y écrivent régulièrement, donc R1–R8 s'appliquent aussi. | @Pwouette |
| optique-ondulatoire | [0002 — Calculs en Python sans dépendance](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0002-calculs-sans-dependance.md) | Les scripts de `travaux/` n'utilisent que la bibliothèque standard tant qu'aucun tracé n'est nécessaire. | @Pwouette |
| optique-ondulatoire | [0003 — Passer au socle v2 et tenir le registre du projet](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0003-passer-au-socle-v2.md) | Le projet suit désormais le socle v2 (règles C1–C11, gardes A1–A7). Chaque script, jeu de données ou source notable a sa carte dans `registre/`, et l'index `registre/INDEX.md` est régénéré à chaque changement. | @Pwouette |
| optique-ondulatoire | [0004 — Ranger le journal des décisions dans le registre](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0004-decisions-dans-le-registre.md) | Le journal passe de `decisions/` à `registre/decisions/`, avec son historique : tout ce qui décrit le projet est dans `registre/`. Les entrées 0001 à 0003 sont déplacées telles quelles ; les chemins `decisions/` qu'elles citent désignent désormais `registre/decisions/`. | @Pwouette |

## Code (1)

| Projet | Carte | Résumé | Qui | Où |
|---|---|---|---|---|
| optique-ondulatoire | [Calcul de l'interfrange des fentes d'Young](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/code/interfrange.md) | Calcule l'interfrange i = λD/a des fentes d'Young et affiche l'ordre de grandeur pour un pointeur laser rouge. | @Pwouette | [`travaux/interfrange.py`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/travaux/interfrange.py) |

## Données (0)

_Aucune carte._

## Sources (2)

| Projet | Carte | Résumé | Qui | Où |
|---|---|---|---|---|
| optique-ondulatoire | [Hecht, Optics (5e édition)](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/hecht-optics.md) | Manuel de référence pour l'optique ondulatoire ; le chapitre 9 traite des interférences et des fentes d'Young. | @Pwouette | [`sources/references.bib`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/sources/references.bib) |
| optique-ondulatoire | [Cours d'optique ondulatoire (Wikiversité)](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/wikiversite-optique.md) | Cours d'introduction en ligne, libre, utile pour les contributeur·ices qui découvrent le sujet. | @Pwouette | [`sources/liens.md`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/sources/liens.md), [fr.wikiversity.org](https://fr.wikiversity.org/wiki/Optique_ondulatoire) |

## Qui a fait quoi

| Personne | Projet | Décisions | Code | Données | Sources |
|---|---|---|---|---|---|
| @Pwouette | optique-ondulatoire | [0001](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0001-adopter-le-socle.md), [0002](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0002-calculs-sans-dependance.md), [0003](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0003-passer-au-socle-v2.md), [0004](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0004-decisions-dans-le-registre.md) | [interfrange](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/code/interfrange.md) |  | [hecht-optics](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/hecht-optics.md), [wikiversite-optique](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/wikiversite-optique.md) |
