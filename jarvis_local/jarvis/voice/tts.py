"""Sprachausgabe (TTS).

Lokaler Default: Piper mit deutscher Thorsten-Stimme (CPU-only, offline, <50 ms
erster Ton). Optionaler Premium-Modus: ElevenLabs Flash (Cloud). Fallback:
:class:`PrintSpeaker` gibt Text aus. Import-gekapselt.

Streaming-Trick: LLM-Antwort satzweise puffern und sofort sprechen.
"""
from __future__ import annotations

import re
from typing import Iterator, Protocol


class Speaker(Protocol):
    def say(self, text: str) -> None: ...


class PrintSpeaker:
    """Fallback: schreibt die Antwort statt sie zu sprechen."""

    def say(self, text: str) -> None:
        print(f"Jarvis: {text}")


class PiperTTS:
    """Piper-Wrapper (deutsche Thorsten-Stimme)."""

    def __init__(self, model_path: str = "de_DE-thorsten-high.onnx") -> None:
        self.model_path = model_path
        self._voice = None

    def _load(self):  # pragma: no cover - benötigt piper + Modell
        if self._voice is None:
            try:
                from piper.voice import PiperVoice  # type: ignore
            except ImportError as exc:
                raise RuntimeError("`pip install piper-tts` und Thorsten-Modell erforderlich.") from exc
            self._voice = PiperVoice.load(self.model_path)
        return self._voice

    def say(self, text: str) -> None:  # pragma: no cover
        import sounddevice as sd  # type: ignore
        voice = self._load()
        for chunk in voice.synthesize_stream_raw(text):
            import numpy as np  # type: ignore
            audio = np.frombuffer(chunk, dtype="int16")
            sd.play(audio, samplerate=voice.config.sample_rate)
            sd.wait()


class ElevenLabsTTS:
    """Optionaler Premium-Modus (Cloud). Daten verlassen das Gerät – DSGVO beachten."""

    def __init__(self, voice_id: str = "", model: str = "eleven_flash_v2_5") -> None:
        self.voice_id = voice_id
        self.model = model

    def say(self, text: str) -> None:  # pragma: no cover
        import os
        try:
            from elevenlabs.client import ElevenLabs  # type: ignore
            from elevenlabs import play  # type: ignore
        except ImportError as exc:
            raise RuntimeError("`pip install elevenlabs` erforderlich.") from exc
        client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
        audio = client.text_to_speech.convert(voice_id=self.voice_id, model_id=self.model, text=text)
        play(audio)


def sentences(text: str) -> Iterator[str]:
    """Zerlegt Text in Sätze (für satzweises Streaming an den Speaker)."""
    for part in re.split(r"(?<=[.!?])\s+", text.strip()):
        if part.strip():
            yield part.strip()


def speak_streaming(speaker: Speaker, text: str) -> None:
    """Spricht satzweise – der erste Satz kommt sofort."""
    for sentence in sentences(text):
        speaker.say(sentence)
