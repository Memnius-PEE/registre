# 0012 — Abandonner l'archiviste local jusqu'à nouvel ordre

- Date : 2026-10-10
- Origine : [humain] « on laisse tombé l'archiviste local pour l'instant (et jusqu'a nouvel ordre) »
- Décidé par : Romain (comité du socle), après présentation au groupe d'étude
- Options écartées : poursuivre la phase prospective de l'archiviste
- Source : projet Claude « Memnius », message de Romain du 2026-10-10
- Remplace : 0009

Le kit ne réserve plus rien pour l'archiviste : plus de dépôt `archives`, plus de bloc `archiviste` dans
le registre, plus de champ `archivage` dans `memnius.yaml` (schéma `memnius/2`). Le drive commun de 0011
reste à l'étude, mais sa partie liée à l'archiviste (nœud et modèle LocalAI sur le serveur, scellés,
dossier `/archives/`) est suspendue avec lui. L'étude de l'archiviste reste lisible dans l'historique Git
et dans le dossier `historique/` du dépôt de travail du kit.
