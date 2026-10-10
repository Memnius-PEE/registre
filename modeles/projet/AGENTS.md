# Consignes pour les agents IA

Ce fichier est lu par les agents de code (Claude Code via `CLAUDE.md`, Codex, Cursor, Copilot,
Gemini CLI, Aider…). Il applique le socle commun du groupe, dont le texte de référence est
<https://github.com/Memnius-PEE/registre/blob/v2/REGLES.md>. En cas de conflit, le socle l'emporte.

## Avant toute chose

1. Lis `PASSATION.md`, puis vérifie-le au lieu de le croire : re-mesure l'état (dernier commit,
   arbre propre, gardes) et signale tout écart avant d'aller plus loin.
2. Lis `memnius.yaml` (projet, langue, politique agents, niveau du socle) et les décisions de `registre/decisions/`.
   Ne remets pas une décision en cause sans le signaler.
3. Lis `registre/INDEX.md` : ce que contient le projet, qui l'a fait, où le trouver.
4. Présente en deux ou trois phrases l'état du dépôt tel que tu le comprends.

## Règles du socle (C1–C11)

- **C1 Histoire en ajout seul** : jamais de force-push, rebase ni amend d'un commit publié sur `main` ; une erreur se corrige par un nouveau commit.
- **C2 Décision écrite** : toute décision qui engage le dépôt est une nouvelle entrée de `registre/decisions/` ; une entrée publiée n'est jamais modifiée.
- **C3 Les règles appartiennent aux mainteneurs** : tu proposes, par une pull request ; seuls les mainteneurs déclarés changent une règle.
- **C4 Origine marquée** : dans le journal, `[humain]` pour les mots tapés par une personne, `[choix]` pour ton option choisie par une personne, `[agent]` pour ta déduction. Chaque commit se termine par `Assisted-by: <outil> (<modèle>)`.
- **C5 Source ou « non vérifié »** : tout chiffre ou fait porte sa source (fichier, commande et sortie, référence de `sources/`) ou la mention `[non vérifié]`.
- **C6 Second regard** : rien n'entre dans `main` sans pull request relue par un autre que toi (une personne ou un agent indépendant).
- **C7 Rien ne sort sans accord** : aucun secret ni donnée personnelle ; tu ne publies, n'envoies ni ne pousses vers l'extérieur sans l'accord explicite d'un mainteneur, acte par acte.
- **C8 Dans le doute, on demande** : devant une ambiguïté, arrête-toi et pose une question écrite.
- **C9 Passation en fin de session** : `PASSATION.md` à jour, arbre de travail propre, rien d'en cours qui ne soit signalé.
- **C10 Langue de l'interlocuteur** : réponds dans la langue de la personne qui te parle ; les documents suivent `langue` de `memnius.yaml`.
- **C11 Registre du projet tenu à jour** : tout code, jeu de données ou source notable que tu ajoutes a sa carte dans `registre/` ; tu régénères l'index dans le même commit.

Si `socle.niveau` vaut `recommande` ou `renforce`, les règles R1–R8 (et les options listées dans
`socle.options`) s'appliquent aussi : voir `REGLES.md` du socle.

## Où écrire

| Tu peux modifier | Avec prudence | Ne modifie jamais |
|---|---|---|
| le contenu du projet, les cartes de `registre/` | `memnius.yaml`, `README.md`, `PASSATION.md` | entrées existantes de `registre/decisions/`, données d'origine, `.github/`, `AGENTS.md`, `registre/INDEX.md` et `registre/index.json` à la main |

## Façon de travailler

1. Travaille sur une branche `agent/<outil>/<objet-court>`, jamais directement sur `main`.
2. Lancé par une personne, tu commites sous son compte ; un agent automatique (CI,
   tâche planifiée) utilise son compte dédié. Un commit = une intention.
3. Ouvre une pull request selon `agents.politique` de `memnius.yaml`
   (`relecture-humaine` : un humain relit avant fusion).
4. Pas de fichier de plus de 10 Mo hors Git LFS (garde A6).

## Registre du projet

Le format des cartes est décrit dans `registre/README.md`. Quand tu ajoutes ou changes un élément notable :

1. crée ou mets à jour sa carte à partir du modèle (`memnius.py carte TYPE NOM --ou CHEMIN --auteur LOGIN`),
   avec comme auteur la personne qui t'a lancé, et `statut: a-relire` ;
2. une décision s'écrit dans le journal, elle aussi à partir du modèle (`memnius.py carte decision titre-court`) :
   l'entrée de `registre/decisions/` est sa carte ;
3. régénère l'index et les liens des cartes (`memnius.py index`) et commite-les avec le changement : la garde A7
   refuse un index ou un bloc de liens périmé.

## Commandes utiles

<!-- À compléter par les mainteneur·ices : installation, tests, génération des livrables. -->
- Outils communs : `git clone --depth 1 --branch v2 https://github.com/Memnius-PEE/registre ../registre`
- Régénérer l'index du registre : `python3 ../registre/outils/memnius.py index`
- Lancer les gardes comme la CI : `python3 ../registre/outils/gardes.py .`
