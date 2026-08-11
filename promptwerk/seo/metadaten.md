# SEO-Grundlagen — Meta-Daten, Handles, Alt-Texte, interne Verlinkung

Zielmarkt: Deutschland (primär), Österreich und Schweiz (sekundär). Sprache Deutsch.
Suchintention der Zielgruppe ist überwiegend **problemorientiert** („chatgpt prompts
für kundenservice deutsch"), nicht markenorientiert — deshalb steht in jedem Titel die
Aufgabe vor der Marke.

---

## 1. Seiten — Meta-Titel und Meta-Beschreibungen

| Seite | Handle | Meta-Titel (≤ 60 Z.) | Meta-Beschreibung (≤ 155 Z.) |
|---|---|---|---|
| Startseite | `/` | PromptWerk – Getestete KI-Prompts für Selbstständige | Fertige ChatGPT- und Claude-Prompts für Marketing, Kundenservice und Verwaltung. Plus Business-Vorlagen für Kleinunternehmer. Sofort-Download, kein Abo. |
| Kollektion | `prompt-bibliotheken-vorlagen` | Prompt-Bibliotheken & Business-Vorlagen | Vier Pakete mit getesteten KI-Prompts und Vorlagen für Selbstständige, Coaches und kleine Teams. PDF plus editierbare Vorlage, sofort verfügbar. |
| Über uns | `ueber-promptwerk` | Über PromptWerk – Prompt-Systeme statt Coaching | Wie unsere Prompts entstehen, was wir bewusst nicht anbieten und warum es keine Abos gibt. Arbeitsmittel für kleine Unternehmen im deutschsprachigen Raum. |
| FAQ | `faq` | Häufige Fragen zu Kauf, Download und Nutzung | Antworten zu Download, Zahlung, Nutzungsrechten, ChatGPT- und Claude-Kompatibilität sowie zum Widerrufsrecht bei digitalen Inhalten. |
| Kontakt | `kontakt` | Kontakt zu PromptWerk | Fragen zu einem Paket oder Problem mit einem Download? Schreib uns über das Formular. Antwort in der Regel innerhalb eines Werktags. |
| Impressum | `impressum` | Impressum | Anbieterangaben nach § 5 DDG. |
| Datenschutz | `datenschutzerklaerung` | Datenschutzerklärung | Informationen zur Verarbeitung personenbezogener Daten nach DSGVO. |
| AGB | `agb` | Allgemeine Geschäftsbedingungen | Vertragsbedingungen für den Kauf digitaler Inhalte bei PromptWerk. |
| Widerrufsbelehrung | `widerrufsbelehrung` | Widerrufsbelehrung | Widerrufsrecht und dessen Erlöschen bei digitalen Inhalten nach § 356 Abs. 5 BGB. |

**Zur Indexierung:** Impressum, Datenschutz, AGB und Widerrufsbelehrung sollten in der
Suche nicht ranken, aber erreichbar bleiben. Sie brauchen kein `noindex` — Shopify
handhabt das über die Standard-Robots-Datei. Eine kurze Meta-Beschreibung genügt.

---

## 2. Produkte — Meta-Daten

Vollständig in `promptwerk/products/katalog.md` und maschinenlesbar in
`shopify-productset.json` (Feld `seo`). Kurzfassung:

| Produkt | Handle | Meta-Titel |
|---|---|---|
| Marketing & Content | `ki-prompt-bibliothek-marketing-content` | KI-Prompt-Bibliothek Marketing & Content – 48 Prompts \| PromptWerk |
| Kundenservice & Verwaltung | `ki-prompt-bibliothek-kundenservice-verwaltung` | KI-Prompts für Kundenservice & Verwaltung – 44 Stück \| PromptWerk |
| Business-Vorlagen | `business-vorlagen-paket-kleinunternehmer` | Business-Vorlagen für Kleinunternehmer – 4 Vorlagen \| PromptWerk |
| Komplettpaket | `promptwerk-komplettpaket` | PromptWerk Komplettpaket – 92 Prompts + 4 Vorlagen für 49 € \| PromptWerk |

**Handle-Logik:** sprechend, mit dem Suchbegriff vorn, ohne Füllwörter, ohne Jahreszahl
(damit sie nicht veralten). Der Handle des Vorlagen-Pakets enthält bewusst
`kleinunternehmer` — das ist der Begriff, nach dem die Zielgruppe sucht.

> ⚠️ Handles nach dem Anlegen **nicht mehr ändern**. Jede Änderung bricht bestehende
> Links; Shopify legt zwar eine Weiterleitung an, aber Rankings gehen dabei verloren.

---

## 3. Alt-Texte je Bild-Slot

Alt-Texte beschreiben, was zu sehen ist — sie sind keine Keyword-Ablage. Struktur je
Produkt (Slot-Definition in `promptwerk/products/katalog.md`):

**Marketing & Content**
1. `Cover der KI-Prompt-Bibliothek Marketing und Content von PromptWerk`
2. `PDF-Innenseite mit Prompts für Social-Media-Redaktionsplanung`
3. `Notion-Vorlage mit den Prompts nach Anwendungsfall sortiert`
4. `Übersicht der 48 Prompts nach Themenbereichen`

**Kundenservice & Verwaltung**
1. `Cover der KI-Prompt-Bibliothek Kundenservice und Verwaltung von PromptWerk`
2. `PDF-Innenseite mit einem Prompt für die Antwort auf eine Beschwerde`
3. `Notion-Vorlage mit Prompts für Kundenanfragen und Termine`
4. `Übersicht der 44 Prompts nach Themenbereichen`

**Business-Vorlagen-Paket**
1. `Cover des Business-Vorlagen-Pakets für Kleinunternehmer von PromptWerk`
2. `Preiskalkulator in Google Sheets mit Beispielwerten zum Stundensatz`
3. `Rechnungsvorlage mit Hinweis auf die Kleinunternehmerregelung nach Paragraf 19 UStG`
4. `Übersicht der vier enthaltenen Vorlagen`

**Komplettpaket**
1. `Cover des PromptWerk Komplettpakets`
2. `Die drei enthaltenen Pakete nebeneinander dargestellt`
3. `Innenseite der Bonus-Kurzanleitung mit der Drei-Block-Regel`
4. `Übersicht aller Inhalte des Komplettpakets`

**Regeln:** kein „Bild von“ am Anfang, keine Sonderzeichen wie `§` oder `&` (Screenreader
lesen sie uneinheitlich vor — deshalb oben „Paragraf“ und „und“ ausgeschrieben),
maximal etwa 125 Zeichen.

---

## 4. Interne Verlinkung

Ziel: Link-Kraft auf das Komplettpaket bündeln und Wechsel zwischen den Einzelprodukten
ermöglichen, ohne dass jede Seite auf jede verlinkt.

```
Startseite
   ├──► Kollektion  ─────────────► alle 4 Produkte
   ├──► Prompt-Beispiel-Sektion ─► Marketing & Content
   └──► FAQ-Teaser ──────────────► FAQ

Marketing & Content ──► Kundenservice & Verwaltung   (Ergänzung)
                    └─► Komplettpaket                (Aufpreis-Pfad)

Kundenservice & Verw. ──► Marketing & Content
                      ├─► Business-Vorlagen
                      └─► Komplettpaket

Business-Vorlagen ──► Kundenservice & Verwaltung
                  └─► Komplettpaket

Komplettpaket ──► alle drei Einzelprodukte           (Beweis des Preisvorteils)

FAQ ──► Komplettpaket, Kontakt, Widerrufsbelehrung
Über uns ──► Kontakt, Impressum
```

Jeder Produkttext enthält diese Links bereits im letzten Absatz — umgesetzt in den
HTML-Dateien in `promptwerk/products/`.

**Ankertexte:** immer der Produktname, nie „hier klicken“ oder „mehr erfahren“.

---

## 5. Weitere SEO-Punkte

- **Strukturierte Daten:** Horizon liefert `Product`-Schema automatisch mit Preis und
  Verfügbarkeit. Nichts zu tun, aber nach Go-Live mit dem Rich-Results-Test prüfen.
- **Sitemap:** Shopify erzeugt `/sitemap.xml` automatisch — erst nach dem Entfernen des
  Passwortschutzes erreichbar.
- **Google Search Console:** nach Go-Live einrichten und die Sitemap einreichen.
  Vorher sinnlos, da der Shop nicht erreichbar ist.
- **Sprachauszeichnung:** Der Shop läuft einsprachig auf Deutsch. Für AT und CH sind
  **keine** eigenen Sprachversionen nötig — kein `hreflang` erforderlich, solange kein
  eigener Markt mit eigener Domain angelegt wird.
- **Titel-Suffix:** In Horizon unter *Theme-Einstellungen → SEO* den Shop-Namen als
  Suffix konfigurieren, damit „| PromptWerk“ nicht doppelt erscheint.
