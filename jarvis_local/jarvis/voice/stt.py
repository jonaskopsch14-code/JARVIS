"""Spracheingabe (STT) via faster-whisper. Imports gekapselt.

Auf dem Windows-PC mit RTX 2080 Super läuft ``large-v3``/``medium`` im GPU-Modus.
Für Umgebungen ohne Audio gibt es :class:`TextInput` als Fallback.
"""
from __future__ import annotations

from typing import Protocol


class SpeechInput(Protocol):
    def listen(self) -> str: ...


class TextInput:
    """Fallback: liest Text von der Konsole (kein Mikrofon nötig)."""

    def __init__(self, prompt: str = "Du: ") -> None:
        self.prompt = prompt

    def listen(self) -> str:
        try:
            return input(self.prompt).strip()
        except EOFError:
            return ""


class WhisperSTT:
    """faster-whisper-Wrapper mit Push-to-Talk-Aufnahme (sounddevice)."""

    def __init__(
        self,
        model_size: str = "large-v3",
        device: str = "cuda",
        compute_type: str = "float16",
        language: str = "de",
        samplerate: int = 16000,
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.samplerate = samplerate
        self._model = None

    def _load(self):  # pragma: no cover - benötigt faster-whisper + Modell
        if self._model is None:
            try:
                from faster_whisper import WhisperModel  # type: ignore
            except ImportError as exc:
                raise RuntimeError("`pip install faster-whisper` erforderlich.") from exc
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio) -> str:  # pragma: no cover
        model = self._load()
        segments, _ = model.transcribe(audio, language=self.language, vad_filter=True)
        return " ".join(seg.text for seg in segments).strip()

    def record(self, seconds: float = 8.0):  # pragma: no cover
        try:
            import sounddevice as sd  # type: ignore
        except ImportError as exc:
            raise RuntimeError("`pip install sounddevice` erforderlich.") from exc
        frames = sd.rec(int(seconds * self.samplerate), samplerate=self.samplerate, channels=1, dtype="float32")
        sd.wait()
        return frames.reshape(-1)

    def listen(self) -> str:  # pragma: no cover
        return self.transcribe(self.record())
