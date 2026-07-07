// ConsentFlow Dashboard – Client-Controller (Vanilla JS).
import { api, isLoggedIn, setToken, clearToken, ApiError } from "./api.js";

const $ = (id) => document.getElementById(id);
const views = ["auth", "app", "editor", "consents", "billing"];
function show(view) {
  views.forEach((v) => $("view-" + v).classList.toggle("hide", v !== view));
  window.scrollTo(0, 0);
}

let currentUser = null;
let sites = [];
let editing = null; // aktuell bearbeitete Site
let authMode = "login";

export function initApp() {
  wireAuth();
  wireNav();
  // Rückkehr aus Stripe-Checkout?
  const params = new URLSearchParams(location.search);
  if (isLoggedIn()) {
    loadDashboard().then(() => {
      if (params.get("status")) openBilling();
    });
  } else {
    show("auth");
  }
}

// ---------------- Auth ----------------
function wireAuth() {
  $("auth-toggle").onclick = (e) => {
    e.preventDefault();
    authMode = authMode === "login" ? "register" : "login";
    const reg = authMode === "register";
    $("auth-title").textContent = reg ? "Konto erstellen" : "Anmelden";
    $("auth-submit").textContent = reg ? "Registrieren (14 Tage gratis)" : "Anmelden";
    $("auth-toggle-text").textContent = reg ? "Schon ein Konto?" : "Noch kein Konto?";
    $("auth-toggle").textContent = reg ? "Zum Login" : "Jetzt registrieren";
    $("auth-error").classList.add("hide");
  };
  $("auth-submit").onclick = submitAuth;
  $("auth-password").addEventListener("keydown", (e) => { if (e.key === "Enter") submitAuth(); });
}

async function submitAuth() {
  const email = $("auth-email").value.trim();
  const password = $("auth-password").value;
  const errEl = $("auth-error");
  errEl.classList.add("hide");
  $("auth-submit").disabled = true;
  try {
    const res = authMode === "register" ? await api.register(email, password) : await api.login(email, password);
    setToken(res.token);
    await loadDashboard();
  } catch (e) {
    errEl.textContent = e.message || "Anmeldung fehlgeschlagen.";
    errEl.classList.remove("hide");
  } finally {
    $("auth-submit").disabled = false;
  }
}

// ---------------- Navigation ----------------
function wireNav() {
  $("link-logout").onclick = (e) => { e.preventDefault(); clearToken(); location.reload(); };
  $("link-billing").onclick = (e) => { e.preventDefault(); openBilling(); };
  $("btn-new-site").onclick = createSite;
  $("editor-back").onclick = (e) => { e.preventDefault(); show("app"); };
  $("consents-back").onclick = (e) => { e.preventDefault(); show("app"); };
  $("billing-back").onclick = (e) => { e.preventDefault(); show("app"); };
  document.querySelectorAll("#view-billing [data-plan]").forEach((b) => {
    b.onclick = () => startCheckout(b.getAttribute("data-plan"));
  });
  $("btn-portal").onclick = openPortal;
}

// ---------------- Dashboard ----------------
async function loadDashboard() {
  try {
    currentUser = (await api.me()).user;
  } catch (e) {
    if (e instanceof ApiError && e.status === 401) { show("auth"); return; }
    throw e;
  }
  $("user-plan").textContent = planLabel(currentUser.plan);
  $("user-email").textContent = currentUser.email;
  await refreshSites();
  show("app");
}

async function refreshSites() {
  sites = (await api.listSites()).sites;
  const list = $("sites-list");
  list.innerHTML = "";
  if (sites.length === 0) {
    list.innerHTML = '<div class="card muted">Noch keine Website. Klicke auf „+ Website hinzufügen“.</div>';
    return;
  }
  for (const site of sites) {
    const card = document.createElement("div");
    card.className = "card";
    card.style.display = "flex";
    card.style.justifyContent = "space-between";
    card.style.alignItems = "center";
    card.style.flexWrap = "wrap";
    card.style.gap = "10px";
    const info = document.createElement("div");
    info.innerHTML = `<strong>${escapeHtml(site.name)}</strong>
      <div class="muted" style="font-size:13px;">${escapeHtml(site.domain || "keine Domain")} · <code>${site.id}</code></div>`;
    const actions = document.createElement("div");
    actions.style.display = "flex";
    actions.style.gap = "8px";
    actions.style.flexWrap = "wrap";
    actions.append(
      btn("Bearbeiten", "btn ghost", () => openEditor(site.id)),
      btn("Einwilligungen", "btn ghost", () => openConsents(site)),
      btn("Löschen", "btn ghost", () => removeSite(site)),
    );
    card.append(info, actions);
    list.append(card);
  }
}

