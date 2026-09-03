/* Vereinsverwaltung — die drei Handgriffe, die ohne JavaScript unbequem wären.
   Alles andere funktioniert auch ohne. */
(function () {
  "use strict";

  // Löschen erst nach Rückfrage.
  document.querySelectorAll("form[data-bestaetigen]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      if (!window.confirm(form.dataset.bestaetigen)) { e.preventDefault(); }
    });
  });

  // Weitere Trainingszeit anhängen bzw. eine Zeile wieder entfernen.
  var liste = document.getElementById("zeiten");
  var vorlage = document.getElementById("zeit-vorlage");
  var mehr = document.getElementById("zeit-mehr");

  if (liste && vorlage && mehr) {
    mehr.addEventListener("click", function () {
      var zeile = vorlage.content.cloneNode(true);
      liste.appendChild(zeile);
      var neu = liste.lastElementChild;
      var erstes = neu && neu.querySelector("select, input");
      if (erstes) { erstes.focus(); }
    });
  }

  document.addEventListener("click", function (e) {
    var weg = e.target.closest && e.target.closest(".zeit__weg");
    if (weg) { weg.closest(".zeit").remove(); }
  });

  // Navigation auf schmalen Bildschirmen.
  var menue = document.querySelector(".kopf__menue");
  var nav = document.getElementById("seitennav");
  if (menue && nav) {
    menue.addEventListener("click", function () {
      var offen = nav.dataset.offen === "true";
      nav.dataset.offen = String(!offen);
      menue.setAttribute("aria-expanded", String(!offen));
    });
  }
})();
