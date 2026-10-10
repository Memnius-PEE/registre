# 0011 — Drive commun sur un serveur dédié avec GPU

- Date : 2026-10-01
- Origine : [choix] options « Nextcloud », « Manifeste simple » et « Serveur avec GPU », choisies par Romain
- Décidé par : Romain (comité du socle)
- Options écartées : Seafile, stockage objet S3 seul ; DVC imposé à tous ; nœud archiviste sur le serveur avec le modèle sur le poste de Romain, archiviste entièrement sur le poste de Romain
- Source : projet Claude « Memnius », fil « drive partagé », document « Memnius : drive partagé et dépôts Git »
- Remplace : —

Git reste la source de vérité ; un drive Nextcloud, hébergé sur un serveur commun dédié avec GPU,
reçoit les fichiers que la garde A6 refuse (plus de 10 Mo, voir 0003), les données brutes, les
sources sous droits, les dépôts libres des contributeurs occasionnels et les scellés de l'archiviste.
L'arborescence suit le registre : `/sujets/<id>/`, `/communs/`, `/archives/` (réservé à l'archiviste).

Un sujet référence ses fichiers du drive dans un manifeste `donnees/drive.yaml` (chemin, empreinte
SHA-256, taille, licence, accès), modifié par PR comme le reste ; DVC reste une option par sujet.
Le registre ne lit que les manifestes, l'archiviste lit Git et le drive. Les droits du drive se
déduisent de GitHub (connexion par compte GitHub, groupes recopiés depuis `memnius.yaml`).

Le même serveur porte le nœud archiviste et son modèle (LocalAI), ce qui complète 0009. Phase
d'étude : aucun serveur n'est loué tant que le schéma du manifeste et l'outil `memnius drive`
n'ont pas été testés sur le poste de Romain.
