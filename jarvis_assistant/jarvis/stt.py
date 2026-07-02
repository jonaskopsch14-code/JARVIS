"""Sprache→Text. Schnittstelle + faster-whisper (Windows) + Konsole (Fallback/Test).

Alle schweren Importe sind lazy, damit das Paket überall importierbar bleibt.
"""

from __future__ import annotations

from typing import Optional, Protocol


class Recognizer(Protocol):
    def listen(self) -> str:
        """Nimmt auf und gibt den erkannten Text zurück (leer = nichts verstanden)."""
        ...


class ConsoleRecognizer:
    """Text-Modus: liest von der Tastatur statt vom Mikrofon."""

    def listen(self) -> str:
        try:
            return input("Du> ").strip()
        except EOFError:
            return ""


class WhisperRecognizer:
    """Mikro-Aufnahme (Auto-Stopp bei Stille) + faster-whisper-Transkription."""

    def __init__(self, model: str = "small", language: str = "de",
                 silence_stop_ms: int = 900, samplerate: int = 16000):
        self.model_name = model
        self.language = language
        self.silence_stop_ms = silence_stop_ms
        self.samplerate = samplerate
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # lazy
            self._model = WhisperModel(self.model_name, device="auto",
                                       compute_type="int8")
        return self._model

    def _record(self):
        import numpy as np  # lazy
        import sounddevice as sd  # lazy
        block = int(self.samplerate * 0.1)  # 100-ms-Blöcke
        silence_blocks = max(1, self.silence_stop_ms // 100)
        frames, quiet, started = [], 0, False
        with sd.InputStream(samplerate=self.samplerate, channels=1,
                            dtype="float32", blocksize=block) as stream:
            for _ in range(0, self.samplerate * 30 // block):  # max 30 s
                data, _ = stream.read(block)
                frames.append(data.copy())
                energy = float((data ** 2).mean() ** 0.5)
                if energy > 0.015:
                    started, quiet = True, 0
                elif started:
                    quiet += 1
                    if quiet >= silence_blocks:
                        break
        import numpy as np
        return np.concatenate(frames, axis=0).flatten() if frames else np.zeros(1)

    def listen(self) -> str:
        try:
            audio = self._record()
            model = self._ensure_model()
            segments, _ = model.transcribe(audio, language=self.language)
            return " ".join(s.text for s in segments).strip()
        except Exception as exc:  # noqa: BLE001
            from .audit import log
            log(f"STT-Fehler: {exc}", "error")
            return ""
