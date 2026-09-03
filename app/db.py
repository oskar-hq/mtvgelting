"""Datenbank des MTV Gelting 08.

Alle Inhalte der Website liegen in einer SQLite-Datei. ``lade_daten()`` liefert
sie genau in der Form, die ``app/render.py`` erwartet — die Seiten selbst wissen
nichts von der Datenbank.
"""

import json
import pathlib
import re
import sqlite3
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SCHEMA = """
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS einstellungen (
  schluessel TEXT PRIMARY KEY,
  wert       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS admins (
  id            INTEGER PRIMARY KEY,
  email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
  name          TEXT NOT NULL DEFAULT '',
  passwort      TEXT NOT NULL,
  angelegt      TEXT NOT NULL,
  letzter_login TEXT
);

CREATE TABLE IF NOT EXISTS vorstand (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL,
  rolle       TEXT NOT NULL DEFAULT '',
  email       TEXT NOT NULL DEFAULT '',
  paragraf26  INTEGER NOT NULL DEFAULT 0,
  sortierung  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS beitraege (
  id         INTEGER PRIMARY KEY,
  gruppe     TEXT NOT NULL,
  kurz       TEXT NOT NULL DEFAULT '',
  monat      TEXT NOT NULL DEFAULT '',
  jahr       TEXT NOT NULL DEFAULT '',
  aktiv      INTEGER NOT NULL DEFAULT 1,
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS termine (
  id         INTEGER PRIMARY KEY,
  titel      TEXT NOT NULL,
  datum      TEXT NOT NULL DEFAULT '',
  zeit       TEXT NOT NULL DEFAULT '',
  ort        TEXT NOT NULL DEFAULT '',
  text       TEXT NOT NULL DEFAULT '',
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS news (
  id         INTEGER PRIMARY KEY,
  titel      TEXT NOT NULL,
  datum      TEXT NOT NULL DEFAULT '',
  kategorie  TEXT NOT NULL DEFAULT '',
  text       TEXT NOT NULL DEFAULT '',
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sponsoren (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  logo       TEXT NOT NULL DEFAULT '',
  url        TEXT NOT NULL DEFAULT '',
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS spielplaene (
  id         INTEGER PRIMARY KEY,
  name       TEXT NOT NULL,
  quelle     TEXT NOT NULL DEFAULT '',
  url        TEXT NOT NULL DEFAULT '',
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dokumente (
  id           INTEGER PRIMARY KEY,
  bereich      TEXT NOT NULL DEFAULT 'satzung',
  titel        TEXT NOT NULL,
  beschreibung TEXT NOT NULL DEFAULT '',
  datei        TEXT NOT NULL DEFAULT '',
  url          TEXT NOT NULL DEFAULT '',
  sortierung   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS kategorien (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS zielgruppen (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS angebote (
  id              INTEGER PRIMARY KEY,
  slug            TEXT NOT NULL UNIQUE,
  name            TEXT NOT NULL,
  kategorie       TEXT NOT NULL DEFAULT '',
  kurz            TEXT NOT NULL DEFAULT '',
  text            TEXT NOT NULL DEFAULT '',
  ort             TEXT NOT NULL DEFAULT '',
  leitung         TEXT NOT NULL DEFAULT '',
  kontakt_email   TEXT NOT NULL DEFAULT '',
  kontakt_telefon TEXT NOT NULL DEFAULT '',
  sortierung      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS angebot_zielgruppen (
  angebot_id    INTEGER NOT NULL REFERENCES angebote(id) ON DELETE CASCADE,
  zielgruppe_id TEXT NOT NULL,
  PRIMARY KEY (angebot_id, zielgruppe_id)
);

CREATE TABLE IF NOT EXISTS zeiten (
  id         INTEGER PRIMARY KEY,
  angebot_id INTEGER NOT NULL REFERENCES angebote(id) ON DELETE CASCADE,
  tag        TEXT NOT NULL DEFAULT 'Montag',
  von        TEXT NOT NULL DEFAULT '',
  bis        TEXT NOT NULL DEFAULT '',
  ort        TEXT NOT NULL DEFAULT '',
  gruppe     TEXT NOT NULL DEFAULT '',
  leitung    TEXT NOT NULL DEFAULT '',
  hinweis    TEXT NOT NULL DEFAULT '',
  sortierung INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_zeiten_angebot ON zeiten(angebot_id);
"""

