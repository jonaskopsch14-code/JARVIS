# Sammy's Car-Shop — Relaunch

Neubau der Website von **Sammy's Car-Shop**, Am Alten Bahnhof 31A, 06886
Lutherstadt Wittenberg (Inhaber: Samuel Kopsch), als Ersatz für die veraltete
Wix-Seite unter [www.scs-wb.de](https://www.scs-wb.de).

Grundlage ist die Bestandsaufnahme, die dem Relaunch vorausging. Der Befund
dort in einem Satz: 5-Seiten-Wix-Baukasten, Copyright „©2021", Stockfotos,
widersprüchliche Öffnungszeiten, kein Cookie-Consent trotz beschriebenem Google
Analytics und YouTube, unvollständiges Impressum, keine Conversion-Elemente.

**Technisch ist das hier bewusst schlicht:** statisches HTML, ein CSS-File, ein
JS-File, keine Abhängigkeiten, kein Build-Schritt, kein Framework. Die Dateien
lassen sich per FTP auf jedes Hosting kopieren. Das ist keine Sparversion,
sondern die Antwort auf das Hauptproblem der alten Seite — sie war an einen
Baukasten gebunden, dessen Standard-Template niemand pflegte.

---

## Schnellstart

```bash
# Lokal ansehen (irgendein statischer Server; Dateien lassen sich auch direkt öffnen)
cd sammys-carshop
python3 -m http.server 8080     # -> http://localhost:8080

# Konsistenz- und Go-live-Prüfung
node tools/check-site.mjs

# Vor dem Go-live: offene Platzhalter werden als Fehler gewertet
node tools/check-site.mjs --strict
```

`check-site.mjs` braucht kein `npm install` — es hat keine Abhängigkeiten.

---

## Aufbau

```
sammys-carshop/
├── index.html            Startseite
├── leistungen.html       Alle Leistungen mit Ankern (#klimaservice, #bremsen …)
├── autogas.html          Autogas/LPG — das bisher ungenutzte Alleinstellungsmerkmal
├── ueber-uns.html        Betrieb, Ablauf einer Reparatur
├── karriere.html         Stellenanzeige Kfz-Mechatroniker
├── kontakt.html          Formular, Kontaktdaten, Anfahrt, Karte (nach Einwilligung)
├── fahrzeuge.html        VORBEREITET, NICHT AKTIV — siehe „Stufe 3"
├── impressum.html        § 5 DDG
├── datenschutz.html      DSGVO
├── 404.html
├── .htaccess             301-Weiterleitungen, Sicherheits-Header, Caching
├── robots.txt / sitemap.xml
├── assets/css/site.css   Ein Stylesheet, keine externen Requests
├── assets/js/site.js     Navigation, Öffnungszeiten-Status, Consent, Formular
├── assets/img/README.md  Shot-Liste für echte Fotos (Ordner absichtlich leer)
├── content/betrieb.json  EINZIGE QUELLE DER WAHRHEIT für alle Betriebsdaten
└── tools/check-site.mjs  Prüft jede Seite gegen betrieb.json
```

### Warum `content/betrieb.json` + `tools/check-site.mjs`

Der teuerste Fehler der alten Präsenz war kein Design-, sondern ein
Datenpflegefehler: Die Öffnungszeiten standen auf der Website anders als in
Cylex und den Gelben Seiten, und im Fuß klebte seit Jahren „©2021".

Deshalb steht jede Betriebsangabe genau einmal in `content/betrieb.json`, und
`check-site.mjs` vergleicht **jede** HTML-Seite damit. Das Skript meldet:

- abweichende Telefonnummer, Adresse, E-Mail, Fax oder Firmenschreibweise
- Öffnungszeiten, die von `betrieb.json` abweichen — auch die Kopie in `site.js`
- fest eingetragene Copyright-Jahre (genau der „©2021"-Fehler)
- fehlende Impressum-/Datenschutz-Links, fehlende Consent-Schaltfläche
- **extern geladene Skripte, Stylesheets, Bilder oder `<iframe>`** — also jeden
  Weg, auf dem ohne Einwilligung Daten zu Dritten abfließen könnten
- Sterne-Bewertungen im Text oder `aggregateRating` im Markup, solange die
  Bewertung nicht verifiziert ist
- offene `{{TODO: …}}`-Platzhalter als Go-live-Blocker

Nach **jeder** inhaltlichen Änderung einmal laufen lassen. Ändert sich eine
Betriebsangabe, zuerst `betrieb.json` anpassen — das Skript zeigt dann alle
Stellen, die nachgezogen werden müssen.

---

## Vor dem Go-live

`node tools/check-site.mjs --strict` listet die offenen Punkte jederzeit
aktuell auf. Es sind ausschließlich Angaben, die **nur der Inhaber liefern
kann**:

| # | Wo | Was fehlt |
|---|---|---|
| 1 | `impressum.html` | Zuständige Handwerkskammer, Eintragung in der Handwerksrolle, gesetzliche Berufsbezeichnung. Pflichtangaben nach § 5 Abs. 1 Nr. 5 DDG, weil das Kfz-Technikerhandwerk zulassungspflichtig ist (Anlage A HwO). Für Lutherstadt Wittenberg ist nach unserer Recherche die **Handwerkskammer Halle (Saale)** zuständig — bitte bestätigen. |
| 2 | `impressum.html` | Erklärung zur Verbraucherstreitbeilegung (§ 36 VSBG). Vorformuliert für den Fall der Nichtteilnahme. |
| 3 | `datenschutz.html` | Name und Anschrift des Hosting-Anbieters, Speicherdauer der Server-Logfiles, Datum des Go-live. |
| 4 | `kontakt.html` | Formular-Endpunkt (siehe unten). Bis dahin verhindert `site.js` das Absenden und zeigt den E-Mail-Fallback — es geht also keine Anfrage verloren. |
| 5 | `content/betrieb.json` | **Öffnungszeiten bestätigen.** Eingetragen sind die der eigenen Website (Mo–Fr 8–17, Sa+So geschlossen). Cylex und Gelbe Seiten sagen Mo–Fr 8–18 und Sa 8–12, Stand 29.06.2025. Eine der beiden Angaben ist falsch. |
| 6 | `content/betrieb.json` | Google-Bewertung am Live-Profil verifizieren (Quellen widersprechen sich: ~4,8★/13 gegen ~4,6★/75–79). Danach eintragen und den vorbereiteten `aggregateRating`-Block in `index.html` aktivieren. |
| 7 | `fahrzeuge.html` | Nur relevant, wenn Fahrzeughandel betrieben wird — siehe „Stufe 3". |

Zusätzlich stehen im Quelltext **`PRÜFEN`-Kommentare** an Stellen, die
inhaltlich abgestimmt werden sollten (Autogas-Details, Gehaltsrahmen in der
Stellenanzeige, HU/AU-Vermittlung, Team-Vorstellung). `check-site.mjs` listet
sie unter „Redaktionelle Prüfpunkte" auf.

### Formular-Endpunkt einrichten

Statisches Hosting kann keine Mails versenden. Drei Wege, absteigend
empfohlen:

1. **Kleines PHP-Skript beim eigenen Hoster** (bei nahezu jedem deutschen
   Paket vorhanden). Keine Drittanbieter, keine Datenübermittlung, kein
   zusätzlicher AV-Vertrag. `action="kontakt.php"` setzen und im Skript das
   Honeypot-Feld `website` prüfen — ist es gefüllt, war es ein Bot.
2. **Formular-Dienst** (z. B. Formspree). Schnell, aber die Anfragen laufen
   über einen Dritten: AV-Vertrag nötig und in der Datenschutzerklärung
   nachzutragen.
3. **`mailto:`-Fallback behalten.** Funktioniert schon jetzt über
   „Stattdessen per E-Mail", ist aber unkomfortabel.

In allen Fällen bleibt die Datenschutz-Checkbox verpflichtend; `check-site.mjs`
erzwingt das.

---

## Weiterleitungen

Die 301-Weiterleitungen in `.htaccess` sind der Grund, warum die bestehenden
Rankings und die Links aus den Branchenverzeichnissen den Umzug überleben.
Abgedeckt sind die alten Wix-Pfade ohne `.html` (`/impressum`, `/kontakt`,
`/über-uns` inklusive der URL-kodierten Umlaut-Variante,
`/kundenbewertungen`) sowie **`/imprint.html`** — die noch älteren statischen
Seite, die parallel erreichbar und indexiert war.

Läuft die Seite nicht auf Apache, müssen die Regeln dort nachgebaut werden:

```nginx
# nginx
location = /impressum   { return 301 /impressum.html; }
location = /kontakt     { return 301 /kontakt.html; }
location = /über-uns    { return 301 /ueber-uns.html; }
location = /imprint.html { return 301 /impressum.html; }
```

```
# Netlify / Cloudflare Pages (_redirects)
/impressum      /impressum.html   301
/kontakt        /kontakt.html     301
/über-uns       /ueber-uns.html   301
/imprint.html   /impressum.html   301
```

Nach dem Umzug in der Google Search Console eine neue Sitemap einreichen und
die alten URLs auf Fehler prüfen.

---

## Was sich im Code nicht lösen lässt

Ein Teil der Analyse betrifft Konten und Einträge außerhalb dieses
Verzeichnisses. Ohne diese Schritte bleibt die halbe Wirkung liegen:

1. **Google-Unternehmensprofil** — Öffnungszeiten, Leistungen und Fotos
   pflegen, sobald Punkt 5 der Tabelle geklärt ist. Das Profil ist für eine
   lokale Werkstatt der wichtigste Kanal, wichtiger als die Website selbst.
2. **Verzeichnisse bereinigen** — Cylex, Gelbe Seiten (zwei Einträge!), 11880,
   golocal, Yelp und die übrigen. Überall dieselbe Schreibweise
   „Sammy's Car-Shop", dieselben Öffnungszeiten, dieselbe Telefonnummer. Der
   veraltete Eintrag „Kopsch Samuel Selbsthilfewerkstatt" beschreibt den
   heutigen Betrieb nicht mehr und verwässert das Profil.
3. **Bewertungen aktiv einholen** — 13 Google-Rezensionen sind gegenüber
   Gänsicke und Schandert wenig. Nach jeder Reparatur einmal danach fragen
   wirkt mehr als jede SEO-Maßnahme; ein QR-Code auf der Rechnung reicht.
4. **Facebook klären** — die Seite `facebook.com/pages/Sammys-Carshop/…` ist
   automatisch generiert und ungepflegt. Entweder übernehmen und pflegen oder
   Löschung beantragen. Sie ist deshalb **absichtlich nicht** als `sameAs`
   verlinkt: ein Link würde eine tote Seite zum offiziellen Kanal erklären.
5. **Wix-Abo kündigen** — erst nachdem die neue Seite live ist, die
   Weiterleitungen greifen und die Domain umgezogen ist.
6. **Echte Fotos** — Shot-Liste in `assets/img/README.md`. Der Auftritt
   funktioniert ohne Fotos vollständig (der Hero ist reine CSS-Geometrie statt
   eines Stockbilds), gewinnt aber deutlich mit ihnen.

---

## Umsetzungsstand gegenüber der Analyse

**Stufe 1 — Rechtssicherheit und Datenhygiene**

| Empfehlung | Status |
|---|---|
| Cookie-Consent rechtskonform | ✅ Anders gelöst, siehe „Abweichungen" — die Seite lädt beim Aufruf nichts von Dritten; die Karte ist einwilligungsgesteuert mit gleichwertigen Schaltflächen |
| Impressum vervollständigen | ⚠️ Struktur samt Kammer-, Berufs- und VSBG-Abschnitt steht; drei Angaben muss der Inhaber liefern |
| Datenschutzerklärung aktualisieren | ✅ Neu geschrieben, beschreibt genau das, was die Seite tut. Universal Analytics (zum 01.07.2023 eingestellt) und YouTube sind ersatzlos entfallen, weil beides nicht mehr eingesetzt wird |
| Öffnungszeiten vereinheitlichen | ⚠️ Eine Quelle im Code, maschinell erzwungen — der inhaltliche Widerspruch braucht die Bestätigung des Inhabers |
| `imprint.html` per 301 weiterleiten | ✅ In `.htaccess` |

**Stufe 2 — Relaunch-Kern**

| Empfehlung | Status |
|---|---|
| Modernes, responsives Design ohne Stockfotos | ✅ Kopfzeile bei 390–1600px geprüft, kein horizontaler Überlauf, Dunkelmodus unterstützt |
| Leistungsseiten je Service | ✅ Neun Leistungen mit eigenen Ankern |
| Autogas/LPG als Alleinstellungsmerkmal | ✅ Eigene Seite plus Navigationspunkt |
| HU/AU ergänzen | ⚠️ Als `PRÜFEN`-Kommentar hinterlegt — unklar, ob angeboten |
| Klick-to-Call, Formular, Terminanfrage, Karte, Bewertungen | ✅ Alles vorhanden; Telefonnummer als Button in jeder Kopfzeile |
| Tonalität vereinheitlichen, Karriere trennen | ✅ Kundenseiten durchgehend „Sie", Recruiting auf `karriere.html` im „Du". Die alte Meta-Description sprach auf der Startseite Bewerber statt Kunden an — `check-site.mjs` verhindert diesen Rückfall |
| LocalBusiness-Schema, lokale Keywords | ✅ `AutoRepair`-JSON-LD mit Adresse, Öffnungszeiten, Leistungskatalog, `areaServed` |

**Stufe 3 — Fahrzeughandel**

Vorbereitet in `fahrzeuge.html`, aber **nicht aktiv**: `noindex`, nicht in der
Navigation, nicht in der Sitemap, in `robots.txt` gesperrt. Die Seite enthält
die Consent-Mechanik für ein Börsen-Widget, den PAngV-Textbaustein und eine
Aktivierungs-Checkliste. Grund für das Zurückhalten: An-/Verkauf ist in
Verzeichnissen als Leistung gelistet, aber es existiert kein online abrufbarer
Bestand — laut Analyse ist der Status ungeklärt. Eine Leistung zu bewerben, die
es möglicherweise nicht gibt, wäre schlechter als die Lücke.

---

## Abweichungen von der Analyse

Drei Empfehlungen sind bewusst anders umgesetzt. Jede ist begründet, keine
davon ist eine Auslassung:

1. **Kein Consent-Banner beim Seitenaufruf.** Die Empfehlung setzte voraus,
   dass Analytics und YouTube weiterlaufen. Dieser Auftritt lädt beim Aufruf
   **nichts** von Dritten: keine Webfonts, kein CDN, kein Analytics, keine
   nicht notwendigen Cookies. Damit gibt es beim Laden nichts, wofür eine
   Einwilligung nötig wäre — ein Banner wäre reine Kulisse. Eingewilligt wird
   punktuell dort, wo tatsächlich ein Drittinhalt geladen werden soll (Karte),
   mit gleichwertigen Schaltflächen und jederzeitigem Widerruf im Seitenfuß.
   Das ist die strengere Variante, nicht die laxere. Wird später Analytics
   ergänzt, muss ein echtes Opt-in-Banner dazukommen — die Consent-Mechanik in
   `site.js` ist bereits auf Kategorien ausgelegt.

2. **Kein Link zur EU-OS-Plattform.** Die Analyse empfiehlt ihn als
   Pflichtangabe. Nach unserem Stand ist das überholt: Die
   Online-Streitbeilegungsplattform der EU-Kommission wurde zum **20.07.2025**
   eingestellt und die Verlinkungspflicht aus der ODR-Verordnung ist entfallen.
   Ein Link würde ins Leere führen und wäre selbst wieder angreifbar. Die
   Erklärung nach § 36 VSBG bleibt und ist vorbereitet. **Bitte im Rahmen der
   anwaltlichen Prüfung gegenprüfen.**

3. **Keine Sterne-Bewertung im Markup.** Ein `aggregateRating` ist vorbereitet,
   aber auskommentiert. Die Analyse nennt zwei unvereinbare Zahlen (~4,8★/13
   gegen ~4,6★/75–79, letztere laut Trustami selbst ungeprüft und kumuliert).
   Ein Rating auszuspielen, das nicht der öffentlich sichtbaren Bewertung
   entspricht, ist irreführend und verstößt gegen die Google-Richtlinien für
   strukturierte Daten — im schlimmsten Fall verliert die Seite ihre
   Rich-Results. Erst verifizieren, dann aktivieren.

---

## Rechtlicher Vorbehalt

Impressum und Datenschutzerklärung sind nach bestem Wissen erstellt und
adressieren die in der Analyse benannten Mängel. Sie sind **keine
Rechtsberatung**. Weil beim Impressum eines zulassungspflichtigen Handwerks
und bei den Preisangaben im Fahrzeughandel (§ 25a UStG, PAngV) Fehler
abmahnfähig sind, sollten beide Texte vor dem Go-live einmal anwaltlich oder
über die Handwerkskammer geprüft werden. Die Kammern bieten ihren Mitgliedern
das üblicherweise kostenlos an — der günstigste Weg, den letzten Rest Risiko
loszuwerden.

---

## Wartung

- Inhaltliche Änderung → danach `node tools/check-site.mjs`.
- Betriebsdaten ändern sich → **zuerst** `content/betrieb.json`, dann die
  Seiten, die das Skript anmahnt, dann Google-Profil und Verzeichnisse.
- Neuer Drittinhalt (Video, Börse, Chat) → immer über
  `data-consent-gate` einbinden und in der Datenschutzerklärung beschreiben.
  Das Skript schlägt an, wenn ein `<iframe>` fest im HTML steht.
- CSS oder JS geändert → beim Ausrollen Dateinamen oder `?v=`-Parameter
  ändern, sonst sehen wiederkehrende Besucher wegen des Ein-Jahres-Cache aus
  `.htaccess` die alte Version.
- Kein `npm install`, keine Abhängigkeiten, keine Update-Pflicht — es gibt
  nichts, was von selbst veralten kann außer den Inhalten.
