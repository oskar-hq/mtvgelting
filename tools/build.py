#!/usr/bin/env python3
"""Erzeugt die statischen Seiten fuer GitHub Pages aus den Dateien in data/."""

import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

V = json.loads((DATA / "verein.json").read_text(encoding="utf-8"))
A = json.loads((DATA / "angebote.json").read_text(encoding="utf-8"))

KATS = {k["id"]: k["name"] for k in A["kategorien"]}
ZG = {z["id"]: z["name"] for z in A["zielgruppen"]}
ANG = A["angebote"]

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]

DEMO_HINWEIS = "Gestaltungsentwurf, nicht die offizielle Website. Fotos sind Platzhalter."


def esc(s):
    return html.escape(str(s), quote=True)


def datum_lang(iso):
    if not iso:
        return ""
    y, m, d = iso.split("-")
    return "%d. %s %s" % (int(d), MONATE[int(m) - 1], y)


def media(tag, cls=""):
    """Platzhalter fuer ein spaeter einzusetzendes Vereinsfoto."""
    return ('<div class="media %s"><span class="media__tag">%s</span></div>'
            % (cls, esc(tag)))


NAV = [
    ("sportangebot.html", "Sportangebot"),
    ("termine.html", "Termine"),
    ("verein.html", "Verein"),
    ("mitglied-werden.html", "Mitglied werden"),
]


def head(title, desc, active, extra=""):
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {esc(V['kurzname'])}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="{esc(title)} — {esc(V['kurzname'])}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0E1116">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter+Tight:wght@600;700&family=Inter:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/css/site.css">
<link rel="icon" href="assets/img/logo.svg" type="image/svg+xml">
{extra}</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
<div class="demo-bar"><strong>Vorschau-Entwurf</strong> · {esc(DEMO_HINWEIS)}</div>
<header class="hdr">
  <div class="wrap hdr__inner">
    <a class="brand" href="index.html">
      <img class="brand__logo" src="assets/img/logo.svg" alt="" width="30" height="40">
      <span class="brand__txt">
        <span class="brand__mark">MTV Gelting</span>
        <span class="brand__sub">seit 1908</span>
      </span>
    </a>
    <nav class="nav" id="hauptnavigation" aria-label="Hauptnavigation" data-open="false">
      {navlinks(active)}
    </nav>
    <div class="hdr__cta">
      <a class="btn btn--primary btn--sm" href="mitglied-werden.html">Mitglied werden</a>
      <button class="burger" type="button" aria-expanded="false" aria-controls="hauptnavigation" aria-label="Menü öffnen"><span></span></button>
    </div>
  </div>
</header>
<main id="inhalt">
"""


def navlinks(active):
    out = []
    for href, name in NAV:
        cur = ' aria-current="page"' if href == active else ""
        out.append(f'<a href="{href}"{cur}>{esc(name)}</a>')
    return "\n      ".join(out)


def footer():
    adr = V["adresse"]
    kats = "".join(
        f'<li><a href="sportangebot.html?kategorie={k["id"]}">{esc(k["name"])}</a></li>'
        for k in A["kategorien"])
    return f"""</main>