# Freie Textfelder mit ihren Voreinstellungen. Alles, was hier steht, laesst
# sich im Verwaltungsbereich unter „Stammdaten“ und „Texte“ aendern.
STANDARD = {
    "name": "Männer-Turn-Verein Gelting von 1908 e.V.",
    "kurzname": "MTV Gelting 08",
    "gegruendet": "1908",
    "claim": "",
    "strasse": "",
    "plz": "",
    "ort": "",
    "telefon": "",
    "telefon_link": "",
    "telefax": "",
    "email": "",
    "register": "",
    "facebook": "",
    "instagram": "",
    "shop": "",
    "beitrag_hinweis": "",
    "quelle": "",
    "oeffnungszeiten": "",
    "jugendschutz_text": "",
    "sprachrohr_text": "",
    "sprachrohr_bild": "",
    "start_titel": "Sport für alle.",
    "start_titel_akzent": "In Gelting.",
    "start_seitentitel": "Sport für alle in Gelting",
    "admin_url": "/admin/",
    "start_bild": "",
    "training_bild": "",
    "hinweisbanner": "",
    "suchmaschinen_sperren": "1",
    "impressum_hinweis": "",
    "datenschutz_text": "",
    "datenschutz_hinweis": "",
    "geaendert": "",
    "revision": "0",
}


# ---------------------------------------------------------------------------
# Verbindung
# ---------------------------------------------------------------------------

def verbinde(pfad):
    conn = sqlite3.connect(str(pfad))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def anlegen(conn):
    """Schema erzeugen und fehlende Einstellungen ergaenzen."""
    conn.executescript(SCHEMA)
    for k, v in STANDARD.items():
        conn.execute("INSERT OR IGNORE INTO einstellungen (schluessel, wert) VALUES (?, ?)", (k, v))
    conn.commit()


def jetzt():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def markiere_aenderung(conn):
    """Vermerken, dass sich Inhalte geaendert haben.

    Neben dem Zeitstempel — der nur zur Anzeige dient — wird ein Zaehler
    hochgesetzt. Der Zeitstempel allein reichte nicht: zwei Aenderungen
    innerhalb derselben Sekunde haetten denselben Wert ergeben, und die
    zwischengespeicherten Seiten waeren stehen geblieben.
    """
    conn.execute("UPDATE einstellungen SET wert = ? WHERE schluessel = 'geaendert'", (jetzt(),))
    conn.execute("UPDATE einstellungen SET wert = CAST(CAST(wert AS INTEGER) + 1 AS TEXT) "
                 "WHERE schluessel = 'revision'")


def stand(conn):
    """Kennung des aktuellen Inhaltsstands – aendert sich bei jeder Aenderung."""
    zeilen = {z["schluessel"]: z["wert"] for z in conn.execute(
        "SELECT schluessel, wert FROM einstellungen "
        "WHERE schluessel IN ('geaendert', 'revision')")}
    return "%s/%s" % (zeilen.get("revision", "0"), zeilen.get("geaendert", ""))


def geaendert_am(conn):
    """Zeitpunkt der letzten Aenderung, nur zur Anzeige."""
    zeile = conn.execute("SELECT wert FROM einstellungen WHERE schluessel = 'geaendert'").fetchone()
    return zeile["wert"] if zeile else ""


def einstellungen(conn):
    werte = dict(STANDARD)
    for zeile in conn.execute("SELECT schluessel, wert FROM einstellungen"):
        werte[zeile["schluessel"]] = zeile["wert"]
    return werte


def setze(conn, schluessel, wert):
    conn.execute(
        "INSERT INTO einstellungen (schluessel, wert) VALUES (?, ?) "
        "ON CONFLICT(schluessel) DO UPDATE SET wert = excluded.wert",
        (schluessel, "" if wert is None else str(wert)))


# ---------------------------------------------------------------------------
# Lesen: Daten fuer den Renderer
# ---------------------------------------------------------------------------

def telefonlink(nummer, vorgabe=""):
    """'04643 1316' -> '+4946431316'. Eine gepflegte Vorgabe hat Vorrang."""
    if vorgabe.strip():
        return vorgabe.strip()
    ziffern = re.sub(r"[^0-9+]", "", nummer or "")
    if not ziffern:
        return ""
    if ziffern.startswith("+"):
        return ziffern
    if ziffern.startswith("0"):
        return "+49" + ziffern[1:]
    return ziffern


