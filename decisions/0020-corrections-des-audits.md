# 0020 — Corrections des audits du 2026-10-11

- Date : 2026-10-11
- Origine : [choix] « Tout », sur la carte « Corriger dans le kit les défauts relevés par les audits ? » rédigée par un agent (Claude) ; [agent] détail des corrections, tiré des deux rapports
- Décidé par : Romain (comité du socle)
- Options écartées : corriger seulement les défauts graves ; lire les rapports avant de décider
- Source : projet Claude « Memnius », rapports `audit/audit-opus.md` et `audit/audit-fable.md` du dossier partagé (audits en lecture seule du kit au commit 106921a et de Memnius-PEE)
- Remplace : 0017, pour le seul point « C2 et A4 » (bornes d'une coquille)

Les deux audits jugent que le système marche et relèvent les mêmes défauts graves. Corrigé :

- **Projets privés.** `REGISTRE.md`, `CARTES.md` et `registre.json` de la branche `super-registre`, publics,
  listaient les projets privés ; seule la page d'accueil les filtrait. Toutes les sorties publiques les
  écartent désormais (réellement privés, ou `visibilite: prive` dans la fiche) ; `REGISTRE.md` dit combien il y
  en a. La vue complète ne va que dans un dépôt privé, `registre-prive` (`creer-vue-complete.sh`). Écarté : une
  ligne par projet privé sans ses cartes (le nom d'un projet peut être sensible) ; un artefact d'exécution
  (téléchargeable par tout compte GitHub sur un dépôt public).
- **Secrets du dépôt `registre`.** Un workflow modifié dans une branche du dépôt lisait tous ses secrets. Ils
  passent dans l'environnement GitHub `super-registre`, réservé à la branche `main`, et seul le comité a
  l'écriture sur `registre`. Écarté : un relecteur requis sur l'environnement (il faudrait approuver chaque
  passe nocturne).
- **Coquille (C2, A4).** Le fond d'une décision pouvait être réécrit sous le nom de « coquille ». Une coquille
  n'ajoute ni ne retire aucun mot, corrige au plus 4 mots et 20 caractères, ne change aucun nombre ni aucun
  champ (ni son nom, ni la valeur de `Date`, `Origine`, `Décidé par`, `Remplace`). Au-delà, nouvelle entrée.
- **Contrôles requis (A1, A2).** gitleaks, seul à lire chaque commit de la pull request, devient un contrôle
  requis ; les deux contrôles sont attachés à GitHub Actions dans le ruleset. Le super-registre vérifie le
  ruleset complet (suppression, force-push, pull request, les deux contrôles) et que le workflow du projet
  appelle toujours `gardes.yml` du dépôt `registre`.

Corrigé aussi :

- **A6** lit chaque commit de la pull request : un gros fichier ajouté puis retiré entrait dans l'historique.
- **A2** reconnaît les jetons `github_pat_`, les JWT, les en-têtes `Bearer`, les clés Google et Hugging Face.
- **A5** ne lit un code comme `A4` ou `C6` comme renvoi que dans son contexte (« format A4 » n'en est pas un).
- **A7** : la liste des fichiers à décrire par une carte se déclare dans `memnius.yaml`
  (`registre.a_couvrir`) ; à défaut, tout fichier rangé dans un dossier hors `registre/` et dossiers cachés
  (`travaux/` et `donnees/` venaient du gabarit abandonné par la 0015). Une carte de données rangées hors du
  dépôt porte leur empreinte : en attendant le drive commun (0011), un stockage institutionnel ou Zenodo
  convient. Les messages de schéma sont en français.
- **Super-registre** : un projet illisible devient une ligne « non lu » au lieu de faire échouer la passe ; le
  quota épuisé est attendu s'il se rétablit dans les 15 minutes ; un échec ouvre le ticket « Super-registre en
  échec » ; les dernières modifications ne sont lues que pour les projets publics ; les auteurs de cartes
  inconnus de GitHub sont signalés ; la page d'accueil n'affiche que des identifiants GitHub, jamais le nom
  inscrit dans un commit, et marque 🤖 les commits faits avec un agent ; `CARTES.md` montre les mots-clés ; une
  décision remplacée est marquée « remplacée par » dans les index ; une décision écrite en liste a un résumé.
- **Étiquettes.** `v2.0`, `v2.1`… sont fixes ; `v2` avance sur la dernière révision compatible ; une révision
  qui ferait échouer un projet conforme ouvre `v3`. Cela précise la 0017, qui déplaçait `v2`.
- **Ménage** : schéma `registre.schema.json` (v1) retiré ; paquets Python épinglés ; clé d'hôte de github.com
  inscrite au lieu d'être acceptée à l'aveugle ; ancienne clé de déploiement retirée quand on en pose une neuve ;
  bilan des gardes affiché sur la page de l'exécution ; format `Assisted-by: <outil> (<modèle>)` dans
  CONTRIBUTING.md ; Git LFS retiré de l'exemple ; LISEZMOI.md remis à jour. La 0017 modifiait la 0014 (A7 ne
  vérifie plus l'index) sans le dire dans `Remplace` : c'est noté ici.

Pas fait : épingler les actions GitHub par empreinte (il faut relever les empreintes des versions voulues) ;
confronter les `auteurs` des cartes à l'historique Git (coûteux, et les auteurs restent déclaratifs, principe 1).
