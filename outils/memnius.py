#!/usr/bin/env python3
"""Outil commun Memnius : registre de chaque projet (cartes et index) et super-registre de l'organisation.

Usage :
  python3 memnius.py verifier [DOSSIER]
      Contrôle un dépôt de projet : structure (garde A3) et registre (garde A7).
  python3 memnius.py index [DOSSIER] [--verifier]
      Régénère registre/INDEX.md et registre/index.json à partir des cartes et du journal
      registre/decisions/, et met à jour dans chaque carte le bloc de liens cliquables vers ce qu'elle cite.
      Avec --verifier, n'écrit rien et sort en erreur si l'index ou un bloc de liens n'est pas à jour.
      En CI, le workflow des gardes le lance après chaque fusion et pousse le résultat sur main (règle C11).
  python3 memnius.py init [DOSSIER] [--id ID] [--titre T] [--mainteneur LOGIN]
      Ajoute à un dépôt de projet les fichiers que le socle exige (modeles/projet/), sans rien remplacer.
  python3 memnius.py carte TYPE NOM [--dossier D] [--titre T] [--ou CHEMIN]… [--auteur LOGIN]…
      Crée une carte à remplir à partir de son modèle (modeles/cartes/) : registre/TYPE/NOM.md pour
      code, donnees, sources ou documents ; registre/decisions/NNNN-NOM.md (numéro suivant) pour une décision.
  python3 memnius.py registre --github ORG [--github AUTRE] [--sortie DIR]
  python3 memnius.py registre --local DOSSIER-DES-CLONES [--sortie DIR]
      Construit le super-registre : REGISTRE.md (les projets), CARTES.md (toutes les cartes, et qui a
      fait quoi), registre.json et ACCUEIL.md, la page d'accueil de l'organisation (modeles/accueil.md
      complété par les dernières modifications des registres des projets publics). Un dépôt de l'organisation est un projet s'il porte le topic GitHub
      « memnius-projet ». Jeton lu dans GITHUB_TOKEN (facultatif si tous les dépôts sont publics).
      Ces sorties sont publiques : un projet privé (réellement ou par sa fiche) n'y figure jamais (C7).
      Avec --complet DIR, écrit aussi dans DIR la vue complète, projets privés compris, à publier
      seulement dans un dépôt privé.

Tout le registre vit dans registre/ : les cartes de décision sont les entrées du journal registre/decisions/,
les autres cartes sont rangées dans registre/code/, registre/donnees/, registre/sources/ et registre/documents/.
L'index, les blocs de liens des cartes et le super-registre sont dérivés : on ne les édite jamais à la main.
Dépendances : PyYAML ; jsonschema est utilisé s'il est installé (sinon contrôles essentiels seulement).
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

import yaml

ICI = Path(__file__).resolve().parent.parent
SCHEMA_FICHE = ICI / "schema" / "memnius.schema.json"
SCHEMA_CARTE = ICI / "schema" / "carte.schema.json"
VOCABULAIRE = ICI / "vocabulaire.yaml"
MODELES = ICI / "modeles"
MODELE_ACCUEIL = MODELES / "accueil.md"

# Garde A3 du socle : README, AGENTS.md, memnius.yaml et un journal registre/decisions/ non vide.
FICHIERS_OBLIGATOIRES = ["README.md", "AGENTS.md", "memnius.yaml"]
FICHIERS_RECOMMANDES = ["CONTRIBUTING.md", ".github/workflows/memnius.yml"]
JOURNAL = "registre/decisions"
ENTREE_JOURNAL = re.compile(r"^registre/decisions/(\d{4})(-[a-z0-9]+(?:-[a-z0-9]+)*)?\.md$")
ANCIEN_JOURNAL = re.compile(r"^decisions/\d{4}")  # emplacement d'avant la décision 0016 du socle
MARQUEURS_MODELE = re.compile(r"TITRE_DU_PROJET|SLUG-DU-PROJET|RÉSUMÉ_EN|IDENTIFIANT_GITHUB|AAAA-MM-JJ|DOMAINE\b")
JOURS_AVANT_DORMANT = 180

# Registre d'un projet (garde A7) : la même structure dans tous les dépôts.
REGISTRE = "registre"
TYPES = {"decision": "Décisions", "code": "Code", "donnees": "Données", "sources": "Sources", "documents": "Documents"}
TYPES_RANGES = ["code", "donnees", "sources", "documents"]  # les décisions sont les entrées de registre/decisions/
# Dossiers que A7 exige ; registre/documents/ (décision 0021) est facultatif, pour que les projets d'avant restent conformes.
DOSSIERS_EXIGES = ["code", "donnees", "sources"]
FICHIERS_REGISTRE = ["registre/README.md"]
FICHIERS_INDEX = ["registre/INDEX.md", "registre/index.json"]  # écrits par la CI (C11), non contrôlés par A7
NOM_CARTE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
A_REMPLIR = "À_REMPLIR"
CHAMPS_PAR_TYPE = {"langage": ("code",), "commande": ("code",), "format": ("donnees", "documents"),
                   "taille": ("donnees",), "empreinte": ("donnees",), "reference": ("sources",),
                   "cle_bib": ("sources",), "doi": ("sources", "documents")}
# Fichiers qu'une carte devrait couvrir (avertissement seulement). Un projet les déclare dans memnius.yaml
# (registre.a_couvrir : dossiers ou fichiers) ; par défaut, tout fichier rangé dans un dossier, hors registre/,
# dossiers cachés (.github/…) et fichiers de gouvernance à la racine.
HORS_COUVERTURE = re.compile(r"(^|/)(\.gitkeep|README\.md)$|^(registre|\.[^/]+)/|^[^/]+$")

NB_MODIFICATIONS = 10  # lignes de « Dernières modifications » sur la page d'accueil de l'organisation
TYPE_SINGULIER = {"decision": "décision", "code": "code", "donnees": "données", "sources": "source", "documents": "document"}

SUJET_GITHUB = "memnius-projet"  # topic GitHub qui marque un dépôt de projet dans l'organisation
# Garde A1 : ce que le ruleset de la branche principale doit contenir, et les contrôles qu'il doit exiger.
REGLES_A1 = {"deletion", "non_fast_forward", "pull_request", "required_status_checks"}
CONTROLES_REQUIS = ["gardes / Gardes A2 à A7", "gardes / A2, second filet (gitleaks)"]
WORKFLOW_PROJET = ".github/workflows/memnius.yml"
ATTENTE_QUOTA_MAX = 900  # secondes qu'on accepte d'attendre la remise à zéro du quota de l'API GitHub


def maintenant():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def en_texte(objet):
    """yaml lit les dates AAAA-MM-JJ comme des objets date : on les remet en texte."""
    return json.loads(json.dumps(objet, default=str))


def charger_vocabulaire():
    if VOCABULAIRE.exists():
        return yaml.safe_load(VOCABULAIRE.read_text(encoding="utf-8")) or {}
    return {}


def valider(objet, chemin_schema):
    """Renvoie la liste des erreurs de schéma (jsonschema si disponible, sinon champs requis)."""
    schema = json.loads(chemin_schema.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        return [f"champ obligatoire manquant : {c}" for c in schema["required"] if c not in objet]
    validateur = jsonschema.Draft202012Validator(schema)
    erreurs = []
    for e in sorted(validateur.iter_errors(objet), key=lambda e: list(e.path)):
        chemin = ".".join(str(p) for p in e.path) or "(racine)"
        erreurs.append(f"{chemin} : {en_francais(e)}")
    return erreurs


def en_francais(e):
    """Les messages courants de jsonschema, en français (le nom du champ fautif reste lisible)."""
    v, attendu = e.validator, e.validator_value
    if v == "required":
        manquants = [c for c in attendu if isinstance(e.instance, dict) and c not in e.instance]
        return "champ obligatoire manquant : " + ", ".join(manquants)
    if v == "additionalProperties" and isinstance(e.instance, dict):
        connus = set((e.schema.get("properties") or {}))
        return "champ inconnu : " + ", ".join(sorted(k for k in e.instance if k not in connus))
    if v == "pattern":
        if "\\d{4}-" in attendu:
            return f"« {e.instance} » : date au format AAAA-MM-JJ attendue"
        return f"« {e.instance} » ne suit pas le format attendu ({attendu})"
    if v == "enum":
        return f"« {e.instance} » : valeur attendue parmi " + ", ".join(map(str, attendu))
    if v == "const":
        return f"« {e.instance} » : valeur attendue {attendu}"
    if v == "minLength":
        return f"texte trop court (au moins {attendu} caractères)"
    if v == "maxLength":
        return f"texte trop long (au plus {attendu} caractères)"
    if v == "minItems":
        return f"liste vide (au moins {attendu} élément)"
    if v == "type":
        return f"type attendu : {attendu}"
    return e.message


def lister_fichiers(dossier):
    """Fichiers du dépôt : suivis par Git ou nouveaux mais non ignorés (une carte qu'on vient d'écrire
    compte avant même son « git add ») ; hors dépôt Git, tous les fichiers."""
    r = subprocess.run(["git", "-C", str(dossier), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                       capture_output=True)
    if r.returncode == 0 and (Path(dossier) / ".git").exists():
        return sorted({f for f in r.stdout.decode().split("\0") if f and (Path(dossier) / f).exists()})
    return sorted(str(p.relative_to(dossier).as_posix()) for p in Path(dossier).rglob("*")
                  if p.is_file() and ".git" not in p.parts)


# ------------------------------------------------------------------ structure (garde A3)


def controler(texte_fiche, fichiers_presents, nom_depot, vocab, derniere_activite=None, branche_protegee=None):
    """Contrôles de structure communs aux modes local et GitHub."""
    erreurs, avertissements = [], []
    fiche = None
    for f in FICHIERS_OBLIGATOIRES:
        if f not in fichiers_presents:
            erreurs.append(f"fichier obligatoire absent : {f}")
    for f in FICHIERS_RECOMMANDES:
        if f not in fichiers_presents:
            avertissements.append(f"fichier recommandé absent : {f}")
    if not any(ENTREE_JOURNAL.match(f) for f in fichiers_presents):
        if any(ANCIEN_JOURNAL.match(f) for f in fichiers_presents):
            erreurs.append("le journal doit passer de decisions/ à registre/decisions/ : git mv decisions registre/decisions")
        else:
            erreurs.append("journal de décisions absent ou vide : registre/decisions/NNNN.md")
    if branche_protegee is False:
        erreurs.append("A1 : la branche principale n'est pas protégée (il faut un ruleset exigeant une pull request et bloquant le force-push)")

    if texte_fiche is not None:
        try:
            fiche = yaml.safe_load(texte_fiche)
            if not isinstance(fiche, dict):
                raise ValueError("la fiche n'est pas un dictionnaire")
        except Exception as exc:  # noqa: BLE001
            erreurs.append(f"memnius.yaml illisible : {exc}")
            fiche = None

    if fiche is not None:
        fiche = en_texte(fiche)
        erreurs += valider(fiche, SCHEMA_FICHE)
        if MARQUEURS_MODELE.search(texte_fiche):
            erreurs.append("memnius.yaml contient encore des valeurs du modèle à remplacer")
        if fiche.get("id") and nom_depot and fiche["id"] != nom_depot:
            erreurs.append(f"id « {fiche['id']} » différent du nom du dépôt « {nom_depot} »")
        for d in fiche.get("domaines") or []:
            if d not in (vocab.get("domaines") or {}):
                erreurs.append(f"domaine inconnu du vocabulaire : {d}")
        for o in fiche.get("outils") or []:
            if o not in (vocab.get("outils") or {}):
                avertissements.append(f"outil absent du vocabulaire : {o}")
        versions = ((vocab.get("socle") or {}).get("versions")) or []
        suivie = (fiche.get("socle") or {}).get("version")
        if versions and suivie and suivie not in versions:
            erreurs.append(f"version du socle inconnue : {suivie}")
        elif versions and suivie and suivie != versions[-1]:
            avertissements.append(f"suit le socle {suivie}, la version courante est {versions[-1]}")
        if derniere_activite and fiche.get("statut") == "actif":
            age = maintenant() - dt.datetime.fromisoformat(derniere_activite.replace("Z", "+00:00"))
            if age.days > JOURS_AVANT_DORMANT:
                avertissements.append(f"statut « actif » mais aucune activité depuis {age.days} jours")

    return fiche, {"niveau": niveau(erreurs, avertissements), "erreurs": erreurs, "avertissements": avertissements}


def niveau(erreurs, avertissements):
    return "non-conforme" if erreurs else ("avertissements" if avertissements else "conforme")


# ------------------------------------------------------------------ cartes et journal

ENTETE = re.compile(r"\A---[ \t]*\n(.*?\n)?---[ \t]*(?:\n|\Z)(.*)\Z", re.S)
CHAMP_JOURNAL = re.compile(r"^-\s*\**(Date|Origine|Décidé par|Remplace)\**\s*:\s*(.*)$", re.M)
CHAMP_JOURNAL_TOUS = re.compile(r"^-\s*\**(Date|Origine|Décidé par|Remplace|Options écartées|Source)\**\s*:.*$", re.M)
TITRE_JOURNAL = re.compile(r"^#\s+(\d{4})\s+[—–-]\s+(.+)$", re.M)
MARQUEUR = re.compile(r"\[(humain|choix|agent)\]")
LOGIN = re.compile(r"^@?([A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))$")


def lire_carte(texte):
    """Sépare l'en-tête YAML (entre deux lignes ---) du texte libre d'une carte."""
    m = ENTETE.match(texte.replace("\r\n", "\n"))
    if not m:
        raise ValueError("en-tête absent : la carte doit commencer par une ligne --- et l'en-tête finir par ---")
    entete = yaml.safe_load(m.group(1) or "")
    if not isinstance(entete, dict):
        raise ValueError("l'en-tête n'est pas une liste de champs « nom: valeur »")
    return en_texte(entete), m.group(2)


def premier_paragraphe(texte, longueur=300):
    """Le premier paragraphe de texte ; à défaut (texte écrit en liste à puces), la première puce."""
    coupe = lambda bloc: bloc if len(bloc) <= longueur else bloc[:longueur - 1].rstrip() + "…"  # noqa: E731
    for bloc in re.split(r"\n\s*\n", texte):
        bloc = " ".join(l.strip() for l in bloc.strip().splitlines())
        if bloc and not bloc.startswith(("#", "-", "*", "```", "<!--", "|")):
            return coupe(bloc)
    puce = re.search(r"^\s*[-*]\s+(.+)$", texte, re.M)
    return coupe(puce.group(1).strip()) if puce else ""


def carte_de_decision(fichier, texte):
    """Une entrée du journal lue comme carte de décision (format vérifié par la garde A4)."""
    champs = {m.group(1): m.group(2).strip() for m in CHAMP_JOURNAL.finditer(texte)}
    titre = TITRE_JOURNAL.search(texte)
    numero = ENTREE_JOURNAL.match(fichier).group(1)
    corps = CHAMP_JOURNAL_TOUS.sub("", TITRE_JOURNAL.sub("", texte, count=1))
    auteurs = [a.strip() for a in re.split(r",| et ", champs.get("Décidé par", "")) if a.strip()]
    carte = {
        "type": "decision",
        "id": f"decisions/{numero}",
        "fichier": fichier,
        "titre": f"{numero} — {titre.group(2).strip()}" if titre else numero,
        "resume": premier_paragraphe(corps),
        "ou": [fichier],
        "auteurs": [LOGIN.match(a).group(1) if LOGIN.match(a) else a for a in auteurs],
        "date": champs.get("Date", ""),
        "origine": sorted(set(MARQUEUR.findall(champs.get("Origine", "")))),
    }
    remplace = champs.get("Remplace", "")
    if remplace and remplace not in ("—", "-", "–"):
        carte["remplace"] = remplace
    return carte


def cartes_du_projet(dossier, fichiers):
    """Lit les cartes rangées et le journal. Renvoie (cartes, défauts de lecture)."""
    cartes, defauts = [], []
    for f in fichiers:
        if ENTREE_JOURNAL.match(f):
            cartes.append(carte_de_decision(f, (Path(dossier) / f).read_text(encoding="utf-8", errors="replace")))
            continue
        parties = PurePosixPath(f).parts
        if len(parties) != 3 or parties[0] != REGISTRE or parties[1] not in TYPES_RANGES:
            continue
        if parties[2] == ".gitkeep" or not parties[2].endswith(".md"):
            continue
        type_, nom = parties[1], parties[2][:-3]
        try:
            entete, _ = lire_carte((Path(dossier) / f).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            defauts.append(f"{f} : {exc}")
            continue
        carte = {"type": type_, "id": f"{type_}/{nom}", "fichier": f}
        for cle in ("titre", "resume", "ou", "auteurs"):
            carte[cle] = entete.get(cle)
        carte.update({k: v for k, v in sorted(entete.items()) if k not in carte})
        cartes.append(carte)
    ordre = list(TYPES)
    cartes.sort(key=lambda c: (ordre.index(c["type"]), c["id"]))
    marquer_remplacees(cartes)
    return cartes, defauts


def marquer_remplacees(cartes):
    """Une décision dont « Remplace » cite l'entrée NNNN : celle-ci reçoit « remplacee_par »."""
    decisions = {c["id"].split("/")[1]: c for c in cartes if c["type"] == "decision"}
    for c in cartes:
        if c["type"] != "decision" or not c.get("remplace"):
            continue
        for numero in re.findall(r"\b(\d{4})\b", c["remplace"]):
            cible = decisions.get(numero)
            if cible and cible is not c:
                cible.setdefault("remplacee_par", []).append(c["id"].split("/")[1])


