#!/usr/bin/env python3
"""CLI for the three-valued evidence gate.

Input (JSON):
  {"claims": [{"text": "...", "kind": "file|text|run|sql|http|json",
               "expect": {...}}],
   "artifacts": {"path": "...", "text": "...", "run": {...}, "sql": {...},
                 "http": {...}, "json": {...}}}

Exit codes: 0 = PASS, 2 = FAIL, 3 = ABSTAIN (never treat absence of evidence as success).

Example:
  python3 evidence_check.py --claims c.json --artifacts a.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from agentmujo_training.guard.evidence_gate import ABSTAIN, FAIL, PASS, claims_from_dicts, gate  # noqa: E402

EXIT = {PASS: 0, FAIL: 2, ABSTAIN: 3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True,
                    help="JSON with 'claims' and 'artifacts'")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    b = json.load(open(a.bundle, encoding="utf-8"))
    claims = claims_from_dicts(b.get("claims"))
    arts = b.get("artifacts") or {}
    r = gate(claims, arts)
    if a.json:
        print(json.dumps({"verdict": r.verdict, "reason": r.reason,
                          "checks": [{"claim": c.claim, "verdict": c.verdict,
                                      "reason": c.reason, "detail": c.detail}
                                     for c in r.checks]}, indent=2, ensure_ascii=False))
    else:
        for c in r.checks:
            print(f"{c.verdict:8s} {c.claim[:58]:58s} {c.reason}")
        print(f"\nVERDICT: {r.verdict.upper()} - {r.reason} "
              f"(pass={r.n_pass} fail={r.n_fail} abstain={r.n_abstain})")
    return EXIT[r.verdict]


if __name__ == "__main__":
    sys.exit(main())