<footer class="ftr">
  <div class="wrap">
    <div class="ftr__cols">
      <div>
        <img class="ftr__logo" src="assets/img/logo.svg" alt="" width="45" height="60">
        <p class="ftr__h">Kontakt</p>
        <ul class="ftr__list">
          <li>{esc(V['name'])}</li>
          <li>{esc(adr['strasse'])}<br>{esc(adr['plz'])} {esc(adr['ort'])}</li>
          <li><a href="tel:{esc(V['telefon_link'])}">{esc(V['telefon'])}</a></li>
          <li><a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a></li>
        </ul>
      </div>
      <div>
        <p class="ftr__h">Sportangebot</p>
        <ul class="ftr__list">{kats}</ul>
      </div>
      <div>
        <p class="ftr__h">Verein</p>
        <ul class="ftr__list">
          <li><a href="verein.html#vorstand">Vorstand</a></li>
          <li><a href="verein.html#geschaeftsstelle">Geschäftsstelle</a></li>
          <li><a href="verein.html#satzung">Satzungen &amp; Ordnungen</a></li>
          <li><a href="verein.html#sprachrohr">Sprachrohr</a></li>
          <li><a href="verein.html#jugendschutz">Kinder- &amp; Jugendschutz</a></li>
        </ul>
      </div>
      <div>
        <p class="ftr__h">Mehr</p>
        <ul class="ftr__list">
          <li><a href="mitglied-werden.html">Mitglied werden</a></li>
          <li><a href="{esc(V['shop'])}" rel="noopener">Vereinsshop</a></li>
          <li><a href="{esc(V['social']['facebook'])}" rel="noopener">Facebook</a></li>
          <li><a href="{esc(V['social']['instagram'])}" rel="noopener">Instagram</a></li>
        </ul>
      </div>
    </div>
    <div class="ftr__word" aria-hidden="true">MTV Gelting 08</div>
    <div class="ftr__bottom">
      <span>© {esc(V['name'])}</span>
      <a href="impressum.html">Impressum</a>
      <a href="datenschutz.html">Datenschutz</a>
      <span style="margin-left:auto">{esc(V['register'])}</span>
    </div>
  </div>
</footer>
<script src="assets/js/site.js"></script>
</body>
</html>
"""


def write(name, title, desc, active, body, extra=""):
    (ROOT / name).write_text(head(title, desc, active, extra) + body + footer(), encoding="utf-8")
    print("  ->", name)


# --------------------------------------------------------------------------
# Bausteine
# --------------------------------------------------------------------------

def zeit_pills(ang):
    """Trainingszeiten als Pillen; unbekannte Zeiten werden offen ausgewiesen."""
    if not ang["zeiten"]:
        return '<span class="pill pill--open">Zeit auf Anfrage</span>'
    out = []
    for z in ang["zeiten"]:
        if z.get("von"):
            out.append(f'<span class="pill">{esc(z["tag"][:2])} {esc(z["von"])}–{esc(z["bis"])}</span>')
        else:
            out.append(f'<span class="pill pill--open">{esc(z["tag"])} · Zeit folgt</span>')
    return "".join(out)


def card(ang):
    such = " ".join([ang["name"], ang["kurz"], KATS[ang["kategorie"]],
                     " ".join(ZG[z] for z in ang["zielgruppen"])]).lower()
    zg = " ".join(ang["zielgruppen"])
    zgtxt = ", ".join(ZG[z] for z in ang["zielgruppen"])
    return f"""      <article class="card" data-kategorie="{esc(ang['kategorie'])}" data-zielgruppen="{esc(zg)}" data-suche="{esc(such)}" id="{esc(ang['slug'])}">
        <p class="card__kat">{esc(KATS[ang['kategorie']])}</p>
        <h3 class="card__name">{esc(ang['name'])}</h3>
        <p class="card__kurz">{esc(ang['kurz'])}</p>
        <div class="card__zeit">{zeit_pills(ang)}</div>
        <details>
          <summary>Details</summary>
          <p>{esc(ang['text'])}</p>
          <p class="card__meta">Ort: {esc(ang['ort'])} &nbsp;·&nbsp; Für: {esc(zgtxt)}</p>
        </details>
      </article>"""


def kategorie_tiles():
    out = []
    for k in A["kategorien"]:
        items = [a for a in ANG if a["kategorie"] == k["id"]]
        namen = ", ".join(a["name"] for a in items[:4])
        if len(items) > 4:
            namen += " u. a."
        out.append(f"""      <a class="tile" href="sportangebot.html?kategorie={k['id']}">
        <span class="tile__count">{len(items):02d} Angebote</span>
        <span class="tile__name">{esc(k['name'])}</span>
        <span class="tile__list">{esc(namen)}</span>
      </a>""")
    return "\n".join(out)


def wochenplan():
    """Wochenplan aus den hinterlegten Trainingszeiten."""
    rows = []
    for tag in WOCHENTAGE:
        eintraege = []
        for a in ANG:
            for z in a["zeiten"]:
                if z["tag"] == tag:
                    eintraege.append((z.get("von") or "", z.get("bis") or "", a, z))
        eintraege.sort(key=lambda e: e[0] or "zz")
        for i, (von, bis, a, z) in enumerate(eintraege):
            tagzelle = f'<td class="t-time"><strong>{esc(tag)}</strong></td>' if i == 0 \
                else '<td class="t-time"></td>'
            zeit = f"{esc(von)}–{esc(bis)}" if von else '<span class="muted">Zeit folgt</span>'
            rows.append(f"""        <tr>
          {tagzelle}
          <td class="t-time">{zeit}</td>
          <td class="t-name"><a href="sportangebot.html#{esc(a['slug'])}" style="text-decoration:none">{esc(a['name'])}</a></td>
          <td>{esc(z.get('ort') or a['ort'])}</td>
          <td class="muted">{esc(KATS[a['kategorie']])}</td>
        </tr>""")
    return "\n".join(rows)


# --------------------------------------------------------------------------
# Seiten
# --------------------------------------------------------------------------

def seite_start():
    news = "".join(f"""      <article class="news__item">
        <p class="news__date">{esc(datum_lang(n['datum']))}</p>
        <div>
          <h3 class="news__title">{esc(n['titel'])}</h3>
          <p class="news__text">{esc(n['text'])}</p>
        </div>
        <p class="news__kat">{esc(n['kategorie'])}</p>
      </article>""" for n in V["news"][:4])

    sp = list(V["sponsoren"])
    sp += [""] * (-len(sp) % 12)
    sponsoren = "".join(
        (f'<div class="sponsor">{esc(s)}</div>' if s
         else '<div class="sponsor" aria-hidden="true"></div>') for s in sp)
    ticker_items = "".join(f"<span>{esc(k['name'])}</span>" for k in A["kategorien"]) * 2

    body = f"""
