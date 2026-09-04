#!/usr/bin/env python3
"""Die vorhandenen Inhalte aus data/*.json einmalig ins Sanity-CMS schreiben.

Damit muss niemand die 36 Sportangebote samt Trainingszeiten von Hand
abtippen. Jedes Dokument bekommt einen festen Schluessel (etwa
``angebot.fussball``); ein zweiter Lauf legt deshalb nichts doppelt an.

    export SANITY_PROJEKT=… SANITY_TOKEN=…      Token mit Schreibrecht
    python3 tools/nach_sanity.py --probe        nur zeigen, was passieren wuerde
    python3 tools/nach_sanity.py                fehlende Dokumente anlegen
    python3 tools/nach_sanity.py --ersetzen     vorhandene ueberschreiben

``--ersetzen`` verwirft Aenderungen, die im CMS gemacht wurden. Ohne die
Option bleiben vorhandene Dokumente unangetastet.
"""

import argparse
import json
import pathlib
import re
import sys
import unicodedata
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import inhalte, sanity          # noqa: E402

# Sanity nimmt bis zu einigen hundert Mutationen je Anfrage; kleinere Pakete
# machen Fehlermeldungen leichter zuzuordnen.
PAKETGROESSE = 50


def schluessel(text):
    text = (text or "").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower() or "eintrag"


def _slug(wert):
    return {"_type": "slug", "current": wert}


def _verweis(kennung):
    return {"_type": "reference", "_ref": kennung}


def dokumente_bauen(V, A):
    """Aus V und A die Sanity-Dokumente erzeugen."""
    docs = []

    docs.append({
        "_id": "verein",
        "_type": "verein",
        "name": V["name"],
        "kurzname": V["kurzname"],
        "gegruendet": int(V["gegruendet"]) if str(V["gegruendet"]).isdigit() else None,
        "claim": V["claim"],
        "adresse": {
            "_type": "object",
            "strasse": V["adresse"]["strasse"],
            "plz": V["adresse"]["plz"],
            "ort": V["adresse"]["ort"],
        },
        "telefon": V["telefon"],
        "telefonLink": "",
        "telefax": V["telefax"],
        "email": V["email"],
        "register": V["register"],
        "oeffnungszeiten": V["oeffnungszeiten"],
        "beitragHinweis": V["beitrag_hinweis"],
        "shop": V["shop"] or None,
        "facebook": V["social"]["facebook"] or None,
        "instagram": V["social"]["instagram"] or None,
    })

    docs.append({
        "_id": "texte",
        "_type": "texte",
        "startTitel": V["start_titel"],
        "startTitelAkzent": V["start_titel_akzent"],
        "startSeitentitel": V["start_seitentitel"],
        "sprachrohrText": V["sprachrohr_text"],
        "jugendschutzText": V["jugendschutz_text"],
        "quelle": A.get("quelle", ""),
        "hinweisbanner": V["hinweisbanner"],
        "suchmaschinenSperren": bool(V["suchmaschinen_sperren"]),
        "impressumHinweis": V["impressum_hinweis"],
        "datenschutzText": V["datenschutz_text"],
        "datenschutzHinweis": V["datenschutz_hinweis"],
    })

    for i, k in enumerate(A["kategorien"]):
        docs.append({"_id": "kategorie.%s" % k["id"], "_type": "kategorie",
                     "name": k["name"], "kennung": _slug(k["id"]), "sortierung": i})
    for i, z in enumerate(A["zielgruppen"]):
        docs.append({"_id": "zielgruppe.%s" % z["id"], "_type": "zielgruppe",
                     "name": z["name"], "kennung": _slug(z["id"]), "sortierung": i})

    for i, a in enumerate(A["angebote"]):
        zeiten = []
        for j, z in enumerate(a["zeiten"]):
            zeiten.append({
                "_type": "trainingszeit",
                "_key": "%s-%d" % (a["slug"], j),
                "tag": z.get("tag") or "Montag",
                "von": z.get("von") or "",
                "bis": z.get("bis") or "",
                "gruppe": z.get("gruppe") or "",
                "ort": z.get("ort") or "",
                "leitung": z.get("leitung") or "",
                "hinweis": z.get("hinweis") or "",
            })
        docs.append({
            "_id": "angebot.%s" % a["slug"],
            "_type": "angebot",
            "name": a["name"],
            "slug": _slug(a["slug"]),
            "kategorie": _verweis("kategorie.%s" % a["kategorie"]) if a["kategorie"] else None,
            "zielgruppen": [dict(_verweis("zielgruppe.%s" % z), _key=z)
                            for z in a["zielgruppen"]],
            "kurz": a["kurz"],
            "text": a["text"],
            "ort": a["ort"],
            "leitung": a.get("leitung", ""),
            "kontaktEmail": a.get("kontakt_email") or None,
            "kontaktTelefon": a.get("kontakt_telefon", ""),
            "zeiten": zeiten,
            "sortierung": i,
        })

    for i, p in enumerate(V["vorstand"]):
        docs.append({"_id": "vorstand.%s" % schluessel(p["name"]), "_type": "vorstandsmitglied",
                     "name": p["name"], "rolle": p["rolle"],
                     "email": p.get("email") or None,
                     "paragraf26": bool(p["paragraf26"]), "sortierung": i})

    for i, b in enumerate(V["beitraege"]):
        docs.append({"_id": "beitrag.%s" % schluessel(b["gruppe"])[:40], "_type": "beitrag",
                     "gruppe": b["gruppe"], "kurz": b.get("kurz", ""),
                     "monat": b["monat"], "jahr": b["jahr"],
                     "aktiv": bool(b.get("aktiv", True)), "sortierung": i})

    for i, t in enumerate(V["termine"]):
        docs.append({"_id": "termin.%s" % schluessel(t["titel"])[:40], "_type": "termin",
                     "titel": t["titel"], "datum": t["datum"] or None, "zeit": t["zeit"],
                     "ort": t["ort"], "text": t["text"], "sortierung": i})

    for i, n in enumerate(V["news"]):
        docs.append({"_id": "news.%s" % schluessel(n["titel"])[:40], "_type": "news",
                     "titel": n["titel"], "datum": n["datum"] or None,
                     "kategorie": n["kategorie"], "text": n["text"]})

    for i, a in enumerate(V["aktionen"]):
        docs.append({"_id": "aktion.%s" % schluessel(a["titel"])[:40], "_type": "aktion",
                     "titel": a["titel"], "aktiv": bool(a.get("aktiv", True)),
                     "kurz": a.get("kurz", ""), "datum": a.get("datum") or None,
                     "datumBis": a.get("datum_bis") or None,
                     "zeit": a.get("zeit", ""), "ort": a.get("ort", ""),
                     "text": a.get("text", ""),
                     "anmeldelink": a.get("anmeldelink") or None,
                     "anmeldetext": a.get("anmeldetext", ""), "sortierung": i})

    for i, s in enumerate(V["sponsoren"]):
        docs.append({"_id": "sponsor.%s" % schluessel(s["name"])[:40], "_type": "sponsor",
                     "name": s["name"], "url": s.get("url") or None, "sortierung": i})

    for i, p in enumerate(V["spielplaene"]):
        docs.append({"_id": "spielplan.%s" % schluessel(p["name"]), "_type": "spielplan",
                     "name": p["name"], "quelle": p["quelle"],
                     "url": p.get("url") or None, "sortierung": i})

    for i, d in enumerate(V["dokumente"]):
        docs.append({"_id": "dokument.%s" % schluessel(d["titel"])[:40], "_type": "dokument",
                     "bereich": d["bereich"], "titel": d["titel"],
                     "beschreibung": d["beschreibung"], "url": d.get("url") or None,
                     "sortierung": i})

    # Felder ohne Wert gar nicht erst senden.
    return [{k: v for k, v in doc.items() if v is not None} for doc in docs]


