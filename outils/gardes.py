#!/usr/bin/env python3
"""Gardes automatiques du socle Memnius (A2 à A7 ; A1 est un ruleset GitHub contrôlé par le super-registre).

Usage :
  python3 gardes.py [DOSSIER] [--base SHA] [--seulement A2,A6]

  --base      commit de référence pour A4 (en CI : base de la pull request). Sans base,
              A4 ne contrôle que le format des entrées et le dit.
  --seulement liste de gardes à lancer (le crochet pre-commit lance A2,A6).

Sortie : une ligne « [ ok ] » ou « [FIRE] » par garde, puis un bilan. Code de sortie 1 si une garde
a sonné ou n'a pas pu tourner : une garde qui n'a pas tourné compte comme un échec, jamais comme un succès.
A2 et A6 n'utilisent que la bibliothèque standard ; A4 tolère une coquille corrigée (C2) ; A3, A5 et A7 ont besoin de PyYAML.
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
REGLES = ICI / "regles.yaml"
SEUIL_GROS_FICHIER = 10_000_000  # 10 Mo, garde A6 (repris de regles.yaml s'il est lisible)
TOUTES = ["A2", "A3", "A4", "A5", "A6", "A7"]
TITRES = {"A2": "Secrets", "A3": "Structure", "A4": "Journal en ajout seul",
          "A5": "Renvois aux règles", "A6": "Gros fichiers", "A7": "Registre du projet"}

# ------------------------------------------------------------------ outils communs


def git(dossier, *args):
    r = subprocess.run(["git", "-C", str(dossier), *args], capture_output=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} : {r.stderr.decode(errors='replace').strip()}")
    return r.stdout


def est_depot_git(dossier):
    try:
        return git(dossier, "rev-parse", "--is-inside-work-tree").strip() == b"true"
    except (RuntimeError, FileNotFoundError):
        return False


def fichiers_suivis(dossier):
    """Fichiers de l'index Git (ce qui sera commité), ou tous les fichiers hors dépôt Git."""
    if est_depot_git(dossier):
        return [f for f in git(dossier, "ls-files", "-z").decode().split("\0") if f]
    return [str(p.relative_to(dossier)) for p in dossier.rglob("*") if p.is_file() and ".git" not in p.parts]


def charger_regles():
    import yaml  # importé ici pour que A2 et A6 tournent sans PyYAML (crochet pre-commit)
    return yaml.safe_load(REGLES.read_text(encoding="utf-8"))


class Feu(Exception):
    """Une garde a sonné ; le message dit pourquoi."""


# ------------------------------------------------------------------ A2 secrets

