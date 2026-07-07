"""Permission Gateway – risiko-gestufte Freigabe im Policy-Layer.

Kernprinzip (Leitfaden Abschnitt H): *Der Agent schlägt vor, das Gateway
entscheidet.* Jede Aktion mit Nebenwirkung wird nach Risiko-Tier klassifiziert:

* **Tier 0** (read / suggest): läuft automatisch.
* **Tier 1** (send / spend / delete / publish): wird **physisch angehalten**.
  Die Ausführung erhält einen durable ``pending_approval``-Zustand (SQLite,
  überlebt Neustart) und wird erst freigegeben, wenn Jonas ausdrücklich
  zustimmt.

Geld auszugeben ist ``EffectCategory.SPEND`` → immer Tier 1 → immer Bestätigung.
"""
from __future__ import annotations

import enum
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .audit_log import AuditLog


class RiskTier(enum.IntEnum):
    TIER0 = 0  # read / suggest → automatisch
    TIER1 = 1  # send / spend / delete / publish → Freigabe nötig


class EffectCategory(str, enum.Enum):
    READ = "read"
    SUGGEST = "suggest"
    SEND = "send"
    SPEND = "spend"
    DELETE = "delete"
    PUBLISH = "publish"


# Welche Wirkungs-Kategorien eine synchrone Freigabe erzwingen.
TIER1_EFFECTS: frozenset[EffectCategory] = frozenset(
    {EffectCategory.SEND, EffectCategory.SPEND, EffectCategory.DELETE, EffectCategory.PUBLISH}
)


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class PermissionError_(Exception):
    """Aktion wurde abgelehnt oder wartet ohne Entscheider auf Freigabe."""


@dataclass(frozen=True)
class Action:
    """Eine vom Agenten vorgeschlagene Aktion mit Nebenwirkung."""

    tool: str
    effect: EffectCategory
    intent: str                       # menschenlesbare Absicht ("E-Mail an X senden")
    args: dict[str, Any] = field(default_factory=dict)
    expected_result: str = ""         # was passieren wird
    rollback: str = ""                # wie rückgängig zu machen


@dataclass
class Decision:
    approval_id: str
    tier: RiskTier
    status: ApprovalStatus
    action: Action

    @property
    def allowed(self) -> bool:
        return self.status is ApprovalStatus.APPROVED


_SCHEMA = """
CREATE TABLE IF NOT EXISTS pending_approvals (
    id           TEXT PRIMARY KEY,
    created_at   REAL NOT NULL,
    tool         TEXT NOT NULL,
    effect       TEXT NOT NULL,
    intent       TEXT NOT NULL,
    args         TEXT NOT NULL,       -- JSON
    expected     TEXT,
    rollback     TEXT,
    status       TEXT NOT NULL,       -- pending | approved | denied
    decided_at   REAL,
    decided_by   TEXT,
    reason       TEXT
);
"""


