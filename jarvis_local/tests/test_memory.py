import tempfile
import unittest

from jarvis.memory.obsidian import ObsidianVault, WIKI
from jarvis.memory.vector_index import HashingEmbedder, VectorIndex


class TestObsidian(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.vault = ObsidianVault(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_write_read_roundtrip(self):
        note = self.vault.write_note(
            "ConsentFlow Preise", "Starter kostet 29 Euro pro Monat.",
            folder=WIKI, topics=["consentflow", "preise"], importance=4,
        )
        loaded = self.vault.read_note(note.path)
        self.assertEqual(loaded.frontmatter["title"], "ConsentFlow Preise")
        self.assertEqual(loaded.frontmatter["importance"], 4)          # int geparst
        self.assertEqual(loaded.frontmatter["topics"], ["consentflow", "preise"])  # Liste geparst
        self.assertIn("29 Euro", loaded.body)

    def test_search_ranks_relevant_first(self):
        self.vault.write_note("Kunde Meier", "Meier will einen roten Banner.", topics=["kunde"])
        self.vault.write_note("Kunde Schulz", "Schulz nutzt Statistik-Cookies.", topics=["kunde"])
        hits = self.vault.search("roter Banner Meier")
        self.assertTrue(hits)
        self.assertEqual(hits[0].title, "Kunde Meier")

    def test_wikilinks_and_resolve(self):
        self.vault.write_note("Projekt Jarvis", "Siehe [[ConsentFlow Preise]].")
        target = self.vault.write_note("ConsentFlow Preise", "29 Euro.")
        src = self.vault.search("Projekt Jarvis")[0]
        self.assertEqual(src.wikilinks(), ["ConsentFlow Preise"])
        self.assertIsNotNone(self.vault.resolve_link("ConsentFlow Preise"))


class TestVectorIndex(unittest.TestCase):
    def test_semantic_hits_return_relevant_doc(self):
        idx = VectorIndex(":memory:", embedder=HashingEmbedder(dim=128))
        idx.add("d1", "Der Cookie-Banner blockiert Skripte bis zur Einwilligung.")
        idx.add("d2", "Das Wetter morgen wird sonnig und warm.")
        hits = idx.search("cookie einwilligung banner")
        self.assertEqual(len(idx), 2)
        self.assertEqual(hits[0].doc_id, "d1")


if __name__ == "__main__":
    unittest.main()
