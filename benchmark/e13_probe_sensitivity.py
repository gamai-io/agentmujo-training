#!/usr/bin/env python3
"""E13 — probe sensitivity: how much does a "100% gate" depend on probe strength?

The E6 invoice gate reports recall 1.0 with a full field recomputation. That number is
only meaningful for the probe that produced it. This script reruns the same 500 invoices
through five progressively weaker probes and reports recall / false positives per level.

Levels (deterministic, no model):
  L0 trust       : no check at all (probe confirms the artifact exists)
  L1 sum_items   : subtotal equals the sum of line totals
  L2 sum+vat     : + VAT equals 17% of subtotal
  L3 lines+sum   : line totals recomputed + subtotal
  L4 full        : line totals + subtotal + VAT + total (the published gate)

Output: JSON with recall/FP per level and the probe ceiling.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal, ROUND_HALF_UP

VAT = Decimal("0.17")
D = lambda x: Decimal(str(x))
R = lambda x: x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def probes(inv):
    """Return fired rule names per level (cumulative strength)."""
    items = inv.get("items") or []
    missing = any("unit_price" not in it or "line_total" not in it for it in items)
    line_bad = False
    for it in items:
        if "unit_price" in it:
            if R(D(it["qty"]) * D(it["unit_price"])) != R(D(it.get("line_total", 0))):
                line_bad = True
    subtotal = R(sum(D(it.get("line_total", 0)) for it in items))
    sum_bad = R(D(inv.get("subtotal", 0))) != subtotal
    vat_bad = R(D(inv.get("vat_total", 0))) != R(subtotal * VAT)
    total_bad = R(D(inv.get("total", 0))) != R(subtotal + R(subtotal * VAT))
    rate_bad = any(it.get("vat_rate") != 0.17 for it in items if "unit_price" in it)
    return {
        "L0_trust": [],
        "L1_sum": ["sum_items"] if sum_bad else [],
        "L2_sum_vat": [x for x, b in (("sum_items", sum_bad), ("vat_amount", vat_bad)) if b],
        "L3_lines_sum": [x for x, b in (("line_total", line_bad), ("sum_items", sum_bad),
                                        ("missing_field", missing)) if b],
        "L4_full": [x for x, b in (("line_total", line_bad), ("sum_items", sum_bad),
                                   ("vat_amount", vat_bad), ("total", total_bad),
                                   ("vat_rate", rate_bad), ("missing_field", missing)) if b],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("invoices", nargs="?", default="benchmark/e6_invoices.jsonl")
    ap.add_argument("--out", default="benchmark/e13_probe_sensitivity.json")
    a = ap.parse_args()
    rows = [json.loads(l) for l in open(a.invoices, encoding="utf-8") if l.strip()]
    dirty = sum(1 for r in rows if r.get("planted_errors"))
    clean = len(rows) - dirty
    levels = ["L0_trust", "L1_sum", "L2_sum_vat", "L3_lines_sum", "L4_full"]
    out = {"n": len(rows), "dirty": dirty, "clean": clean, "levels": {}}
    for lv in levels:
        hit = fp = 0
        for r in rows:
            flagged = bool(probes(r)[lv])
            if r.get("planted_errors"):
                hit += int(flagged)
            else:
                fp += int(flagged)
        rec, rlo, rhi = wilson(hit, dirty)
        fpr, flo, fhi = wilson(fp, clean)
        out["levels"][lv] = {"recall": round(rec, 4), "recall_ci95": [round(rlo, 4), round(rhi, 4)],
                             "caught": hit, "dirty": dirty,
                             "false_positive_rate": round(fpr, 4),
                             "false_positive_ci95": [round(flo, 4), round(fhi, 4)],
                             "false_positives": fp, "clean": clean}
    json.dump(out, open(a.out, "w"), indent=2, ensure_ascii=False)
    print(f"{'level':14s} {'recall':>8s} {'caught':>10s} {'FP rate':>8s} {'FP':>6s}")
    for lv in levels:
        v = out["levels"][lv]
        print(f"{lv:14s} {v['recall']:8.1%} {str(v['caught']) + '/' + str(v['dirty']):>10s} "
              f"{v['false_positive_rate']:8.2%} {str(v['false_positives']) + '/' + str(v['clean']):>6s}")
    print(f"\nprobe ceiling = L4_full; a weaker probe reports less, not more, reliability")
    return 0


if __name__ == "__main__":
    sys.exit(main())
