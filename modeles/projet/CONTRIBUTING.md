# Contribuer

Ce dépôt fait partie du groupe d'étude Memnius. Les règles communes à tous les projets
sont décrites dans <https://github.com/Memnius-PEE/registre> ; voici l'essentiel.

## Selon votre implication

| Vous êtes… | Vous pouvez… | Comment |
|---|---|---|
| **De passage** | signaler, commenter, proposer | ouvrir un ticket, commenter une pull request |
| **Contributeur·ice occasionnel·le** | corriger, ajouter une note | bouton « crayon » de GitHub → pull request ; aucun outil à installer |
| **Contributeur·ice régulier·e** | travailler sur des branches | rôle *Write* ; branches `<pseudo>/<objet>` |
| **Mainteneur·ice** | fusionner, trier, tenir le README à jour | rôle *Maintain* ; un par projet, nommé par le comité du socle |

## Règles minimales

- `main` est protégée : tout passe par une pull request, fusionnée quand les gardes sont vertes.
- Avant de commencer, lisez le README et `AGENTS.md`.
- Une décision qui engage le projet s'écrit dans un nouveau fichier de `registre/decisions/` ; on ne modifie jamais une décision publiée, sauf pour corriger une coquille (message de commit contenant « coquille »).
- Écrivez dans la langue du dépôt (champ `langue` de `memnius.yaml`) ; noms de fichiers en minuscules, sans accents ni espaces (`mon-fichier.md`).
- Travail fait avec un agent IA : ajoutez `Assisted-by: <outil>` au message de commit.
- Fichiers de plus de 10 Mo : refusés par la CI (garde A6), même suivis par Git LFS ; ils vont dans le drive commun, décrits par une carte de `registre/donnees/`.
- Vous ajoutez un script, un jeu de données ou une source importante : ajoutez sa carte dans `registre/` (voir [`registre/README.md`](registre/README.md)) ; la CI régénère l'index. Si vous ne savez pas faire, dites-le dans la pull request : un·e mainteneur·ice s'en chargera.
- Pas de secrets, pas de données personnelles.