MOTIFS_SECRETS = [
    ("clé privée", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("jeton GitLab", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}")),
    ("jeton GitHub", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    ("clé AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("jeton Slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("clé d'API de modèle", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_\-]{20,}")),
    ("mot de passe ou jeton en clair", re.compile(
        r"(?i)\b(?:password|passwd|mot_de_passe|secret|token|jeton|api_?key)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]")),
]
NOMS_INTERDITS = re.compile(r"(^|/)(\.env(\..+)?|id_rsa|id_ed25519|id_ecdsa|[^/]+\.pem|[^/]+\.p12)$")
AUTORISE = "memnius:autorise"  # à mettre sur la ligne d'un faux positif, relu par un mainteneur


def garde_a2(dossier, fichiers, **_):
    trouves = []
    for f in fichiers:
        if NOMS_INTERDITS.search(f) and not f.endswith(".env.exemple"):
            trouves.append(f"{f} : fichier de secrets")
            continue
        p = dossier / f
        try:
            if p.stat().st_size > 2_000_000:
                continue
            brut = p.read_bytes()
        except OSError:
            continue
        if b"\0" in brut[:8000]:
            continue  # binaire
        for n, ligne in enumerate(brut.decode("utf-8", errors="replace").splitlines(), 1):
            if AUTORISE in ligne:
                continue
            for nom, motif in MOTIFS_SECRETS:
                if motif.search(ligne):
                    trouves.append(f"{f}:{n} : {nom}")
    if trouves:
        raise Feu("; ".join(trouves[:10]) + (f" (et {len(trouves) - 10} autres)" if len(trouves) > 10 else ""))
    return f"{len(fichiers)} fichiers parcourus"


# ------------------------------------------------------------------ A3 structure


def memnius():
    """L'outil memnius.py, voisin de ce fichier (importé ici pour que A2 et A6 tournent sans PyYAML)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import memnius as module
    return module


def garde_a3(dossier, **_):
    m = memnius()
    texte = (dossier / "memnius.yaml").read_text(encoding="utf-8") if (dossier / "memnius.yaml").exists() else None
    _, conformite = m.controler(texte, set(m.lister_fichiers(dossier)), dossier.name, m.charger_vocabulaire())
    if conformite["erreurs"]:
        raise Feu("; ".join(conformite["erreurs"]))
    return f"structure {conformite['niveau']}" + (f" ({len(conformite['avertissements'])} avertissements)"
                                                  if conformite["avertissements"] else "")


# ------------------------------------------------------------------ A4 journal

JOURNAL = "registre/decisions/"
NOM_ENTREE = re.compile(r"^registre/decisions/(\d{4})(-[a-z0-9]+(?:-[a-z0-9]+)*)?\.md$")
CHAMP = re.compile(r"^-\s*\**(Date|Origine|Décidé par)\**\s*:\s*(.*)$", re.M)
MARQUEUR = re.compile(r"\[(humain|choix|agent)\]")
RESTES_GABARIT = re.compile(r"AAAA-MM-JJ|NNNN|À_REMPLIR|IDENTIFIANT")


def controler_entree(f, texte):
    """Renvoie la liste des défauts d'une entrée du journal."""
    defauts = []
    numero = NOM_ENTREE.match(f).group(1)
    premiere = texte.lstrip().splitlines()[0] if texte.strip() else ""
    if not re.match(rf"^#\s+{numero}\s+[—–-]\s+\S", premiere):
        defauts.append(f"{f} : première ligne attendue « # {numero} — Titre »")
    champs = {m.group(1): m.group(2).strip() for m in CHAMP.finditer(texte)}
    for c in ("Date", "Origine", "Décidé par"):
        if not champs.get(c):
            defauts.append(f"{f} : champ « {c} » manquant ou vide")
    if champs.get("Date") and not re.match(r"^\d{4}-\d{2}-\d{2}$", champs["Date"]):
        defauts.append(f"{f} : date au format AAAA-MM-JJ attendue")
    if champs.get("Origine") and not MARQUEUR.search(champs["Origine"]):
        defauts.append(f"{f} : l'origine doit porter [humain], [choix] ou [agent] (C4)")
    if RESTES_GABARIT.search(texte):
        defauts.append(f"{f} : valeurs du modèle à remplacer")
    return defauts


def coquille(dossier, base, f):
    """Une entrée publiée peut être retouchée pour une coquille (C2) : chaque commit qui la modifie depuis
    la base dit « coquille » dans son message, et Date, Origine et Décidé par restent identiques."""
    messages = git(dossier, "log", "--format=%B%x00", f"{base}..HEAD", "--", f).decode(errors="replace")
    messages = [m for m in messages.split("\0") if m.strip()]
    if not messages or not all("coquille" in m.lower() for m in messages):
        return False
    avant = git(dossier, "show", f"{base}:{f}").decode(errors="replace")
    apres = (dossier / f).read_text(encoding="utf-8", errors="replace")
    champs = lambda texte: {m.group(1): m.group(2).strip() for m in CHAMP.finditer(texte)}  # noqa: E731
    return champs(avant) == champs(apres)


def garde_a4(dossier, fichiers, base=None, **_):
    defauts, numeros = [], {}
    entrees = []
    for f in fichiers:
        if f.startswith("decisions/") and f != "decisions/README.md":
            defauts.append(f"{f} : le journal vit dans {JOURNAL} (git mv decisions registre/decisions)")
            continue
        if not f.startswith(JOURNAL) or f in (JOURNAL + "README.md", JOURNAL + ".gitkeep"):
            continue
        m = NOM_ENTREE.match(f)
        if not m:
            defauts.append(f"{f} : nom attendu {JOURNAL}NNNN.md ou {JOURNAL}NNNN-titre-court.md")
            continue
        if m.group(1) in numeros:
            defauts.append(f"{f} : numéro {m.group(1)} déjà pris par {numeros[m.group(1)]}")
        numeros[m.group(1)] = f
        entrees.append(f)
        defauts += controler_entree(f, (dossier / f).read_text(encoding="utf-8", errors="replace"))
    if not entrees:
        defauts.append(f"aucune entrée dans {JOURNAL} (au moins l'adoption du socle)")
    portee = "format seul, pas de commit de référence"
    coquilles = 0
    if base and set(base) != {"0"}:
        sortie = git(dossier, "diff", "--name-status", "-M", base, "HEAD", "--", JOURNAL).decode()
        for ligne in sortie.splitlines():
            etat, *chemins = ligne.split("\t")
            ancien = chemins[0]
            if NOM_ENTREE.match(ancien) and etat[0] in "MDRT":
                if RESTES_GABARIT.search(git(dossier, "show", f"{base}:{ancien}").decode(errors="replace")):
                    continue  # entrée encore à remplir : pas encore publiée
                if etat[0] == "M" and coquille(dossier, base, ancien):
                    coquilles += 1
                    continue
                action = {"M": "modifiée", "D": "supprimée", "R": "renommée", "T": "changée de type"}[etat[0]]
                defauts.append(f"{ancien} : entrée publiée {action} (C2 : corriger par une nouvelle entrée)")
        portee = f"comparé à {base[:10]}" + (f", {coquilles} coquille(s) corrigée(s)" if coquilles else "")
    if defauts:
        raise Feu("; ".join(defauts))
    return f"{len(entrees)} entrées, {portee}"


# ------------------------------------------------------------------ A5 renvois

FICHIERS_GOUVERNANCE = re.compile(r"^(README\.md|registre/README\.md|AGENTS\.md|CLAUDE\.md|CONTRIBUTING\.md|PASSATION\.md|REGLES\.md|registre/decisions/[^/]+\.md)$")
RENVOI = re.compile(r"(?<![\w/.#@-])([CROA])(\d{1,2})(?![\w])")


def garde_a5(dossier, fichiers, **_):
    """Le journal est l'histoire : il peut citer une règle abrogée, comme une ligne qui dit qu'elle l'est."""
    ref = charger_regles()
    connus = {**ref.get("regles", {}), **ref.get("gardes", {})}
    defauts, compte = [], 0
    for f in fichiers:
        if not FICHIERS_GOUVERNANCE.match(f):
            continue
        historique = f.startswith(JOURNAL)
        for n, ligne in enumerate((dossier / f).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for m in RENVOI.finditer(ligne):
                code = m.group(1) + m.group(2)
                compte += 1
                if code not in connus:
                    defauts.append(f"{f}:{n} : {code} n'existe pas")
                elif (connus[code] or {}).get("abrogee") and not historique and "abrog" not in ligne.lower():
                    defauts.append(f"{f}:{n} : {code} est abrogée")
    meta = dossier / "memnius.yaml"
    if meta.exists():
        import yaml
        try:
            options = ((yaml.safe_load(meta.read_text(encoding="utf-8")) or {}).get("socle") or {}).get("options") or []
        except yaml.YAMLError:
            options = []  # A3 signale la fiche illisible
        for o in options:
            if o not in connus or not str(o).startswith("O"):
                defauts.append(f"memnius.yaml : option du socle inconnue : {o}")
    if defauts:
        raise Feu("; ".join(defauts))
    return f"{compte} renvois vérifiés"


# ------------------------------------------------------------------ A6 gros fichiers


POINTEUR_LFS = re.compile(rb"^version https://git-lfs\.github\.com/spec/v1\n(?:.*\n)*?size (\d+)", re.M)


def taille_lfs(dossier, sha):
    """Taille du fichier désigné par un pointeur Git LFS, ou None si l'objet n'en est pas un."""
    m = POINTEUR_LFS.match(git(dossier, "cat-file", "blob", sha))
    return int(m.group(1)) if m else None


def garde_a6(dossier, fichiers, **_):
    """Git LFS n'est pas une échappatoire (décision 0017) : on mesure le fichier, pas son pointeur."""
    seuil = SEUIL_GROS_FICHIER
    try:
        seuil = charger_regles()["gardes"]["A6"]["seuil_octets"]
    except Exception:  # noqa: BLE001 — sans PyYAML, on garde le seuil par défaut, identique
        pass
    tailles = {}
    if est_depot_git(dossier):
        # Taille des objets de l'index : un fichier suivi par Git LFS n'y est qu'un pointeur de quelques octets.
        index = git(dossier, "ls-files", "-s", "-z").decode().split("\0")
        objets = {}
        for e in filter(None, index):
            meta, chemin = e.split("\t", 1)
            mode, sha, _ = meta.split()
            if mode != "160000":  # sous-module
                objets[chemin] = sha
        if objets:
            r = subprocess.run(["git", "-C", str(dossier), "cat-file", "--batch-check=%(objectsize)"],
                               input="\n".join(objets.values()) + "\n", capture_output=True, text=True, check=True)
            tailles = dict(zip(objets, (int(t) for t in r.stdout.split())))
            for chemin, taille in list(tailles.items()):
                if taille < 1024 and (vraie := taille_lfs(dossier, objets[chemin])) is not None:
                    tailles[chemin] = vraie
    else:
        tailles = {f: (dossier / f).stat().st_size for f in fichiers}
    gros = [f"{f} ({t / 1_000_000:.1f} Mo)" for f, t in sorted(tailles.items()) if t > seuil]
    if gros:
        raise Feu(f"au-delà de {seuil / 1_000_000:g} Mo, Git LFS compris (à mettre dans le drive commun) : " + ", ".join(gros))
    return f"{len(tailles)} fichiers sous {seuil / 1_000_000:g} Mo"


# ------------------------------------------------------------------ A7 registre du projet


def garde_a7(dossier, **_):
    m = memnius()
    erreurs, avertissements = m.verifier_registre(dossier)
    if erreurs:
        raise Feu("; ".join(erreurs))
    cartes, _ = m.cartes_du_projet(dossier, m.lister_fichiers(dossier))
    detail = f"{len(cartes)} carte(s) valides (l'index est écrit par la CI)"
    if avertissements:
        detail += " ; attention : " + " ; ".join(avertissements)
    return detail


GARDES = {"A2": garde_a2, "A3": garde_a3, "A4": garde_a4, "A5": garde_a5, "A6": garde_a6, "A7": garde_a7}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dossier", nargs="?", default=".")
    p.add_argument("--base")
    p.add_argument("--seulement", default=",".join(TOUTES))
    a = p.parse_args()
    dossier = Path(a.dossier).resolve()
    choisies = [g.strip().upper() for g in a.seulement.split(",") if g.strip()]
    inconnues = [g for g in choisies if g not in GARDES]
    if inconnues:
        p.error(f"garde inconnue : {', '.join(inconnues)}")
    try:
        fichiers = fichiers_suivis(dossier)
    except Exception as exc:  # noqa: BLE001
        print(f"[FIRE] impossible de lister les fichiers : {exc}")
        return 1
    echecs = 0
    for code in choisies:
        try:
            detail = GARDES[code](dossier, fichiers=fichiers, base=a.base)
            print(f"[ ok ] {code} {TITRES[code]} — {detail}")
        except Feu as feu:
            echecs += 1
            print(f"[FIRE] {code} {TITRES[code]} — {feu}")
        except Exception as exc:  # noqa: BLE001 — une garde qui plante compte comme un échec
            echecs += 1
            print(f"[FIRE] {code} {TITRES[code]} — n'a pas pu tourner : {type(exc).__name__} : {exc}")
    print(f"Bilan : {len(choisies) - echecs}/{len(choisies)} gardes vertes")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
