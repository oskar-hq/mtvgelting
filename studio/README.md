# Redaktionsoberfläche (Sanity Studio)

Hier pflegt der Verein die Inhalte der Website. Wer etwas speichert, löst
automatisch einen neuen Build aus; wenige Minuten später steht die Änderung
online.

```
Studio (mtv-gelting.sanity.studio)
   │  jemand speichert
   ▼
Sanity  ──Webhook──►  GitHub Actions
                          │  Inhalte holen, Seiten bauen
                          ▼
                      GitHub Pages
```

Anmeldung im Studio per E-Mail oder Google — **ein GitHub-Konto ist dafür
nicht nötig.**

---

## Einrichtung (einmalig)

Voraussetzung: **Node 22.12 oder neuer** (`node -v`). Ältere Fassungen lehnt
Sanity ab.

### 1. Abhängigkeiten und Anmeldung

```
cd studio
npm install
npx sanity login
```

Beim Login mit dem Konto anmelden, dem das Sanity-Projekt gehört.

### 2. Bestehende Inhalte übertragen

Die 36 Sportangebote mit allen Trainingszeiten, der Vorstand, die Beiträge,
Sponsoren und Termine liegen bereits als JSON im Repository. Dieses Skript
schreibt sie ins CMS, damit niemand sie abtippen muss:

```
cd ..
export SANITY_PROJEKT=tonxqosy
export SANITY_TOKEN=…            # Token mit Schreibrecht, siehe unten
python3 tools/nach_sanity.py --probe     # zeigt nur an, was passieren würde
python3 tools/nach_sanity.py             # überträgt
```

