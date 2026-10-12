# Consignes pour les agents IA

Ce fichier est lu par les agents de code (Claude Code via `CLAUDE.md`, Codex, Cursor, Copilot,
Gemini CLI, Aider…). Il applique le socle commun du groupe, dont le texte de référence est
<https://github.com/Memnius-PEE/registre/blob/v2/REGLES.md>. En cas de conflit, le socle l'emporte.

## Avant toute chose

1. Lis `memnius.yaml` (projet, langue, politique agents, options du socle) et les décisions de `registre/decisions/`.
   Ne remets pas une décision en cause sans le signaler.
2. Lis `registre/INDEX.md` : ce que contient le projet, qui l'a fait, où le trouver.

## Règles du socle (C1–C11, sans les trois abrogées)

- **C1 Histoire en ajout seul** : jamais de force-push, rebase ni amend d'un commit publié sur `main` ; une erreur se corrige par un nouveau commit.
- **C2 Décision écrite** : toute décision qui engage le dépôt est une nouvelle entrée de `registre/decisions/` ; une entrée publiée n'est jamais modifiée, sauf pour une coquille (commit dont le message dit « coquille », sans toucher `Date`, `Origine` ni `Décidé par`).
- **C3 Les règles appartiennent aux mainteneurs** : tu proposes, par une pull request ; seuls les mainteneurs déclarés changent une règle.
- **C4 Origine marquée** : dans le journal, `[humain]` pour les mots tapés par une personne, `[choix]` pour ton option choisie par une personne, `[agent]` pour ta déduction. Chaque commit se termine par `Assisted-by: <outil> (<modèle>)`.
- **C5 Source ou « non vérifié »** : dans un livrable, une carte ou le journal, tout chiffre ou fait porte sa source (fichier, commande et sortie, référence de `sources/`) ou la mention `[non vérifié]`.
- **C7 Rien ne sort sans accord** : aucun secret ni donnée personnelle ; tu ne publies, n'envoies ni ne pousses vers l'extérieur sans l'accord explicite d'un mainteneur, acte par acte.
- **C10 Langue de l'interlocuteur** : réponds dans la langue de la personne qui te parle ; les documents suivent `langue` de `memnius.yaml`.
- **C11 Registre du projet tenu à jour** : tout code, jeu de données, source ou document notable que tu ajoutes a sa carte dans `registre/` ; la CI régénère l'index après la fusion.

Les options listées dans `socle.options` de `memnius.yaml` s'appliquent aussi : voir `REGLES.md` du socle.

## Où écrire

| Tu peux modifier | Avec prudence | Ne modifie jamais |
|---|---|---|
| le contenu du projet, les cartes de `registre/` | `memnius.yaml`, `README.md` | entrées existantes de `registre/decisions/`, données d'origine, `.github/`, `AGENTS.md`, `registre/INDEX.md` et `registre/index.json` à la main |

## Façon de travailler

1. Travaille sur une branche (par exemple `agent/<outil>/<objet-court>`), jamais directement sur `main` : tout passe par une pull request (garde A1).
2. Lancé par une personne, tu commites sous son compte ; un agent automatique (CI,
   tâche planifiée) utilise son compte dédié. Un commit = une intention.
3. Ouvre une pull request selon `agents.politique` de `memnius.yaml`
   (`relecture-humaine` : un humain relit avant fusion).
4. Pas de fichier de plus de 10 Mo, même suivi par Git LFS : il va dans le drive commun (garde A6).

## Registre du projet

Le format des cartes est décrit dans `registre/README.md`. Quand tu ajoutes ou changes un élément notable :

1. crée ou mets à jour sa carte à partir du modèle (`memnius.py carte TYPE NOM --ou CHEMIN --auteur LOGIN`),
   avec comme auteur la personne qui t'a lancé, et `statut: a-relire` ;
2. une décision s'écrit dans le journal, elle aussi à partir du modèle (`memnius.py carte decision titre-court`) :
   l'entrée de `registre/decisions/` est sa carte ;
3. n'écris ni l'index ni les blocs de liens des cartes : la CI les régénère sur `main` après la fusion de ta
   pull request (décision 0021 du socle).

## Commandes utiles

<!-- À compléter par les mainteneur·ices : installation, tests, génération des livrables. -->
- Outils communs : `git clone --depth 1 --branch v2 https://github.com/Memnius-PEE/registre ../registre`
- Voir l'index du registre avant la CI (facultatif) : `python3 ../registre/outils/memnius.py index`
- Lancer les gardes comme la CI : `python3 ../registre/outils/gardes.py .`
