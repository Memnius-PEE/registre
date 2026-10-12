# 0021 — Index écrit après la fusion, et cartes de documents

- Date : 2026-10-11
- Origine : [choix] « Après la fusion », sur la carte « Quand la CI doit-elle écrire l'index du registre d'un projet ? » ; [choix] « Type documents », sur la carte « Ajouter un type de carte pour les notes, documents et livrables ? » (cartes rédigées par un agent, Claude)
- Décidé par : Romain (comité du socle)
- Options écartées : index publié par le super-registre, plus d'index dans les projets ; garder l'index commité dans chaque pull request en ajoutant un contrôle sur main ; deux types « notes » et « livrables » ; aucun type de plus
- Source : projet Claude « Memnius », fil « Corrections des audits » ; rapports `audit/audit-opus.md` (H2, M4) et `audit/audit-fable.md` (M2, M7)
- Remplace : 0017, pour le seul point C11 (index commité sur la branche de chaque pull request) ; 0019, pour l'usage de la clé de déploiement de l'index

**Index.** Les audits ont montré que l'index commité dans chaque pull request fait entrer en conflit deux pull
requests qui ajoutent chacune une carte, n'indexe jamais une pull request venue d'une copie (fork), et laisse
l'index de `main` sans contrôle. La CI régénère donc l'index et les blocs de liens après chaque fusion, sur le
push vers `main`, et les pousse avec la clé de déploiement du projet. Le ruleset de `main` dispense les clés de
déploiement (`actor_type: DeployKey`, seule la CI en détient une en écriture). La clé privée devient le secret
`MEMNIUS_INDEX_CLE` de l'environnement `index` du projet, réservé à `main` : une branche ne peut plus la lire.
Une pull request ne touche jamais l'index ; A7 continue de vérifier les cartes. `publier-projet.sh --regler`
met le ruleset à jour, crée l'environnement et remplace la clé.

**Documents.** Un groupe d'étude produit surtout des textes. Un cinquième type de carte, `documents`, décrit
une note, une synthèse, un compte rendu, un exposé, un cours ou un livrable, avec les champs facultatifs
`format` (le genre du document) et `doi`. Le dossier `registre/documents/` est facultatif : les projets
d'avant restent conformes sans changement, et la révision reste dans `v2`.
