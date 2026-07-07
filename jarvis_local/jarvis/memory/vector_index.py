"""Semantischer Index (Hybrid-Ergänzung zum Markdown-Vault).

Der Leitfaden empfiehlt Markdown als Wahrheit + optionalen Vektor-Index, sobald
der Vault wächst. Diese Umsetzung ist bewusst abhängigkeitsfrei lauffähig:

* ``HashingEmbedder`` – deterministisches Bag-of-Words-Embedding (reines Python),
  damit Index/Suche und Tests ohne Ollama funktionieren.
* ``OllamaEmbedder`` – ``nomic-embed-text`` über Ollama (gekapselter Import).

Der Store hält Vektoren in SQLite und rankt per Cosinus-Ähnlichkeit.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

_SCHEMA = """
CREATE TABLE IF NOT EXISTS vectors (
    doc_id TEXT PRIMARY KEY,
    text   TEXT NOT NULL,
    vec    TEXT NOT NULL   -- JSON-Liste floats
);
"""


class Embedder(Protocol):
    dim: int
    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """Deterministisches, dependency-freies Embedding (Hashing-Trick)."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for token in re.findall(r"\w+", text.lower()):
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            vec[h % self.dim] += 1.0
        return _normalize(vec)


class OllamaEmbedder:
    """Echte Embeddings über Ollama (nomic-embed-text). Import gekapselt."""

    def __init__(self, model: str = "nomic-embed-text", host: str = "http://localhost:11434", dim: int = 768) -> None:
        self.model = model
        self.host = host
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        try:
            import ollama  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("`pip install ollama` und `ollama pull nomic-embed-text`.") from exc
        client = ollama.Client(host=self.host)
        resp = client.embeddings(model=self.model, prompt=text)
        return _normalize(list(resp["embedding"]))


@dataclass
class SearchHit:
    doc_id: str
    text: str
    score: float


class VectorIndex:
    def __init__(self, db_path: str | Path = ":memory:", embedder: Embedder | None = None) -> None:
        self.embedder: Embedder = embedder or HashingEmbedder()
        self._path = str(db_path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def add(self, doc_id: str, text: str) -> None:
        vec = self.embedder.embed(text)
        self._conn.execute(
            "INSERT OR REPLACE INTO vectors (doc_id, text, vec) VALUES (?,?,?)",
            (doc_id, text, json.dumps(vec)),
        )
        self._conn.commit()

    def search(self, query: str, limit: int = 5) -> list[SearchHit]:
        q = self.embedder.embed(query)
        hits: list[SearchHit] = []
        for row in self._conn.execute("SELECT doc_id, text, vec FROM vectors").fetchall():
            score = _cosine(q, json.loads(row["vec"]))
            hits.append(SearchHit(row["doc_id"], row["text"], score))
        hits.sort(key=lambda h: h.score, reverse=True)
        return [h for h in hits[:limit] if h.score > 0]

    def __len__(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0])

    def close(self) -> None:
        self._conn.close()


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm else vec


def _cosine(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    return sum(a[i] * b[i] for i in range(n))
