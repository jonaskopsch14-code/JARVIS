import base64
import email
import tempfile
import unittest

from jarvis.memory.obsidian import ObsidianVault
from jarvis.memory.vector_index import VectorIndex
from jarvis.tools.gmail_tool import GMAIL_SCOPES, build_draft_raw
from jarvis.tools.memory_tool import build_memory_tools


class TestGmailDraft(unittest.TestCase):
    def test_no_send_scope(self):
        # Sicherheitsprinzip: niemals gmail.send anfordern.
        self.assertFalse(any("gmail.send" in s for s in GMAIL_SCOPES))
        self.assertTrue(any("gmail.compose" in s for s in GMAIL_SCOPES))

    def test_build_draft_raw_roundtrip(self):
        raw = build_draft_raw("kunde@example.de", "Angebot", "Hallo, anbei das Angebot. Grüße")
        decoded = base64.urlsafe_b64decode(raw.encode("ascii"))
        msg = email.message_from_bytes(decoded)
        self.assertEqual(msg["To"], "kunde@example.de")
        self.assertEqual(msg["Subject"], "Angebot")
        self.assertIn("Angebot", msg.get_payload(decode=True).decode("utf-8"))


class TestMemoryTools(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = ObsidianVault(self._tmp.name)
        self.index = VectorIndex(":memory:")
        self.tools = {t.name: t for t in build_memory_tools(self.vault, self.index)}

    def tearDown(self):
        self._tmp.cleanup()

    def test_write_then_search(self):
        w = self.tools["memory_write"].run(text="Kunde Meier will einen blauen Banner.", topics="kunde")
        self.assertTrue(w.ok)
        self.assertEqual(len(self.index), 1)  # auch in den Vektor-Index geschrieben
        s = self.tools["memory_search"].run(query="blauer Banner Meier")
        self.assertIn("Meier", s.content)

    def test_write_tool_is_tier0_suggest(self):
        from jarvis.security.permission_gateway import EffectCategory
        self.assertEqual(self.tools["memory_write"].effect, EffectCategory.SUGGEST)
        self.assertEqual(self.tools["memory_search"].effect, EffectCategory.READ)


if __name__ == "__main__":
    unittest.main()
