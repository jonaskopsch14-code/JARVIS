"""Append-only Audit-Trail für jede sicherheitsrelevante Entscheidung.

Jede Aktion mit Nebenwirkung – und jede Freigabe/Ablehnung – wird hier
protokolliert. Reines stdlib-SQLite, keine externen Abhängigkeiten, damit der
Audit-Pfad auch dann funktioniert, wenn sonst nichts installiert ist.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


_SCHEMA = """
CREATE TABLE IF NOT EXISTS audit (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         REAL    NOT NULL,
    kind       TEXT    NOT NULL,   -- z.B. tool_call, approval_requested, approved, denied, executed, error
    tool       TEXT,
    tier       TEXT,
    status     TEXT,
    detail     TEXT               -- JSON
);
"""


@dataclass(frozen=True)
class AuditEntry:
    id: int
    ts: float
    kind: str
    tool: str | None
    tier: str | None
    status: str | None
    detail: dict[str, Any]


class AuditLog:
    """Schreibgeschütztes (nur anhängbares) Protokoll auf SQLite-Basis."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._path = str(db_path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False, damit Voice-Loop und Approval-CLI dieselbe DB teilen können.
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def record(
        self,
        kind: str,
        *,
        tool: str | None = None,
        tier: str | None = None,
        status: str | None = None,
        **detail: Any,
    ) -> int:
        cur = self._conn.execute(
            "INSERT INTO audit (ts, kind, tool, tier, status, detail) VALUES (?,?,?,?,?,?)",
            (time.time(), kind, tool, tier, status, json.dumps(detail, ensure_ascii=False, default=str)),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def entries(self, limit: int | None = None) -> list[AuditEntry]:
        sql = "SELECT * FROM audit ORDER BY id DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows: Iterable[sqlite3.Row] = self._conn.execute(sql).fetchall()
        return [self._row(r) for r in rows]

    @staticmethod
    def _row(r: sqlite3.Row) -> AuditEntry:
        return AuditEntry(
            id=r["id"], ts=r["ts"], kind=r["kind"], tool=r["tool"],
            tier=r["tier"], status=r["status"],
            detail=json.loads(r["detail"]) if r["detail"] else {},
        )

    def close(self) -> None:
        self._conn.close()
