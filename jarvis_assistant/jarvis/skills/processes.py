"""Prozess-/Programmsteuerung (Phase 3).

  list_processes  Stufe 1 (lesen)
  close_process   Stufe 2 (reversibel: Programm schließen)
"""

from __future__ import annotations

from . import skill
from ..security import Risk


@skill(
    name="list_processes",
    description="Zeigt die aktuell laufenden Programme (die speicherhungrigsten zuerst).",
    parameters={"type": "object", "properties": {
        "top": {"type": "integer", "description": "Anzahl (Standard 10)"}}},
    risk=Risk.AUTO,
)
def list_processes(top: int = 10) -> str:
    try:
        import psutil  # lazy
    except Exception as exc:  # noqa: BLE001
        return f"Prozessliste nicht verfügbar (psutil fehlt: {exc})."
    procs = []
    for p in psutil.process_iter(["name", "memory_info"]):
        try:
            mem = p.info["memory_info"].rss // (1024 * 1024) if p.info["memory_info"] else 0
            procs.append((p.info["name"] or "?", mem))
        except Exception:  # noqa: BLE001
            continue
    procs.sort(key=lambda x: x[1], reverse=True)
    return "; ".join(f"{n} ({m} MB)" for n, m in procs[:max(1, top)])


@skill(
    name="close_process",
    description="Schließt ein laufendes Programm anhand seines Namens.",
    parameters={"type": "object", "properties": {
        "name": {"type": "string"}}, "required": ["name"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich dieses Programm schließen?",
)
def close_process(name: str) -> str:
    try:
        import psutil  # lazy
    except Exception as exc:  # noqa: BLE001
        return f"Nicht verfügbar (psutil fehlt: {exc})."
    target = (name or "").strip().lower()
    closed = 0
    for p in psutil.process_iter(["name"]):
        try:
            if target in (p.info["name"] or "").lower():
                p.terminate()
                closed += 1
        except Exception:  # noqa: BLE001
            continue
    return f"{closed} Prozess(e) mit '{name}' geschlossen." if closed \
        else f"Kein laufender Prozess '{name}' gefunden."
