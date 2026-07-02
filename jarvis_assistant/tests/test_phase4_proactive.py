"""Phase 4: proaktive Scheduler-Engine + Briefing (offline, mit Fake-Uhr)."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis.proactive import (  # noqa: E402
    Check, ProactiveEngine, compose_morning_briefing, disk_space_check,
)


def test_interval_check_due_logic():
    c = Check("t", func=lambda: "x", kind="interval", interval_s=100)
    now = datetime(2026, 7, 2, 12, 0, 0)
    assert ProactiveEngine._due(c, now) is True          # noch nie gelaufen
    ProactiveEngine._mark(c, now)
    assert ProactiveEngine._due(c, now) is False         # gerade gelaufen
    later = datetime(2026, 7, 2, 12, 2, 0)               # +120 s
    assert ProactiveEngine._due(c, later) is True


def test_daily_check_fires_once_after_time():
    c = Check("morning", func=lambda: "briefing", kind="daily", at="08:00")
    before = datetime(2026, 7, 2, 7, 59)
    at_time = datetime(2026, 7, 2, 8, 0)
    assert ProactiveEngine._due(c, before) is False
    assert ProactiveEngine._due(c, at_time) is True
    ProactiveEngine._mark(c, at_time)
    later_same_day = datetime(2026, 7, 2, 9, 0)
    assert ProactiveEngine._due(c, later_same_day) is False   # nur einmal am Tag
    next_day = datetime(2026, 7, 3, 8, 1)
    assert ProactiveEngine._due(c, next_day) is True          # am Folgetag wieder


def test_run_once_notifies_only_returning_checks():
    sent = []
    eng = ProactiveEngine(notifier=sent.append)
    eng.add(Check("silent", func=lambda: None, kind="interval", interval_s=0))
    eng.add(Check("loud", func=lambda: "Hinweis!", kind="interval", interval_s=0))
    msgs = eng.run_once(datetime(2026, 7, 2, 12, 0))
    assert msgs == ["Hinweis!"] and sent == ["Hinweis!"]


def test_morning_briefing_composition():
    txt = compose_morning_briefing(
        city="Hamburg",
        weather_fn=lambda: "In Hamburg 18 Grad, teils bewölkt.",
        calendar_fn=lambda: "Heute: Team-Call.",
        user_name="Jonas")
    assert txt.startswith("Guten Morgen, Jonas.")
    assert "Hamburg" in txt and "Team-Call" in txt


def test_disk_space_check_only_warns_when_low(monkeypatch=None):
    from jarvis.skills import system_health
    # viel Platz → keine Meldung
    system_health.free_gb = lambda path=None: 500.0
    assert disk_space_check(threshold_gb=15) is None
    # wenig Platz → Warnung
    system_health.free_gb = lambda path=None: 5.0
    msg = disk_space_check(threshold_gb=15)
    assert msg and "GB frei" in msg


def test_check_exception_does_not_crash_engine():
    def boom():
        raise RuntimeError("kaputt")
    eng = ProactiveEngine(notifier=lambda m: None)
    eng.add(Check("boom", func=boom, kind="interval", interval_s=0))
    assert eng.run_once(datetime(2026, 7, 2, 12, 0)) == []   # geschluckt, kein Crash


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn(); print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1; print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
