# Registre unifié Memnius

`REGISTRE.md` (lecture humaine) et `registre.json` (machines, archiviste) sont **générés** chaque nuit
à partir du `memnius.yaml` de chaque sujet et des faits GitHub. On ne les édite jamais à la main :
pour changer une ligne, on modifie le `memnius.yaml` du sujet.

Un dépôt de l'organisation est un sujet s'il porte le topic GitHub **`memnius-sujet`**.

| Fichier | Rôle | Édité par |
|---|---|---|
| `vocabulaire.yaml` | domaines (liste fermée), outils, versions du socle | le comité, par pull request |
| `schema/memnius.schema.json` | schéma de la fiche `memnius.yaml` (`memnius/1`) | le comité |
| `schema/registre.schema.json` | schéma du registre (`memnius-registre/1`) | le comité |
| `outils/memnius.py` | `verifier` (contrôle d'un sujet, garde A3) et `construire` | le comité |
| `registre.json`, `REGISTRE.md` | registre généré | le workflow `Registre` seulement |

Chaque entrée a quatre blocs : `fiche` (déclaré par le sujet), `depot` et `conformite` (calculés,
dont la garde A1 : `depot.branche_protegee`), `archiviste` (réservé à l'archiviste, recopié depuis
`Memnius-PEE/archives/etat.json`).

```bash
python3 outils/memnius.py verifier ../mon-sujet
python3 outils/memnius.py construire --local ../sujets --sortie /tmp/registre
GITHUB_TOKEN=… python3 outils/memnius.py construire --github memnius --sortie /tmp/registre
```
