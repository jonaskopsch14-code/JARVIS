"""Phase 3: Datei-/Systemsteuerung + Sicherheitsstufen als getesteter Code (offline)."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarvis import skills                       # noqa: E402
from jarvis.assistant import Assistant          # noqa: E402
from jarvis.llm import ScriptedLLM              # noqa: E402
from jarvis.security import Guard, Risk         # noqa: E402
from jarvis.skills import files                 # noqa: E402


def test_file_skills_registered_with_correct_risk():
    assert skills.get("list_dir").risk == Risk.AUTO
    assert skills.get("write_file").risk == Risk.CONFIRM
    assert skills.get("delete_file").risk == Risk.EXPLICIT


def test_write_read_move_delete_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "a.txt"
        assert "geschrieben" in files.write_file(str(f), "Hallo")
        assert f.read_text(encoding="utf-8") == "Hallo"
        g = Path(tmp) / "b.txt"
        assert "Verschoben" in files.move_file(str(f), str(g))
        assert not f.exists() and g.exists()
        assert "Gelöscht" in files.delete_file(str(g))
        assert not g.exists()


def test_delete_blocked_without_confirmation():
    # delete_file ist Stufe 3 → ohne Bestätigung darf die Datei NICHT verschwinden.
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "keep.txt"
        f.write_text("wichtig", encoding="utf-8")
        llm = ScriptedLLM([{"tool": "delete_file", "args": {"path": str(f)}},
                           {"content": "Abgelehnt."}])
        a = Assistant(llm, guard=Guard())  # auto_deny
        a.handle(f"Lösche {f}")
        assert f.exists()  # blockiert → noch da


def test_write_blocked_without_confirmation():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "new.txt"
        llm = ScriptedLLM([{"tool": "write_file",
                            "args": {"path": str(f), "content": "x"}},
                           {"content": "Abgelehnt."}])
        a = Assistant(llm, guard=Guard())  # auto_deny → Stufe 2 blockiert
        a.handle("Schreib die Datei")
        assert not f.exists()


def test_write_allowed_with_confirmation():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "ok.txt"
        llm = ScriptedLLM([{"tool": "write_file",
                            "args": {"path": str(f), "content": "ja"}},
                           {"content": "Erledigt."}])
        a = Assistant(llm, guard=Guard(confirmer=lambda p, r: True))
        a.handle("Schreib die Datei")
        assert f.exists() and f.read_text(encoding="utf-8") == "ja"


def test_phase3_optional_skills_present_or_gracefully_absent():
    # Diese Skills sind hardware/OAuth-gebunden; sie sollen zumindest registriert
    # sein (Import darf den Kern nicht sprengen) und die richtige Risikostufe haben.
    for name, risk in [("gmail_list_unread", Risk.AUTO),
                       ("gmail_send", Risk.EXPLICIT),
                       ("close_process", Risk.CONFIRM),
                       ("browse_page", Risk.AUTO),
                       ("read_screen", Risk.AUTO)]:
        sk = skills.get(name)
        assert sk is not None, f"{name} nicht registriert"
        assert sk.risk == risk


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
