#!/usr/bin/env python3
"""Outil commun Memnius : registre de chaque projet (cartes et index) et super-registre de l'organisation.

Usage :
  python3 memnius.py verifier [DOSSIER]
      Contrôle un dépôt de projet : structure (garde A3) et registre (garde A7).
  python3 memnius.py index [DOSSIER] [--verifier]
      Régénère registre/INDEX.md et registre/index.json à partir des cartes et du journal
      registre/decisions/, et met à jour dans chaque carte le bloc de liens cliquables vers ce qu'elle cite.
      Avec --verifier, n'écrit rien et sort en erreur si l'index ou un bloc de liens n'est pas à jour.
      En CI, le workflow des gardes le lance sur chaque pull request et commite le résultat (règle C11).
  python3 memnius.py init [DOSSIER] [--id ID] [--titre T] [--mainteneur LOGIN]
      Ajoute à un dépôt de projet les fichiers que le socle exige (modeles/projet/), sans rien remplacer.
  python3 memnius.py carte TYPE NOM [--dossier D] [--titre T] [--ou CHEMIN]… [--auteur LOGIN]…
      Crée une carte à remplir à partir de son modèle (modeles/cartes/) : registre/TYPE/NOM.md pour
      code, donnees ou sources ; registre/decisions/NNNN-NOM.md (numéro suivant) pour une décision.
  python3 memnius.py registre --github ORG [--github AUTRE] [--sortie DIR]
  python3 memnius.py registre --local DOSSIER-DES-CLONES [--sortie DIR]
      Construit le super-registre : REGISTRE.md (les projets), CARTES.md (toutes les cartes, et qui a
      fait quoi) et registre.json. Un dépôt de l'organisation est un projet s'il porte le topic GitHub
      « memnius-projet ». Jeton lu dans GITHUB_TOKEN (facultatif si tous les dépôts sont publics).

Tout le registre vit dans registre/ : les cartes de décision sont les entrées du journal registre/decisions/,
les autres cartes sont rangées dans registre/code/, registre/donnees/ et registre/sources/.
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
TYPES = {"decision": "Décisions", "code": "Code", "donnees": "Données", "sources": "Sources"}
TYPES_RANGES = ["code", "donnees", "sources"]  # les décisions sont les entrées de registre/decisions/
FICHIERS_REGISTRE = ["registre/README.md"]
FICHIERS_INDEX = ["registre/INDEX.md", "registre/index.json"]  # écrits par la CI (C11), non contrôlés par A7
NOM_CARTE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
A_REMPLIR = "À_REMPLIR"
CHAMPS_PAR_TYPE = {"langage": "code", "commande": "code", "format": "donnees", "taille": "donnees",
                   "empreinte": "donnees", "reference": "sources", "cle_bib": "sources", "doi": "sources"}
# Fichiers qu'une carte devrait couvrir (avertissement seulement) : le code et les données.
A_COUVRIR = re.compile(r"^(travaux|donnees)/")
HORS_COUVERTURE = re.compile(r"(^|/)(\.gitkeep|README\.md)$")

SUJET_GITHUB = "memnius-projet"  # topic GitHub qui marque un dépôt de projet dans l'organisation


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
        erreurs.append(f"{chemin} : {e.message}")
    return erreurs


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
    for bloc in re.split(r"\n\s*\n", texte):
        bloc = " ".join(l.strip() for l in bloc.strip().splitlines())
        if bloc and not bloc.startswith(("#", "-", "```", "<!--", "|")):
            return bloc if len(bloc) <= longueur else bloc[:longueur - 1].rstrip() + "…"
    return ""


def carte_de_decision(fichier, texte):
    """Une entrée du journal lue comme carte de décision (format vérifié par la garde A4)."""
    champs = {m.group(1): m.group(2).strip() for m in CHAMP_JOURNAL.finditer(texte)}
    titre = TITRE_JOURNAL.search(texte)
    numero = ENTREE_JOURNAL.match(fichier).group(1)
    corps = CHAMP_JOURNAL.sub("", TITRE_JOURNAL.sub("", texte, count=1))
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
    return cartes, defauts


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
        f"{c['donnees']} données, {pluriel(c['sources'], 'source')}.",
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
            etat = f" ({x['statut'].replace('a-relire', 'à relire')})" if x.get("statut") not in (None, "valide") else ""
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
    for t in TYPES_RANGES:
        if f"{REGISTRE}/{t}" not in dossiers_presents:
            erreurs.append(f"dossier du registre absent : {REGISTRE}/{t}/ (garder un .gitkeep s'il est vide)")
    for f in fichiers:
        parties = PurePosixPath(f).parts
        if parties[0] != REGISTRE or f in FICHIERS_REGISTRE + FICHIERS_INDEX or f.startswith(JOURNAL + "/"):
            continue  # le journal est contrôlé par la garde A4
        if len(parties) != 3 or parties[1] not in TYPES_RANGES:
            erreurs.append(f"{f} : hors de la structure commune (registre/decisions/, registre/code/, "
                           "registre/donnees/, registre/sources/)")
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
        for champ, type_attendu in CHAMPS_PAR_TYPE.items():
            if champ in entete and c["type"] != type_attendu:
                avertissements.append(f"{f} : le champ « {champ} » sert aux cartes {type_attendu}")
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

    orphelins = [f for f in fichiers if A_COUVRIR.match(f) and not HORS_COUVERTURE.search(f)
                 and not any(f == c or f.startswith(c + "/") for c in couverts)]
    if orphelins:
        exemples = ", ".join(orphelins[:5]) + (f" (et {len(orphelins) - 5} autres)" if len(orphelins) > 5 else "")
        avertissements.append(f"{len(orphelins)} fichiers de travaux/ ou donnees/ sans carte : {exemples}")
    return erreurs, avertissements


def remplir(texte, valeurs):
    for cle, valeur in valeurs.items():
        texte = texte.replace("{{" + cle + "}}", valeur)
    return texte


def nouvelle_carte(args):
    """Crée une carte à partir de son modèle (modeles/cartes/TYPE.md). Une décision est une entrée du journal."""
    if args.type not in TYPES_RANGES + ["decision"]:
        print(f"type inconnu : {args.type} (decision, code, donnees ou sources)")
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
    print(f"créée : {chemin} (remplacer les « {A_REMPLIR} » ; la CI régénère l'index sur la pull request)")
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
            "etoiles": None,
            "tickets_ouverts": None,
            "branche_protegee": None,
        },
        "conformite": conformite,
        "index": index,
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
          f"({pluriel(c['decision'], 'décision')}, {c['code']} code, {c['donnees']} données, {pluriel(c['sources'], 'source')})")
    return 0


# --------------------------------------------------------------- super-registre : GitHub


class GitHub:
    def __init__(self, jeton, base="https://api.github.com"):
        self.base = base.rstrip("/")
        self.jeton = jeton

    def get(self, chemin, brut=False, **params):
        url = chemin if chemin.startswith("http") else f"{self.base}{chemin}"
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
        entetes = {"Accept": "application/vnd.github.raw" if brut else "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "memnius-registre"}
        if self.jeton:
            entetes["Authorization"] = f"Bearer {self.jeton}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=30) as rep:
                corps = rep.read()
                return (corps.decode("utf-8") if brut else json.loads(corps)), rep.headers
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 409):  # 409 : dépôt vide
                return None, {}
            raise

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
    fichiers, texte, commit, protegee, index = set(), None, None, None, None
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
        # Garde A1 : un ruleset actif sur la branche doit exiger une pull request et interdire le force-push.
        regles, _ = gh.get(f"/repos/{nom}/rules/branches/{ref}")
        types = {r.get("type") for r in regles or []}
        protegee = {"pull_request", "non_fast_forward"} <= types
        if not protegee and depot.get("private"):
            protegee = None  # rulesets indisponibles sur un dépôt privé en offre gratuite : signalé à part
    fiche, conformite = controler(texte, fichiers, depot["name"], vocab, depot.get("pushed_at"), protegee)
    if protegee is None and depot.get("private"):
        conformite["avertissements"].append("A1 non vérifiable : dépôt privé, rulesets réservés aux offres payantes")
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
            "etoiles": depot.get("stargazers_count"),
            "tickets_ouverts": depot.get("open_issues_count"),
            "branche_protegee": protegee,
        },
        "conformite": conformite,
        "index": index,
    }


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


def ecrire_registre_md(registre, chemin):
    vocab = charger_vocabulaire().get("domaines") or {}
    icones = {"conforme": "✅", "avertissements": "⚠️", "non-conforme": "❌"}
    lignes = [
        "# Registre des projets Memnius",
        "",
        f"_Généré le {registre['genere_le']} depuis `{registre['source']}`. Ne pas éditer : chaque projet "
        "tient sa fiche (`memnius.yaml`) et son registre (`registre/`). Toutes les cartes : [CARTES.md](CARTES.md)._",
        "",
        "| Projet | Statut | Domaines | Mainteneur·ices | Décisions | Code | Données | Sources | Socle | Dernière activité | Conformité |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
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
        "Ne pas éditer. Vue par projet : [REGISTRE.md](REGISTRE.md)._",
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
            lignes += ["| Projet | Carte | Résumé | Qui | Où |", "|---|---|---|---|---|"]
        for p, c in du_type:
            ou = [] if t == "decision" else [", ".join(
                lien_ou(o, "") if re.match(r"^(https?://|drive:)", o) else f"[`{o}`]({url_fichier(p, o.rstrip('/'))})"
                for o in en_liste(c.get("ou")))]
            lignes.append("| " + " | ".join([p["id"], f"[{cellule(c.get('titre') or c['id'])}]({c['url']})",
                                             cellule(c.get("resume")), ", ".join(qui(a) for a in c.get("auteurs") or []),
                                             *ou]) + " |")
    lignes += ["", "## Qui a fait quoi", "", "| Personne | Projet | Décisions | Code | Données | Sources |", "|---|---|---|---|---|---|"]
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
            projets += [entree_github(gh, d, vocab) for d in depots]
        source = ", ".join(f"https://github.com/{o}" for o in args.github)
    relier(projets)
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    registre = {"schema": "memnius-registre/2", "genere_le": maintenant().isoformat(), "source": source, "projets": projets}
    (sortie / "registre.json").write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ecrire_registre_md(registre, sortie / "REGISTRE.md")
    ecrire_cartes_md(registre, sortie / "CARTES.md")
    nb = {n: sum(p["conformite"]["niveau"] == n for p in projets) for n in ("conforme", "avertissements", "non-conforme")}
    cartes = sum(len((p["index"] or {}).get("cartes", [])) for p in projets)
    print(f"{len(projets)} projets, {cartes} cartes : {nb['conforme']} conformes, "
          f"{nb['avertissements']} avec avertissements, {nb['non-conforme']} non conformes")
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
    c.add_argument("type", help="decision, code, donnees ou sources")
    c.add_argument("nom", help="nom du fichier, en minuscules-avec-tirets")
    c.add_argument("--dossier", default=".")
    c.add_argument("--titre")
    c.add_argument("--ou", action="append", default=[], help="chemin ou adresse (répétable)")
    c.add_argument("--auteur", action="append", default=[], help="identifiant GitHub (répétable)")
    r = sp.add_parser("registre", help="construire le super-registre de l'organisation")
    src = r.add_mutually_exclusive_group(required=True)
    src.add_argument("--local", help="dossier contenant un clone par projet")
    src.add_argument("--github", action="append", help="organisation GitHub des projets (répétable)")
    r.add_argument("--sortie", default=".", help="dossier où écrire REGISTRE.md, CARTES.md et registre.json")
    args = p.parse_args()
    return {"verifier": verifier, "index": index, "init": init, "carte": nouvelle_carte, "registre": construire_registre}[args.commande](args)


if __name__ == "__main__":
    sys.exit(main())
