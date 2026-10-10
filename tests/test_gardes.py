"""Chaque garde est testée dans les deux sens : elle accepte un dépôt sain et refuse un cas fautif.

Lancer depuis la racine du dépôt registre : python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

GARDES = Path(__file__).resolve().parent.parent / "outils" / "gardes.py"
sys.path.insert(0, str(GARDES.parent))
import memnius  # noqa: E402

FICHE = textwrap.dedent("""\
    schema: memnius/2
    id: {id}
    titre: Sujet de test
    resume: Un sujet minimal qui respecte le socle, pour tester les gardes.
    statut: actif
    nature: etude
    domaines: [physique]
    langue: fr
    mainteneurs:
      - github: mainteneur-test
    agents:
      politique: relecture-humaine
    socle:
      version: v2
      niveau: socle
      options: []
    licence: CC-BY-4.0
    visibilite: public
    cree_le: 2026-09-26
    """)

ENTREE = textwrap.dedent("""\
    # {n} — Adopter le socle

    - Date : 2026-09-26
    - Origine : [humain] « on adopte le socle »
    - Décidé par : @mainteneur-test
    - Remplace : —
    """)


CARTE = textwrap.dedent("""\
    ---
    titre: Calcul de test
    resume: Un calcul minimal décrit par une carte.
    ou: [travaux/calcul.py]
    auteurs: [mainteneur-test]
    date: 2026-10-10
    langage: python
    ---

    Notes libres.
    """)


def sh(dossier, *args):
    subprocess.run(args, cwd=dossier, check=True, capture_output=True)


class DepotDeTest(unittest.TestCase):
    """Crée un dépôt Git sain dans un dossier temporaire nommé comme son id."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name) / "sujet-test"
        self.d.mkdir()
        fichiers = {
            "README.md": "# Sujet de test\n\nVoir la règle C2 et la garde A4.\n",
            "AGENTS.md": "# Agents\n\nAppliquer C1–C10 ; R2 si des agents écrivent.\n",
            "CONTRIBUTING.md": "# Contribuer\n",
            "PASSATION.md": "# Passation\n\n## 5. Ce qui reste dû ou en cours *\n- rien\n",
            ".github/workflows/memnius.yml": "name: Memnius\n",
            "memnius.yaml": FICHE.format(id="sujet-test"),
            "decisions/0001-adopter-le-socle.md": ENTREE.format(n="0001"),
            "notes/idee.md": "Une note ordinaire qui parle de C99 sans être un fichier de gouvernance.\n",
            "travaux/calcul.py": "print(42)\n",
            "registre/README.md": "# Registre\n\nVoir la règle C11 et la garde A7.\n",
            "registre/code/calcul.md": CARTE,
            "registre/donnees/.gitkeep": "",
            "registre/sources/.gitkeep": "",
        }
        for chemin, texte in fichiers.items():
            (self.d / chemin).parent.mkdir(parents=True, exist_ok=True)
            (self.d / chemin).write_text(texte, encoding="utf-8")
        memnius.ecrire_index(self.d)
        sh(self.d, "git", "init", "-q", "-b", "main")
        sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A")
        sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "initial")
        self.base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d, capture_output=True, text=True).stdout.strip()

    def tearDown(self):
        self._tmp.cleanup()

    def ecrire(self, chemin, texte, commit=True):
        p = self.d / chemin
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texte, encoding="utf-8")
        sh(self.d, "git", "add", "-A")
        if commit:
            sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "changement")

    def gardes(self, *options):
        r = subprocess.run([sys.executable, str(GARDES), str(self.d), *options], capture_output=True, text=True)
        return r.returncode, r.stdout

    def assertVerte(self, garde, *options, **kw):
        code, sortie = self.gardes("--seulement", garde, *options, **kw)
        self.assertIn(f"[ ok ] {garde}", sortie, sortie)
        self.assertEqual(code, 0, sortie)

    def assertSonne(self, garde, motif, *options, **kw):
        code, sortie = self.gardes("--seulement", garde, *options, **kw)
        self.assertIn(f"[FIRE] {garde}", sortie, sortie)
        self.assertIn(motif, sortie)
        self.assertEqual(code, 1, sortie)


class Ensemble(DepotDeTest):
    def test_depot_sain_toutes_vertes(self):
        code, sortie = self.gardes("--base", self.base)
        self.assertEqual(code, 0, sortie)
        self.assertIn("Bilan : 6/6 gardes vertes", sortie)


