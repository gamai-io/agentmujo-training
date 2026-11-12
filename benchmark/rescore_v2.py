#!/usr/bin/env python3
"""Rewrite a v2 summary from stored results with the current scorer."""
import argparse
import json
import math
import sys

sys.path.insert(0, "/project/project_465003647/gama/bench_v2")
from run_v2 import score_item, wilson  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--model", default="")
    a = ap.parse_args()

    items = {json.loads(l)["id"]: json.loads(l) for l in open(a.items) if l.strip()}
    rows = [json.loads(l) for l in open(a.results) if l.strip()]

    blocks = {}
    for r in rows:
        it = items[r["id"]]
        ok, _ = score_item(it, r.get("text"))
        b = blocks.setdefault(r["block"], {"ok": 0, "n": 0})
        b["n"] += 1
        b["ok"] += int(ok)

    out = {"model": a.model or "(rescored)", "n": len(rows), "rescored": True, "blocks": {}}
    tot_ok = tot_n = 0
    for b, v in sorted(blocks.items()):
        p, lo, hi = wilson(v["ok"], v["n"])
        out["blocks"][b] = {"ok": v["ok"], "n": v["n"], "acc": round(p, 4),
                            "ci95": [round(lo, 4), round(hi, 4)]}
        tot_ok += v["ok"]
        tot_n += v["n"]
    p, lo, hi = wilson(tot_ok, tot_n)
    out["overall"] = {"ok": tot_ok, "n": tot_n, "acc": round(p, 4),
                      "ci95": [round(lo, 4), round(hi, 4)]}
    json.dump(out, open(a.summary, "w"), indent=2, ensure_ascii=False)
    print(json.dumps({"summary": a.summary, "overall": out["overall"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