def lade_daten(conn):
    """Vereinsdaten (V) und Sportangebote (A) fuer den Renderer."""
    e = einstellungen(conn)

    V = {
        "name": e["name"],
        "kurzname": e["kurzname"],
        "gegruendet": e["gegruendet"],
        "claim": e["claim"],
        "adresse": {"strasse": e["strasse"], "plz": e["plz"], "ort": e["ort"]},
        "telefon": e["telefon"],
        "telefon_link": telefonlink(e["telefon"], e["telefon_link"]),
        "telefax": e["telefax"],
        "email": e["email"],
        "register": e["register"],
        "social": {"facebook": e["facebook"], "instagram": e["instagram"]},
        "shop": e["shop"],
        "beitrag_hinweis": e["beitrag_hinweis"],
        "oeffnungszeiten": e["oeffnungszeiten"],
        "jugendschutz_text": e["jugendschutz_text"],
        "sprachrohr_text": e["sprachrohr_text"],
        "sprachrohr_bild": e["sprachrohr_bild"],
        "start_titel": e["start_titel"],
        "start_titel_akzent": e["start_titel_akzent"],
        "start_seitentitel": e["start_seitentitel"],
        "admin_url": e["admin_url"],
        "start_bild": e["start_bild"],
        "training_bild": e["training_bild"],
        "hinweisbanner": e["hinweisbanner"],
        "suchmaschinen_sperren": e["suchmaschinen_sperren"] == "1",
        "impressum_hinweis": e["impressum_hinweis"],
        "datenschutz_text": e["datenschutz_text"],
        "datenschutz_hinweis": e["datenschutz_hinweis"],
        "vorstand": [
            {"name": r["name"], "rolle": r["rolle"], "email": r["email"],
             "paragraf26": bool(r["paragraf26"])}
            for r in conn.execute("SELECT * FROM vorstand ORDER BY sortierung, id")],
        "beitraege": [
            {"gruppe": r["gruppe"], "kurz": r["kurz"], "monat": r["monat"], "jahr": r["jahr"],
             "aktiv": bool(r["aktiv"])}
            for r in conn.execute("SELECT * FROM beitraege ORDER BY sortierung, id")],
        "sponsoren": [
            {"name": r["name"], "logo": r["logo"], "url": r["url"]}
            for r in conn.execute("SELECT * FROM sponsoren ORDER BY sortierung, id")],
        "news": [
            {"titel": r["titel"], "datum": r["datum"], "kategorie": r["kategorie"], "text": r["text"]}
            for r in conn.execute("SELECT * FROM news ORDER BY datum DESC, id DESC")],
        "termine": [
            {"titel": r["titel"], "datum": r["datum"], "zeit": r["zeit"],
             "ort": r["ort"], "text": r["text"]}
            for r in conn.execute("SELECT * FROM termine ORDER BY sortierung, id")],
        "spielplaene": [
            {"name": r["name"], "quelle": r["quelle"], "url": r["url"]}
            for r in conn.execute("SELECT * FROM spielplaene ORDER BY sortierung, id")],
        "dokumente": [
            {"bereich": r["bereich"], "titel": r["titel"], "beschreibung": r["beschreibung"],
             "datei": r["datei"], "url": r["url"]}
            for r in conn.execute("SELECT * FROM dokumente ORDER BY bereich, sortierung, id")],
    }

    zeiten = {}
    for r in conn.execute("SELECT * FROM zeiten ORDER BY sortierung, id"):
        zeiten.setdefault(r["angebot_id"], []).append(
            {"tag": r["tag"], "von": r["von"], "bis": r["bis"], "ort": r["ort"],
             "gruppe": r["gruppe"], "leitung": r["leitung"], "hinweis": r["hinweis"]})

    zg_zu = {}
    for r in conn.execute("SELECT * FROM angebot_zielgruppen"):
        zg_zu.setdefault(r["angebot_id"], []).append(r["zielgruppe_id"])

    zg_reihenfolge = [r["id"] for r in conn.execute("SELECT id FROM zielgruppen ORDER BY sortierung, id")]

    angebote = []
    for r in conn.execute("SELECT * FROM angebote ORDER BY sortierung, id"):
        gewaehlt = set(zg_zu.get(r["id"], []))
        angebote.append({
            "slug": r["slug"], "name": r["name"], "kategorie": r["kategorie"],
            "zielgruppen": [z for z in zg_reihenfolge if z in gewaehlt],
            "kurz": r["kurz"], "text": r["text"], "ort": r["ort"],
            "leitung": r["leitung"], "kontakt_email": r["kontakt_email"],
            "kontakt_telefon": r["kontakt_telefon"],
            "zeiten": zeiten.get(r["id"], []),
        })

    A = {
        "quelle": e["quelle"],
        "kategorien": [{"id": r["id"], "name": r["name"]}
                       for r in conn.execute("SELECT * FROM kategorien ORDER BY sortierung, id")],
        "zielgruppen": [{"id": r["id"], "name": r["name"]}
                        for r in conn.execute("SELECT * FROM zielgruppen ORDER BY sortierung, id")],
        "angebote": angebote,
    }
    return V, A


