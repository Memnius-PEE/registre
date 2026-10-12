# Consignes pour les agents IA : dépôt commun registre (règles et super-registre)

Ce dépôt contient les règles communes à tous les projets Memnius (`REGLES.md`), leur liste
(`regles.yaml`), l'outil commun (`outils/memnius.py` : cartes, index, super-registre), les gardes
automatiques (`outils/gardes.py`) et leurs tests (`tests/`).

- Les règles appartiennent au comité du socle (C3). Tu peux proposer, par une pull request
  sur une branche à toi ; tu ne fusionnes jamais toi-même.
- Toute modification d'une règle, d'une garde ou du format des cartes commence par une nouvelle entrée de `decisions/` (C2).
- Une règle retirée n'est jamais supprimée de `regles.yaml` : elle passe à `abrogee: true`.
- Toute garde modifiée garde ses deux tests (cas sain accepté, cas fautif refusé) et `python3 -m unittest discover -s tests` reste vert.
- L'index d'un projet ne porte aucune date de génération : les mêmes cartes doivent toujours donner le même index, sinon la CI commiterait un nouvel index à chaque pull request.
- Les fichiers du super-registre (`REGISTRE.md`, `CARTES.md`, `registre.json`) vivent sur la branche `super-registre` et ne s'éditent jamais à la main. Ils sont publics : un projet privé n'y figure jamais, et toute sortie publique nouvelle passe par `public()` avec un test.
- Ne touche jamais aux workflows pour « réparer » une CI rouge, et n'ajoute jamais l'environnement `super-registre` à un job déclenché par une pull request.
- Commits terminés par `Assisted-by: <outil> (<modèle>)` (C4) ; réponse dans la langue de ton interlocuteur (C10).
