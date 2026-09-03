"""Verwaltungsbereich: hier pflegt der Verein alle Inhalte der Website.

Die meisten Bereiche sind gleich aufgebaut — eine Liste mit Eintraegen und ein
Formular je Eintrag. Deshalb sind sie hier als Datensaetze beschrieben
(``BEREICHE``) und werden von denselben Ansichten und Vorlagen bedient.
Nur die Sportangebote haben ein eigenes Formular, weil dort Zielgruppen und
Trainingszeiten mit im Spiel sind.
"""

import pathlib
import re
import secrets
import unicodedata

from flask import (Blueprint, abort, current_app, flash, g, redirect,
                   render_template, request, url_for)
from werkzeug.utils import secure_filename

from . import db as datenbank
from .auth import (anzahl_benutzer, benutzer_anlegen, benutzer_nach_email,
                   csrf_pruefen, csrf_token, gewuenschtes_ziel, hash_passwort,
                   passwort_pruefregel, pruefe_passwort)
from .render import WOCHENTAGE

bp = Blueprint("admin", __name__)

BILD_ENDUNGEN = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
PDF_ENDUNGEN = {".pdf"}


class Feld:
    """Ein Eingabefeld im Formular."""

    def __init__(self, name, label, typ="text", hinweis="", pflicht=False,
                 optionen=None, ordner="", endungen=None, platzhalter=""):
        self.name = name
        self.label = label
        self.typ = typ
        self.hinweis = hinweis
        self.pflicht = pflicht
        self.optionen = optionen or []
        self.ordner = ordner
        self.endungen = endungen or BILD_ENDUNGEN
        self.platzhalter = platzhalter


class Bereich:
    """Eine Inhaltsart mit Liste und Formular."""

    def __init__(self, schluessel, tabelle, titel, einzahl, felder, spalten,
                 beschreibung="", sortierbar=True, reihenfolge="sortierung, id",
                 leer=""):
        self.schluessel = schluessel
        self.tabelle = tabelle
        self.titel = titel
        self.einzahl = einzahl
        self.felder = felder
        self.spalten = spalten
        self.beschreibung = beschreibung
        self.sortierbar = sortierbar
        self.reihenfolge = reihenfolge
        self.leer = leer or ("Noch keine Einträge. Lege den ersten %s an." % einzahl)


BEREICHE = {}


def _bereich(b):
    BEREICHE[b.schluessel] = b
    return b


_bereich(Bereich(
    "termine", "termine", "Termine", "Termin",
    beschreibung="Feste Termine im Vereinsjahr — Turniere, Versammlungen, Feste. "
                 "Sie stehen oben auf der Termineseite.",
    spalten=[("datum", "Datum"), ("titel", "Titel"), ("ort", "Ort")],
    felder=[
        Feld("titel", "Titel", pflicht=True, platzhalter="26. Birklauf"),
        Feld("datum", "Datum", typ="datum",
             hinweis="Leer lassen, wenn der Termin kein festes Datum hat "
                     "(zum Beispiel „jeden ersten Sonntag“)."),
        Feld("zeit", "Uhrzeit", platzhalter="ab 15:45 Uhr",
             hinweis="Freier Text. Ohne Datum steht dieser Text anstelle des Datums."),
        Feld("ort", "Ort", platzhalter="Birkhalle Gelting"),
        Feld("text", "Beschreibung", typ="textarea"),
    ]))

_bereich(Bereich(
    "news", "news", "Aktuelles", "Meldung",
    beschreibung="Kurze Meldungen aus dem Verein. Die vier neuesten erscheinen auf der Startseite.",
    spalten=[("datum", "Datum"), ("titel", "Titel"), ("kategorie", "Kategorie")],
    sortierbar=False, reihenfolge="datum DESC, id DESC",
    felder=[
        Feld("titel", "Überschrift", pflicht=True),
        Feld("datum", "Datum", typ="datum", pflicht=True),
        Feld("kategorie", "Kategorie", platzhalter="Verein"),
        Feld("text", "Text", typ="textarea", pflicht=True),
    ]))

_bereich(Bereich(
    "vorstand", "vorstand", "Vorstand", "Person",
    beschreibung="Der Vorstand erscheint auf der Vereinsseite. Wer den Verein nach § 26 BGB "
                 "vertritt, wird zusätzlich im Impressum genannt.",
    spalten=[("name", "Name"), ("rolle", "Funktion"), ("paragraf26", "§ 26 BGB")],
    felder=[
        Feld("name", "Name", pflicht=True),
        Feld("rolle", "Funktion", platzhalter="1. Vorsitzender"),
        Feld("email", "E-Mail", typ="email",
             hinweis="Erscheint als Link auf der Vereinsseite. Leer lassen, wenn nicht gewünscht."),
        Feld("paragraf26", "Vertritt den Verein nach § 26 BGB", typ="checkbox",
             hinweis="Diese Personen stehen im Impressum unter „Vertreten durch“."),
    ]))

