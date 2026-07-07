# Jarvis – Lokaler Windows-Sprachassistent

Ein persönlicher, überwiegend **lokaler** Sprachassistent für Jonas, gebaut nach
dem technischen Aufbau-Leitfaden 2026. Hybrid-Architektur: Sprache, LLM-Chat,
Gedächtnis und E-Mail laufen lokal; der Web-Agent nutzt ein Cloud-Modell.

> **Sicherheits-Kern:** Jede Aktion mit Nebenwirkung (senden, **Geld ausgeben**,
> löschen, veröffentlichen) wird vom **Permission-Gateway physisch angehalten**,
> bis Jonas zustimmt. Der Agent schlägt vor – das Gateway entscheidet.

## Was schon funktioniert (in diesem Repo, getestet)

Der komplette **Kern ist reines Python (stdlib)** und ohne GPU/Ollama lauffähig:

- **Permission-Gateway** mit Risiko-Tiers (0/1), durable `pending_approval` (SQLite,
  übersteht Neustart), Audit-Trail.
- **Agent-Loop** (ReAct) mit nativem Function-Calling-Schema, Gateway als harte
  Schranke vor jeder Tool-Ausführung.
- **Gedächtnis**: Obsidian-Vault (Markdown + Frontmatter + `[[wikilinks]]`) plus
  optionaler Vektor-Index (dependency-freies Hashing-Embedding als Fallback,
  `nomic-embed-text` als echter Pfad).
- **Tools**: Notizen (schreiben/suchen/lesen), Gmail (lesen + Entwürfe, **kein
  Sende-Recht**), Web-Agent (Cloud, Tier-1), Demo-Kauf (zeigt das Geld-Gate).
- **Router** lokal-vs-Cloud.
- **CLI** inkl. Text-Demo-Modus und Out-of-band-Freigabeverwaltung.

Die Voice-/LLM-/Web-Bausteine sind als saubere Wrapper mit gekapselten Imports
angelegt – sie laufen auf dem Windows-PC, ohne den Rest zu blockieren.

## Schnellstart (ohne GPU, überall lauffähig)

```bash
cd jarvis_local
python -m jarvis.main chat --demo        # regelbasiertes Demo-Backend, kein LLM nötig
```

Beispiel-Eingaben:
- `merke dir: Kunde Meier mag einen blauen Banner` → schreibt eine Notiz
- `was weißt du über Meier` → durchsucht das Gedächtnis
- `zeig ungelesene Mails`
- `kaufe ein Fachbuch für 20 Euro` → **Freigabe-Abfrage** (Tier 1, Geld)

Offene Freigaben verwalten (durable):
```bash
python -m jarvis.main approvals          # offene Tier-1-Aktionen anzeigen
python -m jarvis.main approve <id>       # freigeben
python -m jarvis.main deny <id>          # ablehnen
```

## Tests

```bash
cd jarvis_local
python -m unittest discover -s tests -v  # 26 Tests, keine externen Abhängigkeiten
```

Abgedeckt: Tier-Klassifikation, Tier-0-Automatik, Tier-1-Freigabe/Ablehnung,
**durable Pending über Neustart**, Audit, Obsidian-Roundtrip/Suche/Wikilinks,
Vektor-Suche, Gmail-Entwurf (MIME/base64, kein Sende-Scope), Gedächtnis-Tools,
Router und der komplette Agent-Loop inklusive Geld-Gate.

## Produktivbetrieb auf dem Windows-PC (RTX 2080 Super)

1. **Ollama + Modell:**
   ```powershell
   ollama pull qwen3:8b
   ollama pull nomic-embed-text   # optional, für semantische Suche
   ```
2. **Abhängigkeiten:** `pip install -r requirements.txt`
   (faster-whisper, piper-tts, pynput, sounddevice, google-api-python-client …)
3. **Piper-Stimme:** deutsches Thorsten-Modell (`de_DE-thorsten-high.onnx`) laden.
4. **Gmail (optional):** `credentials.json` aus der Google Cloud Console ablegen;
   erster Lauf öffnet den OAuth-Browser (nur `readonly` + `compose`).
5. **Web-Agent (optional, Cloud):** `ANTHROPIC_API_KEY` oder `OPENAI_API_KEY`
   setzen, `pip install browser-use`.
6. **Starten:**
   ```powershell
   python -m jarvis.main chat     # Text gegen lokales Qwen
   python -m jarvis.main voice    # Sprache (Whisper + Piper), Push-to-Talk Strg+Alt+J
   ```

Konfiguration über Umgebungsvariablen – siehe `.env.example`.

## Architektur

```
jarvis/
  core/    agent_loop.py · llm.py · router.py · demo_backend.py
  voice/   stt.py (faster-whisper) · tts.py (Piper/ElevenLabs) · hotkey.py (pynput)
  tools/   base.py · memory_tool.py · gmail_tool.py · web_agent_tool.py · demo_tool.py
  memory/  obsidian.py · vector_index.py
  security/permission_gateway.py · audit_log.py
  app.py · config.py · main.py
```

### Warum dieser Aufbau
- **Gateway von Tag 1**: Sicherheit liegt im Policy-Layer, nicht im Agent-Code.
  Ein Tool deklariert nur seine Wirkung (`read/suggest/send/spend/delete/publish`);
  das Tier ergibt sich daraus. Geld = `spend` = Tier 1 = immer Bestätigung.
- **Backend-Abstraktion**: der Agent-Loop spricht gegen ein Protokoll – lokal
  Ollama/Qwen, in Tests/Demo ein deterministisches Backend.
- **Lokal zuerst**: der getestete Kern braucht keine schweren Abhängigkeiten;
  GPU-/Cloud-Teile sind gekapselt.

## Phasenplan (Leitfaden)
1. **Sprach-Kern** – Hotkey → Whisper → Qwen → Piper. *(Wrapper vorhanden)*
2. **Gedächtnis** – Obsidian + Vektor-Index. ✅ implementiert & getestet
3. **Tools + Gateway** – Function-Calling, Gmail, Permission-Gateway. ✅
4. **Kundenbetreuung (ConsentFlow)** – Support-Entwürfe, Wissens-Notizen.
5. **Web-Agent (Hybrid)** – browser-use über Cloud, streng Tier-1-gekoppelt. *(Wrapper vorhanden)*

## Hinweis
Claude Code hat den Code gebaut und getestet; das **Live-System läuft auf deinem
Windows-PC**, nicht in der Cloud (GPU, Mikrofon, Ollama sind lokal). Die
datenschutzfreundlichste Kette ist rein lokal (Piper + lokales LLM) – Cloud nur
für den Web-Agenten.