<section class="hero">
  <div class="wrap">
    <p class="label">Männer-Turn-Verein Gelting von 1908 e.V.</p>
    <h1 class="display">Sport für alle.<br><span class="hero__accent">In Gelting.</span></h1>
    <div class="hero__grid">
      <div class="hero__media">
        {media('Vereinsfoto folgt · Hero', 'media--wide')}
      </div>
      <div class="hero__meta">
        <p class="lead">{esc(V['claim'])} {len(ANG)} Angebote vom Eltern-Kind-Turnen bis zum Seniorensport — an einem Ort, in einer Übersicht.</p>
        <div class="btn-row">
          <a class="btn btn--primary" href="sportangebot.html">Angebot finden <span class="arw">→</span></a>
          <a class="btn" href="mitglied-werden.html">Mitglied werden</a>
        </div>
        <div class="hero__stats">
          <div><div class="stat__num">{len(ANG)}</div><div class="stat__txt">Sportangebote</div></div>
          <div><div class="stat__num">5</div><div class="stat__txt">Abteilungen</div></div>
          <div><div class="stat__num">{V['gegruendet']}</div><div class="stat__txt">gegründet</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="ticker" aria-hidden="true"><div class="ticker__track">{ticker_items}</div></div>

<section class="section">
  <div class="wrap">
    <div class="shead">
      <div>
        <p class="label">Sportangebot</p>
        <h2 class="h1">Was möchtest<br>du machen?</h2>
      </div>
      <div class="shead__aside">
        <p class="lead" style="margin-left:auto">Fünf Bereiche, {len(ANG)} Angebote. Wähle einen Bereich — oder filtere direkt nach Alter und Sportart.</p>
        <p style="margin-top:1rem"><a class="btn btn--sm" href="sportangebot.html">Alle Angebote <span class="arw">→</span></a></p>
      </div>
    </div>
    <div class="tiles">
{kategorie_tiles()}
    </div>
  </div>
</section>