_bereich(Bereich(
    "beitraege", "beitraege", "Beiträge", "Beitrag",
    beschreibung="Die Mitgliedsbeiträge. Sie stehen auf „Mitglied werden“ und bestimmen "
                 "den Preis, der auf der Startseite genannt wird.",
    spalten=[("gruppe", "Gruppe"), ("monat", "je Monat"), ("jahr", "je Jahr")],
    felder=[
        Feld("gruppe", "Gruppe", pflicht=True,
             platzhalter="Kinder & Jugendliche bis 18 Jahre"),
        Feld("kurz", "Kurzbezeichnung", platzhalter="Kinder und Jugendliche",
             hinweis="Wird auf der Startseite verwendet, wo wenig Platz ist."),
        Feld("monat", "Beitrag je Monat", platzhalter="7,00 €", pflicht=True),
        Feld("jahr", "Beitrag je Jahr", platzhalter="84,00 €"),
        Feld("aktiv", "Aktive Mitgliedschaft", typ="checkbox",
             hinweis="Nur aktive Mitgliedschaften zählen für den Satz „ab … € im Monat“ "
                     "auf der Startseite. Bei passiven Beiträgen abwählen."),
    ]))

_bereich(Bereich(
    "sponsoren", "sponsoren", "Sponsoren", "Sponsor",
    beschreibung="Logo und Name der Förderer. Das Raster auf der Startseite richtet sich "
                 "automatisch nach der Anzahl — je mehr Einträge, desto mehr Zeilen.",
    spalten=[("logo", "Logo"), ("name", "Name"), ("url", "Website")],
    felder=[
        Feld("name", "Name", pflicht=True),
        Feld("logo", "Logo", typ="datei", ordner="logos", endungen=BILD_ENDUNGEN,
             hinweis="PNG, JPG, WEBP oder GIF. Ohne Logo erscheint der Name als Text."),
        Feld("url", "Website", typ="url", platzhalter="https://…",
             hinweis="Optional. Das Logo wird dann verlinkt."),
    ]))

_bereich(Bereich(
    "spielplaene", "spielplaene", "Spielpläne", "Spielplan",
    beschreibung="Verweise auf die Ansetzungen der Verbände, unten auf der Termineseite.",
    spalten=[("name", "Sportart"), ("quelle", "Verband"), ("url", "Link")],
    felder=[
        Feld("name", "Sportart", pflicht=True),
        Feld("quelle", "Verband", platzhalter="Handballverband Schleswig-Holstein"),
        Feld("url", "Link", typ="url", platzhalter="https://…",
             hinweis="Ohne Link wird nur der Verband genannt."),
    ]))

_bereich(Bereich(
    "dokumente", "dokumente", "Dokumente", "Dokument",
    beschreibung="Satzung, Ordnungen, Aufnahmeantrag und die Ausgaben des Sprachrohrs. "
                 "Der Bereich bestimmt, wo das Dokument auf der Website erscheint.",
    spalten=[("bereich", "Bereich"), ("titel", "Titel"), ("datei", "Datei")],
    reihenfolge="bereich, sortierung, id",
    felder=[
        Feld("bereich", "Bereich", typ="auswahl", pflicht=True,
             optionen=[("satzung", "Satzungen & Ordnungen (Vereinsseite)"),
                       ("sprachrohr", "Sprachrohr (Vereinsseite)"),
                       ("antrag", "Aufnahmeantrag (Mitglied werden)")]),
        Feld("titel", "Titel", pflicht=True, platzhalter="Satzung"),
        Feld("datei", "PDF", typ="datei", ordner="dokumente", endungen=PDF_ENDUNGEN,
             hinweis="Nur PDF-Dateien, höchstens 16 MB."),
        Feld("url", "Alternativer Link", typ="url",
             hinweis="Falls das Dokument woanders liegt statt hochgeladen zu werden."),
        Feld("beschreibung", "Beschreibung",
             hinweis="Beschriftung des Links. Ohne Datei erscheint dieser Text als Hinweis."),
    ]))


# ---------------------------------------------------------------------------
# Hilfen
# ---------------------------------------------------------------------------

def conn():
    return current_app.datenbank()


def geaendert():
    """Nach jeder Aenderung merken, damit die Seiten neu gebaut werden."""
    datenbank.markiere_aenderung(conn())
    conn().commit()


def slug(text):
    """'Eltern-Kind-Turnen' -> 'eltern-kind-turnen'."""
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "eintrag"


def freier_slug(text, ausser=None):
    basis = slug(text)
    kandidat = basis
    n = 2
    while True:
        zeile = conn().execute("SELECT id FROM angebote WHERE slug = ?", (kandidat,)).fetchone()
        if zeile is None or zeile["id"] == ausser:
            return kandidat
        kandidat = "%s-%d" % (basis, n)
        n += 1


def speichere_datei(hochgeladen, ordner, endungen):
    """Datei ablegen und den Pfad zurueckgeben, wie ihn die Seiten brauchen."""
    name = secure_filename(hochgeladen.filename or "")
    endung = pathlib.Path(name).suffix.lower()
    if endung not in endungen:
        raise ValueError("Dieses Dateiformat ist nicht erlaubt. Erlaubt sind: %s."
                         % ", ".join(sorted(e.lstrip(".") for e in endungen)))
    stamm = pathlib.Path(name).stem[:60] or "datei"
    ziel_name = "%s-%s%s" % (stamm, secrets.token_hex(4), endung)
    ziel = pathlib.Path(current_app.config["UPLOADS"], ordner)
    ziel.mkdir(parents=True, exist_ok=True)
    hochgeladen.save(str(ziel / ziel_name))
    return "uploads/%s/%s" % (ordner, ziel_name)


