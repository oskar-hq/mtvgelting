/* MTV Gelting 08 — Navigation & Angebotsfilter */
(function () {
  "use strict";

  /* --- Mobile-Navigation ------------------------------------------------ */
  var burger = document.querySelector(".burger");
  var nav = document.getElementById("hauptnavigation");
  if (burger && nav) {
    burger.addEventListener("click", function () {
      var open = burger.getAttribute("aria-expanded") === "true";
      burger.setAttribute("aria-expanded", String(!open));
      nav.setAttribute("data-open", String(!open));
    });
    nav.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        burger.setAttribute("aria-expanded", "false");
        nav.setAttribute("data-open", "false");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && burger.getAttribute("aria-expanded") === "true") {
        burger.setAttribute("aria-expanded", "false");
        nav.setAttribute("data-open", "false");
        burger.focus();
      }
    });
  }

  /* --- Angebotsfilter --------------------------------------------------- */
  var grid = document.getElementById("angebote");
  if (!grid) return;

  var cards = Array.prototype.slice.call(grid.querySelectorAll(".card"));
  var chips = Array.prototype.slice.call(document.querySelectorAll(".chip"));
  var search = document.getElementById("suche");
  var counter = document.getElementById("treffer");
  var empty = document.getElementById("keine-treffer");

  var state = { kategorie: "alle", zielgruppe: "alle", q: "" };

  function apply() {
    var visible = 0;
    var q = state.q.trim().toLowerCase();

    cards.forEach(function (card) {
      var okKat = state.kategorie === "alle" || card.dataset.kategorie === state.kategorie;
      var okZg  = state.zielgruppe === "alle" ||
                  (card.dataset.zielgruppen || "").split(" ").indexOf(state.zielgruppe) > -1;
      var okQ   = !q || (card.dataset.suche || "").indexOf(q) > -1;
      var show  = okKat && okZg && okQ;
      card.hidden = !show;
      if (show) visible++;
    });

    if (counter) {
      counter.textContent = visible === 1 ? "1 Angebot" : visible + " Angebote";
    }
    if (empty) empty.hidden = visible !== 0;

    // Filterzustand in der URL spiegeln, damit Links teilbar bleiben.
    var params = new URLSearchParams();
    if (state.kategorie !== "alle") params.set("kategorie", state.kategorie);
    if (state.zielgruppe !== "alle") params.set("fuer", state.zielgruppe);
    var qs = params.toString();
    history.replaceState(null, "", qs ? "?" + qs : location.pathname);
  }

  function setChip(group, value) {
    state[group] = value;
    chips.forEach(function (c) {
      if (c.dataset.group === group) {
        c.setAttribute("aria-pressed", String(c.dataset.value === value));
      }
    });
    apply();
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      setChip(chip.dataset.group, chip.dataset.value);
    });
  });

  if (search) {
    search.addEventListener("input", function () {
      state.q = search.value;
      apply();
    });
  }

  // Vorauswahl aus der URL übernehmen (z. B. /sportangebot.html?kategorie=kinder)
  var initial = new URLSearchParams(location.search);
  var kat = initial.get("kategorie");
  var fuer = initial.get("fuer");
  if (kat) setChip("kategorie", kat);
  if (fuer) setChip("zielgruppe", fuer);
  apply();
})();
