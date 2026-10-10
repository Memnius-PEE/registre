# Règles et garde-fous communs Memnius — socle v2

Tous les dépôts de projet partagent un socle court de règles obligatoires (C1–C11, dont trois abrogées)
et 7 gardes automatiques (A1–A7). Les options O1–O8 forment un régime renforcé qu'un dépôt adopte une à
une, par une entrée de son journal. Les règles recommandées R1–R8 sont abrogées (décision 0017).

Un dépôt déclare dans `memnius.yaml` la version du socle qu'il suit et les options qu'il a adoptées
(`socle.version`, `socle.options`). Il peut ajouter ses propres règles, jamais retirer
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

Les règles 6, 8 et 9 de cette série (second regard, dans le doute on demande, passation en fin de
session) sont abrogées depuis la décision 0017 ; leurs numéros restent réservés.

| Règle | Énoncé |
|---|---|
| **C1 Histoire en ajout seul** | Sur la branche principale, on ne réécrit jamais l'histoire : ni force-push, ni rebase, ni amend d'un commit publié. Une erreur se corrige par un nouveau commit. |
| **C2 Décision écrite** | Toute décision qui engage le dépôt (méthode, périmètre, choix d'outil, règle) est une entrée datée du journal `registre/decisions/`. Une entrée publiée n'est jamais modifiée sur le fond ; on la corrige par une nouvelle entrée. Seule exception : une coquille, corrigée par un commit dont le message contient « coquille » et qui ne touche ni `Date`, ni `Origine`, ni `Décidé par`. |
| **C3 Les règles appartiennent aux mainteneurs** | Seuls les mainteneurs déclarés créent, modifient ou suppriment une règle : un comité d'une à trois personnes pour le socle, et pour chaque dépôt un mainteneur nommé par ce comité. Les agents et les autres contributeurs proposent, par une demande de fusion. |
| **C4 Origine marquée** | Chaque entrée du journal dit qui parle : `[humain]` pour les mots tapés par une personne, `[choix]` pour une option rédigée par un agent et choisie par une personne, `[agent]` pour une déduction d'agent. Un commit fait avec un agent le déclare par la ligne `Assisted-by: <outil> (<modèle>)`. |
| **C5 Source ou « non vérifié »** | Tout chiffre ou fait affirmé dans un livrable, une carte du registre ou une entrée du journal porte sa source (fichier, commande et ce qu'elle a rendu, référence) ou la mention `[non vérifié]`. Les notes de travail en sont dispensées. |
| **C7 Rien ne sort sans accord** | Aucun secret ni donnée personnelle dans un dépôt. Un agent ne publie, n'envoie ni ne pousse vers l'extérieur sans l'accord explicite d'un mainteneur, acte par acte. |
| **C10 Langue de l'interlocuteur** | Un agent répond dans la langue de la personne qui lui parle. Les documents d'un dépôt suivent la langue déclarée dans `memnius.yaml`. |
| **C11 Registre du projet tenu à jour** | Chaque dépôt de projet tient un registre de même structure (`registre/`) : une carte par code, jeu de données ou source notable, qui dit ce que c'est, qui l'a fait et où le trouver. Les entrées du journal sont les cartes de décision. L'index `registre/INDEX.md` et les blocs de liens des cartes sont écrits par la CI, qui les ajoute en commit sur la pull request ; personne ne les édite à la main. |

## Gardes automatiques (A1–A7)

L'intégration continue de GitHub (Actions) est le seul verrou qui compte ; le crochet pre-commit n'est qu'un confort pour voir
l'erreur plus tôt. Sortie commune : une ligne `[ ok ]` ou `[FIRE]` par garde, puis un bilan. Une garde
qui n'a pas pu tourner compte comme un échec, jamais comme un succès.

| Garde | Vérifie | Où | Fait respecter |
|---|---|---|---|
| **A1 Branche protégée** | Pas de force-push, de suppression ni de push direct sur `main` ; fusion par pull request, gardes vertes (aucune approbation exigée) | Ruleset GitHub sur `main`, contrôlé chaque nuit par le super-registre | C1 |
| **A2 Secrets** | Aucune clé, mot de passe ou jeton dans les fichiers suivis | `gardes.py` (CI et pre-commit), gitleaks (CI), protection des pushs de GitHub | C7 |
| **A3 Structure** | README.md, AGENTS.md, `memnius.yaml` valide et journal `registre/decisions/` non vide. Champs obligatoires de `memnius.yaml` : `schema`, `id`, `titre`, `resume`, `langue`, `mainteneurs`, `socle`, `visibilite` | CI (`gardes.py` appelle `memnius.py verifier`) | C2, C3, C10 |
| **A4 Journal en ajout seul** | Aucune entrée existante de `registre/decisions/` modifiée ou supprimée, sauf correction de coquille (C2) ; chaque entrée a ses champs `Date`, `Origine` (avec son marqueur) et `Décidé par` | CI | C2, C4 |
| **A5 Renvois aux règles** | Tout renvoi à une règle (C3, O6…) dans les fichiers de gouvernance désigne une règle qui existe et n'est pas abrogée ; le journal, qui est l'histoire, peut citer une règle abrogée | CI | C3 |
| **A6 Gros fichiers** | Aucun fichier de plus de 10 Mo, y compris suivi par Git LFS : un gros fichier va dans le drive commun | CI et pre-commit | C7, drive commun (0011) |
| **A7 Registre du projet** | `registre/` a la structure commune ; chaque carte a ses champs (titre, résumé, où, auteurs, date) ; ses chemins existent dans le dépôt et ses liens visent des cartes connues. L'index et les blocs de liens, écrits par la CI, ne sont pas contrôlés. Signale sans bloquer le code et les données qu'aucune carte ne décrit | CI (`outils/gardes.py` appelle `memnius.py`) | C11 |

Sur GitHub, le ruleset de `main` exige une pull request et le succès du workflow des gardes ; il
n'exige aucune approbation. Limite de l'offre gratuite : les rulesets n'existent que pour les
dépôts **publics** ; un projet privé n'a pas de garde A1, et le super-registre le signale.

Le workflow des gardes a un second rôle sur une pull request qui vient du dépôt lui-même : il régénère
l'index du registre et les blocs de liens des cartes, les ajoute en commit sur la branche de la pull
request, puis relance les gardes sur ce nouveau commit. Pour une pull request venant d'une copie (fork),
il ne peut pas pousser : l'index sera remis à jour par la pull request suivante.

## Règles recommandées R1–R8 (abrogées)

Les huit règles recommandées pour les dépôts à agents sont abrogées depuis la décision 0017 ; leurs
numéros restent réservés et `regles.yaml` garde leurs titres.

## Options du régime renforcé (O1–O8)

Un dépôt adopte une option par une entrée de son journal qui dit pourquoi, et l'ajoute à
`socle.options` dans `memnius.yaml`. Ces options ont un coût réel ; elles restent hors du minimum.
Il n'y a plus de niveau à déclarer : la liste des options adoptées suffit.

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
# 0042 — Adopter l'option O6

- Date : 2026-09-26
- Origine : [humain] « les agents ne lisent pas l'ancien dossier archives/ »
- Décidé par : @mainteneur
- Options écartées : le dire seulement dans AGENTS.md (rien ne le rappelle aux agents)
- Source : pull request #17, commit abc1234
- Remplace : —
```

`Date`, `Origine` (avec `[humain]`, `[choix]` ou `[agent]`) et `Décidé par` sont obligatoires.
Une décision est ce qui autorise un acte ; une simple confirmation n'en est pas une. On écrit la décision
d'abord, on construit ensuite. Une erreur se corrige par une nouvelle entrée dont `Remplace` pointe vers
l'ancienne ; une coquille se corrige sur place, par un commit dont le message contient « coquille » et qui
laisse intacts `Date`, `Origine` et `Décidé par` (A4 le vérifie). Un marquage d'origine faux est pire qu'une absence de marquage : dans le doute, `[agent]`.

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
l'en-tête en tableau, sans liens. L'index et ce bloc sont dérivés : c'est la CI qui lance `memnius.py index`
sur chaque pull request et commite le résultat ; un contributeur n'a qu'à écrire ses cartes.
`INDEX.md` et `CARTES.md` rendent eux aussi chaque emplacement cliquable. Chaque nuit, le super-registre de ce dépôt lit la fiche et l'index de
chaque projet de l'organisation et publie, sur sa branche `super-registre`, `REGISTRE.md` (les projets),
`CARTES.md` (toutes les cartes et qui a fait quoi) et `registre.json`. Un dépôt de l'organisation est un
projet s'il porte le topic GitHub `memnius-projet`.

## Faire entrer un projet

Il n'y a pas de dépôt modèle à copier (décision 0015) : un projet garde son organisation propre. Pour
entrer dans le socle, il lui faut les fichiers que vérifie la garde A3 (README.md, AGENTS.md, `memnius.yaml`,
journal `registre/decisions/`), le reste du dossier `registre/` vérifié par A7 et le workflow des gardes.
`memnius.py init` les crée à partir de `modeles/projet/`, sans jamais remplacer un fichier existant ; il
reste à compléter `memnius.yaml` et à écrire les cartes, à partir des modèles de `modeles/cartes/`.
Un projet qui tenait son journal à la racine le déplace avec son historique : `git mv decisions
registre/decisions` (A3 et A4 le rappellent ; A4 accepte ce déplacement).

## Changer le socle

Le socle vit dans ce dépôt, versionné par étiquettes (`v2`, `v3`…). Chaque projet inclut la CI commune
à une version fixe. Changer une règle commune revient à publier une nouvelle version, décidée dans le
journal de ce dépôt (`decisions/`) par le comité. Le super-registre signale les projets en retard d'une version.