async function createSite() {
  const name = prompt("Name der Website (z. B. Musterpraxis Dr. Meier):");
  if (!name) return;
  try {
    const res = await api.createSite({ name, domain: "" });
    await refreshSites();
    openEditor(res.site.id);
  } catch (e) {
    if (e instanceof ApiError && e.data && e.data.code === "plan_limit") {
      if (confirm(e.message + "\n\nJetzt Plan upgraden?")) openBilling();
    } else {
      alert(e.message);
    }
  }
}

async function removeSite(site) {
  if (!confirm(`„${site.name}“ wirklich löschen? Auch die Einwilligungs-Logs werden entfernt.`)) return;
  await api.deleteSite(site.id);
  await refreshSites();
}

// ---------------- Editor ----------------
async function openEditor(id) {
  const { site } = await api.getSite(id);
  editing = site;
  buildEditorForm(site);
  renderPreview(site.config);
  renderSnippet(site.id);
  $("editor-msg").innerHTML = "";
  show("editor");
}

function buildEditorForm(site) {
  const c = site.config;
  const canRemovePb = currentUser.plan === "agency";
  const form = $("editor-form");
  form.innerHTML = `
    <h3 style="margin-top:0;">Banner bearbeiten</h3>
    <label>Name</label><input data-f="name" value="${escapeAttr(site.name)}" />
    <label>Domain</label><input data-f="domain" value="${escapeAttr(site.domain || "")}" placeholder="example.de" />
    <label>Position</label>
    <select data-f="position">
      <option value="bottom" ${c.position === "bottom" ? "selected" : ""}>Balken unten</option>
      <option value="box" ${c.position === "box" ? "selected" : ""}>Box (unten rechts)</option>
    </select>
    <div style="display:flex;gap:12px;">
      <div style="flex:1;"><label>Primärfarbe</label><input type="color" data-c="primary" value="${c.colors.primary}" /></div>
      <div style="flex:1;"><label>Hintergrund</label><input type="color" data-c="background" value="${c.colors.background}" /></div>
      <div style="flex:1;"><label>Text</label><input type="color" data-c="text" value="${c.colors.text}" /></div>
    </div>
    <label>Titel</label><input data-t="title" value="${escapeAttr(c.texts.title)}" />
    <label>Nachricht</label><textarea data-t="message" rows="3">${escapeHtml(c.texts.message)}</textarea>
    <label>Logo-URL (optional)</label><input data-f="logo" value="${escapeAttr(c.logo || "")}" placeholder="https://.../logo.png" />
    <label style="display:flex;align-items:center;gap:8px;margin-top:14px;font-weight:500;">
      <input type="checkbox" data-pb ${c.showPoweredBy ? "checked" : ""} ${canRemovePb ? "" : "disabled"} style="width:auto;" />
      „geschützt mit ConsentFlow“ anzeigen ${canRemovePb ? "" : "(nur im Agency-Plan abschaltbar)"}
    </label>
    <button id="editor-save" class="btn" style="width:100%;margin-top:18px;">Speichern</button>
  `;
  // Live-Vorschau bei jeder Änderung
  form.querySelectorAll("input,textarea,select").forEach((el) => {
    el.addEventListener("input", () => renderPreview(collectConfig()));
  });
  $("editor-save").onclick = saveEditor;
}

function collectConfig() {
  const form = $("editor-form");
  const c = structuredClone(editing.config);
  c.position = form.querySelector('[data-f="position"]').value;
  c.logo = form.querySelector('[data-f="logo"]').value.trim();
  form.querySelectorAll("[data-c]").forEach((el) => { c.colors[el.dataset.c] = el.value; });
  form.querySelectorAll("[data-t]").forEach((el) => { c.texts[el.dataset.t] = el.value; });
  const pb = form.querySelector("[data-pb]");
  c.showPoweredBy = pb.disabled ? true : pb.checked;
  return c;
}

async function saveEditor() {
  const form = $("editor-form");
  const payload = {
    name: form.querySelector('[data-f="name"]').value.trim(),
    domain: form.querySelector('[data-f="domain"]').value.trim(),
    config: collectConfig(),
  };
  $("editor-save").disabled = true;
  try {
    const { site } = await api.updateSite(editing.id, payload);
    editing = site;
    renderPreview(site.config);
    $("editor-msg").innerHTML = '<div class="ok">Gespeichert.</div>';
    setTimeout(() => ($("editor-msg").innerHTML = ""), 2500);
    refreshSites();
  } catch (e) {
    $("editor-msg").innerHTML = `<div class="error">${escapeHtml(e.message)}</div>`;
  } finally {
    $("editor-save").disabled = false;
  }
}

