# Auslieferung: Automatischer Download via Lemon Squeezy

Dieses Verzeichnis dokumentiert, **wie das Produkt nach dem Kauf beim Kunden landet** —
vollautomatisch, ohne dass Jonas etwas tun muss.

---

## Prinzip

Lemon Squeezy ist **Merchant of Record** und übernimmt Checkout, Zahlung,
EU-Umsatzsteuer und Auslieferung. Nach erfolgreicher Zahlung stellt Lemon Squeezy
dem Käufer automatisch einen **sicheren, zeitlich begrenzten Download-Link** bereit
(per Bestätigungsseite und E-Mail). Kein manueller Versand, keine Lager-/Fulfillment-Kosten.

## Einrichtung (einmalig, ~30 Min, vom Handy machbar)

1. Lemon-Squeezy-Konto anlegen und Store erstellen.
2. **Produkt** anlegen:
   - Typ: *Digital product / Single payment*.
   - Preis: **29 €** (bzw. Bundle-Preis 39 € inkl. Guide).
   - Name/Beschreibung aus `../produkt-spezifikation.md` übernehmen.
3. **Auslieferungsdatei(en)** hochladen — je nach Variante:
   - **Notion:** statt Datei einen `.txt`/`.pdf` mit dem **Notion-Duplicate-Link**
     hochladen (Käufer dupliziert das Template in den eigenen Workspace).
   - **Excel/Sheets:** die `.xlsx`-Datei direkt hochladen.
   - **Bundle:** zusätzlich die Guide-`.pdf` hinzufügen.
4. **Auszahlungskonto** verbinden (Bank/IBAN).
5. Den **Buy-Button** auf der Landingpage mit der Lemon-Squeezy-Checkout-URL bzw.
   dem `data-lsqueezy`-Overlay verbinden (siehe `../../landing/index.html` und
   `../../landing/PAYMENTS.md`).

## Was der Käufer erlebt

1. Klick auf „Jetzt kaufen" → Lemon-Squeezy-Checkout (Overlay oder eigene Seite).
2. Zahlung (Karte, PayPal etc.), Lemon Squeezy weist ggf. EU-VAT korrekt aus.
3. Bestätigungsseite + E-Mail mit **Download-Link** (bzw. Notion-Duplicate-Link).
4. Fertig — sofortige Auslieferung, rund um die Uhr, ohne Zutun.

## Wichtig für die Rechtstexte

Weil digitale Inhalte **sofort** bereitstehen, muss der Käufer im Checkout der
sofortigen Ausführung **ausdrücklich zustimmen** und den **Verlust des
Widerrufsrechts** bestätigen (§ 356 Abs. 5 BGB). Details in
`../../legal/widerruf.html`. Lemon Squeezy bietet dafür Checkout-Optionen —
diese aktivieren.

## Hinweis
> Konkrete Menüpfade in Lemon Squeezy können sich ändern. Im Zweifel die
> offizielle Lemon-Squeezy-Doku prüfen. Dies ist eine Einrichtungs-Skizze, keine Garantie.