<section class="section section--line">
  <div class="wrap">
    <div class="split">
      <div>
        <p class="label label--blue">Schnell gefunden</p>
        <h2 class="h2">Trainingszeiten,<br>Spielpläne, Termine.</h2>
        <p class="lead" style="margin-top:1.25rem">Alle Zeiten in einem Wochenplan statt verteilt auf dreißig Unterseiten. Dazu die Spielpläne der Mannschaften und die festen Termine im Vereinsjahr.</p>
        <p style="margin-top:1.5rem"><a class="btn" href="termine.html">Zum Wochenplan <span class="arw">→</span></a></p>
      </div>
      {media('Vereinsfoto folgt · Training', 'media--wide')}
    </div>
  </div>
</section>

<section class="section section--line">
  <div class="wrap">
    <div class="shead">
      <div><p class="label">Aktuelles</p><h2 class="h2">Aus dem Verein</h2></div>
    </div>
    <div class="news">
{news}
    </div>
  </div>
</section>

<section class="section section--ink">
  <div class="wrap">
    <div class="cta">
      <div>
        <p class="label">Mitglied werden</p>
        <h2 class="h1">Ab 7 € im Monat<br>alles ausprobieren.</h2>
      </div>
      <div>
        <p class="lead">Ein Beitrag, alle Angebote. Kinder und Jugendliche zahlen 7 €, Erwachsene 11 €, Familien 22 € im Monat — und dürfen jede Sparte nutzen.</p>
        <p style="margin-top:1.5rem"><a class="btn btn--light" href="mitglied-werden.html">Beitrag &amp; Anmeldung <span class="arw">→</span></a></p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="shead">
      <div><p class="label">Partner</p><h2 class="h2">Unsere Förderer</h2></div>
      <div class="shead__aside"><p class="muted small">Der Vereinssport in Gelting lebt von der Unterstützung aus der Region.</p></div>
    </div>
    <div class="sponsors">{sponsoren}</div>
  </div>
</section>
"""
    write("index.html", "Sport für alle in Gelting",
          "MTV Gelting 08 — %d Sportangebote für Kinder, Jugendliche, Erwachsene und Senioren in Gelting." % len(ANG),
          "index.html", body)


def seite_sportangebot():
    kat_chips = '<button class="chip" data-group="kategorie" data-value="alle" aria-pressed="true">Alle</button>'
    kat_chips += "".join(
        f'<button class="chip" data-group="kategorie" data-value="{k["id"]}" aria-pressed="false">{esc(k["name"])}</button>'
        for k in A["kategorien"])
    zg_chips = '<button class="chip" data-group="zielgruppe" data-value="alle" aria-pressed="true">Alle</button>'
    zg_chips += "".join(
        f'<button class="chip" data-group="zielgruppe" data-value="{z["id"]}" aria-pressed="false">{esc(z["name"])}</button>'
        for z in A["zielgruppen"])
    cards = "\n".join(card(a) for a in ANG)

    body = f"""
<section class="section section--tight">
  <div class="wrap">
    <p class="label">Sportangebot</p>
    <h1 class="h1">{len(ANG)} Angebote.<br>Eine Seite.</h1>
    <p class="lead" style="margin-top:1.5rem">Filtere nach Bereich oder Alter — oder such direkt nach einer Sportart. Für Details auf „Details“ klicken.</p>
  </div>
</section>

