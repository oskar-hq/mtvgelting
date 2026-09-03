"""Prüfungen für Datenbank, Anmeldung und Verwaltungsbereich.

    python3 -m unittest discover -s tests

Jeder Test bekommt eine frische Datenbank in einem temporären Ordner; die
Dateien des Projekts werden dabei nicht angefasst.
"""

import io
import os
import pathlib
import re
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

# Ein winziges, gültiges PNG (1 × 1 Pixel) für die Upload-Tests.
PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
                    "de0000000c4944415408d763f8cfc00000030101003c1f8f5c0000000049454e44ae426082")

EMAIL = "vorstand@example.org"
PASSWORT = "gelting-sport-2026"


class Basis(unittest.TestCase):
    """Gemeinsames Gerüst: leere Datenbank, angemeldeter Zugang."""

    anmelden_im_setup = True

    def setUp(self):
        self._ordner = tempfile.TemporaryDirectory()
        self.basis = pathlib.Path(self._ordner.name)
        self._umgebung = {k: os.environ.get(k) for k in ("MTV_DATENBANK", "MTV_UPLOADS")}
        os.environ["MTV_DATENBANK"] = str(self.basis / "verein.db")
        os.environ["MTV_UPLOADS"] = str(self.basis / "uploads")

        from app import auth, create_app
        auth._versuche.clear()
        self.export = self.basis / "export"
        self.export.mkdir()
        self.app = create_app({"TESTING": True, "EXPORT": str(self.export)})
        self.c = self.app.test_client()
        if self.anmelden_im_setup:
            self.ersten_zugang_anlegen()

    def tearDown(self):
        for k, v in self._umgebung.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._ordner.cleanup()

    # -- Hilfen ---------------------------------------------------------

    def token(self, pfad=None):
        """Das CSRF-Token der Sitzung.

        Es steht in jedem Formular; für Adressen, die nur POST beantworten,
        wird es von einer beliebigen anzeigbaren Seite geholt.
        """
        for quelle in ([pfad] if pfad else []) + ["/admin/", "/admin/login",
                                                  "/admin/einrichten"]:
            antwort = self.c.get(quelle)
            if antwort.status_code != 200:
                continue
            treffer = re.search(r'name="csrf" value="([^"]+)"',
                                antwort.get_data(as_text=True))
            if treffer:
                return treffer.group(1)
        self.fail("Kein CSRF-Token zu finden (Ausgangspunkt %s)" % pfad)

    def ersten_zugang_anlegen(self):
        antwort = self.c.post("/admin/einrichten", data={
            "csrf": self.token(), "email": EMAIL, "name": "Test",
            "passwort": PASSWORT, "passwort2": PASSWORT})
        self.assertEqual(antwort.status_code, 302)

    def sende(self, pfad, daten, erwartet=302, **kwargs):
        daten = dict(daten, csrf=self.token())
        antwort = self.c.post(pfad, data=daten, **kwargs)
        self.assertEqual(antwort.status_code, erwartet,
                         antwort.get_data(as_text=True)[:800])
        return antwort

    def seite(self, pfad):
        antwort = self.c.get(pfad)
        self.assertEqual(antwort.status_code, 200, pfad)
        return antwort.get_data(as_text=True)

    def ids(self, pfad, muster):
        return re.findall(muster, self.c.get(pfad).get_data(as_text=True))


class OeffentlicheSeiten(Basis):
    anmelden_im_setup = False

    def test_alle_seiten_werden_ausgeliefert(self):
        for pfad in ["/", "/index.html", "/sportangebot.html", "/termine.html", "/verein.html",
                     "/mitglied-werden.html", "/impressum.html", "/datenschutz.html"]:
            self.assertEqual(self.c.get(pfad).status_code, 200, pfad)

    def test_unbekannte_seite_ergibt_404(self):
        self.assertEqual(self.c.get("/gibtsnicht.html").status_code, 404)

    def test_daten_aus_data_werden_uebernommen(self):
        self.assertIn("MTV Gelting 08", self.seite("/"))
        self.assertIn("Wochenplan", self.seite("/termine.html"))