class PermissionGateway:
    """Zentraler Policy-Layer. Klassifiziert und hält Tier-1-Aktionen an."""

    def __init__(
        self,
        db_path: str | Path = ":memory:",
        audit: AuditLog | None = None,
    ) -> None:
        self._path = str(db_path)
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        self.audit = audit or AuditLog(":memory:")

    # ---- Klassifikation ----
    @staticmethod
    def classify(effect: EffectCategory) -> RiskTier:
        return RiskTier.TIER1 if effect in TIER1_EFFECTS else RiskTier.TIER0

    # ---- Kern: Autorisierung ----
    def authorize(
        self,
        action: Action,
        approver: Callable[[Action], bool] | None = None,
    ) -> Decision:
        """Entscheidet über eine Aktion.

        * Tier 0 → sofort erlaubt (nur Audit).
        * Tier 1 → durable pending_approval anlegen. Ist ein ``approver``
          gegeben (z. B. Sprach-Rückfrage »Ja, senden«), wird synchron
          gefragt. Ohne Entscheider bleibt die Aktion PENDING und muss
          out-of-band über :meth:`approve` freigegeben werden.
        """
        tier = self.classify(action.effect)
        if tier is RiskTier.TIER0:
            self.audit.record(
                "authorized", tool=action.tool, tier="TIER0", status="allowed",
                intent=action.intent, effect=action.effect.value,
            )
            return Decision(_new_id(), tier, ApprovalStatus.APPROVED, action)

        # Tier 1: physisch anhalten → durable pending_approval
        approval_id = self._create_pending(action)
        self.audit.record(
            "approval_requested", tool=action.tool, tier="TIER1", status="pending",
            approval_id=approval_id, intent=action.intent, effect=action.effect.value,
            expected=action.expected_result,
        )

        if approver is None:
            # Kein synchroner Entscheider → bleibt hängen (Constraint, kein Vorschlag).
            return Decision(approval_id, tier, ApprovalStatus.PENDING, action)

        ok = bool(approver(action))
        if ok:
            self.approve(approval_id, by="approver")
        else:
            self.deny(approval_id, by="approver", reason="vom Entscheider abgelehnt")
        return Decision(
            approval_id, tier,
            ApprovalStatus.APPROVED if ok else ApprovalStatus.DENIED,
            action,
        )

    def guard(self, action: Action, approver: Callable[[Action], bool] | None = None) -> Decision:
        """Wie :meth:`authorize`, wirft aber bei Nicht-Freigabe.

        Nutzbar als harte Schranke direkt vor der Tool-Ausführung.
        """
        decision = self.authorize(action, approver)
        if not decision.allowed:
            raise PermissionError_(
                f"Aktion '{action.tool}' nicht freigegeben (Status: {decision.status.value}, "
                f"Freigabe-ID: {decision.approval_id})."
            )
        return decision

    # ---- Freigabe-Verwaltung (out-of-band, durable) ----
    def approve(self, approval_id: str, by: str = "jonas") -> None:
        self._decide(approval_id, ApprovalStatus.APPROVED, by, None)
        row = self.get(approval_id)
        self.audit.record(
            "approved", tool=row["tool"] if row else None, tier="TIER1",
            status="approved", approval_id=approval_id, by=by,
        )

    def deny(self, approval_id: str, by: str = "jonas", reason: str = "") -> None:
        self._decide(approval_id, ApprovalStatus.DENIED, by, reason)
        row = self.get(approval_id)
        self.audit.record(
            "denied", tool=row["tool"] if row else None, tier="TIER1",
            status="denied", approval_id=approval_id, by=by, reason=reason,
        )

    def list_pending(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM pending_approvals WHERE status = ? ORDER BY created_at ASC",
            (ApprovalStatus.PENDING.value,),
        ).fetchall()
        return [self._as_dict(r) for r in rows]

    def get(self, approval_id: str) -> dict[str, Any] | None:
        r = self._conn.execute(
            "SELECT * FROM pending_approvals WHERE id = ?", (approval_id,)
        ).fetchone()
        return self._as_dict(r) if r else None

    def status_of(self, approval_id: str) -> ApprovalStatus | None:
        row = self.get(approval_id)
        return ApprovalStatus(row["status"]) if row else None

    # ---- intern ----
    def _create_pending(self, action: Action) -> str:
        approval_id = _new_id()
        self._conn.execute(
            """INSERT INTO pending_approvals
               (id, created_at, tool, effect, intent, args, expected, rollback, status)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                approval_id, time.time(), action.tool, action.effect.value, action.intent,
                json.dumps(action.args, ensure_ascii=False, default=str),
                action.expected_result, action.rollback, ApprovalStatus.PENDING.value,
            ),
        )
        self._conn.commit()
        return approval_id

    def _decide(self, approval_id: str, status: ApprovalStatus, by: str, reason: str | None) -> None:
        row = self.get(approval_id)
        if row is None:
            raise KeyError(f"Unbekannte Freigabe-ID: {approval_id}")
        if row["status"] != ApprovalStatus.PENDING.value:
            raise ValueError(
                f"Freigabe {approval_id} ist bereits '{row['status']}' – keine erneute Entscheidung."
            )
        self._conn.execute(
            "UPDATE pending_approvals SET status=?, decided_at=?, decided_by=?, reason=? WHERE id=?",
            (status.value, time.time(), by, reason, approval_id),
        )
        self._conn.commit()

    @staticmethod
    def _as_dict(r: sqlite3.Row) -> dict[str, Any]:
        d = dict(r)
        if d.get("args"):
            d["args"] = json.loads(d["args"])
        return d

    def close(self) -> None:
        self._conn.close()


def _new_id() -> str:
    return "apr_" + uuid.uuid4().hex[:16]
