# Jarvis — Persönlicher Sprach-Assistent · Phase-1-Feinplan

Status: **Entwurf zum Abnicken.** Noch kein Produktivcode. Sag „OK" oder ändere
einzelne Punkte, dann baue ich Phase 1 genau so.

> Ehrliche Rahmenbedingung: Ich (Claude Code) laufe in einer Linux-Cloud, nicht
> auf deinem Windows-PC. Ich schreibe & pushe den Code + eine exakte Anleitung;
> **ausführen und testen musst du auf deinem PC.** Ich behaupte nie, etwas
> „läuft", bevor du es bei dir bestätigt hast.

---

## 1. Ziel von Phase 1 (Abnahmekriterium)

Du drückst **Strg+Alt+J**, sagst *„Jarvis, was steht heute an"*, und Jarvis
**liest dir Termine + Wetter mit ElevenLabs-Stimme vor**. Dazu die Grund­fähig­
keiten: **App öffnen**, **im Web suchen**, **eine Datei vorlesen/zusammenfassen**.

Alles denkt lokal über **Ollama**; Sprache raus über **ElevenLabs** (Fallback
Windows-SAPI5). Die **Sicherheitsstufen** sind ab Tag 1 echter, getesteter Code.

---

## 2. Technische Entscheidungen (mit Begründung)

| Baustein | Wahl | Warum |
|---|---|---|
| Sprache→Text (STT) | **faster-whisper** (lokal) | Offline, privat, robust; kein Browser nötig. Modell `small`/`base` reicht, läuft neben Ollama auf der GPU/CPU. |
| Denken (LLM) | **Ollama**, Tool-Calling über `/api/chat` | Lokal, wie gewünscht. Qwen2.5/Qwen3 unterstützen natives Tool-Calling → sauberes Werkzeug-Protokoll. |
| Modell (Default) | **`qwen2.5:7b-instruct`** (konfigurierbar) | Passt in 8 GB VRAM der RTX 2080 Super, kann Tools. „Qwen3.5-9B" gibt es als Tag so nicht — Name bleibt in der Config, du kannst jederzeit wechseln (`qwen3:8b` etc.). |
| Text→Sprache (TTS) | **ElevenLabs** API, **SAPI5-Fallback** (pyttsx3) | Film-Stimme; Fallback wenn ElevenLabs offline/Kontingent leer. |
| Push-to-Talk | **`keyboard`**-Lib, Hotkey **Strg+Alt+J** | Globaler Hotkey systemweit. „Press to start, Aufnahme stoppt automatisch bei Stille" (VAD) — bequemer als Halten. |
| Hintergrunddienst | **Ein Python-Prozess** mit Hotkey-Thread + optionaler **FastAPI**-Ecke | Phase 1 schlank; FastAPI-Grundgerüst schon da, damit spätere Phasen (Proaktivität, Tray-UI) andocken. |
| Aus-Schalter | **Tray-Icon** (pystray) + Not-Hotkey **Strg+Alt+Pause** | Sofort stoppen, wie gefordert. |
| Protokoll/Audit | **Logdatei** `logs/jarvis.log` (jede Aktion) | Nachvollziehbar, welche Tools mit welchen Argumenten liefen. |
| Wetter | **Open-Meteo** (kein API-Key) | Echt & gratis, sofort lauffähig. |
| Kalender (Phase 1) | **lokale Quelle** (siehe offene Frage) | Echtes Google Calendar kommt in Phase 3 (OAuth). Für die Abnahme jetzt eine simple lokale Quelle. |

---

## 3. Modul-/Ordnerstruktur (`jarvis_assistant/`)

```
jarvis_assistant/
├─ jarvis/
│  ├─ __init__.py
│  ├─ config.py          # lädt config.json + .env (Keys, Modell, Voice-ID, Ort)
│  ├─ persona.py         # System-Prompt: Ton „Sir/Jonas", trocken-humorvoll
│  ├─ stt.py             # Mikro-Aufnahme + faster-whisper Transkription
│  ├─ llm.py             # Ollama-Client, Chat + natives Tool-Calling
│  ├─ tts.py             # ElevenLabs → Audio abspielen; SAPI5-Fallback
│  ├─ hotkey.py          # globaler Push-to-Talk-Hotkey + Not-Aus
│  ├─ security.py        # 3-Stufen-Risiko-Gate (echte Prüf-Logik)
│  ├─ audit.py           # strukturiertes Logging jeder Aktion
│  ├─ tray.py            # Tray-Icon + Statusanzeige + Beenden
│  ├─ skills/
│  │  ├─ __init__.py     # Tool-Registry (Name→Funktion, Risikostufe, Schema)
│  │  ├─ open_app.py     # Programm öffnen (Stufe 1)
│  │  ├─ web_search.py   # Websuche + kurze Antwort (Stufe 1)
│  │  ├─ read_file.py    # Datei lesen/zusammenfassen (Stufe 1)
│  │  ├─ weather.py      # Open-Meteo (Stufe 1)
│  │  └─ calendar_local.py # heutige Termine aus lokaler Quelle (Stufe 1)
│  └─ main.py            # verdrahtet alles: Hotkey→STT→LLM(+Tools)→TTS
├─ config.example.json   # Vorlage; du kopierst zu config.json
├─ requirements.txt
├─ run_jarvis.bat        # Doppelklick-Start unter Windows
├─ install_autostart.ps1 # optional: mit Windows starten
└─ README_WINDOWS.md     # Schritt-für-Schritt-Setup
```

---

