"""Phase-1-Kern offline testen: Assistent-Schleife, Sicherheits-Gate, Skills.
Kein Mikro/Ollama/ElevenLabs nötig — LLM ist ein Test-Double."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis import skills                       # noqa: E402
from jarvis.assistant import Assistant          # noqa: E402
from jarvis.llm import ScriptedLLM              # noqa: E402
from jarvis.security import Guard, Risk, console_confirmer  # noqa: E402


def test_builtin_skills_registered():
    names = {s.name for s in skills.all_skills()}
    assert {"open_app", "web_search", "read_file", "weather", "calendar_today"} <= names


def test_tools_have_valid_schema():
    for t in skills.build_tools():
        assert t["type"] == "function"
        assert "name" in t["function"] and "parameters" in t["function"]


def test_assistant_direct_answer():
    llm = ScriptedLLM([{"content": "Guten Tag, Sir."}])
    a = Assistant(llm)
    assert a.handle("Hallo") == "Guten Tag, Sir."


def test_assistant_calls_tool_then_answers():
    # LLM ruft erst 'calendar_today', dann formuliert es die Antwort.
    with tempfile.TemporaryDirectory() as tmp:
        cal = Path(tmp) / "heute.md"
        cal.write_text("- 10:00 Zahnarzt\n- 14:00 Team-Call\n", encoding="utf-8")
        from jarvis.skills import calendar_local
        calendar_local.CALENDAR_PATH = cal

        llm = ScriptedLLM([
            {"tool": "calendar_today", "args": {}},
            {"content": "Heute: Zahnarzt und Team-Call, Sir."},
        ])
        a = Assistant(llm, guard=Guard())  # Guard default: Stufe1 ok
        out = a.handle("Was steht heute an?")
        assert "Team-Call" in out or "Sir" in out
        # Das Tool-Ergebnis muss dem LLM als 'tool'-Message geliefert worden sein.
        last_msgs = llm.calls[-1]["messages"]
        assert any(m.get("role") == "tool" and "Zahnarzt" in m.get("content", "")
                   for m in last_msgs)


def test_security_gate_blocks_unconfirmed_level3():
    # Ein riskantes Test-Skill (Stufe 3) darf ohne Bestätigung NICHT laufen.
    ran = {"v": False}

    @skills.skill(name="danger_test", description="gefährlich",
                  parameters={"type": "object", "properties": {}}, risk=Risk.EXPLICIT)
    def _danger():
        ran["v"] = True
        return "ausgeführt"

    llm = ScriptedLLM([{"tool": "danger_test", "args": {}},
                       {"content": "Erledigt bzw. abgelehnt."}])
    a = Assistant(llm, guard=Guard())  # default confirmer = auto_deny
    a.handle("Mach das gefährliche Ding")
    assert ran["v"] is False  # blockiert


def test_security_gate_allows_confirmed(monkeypatch=None):
    ran = {"v": False}

    @skills.skill(name="confirm_test", description="reversibel",
                  parameters={"type": "object", "properties": {}}, risk=Risk.CONFIRM)
    def _c():
        ran["v"] = True
        return "gemacht"

    llm = ScriptedLLM([{"tool": "confirm_test", "args": {}}, {"content": "Erledigt."}])
    a = Assistant(llm, guard=Guard(confirmer=lambda p, r: True))  # bestätigt alles
    a.handle("Mach das reversible Ding")
    assert ran["v"] is True


def test_open_app_simulated_offline():
    # Auf Nicht-Windows meldet open_app sauber eine Simulation statt zu crashen.
    from jarvis.skills.open_app import open_app
    res = open_app("gibtsnichtxyz")
    assert isinstance(res, str) and res


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
