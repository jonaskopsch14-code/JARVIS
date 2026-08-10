#!/usr/bin/env node
/**
 * build-preview.mjs — bündelt den gesamten Auftritt in EINE HTML-Datei.
 *
 * Wofür: zum Herumklicken und Herzeigen, ohne Webserver und ohne Hosting —
 * eine Datei, die man verschicken, doppelklicken oder als Artifact
 * veröffentlichen kann. Der Inhaber kann so die Seite abnehmen, bevor
 * irgendetwas live geht.
 *
 * WICHTIG: Das ist eine Vorschau, NICHT das Auslieferungsformat. Live gehen
 * die einzelnen HTML-Dateien — die sind einzeln indexierbar, haben
 * eigene URLs, eigene Titel und eigene canonical-Tags. Diese Bündeldatei hat
 * das alles nicht und darf nie hochgeladen werden.
 *
 * Aufruf: node tools/build-preview.mjs [ziel.html]
 */

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUT = process.argv[2] || join(ROOT, "vorschau.html");

const PAGES = [
  ["index.html", "Start"],
  ["leistungen.html", "Leistungen"],
  ["ueber-uns.html", "Über uns"],
  ["karriere.html", "Karriere"],
  ["kontakt.html", "Kontakt"],
  ["impressum.html", "Impressum"],
  ["datenschutz.html", "Datenschutz"],
  ["fahrzeuge.html", "Fahrzeuge (inaktiv)"],
  ["404.html", "404"]
];

const read = (f) => readFileSync(join(ROOT, f), "utf8");

/** Inhalt zwischen <tag ...> und </tag> (erste Fundstelle, Tag selbst entfällt). */
function inner(html, tag) {
  const open = new RegExp(`<${tag}[^>]*>`);
  const m = html.match(open);
  if (!m) throw new Error(`<${tag}> nicht gefunden`);
  const start = m.index + m[0].length;
  const end = html.lastIndexOf(`</${tag}>`);
  return html.slice(start, end);
}

/* --- CSS: Dunkelmodus zusätzlich über [data-theme] ansprechbar machen ------
   site.css schaltet den Dunkelmodus nur über prefers-color-scheme. Das
   Artifact-Fenster stempelt bei ausdrücklicher Wahl aber data-theme auf das
   Wurzelelement. Damit die Vorschau in allen drei Zuständen (System, hell
   gewählt, dunkel gewählt) stimmt, werden die Dunkel-Regeln hier zusätzlich
   unter :root[data-theme="dark"] ausgegeben und die Medienabfrage gegen eine
   ausdrückliche Hell-Wahl abgesichert. Die ausgelieferte site.css bleibt
   unberührt — im echten Web gibt es kein data-theme. */
function themeAwareCss(css) {
  const marker = "@media (prefers-color-scheme: dark) {";
  const at = css.indexOf(marker);
  if (at === -1) return css;

  // Passende schließende Klammer der Medienabfrage finden.
  let depth = 0;
  let end = -1;
  for (let i = at + marker.length - 1; i < css.length; i++) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") {
      depth--;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  if (end === -1) return css;

  const body = css.slice(at + marker.length, end);
  const rules = [...body.matchAll(/([^{}]+)\{([^{}]*)\}/g)].map(([, sel, decl]) => [sel.trim(), decl.trim()]);

  const emit = (prefix) =>
    rules
      .map(([sel, decl]) => `${sel === ":root" ? prefix : `${prefix} ${sel}`} { ${decl} }`)
      .join("\n");

  const guardedMedia = `@media (prefers-color-scheme: dark) {\n${emit(':root:not([data-theme="light"])')}\n}`;
  const stamped = `:root[data-theme="dark"] { }\n${emit(':root[data-theme="dark"]')}`;

  return css.slice(0, at) + guardedMedia + "\n\n" + stamped + css.slice(end + 1);
}

/* --- Seiten einsammeln ---------------------------------------------------- */
const index = read("index.html");
const header = index.match(/<header class="site-header">[\s\S]*?<\/header>/)[0];
const footer = index.match(/<footer class="site-footer">[\s\S]*?<\/footer>/)[0];

const sections = PAGES.map(([file]) => {
  const html = read(file);
  const title = html.match(/<title>([^<]*)<\/title>/)[1];
  let main = inner(html, "main");
  // 404 verlinkt absolut ("/leistungen.html") — im Bündel relativ behandeln.
  main = main.replace(/href="\/([a-z0-9-]+\.html)"/g, 'href="$1"').replace(/href="\/"/g, 'href="index.html"');
  return { file, title, main };
});

// Navigation: Zielseite als data-page markieren, damit der Router greift.
const navHtml = header.replace(/href="([a-z0-9-]+\.html)"/g, 'href="$1" data-page="$1"');

const css = themeAwareCss(read("assets/css/site.css"));
const js = read("assets/js/site.js");

