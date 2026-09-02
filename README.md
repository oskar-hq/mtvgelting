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
| `sportangebot.html` | ~31 Abteilungs-Unterseiten | **Eine** filterbare Übersicht: Bereich, Alter, Volltextsuche. Details klappen in der Karte auf. |
| `termine.html` | Trainingszeiten je Sportart, 6 Spielplan-Seiten, Vereinstermine | **Ein** Wochenplan über alle Angebote + Spielplan-Links + Vereinsjahr |
| `verein.html` | Vorstand, Geschäftsstelle, Satzungen, Sprachrohr, Jugendschutz | Eine Seite mit Sprungnavigation |
| `mitglied-werden.html` | Mitglied werden, Beitragsordnung | Beiträge, Ablauf in drei Schritten, Kontakt |

Dazu `impressum.html` und `datenschutz.html`.

Nichts wurde weggeworfen: alle 31 Angebote, alle Abteilungen, alle Vereinsinfos sind enthalten —
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
2. **Trainingszeiten.** Belegt sind nur Badminton, Damengymnastik, Step Aerobic (Zeiten) und
   Kunstturnen (Tage). Die übrigen 27 Angebote zeigen „Zeit auf Anfrage".
3. **Ansprechpartner je Abteilung** — im Datenmodell noch nicht angelegt.
4. **PDFs**: Satzung, Ehrenordnung, Aufnahmeantrag, Sprachrohr.
5. **Kinder- & Jugendschutzkonzept**: Text und Ansprechpersonen.
6. **Öffnungszeiten der Geschäftsstelle.**
7. **E-Mail-Adresse prüfen** — auf der Live-Seite per JavaScript verschleiert; hier ist
   `vorstand@mtv-gelting-08.de` hinterlegt und muss bestätigt werden.
8. **Sponsorenlogos** inkl. Freigabe (aktuell als Namen gesetzt).

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
