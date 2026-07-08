import tempfile
import unittest
from pathlib import Path

from jarvis.app import build_app
from jarvis.config import Config
from jarvis.core.demo_backend import demo_responder
from jarvis.core.llm import ScriptedBackend, final, tool_call


def _app(backend):
    tmp = tempfile.TemporaryDirectory()
    cfg = Config(data_dir=Path(tmp.name), vault_dir=Path(tmp.name) / "vault")
    app = build_app(cfg, backend, persist=False)
    app._tmp = tmp  # am Leben halten
    return app


class TestTier0Flow(unittest.TestCase):
    def test_memory_write_executes_without_approval(self):
        backend = ScriptedBackend(scripted=[
            tool_call("memory_write", text="Kunde Meier mag blau."),
            final("Habe ich mir notiert."),
        ])
        app = _app(backend)
        result = app.agent.run("merke dir das", approver=None)
        self.assertEqual(result.reply, "Habe ich mir notiert.")
        self.assertEqual(result.pending_approvals, [])
        self.assertTrue(app.vault.search("Meier blau"))  # Notiz wurde wirklich geschrieben


class TestTier1MoneyGate(unittest.TestCase):
    def test_purchase_requires_and_gets_approval(self):
        backend = ScriptedBackend(scripted=[
            tool_call("shop_purchase", item="Fachbuch", price_eur=20),
            final("Erledigt."),
        ])
        app = _app(backend)
        result = app.agent.run("kauf das für mich", approver=lambda a: True)
        joined = " ".join(m.get("content", "") for m in result.transcript)
        self.assertIn("Gekauft: Fachbuch", joined)
        self.assertEqual(app.gateway.list_pending(), [])  # nichts bleibt offen

    def test_purchase_blocked_without_approver(self):
        backend = ScriptedBackend(scripted=[
            tool_call("shop_purchase", item="Fachbuch", price_eur=20),
            final("Ich warte auf deine Freigabe."),
        ])
        app = _app(backend)
        result = app.agent.run("kauf das für mich", approver=None)
        self.assertEqual(len(result.pending_approvals), 1)
        self.assertEqual(len(app.gateway.list_pending()), 1)  # durable pending
        joined = " ".join(m.get("content", "") for m in result.transcript)
        self.assertNotIn("Gekauft", joined)  # NICHT ausgeführt

    def test_purchase_denied(self):
        backend = ScriptedBackend(scripted=[
            tool_call("shop_purchase", item="Fachbuch", price_eur=20),
            final("Okay, kein Kauf."),
        ])
        app = _app(backend)
        result = app.agent.run("kauf das für mich", approver=lambda a: False)
        joined = " ".join(m.get("content", "") for m in result.transcript)
        self.assertIn("abgelehnt", joined.lower())
        self.assertNotIn("Gekauft", joined)


class TestDemoBackendEndToEnd(unittest.TestCase):
    def test_note_then_purchase_with_demo_responder(self):
        app = _app(ScriptedBackend(responder=demo_responder))
        r1 = app.agent.run("merke dir: Kunde Meier mag blau", approver=None)
        self.assertIn("gespeichert", r1.reply.lower())
        self.assertTrue(app.vault.search("Meier"))

        r2 = app.agent.run("kaufe ein Fachbuch für 20 Euro", approver=lambda a: True)
        self.assertIn("Gekauft", r2.reply)


if __name__ == "__main__":
    unittest.main()
