"""Phase 6/7: Weckwort-Grundgerüst + Erweiterungs-Beispiele (offline)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis import skills                       # noqa: E402
from jarvis.security import Risk                 # noqa: E402
from jarvis.skills.marketing import draft_marketing_text  # noqa: E402
from jarvis.wakeword import WakeWordListener     # noqa: E402


def test_wakeword_listener_degrades_gracefully():
    # Ohne openwakeword/sounddevice: available() False, start() False — kein Crash.
    wl = WakeWordListener(on_wake=lambda: None, wakeword="jarvis")
    assert wl.available() in (True, False)
    if not wl.available():
        assert wl.start() is False


def test_marketing_draft_is_prepare_only_level1():
    assert skills.get("draft_marketing_text").risk == Risk.AUTO
    out = draft_marketing_text("Cargo Jeans", benefit="bequem und trendy", tone="verknappt")
    assert "Cargo Jeans" in out
    assert "#CargoJeans" in out
    assert "nicht veröffentlicht" in out.lower()  # bereitet nur vor


def test_research_skill_registered():
    sk = skills.get("research_product")
    assert sk is not None and sk.risk == Risk.AUTO


def test_full_skill_catalog_present():
    names = {s.name for s in skills.all_skills()}
    expected = {
        # Phase 1
        "open_app", "web_search", "read_file", "weather", "calendar_today",
        # Phase 2
        "remember_fact", "recall_facts", "forget_fact",
        # Phase 3
        "list_dir", "write_file", "delete_file", "list_processes", "close_process",
        "browse_page", "screenshot", "read_screen",
        "gmail_list_unread", "gmail_prepare_draft", "gmail_send",
        # Phase 4
        "disk_space", "system_status",
        # Phase 5
        "shop_summary", "shop_alerts",
        # Phase 7
        "draft_marketing_text", "research_product",
    }
    missing = expected - names
    assert not missing, f"Fehlende Skills: {missing}"


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