def construire_index(dossier, fichiers=None):
    """Renvoie (index en dict, texte de INDEX.md, défauts de lecture). Aucune date de génération :
    le même état des cartes donne toujours le même index, ce qui permet de vérifier qu'il est à jour."""
    fichiers = lister_fichiers(dossier) if fichiers is None else fichiers
    cartes, defauts = cartes_du_projet(dossier, fichiers)
    fiche = {}
    meta = Path(dossier) / "memnius.yaml"
    if meta.exists():
        try:
            fiche = yaml.safe_load(meta.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            fiche = {}  # A3 signale la fiche illisible
    index = {
        "schema": "memnius-index/1",
        "projet": fiche.get("id") if isinstance(fiche, dict) else None,
        "titre": fiche.get("titre") if isinstance(fiche, dict) else None,
        "comptes": {t: sum(c["type"] == t for c in cartes) for t in TYPES},
        "cartes": cartes,
    }
    return index, index_markdown(index), defauts


def cellule(texte):
    return str(texte or "").replace("|", "\\|").replace("\n", " ").strip()


def qui(auteur):
    m = LOGIN.match(str(auteur))
    return f"@{m.group(1)}" if m else str(auteur)


def depuis_registre(fichier):
    """Lien relatif depuis registre/INDEX.md."""
    return fichier[len(REGISTRE) + 1:] if fichier.startswith(REGISTRE + "/") else f"../{fichier}"


def lien_ou(cible, prefixe):
    """Un emplacement cliquable : adresse web, ou chemin du dépôt relatif au fichier qui le cite (prefixe)."""
    if re.match(r"^https?://", cible):
        return f"[{urllib.parse.urlparse(cible).netloc or cible}]({cible})"
    if cible.startswith("drive:"):
        return f"`{cible}`"
    return f"[`{cible}`]({prefixe}{urllib.parse.quote(cible)})"


# Bloc de liens cliquables tenu par l'outil dans chaque carte, juste sous l'en-tête : GitHub affiche
# l'en-tête YAML en tableau, sans liens ; ce bloc rend cliquables les fichiers et cartes qu'elle cite.
DEBUT_LIENS = "<!-- memnius:liens : bloc généré par « memnius.py index », ne pas éditer -->"
FIN_LIENS = "<!-- /memnius:liens -->"
BLOC_LIENS = re.compile(r"<!-- memnius:liens\b.*?<!-- /memnius:liens -->\n*", re.S)


def en_liste(valeur):
    if valeur is None:
        return []
    return [v for v in (valeur if isinstance(valeur, list) else [valeur]) if isinstance(v, str) and v and A_REMPLIR not in v]


def bloc_liens(carte, fichiers_par_id):
    """Le bloc de liens d'une carte rangée, ou "" si elle ne cite rien."""
    dossier_carte = PurePosixPath(carte["fichier"]).parent
    prefixe = "../" * len(dossier_carte.parts)
    ou = [lien_ou(o, prefixe) for o in en_liste(carte.get("ou"))]
    ou += [lien_ou(u, prefixe) for u in en_liste(carte.get("url"))]
    ou += [f"[doi:{d}](https://doi.org/{d})" for d in en_liste(carte.get("doi"))]
    ou = list(dict.fromkeys(ou))  # une adresse citée dans ou et dans url n'apparaît qu'une fois
    liens = []
    for lien in en_liste(carte.get("liens")):
        cible = fichiers_par_id.get(lien)
        liens.append(f"[{lien}]({os.path.relpath(cible, dossier_carte)})" if cible else f"`{lien}`")
    if not ou and not liens:
        return ""
    lignes = [DEBUT_LIENS]
    if ou:
        lignes.append("- **Où :** " + " · ".join(ou))
    if liens:
        lignes.append("- **Liens :** " + " · ".join(liens))
    return "\n".join(lignes + ["", FIN_LIENS])


def avec_bloc_liens(texte, bloc):
    """Le texte de la carte, bloc de liens remplacé (ou retiré si bloc est vide), le reste intact."""
    texte = texte.replace("\r\n", "\n")
    m = ENTETE.match(texte)
    corps = BLOC_LIENS.sub("", m.group(2)).lstrip("\n")
    morceaux = [x for x in (bloc + "\n" if bloc else "", corps) if x]
    return texte[:m.start(2)] + "\n" + "\n".join(morceaux) if morceaux else texte[:m.start(2)]


def cartes_perimees(dossier, cartes):
    """{fichier : texte attendu} pour les cartes rangées dont le bloc de liens n'est pas à jour."""
    fichiers_par_id = {c["id"]: c["fichier"] for c in cartes}
    attendus = {}
    for c in cartes:
        if c["type"] == "decision":
            continue  # entrées du journal : jamais réécrites (C2, garde A4)
        texte = (Path(dossier) / c["fichier"]).read_text(encoding="utf-8")
        nouveau = avec_bloc_liens(texte, bloc_liens(c, fichiers_par_id))
        if nouveau != texte:
            attendus[c["fichier"]] = nouveau
    return attendus


def personnes(cartes):
    """Qui a fait quoi : {auteur affiché : [cartes]} (auteurs et contributeurs)."""
    par_personne = {}
    for c in cartes:
        for a in (c.get("auteurs") or []) + (c.get("contributeurs") or []):
            par_personne.setdefault(qui(a), []).append(c)
    return dict(sorted(par_personne.items(), key=lambda kv: kv[0].lstrip("@").lower()))


def pluriel(n, mot):
    return f"{n} {mot}{'s' if n > 1 else ''}"


def etat_carte(carte):
    """Mention ajoutée après le titre : statut autre que valide, ou décision remplacée."""
    if carte.get("remplacee_par"):
        return " (remplacée par " + ", ".join(carte["remplacee_par"]) + ")"
    if carte.get("statut") not in (None, "valide"):
        return f" ({carte['statut'].replace('a-relire', 'à relire')})"
    return ""


def index_markdown(index):
    cartes = index["cartes"]
    c = index["comptes"]
    titre = index.get("titre") or index.get("projet") or "ce projet"
    lignes = [
        f"# Index du registre — {titre}",
        "",
        "_Généré par `memnius.py index` à partir des cartes de `registre/` et du journal `registre/decisions/`. "
        "Ne pas éditer : modifier ou ajouter une carte, puis relancer l'outil._",
        "",
        f"{pluriel(len(cartes), 'carte')} : {pluriel(c['decision'], 'décision')}, {c['code']} code, "
        f"{c['donnees']} données, {pluriel(c['sources'], 'source')}, {pluriel(c['documents'], 'document')}.",
    ]
    for t, nom_type in TYPES.items():
        du_type = [x for x in cartes if x["type"] == t]
        lignes += ["", f"## {nom_type}", ""]
        if not du_type:
            lignes.append("_Aucune carte pour l'instant._")
            continue
        if t == "decision":
            lignes += ["| Carte | Résumé | Décidé par | Date |", "|---|---|---|---|"]
        else:
            lignes += ["| Carte | Résumé | Qui | Où | Date |", "|---|---|---|---|---|"]
        for x in du_type:
            etat = etat_carte(x)
            date = x.get("date") or ""
            if x.get("mis_a_jour"):
                date += f", revue {x['mis_a_jour']}"
            lignes.append("| " + " | ".join([
                f"[{cellule(x.get('titre') or x['id'])}]({depuis_registre(x['fichier'])}){etat}",
                cellule(x.get("resume")),
                ", ".join(qui(a) for a in x.get("auteurs") or []),
                *([] if t == "decision" else [", ".join(lien_ou(o, "../") for o in en_liste(x.get("ou")))]),
                date,
            ]) + " |")
    lignes += ["", "## Qui a fait quoi", ""]
    par_personne = personnes(cartes)
    if not par_personne:
        lignes.append("_Personne pour l'instant._")
    for p, siennes in par_personne.items():
        morceaux = []
        for t, nom_type in TYPES.items():
            liste = [x for x in siennes if x["type"] == t]
            if liste:
                morceaux.append(f"{nom_type.lower()} " + ", ".join(
                    f"[{x['id'].split('/')[-1]}]({depuis_registre(x['fichier'])})" for x in liste))
        lignes.append(f"- **{p}** : " + " ; ".join(morceaux))
    return "\n".join(lignes) + "\n"


def textes_index(index, markdown):
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n", markdown


def ecrire_index(dossier):
    index, markdown, defauts = construire_index(dossier)
    for f, texte in cartes_perimees(dossier, index["cartes"]).items():
        (Path(dossier) / f).write_text(texte, encoding="utf-8")
    texte_json, texte_md = textes_index(index, markdown)
    (Path(dossier) / REGISTRE).mkdir(exist_ok=True)
    (Path(dossier) / REGISTRE / "index.json").write_text(texte_json, encoding="utf-8")
    (Path(dossier) / REGISTRE / "INDEX.md").write_text(texte_md, encoding="utf-8")
    return index, defauts


def index_a_jour(dossier, fichiers=None):
    """Renvoie la liste des fichiers d'index absents ou périmés, et des cartes au bloc de liens périmé."""
    index, markdown, _ = construire_index(dossier, fichiers)
    attendus = dict(zip(("registre/index.json", "registre/INDEX.md"), textes_index(index, markdown)))
    perimes = sorted(cartes_perimees(dossier, index["cartes"]))
    for f, texte in attendus.items():
        p = Path(dossier) / f
        if not p.exists() or p.read_text(encoding="utf-8") != texte:
            perimes.append(f)
    return perimes


# ------------------------------------------------------------------ registre du projet (garde A7)


def verifier_registre(dossier, fichiers=None):
    """Contrôle le registre d'un projet. Renvoie (erreurs, avertissements)."""
    dossier = Path(dossier)
    fichiers = lister_fichiers(dossier) if fichiers is None else fichiers
    presents = set(fichiers)
    dossiers_presents = {str(PurePosixPath(f).parent) for f in fichiers}
    for f in list(dossiers_presents):
        dossiers_presents.update(str(p) for p in PurePosixPath(f).parents)
    erreurs, avertissements = [], []

    for f in FICHIERS_REGISTRE:
        if f not in presents:
            erreurs.append(f"fichier du registre absent : {f}")
    for t in DOSSIERS_EXIGES:
        if f"{REGISTRE}/{t}" not in dossiers_presents:
            erreurs.append(f"dossier du registre absent : {REGISTRE}/{t}/ (garder un .gitkeep s'il est vide)")
    for f in fichiers:
        parties = PurePosixPath(f).parts
        if parties[0] != REGISTRE or f in FICHIERS_REGISTRE + FICHIERS_INDEX or f.startswith(JOURNAL + "/"):
            continue  # le journal est contrôlé par la garde A4
        if len(parties) != 3 or parties[1] not in TYPES_RANGES:
            erreurs.append(f"{f} : hors de la structure commune (registre/decisions/, registre/code/, "
                           "registre/donnees/, registre/sources/, registre/documents/)")
        elif parties[2] != ".gitkeep" and not (parties[2].endswith(".md") and NOM_CARTE.match(parties[2][:-3])):
            erreurs.append(f"{f} : nom attendu registre/{parties[1]}/nom-en-minuscules.md")

    cartes, defauts = cartes_du_projet(dossier, fichiers)
    erreurs += defauts
    connues = {c["id"] for c in cartes}
    couverts = set()
    for c in cartes:
        if c["type"] == "decision":
            continue
        f = c["fichier"]
        entete = {k: v for k, v in c.items() if k not in ("type", "id", "fichier")}
        entete = {k: v for k, v in entete.items() if v is not None}
        erreurs += [f"{f} : {e}" for e in valider(entete, SCHEMA_CARTE)]
        if A_REMPLIR in json.dumps(entete, ensure_ascii=False):
            erreurs.append(f"{f} : valeurs « {A_REMPLIR} » à remplacer")
            continue
        hors_depot = [o for o in entete.get("ou") or [] if isinstance(o, str) and re.match(r"^(https?://|drive:)", o)]
        if c["type"] == "donnees" and hors_depot and not entete.get("empreinte"):
            erreurs.append(f"{f} : données rangées hors du dépôt ({hors_depot[0]}) : champ « empreinte » "
                           "(sha256:…) obligatoire, pour vérifier qu'on a le bon fichier")
        for champ, types_attendus in CHAMPS_PAR_TYPE.items():
            if champ in entete and c["type"] not in types_attendus:
                avertissements.append(f"{f} : le champ « {champ} » sert aux cartes {' ou '.join(types_attendus)}")
        for cible in entete.get("ou") or []:
            if not isinstance(cible, str) or re.match(r"^(https?://|drive:)", cible):
                continue
            chemin = PurePosixPath(cible.rstrip("/"))
            if chemin.is_absolute() or ".." in chemin.parts:
                erreurs.append(f"{f} : « {cible} » doit être un chemin relatif à la racine du dépôt")
            elif str(chemin) not in presents and str(chemin) not in dossiers_presents:
                erreurs.append(f"{f} : « {cible} » n'existe pas dans le dépôt")
            else:
                couverts.add(str(chemin))
        for lien in entete.get("liens") or []:
            if not isinstance(lien, str) or ":" in lien:
                continue  # lien vers un autre projet : vérifié par le super-registre, pas ici
            if lien not in connues:
                erreurs.append(f"{f} : lien vers une carte inconnue : {lien}")

    a_couvrir = zones_a_couvrir(dossier)
    orphelins = [f for f in fichiers if a_couvrir(f) and not any(f == c or f.startswith(c + "/") for c in couverts)]
    if orphelins:
        exemples = ", ".join(orphelins[:5]) + (f" (et {len(orphelins) - 5} autres)" if len(orphelins) > 5 else "")
        avertissements.append(f"{len(orphelins)} fichiers sans carte : {exemples}")
    return erreurs, avertissements


def zones_a_couvrir(dossier):
    """Fonction qui dit si un fichier devrait être décrit par une carte : selon registre.a_couvrir de
    memnius.yaml s'il est déclaré, sinon tout fichier rangé dans un dossier (voir HORS_COUVERTURE)."""
    declarees = None
    try:
        fiche = yaml.safe_load((Path(dossier) / "memnius.yaml").read_text(encoding="utf-8")) or {}
        declarees = ((fiche.get("registre") or {}).get("a_couvrir")) if isinstance(fiche, dict) else None
    except (OSError, yaml.YAMLError):
        pass
    if declarees is None:
        return lambda f: not HORS_COUVERTURE.search(f)
    zones = [str(z).strip("/") for z in declarees if str(z).strip("/")]
    return lambda f: not re.search(r"(^|/)(\.gitkeep|README\.md)$", f) and any(f == z or f.startswith(z + "/") for z in zones)


def remplir(texte, valeurs):
    for cle, valeur in valeurs.items():
        texte = texte.replace("{{" + cle + "}}", valeur)
    return texte


def nouvelle_carte(args):
    """Crée une carte à partir de son modèle (modeles/cartes/TYPE.md). Une décision est une entrée du journal."""
    if args.type not in TYPES_RANGES + ["decision"]:
        print(f"type inconnu : {args.type} (decision, code, donnees, sources ou documents)")
        return 2
    if not NOM_CARTE.match(args.nom):
        print("nom attendu en minuscules-avec-tirets, sans accents (ex. calcul-interfrange)")
        return 2
    dossier = Path(args.dossier)
    valeurs = {"titre": args.titre or A_REMPLIR, "date": dt.date.today().isoformat(),
               "ou": "[" + ", ".join(args.ou) + "]" if args.ou else f"[{A_REMPLIR}]",
               "auteurs": "[" + ", ".join(args.auteur) + "]" if args.auteur else f"[{A_REMPLIR}]"}
    if args.type == "decision":
        pris = [int(m.group(1)) for f in lister_fichiers(dossier) if (m := ENTREE_JOURNAL.match(f))]
        valeurs["numero"] = f"{max(pris, default=0) + 1:04d}"
        valeurs["auteurs"] = ", ".join("@" + a.lstrip("@") for a in args.auteur) or A_REMPLIR
        chemin = dossier / JOURNAL / f"{valeurs['numero']}-{args.nom}.md"
    else:
        chemin = dossier / REGISTRE / args.type / f"{args.nom}.md"
    if chemin.exists():
        print(f"{chemin} existe déjà")
        return 1
    texte = remplir((MODELES / "cartes" / f"{args.type}.md").read_text(encoding="utf-8"), valeurs)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(texte, encoding="utf-8")
    print(f"créée : {chemin} (remplacer les « {A_REMPLIR} » ; la CI régénère l'index après la fusion)")
    return 0


def init(args):
    """Ajoute à un dépôt de projet les fichiers que le socle exige, sans jamais remplacer un fichier existant."""
    dossier = Path(args.dossier).resolve()
    valeurs = {"id": args.id or dossier.name, "titre": args.titre or "TITRE_DU_PROJET",
               "mainteneur": (args.mainteneur or "IDENTIFIANT_GITHUB").lstrip("@"), "date": dt.date.today().isoformat()}
    modele = MODELES / "projet"
    journal = any(ENTREE_JOURNAL.match(f) for f in lister_fichiers(dossier))
    ajoutes = []
    for source in sorted(p for p in modele.rglob("*") if p.is_file()):
        rel = source.relative_to(modele).as_posix()
        if rel.startswith(JOURNAL + "/") and journal:
            continue  # le projet tient déjà un journal : on ne lui impose pas d'entrée 0001
        cible = dossier / rel
        if cible.exists():
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(remplir(source.read_text(encoding="utf-8"), valeurs), encoding="utf-8")
        ajoutes.append(rel)
    ecrire_index(dossier)
    for rel in ajoutes:
        print(f"ajouté : {rel}")
    print(f"{len(ajoutes)} fichiers ajoutés, index du registre écrit. À compléter : les valeurs en majuscules "
          f"de memnius.yaml (résumé, domaines), puis une carte par code, jeu de données ou source.")
    return 0


# ------------------------------------------------------------------ contrôle local


def git_local(dossier, *args):
    try:
        return subprocess.run(["git", "-C", str(dossier), *args], capture_output=True, text=True, check=True).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def url_web(distant):
    """git@github.com:org/depot.git ou https://github.com/org/depot.git → https://github.com/org/depot"""
    if not distant:
        return None
    distant = re.sub(r"^git@github\.com:", "https://github.com/", distant)
    return re.sub(r"\.git$", "", distant)


def entree_locale(dossier, vocab, registre=True):
    dossier = Path(dossier)
    texte = (dossier / "memnius.yaml").read_text(encoding="utf-8") if (dossier / "memnius.yaml").exists() else None
    activite = git_local(dossier, "log", "-1", "--format=%cI")
    fichiers = lister_fichiers(dossier)
    fiche, conformite = controler(texte, set(fichiers), dossier.name, vocab, activite)
    if registre:
        erreurs, avertissements = verifier_registre(dossier, fichiers)
        conformite["erreurs"] += [f"A7 : {e}" for e in erreurs]
        conformite["avertissements"] += avertissements
        conformite["niveau"] = niveau(conformite["erreurs"], conformite["avertissements"])
    index = None
    if (dossier / REGISTRE / "index.json").exists():
        try:
            index = json.loads((dossier / REGISTRE / "index.json").read_text(encoding="utf-8"))
        except ValueError:
            index = None
    return {
        "id": (fiche or {}).get("id") or dossier.name,
        "fiche": fiche,
        "depot": {
            "chemin": str(dossier),
            "url": url_web(git_local(dossier, "remote", "get-url", "origin")),
            "branche": git_local(dossier, "rev-parse", "--abbrev-ref", "HEAD"),
            "dernier_commit": git_local(dossier, "rev-parse", "HEAD"),
            "derniere_activite": activite,
            "archive_forge": False,
            "prive": False,
            "etoiles": None,
            "tickets_ouverts": None,
            "branche_protegee": None,
        },
        "conformite": conformite,
        "index": index,
        "modifications": modifications_locales(dossier),
    }


def verifier(args):
    dossier = Path(args.dossier).resolve()
    entree = entree_locale(dossier, charger_vocabulaire())
    c = entree["conformite"]
    for e in c["erreurs"]:
        print(f"ERREUR  {e}")
    for a in c["avertissements"]:
        print(f"ATTENTION  {a}")
    print(f"{dossier.name} : {c['niveau']}")
    return 1 if c["erreurs"] else 0


def index(args):
    dossier = Path(args.dossier).resolve()
    if args.verifier:
        perimes = index_a_jour(dossier)
        if perimes:
            print(f"index pas à jour : {', '.join(perimes)} ; lancer « python3 memnius.py index »")
            return 1
        print("index à jour")
        return 0
    idx, defauts = ecrire_index(dossier)
    for d in defauts:
        print(f"ATTENTION  carte illisible, laissée hors de l'index : {d}")
    c = idx["comptes"]
    print(f"registre/INDEX.md et registre/index.json écrits : {pluriel(len(idx['cartes']), 'carte')} "
          f"({pluriel(c['decision'], 'décision')}, {c['code']} code, {c['donnees']} données, {pluriel(c['sources'], 'source')}, "
          f"{pluriel(c['documents'], 'document')})")
    return 0


# --------------------------------------------------------------- super-registre : GitHub


class GitHub:
    def __init__(self, jeton, base="https://api.github.com"):
        self.base = base.rstrip("/")
        self.jeton = jeton
        self.appels = 0

    def get(self, chemin, brut=False, **params):
        url = chemin if chemin.startswith("http") else f"{self.base}{chemin}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        entetes = {"Accept": "application/vnd.github.raw" if brut else "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "memnius-registre"}
        if self.jeton:
            entetes["Authorization"] = f"Bearer {self.jeton}"
        for essai in (1, 2):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=30) as rep:
                    corps = rep.read()
                    self.appels += 1
                    return (corps.decode("utf-8") if brut else json.loads(corps)), rep.headers
            except urllib.error.HTTPError as exc:
                self.appels += 1
                if exc.code in (404, 409):  # 409 : dépôt vide
                    return None, {}
                attente = self.attente_quota(exc)
                if essai == 1 and attente is not None:
                    print(f"quota de l'API GitHub épuisé : attente de {attente} s")
                    time.sleep(attente)
                    continue
                raise

    @staticmethod
    def attente_quota(exc):
        """Secondes à attendre si l'erreur est un quota épuisé et que la remise à zéro est proche, sinon None."""
        if exc.code not in (403, 429):
            return None
        if exc.headers.get("Retry-After"):
            attente = int(exc.headers["Retry-After"])
        elif exc.headers.get("X-RateLimit-Remaining") == "0" and exc.headers.get("X-RateLimit-Reset"):
            attente = int(exc.headers["X-RateLimit-Reset"]) - int(time.time()) + 1
        else:
            return None
        return max(attente, 1) if attente <= ATTENTE_QUOTA_MAX else None

    def pages(self, chemin, **params):
        url, params = chemin, {"per_page": 100, **params}
        while url:
            donnees, entetes = self.get(url, **params)
            yield from donnees or []
            params = {}
            suivante = re.search(r'<([^>]+)>;\s*rel="next"', (entetes or {}).get("Link", "") or "")
            url = suivante.group(1) if suivante else None


