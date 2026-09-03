#!/usr/bin/env python3
"""Erzeugt die statischen Seiten der Website.

Die Inhalte kommen normalerweise aus dem Sanity-CMS. Ist kein Projekt
hinterlegt, wird aus den Dateien in ``data/`` gebaut — so laesst sich die Seite
auch ohne CMS-Zugang erzeugen und pruefen.

    python3 tools/build.py                     Quelle automatisch waehlen
    python3 tools/build.py --quelle dateien    ausdruecklich aus data/*.json
    python3 tools/build.py --quelle cms        ausdruecklich aus dem CMS
    python3 tools/build.py --sichern           CMS-Stand zusaetzlich nach data/ schreiben

Zugangsdaten kommen aus der Umgebung: SANITY_PROJEKT, SANITY_DATENSATZ
(Vorgabe „production“) und SANITY_TOKEN (nur bei nicht oeffentlichen Daten).
"""

import argparse
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import inhalte, sanity           # noqa: E402
from tools.render import Renderer           # noqa: E402


def quelle_waehlen(gewaehlt, projekt):
    if gewaehlt == "auto":
        return "cms" if projekt else "dateien"
    return gewaehlt


def inhalte_holen(quelle, ziel, zugang):
    if quelle == "dateien":
        print("Quelle: data/*.json")
        return inhalte.aus_json()
    if not zugang["projekt"]:
        raise SystemExit(
            "Für --quelle cms muss SANITY_PROJEKT gesetzt sein "
            "(die Projekt-ID steht in der Sanity-Verwaltung unter „Project ID“).")
    print("Quelle: Sanity-Projekt %s, Datensatz %s" % (zugang["projekt"], zugang["datensatz"]))
    medien = sanity.Medien(ziel)
    V, A = sanity.laden(ziel, zugang["projekt"], zugang["datensatz"], zugang["token"],
                        medien=medien)
    if medien.geholt:
        print("  %d Bilder und Dateien übernommen" % len(medien.geholt))
    return V, A


def assets_kopieren(ziel):
    """CSS, Schriften, Bilder in den Ausgabeordner bringen.

    Wird nur gebraucht, wenn woanders hin gebaut wird als ins Projekt selbst —
    etwa in der CI, wo nur der Ausgabeordner veroeffentlicht wird und nicht der
    Quellcode.
    """
    ziel = pathlib.Path(ziel)
    if ziel.resolve() == ROOT:
        return
    shutil.copytree(ROOT / "assets", ziel / "assets", dirs_exist_ok=True)
    print("  -> assets/")


def schreiben(ziel, seiten):
    ziel = pathlib.Path(ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    for name, seite in seiten.items():
        (ziel / name).write_text(seite, encoding="utf-8")
        print("  ->", name)
    (ziel / ".nojekyll").write_text("", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Statische Seiten erzeugen")
    ap.add_argument("--quelle", choices=["auto", "cms", "dateien"], default="auto",
                    help="woher die Inhalte kommen (Vorgabe: CMS, falls eingerichtet)")
    ap.add_argument("--sichern", action="store_true",
                    help="die geholten Inhalte zusätzlich nach data/*.json schreiben")
    ap.add_argument("--ziel", default=str(ROOT), help="Ausgabeordner")
    args = ap.parse_args()

    zugang = sanity.einstellungen()
    quelle = quelle_waehlen(args.quelle, zugang["projekt"])

    print("Baue Seiten …")
    # Zuerst die mitgelieferten Dateien, dann die aus dem CMS geholten — so
    # ueberschreibt das Kopieren nichts Frischgeladenes.
    assets_kopieren(args.ziel)
    V, A = inhalte_holen(quelle, args.ziel, zugang)

    if args.sichern:
        inhalte.nach_json(V, A)
        print("  -> data/verein.json, data/angebote.json")

    schreiben(args.ziel, Renderer(V, A).pages())
    print("Fertig: %d Angebote, %d Kategorien." % (len(A["angebote"]), len(A["kategorien"])))


if __name__ == "__main__":
    main()
