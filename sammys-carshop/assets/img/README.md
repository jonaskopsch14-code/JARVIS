# Bilder — Shot-Liste für den Relaunch

Dieser Ordner ist **absichtlich leer**. Die alte Website arbeitete
ausschließlich mit Stockfotos aus der Wix-/Unsplash-Bibliothek (Dateinamen wie
`Image by Will Creswick`, `nsplsh_…`) — beliebige Werkstätten, die nichts mit
dem Betrieb zu tun haben. Das war einer der Hauptkritikpunkte der Analyse und
wird nicht durch neue Stockfotos ersetzt, sondern durch echte Aufnahmen.

Bis echte Fotos vorliegen, bleibt der Auftritt textbasiert: der Hero-Bereich
arbeitet mit reiner CSS-Geometrie (Raster + Lichtkegel), nicht mit einem Bild.
Der Auftritt funktioniert so vollständig — Fotos machen ihn besser, sind aber
kein Blocker für den Go-live.

## Was fotografiert werden sollte

Reihenfolge = Priorität. Die ersten vier Aufnahmen tragen den größten Teil der
Wirkung.

| # | Motiv | Verwendung | Format |
|---|---|---|---|
| 1 | Außenansicht mit Einfahrt und Schild, sodass man den Hof wiedererkennt | Hero Startseite, Kontaktseite | 1920×1080 (16:9), quer |
| 2 | Werkstatthalle mit Hebebühne, Fahrzeug darauf, Licht an | Startseite „Warum wir", Über uns | 1600×1067 (3:2), quer |
| 3 | Inhaber am Fahrzeug oder am Diagnosegerät, arbeitend statt posierend | Über uns | 1200×1500 (4:5), hoch |
| 4 | Team vor der Halle, gemeinsam | Über uns, Karriere | 1600×1067 (3:2), quer |
| 5 | Diagnosegerät mit Werten auf dem Display | Leistungen → Diagnose | 1200×800 (3:2) |
| 6 | Klimaservicegerät im Einsatz | Leistungen → Klimaservice | 1200×800 (3:2) |
| 7 | Bremsscheibe/Bremsbeläge, alt neben neu | Leistungen → Bremsen | 1200×800 (3:2) |
| 8 | Autogasanlage im Motorraum oder Tank | Autogas-Seite | 1200×800 (3:2) |
| 9 | Werkstattersatzwagen | Startseite, Unfallreparatur | 1200×800 (3:2) |
| 10 | Reifenlager / Montiermaschine | Leistungen → Reifen | 1200×800 (3:2) |

## Aufnahme-Hinweise

- **Mit dem Handy geht das.** Ein aktuelles Smartphone bei Tageslicht liefert
  mehr als genug Qualität. Wichtiger als die Kamera ist Ordnung im Bild.
- **Hallentor auf, Licht an.** Werkstätten sind dunkler, als das Auge meint.
  Gemischtes Licht (Tageslicht + Neonröhren) am besten vermeiden — entweder
  Tor auf und Kunstlicht aus, oder umgekehrt.
- **Aufräumen im Bildausschnitt.** Ölkanister, Kaffeebecher und Kabel auf dem
  Boden ziehen den Blick. Ein sauberer Vordergrund wirkt professioneller als
  jede Bildbearbeitung.
- **Auf Kennzeichen achten.** Kundenfahrzeuge nur mit Einverständnis
  fotografieren; Kennzeichen am besten so wählen, dass sie nicht lesbar sind,
  oder nachträglich unkenntlich machen.
- **Personen brauchen ihre Einwilligung.** Fotos von Mitarbeitenden dürfen nur
  mit deren Zustimmung veröffentlicht werden — am besten kurz schriftlich
  festhalten (Formulierung: Verwendung auf der Website und im
  Google-Unternehmensprofil, jederzeit widerruflich).
- **Querformat für breite Flächen**, Hochformat nur für Porträts.

## Technisches beim Einbauen

1. **Format:** WebP oder AVIF mit JPG-Fallback. Zielgröße pro Bild unter
   200 KB, Hero unter 350 KB.
2. **Zwei Größen pro Motiv** ausspielen und über `srcset` einbinden, damit
   Handys nicht die Desktop-Datei laden:
   ```html
   <img src="assets/img/werkstatt-800.webp"
        srcset="assets/img/werkstatt-800.webp 800w,
                assets/img/werkstatt-1600.webp 1600w"
        sizes="(min-width: 900px) 50vw, 100vw"
        width="1600" height="1067" loading="lazy" decoding="async"
        alt="Blick in die Werkstatthalle: ein Fahrzeug auf der Hebebühne">
   ```
3. **`width` und `height` immer setzen** — sonst springt das Layout beim Laden
   (schlechter CLS-Wert bei PageSpeed).
4. **`loading="lazy"`** für alles unterhalb des ersten Bildschirms, **nicht**
   für das Hero-Bild.
5. **Alt-Texte beschreiben den Inhalt**, nicht das Keyword. „Blick in die
   Werkstatthalle, Fahrzeug auf der Hebebühne" ist richtig; „Kfz Werkstatt
   Wittenberg Autoreparatur günstig" ist Keyword-Stuffing.
6. **Bildnachweise:** Solange alle Fotos selbst aufgenommen sind, passt der
   Abschnitt „Bildnachweise" im Impressum. Kommt ein Fremdbild dazu, müssen
   Urheber und Lizenz dort ergänzt werden.

## Logo

Das bestehende Logo liegt bei Wix als PNG. Für den neuen Auftritt bitte die
**Originaldatei** besorgen (idealerweise Vektor: SVG, AI, EPS oder PDF) und als
`assets/img/logo.svg` ablegen. Danach in allen Seiten den Platzhalter im
Header ersetzen:

```html
<!-- statt -->
<span class="brand__mark" aria-hidden="true">SCS</span>
<!-- dann -->
<img class="brand__mark" src="assets/img/logo.svg" alt="" width="34" height="34">
```

Solange kein Vektor-Logo vorliegt, bleibt das Kürzel „SCS" im Header — das ist
bewusst schlicht gehalten und kein fremdes Markenzeichen.

Zusätzlich gebraucht (aus dem Logo ableitbar):
`favicon.ico`, `favicon.svg`, `apple-touch-icon.png` (180×180) sowie ein
Social-Preview-Bild 1200×630 für `og:image` — der `og:image`-Tag fehlt in den
Seiten noch, weil es bisher kein geeignetes Bild gibt.
