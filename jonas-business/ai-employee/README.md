# KI-Mitarbeiter — Einrichtung (n8n auf Hetzner, vom Handy machbar)

Diese Anleitung baut den 24/7-KI-Mitarbeiter auf: Er prüft neue E-Mails, erstellt
Antwort-Entwürfe (sendet **nie** selbst), überwacht die Website und schickt
Push-Nachrichten per Telegram aufs Handy.

**Gesamtkosten:** ~10–15 €/Monat (Hetzner CX22 3,79 € + Claude Haiku ~5 € + Rest kostenlos).

---

## Architektur auf einen Blick

```
Hetzner CX22 (Ubuntu, Docker)
 ├─ Caddy  → automatisches HTTPS für n8n.[DOMAIN]
 └─ n8n    → 2 Workflows:
      1) E-Mail-Agent  (alle 20 Min): Gmail lesen → Claude Haiku 4.5 → Gmail-Entwurf → Telegram
      2) Uptime-Check  (alle 5 Min):  Website prüfen → bei Ausfall Telegram-Alarm
Telegram-Bot → Benachrichtigungen aufs Handy
UptimeRobot (optional, kostenlos) → Alternative fürs Uptime-Monitoring
```

**Tiered Permission:** Kein Node sendet, löscht oder gibt Geld aus. Nur Lesen +
Entwürfe + Benachrichtigen. Siehe `SYSTEM-PROMPT.md`.

---

## Voraussetzungen (Konten anlegen)

| Was | Wo | Kosten | Zeit |
|---|---|---|---|
| Hetzner-Cloud-Konto + CX22-Server (Ubuntu) | hetzner.com | 3,79 €/Mon | 15 Min |
| Domain (Subdomain `n8n.` per DNS auf Server-IP) | Namecheap/INWX | ~10 €/Jahr | 10 Min |
| Anthropic-API-Key + Guthaben | console.anthropic.com | ~5–10 € Guthaben | 10 Min |
| Telegram-Bot (via @BotFather) | Telegram-App | kostenlos | 5 Min |
| Business-Gmail-Konto | google.com | kostenlos | 5 Min |
| UptimeRobot (optional) | uptimerobot.com | kostenlos | 10 Min |

---

## Schritt 1 — Server vorbereiten

1. Hetzner CX22 mit **Ubuntu** erstellen. (Einmalig am PC bequemer; vom Handy per
   SSH-App wie **Termius** machbar.)
2. DNS: A-Record `n8n.[DEINE-DOMAIN]` → Server-IP setzen. Ports **80** und **443**
   müssen erreichbar sein.
3. Docker + Docker Compose installieren (auf frischem Ubuntu):
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```
4. **Tägliche Hetzner-Snapshots** (~0,50 €/Monat) im Hetzner-Panel aktivieren — Backup.

## Schritt 2 — Dateien hochladen & starten

1. Den Ordner `ai-employee/` auf den Server kopieren (z. B. per `git clone` oder `scp`).
2. `.env.example` zu `.env` kopieren und **alle Werte eintragen**:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Wichtig: `N8N_HOST`, `N8N_BASIC_AUTH_*`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`,
   `TELEGRAM_CHAT_ID`, `WEBSITE_URL`.
3. Starten:
   ```bash
   docker compose up -d
   ```
4. Nach ~1 Minute `https://n8n.[DEINE-DOMAIN]` im Handy-Browser öffnen (Caddy hat das
   TLS-Zertifikat automatisch geholt). Mit Basic-Auth einloggen.

## Schritt 3 — Telegram-Bot einrichten

1. In Telegram **@BotFather** öffnen → `/newbot` → Namen vergeben → **Token** notieren
   (→ `TELEGRAM_BOT_TOKEN`).
2. Deinem neuen Bot **einmal „Hi" schreiben** (damit er dir schreiben darf).
3. **Chat-ID ermitteln:** im Browser aufrufen
   `https://api.telegram.org/bot<DEIN_TOKEN>/getUpdates` → das Feld `chat.id`
   ablesen (→ `TELEGRAM_CHAT_ID`).

## Schritt 4 — Workflows importieren

1. In n8n oben rechts **„Import from File"** wählen und nacheinander importieren:
   - `workflow-email-agent.json`
   - `workflow-uptime.json`
2. **Gmail-Credential** verbinden: im Gmail-Node „Connect my account" → OAuth-Login mit
   dem **Business-Gmail** durchführen (im Handy-Browser möglich).
3. **Telegram-Credential** verbinden: Telegram-Node → neues Credential → Bot-Token
   einfügen.
4. Der Claude-Aufruf nutzt `{{ $env.ANTHROPIC_API_KEY }}` direkt aus der `.env` — kein
   extra Credential nötig.

## Schritt 5 — Testen & aktivieren

1. Beide Workflows einmal **manuell** ausführen („Execute Workflow") und prüfen:
   - Kommt eine Telegram-Nachricht an?
   - Liegt ein **Entwurf** (kein gesendetes Mail!) in Gmail?
2. Wenn alles passt: beide Workflows auf **Active** schalten.

---

## Uptime: n8n **oder** UptimeRobot?

- **Empfehlung (Report):** Für reines Uptime-Monitoring **UptimeRobot Free** nutzen
  (50 Monitore, 5-Min-Intervall, direkte Telegram-Integration) — nichts selbst zu warten.
- **Alternative:** `workflow-uptime.json`, falls alles an einem Ort in n8n laufen soll.

UptimeRobot einrichten: Konto anlegen → „Add New Monitor" (HTTP(s), `WEBSITE_URL`) →
Telegram als Alert-Kontakt verbinden. Dann `workflow-uptime.json` weglassen.

---

## Wartung (kurz halten)

- n8n-Image ist **auf `1.70.0` gepinnt** — Version nur bewusst und nach Changelog-Check
  erhöhen (nie `:latest`).
- Update: `docker compose pull && docker compose up -d` nach dem Anheben der Version.
- Tägliche Hetzner-Snapshots aktiviert lassen.
- Sicherheits-Patches am Ubuntu-Server gelegentlich einspielen (`apt update && apt upgrade`).

## Sicherheits- & Verhaltensregeln
Der Agent **liest und entwirft nur**. Jonas liest jeden Entwurf, bevor er sendet.
Bei sensiblen Themen (Rechnungen, Rechtliches, Beschwerden, Rückerstattungen) sendet
er nie ungeprüft. Details: `SYSTEM-PROMPT.md`.
