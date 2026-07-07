// Integrationstests für die ConsentFlow-API (Worker gegen In-Memory-D1).
// Ausführen:  node --test  (im Ordner worker/)
import { test } from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";
import { makeD1 } from "./d1-stub.js";
import { hashPassword, verifyPassword, signJwt, verifyJwt } from "../src/crypto.js";

function makeEnv() {
  return { DB: makeD1(), JWT_SECRET: "test-secret-123", CONSENT_VERSION: "1", APP_URL: "http://localhost:4321" };
}

function req(method, path, { body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  if (method === "POST" || method === "PUT") headers["CF-Connecting-IP"] = "203.0.113.5";
  return new Request("https://api.test" + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

test("crypto: Passwort-Hash & Verifikation", async () => {
  const h = await hashPassword("geheim1234");
  assert.ok(h.startsWith("pbkdf2$"));
  assert.equal(await verifyPassword("geheim1234", h), true);
  assert.equal(await verifyPassword("falsch", h), false);
});

test("crypto: JWT signieren & prüfen", async () => {
  const token = await signJwt({ sub: "u1", email: "a@b.de" }, "s");
  const payload = await verifyJwt(token, "s");
  assert.equal(payload.sub, "u1");
  assert.equal(await verifyJwt(token, "anders"), null);
  assert.equal(await verifyJwt("kaputt", "s"), null);
});

test("Registrierung, Login und /me", async () => {
  const env = makeEnv();
  let res = await worker.fetch(req("POST", "/v1/auth/register", { body: { email: "a@b.de", password: "geheim1234" } }), env);
  assert.equal(res.status, 200);
  const reg = await res.json();
  assert.ok(reg.token);
  assert.equal(reg.user.plan, "trial");

  // Doppelte Registrierung → 409
  res = await worker.fetch(req("POST", "/v1/auth/register", { body: { email: "a@b.de", password: "geheim1234" } }), env);
  assert.equal(res.status, 409);

  // Falsches Passwort → 401
  res = await worker.fetch(req("POST", "/v1/auth/login", { body: { email: "a@b.de", password: "falsch" } }), env);
  assert.equal(res.status, 401);

  // Login korrekt
  res = await worker.fetch(req("POST", "/v1/auth/login", { body: { email: "a@b.de", password: "geheim1234" } }), env);
  assert.equal(res.status, 200);
  const login = await res.json();

  res = await worker.fetch(req("GET", "/v1/me", { token: login.token }), env);
  assert.equal((await res.json()).user.email, "a@b.de");
});

test("Auth erforderlich: /v1/sites ohne Token → 401", async () => {
  const env = makeEnv();
  const res = await worker.fetch(req("GET", "/v1/sites"), env);
  assert.equal(res.status, 401);
});

test("Website anlegen, Konfig lesen, Plan-Limit greift", async () => {
  const env = makeEnv();
  const reg = await (await worker.fetch(req("POST", "/v1/auth/register", { body: { email: "c@d.de", password: "geheim1234" } }), env)).json();
  const token = reg.token;

  const res = await worker.fetch(req("POST", "/v1/sites", { token, body: { name: "Meine Seite", domain: "example.de" } }), env);
  assert.equal(res.status, 201);
  const site = (await res.json()).site;
  assert.ok(site.id.startsWith("cf_"));
  assert.equal(site.config.language, "de");
  assert.equal(site.config.showPoweredBy, true);

  // Trial-Limit = 1 Website → zweite muss scheitern
  const res2 = await worker.fetch(req("POST", "/v1/sites", { token, body: { name: "Zweite" } }), env);
  assert.equal(res2.status, 403);
  assert.equal((await res2.json()).code, "plan_limit");

  // Öffentliche Konfiguration (ohne Auth)
  const cfg = await worker.fetch(req("GET", "/v1/config/" + site.id), env);
  assert.equal(cfg.status, 200);
  const cfgBody = await cfg.json();
  assert.equal(cfgBody.siteId, site.id);
  assert.equal(cfgBody.config.texts.acceptAll, "Alle akzeptieren");
});

test("powered-by lässt sich nur mit Agency-Plan entfernen", async () => {
  const env = makeEnv();
  const reg = await (await worker.fetch(req("POST", "/v1/auth/register", { body: { email: "e@f.de", password: "geheim1234" } }), env)).json();
  const token = reg.token;
  const site = (await (await worker.fetch(req("POST", "/v1/sites", { token, body: { name: "S" } }), env)).json()).site;

  // Trial-Nutzer versucht powered-by zu entfernen → bleibt an
  const upd = await worker.fetch(req("PUT", "/v1/sites/" + site.id, { token, body: { config: { showPoweredBy: false } } }), env);
  assert.equal((await upd.json()).site.config.showPoweredBy, true);

  // Nutzer auf Agency hochstufen → jetzt entfernbar
  env.DB.prepare("UPDATE users SET plan='agency' WHERE email='e@f.de'").bind().run();
  const upd2 = await worker.fetch(req("PUT", "/v1/sites/" + site.id, { token, body: { config: { showPoweredBy: false } } }), env);
  assert.equal((await upd2.json()).site.config.showPoweredBy, false);
});

test("Consent protokollieren, Statistik und CSV-Export", async () => {
  const env = makeEnv();
  const reg = await (await worker.fetch(req("POST", "/v1/auth/register", { body: { email: "g@h.de", password: "geheim1234" } }), env)).json();
  const token = reg.token;
  const site = (await (await worker.fetch(req("POST", "/v1/sites", { token, body: { name: "S" } }), env)).json()).site;

  // drei Einwilligungen protokollieren
  await worker.fetch(req("POST", "/v1/consent", { body: { siteId: site.id, action: "accept_all", categories: { statistics: true, marketing: true } } }), env);
  await worker.fetch(req("POST", "/v1/consent", { body: { siteId: site.id, action: "reject_all", categories: { statistics: false, marketing: false } } }), env);
  await worker.fetch(req("POST", "/v1/consent", { body: { siteId: site.id, action: "save", categories: { statistics: true, marketing: false } } }), env);

  const stats = await (await worker.fetch(req("GET", "/v1/sites/" + site.id + "/stats", { token }), env)).json();
  assert.equal(stats.total, 3);
  assert.equal(stats.acceptedAny, 2);
  assert.equal(stats.byAction.accept_all, 1);

  const csvRes = await worker.fetch(req("GET", "/v1/sites/" + site.id + "/export.csv", { token }), env);
  assert.equal(csvRes.headers.get("Content-Type"), "text/csv; charset=utf-8");
  const csv = await csvRes.text();
  const lines = csv.trim().split("\r\n");
  assert.equal(lines.length, 4); // Header + 3 Zeilen
  assert.ok(lines[0].startsWith("zeitstempel,aktion"));

  // Consent für unbekannte Website → 404, aber MIT CORS-Header (Widget-Aufruf)
  const bad = await worker.fetch(req("POST", "/v1/consent", { body: { siteId: "cf_unbekannt", action: "accept_all" } }), env);
  assert.equal(bad.status, 404);
  assert.equal(bad.headers.get("Access-Control-Allow-Origin"), "*");
});

test("Besucher-Hash enthält keine Klartext-IP", async () => {
  const env = makeEnv();
  const reg = await (await worker.fetch(req("POST", "/v1/auth/register", { body: { email: "i@j.de", password: "geheim1234" } }), env)).json();
  const token = reg.token;
  const site = (await (await worker.fetch(req("POST", "/v1/sites", { token, body: { name: "S" } }), env)).json()).site;
  await worker.fetch(req("POST", "/v1/consent", { body: { siteId: site.id, action: "accept_all", categories: { statistics: true } } }), env);

  const row = env.DB.prepare("SELECT visitor_hash FROM consents WHERE site_id = ?").bind(site.id).first();
  assert.ok(row.visitor_hash);
  assert.ok(!row.visitor_hash.includes("203.0.113.5")); // IP nicht im Klartext
});
