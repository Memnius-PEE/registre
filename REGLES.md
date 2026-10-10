# Règles et garde-fous communs Memnius — socle v2

Tous les dépôts de projet partagent un socle court de 11 règles (C1–C11) et 7 gardes automatiques
(A1–A7). Les règles R1–R8 sont recommandées dès que des agents écrivent régulièrement dans un dépôt ;
les options O1–O8 forment un régime renforcé qu'un dépôt adopte par une entrée de son journal.

Un dépôt déclare dans `memnius.yaml` la version du socle qu'il suit et son niveau
(`socle.version`, `socle.niveau`, `socle.options`). Il peut ajouter ses propres règles, jamais retirer
une règle du socle. En cas de conflit entre un dépôt et ce fichier, ce fichier l'emporte.

Les règles sont numérotées une fois pour toutes : une règle retirée garde son numéro, marqué
« abrogée » dans `regles.yaml`, pour que les renvois anciens restent justes.

## Principes

1. **Les garde-fous protègent contre l'inattention, pas contre l'intention.** Une garde rattrape l'oubli
   d'un humain fatigué ou d'un agent pressé ; elle n'arrête pas quelqu'un de décidé à la contourner.
2. **Une décision non écrite n'est pas une décision.** Ce qui n'est pas dans le journal du dépôt n'existe
   pas pour le contributeur ou l'agent suivant.
3. **Les humains décident, les agents proposent.** Tout texte dit d'où il vient : d'un humain ou d'un agent.
4. **L'histoire ne se réécrit pas.** On corrige en ajoutant, jamais en effaçant.
5. **On rapporte ce qu'on a vu, pas ce qu'on attendait.** Un chiffre porte sa source ; un état se
   mesure avant d'être transmis.

Une garde qui reste verte parce qu'elle ne vérifie rien est pire qu'une garde absente : chaque garde
de ce dépôt est testée dans les deux sens (`tests/`), elle doit refuser un cas fautif et accepter un cas sain.

## Règles obligatoires (C1–C11)

