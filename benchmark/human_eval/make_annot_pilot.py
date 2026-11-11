#!/usr/bin/env python3
"""Build the internal annotation file (pilot): 100 fictional-entity items with model answers.

Reads benchmark/items_v2.jsonl (b4_honesty, 100 items) and the Qwen run
benchmark/v2_results/v2_qwen7b.jsonl (text per id), and writes
benchmark/human_eval/items_annot_pilot.jsonl with {id, family, kind, prompt, reference, response}.

For the real-entity half, use make_annot_set_full.py on LUMI (needs the honesty_real responses).
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
ITEMS = os.path.join(REPO, "benchmark", "items_v2.jsonl")
RESP = os.path.join(REPO, "benchmark", "v2_results", "v2_qwen7b.jsonl")
OUT = os.path.join(HERE, "items_annot_pilot.jsonl")

items = [json.loads(l) for l in open(ITEMS, encoding="utf-8") if l.strip()]
b4 = {it["id"]: it for it in items if it["block"] == "b4_honesty"}
resp = {r["id"]: r for r in (json.loads(l) for l in open(RESP, encoding="utf-8") if l.strip())}

rows = []
for iid, it in sorted(b4.items()):
    r = resp.get(iid) or {}
    rows.append({"id": iid, "family": "fictitious", "kind": it.get("kind"),
                 "prompt": it["prompt"], "reference": "",
                 "response": (r.get("text") or "").strip()})

with open(OUT, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(json.dumps({"n": len(rows), "out": OUT,
                  "with_response": sum(1 for r in rows if r["response"])}))
