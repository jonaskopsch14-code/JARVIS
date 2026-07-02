"""Skill: eine Anwendung öffnen (Stufe 1 — informierend/öffnend)."""

from __future__ import annotations

import shutil
import subprocess
import sys

from . import skill
from ..security import Risk

# Freundliche Namen → ausführbare Datei (Windows). Erweiterbar.
KNOWN_APPS = {
    "browser": "start msedge", "edge": "start msedge", "chrome": "start chrome",
    "firefox": "start firefox", "notepad": "notepad", "editor": "notepad",
    "explorer": "explorer", "dateien": "explorer", "rechner": "calc",
    "calculator": "calc", "spotify": "start spotify", "word": "start winword",
    "excel": "start excel", "terminal": "wt", "cmd": "cmd",
}


@skill(
    name="open_app",
    description="Öffnet eine Anwendung auf dem PC (z. B. Browser, Editor, Rechner, Explorer).",
    parameters={
        "type": "object",
        "properties": {"app": {"type": "string", "description": "Name der App, z. B. 'browser' oder 'notepad'"}},
        "required": ["app"],
    },
    risk=Risk.AUTO,
)
def open_app(app: str) -> str:
    key = (app or "").strip().lower()
    cmd = KNOWN_APPS.get(key, key)
    try:
        if sys.platform.startswith("win"):
            # 'start ...' braucht die Shell; einfache Programme direkt.
            subprocess.Popen(cmd, shell=True)
        else:
            # Nicht-Windows (Tests/Dev): nur prüfen, ob es das Programm gäbe.
            exe = cmd.split()[-1]
            if not shutil.which(exe):
                return f"(Simuliert) Würde '{app}' öffnen — auf diesem System nicht ausführbar."
            subprocess.Popen([exe])
        return f"'{app}' wurde geöffnet."
    except Exception as exc:  # noqa: BLE001
        return f"Konnte '{app}' nicht öffnen: {exc}"