<section class="section--tight" style="padding-top:0">
  <div class="wrap">
    <div class="filters">
      <div class="filters__row">
        <span class="filters__legend" id="lg-bereich">Bereich</span>
        <div class="filters__row" role="group" aria-labelledby="lg-bereich" style="gap:.5rem">{kat_chips}</div>
      </div>
      <div class="filters__row">
        <span class="filters__legend" id="lg-fuer">Für wen</span>
        <div class="filters__row" role="group" aria-labelledby="lg-fuer" style="gap:.5rem">{zg_chips}</div>
      </div>
      <div class="filters__row" style="justify-content:space-between">
        <label class="searchbox">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
          <input type="search" id="suche" placeholder="Sportart suchen …" aria-label="Sportart suchen">
        </label>
        <span class="result-count" id="treffer" role="status">{len(ANG)} Angebote</span>
      </div>
    </div>

    <div class="cards" id="angebote">
{cards}
    </div>
    <p class="empty" id="keine-treffer" hidden>Keine Angebote gefunden. Filter zurücksetzen oder <a href="verein.html#geschaeftsstelle">Geschäftsstelle fragen</a>.</p>

    <p class="note" style="margin-top:2.5rem">Trainingszeiten mit dem Hinweis „Zeit auf Anfrage“ liegen für diesen Entwurf noch nicht vor und werden vom Verein ergänzt. Alle vorhandenen Zeiten stehen im <a href="termine.html">Wochenplan</a>.</p>
  </div>
</section>
"""
    write("sportangebot.html", "Sportangebot",
          "Alle %d Sportangebote des MTV Gelting 08 auf einen Blick — filterbar nach Bereich und Alter." % len(ANG),
          "sportangebot.html", body)


def seite_termine():
    termine = "".join(f"""      <article class="news__item">
        <p class="news__date">{esc(datum_lang(t['datum']) or t['zeit'])}</p>
        <div>
          <h3 class="news__title">{esc(t['titel'])}</h3>
          <p class="news__text">{esc(t['text'])}</p>
        </div>
        <p class="news__kat">{esc(t['ort'])}</p>
      </article>""" for t in V["termine"])

    plaene = "".join(
        (f'<li><a href="{esc(p["url"])}" rel="noopener">{esc(p["name"])} — {esc(p["quelle"])} →</a></li>'
         if p["url"] else
         f'<li>{esc(p["name"])} <span class="muted">— über die {esc(p["quelle"])}</span></li>')
        for p in V["spielplaene"])

    body = f"""
<section class="section section--tight">
  <div class="wrap">
    <p class="label">Termine</p>
    <h1 class="h1">Wochenplan &amp;<br>Spieltage.</h1>
    <p class="lead" style="margin-top:1.5rem">Alle Trainingszeiten in einer Tabelle, dazu Spielpläne und die festen Termine im Vereinsjahr.</p>
  </div>
</section>

<section class="section--tight" style="padding-top:0">
  <div class="wrap">
    <div class="table-scroll">
      <table class="plan">
        <caption class="visually-hidden" style="position:absolute;left:-9999px">Trainingszeiten nach Wochentag</caption>
        <thead>
          <tr><th scope="col">Tag</th><th scope="col">Zeit</th><th scope="col">Angebot</th><th scope="col">Ort</th><th scope="col">Bereich</th></tr>
        </thead>
        <tbody>
{wochenplan()}
        </tbody>
      </table>
    </div>
    <p class="note" style="margin-top:1.5rem">Dieser Plan zeigt die Zeiten, die aus dem öffentlichen Auftritt hervorgehen. Die übrigen Abteilungen tragen ihre Zeiten nach — danach ersetzt diese eine Tabelle sämtliche Zeitangaben auf den Einzelseiten.</p>
  </div>
</section>

<section class="section section--line">
  <div class="wrap">
    <div class="split">
      <div>
        <p class="label label--blue">Spielbetrieb</p>
        <h2 class="h2">Spielpläne</h2>
        <p class="lead" style="margin-top:1rem">Die Ansetzungen der Mannschaften laufen über die Verbände — hier direkt verlinkt statt in Einzelseiten versteckt.</p>
      </div>
      <ul class="ftr__list" style="font-size:1rem;gap:.85rem;list-style:none;padding:0;border-top:1px solid var(--line)">
        {plaene}
      </ul>
    </div>
  </div>
</section>

<section class="section section--line">
  <div class="wrap">
    <div class="shead"><div><p class="label">Vereinsjahr</p><h2 class="h2">Feste Termine</h2></div></div>
    <div class="news">
{termine}
    </div>
  </div>