class Anmeldung(Basis):
    anmelden_im_setup = False

    def test_verwaltung_ist_ohne_anmeldung_gesperrt(self):
        for pfad in ["/admin/", "/admin/angebote/", "/admin/stammdaten",
                     "/admin/inhalt/termine/", "/admin/benutzer/"]:
            self.assertEqual(self.c.get(pfad).status_code, 302, pfad)

    def test_ersteinrichtung_und_anmeldung(self):
        self.assertEqual(self.c.get("/admin/login").status_code, 302)
        self.ersten_zugang_anlegen()
        self.assertEqual(self.c.get("/admin/").status_code, 200)
        self.sende("/admin/logout", {})
        self.assertEqual(self.c.get("/admin/").status_code, 302)
        self.sende("/admin/login", {"email": EMAIL, "passwort": PASSWORT})
        self.assertEqual(self.c.get("/admin/").status_code, 200)

    def test_zu_kurzes_passwort_wird_abgelehnt(self):
        antwort = self.c.post("/admin/einrichten", data={
            "csrf": self.token(), "email": EMAIL, "name": "Test",
            "passwort": "kurz", "passwort2": "kurz"})
        self.assertIn("mindestens 10 Zeichen", antwort.get_data(as_text=True))
        self.assertEqual(self.c.get("/admin/").status_code, 302, "Zugang trotzdem angelegt")

    def test_falsches_passwort_meldet_nicht_ob_die_adresse_existiert(self):
        self.ersten_zugang_anlegen()
        self.sende("/admin/logout", {})
        antwort = self.sende("/admin/login", {"email": EMAIL, "passwort": "falsch-falsch"},
                             erwartet=401)
        text = antwort.get_data(as_text=True)
        self.assertIn("E-Mail-Adresse oder Passwort stimmt nicht", text)

    def test_fehlversuche_werden_gebremst(self):
        self.ersten_zugang_anlegen()
        self.sende("/admin/logout", {})
        for i in range(5):
            antwort = self.sende("/admin/login", {"email": EMAIL, "passwort": "falsch-%d" % i},
                                 erwartet=401)
        antwort = self.sende("/admin/login", {"email": EMAIL, "passwort": PASSWORT}, erwartet=429)
        self.assertIn("Zu viele Fehlversuche", antwort.get_data(as_text=True))


class Formularschutz(Basis):
    def test_ohne_token_wird_nichts_gespeichert(self):
        self.c.post("/admin/inhalt/termine/neu", data={"titel": "Schmuggel"})
        self.assertNotIn("Schmuggel", self.seite("/termine.html"))

    def test_falsches_token_wird_abgewiesen(self):
        self.c.post("/admin/inhalt/termine/neu", data={"csrf": "unsinn", "titel": "Schmuggel"})
        self.assertNotIn("Schmuggel", self.seite("/termine.html"))


class Termine(Basis):
    def test_anlegen_aendern_loeschen(self):
        self.sende("/admin/inhalt/termine/neu", {
            "titel": "Sommerfest", "datum": "2026-07-11", "zeit": "ab 14 Uhr",
            "ort": "Birkhalle", "text": "Mit Kaffee und Kuchen."})
        self.assertIn("Sommerfest", self.seite("/termine.html"))

        eid = self.ids("/admin/inhalt/termine/", r"/admin/inhalt/termine/(\d+)\b")[-1]
        formular = self.seite("/admin/inhalt/termine/%s" % eid)
        self.assertIn('value="Sommerfest"', formular)
        self.assertIn('value="2026-07-11"', formular)

        self.sende("/admin/inhalt/termine/%s" % eid, {
            "titel": "Herbstfest", "datum": "2026-10-03", "zeit": "", "ort": "Sportplatz",
            "text": "Neu."})
        seite = self.seite("/termine.html")
        self.assertIn("Herbstfest", seite)
        self.assertNotIn("Sommerfest", seite)

        self.sende("/admin/inhalt/termine/%s/loeschen" % eid, {})
        self.assertNotIn("Herbstfest", self.seite("/termine.html"))

    def test_pflichtfeld_wird_verlangt(self):
        antwort = self.sende("/admin/inhalt/termine/neu",
                             {"titel": "", "datum": "", "zeit": "", "ort": "", "text": ""},
                             erwartet=200)
        self.assertIn("darf nicht leer sein", antwort.get_data(as_text=True))

    def test_termin_ohne_datum_bleibt_zulaessig(self):
        self.sende("/admin/inhalt/termine/neu", {
            "titel": "Vereinsbus", "datum": "", "zeit": "nach Absprache", "ort": "",
            "text": "Ausleihe über die Geschäftsstelle."})
        self.assertIn("nach Absprache", self.seite("/termine.html"))


