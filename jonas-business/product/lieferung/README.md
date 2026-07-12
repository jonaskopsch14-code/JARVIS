# Auslieferung: Automatischer Download via Lemon Squeezy

Dieses Verzeichnis dokumentiert, **wie das Produkt nach dem Kauf beim Kunden landet** —
vollautomatisch, ohne dass du etwas tun musst.

**Produkt:** `ZahlenKlar Etsy-Steuer-Cockpit` (Excel-Datei, v1)
**Datei:** `../cockpit/ZahlenKlar_Etsy-Steuer-Cockpit_2026.xlsx`

---

## Prinzip

Lemon Squeezy ist **Merchant of Record** und übernimmt Checkout, Zahlung, EU-Umsatzsteuer
und Auslieferung. Nach erfolgreicher Zahlung stellt Lemon Squeezy dem Käufer automatisch
einen **sicheren, zeitlich begrenzten Download-Link** bereit (Bestätigungsseite + E-Mail).
Kein manueller Versand, keine Lager-/Fulfillment-Kosten.

## Einrichtung (einmalig, ~30 Min, vom Handy machbar)

1. Lemon-Squeezy-Konto anlegen und Store erstellen.
2. **Produkt** anlegen:
   - Typ: *Digital product / Single payment*.
   - Preis: **29 €**.
   - Name/Beschreibung aus `../produkt-spezifikation.md` übernehmen.
3. **Auslieferungsdatei hochladen:** die Excel-Datei
   `cockpit/ZahlenKlar_Etsy-Steuer-Cockpit_2026.xlsx` als Download-Datei einstellen.
4. **Sofort-Ausführung + Widerrufsverzicht** im Checkout aktivieren (nötig für digitale
   Produkte, siehe `../../legal/widerruf.html`).
5. **Auszahlungskonto** verbinden (Bank/IBAN).
6. Den **Buy-Button** auf der Landingpage mit der Lemon-Squeezy-Checkout-URL bzw. dem
   `data-lsqueezy`-Overlay verbinden (siehe `../../landing/index.html` und
   `../../landing/PAYMENTS.md`).

<!-- TODO wird automatisch angezeigt, falls die xlsx (noch) fehlt — siehe Prüfung unten. -->

## Was der Käufer erlebt

1. Klick auf „Jetzt kaufen" → Lemon-Squeezy-Checkout (Overlay oder eigene Seite).
2. Zahlung (Karte, PayPal etc.), Lemon Squeezy weist ggf. EU-VAT korrekt aus.
3. Bestätigungsseite + E-Mail mit **Download-Link** zur `.xlsx`.
4. Fertig — sofortige Auslieferung, rund um die Uhr, ohne Zutun.

## Hinweis
> Konkrete Menüpfade in Lemon Squeezy können sich ändern. Im Zweifel die offizielle
> Lemon-Squeezy-Doku prüfen. Dies ist eine Einrichtungs-Skizze, keine Garantie.
