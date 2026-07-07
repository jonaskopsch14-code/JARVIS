-- ConsentFlow – Datenbankschema (Cloudflare D1 / SQLite)
-- Ausführen mit:  wrangler d1 execute consentflow --file=./schema.sql

-- Nutzerkonten (Website-Betreiber / Agenturen)
CREATE TABLE IF NOT EXISTS users (
  id                     TEXT PRIMARY KEY,            -- uuid
  email                  TEXT UNIQUE NOT NULL,
  password_hash          TEXT NOT NULL,               -- PBKDF2(SHA-256)
  created_at             TEXT NOT NULL,
  plan                   TEXT NOT NULL DEFAULT 'trial', -- trial | starter | agency
  trial_ends_at          TEXT,
  stripe_customer_id     TEXT,
  stripe_subscription_id TEXT,
  subscription_status    TEXT                         -- active | past_due | canceled | trialing
);

-- Websites (jede Website = ein einbindbares Snippet)
CREATE TABLE IF NOT EXISTS sites (
  id         TEXT PRIMARY KEY,   -- öffentliche Konfig-ID (im Snippet sichtbar)
  user_id    TEXT NOT NULL,
  name       TEXT NOT NULL,
  domain     TEXT,
  config     TEXT NOT NULL,      -- JSON: Farben, Position, Logo, Texte, Kategorien
  created_at TEXT NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sites_user ON sites(user_id);

-- Einwilligungs-Protokoll (Nachweispflicht, pseudonymisiert)
CREATE TABLE IF NOT EXISTS consents (
  id              TEXT PRIMARY KEY,
  site_id         TEXT NOT NULL,
  visitor_hash    TEXT NOT NULL,    -- SHA-256(IP + UA + Tages-Salt) – kein Klarname
  necessary       INTEGER NOT NULL DEFAULT 1,
  statistics      INTEGER NOT NULL DEFAULT 0,
  marketing       INTEGER NOT NULL DEFAULT 0,
  action          TEXT NOT NULL,    -- accept_all | reject_all | save | withdraw
  consent_version TEXT,
  created_at      TEXT NOT NULL,
  FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_consents_site ON consents(site_id, created_at);
