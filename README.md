# MTV Gelting 08 — Website-Entwurf

Gestaltungsentwurf für einen Relaunch von [mtv-gelting-08.de](https://mtv-gelting-08.de) —
fünf Seiten statt vierzig, dazu ein Verwaltungsbereich, in dem der Verein alle Inhalte selbst
pflegt. **Nicht die offizielle Website des Vereins.**

## Die zentrale Änderung: 40+ Seiten → 5 Seiten

Der bestehende Joomla-Auftritt verteilt die Inhalte auf über 40 Unterseiten — pro Sportart eine
eigene Seite, Trainingszeiten und Ansprechpartner jeweils darin versteckt. Wer wissen will
„welcher Sport passt für mein Kind und wann ist das?", klickt sich durch ein halbes Dutzend Seiten.

Dieser Entwurf fasst dieselben Inhalte in fünf Seiten zusammen:

| Seite | Ersetzt | Prinzip |
|---|---|---|
| `index.html` | Startseite, Aktuelles | Einstieg über die Frage „Was möchtest du machen?" |
| `sportangebot.html` | ~36 Abteilungs-Unterseiten | **Eine** filterbare Übersicht: Bereich, Alter, Volltextsuche. Details und alle Trainingszeiten klappen in der Karte auf. |
| `termine.html` | Trainingszeiten je Sportart, 6 Spielplan-Seiten, Vereinstermine | **Ein** Wochenplan mit allen 58 Einheiten inkl. Ort und Übungsleitung |
| `verein.html` | Vorstand, Geschäftsstelle, Satzungen, Sprachrohr, Jugendschutz | Eine Seite mit Sprungnavigation |
| `mitglied-werden.html` | Mitglied werden, Beitragsordnung | Beiträge, Ablauf in drei Schritten, Kontakt |

Dazu `impressum.html` und `datenschutz.html`.

Die zweite Änderung ist der **Verwaltungsbereich**: Termine, Sportangebote, Trainingszeiten,
Beiträge, Vorstand, Sponsorenlogos, Satzung und Sprachrohr werden über eine Anmeldung im Browser
gepflegt — niemand muss dafür an den Code oder an Dateien. Details unter
[„Der Verwaltungsbereich“](#der-verwaltungsbereich).

Nichts wurde weggeworfen: alle 36 Angebote, alle Abteilungen, alle Vereinsinfos sind enthalten —
nur anders sortiert. Die Filter-Links sind teilbar
(`sportangebot.html?kategorie=kinder&fuer=kinder`), sodass jede Abteilung weiterhin einen eigenen
Link für ihre Aushänge hat.

## Technik

Die Website ist eine kleine Python-Anwendung (Flask) mit einer SQLite-Datenbank. Alle Inhalte
stehen in dieser Datenbank; die sieben Seiten werden daraus erzeugt und zwischengespeichert.
Ändert jemand im Verwaltungsbereich etwas, baut die nächste Anfrage die betroffenen Seiten neu —
es gibt keinen Veröffentlichungsschritt und keine Wartezeit.

```
app/__init__.py       Anwendung, öffentliche Seiten, Zwischenspeicher
app/db.py             Datenbankschema, Lesen und Schreiben, Erstbefüllung aus data/
app/auth.py           Anmeldung, Passwörter (scrypt), Schutz vor fremden Formularen
app/admin.py          Verwaltungsbereich: alle Listen und Formulare
app/render.py         erzeugt das HTML der sieben Seiten aus den Daten
app/templates/admin/  Vorlagen des Verwaltungsbereichs
app/static/           Gestaltung des Verwaltungsbereichs
tools/build.py        statischer Export (für GitHub Pages)
tools/verwaltung.py   Einrichtung, Zugänge, Passwörter
tests/                Prüfungen für Datenbank, Anmeldung und Verwaltung
data/*.json           Ausgangsdaten; daraus wird die Datenbank erstmalig gefüllt
assets/css/site.css   Design-System der Website
assets/js/site.js     Navigation + Angebotsfilter
uploads/              hochgeladene Logos, PDFs und Fotos
```

Einzige Abhängigkeit ist Flask. Passwörter werden mit `hashlib.scrypt` aus der
Standardbibliothek gehasht, die Datenbank ist SQLite — es gibt nichts zusätzlich zu betreiben.

## Der Verwaltungsbereich

Der Verein pflegt alle Inhalte selbst, ohne den Programmcode anzufassen. Unten im Footer jeder
Seite steht der Link **„Vereinsintern anmelden“**; dahinter liegt eine Anmeldung mit
E-Mail-Adresse und Passwort.

| Bereich | Was sich dort ändern lässt |
|---|---|
| **Sportangebote** | Name, Bereich, Zielgruppen, Kurz- und Langtext, Ort, **alle Trainingszeiten** (Tag, von/bis, Gruppe, Ort, Übungsleitung, Hinweis) und der **Ansprechpartner der Abteilung** mit Telefon und E-Mail |
| **Termine** | Titel, Datum, Uhrzeit, Ort, Beschreibung. Ohne Datum wird der Termin als Dauerangebot geführt |
| **Aktuelles** | Meldungen für die Startseite |
| **Vorstand** | Name, Funktion, E-Mail, Kennzeichen „vertritt nach § 26 BGB“ (steuert zugleich das Impressum) |
| **Beiträge** | Gruppen mit Monats- und Jahresbeitrag. Der Satz „ab … € im Monat“ auf der Startseite rechnet sich daraus |
| **Dokumente & PDFs** | Satzung, Ehrenordnung, Aufnahmeantrag und die Ausgaben des Sprachrohrs — als PDF hochladen oder verlinken |
| **Sponsoren** | Name, Logo (Bilddatei) und Website |
| **Spielpläne** | Verweise auf die Verbände |
| **Stammdaten** | Vereinsname, Anschrift, Telefon, E-Mail, Register, Öffnungszeiten, Vereinsshop, Facebook, Instagram |
| **Texte & Bilder** | Überschrift der Startseite, Fotos, Sprachrohr-Einleitung, Kinder- & Jugendschutz, Hinweisstreifen, Sperre für Suchmaschinen, Datenschutztext |
| **Bereiche / Zielgruppen** | die Filter des Sportangebots |
| **Zugänge** | wer sich anmelden darf; jede Person kann ihr Passwort selbst ändern |

Ein paar Dinge geschehen dabei von allein:

- **Trainingszeiten stehen an genau einer Stelle.** Was beim Angebot eingetragen wird, erscheint
  zugleich in der Angebotskarte **und** im Wochenplan auf der Termineseite.
- **Das Sponsorenraster passt sich der Anzahl an.** Bei wenigen Sponsoren werden es weniger
  Spalten, bei vielen mehr Zeilen — ohne dass jemand am Layout etwas ändern muss.
- **Die Anschrift steht nur einmal da.** Sie wirkt gleichzeitig im Footer, auf der Vereinsseite
  und im Impressum.
- **Der Beitragssatz auf der Startseite rechnet sich aus den Beiträgen.** Passive Beiträge werden
  dabei ausgenommen, damit dort kein irreführender Preis steht.

### Einrichten

```
python3 -m pip install -r requirements.txt
python3 tools/verwaltung.py einrichten
```

Der zweite Befehl legt `verein.db` an, füllt sie aus `data/*.json` und fragt nach dem ersten
Zugang. Danach starten:

```
flask --app app run
# http://127.0.0.1:5000  — Verwaltung unter /admin/
```

Weitere Zugänge legt man im Browser unter „Zugänge“ an oder auf der Kommandozeile:

```
python3 tools/verwaltung.py zugang-anlegen --email name@example.de
python3 tools/verwaltung.py passwort-setzen --email name@example.de
python3 tools/verwaltung.py zugaenge
```

### Betrieb auf einem Server

`flask run` ist nur für den eigenen Rechner gedacht. Auf einem Server läuft die Anwendung hinter
einem WSGI-Server, zum Beispiel:

```
python3 -m pip install gunicorn
gunicorn --workers 2 --bind 127.0.0.1:8000 "app:create_app()"
```

Davor gehört ein Webserver (nginx, Apache) mit HTTPS. Wichtig sind vier Punkte:

1. **`MTV_HTTPS=1` setzen**, sobald die Seite über HTTPS läuft — dann wird das Sitzungs-Cookie
   nur noch verschlüsselt übertragen.
2. **`verein.db` und `verein.key` sichern.** Darin stehen alle Inhalte und der Sitzungsschlüssel.
   Ein `cp verein.db verein.db.sicherung` im Cron reicht für den Anfang; beide Dateien sind
   bewusst nicht im Repository.
3. **Den Ordner `uploads/` mitsichern** — dort liegen Logos, PDFs und Fotos.
4. **Zuerst einrichten, dann erreichbar machen.** Solange kein Zugang existiert, bietet
   `/admin/einrichten` an, den ersten anzulegen — das soll nicht der erste Besucher tun.

Ohne gesetzte Umgebungsvariablen liegen Datenbank und Uploads neben dem Projekt. Ändern lässt
sich das mit `MTV_DATENBANK`, `MTV_UPLOADS` und `MTV_SECRET_KEY`.

### Statische Ausgabe für GitHub Pages

Der ursprüngliche Weg funktioniert weiterhin. Ohne Datenbank baut

```
python3 tools/build.py
```

die sieben Seiten aus `data/*.json`. Ein Workflow prüft bei jedem Push, dass die eingecheckten
HTML-Dateien dazu passen. Wer die Datenbank als Quelle nehmen will:

```
python3 tools/build.py --db --json
```

Das schreibt zusätzlich den Datenbankstand nach `data/` zurück, sodass beide Quellen wieder
zusammenpassen. Im Verwaltungsbereich macht der Punkt „Statische Seiten“ dasselbe per Knopfdruck.

Der statische Weg hat eine Grenze: GitHub Pages liefert nur Dateien aus, dort läuft kein
Verwaltungsbereich. Wer die Seiten statisch ausspielt, braucht die Anwendung trotzdem irgendwo
zum Bearbeiten — oder blendet den Anmeldelink unter „Texte & Bilder“ aus.

### Tests

```
python3 -m unittest discover -s tests
```

45 Prüfungen für Anmeldung, Fehlversuchssperre, Formularschutz, alle Bearbeitungsmasken,
Datei-Uploads, das Sponsorenraster und den statischen Export. Jeder Test bekommt eine frische
Datenbank in einem temporären Ordner.

### Farben

Die Palette folgt dem Vereinswappen: **Vereinsblau `#134679`**, direkt aus der Logodatei
ausgelesen, dazu Weiß und ein helles Grau `#F2F5F8` als Grundfläche. Dunkle Flächen und der
Footer nutzen ein tieferes Navy `#0C2745`, Fließtext ein dunkles Blaugrau `#11253C`. Alle
Text-Hintergrund-Paare erreichen mindestens 4,5:1 (WCAG AA).

Die beiden Web-Größen des Wappens entstehen aus `assets/img/logo.hd1.png` und sind eingecheckt;
sie werden nicht bei jedem Build neu erzeugt. Nach einem Austausch des Originals:

```
python3 -c "from PIL import Image; s=Image.open('assets/img/logo.hd1.png').convert('RGBA'); \
s.resize((225,300), Image.LANCZOS).quantize(colors=32, method=Image.FASTOCTREE).save('assets/img/logo.png', optimize=True)"
```

### Barrierefreiheit & Robustheit

- Funktioniert ohne JavaScript (Details klappen über `<details>`, nur der Filter braucht JS)
- Tastaturbedienbar, sichtbare Fokus-Ringe, `aria-pressed` an den Filtern, Skip-Link
- Kein horizontaler Überlauf bei 390 / 768 / 1440 px geprüft
- `prefers-reduced-motion` wird respektiert

## Offene Punkte vor einem Livegang

Der Entwurf ist inhaltlich vollständig strukturiert, aber an diesen Stellen fehlen echte Daten.
Alle Stellen sind in den Seiten sichtbar als „folgt" / „auf Anfrage" markiert — nichts ist erfunden.

**Vom Verein zu liefern** — alles davon lässt sich jetzt im Verwaltungsbereich eintragen,
ohne den Code anzufassen.

1. **Fotos.** Sämtliche Bilder sind Platzhalter. Unter „Texte & Bilder“ lassen sich Startseiten-
   und Sprachrohrbild hochladen. Echte Vereinsfotos wären der größte sichtbare Gewinn.
2. **Trainingszeiten** — weitgehend erledigt. Der Hallenbelegungsplan (gültig ab Juni 2026) ist
   vollständig eingepflegt: 58 Einheiten mit Tag, Uhrzeit, Ort, Gruppe und Übungsleitung.
   Nur vier Angebote stehen nicht darin (Volleyball, Reha-Sport, Kunstturnen, Pokern) und zeigen
   „Zeit auf Anfrage". Änderungen laufen über „Sportangebote“.
3. **Ansprechpartner je Abteilung.** Die Felder stehen bereit (Name, Telefon, E-Mail je Angebot),
   die Daten fehlen noch.
4. **PDFs**: Satzung, Ehrenordnung, Aufnahmeantrag, Sprachrohr — unter „Dokumente & PDFs“
   hochladen.
5. **Kinder- & Jugendschutzkonzept**: Text und Ansprechpersonen, unter „Texte & Bilder“.
6. **Öffnungszeiten der Geschäftsstelle**, unter „Stammdaten“.
7. **E-Mail-Adresse prüfen** — hinterlegt ist `vorstand@mtv-gelting-08.de`; zu bestätigen und
   gegebenenfalls unter „Stammdaten“ zu ändern.
8. **Sponsorenlogos** inkl. Freigabe — unter „Sponsoren“ hochladen. Bis dahin erscheint der Name.
9. ~~Vereinswappen~~ — erledigt. Die Originaldatei liegt unter `assets/img/logo.hd1.png` und
   ist in Header, Footer und Favicon eingebunden; das Vereinsblau ist daraus ausgelesen.

**Technisch zu klären**

10. ~~Mitglieder-Login~~ — für den Vorstand erledigt: der Verwaltungsbereich unter `/admin/`
    ersetzt den bisherigen Redaktionsweg. Ein Login **für alle Mitglieder** (wie im
    Joomla-Auftritt) ist damit noch nicht gebaut; falls er gebraucht wird, ist zu klären, welche
    Inhalte er überhaupt zeigen soll.
11. **Schriften lokal einbinden** statt über Google Fonts (Datenschutz).
12. **Spielpläne**: aktuell Links zu den Verbänden. Einbettung wäre möglich, aber
    abhängig von den Schnittstellen der Verbände.
13. **Impressum und Datenschutzerklärung** müssen vor Veröffentlichung rechtlich geprüft werden.
    Beide Texte sind im Verwaltungsbereich änderbar.
14. **Vor dem Livegang**: unter „Texte & Bilder“ den Haken „Für Suchmaschinen sperren“ entfernen
    und den Hinweisstreifen „Vorschau-Entwurf“ leeren.

## GitHub Pages aktivieren

Der Actions-Token darf eine Pages-Site nicht selbst anlegen, solange Pages im Repository noch nie
eingerichtet wurde. Dieser eine Schritt muss deshalb einmalig von Hand erfolgen — unter
**Settings → Pages**:

**Variante A — Deploy from a branch** (einfachster Weg, sofort live)
Source: `Deploy from a branch`, Branch: `claude/mtv-gelting-audit-3jknqv`, Ordner: `/ (root)`.
GitHub veröffentlicht den Branch dann direkt; der Pages-Workflow wird nicht gebraucht.

**Variante B — GitHub Actions**
Source: `GitHub Actions`. Danach den Workflow „GitHub Pages" einmal starten
(Actions → GitHub Pages → Run workflow). Jede weitere Veröffentlichung läuft dann darüber.

Die Adresse lautet anschließend `https://oskar-hq.github.io/mtvgelting/`.

Die Seiten tragen `noindex, nofollow`, damit der Entwurf nicht in Suchmaschinen neben dem
echten Vereinsauftritt auftaucht. Das steuert der Haken „Für Suchmaschinen sperren“ unter
„Texte & Bilder“ (ohne Datenbank: `texte.suchmaschinen_sperren` in `data/verein.json`).

## Lokal ansehen

Mit Verwaltungsbereich:

```
python3 -m pip install -r requirements.txt
python3 tools/verwaltung.py einrichten
flask --app app run
# http://127.0.0.1:5000
```

Nur die statischen Seiten, ohne Python-Anwendung:

```
python3 tools/build.py
python3 -m http.server 8099
# http://localhost:8099
```
