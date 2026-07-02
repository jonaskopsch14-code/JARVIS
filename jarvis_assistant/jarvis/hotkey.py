"""Globaler Push-to-Talk-Hotkey + Not-Aus. Nutzt die 'keyboard'-Lib (Windows).

Alles lazy importiert; auf Systemen ohne 'keyboard' meldet register() das
sauber zurück, statt zu crashen.
"""

from __future__ import annotations

import threading
from typing import Callable


class HotkeyManager:
    def __init__(self, talk_hotkey: str = "ctrl+alt+j",
                 panic_hotkey: str = "ctrl+alt+pause"):
        self.talk_hotkey = talk_hotkey
        self.panic_hotkey = panic_hotkey
        self._busy = threading.Lock()
        self._stop = threading.Event()

    def register(self, on_talk: Callable[[], None],
                 on_panic: Callable[[], None]) -> bool:
        try:
            import keyboard  # lazy
        except Exception as exc:  # noqa: BLE001
            from .audit import log
            log(f"Hotkeys nicht verfügbar ({exc}). Nutze den Text-Modus "
                f"(python -m jarvis.main --text).", "warning")
            return False

        def talk_wrapper():
            # Nicht neu starten, solange eine Interaktion läuft.
            if self._busy.acquire(blocking=False):
                try:
                    on_talk()
                finally:
                    self._busy.release()

        keyboard.add_hotkey(self.talk_hotkey, talk_wrapper)
        keyboard.add_hotkey(self.panic_hotkey, on_panic)
        return True

    def wait(self) -> None:
        self._stop.wait()

    def stop(self) -> None:
        self._stop.set()
