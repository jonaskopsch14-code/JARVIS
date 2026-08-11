# Startseite — Aufbau und finaler Text

Sektionsreihenfolge für das Horizon-Theme. Jede Sektion unten mit fertigem Text.
Die Startseite ist bewusst kurz: sechs Sektionen, keine Slider, kein Popup.

| # | Sektion (Horizon) | Zweck |
|---|---|---|
| 1 | Rich text | Value Proposition + zwei CTAs |
| 2 | Icons with text | Vertrauenselemente (drei Punkte) |
| 3 | Featured collection | die vier Produkte |
| 4 | Multi-column | „Warum PromptWerk“ |
| 5 | Rich text | Prompt-Beispiel als Beweis |
| 6 | Collapsible content | FAQ-Teaser mit Link auf die volle FAQ |

---

## 1 — Header (Rich text)

**Überschrift (H1)**
> Getestete KI-Prompts für den Geschäftsalltag.

**Fließtext**
> Du hast ChatGPT oder Claude offen und weißt genau, was du brauchst — aber nicht, wie du es formulieren musst. PromptWerk liefert fertige Prompt-Systeme und Vorlagen für Marketing, Kundenkommunikation und Verwaltung. Kopieren, zwei Klammern ausfüllen, weiterarbeiten.

**Button 1 (primär):** `Produkte ansehen` → `/collections/prompt-bibliotheken-vorlagen`
**Button 2 (sekundär):** `Wie das funktioniert` → Ankerlink auf Sektion 5

*Hinweis zur Textführung: keine Zahl im H1 („500 Prompts“) — die Menge steht auf den
Produktseiten in der Umfangs-Zeile. Im H1 zählt der Anwendungsfall.*

---

## 2 — Vertrauenselemente (Icons with text, 3 Spalten)

| Icon | Überschrift | Text |
|---|---|---|
| Download | **Sofort verfügbar** | Downloadlink direkt nach dem Kauf per E-Mail. Kein Versand, keine Wartezeit. |
| Kein Wiederholen | **Kein Abo** | Einmal kaufen, dauerhaft nutzen. Keine Verlängerung, keine Folgekosten. |
| Bearbeiten | **Anpassbar** | PDF plus editierbare Vorlage. Du baust die Prompts auf deine Fälle um. |

---

## 3 — Produktübersicht (Featured collection)

**Überschrift:** Die vier Pakete
**Kollektion:** `Prompt-Bibliotheken & Vorlagen`
**Anzeige:** 4 Produkte, Raster, Vendor ausblenden, Umfangs-Zeile einblenden
**Link darunter:** `Alle Produkte ansehen` → `/collections/prompt-bibliotheken-vorlagen`

---

## 4 — Warum PromptWerk (Multi-column, 3 Spalten)

**Sektionsüberschrift:** Warum PromptWerk

**Spalte 1 — Nach Anwendungsfall sortiert, nicht nach Tool**
> Die meisten Prompt-Sammlungen ordnen nach Plattform. Im Alltag suchst du aber nach der Aufgabe: „Ich brauche einen Newsletter“, nicht „Prompts für Tool X“. Genau so ist hier sortiert.

**Spalte 2 — Auf den deutschen Markt zugeschnitten**
> Deutschsprachige Prompts für deutschsprachige Kundschaft — inklusive der Dinge, die im englischen Original fehlen: Siezen und Duzen, Rechnungstexte, Kleinunternehmerregelung.

**Spalte 3 — Vollständig statt angerissen**
> Jeder Prompt ist komplett: Rolle, Kontext, Aufgabe, Regeln. Keine Ein-Zeilen-Stichworte, die du selbst zu Ende bauen musst.

---

## 5 — Prompt-Beispiel (Rich text, Anker `#beispiel`)

**Überschrift:** So sieht ein Prompt aus

**Einleitung**
> Kein Ausschnitt und kein nachgebautes Beispiel. Das ist ein vollständiger Prompt aus der Bibliothek „Marketing & Content“:

**Prompt-Block** (Monospace, dunkle Fläche — Snippet `pw-prompt.liquid`)
```
Du bist Marketing-Texter:in für kleine Dienstleistungsunternehmen
im deutschsprachigen Raum.

KONTEXT
Unternehmen: [WAS DU MACHST, EIN SATZ]
Zielgruppe:  [WER KAUFT, MÖGLICHST KONKRET]
Kanal:       [INSTAGRAM / LINKEDIN / NEWSLETTER]
Tonalität:   sachlich, keine Superlative, kein Hype

AUFGABE
Entwickle 5 Post-Ideen zum Thema [THEMA]. Pro Idee:
  1. Aufhänger, maximal 12 Wörter
  2. Kernaussage in einem Satz
  3. Konkretes Beispiel aus dem Alltag der Zielgruppe
  4. Abschluss ohne Werbe-Handlungsaufforderung

REGELN
- Keine Emojis, keine rhetorische Frage als Einstieg
- Keine Behauptung, die ich nicht belegen kann
- Fehlt dir Kontext, frage nach, statt zu erfinden
```

**Abschlusstext**
> Alles in eckigen Klammern ist ein Eingabefeld, der Rest funktioniert unverändert. Nach demselben Muster sind alle 92 Prompts aufgebaut — deshalb lassen sie sich auf eigene Fälle umbauen, statt bei null anzufangen.

---

## 6 — FAQ-Teaser (Collapsible content, 4 Einträge)

**Sektionsüberschrift:** Häufige Fragen

1. **Wie bekomme ich die Datei nach dem Kauf?**
   Direkt nach dem Bezahlen bekommst du eine E-Mail mit dem Downloadlink. Kein Konto nötig, kein Versand.

2. **Funktioniert das mit ChatGPT und mit Claude?**
   Ja, mit beiden — auch in den kostenlosen Varianten. Die Prompts sind bewusst so geschrieben, dass sie nicht von den Besonderheiten eines einzelnen Anbieters abhängen.

3. **Gibt es ein Abo?**
   Nein. Einmalzahlung, dauerhafte Nutzung. Es gibt nichts zu kündigen.

4. **Kann ich die Vorlagen anpassen?**
   Ja. Neben dem PDF bekommst du eine editierbare Vorlage (Notion beziehungsweise Google Sheets), in der nichts gesperrt ist.

**Link darunter:** `Alle Fragen ansehen` → `/pages/faq`