def loesche_datei(pfad):
    """Eine frueher hochgeladene Datei entfernen — nur innerhalb des Upload-Ordners."""
    if not pfad or not pfad.startswith("uploads/"):
        return
    wurzel = pathlib.Path(current_app.config["UPLOADS"]).resolve()
    datei = (wurzel / pfad[len("uploads/"):]).resolve()
    if wurzel in datei.parents and datei.is_file():
        try:
            datei.unlink()
        except OSError:
            current_app.logger.warning("Datei ließ sich nicht löschen: %s", datei)


def naechste_sortierung(tabelle):
    zeile = conn().execute("SELECT COALESCE(MAX(sortierung), -1) + 1 AS n FROM %s" % tabelle).fetchone()
    return zeile["n"]


def werte_einlesen(bereich, alt=None):
    """Formular auswerten. Gibt (Werte, Fehler) zurueck."""
    werte = {}
    fehler = []
    for feld in bereich.felder:
        if feld.typ == "checkbox":
            werte[feld.name] = 1 if request.form.get(feld.name) else 0
            continue
        if feld.typ == "datei":
            bisher = (alt[feld.name] if alt is not None else "") or ""
            hochgeladen = request.files.get(feld.name)
            if request.form.get(feld.name + "_entfernen"):
                loesche_datei(bisher)
                werte[feld.name] = ""
            elif hochgeladen and hochgeladen.filename:
                try:
                    werte[feld.name] = speichere_datei(hochgeladen, feld.ordner, feld.endungen)
                except ValueError as f:
                    fehler.append("%s: %s" % (feld.label, f))
                    werte[feld.name] = bisher
                else:
                    loesche_datei(bisher)
            else:
                werte[feld.name] = bisher
            continue
        wert = (request.form.get(feld.name) or "").strip()
        if feld.pflicht and not wert:
            fehler.append("%s darf nicht leer sein." % feld.label)
        if feld.typ == "auswahl" and wert and wert not in [o[0] for o in feld.optionen]:
            fehler.append("%s: unbekannte Auswahl." % feld.label)
        if feld.typ == "datum" and wert and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", wert):
            fehler.append("%s: bitte ein Datum auswählen." % feld.label)
        if feld.typ == "email" and wert and "@" not in wert:
            fehler.append("%s: das sieht nicht nach einer E-Mail-Adresse aus." % feld.label)
        werte[feld.name] = wert
    return werte, fehler


def hole(tabelle, eintrag_id):
    """Einen Datensatz als gewoehnliches dict laden.

    Bewusst kein ``sqlite3.Row``: dessen ``in``-Pruefung sieht die Werte statt
    der Spaltennamen, wodurch die Vorlagen leere Felder anzeigen wuerden.
    """
    zeile = conn().execute("SELECT * FROM %s WHERE id = ?" % tabelle, (eintrag_id,)).fetchone()
    if zeile is None:
        abort(404)
    return dict(zeile)


# ---------------------------------------------------------------------------
# Zugang und gemeinsame Vorlagenwerte
# ---------------------------------------------------------------------------

@bp.before_request
def schutz():
    if g.get("benutzer") is None:
        return redirect(url_for("auth.login", weiter=gewuenschtes_ziel()))
    if not csrf_pruefen():
        flash("Das Formular war zu lange offen. Bitte noch einmal absenden.", "fehler")
        return redirect(request.path)
    return None


@bp.app_context_processor
def vorlagenwerte():
    return {"csrf": csrf_token, "bereiche": BEREICHE}


# ---------------------------------------------------------------------------
# Übersicht
# ---------------------------------------------------------------------------

@bp.route("/")
def uebersicht():
    zahlen = {}
    for schluessel, b in BEREICHE.items():
        zahlen[schluessel] = conn().execute(
            "SELECT COUNT(*) AS n FROM %s" % b.tabelle).fetchone()["n"]
    zahlen["angebote"] = conn().execute("SELECT COUNT(*) AS n FROM angebote").fetchone()["n"]
    zahlen["zeiten"] = conn().execute("SELECT COUNT(*) AS n FROM zeiten").fetchone()["n"]
    zahlen["benutzer"] = anzahl_benutzer(conn())
    return render_template("admin/uebersicht.html", zahlen=zahlen,
                           stand=datenbank.geaendert_am(conn()))


# ---------------------------------------------------------------------------
# Listen und Formulare der einfachen Bereiche
# ---------------------------------------------------------------------------

def _bereich_oder_404(schluessel):
    b = BEREICHE.get(schluessel)
    if b is None:
        abort(404)
    return b


@bp.route("/inhalt/<schluessel>/")
def liste(schluessel):
    b = _bereich_oder_404(schluessel)
    eintraege = conn().execute(
        "SELECT * FROM %s ORDER BY %s" % (b.tabelle, b.reihenfolge)).fetchall()
    return render_template("admin/liste.html", b=b, eintraege=eintraege)