def senden(projekt, datensatz, token, mutationen, oeffnen=None):
    adresse = "https://%s.api.sanity.io/v%s/data/mutate/%s?returnIds=true" % (
        projekt, sanity.API_FASSUNG, datensatz)
    daten = json.dumps({"mutations": mutationen}).encode("utf-8")
    kopfzeilen = {"Content-Type": "application/json",
                  "Authorization": "Bearer %s" % token}
    if oeffnen is not None:
        with oeffnen(adresse, daten, kopfzeilen) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    anfrage = urllib.request.Request(adresse, data=daten, headers=kopfzeilen, method="POST")
    try:
        with urllib.request.urlopen(anfrage, timeout=sanity.ZEITLIMIT) as antwort:
            return json.loads(antwort.read().decode("utf-8"))
    except urllib.error.HTTPError as fehler:
        rumpf = fehler.read().decode("utf-8", "replace")[:500]
        hinweis = ""
        if fehler.code in (401, 403):
            hinweis = (" Der Token braucht Schreibrecht — in Sanity unter "
                       "API → Tokens einen mit der Rolle „Editor“ anlegen.")
        raise SystemExit("Sanity antwortete mit %s: %s%s" % (fehler.code, rumpf, hinweis))
    except urllib.error.URLError as fehler:
        raise SystemExit("Sanity war nicht erreichbar: %s" % fehler.reason)


def main():
    ap = argparse.ArgumentParser(description="data/*.json ins Sanity-CMS übertragen")
    ap.add_argument("--ersetzen", action="store_true",
                    help="vorhandene Dokumente überschreiben (verwirft Änderungen im CMS)")
    ap.add_argument("--probe", action="store_true",
                    help="nur anzeigen, was übertragen würde")
    args = ap.parse_args()

    zugang = sanity.einstellungen()
    if not zugang["projekt"]:
        raise SystemExit("SANITY_PROJEKT ist nicht gesetzt.")
    if not args.probe and not zugang["token"]:
        raise SystemExit("SANITY_TOKEN ist nicht gesetzt (Schreibrecht nötig).")

    V, A = inhalte.aus_json()
    docs = dokumente_bauen(V, A)
    art = "createOrReplace" if args.ersetzen else "createIfNotExists"

    nach_typ = {}
    for d in docs:
        nach_typ[d["_type"]] = nach_typ.get(d["_type"], 0) + 1
    print("Zu übertragen (%s):" % ("ersetzend" if args.ersetzen else "nur fehlende"))
    for typ, anzahl in sorted(nach_typ.items()):
        print("  %-20s %3d" % (typ, anzahl))

    if args.probe:
        print("\nProbelauf — es wurde nichts gesendet.")
        return

    mutationen = [{art: d} for d in docs]
    gesendet = 0
    for i in range(0, len(mutationen), PAKETGROESSE):
        paket = mutationen[i:i + PAKETGROESSE]
        senden(zugang["projekt"], zugang["datensatz"], zugang["token"], paket)
        gesendet += len(paket)
        print("  %d/%d übertragen" % (gesendet, len(mutationen)))

    print("\nFertig. Das Studio zeigt die Inhalte jetzt an.")


if __name__ == "__main__":
    main()
