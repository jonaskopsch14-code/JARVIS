# Rechtliche Abgrenzung (Entwurf für AGB)

> Dieser Text ist ein **technischer Entwurf** und muss vor Verwendung von einem
> Rechtsanwalt / Fachanwalt für IT-Recht geprüft werden. ConsentFlow selbst gibt
> keine Rechtsberatung.

## 1. Leistungsgegenstand

ConsentFlow ist ein **technisches Werkzeug** zur Einholung und Protokollierung von
Cookie-Einwilligungen. ConsentFlow stellt **keine Rechtsberatung** dar und ersetzt
diese nicht.

## 2. Was ConsentFlow technisch zusichert

- **Opt-in vor Skript-Laden:** Nicht-notwendige Skripte werden erst nach aktiver
  Einwilligung der Websitebesucher geladen.
- **Protokollierung:** Jede Einwilligung wird mit Zeitstempel, gewählten Kategorien
  und Consent-Version dokumentiert (Nachweispflicht).
- **Widerruf jederzeit:** Besucher können ihre Einwilligung jederzeit ändern oder
  widerrufen (`window.ConsentFlow.open()`).

## 3. Verantwortung des Kunden

Der Kunde (Website-Betreiber) bleibt selbst verantwortlich für:

- die inhaltliche Richtigkeit und Vollständigkeit seiner **Datenschutzerklärung**,
- die korrekte **Kategorisierung** der von ihm eingesetzten Cookies/Skripte
  (Statistik, Marketing, notwendig),
- die tatsächliche technische **Auszeichnung** der zu blockierenden Skripte
  (`type="text/plain" data-cf-category="…"`),
- die Einhaltung weiterer rechtlicher Pflichten (Impressum, Auftragsverarbeitung etc.).

## 4. Datenverarbeitung / Datensparsamkeit

- Es werden **keine personenbezogenen Daten** über das technisch Nötige hinaus
  ausgelesen oder gespeichert.
- Einwilligungs-Logs werden **pseudonymisiert** gespeichert: **kein Klarname**,
  sondern ein **gehashter Wert** aus IP-Adresse + User-Agent + tageweisem Salt,
  zusammen mit Zeitstempel und Consent-Status. Die ursprüngliche IP-Adresse ist
  aus dem gespeicherten Hash **nicht rekonstruierbar**.
- Für den produktiven Einsatz ist zwischen ConsentFlow und dem Kunden ein
  **Auftragsverarbeitungsvertrag (AVV/DPA)** abzuschließen.

## 5. Haftungsbeschränkung

ConsentFlow haftet für die zugesicherte **technische** Funktion (Abschnitt 2).
Eine Haftung für die rechtliche Wirksamkeit der Einwilligungen im Einzelfall oder
für Inhalte des Kunden (insb. Datenschutzerklärung) ist ausgeschlossen, soweit
gesetzlich zulässig.
