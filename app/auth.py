"""Anmeldung fuer den Vereinsbereich.

Passwoerter werden mit scrypt aus der Python-Standardbibliothek gehasht — es
wird also keine zusaetzliche Bibliothek gebraucht. Gespeichert wird
``scrypt$n$r$p$salt$hash``; alte Hashes bleiben damit lesbar, wenn die
Parameter spaeter erhoeht werden.
"""

import hashlib
import hmac
import os
import secrets
import time

from flask import (Blueprint, current_app, flash, g, redirect, render_template,
                   request, session, url_for)

from . import db as datenbank

# Kostenparameter: rund 100 ms je Pruefung auf einem kleinen Server.
SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1


def _speicher(n, r, p):
    """OpenSSL bricht ohne ausdrueckliches Limit bei 32 MB ab.

    scrypt braucht rund ``128 * n * r`` Bytes; mit etwas Luft nach oben
    laeuft es auch, wenn die Parameter spaeter erhoeht werden.
    """
    return int(128 * n * r * p * 1.4) + 1024 * 1024

# Nach so vielen Fehlversuchen in Folge wird die Anmeldung kurz gesperrt.
MAX_VERSUCHE = 5
SPERRE_SEKUNDEN = 300

_versuche = {}

bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------------------
# Passwoerter
# ---------------------------------------------------------------------------

def hash_passwort(passwort, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P):
    salz = os.urandom(16)
    roh = hashlib.scrypt(passwort.encode("utf-8"), salt=salz, n=n, r=r, p=p, dklen=32,
                         maxmem=_speicher(n, r, p))
    return "scrypt$%d$%d$%d$%s$%s" % (n, r, p, salz.hex(), roh.hex())


def pruefe_passwort(gespeichert, passwort):
    try:
        art, n, r, p, salz, roh = gespeichert.split("$")
        if art != "scrypt":
            return False
        n, r, p = int(n), int(r), int(p)
        neu = hashlib.scrypt(passwort.encode("utf-8"), salt=bytes.fromhex(salz),
                             n=n, r=r, p=p, dklen=len(bytes.fromhex(roh)),
                             maxmem=_speicher(n, r, p))
        return hmac.compare_digest(neu, bytes.fromhex(roh))
    except (ValueError, TypeError):
        return False


def passwort_pruefregel(passwort):
    """Mindestanforderung; gibt eine Fehlermeldung zurueck oder None."""
    if len(passwort) < 10:
        return "Das Passwort muss mindestens 10 Zeichen lang sein."
    return None


# ---------------------------------------------------------------------------
# Benutzer
# ---------------------------------------------------------------------------

def benutzer_anlegen(conn, email, name, passwort):
    conn.execute("INSERT INTO admins (email, name, passwort, angelegt) VALUES (?, ?, ?, ?)",
                 (email.strip().lower(), name.strip(), hash_passwort(passwort), datenbank.jetzt()))
    conn.commit()


def benutzer_nach_email(conn, email):
    return conn.execute("SELECT * FROM admins WHERE email = ?", (email.strip().lower(),)).fetchone()


def anzahl_benutzer(conn):
    return conn.execute("SELECT COUNT(*) AS n FROM admins").fetchone()["n"]


# ---------------------------------------------------------------------------
# Fehlversuche bremsen
# ---------------------------------------------------------------------------

def _schluessel(email):
    return "%s|%s" % (request.remote_addr or "?", email.strip().lower())


def gesperrt_bis(email):
    eintrag = _versuche.get(_schluessel(email))
    if not eintrag:
        return 0
    anzahl, letzter = eintrag
    if anzahl < MAX_VERSUCHE:
        return 0
    frei = letzter + SPERRE_SEKUNDEN
    return frei if frei > time.time() else 0


def merke_fehlversuch(email):
    k = _schluessel(email)
    anzahl, _ = _versuche.get(k, (0, 0))
    _versuche[k] = (anzahl + 1, time.time())


def loesche_fehlversuche(email):
    _versuche.pop(_schluessel(email), None)


# ---------------------------------------------------------------------------
# Sitzung
# ---------------------------------------------------------------------------

def angemeldet():
    return session.get("admin_id") is not None


def lade_benutzer():
    """Wird vor jeder Anfrage aufgerufen und legt g.benutzer ab."""
    g.benutzer = None
    aid = session.get("admin_id")
    if aid is None:
        return
    zeile = current_app.datenbank().execute("SELECT * FROM admins WHERE id = ?", (aid,)).fetchone()
    if zeile is None:
        session.clear()
        return
    g.benutzer = zeile


