"""Every wikipedia-derived row must have its source revision pinned.

The rows were harvested with generator=random, so they cannot be regenerated; the only
honest provenance is the revision id and MediaWiki's sha1 of that revision's content.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "pin_wikipedia_sources.py"
MANIFEST = ROOT / "datasets" / "manifests" / "wikipedia_sources_v0.2.json"


class WikipediaSources(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_manifest_covers_every_row(self):
        done = subprocess.run([sys.executable, str(TOOL), "--check"],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_every_entry_has_a_revision_and_a_hash(self):
        for group in self.manifest["files"].values():
            for entry in group:
                self.assertTrue(entry.get("revid"), entry)
                self.assertRegex(entry.get("rev_sha1", ""), r"^[0-9a-f]{40}$", entry)
                self.assertTrue(entry.get("rev_timestamp"), entry)

    def test_knowledge_and_rag_share_titles(self):
        knowledge = {e["id"]: e for e in self.manifest["files"]["knowledge"]}
        for entry in self.manifest["files"]["rag"]:
            parent = knowledge[entry["derived_from"]]
            self.assertEqual(entry["title"], parent["title"])
            self.assertEqual(entry["revid"], parent["revid"])

    def test_retrieved_at_is_recorded(self):
        for group in self.manifest["files"].values():
            for entry in group:
                self.assertRegex(entry.get("retrieved_at", ""), r"^\d{4}-\d{2}-\d{2}$", entry)


if __name__ == "__main__":
    unittest.main()