class Sportangebote(Basis):
    def erstes_angebot(self):
        return self.ids("/admin/angebote/", r'href="/admin/angebote/(\d+)"')[0]

    def test_formular_zeigt_gespeicherte_werte(self):
        formular = self.seite("/admin/angebote/%s" % self.erstes_angebot())
        self.assertRegex(formular, r'id="name"[^>]*value="[^"]+"')
        self.assertIn("selected", formular)
        self.assertIn("checked", formular)

    def test_zeiten_kontakt_und_wochenplan(self):
        from werkzeug.datastructures import MultiDict
        eid = self.erstes_angebot()
        daten = MultiDict([
            ("csrf", self.token()),
            ("name", "Fußball"), ("kategorie", "ballsport"),
            ("zielgruppen", "kinder"), ("zielgruppen", "jugend"),
            ("kurz", "Kurz."), ("text", "Erster Absatz.\n\nZweiter Absatz."),
            ("ort", "Sportplatz"), ("leitung", "Bernd Kratz"),
            ("kontakt_email", "fussball@example.org"), ("kontakt_telefon", "04643 1316"),
            # gefüllte Zeile
            ("zeit_tag", "Montag"), ("zeit_von", "17:00"), ("zeit_bis", "18:30"),
            ("zeit_gruppe", "E-Jugend"), ("zeit_ort", ""), ("zeit_leitung", "B. Surm"),
            ("zeit_hinweis", ""),
            # offenes Ende
            ("zeit_tag", "Freitag"), ("zeit_von", "18:00"), ("zeit_bis", ""),
            ("zeit_gruppe", ""), ("zeit_ort", ""), ("zeit_leitung", ""), ("zeit_hinweis", ""),
            # leere Zeile – muss verworfen werden
            ("zeit_tag", "Montag"), ("zeit_von", ""), ("zeit_bis", ""),
            ("zeit_gruppe", ""), ("zeit_ort", ""), ("zeit_leitung", ""), ("zeit_hinweis", ""),
        ])
        self.assertEqual(self.c.post("/admin/angebote/%s" % eid, data=daten).status_code, 302)

        angebote = self.seite("/sportangebot.html")
        self.assertIn("Bernd Kratz", angebote)
        self.assertIn("fussball@example.org", angebote)
        self.assertIn("Zweiter Absatz.", angebote)

        plan = self.seite("/termine.html")
        self.assertIn("B. Surm", plan)
        self.assertIn("ab 18:00", plan)

        formular = self.seite("/admin/angebote/%s" % eid)
        self.assertEqual(formular.count('name="zeit_tag"'), 3)  # 2 Zeilen + Vorlage

    def test_neues_angebot_und_loeschen(self):
        self.sende("/admin/angebote/neu", {
            "name": "Bogenschießen", "kategorie": "freizeit", "zielgruppen": "erwachsene",
            "kurz": "Auf die Scheibe.", "text": "", "ort": "Sportplatz", "leitung": "",
            "kontakt_email": "", "kontakt_telefon": ""})
        self.assertIn("Bogenschießen", self.seite("/sportangebot.html"))
        self.assertIn('id="bogenschiessen"', self.seite("/sportangebot.html"))

        eid = self.ids("/admin/angebote/", r'href="/admin/angebote/(\d+)"')[-1]
        self.sende("/admin/angebote/%s/loeschen" % eid, {})
        self.assertNotIn("Bogenschießen", self.seite("/sportangebot.html"))

    def test_bereich_ist_pflicht(self):
        antwort = self.sende("/admin/angebote/neu", {
            "name": "Ohne Bereich", "kategorie": "", "kurz": "", "text": "", "ort": "",
            "leitung": "", "kontakt_email": "", "kontakt_telefon": ""}, erwartet=200)
        self.assertIn("Bereich auswählen", antwort.get_data(as_text=True))


