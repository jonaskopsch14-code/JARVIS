import { uuid } from "../crypto.js";
import { json, error, defaultBannerConfig, PLAN_LIMITS } from "../http.js";

// Kurze, gut lesbare öffentliche Site-ID (im Snippet sichtbar).
function siteId() {
  return "cf_" + uuid().replace(/-/g, "").slice(0, 20);
}

export async function listSites(request, env, ctx) {
  const { results } = await env.DB.prepare(
    "SELECT id, name, domain, config, created_at FROM sites WHERE user_id = ? ORDER BY created_at DESC"
  ).bind(ctx.userId).all();
  return json({ sites: results.map(rowToSite) });
}

export async function createSite(request, env, ctx) {
  const body = await safeJson(request);
  const name = String(body.name || "").trim();
  if (!name) return error(400, "Bitte einen Namen für die Website angeben.");

  const user = await env.DB.prepare("SELECT plan FROM users WHERE id = ?").bind(ctx.userId).first();
  const limit = PLAN_LIMITS[user?.plan] ?? PLAN_LIMITS.trial;
  const count = await env.DB.prepare("SELECT COUNT(*) AS n FROM sites WHERE user_id = ?").bind(ctx.userId).first();
  if (count.n >= limit) {
    return error(403, `Dein Plan erlaubt maximal ${limit} Website(s). Bitte upgraden.`, { code: "plan_limit" });
  }

  const id = siteId();
  const config = mergeConfig(defaultBannerConfig(), body.config);
  const now = new Date().toISOString();
  await env.DB.prepare(
    "INSERT INTO sites (id, user_id, name, domain, config, created_at) VALUES (?, ?, ?, ?, ?, ?)"
  ).bind(id, ctx.userId, name, String(body.domain || "").trim(), JSON.stringify(config), now).run();

  return json({ site: { id, name, domain: body.domain || "", config, createdAt: now } }, { status: 201 });
}

export async function getSite(request, env, ctx) {
  const site = await ownedSite(env, ctx);
  if (!site) return error(404, "Website nicht gefunden.");
  return json({ site: rowToSite(site) });
}

export async function updateSite(request, env, ctx) {
  const site = await ownedSite(env, ctx);
  if (!site) return error(404, "Website nicht gefunden.");
  const body = await safeJson(request);

  const name = body.name != null ? String(body.name).trim() : site.name;
  const domain = body.domain != null ? String(body.domain).trim() : site.domain;
  const config = body.config
    ? mergeConfig(JSON.parse(site.config), body.config)
    : JSON.parse(site.config);

  // "powered by" darf nur der Agency-Plan entfernen.
  const user = await env.DB.prepare("SELECT plan FROM users WHERE id = ?").bind(ctx.userId).first();
  if (user?.plan !== "agency") config.showPoweredBy = true;

  await env.DB.prepare(
    "UPDATE sites SET name = ?, domain = ?, config = ? WHERE id = ? AND user_id = ?"
  ).bind(name, domain, JSON.stringify(config), site.id, ctx.userId).run();

  return json({ site: { id: site.id, name, domain, config, createdAt: site.created_at } });
}

export async function deleteSite(request, env, ctx) {
  const res = await env.DB.prepare("DELETE FROM sites WHERE id = ? AND user_id = ?")
    .bind(ctx.params.id, ctx.userId).run();
  if (!res.meta.changes) return error(404, "Website nicht gefunden.");
  return json({ ok: true });
}

// ---------- Helfer ----------
async function ownedSite(env, ctx) {
  return env.DB.prepare("SELECT * FROM sites WHERE id = ? AND user_id = ?")
    .bind(ctx.params.id, ctx.userId).first();
}

function rowToSite(row) {
  return {
    id: row.id,
    name: row.name,
    domain: row.domain,
    config: JSON.parse(row.config),
    createdAt: row.created_at,
  };
}

// Flache, gezielte Zusammenführung – verhindert, dass Clients unbekannte Strukturen einschleusen.
function mergeConfig(base, patch) {
  if (!patch || typeof patch !== "object") return base;
  const out = structuredClone(base);
  const scalar = ["language", "position", "theme", "logo", "showPoweredBy"];
  for (const k of scalar) if (k in patch) out[k] = patch[k];
  if (patch.colors) Object.assign(out.colors, pick(patch.colors, ["background", "text", "primary", "secondary"]));
  if (patch.texts) Object.assign(out.texts, patch.texts);
  if (patch.categories) {
    for (const cat of ["necessary", "statistics", "marketing"]) {
      if (patch.categories[cat]) Object.assign(out.categories[cat], patch.categories[cat]);
    }
    out.categories.necessary.enabled = true; // notwendig ist immer aktiv
  }
  return out;
}

function pick(obj, keys) {
  const out = {};
  for (const k of keys) if (k in obj) out[k] = obj[k];
  return out;
}

async function safeJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}
