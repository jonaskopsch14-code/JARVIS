# jonas-business — ZahlenKlar: Etsy-Steuer-Cockpit + 24/7 KI-Mitarbeiter (DACH, 2026)

Komplettes, handy-taugliches Setup für ein anonym betreibbares Digitalprodukt-Business,
scharf positioniert auf **deutsche Etsy-Verkäufer:innen** (Kleinunternehmer): Verkauf des
**ZahlenKlar Etsy-Steuer-Cockpits** (Excel-Vorlage) über Lemon Squeezy, ein
**KI-Mitarbeiter** übernimmt E-Mail-Triage & Website-Monitoring, und eine schlanke
**Werbekampagne** (Pinterest + Google + organisch) zündet den Start.

> **Kein Get-rich-quick.** Realistisch: 0–300 €/Monat im ersten Jahr, mit Aufbau und
> Konsistenz 500–1.500 €/Monat. Erfolg hängt an Nische, Qualität und Durchhalten.

---

## Was in diesem Projekt liegt

```
jonas-business/
├── product/              Produktdefinition + Auslieferung
│   ├── produkt-spezifikation.md   ZahlenKlar Etsy-Cockpit (6 Blätter der Excel-v1)
│   ├── cockpit/                   >> DAS PRODUKT: ZahlenKlar_Etsy-Steuer-Cockpit_2026.xlsx
│   ├── guide/GUIDE-OUTLINE.md     PDF-Guide (Upsell, Roadmap)
│   └── lieferung/README.md        Automatische Auslieferung via Lemon Squeezy
├── landing/              Verkaufsseite (Etsy-Nische)
│   ├── index.html                 Responsive Landingpage (Deutsch, mobil-first, kein Video)
│   ├── style.css                  Styles (Light/Dark, ohne CDN)
│   └── PAYMENTS.md                Lemon Squeezy (MoR) vs. eigenes Stripe + Einbindung
├── legal/               Deutsche Rechtsseiten (PLATZHALTER — anwaltlich prüfen!)
│   ├── impressum.html             § 5 DDG, c/o-Adresse via Impressum-Service
│   ├── datenschutz.html           DSGVO (Lemon Squeezy, Pinterest, Google, Hosting)
│   ├── widerruf.html              § 356 Abs. 5 BGB — Verlust des Widerrufsrechts bei Download
│   └── agb.html                   AGB
├── ai-employee/         24/7 KI-Mitarbeiter (n8n auf Hetzner) — läuft unabhängig
│   ├── docker-compose.yml         n8n (gepinnt) + Caddy (auto-TLS)
│   ├── Caddyfile                  Reverse Proxy + HTTPS
│   ├── .env.example               Keys/Zugänge
│   ├── workflow-email-agent.json  Gmail → Claude Haiku → Entwurf → Telegram (sendet NIE)
│   ├── workflow-uptime.json       Website-Check → Telegram-Alarm
│   ├── SYSTEM-PROMPT.md            Tiered-Permission-Regeln für Claude
│   └── README.md                  Einrichtung Schritt für Schritt
├── ads/                 Werbekampagne (Etsy-Nische, 50–100 €/Monat)
│   ├── pinterest-kampagne.md      Struktur, Targeting, Pin-Specs
│   ├── pinterest-anzeigentexte.md 5 deutsche Anzeigentexte (DAC7, Gebühren, Reverse Charge …)
│   ├── google-ads-kampagne.md     Suchkampagne, Etsy-Long-Tail-Keywords, 3 RSAs
│   ├── erwartung.md               Ehrliche Werbe-Mathematik
│   └── organisch.md               0-€-Kanäle: organische Pins, SEO-Guide, Communities
├── .env.example         Zentrale Platzhalter für alle Keys
└── README.md            (diese Datei)
```

---

## Modell in einem Satz

Verkauf des **ZahlenKlar Etsy-Steuer-Cockpits** (Excel-Vorlage) über **Lemon Squeezy als
Merchant of Record** — ~90 % Marge, kein Fulfillment, keine EU-VAT-Bürokratie (Lemon
Squeezy führt die Umsatzsteuer ab), handy-verwaltbar und über einen Impressum-Service mit
geschützter Privatadresse betreibbar. Scharfe Nische statt Konkurrenz zu Gratis-Tools:
**deutsche Etsy-Seller als Kleinunternehmer.**

---

## Einrichtungs-Checkliste (alles vom Handy machbar)

Marke ist final: **ZahlenKlar**. Reihenfolge & Zeitaufwand pro Schritt.
**Gesamt einmalig ~3 Stunden**, danach ≤ 60 Min/Tag.