class A2Secrets(DepotDeTest):
    def test_sain(self):
        self.assertVerte("A2")

    def test_jeton_gitlab(self):
        self.ecrire("travaux/config.py", 'URL = "x"\nJETON = "glpat-' + "a" * 20 + '"\n', commit=False)
        self.assertSonne("A2", "travaux/config.py:2 : jeton GitLab")

    def test_mot_de_passe_en_clair(self):
        self.ecrire("notes/acces.md", 'password = "correcthorsebattery"\n', commit=False)  # memnius:autorise (faux secret de test)
        self.assertSonne("A2", "mot de passe")

    def test_fichier_env(self):
        self.ecrire(".env", "RIEN=1\n", commit=False)
        self.assertSonne("A2", ".env : fichier de secrets")

    def test_faux_positif_autorise(self):
        self.ecrire("docs/exemple.md", 'token = "exemple-de-jeton-factice"  <!-- memnius:autorise -->\n', commit=False)
        self.assertVerte("A2")


class A3Structure(DepotDeTest):
    def test_sain(self):
        self.assertVerte("A3")

    def test_passation_absente(self):
        (self.d / "PASSATION.md").unlink()
        self.assertSonne("A3", "PASSATION.md")

    def test_fiche_invalide(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("statut: actif", "statut: fini"))
        self.assertSonne("A3", "statut")

    def test_socle_manquant(self):
        fiche = FICHE.format(id="sujet-test").split("socle:")[0] + "licence: CC-BY-4.0\nvisibilite: public\ncree_le: 2026-09-26\n"
        self.ecrire("memnius.yaml", fiche)
        self.assertSonne("A3", "socle")

    def test_fiche_v1_refusee(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("memnius/2", "memnius/1"))
        self.assertSonne("A3", "memnius/2")


class A4Journal(DepotDeTest):
    def test_sain_avec_nouvelle_entree(self):
        self.ecrire("decisions/0002.md", ENTREE.format(n="0002"))
        self.assertVerte("A4", "--base", self.base)

    def test_entree_publiee_modifiee(self):
        self.ecrire("decisions/0001-adopter-le-socle.md", ENTREE.format(n="0001") + "Ajout après coup.\n")
        self.assertSonne("A4", "entrée publiée modifiée", "--base", self.base)

    def test_entree_a_remplir_puis_remplie(self):
        # Entrée créée à partir du modèle, remplie par la pull request suivante.
        self.ecrire("decisions/0001-adopter-le-socle.md", ENTREE.format(n="0001").replace("2026-09-26", "AAAA-MM-JJ"))
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d, capture_output=True, text=True).stdout.strip()
        self.ecrire("decisions/0001-adopter-le-socle.md", ENTREE.format(n="0001"))
        self.assertVerte("A4", "--base", base)

    def test_entree_publiee_supprimee(self):
        (self.d / "decisions/0001-adopter-le-socle.md").unlink()
        self.ecrire("decisions/0002.md", ENTREE.format(n="0002"))
        self.assertSonne("A4", "entrée publiée", "--base", self.base)  # vue par Git comme supprimée ou renommée

    def test_sans_marqueur_origine(self):
        self.ecrire("decisions/0002.md", ENTREE.format(n="0002").replace("[humain] ", ""))
        self.assertSonne("A4", "[humain], [choix] ou [agent]")

    def test_nom_non_conforme(self):
        self.ecrire("decisions/choix-du-format.md", ENTREE.format(n="0002"))
        self.assertSonne("A4", "nom attendu")

    def test_valeurs_du_modele(self):
        self.ecrire("decisions/0002.md", ENTREE.format(n="0002").replace("2026-09-26", "AAAA-MM-JJ"))
        self.assertSonne("A4", "valeurs du modèle")

    def test_base_introuvable_compte_comme_echec(self):
        self.assertSonne("A4", "n'a pas pu tourner", "--base", "f" * 40)


class A5Renvois(DepotDeTest):
    def test_sain(self):
        self.assertVerte("A5")

    def test_regle_inexistante(self):
        self.ecrire("AGENTS.md", "# Agents\n\nVoir la règle C12.\n")
        self.assertSonne("A5", "C12 n'existe pas")

    def test_option_inconnue(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("options: []", "options: [O9]"))
        self.assertSonne("A5", "option du socle inconnue : O9")

    def test_regle_abrogee(self):
        sys.path.insert(0, str(GARDES.parent))
        import gardes as module
        ancien = module.REGLES
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False, encoding="utf-8") as f:
            f.write(ancien.read_text(encoding="utf-8").replace(
                "C2: {titre: Décision écrite, niveau: socle}", "C2: {titre: Décision écrite, niveau: socle, abrogee: true}"))
        module.REGLES = Path(f.name)
        try:
            with self.assertRaises(module.Feu) as feu:
                module.garde_a5(self.d, module.fichiers_suivis(self.d))
            self.assertIn("C2 est abrogée", str(feu.exception))
        finally:
            module.REGLES = ancien
            os.unlink(f.name)