class Sponsoren(Basis):
    def test_logo_hochladen_ersetzen_entfernen(self):
        self.sende("/admin/inhalt/sponsoren/neu",
                   {"name": "Muster GmbH", "url": "https://example.org",
                    "logo": (io.BytesIO(PNG), "muster logo.png")},
                   content_type="multipart/form-data")
        start = self.seite("/")
        pfad = re.search(r'src="(uploads/logos/[^"]+)"', start)
        self.assertIsNotNone(pfad, "Logo fehlt im Sponsorenraster")
        self.assertEqual(self.c.get("/" + pfad.group(1)).status_code, 200)
        self.assertTrue((self.basis / pfad.group(1)).exists())

        eid = self.ids("/admin/inhalt/sponsoren/", r'href="/admin/inhalt/sponsoren/(\d+)"')[-1]
        self.sende("/admin/inhalt/sponsoren/%s" % eid,
                   {"name": "Muster GmbH", "url": "",
                    "logo": (io.BytesIO(PNG), "anderes.png")},
                   content_type="multipart/form-data")
        self.assertFalse((self.basis / pfad.group(1)).exists(),
                         "Das ersetzte Logo wurde nicht aufgeräumt")

        neu = re.search(r'src="(uploads/logos/[^"]+)"', self.seite("/")).group(1)
        self.sende("/admin/inhalt/sponsoren/%s" % eid,
                   {"name": "Muster GmbH", "url": "", "logo_entfernen": "1"})
        self.assertFalse((self.basis / neu).exists())

    def test_nur_bildformate(self):
        antwort = self.sende("/admin/inhalt/sponsoren/neu",
                             {"name": "Böse", "url": "",
                              "logo": (io.BytesIO(b"<svg onload=alert(1)/>"), "x.svg")},
                             erwartet=200, content_type="multipart/form-data")
        self.assertIn("nicht erlaubt", antwort.get_data(as_text=True))

    def test_raster_kennt_die_anzahl(self):
        vorher = int(re.search(r'data-anzahl="(\d+)"', self.seite("/")).group(1))
        self.sende("/admin/inhalt/sponsoren/neu", {"name": "Noch einer", "url": "", "logo": ""})
        nachher = int(re.search(r'data-anzahl="(\d+)"', self.seite("/")).group(1))
        self.assertEqual(nachher, vorher + 1)


class Dokumente(Basis):
    def test_satzung_austauschen(self):
        eid = self.ids("/admin/inhalt/dokumente/", r'href="/admin/inhalt/dokumente/(\d+)"')[0]
        self.sende("/admin/inhalt/dokumente/%s" % eid,
                   {"bereich": "satzung", "titel": "Satzung", "beschreibung": "Fassung 2026",
                    "url": "", "datei": (io.BytesIO(b"%PDF-1.4 test"), "satzung.pdf")},
                   content_type="multipart/form-data")
        verein = self.seite("/verein.html")
        self.assertIn("Fassung 2026", verein)
        pfad = re.search(r'href="(uploads/dokumente/[^"]+)"', verein)
        self.assertIsNotNone(pfad)
        self.assertEqual(self.c.get("/" + pfad.group(1)).status_code, 200)

    def test_sprachrohr_erscheint_als_liste(self):
        self.sende("/admin/inhalt/dokumente/neu",
                   {"bereich": "sprachrohr", "titel": "Sprachrohr 2026", "beschreibung": "",
                    "url": "", "datei": (io.BytesIO(b"%PDF-1.4"), "sprachrohr.pdf")},
                   content_type="multipart/form-data")
        self.assertIn("Sprachrohr 2026", self.seite("/verein.html"))

    def test_nur_pdf(self):
        antwort = self.sende("/admin/inhalt/dokumente/neu",
                             {"bereich": "satzung", "titel": "X", "beschreibung": "", "url": "",
                              "datei": (io.BytesIO(PNG), "bild.png")},
                             erwartet=200, content_type="multipart/form-data")
        self.assertIn("nicht erlaubt", antwort.get_data(as_text=True))


