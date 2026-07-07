"""Globaler Push-to-Talk-Hotkey (Strg+Alt+J) via pynput. Import gekapselt.

Push-to-Talk vermeidet Whisper-Halluzinationen bei Stille: Halten startet die
Aufnahme, Loslassen beendet und transkribiert.
"""
from __future__ import annotations

from typing import Callable

DEFAULT_HOTKEY = "<ctrl>+<alt>+j"


class PushToTalk:
    def __init__(self, on_activate: Callable[[], None], hotkey: str = DEFAULT_HOTKEY) -> None:
        self.on_activate = on_activate
        self.hotkey = hotkey
        self._listener = None

    def start(self) -> None:  # pragma: no cover - benötigt pynput + Desktop
        try:
            from pynput import keyboard  # type: ignore
        except ImportError as exc:
            raise RuntimeError("`pip install pynput` erforderlich.") from exc
        self._listener = keyboard.GlobalHotKeys({self.hotkey: self.on_activate})
        self._listener.start()

    def join(self) -> None:  # pragma: no cover
        if self._listener is not None:
            self._listener.join()

    def stop(self) -> None:  # pragma: no cover
        if self._listener is not None:
            self._listener.stop()
