#!/usr/bin/env python3
"""Erzeugt die Seiten des MTV Gelting 08 aus den Vereinsdaten.

Der Renderer bekommt die Daten als zwei Dictionaries uebergeben (``V`` mit den
Vereinsdaten, ``A`` mit den Sportangeboten) und liefert fertiges HTML zurueck.
Damit laesst sich dieselbe Website sowohl live aus der Datenbank ausliefern
(``app/__init__.py``) als auch als statische Dateien exportieren
(``tools/build.py``).
"""

import html
import re

WOCHENTAGE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]

SEITEN = ["index.html", "sportangebot.html", "termine.html", "verein.html",
          "mitglied-werden.html", "impressum.html", "datenschutz.html"]

NAV = [
    ("sportangebot.html", "Sportangebot"),
    ("termine.html", "Termine"),
    ("verein.html", "Verein"),
    ("mitglied-werden.html", "Mitglied werden"),
]


def esc(s):
    """HTML-sicher ausgeben; ``None`` wird zu einer leeren Zeichenkette."""
    return html.escape("" if s is None else str(s), quote=True)


def absaetze(text):
    """Mehrzeiligen Pflegetext in Absaetze umsetzen."""
    if not text:
        return ""
    teile = [t.strip() for t in re.split(r"\n\s*\n", str(text).strip()) if t.strip()]
    return "".join("<p>%s</p>" % esc(t).replace("\n", "<br>") for t in teile)


def zeilen(text):
    """Mehrzeiligen Pflegetext als eine Zeile mit Umbruechen ausgeben."""
    if not text:
        return ""
    return esc(str(text).strip()).replace("\n", "<br>")


def datum_lang(iso):
    if not iso:
        return ""
    try:
        y, m, d = str(iso).split("-")
        return "%d. %s %s" % (int(d), MONATE[int(m) - 1], y)
    except (ValueError, IndexError):
        return str(iso)


def preis_zahl(text):
    """'7,00 €' -> 7.0; unlesbare Angaben ergeben None."""
    if not text:
        return None
    treffer = re.search(r"(\d+(?:[.,]\d+)?)", str(text))
    if not treffer:
        return None
    return float(treffer.group(1).replace(",", "."))


def preis_kurz(betrag):
    """7.0 -> '7', 7.5 -> '7,50'."""
    if betrag is None:
        return ""
    if abs(betrag - round(betrag)) < 0.005:
        return "%d" % round(betrag)
    return ("%.2f" % betrag).replace(".", ",")


def media(tag, cls=""):
    """Platzhalter fuer ein spaeter einzusetzendes Vereinsfoto."""
    return ('<div class="media %s"><span class="media__tag">%s</span></div>'
            % (cls, esc(tag)))


def bild(pfad, alt, tag, cls=""):
    """Hochgeladenes Bild, solange keins da ist der Platzhalter."""
    if not pfad:
        return media(tag, cls)
    return ('<div class="media %s"><img src="%s" alt="%s" loading="lazy"></div>'
            % (cls, esc(pfad), esc(alt)))


class Renderer:
    """Baut die Seiten aus einem Datensatz."""

    def __init__(self, V, A):
        self.V = V
        self.A = A
        self.KATS = {k["id"]: k["name"] for k in A["kategorien"]}
        self.ZG = {z["id"]: z["name"] for z in A["zielgruppen"]}
        self.ANG = A["angebote"]
        self.QUELLE = A.get("quelle", "")

    # ------------------------------------------------------------------
    # Rahmen
    # ------------------------------------------------------------------

    def navlinks(self, active):
        out = []
        for href, name in NAV:
            cur = ' aria-current="page"' if href == active else ""
            out.append(f'<a href="{href}"{cur}>{esc(name)}</a>')
        return "\n      ".join(out)

    def hinweisbalken(self):
        """Optionaler Hinweisstreifen ganz oben; der Teil vor dem ersten „·“ steht fett."""
        text = (self.V.get("hinweisbanner") or "").strip()
        if not text:
            return ""
        kopf, _, rest = text.partition("·")
        if rest.strip():
            inhalt = "<strong>%s</strong> · %s" % (esc(kopf.strip()), zeilen(rest.strip()))
        else:
            inhalt = zeilen(text)
        return f'<div class="demo-bar">{inhalt}</div>\n'

    def head(self, title, desc, active, extra=""):
        V = self.V
        robots = "noindex, nofollow" if self.V.get("suchmaschinen_sperren") else "index, follow"
        return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {esc(V['kurzname'])}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<meta property="og:title" content="{esc(title)} — {esc(V['kurzname'])}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta name="theme-color" content="#0E1116">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter+Tight:wght@600;700&family=Inter:wght@400;500&display=swap">
