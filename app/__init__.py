"""Website und Vereinsverwaltung des MTV Gelting 08.

Die oeffentlichen Seiten werden bei jedem Aufruf aus der Datenbank gebaut und
zwischengespeichert; nach jeder Aenderung im Verwaltungsbereich baut die
naechste Anfrage sie neu. Unter ``/admin`` liegt der Bereich, in dem der Verein
alle Inhalte selbst pflegt.
"""

import os
import pathlib
import secrets
from datetime import timedelta

from flask import Flask, abort, g, redirect, send_from_directory, url_for

from . import db as datenbank
from .render import Renderer

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _schluessel(pfad):
    """Sitzungsschluessel aus einer Datei lesen oder einmalig erzeugen.

    So bleiben Anmeldungen ueber einen Neustart hinweg gueltig, ohne dass
    jemand eine Umgebungsvariable setzen muss.
    """
    pfad = pathlib.Path(pfad)
    if pfad.exists():
        return pfad.read_text(encoding="utf-8").strip()
    pfad.parent.mkdir(parents=True, exist_ok=True)
    wert = secrets.token_urlsafe(48)
    pfad.write_text(wert, encoding="utf-8")
    try:
        pfad.chmod(0o600)
    except OSError:
        pass
    return wert


def create_app(testkonfiguration=None):
    app = Flask(__name__)

    dbpfad = os.environ.get("MTV_DATENBANK", str(ROOT / "verein.db"))
    uploads = os.environ.get("MTV_UPLOADS", str(ROOT / "uploads"))

    app.config.from_mapping(
        DATENBANK=dbpfad,
        UPLOADS=uploads,
        ASSETS=str(ROOT / "assets"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("MTV_HTTPS", "") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    )
    if testkonfiguration:
        app.config.update(testkonfiguration)

    app.secret_key = os.environ.get("MTV_SECRET_KEY") or _schluessel(
        pathlib.Path(app.config["DATENBANK"]).with_suffix(".key"))

    for unterordner in ("logos", "dokumente", "bilder"):
        pathlib.Path(app.config["UPLOADS"], unterordner).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Datenbankverbindung je Anfrage
    # ------------------------------------------------------------------

    def verbindung():
        if "conn" not in g:
            g.conn = datenbank.verbinde(app.config["DATENBANK"])
        return g.conn

    app.datenbank = verbindung

    @app.teardown_appcontext
    def schliesse(_fehler=None):
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    with app.app_context():
        conn = datenbank.verbinde(app.config["DATENBANK"])
        datenbank.anlegen(conn)
        if datenbank.ist_leer(conn) and (ROOT / "data" / "verein.json").exists():
            datenbank.befuellen(conn)
            app.logger.info("Datenbank aus data/*.json erstbefüllt.")
        conn.close()

    # ------------------------------------------------------------------
    # Gerenderte Seiten zwischenspeichern
    # ------------------------------------------------------------------

    zwischenspeicher = {"stand": None, "seiten": {}}

    def seiten():
        aktuell = datenbank.stand(verbindung())
        if zwischenspeicher["stand"] != aktuell or not zwischenspeicher["seiten"]:
            V, A = datenbank.lade_daten(verbindung())
            zwischenspeicher["seiten"] = Renderer(V, A).pages()
            zwischenspeicher["stand"] = aktuell
        return zwischenspeicher["seiten"]

    app.seiten = seiten

    # ------------------------------------------------------------------
    # Oeffentliche Seiten
    # ------------------------------------------------------------------

    from . import admin, auth

    app.before_request(auth.lade_benutzer)
    app.register_blueprint(auth.bp, url_prefix="/admin")
    app.register_blueprint(admin.bp, url_prefix="/admin")

    @app.route("/")
    def startseite():
        return seiten()["index.html"], 200, {"Content-Type": "text/html; charset=utf-8"}

    @app.route("/<name>.html")
    def seite(name):
        inhalt = seiten().get(name + ".html")
        if inhalt is None:
            abort(404)
        return inhalt, 200, {"Content-Type": "text/html; charset=utf-8"}

    @app.route("/assets/<path:datei>")
    def assets(datei):
        return send_from_directory(app.config["ASSETS"], datei)

    @app.route("/uploads/<path:datei>")
    def hochgeladen(datei):
        antwort = send_from_directory(app.config["UPLOADS"], datei)
        # Der Browser soll den Dateityp nicht selbst erraten.
        antwort.headers["X-Content-Type-Options"] = "nosniff"
        return antwort

    @app.errorhandler(404)
    def nicht_gefunden(_fehler):
        return ("<!doctype html><html lang=de><meta charset=utf-8>"
                "<title>Seite nicht gefunden</title>"
                "<body style='font-family:system-ui;padding:3rem;max-width:36rem'>"
                "<h1>Seite nicht gefunden</h1>"
                "<p>Diese Adresse gibt es nicht. <a href='/'>Zur Startseite</a></p>", 404)

    @app.errorhandler(413)
    def zu_gross(_fehler):
        return ("<!doctype html><html lang=de><meta charset=utf-8>"
                "<title>Datei zu groß</title>"
                "<body style='font-family:system-ui;padding:3rem;max-width:36rem'>"
                "<h1>Datei zu groß</h1>"
                "<p>Die Datei überschreitet 16 MB. Bitte kleiner speichern und erneut "
                "hochladen. <a href='/admin/'>Zurück</a></p>", 413)

    @app.route("/admin")
    def admin_wurzel():
        return redirect(url_for("admin.uebersicht"))

    return app
