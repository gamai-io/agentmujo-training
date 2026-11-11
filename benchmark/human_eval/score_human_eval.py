#!/usr/bin/env python3
"""Score human annotations: agreement (Cohen/Fleiss kappa) and per-family rates.

Input: one or more CSVs with columns item_id,annotator,verdict (from annotate.html),
plus items_annot.jsonl to know each item's family.

Usage:
  python3 score_human_eval.py --items items_annot.jsonl --csv a.csv b.csv c.csv \
      --out human_eval_results.json
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from collections import Counter, defaultdict

LABELS = ["HEDGE", "ANSWER_OK", "ANSWER_UNSUPPORTED", "FABRICATE"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def cohen_kappa(a, b):
    """a, b: dict item_id -> label for the same items."""
    ids = sorted(set(a) & set(b))
    if not ids:
        return None
    n = len(ids)
    po = sum(1 for i in ids if a[i] == b[i]) / n
    ca, cb = Counter(a[i] for i in ids), Counter(b[i] for i in ids)
    pe = sum((ca[l] / n) * (cb[l] / n) for l in set(ca) | set(cb))
    if pe == 1:
        return 1.0
    return round((po - pe) / (1 - pe), 4)


def fleiss_kappa(rows):
    """rows: list of dict item_id -> label (one per annotator, same items)."""
    ids = sorted(set.intersection(*[set(r) for r in rows]))
    if not ids or len(rows) < 2:
        return None
    n = len(rows)
    counts = []
    for i in ids:
        c = Counter(r[i] for r in rows)
        counts.append([c.get(l, 0) for l in LABELS])
    N = len(ids)
    P = [(sum(x * x for x in c) - n) / (n * (n - 1)) for c in counts]
    pj = [sum(c[j] for c in counts) / (N * n) for j in range(len(LABELS))]
    Pbar = sum(P) / N
    Pe = sum(p * p for p in pj)
    if Pe == 1:
        return 1.0
    return round((Pbar - Pe) / (1 - Pe), 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--csv", nargs="+", required=True)
    ap.add_argument("--out", default="human_eval_results.json")
    a = ap.parse_args()

    fam = {}
    for line in open(a.items, encoding="utf-8"):
        if line.strip():
            it = json.loads(line)
            fam[it["id"]] = it.get("family", "?")

    per = {}
    for path in a.csv:
        with open(path, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                per.setdefault(r["annotator"], {})[r["item_id"]] = r["verdict"]

    ann = sorted(per)
    out = {"annotators": ann, "n_annotators": len(ann), "items_file": a.items,
           "coverage": {k: len(v) for k, v in per.items()}, "pairwise_kappa": {},
           "fleiss_kappa": fleiss_kappa([per[k] for k in ann]) if len(ann) >= 2 else None,
           "per_family": {}, "disagreements": []}

    for x, y in itertools.combinations(ann, 2):
        out["pairwise_kappa"][f"{x}|{y}"] = cohen_kappa(per[x], per[y])

    by_fam = defaultdict(lambda: defaultdict(Counter))
    for k in ann:
        for i, v in per[k].items():
            by_fam[fam.get(i, "?")][k][v] += 1
    for f, d in by_fam.items():
        entry = {}
        for k in ann:
            c = d[k]
            n = sum(c.values())
            fab = c.get("FABRICATE", 0)
            p, lo, hi = wilson(fab, n)
            entry[k] = {"n": n, "counts": dict(c), "fabricate_rate": round(p, 4),
                        "fabricate_ci95": [round(lo, 4), round(hi, 4)]}
        out["per_family"][f] = entry

    ids = sorted(set.intersection(*[set(per[k]) for k in ann])) if ann else []
    for i in ids:
        labels = {k: per[k][i] for k in ann}
        if len(set(labels.values())) > 1:
            out["disagreements"].append({"item_id": i, "family": fam.get(i, "?"), "labels": labels})

    json.dump(out, open(a.out, "w"), indent=2, ensure_ascii=False)
    print(f"annotators: {ann}")
    print(f"coverage: {out['coverage']}")
    print(f"pairwise kappa: {out['pairwise_kappa']}")
    print(f"fleiss kappa: {out['fleiss_kappa']}")
    for f, d in out["per_family"].items():
        for k, v in d.items():
            print(f"  {f:12s} {k:8s} n={v['n']:3d} fab={v['fabricate_rate']:.1%} "
                  f"CI[{v['fabricate_ci95'][0]:.1%},{v['fabricate_ci95'][1]:.1%}]")
    print(f"disagreements: {len(out['disagreements'])} (in JSON)")


if __name__ == "__main__":
    main()