@bp.route("/inhalt/<schluessel>/neu", methods=["GET", "POST"])
def neu(schluessel):
    b = _bereich_oder_404(schluessel)
    if request.method == "POST":
        werte, fehler = werte_einlesen(b)
        if fehler:
            for f in fehler:
                flash(f, "fehler")
            return render_template("admin/formular.html", b=b, eintrag=werte, neu=True)
        spalten = list(werte) + ["sortierung"]
        platzhalter = ", ".join("?" * len(spalten))
        conn().execute("INSERT INTO %s (%s) VALUES (%s)"
                       % (b.tabelle, ", ".join(spalten), platzhalter),
                       list(werte.values()) + [naechste_sortierung(b.tabelle)])
        geaendert()
        flash("%s angelegt." % b.einzahl, "erfolg")
        return redirect(url_for("admin.liste", schluessel=schluessel))

    leer = {f.name: (1 if f.name == "aktiv" else "") for f in b.felder}
    return render_template("admin/formular.html", b=b, eintrag=leer, neu=True)


@bp.route("/inhalt/<schluessel>/<int:eid>", methods=["GET", "POST"])
def bearbeiten(schluessel, eid):
    b = _bereich_oder_404(schluessel)
    eintrag = hole(b.tabelle, eid)
    if request.method == "POST":
        werte, fehler = werte_einlesen(b, eintrag)
        if fehler:
            for f in fehler:
                flash(f, "fehler")
            return render_template("admin/formular.html", b=b,
                                   eintrag=dict(eintrag, **werte), neu=False)
        satz = ", ".join("%s = ?" % k for k in werte)
        conn().execute("UPDATE %s SET %s WHERE id = ?" % (b.tabelle, satz),
                       list(werte.values()) + [eid])
        geaendert()
        flash("Änderungen gespeichert.", "erfolg")
        return redirect(url_for("admin.liste", schluessel=schluessel))
    return render_template("admin/formular.html", b=b, eintrag=eintrag, neu=False)


@bp.route("/inhalt/<schluessel>/<int:eid>/loeschen", methods=["POST"])
def loeschen(schluessel, eid):
    b = _bereich_oder_404(schluessel)
    eintrag = hole(b.tabelle, eid)
    for feld in b.felder:
        if feld.typ == "datei":
            loesche_datei(eintrag[feld.name])
    conn().execute("DELETE FROM %s WHERE id = ?" % b.tabelle, (eid,))
    geaendert()
    flash("%s gelöscht." % b.einzahl, "erfolg")
    return redirect(url_for("admin.liste", schluessel=schluessel))


@bp.route("/inhalt/<schluessel>/<int:eid>/verschieben", methods=["POST"])
def verschieben(schluessel, eid):
    """Einen Eintrag in der Reihenfolge um einen Platz bewegen."""
    b = _bereich_oder_404(schluessel)
    if not b.sortierbar:
        abort(404)
    hoch = request.form.get("richtung") == "hoch"
    eintraege = conn().execute(
        "SELECT id FROM %s ORDER BY sortierung, id" % b.tabelle).fetchall()
    ids = [z["id"] for z in eintraege]
    if eid not in ids:
        abort(404)
    i = ids.index(eid)
    j = i - 1 if hoch else i + 1
    if 0 <= j < len(ids):
        ids[i], ids[j] = ids[j], ids[i]
        for platz, kennung in enumerate(ids):
            conn().execute("UPDATE %s SET sortierung = ? WHERE id = ?" % b.tabelle,
                           (platz, kennung))
        geaendert()
    return redirect(url_for("admin.liste", schluessel=schluessel))


# ---------------------------------------------------------------------------
# Sportangebote
# ---------------------------------------------------------------------------

def angebot_felder():
    kategorien = conn().execute("SELECT * FROM kategorien ORDER BY sortierung, id").fetchall()
    zielgruppen = conn().execute("SELECT * FROM zielgruppen ORDER BY sortierung, id").fetchall()
    return kategorien, zielgruppen


def zeiten_einlesen():
    """Die Trainingszeiten-Zeilen aus dem Formular lesen; leere Zeilen entfallen."""
    spalten = ["tag", "von", "bis", "ort", "gruppe", "leitung", "hinweis"]
    listen = {s: request.form.getlist("zeit_" + s) for s in spalten}
    anzahl = max((len(v) for v in listen.values()), default=0)
    zeilen = []
    for i in range(anzahl):
        zeile = {s: (listen[s][i].strip() if i < len(listen[s]) else "") for s in spalten}
        if not any(zeile[s] for s in spalten if s != "tag"):
            continue
        if zeile["tag"] not in WOCHENTAGE:
            zeile["tag"] = WOCHENTAGE[0]
        zeilen.append(zeile)
    return zeilen


def angebot_einlesen(alt=None):
    werte = {
        "name": (request.form.get("name") or "").strip(),
        "kategorie": (request.form.get("kategorie") or "").strip(),
        "kurz": (request.form.get("kurz") or "").strip(),
        "text": (request.form.get("text") or "").strip(),
        "ort": (request.form.get("ort") or "").strip(),
        "leitung": (request.form.get("leitung") or "").strip(),
        "kontakt_email": (request.form.get("kontakt_email") or "").strip(),
        "kontakt_telefon": (request.form.get("kontakt_telefon") or "").strip(),
    }
    gewaehlt = request.form.getlist("zielgruppen")
    fehler = []
    if not werte["name"]:
        fehler.append("Der Name darf nicht leer sein.")
    if not werte["kategorie"]:
        fehler.append("Bitte einen Bereich auswählen.")
    if werte["kontakt_email"] and "@" not in werte["kontakt_email"]:
        fehler.append("Die Kontakt-E-Mail sieht nicht nach einer Adresse aus.")
    return werte, gewaehlt, zeiten_einlesen(), fehler


