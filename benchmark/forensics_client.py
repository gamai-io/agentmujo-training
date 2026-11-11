#!/usr/bin/env python3
"""Cross-process forensics client: captures text + token logprobs so we can locate the
first divergent token between repeated runs.

POST /v1/chat/completions with logprobs=true, top_logprobs=5, temperature=0.
Writes JSONL: {id, text, tokens[], logprobs[], top_alt[]}.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def call(url, model, prompt, max_tokens, timeout=300):
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.0, "seed": 42, "max_tokens": max_tokens,
               "logprobs": True, "top_logprobs": 5, "stream": False}
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    ch = (d.get("choices") or [{}])[0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    toks = [x.get("token") for x in lp]
    lps = [round(float(x.get("logprob") or 0.0), 6) for x in lp]
    alt = []
    for x in lp:
        tops = x.get("top_logprobs") or []
        alt.append(tops[1].get("token") if len(tops) > 1 else None)
    return {"text": ch.get("message", {}).get("content") or "",
            "tokens": toks, "logprobs": lps, "top_alt": alt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--conc", type=int, default=8)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    items = [json.loads(l) for l in open(a.items, encoding="utf-8") if l.strip()][: a.n]
    rows = []
    t0 = time.time()

    def work(it):
        try:
            r = call(a.url, a.model, it["prompt"], a.max_tokens)
            r["err"] = ""
        except Exception as e:
            r = {"text": "", "tokens": [], "logprobs": [], "top_alt": [],
                 "err": f"{type(e).__name__}: {str(e)[:120]}"}
        r["id"] = it["id"]
        return r

    with ThreadPoolExecutor(max_workers=a.conc) as ex:
        for r in ex.map(work, items):
            rows.append(r)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    errs = sum(1 for r in rows if r.get("err"))
    print(json.dumps({"n": len(rows), "errors": errs,
                      "wall_s": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    sys.exit(main())
