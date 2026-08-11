# PromptWerk — Markenwelt & Design-Tokens

Gestaltungsgrundlage für Theme, Produktseiten und alle Marketing-Assets.
Basis-Theme: **Horizon** (Shopify Erstanbieter). Die Tokens werden als CSS-Variablen
in `promptwerk/theme/promptwerk.css` ausgeliefert.

---

## 1. Gestaltungsprinzip

**„Werkstatt, nicht Raumschiff."**

Die Zielgruppe ist bereits im Geschäft und hat wenig Geduld. Die Oberfläche soll
kompetent wirken, ohne einzuschüchtern: viel Weißraum, ruhige Typografie, ein
einziger Akzentton, der ausschließlich für Handlungen (CTAs, Links) reserviert ist.

Bewusst **vermieden**:
- Lila/Blau-Verläufe („KI-Optik"), Glow-Effekte, Neon
- Stockfotos mit Menschen, 3D-Roboter, Gehirn-Icons
- Ausrufezeichen-Typografie, Countdown-Balken, „Nur heute"-Elemente

Bewusst **eingesetzt**:
- Monospace für echte Prompt-Beispiele → das Produkt wird sichtbar, nicht nur beschrieben
- Eine wiederkehrende Umfangs-Zeile auf jeder Produktseite → Erwartung sofort klar

---

## 2. Farbwelt

| Rolle | Token | Hex | Einsatz |
|---|---|---|---|
| Basis dunkel | `--pw-ink` | `#16202B` | Fließtext, Header-/Footer-Flächen, Code-Blöcke |
| Basis dunkel, weicher | `--pw-ink-soft` | `#28323E` | Rahmen auf dunkel, sekundäre Flächen |
| Hintergrund | `--pw-paper` | `#F7F4EF` | Seitenhintergrund (warmes Off-White) |
| Hintergrund erhöht | `--pw-paper-raised` | `#FFFFFF` | Karten, Produktkacheln |
| Akzent | `--pw-amber` | `#C97B1E` | CTA-Flächen, aktive Zustände |
| Akzent auf hell (Text) | `--pw-amber-ink` | `#8F5510` | Links, Text-Akzente — erfüllt AA auf `--pw-paper` |
| Akzent auf dunkel | `--pw-amber-light` | `#E0A458` | Akzente in Code-Blöcken und auf dunklen Flächen |
| Text gedämpft | `--pw-muted` | `#5E6874` | Hilfstexte, Meta-Zeilen |
| Linien | `--pw-line` | `#E2DCD2` | Trenner, Kartenrahmen |
| Erfolg / Vertrauen | `--pw-verified` | `#2F6B4F` | Häkchen bei „Sofort-Download", „Kein Abo" |

**Kontrastprüfung** (WCAG AA, Normaltext ≥ 4.5:1):

| Kombination | Verhältnis | Status |
|---|---|---|
| `--pw-ink` auf `--pw-paper` | 13,6:1 | AAA |
| `--pw-muted` auf `--pw-paper` | 5,4:1 | AA |
| `--pw-amber-ink` auf `--pw-paper` | 4,9:1 | AA |
| `--pw-paper` auf `--pw-amber` (CTA-Button) | 4,6:1 | AA |
| `--pw-amber-light` auf `--pw-ink` | 7,1:1 | AAA |

> Wichtig: `--pw-amber` (`#C97B1E`) ist **Flächenfarbe**, nicht Textfarbe auf hellem
> Grund. Für Akzenttext auf Off-White immer `--pw-amber-ink` verwenden.

---

## 3. Typografie

| Rolle | Schrift | Begründung |
|---|---|---|
| Überschriften | **Inter**, Weight 600 | in der Shopify-Font-Bibliothek enthalten, sehr gut lesbar, neutral-kompetent |
| Fließtext | **Inter**, Weight 400 | eine Familie für alles → ruhiges Schriftbild, schnelle Ladezeit |
| Prompt-Blöcke | System-Monospace-Stack | kein Zusatz-Webfont nötig, dadurch kein Ladezeit-Nachteil |

Monospace-Stack (bewusst ohne Webfont):
```
ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas,
"Liberation Mono", monospace
```

**Größen** (Fluid, `clamp()` — Werte in `promptwerk.css`):

| Ebene | Mobil → Desktop | Zeilenhöhe |
|---|---|---|
| H1 | 30 → 46 px | 1,15 |
| H2 | 24 → 32 px | 1,2 |
| H3 | 19 → 22 px | 1,3 |
| Fließtext | 16,5 → 17,5 px | 1,65 |
| Prompt-Block | 13,5 → 14,5 px | 1,6 |
| Meta / Umfangszeile | 13,5 → 14 px | 1,45 |

Maximale Textbreite Fließtext: **68 Zeichen** (`--pw-measure: 68ch`).

---

## 4. Wiederkehrendes Markenelement: die Umfangs-Zeile

Eine schmale, gepunktet getrennte Zeile direkt unter dem Produkttitel. Sie beantwortet
in einem Blick: *Wie viel? In welchem Format? Wann verfügbar?*

```
48 Prompts · PDF + Notion-Vorlage · Sofort-Download
```

Regeln:
- immer genau drei Segmente, getrennt durch ` · `
- Segment 1 = Menge, Segment 2 = Format, Segment 3 = Verfügbarkeit
- Segment 3 ist auf allen Produkten identisch: `Sofort-Download`
- gesetzt in Monospace, `--pw-muted`, `letter-spacing: 0.01em`
- technisch gepflegt als Produkt-Metafeld `custom.umfang_zeile` → einmal gepflegt,
  überall gleich gerendert (Produktkachel, Produktseite, Kollektion)

Markup: `promptwerk/theme/snippets/pw-umfang.liquid`

---

## 5. Prompt-Block

Das zentrale Vertrauenselement: ein echter, vollständiger Prompt — kein Ausschnitt.

- dunkle Fläche (`--pw-ink`), Text `#E8E4DC`, Platzhalter in `--pw-amber-light`
- Platzhalter immer in `[ECKIGEN KLAMMERN UND VERSALIEN]` → sofort erkennbar als Eingabefeld
- Kopf-Zeile mit Label „Beispiel-Prompt aus dem Paket" + Kopieren-Button
- horizontal scrollbar (`overflow-x: auto`), bricht auf Mobil nicht um → Prompt bleibt lesbar
- semantisch `<pre><code>` → funktioniert auch ohne geladenes Theme-CSS

Markup: `promptwerk/theme/snippets/pw-prompt.liquid`

---

## 6. Abstände & Formen

| Token | Wert |
|---|---|
| `--pw-space-unit` | 4 px (alle Abstände sind Vielfache) |
| Sektions-Abstand | 64 px mobil → 96 px Desktop |
| `--pw-radius` | 6 px (Karten, Buttons) |
| `--pw-radius-lg` | 10 px (Prompt-Blöcke) |
| Schatten | **keine** — Trennung erfolgt über `--pw-line` und Flächenwechsel |

---

## 7. Bild-Richtung

Da es keine physischen Produkte und (Vorgabe: Anonymität) keine Personen gibt:

- **Produktbilder** = typografische Cover auf `--pw-ink` mit Akzentlinie in `--pw-amber`
- **Keine** Mockups von Laptops/Tablets mit gespiegeltem Bildschirm
- Zweitbild: Screenshot einer echten Seite aus dem PDF (Inhalt statt Verpackung)
- Drittbild: Ausschnitt der Notion-/Sheets-Vorlage
- Viertbild: Übersichtsgrafik „Was ist enthalten"

Slot-Struktur und Alt-Texte: `promptwerk/seo/metadaten.md`
