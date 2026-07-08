# Integrationsplan: Jarvis × CEO-GPT — ein Gehirn, zwei Zugänge

**Datum:** 2026-07-08
**Status:** Entscheidungen GEKLÄRT (2026-07-08) — Umsetzung wartet verbindlich auf die Phase-0-Abnahme (Sprach-Kern am PC). Kein Integrations-Code, bis Phase 0 abgenommen ist.
**Nächster Schritt:** Phase-0-Checkliste → `plans/2026-07-08-phase-0-sprachkern-checkliste.md`
**Betrifft:** Jarvis (`claude/jarvis-local-assistant`, PR #9) + CEO-GPT (Claude-Code-Arbeitsplatz)
**Format:** folgt dem `create-plan.md`-Muster (Kontext → Zielbild → Ist-Zustand → Architektur → Phasen → Risiken → offene Fragen). *Da mir die reale `create-plan.md` von CEO-GPT nicht vorliegt, ist die Struktur sinngemäß nachgebildet.*

---

## 1. Kontext & Leitgedanke

CEO-GPT und Jarvis sind **technisch zwei verschiedene Tiere**:

| | CEO-GPT | Jarvis |
|---|---|---|
| Was | Claude-Code-Arbeitsplatz (Ordner, `CLAUDE.md`, Slash-Befehle, `context/`) | eigenständiges Python-Programm |
| Läuft | nur wenn du das Terminal öffnest | im Hintergrund, hört & spricht |
| Zugang | Tastatur / Terminal | Stimme |
| Stärke | Wissen **pflegen** (kuratierte Markdown-Dateien) | Wissen **aussprechen** + handeln |

Man kann sie nicht „zusammenkippen". Der elegante Weg ist eine **gemeinsame Datenschicht**:

> **CEO-GPT pflegt das Wissen (per Terminal). Jarvis spricht es aus (per Stimme). Beide teilen sich denselben Ordner.** Ein Gehirn, zwei Zugänge.

Die harte Regel bleibt **unangetastet und zentral**: Geld ausgeben / senden / löschen / veröffentlichen nur mit deiner Bestätigung — über das bestehende **Permission-Gateway** von Jarvis (`jarvis/security/permission_gateway.py`, Tier 1). CEO-GPTs „Absicherungs"-Idee und das Jarvis-Gateway sind dasselbe Konzept; **es bleibt genau EINE Instanz davon** (die von Jarvis), keine zweite Genehmigungslogik.

---

## 2. Zielbild

Ein lokaler Assistent auf dem Windows-PC (RTX 2080 Super, 8 GB VRAM), der:

- **(a)** auf das Wake-Word „Jarvis" reagiert — zusätzlich zum bestehenden Push-to-Talk (der als Fallback bleibt);
- **(b)** von sich aus spricht (proaktiv): Morgenbegrüßung mit Kennzahlen, Hinweis auf neue Kunden-Mails;
- **(c)** das CEO-GPT-Wissen (`context/`, `key-metrics.md`) als Gedächtnis nutzt;
- **(d)** die harte Freigaberegel behält (Gateway zentral, auch für proaktive Aktionen).

---

## 3. Ist-Zustand (was schon steht)

**Jarvis (PR #9), getestet, reiner Python-Kern:**
- `security/` — Permission-Gateway (Tier 0/1, durable `pending_approval`, Audit), Geld = `spend` = Tier 1.
- `core/` — ReAct-Agent-Loop, LLM-Abstraktion (Ollama/Qwen ↔ Test-Backend), Router lokal/Cloud.
- `memory/` — `ObsidianVault` (Markdown + Frontmatter + Wikilinks, eigener Parser) + `VectorIndex` (Hashing-Fallback / `nomic-embed-text`).
- `tools/` — Notizen, Gmail (lesen + Entwürfe, **kein** `send`-Scope), Web-Agent (Cloud/Tier 1), Demo-Kauf.
- `voice/` — Wrapper für faster-whisper (STT), Piper/ElevenLabs (TTS), pynput-Hotkey (Push-to-Talk `Strg+Alt+J`). Imports gekapselt → Kern läuft ohne GPU.
- `main.py` — CLI: `chat`, `chat --demo`, `voice`, `approvals`/`approve`/`deny`.

**CEO-GPT (Beschreibung, nicht im Zugriff dieses Plans):**
- `CLAUDE.md`, Slash-Befehle unter `.claude/commands/`, `context/`-Dateien, `key-metrics.md`.
- Module: **Absicherung**, **Kontext**, **Daten** (Stripe/Umsatz), **Intelligenz** (Slack/Meeting-Recorder/Abteilungen).
- Zeitpläne als macOS-`.plist` (launchd).

> ⚠️ **Annahme**, bis du das reale Format lieferst: `context/` sind mehrere thematische `.md`-Dateien (z. B. `company.md`, `offers.md`, `customers.md`), `key-metrics.md` enthält Kennzahlen als Markdown (Überschriften + `Schlüssel: Wert`-Zeilen oder eine kleine Tabelle). Der Reader wird **defensiv** gebaut, damit Formatänderungen ihn nicht brechen.

---

## 4. Zielarchitektur

### 4.1 Datenbrücke — der gemeinsame „brain"-Ordner

Beide Systeme zeigen auf **einen** Ordner. Kein Kopieren, keine Synchronisation, keine doppelte Wahrheit.

```
C:\Jarvis\brain\                (konkreter Pfad → Phase-1-Detail, unkritisch)
├── context\                    ← FREMD-Zone. CEO-GPT pflegt. Jarvis NUR LESEN.
│   └── *.md                    ← beliebiges Markdown (Frontmatter optional)
├── key-metrics.md              ← FREMD-Zone. Jarvis NUR LESEN (falls vorhanden).
├── jarvis-memory\              ← EIGEN-Zone. Jarvis liest & SCHREIBT (Obsidian-Vault).
│   ├── 00-inbox\
│   ├── 10-raw\
│   ├── 20-wiki\
│   └── 90-system\
└── .claude\                    ← CEO-GPT Slash-Befehle + CLAUDE.md (nur fürs Terminal)
```

**Zwei klar getrennte Zonen (Entscheidung #2):**
- **Fremd-Zone** `context/` + `key-metrics.md` → für Jarvis **strikt read-only**. Jarvis kann CEO-GPTs kuratiertes Wissen niemals überschreiben.
- **Eigen-Zone** `jarvis-memory/` → Jarvis' beschreibbarer Obsidian-Vault. Alles, was Jarvis selbst festhält, landet hier (z. B. `00-inbox/`). Du entscheidest via CEO-GPT, was davon ins `context/` übernommen wird.

**Format-Adapter (Entscheidung #1 — Jarvis definiert das Format, kein hartes Schema):**
- Der Reader liest **beliebiges Markdown** aus `context/`: Frontmatter **optional** (der bestehende Parser aus `obsidian.py` kann das), ansonsten reiner Fließtext + Überschriften. Keine Pflichtfelder, keine erzwungene Struktur → robust, egal wie die CEO-GPT-Dateien am Ende aussehen.

**Code-Änderungen (klein, additiv):**
- `config.py`: neue Variablen `JARVIS_BRAIN_DIR`, `JARVIS_CONTEXT_DIR` (= `brain/context`), `JARVIS_METRICS_FILE` (= `brain/key-metrics.md`), `JARVIS_VAULT_DIR` (= `brain/jarvis-memory`).
- `memory/context_source.py` (neu): liest `context/*.md` **schreibgeschützt** ein (flexibler Adapter, s. o.), indexiert sie beim Start in den bestehenden `VectorIndex`, sodass `memory_search` **auch** CEO-GPT-Wissen findet.
- `memory/metrics.py` (neu): **defensiver, optionaler** Parser für `key-metrics.md` → `dict`. Fehlt die Datei oder ein Feld, fällt Jarvis auf eine neutrale Ausgabe zurück (kein Crash, kein hartes Schema).
- `tools/metrics_tool.py` (neu): Tool `metrics_read` (Effekt `READ`, Tier 0) → aktuelle Kennzahlen als Text (oder „keine Kennzahlen hinterlegt").
- Kein Eingriff in Gateway/Agent-Loop nötig.

### 4.2 Wake-Word „Jarvis"

**Bibliotheks-Empfehlung: openWakeWord** (nicht Porcupine).

| | openWakeWord | Porcupine (Picovoice) |
|---|---|---|
| Lizenz | Open Source, lokal | Free-Tier mit Access-Key, kommerziell eingeschränkt |
| „Jarvis"-Modell | vortrainiertes `hey_jarvis` verfügbar | eingebautes Keyword, aber Key nötig |
| Ressourcen | **CPU-only, ~zweistellige MB RAM, 0 GB VRAM** | CPU, sehr klein |
| Cloud | nein (DSGVO-freundlich) | Aktivierung/Key über Anbieter |

→ **openWakeWord** hält die knappen 8 GB VRAM komplett für Qwen frei und läuft rein lokal (passt zu ConsentFlow-Datenschutz-Anspruch).

**Einbau ins `voice/`-Modul:**
- `voice/wake_word.py` (neu): `WakeWordListener` mit Hintergrund-Thread, der einen `sounddevice`-Mikrofon-Stream in openWakeWord speist. Bei Erkennung (Score > Schwelle) → **derselbe Callback** wie beim Push-to-Talk: aufnehmen → Whisper → Agent-Loop → Piper.
- **Push-to-Talk (`Strg+Alt+J`) bleibt unverändert als Fallback** und als sicherer „Kein-Fehlauslöser"-Pfad.
- Zustandsmaschine: Wake-Word **stumm**, solange Jarvis spricht (verhindert Selbst-Trigger). „Barge-in" (Unterbrechen während des Sprechens) ist ausdrücklich **später**, nicht in v1.
- `main.py`: `voice`-Modus startet zusätzlich den `WakeWordListener`; ein Flag `--no-wake` erzwingt reinen Push-to-Talk-Betrieb.

### 4.3 Proaktives Sprechen

Ein vom Anfrage-Loop **getrennter** Auslöser-Mechanismus: `core/proactive.py`. **Zum Start genau ZWEI Trigger, mehr nicht (Entscheidung #3):**

1. **Morgenbegrüßung** (einmal täglich, zeitgesteuert): liest `key-metrics.md` vor, **falls vorhanden** — sonst neutrale Begrüßung ohne Zahlen. Tier 0.
2. **Mail-Hinweis** (ereignisgesteuert, Polling über Gmail `readonly`): „Es sind neue Kunden-Mails / Entwürfe da." Tier 0.

Kalender, ConsentFlow-Umsatz-Alerts etc. kommen **später**, nicht jetzt.

**Gateway-Kopplung (zentral):**
- Reines **Sprechen** ist Tier 0 (keine externe Nebenwirkung) — Jarvis darf einfach reden.
- Jede proaktiv **vorgeschlagene Aktion** mit Nebenwirkung läuft weiter durchs Gateway: „Soll ich Entwürfe vorbereiten?" → Entwurf = Tier 0 (compose), **Senden = Tier 1** (Freigabe). Nichts umgeht das Gateway.

**Zwei Ausführungswege (bewusst getrennt):**
1. **In-Process-Scheduler** (läuft, solange der Jarvis-Prozess läuft): einfache Zeitschleife oder `schedule`-Bibliothek.
2. **Windows Task Scheduler** (garantierte Zeiten, auch Autostart): startet bei Bedarf `pythonw -m jarvis.main proactive --morning` als Einmal-Lauf.

### 4.4 Windows-Anpassung (statt macOS-`.plist`)

CEO-GPTs Zeitpläne als launchd-`.plist` → **Windows Task Scheduler**.

- `setup/windows/register-tasks.ps1` (neu): registriert per `Register-ScheduledTask`/`schtasks`:
  - **Morgen-Task** täglich 08:00 → `pythonw.exe -m jarvis.main proactive --morning`.
  - **Autostart-Task** bei Login → startet den Dauer-Hörprozess (`pythonw.exe -m jarvis.main voice`).
- `pythonw.exe` (statt `python.exe`) → kein Konsolenfenster im Hintergrund.
- Zusätzlich zu dokumentieren: Audio-Gerätewahl unter Windows (WASAPI via `sounddevice`), CUDA für faster-whisper auf der 2080 Super, Ollama als Windows-Dienst.

---

## 5. Was du als Solo-Betrieb NICHT brauchst (ehrliche Bewertung)

Du arbeitest allein und anonym, kein Team. Empfehlung:

| CEO-GPT-Teil | Verdikt | Begründung |
|---|---|---|
| **Kontext** (`context/`) | ✅ übernehmen | Kern der Datenbrücke — Jarvis' Wissen. |
| **Daten** (Stripe/`key-metrics.md`) | ✅ übernehmen | ConsentFlow-Umsatz, ideal für die Morgenbegrüßung. |
| **Absicherung** | ⚠️ nicht doppeln | Konzept = Jarvis-Gateway. Jarvis-Gateway bleibt die einzige Instanz. |
| **Intelligenz** (Slack, Meeting-Recorder, Abteilungen/Agenten) | ❌ weglassen | Team-Features ohne Team. Reine Wartungslast, kein Nutzen für Solo. |

---

## 6. Phasen & Reihenfolge (kein Big-Bang)

> **Grundregel: erst der Sprach-Kern auf deinem PC, dann die Integration.**

### Phase 0 — Voraussetzung (DU, am PC): Jarvis-Sprach-Kern live
Ollama + `qwen3:8b`, Piper (Thorsten), faster-whisper auf CUDA, Push-to-Talk.
**Abnahme:** flüssiger Loop < 2 s, sauberer deutscher Sprach-Roundtrip.
**Vor dieser Abnahme wird KEINE Integration gebaut.**

### Phase 1 — Datenbrücke (reine Software, hardware-unabhängig testbar)
`context_source.py`, `metrics.py`, `metrics_read`-Tool, gemeinsamer `brain/`-Ordner, `config.py`-Erweiterung.
**Abnahme:** `memory_search` findet CEO-GPT-Wissen; `metrics_read` liefert echte Kennzahlen; Unit-Tests grün. *(Diese Phase könnte sogar ohne deinen PC vorab gebaut & getestet werden, sobald du das echte `context/`-/`key-metrics.md`-Format lieferst.)*

### Phase 2 — Proaktives Sprechen
`core/proactive.py` (In-Process-Scheduler) + Task-Scheduler-Morgen-Task + Gmail-Poll. Gateway-Kopplung.
**Abnahme:** Morgenbegrüßung spricht echte Kennzahlen; neue-Mail-Hinweis funktioniert; kein Gateway-Bypass.

### Phase 3 — Wake-Word
openWakeWord `hey_jarvis`, Integration in `voice/`, Stummschaltung während TTS. Push-to-Talk bleibt Fallback.
**Abnahme:** „Jarvis" aktiviert zuverlässig; akzeptable Fehlauslöserate; PTT weiter funktionsfähig.

### Phase 4 — Politur
Autostart-Task, Hintergrund-Dienst, Fehlauslöser-Feintuning, optional Barge-in.

---

## 7. Risiken & Gegenmaßnahmen

| Risiko | Auswirkung | Gegenmaßnahme |
|---|---|---|
| **Wake-Word-Fehlauslösung** (TV, Gespräche) | Jarvis meldet sich ungefragt | Score-Schwelle, Stumm während TTS, VAD, PTT-Fallback, Bestätigungs-Ton |
| **VRAM-Grenze 8 GB** | Qwen3-8B Q4 ~6 GB + Whisper + … → Überlauf, 5–10× langsamer | Whisper `medium` statt `large-v3` **oder** STT auf CPU; openWakeWord auf CPU (0 VRAM); Kontext 16 K; VRAM-Budget-Tabelle vor Phase 3 |
| **CEO-GPT-Format ändert sich** | Reader bricht | defensiver Parser, tolerant gegenüber fehlenden Feldern; Schema-Test |
| **Doppelte Genehmigungslogik** | zwei Wahrheiten, Sicherheitslücke | nur EIN Gateway (Jarvis); CEO-GPT-„Absicherung" nicht importieren |
| **Wartbarkeit** | wächst zum unwartbaren Monolith | Wake-Word & Proaktiv sind **additiv**; Gateway/Agent-Core bleiben unberührt |
| **Always-listening-Datenschutz** | Mikrofon dauerhaft an | alles lokal (openWakeWord + Whisper lokal), nichts in die Cloud — passt zum ConsentFlow-Anspruch |

### VRAM-Budget (grobe Schätzung, RTX 2080 Super / 8 GB)
| Komponente | VRAM |
|---|---|
| Qwen3-8B Q4_K_M | ~6,0 GB |
| faster-whisper `medium` (float16) | ~2,0 GB → **eng**; ggf. CPU oder on-demand laden |
| openWakeWord | 0 GB (CPU) |
| Piper | 0 GB (CPU) |

→ Empfehlung: **Whisper auf `medium` oder CPU**, damit Qwen dauerhaft im VRAM bleibt. Feste Messung in Phase 0/3.

---

## 8. Zusammenfassung

Der elegante Weg ist **keine Verschmelzung der Programme, sondern eine geteilte Datenschicht**: ein `brain/`-Ordner, den CEO-GPT pflegt und Jarvis ausspricht. Jarvis bekommt drei additive Fähigkeiten (CEO-GPT-Wissen lesen, proaktiv sprechen, Wake-Word) — der bewährte Kern (Gateway, Agent-Loop) bleibt unverändert. Gebaut wird **strikt phasenweise**: erst dein Sprach-Kern am PC, dann die reine Software-Datenbrücke, dann proaktives Sprechen, zuletzt das Wake-Word. Team-Features (Intelligenz-Modul) werden bewusst weggelassen.

## 9. Geklärte Entscheidungen (2026-07-08)

Alle offenen Fragen sind beantwortet. ✅ = verbindlich entschieden.

1. ✅ **Format:** Jarvis definiert das Format. Schlanker Adapter liest **beliebiges Markdown** in `brain/context/` (Frontmatter optional, sonst Fließtext + Überschriften). **Kein hartes Schema** — robust gegenüber jeder späteren CEO-GPT-Struktur.
2. ✅ **Schreibrechte / Zonen:** Fremd-Zone (`context/`, `key-metrics.md`) **strikt read-only**. Eigen-Zone `brain/jarvis-memory/` (bestehender Obsidian-Vault) ist beschreibbar. Zwei klar getrennte Zonen.
3. ✅ **Proaktive Trigger:** Genau zwei zum Start — (a) Morgenbegrüßung (liest `key-metrics.md`, falls vorhanden; sonst neutral) und (b) Hinweis auf neue Gmail-Entwürfe/wichtige ungelesene Mails. Beide Tier 0. Kalender/ConsentFlow-Alerts später.
4. ✅ **Wake-Word:** openWakeWord „hey jarvis", CPU-only. Push-to-Talk (`Strg+Alt+J`) bleibt **gleichwertiger Fallback**, wird nicht ersetzt.
5. ✅ **Modul-Abgrenzung (Solo):** Kontext ✅, Daten/Stripe ✅ (später für ConsentFlow-Umsatz), Absicherung ⚠️ nicht doppeln (Jarvis hat Gateway/Git/Tests), Intelligenz-Modul ❌ komplett weglassen.
6. ✅ **VRAM:** Whisper `medium` **auf CPU**, damit Qwen3-8B ungestört im VRAM bleibt. Nur falls CPU-Whisper zu langsam → dann GPU-`medium` testen; nie beide groß gleichzeitig auf 8 GB.
7. ✅ **Reihenfolge (verbindlich):** Phase 0 (Sprach-Kern am PC) muss abgeschlossen und **von Jonas abgenommen** sein, BEVOR Phase 1 gebaut wird. Der Plan bleibt Plan, bis der Sprach-Kern läuft.

### Noch nicht entschieden (unkritisch, erst zu Phase-1-Beginn)
- Konkreter `brain/`-Pfad auf dem PC (Vorschlag `C:\Jarvis\brain`).
- Repo-Struktur der Integration (Vorschlag: im bestehenden `jarvis_local/` wachsen lassen).
- Autostart des Dauer-Hörprozesses beim Windows-Login (Vorschlag: ja, per Task Scheduler).

---
*Planungsdokument. Umsetzung der Integration erst nach Phase-0-Abnahme. Nächster Schritt: `plans/2026-07-08-phase-0-sprachkern-checkliste.md`.*
