"""Audit-Log: jede Aktion wird nachvollziehbar protokolliert (JSON-Zeilen).

Qualitätsanspruch aus dem Auftrag: „Jede Aktion protokollieren" und „Fehler nie
stillschweigend schlucken". Dieses Modul ist die zentrale Stelle dafür.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_LOGGER = logging.getLogger("jarvis")
_AUDIT_PATH: Optional[Path] = None


def setup(log_file: Optional[Path] = None, level: str = "INFO") -> None:
    """Konsolen- + Datei-Logging einrichten."""
    global _AUDIT_PATH
    _LOGGER.setLevel(level)
    _LOGGER.handlers.clear()
    fmt = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s")

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    _LOGGER.addHandler(sh)

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        _LOGGER.addHandler(fh)
        _AUDIT_PATH = log_file.with_suffix(".audit.jsonl")


def log(msg: str, level: str = "info") -> None:
    getattr(_LOGGER, level, _LOGGER.info)(msg)


def audit(action: str, *, args: Optional[dict] = None, risk: Optional[int] = None,
          allowed: Optional[bool] = None, ok: Optional[bool] = None,
          result: str = "", error: str = "") -> None:
    """Strukturierter Audit-Eintrag für eine (versuchte) Aktion."""
    rec = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "action": action, "args": args or {}, "risk": risk,
        "allowed": allowed, "ok": ok,
        "result": (result or "")[:500], "error": (error or "")[:500],
    }
    _LOGGER.info("AUDIT %s risk=%s allowed=%s ok=%s %s",
                 action, risk, allowed, ok, error or "")
    if _AUDIT_PATH:
        try:
            with open(_AUDIT_PATH, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except OSError:
            pass