def entree_github(gh, depot, vocab):
    nom, branche = depot["full_name"], depot.get("default_branch")
    fichiers, texte, commit, protegee, index, workflow, regles = set(), None, None, None, None, None, None
    # Ne pas se fier à depot["size"] : GitHub le calcule en différé et le laisse à 0 sur un dépôt récent.
    if branche:
        ref = urllib.parse.quote(branche, safe="")
        arbre, _ = gh.get(f"/repos/{nom}/git/trees/{ref}", recursive="1")
        fichiers = {e["path"] for e in (arbre or {}).get("tree", []) if e["type"] == "blob"}
        if "memnius.yaml" in fichiers:
            texte, _ = gh.get(f"/repos/{nom}/contents/memnius.yaml", brut=True, ref=branche)
        if "registre/index.json" in fichiers:
            brut, _ = gh.get(f"/repos/{nom}/contents/registre/index.json", brut=True, ref=branche)
            try:
                index = json.loads(brut) if brut else None
            except ValueError:
                index = None
        info, _ = gh.get(f"/repos/{nom}/commits/{ref}")
        commit = (info or {}).get("sha")
        # Garde A1 : le ruleset actif sur la branche doit être complet (voir manques_a1).
        regles, _ = gh.get(f"/repos/{nom}/rules/branches/{ref}")
        manques = manques_a1(regles)
        if not regles:
            protegee = None if depot.get("private") else False  # rulesets indisponibles sur un dépôt privé en offre gratuite
        else:
            protegee = not manques
        if WORKFLOW_PROJET in fichiers:
            workflow, _ = gh.get(f"/repos/{nom}/contents/{WORKFLOW_PROJET}", brut=True, ref=branche)
    fiche, conformite = controler(texte, fichiers, depot["name"], vocab, depot.get("pushed_at"),
                                  False if protegee is False and not regles else None)
    if protegee is None and depot.get("private"):
        conformite["avertissements"].append("A1 non vérifiable : dépôt privé, rulesets réservés aux offres payantes")
    elif protegee is False and regles:
        conformite["erreurs"].append("A1 : ruleset de la branche principale incomplet : " + "; ".join(manques)
                                     + " (relancer publier-projet.sh NOM --regler)")
    if branche:
        defaut = controle_workflow(workflow, nom.split("/")[0])
        if defaut:
            conformite["erreurs"].append(defaut)
    if index is None or index.get("schema") != "memnius-index/1":
        conformite["erreurs"].append("A7 : registre du projet absent ou illisible (registre/index.json)")
        index = None
    declaree = (fiche or {}).get("visibilite")
    reelle = "prive" if depot.get("private") else "public"
    if declaree and declaree != reelle:
        conformite["avertissements"].append(f"visibilité déclarée « {declaree} », réelle « {reelle} »")
    conformite["niveau"] = niveau(conformite["erreurs"], conformite["avertissements"])
    return {
        "id": depot["name"],
        "fiche": fiche,
        "depot": {
            "chemin": nom,
            "url": depot["html_url"],
            "branche": branche,
            "dernier_commit": commit,
            "derniere_activite": depot.get("pushed_at"),
            "archive_forge": bool(depot.get("archived")),
            "prive": bool(depot.get("private")),
            "etoiles": depot.get("stargazers_count"),
            "tickets_ouverts": depot.get("open_issues_count"),
            "branche_protegee": protegee,
        },
        "conformite": conformite,
        "index": index,
        # Les dernières modifications ne servent qu'à la page d'accueil, où un projet privé ne figure jamais.
        "modifications": modifications_github(gh, nom, branche) if branche and not depot.get("private") else [],
    }