# ---------------------------------------------------------------------------
# JSON: Erstbefuellung und Export
# ---------------------------------------------------------------------------

def aus_json(datenordner=DATA):
    """V und A direkt aus data/*.json lesen – ohne Datenbank.

    Damit laesst sich die Website auch ohne laufenden Server bauen; fehlende
    Felder werden mit den Voreinstellungen aufgefuellt.
    """
    roh = json.loads((pathlib.Path(datenordner) / "verein.json").read_text(encoding="utf-8"))
    A = json.loads((pathlib.Path(datenordner) / "angebote.json").read_text(encoding="utf-8"))

    e = dict(STANDARD)
    for k in ("name", "kurzname", "gegruendet", "claim", "telefon", "telefon_link",
              "telefax", "email", "register", "shop", "beitrag_hinweis"):
        if roh.get(k) not in (None, ""):
            e[k] = str(roh[k])
    for k, v in (roh.get("adresse") or {}).items():
        e[k] = v
    for k, v in (roh.get("social") or {}).items():
        e[k] = v
    for k, v in (roh.get("texte") or {}).items():
        e[k] = v
    e["quelle"] = A.get("quelle", "")

    V = {
        "name": e["name"], "kurzname": e["kurzname"], "gegruendet": e["gegruendet"],
        "claim": e["claim"],
        "adresse": {"strasse": e["strasse"], "plz": e["plz"], "ort": e["ort"]},
        "telefon": e["telefon"], "telefon_link": telefonlink(e["telefon"], e["telefon_link"]),
        "telefax": e["telefax"], "email": e["email"], "register": e["register"],
        "social": {"facebook": e["facebook"], "instagram": e["instagram"]},
        "shop": e["shop"], "beitrag_hinweis": e["beitrag_hinweis"],
        "oeffnungszeiten": e["oeffnungszeiten"],
        "jugendschutz_text": e["jugendschutz_text"],
        "sprachrohr_text": e["sprachrohr_text"], "sprachrohr_bild": e["sprachrohr_bild"],
        "start_titel": e["start_titel"], "start_titel_akzent": e["start_titel_akzent"],
        "start_seitentitel": e["start_seitentitel"], "admin_url": e["admin_url"],
        "start_bild": e["start_bild"], "training_bild": e["training_bild"],
        "hinweisbanner": e["hinweisbanner"],
        "suchmaschinen_sperren": str(e["suchmaschinen_sperren"]) == "1",
        "impressum_hinweis": e["impressum_hinweis"],
        "datenschutz_text": e["datenschutz_text"],
        "datenschutz_hinweis": e["datenschutz_hinweis"],
        "vorstand": [{"name": p["name"], "rolle": p.get("rolle", ""),
                      "email": p.get("email", ""), "paragraf26": bool(p.get("paragraf26"))}
                     for p in roh.get("vorstand", [])],
        "beitraege": [{"gruppe": b["gruppe"], "kurz": b.get("kurz", ""),
                       "monat": b.get("monat", ""), "jahr": b.get("jahr", ""),
                       "aktiv": bool(b.get("aktiv", True))}
                      for b in roh.get("beitraege", [])],
        "sponsoren": [({"name": s, "logo": "", "url": ""} if isinstance(s, str)
                       else {"name": s.get("name", ""), "logo": s.get("logo", ""),
                             "url": s.get("url", "")})
                      for s in roh.get("sponsoren", [])],
        "news": [{"titel": n["titel"], "datum": n.get("datum", ""),
                  "kategorie": n.get("kategorie", ""), "text": n.get("text", "")}
                 for n in roh.get("news", [])],
        "termine": [{"titel": t["titel"], "datum": t.get("datum", ""), "zeit": t.get("zeit", ""),
                     "ort": t.get("ort", ""), "text": t.get("text", "")}
                    for t in roh.get("termine", [])],
        "spielplaene": [{"name": p["name"], "quelle": p.get("quelle", ""), "url": p.get("url", "")}
                        for p in roh.get("spielplaene", [])],
        "dokumente": [{"bereich": d.get("bereich", "satzung"), "titel": d["titel"],
                       "beschreibung": d.get("beschreibung", ""), "datei": d.get("datei", ""),
                       "url": d.get("url", "")}
                      for d in roh.get("dokumente", [])],
    }

    # Zielgruppen immer in der Reihenfolge ihrer Definition ausgeben. Aus der
    # Datenbank kommen sie ohnehin so; ohne diese Angleichung wuerden statisch
    # gebaute und live ausgelieferte Seiten sich unterscheiden.
    zg_reihenfolge = [z["id"] for z in A["zielgruppen"]]
    angebote = []
    for a in A["angebote"]:
        gewaehlt = set(a.get("zielgruppen", []))
        angebote.append({
            "slug": a["slug"], "name": a["name"], "kategorie": a.get("kategorie", ""),
            "zielgruppen": [z for z in zg_reihenfolge if z in gewaehlt],
            "kurz": a.get("kurz", ""),
            "text": a.get("text", ""), "ort": a.get("ort", ""),
            "leitung": a.get("leitung", ""), "kontakt_email": a.get("kontakt_email", ""),
            "kontakt_telefon": a.get("kontakt_telefon", ""),
            "zeiten": [dict(z) for z in a.get("zeiten", [])],
        })
    A = {"quelle": A.get("quelle", ""), "kategorien": A["kategorien"],
         "zielgruppen": A["zielgruppen"], "angebote": angebote}
    return V, A


