"""The PII scanner must catch real leaks and ignore the placeholders we ship."""
from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "pii_scan.py"


def run(text: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as td:
        target = pathlib.Path(td) / "sample.txt"
        target.write_text(text, encoding="utf-8")
        return subprocess.run([sys.executable, str(TOOL), str(target)],
                              capture_output=True, text=True)


class Scanner(unittest.TestCase):
    def test_placeholder_address_is_allowed(self):
        done = run("kontakt: kupac@example.com\n")
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_real_address_is_flagged(self):
        address = "ivana.markovic" + "@" + "gmail" + ".com"   # assembled so this file is clean
        done = run(f"kontakt: {address}\n")
        self.assertEqual(done.returncode, 1)
        self.assertIn("email", done.stdout)

    def test_jmbg_is_flagged(self):
        jmbg = "1503996" + "175028"            # assembled so this file is clean
        done = run(f"JMBG {jmbg}\n")
        self.assertEqual(done.returncode, 1, done.stdout)
        self.assertIn("jmbg", done.stdout)

    def test_thirteen_digit_number_is_not_a_jmbg(self):
        done = run("artikl 9900000000001\n")
        self.assertEqual(done.returncode, 0, done.stdout)

    def test_api_key_is_flagged(self):
        done = run("key ghp_" + "a" * 36 + "\n")
        self.assertEqual(done.returncode, 1)
        self.assertIn("api_key", done.stdout)

    def test_repository_is_clean(self):
        done = subprocess.run([sys.executable, str(TOOL)],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stdout[-2000:])


if __name__ == "__main__":
    unittest.main()
