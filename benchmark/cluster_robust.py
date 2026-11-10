#!/usr/bin/env python3
"""Cluster-robust re-analysis of AgentMujo Bench v2.

Bench v2 has 24 distinct prompt templates (b1: 3, b2: 1, b4: 8, b5: 12), so 700 items
are NOT 700 independent observations. This script:

  1. assigns every item a template (cluster) id,
  2. reports the naive accuracy and the Wilson interval (what we published),
  3. reports a cluster bootstrap interval (resampling templates within block) and the
     design effect (ratio of cluster variance to binomial variance),
  4. reports per-cluster accuracy spread and the leave-one-template-out range,
  5. flags blocks with a single template (their cluster variance is unidentifiable).

Usage:
  python3 cluster_robust.py --items items_v2.jsonl \
      --results v2_qwen7b.jsonl v2_llama70b.jsonl --out cluster_stats.json
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys

B = 4000


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, c - h), min(1.0, c + h))


def cluster_of(it):
    """Template id. Derived from the generator's structure, not from the answer."""
    blk = it["block"]
    p = it["prompt"]
    if blk == "b1_arith":
        if "ukupno sa PDV" in p:
            return "b1_total"
        if "Koliko iznosi PDV" in p:
            return "b1_vat"
        if "Kolika je osnovica" in p:
            return "b1_sub"
        return "b1_other"
    if blk == "b2_needle":
        return "b2_needle"
    if blk == "b4_honesty":
        return "b4_" + str(it.get("kind", "unknown"))
    if blk == "b5_toolargs":
        m = re.search(r"Alat:\s*([A-Za-z0-9_]+)", p)
        return "b5_" + (m.group(1) if m else "unknown")
    return blk


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def analyse(name, items, results, rng, by_item=None, rescore=False):
    by_id = {r["id"]: r for r in results}
    rows = []
    for it in items:
        r = by_id.get(it["id"])
        if r is None:
            continue
        ok = bool(r.get("ok"))
        if rescore and by_item is not None:
            from run_v2 import score_item
            ok, _why = score_item(by_item[it["id"]], r.get("text") or "")
        rows.append({"cluster": cluster_of(it), "block": it["block"],
                     "ok": 1 if ok else 0})
    n = len(rows)
    k = sum(r["ok"] for r in rows)
    p_naive, w_lo, w_hi = wilson(k, n)

    blocks = {}
    for r in rows:
        blocks.setdefault(r["block"], {}).setdefault(r["cluster"], []).append(r["ok"])

    single = [b for b, cl in blocks.items() if len(cl) < 2]

    # cluster bootstrap: resample clusters with replacement inside each block
    boot = []
    for _ in range(B):
        tot = ok = 0
        for b, cl in blocks.items():
            keys = list(cl)
            if len(keys) == 1:
                vals = cl[keys[0]]
                tot += len(vals)
                ok += sum(vals)
                continue
            pick = [rng.choice(keys) for _ in keys]
            for c in pick:
                tot += len(cl[c])
                ok += sum(cl[c])
        boot.append(ok / tot if tot else 0.0)
    boot.sort()
    b_lo = boot[int(0.025 * len(boot))]
    b_hi = boot[int(0.975 * len(boot)) - 1]
    var_boot = sum((x - p_naive) ** 2 for x in boot) / (len(boot) - 1)
    var_bin = p_naive * (1 - p_naive) / n if n else 0.0
    deff = (var_boot / var_bin) if var_bin else float("nan")

    per_cluster = {}
    for b, cl in blocks.items():
        for c, vals in cl.items():
            per_cluster[c] = {"block": b, "n": len(vals), "ok": sum(vals),
                              "acc": round(sum(vals) / len(vals), 4)}

    # leave-one-template-out: accuracy over all items except one cluster
    loto = {}
    for b, cl in blocks.items():
        for c, vals in cl.items():
            rest_n = n - len(vals)
            rest_ok = k - sum(vals)
            if rest_n:
                loto[c] = round(rest_ok / rest_n, 4)
    loto_vals = sorted(loto.values())

    return {
        "model": name,
        "n": n,
        "ok": k,
        "acc": round(p_naive, 4),
        "wilson95": [round(w_lo, 4), round(w_hi, 4)],
        "cluster_bootstrap95": [round(b_lo, 4), round(b_hi, 4)],
        "design_effect": round(deff, 3) if deff == deff else None,
        "effective_n": round(n / deff, 1) if deff and deff == deff else None,
        "n_clusters": len(per_cluster),
        "clusters": per_cluster,
        "cluster_acc_range": [round(min(v["acc"] for v in per_cluster.values()), 4),
                              round(max(v["acc"] for v in per_cluster.values()), 4)],
        "loto_acc_range": [loto_vals[0], loto_vals[-1]] if loto_vals else None,
        "blocks_with_single_template": single,
        "note": ("Blocks with a single template contribute no identifiable cluster variance; "
                 "their within-block variance is unidentifiable by design."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--results", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--rescore", action="store_true",
                    help="recompute ok from the stored text with the current run_v2 scorer")
    a = ap.parse_args()

    items = load_jsonl(a.items)
    by_item = {it["id"]: it for it in items}
    rng = random.Random(42)
    out = {"bench": "v2", "n_items": len(items), "bootstrap": B,
           "rescored": bool(a.rescore), "models": {}}
    for path in a.results:
        res = load_jsonl(path)
        name = path.rsplit("/", 1)[-1].replace(".jsonl", "")
        out["models"][name] = analyse(name, items, res, rng, by_item, a.rescore)

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"{'model':22s} {'n':>4s} {'acc':>7s} {'wilson95':>16s} {'cluster95':>16s} {'deff':>6s} {'effN':>6s}")
    for name, m in out["models"].items():
        print(f"{name:22s} {m['n']:4d} {m['acc']:7.3f} "
              f"[{m['wilson95'][0]:.3f},{m['wilson95'][1]:.3f}] "
              f"[{m['cluster_bootstrap95'][0]:.3f},{m['cluster_bootstrap95'][1]:.3f}] "
              f"{m['design_effect']:6.2f} {m['effective_n']:6.1f}")
    print("single-template blocks:", sorted({b for m in out["models"].values()
                                             for b in m["blocks_with_single_template"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
