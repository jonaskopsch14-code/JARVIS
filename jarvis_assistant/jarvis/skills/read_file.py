"""Skill: Datei lesen (Stufe 1). Gibt den Textinhalt zurück; das LLM fasst zusammen."""

from __future__ import annotations

from pathlib import Path

from . import skill
from ..security import Risk

MAX_CHARS = 8000  # damit der Kontext nicht überläuft


@skill(
    name="read_file",
    description="Liest eine Textdatei und gibt ihren Inhalt zurück (zum Vorlesen/Zusammenfassen).",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Pfad zur Datei"}},
        "required": ["path"],
    },
    risk=Risk.AUTO,
)
def read_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_file():
        return f"Datei nicht gefunden: {path}"
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"Konnte Datei nicht lesen: {exc}"
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n… (gekürzt, {len(text)} Zeichen gesamt)"
    return text or "(Datei ist leer.)"