class A6GrosFichiers(DepotDeTest):
    def test_sain(self):
        self.ecrire("donnees/brut/mesures.csv", "x,y\n" * 1000, commit=False)
        self.assertVerte("A6")

    def test_fichier_de_11_mo(self):
        (self.d / "donnees/brut").mkdir(parents=True, exist_ok=True)
        (self.d / "donnees/brut/gros.bin").write_bytes(os.urandom(11_000_000))
        sh(self.d, "git", "add", "-A")
        self.assertSonne("A6", "donnees/brut/gros.bin (11.0 Mo)")

    def test_pointeur_lfs_accepte(self):
        pointeur = "version https://git-lfs.github.com/spec/v1\noid sha256:" + "0" * 64 + "\nsize 50000000\n"
        self.ecrire("donnees/brut/gros.h5", pointeur, commit=False)
        self.assertVerte("A6")


class A7Registre(DepotDeTest):
    def test_sain(self):
        self.assertVerte("A7")

    def test_nouvelle_carte_avec_index_regenere(self):
        self.ecrire("sources/livre.bib", "@book{x, title={X}}\n", commit=False)
        self.ecrire("registre/sources/livre.md", CARTE.replace("travaux/calcul.py", "sources/livre.bib")
                    .replace("langage: python\n", "reference: Auteur, Livre, 2020\n"), commit=False)
        memnius.ecrire_index(self.d)
        self.assertVerte("A7")

    def test_index_perime(self):
        self.ecrire("registre/code/autre.md", CARTE)
        self.assertSonne("A7", "index absent ou pas à jour")

    def test_index_edite_a_la_main(self):
        self.ecrire("registre/INDEX.md", "# Index retouché\n")
        self.assertSonne("A7", "registre/INDEX.md")

    def test_carte_sans_auteur(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("auteurs: [mainteneur-test]\n", ""))
        memnius.ecrire_index(self.d)
        self.assertSonne("A7", "auteurs")

    def test_emplacement_inexistant(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("travaux/calcul.py", "travaux/absent.py"))
        memnius.ecrire_index(self.d)
        self.assertSonne("A7", "« travaux/absent.py » n'existe pas")

    def test_emplacement_hors_du_depot(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("travaux/calcul.py", "../ailleurs.py"))
        memnius.ecrire_index(self.d)
        self.assertSonne("A7", "chemin relatif")

    def test_lien_vers_carte_inconnue(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("langage: python", "liens: [sources/inconnue]"))
        memnius.ecrire_index(self.d)
        self.assertSonne("A7", "lien vers une carte inconnue : sources/inconnue")

    def test_lien_vers_une_decision(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("langage: python", "liens: [decisions/0001]"))
        memnius.ecrire_index(self.d)
        self.assertVerte("A7")

    def test_carte_sans_en_tete(self):
        self.ecrire("registre/code/calcul.md", "# Calcul\n\nPas d'en-tête.\n")
        memnius.ecrire_index(self.d)
        self.assertSonne("A7", "en-tête absent")

    def test_carte_a_remplir(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("Calcul de test", "À_REMPLIR"))
        memnius.ecrire_index(self.d)
        self.assertSonne("A7", "À_REMPLIR")

    def test_dossier_du_registre_absent(self):
        (self.d / "registre/sources/.gitkeep").unlink()
        sh(self.d, "git", "add", "-A")
        self.assertSonne("A7", "registre/sources/")

    def test_rangement_hors_structure(self):
        self.ecrire("registre/divers/note.md", "texte\n")
        self.assertSonne("A7", "hors de la structure commune")

    def test_fichier_sans_carte_signale_sans_bloquer(self):
        self.ecrire("travaux/orphelin.py", "pass\n")
        code, sortie = self.gardes("--seulement", "A7")
        self.assertEqual(code, 0, sortie)
        self.assertIn("sans carte : travaux/orphelin.py", sortie)


if __name__ == "__main__":
    unittest.main()
