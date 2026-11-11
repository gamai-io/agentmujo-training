#!/usr/bin/env python3
"""E14 client: ask who caused the recovery and parse AGENT / SYSTEM / NEJASNO."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def parse(txt):
    u = txt.upper()
    if "AGENT" in u or "MOJA" in u:
        return "AGENT"
    if "SYSTEM" in u or "SISTEM" in u:
        return "SYSTEM"
    if "NEJASNO" in u or "NE ZNAM" in u:
        return "NEJASNO"
    return "UNPARSED"


def ask(url, model, prompt, timeout=120):
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.0, "max_tokens": 8, "stream": False}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    ch = (d.get("choices") or [{}])[0]
    txt = ((ch.get("message") or {}).get("content") or "").strip()
    return {"verdict": parse(txt), "raw": txt[:40]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--conc", type=int, default=32)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(a.items, encoding="utf-8") if l.strip()][: a.n]
    rows = []
    t0 = time.time()

    def one(it):
        try:
            r = ask(a.url, a.model, it["prompt"])
        except Exception as e:
            r = {"verdict": "ERR", "raw": type(e).__name__}
        r.update({"id": it["id"], "kind": it["kind"], "expected": it["expected"]})
        return r

    with ThreadPoolExecutor(max_workers=a.conc) as ex:
        for r in ex.map(one, items):
            rows.append(r)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"n": len(rows), "wall_s": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    sys.exit(main())
