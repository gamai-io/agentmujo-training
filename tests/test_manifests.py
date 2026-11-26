"""Every dataset manifest must match the file it describes."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "refresh_manifests.py"


class Manifests(unittest.TestCase):
    def test_every_manifest_matches_its_file(self):
        done = subprocess.run([sys.executable, str(TOOL), "--check"],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertIn("ok", done.stdout)

    def test_manifests_carry_a_hash(self):
        import json
        for path in (ROOT / "datasets" / "manifests").glob("*.json"):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            self.assertRegex(manifest.get("sha256", ""), r"^[0-9a-f]{64}$", path.name)


if __name__ == "__main__":
    unittest.main()
