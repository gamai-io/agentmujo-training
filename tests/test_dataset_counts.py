"""The row counts in the README must be the row counts on disk.

The README has carried three different totals for the same corpus (2,911 / 2,956 /
4,496). This test fixes the numbers to the files and fails when they drift.
"""
from __future__ import annotations

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPLITS = ROOT / "datasets" / "splits"
CANONICAL = ROOT / "datasets" / "canonical" / "thinking_v0.1.jsonl"

EXPECTED = {
    "fc": 1389,
    "ag": 749,
    "bc": 1178,
    "thinking": 75,
}
EXPECTED_TRAIN = 2716


def rows(path: pathlib.Path) -> int:
    return sum(1 for line in path.open(encoding="utf-8") if line.strip())


class Counts(unittest.TestCase):
    def test_per_category_totals(self):
        for category, expected in EXPECTED.items():
            if category == "thinking":
                self.assertEqual(rows(CANONICAL), expected, category)
                continue
            total = sum(rows(p) for p in (SPLITS / category).glob("*.jsonl"))
            self.assertEqual(total, expected, category)

    def test_train_total(self):
        total = sum(rows(SPLITS / c / "train.jsonl") for c in ("fc", "ag", "bc"))
        self.assertEqual(total, EXPECTED_TRAIN)

    def test_every_split_row_is_json(self):
        for path in SPLITS.rglob("*.jsonl"):
            with path.open(encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    if not line.strip():
                        continue
                    try:
                        json.loads(line)
                    except json.JSONDecodeError as exc:
                        self.fail(f"{path}:{n}: {exc}")

    def test_readme_states_the_total(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        total = sum(EXPECTED.values())
        pretty = f"{total:,}".replace(",", ".")
        self.assertIn(pretty, text, f"README must state {pretty} rows")


if __name__ == "__main__":
    unittest.main()
