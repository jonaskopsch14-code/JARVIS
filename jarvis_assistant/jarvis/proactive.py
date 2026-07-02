"""Proaktivität (Phase 4): der Mechanismus, mit dem Jarvis von selbst meldet.

Eine kleine, testbare Scheduler-Engine führt registrierte Checks aus — entweder
in Intervallen ("alle X Sekunden") oder täglich zu einer Uhrzeit ("um 08:00").
Gibt ein Check einen Text zurück, wird er über den `notifier` gemeldet
(im Sprach-Modus: vorgelesen).

Die Terminlogik (`_due`) ist reine Funktion und mit einer Fake-Uhr testbar.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional

Notifier = Callable[[str], None]
CheckFunc = Callable[[], Optional[str]]


@dataclass
class Check:
    name: str
    func: CheckFunc
    kind: str = "interval"          # "interval" | "daily"
    interval_s: int = 3600
    at: str = "08:00"               # nur bei kind="daily"
    _last_ts: float = 0.0
    _last_day: str = field(default="")


class ProactiveEngine:
    def __init__(self, notifier: Notifier):
        self.notifier = notifier
        self.checks: List[Check] = []
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def add(self, check: Check) -> None:
        self.checks.append(check)

    # -- reine Terminlogik (testbar) ----------------------------------------
    @staticmethod
    def _due(c: Check, now: datetime) -> bool:
        if c.kind == "daily":
            today = now.strftime("%Y-%m-%d")
            return now.strftime("%H:%M") >= c.at and c._last_day != today
        return (now.timestamp() - c._last_ts) >= c.interval_s

    @staticmethod
    def _mark(c: Check, now: datetime) -> None:
        c._last_ts = now.timestamp()
        c._last_day = now.strftime("%Y-%m-%d")

    def run_once(self, now: Optional[datetime] = None) -> List[str]:
        """Fällige Checks ausführen; gemeldete Texte zurückgeben (und notifizieren)."""
        now = now or datetime.now()
        messages: List[str] = []
        for c in self.checks:
            if not self._due(c, now):
                continue
            self._mark(c, now)
            try:
                msg = c.func()
            except Exception as exc:  # noqa: BLE001
                msg = None
                from .audit import log
                log(f"Proaktiv-Check '{c.name}' fehlgeschlagen: {exc}", "warning")
            if msg:
                messages.append(msg)
        for m in messages:
            try:
                self.notifier(m)
            except Exception:  # noqa: BLE001
                pass
        return messages

    # -- Hintergrundbetrieb -------------------------------------------------
    def start(self, tick_seconds: int = 60) -> None:
        def loop():
            while not self._stop.wait(timeout=tick_seconds):
                self.run_once()
        self._thread = threading.Thread(target=loop, name="jarvis-proactive", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()


# ---------------------------------------------------------------------------
# Fertige Checks.
# ---------------------------------------------------------------------------
def compose_morning_briefing(city: str = "Berlin",
                             weather_fn: CheckFunc = None,
                             calendar_fn: CheckFunc = None,
                             mail_fn: CheckFunc = None,
                             user_name: str = "Jonas") -> str:
    """Baut das morgendliche Briefing aus Wetter, Terminen und (optional) Mail."""
    if weather_fn is None:
        from .skills.weather import weather as _w
        weather_fn = lambda: _w(city)
    if calendar_fn is None:
        from .skills.calendar_local import calendar_today as _c
        calendar_fn = _c

    parts = [f"Guten Morgen, {user_name}."]
    try:
        parts.append(weather_fn() or "")
    except Exception:  # noqa: BLE001
        pass
    try:
        parts.append(calendar_fn() or "")
    except Exception:  # noqa: BLE001
        pass
    if mail_fn is not None:
        try:
            parts.append(mail_fn() or "")
        except Exception:  # noqa: BLE001
            pass
    return " ".join(p for p in parts if p).strip()


def disk_space_check(threshold_gb: float = 15.0) -> Optional[str]:
    """Warnt nur, wenn wenig Platz frei ist (sonst still)."""
    from .skills.system_health import free_gb
    gb = free_gb()
    if 0 <= gb < threshold_gb:
        return (f"Kurzer Hinweis, Sir: auf der Systemplatte sind nur noch "
                f"{gb} GB frei. Vielleicht sollten wir aufräumen.")
    return None


def build_default_engine(cfg, notifier: Notifier) -> ProactiveEngine:
    """Standard-Checks aus der Config zusammenstellen."""
    eng = ProactiveEngine(notifier)
    if getattr(cfg, "proactive_enabled", True):
        eng.add(Check("morning_briefing",
                      func=lambda: compose_morning_briefing(cfg.city, user_name=cfg.user_name),
                      kind="daily", at=cfg.morning_briefing_time))
        eng.add(Check("disk_space", func=disk_space_check,
                      kind="interval", interval_s=6 * 3600))
    return eng
