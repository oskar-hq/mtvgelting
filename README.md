# MTV Gelting 08 — Website-Entwurf

Gestaltungsentwurf für einen Relaunch von [mtv-gelting-08.de](https://mtv-gelting-08.de) als
statische Website auf GitHub Pages. **Nicht die offizielle Website des Vereins.**

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

Nichts wurde weggeworfen: alle 36 Angebote, alle Abteilungen, alle Vereinsinfos sind enthalten —
nur anders sortiert. Die Filter-Links sind teilbar
(`sportangebot.html?kategorie=kinder&fuer=kinder`), sodass jede Abteilung weiterhin einen eigenen
Link für ihre Aushänge hat.

## Technik

Statisches HTML/CSS/JS, kein Build-Tool, keine Abhängigkeiten, keine Datenbank — direkt über
GitHub Pages ausspielbar. Kein Cookie-Banner nötig, da kein Tracking eingebunden ist.

Die Seiten werden aus den JSON-Dateien in `data/` erzeugt:

```
python3 tools/build.py
```

Ein Workflow prüft bei jedem Push, dass die eingecheckten HTML-Dateien zu den Daten in `data/`
passen — wer JSON ändert und den Generator vergisst, bekommt eine rote CI statt einer stillen
Abweichung.

```
data/verein.json      Stammdaten, Vorstand, Beiträge, News, Termine, Sponsoren
data/angebote.json    alle 31 Sportangebote mit Kategorie, Zielgruppe, Zeiten
tools/build.py        Generator (Templates + Seiteninhalte)
assets/css/site.css   Design-System
assets/js/site.js     Navigation + Angebotsfilter
```

### Farben

Die Palette folgt dem Vereinswappen: Vereinsblau `#1D4E7C`, Weiß und ein helles Grau
`#F2F5F8` als Grundfläche. Dunkle Flächen und der Footer nutzen ein tieferes Navy
`#102D48`, Fließtext ein dunkles Blaugrau `#12283B`. Alle Text-Hintergrund-Paare
erreichen mindestens 4,5:1 (WCAG AA).

Inhaltspflege läuft damit über die JSON-Dateien, nicht über HTML. Trainingszeiten stehen an genau
einer Stelle (`angebote.json`) und erscheinen automatisch auf der Angebotsseite **und** im
Wochenplan.

### Barrierefreiheit & Robustheit

- Funktioniert ohne JavaScript (Details klappen über `<details>`, nur der Filter braucht JS)
- Tastaturbedienbar, sichtbare Fokus-Ringe, `aria-pressed` an den Filtern, Skip-Link
- Kein horizontaler Überlauf bei 390 / 768 / 1440 px geprüft
- `prefers-reduced-motion` wird respektiert

## Offene Punkte vor einem Livegang

Der Entwurf ist inhaltlich vollständig strukturiert, aber an diesen Stellen fehlen echte Daten.
Alle Stellen sind in den Seiten sichtbar als „folgt" / „auf Anfrage" markiert — nichts ist erfunden.

**Vom Verein zu liefern**

1. **Fotos.** Sämtliche Bilder sind Platzhalter. Der aktuelle Auftritt nutzt Stockfotos —
   echte Vereinsfotos wären der größte sichtbare Gewinn.
2. **Trainingszeiten** — weitgehend erledigt. Der Hallenbelegungsplan (gültig ab Juni 2026) ist
   vollständig eingepflegt: 58 Einheiten mit Tag, Uhrzeit, Ort, Gruppe und Übungsleitung.
   Nur vier Angebote stehen nicht darin (Volleyball, Reha-Sport, Kunstturnen, Pokern) und zeigen
   „Zeit auf Anfrage".
3. **Ansprechpartner je Abteilung.** Die Übungsleitung steht pro Trainingseinheit; was fehlt, sind
   Kontaktdaten (Telefon/E-Mail) der Abteilungsleitungen.
4. **PDFs**: Satzung, Ehrenordnung, Aufnahmeantrag, Sprachrohr.
5. **Kinder- & Jugendschutzkonzept**: Text und Ansprechpersonen.
6. **Öffnungszeiten der Geschäftsstelle.**
7. **E-Mail-Adresse prüfen** — auf der Live-Seite per JavaScript verschleiert; hier ist
   `vorstand@mtv-gelting-08.de` hinterlegt und muss bestätigt werden.
8. **Sponsorenlogos** inkl. Freigabe (aktuell als Namen gesetzt).
9. **Vereinswappen als Datei.** Ein Nachbau war nicht gut genug und wurde wieder entfernt; der
   Header trägt derzeit eine reine Wortmarke. Sobald das Original als SVG oder PNG vorliegt, wird
   es in Header, Footer und Favicon eingebunden. Auch der Blauton `--blue` ist aus einer
   Abbildung des Wappens geschätzt und sollte gegen den echten Wert geprüft werden.

**Technisch zu klären**

9. **Mitglieder-Login.** Der Joomla-Auftritt hat einen Login-Bereich. GitHub Pages ist rein
   statisch — der Bereich entfällt oder braucht einen externen Dienst.
10. **Schriften lokal einbinden** statt über Google Fonts (Datenschutz).
11. **Spielpläne**: aktuell Links zu den Verbänden. Einbettung wäre möglich, aber
    abhängig von den Schnittstellen der Verbände.
12. **Impressum und Datenschutzerklärung** müssen vor Veröffentlichung rechtlich geprüft werden.

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
echten Vereinsauftritt auftaucht. Vor einem echten Livegang muss das Meta-Tag in
`tools/build.py` entfernt werden.

## Lokal ansehen

```
python3 -m http.server 8099
# http://localhost:8099
```
