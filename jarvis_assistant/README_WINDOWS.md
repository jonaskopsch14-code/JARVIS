# Jarvis — Setup auf Windows

Persönlicher Sprach-Assistent (Iron-Man-Stil). Denkt lokal über **Ollama**,
spricht über **ElevenLabs** (Fallback: Windows-Stimme). Push-to-Talk per
**Strg+Alt+J**.

> Der Assistent läuft auch komplett **ohne Mikrofon im Text-Modus** — praktisch
> zum ersten Ausprobieren und als Fallback.

## 1. Einmalige Einrichtung

1. **Python 3.11+** installieren — https://www.python.org/downloads/
   (beim Setup Häkchen „Add python.exe to PATH").
2. **Ollama** installieren — https://ollama.com — dann in der Eingabeaufforderung:
   ```
   ollama pull qwen2.5:7b-instruct
   ```
   (Anderes Modell möglich — Name in `config.json` unter `model` anpassen.)
3. Abhängigkeiten installieren (im Ordner `jarvis_assistant/`):
   ```
   pip install -r requirements.txt
   ```
   Für die Browser-Automatisierung (Phase 3) zusätzlich:
   ```
   playwright install chromium
   ```
4. **Konfiguration:** `config.example.json` → nach `config.json` kopieren und
   ausfüllen (mindestens `elevenlabs_api_key`, `elevenlabs_voice_id`, `city`).

## 2. Erster Test — ohne Mikrofon (Text-Modus)

```
python -m jarvis.main --text
```
Tippe z. B. `Was steht heute an?` — Jarvis nutzt Kalender + Wetter und antwortet
als Text. So prüfst du, dass Ollama + Skills laufen, bevor Audio ins Spiel kommt.

Termine hinterlegen: eine Textdatei `heute.md` in deinem Jarvis-Datenordner
(`%APPDATA%\Jarvis\heute.md`), eine Zeile pro Termin, z. B.:
```
- 10:00 Zahnarzt
- 14:00 Team-Call
```

## 3. Sprach-Modus

```
python -m jarvis.main
```
oder Doppelklick auf **`run_jarvis.bat`**. Dann:
- **Strg+Alt+J** drücken, sprechen (Aufnahme stoppt automatisch bei Stille).
- Jarvis antwortet mit Stimme.
- **Strg+Alt+Pause** = Not-Aus. Tray-Icon rechts unten zum Beenden.

Hinweis: Globale Hotkeys brauchen unter Windows evtl. **Administratorrechte**
(Eingabeaufforderung „als Administrator ausführen").

## 4. Mit Windows starten (optional)

Rechtsklick auf `install_autostart.ps1` → „Mit PowerShell ausführen".
Entfernen: die erzeugte `Jarvis.lnk` aus dem Autostart-Ordner löschen.

## 5. Sicherheitsstufen

Jede Werkzeug-Aktion wird vor Ausführung geprüft:
- **Stufe 1** (lesen/öffnen/informieren): läuft automatisch.
- **Stufe 2** (reversibel ändern): kurze Bestätigung.
- **Stufe 3** (löschen/Geld/senden/öffentlich): ausdrückliche Bestätigung, Default Nein.

Alles wird in `%APPDATA%\Jarvis\logs\` protokolliert (auch als `.audit.jsonl`).

## 6. Fehlerdiagnose

- **Kein Ton:** ElevenLabs-Key/Voice-ID prüfen; sonst greift automatisch die
  Windows-Stimme (SAPI5). Text erscheint zusätzlich im Konsolenfenster.
- **„Ollama nicht erreichbar":** läuft `ollama serve`? Modell gezogen?
- **Hotkey reagiert nicht:** Konsole als Administrator starten.
- **Mikro wird nicht erkannt:** in den Windows-Sound-Einstellungen als
  Standard-Aufnahmegerät setzen.

Die Ausbaustufen (Gedächtnis, Systemkontrolle, Proaktivität, Shop-Wächter) sind
in `PHASES.md` beschrieben.