// Mini-Nachbau des echten Banners für die Vorschau.
function renderPreview(c) {
  const box = $("preview");
  box.innerHTML = "";
  const col = c.colors, t = c.texts;
  const panel = document.createElement("div");
  const boxPos = c.position === "box"
    ? "right:10px;bottom:10px;max-width:78%;border-radius:12px;"
    : "left:10px;right:10px;bottom:10px;border-radius:10px;";
  panel.style.cssText = `position:absolute;${boxPos}background:${col.background};color:${col.text};
    box-shadow:0 6px 24px rgba(0,0,0,.18);padding:14px 16px;font-size:13px;`;
  panel.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
      ${c.logo ? `<img src="${escapeAttr(c.logo)}" style="height:18px;" onerror="this.style.display='none'"/>` : ""}
      <strong>${escapeHtml(t.title)}</strong>
    </div>
    <div style="opacity:.85;margin-bottom:10px;">${escapeHtml(t.message)}</div>
    <div style="display:flex;gap:6px;flex-wrap:wrap;">
      <span style="background:${col.primary};color:#fff;padding:7px 12px;border-radius:7px;font-weight:600;">${escapeHtml(t.acceptAll)}</span>
      <span style="background:${col.secondary};color:${col.text};padding:7px 12px;border-radius:7px;font-weight:600;">${escapeHtml(t.rejectAll)}</span>
      <span style="padding:7px 12px;text-decoration:underline;">${escapeHtml(t.settings)}</span>
    </div>
    ${c.showPoweredBy ? `<div style="text-align:right;font-size:10px;opacity:.6;margin-top:8px;">${escapeHtml(t.poweredBy)}</div>` : ""}
  `;
  box.append(panel);
}

function renderSnippet(id) {
  const base = api.apiBase.replace(/\/$/, "");
  // In Produktion liegt das Widget auf dem CDN; hier die API-Domain als Default.
  $("snippet").textContent =
    `<script async\n  src="${base}/widget.js"\n  data-cf-site="${id}"\n  data-cf-api="${base}"><\/script>`;
  $("btn-copy").onclick = () => {
    navigator.clipboard.writeText($("snippet").textContent);
    $("btn-copy").textContent = "Kopiert ✓";
    setTimeout(() => ($("btn-copy").textContent = "Snippet kopieren"), 1800);
  };
}

// ---------------- Einwilligungen ----------------
async function openConsents(site) {
  $("consents-title").textContent = "Einwilligungen – " + site.name;
  const stats = await api.stats(site.id);
  $("consents-stats").innerHTML = [
    statCard("Gesamt protokolliert", stats.total),
    statCard("Letzte 30 Tage", stats.last30Days),
    statCard("mit Statistik/Marketing", stats.acceptedAny),
    statCard("Alle akzeptiert", stats.byAction.accept_all || 0),
    statCard("Abgelehnt", stats.byAction.reject_all || 0),
  ].join("");
  const link = $("consents-csv");
  link.onclick = (e) => { e.preventDefault(); downloadCsv(site); };
  show("consents");
}

async function downloadCsv(site) {
  // CSV-Endpunkt braucht den Auth-Header → per fetch holen, dann als Blob speichern.
  const res = await fetch(api.csvUrl(site.id), {
    headers: { Authorization: "Bearer " + localStorage.getItem("consentflow_token") },
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "consent-log-" + site.id + ".csv";
  a.click();
  URL.revokeObjectURL(url);
}

function statCard(label, value) {
  return `<div class="card"><div style="font-size:28px;font-weight:800;">${value}</div>
    <div class="muted" style="font-size:13px;">${label}</div></div>`;
}

// ---------------- Abrechnung ----------------
async function openBilling() {
  currentUser = (await api.me()).user;
  $("billing-plan").textContent = planLabel(currentUser.plan);
  $("billing-status").textContent = currentUser.subscriptionStatus ? `(${currentUser.subscriptionStatus})` : "";
  const params = new URLSearchParams(location.search);
  if (params.get("status") === "success") {
    $("billing-msg").innerHTML = '<div class="ok">Danke! Dein Abo wird aktiviert, sobald Stripe die Zahlung bestätigt.</div>';
  } else if (params.get("status") === "cancel") {
    $("billing-msg").innerHTML = '<div class="error">Checkout abgebrochen.</div>';
  } else {
    $("billing-msg").innerHTML = "";
  }
  show("billing");
}

async function startCheckout(plan) {
  try {
    const { url } = await api.checkout(plan);
    location.href = url;
  } catch (e) {
    $("billing-msg").innerHTML = `<div class="error">${escapeHtml(e.message)}</div>`;
  }
}

async function openPortal() {
  try {
    const { url } = await api.portal();
    location.href = url;
  } catch (e) {
    $("billing-msg").innerHTML = `<div class="error">${escapeHtml(e.message)}</div>`;
  }
}

// ---------------- Helfer ----------------
function planLabel(p) {
  return { trial: "Free-Trial", starter: "Starter", agency: "Agency" }[p] || p;
}
function btn(text, cls, onclick) {
  const b = document.createElement("button");
  b.className = cls;
  b.textContent = text;
  b.onclick = onclick;
  return b;
}
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function escapeAttr(s) {
  return escapeHtml(s);
}
