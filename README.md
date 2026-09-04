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

Die zweite Änderung: **der Verein pflegt alles selbst**, ohne den Code anzufassen. Termine,
Sportangebote, Trainingszeiten, Beiträge, Vorstand, Sponsorenlogos, Satzung und Sprachrohr stehen
in einem CMS, in dem man sich mit E-Mail-Adresse anmeldet. Wer dort speichert, löst automatisch
einen neuen Build aus. Einrichtung und Bedienung: **[`studio/README.md`](studio/README.md)**.

Die zweite Änderung ist der **Verwaltungsbereich**: Termine, Sportangebote, Trainingszeiten,
Beiträge, Vorstand, Sponsorenlogos, Satzung und Sprachrohr werden über eine Anmeldung im Browser
gepflegt — niemand muss dafür an den Code oder an Dateien. Details unter
[„Der Verwaltungsbereich“](#der-verwaltungsbereich).

Nichts wurde weggeworfen: alle 36 Angebote, alle Abteilungen, alle Vereinsinfos sind enthalten —
nur anders sortiert. Die Filter-Links sind teilbar
(`sportangebot.html?kategorie=kinder&fuer=kinder`), sodass jede Abteilung weiterhin einen eigenen
Link für ihre Aushänge hat.

## Wie es zusammenhängt

```
Sanity Studio                 Redaktion: Anmeldung per E-Mail,
(mtv-gelting.sanity.studio)   kein GitHub-Konto nötig
        │
        │  jemand speichert  →  Webhook
        ▼
GitHub Actions                .github/workflows/pages.yml
        │  1. Inhalte aus dem CMS holen      tools/sanity.py
        │  2. Bilder und PDFs herunterladen
        │  3. sieben Seiten erzeugen         tools/render.py
        ▼
GitHub Pages                  fertiges HTML, kein Server nötig
```

Auf der Website läuft damit nichts als HTML, CSS und ein wenig JavaScript für den Filter — kein
Server, keine Datenbank, keine Anmeldung. Alles Bewegliche passiert beim Bauen.

| Datei | Aufgabe |
|---|---|
| `tools/render.py` | erzeugt aus den Inhalten die sieben Seiten |
| `tools/inhalte.py` | lädt Inhalte aus `data/*.json` und bringt sie in die Form des Generators |
| `tools/sanity.py` | holt dieselben Inhalte stattdessen aus dem CMS, samt Bildern und PDFs |
| `tools/build.py` | das Kommando, das beides zusammenführt |
| `tools/nach_sanity.py` | überträgt die Bestandsinhalte einmalig ins CMS |
| `studio/` | die Redaktionsoberfläche: Dokumentarten, Felder, Menüaufbau |
| `data/*.json` | Sicherung des CMS-Stands; zugleich Quelle, wenn ohne CMS gebaut wird |
| `assets/css/site.css` | Design-System |
| `assets/js/site.js` | Navigation und Angebotsfilter |

Der Generator braucht **nur die Python-Standardbibliothek** — keine Abhängigkeiten, kein
`pip install`. Das Studio ist ein gewöhnliches Node-Projekt und wird nur zum Bearbeiten gebraucht,
nicht zum Ausliefern.

### Bauen

```
python3 tools/build.py                     Quelle automatisch wählen
python3 tools/build.py --quelle dateien    aus data/*.json, ohne CMS
python3 tools/build.py --quelle cms        aus dem CMS
python3 tools/build.py --ziel _site        in einen eigenen Ordner
```

Ohne gesetzte Umgebungsvariablen wird aus `data/*.json` gebaut. Für den CMS-Weg:

```
export SANITY_PROJEKT=tonxqosy
export SANITY_TOKEN=…          nur nötig, wenn der Datensatz nicht öffentlich ist
python3 tools/build.py --quelle cms
```

Die erzeugten HTML-Dateien sind **nicht eingecheckt**: sie entstehen bei jedem Build neu und wären
nach der nächsten Änderung im CMS ohnehin veraltet.

### Was von allein passiert

- **Trainingszeiten stehen an genau einer Stelle** — beim Sportangebot. Von dort erscheinen sie
  zugleich in der Angebotskarte und im Wochenplan auf der Termineseite.
- **Die Anschrift steht nur einmal da** und wirkt zugleich im Footer, auf der Vereinsseite und im
  Impressum.
- **Der Satz „ab … € im Monat"** auf der Startseite rechnet sich aus den gepflegten Beiträgen;
  passive Beiträge bleiben dabei außen vor, damit dort kein irreführender Preis steht.
- **Das Sponsorenraster richtet sich nach der Anzahl** — weniger Sponsoren ergeben weniger
  Spalten, mehr ergeben weitere Zeilen.
- **Bilder und PDFs werden beim Bauen heruntergeladen** und neben die Seiten gelegt. Besucher
  laden nichts beim CMS-Anbieter nach.
- **Aktionen auf der Startseite** (Birklauf, Flohmarkt, Herbstcamp) stehen als dunkel abgesetzter
  Block gleich unter dem Kopfbereich und lassen sich einzeln ein- und ausblenden, ohne sie zu
  löschen; der Anmeldelink wird je Aktion gepflegt. Der Status je Karte — „Anmeldung offen“,
  „Termin steht“, „in Planung“ — ergibt sich aus den gepflegten Feldern. Ohne aktive Aktion
  entfällt der Abschnitt.

### Abläufe in GitHub Actions

| Ablauf | Wann | Was |
|---|---|---|
| `pages.yml` | Webhook aus dem CMS, Push auf `main`, von Hand | Inhalte holen, bauen, auf Pages veröffentlichen |
| `inhalte-sichern.yml` | nachts um 3:17 Uhr | CMS-Stand als `data/*.json` ins Repository sichern |
| `check.yml` | jeder Push | Tests, Bau aus `data/`, Prüfung des CMS-Schemas |

`inhalte-sichern.yml` ist die Rückversicherung: Sollte Sanity ausfallen oder der Verein den
Anbieter wechseln wollen, liegen alle Inhalte lesbar im Git und die Seite lässt sich mit
`--quelle dateien` weiterbauen.

### Tests

```
python3 -m unittest discover -s tests
```

30 Prüfungen, alle ohne Netzzugriff — die Antworten des CMS werden nachgebaut. Die wichtigste ist
`RundeReise`: sie schickt die Inhalte aus `data/*.json` durch die Übertragung ins CMS, durch die
Abfrage und durch den Generator und vergleicht das Ergebnis mit dem direkten Bau. Passt ein
Feldname zwischen `tools/nach_sanity.py`, der Abfrage und `tools/sanity.py` nicht zusammen, fällt
das dort auf statt erst im Betrieb.

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

**Vom Verein zu liefern** — alles davon lässt sich im CMS eintragen, ohne den Code anzufassen.

1. **Fotos.** Sämtliche Bilder sind Platzhalter. Unter *Texte & Bilder* lassen sich Startseiten-
   und Sprachrohrbild hochladen. Echte Vereinsfotos wären der größte sichtbare Gewinn.
2. **Trainingszeiten** — weitgehend erledigt. Der Hallenbelegungsplan (gültig ab Juni 2026) ist
   vollständig eingepflegt: 58 Einheiten mit Tag, Uhrzeit, Ort, Gruppe und Übungsleitung.
   Nur vier Angebote stehen nicht darin (Volleyball, Reha-Sport, Kunstturnen, Pokern) und zeigen
   „Zeit auf Anfrage". Änderungen laufen über *Sportangebote*.
3. **Ansprechpartner je Abteilung.** Die Felder stehen bereit (Name, Telefon, E-Mail je Angebot),
   die Daten fehlen noch.
4. **PDFs**: Satzung, Ehrenordnung, Aufnahmeantrag, Sprachrohr — unter *Dokumente & PDFs*
   hochladen.
5. **Kinder- & Jugendschutzkonzept**: Text und Ansprechpersonen, unter *Texte & Bilder*.
6. **Öffnungszeiten der Geschäftsstelle**, unter *Stammdaten*.
7. **E-Mail-Adresse prüfen** — hinterlegt ist `vorstand@mtv-gelting-08.de`; zu bestätigen und
   gegebenenfalls unter *Stammdaten* zu ändern.
8. **Sponsorenlogos** inkl. Freigabe — unter *Sponsoren* hochladen. Bis dahin erscheint der Name.
9. ~~Vereinswappen~~ — erledigt. Die Originaldatei liegt unter `assets/img/logo.hd1.png` und
   ist in Header, Footer und Favicon eingebunden; das Vereinsblau ist daraus ausgelesen.

**Technisch zu klären**

10. ~~Inhaltspflege ohne Code~~ — erledigt. Sie läuft über das CMS; siehe
    [`studio/README.md`](studio/README.md).
11. **Mitglieder-Login.** Der Joomla-Auftritt hat einen Bereich für alle Mitglieder. Das CMS
    ersetzt nur die Redaktion, nicht diesen Bereich. Falls er gebraucht wird, ist zuerst zu
    klären, welche Inhalte er überhaupt zeigen soll — auf rein statischen Seiten gibt es dafür
    keine Lösung ohne zusätzlichen Dienst.
12. **Schriften lokal einbinden** statt über Google Fonts (Datenschutz). Bilder und PDFs werden
    bereits lokal ausgeliefert.
13. **Spielpläne**: aktuell Links zu den Verbänden. Einbettung wäre möglich, aber abhängig von
    den Schnittstellen der Verbände.
14. **Impressum und Datenschutzerklärung** müssen vor Veröffentlichung rechtlich geprüft werden.
    Beide Texte sind im CMS änderbar.
15. **Vor dem Livegang**: unter *Texte & Bilder → Sichtbarkeit* den Haken „Für Suchmaschinen
    sperren" entfernen und den Hinweisstreifen „Vorschau-Entwurf" leeren.

## GitHub Pages aktivieren

Einmalig unter **Settings → Pages** die Source auf **GitHub Actions** stellen. Der Weg „Deploy
from a branch" funktioniert nicht mehr: die HTML-Dateien liegen bewusst nicht mehr im
Repository, sondern entstehen bei jedem Lauf neu.

Danach den Ablauf einmal von Hand starten (*Actions → Website veröffentlichen → Run workflow*).
Jede weitere Veröffentlichung löst das CMS selbst aus.

Die Adresse lautet anschließend `https://oskar-hq.github.io/mtvgelting/`.

Was dafür in GitHub hinterlegt sein muss — Variable `SANITY_PROJEKT`, Secret `SANITY_TOKEN` und
der Webhook in Sanity — steht Schritt für Schritt in [`studio/README.md`](studio/README.md).

## Lokal ansehen

```
python3 tools/build.py --ziel _site
python3 -m http.server 8099 --directory _site
# http://localhost:8099
```

Ohne gesetztes `SANITY_PROJEKT` wird aus `data/*.json` gebaut — es braucht dafür also weder
CMS-Zugang noch Internet.

Die Redaktionsoberfläche zum Ausprobieren:

```
cd studio && npm install && npm run dev
# http://localhost:3333
```
