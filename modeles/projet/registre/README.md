# Registre du projet

Ce dossier a la même structure dans tous les projets du groupe (règle C11, vérifiée par la garde A7).
Il dit **ce que contient le projet, qui l'a fait et où le trouver**, en une carte par élément notable.

| Dossier ou fichier | Contenu |
|---|---|
| [`decisions/`](decisions/) | le journal des décisions : une entrée par décision structurante, jamais modifiée une fois publiée (C2) ; ce sont les cartes de décision |
| `code/` | une carte par script, notebook, programme ou bibliothèque |
| `donnees/` | une carte par jeu de données (dans le dépôt ou rangé ailleurs, par exemple sur le drive) |
| `sources/` | une carte par référence importante (livre, article, site, cours) |
| `documents/` | une carte par document écrit dans le projet : note, synthèse, compte rendu, exposé, livrable (dossier facultatif) |
| [`INDEX.md`](INDEX.md) | index de toutes les cartes, **généré par la CI après chaque fusion** : ne pas l'éditer à la main |
| `index.json` | le même index pour les machines, lu par le super-registre du groupe |

Tout ce qui décrit le projet est ici, décisions comprises : l'index reprend telles quelles les entrées
du journal `decisions/`, et les cartes des autres dossiers.

## Une carte

Un fichier Markdown nommé en minuscules-avec-tirets (`code/calcul-interfrange.md`), qui commence par un
en-tête entre deux lignes `---`, suivi de notes libres :

```markdown
---
titre: Calcul de l'interfrange
resume: >-
  Calcule l'interfrange des fentes d'Young (i = λD/a) et affiche un ordre de grandeur.
ou: [travaux/interfrange.py]        # chemin dans le dépôt, https://… ou drive:/…
auteurs: [Pwouette]                 # identifiants GitHub de qui l'a fait
date: 2026-09-26
statut: valide                      # brouillon | a-relire | valide | obsolete
liens: [sources/hecht-optics, decisions/0002]
langage: python
commande: python3 travaux/interfrange.py
---

Notes libres : comment s'en servir, limites, ce qui reste à faire.
```

GitHub affiche l'en-tête en tableau, sans liens. L'outil ajoute donc juste dessous un bloc qu'il tient
lui-même à jour, où chaque fichier de `ou`, chaque adresse (`url`, `doi`) et chaque carte de `liens` est
cliquable. On ne l'édite pas : on modifie l'en-tête, et la CI remet le bloc à jour après la fusion.

Obligatoires : `titre`, `resume`, `ou`, `auteurs` (qui l'a fait ; pour une source, qui l'a apportée au projet), `date`. Facultatifs : `contributeurs`, `mis_a_jour`,
`statut`, `mots_cles`, `liens` (vers une autre carte, ou `autre-projet:code/nom` vers un autre projet), et selon
le type : `langage`, `commande` (code) ; `format`, `licence`, `taille`, `empreinte` (données) ;
`reference`, `cle_bib`, `doi`, `url` (sources) ; `format` (genre du document : note, synthèse, exposé,
livrable…) et `doi` (documents). Une carte écrite par un agent porte `statut: a-relire`
tant qu'une personne ne l'a pas relue. `auteurs` donne des identifiants GitHub exacts : le super-registre
signale ceux qui n'existent pas.

## Mettre à jour

Chaque type de carte a son modèle, dans le dossier `modeles/cartes/` du dépôt commun `registre` de
l'organisation (étiquette `v2`). L'outil commun copie le bon modèle et le pré-remplit :

```bash
python3 ../registre/outils/memnius.py carte code calcul-interfrange --ou travaux/interfrange.py --auteur moi
python3 ../registre/outils/memnius.py carte decision choix-du-format --auteur moi   # registre/decisions/NNNN-choix-du-format.md
python3 ../registre/outils/memnius.py index      # facultatif : la CI le fait après chaque fusion
```

On remplace ensuite les « À_REMPLIR » : les gardes refusent une carte ou une décision qui en contient encore.

La garde A7 refuse une pull request si une carte est mal formée ou si elle renvoie vers un fichier qui
n'existe pas. L'index et les liens des cartes sont régénérés par la CI sur `main` après chaque fusion
(règle C11) : une pull request n'y touche pas. A7 signale, sans bloquer, les fichiers qu'aucune carte ne décrit : par défaut tout
fichier rangé dans un dossier, hors `registre/` et dossiers cachés ; un projet peut restreindre la liste dans
`memnius.yaml` (`registre: {a_couvrir: [analyses/, site/]}`). Une carte de données rangées hors du dépôt
(`https://…`, `drive:/…`) porte leur `empreinte` (`sha256:…`, donnée par `sha256sum fichier`).
