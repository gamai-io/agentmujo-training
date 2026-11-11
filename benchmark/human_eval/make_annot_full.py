#!/usr/bin/env python3
"""Join the 200-item human-eval kit with model responses into the annotation file.

Runs on LUMI after the response job:
  python3 make_annot_full.py --items items_200.jsonl --responses v2annot.jsonl \
      --out items_annot.jsonl
"""
from __future__ import annotations

import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--responses", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(a.items, encoding="utf-8") if l.strip()]
    resp = {r["id"]: (r.get("text") or "").strip()
            for r in (json.loads(l) for l in open(a.responses, encoding="utf-8") if l.strip())}
    rows = []
    for it in items:
        rows.append({"id": it["id"], "family": it.get("family", "?"),
                     "kind": it.get("kind", ""), "prompt": it["prompt"],
                     "reference": (it.get("reference") or ""),
                     "response": resp.get(it["id"], "")})
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_resp = sum(1 for r in rows if r["response"])
    print(json.dumps({"n": len(rows), "with_response": n_resp, "out": a.out}))


if __name__ == "__main__":
    main()
