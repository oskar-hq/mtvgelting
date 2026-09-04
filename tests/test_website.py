"""Prüfungen für Generator und CMS-Anbindung.

    python3 -m unittest discover -s tests

Die Sanity-API wird dabei nicht angesprochen: die Antworten werden nachgebaut.
Der wichtigste Test ist `RundeReise` — er stellt sicher, dass die Feldnamen in
tools/nach_sanity.py, in der GROQ-Abfrage und in tools/sanity.py zusammenpassen.
Ein Tippfehler in einem Feldnamen fällt sonst erst im echten Betrieb auf.
"""

import io
import json
import pathlib
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tools import inhalte, nach_sanity, sanity          # noqa: E402
from tools.render import SEITEN, Renderer               # noqa: E402


class StilleMedien(sanity.Medien):
    """Medien, die nichts herunterladen — für Tests ohne Netz."""

    def __init__(self, wurzel, fehlschlag=False):
        super().__init__(wurzel, laden=self._erfinden)
        self.fehlschlag = fehlschlag
        self.abgerufen = []

    def _erfinden(self, adresse):
        self.abgerufen.append(adresse)
        if self.fehlschlag:
            raise urllib.error.URLError("kein Netz")
        return b"BILDDATEN"


def antwort(nutzlast, code=200):
    """Eine urlopen-Antwort nachbauen."""

    class Antwort(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_):
            self.close()

    return Antwort(json.dumps(nutzlast).encode("utf-8"))


# ---------------------------------------------------------------------------


class Generator(unittest.TestCase):
    def test_alle_seiten_aus_data(self):
        V, A = inhalte.aus_json()
        seiten = Renderer(V, A).pages()
        self.assertEqual(sorted(seiten), sorted(SEITEN))
        for name, seite in seiten.items():
            self.assertTrue(seite.startswith("<!doctype html>"), name)
            self.assertIn("</html>", seite)
            self.assertNotIn("None", seite.replace("None-", ""), name)

    def test_trainingszeiten_stehen_in_karte_und_wochenplan(self):
        V, A = inhalte.aus_json()
        seiten = Renderer(V, A).pages()
        self.assertIn("B. Kratz", seiten["sportangebot.html"])
        self.assertIn("B. Kratz", seiten["termine.html"])

    def test_sponsorenraster_kennt_die_anzahl(self):
        V, A = inhalte.aus_json()
        V = dict(V, sponsoren=[{"name": "Einer", "logo": "", "url": ""}])
        self.assertIn('data-anzahl="1"', Renderer(V, A).pages()["index.html"])

    def test_ohne_anmeldelink_im_footer(self):
        V, A = inhalte.aus_json()
        self.assertNotIn("/admin/", Renderer(V, A).pages()["index.html"])


class Telefonlink(unittest.TestCase):
    def test_ableitung(self):
        self.assertEqual(inhalte.telefonlink("04643 1316"), "+4946431316")
        self.assertEqual(inhalte.telefonlink("+49 4643 1316"), "+4946431316")
        self.assertEqual(inhalte.telefonlink(""), "")

    def test_eigene_angabe_hat_vorrang(self):
        self.assertEqual(inhalte.telefonlink("04643 1316", "+49123"), "+49123")


class Abfrage(unittest.TestCase):
    def test_ergebnis_wird_ausgepackt(self):
        gerufen = {}

        def oeffnen(adresse, kopfzeilen):
            gerufen["adresse"] = adresse
            gerufen["kopfzeilen"] = kopfzeilen
            return antwort({"result": {"verein": {"name": "MTV"}}})

        ergebnis = sanity.abfragen("abc", "production", "geheim", oeffnen=oeffnen)
        self.assertEqual(ergebnis["verein"]["name"], "MTV")
        self.assertIn("abc.api.sanity.io", gerufen["adresse"])
        self.assertIn("/data/query/production", gerufen["adresse"])
        self.assertEqual(gerufen["kopfzeilen"]["Authorization"], "Bearer geheim")

    def test_ohne_token_keine_kopfzeile(self):
        gerufen = {}

        def oeffnen(adresse, kopfzeilen):
            gerufen.update(kopfzeilen)
            return antwort({"result": {}})

        sanity.abfragen("abc", oeffnen=oeffnen)
        self.assertNotIn("Authorization", gerufen)

    def test_entwuerfe_bleiben_draussen(self):
        self.assertIn("drafts.**", sanity.ABFRAGE)
        # Jede Liste muss den Filter tragen, sonst rutschen halbfertige
        # Einträge auf die Website.
        self.assertEqual(sanity.ABFRAGE.count("_type =="),
                         sanity.ABFRAGE.count("!(_id in path('drafts.**'))"))

    def test_fehlermeldung_bei_fehlender_berechtigung(self):
        def oeffnen(adresse, kopfzeilen):
            raise urllib.error.HTTPError(adresse, 401, "Unauthorized", {}, None)

        with self.assertRaises(sanity.SanityFehler) as f:
            sanity.abfragen("abc", oeffnen=oeffnen)
        self.assertIn("SANITY_TOKEN", str(f.exception))

    def test_fehlermeldung_wenn_nicht_erreichbar(self):
        def oeffnen(adresse, kopfzeilen):
            raise urllib.error.URLError("Name or service not known")

        with self.assertRaises(sanity.SanityFehler):
            sanity.abfragen("abc", oeffnen=oeffnen)

    def test_unerwartete_antwort(self):
        with self.assertRaises(sanity.SanityFehler):
            sanity.abfragen("abc", oeffnen=lambda a, k: antwort({"error": "kaputt"}))