def manques_a1(regles):
    """Ce qui manque au ruleset de la branche principale pour la garde A1 (liste vide : complet). regles est la
    réponse de /repos/{depot}/rules/branches/{branche}."""
    types = {r.get("type") for r in regles or []}
    manques = [f"règle {t} absente" for t in sorted(REGLES_A1 - types)]
    exiges = {c.get("context") for r in regles or [] if r.get("type") == "required_status_checks"
              for c in (r.get("parameters") or {}).get("required_status_checks") or []}
    if "required_status_checks" in types:
        manques += [f"contrôle « {c} » non exigé" for c in CONTROLES_REQUIS if c not in exiges]
    return manques


def controle_workflow(texte, organisation):
    """Un projet appelle les gardes du socle par son workflow : sans lui, le contrôle requis par le ruleset
    peut être imité par un autre job du même nom. Renvoie le défaut, ou None."""
    if texte is None:
        return f"A3 : {WORKFLOW_PROJET} absent de la branche principale"
    attendu = re.compile(rf"^\s*uses:\s*{re.escape(organisation)}/registre/\.github/workflows/gardes\.yml@\S+", re.M | re.I)
    if not re.search(r"^\s{2}gardes:\s*$", texte, re.M) or not attendu.search(texte):
        return (f"A1 : {WORKFLOW_PROJET} n'appelle plus les gardes du socle (job « gardes » qui utilise "
                f"{organisation}/registre/.github/workflows/gardes.yml) : le contrôle requis ne prouve plus rien")
    return None