<link rel="stylesheet" href="assets/css/site.css">
<link rel="icon" href="assets/img/favicon.png" type="image/png" sizes="128x128">
{extra}</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
{self.hinweisbalken()}<header class="hdr">
  <div class="wrap hdr__inner">
    <a class="brand" href="index.html">
      <img class="brand__logo" src="assets/img/logo.png" alt="" width="225" height="300">
      <span class="brand__txt">
        <span class="brand__mark">{esc(V['kurzname'].replace(' 08', ''))}</span>
        <span class="brand__sub">seit {esc(V['gegruendet'])}</span>
      </span>
    </a>
    <nav class="nav" id="hauptnavigation" aria-label="Hauptnavigation" data-open="false">
      {self.navlinks(active)}
    </nav>
    <div class="hdr__cta">
      <a class="btn btn--primary btn--sm" href="mitglied-werden.html">Mitglied werden</a>
      <button class="burger" type="button" aria-expanded="false" aria-controls="hauptnavigation" aria-label="Menü öffnen"><span></span></button>
    </div>
  </div>
</header>
<main id="inhalt">
"""

    def footer(self):
        V, A = self.V, self.A
        adr = V["adresse"]
        kats = "".join(
            f'<li><a href="sportangebot.html?kategorie={k["id"]}">{esc(k["name"])}</a></li>'
            for k in A["kategorien"])
        social = []
        if V["social"].get("facebook"):
            social.append(f'<li><a href="{esc(V["social"]["facebook"])}" rel="noopener">Facebook</a></li>')
        if V["social"].get("instagram"):
            social.append(f'<li><a href="{esc(V["social"]["instagram"])}" rel="noopener">Instagram</a></li>')
        shop = f'<li><a href="{esc(V["shop"])}" rel="noopener">Vereinsshop</a></li>' if V.get("shop") else ""
        fax = f'<span style="margin-left:auto">{esc(V["register"])}</span>' if V.get("register") else ""
        admin = (f'<a class="ftr__admin" href="{esc(V["admin_url"])}">Vereinsintern anmelden</a>'
                 if V.get("admin_url") else "")
        return f"""</main>
<footer class="ftr">
  <div class="wrap">
    <div class="ftr__cols">
      <div>
        <img class="ftr__logo" src="assets/img/logo.png" alt="" width="225" height="300">
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
          {shop}{"".join(social)}
        </ul>
      </div>
    </div>
    <div class="ftr__word" aria-hidden="true">{esc(V['kurzname'])}</div>
    <div class="ftr__bottom">
      <span>© {esc(V['name'])}</span>
      <a href="impressum.html">Impressum</a>
      <a href="datenschutz.html">Datenschutz</a>
      {admin}
      {fax}
    </div>
  </div>