def zeiten_schreiben(angebot_id, zeilen):
    conn().execute("DELETE FROM zeiten WHERE angebot_id = ?", (angebot_id,))
    for i, z in enumerate(zeilen):
        conn().execute(
            "INSERT INTO zeiten (angebot_id, tag, von, bis, ort, gruppe, leitung, hinweis, "
            "sortierung) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (angebot_id, z["tag"], z["von"], z["bis"], z["ort"], z["gruppe"], z["leitung"],
             z["hinweis"], i))


def zielgruppen_schreiben(angebot_id, gewaehlt):
    erlaubt = {z["id"] for z in conn().execute("SELECT id FROM zielgruppen")}
    conn().execute("DELETE FROM angebot_zielgruppen WHERE angebot_id = ?", (angebot_id,))
    for z in gewaehlt:
        if z in erlaubt:
            conn().execute("INSERT OR IGNORE INTO angebot_zielgruppen (angebot_id, zielgruppe_id) "
                           "VALUES (?, ?)", (angebot_id, z))


@bp.route("/angebote/")
def angebote():
    zeilen = conn().execute("""
        SELECT a.*, k.name AS kategorie_name,
               (SELECT COUNT(*) FROM zeiten z WHERE z.angebot_id = a.id) AS anzahl_zeiten
        FROM angebote a LEFT JOIN kategorien k ON k.id = a.kategorie
        ORDER BY a.sortierung, a.id""").fetchall()
    return render_template("admin/angebote.html", angebote=zeilen)


@bp.route("/angebote/neu", methods=["GET", "POST"])
def angebot_neu():
    kategorien, zielgruppen = angebot_felder()
    if request.method == "POST":
        werte, gewaehlt, zeilen, fehler = angebot_einlesen()
        if fehler:
            for f in fehler:
                flash(f, "fehler")
        else:
            cur = conn().execute(
                "INSERT INTO angebote (slug, name, kategorie, kurz, text, ort, leitung, "
                "kontakt_email, kontakt_telefon, sortierung) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (freier_slug(werte["name"]), werte["name"], werte["kategorie"], werte["kurz"],
                 werte["text"], werte["ort"], werte["leitung"], werte["kontakt_email"],
                 werte["kontakt_telefon"], naechste_sortierung("angebote")))
            zielgruppen_schreiben(cur.lastrowid, gewaehlt)
            zeiten_schreiben(cur.lastrowid, zeilen)
            geaendert()
            flash("Angebot angelegt.", "erfolg")
            return redirect(url_for("admin.angebote"))
        return render_template("admin/angebot.html", a=werte, gewaehlt=gewaehlt, zeiten=zeilen,
                               kategorien=kategorien, zielgruppen=zielgruppen,
                               wochentage=WOCHENTAGE, neu=True)

    leer = {k: "" for k in ("name", "kategorie", "kurz", "text", "ort", "leitung",
                            "kontakt_email", "kontakt_telefon")}
    return render_template("admin/angebot.html", a=leer, gewaehlt=[], zeiten=[],
                           kategorien=kategorien, zielgruppen=zielgruppen,
                           wochentage=WOCHENTAGE, neu=True)


@bp.route("/angebote/<int:eid>", methods=["GET", "POST"])
def angebot_bearbeiten(eid):
    kategorien, zielgruppen = angebot_felder()
    eintrag = hole("angebote", eid)
    if request.method == "POST":
        werte, gewaehlt, zeilen, fehler = angebot_einlesen(eintrag)
        if fehler:
            for f in fehler:
                flash(f, "fehler")
            return render_template("admin/angebot.html", a=dict(eintrag, **werte),
                                   gewaehlt=gewaehlt, zeiten=zeilen, kategorien=kategorien,
                                   zielgruppen=zielgruppen, wochentage=WOCHENTAGE, neu=False,
                                   eid=eid)
        conn().execute(
            "UPDATE angebote SET slug = ?, name = ?, kategorie = ?, kurz = ?, text = ?, ort = ?, "
            "leitung = ?, kontakt_email = ?, kontakt_telefon = ? WHERE id = ?",
            (freier_slug(werte["name"], ausser=eid), werte["name"], werte["kategorie"],
             werte["kurz"], werte["text"], werte["ort"], werte["leitung"],
             werte["kontakt_email"], werte["kontakt_telefon"], eid))
        zielgruppen_schreiben(eid, gewaehlt)
        zeiten_schreiben(eid, zeilen)
        geaendert()
        flash("Änderungen gespeichert.", "erfolg")
        return redirect(url_for("admin.angebote"))

    gewaehlt = [z["zielgruppe_id"] for z in conn().execute(
        "SELECT zielgruppe_id FROM angebot_zielgruppen WHERE angebot_id = ?", (eid,))]
    zeilen = [dict(z) for z in conn().execute(
        "SELECT * FROM zeiten WHERE angebot_id = ? ORDER BY sortierung, id", (eid,))]
    return render_template("admin/angebot.html", a=eintrag, gewaehlt=gewaehlt, zeiten=zeilen,
                           kategorien=kategorien, zielgruppen=zielgruppen,
                           wochentage=WOCHENTAGE, neu=False, eid=eid)


