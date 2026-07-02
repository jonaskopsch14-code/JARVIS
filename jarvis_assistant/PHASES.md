# Jarvis — Phasenübersicht & Status

Persönlicher Sprach-Assistent (Iron-Man-Stil) für Windows. Denkt lokal über
Ollama, spricht über ElevenLabs, mit gestuften Sicherheitsrechten über den PC.

> **Ehrlicher Teststatus:** Der gesamte Code ist geschrieben und die
> **hardware-unabhängige Logik ist offline getestet** (33 Tests, alle grün:
> Assistent-Schleife, Sicherheits-Gate, Gedächtnis, Datei-/Systemsteuerung,
> Proaktiv-Scheduler, Shop-Analyse, Erweiterungen). Die Teile, die Mikrofon,
> Audio, Ollama, ElevenLabs, Playwright oder Gmail brauchen, sind lauffähiger
> Code mit Fallbacks — **verifiziert werden sie erst auf deinem Windows-PC.**
> Deshalb ist die Reihenfolge: Phase für Phase bei dir starten und prüfen.

## Was du zum Loslegen tust
Siehe **`README_WINDOWS.md`**. Kurzform: Python + Ollama installieren,
`ollama pull qwen2.5:7b-instruct`, `pip install -r requirements.txt`,
`config.example.json` → `config.json` ausfüllen, dann erst im **Text-Modus**
testen (`python -m jarvis.main --text`), danach Sprach-Modus.

## Phasen

| Phase | Inhalt | Status |
|---|---|---|
| **1 Kern-Sprachschleife** | Hotkey Strg+Alt+J → STT → Ollama(+Tools) → ElevenLabs; Skills: App öffnen, Websuche, Datei lesen, Wetter, Kalender; 3-Stufen-Sicherheits-Gate | Code + Tests ✓, PC-Test offen |
| **2 Gedächtnis & Persönlichkeit** | SQLite-Gedächtnis (Vorlieben, Themen), feste Persona, Merk-Skills | Code + Tests ✓ |
| **3 Tiefe Systemkontrolle** | Dateien (L1/L2/L3), Prozesse, Browser (Playwright), Bildschirm sehen (Vision), Gmail lesen/Entwurf/Senden | Code + Tests ✓ |
| **4 Proaktivität** | Scheduler-Engine, morgendliches Briefing, Speicher-/Systemchecks, selbstständiges Melden | Code + Tests ✓ |
| **5 Shop-Wächter** | Shopify-Anbindung; Checks: fast ausverkauft, Umsatz-Ausreißer, Kaufabbrüche, Ladenhüter → kurze Vorschläge | Code + Tests ✓ |
| **6 Politur** | Always-on-Weckwort (openWakeWord), Tray mit Aktivitätslog, diese Doku | Code + Tests ✓ |
| **7+ Ausbau** | Beispiele: Marketing-Entwurf, Produktrecherche — nach dem Muster „vorbereiten, erst mit Okay ausführen". Weitere Skills per `EXTENDING.md` | Muster + Beispiele ✓ |

## Sicherheitsstufen (in jeder Phase aktiv)
- **Stufe 1** automatisch (lesen/öffnen/informieren)
- **Stufe 2** kurze Bestätigung (reversibel ändern)
- **Stufe 3** ausdrückliche Bestätigung (löschen, Geld, senden, öffentlich)
- Unbekannte Werkzeuge werden konservativ als Stufe 3 behandelt.
- Not-Aus per Hotkey (Strg+Alt+Pause) und Tray. Alles wird protokolliert.

## Was noch von dir kommt (wenn die jeweilige Phase dran ist)
- **Phase 3:** Gmail-OAuth (Google Cloud Console) — Anleitung in `email_gmail.py`.
- **Phase 5:** Shopify Admin-API-Token + Store-Domain in `config.json`.
- Optional Phase 6: `pip install openwakeword` fürs Weckwort.

## Eigene Fähigkeiten hinzufügen
Siehe **`EXTENDING.md`** — ein Skill ist eine Funktion mit `@skill`-Dekorator und
einer Risikostufe. Mehr braucht es nicht.
