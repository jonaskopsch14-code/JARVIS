"""Datei-Verwaltung (Phase 3) mit passenden Sicherheitsstufen.

  list_dir     Stufe 1 (lesen)
  write_file   Stufe 2 (reversibel: überschreibt/erstellt)
  append_file  Stufe 2
  move_file    Stufe 2
  delete_file  Stufe 3 (endgültig)
"""

from __future__ import annotations

import shutil
from pathlib import Path

from . import skill
from ..security import Risk


@skill(
    name="list_dir",
    description="Listet Dateien und Ordner in einem Verzeichnis auf.",
    parameters={"type": "object", "properties": {
        "path": {"type": "string"}}, "required": ["path"]},
    risk=Risk.AUTO,
)
def list_dir(path: str) -> str:
    p = Path(path).expanduser()
    if not p.is_dir():
        return f"Kein Verzeichnis: {path}"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    items = [("📁 " if e.is_dir() else "📄 ") + e.name for e in entries[:100]]
    return "; ".join(items) if items else "(leer)"


@skill(
    name="write_file",
    description="Schreibt Text in eine Datei (überschreibt vorhandenen Inhalt).",
    parameters={"type": "object", "properties": {
        "path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich die Datei schreiben/überschreiben?",
)
def write_file(path: str, content: str) -> str:
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Datei geschrieben: {p} ({len(content)} Zeichen)."
    except OSError as exc:
        return f"Konnte nicht schreiben: {exc}"


@skill(
    name="append_file",
    description="Hängt Text an eine Datei an.",
    parameters={"type": "object", "properties": {
        "path": {"type": "string"}, "content": {"type": "string"}},
        "required": ["path", "content"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich den Text an die Datei anhängen?",
)
def append_file(path: str, content: str) -> str:
    p = Path(path).expanduser()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(content)
        return f"An {p} angehängt ({len(content)} Zeichen)."
    except OSError as exc:
        return f"Konnte nicht anhängen: {exc}"


@skill(
    name="move_file",
    description="Verschiebt oder benennt eine Datei um.",
    parameters={"type": "object", "properties": {
        "src": {"type": "string"}, "dst": {"type": "string"}},
        "required": ["src", "dst"]},
    risk=Risk.CONFIRM,
    confirm_prompt="Soll ich die Datei verschieben/umbenennen?",
)
def move_file(src: str, dst: str) -> str:
    s, d = Path(src).expanduser(), Path(dst).expanduser()
    if not s.exists():
        return f"Quelle fehlt: {src}"
    try:
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return f"Verschoben: {s} → {d}."
    except OSError as exc:
        return f"Verschieben fehlgeschlagen: {exc}"


@skill(
    name="delete_file",
    description="Löscht eine Datei endgültig.",
    parameters={"type": "object", "properties": {
        "path": {"type": "string"}}, "required": ["path"]},
    risk=Risk.EXPLICIT,
    confirm_prompt="ACHTUNG: Diese Datei wird endgültig gelöscht.",
)
def delete_file(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists():
        return f"Datei existiert nicht: {path}"
    try:
        p.unlink()
        return f"Gelöscht: {p}."
    except OSError as exc:
        return f"Löschen fehlgeschlagen: {exc}"
