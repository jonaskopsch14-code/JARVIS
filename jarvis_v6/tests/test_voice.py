"""Tests for the voice / conversation module ("Telefon-Modus").

The dialogue engine is a pure function of (utterance, injected providers), so it
is tested fully offline with fakes — no microphone, no network, no API key.
A small live HTTP smoke test exercises the /api/voice endpoint. Standard
library only.
"""

import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voice import VoiceBrain, normalize  # noqa: E402
from webapp import create_server  # noqa: E402


# ---------------------------------------------------------------------------
# Fakes / helpers.
# ---------------------------------------------------------------------------
def make_brain(state="idle", running=False, briefing="", dry_run=True,
               counts=None, started=True, preflight_rows=None):
    counts = counts if counts is not None else {"leads": 0, "winners": 0,
                                                "suppliers": 0, "drafts": 0}
    calls = {"start": 0}

    def status_fn():
        return {"state": state, "running": running, "briefing": briefing,
                "dry_run": dry_run, "wake_hour": 16, "wake_minute": 0,
                "counts": counts}

    def start_fn():
        calls["start"] += 1
        return started

    def preflight_fn():
        return {"rows": preflight_rows or []}

    brain = VoiceBrain(status_fn=status_fn, start_fn=start_fn,
                       preflight_fn=preflight_fn,
                       _now=lambda: dt.datetime(2026, 6, 26, 14, 30))
    return brain, calls


# ---------------------------------------------------------------------------
# Normalisation.
# ---------------------------------------------------------------------------
def test_normalize_folds_umlauts_and_punctuation():
    assert normalize("Lieferanten?") == "lieferanten"
    assert normalize("Wie VIEL Uhr ist es!") == "wie viel uhr ist es"
    assert normalize("Entwürfe & Größe") == "entwuerfe groesse"
    assert normalize("   ") == ""


# ---------------------------------------------------------------------------
# Intents.
# ---------------------------------------------------------------------------
def test_greeting_intent():
    brain, _ = make_brain()
    assert brain.reply("Hallo JARVIS").intent == "greeting"


def test_status_reports_state_and_mode():
    brain, _ = make_brain(state="night_shift", dry_run=True)
    r = brain.reply("Wie ist der Status?")
    assert r.intent == "status"
    assert "Nachtschicht" in r.text
    assert "Dry-Run" in r.text


def test_start_triggers_action_and_calls_provider():
    brain, calls = make_brain(started=True)
    r = brain.reply("Starte die Nachtschicht")
    assert r.intent == "start"
    assert r.action == "started"
    assert calls["start"] == 1


def test_start_when_already_running():
    brain, calls = make_brain(started=False)
    r = brain.reply("Starte das Protokoll")
    assert r.intent == "start_already"
    assert r.action is None
    assert calls["start"] == 1


def test_goodbye_ends_the_call():
    brain, _ = make_brain()
    r = brain.reply("Tschüss")
    assert r.intent == "goodbye"
    assert r.end is True


def test_counts_overall_and_single_section():
    brain, _ = make_brain(counts={"leads": 1, "winners": 2, "suppliers": 0, "drafts": 3})
    overall = brain.reply("Gib mir die Zahlen vom Dashboard")
    assert overall.intent == "counts"
    assert "ein Lead" in overall.text          # singular form
    assert "zwei Winning Products" in overall.text

    leads = brain.reply("Wie viele Leads?")
    assert leads.intent == "counts_leads"
    assert "ein Lead" in leads.text


def test_briefing_present_and_empty():
    brain, _ = make_brain(briefing="Alles erledigt, Jonas.")
    assert brain.reply("Gib mir das Briefing").text == "Alles erledigt, Jonas."
    empty, _ = make_brain(briefing="")
    assert empty.reply("Briefing bitte").intent == "briefing_empty"


def test_wake_time_uses_config():
    brain, _ = make_brain()
    r = brain.reply("Wann ist die Weckzeit?")
    assert r.intent == "wake"
    assert "16:00" in r.text


def test_safety_mode():
    dry, _ = make_brain(dry_run=True)
    assert dry.reply("Sind wir im Sicherheitsmodus?").intent == "safety"
    live, _ = make_brain(dry_run=False)
    assert live.reply("Sind wir scharf?").intent == "safety_live"


def test_preflight_ok_and_fail():
    ok, _ = make_brain(preflight_rows=[{"capability": "Mailbox", "status": "READY", "detail": ""}])
    assert ok.reply("Mach einen Preflight").intent == "preflight_ok"
    bad, _ = make_brain(preflight_rows=[
        {"capability": "Mailbox", "status": "FAIL", "detail": "no host"},
        {"capability": "Store", "status": "READY", "detail": ""}])
    r = bad.reply("Bist du bereit?")
    assert r.intent == "preflight_fail"
    assert "Mailbox" in r.text


def test_clock_uses_injected_now():
    brain, _ = make_brain()
    r = brain.reply("Wie spät ist es?")
    assert r.intent == "clock"
    assert "14:30" in r.text


def test_help_and_fallback():
    brain, _ = make_brain()
    assert brain.reply("Was kannst du?").intent == "help"
    assert brain.reply("asdf qwerty zzz").intent == "fallback"
    assert brain.reply("").intent == "empty"


def test_llm_fallback_used_only_when_no_intent():
    brain, _ = make_brain()
    brain.llm_fn = lambda q: f"LLM: {q}"
    # A built-in intent must still win over the LLM.
    assert brain.reply("Status?").intent == "status"
    # Unmatched input falls through to the LLM.
    r = brain.reply("Erzähl mir einen Witz")
    assert r.intent == "llm"
    assert r.text.startswith("LLM:")


# ---------------------------------------------------------------------------
# Live HTTP smoke test against /api/voice.
# ---------------------------------------------------------------------------
def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def _post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return r.status, json.loads(r.read().decode("utf-8"))


def test_voice_endpoint_roundtrip():
    httpd, _app = create_server(host="127.0.0.1", port=0)
    import threading
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    try:
        host, port = httpd.server_address
        base = f"http://{host}:{port}"

        code, greet = _get(f"{base}/api/voice")
        assert code == 200 and greet["intent"] == "greeting"
        assert "JARVIS" in greet["reply"]

        code, reply = _post(f"{base}/api/voice", {"text": "Wie ist der Status?"})
        assert code == 200 and reply["intent"] == "status"
        assert reply["end"] is False

        code, bye = _post(f"{base}/api/voice", {"text": "Auflegen"})
        assert bye["intent"] == "goodbye" and bye["end"] is True
    finally:
        httpd.shutdown()
