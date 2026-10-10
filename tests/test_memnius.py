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
        self.assertIn("decision, code, donnees ou sources", sortie)

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
        for f in ("AGENTS.md", "PASSATION.md", "registre/README.md", "registre/INDEX.md", ".github/workflows/memnius.yml"):
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

    def test_journal_existant_garde(self):
        (self.d / "registre/decisions").mkdir(parents=True)
        (self.d / "registre/decisions/0001-autre-chose.md").write_text("# 0001 — Autre chose\n", encoding="utf-8")
        lancer("init", str(self.d))
        self.assertEqual(sorted(p.name for p in (self.d / "registre/decisions").iterdir()), ["0001-autre-chose.md"])


class Index(DepotDeTest):
    def test_contenu(self):
        index = json.loads((self.d / "registre/index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["projet"], "sujet-test")
        self.assertEqual(index["comptes"], {"decision": 1, "code": 1, "donnees": 0, "sources": 0})
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


class SuperRegistre(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.racine = Path(self._tmp.name) / "projets"
        self.sortie = Path(self._tmp.name) / "sortie"
        for nom, carte in (("alpha", CARTE), ("beta", CARTE.replace("langage: python", "liens: [alpha:code/calcul, alpha:code/absent]"))):
            d = self.racine / nom
            fichiers = {
                "README.md": "# Projet\n", "AGENTS.md": "# Agents\n", "CONTRIBUTING.md": "# Contribuer\n",
                "PASSATION.md": "# Passation\n", ".github/workflows/memnius.yml": "name: Memnius\n",
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

    def test_vue_generale(self):
        code, sortie = lancer("registre", "--local", str(self.racine), "--sortie", str(self.sortie))
        self.assertEqual(code, 0, sortie)
        self.assertIn("2 projets, 4 cartes", sortie)
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

    def test_projet_sans_registre(self):
        d = self.racine / "alpha"
        for f in ("registre/index.json", "registre/INDEX.md"):
            (d / f).unlink()
        lancer("registre", "--local", str(self.racine), "--sortie", str(self.sortie))
        registre = json.loads((self.sortie / "registre.json").read_text(encoding="utf-8"))
        alpha = next(p for p in registre["projets"] if p["id"] == "alpha")
        self.assertEqual(alpha["conformite"]["niveau"], "non-conforme")
        self.assertIsNone(alpha["index"])


if __name__ == "__main__":
    unittest.main()