@bp.route("/angebote/<int:eid>/loeschen", methods=["POST"])
def angebot_loeschen(eid):
    hole("angebote", eid)
    conn().execute("DELETE FROM zeiten WHERE angebot_id = ?", (eid,))
    conn().execute("DELETE FROM angebot_zielgruppen WHERE angebot_id = ?", (eid,))
    conn().execute("DELETE FROM angebote WHERE id = ?", (eid,))
    geaendert()
    flash("Angebot gelöscht.", "erfolg")
    return redirect(url_for("admin.angebote"))


@bp.route("/angebote/<int:eid>/verschieben", methods=["POST"])
def angebot_verschieben(eid):
    hoch = request.form.get("richtung") == "hoch"
    ids = [z["id"] for z in conn().execute("SELECT id FROM angebote ORDER BY sortierung, id")]
    if eid not in ids:
        abort(404)
    i = ids.index(eid)
    j = i - 1 if hoch else i + 1
    if 0 <= j < len(ids):
        ids[i], ids[j] = ids[j], ids[i]
        for platz, kennung in enumerate(ids):
            conn().execute("UPDATE angebote SET sortierung = ? WHERE id = ?", (platz, kennung))
        geaendert()
    return redirect(url_for("admin.angebote"))


# ---------------------------------------------------------------------------
# Bereiche und Zielgruppen
# ---------------------------------------------------------------------------

ORDNUNGEN = {
    "kategorien": ("Bereiche", "Bereich", "kategorie",
                   "Die Bereiche gliedern das Sportangebot und stehen als Kacheln auf der "
                   "Startseite."),
    "zielgruppen": ("Zielgruppen", "Zielgruppe", "zielgruppe",
                    "Nach diesen Gruppen lässt sich das Sportangebot filtern."),
}


@bp.route("/ordnung/<art>/", methods=["GET", "POST"])
def ordnung(art):
    if art not in ORDNUNGEN:
        abort(404)
    titel, einzahl, _, beschreibung = ORDNUNGEN[art]
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        if not name:
            flash("Bitte einen Namen angeben.", "fehler")
        else:
            kennung = slug(name)
            if conn().execute("SELECT 1 FROM %s WHERE id = ?" % art, (kennung,)).fetchone():
                flash("Diesen Eintrag gibt es schon.", "fehler")
            else:
                conn().execute("INSERT INTO %s (id, name, sortierung) VALUES (?, ?, ?)"
                               % art, (kennung, name, naechste_sortierung(art)))
                geaendert()
                flash("%s angelegt." % einzahl, "erfolg")
        return redirect(url_for("admin.ordnung", art=art))

    eintraege = conn().execute("SELECT * FROM %s ORDER BY sortierung, id" % art).fetchall()
    if art == "kategorien":
        genutzt = {z["kategorie"]: z["n"] for z in conn().execute(
            "SELECT kategorie, COUNT(*) AS n FROM angebote GROUP BY kategorie")}
    else:
        genutzt = {z["zielgruppe_id"]: z["n"] for z in conn().execute(
            "SELECT zielgruppe_id, COUNT(*) AS n FROM angebot_zielgruppen GROUP BY zielgruppe_id")}
    return render_template("admin/ordnung.html", art=art, titel=titel, einzahl=einzahl,
                           beschreibung=beschreibung, eintraege=eintraege, genutzt=genutzt)


@bp.route("/ordnung/<art>/<kennung>/umbenennen", methods=["POST"])
def ordnung_umbenennen(art, kennung):
    if art not in ORDNUNGEN:
        abort(404)
    name = (request.form.get("name") or "").strip()
    if name:
        conn().execute("UPDATE %s SET name = ? WHERE id = ?" % art, (name, kennung))
        geaendert()
        flash("Umbenannt.", "erfolg")
    return redirect(url_for("admin.ordnung", art=art))


@bp.route("/ordnung/<art>/<kennung>/loeschen", methods=["POST"])
def ordnung_loeschen(art, kennung):
    if art not in ORDNUNGEN:
        abort(404)
    _, einzahl, _, _ = ORDNUNGEN[art]
    if art == "kategorien":
        n = conn().execute("SELECT COUNT(*) AS n FROM angebote WHERE kategorie = ?",
                           (kennung,)).fetchone()["n"]
    else:
        n = conn().execute("SELECT COUNT(*) AS n FROM angebot_zielgruppen WHERE zielgruppe_id = ?",
                           (kennung,)).fetchone()["n"]
    if n:
        flash("%s wird noch von %d Angeboten benutzt und kann nicht gelöscht werden."
              % (einzahl, n), "fehler")
    else:
        conn().execute("DELETE FROM %s WHERE id = ?" % art, (kennung,))
        geaendert()
        flash("%s gelöscht." % einzahl, "erfolg")
    return redirect(url_for("admin.ordnung", art=art))


