# Produktspezifikation: „Steuer- & Buchhaltungs-Cockpit für Kleinunternehmer"

**Format:** Notion-Template (Hauptversion) + Excel-/Google-Sheets-Variante (Alternative)
**Zielgruppe:** DACH-Solo-Selbstständige, Freelancer, Kleinunternehmer nach § 19 UStG
**Preis:** 29 € (Sweet-Spot für Impulskauf, siehe `../landing/PAYMENTS.md`)
**Auslieferung:** Automatischer Download-Link via Lemon Squeezy (siehe `lieferung/README.md`)

---

## Problem, das gelöst wird

Kleinunternehmer in Deutschland/Österreich/Schweiz kämpfen mit denselben
wiederkehrenden Aufgaben:

- Einnahmen und Ausgaben sauber für die **EÜR (Einnahmen-Überschuss-Rechnung)** erfassen.
- Belege nicht verlieren und dem richtigen Vorgang zuordnen.
- Den Überblick behalten, **wie nah man an den Umsatzgrenzen** der
  Kleinunternehmerregelung ist (25.000 € Vorjahr / 100.000 € laufendes Jahr, Stand seit 1.1.2025).
- Rechtssichere **Rechnungen ohne Umsatzsteuer** mit dem korrekten § 19-Hinweis schreiben.

Das Cockpit bündelt genau diese vier Dinge in einer bedienbaren Vorlage.

---

## Enthaltene Bausteine

### 1. EÜR-Tabelle
- Zwei Bereiche: **Betriebseinnahmen** und **Betriebsausgaben**.
- Spalten: Datum, Beleg-Nr., Kategorie, Betrag (brutto), Netto, Notiz, Beleg-Link.
- Ausgaben-Kategorien vorbereitet (Wareneinkauf, Software/Abos, Bürobedarf,
  Reisekosten, Telefon/Internet, Werbung, Gebühren, Sonstiges).
- Automatische Summen pro Monat und pro Jahr.
- **Ergebnis-Kachel:** Gewinn = Einnahmen − Ausgaben (die zentrale EÜR-Zahl fürs Finanzamt).

### 2. Belege-Tracker
- Jede Zeile = ein Beleg: Datum, Betrag, Händler, Kategorie, Status
  („erfasst" / „fehlt noch" / „digital abgelegt"), Link/Dateiname.
- Verknüpfung mit der EÜR-Zeile über die Beleg-Nr.
- Filter „fehlende Belege" für die monatliche Aufräum-Routine.

### 3. Kleinunternehmer-Umsatzgrenzen-Ampel (25k / 100k)
- Zeigt den **laufenden Jahresumsatz** automatisch als Fortschrittsbalken.
- Ampellogik:
  - 🟢 **Grün:** unter 25.000 € — Kleinunternehmerregelung sicher anwendbar.
  - 🟡 **Gelb:** 25.000 €–100.000 € — Vorjahresgrenze überschritten bzw. nah dran,
    Status für Folgejahr prüfen, Steuerberater ins Auge fassen.
  - 🔴 **Rot:** Annäherung an bzw. Überschreiten von 100.000 € — **Fallbeileffekt**:
    ab dem überschreitenden Umsatz entfällt die Steuerbefreiung sofort im laufenden Jahr.
- Kurzer Erklärtext direkt in der Vorlage (Rechtsstand 1.1.2025, Jahressteuergesetz 2024).

### 4. USt-freie Rechnungsvorlage mit § 19-Hinweis
- Vorlage für Rechnungen ohne ausgewiesene Umsatzsteuer.
- Pflichtfelder: Rechnungsnummer (fortlaufend), Rechnungsdatum, Leistungsdatum,
  Empfänger, Positionen, Gesamtbetrag.
- **Vorformulierter Pflichthinweis:**
  > „Gemäß § 19 UStG wird keine Umsatzsteuer berechnet (Kleinunternehmerregelung)."
- Platzhalter für eigene Absenderdaten (kompatibel mit der Impressum-/c-o-Adresse).

---

## Was NICHT enthalten ist (bewusst, zur Erwartungssteuerung)

- Keine automatische Übermittlung ans Finanzamt (ELSTER) — die Vorlage bereitet die
  Zahlen auf, ersetzt aber keine Steuerberatung.
- Keine Rechtsberatung — der § 19-Hinweis und die Grenzwerte sind auf dem Stand
  1.1.2025; Nutzer prüfen die Aktualität selbst bzw. mit Steuerberater.

## Varianten für die Auslieferung
- **Notion:** geteilter „Duplicate"-Link (Käufer dupliziert in den eigenen Workspace).
- **Excel / Google Sheets:** `.xlsx`-Datei mit denselben vier Bausteinen und Formeln.

## Hinweis (Platzhalter)
> Die steuerlichen Grenzwerte und Formulierungen sind auf dem Stand 1.1.2025
> (Jahressteuergesetz 2024). Vor Verkauf und regelmäßig danach aktuellen Stand prüfen.
> Diese Vorlage ist keine Steuer- oder Rechtsberatung.
