# ConsentFlow

**DSGVO-konformer Cookie-Consent-Banner als Micro-SaaS für den DACH-Raum.**

Ein per Copy-&-Paste einbindbares Consent-Banner + zentrales Dashboard, mit dem
kleine Website-Betreiber und Agenturen rechtssichere Einwilligungen einsammeln,
protokollieren und verwalten — ab 29 €/Monat, ohne technisches Wissen.

> ⚖️ ConsentFlow ist ein **technisches Werkzeug**, keine Rechtsberatung.
> Details siehe [`RECHTLICHES.md`](./RECHTLICHES.md).

---

## Warum ConsentFlow

- **Echtes Opt-in** — nicht-notwendige Skripte (Analytics, Marketing) werden erst
  *nach* Einwilligung geladen. Genau das verlangt die DSGVO/TTDSG.
- **Nachweispflicht erfüllt** — jede Einwilligung wird pseudonymisiert protokolliert
  (gehashte IP + Zeitstempel + Consent-Status) und ist als CSV exportierbar.
- **Deutsch & anpassbar** — Farben, Position, Logo, Texte pro Website; Live-Vorschau.
- **Leicht & schnell** — Widget < 20 KB, framework-frei, `async` eingebunden.

## Architektur

```
consentflow/
├── widget/       Consent-Banner (Vanilla JS) – läuft auf den Kundenseiten
├── worker/       Backend-API (Cloudflare Worker + D1/SQLite)
└── dashboard/    Kunden-Dashboard (Astro, statisch → Cloudflare Pages)
```

| Baustein   | Technik                         | Warum                                   |
|------------|---------------------------------|-----------------------------------------|
| Widget     | Vanilla JS                      | klein, schnell, ohne Build auf jeder Seite lauffähig |
| Backend    | Cloudflare Worker + D1          | Serverless, kostenlos im Free-Tier      |
| Auth       | Eigenes JWT (Web Crypto/PBKDF2) | kein externer Dienst, keine Fixkosten   |
| Dashboard  | Astro (statisch) + Vanilla JS   | deploybar auf Cloudflare Pages (Free)   |
| Zahlung    | Stripe Checkout + Portal        | keine Fixkosten, nur % pro Transaktion  |

Der komplette Stack läuft (außer Domain & Stripe-Gebühren) im kostenlosen Tier.

### Datenfluss

```
Besucher ─▶ Widget ─▶ GET /v1/config/:id   (Bannerkonfiguration)
                   └▶ POST /v1/consent      (Einwilligung protokollieren, pseudonym)

Kunde   ─▶ Dashboard ─▶ /v1/auth/*, /v1/sites/*, /v1/billing/*  (JWT-geschützt)
                       └▶ Stripe Checkout / Customer Portal
```

## Schnellstart (lokal)

### 1. Backend (Worker + D1)

```bash
cd worker
npm install
npm run db:init:local          # Schema in lokale D1 laden
# Secrets für lokale Entwicklung in .dev.vars anlegen:
#   JWT_SECRET="dev-secret-bitte-aendern"
npm run dev                    # startet auf http://localhost:8787
```

### 2. Dashboard (Astro)

```bash
cd dashboard
npm install
echo "PUBLIC_API_URL=http://localhost:8787" > .env
npm run dev                    # startet auf http://localhost:4321
```

### 3. Widget testen

`widget/demo.html` im Browser öffnen (bindet die Widget-Quelle + lokale API ein)
oder das im Dashboard erzeugte Snippet auf einer eigenen Testseite einfügen.

## Tests

```bash
cd worker && npm test          # 9 Integrationstests (API end-to-end gegen In-Memory-D1)
```

Die Tests decken Registrierung/Login, JWT, Passwort-Hashing, Website-Verwaltung,
Plan-Limits, „powered by“-Regel, Consent-Protokollierung, Statistik, CSV-Export
und die Pseudonymisierung (keine Klartext-IP) ab.

## Deployment

### Worker (API)

```bash
cd worker
wrangler d1 create consentflow            # database_id in wrangler.toml eintragen
npm run db:init                           # Schema in Produktions-D1 laden
wrangler secret put JWT_SECRET
wrangler secret put STRIPE_SECRET_KEY
wrangler secret put STRIPE_WEBHOOK_SECRET
# STRIPE_PRICE_STARTER / STRIPE_PRICE_AGENCY in wrangler.toml [vars] setzen
npm run deploy
```

Das gebaute Widget (`widget/dist/widget.js`, via `npm run build`) unter
`/widget.js` bzw. auf einem CDN ausliefern.

### Dashboard (Pages)

```bash
cd dashboard
PUBLIC_API_URL=https://api.consentflow.de npm run build   # → dist/ auf Cloudflare Pages
```

### Stripe

1. Zwei Produkte/Preise anlegen: Starter (29 €/Monat), Agency (59 €/Monat).
2. Preis-IDs in `worker/wrangler.toml` (`STRIPE_PRICE_*`) eintragen.
3. Webhook-Endpunkt `https://api.consentflow.de/v1/billing/webhook` einrichten
   (Events: `checkout.session.completed`, `customer.subscription.*`).

## Pläne

| Plan       | Preis        | Websites | Besonderheit                     |
|------------|--------------|----------|----------------------------------|
| Free-Trial | 0 € / 14 Tage| 1        | voller Funktionsumfang           |
| Starter    | 29 € / Monat | bis 3    | deutscher E-Mail-Support         |
| Agency     | 59 € / Monat | bis 25   | „powered by“ entfernbar          |

## Freigabe-Punkte (durch Jonas)

Diese Schritte erfordern menschliche Freigabe (siehe Spec Abschnitt 7):
Domain kaufen · Cloudflare-Konto verbinden · Stripe-Konto (echte Zahlungen) ·
Go-Live · erste Marketing-Nachrichten.

## Status

Phase 1 (MVP) implementiert und getestet: Widget, Backend-API, Dashboard,
Stripe-Anbindung. Verifiziert durch API-Integrationstests und einen
Browser-End-to-End-Test des Opt-in-Flows.
