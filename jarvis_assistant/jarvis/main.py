"""Einstiegspunkt: verdrahtet Hotkey → STT → Assistent(+Tools) → TTS.

Zwei Modi:
  python -m jarvis.main            Sprach-Modus (Hotkey, Mikro, Stimme)
  python -m jarvis.main --text     Text-Modus (Tastatur/Konsole, kein Mikro)

Der Text-Modus ist zugleich der Fallback und macht den Kern überall lauffähig.
"""

from __future__ import annotations

import sys
import threading

from . import skills
from .assistant import Assistant
from .audit import audit, log, setup as audit_setup
from .config import Config
from .llm import OllamaClient
from .security import Guard, Risk, console_confirmer
from .stt import ConsoleRecognizer, WhisperRecognizer
from .tts import ConsoleSpeaker, ElevenLabsSpeaker


def _apply_config_to_skills(cfg: Config) -> None:
    """Config-Werte in die Skill-Module spiegeln (Ort, Kalenderpfad)."""
    from .skills import weather as w
    from .skills import calendar_local as c
    w.DEFAULT_CITY = cfg.city
    c.CALENDAR_PATH = cfg.calendar_file
    # Phase 3: Bildschirm (Vision) und Gmail-Datenordner
    try:
        from .skills import screen as s
        s.OLLAMA_URL = cfg.ollama_url
    except Exception:  # noqa: BLE001
        pass
    try:
        from .skills import email_gmail as e
        e.DATA_DIR = cfg.data_dir
    except Exception:  # noqa: BLE001
        pass
    # Phase 5: Shopify
    try:
        from .skills import shop_watch as sw
        sw.configure(cfg.shopify_domain, cfg.shopify_token)
    except Exception:  # noqa: BLE001
        pass


def _build_memory(cfg: Config):
    try:
        from .memory import Memory  # Phase 2 (optional)
        mem = Memory(cfg.memory_db)
        # Speicher auch den Gedächtnis-Skills bekannt machen.
        from .skills import memory_skills
        memory_skills.MEMORY = mem
        return mem
    except Exception:  # noqa: BLE001
        return None


def _make_assistant(cfg: Config, guard: Guard) -> Assistant:
    llm = OllamaClient(cfg.model, cfg.ollama_url, cfg.temperature)
    return Assistant(llm, guard=guard, user_name=cfg.user_name,
                     memory=_build_memory(cfg))


def run_text() -> None:
    cfg = Config.load()
    cfg.ensure_dirs()
    audit_setup(cfg.log_file)
    _apply_config_to_skills(cfg)
    log(f"Jarvis (Text-Modus). Modell={cfg.model}. Skills: "
        f"{', '.join(s.name for s in skills.all_skills())}")
    guard = Guard(confirmer=console_confirmer)
    assistant = _make_assistant(cfg, guard)
    speaker = ConsoleSpeaker()
    recog = ConsoleRecognizer()
    print("Tippe deine Nachricht (oder 'exit'):")
    while True:
        text = recog.listen()
        if text.lower() in ("exit", "quit", "ende", "tschüss"):
            speaker.say("Bis später, Sir.")
            break
        if not text:
            continue
        speaker.say(assistant.handle(text))


def run_voice() -> None:
    cfg = Config.load()
    cfg.ensure_dirs()
    audit_setup(cfg.log_file)
    _apply_config_to_skills(cfg)

    speaker = ElevenLabsSpeaker(cfg.elevenlabs_api_key, cfg.elevenlabs_voice_id,
                                cfg.tts_fallback)
    recog = WhisperRecognizer(cfg.whisper_model, cfg.language, cfg.silence_stop_ms)

    # Sprach-Bestätiger: Stufe 2/3 werden vorgelesen und per Stimme bestätigt.
    def voice_confirmer(prompt: str, risk: Risk) -> bool:
        speaker.say(prompt + (" Bitte sage ausdrücklich ja."
                              if risk == Risk.EXPLICIT else " Soll ich?"))
        answer = recog.listen().lower()
        return "ja" in answer

    guard = Guard(confirmer=voice_confirmer)
    assistant = _make_assistant(cfg, guard)

    def on_talk() -> None:
        text = recog.listen()
        if not text:
            return
        log(f"Verstanden: {text}")
        speaker.say(assistant.handle(text))

    stop = threading.Event()

    def on_panic() -> None:
        log("NOT-AUS ausgelöst.", "warning")
        speaker.say("Ich stoppe, Sir.")
        stop.set()

    from .hotkey import HotkeyManager
    hk = HotkeyManager(cfg.hotkey, cfg.panic_hotkey)
    if not hk.register(on_talk, on_panic):
        log("Kein globaler Hotkey möglich — wechsle in den Text-Modus.")
        return run_text()

    speaker.say(f"Jarvis ist bereit, {cfg.user_name}. "
                f"Drücke {cfg.hotkey}, um mit mir zu sprechen.")
    log(f"Sprach-Modus aktiv. Push-to-Talk: {cfg.hotkey}, Not-Aus: {cfg.panic_hotkey}")

    # Optionales Tray-Icon (blockiert, wenn vorhanden); sonst auf Stop warten.
    try:
        from .tray import Tray
        tray = Tray(on_quit=stop.set)
        if not tray.run():
            stop.wait()
    except Exception:  # noqa: BLE001
        stop.wait()


def main() -> None:
    if "--text" in sys.argv:
        run_text()
    else:
        run_voice()


if __name__ == "__main__":
    main()
