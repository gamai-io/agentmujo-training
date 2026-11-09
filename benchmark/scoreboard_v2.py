#!/usr/bin/env python3
"""Collect v2_*.summary.json files into one scoreboard table."""
import glob
import json
import sys

BLOCKS = ["b1_arith", "b2_needle", "b4_honesty", "b5_toolargs"]
files = sys.argv[1:]
if not files:
    files = sorted(glob.glob("/project/project_465003647/gama/out/v2_*.summary.json"))

rows = []
for f in files:
    try:
        s = json.load(open(f))
    except Exception as e:
        print("skip", f, e)
        continue
    tag = f.split("v2_")[-1].split("_")[0]
    r = {"tag": tag, "n": s.get("n"), "wall": s.get("wall_s"), "rps": s.get("rps")}
    for b in BLOCKS:
        r[b] = (s.get("blocks", {}).get(b) or {}).get("ok")
        r[b + "_n"] = (s.get("blocks", {}).get(b) or {}).get("n")
    r["overall"] = s.get("overall", {}).get("acc")
    r["ci"] = s.get("overall", {}).get("ci95")
    rows.append(r)

hdr = f"{'model':12s} " + " ".join(f"{b:>13s}" for b in BLOCKS) + f" {'overall':>9s} {'rps':>6s}"
print(hdr)
print("-" * len(hdr))
for r in sorted(rows, key=lambda x: -(x["overall"] or 0)):
    cells = []
    for b in BLOCKS:
        ok, n = r[b], r[b + "_n"]
        cells.append(f"{ok}/{n} ({100*ok/n:5.1f}%)" if n else "     -     ")
    print(f"{r['tag']:12s} " + " ".join(f"{c:>13s}" for c in cells)
          + f" {100*(r['overall'] or 0):8.1f}% {r['rps'] or 0:6.1f}")
