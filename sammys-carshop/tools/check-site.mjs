#!/usr/bin/env node
/**
 * check-site.mjs — Konsistenz- und Go-live-Prüfung für den Sammy's-Car-Shop-Auftritt.
 *
 * Warum es das gibt: Die alte Website hatte widersprüchliche Öffnungszeiten
 * (Website 8–17, Verzeichnisse 8–18/Sa 8–12) und ein "©2021" im Fuß. Solche
 * Fehler entstehen, weil dieselbe Angabe an mehreren Stellen gepflegt werden
 * muss. Dieses Skript macht content/betrieb.json zur einzigen Quelle der
 * Wahrheit und meldet jede Abweichung.
 *
 * Aufruf:
 *   node tools/check-site.mjs            Konsistenzprüfung (Exit 1 nur bei echten Fehlern)
 *   node tools/check-site.mjs --strict   zusätzlich Go-live-Blocker als Fehler werten
 *
 * Keine Abhängigkeiten, keine Installation nötig.
 */

import { readFileSync, readdirSync, existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const STRICT = process.argv.includes("--strict");

const errors = [];
const warnings = [];
const blockers = [];
const editorial = [];

const err = (file, msg) => errors.push(`${file}: ${msg}`);
const warn = (file, msg) => warnings.push(`${file}: ${msg}`);

/* ---------------------------------------------------------------- Grunddaten */
const betriebPath = join(ROOT, "content/betrieb.json");
if (!existsSync(betriebPath)) {
  console.error("content/betrieb.json fehlt — ohne diese Datei kann nichts geprüft werden.");
  process.exit(1);
}
const b = JSON.parse(readFileSync(betriebPath, "utf8"));

const DAYS = { 1: "mo", 2: "di", 3: "mi", 4: "do", 5: "fr", 6: "sa", 0: "so" };

/** Erwarteter Zellinhalt in den Öffnungszeiten-Tabellen. */
function hoursCell(key) {
  const v = b.oeffnungszeiten[key];
  return v ? `${v[0]}–${v[1]}` : "geschlossen";
}

/* ------------------------------------------------------------- Seitenauswahl */
const pages = readdirSync(ROOT).filter((f) => f.endsWith(".html")).sort();
if (pages.length === 0) {
  console.error("Keine HTML-Seiten im Projektverzeichnis gefunden.");
  process.exit(1);
}

/** Seiten, die absichtlich nicht indexiert werden. */
const NOINDEX = new Set(["impressum.html", "datenschutz.html", "404.html", "fahrzeuge.html"]);
/** Seiten ohne vollständigen Footer-/Kontaktblock gibt es nicht — alle müssen ihn haben. */
const ADDR = b.adresse;

for (const page of pages) {
  const html = readFileSync(join(ROOT, page), "utf8");
  const isFahrzeuge = page === "fahrzeuge.html";

  /* --- Grundgerüst ------------------------------------------------------ */
  if (!/<html lang="de">/.test(html)) err(page, 'Attribut lang="de" fehlt im <html>-Tag.');
  if (!/<meta charset="utf-8">/i.test(html)) err(page, "<meta charset> fehlt.");
  if (!/name="viewport"/.test(html)) err(page, "Viewport-Meta fehlt (Seite wäre auf dem Handy unbrauchbar).");

  const title = html.match(/<title>([^<]*)<\/title>/);
  if (!title) {
    err(page, "<title> fehlt.");
  } else if (title[1].length > 70) {
    warn(page, `Title ist ${title[1].length} Zeichen lang — Google kürzt meist ab ~60–65.`);
  }

  const desc = html.match(/name="description" content="([^"]*)"/);
  if (!desc) {
    if (page !== "404.html") err(page, "Meta-Description fehlt.");
  } else {
    if (desc[1].length > 170) warn(page, `Meta-Description ist ${desc[1].length} Zeichen lang — wird gekürzt.`);
    if (/\bdu\b|\bdich\b|\bdein/i.test(desc[1]) && page !== "karriere.html") {
      err(page, "Meta-Description ist im Du-Ton. Kundenseiten sprechen mit Sie; Recruiting gehört auf karriere.html.");
    }
  }

  // Die 404-Seite bekommt bewusst kein canonical — sie steht für viele URLs.
  if (page !== "404.html" && !/rel="canonical"/.test(html)) err(page, "Canonical-Link fehlt.");

  /* --- Indexierbarkeit -------------------------------------------------- */
  const robots = html.match(/name="robots" content="([^"]*)"/);
  if (NOINDEX.has(page)) {
    if (!robots || !/noindex/.test(robots[1])) err(page, "Diese Seite muss noindex tragen.");
  } else if (robots && /noindex/.test(robots[1])) {
    err(page, "Seite ist auf noindex gesetzt, soll aber gefunden werden.");
  }

  /* --- Kontaktdaten (NAP-Konsistenz) ----------------------------------- */
  if (!html.includes(b.telefon)) err(page, `Telefonnummer "${b.telefon}" kommt nicht vor.`);
  if (!html.includes(`tel:${b.telefonE164}`)) err(page, `Klick-to-Call-Link tel:${b.telefonE164} fehlt.`);
  if (!html.includes(b.email)) err(page, `E-Mail-Adresse ${b.email} kommt nicht vor.`);
  if (!html.includes(ADDR.strasse)) err(page, `Straße "${ADDR.strasse}" kommt nicht vor.`);
  if (!html.includes(`${ADDR.plz} ${ADDR.ort}`)) err(page, `"${ADDR.plz} ${ADDR.ort}" kommt nicht vor.`);
  if (b.fax && !html.includes(b.fax)) warn(page, `Faxnummer ${b.fax} fehlt.`);

  /* --- Firmenname: eine Schreibweise ----------------------------------- */
  if (!html.includes(b.name)) err(page, `Firmenname in der kanonischen Schreibweise "${b.name}" kommt nicht vor.`);
  for (const variante of b.nameVarianten) {
    if (html.includes(variante)) {
      err(page, `Abweichende Schreibweise "${variante}" gefunden — schwächt das Local SEO. Bitte "${b.name}" verwenden.`);
    }
  }

  /* --- Pflichtlinks im Footer ------------------------------------------ */
  if (!/href="\/?impressum\.html"/.test(html)) err(page, "Link zum Impressum fehlt (Pflicht auf jeder Seite).");
  if (!/href="\/?datenschutz\.html"/.test(html)) err(page, "Link zur Datenschutzerklärung fehlt (Pflicht auf jeder Seite).");
  if (!/data-consent-revoke/.test(html)) err(page, "Schaltfläche zum Widerruf der Einwilligung fehlt im Footer.");

  /* --- Jahresangabe im Copyright --------------------------------------- */
  const stale = html.match(/©\s*(19|20)\d\d/);
  if (stale) {
    err(page, `Feste Jahresangabe "${stale[0]}" im Copyright. Bewusst weglassen — genau daran ist die alte Seite mit "©2021" veraltet.`);
  }

  /* --- Öffnungszeiten --------------------------------------------------- */
  const rows = [...html.matchAll(/data-day="(\d)"[\s\S]*?<td>([^<]*)<\/td>/g)];
  if (rows.length === 0) {
    warn(page, "Keine Öffnungszeiten-Tabelle gefunden.");
  } else {
    const seen = new Set();
    for (const [, day, cell] of rows) {
      seen.add(day);
      const expected = hoursCell(DAYS[day]);
      if (cell.trim() !== expected) {
        err(page, `Öffnungszeit für Tag ${day} ist "${cell.trim()}", betrieb.json sagt "${expected}".`);
      }
    }
    for (const d of Object.keys(DAYS)) {
      if (!seen.has(d)) warn(page, `Öffnungszeiten-Tabelle: Tag ${d} fehlt.`);
    }
  }
  if (!/data-hours-status/.test(html)) warn(page, 'Kein "Jetzt geöffnet"-Status auf der Seite.');

  /* --- Datenschutz: keine automatisch geladenen Drittinhalte ----------- */
  const extScript = html.match(/<script[^>]+src="https?:\/\/[^"]+"/);
  if (extScript) err(page, `Externes Skript wird ungefragt geladen: ${extScript[0]}. Nur selbst gehostete Skripte einsetzen.`);
  const extStyle = html.match(/<link[^>]+rel="stylesheet"[^>]+href="https?:\/\/[^"]+"/);
  if (extStyle) err(page, `Externes Stylesheet wird ungefragt geladen: ${extStyle[0]}.`);
  const extImg = html.match(/<img[^>]+src="https?:\/\/[^"]+"/);
  if (extImg) err(page, `Bild von einer externen Domain: ${extImg[0]}. Bilder selbst hosten.`);
  const rawFrame = html.match(/<iframe[^>]*>/);
  if (rawFrame) {
    err(page, "Fest eingebautes <iframe> gefunden. Drittinhalte müssen über data-consent-gate laufen, sonst fehlt die Einwilligung nach § 25 TDDDG.");
  }

  /* --- Navigation ------------------------------------------------------- */
  const headerNav = html.match(/<nav class="nav"[\s\S]*?<\/nav>/);
  if (!headerNav) {
    err(page, "Hauptnavigation nicht gefunden.");
  } else if (!isFahrzeuge && b.fahrzeughandel.status !== "BESTAETIGT" && headerNav[0].includes("fahrzeuge.html")) {
    err(page, "fahrzeuge.html ist in der Hauptnavigation verlinkt, obwohl der Fahrzeughandel nicht bestätigt ist.");
  }
  // Seiten, die absichtlich keinen Menüpunkt haben, brauchen kein aria-current.
  const NO_NAV_ENTRY = new Set(["404.html", "fahrzeuge.html", "impressum.html", "datenschutz.html"]);
  const current = html.match(/aria-current="page"/g);
  if (!NO_NAV_ENTRY.has(page) && !current) {
    warn(page, 'Kein aria-current="page" in der Navigation — der aktive Menüpunkt ist nicht markiert.');
  } else if (current && current.length > 1) {
    err(page, 'Mehr als ein aria-current="page" in der Navigation.');
  }

  /* --- Formular --------------------------------------------------------- */
  if (/data-contact-form/.test(html)) {
    if (!/name="datenschutz"[^>]*required/.test(html)) {
      err(page, "Kontaktformular ohne verpflichtende Datenschutz-Checkbox.");
    }
    if (!/href="\/?datenschutz\.html"/.test(html)) {
      err(page, "Kontaktformular verlinkt die Datenschutzerklärung nicht.");
    }
  }

  /* --- Bewertungen ------------------------------------------------------ */
  if (/"aggregateRating"/.test(html) && !/<!--[\s\S]*?"aggregateRating"[\s\S]*?-->/.test(html)) {
    if (b.google.bewertung === null) {
      err(page, "aggregateRating ist im Markup aktiv, obwohl in betrieb.json keine verifizierte Bewertung steht.");
    }
  }
  if (/\d[,.]\d\s*(Sterne|★)/.test(html) && b.google.bewertung === null) {
    err(page, "Sterne-Bewertung im Text, aber in betrieb.json ist keine verifizierte Bewertung hinterlegt.");
  }

  /* --- Go-live-Blocker und redaktionelle Prüfpunkte -------------------- */
  for (const m of html.matchAll(/\{\{TODO:?\s*([^}]*)\}\}/g)) {
    blockers.push(`${page}: ${m[1].replace(/\s+/g, " ").trim().slice(0, 150)}`);
  }
  for (const m of html.matchAll(/<!--\s*PRÜFEN[:\s]([\s\S]*?)-->/g)) {
    editorial.push(`${page}: ${m[1].replace(/\s+/g, " ").trim().slice(0, 140)}…`);
  }
}

