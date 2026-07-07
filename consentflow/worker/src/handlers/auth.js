import { uuid, hashPassword, verifyPassword, signJwt } from "../crypto.js";
import { json, error } from "../http.js";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const TRIAL_DAYS = 14;

export async function register(request, env) {
  const body = await safeJson(request);
  const email = String(body.email || "").trim().toLowerCase();
  const password = String(body.password || "");

  if (!EMAIL_RE.test(email)) return error(400, "Bitte eine gültige E-Mail-Adresse angeben.");
  if (password.length < 8) return error(400, "Das Passwort muss mindestens 8 Zeichen lang sein.");

  const existing = await env.DB.prepare("SELECT id FROM users WHERE email = ?").bind(email).first();
  if (existing) return error(409, "Für diese E-Mail existiert bereits ein Konto.");

  const id = uuid();
  const now = new Date();
  const trialEnds = new Date(now.getTime() + TRIAL_DAYS * 86400_000);
  const passwordHash = await hashPassword(password);

  await env.DB.prepare(
    `INSERT INTO users (id, email, password_hash, created_at, plan, trial_ends_at, subscription_status)
     VALUES (?, ?, ?, ?, 'trial', ?, 'trialing')`
  ).bind(id, email, passwordHash, now.toISOString(), trialEnds.toISOString()).run();

  const token = await signJwt({ sub: id, email }, env.JWT_SECRET);
  return json({ token, user: publicUser({ id, email, plan: "trial", trial_ends_at: trialEnds.toISOString() }) });
}

export async function login(request, env) {
  const body = await safeJson(request);
  const email = String(body.email || "").trim().toLowerCase();
  const password = String(body.password || "");

  const user = await env.DB.prepare("SELECT * FROM users WHERE email = ?").bind(email).first();
  if (!user || !(await verifyPassword(password, user.password_hash))) {
    return error(401, "E-Mail oder Passwort ist falsch.");
  }
  const token = await signJwt({ sub: user.id, email: user.email }, env.JWT_SECRET);
  return json({ token, user: publicUser(user) });
}

export async function me(request, env, ctx) {
  const user = await env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(ctx.userId).first();
  if (!user) return error(404, "Konto nicht gefunden.");
  return json({ user: publicUser(user) });
}

export function publicUser(u) {
  return {
    id: u.id,
    email: u.email,
    plan: u.plan,
    trialEndsAt: u.trial_ends_at || null,
    subscriptionStatus: u.subscription_status || null,
    hasBilling: Boolean(u.stripe_customer_id),
  };
}

async function safeJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}
