# 0010 — Forge : GitHub remplace GitLab.com

- Date : 2026-09-26
- Origine : [choix] option « Nouvelle forge : GitHub remplace GitLab.com », choisie par Romain
- Décidé par : Romain (comité du socle)
- Options écartées : garder GitLab.com et utiliser le dépôt GitHub comme simple copie de travail
- Source : projet Claude « Memnius », fil « construire le kit »
- Remplace : 0002

Tous les dépôts vivent sur GitHub, dans une organisation. La CI devient GitHub Actions (workflow
réutilisable du dépôt regles), A1 devient un ruleset sur `main`, le gabarit un dépôt modèle, et un
dépôt de sujet se reconnaît au topic `memnius-sujet`.
