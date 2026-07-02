"""Always-on Weckwort (Phase 6): reagiert auf gesprochenes „Jarvis" ohne Taste.

Nutzt openWakeWord + sounddevice (beides lazy). Ohne diese Pakete meldet der
Listener das sauber und Jarvis bleibt beim Push-to-Talk-Hotkey.
"""

from __future__ import annotations

import threading
from typing import Callable


class WakeWordListener:
    def __init__(self, on_wake: Callable[[], None], wakeword: str = "jarvis",
                 samplerate: int = 16000):
        self.on_wake = on_wake
        self.wakeword = wakeword
        self.samplerate = samplerate
        self._stop = threading.Event()
        self._thread = None

    def available(self) -> bool:
        try:
            import openwakeword  # noqa: F401
            import sounddevice  # noqa: F401
            return True
        except Exception:  # noqa: BLE001
            return False

    def start(self) -> bool:
        if not self.available():
            from .audit import log
            log("Weckwort nicht verfügbar (openwakeword/sounddevice fehlen) — "
                "nutze weiter den Hotkey.", "warning")
            return False
        self._thread = threading.Thread(target=self._loop, name="jarvis-wake", daemon=True)
        self._thread.start()
        return True

    def _loop(self) -> None:
        import numpy as np
        import sounddevice as sd
        from openwakeword.model import Model
        from .audit import log
        try:
            model = Model()  # Standardmodelle inkl. Aktivierungswörter
        except Exception as exc:  # noqa: BLE001
            log(f"Weckwort-Modell nicht ladbar: {exc}", "warning")
            return
        block = 1280  # ~80 ms bei 16 kHz
        with sd.InputStream(samplerate=self.samplerate, channels=1,
                            dtype="int16", blocksize=block) as stream:
            log(f"Weckwort aktiv: sag einfach '{self.wakeword}'.")
            while not self._stop.is_set():
                data, _ = stream.read(block)
                preds = model.predict(np.frombuffer(data, dtype=np.int16))
                if any(score > 0.5 for score in preds.values()):
                    self.on_wake()

    def stop(self) -> None:
        self._stop.set()
