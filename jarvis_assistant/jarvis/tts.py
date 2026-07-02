"""Text→Sprache. ElevenLabs (Film-Stimme) mit SAPI5-Fallback und Konsole (Test).

Reihenfolge: ElevenLabs → (bei Fehler) Windows-SAPI5 → (sonst) Konsolenausgabe.
"""

from __future__ import annotations

from typing import Optional, Protocol


class Speaker(Protocol):
    def say(self, text: str) -> None:
        ...


class ConsoleSpeaker:
    """Fallback/Test: gibt die Antwort als Text aus."""

    def say(self, text: str) -> None:
        print(f"Jarvis> {text}")


class Sapi5Speaker:
    """Windows-Bordmittel (offline). Notfall-Fallback."""

    def say(self, text: str) -> None:
        try:
            import pyttsx3  # lazy
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except Exception:  # noqa: BLE001
            print(f"Jarvis> {text}")


class ElevenLabsSpeaker:
    """ElevenLabs-TTS mit automatischem Fallback."""

    def __init__(self, api_key: str, voice_id: str = "Rachel",
                 fallback: bool = True):
        self.api_key = api_key
        self.voice_id = voice_id
        self.fallback = fallback
        self._sapi = Sapi5Speaker()
        self._console = ConsoleSpeaker()

    def say(self, text: str) -> None:
        if not text:
            return
        if not self.api_key:
            return self._fallback(text)
        try:
            import httpx  # lazy
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            r = httpx.post(url, timeout=30.0,
                           headers={"xi-api-key": self.api_key,
                                    "Content-Type": "application/json"},
                           json={"text": text, "model_id": "eleven_multilingual_v2"})
            r.raise_for_status()
            self._play(r.content)
        except Exception as exc:  # noqa: BLE001
            from .audit import log
            log(f"ElevenLabs-Fehler, nutze Fallback: {exc}", "warning")
            self._fallback(text)

    def _play(self, mp3_bytes: bytes) -> None:
        import io
        try:
            from playsound import playsound  # optional
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(mp3_bytes)
                path = f.name
            playsound(path)
        except Exception:  # noqa: BLE001
            # Ohne Player: über simpleaudio/pydub versuchen, sonst aufgeben.
            try:
                from pydub import AudioSegment
                from pydub.playback import play
                play(AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3"))
            except Exception:  # noqa: BLE001
                pass

    def _fallback(self, text: str) -> None:
        if self.fallback:
            self._sapi.say(text)
        else:
            self._console.say(text)