</footer>
<script src="assets/js/site.js"></script>
</body>
</html>
"""

    def seite(self, name, title, desc, active, body, extra=""):
        return self.head(title, desc, active, extra) + body + self.footer()

    # ------------------------------------------------------------------
    # Bausteine
    # ------------------------------------------------------------------

    @staticmethod
    def zeitspanne(z):
        """Zeitangabe einer Einheit; offene Enden bleiben als solche sichtbar."""
        if z.get("von") and z.get("bis"):
            return "%s–%s" % (z["von"], z["bis"])
        if z.get("von"):
            return "ab %s" % z["von"]
        return ""

    def zeit_pills(self, ang):
        """Kurzuebersicht der Trainingszeiten; lange Listen werden gekuerzt."""
        if not ang["zeiten"]:
            return '<span class="pill pill--open">Zeit auf Anfrage</span>'
        out = []
        for z in ang["zeiten"][:3]:
            sp = self.zeitspanne(z)
            if sp:
                out.append('<span class="pill">%s %s</span>' % (esc(z["tag"][:2]), esc(sp)))
            else:
                out.append('<span class="pill pill--open">%s</span>' % esc(z["tag"]))
        rest = len(ang["zeiten"]) - 3
        if rest > 0:
            out.append('<span class="pill pill--more">+%d weitere</span>' % rest)
        return "".join(out)

    def zeit_liste(self, ang):
        """Alle Einheiten eines Angebots als gestapelte Liste – passt in schmale Karten."""
        if not ang["zeiten"]:
            return ""
        items = []
        for z in ang["zeiten"]:
            kopf = "%s %s" % (z["tag"], self.zeitspanne(z) or "nach Absprache")
            meta = [z.get("ort") or ang["ort"]]
            if z.get("leitung"):
                meta.append(z["leitung"])
            gruppe = ('<span class="z-grp">%s</span>' % esc(z["gruppe"])) if z.get("gruppe") else ""
            hinweis = ('<span class="z-note">%s</span>' % esc(z["hinweis"])) if z.get("hinweis") else ""
            items.append('<li><span class="z-when">%s</span>%s<span class="z-meta">%s</span>%s</li>'
                         % (esc(kopf), gruppe, esc(" · ".join(x for x in meta if x)), hinweis))
        return '<ul class="zeiten">%s</ul>' % "".join(items)

    @staticmethod
    def kontaktzeile(ang):
        """Ansprechpartner der Abteilung, sofern gepflegt."""
        name = ang.get("leitung") or ""
        mail = ang.get("kontakt_email") or ""
        tel = ang.get("kontakt_telefon") or ""
        if not (name or mail or tel):
            return ""
        teile = []
        if name:
            teile.append(esc(name))
        if tel:
            teile.append('<a href="tel:%s">%s</a>' % (esc(re.sub(r"[^0-9+]", "", tel)), esc(tel)))
        if mail:
            teile.append('<a href="mailto:%s">%s</a>' % (esc(mail), esc(mail)))
        return ('<p class="card__kontakt"><span class="card__kontakt-h">Ansprechpartner</span>%s</p>'
                % " · ".join(teile))

    def card(self, ang):
        KATS, ZG = self.KATS, self.ZG
        such = " ".join([ang["name"], ang["kurz"], KATS.get(ang["kategorie"], ""),
                         " ".join(ZG.get(z, "") for z in ang["zielgruppen"])]
                        + [z.get("gruppe") or "" for z in ang["zeiten"]]
                        + [ang.get("leitung") or ""]).lower()
        zg = " ".join(ang["zielgruppen"])
        zgtxt = ", ".join(ZG.get(z, z) for z in ang["zielgruppen"])
        n = len(ang["zeiten"])
        summary = "Details" if n <= 1 else "Details & alle %d Zeiten" % n
        return f"""      <article class="card" data-kategorie="{esc(ang['kategorie'])}" data-zielgruppen="{esc(zg)}" data-suche="{esc(such)}" id="{esc(ang['slug'])}">
        <p class="card__kat">{esc(KATS.get(ang['kategorie'], ''))}</p>
        <h3 class="card__name">{esc(ang['name'])}</h3>
        <p class="card__kurz">{esc(ang['kurz'])}</p>
        <div class="card__zeit">{self.zeit_pills(ang)}</div>
        <details>
          <summary>{esc(summary)}</summary>
          {absaetze(ang['text'])}
          {self.zeit_liste(ang)}
          <p class="card__meta">Ort: {esc(ang['ort'])} &nbsp;·&nbsp; Für: {esc(zgtxt)}</p>
          {self.kontaktzeile(ang)}
        </details>
      </article>"""

    def kategorie_tiles(self):
        out = []
        for k in self.A["kategorien"]:
            items = [a for a in self.ANG if a["kategorie"] == k["id"]]
            namen = ", ".join(a["name"] for a in items[:4])
            if len(items) > 4:
                namen += " u. a."
            out.append(f"""      <a class="tile" href="sportangebot.html?kategorie={k['id']}">
        <span class="tile__count">{len(items):02d} Angebote</span>
        <span class="tile__name">{esc(k['name'])}</span>
        <span class="tile__list">{esc(namen)}</span>
      </a>""")
        return "\n".join(out)

    def wochenplan(self):
        """Alle Trainingszeiten aller Angebote, nach Wochentag und Uhrzeit."""
        rows = []
        for tag in WOCHENTAGE:
            eintraege = [(z, a) for a in self.ANG for z in a["zeiten"] if z["tag"] == tag]
            eintraege.sort(key=lambda e: e[0].get("von") or "zz")
            for i, (z, a) in enumerate(eintraege):
                tagzelle = ('<th scope="row" class="t-day">%s</th>' % esc(tag)) if i == 0 \
                    else '<td class="t-day"></td>'
                sp = self.zeitspanne(z)
                zeit = esc(sp) if sp else '<span class="muted">nach Absprache</span>'
                name = esc(a["name"])
                if z.get("gruppe"):
                    name += '<span class="t-grp">%s</span>' % esc(z["gruppe"])
                hinweis = ('<span class="t-note">%s</span>' % esc(z["hinweis"])) if z.get("hinweis") else ""
                rows.append("""        <tr>
          %s
          <td class="t-time">%s</td>
          <td class="t-name"><a href="sportangebot.html#%s">%s</a>%s</td>
          <td>%s</td>
          <td class="muted">%s</td>
        </tr>""" % (tagzelle, zeit, esc(a["slug"]), name, hinweis,
                    esc(z.get("ort") or a["ort"]), esc(z.get("leitung") or "–")))
        return "\n".join(rows)

    def sponsoren_kacheln(self):
        """Sponsorenraster – die Spaltenzahl ergibt sich aus der Menge (CSS auto-fit)."""
        sp = self.V["sponsoren"]
        if not sp:
            return '<p class="note">Partner werden ergänzt.</p>'
        out = []
        for s in sp:
            if s.get("logo"):
                inner = ('<img src="%s" alt="%s" loading="lazy">'
                         % (esc(s["logo"]), esc(s["name"])))
            else:
                inner = '<span class="sponsor__name">%s</span>' % esc(s["name"])
            if s.get("url"):
                out.append('<a class="sponsor" href="%s" rel="noopener" title="%s">%s</a>'
                           % (esc(s["url"]), esc(s["name"]), inner))
            else:
                out.append('<div class="sponsor" title="%s">%s</div>' % (esc(s["name"]), inner))
        return '<div class="sponsors" data-anzahl="%d">%s</div>' % (len(sp), "".join(out))

    def dokumente(self, bereich):
        return [d for d in self.V.get("dokumente", []) if d.get("bereich") == bereich]

    @staticmethod
    def dokument_zeile(d):
        ziel = d.get("datei") or d.get("url")
        if ziel:
            return '<a href="%s" rel="noopener">%s</a>' % (esc(ziel), esc(d.get("beschreibung") or "PDF öffnen"))
        return esc(d.get("beschreibung") or "wird vom Verein bereitgestellt")

    # ------------------------------------------------------------------
    # Seiten
    # ------------------------------------------------------------------

    def beitrag_saetze(self):
        """Ueberschrift und Fliesstext des Beitragsblocks aus den Beitraegen ableiten."""
        V = self.V
        aktive = [b for b in V["beitraege"] if b.get("aktiv", True)] or V["beitraege"]
        preise = [preis_zahl(b["monat"]) for b in aktive]
        preise = [p for p in preise if p is not None]
        if preise:
            titel = "Ab %s € im Monat<br>alles ausprobieren." % preis_kurz(min(preise))
        else:
            titel = "Ein Beitrag.<br>Alle Angebote."
        teile = []
        for b in aktive:
            name = b.get("kurz") or b["gruppe"]
            p = preis_zahl(b["monat"])
            teile.append("%s %s €" % (name, preis_kurz(p)) if p is not None else name)
        if teile:
            text = ("Ein Beitrag, alle Angebote. %s im Monat — und jede Sparte darf genutzt werden."
                    % ", ".join(teile))
        else:
            text = "Ein Beitrag, alle Angebote."
        return titel, text

    def seite_start(self):
        V, A, ANG = self.V, self.A, self.ANG
        news = "".join(f"""      <article class="news__item">
        <p class="news__date">{esc(datum_lang(n['datum']))}</p>
        <div>
          <h3 class="news__title">{esc(n['titel'])}</h3>
          <p class="news__text">{esc(n['text'])}</p>
        </div>
        <p class="news__kat">{esc(n['kategorie'])}</p>
      </article>""" for n in V["news"][:4])
        news_block = f"""
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
""" if news else ""

        ticker_items = "".join(f"<span>{esc(k['name'])}</span>" for k in A["kategorien"]) * 2
        cta_titel, cta_text = self.beitrag_saetze()
        n_zeiten = sum(len(a["zeiten"]) for a in ANG)

        body = f"""
