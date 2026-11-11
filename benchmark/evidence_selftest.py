#!/usr/bin/env python3
"""Dependency-free selftest for the evidence gate (runs on any node without pytest).

Verifies the five properties that matter and prints GATE_SELFTEST_OK only if all hold.
"""
from __future__ import annotations

import hashlib
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from agentmujo_training.guard.evidence_gate import (  # noqa: E402
    ABSTAIN, FAIL, PASS, Claim, gate)


def main():
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "artifact.json")
        open(p, "w").write('{"n": 700}')
        sha = hashlib.sha256(open(p, "rb").read()).hexdigest()

        cases = [
            ("no claims -> abstain", gate([]).verdict, ABSTAIN),
            ("unknown kind -> abstain", gate([Claim("x", "vibes", {})]).verdict, ABSTAIN),
            ("wrong sha -> fail",
             gate([Claim("x", "file", {"path": p, "sha256": "0" * 64})]).verdict, FAIL),
            ("right sha -> pass",
             gate([Claim("x", "file", {"path": p, "sha256": sha})]).verdict, PASS),
            ("pass+abstain -> abstain",
             gate([Claim("x", "file", {"path": p}),
                   Claim("y", "run", {"exit_code": 0})], {}).verdict, ABSTAIN),
        ]
        bad = [name for name, got, want in cases if got != want]
        for name, got, want in cases:
            print(f"{'OK ' if got == want else 'BAD'} {name}: {got}")
        if bad:
            print("GATE_SELFTEST_FAILED", len(bad))
            return 1
        print(f"GATE_SELFTEST_OK {len(cases)}/{len(cases)}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
