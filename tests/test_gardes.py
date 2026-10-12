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
            "AGENTS.md": "# Agents\n\nAppliquer C1–C11 ; O6 si des agents lisent trop large. R2 est abrogée.\n",
            "CONTRIBUTING.md": "# Contribuer\n",
            ".github/workflows/memnius.yml": "name: Memnius\n",
            "memnius.yaml": FICHE.format(id="sujet-test"),
            "registre/decisions/0001-adopter-le-socle.md": ENTREE.format(n="0001"),
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

    def ecrire(self, chemin, texte, commit=True, message="changement"):
        p = self.d / chemin
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texte, encoding="utf-8")
        sh(self.d, "git", "add", "-A")
        if commit:
            sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)

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

    def test_jeton_github_fin_et_jwt(self):
        # Audit Fable (M1) : un jeton github_pat_ nu et un JWT passaient.
        self.ecrire("notes/a.md", "github_pat_" + "A1b2" * 10 + "\n", commit=False)
        self.ecrire("notes/b.md", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U\n", commit=False)
        code, sortie = self.gardes("--seulement", "A2")
        self.assertEqual(code, 1, sortie)
        self.assertIn("notes/a.md:1 : jeton GitHub", sortie)
        self.assertIn("notes/b.md:1 : jeton JWT", sortie)

    def test_fichier_env(self):
        self.ecrire(".env", "RIEN=1\n", commit=False)
        self.assertSonne("A2", ".env : fichier de secrets")

    def test_faux_positif_autorise(self):
        self.ecrire("docs/exemple.md", 'token = "exemple-de-jeton-factice"  <!-- memnius:autorise -->\n', commit=False)
        self.assertVerte("A2")


class A3Structure(DepotDeTest):
    def test_sain(self):
        self.assertVerte("A3")

    def test_agents_absent(self):
        (self.d / "AGENTS.md").unlink()
        self.assertSonne("A3", "AGENTS.md")

    def test_passation_plus_exigee(self):
        self.assertFalse((self.d / "PASSATION.md").exists())
        self.assertVerte("A3")

    def test_fiche_allegee(self):
        # Décision 0017 : seuls schema, id, titre, resume, langue, mainteneurs, socle et visibilite sont exigés.
        self.ecrire("memnius.yaml", textwrap.dedent("""\
            schema: memnius/2
            id: sujet-test
            titre: Sujet de test
            resume: Fiche réduite aux champs obligatoires.
            langue: fr
            mainteneurs:
              - github: mainteneur-test
            socle:
              version: v2
            visibilite: public
            """))
        self.assertVerte("A3")

    def test_champ_obligatoire_manquant(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("langue: fr\n", ""))
        self.assertSonne("A3", "champ obligatoire manquant : langue")

    def test_niveau_du_socle_refuse(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("  version: v2\n", "  version: v2\n  niveau: socle\n"))
        self.assertSonne("A3", "niveau")

    def test_fiche_invalide(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("statut: actif", "statut: fini"))
        self.assertSonne("A3", "statut")

    def test_socle_manquant(self):
        fiche = FICHE.format(id="sujet-test").split("socle:")[0] + "licence: CC-BY-4.0\nvisibilite: public\ncree_le: 2026-09-26\n"
        self.ecrire("memnius.yaml", fiche)
        self.assertSonne("A3", "socle")

    def test_journal_a_l_ancienne_place(self):
        sh(self.d, "git", "mv", "registre/decisions", "decisions")
        self.assertSonne("A3", "git mv decisions registre/decisions")

    def test_fiche_v1_refusee(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("memnius/2", "memnius/1"))
        self.assertSonne("A3", "memnius/2")


class A4Journal(DepotDeTest):
    def test_sain_avec_nouvelle_entree(self):
        self.ecrire("registre/decisions/0002.md", ENTREE.format(n="0002"))
        self.assertVerte("A4", "--base", self.base)

    def test_entree_publiee_modifiee(self):
        self.ecrire("registre/decisions/0001-adopter-le-socle.md", ENTREE.format(n="0001") + "Ajout après coup.\n")
        self.assertSonne("A4", "entrée publiée modifiée", "--base", self.base)

    def base_avec_coquille(self):
        """Une entrée 0002 publiée avec deux fautes, et le commit de base qui la contient."""
        self.ecrire("registre/decisions/0002.md", ENTREE.format(n="0002").replace("Adopter le socle", "Adoptre le socel")
                    + "\nLe projet adopte le socle v2 et ses 7 gardes.\n")
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d, capture_output=True, text=True).stdout.strip()

    def test_coquille_corrigee(self):
        base = self.base_avec_coquille()
        texte = (self.d / "registre/decisions/0002.md").read_text(encoding="utf-8")
        self.ecrire("registre/decisions/0002.md", texte.replace("Adoptre le socel", "Adopter le socle"),
                    message="Coquille dans la décision 0002")
        self.assertVerte("A4", "--base", base)

    def test_coquille_qui_reecrit_le_fond(self):
        # Audits du 2026-10-11 : tout le texte remplacé sous le nom de « coquille ».
        base = self.base_avec_coquille()
        texte = (self.d / "registre/decisions/0002.md").read_text(encoding="utf-8")
        self.ecrire("registre/decisions/0002.md", texte.replace("Le projet adopte le socle v2 et ses 7 gardes.",
                    "Tout le contraire : on utilise numpy, scipy et matplotlib partout."), message="coquille")
        self.assertSonne("A4", "plus qu'une coquille", "--base", base)

    def test_coquille_qui_ajoute_une_negation(self):
        base = self.base_avec_coquille()
        texte = (self.d / "registre/decisions/0002.md").read_text(encoding="utf-8")
        self.ecrire("registre/decisions/0002.md", texte.replace("Le projet adopte", "Le projet n'adopte pas"), message="coquille")
        self.assertSonne("A4", "mots ajoutés ou retirés", "--base", base)

    def test_coquille_qui_change_un_nombre(self):
        base = self.base_avec_coquille()
        texte = (self.d / "registre/decisions/0002.md").read_text(encoding="utf-8")
        self.ecrire("registre/decisions/0002.md", texte.replace("7 gardes", "5 gardes"), message="coquille")
        self.assertSonne("A4", "nombre changé", "--base", base)

    def test_coquille_qui_ajoute_un_champ(self):
        base = self.base_avec_coquille()
        texte = (self.d / "registre/decisions/0002.md").read_text(encoding="utf-8")
        self.ecrire("registre/decisions/0002.md", texte.replace("- Remplace", "- Source : x\n- Remplace"), message="coquille")
        self.assertSonne("A4", "champ ajouté ou retiré", "--base", base)

    def test_coquille_sans_le_dire(self):
        corrigee = ENTREE.format(n="0001").replace("Adopter le socle", "Adopter le socle commun")
        self.ecrire("registre/decisions/0001-adopter-le-socle.md", corrigee, message="petite retouche")
        self.assertSonne("A4", "entrée publiée modifiée", "--base", self.base)

    def test_coquille_qui_touche_un_champ(self):
        corrigee = ENTREE.format(n="0001").replace("2026-09-26", "2026-09-27")
        self.ecrire("registre/decisions/0001-adopter-le-socle.md", corrigee, message="coquille sur la date")
        self.assertSonne("A4", "entrée publiée modifiée", "--base", self.base)

    def test_entree_a_remplir_puis_remplie(self):
        # Entrée créée à partir du modèle, remplie par la pull request suivante.
        self.ecrire("registre/decisions/0001-adopter-le-socle.md", ENTREE.format(n="0001").replace("2026-09-26", "AAAA-MM-JJ"))
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d, capture_output=True, text=True).stdout.strip()
        self.ecrire("registre/decisions/0001-adopter-le-socle.md", ENTREE.format(n="0001"))
        self.assertVerte("A4", "--base", base)

    def test_entree_publiee_supprimee(self):
        (self.d / "registre/decisions/0001-adopter-le-socle.md").unlink()
        self.ecrire("registre/decisions/0002.md", ENTREE.format(n="0002"))
        self.assertSonne("A4", "entrée publiée", "--base", self.base)  # vue par Git comme supprimée ou renommée

    def test_sans_marqueur_origine(self):
        self.ecrire("registre/decisions/0002.md", ENTREE.format(n="0002").replace("[humain] ", ""))
        self.assertSonne("A4", "[humain], [choix] ou [agent]")

    def test_nom_non_conforme(self):
        self.ecrire("registre/decisions/choix-du-format.md", ENTREE.format(n="0002"))
        self.assertSonne("A4", "nom attendu")

    def test_valeurs_du_modele(self):
        self.ecrire("registre/decisions/0002.md", ENTREE.format(n="0002").replace("2026-09-26", "AAAA-MM-JJ"))
        self.assertSonne("A4", "valeurs du modèle")

    def test_journal_deplace_dans_le_registre(self):
        # Projet qui tenait son journal à la racine (avant la décision 0016 du socle) et le déplace.
        sh(self.d, "git", "mv", "registre/decisions", "decisions")
        sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "ancien emplacement")
        base = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.d, capture_output=True, text=True).stdout.strip()
        self.assertSonne("A4", "le journal vit dans registre/decisions/")
        sh(self.d, "git", "mv", "decisions", "registre/decisions")
        sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "journal dans le registre")
        self.assertVerte("A4", "--base", base)

    def test_base_introuvable_compte_comme_echec(self):
        self.assertSonne("A4", "n'a pas pu tourner", "--base", "f" * 40)