class Stammdaten(Basis):
    def test_anschrift_wirkt_auf_allen_seiten(self):
        self.sende("/admin/stammdaten", {
            "name": "Männer-Turn-Verein Gelting von 1908 e.V.", "kurzname": "MTV Gelting 08",
            "gegruendet": "1908", "claim": "Sport in Gelting.", "strasse": "Neue Straße 5",
            "plz": "24395", "ort": "Gelting", "telefon": "04643 1316", "telefon_link": "",
            "telefax": "", "email": "neu@example.org", "register": "VR 1033 FL",
            "oeffnungszeiten": "Dienstag 9–12 Uhr", "facebook": "", "instagram": "", "shop": ""})
        self.assertIn("Neue Straße 5", self.seite("/"))
        self.assertIn("Dienstag 9–12 Uhr", self.seite("/verein.html"))
        self.assertIn("neu@example.org", self.seite("/impressum.html"))

    def test_telefonlink_wird_abgeleitet(self):
        self.sende("/admin/stammdaten", {
            "name": "Verein", "kurzname": "Verein", "gegruendet": "1908", "claim": "",
            "strasse": "", "plz": "", "ort": "", "telefon": "04643 1316", "telefon_link": "",
            "telefax": "", "email": "a@b.de", "register": "", "oeffnungszeiten": "",
            "facebook": "", "instagram": "", "shop": ""})
        self.assertIn('href="tel:+4946431316"', self.seite("/"))

    def test_email_ist_pflicht(self):
        antwort = self.sende("/admin/stammdaten", {
            "name": "Verein", "kurzname": "Verein", "gegruendet": "", "claim": "", "strasse": "",
            "plz": "", "ort": "", "telefon": "", "telefon_link": "", "telefax": "", "email": "",
            "register": "", "oeffnungszeiten": "", "facebook": "", "instagram": "", "shop": ""},
            erwartet=200)
        self.assertIn("darf nicht leer sein", antwort.get_data(as_text=True))


class Beitraege(Basis):
    def test_ueberschrift_folgt_den_aktiven_beitraegen(self):
        self.assertIn("Ab 7 € im Monat", self.seite("/"))
        eid = self.ids("/admin/inhalt/beitraege/", r'href="/admin/inhalt/beitraege/(\d+)"')[0]
        self.sende("/admin/inhalt/beitraege/%s" % eid, {
            "gruppe": "Kinder & Jugendliche", "kurz": "Kinder", "monat": "8,00 €",
            "jahr": "96,00 €", "aktiv": "1"})
        self.assertIn("Ab 8 € im Monat", self.seite("/"))

    def test_passiver_beitrag_bestimmt_die_ueberschrift_nicht(self):
        self.sende("/admin/inhalt/beitraege/neu", {
            "gruppe": "Fördermitglied", "kurz": "Förderer", "monat": "2,00 €", "jahr": "24,00 €"})
        self.assertIn("Fördermitglied", self.seite("/mitglied-werden.html"))
        self.assertNotIn("Ab 2 € im Monat", self.seite("/"))

    def test_haken_laesst_sich_setzen_und_entfernen(self):
        eid = self.ids("/admin/inhalt/beitraege/", r'href="/admin/inhalt/beitraege/(\d+)"')[0]
        self.assertIn('value="1" checked', self.seite("/admin/inhalt/beitraege/%s" % eid))
        self.sende("/admin/inhalt/beitraege/%s" % eid,
                   {"gruppe": "Kinder", "kurz": "", "monat": "7,00 €", "jahr": ""})
        self.assertNotIn('value="1" checked', self.seite("/admin/inhalt/beitraege/%s" % eid))