class Medien(unittest.TestCase):
    def bild(self, kennung="image-abc-1200x800-png", name="Logo Muster.png", endung="png"):
        return {"asset": {"_id": kennung, "url": "https://cdn.sanity.io/images/x/y/%s.%s"
                                                 % (kennung, endung),
                          "originalFilename": name, "extension": endung}}

    def test_bild_wird_abgelegt(self):
        with tempfile.TemporaryDirectory() as ordner:
            m = StilleMedien(ordner)
            pfad = m.bild(self.bild())
            self.assertTrue(pfad.startswith("assets/img/inhalte/"), pfad)
            self.assertTrue(pfad.endswith(".png"))
            self.assertTrue((pathlib.Path(ordner) / pfad).exists())
            # Der Name enthält den lesbaren Originalnamen …
            self.assertIn("logo-muster", pfad)
            # … und die Breite wird beim CDN angefordert, statt das Original zu laden.
            self.assertIn("w=%d" % sanity.BILDBREITE, m.abgerufen[0])

    def test_dateiname_bleibt_ueber_neubauten_gleich(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.assertEqual(StilleMedien(a).bild(self.bild()),
                             StilleMedien(b).bild(self.bild()))

    def test_verschiedene_bilder_kollidieren_nicht(self):
        with tempfile.TemporaryDirectory() as ordner:
            m = StilleMedien(ordner)
            eins = m.bild(self.bild("image-eins-1x1-png"))
            zwei = m.bild(self.bild("image-zwei-1x1-png"))
            self.assertNotEqual(eins, zwei)

    def test_pdf_landet_bei_den_dokumenten(self):
        with tempfile.TemporaryDirectory() as ordner:
            feld = {"asset": {"_id": "file-abc-pdf", "originalFilename": "Satzung.pdf",
                              "extension": "pdf",
                              "url": "https://cdn.sanity.io/files/x/y/abc.pdf"}}
            pfad = StilleMedien(ordner).datei(feld)
            self.assertTrue(pfad.startswith("assets/dokumente/"), pfad)
            self.assertTrue(pfad.endswith(".pdf"))

    def test_leeres_feld_ergibt_leeren_pfad(self):
        with tempfile.TemporaryDirectory() as ordner:
            m = StilleMedien(ordner)
            self.assertEqual(m.bild(None), "")
            self.assertEqual(m.bild({}), "")
            self.assertEqual(m.datei({"asset": None}), "")

    def test_fehlschlag_bricht_den_build_nicht_ab(self):
        with tempfile.TemporaryDirectory() as ordner:
            self.assertEqual(StilleMedien(ordner, fehlschlag=True).bild(self.bild()), "")


# ---------------------------------------------------------------------------


def groq_nachstellen(docs):
    """Nachbilden, was die GROQ-Abfrage aus den Dokumenten machen würde.

    Bewusst von Hand nachgebaut statt die Abfrage auszuführen: so prüft der
    Test genau die Stelle, an der Fehler entstehen — die Feldnamen zwischen
    dem, was hochgeladen, und dem, was gelesen wird.
    """
    nach_typ = {}
    for d in docs:
        nach_typ.setdefault(d["_type"], []).append(d)

    def sortiert(typ, *felder):
        return sorted(nach_typ.get(typ, []),
                      key=lambda d: tuple(d.get(f) or "" if isinstance(d.get(f), str)
                                          else (d.get(f) or 0) for f in felder))

    def erster(typ):
        eintraege = nach_typ.get(typ, [])
        return eintraege[0] if eintraege else None

    kennungen = {d["_id"]: d for d in docs}

    def kennung_von(verweis):
        if not verweis:
            return None
        ziel = kennungen.get(verweis["_ref"])
        return ziel["kennung"]["current"] if ziel else None

    angebote = []
    for a in sorted(nach_typ.get("angebot", []), key=lambda d: d.get("sortierung", 0)):
        angebote.append({
            "slug": a["slug"]["current"],
            "name": a.get("name"),
            "kurz": a.get("kurz"),
            "text": a.get("text"),
            "ort": a.get("ort"),
            "leitung": a.get("leitung"),
            "kontaktEmail": a.get("kontaktEmail"),
            "kontaktTelefon": a.get("kontaktTelefon"),
            "kategorie": kennung_von(a.get("kategorie")),
            "zielgruppen": [kennung_von(z) for z in a.get("zielgruppen", [])],
            "zeiten": a.get("zeiten", []),
        })

    return {
        "verein": erster("verein"),
        "texte": erster("texte"),
        "vorstand": sortiert("vorstandsmitglied", "sortierung"),
        "beitraege": sortiert("beitrag", "sortierung"),
        "termine": sortiert("termin", "sortierung"),
        "news": sorted(nach_typ.get("news", []), key=lambda d: d.get("datum") or "",
                       reverse=True),
        "aktionen": sortiert("aktion", "sortierung"),
        "sponsoren": [{"name": s.get("name"), "url": s.get("url"), "logo": s.get("logo")}
                      for s in sortiert("sponsor", "sortierung")],
        "spielplaene": sortiert("spielplan", "sortierung"),
        "dokumente": [{"bereich": d.get("bereich"), "titel": d.get("titel"),
                       "beschreibung": d.get("beschreibung"), "url": d.get("url"),
                       "datei": d.get("datei")}
                      for d in sorted(nach_typ.get("dokument", []),
                                      key=lambda d: (d.get("bereich") or "",
                                                     d.get("sortierung", 0)))],
        "kategorien": [{"id": k["kennung"]["current"], "name": k.get("name")}
                       for k in sortiert("kategorie", "sortierung")],
        "zielgruppen": [{"id": z["kennung"]["current"], "name": z.get("name")}
                        for z in sortiert("zielgruppe", "sortierung")],
        "angebote": angebote,
    }


class RundeReise(unittest.TestCase):
    """data/*.json → Sanity → zurück muss dieselben Seiten ergeben.

    Deckt die Feldnamen in beiden Richtungen ab: schreibt nach_sanity.py etwa
    `kontaktEmail`, liest sanity.py aber `kontaktMail`, fällt das hier auf.
    """

    def setUp(self):
        self.V, self.A = inhalte.aus_json()
        self.docs = nach_sanity.dokumente_bauen(self.V, self.A)
        self.ordner = tempfile.TemporaryDirectory()
        self.gelesen = sanity.nach_inhalten(groq_nachstellen(self.docs),
                                            StilleMedien(self.ordner.name))

    def tearDown(self):
        self.ordner.cleanup()

    def test_seiten_sind_identisch(self):
        aus_dateien = Renderer(self.V, self.A).pages()
        aus_cms = Renderer(*self.gelesen).pages()
        for name in aus_dateien:
            self.assertEqual(aus_dateien[name], aus_cms[name],
                             "%s unterscheidet sich zwischen data/ und CMS" % name)

    def test_alle_angebote_kommen_an(self):
        V, A = self.gelesen
        self.assertEqual(len(A["angebote"]), len(self.A["angebote"]))
        self.assertEqual([a["slug"] for a in A["angebote"]],
                         [a["slug"] for a in self.A["angebote"]])

    def test_trainingszeiten_bleiben_vollstaendig(self):
        V, A = self.gelesen
        vorher = sum(len(a["zeiten"]) for a in self.A["angebote"])
        nachher = sum(len(a["zeiten"]) for a in A["angebote"])
        self.assertEqual(vorher, nachher)
        self.assertGreater(nachher, 50)

    def test_verweise_loesen_sich_auf(self):
        V, A = self.gelesen
        kennungen = {k["id"] for k in A["kategorien"]}
        for a in A["angebote"]:
            self.assertIn(a["kategorie"], kennungen, a["name"])

    def test_dokumentschluessel_sind_eindeutig(self):
        schluessel = [d["_id"] for d in self.docs]
        doppelte = {k for k in schluessel if schluessel.count(k) > 1}
        self.assertEqual(doppelte, set(), "Doppelte Schlüssel überschreiben sich gegenseitig")

    def test_ein_zweiter_lauf_legt_nichts_doppelt_an(self):
        nochmal = nach_sanity.dokumente_bauen(self.V, self.A)
        self.assertEqual([d["_id"] for d in self.docs], [d["_id"] for d in nochmal])


class Aktionen(unittest.TestCase):
    """Die schaltbaren Aktionen auf der Startseite."""

    def seite(self, aktionen):
        V, A = inhalte.aus_json()
        return Renderer(dict(V, aktionen=aktionen), A).pages()["index.html"]

    def basis(self, **abweichungen):
        eintrag = {"titel": "Birklauf", "aktiv": True, "kurz": "Volkslauf", "datum": "2026-08-29",
                   "datum_bis": "", "zeit": "ab 15:45 Uhr", "ort": "Birkhalle",
                   "text": "Rund um Gelting.", "anmeldelink": "",
                   "anmeldetext": "Zur Anmeldung"}
        eintrag.update(abweichungen)
        return eintrag

    def test_alle_drei_sind_eingerichtet_und_aktiv(self):
        V, _ = inhalte.aus_json()
        titel = [a["titel"] for a in V["aktionen"]]
        self.assertEqual(len(titel), 3)
        for gesucht in ("Birklauf", "Flohmarkt", "Herbstcamp"):
            self.assertTrue(any(gesucht in t for t in titel), "%s fehlt" % gesucht)
        self.assertTrue(all(a["aktiv"] for a in V["aktionen"]), "nicht alle sind aktiv")

    def test_abgeschaltete_aktion_erscheint_nicht(self):
        seite = self.seite([self.basis(aktiv=False)])
        self.assertNotIn("Birklauf", seite)

    def test_ohne_aktive_aktion_faellt_der_abschnitt_weg(self):
        self.assertNotIn('class="aktionen"', self.seite([self.basis(aktiv=False)]))
        self.assertNotIn('class="aktionen"', self.seite([]))

    def test_anmeldelink_wird_zum_knopf(self):
        seite = self.seite([self.basis(anmeldelink="https://example.org/lauf",
                                       anmeldetext="Jetzt anmelden")])
        self.assertIn('href="https://example.org/lauf"', seite)
        self.assertIn("Jetzt anmelden", seite)
        self.assertNotIn("Anmeldung folgt", seite)

    def test_ohne_link_steht_ein_hinweis(self):
        seite = self.seite([self.basis(anmeldelink="")])
        self.assertIn("Anmeldung folgt", seite)
        self.assertNotIn("<a class=\"btn btn--primary\" href=\"\"", seite)

    def test_eckdaten_werden_zusammengesetzt(self):
        seite = self.seite([self.basis()])
        self.assertIn("29. August 2026 · ab 15:45 Uhr · Birkhalle", seite)

    def test_fehlende_eckdaten_hinterlassen_keine_trennzeichen(self):
        seite = self.seite([self.basis(datum="", zeit="", ort="Birkhalle")])
        self.assertIn("Birkhalle", seite)
        self.assertNotIn("· ·", seite)
        self.assertNotIn('class="aktion__meta"> ·', seite)

    def test_status_richtet_sich_nach_dem_stand(self):
        self.assertIn("Anmeldung offen",
                      self.seite([self.basis(anmeldelink="https://example.org")]))
        self.assertIn("Termin steht",
                      self.seite([self.basis(anmeldelink="", datum="2026-08-29")]))
        self.assertIn("in Planung",
                      self.seite([self.basis(anmeldelink="", datum="", datum_bis="")]))

    def test_offene_anmeldung_wird_hervorgehoben(self):
        offen = self.seite([self.basis(anmeldelink="https://example.org")])
        zu = self.seite([self.basis(anmeldelink="")])
        self.assertIn("aktion--offen", offen)
        self.assertNotIn("aktion--offen", zu)

    def test_abschnitt_hebt_sich_dunkel_ab(self):
        seite = self.seite([self.basis()])
        self.assertIn("section--ink aktionsband", seite)

    def test_steht_vor_dem_sportangebot(self):
        seite = self.seite([self.basis()])
        self.assertLess(seite.index("aktionsband"), seite.index("Was möchtest"),
                        "Der Abschnitt muss oben stehen, sonst fällt er nicht auf")

    def test_mehrtaegige_aktion_zeigt_eine_spanne(self):
        seite = self.seite([self.basis(datum="2026-10-12", datum_bis="2026-10-16")])
        self.assertIn("12. – 16. Oktober 2026", seite)

    def test_nur_auf_der_startseite(self):
        V, A = inhalte.aus_json()
        seiten = Renderer(V, A).pages()
        for name, seite in seiten.items():
            if name != "index.html":
                self.assertNotIn('class="aktionen"', seite, name)

    def test_text_wird_maskiert(self):
        seite = self.seite([self.basis(titel="Lauf <script>alert(1)</script>")])
        self.assertNotIn("<script>alert(1)</script>", seite)


class Datumsspanne(unittest.TestCase):
    def test_faelle(self):
        from tools.render import datum_spanne
        self.assertEqual(datum_spanne("2026-10-12", "2026-10-16"), "12. – 16. Oktober 2026")
        self.assertEqual(datum_spanne("2026-09-28", "2026-10-02"),
                         "28. September – 2. Oktober 2026")
        self.assertEqual(datum_spanne("2026-12-28", "2027-01-03"),
                         "28. Dezember 2026 – 3. Januar 2027")
        self.assertEqual(datum_spanne("2026-04-18", ""), "18. April 2026")
        self.assertEqual(datum_spanne("", ""), "")

    def test_ende_vor_anfang_wird_ignoriert(self):
        from tools.render import datum_spanne
        self.assertEqual(datum_spanne("2026-04-18", "2026-04-01"), "18. April 2026")

    def test_unlesbares_datum_stuerzt_nicht_ab(self):
        from tools.render import datum_spanne
        self.assertEqual(datum_spanne("demnächst", "2026-04-01"), "demnächst")


class Abbildung(unittest.TestCase):
    """Einzelne Eigenheiten der Umsetzung von Sanity auf den Generator."""

    def umsetzen(self, roh):
        self.ordner = tempfile.TemporaryDirectory()
        self.addCleanup(self.ordner.cleanup)
        return sanity.nach_inhalten(roh, StilleMedien(self.ordner.name))

    def test_leere_antwort_ergibt_brauchbare_seiten(self):
        V, A = self.umsetzen({})
        seiten = Renderer(V, A).pages()
        self.assertEqual(sorted(seiten), sorted(SEITEN))
        self.assertIn(inhalte.STANDARD["kurzname"], seiten["index.html"])

    def test_fehlende_angabe_sperrt_suchmaschinen(self):
        V, _ = self.umsetzen({"texte": {}})
        self.assertTrue(V["suchmaschinen_sperren"])
        V, _ = self.umsetzen({"texte": {"suchmaschinenSperren": False}})
        self.assertFalse(V["suchmaschinen_sperren"])

    def test_zielgruppen_folgen_der_reihenfolge_im_cms(self):
        roh = {
            "zielgruppen": [{"id": "kinder", "name": "Kinder"},
                            {"id": "jugend", "name": "Jugend"},
                            {"id": "erwachsene", "name": "Erwachsene"}],
            "angebote": [{"slug": "x", "name": "X", "kategorie": "a",
                          "zielgruppen": ["erwachsene", "kinder"], "zeiten": []}],
        }
        _, A = self.umsetzen(roh)
        self.assertEqual(A["angebote"][0]["zielgruppen"], ["kinder", "erwachsene"])

    def test_telefonlink_wird_abgeleitet(self):
        V, _ = self.umsetzen({"verein": {"telefon": "04643 1316"}})
        self.assertEqual(V["telefon_link"], "+4946431316")

    def test_angebot_ohne_slug_bekommt_einen(self):
        _, A = self.umsetzen({"angebote": [{"name": "Eltern-Kind-Turnen", "zeiten": []}]})
        self.assertEqual(A["angebote"][0]["slug"], "eltern-kind-turnen")

    def test_aktion_ohne_angabe_gilt_als_aktiv(self):
        V, _ = self.umsetzen({"aktionen": [{"titel": "Flohmarkt"}]})
        self.assertTrue(V["aktionen"][0]["aktiv"])

    def test_abgeschaltete_aktion_kommt_als_solche_an(self):
        V, _ = self.umsetzen({"aktionen": [{"titel": "Flohmarkt", "aktiv": False}]})
        self.assertFalse(V["aktionen"][0]["aktiv"])

    def test_leere_zielgruppen_verweise_werden_verworfen(self):
        roh = {"zielgruppen": [{"id": "kinder", "name": "Kinder"}],
               "angebote": [{"slug": "x", "name": "X", "zielgruppen": [None, "kinder"],
                             "zeiten": []}]}
        _, A = self.umsetzen(roh)
        self.assertEqual(A["angebote"][0]["zielgruppen"], ["kinder"])
