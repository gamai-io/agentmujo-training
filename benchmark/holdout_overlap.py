#!/usr/bin/env python3
"""Holdout v0.2 leakage check against every dev/eval set we use.

For each private holdout item, compute the max token-set Jaccard similarity against
all public/dev prompts. Reports exact duplicates (1.0), near-duplicates (>=0.8) and
the overall max, plus a PASS/FAIL verdict (target: 0 near-duplicates).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HOLDOUT = "/root/gamaos/private/holdout_v0.2/items.jsonl"

SOURCES = [
    "/tmp/gamai/agentmujo-training/benchmark/cases_v0.6.jsonl",
    "/tmp/gamai/agentmujo-training/benchmark/cases_conf14.jsonl",
    "/tmp/gamai/agentmujo-training/benchmark/cases_conf50.jsonl",
    "/tmp/gamai/agentmujo-training/benchmark/items_v2.jsonl",
    "/tmp/bal5_data.jsonl",
    "/tmp/bal6_data.jsonl",
    "/tmp/amjres/eval_prompts.jsonl",
    "/tmp/amjres/items_v2.jsonl",
]

WORD = re.compile(r"[a-z0-9čćžšđ]+", re.I)


def toks(s):
    return set(WORD.findall((s or "").lower()))


def jac(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_prompts(path):
    out = []
    p = Path(path)
    if not p.exists():
        return out
    for line in p.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        for key in ("prompt", "goal", "task", "question", "text", "input"):
            v = d.get(key)
            if isinstance(v, str) and v.strip():
                out.append((str(d.get("id") or d.get("case") or "?"), v))
                break
    return out


def main():
    hold = load_prompts(HOLDOUT)
    if not hold:
        print("HOLDOUT_MISSING_OR_EMPTY", HOLDOUT)
        return 2

    dev = []
    for s in SOURCES:
        items = load_prompts(s)
        dev.extend([(s, i, t) for i, t in items])
    print(f"holdout items: {len(hold)} | dev prompts: {len(dev)}")

    ht = [(i, t, toks(t)) for i, t in hold]
    worst = []
    exact = 0
    near = 0
    for hid, htext, htoks in ht:
        best = (0.0, None, None)
        for src, did, dtext in dev:
            j = jac(htoks, toks(dtext))
            if j > best[0]:
                best = (j, f"{src}:{did}", dtext)
        worst.append((hid, best[0], best[1], htext, best[2]))
        if best[0] >= 0.999:
            exact += 1
        elif best[0] >= 0.8:
            near += 1

    worst.sort(key=lambda x: -x[1])
    print(f"exact duplicates: {exact} | near-duplicates (>=0.8): {near}")
    print("top 5 most similar:")
    for hid, j, src, htext, dtext in worst[:5]:
        print(f"  {j:.3f}  holdout={hid}  vs {src}")
        print(f"        H: {htext[:90]}")
        print(f"        D: {(dtext or '')[:90]}")

    verdict = "PASS" if (exact == 0 and near == 0) else "FAIL"
    print(f"VERDICT: {verdict} (max={worst[0][1]:.3f})")
    json.dump({"n_holdout": len(hold), "n_dev": len(dev), "exact": exact,
               "near": near, "max_similarity": worst[0][1], "verdict": verdict,
               "top": [{"holdout": h, "sim": round(j, 4), "source": s}
                       for h, j, s, _, _ in worst[:10]]},
              open("/tmp/holdout_overlap.json", "w"), indent=2, ensure_ascii=False)
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
