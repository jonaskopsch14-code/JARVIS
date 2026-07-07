import { uuid, visitorHash } from "../crypto.js";
import { json, error, corsHeaders } from "../http.js";

// Öffentlich: Bannerkonfiguration für das Widget (ohne Auth, CORS offen).
export async function publicConfig(request, env, ctx) {
  const site = await env.DB.prepare("SELECT id, config FROM sites WHERE id = ?")
    .bind(ctx.params.id).first();
  if (!site) return error(404, "Unbekannte Website-ID.", { headers: corsHeaders() });

  const config = JSON.parse(site.config);
  return json(
    { siteId: site.id, consentVersion: env.CONSENT_VERSION || "1", config },
    { headers: { ...corsHeaders(), "Cache-Control": "public, max-age=300" } }
  );
}

// Öffentlich: Einwilligung protokollieren (Nachweispflicht, pseudonymisiert).
export async function logConsent(request, env, ctx) {
  const body = await safeJson(request);
  const siteId = String(body.siteId || "");
  if (!siteId) return error(400, "siteId fehlt.", { headers: corsHeaders() });

  const site = await env.DB.prepare("SELECT id FROM sites WHERE id = ?").bind(siteId).first();
  if (!site) return error(404, "Unbekannte Website-ID.", { headers: corsHeaders() });

  const cats = body.categories || {};
  const action = ["accept_all", "reject_all", "save", "withdraw"].includes(body.action)
    ? body.action
    : "save";

  const ip = request.headers.get("CF-Connecting-IP") || "";
  const ua = request.headers.get("User-Agent") || "";
  const daySalt = new Date().toISOString().slice(0, 10) + (env.JWT_SECRET || "salt");
  const vhash = await visitorHash(ip, ua, daySalt);

  await env.DB.prepare(
    `INSERT INTO consents (id, site_id, visitor_hash, necessary, statistics, marketing, action, consent_version, created_at)
     VALUES (?, ?, ?, 1, ?, ?, ?, ?, ?)`
  ).bind(
    uuid(), siteId, vhash,
    cats.statistics ? 1 : 0,
    cats.marketing ? 1 : 0,
    action,
    String(body.consentVersion || env.CONSENT_VERSION || "1"),
    new Date().toISOString()
  ).run();

  return json({ ok: true }, { headers: corsHeaders() });
}

// Auth: Statistik zu Einwilligungen einer Website.
export async function consentStats(request, env, ctx) {
  const owned = await env.DB.prepare("SELECT id FROM sites WHERE id = ? AND user_id = ?")
    .bind(ctx.params.id, ctx.userId).first();
  if (!owned) return error(404, "Website nicht gefunden.");

  const total = await env.DB.prepare("SELECT COUNT(*) AS n FROM consents WHERE site_id = ?")
    .bind(ctx.params.id).first();
  const byAction = await env.DB.prepare(
    "SELECT action, COUNT(*) AS n FROM consents WHERE site_id = ? GROUP BY action"
  ).bind(ctx.params.id).all();
  const accepted = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM consents WHERE site_id = ? AND (statistics = 1 OR marketing = 1)"
  ).bind(ctx.params.id).first();
  const last30 = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM consents WHERE site_id = ? AND created_at >= ?"
  ).bind(ctx.params.id, new Date(Date.now() - 30 * 86400_000).toISOString()).first();

  const actions = {};
  for (const row of byAction.results) actions[row.action] = row.n;

  return json({
    total: total.n,
    acceptedAny: accepted.n,
    last30Days: last30.n,
    byAction: actions,
  });
}

// Auth: CSV-Export der Einwilligungen (Nachweispflicht).
export async function exportCsv(request, env, ctx) {
  const owned = await env.DB.prepare("SELECT id, name FROM sites WHERE id = ? AND user_id = ?")
    .bind(ctx.params.id, ctx.userId).first();
  if (!owned) return error(404, "Website nicht gefunden.");

  const { results } = await env.DB.prepare(
    `SELECT created_at, action, necessary, statistics, marketing, consent_version, visitor_hash
     FROM consents WHERE site_id = ? ORDER BY created_at DESC LIMIT 50000`
  ).bind(ctx.params.id).all();

  const header = "zeitstempel,aktion,notwendig,statistik,marketing,consent_version,besucher_hash";
  const rows = results.map((r) =>
    [r.created_at, r.action, r.necessary, r.statistics, r.marketing, r.consent_version, r.visitor_hash]
      .map(csvCell).join(",")
  );
  const csv = [header, ...rows].join("\r\n");

  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="consent-log-${ctx.params.id}.csv"`,
    },
  });
}

function csvCell(v) {
  const s = String(v ?? "");
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

async function safeJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}
