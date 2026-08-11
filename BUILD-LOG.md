# BUILD-LOG — PromptWerk

Laufendes Protokoll des Aufbaus. Neueste Einträge unten.
Ist-Zustand vor Beginn: `AUDIT.md` · Inhalte: `promptwerk/`

---

## Schritt 1 — Audit

**Erledigt.** Ergebnis in `AUDIT.md`.

Kernbefund: Der verbundene Store ist **nicht leer**. Es ist `RESTORA`
(`swszg1-tg.myshopify.com`), ein deutscher Shop für **physische** Massagegeräte mit drei
aktiven Produkten, eigenen Seiten, eigenen Rechtstexten und dem Theme „Horizon".
PromptWerk ist ein anderes Geschäftsmodell (digitale Downloads) und eine andere Marke.

**Daraus abgeleitete Arbeitsweise:** rein **additiv**. Nichts von RESTORA wurde gelöscht,
überschrieben oder deaktiviert. Kein Produkt, keine Seite, kein Menü und nicht das
Live-Theme wurden verändert.

Nebenbefunde (nicht angefasst, da RESTORA betreffend): unaufgelöster Platzhalter
`[HIER LIEFERZEIT EINTRAGEN]` in einer öffentlichen Produktbeschreibung, drei identische
leere Kollektionen „Muskel-Recovery", defekter Footer-Link `/pages/kontakt` → 404.

---

## Schritt 2 — Markenwelt und Design-Richtung

**Erledigt.** `promptwerk/brand/design-tokens.md`, umgesetzt in
`promptwerk/theme/promptwerk.css`.

- Farbwelt: Tiefblau-Anthrazit `#16202B`, warmes Off-White `#F7F4EF`, ein Akzent in
  Bernstein `#C97B1E`. Kontraste gegen WCAG AA geprüft und dokumentiert.
- Typografie: Inter für alles, plus System-Monospace-Stack für Prompt-Blöcke (kein
  zusätzlicher Webfont → keine Ladezeit-Kosten).
- Wiederkehrendes Markenelement: die **Umfangs-Zeile**
  (`48 Prompts · PDF + Notion-Vorlage · Sofort-Download`), technisch als Metafeld
  `custom.umfang_zeile` gelöst und über `snippets/pw-umfang.liquid` überall gleich
  gerendert.
- Bewusst vermieden: KI-Lila-Verlauf, Neon, Glow, Stockfotos mit Personen.

---

## Schritt 3 — Seitenstruktur

**Erledigt (Texte).** `promptwerk/pages/`

| Seite | Datei | Stand |
|---|---|---|
| Startseite | `startseite.md` | 6 Sektionen, finaler Text |
| Über uns | `ueber-uns.html` | final, sachlich, ohne Personenbezug |
| FAQ | `faq.html` | final, 13 Fragen inkl. der vier vorgegebenen |
| Kontakt | `kontakt.html` | final, Formular ohne Telefonnummer-Pflicht |

Navigation (Haupt- und Footer-Menü) spezifiziert in `promptwerk/einrichtung.md`.

---

## Schritt 4 — Produktkatalog

**Texte erledigt, Anlage im Shop offen.**

Vier vollständige Verkaufstexte in `promptwerk/products/` — je mit Nutzenversprechen in
der ersten Zeile, Umfangs-Zeile, 4–5 konkreten Bullet-Points, einem **vollständigen**
Prompt im Monospace-Block, Lieferhinweis und interner Verlinkung.

| # | Produkt | Preis | Handle |
|---|---|---|---|
| 1 | KI-Prompt-Bibliothek: Marketing & Content | 19 € | `ki-prompt-bibliothek-marketing-content` |
| 2 | KI-Prompt-Bibliothek: Kundenservice & Verwaltung | 19 € | `ki-prompt-bibliothek-kundenservice-verwaltung` |
| 3 | Business-Vorlagen-Paket für Kleinunternehmer | 29 € | `business-vorlagen-paket-kleinunternehmer` |
| 4 | PromptWerk Komplettpaket | 49 € (statt 67 €) | `promptwerk-komplettpaket` |