def ist_leer(conn):
    return conn.execute("SELECT COUNT(*) AS n FROM angebote").fetchone()["n"] == 0 \
        and conn.execute("SELECT COUNT(*) AS n FROM termine").fetchone()["n"] == 0


def befuellen(conn, datenordner=DATA):
    """Datenbank aus data/*.json erstbefuellen."""
    V, A = aus_json(datenordner)

    werte = {
        "name": V["name"], "kurzname": V["kurzname"], "gegruendet": V["gegruendet"],
        "claim": V["claim"], "strasse": V["adresse"]["strasse"], "plz": V["adresse"]["plz"],
        "ort": V["adresse"]["ort"], "telefon": V["telefon"], "telefon_link": V["telefon_link"],
        "telefax": V["telefax"], "email": V["email"], "register": V["register"],
        "facebook": V["social"]["facebook"], "instagram": V["social"]["instagram"],
        "shop": V["shop"], "beitrag_hinweis": V["beitrag_hinweis"], "quelle": A["quelle"],
        "oeffnungszeiten": V["oeffnungszeiten"], "jugendschutz_text": V["jugendschutz_text"],
        "sprachrohr_text": V["sprachrohr_text"], "sprachrohr_bild": V["sprachrohr_bild"],
        "start_titel": V["start_titel"], "start_titel_akzent": V["start_titel_akzent"],
        "start_seitentitel": V["start_seitentitel"], "admin_url": V["admin_url"],
        "start_bild": V["start_bild"], "training_bild": V["training_bild"],
        "hinweisbanner": V["hinweisbanner"],
        "suchmaschinen_sperren": "1" if V["suchmaschinen_sperren"] else "0",
        "impressum_hinweis": V["impressum_hinweis"],
        "datenschutz_text": V["datenschutz_text"],
        "datenschutz_hinweis": V["datenschutz_hinweis"],
    }
    for k, v in werte.items():
        setze(conn, k, v)

    for i, p in enumerate(V["vorstand"]):
        conn.execute("INSERT INTO vorstand (name, rolle, email, paragraf26, sortierung) "
                     "VALUES (?, ?, ?, ?, ?)",
                     (p["name"], p["rolle"], p["email"], int(p["paragraf26"]), i))
    for i, b in enumerate(V["beitraege"]):
        conn.execute("INSERT INTO beitraege (gruppe, kurz, monat, jahr, aktiv, sortierung) "
                     "VALUES (?, ?, ?, ?, ?, ?)",
                     (b["gruppe"], b["kurz"], b["monat"], b["jahr"], int(b["aktiv"]), i))
    for i, t in enumerate(V["termine"]):
        conn.execute("INSERT INTO termine (titel, datum, zeit, ort, text, sortierung) "
                     "VALUES (?, ?, ?, ?, ?, ?)",
                     (t["titel"], t["datum"], t["zeit"], t["ort"], t["text"], i))
    for i, n in enumerate(V["news"]):
        conn.execute("INSERT INTO news (titel, datum, kategorie, text, sortierung) "
                     "VALUES (?, ?, ?, ?, ?)", (n["titel"], n["datum"], n["kategorie"], n["text"], i))
    for i, s in enumerate(V["sponsoren"]):
        conn.execute("INSERT INTO sponsoren (name, logo, url, sortierung) VALUES (?, ?, ?, ?)",
                     (s["name"], s["logo"], s["url"], i))
    for i, p in enumerate(V["spielplaene"]):
        conn.execute("INSERT INTO spielplaene (name, quelle, url, sortierung) VALUES (?, ?, ?, ?)",
                     (p["name"], p["quelle"], p["url"], i))
    for i, d in enumerate(V["dokumente"]):
        conn.execute("INSERT INTO dokumente (bereich, titel, beschreibung, datei, url, sortierung) "
                     "VALUES (?, ?, ?, ?, ?, ?)",
                     (d["bereich"], d["titel"], d["beschreibung"], d["datei"], d["url"], i))
    for i, k in enumerate(A["kategorien"]):
        conn.execute("INSERT OR REPLACE INTO kategorien (id, name, sortierung) VALUES (?, ?, ?)",
                     (k["id"], k["name"], i))
    for i, z in enumerate(A["zielgruppen"]):
        conn.execute("INSERT OR REPLACE INTO zielgruppen (id, name, sortierung) VALUES (?, ?, ?)",
                     (z["id"], z["name"], i))
    for i, a in enumerate(A["angebote"]):
        cur = conn.execute(
            "INSERT INTO angebote (slug, name, kategorie, kurz, text, ort, leitung, "
            "kontakt_email, kontakt_telefon, sortierung) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (a["slug"], a["name"], a["kategorie"], a["kurz"], a["text"], a["ort"],
             a["leitung"], a["kontakt_email"], a["kontakt_telefon"], i))
        aid = cur.lastrowid
        for z in a["zielgruppen"]:
            conn.execute("INSERT OR IGNORE INTO angebot_zielgruppen (angebot_id, zielgruppe_id) "
                         "VALUES (?, ?)", (aid, z))
        for j, z in enumerate(a["zeiten"]):
            conn.execute("INSERT INTO zeiten (angebot_id, tag, von, bis, ort, gruppe, leitung, "
                         "hinweis, sortierung) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (aid, z.get("tag", ""), z.get("von", ""), z.get("bis", ""),
                          z.get("ort", ""), z.get("gruppe", ""), z.get("leitung", ""),
                          z.get("hinweis", ""), j))
    markiere_aenderung(conn)
    conn.commit()


