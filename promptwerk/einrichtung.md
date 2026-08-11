# Einrichtung — Märkte, Steuern, Navigation, digitale Auslieferung, Theme

Alles, was im Shopify-Admin bzw. Theme-Editor gesetzt wird. Reihenfolge ist die
empfohlene Abarbeitungsreihenfolge.

---

## 1. Märkte: DE / AT / CH

**Ist-Zustand:** nur ein Markt „Germany" (`de`), aktiv.
**Soll:** Deutschland, Österreich, Schweiz — sonst nichts.

*Einstellungen → Märkte*

| Markt | Länder | Währung | Hinweis |
|---|---|---|---|
| Deutschland | DE | EUR | bestehender Hauptmarkt, unverändert lassen |
| Österreich | AT | EUR | dem bestehenden Markt hinzufügen **oder** eigener Markt |
| Schweiz | CH | CHF oder EUR | siehe unten |

Alle übrigen Länder bleiben **deaktiviert**. Damit kann außerhalb von DE/AT/CH nicht
bestellt werden.

### Warum diese Begrenzung

Bewusste Einfachheits-Entscheidung für den Start, kein technisches Limit:

- Als Kleinunternehmer nach § 19 UStG bleibt der Verkauf so in der inländischen Regelung.
- Beim grenzüberschreitenden B2C-Verkauf digitaler Leistungen in der EU greift ab
  **10.000 € netto pro Jahr (EU-weit kumuliert)** die Pflicht zur Besteuerung im
  Bestimmungsland — üblicherweise über das **OSS-Verfahren**. Mit einem kleinen
  Länderkreis bleibt diese Schwelle überschaubar und der Umsatz nachvollziehbar.
- Später jederzeit erweiterbar.

> ⚠️ **Wichtig zur Schwelle, von Jonas mit dem Steuerbüro zu klären:** Wie sich die
> Kleinunternehmerregelung und die EU-Digitalsteuer-Schwelle im konkreten Fall zueinander
> verhalten, ist eine steuerliche Frage — auch die Wechselwirkung mit dem seit 2025
> möglichen EU-weiten Kleinunternehmer-Status. Diese Umsetzung trifft dazu **keine**
> Aussage, sie begrenzt nur den Länderkreis.

> ⚠️ **Schweiz:** Kein EU-Mitglied. Damit gelten eigene Regeln (u. a. Schweizer
> MWST-Pflicht ab einer Umsatzschwelle für ausländische Anbieter elektronischer
> Dienstleistungen). Wenn das den Start unnötig verkompliziert, ist die pragmatische
> Variante: **zunächst nur DE und AT freischalten** und CH später ergänzen. Empfehlung:
> mit dem Steuerbüro klären, bevor CH aktiviert wird.

### Steuern

*Einstellungen → Steuern und Zölle → Deutschland*

- Sicherstellen, dass **kein Steuersatz** auf die Produkte angewendet wird.
- Die Produkte sind bereits mit `taxable: false` vorbereitet (siehe `products/katalog.md`).
- Ergebnis: keine Steuerzeile im Checkout, der angezeigte Preis ist der Endpreis.

---

## 2. Digitale Auslieferung: App „Digital Downloads"

**Muss Jonas manuell erledigen** — Apps lassen sich nicht über die API installieren.

1. Shopify App Store → **„Digital Downloads"** (Erstanbieter-App von Shopify, kostenlos).
2. Installieren.
3. Je Produkt die Datei(en) anhängen: App öffnen → Produkt wählen → Datei hochladen.

Warum diese App: kostenlos, von Shopify selbst, liefert automatisch nach Zahlungseingang
per E-Mail aus. Für vier Produkte völlig ausreichend. Wechsel auf eine kostenpflichtige
Alternative lohnt erst bei Lizenzschlüsseln, Zugangsbeschränkungen oder Streaming.

**Bereits vorbereitet, damit die App direkt greift:**

- Alle Produkte auf **kein Versand erforderlich** (`requiresShipping: false`) → im
  Checkout entfällt der Versandschritt vollständig
- **Bestandsverfolgung aus** → unbegrenzt verkaufbar
- Genau **eine Standardvariante** je Produkt → eindeutige Dateizuordnung

**Noch nicht möglich:** Die echten Dateien (Prompt-PDFs, Notion- und Sheets-Vorlagen)
existieren noch nicht. Das ist ein eigener Content-Erstellungsschritt.

---

## 3. Navigation

### Hauptmenü

| Eintrag | Ziel |
|---|---|
| Produkte | `/collections/prompt-bibliotheken-vorlagen` |
| Komplettpaket | `/products/promptwerk-komplettpaket` |
| FAQ | `/pages/faq` |
| Kontakt | `/pages/kontakt` |

Bewusst ohne „Startseite" (das Logo führt dorthin) und ohne Dropdowns — vier Produkte
brauchen keine Menü-Hierarchie. Das Komplettpaket steht eigenständig im Menü, weil es
das umsatzstärkste Produkt sein soll.

### Footer-Menü

