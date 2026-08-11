# PromptWerk — Store-Inhalte

Alle Inhalte und Konfigurationen für den PromptWerk-Shopify-Store.

**Zuerst lesen:** [`../AUDIT.md`](../AUDIT.md) (Ist-Zustand) und
[`../BUILD-LOG.md`](../BUILD-LOG.md) (Stand der Arbeit, offene Schritte).

> ⚠️ Der verbundene Shopify-Store ist `RESTORA` — eine andere Marke mit physischen
> Produkten. An RESTORA wurde nichts verändert. Ob PromptWerk diesen Store übernimmt oder
> einen eigenen bekommt, ist eine offene Entscheidung (BUILD-LOG, „Offene manuelle
> Schritte", Punkt 1).

## Ordnerstruktur

```
promptwerk/
├── einrichtung.md          Märkte, Steuern, Navigation, Digital Downloads, Theme-Setup
├── brand/
│   └── design-tokens.md    Farben, Typografie, Markenelemente, Kontrastprüfung
├── products/
│   ├── 01-…04-*.html       Verkaufstexte, direkt als Produktbeschreibung nutzbar
│   ├── katalog.md          Preise, Handles, SEO, Tags, Bild-Slots
│   ├── build-payload.py    erzeugt die Shopify-Payloads aus den HTML-Texten
│   └── shopify-productset.json   einspielbare productSet-Eingaben
├── pages/
│   ├── startseite.md       Sektionsaufbau mit finalem Text
│   ├── ueber-uns.html
│   ├── faq.html
│   └── kontakt.html
├── legal/                  vier Platzhalter-Gerüste (Impressum, Datenschutz, AGB,
│                           Widerrufsbelehrung) — NICHT ohne Prüfung veröffentlichen
├── checkout/
│   └── widerrufsverzicht.md  § 356 Abs. 5 BGB: Lösungsweg, Plan-Grenzen, Prüfliste
├── email/
│   └── auftragsbestaetigung.liquid  Baustein für die Bestellbestätigung (§ 312f BGB)
├── seo/
│   └── metadaten.md        Meta-Daten, Alt-Texte, interne Verlinkung
└── theme/
    ├── promptwerk.css      → assets/promptwerk.css
    └── snippets/
        ├── pw-umfang.liquid            Umfangs-Zeile (Markenelement)
        ├── pw-prompt.liquid            Prompt-Block mit Kopieren-Funktion
        └── pw-widerrufsverzicht.liquid Pflicht-Checkbox im Warenkorb
```

## Produkttexte ändern

Text nur in den `.html`-Dateien unter `products/` pflegen, danach:

```bash
python3 promptwerk/products/build-payload.py
```

Damit bleiben Verkaufstext und Shopify-Payload synchron.

## Drei Dinge, die leicht übersehen werden

1. **Dynamische Kaufen-Buttons abschalten.** Sonst umgeht Kundschaft den Warenkorb und
   damit die Widerrufsverzicht-Checkbox — der Widerrufsausschluss greift dann nicht.
2. **Mengenangaben müssen stimmen.** Die Texte nennen 48 und 44 Prompts sowie vier
   Vorlagen. Weichen die echten Dateien davon ab, sind die Beschreibungen irreführend.
3. **Rechtstexte sind Platzhalter.** Jede Datei unter `legal/` ist als solche markiert.
   Nicht ungeprüft live schalten.
