# Toutes les cartes des projets Memnius

_Généré le 2026-10-21T07:46:37+00:00 à partir du `registre/index.json` de chaque projet. Ne pas éditer. Vue par projet : [REGISTRE.md](REGISTRE.md). Chercher un mot dans toutes les cartes : recherche de code GitHub `org:Memnius-PEE path:registre/ le-mot`._

## Décisions (9)

| Projet | Carte | Résumé | Qui |
|---|---|---|---|
| horloge-hello | [0001 — Adopter le socle commun Memnius v2](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/decisions/0001-adopter-le-socle.md) | Le projet suit les règles et les gardes A1–A7 du socle v2, ainsi que les options déclarées dans `memnius.yaml` (`socle.options`). | @Pwouette |
| horloge-hello | [0002 — Page statique sans dépendance](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/decisions/0002-page-statique-sans-dependance.md) | La page est un simple fichier HTML et un script JavaScript, sans bibliothèque ni étape de construction : elle s'ouvre directement dans un navigateur et sert à éprouver le kit Memnius de bout en bout. | @Pwouette |
| horloge-hello | [0003 — Publier la page avec GitHub Pages](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/decisions/0003-publier-avec-github-pages.md) | Le dossier `site/` est publié sur GitHub Pages par le workflow `.github/workflows/pages.yml`, à chaque fusion dans `main` qui le touche : <https://memnius-pee.github.io/horloge-hello/>. Le projet passe aussi au workflow des gardes de la décision 0019 du socle (index poussé par la clé de déploiement… | @Pwouette |
| optique-ondulatoire | [0001 — Adopter le socle commun Memnius v1](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0001-adopter-le-socle.md) (remplacée par 0003) | Le sujet suit les règles C1–C10 et les gardes A1–A6 du socle v1, au niveau `recommande` : des agents y écrivent régulièrement, donc R1–R8 s'appliquent aussi. | @Pwouette |
| optique-ondulatoire | [0002 — Calculs en Python sans dépendance](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0002-calculs-sans-dependance.md) | Les scripts de `travaux/` n'utilisent que la bibliothèque standard tant qu'aucun tracé n'est nécessaire. | @Pwouette |
| optique-ondulatoire | [0003 — Passer au socle v2 et tenir le registre du projet](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0003-passer-au-socle-v2.md) | Le projet suit désormais le socle v2 (règles C1–C11, gardes A1–A7). Chaque script, jeu de données ou source notable a sa carte dans `registre/`, et l'index `registre/INDEX.md` est régénéré à chaque changement. | @Pwouette |
| optique-ondulatoire | [0004 — Ranger le journal des décisions dans le registre](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0004-decisions-dans-le-registre.md) | Le journal passe de `decisions/` à `registre/decisions/`, avec son historique : tout ce qui décrit le projet est dans `registre/`. Les entrées 0001 à 0003 sont déplacées telles quelles ; les chemins `decisions/` qu'elles citent désignent désormais `registre/decisions/`. | @Pwouette |
| optique-ondulatoire | [0005 — Suivre le socle v2 révisé](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0005-socle-v2-revise.md) | Le projet suit le socle v2 révisé. PASSATION.md est retiré : ce qui reste à faire est dans le README, et le piège sur les unités est noté dans la carte `registre/code/interfrange.md`. `memnius.yaml` ne déclare plus de niveau. L'index du registre est désormais écrit par la CI sur chaque pull request… | @Pwouette |
| optique-ondulatoire | [0006 — L'index est poussé par la clé de déploiement du projet](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0006-index-pousse-par-cle.md) | La CI commite l'index du registre avec la clé de déploiement du projet (secret `MEMNIUS_INDEX_CLE`), ce qui relance normalement les gardes sur la pull request. Le workflow `memnius.yml` n'a plus besoin que du droit `contents: read` et transmet ses secrets au workflow commun (`secrets: inherit`) ; l… | @Pwouette |

## Code (2)

| Projet | Carte | Résumé | Qui | Où | Mots-clés |
|---|---|---|---|---|---|
| horloge-hello | [Page horloge et Hello world](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/code/page-horloge.md) (à relire) | Page web statique qui affiche l'heure locale, mise à jour chaque seconde, et écrit « Hello world » quand on clique sur le bouton. | @Pwouette | [`site/index.html`](https://github.com/Memnius-PEE/horloge-hello/blob/main/site/index.html), [`site/horloge.js`](https://github.com/Memnius-PEE/horloge-hello/blob/main/site/horloge.js), [memnius-pee.github.io](https://memnius-pee.github.io/horloge-hello/) |  |
| optique-ondulatoire | [Calcul de l'interfrange des fentes d'Young](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/code/interfrange.md) (à relire) | Calcule l'interfrange i = λD/a des fentes d'Young et affiche l'ordre de grandeur pour un pointeur laser rouge. | @Pwouette | [`travaux/interfrange.py`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/travaux/interfrange.py) | interferences, fentes-young |

## Données (0)

_Aucune carte._

## Sources (2)

| Projet | Carte | Résumé | Qui | Où | Mots-clés |
|---|---|---|---|---|---|
| optique-ondulatoire | [Hecht, Optics (5e édition)](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/hecht-optics.md) (à relire) | Manuel de référence pour l'optique ondulatoire ; le chapitre 9 traite des interférences et des fentes d'Young. | @Pwouette | [`sources/references.bib`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/sources/references.bib) |  |
| optique-ondulatoire | [Cours d'optique ondulatoire (Wikiversité)](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/wikiversite-optique.md) (à relire) | Cours d'introduction en ligne, libre, utile pour les contributeur·ices qui découvrent le sujet. | @Pwouette | [`sources/liens.md`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/sources/liens.md), [fr.wikiversity.org](https://fr.wikiversity.org/wiki/Optique_ondulatoire) |  |

## Documents (2)

| Projet | Carte | Résumé | Qui | Où | Mots-clés |
|---|---|---|---|---|---|
| horloge-hello | [Mode d'emploi de la page](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/documents/mode-d-emploi.md) (à relire) | Explique en trois étapes comment ouvrir la page et ce qu'elle fait, pour quelqu'un qui découvre le projet. | @Pwouette | [`docs/mode-d-emploi.md`](https://github.com/Memnius-PEE/horloge-hello/blob/main/docs/mode-d-emploi.md) |  |
| optique-ondulatoire | [Note sur les fentes d'Young](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/documents/fentes-young.md) (à relire) | Rappelle le montage des fentes d'Young et la formule de l'interfrange i = λD/a, avec un ordre de grandeur pour un pointeur laser rouge. | @Pwouette | [`notes/fentes-young.md`](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/notes/fentes-young.md) | interferences, fentes-young |

## Qui a fait quoi

| Personne | Projet | Décisions | Code | Données | Sources | Documents |
|---|---|---|---|---|---|---|
| @Pwouette | horloge-hello | [0001](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/decisions/0001-adopter-le-socle.md), [0002](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/decisions/0002-page-statique-sans-dependance.md), [0003](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/decisions/0003-publier-avec-github-pages.md) | [page-horloge](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/code/page-horloge.md) |  |  | [mode-d-emploi](https://github.com/Memnius-PEE/horloge-hello/blob/main/registre/documents/mode-d-emploi.md) |
| @Pwouette | optique-ondulatoire | [0001](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0001-adopter-le-socle.md), [0002](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0002-calculs-sans-dependance.md), [0003](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0003-passer-au-socle-v2.md), [0004](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0004-decisions-dans-le-registre.md), [0005](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0005-socle-v2-revise.md), [0006](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/decisions/0006-index-pousse-par-cle.md) | [interfrange](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/code/interfrange.md) |  | [hecht-optics](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/hecht-optics.md), [wikiversite-optique](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/sources/wikiversite-optique.md) | [fentes-young](https://github.com/Memnius-PEE/optique-ondulatoire/blob/main/registre/documents/fentes-young.md) |
