/*!
 * ConsentFlow Widget – DSGVO Cookie-Consent Banner
 * Vanilla JS, framework-frei. Echtes Opt-in: nicht-notwendige Skripte werden
 * erst nach Einwilligung geladen.
 *
 * Einbindung:
 *   <script async src="https://cdn.consentflow.de/v1/widget.js" data-cf-site="cf_xxx"></script>
 *
 * Zu blockierende Skripte auf der Kundenseite so auszeichnen:
 *   <script type="text/plain" data-cf-category="statistics" src="https://.../analytics.js"></script>
 *   <script type="text/plain" data-cf-category="marketing"> ...inline code... </script>
 */
(function () {
  "use strict";

  var script = document.currentScript || (function () {
    var s = document.getElementsByTagName("script");
    return s[s.length - 1];
  })();

  var SITE_ID = script && script.getAttribute("data-cf-site");
  var API = (script && script.getAttribute("data-cf-api")) || "https://api.consentflow.de";
  if (!SITE_ID) {
    console.warn("[ConsentFlow] data-cf-site fehlt – Banner wird nicht geladen.");
    return;
  }

  var STORAGE_KEY = "consentflow:" + SITE_ID;
  var CATEGORIES = ["necessary", "statistics", "marketing"];
  var state = { config: null, consent: null, version: "1", root: null };

  // ---------- Persistenz ----------
  function loadConsent() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }
  function saveConsent(consent) {
    consent.ts = new Date().toISOString();
    consent.v = state.version;
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(consent)); } catch (e) {}
    // Auch als Cookie (1 Jahr), damit serverseitige Nutzung möglich ist.
    try {
      document.cookie = STORAGE_KEY + "=" + encodeURIComponent(JSON.stringify(consent)) +
        ";path=/;max-age=31536000;SameSite=Lax";
    } catch (e) {}
    state.consent = consent;
  }

  // ---------- Backend-Log ----------
  function report(action, consent) {
    var body = JSON.stringify({
      siteId: SITE_ID, action: action, consentVersion: state.version,
      categories: { statistics: !!consent.statistics, marketing: !!consent.marketing }
    });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(API + "/v1/consent", new Blob([body], { type: "application/json" }));
      } else {
        fetch(API + "/v1/consent", { method: "POST", headers: { "Content-Type": "application/json" }, body: body, keepalive: true });
      }
    } catch (e) {}
  }

  // ---------- Skript-Freischaltung (echtes Opt-in) ----------
  function activateScripts(consent) {
    var blocked = document.querySelectorAll('script[type="text/plain"][data-cf-category]');
    Array.prototype.forEach.call(blocked, function (old) {
      var cat = old.getAttribute("data-cf-category");
      if (cat !== "necessary" && !consent[cat]) return;
      if (old.getAttribute("data-cf-activated")) return;
      var s = document.createElement("script");
      for (var i = 0; i < old.attributes.length; i++) {
        var a = old.attributes[i];
        if (a.name === "type" || a.name === "data-cf-category") continue;
        s.setAttribute(a.name, a.value);
      }
      if (old.src) s.src = old.src; else s.textContent = old.textContent;
      s.setAttribute("data-cf-activated", "1");
      old.parentNode.insertBefore(s, old.nextSibling);
    });
  }

  function applyConsent(consent, action) {
    saveConsent(consent);
    activateScripts(consent);
    report(action, consent);
    // Event für die Kundenseite (z. B. eigenes Tag-Management)
    try { window.dispatchEvent(new CustomEvent("consentflow:change", { detail: consent })); } catch (e) {}
  }

  // ---------- UI ----------
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "style") node.style.cssText = attrs[k];
      else if (k === "text") node.textContent = attrs[k];
      else node.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { if (c) node.appendChild(c); });
    return node;
  }

  function render() {
    var c = state.config;
    var t = c.texts, col = c.colors;
    if (state.root) state.root.remove();

    var wrap = el("div", { "data-consentflow": "1", "role": "dialog", "aria-label": "Cookie-Einwilligung" });
    var boxPos = c.position === "box"
      ? "left:auto;right:20px;bottom:20px;max-width:420px;border-radius:14px;"
      : "left:0;right:0;bottom:0;border-radius:14px 14px 0 0;";
    var panel = el("div", {
      style: "position:fixed;z-index:2147483647;" + boxPos +
        "margin:16px;background:" + col.background + ";color:" + col.text +
        ";box-shadow:0 8px 40px rgba(0,0,0,.22);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;" +
        "padding:20px 22px;box-sizing:border-box;"
    });

    var head = el("div", { style: "display:flex;align-items:center;gap:10px;margin-bottom:8px;" }, [
      c.logo ? el("img", { src: c.logo, alt: "", style: "height:26px;width:auto;" }) : null,
      el("strong", { text: t.title, style: "font-size:16px;" })
    ]);
    var msg = el("p", { text: t.message, style: "margin:0 0 14px;opacity:.9;" });

    var settings = buildSettings(c);
    settings.style.display = "none";

    var btnStyle = "cursor:pointer;border:0;border-radius:9px;padding:11px 16px;font-weight:600;font-size:14px;";
    var accept = el("button", {
      text: t.acceptAll, style: btnStyle + "background:" + col.primary + ";color:#fff;flex:1;"
    });
    var reject = el("button", {
      text: t.rejectAll, style: btnStyle + "background:" + col.secondary + ";color:" + col.text + ";flex:1;"
    });
    var settingsBtn = el("button", {
      text: t.settings, style: btnStyle + "background:transparent;color:" + col.text + ";text-decoration:underline;flex:0 0 auto;"
    });
    var saveBtn = el("button", {
      text: t.save, style: btnStyle + "background:" + col.primary + ";color:#fff;flex:1;display:none;"
    });

    accept.onclick = function () { decideAll(true); };
    reject.onclick = function () { decideAll(false); };
    settingsBtn.onclick = function () {
      var open = settings.style.display === "none";
      settings.style.display = open ? "block" : "none";
      saveBtn.style.display = open ? "block" : "none";
    };
    saveBtn.onclick = function () {
      var consent = { necessary: true };
      CATEGORIES.forEach(function (cat) {
        if (cat === "necessary") return;
        var cb = settings.querySelector('input[data-cat="' + cat + '"]');
        consent[cat] = cb ? cb.checked : false;
      });
      finish(consent, "save");
    };

    var actions = el("div", { style: "display:flex;flex-wrap:wrap;gap:8px;align-items:center;" },
      [accept, reject, settingsBtn, saveBtn]);

    panel.appendChild(head);
    panel.appendChild(msg);
    panel.appendChild(settings);
    panel.appendChild(actions);

    if (c.showPoweredBy) {
      panel.appendChild(el("div", {
        style: "margin-top:10px;font-size:11px;opacity:.6;text-align:right;"
      }, [el("span", { text: t.poweredBy })]));
    }

    wrap.appendChild(panel);
    document.body.appendChild(wrap);
    state.root = wrap;
  }

  function buildSettings(c) {
    var box = el("div", { style: "margin:0 0 14px;border-top:1px solid rgba(127,127,127,.25);padding-top:12px;" });
    CATEGORIES.forEach(function (cat) {
      var cfg = c.categories[cat];
      if (!cfg || !cfg.enabled) return;
      var necessary = cat === "necessary";
      var checked = necessary || (state.consent ? !!state.consent[cat] : false);
      var input = el("input", { type: "checkbox", "data-cat": cat });
      input.checked = checked;
      if (necessary) input.disabled = true;
      var row = el("label", {
        style: "display:flex;gap:10px;align-items:flex-start;margin:8px 0;cursor:" + (necessary ? "default" : "pointer") + ";"
      }, [
        input,
        el("span", {}, [
          el("strong", { text: cfg.label, style: "display:block;" }),
          el("span", { text: cfg.description, style: "font-size:13px;opacity:.8;" })
        ])
      ]);
      box.appendChild(row);
    });
    return box;
  }

  function decideAll(value) {
    var consent = { necessary: true };
    CATEGORIES.forEach(function (cat) { if (cat !== "necessary") consent[cat] = value; });
    finish(consent, value ? "accept_all" : "reject_all");
  }

  function finish(consent, action) {
    applyConsent(consent, action);
    if (state.root) { state.root.remove(); state.root = null; }
  }

  // ---------- Öffentliche API ----------
  window.ConsentFlow = {
    open: function () { if (!state.config) return; render(); },     // Widerruf/Ändern jederzeit
    getConsent: function () { return state.consent; },
    reset: function () {
      try { localStorage.removeItem(STORAGE_KEY); } catch (e) {}
      state.consent = null; render();
    }
  };

  // ---------- Start ----------
  function boot() {
    fetch(API + "/v1/config/" + encodeURIComponent(SITE_ID))
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        state.config = data.config;
        state.version = String(data.consentVersion || "1");
        state.consent = loadConsent();
        if (state.consent && state.consent.v === state.version) {
          activateScripts(state.consent); // frühere Zustimmung anwenden
        } else {
          state.consent = null;
          render(); // neue oder veraltete Einwilligung → Banner zeigen
        }
      })
      .catch(function (e) { console.warn("[ConsentFlow] Konfiguration konnte nicht geladen werden:", e); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