Der Vergleichspreis 67 € ist die **tatsächliche** Summe der Einzelpreise (19+19+29) —
kein erfundener Streichpreis.

Bild-Slots als Platzhalter-Struktur definiert (4 Slots je Produkt mit Format und
Alt-Text-Muster), da die echten Produktdateien noch nicht existieren.

### Status in Shopify

- ✅ Kollektion **„Prompt-Bibliotheken & Vorlagen"** angelegt
  (`gid://shopify/Collection/710415090009`), Sortierung manuell.
- ⛔ **Die vier Produkte wurden NICHT angelegt.** Die Schreibvorgänge wurden bei der
  Bestätigung mehrfach abgebrochen. Nach dem dritten Abbruch habe ich keine weiteren
  Versuche unternommen.

**Ersatzweg, damit nichts verloren ist:** Die fertigen Shopify-Payloads liegen in
`promptwerk/products/shopify-productset.json` — vier `productSet`-Eingaben mit Titel,
Handle, Beschreibung, Preis, Vergleichspreis, SKU, Tags, SEO-Feldern, Metafeld,
Kollektionszuordnung und Variante. Einspielbar mit:

```graphql
mutation ($input: ProductSetInput!) {
  productSet(input: $input, synchronous: true) {
    product { id title handle status }
    userErrors { field message }
  }
}
```

Die Datei wird aus den HTML-Texten erzeugt (`build-payload.py`) — nach Textänderungen
einfach neu laufen lassen, dann bleiben Text und Payload synchron.

---

## Schritt 5 — Digitale Auslieferung

**Vorbereitet.** Produktstruktur so gebaut, dass die App direkt greifen kann:
`requiresShipping: false`, Bestandsverfolgung aus, genau eine Standardvariante je Produkt.

> **Jonas muss „Digital Downloads" aus dem Shopify App Store installieren und die finalen
> Dateien hochladen.**

Details in `promptwerk/einrichtung.md`, Abschnitt 2.

---

## Schritt 6 — Markt- und Steuereinstellungen

**Spezifiziert, nicht gesetzt** (Markt-Schreibvorgänge gehören zu denselben blockierten
Admin-Änderungen). Sollzustand in `promptwerk/einrichtung.md`, Abschnitt 1:
Verkauf auf **DE, AT, CH** begrenzen, alle übrigen Länder deaktiviert.

Zwei Punkte, die dabei eine Entscheidung von Jonas brauchen:

- **Schweiz ist kein EU-Mitglied** — eigene MWST-Regeln für ausländische Anbieter
  elektronischer Dienstleistungen. Pragmatische Startvariante: zunächst nur **DE und AT**,
  CH später ergänzen.
- **EU-Schwelle 10.000 € netto** (grenzüberschreitender B2C, EU-weit kumuliert) und ihr
  Verhältnis zur Kleinunternehmerregelung ist eine steuerliche Frage → Steuerbüro.

Produkte sind bereits mit `taxable: false` vorbereitet, damit keine Umsatzsteuerzeile
erscheint (§ 19 UStG).

---

## Schritt 7 — Rechtstexte und Widerrufsverzicht

**Erledigt, als klar gekennzeichnete Platzhalter.** `promptwerk/legal/`

Vier vollständige Gerüste — Impressum, Datenschutzerklärung, AGB, Widerrufsbelehrung —
jeweils mit dem Hinweis:

> [PLATZHALTER — vor Veröffentlichung durch echten Rechtstext ersetzen, z. B. über einen
> Generator wie IT-Recht Kanzlei, Händlerbund oder eRecht24, oder anwaltlich prüfen lassen]

Die Gliederungen sind auf digitale Inhalte zugeschnitten (Nutzungsrechte, §§ 327 ff. BGB,
kein Versand, § 19 UStG) und enthalten an den kritischen Stellen zusätzliche Warnhinweise
— unter anderem zur nicht mehr existierenden OS-Plattform der EU und zur
Impressumspflicht, die sich mit vollständiger Anonymität **nicht** vereinbaren lässt.

