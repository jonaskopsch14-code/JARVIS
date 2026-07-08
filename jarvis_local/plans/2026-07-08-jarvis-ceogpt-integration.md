# Integrationsplan: Jarvis × CEO-GPT — ein Gehirn, zwei Zugänge

**Datum:** 2026-07-08
**Status:** ENTWURF — nur Plan, noch keine Implementierung
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
C:\Jarvis\brain\                (Vorschlag – Pfad ist offene Frage #2)
├── context\                    ← CEO-GPT pflegt (per Terminal). Jarvis liest NUR.
│   ├── company.md
│   ├── offers.md
│   ├── customers.md
│   └── ...
├── key-metrics.md              ← CEO-GPT/Daten-Modul pflegt. Jarvis liest NUR.
├── vault\                      ← Jarvis' Obsidian-Vault. Jarvis liest & SCHREIBT.
│   ├── 00-inbox\
│   ├── 10-raw\
│   ├── 20-wiki\
│   └── 90-system\
└── .claude\                    ← CEO-GPT Slash-Befehle + CLAUDE.md (nur fürs Terminal)
```

**Rollentrennung (wichtig gegen Datenkorruption):**
- `context/` + `key-metrics.md` → für Jarvis **read-only**. So kann Jarvis CEO-GPTs kuratiertes Wissen niemals überschreiben.
- Neue Erkenntnisse, die Jarvis selbst festhält (z. B. aus einem Gespräch), landen in `vault/00-inbox/`. Du (via CEO-GPT) entscheidest, was davon ins kuratierte `context/` wandert.

**Code-Änderungen (klein, additiv):**
- `config.py`: neue Variablen `JARVIS_BRAIN_DIR`, `JARVIS_CONTEXT_DIR` (= `brain/context`), `JARVIS_METRICS_FILE` (= `brain/key-metrics.md`), `JARVIS_VAULT_DIR` (= `brain/vault`).
- `memory/context_source.py` (neu): liest `context/*.md` schreibgeschützt ein, indexiert sie beim Start in den bestehenden `VectorIndex`, sodass `memory_search` **auch** CEO-GPT-Wissen findet.
- `memory/metrics.py` (neu): defensiver Parser für `key-metrics.md` → `dict` (z. B. `{"mrr_eur": 190, "kunden": 7}`); tolerant gegenüber fehlenden/umbenannten Feldern.
- `tools/metrics_tool.py` (neu): Tool `metrics_read` (Effekt `READ`, Tier 0) → aktuelle Kennzahlen als Text.
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

Ein vom Anfrage-Loop **getrennter** Auslöser-Mechanismus: `core/proactive.py`.

- **Zeitgesteuert:** Morgenbegrüßung (z. B. 08:00) → gesprochene Zusammenfassung aus `key-metrics.md` (MRR, Kundenzahl) + Zahl neuer ungelesener Mails.
- **Ereignisgesteuert:** Polling alle N Minuten über Gmail (`readonly`) → „Es sind 3 neue Kunden-Mails."

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

## 9. Offene Fragen (bevor `/implement` laufen kann)

1. **CEO-GPT real:** Kannst du das echte `context/`-Layout und das **Format von `key-metrics.md`** teilen (Beispieldatei)? Der Reader braucht das reale Format — sonst rate ich.
2. **Pfad:** Wo soll der gemeinsame `brain/`-Ordner liegen? (Vorschlag `C:\Jarvis\brain`)
3. **Schreibrechte:** Darf Jarvis in `context/` **schreiben** (Erkenntnisse anhängen), oder strikt read-only dort und schreiben nur in `vault/`?
4. **Proaktive Trigger v1:** Welche willst du zuerst? (Morgenbegrüßung? Neue-Mail-Hinweis? ConsentFlow-MRR-Änderung?)
5. **Wake-Word:** openWakeWords vortrainiertes „hey jarvis" (zwei Wörter) — oder ein eigen-trainiertes einzelnes „Jarvis" (braucht Sprach-Samples von dir)?
6. **Autostart:** Soll der Dauer-Hörprozess automatisch beim Windows-Login starten?
7. **Repo-Struktur:** Soll die CEO-GPT-Integration im bestehenden `jarvis_local/`-Projekt wachsen, oder willst du CEO-GPT als eigenes Verzeichnis im Repo?

---
*Nur Planungsdokument. Umsetzung erst nach Klärung der offenen Fragen und Phase-0-Abnahme.*