def gewuenschtes_ziel():
    """Adresse, zu der nach der Anmeldung zurueckgesprungen wird."""
    ziel = request.full_path
    return ziel[:-1] if ziel.endswith("?") else ziel


# ---------------------------------------------------------------------------
# Schutz vor fremden Formularen (CSRF)
# ---------------------------------------------------------------------------

def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


def csrf_pruefen():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return True
    gesendet = request.form.get("csrf") or request.headers.get("X-CSRF-Token") or ""
    return bool(session.get("csrf")) and hmac.compare_digest(gesendet, session["csrf"])


# ---------------------------------------------------------------------------
# Ansichten
# ---------------------------------------------------------------------------

def _sicheres_ziel(weiter):
    """Nur Weiterleitungen innerhalb der eigenen Seite zulassen."""
    if weiter and weiter.startswith("/") and not weiter.startswith("//"):
        return weiter
    return url_for("admin.uebersicht")


@bp.route("/login", methods=["GET", "POST"])
def login():
    conn = current_app.datenbank()
    if anzahl_benutzer(conn) == 0:
        return redirect(url_for("auth.einrichten"))
    if g.get("benutzer") is not None:
        return redirect(url_for("admin.uebersicht"))

    weiter = request.args.get("weiter") or request.form.get("weiter") or ""
    if request.method == "POST":
        if not csrf_pruefen():
            flash("Die Sitzung ist abgelaufen. Bitte noch einmal versuchen.", "fehler")
            return redirect(url_for("auth.login"))
        email = request.form.get("email", "")
        passwort = request.form.get("passwort", "")
        sperre = gesperrt_bis(email)
        if sperre:
            flash("Zu viele Fehlversuche. Bitte in %d Minuten noch einmal versuchen."
                  % max(1, int((sperre - time.time()) / 60) + 1), "fehler")
            return render_template("admin/login.html", email=email, weiter=weiter), 429
        zeile = benutzer_nach_email(conn, email)
        if zeile is not None and pruefe_passwort(zeile["passwort"], passwort):
            loesche_fehlversuche(email)
            session.clear()
            session["admin_id"] = zeile["id"]
            session.permanent = True
            conn.execute("UPDATE admins SET letzter_login = ? WHERE id = ?",
                         (datenbank.jetzt(), zeile["id"]))
            conn.commit()
            return redirect(_sicheres_ziel(weiter))
        merke_fehlversuch(email)
        # Bewusst keine Auskunft daruber, ob die Adresse existiert.
        flash("E-Mail-Adresse oder Passwort stimmt nicht.", "fehler")
        return render_template("admin/login.html", email=email, weiter=weiter), 401

    return render_template("admin/login.html", email="", weiter=weiter)


@bp.route("/einrichten", methods=["GET", "POST"])
def einrichten():
    """Einmalige Ersteinrichtung, solange noch kein Zugang existiert."""
    conn = current_app.datenbank()
    if anzahl_benutzer(conn) > 0:
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        if not csrf_pruefen():
            flash("Die Sitzung ist abgelaufen. Bitte noch einmal versuchen.", "fehler")
            return redirect(url_for("auth.einrichten"))
        email = request.form.get("email", "").strip()
        name = request.form.get("name", "").strip()
        passwort = request.form.get("passwort", "")
        wiederholung = request.form.get("passwort2", "")
        fehler = None
        if "@" not in email:
            fehler = "Bitte eine gültige E-Mail-Adresse angeben."
        elif passwort != wiederholung:
            fehler = "Die beiden Passwörter stimmen nicht überein."
        else:
            fehler = passwort_pruefregel(passwort)
        if fehler:
            flash(fehler, "fehler")
            return render_template("admin/einrichten.html", email=email, name=name)
        benutzer_anlegen(conn, email, name, passwort)
        zeile = benutzer_nach_email(conn, email)
        session.clear()
        session["admin_id"] = zeile["id"]
        session.permanent = True
        flash("Zugang angelegt. Willkommen!", "erfolg")
        return redirect(url_for("admin.uebersicht"))

    return render_template("admin/einrichten.html", email="", name="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Du bist abgemeldet.", "erfolg")
    return redirect(url_for("auth.login"))
