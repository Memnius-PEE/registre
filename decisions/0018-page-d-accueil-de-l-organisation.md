# 0018 — Une page d'accueil pour l'organisation, réécrite chaque nuit

- Date : 2026-10-10
- Origine : [humain] « est ce possible sur une organisation github d'avoir un readme "general" ? » ; [humain] « afficher les "derniere modification" mais surtout indiquer au devs ou trouver les regles, leur faire une breves description des regles fondamentales et un rappel de "LIRE LE MANUEL!" » ; [agent] contenu des « dernières modifications », clé de déploiement, projets privés exclus
- Décidé par : Romain (comité du socle)
- Options écartées : un README écrit à la main dans `.github` (le résumé des règles et la liste divergent du socle) ; donner à l'App `memnius-registre` l'écriture sur toute l'organisation (elle reste en lecture seule, décision 0007) ; un jeton personnel (lié à une personne, il expire) ; un dépôt `.github-private` visible des seuls membres (les nouveaux venus et les contributeurs occasionnels ne le verraient pas)
- Source : projet Claude « Memnius », messages de Romain du 2026-10-10
- Remplace : —

L'organisation a un dépôt public `.github` dont GitHub affiche `profile/README.md` en haut de la page de
l'organisation, au-dessus de la liste des dépôts. Cette page dit aux contributeurs où trouver les règles
(`REGLES.md` de ce dépôt), résume les règles fondamentales en vigueur et rappelle « LIRE LE MANUEL ! »,
puis liste les dix dernières cartes et décisions ajoutées ou modifiées dans les registres des projets.

La partie fixe est `modeles/accueil.md` de ce dépôt : elle se modifie par pull request, comme les règles
qu'elle résume. Le workflow « Super-registre » complète chaque nuit la partie « Dernières modifications »
à partir de l'historique Git du dossier `registre/` de chaque projet (commits de robots, fusions, index et
README exclus), écrit le résultat dans `ACCUEIL.md` de sa branche `super-registre` et le pousse dans
`.github`. La page étant publique, un projet privé, réellement ou par sa fiche, n'y figure jamais (C7).

Le jeton du workflow n'écrit que dans ce dépôt : il pousse dans `.github` avec une clé de déploiement qui
n'a d'écriture que sur ce dépôt-là (secret `MEMNIUS_ACCUEIL_CLE`), créée par `creer-accueil.sh` du kit.
`.github` n'a pas de ruleset : tout son contenu est généré, et une retouche à la main serait effacée la
nuit suivante.