## 4. Ablauf einer Sprach-Interaktion (Phase 1)

```
Strg+Alt+J
   │
   ▼
[hotkey] startet Aufnahme ──► [stt] faster-whisper ──► Text
   │                                                     │
   │                                                     ▼
   │                              [llm] Ollama + System-Prompt + Tools
   │                                     │  (Modell darf Tools aufrufen)
   │                                     ▼
   │                        [security] Risikostufe je Tool prüfen
   │                          Stufe1 = sofort │ Stufe2 = kurz bestätigen
   │                          Stufe3 = explizit bestätigen
   │                                     ▼
   │                        [skills] Tool ausführen ──► Ergebnis zurück ins LLM
   │                                     ▼
   │                        finale Antwort (Text)
   ▼                                     ▼
[audit] alles protokolliert      [tts] ElevenLabs spricht ──► Lautsprecher
```

Fehler werden **nie stillschweigend geschluckt**: schlägt ein Tool fehl, sagt
Jarvis es dir („Das Öffnen hat nicht geklappt, Grund: …") und loggt es.

---

## 5. Sicherheitsstufen — als echter Code

`security.py` bekommt eine Funktion, die **vor jeder** Tool-Ausführung läuft:

```
assess(tool_name, args) -> Stufe (1 | 2 | 3)
```

- **Stufe 1 – automatisch:** lesen, informieren, Apps öffnen, Web/Shop abrufen,
  Bildschirm lesen. → läuft ohne Rückfrage.
- **Stufe 2 – kurze Bestätigung** (reversibel): Datei schreiben/ändern, Programm
  schließen, Einstellung ändern. → Jarvis fragt einmal kurz („Soll ich?"),
  du sagst „ja".
- **Stufe 3 – immer explizit** (Geld/endgültig/nach außen): löschen, Geld
  ausgeben, Shopify-Preise/Einstellungen, E-Mail in deinem Namen senden,
  öffentlich posten. → verlangt klare Bestätigung; Default ist **Nein**.

Jedes Skill in der Registry trägt seine **Standard-Stufe**. Unbekanntes/Neues
wird konservativ als **Stufe 3** behandelt (sicher per Default). In Phase 1 gibt
es nur Stufe-1-Skills, aber der Mechanismus + Tests sind vollständig da, damit
Phase 3 (Dateien schreiben, E-Mail-Entwürfe) direkt sicher andockt.

---

## 6. Setup-Checkliste (machst du einmal auf dem PC)

1. **Python 3.11+** installieren (Häkchen „Add to PATH").
2. **Ollama** installieren → https://ollama.com → dann in der Eingabe­auf­forderung:
   `ollama pull qwen2.5:7b-instruct`
3. **ElevenLabs-Key** holen (Free-Tier) → in `config.json` eintragen.
4. Repo-Ordner `jarvis_assistant/` holen, dann:
   `pip install -r requirements.txt`
5. `config.example.json` → `config.json` kopieren, ausfüllen (Key, Voice-ID, Ort).
6. **Mikrofon** in Windows als Standard-Aufnahmegerät setzen.
7. Start per Doppelklick auf **`run_jarvis.bat`** (oder `python -m jarvis.main`).
8. **Test:** Strg+Alt+J → „Jarvis, was steht heute an" → er antwortet mit Stimme.

Hinweise, die ich in die README schreibe: `keyboard` braucht evtl. **Adminrechte**
für globale Hotkeys; erste ElevenLabs-Ausgabe kann 1–2 s brauchen; bei „kein Ton"
prüfen wir Fallback-SAPI5.

---

## 7. Offene Fragen für Phase 1 (bitte kurz beantworten)

1. **Kalender-Quelle jetzt:** Echtes Google Calendar ist erst Phase 3 (OAuth).
   Für die Abnahme jetzt — was ist dir lieber?
   - (a) **Lokale Textdatei** `heute.md`, in die du Termine schreibst (super
     einfach, sofort), oder
   - (b) **Windows-/Outlook-Kalender** per `.ics`-Export einlesen, oder
   - (c) Kalender in Phase 1 **weglassen**, nur Wetter — Google-Kalender kommt
     dann „richtig" in Phase 3.
   → Mein Vorschlag: **(a)** für Phase 1, in Phase 3 auf Google umstellen.
2. **Push-to-Talk-Stil:** „Drücken → sprechen → stoppt automatisch bei Stille"
   (mein Vorschlag) — oder lieber „Taste gedrückt halten während des Sprechens"?
3. **Autostart mit Windows** schon in Phase 1 einrichten, oder erst in Phase 6
   (Politur)? Vorschlag: Skript liefere ich mit, aktivieren optional.

---

## 8. Was NICHT in Phase 1 ist (ehrliche Abgrenzung)

- Kein Weckwort ohne Knopf (kommt Phase 6) — Phase 1 ist Push-to-Talk.
- Kein echtes Gmail/Shopify (Phase 3/5) — Zugangsdaten holen wir dann.
- Kein Langzeit-Gedächtnis über Sitzungen (Phase 2) — Phase 1 merkt sich nur den
  laufenden Dialog.
- Keine Proaktivität (Phase 4) — Phase 1 reagiert nur auf den Hotkey.

---

## 9. Danach

Sagst du „OK" (ggf. mit Antworten zu §7), baue ich Phase 1 komplett in
`jarvis_assistant/`, pushe alles inkl. `README_WINDOWS.md`, und gebe dir die
genaue Startanleitung. Dann führst du es aus und wir bringen es bei dir zum
Laufen — bevor wir Phase 2 anfassen.
