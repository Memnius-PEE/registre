"""Outil memnius.py : init d'un projet, cartes à partir des modèles, index et super-registre (mode local).

Lancer depuis la racine du dépôt registre : python3 -m unittest discover -s tests -v
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_gardes import CARTE, DepotDeTest, FICHE, sh

OUTIL = Path(__file__).resolve().parent.parent / "outils" / "memnius.py"
sys.path.insert(0, str(OUTIL.parent))
import memnius  # noqa: E402


def lancer_gardes(dossier, *gardes):
    options = ["--seulement", ",".join(gardes)] if gardes else []
    r = subprocess.run([sys.executable, str(OUTIL.parent / "gardes.py"), str(dossier), *options], capture_output=True, text=True)
    return r.returncode, r.stdout


def lancer(*args, cwd=None):
    r = subprocess.run([sys.executable, str(OUTIL), *args], capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr


class Carte(DepotDeTest):
    def test_carte_creee_a_remplir(self):
        code, sortie = lancer("carte", "donnees", "mesures", "--dossier", str(self.d), "--ou", "travaux/calcul.py")
        self.assertEqual(code, 0, sortie)
        texte = (self.d / "registre/donnees/mesures.md").read_text(encoding="utf-8")
        entete, _ = memnius.lire_carte(texte)
        self.assertEqual(entete["ou"], ["travaux/calcul.py"])
        self.assertIn("Colonnes ou variables", texte)  # texte du modèle de carte de données
        erreurs, _ = memnius.verifier_registre(self.d)
        self.assertTrue(any("À_REMPLIR" in e for e in erreurs), erreurs)

    def test_carte_remplie_acceptee(self):
        lancer("carte", "code", "autre", "--dossier", str(self.d), "--titre", "Autre calcul",
               "--ou", "travaux/calcul.py", "--auteur", "quelqu-un")
        chemin = self.d / "registre/code/autre.md"
        chemin.write_text(chemin.read_text(encoding="utf-8").replace(
            "À_REMPLIR en une à trois phrases : ce que fait ce code, à quoi il sert.", "Un second calcul de test."),
            encoding="utf-8")
        memnius.ecrire_index(self.d)
        erreurs, _ = memnius.verifier_registre(self.d)
        self.assertEqual(erreurs, [])

    def test_type_inconnu(self):
        code, sortie = lancer("carte", "article", "x", "--dossier", str(self.d))
        self.assertEqual(code, 2)
        self.assertIn("decision, code, donnees, sources ou documents", sortie)

    def test_decision_a_partir_du_modele(self):
        code, sortie = lancer("carte", "decision", "choix-du-format", "--dossier", str(self.d),
                              "--titre", "Choisir le format", "--auteur", "mainteneur-test")
        self.assertEqual(code, 0, sortie)
        chemin = self.d / "registre/decisions/0002-choix-du-format.md"
        texte = chemin.read_text(encoding="utf-8")
        self.assertTrue(texte.startswith("# 0002 — Choisir le format"), texte)
        self.assertIn("- Décidé par : @mainteneur-test", texte)
        sh(self.d, "git", "add", "-A")
        code, sortie = lancer_gardes(self.d, "A4")
        self.assertEqual(code, 1, sortie)
        self.assertIn("valeurs du modèle", sortie)

    def test_carte_de_document_a_partir_du_modele(self):
        code, sortie = lancer("carte", "documents", "synthese", "--dossier", str(self.d), "--ou", "README.md")
        self.assertEqual(code, 0, sortie)
        self.assertIn("format:", (self.d / "registre/documents/synthese.md").read_text(encoding="utf-8"))

    def test_carte_existante_jamais_ecrasee(self):
        avant = (self.d / "registre/code/calcul.md").read_text(encoding="utf-8")
        code, _ = lancer("carte", "code", "calcul", "--dossier", str(self.d))
        self.assertEqual(code, 1)
        self.assertEqual((self.d / "registre/code/calcul.md").read_text(encoding="utf-8"), avant)


class Init(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name) / "projet-existant"
        (self.d / "travaux").mkdir(parents=True)
        (self.d / "README.md").write_text("# Mon projet, déjà là\n", encoding="utf-8")
        (self.d / "travaux/calcul.py").write_text("print(1)\n", encoding="utf-8")
        sh(self.d, "git", "init", "-q", "-b", "main")

    def tearDown(self):
        self._tmp.cleanup()

    def test_ajoute_sans_remplacer(self):
        code, sortie = lancer("init", str(self.d), "--titre", "Mon projet", "--mainteneur", "@quelqu-un")
        self.assertEqual(code, 0, sortie)
        self.assertEqual((self.d / "README.md").read_text(encoding="utf-8"), "# Mon projet, déjà là\n")
        fiche = (self.d / "memnius.yaml").read_text(encoding="utf-8")
        self.assertIn("id: projet-existant", fiche)
        self.assertIn("- github: quelqu-un", fiche)
        self.assertIn("@quelqu-un", (self.d / "registre/decisions/0001-adopter-le-socle.md").read_text(encoding="utf-8"))
        self.assertFalse((self.d / "PASSATION.md").exists())
        for f in ("AGENTS.md", "CONTRIBUTING.md", "registre/README.md", "registre/INDEX.md", ".github/workflows/memnius.yml"):
            self.assertTrue((self.d / f).exists(), f)
        self.assertNotIn("{{", "".join(p.read_text(encoding="utf-8") for p in self.d.rglob("*.md")))

    def test_reste_a_remplir_le_resume_et_les_domaines(self):
        lancer("init", str(self.d), "--titre", "Mon projet", "--mainteneur", "quelqu-un")
        sh(self.d, "git", "add", "-A")
        code, sortie = lancer_gardes(self.d)
        self.assertEqual(code, 1, sortie)
        self.assertIn("[FIRE] A3", sortie)
        self.assertIn("[ ok ] A4", sortie)
        self.assertIn("[ ok ] A7", sortie)
        self.assertIn("sans carte : travaux/calcul.py", sortie)

    def test_projet_neuf_range_dans_un_autre_depot(self):
        # Préparé dans un dossier d'un autre dépôt Git (projets/<nom>/ du kit), pas encore « git init » :
        # les gardes le lisent comme un simple dossier, sans conclure qu'il n'a aucun fichier.
        neuf = self.d / "projets" / "neuf"
        neuf.mkdir(parents=True)
        lancer("init", str(neuf), "--titre", "Neuf", "--mainteneur", "quelqu-un")
        code, sortie = lancer_gardes(neuf, "A4")
        self.assertEqual(code, 0, sortie)
        self.assertIn("[ ok ] A4", sortie)

    def test_journal_existant_garde(self):
        (self.d / "registre/decisions").mkdir(parents=True)
        (self.d / "registre/decisions/0001-autre-chose.md").write_text("# 0001 — Autre chose\n", encoding="utf-8")
        lancer("init", str(self.d))
        self.assertEqual(sorted(p.name for p in (self.d / "registre/decisions").iterdir()), ["0001-autre-chose.md"])


class Index(DepotDeTest):
    def test_contenu(self):
        index = json.loads((self.d / "registre/index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["projet"], "sujet-test")
        self.assertEqual(index["comptes"], {"decision": 1, "code": 1, "donnees": 0, "sources": 0, "documents": 0})
        decision = index["cartes"][0]
        self.assertEqual((decision["id"], decision["auteurs"], decision["origine"]),
                         ("decisions/0001", ["mainteneur-test"], ["humain"]))
        md = (self.d / "registre/INDEX.md").read_text(encoding="utf-8")
        self.assertIn("[Calcul de test](code/calcul.md)", md)
        self.assertIn("- **@mainteneur-test** : décisions [0001]", md)

    def test_liens_cliquables_dans_la_carte(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace(
            "langage: python", "liens: [decisions/0001, sources/absente, autre:code/x]\nurl: https://exemple.org/calcul"))
        journal = (self.d / "registre/decisions/0001-adopter-le-socle.md").read_text(encoding="utf-8")
        memnius.ecrire_index(self.d)
        texte = (self.d / "registre/code/calcul.md").read_text(encoding="utf-8")
        entete, corps = memnius.lire_carte(texte)
        self.assertEqual(entete["ou"], ["travaux/calcul.py"])
        self.assertTrue(corps.startswith("\n" + memnius.DEBUT_LIENS), corps)
        self.assertIn("- **Où :** [`travaux/calcul.py`](../../travaux/calcul.py) · [exemple.org](https://exemple.org/calcul)", corps)
        self.assertIn("[decisions/0001](../decisions/0001-adopter-le-socle.md) · `sources/absente` · `autre:code/x`", corps)
        self.assertTrue(corps.endswith("Notes libres.\n"), corps)
        self.assertEqual((self.d / "registre/decisions/0001-adopter-le-socle.md").read_text(encoding="utf-8"), journal)
        memnius.ecrire_index(self.d)
        self.assertEqual((self.d / "registre/code/calcul.md").read_text(encoding="utf-8"), texte)

    def test_decision_remplacee(self):
        self.ecrire("registre/decisions/0002-autre-choix.md", "# 0002 — Autre choix\n\n- Date : 2026-10-11\n"
                    "- Origine : [humain] « on change »\n- Décidé par : @mainteneur-test\n- Remplace : 0001\n\nOn change d'avis.\n")
        memnius.ecrire_index(self.d)
        index = json.loads((self.d / "registre/index.json").read_text(encoding="utf-8"))
        d1 = next(c for c in index["cartes"] if c["id"] == "decisions/0001")
        self.assertEqual(d1["remplacee_par"], ["0002"])
        self.assertIn("(remplacée par 0002)", (self.d / "registre/INDEX.md").read_text(encoding="utf-8"))

    def test_resume_d_une_decision_en_liste(self):
        # Audit Fable (F2) : une décision écrite en liste à puces avait un résumé vide.
        texte = ("# 0002 — Liste\n\n- Date : 2026-10-11\n- Origine : [humain] « x »\n- Décidé par : @m\n"
                 "- Options écartées : rien\n\n- Premier point.\n- Second point.\n")
        carte = memnius.carte_de_decision("registre/decisions/0002-liste.md", texte)
        self.assertEqual(carte["resume"], "Premier point.")

    def test_carte_qui_ne_cite_rien(self):
        texte = CARTE.replace("ou: [travaux/calcul.py]", "ou: [À_REMPLIR]")
        self.assertEqual(memnius.avec_bloc_liens(texte, memnius.bloc_liens(
            {"fichier": "registre/code/x.md", "ou": ["À_REMPLIR"]}, {})), texte)

    def test_meme_cartes_meme_index(self):
        avant = (self.d / "registre/index.json").read_text(encoding="utf-8")
        memnius.ecrire_index(self.d)
        self.assertEqual((self.d / "registre/index.json").read_text(encoding="utf-8"), avant)

    def test_verifier_sans_ecrire(self):
        self.ecrire("registre/code/autre.md", CARTE)
        code, sortie = lancer("index", str(self.d), "--verifier")
        self.assertEqual(code, 1, sortie)
        self.assertNotIn("autre", (self.d / "registre/index.json").read_text(encoding="utf-8"))
        lancer("index", str(self.d))
        self.assertEqual(lancer("index", str(self.d), "--verifier")[0], 0)


class ProjetsDeTest(unittest.TestCase):
    """Deux projets, alpha et beta, avec leur index, dans un dossier de clones (super-registre en mode local)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name) / "projets"
        self.sortie = Path(self._tmp.name) / "sortie"
        for nom, carte in (("alpha", CARTE), ("beta", CARTE.replace("langage: python", "liens: [alpha:code/calcul, alpha:code/absent]"))):
            d = self.racine / nom
            fichiers = {
                "README.md": "# Projet\n", "AGENTS.md": "# Agents\n", "CONTRIBUTING.md": "# Contribuer\n",
                ".github/workflows/memnius.yml": "name: Memnius\n",
                "memnius.yaml": FICHE.format(id=nom).replace("mainteneur-test", f"mainteneur-{nom}"),
                "registre/decisions/0001.md": "# 0001 — Adopter le socle\n\n- Date : 2026-10-10\n- Origine : [humain] « oui »\n- Décidé par : @Pwouette\n",
                "travaux/calcul.py": "print(1)\n", "registre/README.md": "# Registre\n", "registre/code/calcul.md": carte,
                "registre/donnees/.gitkeep": "", "registre/sources/.gitkeep": "",
            }
            for chemin, texte in fichiers.items():
                (d / chemin).parent.mkdir(parents=True, exist_ok=True)
                (d / chemin).write_text(texte, encoding="utf-8")
            memnius.ecrire_index(d)
            sh(d, "git", "init", "-q", "-b", "main")

    def tearDown(self):
        self._tmp.cleanup()


