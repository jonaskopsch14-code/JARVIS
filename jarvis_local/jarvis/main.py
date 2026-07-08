"""Jarvis – Einstiegspunkt (CLI).

Modi:
  python -m jarvis.main chat            # Text-Dialog gegen lokales Qwen (Ollama)
  python -m jarvis.main chat --demo     # Text-Dialog ohne LLM (regelbasiertes Demo-Backend)
  python -m jarvis.main voice           # Sprach-Dialog (Whisper + Piper + Hotkey) – Windows-PC
  python -m jarvis.main approvals       # offene Tier-1-Freigaben anzeigen
  python -m jarvis.main approve <id>    # Freigabe erteilen
  python -m jarvis.main deny <id>       # Freigabe ablehnen
"""
from __future__ import annotations

import argparse
import sys

from .app import build_app
from .config import Config
from .core.demo_backend import demo_responder
from .core.llm import LLMBackend, OllamaBackend, ScriptedBackend
from .security.permission_gateway import Action


# ---------- Approver (Mensch bestätigt Tier-1-Aktionen) ----------
def console_approver(action: Action) -> bool:
    print("\n⏸  FREIGABE ERFORDERLICH (Tier 1)")
    print(f"    Aktion:   {action.tool}")
    print(f"    Absicht:  {action.intent}")
    if action.effect.value == "spend":
        print("    ⚠️  Diese Aktion gibt Geld aus.")
    if action.expected_result:
        print(f"    Wirkung:  {action.expected_result}")
    answer = input("    Freigeben? [j/N]: ").strip().lower()
    return answer in ("j", "ja", "y", "yes")


# ---------- Text-Dialog ----------
def run_chat(config: Config, backend: LLMBackend, *, persist: bool) -> None:
    app = build_app(config, backend, persist=persist)
    print("Jarvis ist bereit. Beenden mit 'exit' oder Strg+D.\n")
    while True:
        try:
            user = input("Du: ").strip()
        except EOFError:
            print()
            break
        if not user:
            continue
        if user.lower() in ("exit", "quit", "beenden", "tschüss"):
            break
        result = app.agent.run(user, approver=console_approver)
        print(f"Jarvis: {result.reply}")
        if result.pending_approvals:
            print(f"   (offene Freigaben: {', '.join(result.pending_approvals)})")


# ---------- Sprach-Dialog (Windows-PC) ----------
def run_voice(config: Config) -> None:  # pragma: no cover - benötigt Audio/GPU
    from .voice.stt import WhisperSTT
    from .voice.tts import PiperTTS, speak_streaming

    backend = OllamaBackend(config.ollama_model, config.ollama_host, config.temperature, config.num_ctx)
    app = build_app(config, backend, persist=True)
    stt = WhisperSTT(config.whisper_model, config.whisper_device, compute_type=config.whisper_compute)
    tts = PiperTTS(config.piper_model)

    def voice_approver(action: Action) -> bool:
        tts.say(f"Freigabe nötig: {action.intent}. Soll ich das tun?")
        answer = stt.listen().lower()
        return "ja" in answer

    print("Sprach-Modus aktiv (Push-to-Talk-Integration siehe voice/hotkey.py). Strg+C beendet.")
    try:
        while True:
            print("… höre zu (record) …")
            user = stt.listen()
            if not user:
                continue
            print(f"Du: {user}")
            result = app.agent.run(user, approver=voice_approver)
            speak_streaming(tts, result.reply)
    except KeyboardInterrupt:
        print("\nBeendet.")


# ---------- Freigabe-Verwaltung (durable, out-of-band) ----------
def run_approvals(config: Config) -> None:
    app = build_app(config, ScriptedBackend(scripted=[]), persist=True)
    pending = app.gateway.list_pending()
    if not pending:
        print("Keine offenen Freigaben.")
        return
    for p in pending:
        print(f"[{p['id']}] {p['effect'].upper()}  {p['intent']}")


def decide(config: Config, approval_id: str, approve: bool) -> None:
    app = build_app(config, ScriptedBackend(scripted=[]), persist=True)
    if app.gateway.get(approval_id) is None:
        print(f"Unbekannte Freigabe-ID: {approval_id}")
        sys.exit(1)
    if approve:
        app.gateway.approve(approval_id)
        print(f"Freigegeben: {approval_id}")
    else:
        app.gateway.deny(approval_id, reason="per CLI abgelehnt")
        print(f"Abgelehnt: {approval_id}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="jarvis", description="Lokaler Sprachassistent Jarvis")
    sub = parser.add_subparsers(dest="cmd")

    p_chat = sub.add_parser("chat", help="Text-Dialog")
    p_chat.add_argument("--demo", action="store_true", help="ohne LLM, regelbasiertes Demo-Backend")
    p_chat.add_argument("--no-persist", action="store_true", help="In-Memory statt Dateien (für Tests)")

    sub.add_parser("voice", help="Sprach-Dialog (Windows-PC)")
    sub.add_parser("approvals", help="offene Tier-1-Freigaben anzeigen")
    p_ap = sub.add_parser("approve", help="Freigabe erteilen"); p_ap.add_argument("id")
    p_dn = sub.add_parser("deny", help="Freigabe ablehnen"); p_dn.add_argument("id")

    args = parser.parse_args(argv)
    config = Config.from_env()
    cmd = args.cmd or "chat"

    if cmd == "chat":
        demo = getattr(args, "demo", False)
        backend: LLMBackend = ScriptedBackend(responder=demo_responder) if demo else OllamaBackend(
            config.ollama_model, config.ollama_host, config.temperature, config.num_ctx
        )
        run_chat(config, backend, persist=not getattr(args, "no_persist", False))
    elif cmd == "voice":
        run_voice(config)
    elif cmd == "approvals":
        run_approvals(config)
    elif cmd == "approve":
        decide(config, args.id, approve=True)
    elif cmd == "deny":
        decide(config, args.id, approve=False)


if __name__ == "__main__":
    main()
