#!/usr/bin/env python3
"""E12 verifier batch: ask a model to judge claims (with or without a reference).

Reads items (question + reference) and answers (id -> text), builds a verification prompt,
and records TACNO / NETACNO / NE ZNAM per item.

Modes:
  noref : verifier sees only question + claimed answer (must use its own knowledge)
  ref   : verifier also sees the reference value (upper bound / cost baseline)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor


def prompt_noref(q, a):
    return (f"Pitanje: {q}\nPonuđeni odgovor: {a}\n\n"
            "Da li je ponuđeni odgovor tačan? Ako ne možeš provjeriti, odgovori NE ZNAM.\n"
            "Odgovori jednom riječju: TACNO, NETACNO ili NE ZNAM.")


def prompt_ref(q, a, ref):
    return (f"Pitanje: {q}\nPonuđeni odgovor: {a}\nReferentna vrijednost: {ref}\n\n"
            "Da li je ponuđeni odgovor tačan u odnosu na referencu?\n"
            "Odgovori jednom riječju: TACNO, NETACNO ili NE ZNAM.")


def prompt_refnum(q, a, ref):
    return (f"Pitanje: {q}\nPonuđeni odgovor: {a}\nReferentna vrijednost: {ref}\n\n"
            "Uporedi NUMERIČKI, sa tolerancijom 2%. Formati kao 1493 i 1493.0 su isti broj; "
            "za godine dozvoli ±1.\n"
            "Odgovori jednom riječju: TACNO, NETACNO ili NE ZNAM.")


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
    usage = d.get("usage") or {}
    up = txt.upper().replace("NE ZNAM", "NE_ZNAM")
    if "NETACNO" in up or "NETAČNO" in up:
        v = "NETACNO"
    elif "TACNO" in up or "TAČNO" in up:
        v = "TACNO"
    elif "NE_ZNAM" in up or "NE ZNAM" in up:
        v = "NE_ZNAM"
    else:
        v = "UNPARSED"
    return {"verdict": v, "raw": txt[:40],
            "out_tokens": int(usage.get("completion_tokens") or 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--answers", required=True)
    ap.add_argument("--mode", choices=["noref", "ref", "refnum"], default="noref")
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--conc", type=int, default=32)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    items = [json.loads(l) for l in open(a.items, encoding="utf-8") if l.strip()]
    ans = {x["id"]: x for x in (json.loads(l) for l in open(a.answers, encoding="utf-8") if l.strip())}
    work = []
    for it in items:
        r = ans.get(it["id"])
        if not r:
            continue
        work.append((it, (r.get("text") or "").strip()))
    work = work[: a.n]

    rows = []
    t0 = time.time()

    def one(pair):
        it, text = pair
        if not text:
            return {"id": it["id"], "verdict": "EMPTY_ANSWER", "out_tokens": 0}
        if a.mode == "ref":
            p = prompt_ref(it["prompt"], text, it["expected"])
        elif a.mode == "refnum":
            p = prompt_refnum(it["prompt"], text, it["expected"])
        else:
            p = prompt_noref(it["prompt"], text)
        try:
            r = ask(a.url, a.model, p)
        except Exception as e:
            r = {"verdict": "ERR", "raw": f"{type(e).__name__}", "out_tokens": 0}
        r["id"] = it["id"]
        return r

    with ThreadPoolExecutor(max_workers=a.conc) as ex:
        for r in ex.map(one, work):
            rows.append(r)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    toks = sum(r.get("out_tokens", 0) for r in rows)
    print(json.dumps({"n": len(rows), "wall_s": round(time.time() - t0, 1),
                      "out_tokens": toks, "mode": a.mode, "model": a.model}))


if __name__ == "__main__":
    sys.exit(main())
