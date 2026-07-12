# Produktspezifikation: „ZahlenKlar Etsy-Steuer-Cockpit 2026"

**Format:** Excel-Vorlage (`.xlsx`) — läuft auch in LibreOffice Calc & Google Sheets
**Zielgruppe:** Deutsche Etsy-Verkäufer:innen als Kleinunternehmer nach § 19 UStG
**Preis:** 29 € (einmalig)
**Status:** **v1 fertig gebaut** — Datei liegt in `cockpit/ZahlenKlar_Etsy-Steuer-Cockpit_2026.xlsx`
**Auslieferung:** Automatischer Download via Lemon Squeezy (siehe `lieferung/README.md`)

---

## Problem, das gelöst wird

Seit 2023 meldet Etsy die Umsätze seiner Verkäufer:innen über **DAC7** automatisch an
die Finanzbehörden. Wer auf Etsy verkauft, muss seine Zahlen also sauber haben. Typische
Schmerzpunkte deutscher Etsy-Kleinunternehmer:innen:

- **Etsy-Gebühren fressen die Marge** (bis ~25 % des Verkaufspreises inkl. Versand) —
  ohne Rechnung weiß niemand, was pro Produkt übrig bleibt.
- **Die Reverse-Charge-Falle** (§ 13b UStG): Mit hinterlegter USt-IdNr. schuldet man die
  19 % USt auf die Etsy-Gebühren selbst — überraschend auch für Kleinunternehmer.
- **Umsatzgrenzen** der Kleinunternehmerregelung (25.000 € / 100.000 €) — inkl.
  Versandkosten, die viele nicht mitzählen.
- **EÜR & Rechnungen** rechtssicher ohne Umsatzsteuer erstellen (§ 19-Hinweis).

---

## Die 6 Blätter der v1 (wie ausgeliefert)

### 1. Start
Übersicht „Was ist drin?", Farb-Legende (gelbe Zellen = eintragen, blaue Schrift =
anpassbare Sätze, schwarze Schrift = Formeln nicht überschreiben) und ein
Schnellstart in 3 Schritten. Enthält den Hinweis „Organisations- und Rechenhilfe,
keine Steuerberatung, Stand Juli 2026".

### 2. EÜR — Einnahmen-Überschuss-Rechnung
Zeilenweise Erfassung nach Zufluss-/Abfluss-Prinzip: Datum, Beleg-Nr., Beschreibung,
Typ, Kategorie, Betrag, Monat. Automatische **Einnahmen-/Ausgaben-Summen**, **Gewinn/Verlust**
und eine **Monatsübersicht** (Jan–Dez). Beispielzeilen zum Überschreiben.

### 3. Etsy-Gebühren (Reverse Charge)
Monatliche **Netto-Gebühren** aus der Etsy-Abrechnung eintragen; die ggf. per Reverse
Charge geschuldete **USt (19 %)** wird automatisch berechnet. Erklärt beide Fälle direkt
im Blatt:
- **Fall A — keine USt-IdNr. hinterlegt:** Etsy stellt Gebühren inkl. 19 % USt in Rechnung
  und führt sie selbst ab → einfach als Brutto-Ausgabe in die EÜR, dieses Blatt nicht nötig.
- **Fall B — USt-IdNr. hinterlegt (Reverse Charge):** Etsy rechnet netto ab, die 19 % USt
  schuldest **du** dem Finanzamt (auch als Kleinunternehmer, ohne Vorsteuerabzug) →
  Meldung über die Umsatzsteuererklärung/-voranmeldung.

### 4. Umsatz-Ampel (§ 19 UStG)
**Grün/Gelb/Rot** je nach Nähe zu den Grenzen seit 1.1.2025 (Jahressteuergesetz 2024):
Vorjahresumsatz **25.000 €** und laufender Umsatz **100.000 €** (Fallbeileffekt). Der
laufende Umsatz kommt automatisch aus der EÜR. Ausdrücklicher Hinweis: **Versandkosten
zählen zum Umsatz dazu.**

### 5. Margenrechner
Was bleibt pro Etsy-Verkauf übrig? Eingaben: Verkaufspreis, berechneter Versand,
Materialkosten, eigene Versandkosten, Offsite-Ad ja/nein. Berücksichtigt
**Transaktionsgebühr** (auf Preis + Versand), **Zahlungsgebühr** (% + fix),
**Einstellgebühr** (≈ 0,20 USD), **Offsite-Ads-Satz** und optional die **19 % USt auf
Gebühren** (bei USt-IdNr.). Ergebnis: Gewinn und Marge mit **Ampel** (grün ≥ 30 %,
gelb 15–30 %, rot < 15 %).

### 6. Rechnungsvorlage
USt-freie Rechnung mit vorformuliertem **§ 19-Pflichthinweis**.

---

## Roadmap (nicht Teil der v1)

| Produkt / Version | Beschreibung | Preis | Status |
|---|---|---|---|
| **Notion-Version** des Etsy-Cockpits | gleiche Logik als Notion-Workspace | 39 € (Upsell) | Roadmap v2 |
| **FeWo-/Airbnb-Cockpit** | Zweites Produkt für Kurzzeitvermieter:innen | 49 € | Roadmap (Produkt #2) |

Katalog-Effekt: Ein zweites/drittes Produkt verkauft sich neben dem ersten mit — aber
erst bauen, wenn die v1 konstant läuft (> 10 Verkäufe/Monat organisch).

---

## Hinweis
> Gebührensätze und Steuergrenzen (Stand Juli 2026) können sich ändern. Im Zweifel im
> Etsy-Konto (Shop-Manager → Finanzen) bzw. mit dem Steuerbüro abgleichen. Keine
> Steuer- oder Rechtsberatung.