class SuperRegistre(ProjetsDeTest):
    def test_vue_generale(self):
        code, sortie = lancer("registre", "--local", str(self.racine), "--sortie", str(self.sortie))
        self.assertEqual(code, 0, sortie)
        self.assertIn("2 projets (0 privés), 4 cartes", sortie)
        registre = json.loads((self.sortie / "registre.json").read_text(encoding="utf-8"))
        self.assertEqual(registre["schema"], "memnius-registre/2")
        beta = next(p for p in registre["projets"] if p["id"] == "beta")
        self.assertIn("lien vers une carte inconnue d'un autre projet : alpha:code/absent", " ".join(beta["conformite"]["avertissements"]))
        self.assertNotIn("alpha:code/calcul", " ".join(beta["conformite"]["avertissements"]))
        projets = (self.sortie / "REGISTRE.md").read_text(encoding="utf-8")
        self.assertIn("| Projet | Statut |", projets)
        cartes = (self.sortie / "CARTES.md").read_text(encoding="utf-8")
        self.assertIn("## Code (2)", cartes)
        self.assertIn("| @Pwouette | alpha |", cartes)
        self.assertIn("[`travaux/calcul.py`](", cartes)

    def test_projet_prive_absent_des_sorties_publiques(self):
        # Audits du 2026-10-11 (H1) : un projet privé sortait dans CARTES.md, REGISTRE.md et registre.json.
        fiche = self.racine / "beta/memnius.yaml"
        fiche.write_text(fiche.read_text(encoding="utf-8").replace("visibilite: public", "visibilite: prive"), encoding="utf-8")
        complet = Path(self._tmp.name) / "complet"
        code, sortie = lancer("registre", "--local", str(self.racine), "--sortie", str(self.sortie), "--complet", str(complet))
        self.assertEqual(code, 0, sortie)
        for f in ("CARTES.md", "REGISTRE.md", "registre.json", "ACCUEIL.md"):
            self.assertNotIn("beta", (self.sortie / f).read_text(encoding="utf-8"), f)
        self.assertIn("1 projet privé non publié ici", (self.sortie / "REGISTRE.md").read_text(encoding="utf-8"))
        self.assertIn("beta", (complet / "CARTES.md").read_text(encoding="utf-8"))
        self.assertIn("beta", (complet / "registre.json").read_text(encoding="utf-8"))

    def test_projet_sans_registre(self):
        d = self.racine / "alpha"
        for f in ("registre/index.json", "registre/INDEX.md"):
            (d / f).unlink()
        lancer("registre", "--local", str(self.racine), "--sortie", str(self.sortie))
        registre = json.loads((self.sortie / "registre.json").read_text(encoding="utf-8"))
        alpha = next(p for p in registre["projets"] if p["id"] == "alpha")
        self.assertEqual(alpha["conformite"]["niveau"], "non-conforme")
        self.assertIsNone(alpha["index"])


