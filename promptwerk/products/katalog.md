# PromptWerk — Produktkatalog (Anlage-Spezifikation)

Alle Werte, die beim Anlegen in Shopify gesetzt werden. Die Verkaufstexte liegen als
fertiges HTML in den Dateien `01-…` bis `04-…` in diesem Ordner und werden 1:1 in das
Feld *Beschreibung* übernommen.

Maschinenlesbare Fassung zum direkten Einspielen: `shopify-productset.json`

---

## Übersicht

| # | Titel | Handle | Preis | Vergleichspreis |
|---|---|---|---|---|
| 1 | KI-Prompt-Bibliothek: Marketing & Content | `ki-prompt-bibliothek-marketing-content` | 19,00 € | — |
| 2 | KI-Prompt-Bibliothek: Kundenservice & Verwaltung | `ki-prompt-bibliothek-kundenservice-verwaltung` | 19,00 € | — |
| 3 | Business-Vorlagen-Paket für Kleinunternehmer | `business-vorlagen-paket-kleinunternehmer` | 29,00 € | — |
| 4 | PromptWerk Komplettpaket | `promptwerk-komplettpaket` | 49,00 € | 67,00 € |

**Titel-Logik:** Kein generisches „500 Prompts“. Jeder Titel nennt den Anwendungsbereich,
der Nischenbezug („für Selbstständige, Coaches und kleine Teams“) steht in Beschreibung
und Meta-Description statt im Titel — das hält den Titel kurz genug für die Google-SERP.

---

## Für alle vier Produkte identisch

| Feld | Wert | Begründung |
|---|---|---|
| Status | **DRAFT** | Auftrag: Store nicht veröffentlichen |
| Vendor | `PromptWerk` | |
| Produkttyp | `Digitales Produkt` | |
| Kollektion | `Prompt-Bibliotheken & Vorlagen` (`gid://shopify/Collection/710415090009`) | bereits angelegt |
| Variante | eine Standardvariante (`Title` / `Default Title`) | keine Auswahl nötig |
| **Versand erforderlich** | **nein** (`inventoryItem.requiresShipping: false`) | rein digitales Produkt → kein Versandschritt im Checkout |
| Bestand verfolgen | **nein** (`inventoryItem.tracked: false`) | unbegrenzt verkaufbar |
| Steuerpflichtig | **nein** (`taxable: false`) | Kleinunternehmer § 19 UStG — es wird keine USt. ausgewiesen. Details unten. |
| Gewicht | nicht gesetzt | |

### Warum `taxable: false`

Der Shop läuft auf „Preise inklusive Steuer“. Als Kleinunternehmer nach § 19 UStG weist
Jonas **keine** Umsatzsteuer aus. Mit `taxable: false` erscheint im Checkout und auf der
Rechnung keine Steuerzeile — der gezeigte Preis ist der gezahlte Preis.

> **Manuell zu prüfen:** zusätzlich unter *Einstellungen → Steuern und Zölle → Deutschland*
> sicherstellen, dass kein Standardsatz greift. Der Hinweistext „Gemäß § 19 UStG wird keine
> Umsatzsteuer berechnet“ gehört zusätzlich in AGB und Bestellbestätigung
> (siehe `promptwerk/email/auftragsbestaetigung.liquid`).

---

## Produkt 1 — Marketing & Content

- **Titel:** KI-Prompt-Bibliothek: Marketing & Content
- **Handle:** `ki-prompt-bibliothek-marketing-content`
- **Preis:** 19,00 € · **SKU:** `PW-PROMPT-MKT`
- **Beschreibung:** `01-marketing-content.html`
- **Umfangs-Zeile** (Metafeld `custom.umfang_zeile`): `48 Prompts · PDF + Notion-Vorlage · Sofort-Download`
- **Tags:** `Prompts`, `Marketing`, `Content`, `Digital`, `ChatGPT`, `Claude`
- **SEO-Titel:** KI-Prompt-Bibliothek Marketing & Content – 48 Prompts | PromptWerk
- **SEO-Beschreibung:** 48 getestete Prompts für Social Media, Newsletter, Produkttexte und Werbung. Für Selbstständige und kleine Teams. PDF + Notion-Vorlage, Sofort-Download.

## Produkt 2 — Kundenservice & Verwaltung

