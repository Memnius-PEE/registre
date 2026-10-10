# Registre et règles communes du groupe Memnius

Dépôt commun du groupe d'étude Memnius, nommé `registre` dans l'organisation. Il réunit depuis le socle v2
ce qui était auparavant dans deux dépôts (`regles` et l'ancien `registre`, décision 0013) :

- **les règles** que suivent tous les dépôts de projet, et les gardes qui les font respecter ;
- **l'outil commun** `memnius.py`, qui tient le registre de chaque projet (cartes et index) ;
- **le super-registre**, la vue générale de tous les projets, qui pointe vers chacun d'eux.

| Fichier | Contenu |
|---|---|
| [`REGLES.md`](REGLES.md) | texte de référence : C1–C11, A1–A7, R1–R8, O1–O8, registre, journal, passation |
| [`regles.yaml`](regles.yaml) | liste des règles et gardes, lue par la garde A5 |
| [`vocabulaire.yaml`](vocabulaire.yaml) | domaines (liste fermée), outils, versions du socle |
| [`schema/`](schema/) | schémas de `memnius.yaml` (`memnius/2`) et des cartes |
| [`outils/memnius.py`](outils/memnius.py) | cartes, index d'un projet, contrôle d'un projet, super-registre |
| [`outils/gardes.py`](outils/gardes.py) | gardes A2 à A7 (CI et pre-commit) |
| [`modeles/cartes/`](modeles/cartes/) | modèle de chaque type de carte : décision, code, données, sources |
| [`modeles/projet/`](modeles/projet/) | fichiers exigés d'un projet, créés par `memnius.py init` |
| [`tests/`](tests/) | chaque garde testée dans les deux sens, et l'outil |
| [`decisions/`](decisions/) | journal des décisions du socle |
| `.github/workflows/gardes.yml` | workflow réutilisable appelé par chaque projet |
| `.github/workflows/registre.yml` | super-registre reconstruit chaque nuit |
| `.pre-commit-hooks.yaml` | crochets locaux facultatifs (A2 et A6, index du registre) |

## Le registre de chaque projet

Chaque dépôt de projet a un dossier `registre/` de même structure (règle C11, garde A7) : une **carte** par
code, jeu de données ou source notable, qui dit ce que c'est, qui l'a fait et où le trouver. Le journal
des décisions y est aussi, dans `registre/decisions/` : chaque entrée est une carte de décision. Un script
en tire l'index du projet et rend cliquables, dans chaque carte, les fichiers qu'elle cite :

```bash
python3 outils/memnius.py init ../mon-projet --titre "Mon projet" --mainteneur moi   # fichiers exigés, rien n'est remplacé
python3 outils/memnius.py carte code calcul-interfrange --dossier ../mon-projet --ou travaux/interfrange.py --auteur moi
python3 outils/memnius.py index ../mon-projet        # écrit registre/INDEX.md, registre/index.json et les liens des cartes
python3 outils/memnius.py verifier ../mon-projet     # gardes A3 et A7
python3 outils/gardes.py ../mon-projet               # toutes les gardes, comme la CI
```

## Le super-registre

Le workflow `Super-registre` lit chaque nuit la fiche (`memnius.yaml`) et l'index (`registre/index.json`)
de chaque dépôt de l'organisation qui porte le topic **`memnius-projet`**, et publie sur la branche
[`super-registre`](../../tree/super-registre) de ce dépôt :

- `REGISTRE.md` : un tableau des projets (statut, domaines, mainteneur·ices, nombre de cartes par type,
  conformité), chaque projet renvoyant vers son dépôt et son index ;
- `CARTES.md` : toutes les cartes de tous les projets, par type, puis qui a fait quoi, personne par personne ;
- `registre.json` : la même chose pour les machines.

Ces fichiers sont générés : on ne les édite jamais à la main. En local :
`GITHUB_TOKEN=… python3 outils/memnius.py registre --github Memnius-PEE --sortie /tmp/sortie`.

## Versions

Les projets appellent le workflow réutilisable à une étiquette fixe : `.github/workflows/gardes.yml@v2`.
Le comité du socle (pour l'instant Romain seul, décision 0004) valide toute pull request.
