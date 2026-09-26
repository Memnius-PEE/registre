#!/usr/bin/env python3
"""Outil commun Memnius : vérifier un dépôt de sujet et construire le registre unifié.

Usage :
  python3 memnius.py verifier <dossier-du-depot>
  python3 memnius.py construire --local <dossier-contenant-les-depots> [--sortie DIR]
  python3 memnius.py construire --github memnius [--github autre-organisation] [--sortie DIR]
      Parcourt les dépôts de l'organisation qui portent le sujet GitHub (topic) « memnius-sujet ».
      Jeton lu dans GITHUB_TOKEN (lecture seule suffit ; facultatif si tous les dépôts sont publics).
  option --archiviste FICHIER : état publié par l'archiviste (dépôt Memnius-PEE/archives, etat.json),
      recopié dans le bloc « archiviste » de chaque sujet. Sans elle, le bloc de la génération précédente est gardé.

Dépendances : PyYAML ; jsonschema est utilisé s'il est installé (sinon contrôles essentiels seulement).
Le registre produit (registre.json + REGISTRE.md) est un fichier dérivé : on ne l'édite jamais à la main,
la source de vérité est le memnius.yaml de chaque dépôt.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ICI = Path(__file__).resolve().parent.parent
SCHEMA_FICHE = ICI / "schema" / "memnius.schema.json"
VOCABULAIRE = ICI / "vocabulaire.yaml"

# Garde A3 du socle : README, AGENTS.md, memnius.yaml, PASSATION.md et un journal decisions/ non vide.
FICHIERS_OBLIGATOIRES = ["README.md", "AGENTS.md", "memnius.yaml", "PASSATION.md"]
FICHIERS_RECOMMANDES = ["CONTRIBUTING.md", ".github/workflows/memnius.yml"]
ENTREE_JOURNAL = re.compile(r"^decisions/\d{4}(-[a-z0-9-]+)?\.md$")
MARQUEURS_GABARIT = re.compile(r"TITRE_DU_SUJET|SLUG-DU-SUJET|RÉSUMÉ_EN|IDENTIFIANT_GITHUB|AAAA-MM-JJ|DOMAINE\b")
JOURS_AVANT_DORMANT = 180


def maintenant():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def charger_vocabulaire():
    if VOCABULAIRE.exists():
        return yaml.safe_load(VOCABULAIRE.read_text(encoding="utf-8")) or {}
    return {}


def valider_schema(fiche):
    """Renvoie la liste des erreurs de schéma (jsonschema si disponible, sinon champs requis)."""
    schema = json.loads(SCHEMA_FICHE.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        return [f"champ obligatoire manquant : {c}" for c in schema["required"] if c not in fiche]
    validateur = jsonschema.Draft202012Validator(schema)
    erreurs = []
    for e in sorted(validateur.iter_errors(fiche), key=lambda e: list(e.path)):
        chemin = ".".join(str(p) for p in e.path) or "(racine)"
        erreurs.append(f"{chemin} : {e.message}")
    return erreurs


def controler(texte_fiche, fichiers_presents, chemin_depot, vocab, derniere_activite=None, branche_protegee=None):
    """Contrôles de conformité communs aux modes local et GitHub."""
    erreurs, avertissements = [], []
    fiche = None
    for f in FICHIERS_OBLIGATOIRES:
        if f not in fichiers_presents:
            erreurs.append(f"fichier obligatoire absent : {f}")
    for f in FICHIERS_RECOMMANDES:
        if f not in fichiers_presents:
            avertissements.append(f"fichier recommandé absent : {f}")
    if not any(ENTREE_JOURNAL.match(f) for f in fichiers_presents):
        erreurs.append("journal de décisions absent ou vide : decisions/NNNN.md")
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
        # yaml lit les dates AAAA-MM-JJ comme des objets date : on les remet en texte.
        fiche = json.loads(json.dumps(fiche, default=str))
        erreurs += valider_schema(fiche)
        if MARQUEURS_GABARIT.search(texte_fiche):
            erreurs.append("memnius.yaml contient encore des valeurs du gabarit à remplacer")
        nom_depot = chemin_depot.rstrip("/").split("/")[-1]
        if fiche.get("id") and fiche["id"] != nom_depot:
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

    niveau = "non-conforme" if erreurs else ("avertissements" if avertissements else "conforme")
    return fiche, {"niveau": niveau, "erreurs": erreurs, "avertissements": avertissements}


# ---------------------------------------------------------------- mode local

def fichiers_locaux(dossier):
    return {str(p.relative_to(dossier)) for p in dossier.rglob("*") if p.is_file() and ".git" not in p.parts}


def git_local(dossier, *args):
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(dossier), *args], capture_output=True, text=True, check=True).stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def entree_locale(dossier, vocab):
    texte = (dossier / "memnius.yaml").read_text(encoding="utf-8") if (dossier / "memnius.yaml").exists() else None
    activite = git_local(dossier, "log", "-1", "--format=%cI")
    fichiers = fichiers_locaux(dossier)
    fiche, conformite = controler(texte, fichiers, dossier.name, vocab, activite)
    return {
        "id": dossier.name,
        "fiche": fiche,
        "depot": {
            "chemin": str(dossier),
            "url": git_local(dossier, "remote", "get-url", "origin"),
            "branche": git_local(dossier, "rev-parse", "--abbrev-ref", "HEAD"),
            "dernier_commit": git_local(dossier, "rev-parse", "HEAD"),
            "derniere_activite": activite,
            "archive_forge": False,
            "etoiles": None,
            "tickets_ouverts": None,
            "branche_protegee": None,
            "decisions": sum(bool(ENTREE_JOURNAL.match(f)) for f in fichiers),
        },
        "conformite": conformite,
    }


# --------------------------------------------------------------- mode GitHub

SUJET_GITHUB = "memnius-sujet"  # topic GitHub qui marque un dépôt de sujet dans l'organisation


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
    fichiers, texte, commit, protegee = set(), None, None, None
    # Ne pas se fier à depot["size"] : GitHub le calcule en différé et le laisse à 0 sur un dépôt récent.
    if branche:
        arbre, _ = gh.get(f"/repos/{nom}/git/trees/{urllib.parse.quote(branche, safe='')}", recursive="1")
        fichiers = {e["path"] for e in (arbre or {}).get("tree", []) if e["type"] == "blob"}
        if "memnius.yaml" in fichiers:
            texte, _ = gh.get(f"/repos/{nom}/contents/memnius.yaml", brut=True, ref=branche)
        info, _ = gh.get(f"/repos/{nom}/commits/{urllib.parse.quote(branche, safe='')}")
        commit = (info or {}).get("sha")
        # Garde A1 : un ruleset actif sur la branche doit exiger une pull request et interdire le force-push.
        regles, _ = gh.get(f"/repos/{nom}/rules/branches/{urllib.parse.quote(branche, safe='')}")
        types = {r.get("type") for r in regles or []}
        protegee = {"pull_request", "non_fast_forward"} <= types
        if not protegee and depot.get("private"):
            protegee = None  # rulesets indisponibles sur un dépôt privé en offre gratuite : signalé à part
    fiche, conformite = controler(texte, fichiers, depot["name"], vocab, depot.get("pushed_at"), protegee)
    if protegee is None and depot.get("private"):
        conformite["avertissements"].append("A1 non vérifiable : dépôt privé, rulesets réservés aux offres payantes")
    declaree = (fiche or {}).get("visibilite")
    reelle = "prive" if depot.get("private") else "public"
    if declaree and declaree != reelle:
        conformite["avertissements"].append(f"visibilité déclarée « {declaree} », réelle « {reelle} »")
    if conformite["avertissements"] and conformite["niveau"] == "conforme":
        conformite["niveau"] = "avertissements"
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
            "decisions": sum(bool(ENTREE_JOURNAL.match(f)) for f in fichiers),
        },
        "conformite": conformite,
    }


# ------------------------------------------------------------------ sorties

def verifier_liens(sujets):
    ids = {s["id"] for s in sujets}
    for s in sujets:
        for lien in ((s["fiche"] or {}).get("liens") or {}).get("sujets") or []:
            if lien.get("id") not in ids:
                c = s["conformite"]
                c["avertissements"].append(f"lien vers un sujet inconnu : {lien.get('id')}")
                if c["niveau"] == "conforme":
                    c["niveau"] = "avertissements"


def reprendre_archiviste(sujets, ancien, etat_archiviste=None):
    """Remplit le bloc « archiviste », que ce programme n'écrit jamais lui-même.

    Source : l'état publié par l'archiviste dans son propre dépôt (etat.json : {"sujets": {id: bloc}}),
    sinon le bloc de la génération précédente du registre. L'archiviste n'a ainsi besoin d'écrire
    que dans Memnius-PEE/archives.
    """
    precedents = {}
    if ancien.exists():
        precedents = {s["id"]: s.get("archiviste") for s in json.loads(ancien.read_text(encoding="utf-8")).get("sujets", [])}
    if etat_archiviste:
        precedents.update(json.loads(Path(etat_archiviste).read_text(encoding="utf-8")).get("sujets", {}))
    for s in sujets:
        s["archiviste"] = precedents.get(s["id"])


def ecrire_markdown(registre, chemin):
    vocab = charger_vocabulaire().get("domaines") or {}
    icones = {"conforme": "✅", "avertissements": "⚠️", "non-conforme": "❌"}
    lignes = [
        "# Registre des sujets Memnius",
        "",
        f"_Généré le {registre['genere_le']} depuis `{registre['source']}`. Ne pas éditer : modifier le `memnius.yaml` du sujet._",
        "",
        "| Sujet | Statut | Domaines | Mainteneur·ices | Entrée | Agents | Socle | Dernière activité | Conformité |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for s in sorted(registre["sujets"], key=lambda s: s["id"]):
        f = s["fiche"] or {}
        titre = f.get("titre") or s["id"]
        lien = f"[{titre}]({s['depot']['url']})" if s["depot"].get("url") else titre
        domaines = ", ".join(vocab.get(d, d) for d in f.get("domaines") or [])
        mainteneurs = ", ".join("@" + m["github"] for m in f.get("mainteneurs") or [] if isinstance(m, dict) and "github" in m)
        entree = (f.get("contribution") or {}).get("niveau_entree", "")
        agents = (f.get("agents") or {}).get("politique", "")
        activite = (s["depot"].get("derniere_activite") or "")[:10]
        socle = f.get("socle") or {}
        socle = f"{socle.get('version', '?')} {socle.get('niveau', '')}".strip() if socle else ""
        lignes.append(f"| {lien} | {f.get('statut', '?')} | {domaines} | {mainteneurs} | {entree} | {agents} | {socle} | {activite} | {icones[s['conformite']['niveau']]} |")
    problemes = [s for s in registre["sujets"] if s["conformite"]["niveau"] != "conforme"]
    if problemes:
        lignes += ["", "## À corriger", ""]
        for s in problemes:
            for e in s["conformite"]["erreurs"]:
                lignes.append(f"- **{s['id']}** ❌ {e}")
            for a in s["conformite"]["avertissements"]:
                lignes.append(f"- **{s['id']}** ⚠️ {a}")
    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def construire(args):
    vocab = charger_vocabulaire()
    if args.local:
        racine = Path(args.local)
        dossiers = [d for d in sorted(racine.iterdir()) if d.is_dir() and not d.name.startswith(".")]
        sujets = [entree_locale(d, vocab) for d in dossiers]
        source = str(racine)
    else:
        gh = GitHub(os.environ.get("GITHUB_TOKEN", ""), os.environ.get("GITHUB_API_URL", "https://api.github.com"))
        sujets = []
        for org in args.github:
            proprietaire, _ = gh.get(f"/users/{org}")
            liste = f"/orgs/{org}/repos" if (proprietaire or {}).get("type") != "User" else f"/users/{org}/repos"
            depots = [d for d in gh.pages(liste, type="all") if SUJET_GITHUB in (d.get("topics") or [])]
            sujets += [entree_github(gh, d, vocab) for d in depots]
        source = ", ".join(f"https://github.com/{o}" for o in args.github)
    verifier_liens(sujets)
    sortie = Path(args.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    reprendre_archiviste(sujets, sortie / "registre.json", args.archiviste)
    registre = {"schema": "memnius-registre/1", "genere_le": maintenant().isoformat(), "source": source, "sujets": sujets}
    (sortie / "registre.json").write_text(json.dumps(registre, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ecrire_markdown(registre, sortie / "REGISTRE.md")
    nb = {n: sum(s["conformite"]["niveau"] == n for s in sujets) for n in ("conforme", "avertissements", "non-conforme")}
    print(f"{len(sujets)} sujets : {nb['conforme']} conformes, {nb['avertissements']} avec avertissements, {nb['non-conforme']} non conformes")
    return 0


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


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="commande", required=True)
    v = sp.add_parser("verifier", help="contrôler un dépôt local")
    v.add_argument("dossier", nargs="?", default=".")
    c = sp.add_parser("construire", help="construire le registre")
    src = c.add_mutually_exclusive_group(required=True)
    src.add_argument("--local", help="dossier contenant un clone par sujet")
    src.add_argument("--github", action="append", help="organisation GitHub des sujets (répétable)")
    c.add_argument("--sortie", default=".", help="dossier où écrire registre.json et REGISTRE.md")
    c.add_argument("--archiviste", help="etat.json publié par l'archiviste (facultatif)")
    args = p.parse_args()
    return verifier(args) if args.commande == "verifier" else construire(args)


if __name__ == "__main__":
    sys.exit(main())