class Accueil(ProjetsDeTest):
    """Page d'accueil de l'organisation (profile/README.md du dépôt .github) : partie fixe et dernières modifications."""

    def commit(self, nom, message, auteur="Pwouette", courriel="pwouette@example.org", date="2026-10-10T12:00:00+00:00"):
        d = self.racine / nom
        sh(d, "git", "add", "-A")
        sh(d, "git", "-c", f"user.name={auteur}", "-c", f"user.email={courriel}", "commit", "-q", "-m", message,
           f"--date={date}")

    def accueil(self):
        code, sortie = lancer("registre", "--local", str(self.racine), "--sortie", str(self.sortie))
        self.assertEqual(code, 0, sortie)
        return (self.sortie / "ACCUEIL.md").read_text(encoding="utf-8")

    def test_partie_fixe(self):
        texte = self.accueil()
        self.assertIn("LIRE LE MANUEL !", texte)
        self.assertIn("REGLES.md", texte)
        self.assertIn("## Dernières modifications", texte)
        self.assertNotIn("{{", texte)

    def test_sans_historique(self):
        self.assertIn("Aucune carte ni décision", self.accueil())

    def test_dernieres_modifications(self):
        self.commit("alpha", "Création", date="2026-10-01T09:00:00+02:00")
        self.commit("beta", "Création", auteur="autre-personne", date="2026-10-03T09:00:00+00:00")
        (self.racine / "alpha/registre/code/calcul.md").write_text(CARTE + "\nPrécision.\n", encoding="utf-8")
        self.commit("alpha", "Carte précisée", date="2026-10-05T09:00:00+00:00")
        (self.racine / "alpha/registre/INDEX.md").write_text("# Index régénéré\n", encoding="utf-8")
        self.commit("alpha", "Index régénéré par la CI", auteur="github-actions[bot]",
                    courriel="41898282+github-actions[bot]@users.noreply.github.com", date="2026-10-06T09:00:00+00:00")
        texte = self.accueil()
        tableau = [l for l in texte.splitlines() if l.startswith("| 2026-")]
        self.assertTrue(tableau[0].startswith("| 2026-10-05 | alpha |"), tableau[0])
        self.assertIn("| modifiée | @Pwouette |", tableau[0])
        self.assertTrue(tableau[1].startswith("| 2026-10-03 | beta |"), tableau[1])
        self.assertIn("| ajoutée | @autre-personne |", tableau[1])
        self.assertEqual(len(tableau), 5)  # alpha : carte et décision ajoutées, puis carte modifiée ; beta : deux ajouts
        self.assertNotIn("Index régénéré", texte)  # l'index n'est pas une carte, et les robots sont ignorés
        self.assertNotIn("[bot]", texte)

    def test_projet_prive_absent(self):
        fiche = self.racine / "beta/memnius.yaml"
        fiche.write_text(fiche.read_text(encoding="utf-8").replace("visibilite: public", "visibilite: prive"), encoding="utf-8")
        self.commit("alpha", "Création")
        self.commit("beta", "Création", auteur="secret-beta")
        texte = self.accueil()
        self.assertIn("| alpha |", texte)
        self.assertNotIn("beta", texte)

    def test_limite_a_dix(self):
        self.commit("alpha", "Création", date="2026-10-01T09:00:00+00:00")
        for i in range(12):
            (self.racine / f"alpha/registre/sources/s{i}.md").write_text(CARTE.replace("travaux/calcul.py", "README.md"), encoding="utf-8")
            self.commit("alpha", f"Source {i}", date=f"2026-10-02T{10 + i}:00:00+00:00")
        tableau = [l for l in self.accueil().splitlines() if l.startswith("| 2026-")]
        self.assertEqual(len(tableau), 10)
        self.assertIn("`s11`", tableau[0])  # cartes absentes de l'index (non régénéré) : nom et lien vers le commit

    def test_page_publique_sans_nom_civil(self):
        # Audit Fable (M5) : un commit sans compte GitHub affichait le nom Git sur la page publique.
        projets = [{"id": "alpha", "fiche": {}, "depot": {"prive": False, "url": "https://github.com/o/alpha", "branche": "main"},
                    "index": {"cartes": []}, "modifications": [
                        {"sha": "c1", "date": "2026-10-01T00:00:00Z", "auteur": None, "agent": True,
                         "statut": "ajoutée", "fichier": "registre/code/x.md"}]}]
        sortie = Path(self._tmp.name) / "ACCUEIL.md"
        memnius.ecrire_accueil({"projets": projets}, sortie)
        ligne = next(l for l in sortie.read_text(encoding="utf-8").splitlines() if l.startswith("| 2026-"))
        self.assertTrue(ligne.endswith("| — 🤖 |"), ligne)

    def test_lecture_par_l_api_github(self):
        class FauxGitHub:
            def get(self, chemin, **params):
                if chemin.endswith("/commits"):
                    self.params = params
                    return [
                        {"sha": "c3", "parents": [{}], "author": {"login": "github-actions[bot]", "type": "Bot"},
                         "commit": {"author": {"name": "github-actions[bot]", "date": "2026-10-03T00:00:00Z"}}},
                        {"sha": "c2", "parents": [{}, {}], "author": {"login": "Pwouette", "type": "User"},
                         "commit": {"author": {"name": "Romain", "date": "2026-10-02T00:00:00Z"}}},
                        {"sha": "c1", "parents": [{}], "author": None,
                         "commit": {"author": {"name": "Sans Compte", "date": "2026-10-01T00:00:00Z"},
                                    "message": "Carte\n\nAssisted-by: Claude Code (Opus)"}},
                    ], {}
                assert chemin.endswith("/commits/c1"), chemin  # robot et fusion ignorés sans être lus
                return {"files": [{"filename": "registre/code/calcul.md", "status": "added"},
                                  {"filename": "registre/INDEX.md", "status": "modified"},
                                  {"filename": "registre/decisions/0002-x.md", "status": "removed"}]}, {}
        gh = FauxGitHub()
        modifs = memnius.modifications_github(gh, "org/alpha", "main")
        self.assertEqual(gh.params["path"], "registre")
        self.assertTrue(all(m["agent"] for m in modifs))  # ligne Assisted-by du commit
        self.assertEqual([(m["fichier"], m["statut"], m["auteur"]) for m in modifs],
                         [("registre/code/calcul.md", "ajoutée", None), ("registre/decisions/0002-x.md", "supprimée", None)])