class A5Renvois(DepotDeTest):
    def test_sain(self):
        self.assertVerte("A5")

    def test_regle_inexistante(self):
        self.ecrire("AGENTS.md", "# Agents\n\nVoir la règle C12.\n")
        self.assertSonne("A5", "C12 n'existe pas")

    def test_mots_courants_pas_des_renvois(self):
        # Audit Fable (F3) : « format A4 » et « vitamine C6 » ne citent pas de règle.
        self.ecrire("README.md", "# Sujet\n\nImprimer au format A4. La vitamine C6 n'existe pas.\n")
        self.assertVerte("A5")

    def test_renvoi_entre_parentheses(self):
        self.ecrire("README.md", "# Sujet\n\nToute pull request est relue (C12).\n")
        self.assertSonne("A5", "C12 n'existe pas")

    def test_option_inconnue(self):
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test").replace("options: []", "options: [O9]"))
        self.assertSonne("A5", "option du socle inconnue : O9")

    def test_regle_abrogee_citee(self):
        self.ecrire("AGENTS.md", "# Agents\n\nToute pull request est relue (C6).\n")
        self.assertSonne("A5", "C6 est abrogée")

    def test_regle_abrogee_dans_le_journal(self):
        # Le journal est l'histoire : une ancienne entrée peut citer une règle abrogée depuis.
        self.ecrire("registre/decisions/0002.md", ENTREE.format(n="0002") + "\nLes règles R1–R8 s'appliquent (C9).\n")
        self.assertVerte("A5")

    def test_regle_abrogee_modifiee(self):
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

    def test_gros_fichier_lfs_refuse(self):
        # Décision 0017 : Git LFS n'est plus une échappatoire, on mesure le fichier désigné par le pointeur.
        pointeur = "version https://git-lfs.github.com/spec/v1\noid sha256:" + "0" * 64 + "\nsize 50000000\n"
        self.ecrire("donnees/brut/gros.h5", pointeur, commit=False)
        self.assertSonne("A6", "donnees/brut/gros.h5 (50.0 Mo)")

    def test_gros_fichier_ajoute_puis_retire_dans_la_branche(self):
        # Audit Opus (M2) : sans --base, A6 ne voit que l'état final ; avec, il lit chaque commit de la branche.
        (self.d / "donnees/brut").mkdir(parents=True, exist_ok=True)
        (self.d / "donnees/brut/gros.bin").write_bytes(os.urandom(11_000_000))
        sh(self.d, "git", "add", "-A")
        sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "ajout")
        sh(self.d, "git", "rm", "-q", "donnees/brut/gros.bin")
        sh(self.d, "git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "retrait")
        self.assertVerte("A6")
        self.assertSonne("A6", "donnees/brut/gros.bin (11.0 Mo, dans un commit de la branche)", "--base", self.base)

    def test_historique_sain(self):
        self.ecrire("donnees/brut/mesures.csv", "x,y\n" * 1000)
        self.assertVerte("A6", "--base", self.base)

    def test_petit_fichier_lfs_accepte(self):
        pointeur = "version https://git-lfs.github.com/spec/v1\noid sha256:" + "0" * 64 + "\nsize 300000\n"
        self.ecrire("donnees/brut/image.png", pointeur, commit=False)
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

    def test_index_ecrit_par_la_ci(self):
        # Règle C11 (décision 0017) : l'index et les blocs de liens sont écrits par la CI, A7 ne les contrôle pas.
        self.ecrire("registre/code/autre.md", CARTE)
        self.ecrire("registre/INDEX.md", "# Index retouché\n")
        self.assertVerte("A7")
        (self.d / "registre/INDEX.md").unlink()
        (self.d / "registre/index.json").unlink()
        sh(self.d, "git", "add", "-A")
        self.assertVerte("A7")

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
        # Par défaut, tout fichier rangé dans un dossier hors registre/ et dossiers cachés (audits, M4).
        self.ecrire("travaux/orphelin.py", "pass\n")
        code, sortie = self.gardes("--seulement", "A7")
        self.assertEqual(code, 0, sortie)
        self.assertIn("2 fichiers sans carte : notes/idee.md, travaux/orphelin.py", sortie)
        self.assertNotIn(".github", sortie)

    def test_couverture_declaree(self):
        self.ecrire("site/index.html", "<p>x</p>\n")
        self.ecrire("memnius.yaml", FICHE.format(id="sujet-test") + "registre:\n  a_couvrir: [site/]\n")
        code, sortie = self.gardes("--seulement", "A3,A7")
        self.assertEqual(code, 0, sortie)
        self.assertIn("1 fichiers sans carte : site/index.html", sortie)

    def test_donnees_hors_depot_sans_empreinte(self):
        donnees = CARTE.replace("travaux/calcul.py", "https://zenodo.org/records/1").replace("langage: python\n", "")
        self.ecrire("registre/donnees/mesures.md", donnees)
        self.assertSonne("A7", "« empreinte »")
        self.ecrire("registre/donnees/mesures.md", donnees.replace("date:", "empreinte: sha256:" + "a" * 64 + "\ndate:"))
        self.assertVerte("A7")

    def test_carte_de_document(self):
        # Décision 0021 : cartes des notes, synthèses, exposés et livrables ; dossier registre/documents/ facultatif.
        self.ecrire("notes/synthese.md", "# Synthèse\n")
        self.ecrire("registre/documents/synthese.md", CARTE.replace("travaux/calcul.py", "notes/synthese.md")
                    .replace("langage: python", "format: synthèse"))
        code, sortie = self.gardes("--seulement", "A7")
        self.assertEqual(code, 0, sortie)
        self.assertNotIn("le champ « format »", sortie)
        self.assertNotIn("notes/synthese.md", sortie)  # couvert par sa carte

    def test_message_en_francais(self):
        self.ecrire("registre/code/calcul.md", CARTE.replace("langage: python", "langue: python"))
        self.assertSonne("A7", "champ inconnu : langue")


if __name__ == "__main__":
    unittest.main()