- **Titel:** KI-Prompt-Bibliothek: Kundenservice & Verwaltung
- **Handle:** `ki-prompt-bibliothek-kundenservice-verwaltung`
- **Preis:** 19,00 € · **SKU:** `PW-PROMPT-SERVICE`
- **Beschreibung:** `02-kundenservice-verwaltung.html`
- **Umfangs-Zeile:** `44 Prompts · PDF + Notion-Vorlage · Sofort-Download`
- **Tags:** `Prompts`, `Kundenservice`, `Verwaltung`, `Digital`, `ChatGPT`, `Claude`
- **SEO-Titel:** KI-Prompts für Kundenservice & Verwaltung – 44 Stück | PromptWerk
- **SEO-Beschreibung:** 44 getestete Prompts für Kundenanfragen, Angebote, Beschwerden, FAQ und Termine. Für Selbstständige und kleine Teams. PDF + Notion, Sofort-Download.

## Produkt 3 — Business-Vorlagen-Paket

- **Titel:** Business-Vorlagen-Paket für Kleinunternehmer
- **Handle:** `business-vorlagen-paket-kleinunternehmer`
- **Preis:** 29,00 € · **SKU:** `PW-VORLAGEN`
- **Beschreibung:** `03-business-vorlagen.html`
- **Umfangs-Zeile:** `4 Vorlagen · Google Sheets + Notion · Sofort-Download`
- **Tags:** `Vorlagen`, `Kalkulation`, `Rechnung`, `Digital`, `Kleinunternehmer`
- **SEO-Titel:** Business-Vorlagen für Kleinunternehmer – 4 Vorlagen | PromptWerk
- **SEO-Beschreibung:** Preiskalkulator, Rechnungsvorlage mit § 19 UStG-Hinweis, Content-Kalender und Kundenübersicht. Google Sheets + Notion, Formeln hinterlegt, Sofort-Download.

## Produkt 4 — Komplettpaket

- **Titel:** PromptWerk Komplettpaket
- **Handle:** `promptwerk-komplettpaket`
- **Preis:** 49,00 € · **Vergleichspreis:** 67,00 € · **SKU:** `PW-KOMPLETT`
- **Beschreibung:** `04-komplettpaket.html`
- **Umfangs-Zeile:** `92 Prompts + 4 Vorlagen + Bonus-PDF · Sofort-Download`
- **Tags:** `Bundle`, `Prompts`, `Vorlagen`, `Digital`, `Sparpaket`
- **SEO-Titel:** PromptWerk Komplettpaket – 92 Prompts + 4 Vorlagen für 49 € | PromptWerk
- **SEO-Beschreibung:** Beide Prompt-Bibliotheken, das Vorlagen-Paket und die Bonus-Kurzanleitung. 49 € statt 67 € im Einzelkauf. Sofort-Download, kein Abo.

> Der **Vergleichspreis 67,00 €** erzeugt in Horizon automatisch die durchgestrichene
> Preisangabe und das Spar-Kennzeichen. Wichtig: 67 € ist die tatsächliche Summe der drei
> Einzelpreise (19 + 19 + 29) — kein erfundener Streichpreis. Das ist auch die
> wettbewerbsrechtlich saubere Variante.

---

## Bild-Slots (Platzhalter-Struktur)

Die echten Produktdateien existieren noch nicht, deshalb wird nur die **Struktur**
festgelegt. Pro Produkt vier Slots, immer in dieser Reihenfolge:

| Slot | Inhalt | Seitenverhältnis | Alt-Text-Muster |
|---|---|---|---|
| 1 | Cover-Grafik (typografisch, dunkler Grund, Akzentlinie) | 1:1, 1600 × 1600 | `Cover der {PRODUKTNAME} von PromptWerk` |
| 2 | Screenshot einer echten PDF-Innenseite | 4:5, 1600 × 2000 | `Innenseite des PDFs mit {THEMA}-Prompts` |
| 3 | Ausschnitt der Notion- bzw. Sheets-Vorlage | 4:5, 1600 × 2000 | `Ausschnitt der {FORMAT}-Vorlage mit {INHALT}` |
| 4 | Übersicht „Was ist enthalten“ | 1:1, 1600 × 1600 | `Übersicht der Inhalte von {PRODUKTNAME}` |

Slot 1 ist das Beitragsbild (Kollektions- und Suchansicht). Konkrete Alt-Texte je Produkt:
`promptwerk/seo/metadaten.md`.

**Solange keine echten Bilder existieren:** Produkte ohne Bild anlegen. Horizon zeigt
dann einen neutralen Platzhalter — besser als ein sichtbar generisches Stockbild.