# --------------------------------------------- super-registre : dernières modifications des registres


def est_carte(fichier):
    """Vrai pour une entrée du journal ou une carte rangée ; faux pour l'index, le README et les .gitkeep."""
    parties = PurePosixPath(fichier).parts
    return bool(ENTREE_JOURNAL.match(fichier)) or (
        len(parties) == 3 and parties[0] == REGISTRE and parties[1] in TYPES_RANGES and parties[2].endswith(".md"))


def est_robot(*noms):
    return any("[bot]" in (n or "") for n in noms)


def changements(commit):
    """Un commit (sha, date, auteur, [(statut, fichier)]) → une modification par carte touchée."""
    return [{"sha": commit["sha"], "date": commit["date"], "auteur": commit["auteur"], "agent": commit.get("agent", False),
             "statut": statut, "fichier": f} for statut, f in commit["fichiers"] if est_carte(f)]


STATUTS_GIT = {"A": "ajoutée", "M": "modifiée", "D": "supprimée", "R": "renommée", "C": "ajoutée"}
STATUTS_GITHUB = {"added": "ajoutée", "modified": "modifiée", "changed": "modifiée", "removed": "supprimée",
                  "renamed": "renommée", "copied": "ajoutée"}


def modifications_locales(dossier, n=NB_MODIFICATIONS):
    """Dernières cartes ajoutées, modifiées ou supprimées d'un clone, d'après git log (fusions et robots exclus)."""
    sortie = git_local(dossier, "log", "--no-merges", "-n", str(4 * n),
                       "--format=%x1e%H%x1f%aI%x1f%an%x1f%ae%x1f%(trailers:key=Assisted-by,valueonly,separator=%x2C)",
                       "--name-status", "--", REGISTRE)
    modifications = []
    for bloc in (sortie or "").split("\x1e"):
        lignes = [l for l in bloc.strip().splitlines() if l.strip()]
        if not lignes:
            continue
        sha, date, nom, courriel, agent = lignes[0].split("\x1f")
        if est_robot(nom, courriel):
            continue
        fichiers = []
        for l in lignes[1:]:
            champs = l.split("\t")
            fichiers.append((STATUTS_GIT.get(champs[0][:1], "modifiée"), champs[-1]))
        modifications += changements({"sha": sha, "date": date, "auteur": nom, "agent": bool(agent.strip()),
                                      "fichiers": fichiers})
        if len(modifications) >= n:
            break
    return modifications[:n]


