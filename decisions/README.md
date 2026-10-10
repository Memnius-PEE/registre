# Journal de décisions

Une décision par fichier, numérotée sur quatre chiffres : `0001.md`, `0002-choix-du-format.md`…
Ajouter une décision ne modifie jamais un fichier existant ; pour corriger, on écrit une nouvelle
entrée dont le champ `Remplace` pointe vers l'ancienne (règle C2, vérifiée par la garde A4).

```markdown
# 0002 — Titre de la décision

- Date : 2026-09-26
- Origine : [humain] « les mots tapés par la personne » | [choix] option d'agent choisie par une personne | [agent] déduction d'agent
- Décidé par : @mainteneur
- Options écartées : …
- Source : pull request #12, commit abc1234
- Remplace : —
```

`Date`, `Origine` et `Décidé par` sont obligatoires. Dans le doute sur l'origine, écrire `[agent]`.
