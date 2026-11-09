"""Deterministic gate for E6 synthetic invoices (BiH VAT 17%).

Recomputes each invoice from its own line items and flags inconsistencies.
No model involved: this is the fail-closed gate that must catch planted errors
with recall 100% and false-positive rate <= 1%.

Usage:
    python3 benchmark/e6_gate.py invoices.jsonl --json e6_check.json
"""
from __future__ import annotations

import argparse
import json
import math
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


def detect(inv):
    """Return list of rule names that fired."""
    fired = []
    items = inv.get("items") or []
    for i, it in enumerate(items):
        if "unit_price" not in it:
            fired.append("missing_field")
            continue
        if it.get("vat_rate") != 0.17:
            fired.append("vat_rate")
        expected_lt = R(D(it["qty"]) * D(it["unit_price"]))
        if "line_total" not in it or R(D(it["line_total"])) != expected_lt:
            fired.append("line_total")
    subtotal = R(sum(D(it.get("line_total", 0)) for it in items))
    if R(D(inv.get("subtotal", 0))) != subtotal:
        fired.append("sum_items")
    if R(D(inv.get("vat_total", 0))) != R(subtotal * VAT):
        fired.append("vat_amount")
    if R(D(inv.get("total", 0))) != R(subtotal + R(subtotal * VAT)):
        fired.append("total")
    return sorted(set(fired))


def run(path):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    flagged_dirty = flagged_clean = 0
    missed = []
    per_kind = {}
    for r in rows:
        planted = r.get("planted_errors") or []
        kinds = [e["kind"] for e in planted]
        fired = detect(r)
        flagged = bool(fired)
        if planted:
            if flagged:
                flagged_dirty += 1
            else:
                missed.append(r["id"])
            for k in kinds:
                hit, tot = per_kind.get(k, (0, 0))
                per_kind[k] = (hit + (1 if k in fired else 0), tot + 1)
        elif flagged:
            flagged_clean += 1

    dirty = sum(1 for r in rows if r.get("planted_errors"))
    clean = len(rows) - dirty
    p, lo, hi = wilson(flagged_dirty, dirty)
    fp_p, fp_lo, fp_hi = wilson(flagged_clean, clean)
    result = {
        "n": len(rows), "dirty": dirty, "clean": clean,
        "flagged_dirty": flagged_dirty, "flagged_clean": flagged_clean,
        "recall": round(p, 4), "recall_ci95": [round(lo, 4), round(hi, 4)],
        "false_positive_rate": round(fp_p, 4),
        "false_positive_ci95": [round(fp_lo, 4), round(fp_hi, 4)],
        "missed_ids": missed,
        "per_kind": {k: {"hit": h, "total": t, "recall": round(h / t, 4)}
                     for k, (h, t) in sorted(per_kind.items())},
        "thresholds": {"recall": 1.0, "false_positive_rate_max": 0.01},
        "pass": (flagged_dirty == dirty and (clean == 0 or flagged_clean / clean <= 0.01)),
    }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    out = run(a.jsonl)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
