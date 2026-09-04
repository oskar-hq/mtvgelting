#!/usr/bin/env python3
"""Inhalte aus dem Sanity-CMS holen.

Eine einzige GROQ-Abfrage holt alles, was die Website braucht; das Ergebnis
wird auf dieselbe Struktur abgebildet, die auch ``tools/inhalte.aus_json``
liefert. Der Generator merkt dadurch nicht, woher die Inhalte kommen.

Bilder und PDFs werden beim Bauen **heruntergeladen** und neben die Seiten
gelegt, statt auf das Sanity-CDN zu verlinken. So laedt kein Besucher etwas bei
einem Dritten nach — das erspart einen Abschnitt in der Datenschutzerklaerung
und die Seite funktioniert auch dann noch, wenn das CMS einmal nicht erreichbar
ist.

Ohne Zusatzbibliotheken: die Sanity-API ist schlichtes HTTP mit JSON.
"""

import hashlib
import json
import os
import pathlib
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

from . import inhalte

# Datum der API-Fassung. Sanity verlangt eine Angabe und garantiert dafuer,
# dass sich das Verhalten spaeter nicht unter uns veraendert.
API_FASSUNG = "2024-10-01"

# Groesste ausgelieferte Bildbreite. Sanity rechnet das beim Abruf herunter,
# vergroessert aber nie ueber das Original hinaus.
BILDBREITE = 1600

ZEITLIMIT = 30


class SanityFehler(RuntimeError):
    """Das CMS war nicht erreichbar oder hat etwas Unerwartetes geliefert."""


# ---------------------------------------------------------------------------
# Abfrage
# ---------------------------------------------------------------------------

# „!(_id in path('drafts.**'))“ blendet unveroeffentlichte Entwuerfe aus. Ohne
# das erschienen halbfertige Eintraege auf der Website, sobald jemand im CMS
# etwas anfaengt und liegen laesst.
VEROEFFENTLICHT = "!(_id in path('drafts.**'))"

BILDFELDER = "{asset->{_id, url, originalFilename, extension}}"

ABFRAGE = """{
  "verein": *[_type == "verein" && %(v)s][0],
  "texte": *[_type == "texte" && %(v)s][0]{
    ...,
    startBild%(b)s,
    trainingBild%(b)s,
    sprachrohrBild%(b)s
  },
  "vorstand": *[_type == "vorstandsmitglied" && %(v)s] | order(sortierung asc, name asc),
  "beitraege": *[_type == "beitrag" && %(v)s] | order(sortierung asc),
  "termine": *[_type == "termin" && %(v)s] | order(sortierung asc, datum asc),
  "news": *[_type == "news" && %(v)s] | order(datum desc),
  "aktionen": *[_type == "aktion" && %(v)s] | order(sortierung asc, titel asc),
  "sponsoren": *[_type == "sponsor" && %(v)s] | order(sortierung asc, name asc){
    name, url, logo%(b)s
  },
  "spielplaene": *[_type == "spielplan" && %(v)s] | order(sortierung asc, name asc),
  "dokumente": *[_type == "dokument" && %(v)s] | order(bereich asc, sortierung asc){
    bereich, titel, beschreibung, url, datei%(b)s
  },
  "kategorien": *[_type == "kategorie" && %(v)s] | order(sortierung asc){
    "id": kennung.current, name
  },
  "zielgruppen": *[_type == "zielgruppe" && %(v)s] | order(sortierung asc){
    "id": kennung.current, name
  },
  "angebote": *[_type == "angebot" && %(v)s] | order(sortierung asc, name asc){
    "slug": slug.current, name, kurz, text, ort, leitung, kontaktEmail, kontaktTelefon,
    "kategorie": kategorie->kennung.current,
    "zielgruppen": zielgruppen[]->kennung.current,
    zeiten
  }
}""" % {"v": VEROEFFENTLICHT, "b": BILDFELDER}


def _oeffnen(url, kopfzeilen=None):
    anfrage = urllib.request.Request(url, headers=kopfzeilen or {})
    return urllib.request.urlopen(anfrage, timeout=ZEITLIMIT)


