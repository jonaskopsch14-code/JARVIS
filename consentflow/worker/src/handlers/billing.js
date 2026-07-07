import { json, error } from "../http.js";

// Stripe via REST (kein SDK nötig im Worker).
const STRIPE_API = "https://api.stripe.com/v1";

function stripe(env, path, method = "POST", form = null) {
  const init = {
    method,
    headers: {
      Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
  };
  if (form) init.body = new URLSearchParams(form).toString();
  return fetch(`${STRIPE_API}${path}`, init);
}

const PRICE_BY_PLAN = (env) => ({
  starter: env.STRIPE_PRICE_STARTER,
  agency: env.STRIPE_PRICE_AGENCY,
});

// Stripe Checkout-Session erzeugen → gibt URL zurück, auf die das Dashboard weiterleitet.
export async function checkout(request, env, ctx) {
  if (!env.STRIPE_SECRET_KEY) return error(503, "Zahlung ist noch nicht konfiguriert.");
  const body = await safeJson(request);
  const plan = body.plan === "agency" ? "agency" : "starter";
  const price = PRICE_BY_PLAN(env)[plan];
  if (!price) return error(500, "Preis-ID für den Plan fehlt in der Konfiguration.");

  const user = await env.DB.prepare("SELECT * FROM users WHERE id = ?").bind(ctx.userId).first();
  let customerId = user.stripe_customer_id;
  if (!customerId) {
    const res = await stripe(env, "/customers", "POST", {
      email: user.email,
      "metadata[user_id]": user.id,
    });
    const customer = await res.json();
    if (!res.ok) return error(502, "Stripe-Kunde konnte nicht angelegt werden.", { detail: customer.error?.message });
    customerId = customer.id;
    await env.DB.prepare("UPDATE users SET stripe_customer_id = ? WHERE id = ?")
      .bind(customerId, user.id).run();
  }

  const appUrl = env.APP_URL || "https://app.consentflow.de";
  const res = await stripe(env, "/checkout/sessions", "POST", {
    mode: "subscription",
    customer: customerId,
    "line_items[0][price]": price,
    "line_items[0][quantity]": "1",
    success_url: `${appUrl}/billing?status=success`,
    cancel_url: `${appUrl}/billing?status=cancel`,
    "metadata[user_id]": user.id,
    "metadata[plan]": plan,
    "subscription_data[metadata][user_id]": user.id,
    "subscription_data[metadata][plan]": plan,
  });
  const session = await res.json();
  if (!res.ok) return error(502, "Checkout konnte nicht erstellt werden.", { detail: session.error?.message });
  return json({ url: session.url });
}

// Stripe Customer Portal (Abo verwalten/kündigen, Zahlungsdaten).
export async function portal(request, env, ctx) {
  if (!env.STRIPE_SECRET_KEY) return error(503, "Zahlung ist noch nicht konfiguriert.");
  const user = await env.DB.prepare("SELECT stripe_customer_id FROM users WHERE id = ?")
    .bind(ctx.userId).first();
  if (!user?.stripe_customer_id) return error(400, "Noch kein Abo vorhanden.");

  const res = await stripe(env, "/billing_portal/sessions", "POST", {
    customer: user.stripe_customer_id,
    return_url: `${env.APP_URL || "https://app.consentflow.de"}/billing`,
  });
  const session = await res.json();
  if (!res.ok) return error(502, "Portal konnte nicht geöffnet werden.", { detail: session.error?.message });
  return json({ url: session.url });
}

// Stripe-Webhook: Abostatus & Plan synchronisieren.
export async function webhook(request, env) {
  const payload = await request.text();
  const sig = request.headers.get("Stripe-Signature") || "";
  if (env.STRIPE_WEBHOOK_SECRET) {
    const ok = await verifyStripeSignature(payload, sig, env.STRIPE_WEBHOOK_SECRET);
    if (!ok) return error(400, "Ungültige Webhook-Signatur.");
  }

  let event;
  try {
    event = JSON.parse(payload);
  } catch {
    return error(400, "Ungültiger Payload.");
  }

  const obj = event.data?.object || {};
  switch (event.type) {
    case "checkout.session.completed":
    case "customer.subscription.created":
    case "customer.subscription.updated": {
      const plan = obj.metadata?.plan || (await inferPlan(env, obj));
      const status = obj.status || "active";
      const customerId = obj.customer;
      const subId = obj.subscription || obj.id;
      await env.DB.prepare(
        `UPDATE users SET plan = COALESCE(?, plan), subscription_status = ?, stripe_subscription_id = ?
         WHERE stripe_customer_id = ?`
      ).bind(plan || null, status, subId, customerId).run();
      break;
    }
    case "customer.subscription.deleted": {
      await env.DB.prepare(
        "UPDATE users SET plan = 'trial', subscription_status = 'canceled' WHERE stripe_customer_id = ?"
      ).bind(obj.customer).run();
      break;
    }
  }
  return json({ received: true });
}

async function inferPlan(env, obj) {
  const price = obj.items?.data?.[0]?.price?.id;
  if (price === env.STRIPE_PRICE_AGENCY) return "agency";
  if (price === env.STRIPE_PRICE_STARTER) return "starter";
  return null;
}

// Stripe-Signaturprüfung (HMAC-SHA256 über `${t}.${payload}`).
async function verifyStripeSignature(payload, header, secret) {
  const parts = Object.fromEntries(header.split(",").map((p) => p.split("=")));
  const t = parts.t;
  const v1 = parts.v1;
  if (!t || !v1) return false;
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(`${t}.${payload}`));
  const hex = [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
  // konstantzeitähnlicher Vergleich
  if (hex.length !== v1.length) return false;
  let diff = 0;
  for (let i = 0; i < hex.length; i++) diff |= hex.charCodeAt(i) ^ v1.charCodeAt(i);
  return diff === 0;
}

async function safeJson(request) {
  try {
    return await request.json();
  } catch {
    return {};
  }
}