def nach_json(conn, datenordner=DATA):
    """Datenbankinhalt zurueck nach data/*.json schreiben.

    So bleibt der Stand auch ohne Datenbank baubar und ist im Git nachvollziehbar.
    """
    V, A = lade_daten(conn)
    verein = {
        "name": V["name"], "kurzname": V["kurzname"],
        "gegruendet": int(V["gegruendet"]) if str(V["gegruendet"]).isdigit() else V["gegruendet"],
        "claim": V["claim"], "adresse": V["adresse"], "telefon": V["telefon"],
        "telefon_link": V["telefon_link"], "telefax": V["telefax"], "email": V["email"],
        "register": V["register"], "social": V["social"], "shop": V["shop"],
        "texte": {
            "oeffnungszeiten": V["oeffnungszeiten"], "jugendschutz_text": V["jugendschutz_text"],
            "sprachrohr_text": V["sprachrohr_text"], "sprachrohr_bild": V["sprachrohr_bild"],
            "start_titel": V["start_titel"], "start_titel_akzent": V["start_titel_akzent"],
            "start_seitentitel": V["start_seitentitel"], "admin_url": V["admin_url"],
            "start_bild": V["start_bild"], "training_bild": V["training_bild"],
            "hinweisbanner": V["hinweisbanner"],
            "suchmaschinen_sperren": "1" if V["suchmaschinen_sperren"] else "0",
            "impressum_hinweis": V["impressum_hinweis"],
            "datenschutz_text": V["datenschutz_text"],
            "datenschutz_hinweis": V["datenschutz_hinweis"],
        },
        "vorstand": V["vorstand"], "beitraege": V["beitraege"],
        "beitrag_hinweis": V["beitrag_hinweis"], "sponsoren": V["sponsoren"],
        "news": V["news"], "termine": V["termine"], "spielplaene": V["spielplaene"],
        "dokumente": V["dokumente"],
    }
    ordner = pathlib.Path(datenordner)
    (ordner / "verein.json").write_text(
        json.dumps(verein, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ordner / "angebote.json").write_text(
        json.dumps(A, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
