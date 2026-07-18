"""
JARVIS V6 — Tier-based permission system.

The existing night-shift tasks are gated by a single ``dry_run`` / ``confirm_live``
switch. The interactive capabilities (browser task execution, briefing) need a
finer, per-action model — the one described in the spec:

  * ``read`` / ``suggest``  → run automatically. They are reversible and move no
    money: opening a page, reading it, searching, filling a cart, drafting text.
  * ``send`` / ``spend`` / ``delete`` / ``publish`` → require an explicit
    confirmation before they run. Anything that spends money, sends something
    out, removes data or publishes to the world stops and asks first.

This module is pure standard library and fully testable offline: the actual
confirmation is an injected callable, so tests use a fake and the web/voice
layer wires in a real "ask Jonas" prompt. With no confirm function wired in,
the safe default is to **refuse** confirmation-tier actions rather than perform
them unattended.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional


class Tier(str, Enum):
    """Permission tiers, from freely-automatic to must-confirm."""

    READ = "read"          # look at something (page content, inbox, dashboard)
    SUGGEST = "suggest"    # prepare/draft something reversible (search, cart, type)
    SEND = "send"          # send a message / submit a form outward
    SPEND = "spend"        # move money (checkout, "jetzt kaufen", pay)
    DELETE = "delete"      # remove data irreversibly
    PUBLISH = "publish"    # publish to the world


#: Tiers that run without asking — reversible, no money moved, nothing sent out.
AUTO_TIERS = frozenset({Tier.READ, Tier.SUGGEST})
#: Tiers that always require an explicit confirmation before execution.
CONFIRM_TIERS = frozenset({Tier.SEND, Tier.SPEND, Tier.DELETE, Tier.PUBLISH})


class PermissionDenied(RuntimeError):
    """Raised by :meth:`PermissionManager.require` when an action is refused."""

    def __init__(self, decision: "Decision"):
        self.decision = decision
        super().__init__(decision.reason)


@dataclass
class Decision:
    """The outcome of a permission check — safe to log and surface to the user."""

    allowed: bool
    tier: Tier
    action: str
    reason: str
    needed_confirmation: bool = False

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "tier": self.tier.value,
            "action": self.action,
            "reason": self.reason,
            "needed_confirmation": self.needed_confirmation,
        }


#: An injected confirmation prompt: given (tier, action) return True to allow.
ConfirmFn = Callable[[Tier, str], bool]


class PermissionManager:
    """Decide whether an action of a given tier may run.

    Parameters
    ----------
    confirm_fn:
        Called for confirmation-tier actions with ``(tier, action)``; return
        True to allow. If omitted, confirmation-tier actions are **refused**
        (the safe default — nothing money-moving happens unattended).
    auto_approve:
        Test/automation escape hatch: when True, every tier is allowed without
        calling ``confirm_fn``. Never set this in an unattended live path.
    """

    def __init__(self, confirm_fn: Optional[ConfirmFn] = None,
                 auto_approve: bool = False):
        self.confirm_fn = confirm_fn
        self.auto_approve = auto_approve

    def check(self, tier: Tier, action: str) -> Decision:
        """Return a :class:`Decision` for ``tier``/``action`` (never raises)."""
        if tier in AUTO_TIERS:
            return Decision(True, tier, action,
                            reason=f"{tier.value}-Tier läuft automatisch.")

        # Confirmation tier from here on.
        if self.auto_approve:
            return Decision(True, tier, action, needed_confirmation=True,
                            reason=f"{tier.value}-Tier automatisch freigegeben (auto_approve).")

        if self.confirm_fn is None:
            return Decision(False, tier, action, needed_confirmation=True,
                            reason=(f"{tier.value}-Tier braucht eine Bestätigung, aber es ist "
                                    f"kein Bestätigungsweg angebunden — abgelehnt."))

        try:
            approved = bool(self.confirm_fn(tier, action))
        except Exception as exc:  # noqa: BLE001 - a failing prompt must not crash the agent
            return Decision(False, tier, action, needed_confirmation=True,
                            reason=f"Bestätigung fehlgeschlagen ({exc}) — abgelehnt.")

        if approved:
            return Decision(True, tier, action, needed_confirmation=True,
                            reason=f"{tier.value}-Tier von Jonas bestätigt.")
        return Decision(False, tier, action, needed_confirmation=True,
                        reason=f"{tier.value}-Tier von Jonas abgelehnt.")

    def require(self, tier: Tier, action: str) -> Decision:
        """Like :meth:`check`, but raise :class:`PermissionDenied` if refused."""
        decision = self.check(tier, action)
        if not decision.allowed:
            raise PermissionDenied(decision)
        return decision