### Technisch umgesetzt

**Widerrufsverzicht-Checkbox** — `promptwerk/theme/snippets/pw-widerrufsverzicht.liquid`,
Begründung in `promptwerk/checkout/widerrufsverzicht.md`.

Recherchiert statt geraten: Eine Checkbox **im Shopify-Checkout ist auf dem Basic-Plan
nicht möglich** — Checkout-UI-Extensions für die Checkout-Schritte sind laut
Shopify-Dev-Doku Plus-exklusiv, `checkout.liquid` ebenfalls. Umgesetzt wurde deshalb der
für deutsche Shops ohne Plus übliche Weg: Pflicht-Checkbox auf der **Warenkorbseite**, die
den Checkout-Button sperrt.

- **nicht vorangehakt** (zwingend nach § 356 Abs. 5 BGB)
- beide Erklärungen im Text: Zustimmung zum sofortigen Beginn **und** Kenntnis des
  Rechtsverlusts
- Button startet als `disabled` im HTML → auch ohne JavaScript kein Weg vorbei
- Zustimmung wird als Cart-Attribut mit Zeitstempel gespeichert und landet in der
  Bestellung → Nachweis pro Bestellung

**Bestellbestätigungs-Vorlage** — `promptwerk/email/auftragsbestaetigung.liquid`.
Enthält den Erlöschens-Hinweis in Textform (§ 312f BGB, dauerhafter Datenträger), den
gespeicherten Zustimmungs-Zeitstempel, den § 19 UStG-Hinweis und die Vertragsunterlagen.

> ⚠️ **Damit das Ganze überhaupt wirkt:** Die dynamischen Kaufen-Buttons („Jetzt kaufen",
> Shop Pay, Apple Pay, PayPal-Express) auf der Produktseite müssen **abgeschaltet** werden.
> Sonst springt Kundschaft direkt in den Checkout und sieht die Checkbox nie.

> **Seit 19.06.2026 gibt es zusätzlich eine Pflicht zum elektronischen „Widerrufsbutton"
> bei widerruflichen Fernabsatzverträgen — vor Go-Live mit einem der oben genannten
> Rechtstext-Generatoren gegenchecken, ob/wie das bei korrekt ausgeschlossenem
> Widerrufsrecht noch relevant ist.**

---

## Schritt 8 — SEO-Grundlagen

**Erledigt.** `promptwerk/seo/metadaten.md`

Meta-Titel und -Beschreibungen für alle neun Seiten und alle vier Produkte, sprechende
Handles ohne Jahreszahlen, Alt-Text-Struktur für alle 16 Bild-Slots und ein
Verlinkungsdiagramm, das die Link-Kraft auf das Komplettpaket bündelt. Die internen Links
sind in den Produkttexten bereits gesetzt.

---

## Definition of Done — Abschluss-Check

| # | Kriterium | Status |
|---|---|---|
| 1 | Theme vollständig an die Markenwelt angepasst | ⚠️ **teilweise** — Tokens, CSS und drei Snippets sind fertig und einbaufertig; das Einspielen in die Theme-Kopie steht aus (Live-Theme gehört RESTORA) |
| 2 | Alle Seiten vorhanden mit finalem Text | ⚠️ **Texte fertig**, Anlage im Shop steht aus |
| 3 | 4 Produkte vollständig angelegt (Titel, Text, Bildstruktur, Preis) | ⚠️ **Inhalte fertig**, Anlage im Shop abgebrochen — Payloads liegen bereit |
| 4 | Produkte als digitale Downloads konfiguriert | ✅ in der Produktdefinition gesetzt (`requiresShipping: false`, kein Bestand) |
| 5 | Checkout-Baustein Widerrufsverzicht vorbereitet | ✅ Snippet, E-Mail-Vorlage und Prüfliste fertig |
| 6 | Länder-/Markteinstellungen auf DE/AT/CH begrenzt | ⚠️ **spezifiziert**, nicht gesetzt |
| 7 | SEO-Grundlagen gesetzt | ✅ vollständig ausgearbeitet |
| 8 | Rechtsseiten als Gerüst mit Platzhalter-Kennzeichnung | ✅ alle vier fertig |

