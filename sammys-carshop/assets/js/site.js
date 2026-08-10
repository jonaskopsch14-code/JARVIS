/* ==========================================================================
   Sammy's Car-Shop — site.js
   Kein Framework, keine externen Requests, keine Tracker.
   Module:
     1. Navigation (Mobile-Toggle)
     2. Öffnungszeiten-Status ("Jetzt geöffnet")
     3. Consent (nur für eingebettete Drittinhalte, z. B. Google Maps)
     4. Kontaktformular (Validierung + E-Mail-Fallback)
   ========================================================================== */
(function () {
  "use strict";

  /* ---------------------------------------------------------------------
     Öffnungszeiten — MUSS identisch zu content/betrieb.json sein.
     tools/check-site.mjs prüft das bei jedem Lauf.
     --------------------------------------------------------------------- */
  var HOURS = {
    1: ["08:00", "18:00"], // Mo
    2: ["08:00", "18:00"], // Di
    3: ["08:00", "18:00"], // Mi
    4: ["08:00", "18:00"], // Do
    5: ["08:00", "18:00"], // Fr
    6: ["08:00", "12:00"], // Sa
    0: null // So
  };

  var CONSENT_KEY = "scs-consent-v1";

  /* === 1. Navigation =================================================== */
  function initNav() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".nav");
    if (!toggle || !nav) return;

    function setOpen(open) {
      nav.setAttribute("data-open", open ? "true" : "false");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    }
    setOpen(false);

    toggle.addEventListener("click", function () {
      setOpen(nav.getAttribute("data-open") !== "true");
    });

    // Schließen bei Escape und beim Klick auf einen Link.
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.getAttribute("data-open") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setOpen(false);
    });

    // Beim Wechsel auf Desktop-Breite den Inline-State zurücksetzen.
    var mq = window.matchMedia("(min-width: 1024px)");
    mq.addEventListener("change", function (e) {
      if (e.matches) setOpen(false);
    });
  }

  /* === 2. Öffnungszeiten-Status ======================================== */
  function toMinutes(hhmm) {
    var p = hhmm.split(":");
    return parseInt(p[0], 10) * 60 + parseInt(p[1], 10);
  }

  function initHours() {
    var now = new Date();
    var day = now.getDay();
    var minutes = now.getHours() * 60 + now.getMinutes();
    var today = HOURS[day];
    var isOpen = !!today && minutes >= toMinutes(today[0]) && minutes < toMinutes(today[1]);

    // Heutige Zeile in allen Öffnungszeiten-Tabellen hervorheben.
    Array.prototype.forEach.call(document.querySelectorAll(".hours tr[data-day]"), function (row) {
      row.setAttribute("data-today", String(Number(row.getAttribute("data-day")) === day));
    });

    Array.prototype.forEach.call(document.querySelectorAll("[data-hours-status]"), function (el) {
      el.setAttribute("data-open", String(isOpen));
      if (isOpen) {
        el.textContent = "Jetzt geöffnet – bis " + today[1] + " Uhr";
        return;
      }
      // Nächste Öffnung suchen (max. 7 Tage vorausschauen).
      for (var i = 1; i <= 7; i++) {
        var d = (day + i) % 7;
        if (HOURS[d]) {
          var names = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"];
          var label = i === 1 ? "morgen" : names[d];
          el.textContent = "Geschlossen – öffnet " + label + " " + HOURS[d][0] + " Uhr";
          return;
        }
      }
      el.textContent = "Aktuell geschlossen";
    });
  }

  /* === 3. Consent ======================================================
     Beim Seitenaufruf werden KEINE Drittanbieter-Ressourcen geladen und
     keine nicht notwendigen Cookies gesetzt. Deshalb gibt es bewusst kein
     Consent-Banner beim Laden — eingewilligt wird punktuell und erst dann,
     wenn ein Drittinhalt (Karte) wirklich geladen werden soll (§ 25 TDDDG).
     Die Einwilligung liegt im localStorage, nicht in einem Cookie, und ist
     über den Footer jederzeit widerrufbar.
     --------------------------------------------------------------------- */
  function readConsent() {
    try {
      return JSON.parse(window.localStorage.getItem(CONSENT_KEY)) || {};
    } catch (e) {
      return {};
    }
  }

  function writeConsent(state) {
    try {
      window.localStorage.setItem(CONSENT_KEY, JSON.stringify(state));
    } catch (e) {
      /* localStorage blockiert (z. B. privater Modus) — Einwilligung gilt dann nur für diesen Seitenaufruf. */
    }
  }

  function loadEmbed(gate) {
    var src = gate.getAttribute("data-embed-src");
    var title = gate.getAttribute("data-embed-title") || "Eingebetteter Inhalt";
    if (!src) return;
    var frame = document.createElement("iframe");
    frame.src = src;
    frame.title = title;
    frame.className = "map-frame";
    frame.loading = "lazy";
    frame.referrerPolicy = "no-referrer-when-downgrade";
    frame.setAttribute("allowfullscreen", "");
    gate.replaceWith(frame);
  }

  function initConsent() {
    var state = readConsent();

    Array.prototype.forEach.call(document.querySelectorAll("[data-consent-gate]"), function (gate) {
      var category = gate.getAttribute("data-consent-gate");

      if (state[category] === true) {
        loadEmbed(gate);
        return;
      }

      var once = gate.querySelector("[data-consent-once]");
      var always = gate.querySelector("[data-consent-always]");

      if (once) {
        once.addEventListener("click", function () {
          loadEmbed(gate); // nur für diesen Aufruf, nichts gespeichert
        });
      }
      if (always) {
        always.addEventListener("click", function () {
          var s = readConsent();
          s[category] = true;
          writeConsent(s);
          loadEmbed(gate);
        });
      }
    });

    // Widerruf im Footer
    Array.prototype.forEach.call(document.querySelectorAll("[data-consent-revoke]"), function (btn) {
      btn.addEventListener("click", function () {
        try {
          window.localStorage.removeItem(CONSENT_KEY);
        } catch (e) {
          /* ignorieren */
        }
        var msg = document.getElementById("consent-revoked");
        if (msg) {
          msg.hidden = false;
          msg.textContent =
            "Einwilligung zurückgesetzt. Eingebettete Karten werden erst nach erneuter Freigabe geladen.";
        }
      });
    });
  }

  /* === 4. Kontaktformular ============================================== */
  function initForm() {
    var form = document.querySelector("[data-contact-form]");
    if (!form) return;

    function fieldOf(input) {
      return input.closest(".field");
    }

    function showError(input, message) {
      var field = fieldOf(input);
      if (!field) return;
      field.setAttribute("data-invalid", "true");
      var err = field.querySelector(".field__error");
      if (!err) {
        err = document.createElement("p");
        err.className = "field__error";
        field.appendChild(err);
      }
      err.textContent = message;
      input.setAttribute("aria-invalid", "true");
    }

    function clearError(input) {
      var field = fieldOf(input);
      if (!field) return;
      field.removeAttribute("data-invalid");
      var err = field.querySelector(".field__error");
      if (err) err.remove();
      input.removeAttribute("aria-invalid");
    }

    function validate() {
      var ok = true;
      var first = null;

      // Zu prüfen sind alle Pflichtfelder — plus jedes E-Mail-Feld, das etwas
      // enthält, auch wenn es freiwillig ist. Das Formular trägt novalidate,
      // also übernimmt der Browser hier nichts: eine Tippfehler-Adresse würde
      // sonst unbemerkt durchgehen und die Antwort landet nirgends.
      var fields = [];
      var add = function (input) {
        if (fields.indexOf(input) === -1) fields.push(input);
      };
      Array.prototype.forEach.call(form.querySelectorAll("[required]"), add);
      Array.prototype.forEach.call(form.querySelectorAll('input[type="email"]'), add);

      fields.forEach(function (input) {
        clearError(input);
        var value = input.type === "checkbox" ? "" : input.value.trim();
        var empty = input.type === "checkbox" ? !input.checked : !value;
        var required = input.hasAttribute("required");

        if (required && empty) {
          showError(input, input.type === "checkbox" ? "Bitte bestätigen, um fortzufahren." : "Bitte ausfüllen.");
          ok = false;
        } else if (input.type === "email" && value && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) {
          showError(input, "Bitte eine gültige E-Mail-Adresse angeben.");
          ok = false;
        }
        if (!ok && !first) first = input;
      });

      if (first) first.focus();
      return ok;
    }

    form.addEventListener("submit", function (e) {
      if (!validate()) {
        e.preventDefault();
        return;
      }
      // Solange kein Formular-Endpunkt konfiguriert ist, wird nichts
      // abgeschickt (siehe README, Abschnitt "Formular-Endpunkt").
      var action = form.getAttribute("action") || "";
      if (!action || action.indexOf("TODO") !== -1) {
        e.preventDefault();
        var hint = form.querySelector("[data-form-fallback]");
        if (hint) hint.hidden = false;
      }
    });

    // E-Mail-Fallback: vorbefüllte Mail an die Werkstatt öffnen.
    var mailBtn = form.querySelector("[data-mailto]");
    if (mailBtn) {
      mailBtn.addEventListener("click", function () {
        var get = function (name) {
          var el = form.elements[name];
          return el && el.value ? el.value.trim() : "";
        };
        var body = [
          "Name: " + get("name"),
          "Telefon: " + get("telefon"),
          "E-Mail: " + get("email"),
          "Fahrzeug: " + get("fahrzeug"),
          "Leistung: " + get("leistung"),
          "",
          get("nachricht")
        ].join("\n");
        window.location.href =
          "mailto:kontakt@scs-wb.de?subject=" +
          encodeURIComponent("Terminanfrage über die Website") +
          "&body=" +
          encodeURIComponent(body);
      });
    }
  }

  /* === Start =========================================================== */
  function init() {
    initNav();
    initHours();
    initConsent();
    initForm();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
