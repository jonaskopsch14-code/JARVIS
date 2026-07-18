"""Offline tests for the briefing skill.

The network parts (news, inbox) are injected fakes, so the composition — equal
weighting of both sources, the item cap and the spoken Jarvis tone — is verified
without any network or IMAP. Standard library only.
"""

import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integrations.briefing import (  # noqa: E402
    BriefItem, BriefingConfig, briefing_compile, compose_briefing,
)

NOON = dt.datetime(2026, 7, 18, 9, 0)


def _news(n):
    return [BriefItem("news", f"Schlagzeile {i}", detail=f"Quelle {i}") for i in range(n)]


def _inbox(n):
    return [BriefItem("inbox", f"Betreff {i}", detail=f"absender{i}@example.com")
            for i in range(n)]


# ---------------------------------------------------------------------------
# Composition core.
# ---------------------------------------------------------------------------
def test_empty_sources_still_addresses_jonas():
    text = compose_briefing([], [], now=NOON)
    assert "Jonas" in text and "nichts Neues" in text


def test_both_sources_equal_weight_and_capped():
    text = compose_briefing(_news(5), _inbox(5), max_items=4, now=NOON)
    # Interleaved 1:1, capped at 4 => 2 news + 2 inbox.
    assert "Schlagzeile 0" in text and "Schlagzeile 1" in text
    assert "Schlagzeile 2" not in text
    assert "Betreff 0" in text and "Betreff 1" in text
    assert "Betreff 2" not in text


def test_tone_addresses_and_greets_by_time():
    morning = compose_briefing(_news(1), [], now=dt.datetime(2026, 7, 18, 8, 0))
    assert morning.startswith("Guten Morgen, Jonas.")
    evening = compose_briefing(_news(1), [], now=dt.datetime(2026, 7, 18, 20, 0))
    assert evening.startswith("Guten Abend, Jonas.")


def test_inbox_item_names_sender():
    text = compose_briefing([], _inbox(1), now=NOON)
    assert "absender0@example.com" in text and "Postfach" in text


def test_news_only_when_inbox_empty():
    text = compose_briefing(_news(2), [], now=NOON)
    assert "Nachrichten" in text and "Postfach" not in text


# ---------------------------------------------------------------------------
# briefing_compile end-to-end with injected fetchers.
# ---------------------------------------------------------------------------
def test_compile_uses_injected_fetchers_no_network():
    cfg = BriefingConfig(topics=["Tech"], max_items=6, user="Jonas")
    text = briefing_compile(
        ["news", "inbox"], config=cfg, now=NOON,
        news_fetcher=lambda topics, limit: _news(3),
        inbox_fetcher=lambda limit: _inbox(3),
    )
    assert "Schlagzeile 0" in text and "Betreff 0" in text


def test_compile_respects_selected_sources_only():
    cfg = BriefingConfig(topics=["Tech"], max_items=6)
    text = briefing_compile(
        ["news"], config=cfg, now=NOON,
        news_fetcher=lambda topics, limit: _news(2),
        inbox_fetcher=lambda limit: (_ for _ in ()).throw(AssertionError("inbox darf nicht laufen")),
    )
    assert "Schlagzeile 0" in text and "Postfach" not in text


def test_compile_survives_a_failing_source():
    cfg = BriefingConfig(topics=["Tech"], max_items=6)
    text = briefing_compile(
        ["news", "inbox"], config=cfg, now=NOON,
        news_fetcher=lambda topics, limit: (_ for _ in ()).throw(RuntimeError("news down")),
        inbox_fetcher=lambda limit: _inbox(2),
    )
    # News blew up; the briefing still speaks the inbox items.
    assert "Betreff 0" in text


# ---------------------------------------------------------------------------
# Config loading.
# ---------------------------------------------------------------------------
def test_config_from_env_topics_win():
    cfg = BriefingConfig.load(env={"JARVIS_BRIEFING_TOPICS": "A, B ,C"})
    assert cfg.topics == ["A", "B", "C"]


def test_config_from_json_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "briefing.json"
        p.write_text(json.dumps({"topics": ["Wirtschaft"], "max_items": 5}), encoding="utf-8")
        cfg = BriefingConfig.load(env={"JARVIS_BRIEFING_CONFIG": str(p)})
        assert cfg.topics == ["Wirtschaft"] and cfg.max_items == 5


def test_config_defaults_when_unset():
    cfg = BriefingConfig.load(env={})
    assert cfg.topics  # non-empty sensible default
    assert cfg.max_items == 10


if __name__ == "__main__":
    funcs = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in funcs:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(funcs) - failed}/{len(funcs)} passed")
    sys.exit(1 if failed else 0)