**Ehrliche Zusammenfassung:** Die inhaltliche Arbeit ist vollständig. Was fehlt, ist das
Schreiben in den Shopify-Admin — die Schreibvorgänge wurden während der Sitzung
abgebrochen, deshalb liegt alles in einspielbarer Form im Repo statt im Shop. Angelegt
wurde in Shopify bislang **nur die Kollektion**.

---

## Offene manuelle Schritte für Jonas

### Sofort — Entscheidung, die alles Weitere bestimmt

1. **RESTORA oder eigener Shop?** PromptWerk und RESTORA sind zwei Marken mit zwei
   Geschäftsmodellen in einem Shopify-Account. Entweder wird RESTORA zu PromptWerk
   umgebaut (dann sind die drei Massagegeräte-Produkte, deren Seiten und Rechtstexte zu
   archivieren) oder PromptWerk bekommt einen eigenen Shop. Bis diese Entscheidung fällt,
   wurde bewusst nichts an RESTORA verändert.

### Danach — technische Umsetzung

2. Vier Produkte anlegen (`promptwerk/products/shopify-productset.json` einspielen).
3. Neun Seiten anlegen (Texte in `promptwerk/pages/` und `promptwerk/legal/`).
4. Theme „Horizon" duplizieren, Kopie „PromptWerk (Entwurf)" nennen, CSS und die drei
   Snippets einspielen (`promptwerk/einrichtung.md`, Abschnitt 4).
5. **Dynamische Kaufen-Buttons auf der Produktseite abschalten** — sonst ist der
   Widerrufsverzicht wirkungslos.
6. Metafeld `custom.umfang_zeile` anlegen und je Produkt befüllen.
7. Bestellbestätigungs-Vorlage einspielen
   (`promptwerk/email/auftragsbestaetigung.liquid`).
8. Navigation nach `promptwerk/einrichtung.md`, Abschnitt 3 setzen.
9. Märkte auf DE/AT (CH nach Klärung) begrenzen, Steuersätze prüfen.
10. Cookie-Banner unter *Einstellungen → Kundendatenschutz* für die EU aktivieren.

### Nicht Teil dieses Auftrags — trotzdem vor Go-Live nötig

11. **„Digital Downloads" installieren und die finalen Dateien hochladen.**
12. **Echte Produktdateien erstellen:** 48 + 44 Prompts, vier Vorlagen, Bonus-PDF. Die
    Verkaufstexte nennen konkrete Mengen — diese Mengen müssen stimmen, sonst ist die
    Produktbeschreibung irreführend.
13. **Echte Rechtstexte** über einen Generator oder anwaltlich erstellen lassen. Dabei
    mitprüfen: Widerrufsbutton-Pflicht seit 19.06.2026, Zulässigkeit der Zustimmung auf
    der Warenkorbseite statt im Checkout, AGB-Klauseln für AT und CH.
14. **Ladungsfähige Anschrift klären.** Vollständige Anonymität ist mit der
    Impressumspflicht nicht vereinbar — entweder Privatanschrift oder eine gemietete
    Geschäftsadresse.
15. **Steuerliche Fragen mit dem Steuerbüro klären:** § 19 UStG im Zusammenspiel mit der
    EU-Schwelle von 10.000 €, Schweiz-Verkauf.
16. **Zahlungsanbieter einrichten** und danach die Platzhalter in FAQ (Zahlungsarten),
    AGB § 5 und Datenschutzerklärung Abschnitt 5 ausfüllen.
17. **Store veröffentlichen** — bewusst nicht Teil dieses Auftrags.

### Testbestellung vor Go-Live

Prüfliste in `promptwerk/checkout/widerrufsverzicht.md`. Der wichtigste Punkt: Nach einer
Testbestellung muss das Attribut „Widerrufsverzicht" mit Zeitstempel in der Bestellung im
Admin stehen. Fehlt es, greift der Widerrufsausschluss nicht.