class Texte(Basis):
    def alle_texte(self, **abweichungen):
        werte = {"start_titel": "Sport für alle.", "start_titel_akzent": "In Gelting.",
                 "start_seitentitel": "Sport für alle in Gelting", "beitrag_hinweis": "",
                 "sprachrohr_text": "", "jugendschutz_text": "", "quelle": "",
                 "hinweisbanner": "", "admin_url": "/admin/", "datenschutz_text": "",
                 "datenschutz_hinweis": "", "impressum_hinweis": ""}
        werte.update(abweichungen)
        return werte

    def test_hinweisstreifen_und_suchmaschinen(self):
        self.assertIn("demo-bar", self.seite("/"))
        self.assertIn('content="noindex, nofollow"', self.seite("/"))
        self.sende("/admin/texte", self.alle_texte())
        self.assertNotIn("demo-bar", self.seite("/"))
        self.assertIn('content="index, follow"', self.seite("/"))

    def test_jugendschutztext_erscheint(self):
        self.sende("/admin/texte", self.alle_texte(
            jugendschutz_text="Ansprechperson: Ilse Meier.\n\nZweiter Absatz."))
        verein = self.seite("/verein.html")
        self.assertIn("Ansprechperson: Ilse Meier.", verein)
        self.assertIn("Zweiter Absatz.", verein)

    def test_anmeldelink_laesst_sich_ausblenden(self):
        self.assertIn("ftr__admin", self.seite("/"))
        self.sende("/admin/texte", self.alle_texte(admin_url=""))
        self.assertNotIn("ftr__admin", self.seite("/"))


class BereicheUndZielgruppen(Basis):
    def test_anlegen_und_loeschen(self):
        self.sende("/admin/ordnung/kategorien/", {"name": "Wassersport"})
        self.assertIn("Wassersport", self.seite("/"))
        self.sende("/admin/ordnung/kategorien/wassersport/loeschen", {})
        self.assertNotIn("Wassersport", self.seite("/"))

    def test_benutzter_bereich_bleibt_geschuetzt(self):
        antwort = self.sende("/admin/ordnung/kategorien/ballsport/loeschen", {})
        self.assertIn("ballsport", str(self.c.get("/sportangebot.html").get_data(as_text=True)))
        self.assertIn("kann nicht gelöscht werden",
                      self.c.get("/admin/ordnung/kategorien/").get_data(as_text=True))

    def test_umbenennen(self):
        self.sende("/admin/ordnung/kategorien/ballsport/umbenennen", {"name": "Mannschaftssport"})
        self.assertIn("Mannschaftssport", self.seite("/sportangebot.html"))


class Reihenfolge(Basis):
    def test_vorstand_laesst_sich_sortieren(self):
        vorher = self.seite("/verein.html")
        ids = self.ids("/admin/inhalt/vorstand/", r"/admin/inhalt/vorstand/(\d+)/verschieben")
        self.sende("/admin/inhalt/vorstand/%s/verschieben" % ids[1], {"richtung": "hoch"})
        self.assertNotEqual(vorher, self.seite("/verein.html"))


class Zugaenge(Basis):
    def test_weiteren_zugang_anlegen_und_loeschen(self):
        self.sende("/admin/benutzer/", {"name": "Zweite", "email": "zwei@example.org",
                                        "passwort": "noch-ein-langes-wort"})
        self.assertIn("zwei@example.org", self.seite("/admin/benutzer/"))
        eid = re.search(r'/admin/benutzer/(\d+)/loeschen',
                        self.seite("/admin/benutzer/")).group(1)
        self.sende("/admin/benutzer/%s/loeschen" % eid, {})

    def test_eigener_zugang_ist_nicht_loeschbar(self):
        eid = re.search(r'/admin/benutzer/(\d+)/loeschen',
                        self.seite("/admin/benutzer/")).group(1)
        self.sende("/admin/benutzer/%s/loeschen" % eid, {})
        self.assertIn(EMAIL, self.seite("/admin/benutzer/"))

    def test_passwort_aendern(self):
        antwort = self.sende("/admin/passwort", {"alt": "falsch", "neu": "ein-neues-passwort",
                                                 "neu2": "ein-neues-passwort"}, erwartet=200)
        self.assertIn("stimmt nicht", antwort.get_data(as_text=True))
        self.sende("/admin/passwort", {"alt": PASSWORT, "neu": "ein-neues-passwort",
                                       "neu2": "ein-neues-passwort"})
        self.sende("/admin/logout", {})
        self.sende("/admin/login", {"email": EMAIL, "passwort": "ein-neues-passwort"})
        self.assertEqual(self.c.get("/admin/").status_code, 200)