<section class="hero">
  <div class="wrap">
    <p class="label">{esc(V['name'])}</p>
    <h1 class="display">{esc(V['start_titel'])}<br><span class="hero__accent">{esc(V['start_titel_akzent'])}</span></h1>
    <div class="hero__grid">
      <div class="hero__media">
        {bild(V.get('start_bild'), V['kurzname'], 'Vereinsfoto folgt · Hero', 'media--wide')}
      </div>
      <div class="hero__meta">
        <p class="lead">{esc(V['claim'])} {len(ANG)} Angebote vom Eltern-Kind-Turnen bis zum Seniorensport — an einem Ort, in einer Übersicht.</p>
        <div class="btn-row">
          <a class="btn btn--primary" href="sportangebot.html">Angebot finden <span class="arw">→</span></a>
          <a class="btn" href="mitglied-werden.html">Mitglied werden</a>
        </div>
        <div class="hero__stats">
          <div><div class="stat__num">{len(ANG)}</div><div class="stat__txt">Sportangebote</div></div>
          <div><div class="stat__num">{n_zeiten}</div><div class="stat__txt">Trainingszeiten</div></div>
          <div><div class="stat__num">{esc(V['gegruendet'])}</div><div class="stat__txt">gegründet</div></div>
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
        <p class="lead" style="margin-left:auto">{len(A['kategorien'])} Bereiche, {len(ANG)} Angebote. Wähle einen Bereich — oder filtere direkt nach Alter und Sportart.</p>
        <p style="margin-top:1rem"><a class="btn btn--sm" href="sportangebot.html">Alle Angebote <span class="arw">→</span></a></p>
      </div>
    </div>
    <div class="tiles">
{self.kategorie_tiles()}
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
      {bild(V.get('training_bild'), 'Training beim ' + V['kurzname'], 'Vereinsfoto folgt · Training', 'media--wide')}
    </div>
  </div>
