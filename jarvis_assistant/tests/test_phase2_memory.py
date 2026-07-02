"""Phase 2: Gedächtnis über Sitzungen + Merk-Skills (offline)."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis.memory import Memory                # noqa: E402
from jarvis.assistant import Assistant          # noqa: E402
from jarvis.llm import ScriptedLLM              # noqa: E402
from jarvis.security import Guard               # noqa: E402


def test_facts_persist_across_instances():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "m.sqlite3"
        m = Memory(db); m.remember("lieblingsfarbe", "blau"); m.close()
        m2 = Memory(db)          # neue "Sitzung"
        assert m2.recall("lieblingsfarbe") == "blau"
        assert m2.forget("lieblingsfarbe") is True
        assert m2.recall("lieblingsfarbe") == ""


def test_observe_builds_topics_and_context():
    with tempfile.TemporaryDirectory() as tmp:
        m = Memory(Path(tmp) / "m.sqlite3")
        m.remember("stadt", "Hamburg")
        m.observe("Wie läuft mein Shopify Shop heute?", "Gut.")
        m.observe("Zeig mir die Shopify Umsätze.", "Hier.")
        ctx = m.context_block()
        assert "Hamburg" in ctx
        assert "shopify" in ctx.lower()


def test_memory_skills_through_assistant():
    with tempfile.TemporaryDirectory() as tmp:
        m = Memory(Path(tmp) / "m.sqlite3")
        from jarvis.skills import memory_skills
        memory_skills.MEMORY = m
        # LLM merkt einen Fakt, dann bestätigt es.
        llm = ScriptedLLM([
            {"tool": "remember_fact", "args": {"key": "lieblingsgetränk", "value": "Espresso"}},
            {"content": "Gemerkt, Sir."},
        ])
        a = Assistant(llm, guard=Guard(), memory=m)
        a.handle("Merk dir, ich trinke am liebsten Espresso.")
        assert m.recall("lieblingsgetränk") == "Espresso"


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