| Eintrag | Ziel |
|---|---|
| Über PromptWerk | `/pages/ueber-promptwerk` |
| FAQ | `/pages/faq` |
| Kontakt | `/pages/kontakt` |
| Impressum | `/pages/impressum` |
| Datenschutzerklärung | `/pages/datenschutzerklaerung` |
| AGB | `/pages/agb` |
| Widerrufsbelehrung | `/pages/widerrufsbelehrung` |

> Die vier Rechtsseiten müssen **von jeder Seite aus in maximal einem Klick** erreichbar
> sein — deshalb vollständig in den Footer, nicht zusammengefasst hinter „Rechtliches".

> ⚠️ **Im Bestandsshop gefunden:** Der aktuelle Footer-Eintrag „Kontakt" zeigt auf
> `/pages/kontakt`, die vorhandene Seite hat aber den Handle `contact` → 404. Bei der
> PromptWerk-Struktur ist `kontakt` der richtige Handle; beim Bestandsshop RESTORA wäre
> der Link zu korrigieren.

---

## 4. Theme

**Vorgehen: Kopie statt Live-Theme.** Das aktive Theme „Horizon" gehört zu RESTORA und
wird nicht angefasst.

1. *Onlineshop → Themes → Horizon → ⋯ → Duplizieren*
2. Kopie umbenennen in **„PromptWerk (Entwurf)"**
3. Nur in der Kopie arbeiten, **nicht veröffentlichen**

### Theme-Einstellungen (Theme-Editor → Theme-Einstellungen)

| Bereich | Einstellung |
|---|---|
| Farben — Hintergrund | `#F7F4EF` |
| Farben — Text | `#16202B` |
| Farben — Akzent / Buttons | `#C97B1E`, Beschriftung `#F7F4EF` |
| Farben — Linien | `#E2DCD2` |
| Typografie — Überschriften | Inter, Weight 600 |
| Typografie — Fließtext | Inter, Weight 400 |
| Buttons | Radius 6 px, keine Schatten |
| Produktseite — dynamische Kaufen-Buttons | **AUS** ⚠️ zwingend, siehe unten |
| SEO | Shop-Name als Titel-Suffix |

> ⚠️ **Dynamische Kaufen-Buttons müssen aus sein.** „Jetzt kaufen", Shop Pay, Apple Pay
> und PayPal-Express auf der Produktseite überspringen den Warenkorb — und damit die
> Widerrufsverzicht-Checkbox. Bleiben sie aktiv, ist die gesamte
> § 356 Abs. 5 BGB-Konstruktion wirkungslos. Details: `checkout/widerrufsverzicht.md`.

### Dateien in die Theme-Kopie einspielen

| Datei | Ziel im Theme |
|---|---|
| `theme/promptwerk.css` | `assets/promptwerk.css` |
| `theme/snippets/pw-umfang.liquid` | `snippets/pw-umfang.liquid` |
| `theme/snippets/pw-prompt.liquid` | `snippets/pw-prompt.liquid` |
| `theme/snippets/pw-widerrufsverzicht.liquid` | `snippets/pw-widerrufsverzicht.liquid` |

Danach in `layout/theme.liquid` im `<head>`, nach dem Theme-CSS:

```liquid
{{ 'promptwerk.css' | asset_url | stylesheet_tag }}
```

Und in der Warenkorb-Sektion direkt oberhalb des Checkout-Buttons:

```liquid
{% render 'pw-widerrufsverzicht' %}
```

Sowie auf der Produktseite unter dem Titel:

```liquid
{% render 'pw-umfang', produkt: product %}
```

### Metafeld für die Umfangs-Zeile

*Einstellungen → Benutzerdefinierte Daten → Produkte → Definition hinzufügen*

| Feld | Wert |
|---|---|
| Name | Umfangs-Zeile |
| Namespace und Schlüssel | `custom.umfang_zeile` |
| Typ | Einzeiliger Text |

Die Werte je Produkt stehen in `products/katalog.md` und in `shopify-productset.json`.

---

## 5. Kundendatenschutz / Cookie-Banner

*Einstellungen → Kundendatenschutz*

- Cookie-Banner aktivieren, Region **Europäische Union** (und Schweiz, falls aktiviert)
- Einwilligung **vor** dem Setzen nicht notwendiger Cookies (§ 25 TDDDG)

Ohne diesen Schritt werden Cookies vor der Einwilligung gesetzt — ein häufiger und
leicht vermeidbarer Fehler beim Go-Live.

---

## 6. Was hier bewusst NICHT eingerichtet wird

| Punkt | Grund |
|---|---|
| Zahlungsanbieter | ausdrücklich nicht Teil des Auftrags — macht Jonas |
| Veröffentlichung / Passwortschutz entfernen | ausdrücklich nicht Teil des Auftrags |
| Echte Rechtstexte | nur Platzhalter-Gerüste, siehe `legal/` |
| Echte Produktdateien | eigener Content-Schritt |
| Eigene Domain | nicht beauftragt; aktuell nur `swszg1-tg.myshopify.com` |