def abfragen(projekt, datensatz="production", token="", groq=ABFRAGE, oeffnen=_oeffnen):
    """Die GROQ-Abfrage ausfuehren und das Ergebnis zurueckgeben."""
    adresse = "https://%s.api.sanity.io/v%s/data/query/%s?%s" % (
        projekt, API_FASSUNG, datensatz,
        urllib.parse.urlencode({"query": groq}))
    kopfzeilen = {"Accept": "application/json"}
    if token:
        kopfzeilen["Authorization"] = "Bearer %s" % token
    try:
        with oeffnen(adresse, kopfzeilen) as antwort:
            geladen = json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as fehler:
        hinweis = ""
        if fehler.code in (401, 403):
            hinweis = (" Bei einem nicht oeffentlichen Datensatz muss SANITY_TOKEN "
                       "gesetzt sein (Leserecht genuegt).")
        raise SanityFehler("Sanity antwortete mit %s %s.%s"
                           % (fehler.code, fehler.reason, hinweis)) from fehler
    except urllib.error.URLError as fehler:
        raise SanityFehler("Sanity war nicht erreichbar: %s" % fehler.reason) from fehler
    except json.JSONDecodeError as fehler:
        raise SanityFehler("Sanity lieferte kein JSON zurueck.") from fehler

    if "result" not in geladen:
        raise SanityFehler("Unerwartete Antwort von Sanity: %s"
                           % json.dumps(geladen)[:300])
    return geladen["result"]


# ---------------------------------------------------------------------------
# Bilder und Dateien
# ---------------------------------------------------------------------------

def _kurzname(text):
    text = (text or "").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower() or "datei"


class Medien:
    """Laedt Bilder und Dateien aus Sanity herunter und merkt sich die Pfade.

    Die Dateinamen bleiben ueber Neubauten hinweg gleich (sie enthalten einen
    Teil der Sanity-Kennung), damit sich bei unveraenderten Inhalten auch nichts
    am Ergebnis aendert.
    """

    def __init__(self, wurzel, bildordner="assets/img/inhalte",
                 dateiordner="assets/dokumente", laden=None):
        self.wurzel = pathlib.Path(wurzel)
        self.bildordner = bildordner
        self.dateiordner = dateiordner
        self._laden = laden or self._herunterladen
        self.geholt = []

    @staticmethod
    def _herunterladen(adresse):
        with _oeffnen(adresse) as antwort:
            return antwort.read()

    @staticmethod
    def _asset(feld):
        if isinstance(feld, dict):
            asset = feld.get("asset")
            if isinstance(asset, dict) and asset.get("url"):
                return asset
        return None

    def _ablegen(self, asset, ordner, adresse):
        endung = asset.get("extension") or pathlib.Path(
            urllib.parse.urlparse(asset["url"]).path).suffix.lstrip(".") or "bin"
        stamm = _kurzname(pathlib.Path(asset.get("originalFilename") or "datei").stem)[:50]
        kennung = hashlib.sha1((asset.get("_id") or asset["url"]).encode("utf-8")).hexdigest()[:8]
        pfad = "%s/%s-%s.%s" % (ordner, stamm, kennung, endung.lower())

        ziel = self.wurzel / pfad
        ziel.parent.mkdir(parents=True, exist_ok=True)
        if not ziel.exists():
            try:
                ziel.write_bytes(self._laden(adresse))
            except (urllib.error.URLError, OSError) as fehler:
                # Ein fehlendes Bild darf den ganzen Build nicht scheitern
                # lassen; der Generator setzt dann seinen Platzhalter ein.
                print("  ! %s liess sich nicht laden: %s" % (pfad, fehler))
                return ""
        self.geholt.append(pfad)
        return pfad

    def bild(self, feld):
        asset = self._asset(feld)
        if not asset:
            return ""
        trennzeichen = "&" if "?" in asset["url"] else "?"
        return self._ablegen(asset, self.bildordner,
                             "%s%sw=%d&q=80" % (asset["url"], trennzeichen, BILDBREITE))

    def datei(self, feld):
        asset = self._asset(feld)
        if not asset:
            return ""
        return self._ablegen(asset, self.dateiordner, asset["url"])