def modifications_github(gh, nom, branche, n=NB_MODIFICATIONS):
    """Même chose par l'API GitHub : derniers commits touchant registre/, puis leurs fichiers."""
    commits, _ = gh.get(f"/repos/{nom}/commits", sha=branche, path=REGISTRE, per_page=2 * n)
    modifications = []
    for c in commits or []:
        auteur = c.get("author") or {}
        nom_git = ((c.get("commit") or {}).get("author") or {}).get("name")
        if len(c.get("parents") or []) > 1 or auteur.get("type") == "Bot" or est_robot(auteur.get("login"), nom_git):
            continue
        detail, _ = gh.get(f"/repos/{nom}/commits/{c['sha']}")
        fichiers = [(STATUTS_GITHUB.get(f.get("status"), "modifiée"), f["filename"]) for f in (detail or {}).get("files") or []]
        # Seul l'identifiant GitHub est publié : le nom Git d'un commit sans compte est souvent un nom civil (C7).
        message = (c.get("commit") or {}).get("message") or ""
        modifications += changements({"sha": c["sha"], "date": c["commit"]["author"]["date"],
                                      "auteur": auteur.get("login"), "agent": bool(re.search(r"(?im)^Assisted-by:", message)),
                                      "fichiers": fichiers})
        if len(modifications) >= n:
            break
    return modifications[:n]