class StatischerExport(Basis):
    def test_sieben_seiten_mit_aktuellem_inhalt(self):
        self.sende("/admin/inhalt/termine/neu", {
            "titel": "Exportprobe", "datum": "2026-05-01", "zeit": "", "ort": "", "text": ""})
        self.sende("/admin/veroeffentlichen", {})
        erzeugt = sorted(p.name for p in self.export.glob("*.html"))
        self.assertEqual(len(erzeugt), 7, erzeugt)
        self.assertIn("Exportprobe",
                      (self.export / "termine.html").read_text(encoding="utf-8"))
        self.assertTrue((self.export / "data" / "verein.json").exists())
        self.assertIn("Exportprobe",
                      (self.export / "data" / "verein.json").read_text(encoding="utf-8"))

    def test_export_fasst_die_projektdateien_nicht_an(self):
        projekt = pathlib.Path(__file__).resolve().parent.parent
        vorher = (projekt / "data" / "verein.json").read_text(encoding="utf-8")
        self.sende("/admin/inhalt/termine/neu", {
            "titel": "Darf nicht ins Projekt", "datum": "2026-05-01", "zeit": "", "ort": "",
            "text": ""})
        self.sende("/admin/veroeffentlichen", {})
        self.assertEqual(vorher, (projekt / "data" / "verein.json").read_text(encoding="utf-8"))


class Passwoerter(unittest.TestCase):
    def test_hash_und_pruefung(self):
        from app.auth import hash_passwort, pruefe_passwort
        h = hash_passwort("ein-langes-passwort")
        self.assertTrue(pruefe_passwort(h, "ein-langes-passwort"))
        self.assertFalse(pruefe_passwort(h, "ein-langes-passwort "))
        self.assertFalse(pruefe_passwort(h, ""))
        self.assertNotEqual(h, hash_passwort("ein-langes-passwort"), "Salz fehlt")

    def test_kaputter_hash_stuerzt_nicht_ab(self):
        from app.auth import pruefe_passwort
        for kaputt in ["", "unsinn", "scrypt$a$b$c$d$e", "md5$1$1$1$aa$bb"]:
            self.assertFalse(pruefe_passwort(kaputt, "irgendwas"))


class DatenUndRenderer(unittest.TestCase):
    """Der Weg data/*.json -> Renderer muss auch ohne Datenbank funktionieren."""

    def test_bauen_aus_json(self):
        from app.db import aus_json
        from app.render import SEITEN, Renderer
        V, A = aus_json()
        seiten = Renderer(V, A).pages()
        self.assertEqual(sorted(seiten), sorted(SEITEN))
        for name, inhalt in seiten.items():
            self.assertTrue(inhalt.startswith("<!doctype html>"), name)
            self.assertIn("</html>", inhalt)

    def test_datenbank_und_json_ergeben_dasselbe(self):
        import tempfile as tf
        from app import db
        from app.render import Renderer
        with tf.TemporaryDirectory() as ordner:
            conn = db.verbinde(pathlib.Path(ordner) / "p.db")
            db.anlegen(conn)
            db.befuellen(conn)
            aus_db = Renderer(*db.lade_daten(conn)).pages()
            conn.close()
        aus_dateien = Renderer(*db.aus_json()).pages()
        for name in aus_dateien:
            self.assertEqual(aus_dateien[name], aus_db[name],
                             "%s unterscheidet sich zwischen data/ und Datenbank" % name)


if __name__ == "__main__":
    unittest.main()