</section>
{news_block}
<section class="section section--ink">
  <div class="wrap">
    <div class="cta">
      <div>
        <p class="label">Mitglied werden</p>
        <h2 class="h1">{cta_titel}</h2>
      </div>
      <div>
        <p class="lead">{esc(cta_text)}</p>
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
    {self.sponsoren_kacheln()}
  </div>
</section>
"""
        return self.seite("index.html", V["start_seitentitel"],
                          "%s — %d Sportangebote für Kinder, Jugendliche, Erwachsene und Senioren in %s."
                          % (V["kurzname"], len(ANG), V["adresse"]["ort"]),
                          "index.html", body)

    def seite_sportangebot(self):
        V, A, ANG = self.V, self.A, self.ANG
        kat_chips = '<button class="chip" data-group="kategorie" data-value="alle" aria-pressed="true">Alle</button>'
        kat_chips += "".join(
            f'<button class="chip" data-group="kategorie" data-value="{k["id"]}" aria-pressed="false">{esc(k["name"])}</button>'
            for k in A["kategorien"])
        zg_chips = '<button class="chip" data-group="zielgruppe" data-value="alle" aria-pressed="true">Alle</button>'
        zg_chips += "".join(
            f'<button class="chip" data-group="zielgruppe" data-value="{z["id"]}" aria-pressed="false">{esc(z["name"])}</button>'
            for z in A["zielgruppen"])
        cards = "\n".join(self.card(a) for a in ANG)
        ohne_zeiten = sum(1 for a in ANG if not a["zeiten"])
        quelle = ""
        if self.QUELLE:
            fehlend = ("%d Angebote sind dort nicht aufgeführt und zeigen deshalb „Zeit auf Anfrage“. "
                       % ohne_zeiten) if ohne_zeiten else ""
            quelle = (f'<p class="note" style="margin-top:2.5rem">Die Zeiten stammen aus dem '
                      f'{esc(self.QUELLE)}. {fehlend}Alle Zeiten im Überblick stehen im '
                      f'<a href="termine.html">Wochenplan</a>.</p>')

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
    {quelle}
  </div>
</section>
"""
        return self.seite("sportangebot.html", "Sportangebot",
                          "Alle %d Sportangebote des %s auf einen Blick — filterbar nach Bereich und Alter."
                          % (len(ANG), V["kurzname"]),
                          "sportangebot.html", body)

    def termin_karten(self):
        """Feste Termine, datierte zuerst; undatierte Dauerangebote ans Ende."""
        sortiert = sorted(self.V["termine"], key=lambda t: t["datum"] or "9999")
        out = []
        for t in sortiert:
            if t["datum"]:
                y, m, d = t["datum"].split("-")
                datum = ('<span class="event__day">%d.</span>'
                         '<span class="event__mon">%s</span>'
                         '<span class="event__yr">%s</span>'
                         % (int(d), esc(MONATE[int(m) - 1][:3]), esc(y)))
                attr = ' data-datum="%s"' % esc(t["datum"])
            else:
                datum = '<span class="event__open">%s</span>' % esc(t["zeit"])
                attr = ""
            meta = " · ".join(x for x in [t["zeit"] if t["datum"] else "", t["ort"]] if x)
            out.append(f"""      <article class="event"{attr}>
        <p class="event__date">{datum}</p>
        <div class="event__body">
          <h3 class="event__title">{esc(t['titel'])}</h3>
          <p class="event__meta">{esc(meta)}</p>
          <p class="event__text">{esc(t['text'])}</p>
        </div>
      </article>""")
        return "\n".join(out)

    def seite_termine(self):
        V, ANG = self.V, self.ANG
        plaene = "".join(
            (f'<li><a href="{esc(p["url"])}" rel="noopener">{esc(p["name"])} — {esc(p["quelle"])} →</a></li>'
             if p["url"] else
             f'<li>{esc(p["name"])} <span class="muted">— über die {esc(p["quelle"])}</span></li>')
            for p in V["spielplaene"])
        n_zeiten = sum(len(a["zeiten"]) for a in ANG)

        karten = self.termin_karten()
        termin_block = f"""
<section class="section--tight" style="padding-top:0">
  <div class="wrap">
    <div class="events">
{karten}
    </div>
  </div>
</section>
""" if karten else """
<section class="section--tight" style="padding-top:0">
  <div class="wrap"><p class="note">Zurzeit sind keine besonderen Termine eingetragen.</p></div>
</section>
"""
        plan_block = f"""
<section class="section section--line">
  <div class="wrap">
    <div class="split">
      <div>
        <p class="label label--blue">Spielbetrieb</p>
        <h2 class="h2">Spielpläne</h2>
        <p class="lead" style="margin-top:1rem">Die Ansetzungen der Mannschaften laufen über die Verbände — hier direkt verlinkt statt in Einzelseiten versteckt.</p>
      </div>
      <ul class="linklist">
        {plaene}
      </ul>
    </div>
  </div>
</section>
""" if plaene else ""
        quelle = (f'<p class="note" style="margin-top:1.5rem">Quelle: {esc(self.QUELLE)}.</p>'
                  if self.QUELLE else "")

        body = f"""
<section class="section section--tight">
  <div class="wrap">
    <p class="label">Termine</p>
    <h1 class="h1">Was als<br>Nächstes ansteht.</h1>
    <p class="lead" style="margin-top:1.5rem">Zuerst die festen Termine im Vereinsjahr, darunter der Wochenplan mit allen {n_zeiten} Trainingszeiten und die Spielpläne der Mannschaften.</p>
  </div>
</section>
{termin_block}
<section class="section section--line">
  <div class="wrap">
    <div class="shead">
      <div><p class="label label--blue">Woche für Woche</p><h2 class="h2">Wochenplan</h2></div>
      <div class="shead__aside"><p class="muted small">{n_zeiten} Trainingszeiten mit Ort und Übungsleitung</p></div>
    </div>
    <div class="table-scroll">
      <table class="plan">
        <caption style="position:absolute;left:-9999px">Trainingszeiten nach Wochentag</caption>
        <thead>
          <tr><th scope="col">Tag</th><th scope="col">Zeit</th><th scope="col">Angebot</th><th scope="col">Ort</th><th scope="col">Leitung</th></tr>
        </thead>
        <tbody>
{self.wochenplan()}
        </tbody>
      </table>
    </div>
    {quelle}
  </div>
</section>
{plan_block}"""
        return self.seite("termine.html", "Termine & Trainingszeiten",
                          "Vereinstermine, Wochenplan mit allen Trainingszeiten und Spielpläne des %s."
                          % V["kurzname"],
                          "termine.html", body)

    def seite_verein(self):
        V, ANG = self.V, self.ANG
        p26 = "".join(f"""        <div class="person">
          <p class="person__name">{esc(p['name'])}</p>
          <p class="person__role">{esc(p['rolle'])}{' · § 26 BGB' if p['paragraf26'] else ''}</p>
          {('<p class="person__kontakt"><a href="mailto:%s">%s</a></p>' % (esc(p['email']), esc(p['email']))) if p.get('email') else ''}
        </div>""" for p in V["vorstand"])
        adr = V["adresse"]

        oz = V.get("oeffnungszeiten") or ""
        oz_zeile = (f'<div><dt>Öffnungszeiten</dt><dd>{zeilen(oz)}</dd></div>' if oz.strip()
                    else "")
        oz_hinweis = "" if oz.strip() else \
            '<p class="note" style="margin-top:1.5rem">Öffnungszeiten der Geschäftsstelle werden vom Verein ergänzt.</p>'
        fax = f'<div><dt>Telefax</dt><dd>{esc(V["telefax"])}</dd></div>' if V.get("telefax") else ""
        reg = f'<div><dt>Register</dt><dd>{esc(V["register"])}</dd></div>' if V.get("register") else ""

        satzung = self.dokumente("satzung")
        satzung_liste = "".join(
            f'<div><dt>{esc(d["titel"])}</dt><dd>{self.dokument_zeile(d)}</dd></div>' for d in satzung)
        satzung_liste += ('<div><dt>Beitragsordnung</dt><dd>Übersicht der Beiträge auf '
                          '<a href="mitglied-werden.html">Mitglied werden</a></dd></div>')

        hefte = self.dokumente("sprachrohr")
        if hefte:
            heft_links = "".join(
                (f'<li><a class="btn btn--sm" href="{esc(d.get("datei") or d.get("url"))}" rel="noopener">{esc(d["titel"])}</a></li>'
                 if (d.get("datei") or d.get("url"))
                 else f'<li><span class="btn btn--sm" style="opacity:.55;pointer-events:none">{esc(d["titel"])} — folgt</span></li>')
                for d in hefte)
            heft_block = f'<ul class="doclist" style="margin-top:1.25rem">{heft_links}</ul>'
        else:
            heft_block = ('<p style="margin-top:1.25rem"><span class="btn btn--sm" '
                          'style="opacity:.55;pointer-events:none">PDF folgt</span></p>')

        js_text = V.get("jugendschutz_text") or ""
        js_block = absaetze(js_text) if js_text.strip() else \
            '<p class="note">Konzepttext und Ansprechpersonen werden vom Verein ergänzt.</p>'

        body = f"""
<section class="section section--tight">
  <div class="wrap">
    <p class="label">Unser Verein</p>
    <h1 class="h1">Wer wir sind.</h1>
    <p class="lead" style="margin-top:1.5rem">{esc(V['claim'])} Gegründet {esc(V['gegruendet'])} — heute mit {len(ANG)} Angeboten in {len(self.A['kategorien'])} Bereichen.</p>
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
          <p class="lead" style="margin:1rem 0 1.75rem">Der Vorstand führt den Verein ehrenamtlich. Die mit § 26 BGB gekennzeichneten Personen vertreten den {esc(V['kurzname'])} rechtlich.</p>
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
            {fax}
            <div><dt>E-Mail</dt><dd><a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a></dd></div>
            {oz_zeile}
            {reg}
          </dl>
          {oz_hinweis}
        </section>

        <section id="satzung" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Satzungen &amp; Ordnungen</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">Satzung, Beitragsordnung und weitere Ordnungen des Vereins zum Nachlesen.</p>
          <dl class="facts">
{satzung_liste}
          </dl>
        </section>

        <section id="sprachrohr" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Sprachrohr</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">{esc(V.get('sprachrohr_text') or 'Die Vereinszeitschrift erscheint jährlich mit Rückblicken aus allen Abteilungen, Terminen und Porträts.')}</p>
          {bild(V.get('sprachrohr_bild'), 'Titelbild Sprachrohr', 'Titelbild Sprachrohr folgt', 'media--wide')}
          {heft_block}
        </section>

        <section id="jugendschutz" style="scroll-margin-top:100px;margin-top:4rem">
          <h2 class="h2">Kinder- &amp; Jugendschutz</h2>
          <p class="lead" style="margin:1rem 0 1.5rem">Kinder und Jugendliche sollen sich im Verein sicher fühlen. Der {esc(V['kurzname'])} arbeitet dafür mit einem Schutzkonzept und benennt feste Ansprechpersonen.</p>
          {js_block}
        </section>
      </div>
    </div>
  </div>
</section>
"""
        return self.seite("verein.html", "Unser Verein",
                          "Vorstand, Geschäftsstelle, Satzungen, Sprachrohr und Kinderschutz des %s."
                          % V["kurzname"],
                          "verein.html", body)

    def seite_mitglied(self):
        V, ANG = self.V, self.ANG
        rates = "".join(f"""      <div class="rate">
        <div class="rate__price">{esc(preis_kurz(preis_zahl(b['monat'])) or b['monat'])}<span style="font-size:.5em"> €</span></div>
        <div class="rate__per">pro Monat · {esc(b['jahr'])} im Jahr</div>
        <div class="rate__grp">{esc(b['gruppe'])}</div>
      </div>""" for b in V["beitraege"])
        rates_block = f"""    <div class="rates">
{rates}
    </div>
""" if rates else '    <p class="note">Die Beiträge werden vom Verein ergänzt.</p>\n'
        hinweis = (f'<p class="note" style="margin-top:1.5rem">{zeilen(V["beitrag_hinweis"])}</p>'
                   if V.get("beitrag_hinweis") else "")

        antrag = self.dokumente("antrag")
        antrag_links = "".join(
            f'<a class="btn btn--light" href="{esc(d.get("datei") or d.get("url"))}" rel="noopener">{esc(d["titel"])}</a>'
            for d in antrag if (d.get("datei") or d.get("url")))
        antrag_hinweis = "" if antrag_links else \
            ('<p class="small" style="margin-top:2rem;color:rgba(246,246,242,.55)">Der Aufnahmeantrag als PDF '
             'wird ergänzt, sobald der Verein die Unterlagen bereitstellt.</p>')

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
{rates_block}    {hinweis}
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
        {antrag_links}
      </div>
    </div>
    {antrag_hinweis}
  </div>
