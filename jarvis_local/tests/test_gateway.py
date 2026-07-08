import tempfile
import unittest
from pathlib import Path

from jarvis.security.audit_log import AuditLog
from jarvis.security.permission_gateway import (
    Action, ApprovalStatus, EffectCategory, PermissionError_, PermissionGateway, RiskTier,
)


def _action(effect=EffectCategory.SPEND, tool="shop_purchase"):
    return Action(tool=tool, effect=effect, intent="Kauf: Buch für 20 €", args={"item": "Buch", "price_eur": 20})


class TestClassification(unittest.TestCase):
    def test_read_and_suggest_are_tier0(self):
        self.assertEqual(PermissionGateway.classify(EffectCategory.READ), RiskTier.TIER0)
        self.assertEqual(PermissionGateway.classify(EffectCategory.SUGGEST), RiskTier.TIER0)

    def test_side_effects_are_tier1(self):
        for eff in (EffectCategory.SEND, EffectCategory.SPEND, EffectCategory.DELETE, EffectCategory.PUBLISH):
            self.assertEqual(PermissionGateway.classify(eff), RiskTier.TIER1)


class TestAuthorize(unittest.TestCase):
    def setUp(self):
        self.gw = PermissionGateway(":memory:")

    def test_tier0_auto_approved(self):
        d = self.gw.authorize(Action("memory_search", EffectCategory.READ, "suchen"))
        self.assertTrue(d.allowed)
        self.assertEqual(d.status, ApprovalStatus.APPROVED)

    def test_tier1_pending_without_approver(self):
        d = self.gw.authorize(_action())
        self.assertFalse(d.allowed)
        self.assertEqual(d.status, ApprovalStatus.PENDING)
        self.assertEqual(len(self.gw.list_pending()), 1)

    def test_tier1_approved_with_approver(self):
        d = self.gw.authorize(_action(), approver=lambda a: True)
        self.assertTrue(d.allowed)
        self.assertEqual(self.gw.status_of(d.approval_id), ApprovalStatus.APPROVED)

    def test_tier1_denied_with_approver(self):
        d = self.gw.authorize(_action(), approver=lambda a: False)
        self.assertFalse(d.allowed)
        self.assertEqual(self.gw.status_of(d.approval_id), ApprovalStatus.DENIED)

    def test_guard_raises_when_not_allowed(self):
        with self.assertRaises(PermissionError_):
            self.gw.guard(_action(), approver=lambda a: False)

    def test_double_decision_rejected(self):
        d = self.gw.authorize(_action())
        self.gw.approve(d.approval_id)
        with self.assertRaises(ValueError):
            self.gw.deny(d.approval_id)


class TestDurability(unittest.TestCase):
    def test_pending_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "approvals.sqlite3"
            gw1 = PermissionGateway(db)
            d = gw1.authorize(_action())
            gw1.close()

            # Neustart simulieren: neue Instanz, gleiche Datei.
            gw2 = PermissionGateway(db)
            pending = gw2.list_pending()
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0]["id"], d.approval_id)
            gw2.approve(d.approval_id)
            self.assertEqual(gw2.status_of(d.approval_id), ApprovalStatus.APPROVED)


class TestAuditIntegration(unittest.TestCase):
    def test_spend_is_audited_as_tier1(self):
        audit = AuditLog(":memory:")
        gw = PermissionGateway(":memory:", audit=audit)
        gw.authorize(_action())
        kinds = [e.kind for e in audit.entries()]
        self.assertIn("approval_requested", kinds)


if __name__ == "__main__":
    unittest.main()
