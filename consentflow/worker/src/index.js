// ConsentFlow – Backend-API (Cloudflare Worker + D1)
//
// Öffentliche Endpunkte (Widget):
//   GET  /v1/config/:id          Bannerkonfiguration
//   POST /v1/consent             Einwilligung protokollieren
// Auth:
//   POST /v1/auth/register       Registrierung (14-Tage-Trial)
//   POST /v1/auth/login          Login
//   GET  /v1/me                  Aktuelles Konto
// Websites (Auth):
//   GET/POST        /v1/sites
//   GET/PUT/DELETE  /v1/sites/:id
//   GET  /v1/sites/:id/stats
//   GET  /v1/sites/:id/export.csv
// Abrechnung (Auth):
//   POST /v1/billing/checkout
//   POST /v1/billing/portal
//   POST /v1/billing/webhook     (Stripe, ohne Auth – Signaturprüfung)

import { verifyJwt } from "./crypto.js";
import { json, error, corsHeaders } from "./http.js";
import { register, login, me } from "./handlers/auth.js";
import {
  listSites, createSite, getSite, updateSite, deleteSite,
} from "./handlers/sites.js";
import {
  publicConfig, logConsent, consentStats, exportCsv,
} from "./handlers/consent.js";
import { checkout, portal, webhook } from "./handlers/billing.js";

// [method, pattern, handler, needsAuth]
const ROUTES = [
  ["GET", "/health", () => json({ ok: true, service: "consentflow-api" }), false],

  // Widget (öffentlich)
  ["GET", "/v1/config/:id", publicConfig, false],
  ["POST", "/v1/consent", logConsent, false],

  // Auth
  ["POST", "/v1/auth/register", register, false],
  ["POST", "/v1/auth/login", login, false],
  ["GET", "/v1/me", me, true],

  // Websites
  ["GET", "/v1/sites", listSites, true],
  ["POST", "/v1/sites", createSite, true],
  ["GET", "/v1/sites/:id", getSite, true],
  ["PUT", "/v1/sites/:id", updateSite, true],
  ["DELETE", "/v1/sites/:id", deleteSite, true],
  ["GET", "/v1/sites/:id/stats", consentStats, true],
  ["GET", "/v1/sites/:id/export.csv", exportCsv, true],

  // Abrechnung
  ["POST", "/v1/billing/checkout", checkout, true],
  ["POST", "/v1/billing/portal", portal, true],
  ["POST", "/v1/billing/webhook", webhook, false],
];

function match(pattern, path) {
  const p = pattern.split("/");
  const s = path.split("/");
  if (p.length !== s.length) return null;
  const params = {};
  for (let i = 0; i < p.length; i++) {
    if (p[i].startsWith(":")) params[p[i].slice(1)] = decodeURIComponent(s[i]);
    else if (p[i] !== s[i]) return null;
  }
  return params;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders() });
    }

    for (const [method, pattern, handler, needsAuth] of ROUTES) {
      if (method !== request.method) continue;
      const params = match(pattern, path);
      if (!params) continue;

      const ctx = { params };
      if (needsAuth) {
        const auth = request.headers.get("Authorization") || "";
        const token = auth.startsWith("Bearer ") ? auth.slice(7) : "";
        const payload = token ? await verifyJwt(token, env.JWT_SECRET) : null;
        if (!payload) return error(401, "Nicht autorisiert. Bitte anmelden.");
        ctx.userId = payload.sub;
        ctx.email = payload.email;
      }

      try {
        return await handler(request, env, ctx);
      } catch (err) {
        return error(500, "Interner Serverfehler.", { detail: String(err?.message || err) });
      }
    }

    return error(404, "Endpunkt nicht gefunden.");
  },
};