</section>
"""
        return self.seite("mitglied-werden.html", "Mitglied werden",
                          "Beiträge, Ablauf und Anmeldung beim %s." % V["kurzname"],
                          "mitglied-werden.html", body)

    def seite_impressum(self):
        V = self.V
        adr = V["adresse"]
        p26 = ", ".join(p["name"] for p in V["vorstand"] if p["paragraf26"])
        verantwortlich = V["vorstand"][0]["name"] if V["vorstand"] else ""
        rechtshinweis = (f'<p class="note" style="margin-top:2rem">{zeilen(V["impressum_hinweis"])}</p>'
                         if V.get("impressum_hinweis") else "")
        fax = f'<br>Telefax: {esc(V["telefax"])}' if V.get("telefax") else ""
        reg = (f'<h2 class="h3">Registereintrag</h2><p>{esc(V["register"])}</p>'
               if V.get("register") else "")
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
      <p>Telefon: <a href="tel:{esc(V['telefon_link'])}">{esc(V['telefon'])}</a>{fax}<br>
         E-Mail: <a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a></p>
      {reg}
      <h2 class="h3">Verantwortlich für den Inhalt</h2>
      <p>{esc(verantwortlich)}, Anschrift wie oben.</p>
      {rechtshinweis}
    </div>
  </div>
</section>
"""
        return self.seite("impressum.html", "Impressum", "Impressum des %s." % V["kurzname"], "", body)

    def seite_datenschutz(self):
        V = self.V
        adr = V["adresse"]
        text = V.get("datenschutz_text") or ""
        inhalt = absaetze(text) if text.strip() else f"""
      <h2 class="h3">Verantwortliche Stelle</h2>
      <p>{esc(V['name'])}, {esc(adr['strasse'])}, {esc(adr['plz'])} {esc(adr['ort'])},
         E-Mail <a href="mailto:{esc(V['email'])}">{esc(V['email'])}</a>.</p>

      <h2 class="h3">Cookies und Tracking</h2>
      <p>Diese Website bindet keine Analyse- oder Trackingdienste ein. Im vereinsinternen
         Verwaltungsbereich wird ein technisch notwendiges Sitzungs-Cookie gesetzt, das nur
         angemeldete Personen betrifft und beim Abmelden endet.</p>

      <h2 class="h3">Schriftarten</h2>
      <p>Die Seite lädt Schriftarten von Google Fonts. Dabei wird eine Verbindung zu Servern von Google hergestellt.</p>

      <h2 class="h3">Externe Links</h2>
      <p>Verlinkte Angebote wie der Vereinsshop, Facebook, Instagram und die Verbandsseiten sind eigenständige Dienste mit eigenen Datenschutzbestimmungen. Es werden erst beim Klick Daten übertragen.</p>

      <h2 class="h3">Ihre Rechte</h2>
      <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit sowie ein Beschwerderecht bei einer Aufsichtsbehörde.</p>
"""
        hinweis = (f'<p class="note" style="margin-top:2rem">{zeilen(V["datenschutz_hinweis"])}</p>'
                   if V.get("datenschutz_hinweis") else "")
        body = f"""
<section class="section">
  <div class="wrap">
    <p class="label">Rechtliches</p>
    <h1 class="h1">Datenschutz</h1>
    <div class="prose" style="margin-top:2.5rem">
{inhalt}
      {hinweis}
    </div>
  </div>
</section>
"""
        return self.seite("datenschutz.html", "Datenschutz",
                          "Datenschutzerklärung des %s." % V["kurzname"], "", body)

    # ------------------------------------------------------------------

    def page(self, name):
        bauer = {
            "index.html": self.seite_start,
            "sportangebot.html": self.seite_sportangebot,
            "termine.html": self.seite_termine,
            "verein.html": self.seite_verein,
            "mitglied-werden.html": self.seite_mitglied,
            "impressum.html": self.seite_impressum,
            "datenschutz.html": self.seite_datenschutz,
        }.get(name)
        return bauer() if bauer else None

    def pages(self):
        return {name: self.page(name) for name in SEITEN}