class FauxDepot:
    """Une fausse API GitHub pour un dépôt public « org/alpha », dont on règle le ruleset et le workflow."""

    REGLES_COMPLETES = [{"type": "deletion"}, {"type": "non_fast_forward"}, {"type": "pull_request"},
                        {"type": "required_status_checks", "parameters": {"required_status_checks": [
                            {"context": c} for c in memnius.CONTROLES_REQUIS]}}]
    WORKFLOW = "name: Memnius\njobs:\n  gardes:\n    uses: org/registre/.github/workflows/gardes.yml@v2\n    secrets: inherit\n"

    def __init__(self, regles=None, workflow=WORKFLOW, erreur=None):
        self.regles = self.REGLES_COMPLETES if regles is None else regles
        self.workflow, self.erreur = workflow, erreur

    def get(self, chemin, brut=False, **params):
        if self.erreur:
            raise self.erreur
        if "/git/trees/" in chemin:
            return {"tree": [{"path": f, "type": "blob"} for f in
                             ("README.md", "AGENTS.md", "memnius.yaml", "registre/decisions/0001.md", "registre/index.json",
                              "CONTRIBUTING.md", memnius.WORKFLOW_PROJET)]}, {}
        if chemin.endswith("/memnius.yaml"):
            return FICHE.format(id="alpha"), {}
        if chemin.endswith("/registre/index.json"):
            return json.dumps({"schema": "memnius-index/1", "cartes": []}), {}
        if chemin.endswith(memnius.WORKFLOW_PROJET):
            return self.workflow, {}
        if "/rules/branches/" in chemin:
            return self.regles, {}
        if chemin.endswith("/commits"):
            return [], {}
        return {"sha": "abc"}, {}

    DEPOT = {"full_name": "org/alpha", "name": "alpha", "default_branch": "main", "html_url": "https://github.com/org/alpha",
             "private": False, "pushed_at": "2026-10-11T00:00:00Z"}

    def entree(self):
        return memnius.entree_github(self, self.DEPOT, memnius.charger_vocabulaire())