const previewCss = `
/* --- Nur für die Vorschau: schmale Leiste, bewusst zurückhaltend, Farben
   aus dem bestehenden Token-Satz. --------------------------------------- */
.pv-bar {
  position: sticky; top: 0; z-index: 60;
  display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem 0.9rem;
  padding: 0.6rem clamp(1rem, 4vw, 2rem);
  background: var(--bg-dark); color: rgb(255 255 255 / 72%);
  font-size: 0.8125rem; line-height: 1.4;
  border-bottom: 1px solid rgb(255 255 255 / 14%);
}
.pv-bar b { color: #fff; font-weight: 650; letter-spacing: 0.02em; }
.pv-bar .pv-sep { width: 1px; height: 1.1em; background: rgb(255 255 255 / 22%); }
.pv-bar select {
  font: inherit; font-weight: 600; color: #fff;
  background: rgb(255 255 255 / 10%);
  border: 1px solid rgb(255 255 255 / 26%);
  border-radius: 8px; padding: 0.25rem 0.5rem;
}
.pv-bar select option { color: #14171a; background: #fff; }
.pv-note { color: rgb(255 255 255 / 58%); }
.site-header { top: 0; }
.pv-page[hidden] { display: none; }
.pv-blocked {
  display: grid; gap: 0.5rem; place-items: center; text-align: center;
  min-height: 12rem; padding: 1.5rem;
  background: var(--bg-soft); border: 1px dashed var(--line-strong);
  border-radius: var(--radius-lg);
}
.pv-blocked strong { color: var(--ink); }
.pv-blocked p { color: var(--ink-soft); font-size: 0.9375rem; margin: 0; max-width: 48ch; }
`;

const routerJs = `
/* --- Router nur für die Vorschau ---------------------------------------- */
(function () {
  var pages = Array.prototype.slice.call(document.querySelectorAll(".pv-page"));
  var picker = document.getElementById("pv-picker");
  var titleEl = document.getElementById("pv-title");

  function show(name, frag) {
    var found = false;
    pages.forEach(function (el) {
      var match = el.getAttribute("data-page") === name;
      el.hidden = !match;
      if (match) { found = true; if (titleEl) titleEl.textContent = el.getAttribute("data-title"); }
    });
    if (!found) return show("404.html", null);
    if (picker) picker.value = name;
    // Aktiven Menüpunkt setzen
    Array.prototype.forEach.call(document.querySelectorAll(".nav a[data-page]"), function (a) {
      if (a.getAttribute("data-page") === name) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
    if (frag) {
      var t = document.getElementById(frag);
      if (t) { t.scrollIntoView(); return; }
    }
    window.scrollTo(0, 0);
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest("a");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (/^(https?:|mailto:|tel:)/.test(href)) return;
    var clean = href.replace(/^\\//, "");
    if (clean === "" ) { e.preventDefault(); show("index.html", null); return; }
    var parts = clean.split("#");
    if (parts[0] === "") return; // reiner Anker: Browser erledigt das
    if (!/\\.html$/.test(parts[0])) return;
    e.preventDefault();
    show(parts[0], parts[1] || null);
  });

  if (picker) picker.addEventListener("change", function () { show(picker.value, null); });

  // Karte/Börse: im Vorschau-Bündel blockiert die Artifact-Sicherheitsregel
  // jeden Request nach außen. Statt eines leeren Rahmens eine Erklärung.
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-consent-once], [data-consent-always]");
    if (!btn) return;
    var gate = btn.closest("[data-consent-gate]");
    if (!gate) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    var box = document.createElement("div");
    box.className = "pv-blocked";
    box.innerHTML = "<strong>Einwilligung erteilt \\u2014 hier trotzdem keine Karte</strong>" +
      "<p>Genau an dieser Stelle w\\u00fcrde jetzt die Google-Maps-Karte erscheinen. " +
      "In dieser Vorschau blockiert die Sicherheitsregel der Artifact-Seite alle " +
      "Verbindungen nach au\\u00dfen. Auf dem echten Hosting l\\u00e4dt die Karte an " +
      "dieser Stelle \\u2014 und zwar erst nach diesem Klick, vorher geht kein " +
      "einziger Request an Google.</p>";
    gate.replaceWith(box);
  }, true);

  show("index.html", null);
})();
`;

const html = `<title>SAMMY'S CAR-SHOP &mdash; Vorschau des neuen Auftritts</title>

<div class="pv-bar">
  <b>Vorschau &middot; Entwurf</b>
  <span class="pv-sep"></span>
  <label for="pv-picker">Seite:</label>
  <select id="pv-picker">
${PAGES.map(([f, label]) => `    <option value="${f}">${label}</option>`).join("\n")}
  </select>
  <span class="pv-sep"></span>
  <span class="pv-note">Alle zehn Seiten in einer Datei. Noch nicht ver&ouml;ffentlicht &mdash; orange umrahmte Platzhalter warten auf Angaben des Inhabers.</span>
</div>

${navHtml}

<main id="main">
${sections
  .map(
    (s) =>
      `<div class="pv-page" data-page="${s.file}" data-title="${s.title.replace(/"/g, "&quot;")}" hidden>\n${s.main}\n</div>`
  )
  .join("\n\n")}
</main>

${footer}

<style>
${css}
${previewCss}
</style>

<script>
${js}
${routerJs}
</script>
`;

writeFileSync(OUT, html);
console.log(`Vorschau geschrieben: ${OUT}`);
console.log(`  ${sections.length} Seiten, ${(html.length / 1024).toFixed(0)} KB`);
