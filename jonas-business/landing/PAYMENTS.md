# Zahlungen: Lemon Squeezy (Merchant of Record) — Einrichtung & Begründung

Diese Datei erklärt, **wie** die Zahlung technisch eingebunden wird und **warum**
Lemon Squeezy für dieses anonyme, wartungsarme Setup die richtige Wahl ist.

---

## Kurz-Empfehlung

**Nutze Lemon Squeezy** (Merchant of Record), **nicht** eigenes Stripe.
Grund: Anonymität + minimaler Verwaltungsaufwand — Lemon Squeezy übernimmt die
komplette EU-Umsatzsteuer und tritt gegenüber dem Käufer als Verkäufer auf.

---

## Technische Einbindung (Overlay-Checkout)

1. In `index.html` das Lemon-Squeezy-Script im `<head>` aktivieren (Platzhalter ist vorbereitet):
   ```html
   <script src="https://assets.lemonsqueezy.com/lemon.js" defer></script>
   ```
2. Der Kaufen-Button trägt bereits `data-lsqueezy="1"` und eine Checkout-URL im Muster:
   ```html
   <a href="https://[STORE].lemonsqueezy.com/checkout/buy/[PRODUKT-ID]?embed=1"
      data-lsqueezy="1">Jetzt kaufen</a>
   ```
   → `[STORE]` und `[PRODUKT-ID]` durch die echten Werte aus dem Lemon-Squeezy-Dashboard ersetzen.
   Mit `?embed=1` öffnet der Checkout als Overlay statt als neue Seite.
3. Optional: **Sofort-Ausführung + Widerrufsverzicht** im Produkt/Checkout aktivieren
   (nötig für digitale Produkte, siehe `../legal/widerruf.html`).

Die eigentliche Auslieferung (Download-Link) ist in `../product/lieferung/README.md` beschrieben.

---

## Warum Merchant of Record (MoR)?

Ein Merchant of Record **kauft dein Produkt rechtlich und verkauft es im eigenen
Namen weiter**. Daraus folgt:

- **EU-Umsatzsteuer (VAT/OSS):** Lemon Squeezy berechnet, erhebt und führt die
  EU-VAT über das OSS-Verfahren selbst ab. **Du musst dich NICHT in EU-Ländern
  umsatzsteuerlich registrieren.**
- **Anonymität gegenüber dem Käufer:** Auf Rechnung/Beleg erscheint Lemon Squeezy
  als Verkäufer, nicht deine Privatperson. (Die Impressumspflicht auf deiner
  Website bleibt davon unberührt — siehe `../legal/impressum.html`.)
- **Weniger Admin:** keine eigene VAT-Meldung, keine Rechnungsstellung an EU-Kunden.

### Gebühren (Stand 2026)
- Lemon Squeezy: **5 % + 0,50 $** pro Transaktion (all-inclusive).
- **+1,5 %** für internationale (Nicht-US-)Transaktionen laut Lemon-Squeezy-Doku.
- Für DACH-Kunden also effektiv **~6,5 % + 0,50 $**.

Beispiel bei 29 € Verkaufspreis: grob ~2,3 € Gebühr → ~26–27 € netto.

---

## Gegenüberstellung: Lemon Squeezy vs. eigenes Stripe

| Aspekt | Lemon Squeezy (MoR) | Eigenes Stripe |
|---|---|---|
| EU-VAT / OSS | Lemon Squeezy erhebt & führt ab | **Du** musst OSS registrieren, erheben, melden, abführen |
| Anonymität ggü. Käufer | Ja (LS ist Verkäufer) | Nein (du bist Verkäufer auf dem Beleg) |
| Rechnungsstellung EU | Automatisch | Selbst / eigenes Tool |
| Gebühr | ~6,5 % + 0,50 $ (DACH) | ~1,5 % + 0,25 € (EU-Karten) + eigener Admin-Aufwand |
| Verwaltungsaufwand | Minimal | Hoch (Steuer-Compliance liegt bei dir) |

**Fazit:** Die etwas höhere Gebühr bei Lemon Squeezy ist der Preis dafür, dass die
komplette Umsatzsteuer-Bürokratie und ein Stück Anonymität ausgelagert werden — für
ein Ein-Personen-Business mit ~60 Min/Tag genau der richtige Trade-off.

---

## Hinweis
> Gebühren und Funktionsumfang können sich ändern. Vor dem Start die aktuelle
> Lemon-Squeezy-Preis- und Steuer-Doku prüfen. Dies ist keine Steuerberatung.
