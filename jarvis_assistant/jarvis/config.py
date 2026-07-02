"""Konfiguration: lädt aus config.json (+ Umgebungsvariablen als Override).

Dependency-frei und testbar. Echte Secrets (ElevenLabs-Key) kommen aus
config.json / Env — nie in den Code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


def _default_data_dir() -> Path:
    # Unter Windows landet das in %APPDATA%\Jarvis, sonst ~/.jarvis
    base = os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "Jarvis"


@dataclass
class Config:
    # --- LLM (lokal über Ollama) ---
    model: str = "qwen2.5:7b-instruct"        # konfigurierbar; muss ein echter Ollama-Tag sein
    ollama_url: str = "http://127.0.0.1:11434"
    temperature: float = 0.6

    # --- Stimme raus (ElevenLabs, Fallback SAPI5) ---
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "Rachel"       # Beispiel; eigene Voice-ID eintragen
    tts_fallback: bool = True                  # bei ElevenLabs-Fehler SAPI5 nutzen

    # --- Sprache rein (faster-whisper) ---
    whisper_model: str = "small"
    language: str = "de"
    silence_stop_ms: int = 900                 # Auto-Stopp nach dieser Stille

    # --- Bedienung ---
    hotkey: str = "ctrl+alt+j"                 # Push-to-Talk
    panic_hotkey: str = "ctrl+alt+pause"       # Not-Aus
    wakeword_enabled: bool = False             # Phase 6
    wakeword: str = "jarvis"

    # --- Ort für Wetter ---
    city: str = "Berlin"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # --- Anrede/Persönlichkeit ---
    user_name: str = "Jonas"

    # --- Shopify (Phase 5; leer = Shop-Wächter aus) ---
    shopify_domain: str = ""
    shopify_token: str = ""

    # --- Proaktivität (Phase 4) ---
    morning_briefing_time: str = "08:00"
    proactive_enabled: bool = True

    # --- Ablage ---
    data_dir: Path = field(default_factory=_default_data_dir)

    # ----------------------------------------------------------------------
    @property
    def calendar_file(self) -> Path:
        return self.data_dir / "heute.md"

    @property
    def memory_db(self) -> Path:
        return self.data_dir / "memory.sqlite3"

    @property
    def log_file(self) -> Path:
        return self.data_dir / "logs" / "jarvis.log"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------------
    @classmethod
    def load(cls, path: Optional[str] = None) -> "Config":
        """Lädt config.json (falls vorhanden) und überschreibt mit JARVIS_*-Env."""
        cfg = cls()
        p = Path(path) if path else Path("config.json")
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if hasattr(cfg, k) and v is not None:
                        setattr(cfg, k, v)
            except (OSError, ValueError):
                pass
        # Env-Overrides: JARVIS_MODEL, JARVIS_ELEVENLABS_API_KEY, …
        for k in vars(cfg):
            env = os.getenv("JARVIS_" + k.upper())
            if env is not None:
                cur = getattr(cfg, k)
                try:
                    if isinstance(cur, bool):
                        setattr(cfg, k, env not in ("0", "false", "False", ""))
                    elif isinstance(cur, int):
                        setattr(cfg, k, int(env))
                    elif isinstance(cur, float):
                        setattr(cfg, k, float(env))
                    else:
                        setattr(cfg, k, env)
                except ValueError:
                    setattr(cfg, k, env)
        if isinstance(cfg.data_dir, str):
            cfg.data_dir = Path(cfg.data_dir)
        return cfg

    def to_public_dict(self) -> dict:
        """Wie asdict, aber Secrets maskiert (für Logs/Anzeige)."""
        d = asdict(self)
        d["data_dir"] = str(self.data_dir)
        if d.get("elevenlabs_api_key"):
            d["elevenlabs_api_key"] = "***"
        if d.get("shopify_token"):
            d["shopify_token"] = "***"
        return d
