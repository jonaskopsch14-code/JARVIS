"""Tray-Icon mit Statusanzeige und Beenden-Schalter (Phase 1/6).

Optional: braucht 'pystray' + 'Pillow'. Fehlt es, läuft Jarvis ohne Tray weiter.
"""

from __future__ import annotations

from typing import Callable, Optional


class Tray:
    def __init__(self, on_quit: Callable[[], None],
                 on_toggle: Optional[Callable[[], None]] = None,
                 log_file: Optional[str] = None):
        self.on_quit = on_quit
        self.on_toggle = on_toggle
        self.log_file = log_file
        self._icon = None

    def _open_log(self) -> None:
        """Aktivitätslog im Standard-Editor öffnen (Phase 6)."""
        if not self.log_file:
            return
        try:
            import os
            os.startfile(self.log_file)  # type: ignore[attr-defined]  # Windows
        except Exception:  # noqa: BLE001
            import subprocess
            import sys
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            try:
                subprocess.Popen([opener, self.log_file])
            except Exception:  # noqa: BLE001
                pass

    def _image(self):
        from PIL import Image, ImageDraw  # lazy
        img = Image.new("RGB", (64, 64), "#05080d")
        d = ImageDraw.Draw(img)
        d.ellipse((10, 10, 54, 54), outline="#00c8ff", width=4)
        d.ellipse((24, 24, 40, 40), fill="#7fe8ff")
        return img

    def run(self) -> bool:
        """Blockiert im Tray-Loop. Gibt False zurück, wenn kein Tray möglich ist."""
        try:
            import pystray  # lazy
        except Exception as exc:  # noqa: BLE001
            from .audit import log
            log(f"Tray nicht verfügbar ({exc}) — laufe ohne Tray weiter.", "warning")
            return False
        items = [pystray.MenuItem("Jarvis beenden", lambda: self._quit())]
        if self.log_file:
            items.insert(0, pystray.MenuItem("Aktivitätslog öffnen", lambda: self._open_log()))
        if self.on_toggle:
            items.insert(0, pystray.MenuItem("Pause/Weiter", lambda: self.on_toggle()))
        self._icon = pystray.Icon("jarvis", self._image(), "Jarvis",
                                  pystray.Menu(*items))
        self._icon.run()
        return True

    def _quit(self) -> None:
        try:
            if self._icon:
                self._icon.stop()
        finally:
            self.on_quit()
