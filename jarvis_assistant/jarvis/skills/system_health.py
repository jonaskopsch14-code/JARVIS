"""System-Zustand (Phase 4) — alles Stufe 1 (nur lesen)."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import skill
from ..security import Risk


def free_gb(path: str = None) -> float:
    root = path or ("C:\\" if Path("C:\\").exists() else "/")
    try:
        return round(shutil.disk_usage(root).free / (1024 ** 3), 1)
    except OSError:
        return -1.0


@skill(
    name="disk_space",
    description="Freier Speicherplatz auf der Systemfestplatte.",
    parameters={"type": "object", "properties": {}},
    risk=Risk.AUTO,
)
def disk_space() -> str:
    gb = free_gb()
    return f"Auf der Systemplatte sind noch {gb} GB frei." if gb >= 0 \
        else "Speicherplatz konnte nicht ermittelt werden."


@skill(
    name="system_status",
    description="Kurzer Systemüberblick: Speicher, RAM, Akku (sofern vorhanden).",
    parameters={"type": "object", "properties": {}},
    risk=Risk.AUTO,
)
def system_status() -> str:
    parts = [f"{free_gb()} GB Speicher frei"]
    try:
        import psutil  # lazy
        parts.append(f"RAM-Auslastung {psutil.virtual_memory().percent} Prozent")
        bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        if bat is not None:
            parts.append(f"Akku {int(bat.percent)} Prozent"
                         + (" (am Netz)" if bat.power_plugged else ""))
    except Exception:  # noqa: BLE001
        pass
    return ", ".join(parts) + "."