Den Token gibt es unter [sanity.io/manage](https://www.sanity.io/manage) →
Projekt → **API → Tokens → Add API token**, Rolle **Editor**. Nach der
Übertragung darf dieser Token wieder gelöscht werden — für den laufenden
Betrieb genügt ein Lesetoken.

Ein zweiter Lauf legt nichts doppelt an: jedes Dokument hat einen festen
Schlüssel. `--ersetzen` überschreibt vorhandene Dokumente und verwirft dabei
Änderungen, die inzwischen im Studio gemacht wurden — also nur bewusst
einsetzen.

### 3. Studio veröffentlichen

```
cd studio
npm run deploy
```

Danach ist es unter **https://mtv-gelting.sanity.studio** erreichbar. Die
Adresse steht in `sanity.cli.js` (`studioHost`) und lässt sich dort ändern.

Zum Ausprobieren auf dem eigenen Rechner genügt `npm run dev`
(http://localhost:3333).

### 4. Leute einladen

[sanity.io/manage](https://www.sanity.io/manage) → Projekt → **Members →
Invite member**. Die eingeladene Person bekommt eine E-Mail und meldet sich
mit ihrer Adresse an.

Sinnvolle Rolle für Trainer und Vorstand: **Editor** (darf Inhalte ändern und
veröffentlichen, aber nichts an der Struktur des CMS). Im Gratis-Tarif ist die
Zahl der Mitglieder begrenzt — die aktuelle Grenze steht in der
Sanity-Verwaltung.

### 5. GitHub vorbereiten

**Variable und Geheimnis** unter *Settings → Secrets and variables → Actions*:

| Art | Name | Wert |
|---|---|---|
| Variable | `SANITY_PROJEKT` | `tonxqosy` |
| Variable | `SANITY_DATENSATZ` | `production` (optional, ist die Vorgabe) |
| Secret | `SANITY_TOKEN` | Lesetoken, Rolle **Viewer** |

Die Projekt-ID ist keine Geheimhaltungssache — sie steht ohnehin in
`sanity.config.js`. Der Token gehört dagegen unter *Secrets*.

**GitHub Pages** unter *Settings → Pages*: Source auf **GitHub Actions**
stellen.

### 6. Webhook einrichten

Damit das Speichern im Studio den Build auslöst.

Zuerst ein GitHub-Token erzeugen: *GitHub → Settings → Developer settings →
Personal access tokens → Fine-grained tokens → Generate new token*

- Repository access: **Only select repositories** → `oskar-hq/mtvgelting`
- Permissions → Repository permissions → **Contents: Read and write**

Dann in [sanity.io/manage](https://www.sanity.io/manage) → Projekt → **API →
Webhooks → Create webhook**:

| Feld | Wert |
|---|---|
| Name | `GitHub Pages bauen` |
| URL | `https://api.github.com/repos/oskar-hq/mtvgelting/dispatches` |
| Dataset | `production` |
| Trigger on | Create, Update, Delete |
| Filter | leer lassen |
| Projection | `{"event_type": "sanity-update"}` |
| HTTP method | `POST` |
| HTTP headers | `Authorization: Bearer <das eben erzeugte Token>`<br>`Accept: application/vnd.github+json` |

Die **Projection** ist der wichtige Teil: sie bestimmt, was Sanity an GitHub
schickt. `event_type` muss `sanity-update` lauten — darauf hört
`.github/workflows/pages.yml`.

### 7. Ausprobieren

Im Studio eine Kleinigkeit ändern und speichern. Unter *Actions* im
GitHub-Repository sollte innerhalb einer Minute der Lauf
**„Website veröffentlichen"** starten.

Startet nichts, lässt sich der Webhook in Sanity unter *API → Webhooks →
(der Webhook) → Attempts* nachvollziehen — dort steht die Antwort von GitHub.
Ein `404` bedeutet meist, dass das Token keine Schreibrechte auf *Contents*
hat.

---

## Aufbau des Studios

| Menüpunkt | Inhalt |
|---|---|
| **Sportangebote** | Name, Bereich, Zielgruppen, Texte, Ort, alle Trainingszeiten und der Ansprechpartner der Abteilung |
| **Termine** | Titel, Datum, Uhrzeit, Ort, Beschreibung |
| **Aktuelles** | kurze Meldungen; die vier neuesten stehen auf der Startseite |
| **Vorstand** | Name, Funktion, E-Mail, Kennzeichen „§ 26 BGB" |
| **Beiträge** | Gruppen mit Monats- und Jahresbeitrag |
| **Dokumente & PDFs** | Satzung, Ehrenordnung, Aufnahmeantrag, Sprachrohr |
| **Sponsoren** | Name, Logo, Website |
| **Spielpläne** | Verweise auf die Verbände |
| **Stammdaten des Vereins** | Anschrift, Telefon, E-Mail, Register, Öffnungszeiten |
| **Texte & Bilder der Seiten** | Überschriften, Fotos, Jugendschutz, Rechtstexte, Sichtbarkeit |
| **Bereiche / Zielgruppen** | die Filter des Sportangebots |

„Stammdaten" und „Texte & Bilder" gibt es je genau einmal; sie lassen sich
nicht doppelt anlegen oder löschen.

## Gut zu wissen

**Entwürfe erscheinen nicht auf der Website.** Sanity legt beim Bearbeiten
zunächst einen Entwurf an; erst **Publish** macht die Änderung sichtbar. Der
Build holt ausdrücklich nur veröffentlichte Dokumente.

**Bilder und PDFs werden beim Bauen heruntergeladen** und neben die Seiten
gelegt. Besucher laden also nichts bei Sanity nach — das hält die
Datenschutzerklärung kurz und die Seite funktioniert auch, wenn Sanity einmal
nicht erreichbar ist.

**Trainingszeiten stehen an genau einer Stelle**, nämlich beim Angebot. Sie
erscheinen von dort automatisch auch im Wochenplan auf der Termineseite.

**Das Sponsorenraster passt sich der Anzahl an**: weniger Sponsoren ergeben
weniger Spalten, mehr ergeben weitere Zeilen.

**Vor dem Livegang**: unter *Texte & Bilder → Sichtbarkeit* den Haken „Für
Suchmaschinen sperren" entfernen und den Hinweisstreifen „Vorschau-Entwurf"
leeren.

## Schema ändern

Die Dokumentarten liegen in `schemaTypes/`. Nach einer Änderung:

```
npx sanity schema validate    # prüft das Schema
npm run dev                   # lokal ansehen
npm run deploy                # veröffentlichen
```

Kommt ein Feld hinzu, das auf der Website erscheinen soll, muss es auch in die
Abfrage in `tools/sanity.py` (`ABFRAGE`) und in die Umsetzung
(`nach_inhalten`) aufgenommen werden. Der Test `RundeReise` in
`tests/test_website.py` schlägt fehl, wenn beides nicht zusammenpasst.
