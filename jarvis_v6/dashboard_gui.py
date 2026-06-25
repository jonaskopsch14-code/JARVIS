"""
JARVIS V6 — Arc-Reactor Dashboard GUI
=====================================

The glowing, reactive Arc-Reactor interface for the Night-Shift Overclock
Protocol. Built on Tkinter (standard library) so the baseline renders on any
desktop Python with no extra install. If you later want a GPU-accelerated
look, swap the Canvas drawing for PySide6 — the supervisor contract is
unchanged.

Reactive behaviour, wired to NightShiftSupervisor's state stream:

  * NIGHT_SHIFT  -> the window drops to ~5% opacity and sinks behind others,
                    so it stops burning pixels and stops spending GPU cycles
                    while the overnight tasks run.
  * SLEEPING     -> stays dimmed, slow "heartbeat" pulse.
  * WAKING       -> at the wake clock (16:00): the reactor pops to the front,
                    ramps to full brightness, and fires a sound cue.
  * BRIEFING     -> shows the executive summary text and speaks it (TTS).
  * IDLE         -> calm steady glow, ready for the next command.

Thread-safety: the supervisor runs on a background thread and pushes state
updates into a queue; only the Tk main thread ever touches widgets (polled via
`after`). This is the correct, crash-free way to bridge the two.
"""

from __future__ import annotations

import math
import queue
import sys
import threading
from typing import Optional, Tuple

try:
    import tkinter as tk
    from tkinter import font as tkfont
except Exception as exc:  # pragma: no cover - headless box
    raise RuntimeError(f"Tkinter is required for the dashboard GUI: {exc}")

from main import NightShiftConfig, NightShiftSupervisor, SystemState


# ---------------------------------------------------------------------------
# Colour helpers — Iron-Man arc-reactor cyan/white palette.
# ---------------------------------------------------------------------------
def _lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * max(0.0, min(1.0, t))))


def _mix(c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> str:
    return "#%02x%02x%02x" % (
        _lerp(c1[0], c2[0], t), _lerp(c1[1], c2[1], t), _lerp(c1[2], c2[2], t)
    )


CORE = (210, 245, 255)      # near-white hot core
GLOW = (0, 200, 255)        # cyan glow
DEEP = (0, 60, 110)         # deep ring
BG = "#05080d"              # near-black background


class ArcReactor:
    """Draws and animates the reactor on a Tk Canvas."""

    def __init__(self, canvas: tk.Canvas, size: int = 360):
        self.canvas = canvas
        self.size = size
        self.cx = self.cy = size / 2
        self.phase = 0.0
        self.brightness = 1.0       # 0..1, scales the whole glow
        self.target_brightness = 1.0
        self.pulse_speed = 0.12     # radians per frame
        self.segments = 8

    def set_brightness(self, value: float, *, instant: bool = False) -> None:
        self.target_brightness = max(0.0, min(1.0, value))
        if instant:
            self.brightness = self.target_brightness

    def _radius(self, frac: float) -> float:
        return (self.size * 0.42) * frac

    def draw(self) -> None:
        c = self.canvas
        c.delete("reactor")
        # Ease brightness toward its target for smooth ramps.
        self.brightness += (self.target_brightness - self.brightness) * 0.15
        b = self.brightness
        # Breathing pulse.
        pulse = 0.5 + 0.5 * math.sin(self.phase)
        cx, cy = self.cx, self.cy

        # --- outer glow halo (concentric translucent-looking rings) ---------
        for i in range(10, 0, -1):
            frac = 1.0 + i * 0.06
            r = self._radius(frac)
            t = (i / 10.0)
            col = _mix(GLOW, BG, 0.35 + 0.6 * t)
            col = _mix(BG, col, b)  # fade with brightness
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          outline=col, width=2, tags="reactor")

        # --- outer ring -----------------------------------------------------
        r = self._radius(1.0)
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      outline=_mix(BG, GLOW, b), width=4, tags="reactor")

        # --- radiating coil segments (the iconic triangular wedges) ---------
        r_out = self._radius(0.92)
        r_in = self._radius(0.62)
        for k in range(self.segments):
            a0 = (2 * math.pi / self.segments) * k + self.phase * 0.15
            a1 = a0 + (2 * math.pi / self.segments) * 0.6
            seg_glow = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(self.phase + k))
            col = _mix(BG, GLOW, b * seg_glow)
            pts = [
                cx + r_in * math.cos(a0), cy + r_in * math.sin(a0),
                cx + r_out * math.cos(a0), cy + r_out * math.sin(a0),
                cx + r_out * math.cos(a1), cy + r_out * math.sin(a1),
                cx + r_in * math.cos(a1), cy + r_in * math.sin(a1),
            ]
            c.create_polygon(pts, fill=col, outline="", tags="reactor")

        # --- inner ring -----------------------------------------------------
        r = self._radius(0.58)
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      outline=_mix(BG, CORE, b), width=3, tags="reactor")

        # --- glowing core ---------------------------------------------------
        for i in range(6, 0, -1):
            r = self._radius(0.40) * (i / 6.0)
            t = i / 6.0
            col = _mix(CORE, GLOW, 1 - t)
            col = _mix(BG, col, b * (0.6 + 0.4 * pulse))
            c.create_oval(cx - r, cy - r, cx + r, cy + r,
                          fill=col, outline="", tags="reactor")

        self.phase += self.pulse_speed