@bp.route("/ordnung/<art>/<kennung>/verschieben", methods=["POST"])
def ordnung_verschieben(art, kennung):
    if art not in ORDNUNGEN:
        abort(404)
    hoch = request.form.get("richtung") == "hoch"
    ids = [z["id"] for z in conn().execute("SELECT id FROM %s ORDER BY sortierung, id" % art)]
    if kennung in ids:
        i = ids.index(kennung)
        j = i - 1 if hoch else i + 1
        if 0 <= j < len(ids):
            ids[i], ids[j] = ids[j], ids[i]
            for platz, k in enumerate(ids):
                conn().execute("UPDATE %s SET sortierung = ? WHERE id = ?" % art, (platz, k))
            geaendert()
    return redirect(url_for("admin.ordnung", art=art))


# ---------------------------------------------------------------------------
# Stammdaten und Texte
# ---------------------------------------------------------------------------

class Gruppe:
    """Ein Formular, das direkt in die Einstellungen schreibt."""

    def __init__(self, titel, beschreibung, felder):
        self.titel = titel
        self.beschreibung = beschreibung
        self.felder = felder


STAMMDATEN = Gruppe(
    "Stammdaten", "Name, Anschrift und Kontakt des Vereins. Diese Angaben stehen im Footer, "
                  "auf der Vereinsseite und im Impressum.",
    [
        Feld("name", "Vollständiger Vereinsname", pflicht=True),
        Feld("kurzname", "Kurzname", pflicht=True,
             hinweis="Erscheint im Seitentitel und groß im Footer."),
        Feld("gegruendet", "Gegründet", platzhalter="1908"),
        Feld("claim", "Ein Satz über den Verein", typ="textarea",
             hinweis="Steht auf der Startseite und oben auf der Vereinsseite."),
        Feld("strasse", "Straße und Hausnummer"),
        Feld("plz", "Postleitzahl"),
        Feld("ort", "Ort"),
        Feld("telefon", "Telefon", platzhalter="04643 1316"),
        Feld("telefon_link", "Telefonnummer für Links", platzhalter="+4946431316",
             hinweis="Leer lassen — dann wird sie automatisch aus der Telefonnummer gebildet."),
        Feld("telefax", "Telefax"),
        Feld("email", "E-Mail-Adresse", typ="email", pflicht=True),
        Feld("register", "Registereintrag", platzhalter="VR 1033 FL, Amtsgericht Flensburg"),
        Feld("oeffnungszeiten", "Öffnungszeiten der Geschäftsstelle", typ="textarea",
             hinweis="Leer lassen, solange es keine festen Zeiten gibt."),
        Feld("facebook", "Facebook", typ="url"),
        Feld("instagram", "Instagram", typ="url"),
        Feld("shop", "Vereinsshop", typ="url"),
    ])

TEXTE = Gruppe(
    "Texte & Bilder", "Überschriften, längere Texte und die Bilder der Website.",
    [
        Feld("start_titel", "Startseite: Überschrift", platzhalter="Sport für alle."),
        Feld("start_titel_akzent", "Startseite: hervorgehobener Teil", platzhalter="In Gelting.",
             hinweis="Steht in der zweiten Zeile und wird farbig gesetzt."),
        Feld("start_seitentitel", "Startseite: Titel im Browser-Tab"),
        Feld("start_bild", "Startseite: großes Bild", typ="datei", ordner="bilder",
             hinweis="Ohne Bild erscheint ein Platzhalter."),
        Feld("training_bild", "Startseite: Bild beim Wochenplan", typ="datei", ordner="bilder"),
        Feld("beitrag_hinweis", "Hinweis unter den Beiträgen", typ="textarea"),
        Feld("sprachrohr_text", "Sprachrohr: Einleitung", typ="textarea"),
        Feld("sprachrohr_bild", "Sprachrohr: Titelbild", typ="datei", ordner="bilder"),
        Feld("jugendschutz_text", "Kinder- & Jugendschutz", typ="textarea",
             hinweis="Konzept und Ansprechpersonen. Eine Leerzeile trennt Absätze."),
        Feld("quelle", "Quelle der Trainingszeiten", typ="textarea",
             hinweis="Wird unter dem Wochenplan genannt. Leer lassen, um den Hinweis "
                     "auszublenden."),
        Feld("hinweisbanner", "Hinweisstreifen ganz oben", typ="textarea",
             hinweis="Leer lassen, um den Streifen auszublenden. Der Teil vor dem ersten „·“ "
                     "wird fett gesetzt."),
        Feld("suchmaschinen_sperren", "Für Suchmaschinen sperren", typ="checkbox",
             hinweis="Solange die Seite ein Entwurf ist, sollte das angehakt bleiben. "
                     "Vor dem Livegang abwählen."),
        Feld("admin_url", "Adresse des Anmeldelinks im Footer", platzhalter="/admin/",
             hinweis="Leer lassen, um den Link „Vereinsintern anmelden“ auszublenden."),
        Feld("datenschutz_text", "Datenschutzerklärung", typ="textarea",
             hinweis="Leer lassen, um den mitgelieferten Standardtext zu verwenden. "
                     "Eine Leerzeile trennt Absätze."),
        Feld("datenschutz_hinweis", "Hinweis unter der Datenschutzerklärung", typ="textarea"),
        Feld("impressum_hinweis", "Hinweis unter dem Impressum", typ="textarea"),
    ])


