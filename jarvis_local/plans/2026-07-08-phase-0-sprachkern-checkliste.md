# Phase 0 — Sprach-Kern auf dem Windows-PC zum Laufen bringen

**Ziel:** Beweisen, dass die lokale Sprachkette läuft — Hotkey → Whisper → Qwen3-8B → Piper, flüssig auf Deutsch. **Erst wenn du das abnimmst, wird Phase 1 (CEO-GPT-Integration) gebaut.**

**Zielhardware:** Windows-PC, RTX 2080 Super (8 GB VRAM), Mikrofon.
**Aufteilung (Entscheidung #6):** Qwen3-8B auf der GPU, **Whisper `medium` auf der CPU**, Piper + Wake-Word ohnehin CPU.

> Reihenfolge: Punkte **0–5 einzeln** abarbeiten und je mit dem Test-Schnipsel prüfen. Erst wenn alle vier Bausteine einzeln laufen, den **Gesamt-Loop** (Punkt 6) starten.

---

## 0. Voraussetzungen prüfen

```powershell
python --version        # muss 3.11.x sein
nvidia-smi              # zeigt die RTX 2080 Super + Treiber; VRAM ~8 GB
```
- [ ] Python 3.11 vorhanden
- [ ] NVIDIA-Treiber aktuell, `nvidia-smi` funktioniert
- [ ] Ein Mikrofon ist angeschlossen und in den Windows-Sound-Einstellungen als Standard-Eingabe gesetzt
- [ ] Repo lokal, im Ordner `jarvis_local`:
  ```powershell
  cd <pfad>\jarvis_local
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

---

## 1. Ollama + qwen3:8b

1. **Ollama für Windows** installieren: <https://ollama.com/download> → Installer ausführen (startet den Dienst automatisch).
2. Modell ziehen und testen:
   ```powershell
   ollama pull qwen3:8b
   ollama run qwen3:8b "Antworte in einem kurzen deutschen Satz: Wer bist du?"
   ```
3. VRAM-Belegung prüfen (soll fast komplett auf der GPU liegen):
   ```powershell
   ollama ps        # Spalte PROCESSOR sollte "GPU" zeigen, SIZE ~6 GB
   ```

**Test aus Jarvis heraus** (nutzt die echte `OllamaBackend`-Klasse):
```powershell
python -c "from jarvis.core.llm import OllamaBackend; b=OllamaBackend('qwen3:8b'); print(b.chat([{'role':'user','content':'Antworte kurz auf Deutsch: Wie geht es dir?'}])['content'])"
```
- [ ] Ollama läuft, `qwen3:8b` antwortet auf Deutsch
- [ ] `ollama ps` zeigt GPU-Nutzung, SIZE ~6 GB (Rest der 8 GB bleibt frei)

---

## 2. Python-Abhängigkeiten für den Sprach-Kern

Nur die vier Kern-Bausteine (Gmail/Web brauchst du in Phase 0 **nicht**):
```powershell
pip install ollama faster-whisper sounddevice numpy piper-tts pynput
```
- [ ] Installation ohne Fehler (bei `sounddevice` ggf. „Microsoft C++ Build Tools" nötig)

---

## 3. Spracheingabe — faster-whisper `medium` auf CPU

`faster-whisper` lädt das Modell beim ersten Lauf selbst herunter (~1,5 GB). Für **CPU** ist `compute_type="int8"` richtig (nicht `float16` — das ist GPU-only).

**Test** (5 s aufnehmen, transkribieren):
```powershell
python -c "from jarvis.voice.stt import WhisperSTT; s=WhisperSTT('medium','cpu',compute_type='int8'); print('Sprich jetzt 5 Sekunden deutsch...'); print('Erkannt:', s.transcribe(s.record(5)))"
```
- [ ] Deutscher Satz wird korrekt (oder nahezu) transkribiert
- [ ] Dauer der Transkription notieren (für die < 2-s-Bewertung später). Ist CPU zu langsam → **erst dann** GPU testen: `WhisperSTT('medium','cuda',compute_type='float16')` und `ollama ps` / `nvidia-smi` auf VRAM-Überlauf prüfen. Nie Qwen **und** großes Whisper gleichzeitig auf der GPU quetschen.

---

## 4. Sprachausgabe — Piper mit Thorsten-Stimme

1. Deutsches **Thorsten-high**-Modell laden (zwei Dateien) aus `rhasspy/piper-voices` auf Hugging Face:
   `de/de_DE/thorsten/high/de_DE-thorsten-high.onnx` **und** die zugehörige `...onnx.json`.
   Beide in einen Ordner legen, z. B. `C:\Jarvis\voices\`.
2. **Test:**
   ```powershell
   python -c "from jarvis.voice.tts import PiperTTS; PiperTTS(r'C:\Jarvis\voices\de_DE-thorsten-high.onnx').say('Hallo Jonas, ich bin Jarvis. Der Sprach-Kern läuft.')"
   ```
- [ ] Du hörst einen natürlichen deutschen Satz (erster Ton fast sofort)
- [ ] Pfad zum `.onnx` gemerkt → kommt gleich in `JARVIS_PIPER_MODEL`

---

## 5. Hotkey (Push-to-Talk, `Strg+Alt+J`)

**Test:**
```powershell
python -c "import time; from jarvis.voice.hotkey import PushToTalk; p=PushToTalk(lambda: print('>>> HOTKEY AKTIVIERT')); p.start(); print('Druecke Strg+Alt+J (20 s Zeit)...'); time.sleep(20)"
```
- [ ] Beim Drücken von `Strg+Alt+J` erscheint `>>> HOTKEY AKTIVIERT`
  *(Hinweis: globale Hotkeys brauchen unter Windows ggf. ein Terminal „als Administrator".)*

---

## 6. Gesamter Sprach-Loop

Umgebungsvariablen setzen (CPU-Whisper `medium`, Piper-Pfad):
```powershell
$env:JARVIS_WHISPER_DEVICE="cpu"
$env:JARVIS_WHISPER_MODEL="medium"
$env:JARVIS_PIPER_MODEL="C:\Jarvis\voices\de_DE-thorsten-high.onnx"
$env:JARVIS_DATA_DIR="C:\Jarvis\data"
python -m jarvis.main voice
```
Dann sprechen (z. B. „Merke dir: Kunde Meier mag einen blauen Banner"), Jarvis antwortet per Stimme.

> ⚠️ **Eine kleine Kern-Anpassung ist hier nötig** (kein Integrations-Code, gehört zu Phase 0): `main.run_voice` baut das STT aktuell ohne `compute_type` → Default `float16`, das läuft **nicht** auf CPU. Für den CPU-Pfad muss `compute_type="int8"` durchgereicht werden (1 Zeile). **Sag mir Bescheid, sobald du bei Punkt 6 bist — dann setze ich diese eine Zeile (plus optional eine `JARVIS_WHISPER_COMPUTE`-Variable) und pushe sie.** Punkte 1–5 laufen ohne diese Änderung.

---

## Abnahmekriterien (das nimmst du ab)

- [ ] **Ollama:** `qwen3:8b` antwortet auf Deutsch, läuft auf der GPU (~6 GB).
- [ ] **STT:** Whisper `medium` transkribiert deutsche Sprache brauchbar; Latenz notiert.
- [ ] **TTS:** Piper spricht Thorsten-Stimme natürlich, erster Ton schnell.
- [ ] **Hotkey:** `Strg+Alt+J` löst zuverlässig aus.
- [ ] **Gesamt-Loop:** ein voller Durchlauf Sprache-rein → Antwort-raus in **spürbar < 2 s nach STT** und flüssig auf Deutsch.
- [ ] **Gateway-Beweis:** Sag „Kaufe ein Fachbuch für 20 Euro" → Jarvis **fragt vor Ausführung nach Freigabe** (die Geld-Regel greift auch per Stimme).

**Wenn diese Punkte grün sind → melde „Phase 0 abgenommen".** Dann (und erst dann) baue ich Phase 1 (Datenbrücke).

---

## Troubleshooting (Kurzreferenz)

| Symptom | Ursache / Fix |
|---|---|
| `faster-whisper`: `float16` Fehler auf CPU | `compute_type="int8"` verwenden (siehe Punkt 3/6). |
| STT extrem langsam | CPU-Last; kleineres Modell (`base`/`small`) testen oder GPU-`medium` (VRAM prüfen!). |
| `ollama ps` zeigt „CPU" statt „GPU" | GPU-Layer nicht ausgelagert → Ollama/Treiber neu starten; VRAM frei? |
| VRAM-Überlauf (langsam, „spill") | Whisper auf CPU lassen; Qwen-Kontext `JARVIS_NUM_CTX=16384` nicht erhöhen. |
| Piper findet Stimme nicht | absoluter Pfad zur `.onnx`; die `.onnx.json` muss daneben liegen. |
| Hotkey reagiert nicht | Terminal „als Administrator" starten; anderes Programm belegt den Hotkey? |
| Kein Mikrofon-Signal | in Windows Standard-Eingabegerät setzen; `python -c "import sounddevice as sd; print(sd.query_devices())"`. |

---

## Kleine Kern-Anpassungen, die ich auf dein Signal mache (kein Integrations-Code)
1. **CPU-`compute_type`** in `main.run_voice` durchreichen + optional `JARVIS_WHISPER_COMPUTE`-Variable (Punkt 6).
2. *(optional)* Piper-Stimmen-Autodownload-Hinweis / Pfad-Prüfung beim Start mit klarer Fehlermeldung.

Beides ist Phase-0-Enablement (Sprach-Kern), **nicht** die CEO-GPT-Integration — die bleibt bis zur Abnahme unberührt.
