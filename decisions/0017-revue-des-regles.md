# 0017 — Revue des règles du socle : allègement, index écrit par la CI

- Date : 2026-10-10
- Origine : [humain] « certaines regles/options doivent etre modifiés/suprimer. Nous allons les revoir une a une avec l'outil de questions » ; [choix] 24 options choisies une à une sur des cartes de décision rédigées par un agent (Claude)
- Décidé par : Romain (comité du socle)
- Options écartées : voir le détail ci-dessous, point par point
- Source : projet Claude « Memnius », fil « revue de REGLES.md » du 2026-10-10 ; relevé des choix dans le dossier partagé du projet (`regles-revue/choix.md`)
- Remplace : —

Gardé sans changement : les cinq principes, l'interdiction de déroger au socle (un projet ajoute des
règles, n'en retire aucune), C1, C4, C7, C10, les gardes A2 et A5, les options O1–O8.

Changé :

- **C2 et A4** : une entrée publiée du journal peut être corrigée sur place pour une coquille, si chaque
  commit qui la touche dit « coquille » dans son message et que `Date`, `Origine` et `Décidé par` restent
  identiques. Écarté : garder l'interdiction totale ; abroger le journal.
- **C3** : le comité du socle compte d'une à trois personnes (il n'en compte qu'une aujourd'hui).
  Écarté : laisser chaque projet choisir son mainteneur ; abroger.
- **C5** : la règle ne vise plus que les livrables, les cartes du registre et le journal ; les notes de
  travail en sont dispensées. Écarté : garder pour tout document ; abroger.
- **C11** : l'index du registre et les blocs de liens des cartes sont écrits par la CI, qui les commite sur
  la branche de chaque pull request du dépôt (pas pour une pull request venant d'une copie), puis relance
  les gardes ; A7 ne vérifie plus que les cartes. Écarté : index commité par le contributeur ; index
  publié sur une branche à part ; pas d'index dans les projets.
- **A1** : le ruleset de `main` exige une pull request et des gardes vertes, sans approbation (suite de
  l'abrogation de C6) ; un dépôt privé sans ruleset reste un simple avertissement.
- **A3** : PASSATION.md n'est plus exigé ; `memnius.yaml` n'exige plus que `schema`, `id`, `titre`,
  `resume`, `langue`, `mainteneurs`, `socle` et `visibilite`. Écarté : rendre AGENTS.md facultatif.
- **A6** : seuil gardé à 10 Mo, mais Git LFS n'est plus une échappatoire : la garde mesure le fichier
  désigné par un pointeur LFS. Un gros fichier va dans le drive commun (décision 0011). Écarté : seuils de
  5 Mo ou 50 Mo.
- **Niveaux** : le champ `socle.niveau` disparaît ; un projet déclare `socle.version` et ses options.

Abrogé (numéros réservés, `abrogee: true` dans `regles.yaml`) :

- **C6** Second regard ; **C8** Dans le doute, on demande ; **C9** Passation en fin de session. Le rituel
  de passation, le modèle PASSATION.md et les PASSATION.md existants sont retirés.
- **R1–R8**, les règles recommandées pour les dépôts à agents.

La garde A5 accepte désormais qu'une entrée du journal, ou une ligne qui dit qu'une règle est abrogée,
cite une règle abrogée : sans cela, une ancienne entrée qui cite R1–R8 ne pourrait plus passer, et elle ne
peut pas être modifiée.

Ces changements ne sont pas compatibles avec les projets en v2 (champ `niveau`, PASSATION.md, workflow).
Choix de Romain : pas de v3, l'étiquette `v2` est déplacée sur ce socle, et le seul projet existant
(optique-ondulatoire) est mis à jour dans la même opération.
