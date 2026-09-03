#!/usr/bin/env python3
"""Erzeugt die statischen Seiten fuer GitHub Pages.

Ohne Argumente wird aus den Dateien in ``data/`` gebaut — so laeuft der Build
auch in der CI, wo keine Datenbank liegt. Mit ``--db`` kommen die Inhalte aus
der Vereinsdatenbank; ``--json`` schreibt den Datenbankstand zusaetzlich nach
``data/`` zurueck, damit beide Quellen zusammenpassen.

    python3 tools/build.py                 aus data/*.json bauen
    python3 tools/build.py --db --json     aus der Datenbank bauen und data/ auffrischen
"""

import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import db as datenbank
from app.render import Renderer

ROOT = pathlib.Path(__file__).resolve().parent.parent


def schreibe(ziel, seiten):
    ziel = pathlib.Path(ziel)
    ziel.mkdir(parents=True, exist_ok=True)
    for name, inhalt in seiten.items():
        (ziel / name).write_text(inhalt, encoding="utf-8")
        print("  ->", name)
    (ziel / ".nojekyll").write_text("", encoding="utf-8")


def daten(aus_db, dbpfad, json_zurueck):
    if not aus_db:
        return datenbank.aus_json()
    if not pathlib.Path(dbpfad).exists():
        raise SystemExit("Keine Datenbank unter %s. Erst 'python3 tools/verwaltung.py einrichten' "
                         "ausfuehren oder ohne --db bauen." % dbpfad)
    conn = datenbank.verbinde(dbpfad)
    datenbank.anlegen(conn)
    if json_zurueck:
        datenbank.nach_json(conn)
        print("  -> data/verein.json, data/angebote.json")
    V, A = datenbank.lade_daten(conn)
    conn.close()
    return V, A


def main():
    ap = argparse.ArgumentParser(description="Statische Seiten erzeugen")
    ap.add_argument("--db", action="store_true", help="Inhalte aus der Datenbank statt aus data/")
    ap.add_argument("--dbpfad", default=str(ROOT / "verein.db"), help="Pfad zur Datenbankdatei")
    ap.add_argument("--json", action="store_true", help="Datenbankstand nach data/ zurueckschreiben")
    ap.add_argument("--ziel", default=str(ROOT), help="Ausgabeordner")
    args = ap.parse_args()

    print("Baue Seiten …")
    V, A = daten(args.db, args.dbpfad, args.json)
    schreibe(args.ziel, Renderer(V, A).pages())
    print("Fertig: %d Angebote, %d Kategorien." % (len(A["angebote"]), len(A["kategorien"])))


if __name__ == "__main__":
    main()