</section>
"""
    write("termine.html", "Termine & Trainingszeiten",
          "Trainingszeiten, Spielpläne und Vereinstermine des MTV Gelting 08 in einer Übersicht.",
          "termine.html", body)


def seite_verein():
    p26 = "".join(f"""        <div class="person">
          <p class="person__name">{esc(p['name'])}</p>
          <p class="person__role">{esc(p['rolle'])}{' · § 26 BGB' if p['paragraf26'] else ''}</p>
        </div>""" for p in V["vorstand"])
    adr = V["adresse"]

    body = f"""
<section class="section section--tight">
  <div class="wrap">
    <p class="label">Unser Verein</p>
    <h1 class="h1">Wer wir sind.</h1>
    <p class="lead" style="margin-top:1.5rem">{esc(V['claim'])} Gegründet {V['gegruendet']} — heute mit {len(ANG)} Angeboten in fünf Bereichen.</p>
  </div>
</section>

<section class="section--tight" style="padding-top:0">
  <div class="wrap">
    <div class="split split--aside">
      <nav class="anchor-nav" aria-label="Auf dieser Seite">
        <a href="#vorstand">Vorstand</a>
        <a href="#geschaeftsstelle">Geschäftsstelle</a>
        <a href="#satzung">Satzungen &amp; Ordnungen</a>
        <a href="#sprachrohr">Sprachrohr</a>
        <a href="#jugendschutz">Kinder- &amp; Jugendschutz</a>
      </nav>

      <div>
        <section id="vorstand" style="scroll-margin-top:100px">
          <h2 class="h2">Vorstand</h2>
          <p class="lead" style="margin:1rem 0 1.75rem">Der Vorstand führt den Verein ehrenamtlich. Die drei erstgenannten Personen vertreten den MTV Gelting 08 nach § 26 BGB.</p>
          <div class="people">
{p26}
          </div>
        </section>

        <section id="geschaeftsstelle" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Geschäftsstelle</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">Erste Anlaufstelle für Mitgliedschaft, Beiträge, Vereinsbus und alle organisatorischen Fragen.</p>
          <dl class="facts">
            <div><dt>Anschrift</dt><dd>{esc(adr['strasse'])}, {esc(adr['plz'])} {esc(adr['ort'])}</dd></div>
            <div><dt>Telefon</dt><dd><a href="tel:{esc(V['telefon_link'])}">{esc(V['telefon'])}</a></dd></div>
            <div><dt>Telefax</dt><dd>{esc(V['telefax'])}</dd></div>
            <div><dt>E-Mail</dt><dd><a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a></dd></div>
            <div><dt>Register</dt><dd>{esc(V['register'])}</dd></div>
          </dl>
          <p class="note" style="margin-top:1.5rem">Öffnungszeiten der Geschäftsstelle werden vom Verein ergänzt.</p>
        </section>

        <section id="satzung" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Satzungen &amp; Ordnungen</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">Satzung, Beitragsordnung und weitere Ordnungen des Vereins zum Nachlesen.</p>
          <dl class="facts">
            <div><dt>Satzung</dt><dd>PDF wird vom Verein bereitgestellt</dd></div>
            <div><dt>Beitragsordnung</dt><dd>Übersicht der Beiträge auf <a href="mitglied-werden.html">Mitglied werden</a></dd></div>
            <div><dt>Ehrenordnung</dt><dd>PDF wird vom Verein bereitgestellt</dd></div>
          </dl>
        </section>

        <section id="sprachrohr" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Sprachrohr</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">Die Vereinszeitschrift erscheint jährlich mit Rückblicken aus allen Abteilungen, Terminen und Porträts.</p>
          {media('Titelbild Sprachrohr folgt', 'media--wide')}
          <p style="margin-top:1.25rem"><span class="btn btn--sm" style="opacity:.55;pointer-events:none">PDF folgt</span></p>
        </section>

        <section id="jugendschutz" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Kinder- &amp; Jugendschutz</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">Kinder und Jugendliche sollen sich im Verein sicher fühlen. Der MTV Gelting 08 arbeitet dafür mit einem Schutzkonzept und benennt feste Ansprechpersonen.</p>
          <p class="note">Konzepttext und Ansprechpersonen werden vom Verein ergänzt.</p>
        </section>
      </div>
    </div>
  </div>
