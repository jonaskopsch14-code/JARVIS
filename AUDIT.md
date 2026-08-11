# AUDIT — Ist-Zustand vor dem PromptWerk-Aufbau

**Datum:** 2026-08-11
**Erhoben über:** Shopify Admin GraphQL API (MCP-Verbindung)

---

## 1. Kernbefund (wichtig)

Der verbundene Shopify-Store ist **nicht leer und nicht neu**. Es handelt sich um einen
bereits aufgebauten Store mit einer **anderen Marke und einem anderen Geschäftsmodell**:

| | |
|---|---|
| Store-Name | **RESTORA** |
| Domain | `swszg1-tg.myshopify.com` (keine eigene Domain verbunden) |
| Plan | Basic |
| Währung | EUR |
| Land / Adresse | Deutschland, Lutherstadt Wittenberg |
| Preise inkl. Steuer | ja (`taxesIncluded: true`) |
| Geschäftsmodell | **physische Produkte** (Massagegeräte), Lieferzeit 7–14 Werktage → Dropshipping-Muster |

PromptWerk ist dagegen ein Store für **digitale Downloads**. Das sind zwei verschiedene
Marken in einem Shopify-Account.

**Konsequenz für diesen Auftrag:** Es wird nichts von RESTORA gelöscht, überschrieben oder
deaktiviert. PromptWerk wird **additiv** aufgebaut (Produkte als Entwurf, Theme als
unveröffentlichte Kopie, neue Seiten unveröffentlicht). Die Entscheidung, ob RESTORA
ersetzt werden soll oder PromptWerk einen eigenen Store bekommt, ist eine
Geschäftsentscheidung von Jonas — siehe `BUILD-LOG.md`, Abschnitt „Offene Entscheidungen".

---

## 2. Produkte (Ist)

Alle 3 Produkte sind **ACTIVE** (im Storefront sichtbar, sofern Store veröffentlicht),
Vendor `RESTORA`, Bestand jeweils 0, keine Tags, keine SKUs.

| Titel | Handle | Preis | Typ |
|---|---|---|---|
| RESTORA Nacken- & Schulter-Massager (6 Rollen) | `restora-nacken-schulter-massagegerat-beheizt` | 59,95 € | Nacken-Massagegeraet |
| RESTORA Augen-Massagegerät (beheizt, kabellos) | `restora-augen-massagegerat-beheizt-kabellos` | 44,95 € | Augen-Massagegeraet |
| RESTORA Massagepistole – Muskel-Recovery (6 Aufsätze) | `restora-massagepistole-muskel-recovery-6-aufsatze` | 69,95 € | Massagepistole |

**Auffälligkeiten (nicht Teil dieses Auftrags, aber notiert):**
- Bei der Massagepistole steht ein unaufgelöster Platzhalter in der öffentlichen
  Beschreibung: `Lieferzeit: [HIER LIEFERZEIT EINTRAGEN]`.
- Alle Produkte haben Bestand 0.
- Keine SKUs vergeben.

## 3. Kollektionen (Ist)

| Titel | Handle | Produkte |
|---|---|---|
| Home page | `frontpage` | 1 |
| Muskel-Recovery | `muskel-recovery` | 0 |
| Muskel-Recovery | `muskel-recovery-2` | 0 |
| Muskel-Recovery | `muskel-recovery-3` | 0 |

**Auffälligkeit:** „Muskel-Recovery" existiert dreimal, alle leer — vermutlich
versehentliche Mehrfachanlage. Aufräumen wäre sinnvoll, gehört aber nicht zu diesem Auftrag.

## 4. Seiten (Ist)

| Titel | Handle | veröffentlicht |
|---|---|---|
| Contact | `contact` | ja |
| Über uns | `uber-uns` | ja |
| Impressum | `impressum` | ja |
| Versand & Lieferung | `versand-lieferung` | ja |

**Fehlend für einen Digital-Store:** FAQ, Widerrufsbelehrung als eigene Seite, AGB als Seite,
Datenschutz als Seite (existiert nur als Shop-Policy).

## 5. Navigation (Ist)

**Hauptmenü (`main-menu`):** Startseite · Produkte (`/collections/all`) · Kontakt (`/pages/contact`)

**Footer (`footer`):** Search · Impressum · Kontakt (`/pages/kontakt`) · Versand & Lieferung

**Defekter Link gefunden:** Der Footer-Eintrag „Kontakt" zeigt auf `/pages/kontakt`, die Seite
hat aber den Handle `contact` → **404**. (Notiert, nicht verändert, weil es RESTORA betrifft.)

## 6. Rechtstexte / Shop-Policies (Ist)

Als Shopify-Policies vorhanden: Kontakt, Impressum, Datenschutzerklärung, Widerrufsrecht,
Versand, AGB. Inhalte auf RESTORA (physische Ware) zugeschnitten — für digitale Downloads
inhaltlich **nicht** passend (Widerrufsrecht bei digitalen Inhalten funktioniert anders,
Versandpolicy entfällt).

## 7. Theme (Ist)

| | |
|---|---|
| Aktives Theme | **Horizon** (Shopify-Erstanbieter-Theme, aktuelle Generation) |
| Rolle | MAIN (live) |
| Weitere Themes | keine |

Horizon ist ein gutes Fundament: modern, schnell, unterstützt Sections/Blocks und
Theme-Blocks. Für PromptWerk wird eine **Kopie** angelegt und angepasst, das Live-Theme
bleibt unberührt.

## 8. Märkte (Ist)

| Markt | Handle | Status |
|---|---|---|
| Germany | `de` | ACTIVE |

Nur Deutschland aktiv. Für PromptWerk sollen zusätzlich Österreich und Schweiz aufgenommen
werden (Schritt 6 des Auftrags).

## 9. Weiteres

- **Blog:** „News" (`news`) vorhanden, leer bzw. ungenutzt.
- **Apps:** Der API-Zugriff auf `appInstallations` ist für diese Verbindung nicht
  freigegeben (`access denied`) — die Liste installierter Apps konnte **nicht** ausgelesen
  werden. Jonas muss im Admin unter *Einstellungen → Apps und Vertriebskanäle* selbst
  prüfen. Relevant ist vor allem, ob **„Digital Downloads"** (Shopify-Erstanbieter) bereits
  installiert ist — nach aktuellem Stand ist es das vermutlich nicht, da der Store bisher
  rein physische Ware führt.
- **Bestellungen/Kunden:** nicht abgefragt (für den Aufbau nicht relevant).

---

## 10. Startpunkt für PromptWerk

Zusammengefasst: kein leerer Store, sondern ein fremdes Marken-Setup, das intakt bleiben
muss. PromptWerk startet damit bei **null eigener Substanz**, kann aber auf einer
brauchbaren technischen Basis aufsetzen (Horizon-Theme, DE-Markt, EUR, Steuer inklusive).
