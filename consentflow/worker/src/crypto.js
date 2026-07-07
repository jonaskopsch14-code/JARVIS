// Krypto-Helfer auf Basis der Web Crypto API (Cloudflare Workers & Node 22).
// Keine externen Abhängigkeiten.

const enc = new TextEncoder();
const dec = new TextDecoder();

export function uuid() {
  return crypto.randomUUID();
}

// ---------- Base64URL ----------
function bytesToB64url(bytes) {
  let bin = "";
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function b64urlToBytes(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  while (str.length % 4) str += "=";
  const bin = atob(str);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}

// ---------- Passwort-Hashing (PBKDF2-SHA256) ----------
const PBKDF2_ITERATIONS = 100_000;

export async function hashPassword(password) {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const bits = await pbkdf2(password, salt, PBKDF2_ITERATIONS);
  return `pbkdf2$${PBKDF2_ITERATIONS}$${bytesToB64url(salt)}$${bytesToB64url(bits)}`;
}

export async function verifyPassword(password, stored) {
  try {
    const [scheme, iterStr, saltB64, hashB64] = stored.split("$");
    if (scheme !== "pbkdf2") return false;
    const salt = b64urlToBytes(saltB64);
    const expected = b64urlToBytes(hashB64);
    const bits = await pbkdf2(password, salt, parseInt(iterStr, 10));
    return timingSafeEqual(bits, expected);
  } catch {
    return false;
  }
}

async function pbkdf2(password, salt, iterations) {
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(password),
    "PBKDF2",
    false,
    ["deriveBits"]
  );
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations, hash: "SHA-256" },
    key,
    256
  );
  return new Uint8Array(bits);
}

function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
  return diff === 0;
}

// ---------- JWT (HS256) ----------
async function hmacKey(secret) {
  return crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

export async function signJwt(payload, secret, expiresInSeconds = 60 * 60 * 24 * 30) {
  const header = { alg: "HS256", typ: "JWT" };
  const now = Math.floor(Date.now() / 1000);
  const body = { ...payload, iat: now, exp: now + expiresInSeconds };
  const h = bytesToB64url(enc.encode(JSON.stringify(header)));
  const p = bytesToB64url(enc.encode(JSON.stringify(body)));
  const data = `${h}.${p}`;
  const key = await hmacKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(data));
  return `${data}.${bytesToB64url(new Uint8Array(sig))}`;
}

export async function verifyJwt(token, secret) {
  try {
    const [h, p, s] = token.split(".");
    if (!h || !p || !s) return null;
    const data = `${h}.${p}`;
    const key = await hmacKey(secret);
    const ok = await crypto.subtle.verify("HMAC", key, b64urlToBytes(s), enc.encode(data));
    if (!ok) return null;
    const payload = JSON.parse(dec.decode(b64urlToBytes(p)));
    if (payload.exp && Math.floor(Date.now() / 1000) > payload.exp) return null;
    return payload;
  } catch {
    return null;
  }
}

// ---------- Besucher-Pseudonymisierung ----------
// SHA-256 über IP + User-Agent + Tages-Salt. Kein Klarname, IP nicht rekonstruierbar.
export async function visitorHash(ip, userAgent, daySalt) {
  const input = `${ip || "0.0.0.0"}|${userAgent || ""}|${daySalt}`;
  const digest = await crypto.subtle.digest("SHA-256", enc.encode(input));
  return bytesToB64url(new Uint8Array(digest));
}
