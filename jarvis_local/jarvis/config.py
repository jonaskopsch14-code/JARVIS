"""Zentrale Konfiguration (env-getrieben)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass
class Config:
    data_dir: Path
    vault_dir: Path
    # LLM
    ollama_model: str = "qwen3:8b"
    ollama_host: str = "http://localhost:11434"
    temperature: float = 0.0
    num_ctx: int = 16384
    # Voice
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    piper_model: str = "de_DE-thorsten-high.onnx"

    @property
    def audit_db(self) -> Path:
        return self.data_dir / "audit.sqlite3"

    @property
    def approvals_db(self) -> Path:
        return self.data_dir / "approvals.sqlite3"

    @property
    def vector_db(self) -> Path:
        return self.data_dir / "vectors.sqlite3"

    @classmethod
    def from_env(cls) -> "Config":
        data_dir = Path(_env("JARVIS_DATA_DIR", str(Path.home() / ".jarvis")))
        vault_dir = Path(_env("JARVIS_VAULT_DIR", str(data_dir / "vault")))
        return cls(
            data_dir=data_dir,
            vault_dir=vault_dir,
            ollama_model=_env("JARVIS_OLLAMA_MODEL", "qwen3:8b"),
            ollama_host=_env("JARVIS_OLLAMA_HOST", "http://localhost:11434"),
            temperature=float(_env("JARVIS_TEMPERATURE", "0.0")),
            num_ctx=int(_env("JARVIS_NUM_CTX", "16384")),
            whisper_model=_env("JARVIS_WHISPER_MODEL", "large-v3"),
            whisper_device=_env("JARVIS_WHISPER_DEVICE", "cuda"),
            piper_model=_env("JARVIS_PIPER_MODEL", "de_DE-thorsten-high.onnx"),
        )

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