class SuperRegistreGitHub(unittest.TestCase):
    def test_conforme(self):
        entree = FauxDepot().entree()
        self.assertEqual(entree["conformite"]["erreurs"], [])
        self.assertTrue(entree["depot"]["branche_protegee"])

    def test_ruleset_sans_gitleaks(self):
        # Audits (H3, B2) : A1 tenait la branche pour protégée sans vérifier les contrôles exigés.
        regles = FauxDepot.REGLES_COMPLETES[:3] + [{"type": "required_status_checks", "parameters": {
            "required_status_checks": [{"context": "gardes / Gardes A2 à A7"}]}}]
        entree = FauxDepot(regles=regles).entree()
        self.assertIn("contrôle « gardes / A2, second filet (gitleaks) » non exigé", " ".join(entree["conformite"]["erreurs"]))
        self.assertFalse(entree["depot"]["branche_protegee"])

    def test_ruleset_sans_suppression_interdite(self):
        entree = FauxDepot(regles=FauxDepot.REGLES_COMPLETES[1:]).entree()
        self.assertIn("règle deletion absente", " ".join(entree["conformite"]["erreurs"]))

    def test_sans_ruleset(self):
        entree = FauxDepot(regles=[]).entree()
        self.assertIn("n'est pas protégée", " ".join(entree["conformite"]["erreurs"]))

    def test_workflow_qui_n_appelle_plus_les_gardes(self):
        # Audit Opus (H3) : un job du même nom qui finit par « exit 0 » satisfait le contrôle requis.
        faux = "name: Memnius\njobs:\n  gardes:\n    name: Gardes A2 à A7\n    runs-on: ubuntu-latest\n    steps:\n      - run: exit 0\n"
        entree = FauxDepot(workflow=faux).entree()
        self.assertIn("n'appelle plus les gardes du socle", " ".join(entree["conformite"]["erreurs"]))

    def test_projet_illisible_ne_fait_pas_tomber_la_passe(self):
        entree = memnius.entree_illisible(FauxDepot.DEPOT, RuntimeError("HTTP 502"))
        self.assertEqual(entree["conformite"]["niveau"], "non-conforme")
        self.assertIn("non lu : RuntimeError : HTTP 502", entree["conformite"]["erreurs"])

    def test_auteur_inconnu_de_github(self):
        class Faux:
            def get(self, chemin, **_):
                return (None if chemin == "/users/pwouete" else {"login": "x"}), {}
        projet = {"index": {"cartes": [{"fichier": "registre/code/a.md", "auteurs": ["Pwouette", "pwouete", "Marie Curie"]}]},
                  "conformite": {"erreurs": [], "avertissements": []}}
        memnius.verifier_auteurs(Faux(), [projet])
        self.assertEqual(projet["conformite"]["avertissements"], ["registre/code/a.md : auteur inconnu de GitHub : pwouete"])

    def test_quota_epuise(self):
        import email.message
        import urllib.error
        entetes = email.message.Message()
        entetes["X-RateLimit-Remaining"] = "0"
        entetes["X-RateLimit-Reset"] = str(int(__import__("time").time()) + 30)
        exc = urllib.error.HTTPError("u", 403, "rate limit", entetes, None)
        self.assertTrue(1 <= memnius.GitHub.attente_quota(exc) <= 31)
        entetes.replace_header("X-RateLimit-Reset", str(int(__import__("time").time()) + 3600))
        self.assertIsNone(memnius.GitHub.attente_quota(exc))


if __name__ == "__main__":
    unittest.main()
