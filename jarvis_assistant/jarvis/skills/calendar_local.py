"""Skill: heutige Termine aus einer lokalen Quelle (Stufe 1).

Phase 1: liest eine einfache Textdatei `heute.md` (eine Zeile pro Termin) und/oder
eine `.ics`-Datei. Echtes Google Calendar folgt in Phase 3.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from . import skill
from ..security import Risk

# Von main aus Config gesetzt.
CALENDAR_PATH = Path.home() / "Jarvis" / "heute.md"


def _read_markdown(p: Path) -> list[str]:
    items = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip().lstrip("-*• ").strip()
        if line and not line.startswith("#"):
            items.append(line)
    return items


def _read_ics_today(p: Path) -> list[str]:
    today = date.today().strftime("%Y%m%d")
    text = p.read_text(encoding="utf-8", errors="replace")
    events = []
    for block in text.split("BEGIN:VEVENT")[1:]:
        summary = re.search(r"SUMMARY:(.+)", block)
        start = re.search(r"DTSTART[^:]*:(\d{8})", block)
        if start and start.group(1) == today and summary:
            time = re.search(r"DTSTART[^:]*:\d{8}T(\d{2})(\d{2})", block)
            when = f"{time.group(1)}:{time.group(2)} " if time else ""
            events.append(f"{when}{summary.group(1).strip()}")
    return events


@skill(
    name="calendar_today",
    description="Gibt die heutigen Termine des Nutzers zurück.",
    parameters={"type": "object", "properties": {}},
    risk=Risk.AUTO,
)
def calendar_today() -> str:
    p = Path(CALENDAR_PATH)
    if not p.exists():
        return ("Keine Termine hinterlegt. (Lege Termine in der Datei "
                f"{p} ab — eine Zeile pro Termin.)")
    try:
        items = _read_ics_today(p) if p.suffix.lower() == ".ics" else _read_markdown(p)
    except OSError as exc:
        return f"Konnte Kalender nicht lesen: {exc}"
    if not items:
        return "Für heute sind keine Termine eingetragen."
    return "Heute stehen an: " + "; ".join(items) + "."
