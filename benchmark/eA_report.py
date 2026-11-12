#!/usr/bin/env python3
"""Summarize E-A full atlas: rows = TP x arm, cols = B; exact-match vs B=1 and variation."""
import json, glob, os, re, sys
rows = []
for f in sorted(glob.glob(sys.argv[1] + "/*.summary.json")):
    s = json.load(open(f))
    tag = s.get("tag", "")
    m = re.match(r"(def|bi|triton|bitriton)_tp(\d+)", tag)
    if not m:
        continue
    rows.append({"arm": m.group(1), "tp": int(m.group(2)), "batch": s["batch"],
                 "var": s["prompts_with_variation"], "match": s.get("ref_exact_match_rate"),
                 "n": s.get("requests")})
arms = ["def", "bi", "triton", "bitriton"]
print("cells:", len(rows))
print("%-9s %-3s %5s %8s %8s" % ("arm", "tp", "B", "match", "var/16"))
for a in arms:
    for tp in sorted({r['tp'] for r in rows}):
        for b in [1, 2, 8, 32]:
            r = next((x for x in rows if x['arm'] == a and x['tp'] == tp and x['batch'] == b), None)
            if not r:
                continue
            mt = "-" if r["match"] is None else "%.4f" % r["match"]
            print("%-9s %-3d %5d %8s %5d/16" % (a, tp, b, mt, r["var"]))
