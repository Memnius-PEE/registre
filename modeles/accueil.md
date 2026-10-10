<!-- Page d'accueil de l'organisation (dépôt .github, fichier profile/README.md), réécrite chaque nuit par le
     workflow « Super-registre » du dépôt registre. Ne pas l'éditer dans .github : la partie fixe se modifie ici,
     dans registre/modeles/accueil.md, par une pull request ; la partie « Dernières modifications » est générée. -->
# Groupe d'étude Memnius

Chaque dépôt de cette organisation est un projet du groupe d'étude. Tous suivent le même socle de règles,
que l'on contribue souvent ou une seule fois, en personne ou par un agent IA.

> [!IMPORTANT]
> ## 📖 LIRE LE MANUEL !
> Avant votre première contribution, lisez **[les règles du socle (`REGLES.md`)](https://github.com/Memnius-PEE/registre/blob/main/REGLES.md)**,
> puis le `README.md` et le `AGENTS.md` du projet où vous travaillez. Un agent IA les lit aussi avant d'agir.

## Où trouver quoi

| Pour… | Aller à |
|---|---|
| Les règles communes, en entier | [`REGLES.md`](https://github.com/Memnius-PEE/registre/blob/main/REGLES.md) du dépôt [`registre`](https://github.com/Memnius-PEE/registre) |
| Pourquoi une règle existe | [le journal des décisions du socle](https://github.com/Memnius-PEE/registre/tree/main/decisions) |
| La liste des projets | [`REGISTRE.md`](https://github.com/Memnius-PEE/registre/blob/super-registre/REGISTRE.md) (mis à jour chaque nuit) |
| Qui a fait quoi, et où le trouver | [`CARTES.md`](https://github.com/Memnius-PEE/registre/blob/super-registre/CARTES.md), et dans chaque projet `registre/INDEX.md` |
| Écrire une carte ou une décision | [les modèles de cartes](https://github.com/Memnius-PEE/registre/tree/main/modeles/cartes) et `python3 outils/memnius.py carte` |

## Les règles fondamentales, en bref

- **Tout passe par une pull request.** `main` est protégée : ni push direct, ni force-push, ni réécriture
  de l'histoire ; une erreur se corrige par un nouveau commit (C1).
- **Une décision non écrite n'existe pas.** Toute décision qui engage un projet est une entrée datée de son
  journal `registre/decisions/`, jamais réécrite ensuite (C2).
- **Les mainteneurs font les règles, les autres proposent.** Le comité du socle tient les règles communes,
  un mainteneur par projet tient les siennes ; agents et contributeurs proposent par pull request (C3).
- **On dit qui parle.** Le journal marque chaque origine `[humain]`, `[choix]` ou `[agent]` ; un commit
  fait avec un agent porte la ligne `Assisted-by: <outil> (<modèle>)` (C4).
- **Un fait porte sa source**, ou la mention `[non vérifié]` (C5).
- **Rien ne sort sans accord.** Aucun secret ni donnée personnelle dans un dépôt ; un agent ne publie ni
  n'envoie rien sans l'accord explicite d'un mainteneur (C7).
- **Chaque projet tient son registre** : une carte par code, jeu de données ou source notable, qui dit ce
  que c'est, qui l'a fait et où le trouver. L'index est écrit par la CI (C11).
- **Les gros fichiers vont dans le drive commun** : au-delà de 10 Mo, un fichier est refusé, même par Git LFS.

Les gardes automatiques (A1 à A7) vérifient tout cela sur chaque pull request. Un agent répond dans la
langue de la personne qui lui parle (C10).

## Dernières modifications

{{DERNIERES_MODIFICATIONS}}