</section>
"""
    write("verein.html", "Unser Verein",
          "Vorstand, Geschäftsstelle, Satzungen, Sprachrohr und Kinderschutz des MTV Gelting 08.",
          "verein.html", body)


def seite_mitglied():
    rates = "".join(f"""      <div class="rate">
        <div class="rate__price">{esc(b['monat'].replace(' €',''))}<span style="font-size:.5em"> €</span></div>
        <div class="rate__per">pro Monat · {esc(b['jahr'])} im Jahr</div>
        <div class="rate__grp">{esc(b['gruppe'])}</div>
      </div>""" for b in V["beitraege"])

    body = f"""
<section class="section section--tight">
  <div class="wrap">
    <p class="label">Mitglied werden</p>
    <h1 class="h1">Ein Beitrag.<br>Alle Angebote.</h1>
    <p class="lead" style="margin-top:1.5rem">Als Mitglied kannst du jedes der {len(ANG)} Angebote nutzen — ohne Zusatzgebühr je Sparte. Probetraining ist jederzeit möglich.</p>
  </div>
</section>

<section class="section--tight" style="padding-top:0">
  <div class="wrap">
    <div class="rates">
{rates}
    </div>
    <p class="note" style="margin-top:1.5rem">{esc(V['beitrag_hinweis'])}</p>
  </div>
</section>

<section class="section section--line">
  <div class="wrap">
    <div class="shead"><div><p class="label label--blue">So geht's</p><h2 class="h2">In drei Schritten dabei</h2></div></div>
    <div class="steps">
      <div class="step">
        <h3 class="h3">Angebot aussuchen</h3>
        <p>Im <a href="sportangebot.html">Sportangebot</a> nach Alter oder Bereich filtern und die passende Gruppe finden.</p>
      </div>
      <div class="step">
        <h3 class="h3">Probetraining</h3>
        <p>Einfach zur im <a href="termine.html">Wochenplan</a> genannten Zeit vorbeikommen. Ein Anruf vorab schadet nicht, ist aber kein Muss.</p>
      </div>
      <div class="step">
        <h3 class="h3">Aufnahmeantrag</h3>
        <p>Antrag ausfüllen und in der Geschäftsstelle abgeben oder per Post schicken. Der Beitrag wird per Lastschrift eingezogen.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--ink">
  <div class="wrap">
    <div class="cta">
      <div>
        <p class="label">Aufnahmeantrag</p>
        <h2 class="h2">Fragen? Ruf einfach an.</h2>
        <p class="lead" style="margin-top:1rem">Die Geschäftsstelle hilft bei Beiträgen, Anträgen und der Frage, welches Angebot passt.</p>
      </div>
      <div class="btn-row">
        <a class="btn btn--light" href="tel:{esc(V['telefon_link'])}">{esc(V['telefon'])}</a>
        <a class="btn btn--light" href="mailto:{esc(V['email'])}">E-Mail schreiben</a>
      </div>
    </div>
    <p class="small" style="margin-top:2rem;color:rgba(246,246,242,.55)">Aufnahmeantrag als PDF und ein Online-Formular werden ergänzt, sobald der Verein die Unterlagen bereitstellt. Für Familien, die den Beitrag nicht aufbringen können, gibt es die Aktion „Alle Kids treiben Sport!“.</p>
  </div>
</section>
"""
    write("mitglied-werden.html", "Mitglied werden",
          "Beiträge, Ablauf und Anmeldung beim MTV Gelting 08 — ab 7 € im Monat.",
          "mitglied-werden.html", body)


def seite_impressum():
    adr = V["adresse"]
    p26 = ", ".join(p["name"] for p in V["vorstand"] if p["paragraf26"])
    body = f"""
