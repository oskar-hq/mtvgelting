#!/usr/bin/env python3
"""Inhalte laden und in die Form bringen, die der Generator erwartet.

Der Generator (``tools/render.py``) bekommt zwei Dictionaries: ``V`` mit den
Vereinsdaten und ``A`` mit den Sportangeboten. Woher die Inhalte stammen, ist
ihm gleich — im Normalfall aus dem CMS (``tools/sanity.py``), ersatzweise aus
den JSON-Dateien in ``data/``.
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


# Voreinstellungen aller freien Textfelder. Was im CMS leer bleibt oder dort
# gar nicht gepflegt wird, faellt auf diese Werte zurueck.
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
    "start_bild": "",
    "training_bild": "",
    "hinweisbanner": "",
    "suchmaschinen_sperren": "1",
    "impressum_hinweis": "",
    "datenschutz_text": "",
    "datenschutz_hinweis": "",
}


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
        "start_seitentitel": e["start_seitentitel"],
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
        # Neueste zuerst — dieselbe Reihenfolge, die auch das CMS liefert.
        "news": sorted(
            [{"titel": n["titel"], "datum": n.get("datum", ""),
              "kategorie": n.get("kategorie", ""), "text": n.get("text", "")}
             for n in roh.get("news", [])],
            key=lambda n: n["datum"], reverse=True),
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


def nach_json(V, A, datenordner=DATA):
    """V und A als data/*.json ablegen.

    Damit liegt im Repository immer eine lesbare Sicherung dessen, was zuletzt
    im CMS stand — und die Seiten lassen sich auch ohne CMS bauen.
    """
    verein = {
        "name": V["name"], "kurzname": V["kurzname"],
        "gegruendet": int(V["gegruendet"]) if str(V["gegruendet"]).isdigit() else V["gegruendet"],
        "claim": V["claim"], "adresse": V["adresse"], "telefon": V["telefon"],
        "telefon_link": V["telefon_link"], "telefax": V["telefax"], "email": V["email"],
        "register": V["register"], "social": V["social"], "shop": V["shop"],
        "texte": {
            "start_titel": V["start_titel"], "start_titel_akzent": V["start_titel_akzent"],
            "start_seitentitel": V["start_seitentitel"], "start_bild": V["start_bild"],
            "training_bild": V["training_bild"], "oeffnungszeiten": V["oeffnungszeiten"],
            "jugendschutz_text": V["jugendschutz_text"],
            "sprachrohr_text": V["sprachrohr_text"], "sprachrohr_bild": V["sprachrohr_bild"],
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
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / "verein.json").write_text(
        json.dumps(verein, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ordner / "angebote.json").write_text(
        json.dumps(A, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