def _einstellungen_formular(gruppe, vorlage, ziel):
    werte = datenbank.einstellungen(conn())
    if request.method == "POST":
        neu_werte, fehler = werte_einlesen(gruppe, werte)
        if fehler:
            for f in fehler:
                flash(f, "fehler")
            return render_template(vorlage, gruppe=gruppe, werte=dict(werte, **neu_werte))
        typen = {f.name: f.typ for f in gruppe.felder}
        for k, v in neu_werte.items():
            if typen[k] == "checkbox":
                v = "1" if v else ""
            datenbank.setze(conn(), k, v)
        geaendert()
        flash("Gespeichert.", "erfolg")
        return redirect(url_for(ziel))
    return render_template(vorlage, gruppe=gruppe, werte=werte)


@bp.route("/stammdaten", methods=["GET", "POST"])
def stammdaten():
    return _einstellungen_formular(STAMMDATEN, "admin/einstellungen.html", "admin.stammdaten")


@bp.route("/texte", methods=["GET", "POST"])
def texte():
    return _einstellungen_formular(TEXTE, "admin/einstellungen.html", "admin.texte")


# ---------------------------------------------------------------------------
# Zugänge
# ---------------------------------------------------------------------------

@bp.route("/benutzer/", methods=["GET", "POST"])
def benutzer():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        name = (request.form.get("name") or "").strip()
        passwort = request.form.get("passwort") or ""
        fehler = None
        if "@" not in email:
            fehler = "Bitte eine gültige E-Mail-Adresse angeben."
        elif benutzer_nach_email(conn(), email) is not None:
            fehler = "Für diese E-Mail-Adresse gibt es schon einen Zugang."
        else:
            fehler = passwort_pruefregel(passwort)
        if fehler:
            flash(fehler, "fehler")
        else:
            benutzer_anlegen(conn(), email, name, passwort)
            flash("Zugang für %s angelegt." % email, "erfolg")
        return redirect(url_for("admin.benutzer"))

    zeilen = conn().execute("SELECT id, email, name, angelegt, letzter_login FROM admins "
                            "ORDER BY email").fetchall()
    return render_template("admin/benutzer.html", benutzer=zeilen)


@bp.route("/benutzer/<int:eid>/loeschen", methods=["POST"])
def benutzer_loeschen(eid):
    if eid == g.benutzer["id"]:
        flash("Den eigenen Zugang kann man nicht löschen.", "fehler")
    elif anzahl_benutzer(conn()) <= 1:
        flash("Der letzte Zugang kann nicht gelöscht werden.", "fehler")
    else:
        conn().execute("DELETE FROM admins WHERE id = ?", (eid,))
        conn().commit()
        flash("Zugang gelöscht.", "erfolg")
    return redirect(url_for("admin.benutzer"))


@bp.route("/passwort", methods=["GET", "POST"])
def passwort():
    if request.method == "POST":
        alt = request.form.get("alt") or ""
        neu = request.form.get("neu") or ""
        neu2 = request.form.get("neu2") or ""
        fehler = None
        if not pruefe_passwort(g.benutzer["passwort"], alt):
            fehler = "Das bisherige Passwort stimmt nicht."
        elif neu != neu2:
            fehler = "Die beiden neuen Passwörter stimmen nicht überein."
        else:
            fehler = passwort_pruefregel(neu)
        if fehler:
            flash(fehler, "fehler")
        else:
            conn().execute("UPDATE admins SET passwort = ? WHERE id = ?",
                           (hash_passwort(neu), g.benutzer["id"]))
            conn().commit()
            flash("Passwort geändert.", "erfolg")
            return redirect(url_for("admin.uebersicht"))
    return render_template("admin/passwort.html")


# ---------------------------------------------------------------------------
# Statische Seiten erzeugen
# ---------------------------------------------------------------------------

@bp.route("/veroeffentlichen", methods=["GET", "POST"])
def veroeffentlichen():
    from .render import Renderer

    ziel = pathlib.Path(current_app.config.get("EXPORT")
                        or pathlib.Path(current_app.root_path).parent)
    if request.method == "POST":
        V, A = datenbank.lade_daten(conn())
        try:
            for name, inhalt in Renderer(V, A).pages().items():
                (ziel / name).write_text(inhalt, encoding="utf-8")
            # Die JSON-Dateien gehoeren zum selben Ausgabeordner – sonst
            # schriebe der Export in ein fremdes Verzeichnis.
            datenordner = ziel / "data"
            datenordner.mkdir(parents=True, exist_ok=True)
            datenbank.nach_json(conn(), datenordner)
        except OSError as f:
            flash("Die Dateien ließen sich nicht schreiben: %s" % f, "fehler")
        else:
            flash("Die statischen Seiten in %s wurden neu erzeugt." % ziel, "erfolg")
        return redirect(url_for("admin.veroeffentlichen"))
    return render_template("admin/veroeffentlichen.html", ziel=ziel)