/* ------------------------------------------------- Öffnungszeiten in site.js */
const jsPath = join(ROOT, "assets/js/site.js");
if (!existsSync(jsPath)) {
  errors.push("assets/js/site.js fehlt.");
} else {
  const js = readFileSync(jsPath, "utf8");
  const block = js.match(/var HOURS = \{([\s\S]*?)\};/);
  if (!block) {
    errors.push("assets/js/site.js: HOURS-Block nicht gefunden.");
  } else {
    for (const [day, key] of Object.entries(DAYS)) {
      const v = b.oeffnungszeiten[key];
      const expected = v ? `["${v[0]}", "${v[1]}"]` : "null";
      const found = block[1].match(new RegExp(`\\b${day}:\\s*(\\[[^\\]]*\\]|null)`));
      if (!found) {
        errors.push(`assets/js/site.js: HOURS enthält keinen Eintrag für Tag ${day}.`);
      } else if (found[1].replace(/\s+/g, " ") !== expected) {
        errors.push(`assets/js/site.js: HOURS für Tag ${day} ist ${found[1]}, betrieb.json sagt ${expected}.`);
      }
    }
  }
}

/* ------------------------------------------------------- CSS: keine Fremd-URLs */
const cssPath = join(ROOT, "assets/css/site.css");
if (!existsSync(cssPath)) {
  errors.push("assets/css/site.css fehlt.");
} else {
  const css = readFileSync(cssPath, "utf8");
  if (/@import\s+url\(\s*['"]?https?:/.test(css)) {
    errors.push("assets/css/site.css: @import einer externen Ressource (z. B. Google Fonts) — lädt ungefragt Daten zu Dritten.");
  }
  if (/url\(\s*['"]?https?:/.test(css)) {
    errors.push("assets/css/site.css: url() verweist auf eine externe Domain.");
  }
}

/* --------------------------------------------------------- Pflichtdateien */
for (const f of ["robots.txt", "sitemap.xml", ".htaccess", "impressum.html", "datenschutz.html", "404.html"]) {
  if (!existsSync(join(ROOT, f))) errors.push(`${f} fehlt.`);
}

/* --- sitemap darf keine noindex-Seiten enthalten ------------------------ */
if (existsSync(join(ROOT, "sitemap.xml"))) {
  // Kommentare entfernen: dort werden die ausgenommenen Seiten absichtlich genannt.
  const sm = readFileSync(join(ROOT, "sitemap.xml"), "utf8").replace(/<!--[\s\S]*?-->/g, "");
  for (const p of NOINDEX) {
    if (sm.includes(p)) errors.push(`sitemap.xml enthält ${p}, obwohl die Seite noindex ist.`);
  }
  for (const p of pages) {
    if (!NOINDEX.has(p) && p !== "index.html" && !sm.includes(p)) {
      warnings.push(`sitemap.xml: ${p} fehlt.`);
    }
  }
}

/* ------------------------------------------------------ Unbestätigte Daten */
if (b.oeffnungszeiten.status !== "BESTAETIGT") {
  blockers.push(
    "content/betrieb.json: Öffnungszeiten sind UNBESTAETIGT. Website sagt Mo–Fr 8–17/Sa+So zu, " +
      "Cylex und Gelbe Seiten sagen Mo–Fr 8–18/Sa 8–12 (Stand 29.06.2025). Beim Inhaber klären, " +
      "überall identisch eintragen, dann Status auf BESTAETIGT setzen."
  );
}
if (b.fahrzeughandel.status !== "BESTAETIGT") {
  blockers.push(
    "content/betrieb.json: Fahrzeughandel ist UNBESTAETIGT — fahrzeuge.html bleibt bis zur Klärung " +
      "auf noindex und aus der Navigation."
  );
}
if (b.google.bewertung === null) {
  warnings.push(
    "content/betrieb.json: Google-Bewertung nicht verifiziert. Am Live-Profil prüfen, dann eintragen und den " +
      "aggregateRating-Block in index.html aktivieren (die Quellen widersprechen sich: ~4,8/13 vs. ~4,6/75–79)."
  );
}

/* ------------------------------------------------------------------ Ausgabe */
const line = "─".repeat(72);
console.log(`\n${line}\nPrüfung: Sammy's Car-Shop — ${pages.length} Seiten\n${line}`);

const section = (label, items, symbol) => {
  if (items.length === 0) return;
  console.log(`\n${symbol} ${label} (${items.length})`);
  for (const i of items) console.log(`   • ${i}`);
};

section("Fehler — müssen behoben werden", errors, "✖");
section("Warnungen", warnings, "!");
section("Go-live-Blocker — offene Angaben, die nur der Inhaber liefern kann", blockers, "□");
section("Redaktionelle Prüfpunkte (PRÜFEN-Kommentare im Quelltext)", editorial, "·");

console.log(`\n${line}`);
if (errors.length === 0) {
  console.log("Konsistenz: in Ordnung. Alle Seiten stimmen mit content/betrieb.json überein.");
} else {
  console.log(`Konsistenz: ${errors.length} Fehler.`);
}
if (blockers.length > 0) {
  console.log(
    `Go-live: NICHT freigegeben — ${blockers.length} offene Angabe(n).` +
      (STRICT ? "" : " Mit --strict wird das als Fehler gewertet.")
  );
} else {
  console.log("Go-live: keine offenen Platzhalter.");
}
console.log(`${line}\n`);

process.exit(errors.length > 0 || (STRICT && blockers.length > 0) ? 1 : 0);
