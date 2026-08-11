# Widerrufsverzicht bei digitalen Inhalten — technische Umsetzung

Rechtlicher Zweck: Das Widerrufsrecht bei nicht auf einem körperlichen Datenträger
gelieferten digitalen Inhalten erlischt nach **§ 356 Abs. 5 BGB** nur, wenn **alle drei**
Bedingungen erfüllt sind:

1. Der Kunde stimmt **ausdrücklich** zu, dass mit der Ausführung vor Ablauf der
   Widerrufsfrist begonnen wird.
2. Der Kunde **bestätigt seine Kenntnis** davon, dass er dadurch sein Widerrufsrecht
   verliert.
3. Der Händler stellt eine **Vertragsbestätigung nach § 312f BGB auf einem dauerhaften
   Datenträger** zur Verfügung (→ Bestellbestätigungs-E-Mail,
   `promptwerk/email/auftragsbestaetigung.liquid`).

Fehlt eine davon, bleibt das Widerrufsrecht bestehen — der Kunde kann also nach dem
Download widerrufen und das Geld zurückverlangen.

---

## Der entscheidende Plan-Vorbehalt

**Eine Checkbox im Shopify-Checkout ist auf dem Basic-Plan technisch nicht möglich.**

Recherchiert in der Shopify-Dev-Doku (Stand dieser Umsetzung):

> „Checkout UI extensions that render on the information and shipping and payment steps
> in checkout are available **only to stores on a Shopify Plus plan**."
> — <https://shopify.dev/docs/apps/build/checkout/technologies>

Auch `checkout.liquid` ist Plus-exklusiv und wird ohnehin abgekündigt. Für den Basic-Plan
bleiben genau drei Wege:

| Weg | Bewertung |
|---|---|
| **A — Pflicht-Checkbox auf der Warenkorbseite**, die den Checkout-Button bis zur Zustimmung sperrt | **Gewählt.** Ohne App, ohne Plus, in Deutschland der etablierte Standardweg (dieselbe Mechanik wie die verbreitete AGB-Checkbox). |
| B — App aus dem App Store („Agree to Terms"-Apps) | Zusätzliche Kosten und Abhängigkeit; die meisten lösen dasselbe wie A. |
| C — Upgrade auf Shopify Plus | Für diesen Shop wirtschaftlich absurd. |

**Konsequenz von Weg A:** Die Zustimmung wird **vor** dem Checkout eingeholt, nicht darin.
Das ist zulässig, solange die Erklärung eindeutig, unmittelbar vor dem Kaufabschluss und
**nicht vorangehakt** erfolgt — und solange sie in der Bestellung dokumentiert wird.

> ⚠️ **Von Jonas rechtlich gegenprüfen zu lassen:** ob die Einholung auf der
> Warenkorbseite (statt im Checkout selbst) für den konkreten Fall genügt. Das ist eine
> Rechtsfrage, keine technische. Der Rechtstext-Generator bzw. die anwaltliche Prüfung
> muss das bestätigen.

---

## Umsetzung

Datei: `promptwerk/theme/snippets/pw-widerrufsverzicht.liquid`
Einbindung: in der Warenkorb-Sektion **direkt oberhalb** des Checkout-Buttons.

### Funktionsweise

1. Zwei getrennte Erklärungen in **einer** Checkbox — bewusst zusammengefasst, weil § 356
   Abs. 5 BGB beide verlangt und eine getrennte Abfrage die Zustimmungsquote senkt, ohne
   rechtlich mehr zu leisten. Der Text nennt beide Punkte ausdrücklich.
2. **Nicht vorangehakt** (`checked` ist nirgends gesetzt) — das ist zwingend.
3. Der Checkout-Button ist bis zum Anhaken `disabled`.
4. Beim Anhaken wird ein **Cart-Attribut** gesetzt:
   `attributes[Widerrufsverzicht]` = `"Zugestimmt am <ISO-Zeitstempel>"`.
   Cart-Attribute wandern automatisch in die Bestellung und erscheinen im Admin unter
   *Zusätzliche Details* — damit ist die Zustimmung **pro Bestellung dokumentiert**.
5. Ohne JavaScript bleibt der Button gesperrt (`disabled` steht im HTML, nicht per JS) →
   kein Weg, ohne Zustimmung zu bestellen.

### Warum ein Cart-Attribut und keine Cart-Note

Die Note ist ein einziges freies Textfeld, das Kundschaft überschreiben kann. Attribute
sind benannte Schlüssel-Wert-Paare, die pro Bestellung sauber ausgelesen und in der
E-Mail-Vorlage referenziert werden können (`{{ attributes.Widerrufsverzicht }}`).

---

## Zusammenspiel mit der Bestellbestätigung

Die Bestätigung nach § 312f BGB muss den Erlöschens-Hinweis **in Textform** enthalten.
Die Vorlage `promptwerk/email/auftragsbestaetigung.liquid` gibt den Hinweis aus und
zeigt zusätzlich den gespeicherten Zeitstempel der Zustimmung an. Damit sind Bedingung 2
und 3 nachweisbar erfüllt.

---

## Prüfliste vor Go-Live

- [ ] Checkbox erscheint auf der Warenkorbseite oberhalb des Checkout-Buttons
- [ ] Checkbox ist **nicht** vorausgewählt
- [ ] Checkout-Button ist ohne Haken nicht anklickbar (auch bei deaktiviertem JavaScript)
- [ ] Nach einer Testbestellung steht das Attribut „Widerrufsverzicht" mit Zeitstempel in der Bestellung im Admin
- [ ] Bestellbestätigungs-E-Mail enthält den Erlöschens-Hinweis im Text
- [ ] Die Links auf Widerrufsbelehrung und AGB in der Checkbox-Zeile funktionieren
- [ ] Express-Checkout-Buttons (Shop Pay, PayPal, Apple Pay) auf der **Produktseite** sind deaktiviert — sonst umgehen sie den Warenkorb und damit die Checkbox ⚠️ **wichtig, wird leicht übersehen**
- [ ] Rechtliche Bestätigung eingeholt, dass die Einholung auf der Warenkorbseite genügt

> **Zum vorletzten Punkt:** Solange dynamische Checkout-Buttons („Jetzt kaufen", Shop Pay,
> Apple Pay) auf der Produktseite aktiv sind, springt Kundschaft direkt in den Checkout und
> sieht die Checkbox nie. Diese Buttons müssen im Theme-Editor unter
> *Produktseite → Kaufen-Buttons* abgeschaltet werden. Ohne diesen Schritt ist die gesamte
> Konstruktion wirkungslos.