# ---------------------------------------------------------------------------
# Abbildung auf die Struktur des Generators
# ---------------------------------------------------------------------------

def _text(quelle, feld, vorgabe=""):
    """Ein Textfeld lesen; fehlt es oder ist es leer, gilt die Vorgabe."""
    wert = (quelle or {}).get(feld)
    if wert is None:
        return vorgabe
    wert = str(wert).strip()
    return wert if wert else vorgabe


def _liste(roh, name):
    wert = roh.get(name)
    return wert if isinstance(wert, list) else []


def nach_inhalten(roh, medien):
    """Die Antwort von Sanity in die Dictionaries V und A umsetzen."""
    verein = roh.get("verein") or {}
    texte = roh.get("texte") or {}
    adresse = verein.get("adresse") or {}
    std = inhalte.STANDARD

    telefon = _text(verein, "telefon")
    V = {
        "name": _text(verein, "name", std["name"]),
        "kurzname": _text(verein, "kurzname", std["kurzname"]),
        "gegruendet": _text(verein, "gegruendet", std["gegruendet"]),
        "claim": _text(verein, "claim"),
        "adresse": {
            "strasse": _text(adresse, "strasse"),
            "plz": _text(adresse, "plz"),
            "ort": _text(adresse, "ort"),
        },
        "telefon": telefon,
        "telefon_link": inhalte.telefonlink(telefon, _text(verein, "telefonLink")),
        "telefax": _text(verein, "telefax"),
        "email": _text(verein, "email"),
        "register": _text(verein, "register"),
        "social": {
            "facebook": _text(verein, "facebook"),
            "instagram": _text(verein, "instagram"),
        },
        "shop": _text(verein, "shop"),
        "beitrag_hinweis": _text(verein, "beitragHinweis"),
        "oeffnungszeiten": _text(verein, "oeffnungszeiten"),

        "start_titel": _text(texte, "startTitel", std["start_titel"]),
        "start_titel_akzent": _text(texte, "startTitelAkzent", std["start_titel_akzent"]),
        "start_seitentitel": _text(texte, "startSeitentitel", std["start_seitentitel"]),
        "start_bild": medien.bild(texte.get("startBild")),
        "training_bild": medien.bild(texte.get("trainingBild")),
        "sprachrohr_text": _text(texte, "sprachrohrText"),
        "sprachrohr_bild": medien.bild(texte.get("sprachrohrBild")),
        "jugendschutz_text": _text(texte, "jugendschutzText"),
        "hinweisbanner": _text(texte, "hinweisbanner"),
        # Fehlt die Angabe, wird gesperrt – das ist die vorsichtigere Annahme.
        "suchmaschinen_sperren": bool(texte.get("suchmaschinenSperren", True)),
        "impressum_hinweis": _text(texte, "impressumHinweis"),
        "datenschutz_text": _text(texte, "datenschutzText"),
        "datenschutz_hinweis": _text(texte, "datenschutzHinweis"),

        "vorstand": [
            {"name": _text(p, "name"), "rolle": _text(p, "rolle"),
             "email": _text(p, "email"), "paragraf26": bool(p.get("paragraf26"))}
            for p in _liste(roh, "vorstand")],
        "beitraege": [
            {"gruppe": _text(b, "gruppe"), "kurz": _text(b, "kurz"),
             "monat": _text(b, "monat"), "jahr": _text(b, "jahr"),
             "aktiv": bool(b.get("aktiv", True))}
            for b in _liste(roh, "beitraege")],
        "sponsoren": [
            {"name": _text(s, "name"), "logo": medien.bild(s.get("logo")),
             "url": _text(s, "url")}
            for s in _liste(roh, "sponsoren")],
        "news": [
            {"titel": _text(n, "titel"), "datum": _text(n, "datum"),
             "kategorie": _text(n, "kategorie"), "text": _text(n, "text")}
            for n in _liste(roh, "news")],
        "termine": [
            {"titel": _text(t, "titel"), "datum": _text(t, "datum"),
             "zeit": _text(t, "zeit"), "ort": _text(t, "ort"), "text": _text(t, "text")}
            for t in _liste(roh, "termine")],
        "aktionen": [
            {"titel": _text(a, "titel"), "aktiv": bool(a.get("aktiv", True)),
             "kurz": _text(a, "kurz"), "datum": _text(a, "datum"),
             "datum_bis": _text(a, "datumBis"), "zeit": _text(a, "zeit"),
             "ort": _text(a, "ort"), "text": _text(a, "text"), "bild": "",
             "anmeldelink": _text(a, "anmeldelink"),
             "anmeldetext": _text(a, "anmeldetext")}
            for a in _liste(roh, "aktionen")],
        "spielplaene": [
            {"name": _text(p, "name"), "quelle": _text(p, "quelle"), "url": _text(p, "url")}
            for p in _liste(roh, "spielplaene")],
        "dokumente": [
            {"bereich": _text(d, "bereich", "satzung"), "titel": _text(d, "titel"),
             "beschreibung": _text(d, "beschreibung"), "datei": medien.datei(d.get("datei")),
             "url": _text(d, "url")}
            for d in _liste(roh, "dokumente")],
    }

    kategorien = [{"id": _text(k, "id"), "name": _text(k, "name")}
                  for k in _liste(roh, "kategorien") if _text(k, "id")]
    zielgruppen = [{"id": _text(z, "id"), "name": _text(z, "name")}
                   for z in _liste(roh, "zielgruppen") if _text(z, "id")]
    reihenfolge = [z["id"] for z in zielgruppen]

    angebote = []
    for a in _liste(roh, "angebote"):
        gewaehlt = {z for z in (a.get("zielgruppen") or []) if z}
        angebote.append({
            "slug": _text(a, "slug") or _kurzname(_text(a, "name")),
            "name": _text(a, "name"),
            "kategorie": _text(a, "kategorie"),
            # Immer in der im CMS festgelegten Reihenfolge, unabhaengig davon,
            # in welcher sie beim Angebot angehakt wurden.
            "zielgruppen": [z for z in reihenfolge if z in gewaehlt],
            "kurz": _text(a, "kurz"),
            "text": _text(a, "text"),
            "ort": _text(a, "ort"),
            "leitung": _text(a, "leitung"),
            "kontakt_email": _text(a, "kontaktEmail"),
            "kontakt_telefon": _text(a, "kontaktTelefon"),
            "zeiten": [
                {"tag": _text(z, "tag"), "von": _text(z, "von"), "bis": _text(z, "bis"),
                 "ort": _text(z, "ort"), "gruppe": _text(z, "gruppe"),
                 "leitung": _text(z, "leitung"), "hinweis": _text(z, "hinweis")}
                for z in (a.get("zeiten") or [])],
        })

    A = {
        "quelle": _text(texte, "quelle"),
        "kategorien": kategorien,
        "zielgruppen": zielgruppen,
        "angebote": angebote,
    }
    return V, A


def einstellungen(umgebung=None):
    """Zugangsdaten aus den Umgebungsvariablen lesen."""
    umgebung = os.environ if umgebung is None else umgebung
    return {
        "projekt": umgebung.get("SANITY_PROJEKT", "").strip(),
        "datensatz": umgebung.get("SANITY_DATENSATZ", "production").strip() or "production",
        "token": umgebung.get("SANITY_TOKEN", "").strip(),
    }


def laden(wurzel, projekt, datensatz="production", token="", oeffnen=_oeffnen, medien=None):
    """Alles holen: Inhalte abfragen, Bilder herunterladen, V und A liefern."""
    roh = abfragen(projekt, datensatz, token, oeffnen=oeffnen)
    if not isinstance(roh, dict):
        raise SanityFehler("Sanity lieferte kein Ergebnisobjekt zurueck.")
    return nach_inhalten(roh, medien or Medien(wurzel))
