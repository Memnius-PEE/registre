# 0015 — Plus de dépôt gabarit : des modèles de cartes et un script d'entrée

- Date : 2026-10-10
- Origine : [humain] « on peux laisser tomber le gabarit des projet, on ne garde que les gabarit sur les cartes » ; [choix] « Registre et règles » : on exige toujours les fichiers de la garde A3, créés par un script
- Décidé par : Romain (comité du socle)
- Options écartées : garder le dépôt gabarit (« Use this template ») ; n'exiger que le dossier registre/ et faire des décisions des cartes comme les autres
- Source : projet Claude « Memnius », messages de Romain du 2026-10-10
- Remplace : —

Le dépôt `gabarit` et son arborescence imposée (`docs/`, `notes/`, `travaux/`, `donnees/`, `sources/`,
`livrables/`…) disparaissent : chaque projet garde son organisation. Le socle fournit à la place :

- un modèle par type de carte, dans `modeles/cartes/` (décision, code, données, sources), que
  `memnius.py carte` copie et pré-remplit ;
- les fichiers exigés d'un projet, dans `modeles/projet/` : README.md, AGENTS.md, CLAUDE.md, `memnius.yaml`,
  PASSATION.md, `decisions/0001`, `registre/README.md` et le workflow des gardes. `memnius.py init` les
  ajoute à un dépôt sans jamais remplacer un fichier existant.

Les gardes A3 et A7 ne changent pas : elles vérifient toujours ces fichiers et le registre.