| # | Schritt | Wo / Datei | Zeit |
|---|---|---|---|
| 1 | **Impressum-Service** buchen (ladungsfähige c/o-Adresse, ~4,50 €/Mon) | `legal/impressum.html` | 5 Min |
| 2 | **Domain** kaufen (Namecheap/INWX), DNS vorbereiten | `.env.example` | 10 Min |
| 3 | **Excel-Datei** liegt bereit in `product/cockpit/ZahlenKlar_Etsy-Steuer-Cockpit_2026.xlsx` | `product/cockpit/` | — |
| 4 | **Lemon-Squeezy-Konto**: Produkt + Preis (29 €) anlegen, die **xlsx hochladen**, Auszahlung verbinden | `product/lieferung/README.md`, `landing/PAYMENTS.md` | 30 Min |
| 5 | **4 Screenshots** aus der Excel-Datei erstellen (Margenrechner, Reverse-Charge, Umsatz-Ampel, EÜR) und die `[SCREENSHOT: …]`-Platzhalter in `landing/index.html` ersetzen | `landing/index.html` | 20 Min |
| 6 | **Business-Gmail** anlegen (nicht privat) | — | 5 Min |
| 7 | **Hetzner CX22** (Ubuntu) erstellen, Docker installieren | `ai-employee/README.md` | 15 Min |
| 8 | **Telegram-Bot** via @BotFather, Token + Chat-ID | `ai-employee/README.md` | 5 Min |
| 9 | **Anthropic-API-Key** erstellen, ~5–10 € Guthaben | `ai-employee/.env.example` | 10 Min |
| 10 | **n8n-Workflows** importieren, Gmail-OAuth + Telegram + Claude verbinden | `ai-employee/README.md` | 30 Min |
| 11 | **UptimeRobot** (kostenlos), Monitor + Telegram-Alert | `ai-employee/README.md` | 10 Min |
| 12 | **Pinterest-Business + Werbekonto**, erste Kampagne | `ads/pinterest-kampagne.md` | 30 Min |
| 13 | **Google-Ads-Konto** (optional), Suchkampagne | `ads/google-ads-kampagne.md` | 20 Min |
| 14 | **Landingpage + Rechtsseiten** deployen (statisches Hosting), Buy-Button + Tags einbauen | `landing/`, `legal/` | 20 Min |

---

## Empfohlener Zeitplan

1. **Woche 1–2:** Impressum + Domain + Lemon Squeezy + das **Etsy-Cockpit** live bringen
   (xlsx hochladen, Screenshots einbauen). Vorher Marktcheck (Google/Etsy: „etsy steuern",
   „etsy gebühren rechner"). Ziel: verkaufsfähig, bevor Werbung startet.
2. **Woche 3:** KI-Mitarbeiter aufsetzen (Hetzner + n8n + Telegram). Erst wenn er
   zuverlässig Entwürfe liefert, weiter.
3. **Woche 4:** Pinterest-Kampagne mit 60 €, Google mit 15 € starten; parallel organische
   Pins + SEO-Guide (siehe `ads/organisch.md`).
   **Schwelle:** bei Conversion < 1 % nach 150 € Spend → Seite/Preis/Creatives fixen,
   nicht Budget erhöhen.
4. **Skalierung:** zweites Produkt (Notion-Version 39 € / FeWo-Cockpit 49 €) erst ab
   konstant > 10 Verkäufen/Monat organisch. Budget erst hoch bei ROAS > 1,5.
5. **Steuer:** bei Annäherung an 25.000 €/Jahr (bzw. spätestens vor 100.000 €)
   Steuerberater einschalten. **Gewerbeanmeldung** nicht vergessen — unabhängig von der
   Umsatzsteuerfrage nötig.

---

## Täglicher Ablauf (≤ 60 Min)

1. **Telegram** checken (Was ist reingekommen? Ist die Website online?).
2. **Gmail-Entwürfe** prüfen/anpassen/**selbst senden** (der KI-Mitarbeiter sendet nie).
3. **1× pro Woche** Kampagnen-Zahlen kontrollieren.

---

## Wichtige Hinweise (unbedingt lesen)

- ⚖️ **Rechtstexte sind Platzhalter.** Impressum, Datenschutz, Widerruf und AGB müssen
  final von einem Anwalt/Impressum-Service (z. B. eRecht24) geprüft werden. Besonders die
  **Widerrufsbelehrung für digitale Produkte** (§ 356 Abs. 5 BGB) ist fehleranfällig —
  bei falscher Umsetzung droht ein 14-tägiges Rückgaberecht trotz Download.
- 🕵️ **Vollständige Anonymität ist rechtlich unmöglich.** Ein Impressum-Service schützt
  die Privatadresse, aber Behörden/Abmahner können den Betreiber erreichen. Ein reines
  Postfach oder Scan-Service reicht **nicht** — es braucht eine echte c/o-Adresse mit
  Zustellungsbevollmächtigung.
- 🧾 **Keine Steuerberatung.** Das Cockpit ist eine Organisations- und Rechenhilfe; alle
  Angaben ohne Gewähr (Stand Juli 2026). Gebührensätze & Steuergrenzen können sich ändern.
- 🤖 **KI-Entwürfe können falsch sein.** Jeden Entwurf vor dem Senden lesen. Bei sensiblen
  Themen (Rechnungen, Rechtliches, Beschwerden, Rückerstattungen) nie ungeprüft senden.
- 💶 **Einnahmen sind unsicher.** Alle Zahlen sind Bandbreiten aus Sekundärquellen.
- 📈 **API-/Ad-Preise ändern sich.** Vor dem Start aktuelle Preise prüfen.

---

## Nächste manuelle Schritte für Jonas

1. `[DEINE-DOMAIN]`, `[E-MAIL]`, `[STORE]`/`[PRODUKT-ID]` und die Adress-Platzhalter in
   allen Dateien durch echte Werte ersetzen (Suche nach `[` hilft). Die Marke `ZahlenKlar`
   ist bereits überall gesetzt.
2. Die **xlsx bei Lemon Squeezy hochladen** und **4 Screenshots** aus der Datei in die
   Landingpage einbauen.
3. Rechtstexte prüfen lassen (eRecht24/Anwalt) und Impressum-Adresse eintragen.
4. Checkliste oben Schritt für Schritt abarbeiten.
