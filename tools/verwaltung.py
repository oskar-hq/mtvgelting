#!/usr/bin/env python3
"""Wartungsbefehle für die Vereinsdatenbank.

    python3 tools/verwaltung.py einrichten          Datenbank anlegen und aus data/ füllen
    python3 tools/verwaltung.py zugang-anlegen      Anmeldung für eine Person anlegen
    python3 tools/verwaltung.py passwort-setzen     Passwort einer Person neu setzen
    python3 tools/verwaltung.py zugaenge            vorhandene Anmeldungen auflisten
    python3 tools/verwaltung.py nach-json           Datenbankstand nach data/*.json schreiben

Der Pfad zur Datenbank lässt sich mit --datenbank oder über die Umgebungs-
variable MTV_DATENBANK ändern.
"""

import argparse
import getpass
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app import auth
from app import db as datenbank

ROOT = pathlib.Path(__file__).resolve().parent.parent
STANDARD_DB = os.environ.get("MTV_DATENBANK", str(ROOT / "verein.db"))


def oeffne(pfad):
    conn = datenbank.verbinde(pfad)
    datenbank.anlegen(conn)
    return conn


def passwort_abfragen():
    while True:
        eins = getpass.getpass("Passwort: ")
        fehler = auth.passwort_pruefregel(eins)
        if fehler:
            print("  " + fehler)
            continue
        if eins != getpass.getpass("Passwort wiederholen: "):
            print("  Die Passwörter stimmen nicht überein.")
            continue
        return eins


def befehl_einrichten(args):
    conn = oeffne(args.datenbank)
    if datenbank.ist_leer(conn):
        datenbank.befuellen(conn)
        print("Datenbank %s angelegt und aus data/*.json gefüllt." % args.datenbank)
    else:
        print("Datenbank %s ist bereits gefüllt — Inhalte bleiben unangetastet." % args.datenbank)
    if auth.anzahl_benutzer(conn) == 0:
        print("Es gibt noch keinen Zugang. Lege jetzt den ersten an "
              "(oder später im Browser unter /admin/einrichten).")
        email = input("E-Mail-Adresse (leer = überspringen): ").strip()
        if email:
            name = input("Name: ").strip()
            auth.benutzer_anlegen(conn, email, name, passwort_abfragen())
            print("Zugang für %s angelegt." % email)
    conn.close()


def befehl_zugang_anlegen(args):
    conn = oeffne(args.datenbank)
    email = args.email or input("E-Mail-Adresse: ").strip()
    if auth.benutzer_nach_email(conn, email) is not None:
        raise SystemExit("Für %s gibt es bereits einen Zugang." % email)
    name = args.name if args.name is not None else input("Name: ").strip()
    auth.benutzer_anlegen(conn, email, name, passwort_abfragen())
    print("Zugang für %s angelegt." % email)
    conn.close()


def befehl_passwort_setzen(args):
    conn = oeffne(args.datenbank)
    email = args.email or input("E-Mail-Adresse: ").strip()
    zeile = auth.benutzer_nach_email(conn, email)
    if zeile is None:
        raise SystemExit("Kein Zugang für %s gefunden." % email)
    conn.execute("UPDATE admins SET passwort = ? WHERE id = ?",
                 (auth.hash_passwort(passwort_abfragen()), zeile["id"]))
    conn.commit()
    print("Passwort für %s neu gesetzt." % email)
    conn.close()


def befehl_zugaenge(args):
    conn = oeffne(args.datenbank)
    zeilen = conn.execute("SELECT email, name, letzter_login FROM admins ORDER BY email").fetchall()
    if not zeilen:
        print("Noch keine Zugänge.")
    for z in zeilen:
        print("  %-38s %-22s zuletzt: %s"
              % (z["email"], z["name"] or "—", (z["letzter_login"] or "nie")[:10]))
    conn.close()


def befehl_nach_json(args):
    conn = oeffne(args.datenbank)
    datenbank.nach_json(conn)
    print("data/verein.json und data/angebote.json aus der Datenbank geschrieben.")
    conn.close()


def main():
    ap = argparse.ArgumentParser(description="Wartung der Vereinsdatenbank")
    ap.add_argument("--datenbank", default=STANDARD_DB, help="Pfad zur Datenbankdatei")
    unter = ap.add_subparsers(dest="befehl", required=True)

    unter.add_parser("einrichten", help="Datenbank anlegen und aus data/ füllen") \
        .set_defaults(funktion=befehl_einrichten)

    p = unter.add_parser("zugang-anlegen", help="Anmeldung für eine Person anlegen")
    p.add_argument("--email")
    p.add_argument("--name")
    p.set_defaults(funktion=befehl_zugang_anlegen)

    p = unter.add_parser("passwort-setzen", help="Passwort einer Person neu setzen")
    p.add_argument("--email")
    p.set_defaults(funktion=befehl_passwort_setzen)

    unter.add_parser("zugaenge", help="vorhandene Anmeldungen auflisten") \
        .set_defaults(funktion=befehl_zugaenge)

    unter.add_parser("nach-json", help="Datenbankstand nach data/*.json schreiben") \
        .set_defaults(funktion=befehl_nach_json)

    args = ap.parse_args()
    args.funktion(args)


if __name__ == "__main__":
    main()