class Dashboard:
    """The top-level window + the bridge to the supervisor."""

    def __init__(self, config: Optional[NightShiftConfig] = None):
        self.config = config or NightShiftConfig()
        self.events: "queue.Queue[tuple]" = queue.Queue()
        self.supervisor = NightShiftSupervisor(
            config=self.config, on_state=self._on_state_threadsafe
        )

        self.root = tk.Tk()
        self.root.title("JARVIS V6 — Arc Reactor")
        self.root.configure(bg=BG)
        self.root.geometry("460x560")
        self.root.minsize(420, 520)

        self.canvas = tk.Canvas(self.root, width=360, height=360,
                                bg=BG, highlightthickness=0)
        self.canvas.pack(pady=(24, 8))
        self.reactor = ArcReactor(self.canvas, size=360)

        self.status_font = tkfont.Font(family="Helvetica", size=12, weight="bold")
        self.status = tk.Label(self.root, text="SYSTEM BEREIT", fg="#7fe8ff",
                               bg=BG, font=self.status_font)
        self.status.pack()

        self.briefing = tk.Label(self.root, text="", fg="#bfefff", bg=BG,
                                 wraplength=400, justify="center",
                                 font=tkfont.Font(family="Helvetica", size=10))
        self.briefing.pack(pady=8, fill="x")

        self.start_btn = tk.Button(
            self.root, text="Starte Nachtschicht-Protokoll",
            command=self.start_protocol, bg="#0a2a3a", fg="#7fe8ff",
            activebackground="#0f3d52", activeforeground="#ffffff",
            relief="flat", padx=14, pady=8,
        )
        self.start_btn.pack(pady=(4, 18))

        self._dimmed = False
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._tick()              # start animation loop
        self._drain_events()      # start event-queue poller

    # -- supervisor -> GUI bridge -------------------------------------------
    def _on_state_threadsafe(self, state: SystemState, info: dict) -> None:
        # Called from the supervisor's background thread. Do NOT touch Tk here;
        # just hand the event to the queue the main thread drains.
        self.events.put((state, info))

    def _drain_events(self) -> None:
        try:
            while True:
                state, info = self.events.get_nowait()
                self._apply_state(state, info)
        except queue.Empty:
            pass
        self.root.after(50, self._drain_events)

    def _apply_state(self, state: SystemState, info: dict) -> None:
        labels = {
            SystemState.BOOTING: "INITIALISIERE…",
            SystemState.NIGHT_SHIFT: "NACHTSCHICHT AKTIV",
            SystemState.SLEEPING: "WARTE AUF WECK-FENSTER",
            SystemState.WAKING: "WECK-SEQUENZ",
            SystemState.BRIEFING: "EXECUTIVE BRIEFING",
            SystemState.IDLE: "SYSTEM BEREIT",
            SystemState.STOPPED: "GESTOPPT",
        }
        self.status.config(text=labels.get(state, state.value.upper()))

        if state in (SystemState.NIGHT_SHIFT, SystemState.SLEEPING):
            self._enter_night_mode()
        elif state == SystemState.WAKING:
            self._wake_sequence()
        elif state == SystemState.BRIEFING:
            text = info.get("text", "")
            self.briefing.config(text=text)
            self._speak_async(text)
        elif state == SystemState.IDLE:
            self.reactor.set_brightness(1.0)

    # -- night / wake visual transitions ------------------------------------
    def _enter_night_mode(self) -> None:
        """Drop opacity to ~5% and sink behind other windows to save the
        panel + GPU. Slow heartbeat pulse."""
        if self._dimmed:
            return
        self._dimmed = True
        self.reactor.pulse_speed = 0.04
        self.reactor.set_brightness(0.18)
        try:
            self.root.attributes("-alpha", 0.05)
            self.root.lower()
        except tk.TclError:
            pass  # platform without alpha support

    def _wake_sequence(self) -> None:
        """At 16:00: pop to front, ramp to full brightness, sound cue."""
        self._dimmed = False
        self.reactor.pulse_speed = 0.12
        self.reactor.set_brightness(1.0)
        try:
            self.root.attributes("-alpha", 1.0)
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(1500, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        self._sound_cue()

    def _sound_cue(self) -> None:
        if sys.platform.startswith("win"):
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
                return
            except Exception:
                pass
        try:
            self.root.bell()
        except tk.TclError:
            pass

    def _speak_async(self, text: str) -> None:
        # TTS can block; run it off the Tk thread.
        threading.Thread(target=self._speak, args=(text,), daemon=True).start()

    @staticmethod
    def _speak(text: str) -> None:
        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception:
            pass  # already shown on screen

    # -- animation loop ------------------------------------------------------
    def _tick(self) -> None:
        self.reactor.draw()
        self.root.after(33, self._tick)  # ~30 fps

    # -- controls ------------------------------------------------------------
    def start_protocol(self) -> None:
        self.start_btn.config(state="disabled")
        self.briefing.config(text="")
        # The supervisor delivers the briefing via the WAKING/BRIEFING states,
        # so we pass a no-op wake_callback (the GUI owns presentation).
        self.supervisor.start_async(wake_callback=lambda _text: None)

    def _on_close(self) -> None:
        self.supervisor.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def launch(config: Optional[NightShiftConfig] = None) -> None:
    Dashboard(config).run()


if __name__ == "__main__":
    launch()