<section class="section">
  <div class="wrap">
    <p class="label">Rechtliches</p>
    <h1 class="h1">Impressum</h1>
    <div class="prose" style="margin-top:2.5rem">
      <h2 class="h3">Angaben gemäß § 5 DDG</h2>
      <p>{esc(V['name'])}<br>{esc(adr['strasse'])}<br>{esc(adr['plz'])} {esc(adr['ort'])}</p>
      <h2 class="h3">Vertreten durch</h2>
      <p>Vorstand gemäß § 26 BGB: {esc(p26)}</p>
      <h2 class="h3">Kontakt</h2>
      <p>Telefon: <a href="tel:{esc(V['telefon_link'])}">{esc(V['telefon'])}</a><br>
         Telefax: {esc(V['telefax'])}<br>
         E-Mail: <a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a></p>
      <h2 class="h3">Registereintrag</h2>
      <p>{esc(V['register'])}</p>
      <h2 class="h3">Verantwortlich für den Inhalt</h2>
      <p>{esc(V['vorstand'][0]['name'])}, Anschrift wie oben.</p>
      <p class="note" style="margin-top:2rem">Dies ist ein Gestaltungsentwurf. Vor einer Veröffentlichung ist das Impressum vom Verein rechtlich zu prüfen und zu vervollständigen.</p>
    </div>
  </div>
</section>
"""
    write("impressum.html", "Impressum", "Impressum des MTV Gelting 08.", "", body)


def seite_datenschutz():
    body = f"""
<section class="section">
  <div class="wrap">
    <p class="label">Rechtliches</p>
    <h1 class="h1">Datenschutz</h1>
    <div class="prose" style="margin-top:2.5rem">
      <h2 class="h3">Verantwortliche Stelle</h2>
      <p>{esc(V['name'])}, {esc(V['adresse']['strasse'])}, {esc(V['adresse']['plz'])} {esc(V['adresse']['ort'])},
         E-Mail <a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a>.</p>

      <h2 class="h3">Hosting</h2>
      <p>Diese Seiten werden als statische Website über GitHub Pages ausgeliefert (GitHub Inc.). Beim Abruf verarbeitet der Anbieter technisch notwendige Verbindungsdaten wie IP-Adresse, Zeitpunkt und aufgerufene Datei.</p>

      <h2 class="h3">Cookies und Tracking</h2>
      <p>Diese Website setzt keine Cookies und bindet keine Analyse- oder Trackingdienste ein.</p>

      <h2 class="h3">Schriftarten</h2>
      <p>Die Seite lädt Schriftarten von Google Fonts. Dabei wird eine Verbindung zu Servern von Google hergestellt. Für den Livegang empfehlen wir, die Schriften lokal einzubinden, sodass diese Verbindung entfällt.</p>

      <h2 class="h3">Externe Links</h2>
      <p>Verlinkte Angebote wie der Vereinsshop, Facebook, Instagram und die Verbandsseiten sind eigenständige Dienste mit eigenen Datenschutzbestimmungen. Es werden erst beim Klick Daten übertragen.</p>

      <h2 class="h3">Ihre Rechte</h2>
      <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie ein Beschwerderecht bei einer Aufsichtsbehörde.</p>

      <p class="note" style="margin-top:2rem">Dies ist ein Gestaltungsentwurf. Vor einer Veröffentlichung ist die Datenschutzerklärung vom Verein rechtlich zu prüfen und an die tatsächlich eingesetzten Dienste anzupassen.</p>
    </div>
  </div>
</section>
"""
    write("datenschutz.html", "Datenschutz", "Datenschutzerklärung des MTV Gelting 08.", "", body)


def main():
    print("Baue Seiten …")
    seite_start()
    seite_sportangebot()
    seite_termine()
    seite_verein()
    seite_mitglied()
    seite_impressum()
    seite_datenschutz()
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print("Fertig: %d Angebote, %d Kategorien." % (len(ANG), len(A["kategorien"])))


if __name__ == "__main__":
    main()