def instant(date):
    try:
        return dt.datetime.fromisoformat(str(date).replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    except ValueError:
        return dt.datetime.min.replace(tzinfo=dt.timezone.utc)


def public(projet):
    """Un projet privé, réellement ou par sa fiche, n'apparaît jamais sur la page d'accueil (C7)."""
    return not projet["depot"].get("prive") and (projet["fiche"] or {}).get("visibilite") != "prive"


def dernieres_modifications(projets, n=NB_MODIFICATIONS):
    """Les n dernières modifications de cartes de tous les projets publics, la plus récente d'abord."""
    lignes = []
    for p in projets:
        if not public(p):
            continue
        cartes = {c["fichier"]: c for c in (p["index"] or {}).get("cartes", [])}
        url = p["depot"].get("url")
        for m in p.get("modifications") or []:
            carte = cartes.get(m["fichier"])
            type_ = "decision" if ENTREE_JOURNAL.match(m["fichier"]) else PurePosixPath(m["fichier"]).parts[1]
            if carte and m["statut"] != "supprimée":
                lien = f"[{cellule(carte.get('titre') or carte['id'])}]({url_fichier(p, m['fichier'])})"
            else:
                nom = PurePosixPath(m["fichier"]).stem
                lien = f"[`{nom}`]({url}/commit/{m['sha']})" if url else f"`{nom}`"
            lignes.append((instant(m["date"]), p["id"], lien, TYPE_SINGULIER[type_], m["statut"], m["auteur"], m.get("agent")))
    lignes.sort(key=lambda l: l[0], reverse=True)
    return lignes[:n]


def ecrire_accueil(registre, chemin, organisation=None):
    """Page d'accueil de l'organisation : partie fixe (modeles/accueil.md) puis dernières modifications."""
    lignes = dernieres_modifications(registre["projets"])
    if lignes:
        tableau = ["| Date | Projet | Carte | Type | Changement | Par |", "|---|---|---|---|---|---|"]
        tableau += [f"| {d:%Y-%m-%d} | {projet} | {lien} | {type_} | {statut} | "
                    f"{cellule(qui(auteur)) if auteur else '—'}{' 🤖' if agent else ''} |"
                    for d, projet, lien, type_, statut, auteur, agent in lignes]
        tableau += ["", f"_Les {len(lignes)} dernières cartes et décisions ajoutées ou modifiées dans les registres "
                        "des projets publics, d'après leur historique Git. 🤖 : commit fait avec un agent (ligne "
                        "`Assisted-by`) ; — : commit sans compte GitHub. Toutes les cartes : "
                        "[`CARTES.md`](https://github.com/Memnius-PEE/registre/blob/super-registre/CARTES.md)._"]
        partie = "\n".join(tableau)
    else:
        partie = "_Aucune carte ni décision dans les registres des projets pour l'instant._"
    texte = MODELE_ACCUEIL.read_text(encoding="utf-8").replace("{{DERNIERES_MODIFICATIONS}}", partie)
    if organisation:
        texte = texte.replace("Memnius-PEE", organisation)
    chemin.write_text(texte.rstrip("\n") + "\n", encoding="utf-8")


# ------------------------------------------------------------------ super-registre : sorties


def url_fichier(projet, fichier):
    d = projet["depot"]
    if (d.get("url") or "").startswith("https://github.com/") and d.get("branche"):
        return f"{d['url']}/blob/{d['branche']}/{fichier}"
    return f"{d['chemin']}/{fichier}"


def relier(projets):
    """Ajoute l'adresse de chaque carte et vérifie les liens entre projets."""
    ids = {p["id"] for p in projets}
    cartes_par_projet = {p["id"]: {c["id"] for c in (p["index"] or {}).get("cartes", [])} for p in projets}
    for p in projets:
        avert = p["conformite"]["avertissements"]
        for lien in ((p["fiche"] or {}).get("liens") or {}).get("projets") or []:
            if lien.get("id") not in ids:
                avert.append(f"lien vers un projet inconnu : {lien.get('id')}")
        for c in (p["index"] or {}).get("cartes", []):
            c["url"] = url_fichier(p, c["fichier"])
            for lien in c.get("liens") or []:
                if ":" in lien:
                    autre, carte = lien.split(":", 1)
                    if autre not in ids or carte not in cartes_par_projet[autre]:
                        avert.append(f"{c['fichier']} : lien vers une carte inconnue d'un autre projet : {lien}")
        p["conformite"]["niveau"] = niveau(p["conformite"]["erreurs"], avert)


def ecrire_registre_md(registre, chemin, note_prives=None):
    vocab = charger_vocabulaire().get("domaines") or {}
    icones = {"conforme": "✅", "avertissements": "⚠️", "non-conforme": "❌"}
    lignes = [
        "# Registre des projets Memnius",
        "",
        f"_Généré le {registre['genere_le']} depuis `{registre['source']}`. Ne pas éditer : chaque projet "
        "tient sa fiche (`memnius.yaml`) et son registre (`registre/`). Toutes les cartes : [CARTES.md](CARTES.md)._",
        "",
        "| Projet | Statut | Domaines | Mainteneur·ices | " + " | ".join(TYPES.values()) + " | Socle | Dernière activité | Conformité |",
        "|---|---|---|---|" + "---|" * len(TYPES) + "---|---|---|",
    ]
    if note_prives:
        lignes[3:3] = [f"_{note_prives}_", ""]
    for p in sorted(registre["projets"], key=lambda p: p["id"]):
        f = p["fiche"] or {}
        titre = cellule(f.get("titre") or p["id"])
        lien = f"[{titre}]({p['depot']['url']})" if p["depot"].get("url") else titre
        domaines = ", ".join(vocab.get(d, d) for d in f.get("domaines") or [])
        mainteneurs = ", ".join("@" + m["github"] for m in f.get("mainteneurs") or [] if isinstance(m, dict) and "github" in m)
        if p["index"]:
            index_url = url_fichier(p, "registre/INDEX.md")
            comptes = [f"[{p['index']['comptes'].get(t, 0)}]({index_url})" for t in TYPES]
        else:
            comptes = ["—"] * len(TYPES)
        socle = f.get("socle") or {}
        options = ", ".join(socle.get("options") or []) if socle else ""
        socle = f"{socle.get('version', '?')}" + (f" ({options})" if options else "") if socle else ""
        activite = (p["depot"].get("derniere_activite") or "")[:10]
        lignes.append("| " + " | ".join([lien, f.get("statut", "?"), domaines, mainteneurs, *comptes, socle, activite,
                                          icones[p["conformite"]["niveau"]]]) + " |")
    problemes = [p for p in registre["projets"] if p["conformite"]["niveau"] != "conforme"]
    if problemes:
        lignes += ["", "## À corriger", ""]
        for p in problemes:
            lignes += [f"- **{p['id']}** ❌ {e}" for e in p["conformite"]["erreurs"]]
            lignes += [f"- **{p['id']}** ⚠️ {a}" for a in p["conformite"]["avertissements"]]
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def ecrire_cartes_md(registre, chemin):
    toutes = [(p, c) for p in sorted(registre["projets"], key=lambda p: p["id"]) for c in (p["index"] or {}).get("cartes", [])]
    lignes = [
        "# Toutes les cartes des projets Memnius",
        "",
        f"_Généré le {registre['genere_le']} à partir du `registre/index.json` de chaque projet. "
        "Ne pas éditer. Vue par projet : [REGISTRE.md](REGISTRE.md). Chercher un mot dans toutes les cartes : "
        "recherche de code GitHub `org:Memnius-PEE path:registre/ le-mot`._",
    ]
    for t, nom_type in TYPES.items():
        du_type = [(p, c) for p, c in toutes if c["type"] == t]
        lignes += ["", f"## {nom_type} ({len(du_type)})", ""]
        if not du_type:
            lignes.append("_Aucune carte._")
            continue
        if t == "decision":
            lignes += ["| Projet | Carte | Résumé | Qui |", "|---|---|---|---|"]
        else:
            lignes += ["| Projet | Carte | Résumé | Qui | Où | Mots-clés |", "|---|---|---|---|---|---|"]
        for p, c in du_type:
            ou = [] if t == "decision" else [", ".join(
                lien_ou(o, "") if re.match(r"^(https?://|drive:)", o) else f"[`{o}`]({url_fichier(p, o.rstrip('/'))})"
                for o in en_liste(c.get("ou"))), cellule(", ".join(en_liste(c.get("mots_cles"))))]
            lignes.append("| " + " | ".join([p["id"], f"[{cellule(c.get('titre') or c['id'])}]({c['url']}){etat_carte(c)}",
                                             cellule(c.get("resume")), ", ".join(qui(a) for a in c.get("auteurs") or []),
                                             *ou]) + " |")
    lignes += ["", "## Qui a fait quoi", "", "| Personne | Projet | " + " | ".join(TYPES.values()) + " |",
               "|---|---|" + "---|" * len(TYPES)]
    par_personne = {}
    for p, c in toutes:
        for a in (c.get("auteurs") or []) + (c.get("contributeurs") or []):
            par_personne.setdefault(qui(a), {}).setdefault(p["id"], []).append(c)
    for personne in sorted(par_personne, key=lambda x: x.lstrip("@").lower()):
        for projet, siennes in sorted(par_personne[personne].items()):
            cases = []
            for t in TYPES:
                liste = [c for c in siennes if c["type"] == t]
                cases.append(", ".join(f"[{c['id'].split('/')[-1]}]({c['url']})" for c in liste))
            lignes.append(f"| {personne} | {projet} | " + " | ".join(cases) + " |")
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def entree_illisible(depot, exc):
    """Un projet que l'API n'a pas pu lire : une ligne ❌ au lieu de faire tomber toute la passe."""
    return {
        "id": depot["name"], "fiche": None,
        "depot": {"chemin": depot["full_name"], "url": depot.get("html_url"), "branche": depot.get("default_branch"),
                  "dernier_commit": None, "derniere_activite": depot.get("pushed_at"), "archive_forge": bool(depot.get("archived")),
                  "prive": bool(depot.get("private")), "etoiles": None, "tickets_ouverts": None, "branche_protegee": None},
        "conformite": {"niveau": "non-conforme", "erreurs": [f"non lu : {type(exc).__name__} : {exc}"], "avertissements": []},
        "index": None, "modifications": [],
    }


def verifier_auteurs(gh, projets):
    """Un auteur de carte écrit comme un identifiant GitHub doit exister : une faute de frappe créerait sinon
    une nouvelle « personne » dans « Qui a fait quoi ». Avertissement seulement, un appel par identifiant."""
    connus = {}
    for p in projets:
        for c in (p["index"] or {}).get("cartes", []):
            for a in (c.get("auteurs") or []) + (c.get("contributeurs") or []):
                m = LOGIN.match(str(a))
                if not m or " " in str(a):
                    continue  # nom d'une personne sans compte : accepté tel quel
                login = m.group(1).lower()
                if login not in connus:
                    utilisateur, _ = gh.get(f"/users/{login}")
                    connus[login] = utilisateur is not None
                if not connus[login]:
                    p["conformite"]["avertissements"].append(f"{c['fichier']} : auteur inconnu de GitHub : {a}")
        p["conformite"]["niveau"] = niveau(p["conformite"]["erreurs"], p["conformite"]["avertissements"])


def ecrire_sorties(registre, sortie, organisation, note_prives=None):
    sortie.mkdir(parents=True, exist_ok=True)
    (sortie / "registre.json").write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ecrire_registre_md(registre, sortie / "REGISTRE.md", note_prives)
    ecrire_cartes_md(registre, sortie / "CARTES.md")
    ecrire_accueil(registre, sortie / "ACCUEIL.md", organisation)


def construire_registre(args):
    vocab = charger_vocabulaire()
    if args.local:
        racine = Path(args.local)
        projets = [entree_locale(d, vocab) for d in sorted(racine.iterdir()) if d.is_dir() and not d.name.startswith(".")]
        for p in projets:  # comme en mode GitHub : sans index (écrit par la CI, C11), le projet n'est pas lisible
            if p["index"] is None or p["index"].get("schema") != "memnius-index/1":
                p["index"] = None
                p["conformite"]["erreurs"].append("A7 : registre du projet absent ou illisible (registre/index.json)")
                p["conformite"]["niveau"] = niveau(p["conformite"]["erreurs"], p["conformite"]["avertissements"])
        source = str(racine)
    else:
        gh = GitHub(os.environ.get("GITHUB_TOKEN", ""), os.environ.get("GITHUB_API_URL", "https://api.github.com"))
        projets = []
        for org in args.github:
            proprietaire, _ = gh.get(f"/users/{org}")
            liste = f"/orgs/{org}/repos" if (proprietaire or {}).get("type") != "User" else f"/users/{org}/repos"
            depots = [d for d in gh.pages(liste, type="all") if SUJET_GITHUB in (d.get("topics") or [])]
            for d in depots:
                try:
                    projets.append(entree_github(gh, d, vocab))
                except Exception as exc:  # noqa: BLE001 — un projet illisible ne fait pas tomber les autres
                    print(f"ATTENTION  {d['full_name']} non lu : {exc}")
                    projets.append(entree_illisible(d, exc))
        verifier_auteurs(gh, projets)
        source = ", ".join(f"https://github.com/{o}" for o in args.github)
        print(f"{gh.appels} appels à l'API GitHub")
    relier(projets)
    organisation = args.github[0] if args.github and len(args.github) == 1 else None
    genere_le = maintenant().isoformat()
    publics = [p for p in projets if public(p)]
    prives = len(projets) - len(publics)
    lecture = os.environ.get("MEMNIUS_LECTURE", "")
    if lecture == "workflow":
        note = ("Les projets privés ne sont pas lus : l'App `memnius-registre` n'est pas installée "
                "(variable `MEMNIUS_APP_ID` absente).")
    else:
        note = f"{pluriel(prives, 'projet privé')} non publié{'s' if prives > 1 else ''} ici (C7)." if prives else None
    # Les sorties publiques (branche super-registre d'un dépôt public, page d'accueil) ne contiennent jamais
    # un projet privé ; la vue complète ne s'écrit qu'à la demande, pour un dépôt privé.
    ecrire_sorties({"schema": "memnius-registre/2", "genere_le": genere_le, "source": source, "projets": publics},
                   Path(args.sortie), organisation, note)
    if args.complet:
        ecrire_sorties({"schema": "memnius-registre/2", "genere_le": genere_le, "source": source, "projets": projets},
                       Path(args.complet), organisation)
    nb = {n: sum(p["conformite"]["niveau"] == n for p in projets) for n in ("conforme", "avertissements", "non-conforme")}
    cartes = sum(len((p["index"] or {}).get("cartes", [])) for p in projets)
    print(f"{len(projets)} projets ({prives} privés), {cartes} cartes : {nb['conforme']} conformes, "
          f"{nb['avertissements']} avec avertissements, {nb['non-conforme']} non conformes")
    illisibles = [p["id"] for p in projets if any(e.startswith("non lu :") for e in p["conformite"]["erreurs"])]
    if illisibles:
        print(f"ATTENTION  projets non lus : {', '.join(illisibles)}")
        return 3  # sorties écrites, mais la passe est incomplète : le workflow le signale
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="commande", required=True)
    v = sp.add_parser("verifier", help="contrôler un dépôt de projet (gardes A3 et A7)")
    v.add_argument("dossier", nargs="?", default=".")
    i = sp.add_parser("index", help="régénérer l'index du registre d'un projet")
    i.add_argument("dossier", nargs="?", default=".")
    i.add_argument("--verifier", action="store_true", help="ne rien écrire, dire si l'index est à jour")
    n = sp.add_parser("init", help="ajouter à un projet les fichiers que le socle exige")
    n.add_argument("dossier", nargs="?", default=".")
    n.add_argument("--id", help="identifiant du projet (par défaut : nom du dossier)")
    n.add_argument("--titre")
    n.add_argument("--mainteneur", help="identifiant GitHub du mainteneur")
    c = sp.add_parser("carte", help="créer une carte à partir de son modèle")
    c.add_argument("type", help="decision, code, donnees, sources ou documents")
    c.add_argument("nom", help="nom du fichier, en minuscules-avec-tirets")
    c.add_argument("--dossier", default=".")
    c.add_argument("--titre")
    c.add_argument("--ou", action="append", default=[], help="chemin ou adresse (répétable)")
    c.add_argument("--auteur", action="append", default=[], help="identifiant GitHub (répétable)")
    r = sp.add_parser("registre", help="construire le super-registre de l'organisation")
    src = r.add_mutually_exclusive_group(required=True)
    src.add_argument("--local", help="dossier contenant un clone par projet")
    src.add_argument("--github", action="append", help="organisation GitHub des projets (répétable)")
    r.add_argument("--sortie", default=".", help="dossier où écrire REGISTRE.md, CARTES.md, registre.json et ACCUEIL.md (publics)")
    r.add_argument("--complet", help="dossier où écrire aussi la vue complète, projets privés compris (pour un dépôt privé)")
    args = p.parse_args()
    return {"verifier": verifier, "index": index, "init": init, "carte": nouvelle_carte, "registre": construire_registre}[args.commande](args)


if __name__ == "__main__":
    sys.exit(main())
