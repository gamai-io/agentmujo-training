"""docs/REGISTRY.md must be what the generator produces, not a stale copy."""
from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from agentmujo_training.registry import build  # noqa: E402


class RegistryDoc(unittest.TestCase):
    def test_committed_doc_matches_generator(self):
        expected = build(ROOT)
        actual = (ROOT / "docs" / "REGISTRY.md").read_text(encoding="utf-8")
        self.assertEqual(actual, expected,
                         "docs/REGISTRY.md is stale: run `amj registry build`")

    def test_generator_is_deterministic(self):
        self.assertEqual(build(ROOT), build(ROOT))


if __name__ == "__main__":
    unittest.main()