| Règle | Énoncé |
|---|---|
| **C1 Histoire en ajout seul** | Sur la branche principale, on ne réécrit jamais l'histoire : ni force-push, ni rebase, ni amend d'un commit publié. Une erreur se corrige par un nouveau commit. |
| **C2 Décision écrite** | Toute décision qui engage le dépôt (méthode, périmètre, choix d'outil, règle) est une entrée datée du journal `registre/decisions/`. Une entrée publiée n'est jamais modifiée ; on la corrige par une nouvelle entrée. |
| **C3 Les règles appartiennent aux mainteneurs** | Seuls les mainteneurs déclarés créent, modifient ou suppriment une règle : un comité de deux ou trois personnes pour le socle, et pour chaque dépôt un mainteneur nommé par ce comité. Les agents et les autres contributeurs proposent, par une demande de fusion. |
| **C4 Origine marquée** | Chaque entrée du journal dit qui parle : `[humain]` pour les mots tapés par une personne, `[choix]` pour une option rédigée par un agent et choisie par une personne, `[agent]` pour une déduction d'agent. Un commit fait avec un agent le déclare par la ligne `Assisted-by: <outil> (<modèle>)`. |
| **C5 Source ou « non vérifié »** | Tout chiffre ou fait affirmé dans un document porte sa source (fichier, commande et ce qu'elle a rendu, référence) ou la mention `[non vérifié]`. |
| **C6 Second regard** | Rien n'entre dans la branche principale sans une demande de fusion relue par quelqu'un qui n'en est pas l'auteur : une personne, ou un agent indépendant de celui qui a produit le changement. |
| **C7 Rien ne sort sans accord** | Aucun secret ni donnée personnelle dans un dépôt. Un agent ne publie, n'envoie ni ne pousse vers l'extérieur sans l'accord explicite d'un mainteneur, acte par acte. |
| **C8 Dans le doute, on demande** | Un agent qui rencontre une ambiguïté s'arrête et pose une question écrite, plutôt que de deviner. |
| **C9 Passation en fin de session** | Une session de travail d'agent se termine par un `PASSATION.md` à jour, un arbre de travail propre et rien d'en cours qui ne soit signalé. |
| **C10 Langue de l'interlocuteur** | Un agent répond dans la langue de la personne qui lui parle. Les documents d'un dépôt suivent la langue déclarée dans `memnius.yaml`. |
| **C11 Registre du projet tenu à jour** | Chaque dépôt de projet tient un registre de même structure (`registre/`) : une carte par code, jeu de données ou source notable, qui dit ce que c'est, qui l'a fait et où le trouver. Les entrées du journal sont les cartes de décision. L'index `registre/INDEX.md` est régénéré par l'outil commun dans le même commit que les cartes, jamais édité à la main. |

## Gardes automatiques (A1–A7)

L'intégration continue de GitHub (Actions) est le seul verrou qui compte ; le crochet pre-commit n'est qu'un confort pour voir
l'erreur plus tôt. Sortie commune : une ligne `[ ok ]` ou `[FIRE]` par garde, puis un bilan. Une garde
qui n'a pas pu tourner compte comme un échec, jamais comme un succès.

| Garde | Vérifie | Où | Fait respecter |
|---|---|---|---|
| **A1 Branche protégée** | Pas de force-push ni de push direct sur `main` ; fusion par pull request relue, gardes vertes | Ruleset GitHub sur `main`, contrôlé chaque nuit par le super-registre | C1, C6 |
| **A2 Secrets** | Aucune clé, mot de passe ou jeton dans les fichiers suivis | `gardes.py` (CI et pre-commit), gitleaks (CI), protection des pushs de GitHub | C7 |
| **A3 Structure** | README.md, AGENTS.md, `memnius.yaml` valide, journal `registre/decisions/` et `PASSATION.md` présents | CI (`gardes.py` appelle `memnius.py verifier`) | C2, C9 |
| **A4 Journal en ajout seul** | Aucune entrée existante de `registre/decisions/` modifiée ou supprimée ; chaque entrée a ses champs et un marqueur d'origine | CI | C2, C4 |
| **A5 Renvois aux règles** | Tout renvoi à une règle (C3, R5…) dans les fichiers de gouvernance désigne une règle qui existe et n'est pas abrogée | CI | C3 |
| **A6 Gros fichiers** | Aucun fichier de plus de 10 Mo hors Git LFS | CI et pre-commit | C7, drive commun (0011) |
| **A7 Registre du projet** | `registre/` a la structure commune ; chaque carte a ses champs (titre, résumé, où, auteurs, date) ; ses chemins existent dans le dépôt et ses liens visent des cartes connues ; l'index et le bloc de liens de chaque carte sont à jour. Signale sans bloquer le code et les données qu'aucune carte ne décrit | CI (`outils/gardes.py` appelle `memnius.py`) | C11 |

Sur GitHub, le ruleset de `main` exige une pull request approuvée par une autre personne que son auteur
(GitHub interdit à l'auteur d'approuver sa propre pull request) et le succès du workflow des gardes :
C6 est donc appliquée par la forge. Limite de l'offre gratuite : les rulesets n'existent que pour les
dépôts **publics** ; un projet privé n'a pas de garde A1, et le super-registre le signale.

## Règles recommandées pour les dépôts à agents (R1–R8)

| Règle | Énoncé |
|---|---|
| **R1 Se présenter avant d'agir** | Un agent commence par dire en deux ou trois phrases l'état du dépôt tel qu'il le comprend, avant tout changement. |
| **R2 Brouillons à part** | Un agent produit d'abord sur une branche `agent/<outil>/<objet>` ; rien n'est promu sans vérification par un agent indépendant ou une personne. |
| **R3 Délégation tracée** | Toute délégation à un sous-agent nomme le modèle utilisé, et la consigne transmise est conservée. |
| **R4 Annoncer les grands essaims** | Au-delà de cinq sous-agents pour une même tâche, l'agent l'annonce avant de lancer. |
| **R5 Trois allers-retours, puis escalade** | Un défaut qui survit à trois allers-retours entre producteur et vérificateur remonte à un mainteneur. |
| **R6 Copier, jamais paraphraser** | Un chiffre repris est re-mesuré avant réutilisation ; une sortie de commande est copiée, pas résumée ; une liste est comptée en entier, jamais sur une sortie tronquée. |
| **R7 Test des deux mondes** | On n'écrit pas comme un fait ce qui dépend d'un acte encore en cours : la phrase doit rester vraie que cet acte aboutisse ou non. |
| **R8 Échecs consignés** | Tout manquement aux règles, même commis par l'agent contre lui-même, est inscrit et daté dans le journal de décisions. |

## Options du régime renforcé (O1–O8)

Un dépôt adopte une option par une entrée de son journal qui dit pourquoi, et l'ajoute à
`socle.options` dans `memnius.yaml`. Ces options ont un coût réel ; elles restent hors du minimum.

| Option | Quand l'adopter |
|---|---|
| **O1 Dépôt de quarantaine séparé** | Les brouillons d'agents sont nombreux ou volumineux, et on veut qu'ils n'aient aucune autorité dans le dépôt principal. |
| **O2 Empreintes des gardes** | Le dépôt a ses propres gardes et on veut détecter qu'une garde a été modifiée sans le dire (manifeste avec empreinte sha256 par garde). |
| **O3 Contrôles de sabotage** | Chaque garde propre au dépôt est testée dans les deux sens : elle doit refuser un cas fautif et accepter un cas sain. |
| **O4 Journal de conversation** | Les décisions se prennent surtout en conversation avec des agents ; un crochet de fin de tour enregistre les réponses des personnes, dont on tire les entrées du journal. |
| **O5 Crochets d'agent** | L'outil d'agent le permet : refuser une délégation qui ne nomme pas son modèle, injecter un rappel des règles à chaque message. |
| **O6 Zones interdites** | Un répertoire ou un ancien dépôt ne doit pas être lu par les agents, même par une recherche large. |
| **O7 Langue et vocabulaire** | Le dépôt impose une langue unique, au-delà de C10, et la définition de tout terme technique. |
| **O8 Correction à côté** | Des documents historiques doivent rester intacts à l'octet près ; une correction datée s'écrit à côté, jamais à la place. |

## Journal de décisions

Chaque projet tient son journal dans son registre, `registre/decisions/` (décision 0016), un fichier par
décision nommé par un numéro à quatre chiffres, éventuellement suivi d'un titre court
(`registre/decisions/0001.md` ou `registre/decisions/0001-adopter-le-socle.md`). Le dépôt commun garde le
sien à la racine, dans `decisions/` : il n'a pas de registre de projet.
Ajouter une décision ne touche jamais un fichier existant. Format, vérifié par A4 :

```markdown
# 0042 — Adopter la règle recommandée R2

- Date : 2026-09-26
- Origine : [humain] « on passe les agents sur des branches de brouillon »
- Décidé par : @mainteneur
- Options écartées : garder le travail direct sur main (plus rapide, mais sans relecture)
- Source : pull request #17, commit abc1234
- Remplace : —
```

`Date`, `Origine` (avec `[humain]`, `[choix]` ou `[agent]`) et `Décidé par` sont obligatoires.
Une décision est ce qui autorise un acte ; une simple confirmation n'en est pas une. On écrit la décision
d'abord, on construit ensuite. Une erreur se corrige par une nouvelle entrée dont `Remplace` pointe vers
l'ancienne. Un marquage d'origine faux est pire qu'une absence de marquage : dans le doute, `[agent]`.

## Registre du projet et super-registre

Tout ce qui décrit un projet est dans son dossier `registre/` : le journal `registre/decisions/`, dont
chaque entrée est une carte de décision, et les cartes rangées dans `registre/code/`, `registre/donnees/` et
`registre/sources/` ;
le format est décrit dans `modeles/projet/registre/README.md`, les modèles de chaque type de carte dans
`modeles/cartes/` et le schéma dans `schema/carte.schema.json`. Une carte
est un fichier Markdown qui commence par un en-tête YAML entre deux lignes `---` :

```markdown
---
titre: Calcul de l'interfrange
resume: Calcule l'interfrange des fentes d'Young (i = λD/a).
ou: [travaux/interfrange.py]
auteurs: [Pwouette]
date: 2026-09-26
---
```

`memnius.py index` en tire `registre/INDEX.md` (lecture humaine, avec « qui a fait quoi ») et
`registre/index.json` (machines). Il écrit aussi, juste sous l'en-tête de chaque carte, un bloc qui rend
cliquables les fichiers et adresses de `ou`, `url` et `doi` et les cartes de `liens` : GitHub affiche
l'en-tête en tableau, sans liens. Ce bloc est dérivé comme l'index ; A7 refuse qu'il soit périmé ou retouché.
`INDEX.md` et `CARTES.md` rendent eux aussi chaque emplacement cliquable. Chaque nuit, le super-registre de ce dépôt lit la fiche et l'index de
chaque projet de l'organisation et publie, sur sa branche `super-registre`, `REGISTRE.md` (les projets),
`CARTES.md` (toutes les cartes et qui a fait quoi) et `registre.json`. Un dépôt de l'organisation est un
projet s'il porte le topic GitHub `memnius-projet`.

## Rituel de passation

`PASSATION.md`, à la racine, est réécrit à chaque fin de session ; l'historique Git garde les versions
précédentes. Les sections marquées d'une étoile sont obligatoires pour tous (C9), les autres pour les
dépôts à agents. La note n'a aucune autorité : seul l'état re-mesuré compte.

```markdown
# Passation — AAAA-MM-JJ — rédigée par … , vérifiée par : …

## 0. En une phrase *
## 1. État mesuré * (commandes lancées et sortie copiée : dernier commit, arbre propre, résultat des gardes)
## 2. Ce qui est entré, et qui l'a vérifié
## 3. Décisions prises (numéros du journal)
## 4. Manquements aux règles (R8)
## 5. Ce qui reste dû ou en cours *
## 6. Pièges rencontrés
## 7. Ce qui n'a PAS été vérifié *
```

L'agent qui reprend fait quatre choses avant tout travail : il re-mesure l'état avec les commandes de
la section 1 et compare avec la note ; il lance les gardes et rapporte ce qu'il a vu ; il signale tout
écart avant d'aller plus loin ; il se présente en deux ou trois phrases (R1). Un contributeur humain
occasionnel n'a qu'une obligation : lire la section 5 avant de commencer.

## Faire entrer un projet

Il n'y a pas de dépôt modèle à copier (décision 0015) : un projet garde son organisation propre. Pour
entrer dans le socle, il lui faut les fichiers que vérifie la garde A3 (README.md, AGENTS.md, `memnius.yaml`,
PASSATION.md, journal `registre/decisions/`), le reste du dossier `registre/` vérifié par A7 et le workflow des gardes.
`memnius.py init` les crée à partir de `modeles/projet/`, sans jamais remplacer un fichier existant ; il
reste à compléter `memnius.yaml` et à écrire les cartes, à partir des modèles de `modeles/cartes/`.
Un projet qui tenait son journal à la racine le déplace avec son historique : `git mv decisions
registre/decisions` (A3 et A4 le rappellent ; A4 accepte ce déplacement).

## Changer le socle

Le socle vit dans ce dépôt, versionné par étiquettes (`v2`, `v3`…). Chaque projet inclut la CI commune
à une version fixe. Changer une règle commune revient à publier une nouvelle version, décidée dans le
journal de ce dépôt (`decisions/`) par le comité. Le super-registre signale les projets en retard d'une version.
