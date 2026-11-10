#!/usr/bin/env python3
"""Throughput/latency load generator for scaling and MFU measurement.

Sends `n` chat requests with a fixed prompt length and `ignore_eos` so the completion
length is exactly `max_tokens` (vLLM supports both). Reports requests/s, output
tokens/s, latency percentiles, and an approximate MFU for a dense transformer.

MFU = 2 * params * output_tokens_per_s / (gpus * peak_per_gpu)
with MI250X BF16 peak taken as 191.5 TFLOPS per GCD (383 TFLOPS per package / 2).
This is an estimate: it ignores attention FLOPs, prompt prefill, and sparsity.

Usage:
  python3 loadgen.py --url http://127.0.0.1:8000 --model qwen --n 512 --conc 64 \
      --max-tokens 128 --prompt-tokens 256 --gpus 4 --params-b 7.6 --out s.json
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PEAK_TFLOPS_GCD = 191.5

FILLER = ("Sistem bilježi događaje, provjerava stanje servisa i upoređuje rezultate sa "
          "očekivanim vrijednostima. ")


def make_prompt(target_tokens):
    # ~1.6 tokens per word for this text; approximate is fine for a fixed workload
    words = max(1, int(target_tokens / 1.6))
    base = (FILLER * (words // len(FILLER.split()) + 1)).split()
    return " ".join(base[:words])


def call(url, model, prompt, max_tokens, timeout):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "ignore_eos": True,
        "stream": False,
    }
    body = json.dumps(payload).encode()
    t0 = time.time()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    dt = time.time() - t0
    usage = d.get("usage") or {}
    return dt, int(usage.get("completion_tokens") or 0), int(usage.get("prompt_tokens") or 0)


def pct(vals, q):
    if not vals:
        return 0.0
    s = sorted(vals)
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return round(s[i], 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="one url or comma-separated urls (DP)")
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=512)
    ap.add_argument("--conc", type=int, default=64)
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--prompt-tokens", type=int, default=256)
    ap.add_argument("--gpus", type=int, default=4)
    ap.add_argument("--params-b", type=float, default=7.6)
    ap.add_argument("--timeout", type=float, default=600)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    urls = [u.strip() for u in a.url.split(",") if u.strip()]
    prompt = make_prompt(a.prompt_tokens)
    lat, ctok, ptok = [], 0, 0
    errs = 0
    t0 = time.time()

    def work(i):
        url = urls[i % len(urls)]
        return call(url, a.model, prompt, a.max_tokens, a.timeout)

    with ThreadPoolExecutor(max_workers=a.conc) as ex:
        futs = [ex.submit(work, i) for i in range(a.n)]
        for f in futs:
            try:
                dt, c, p = f.result()
                lat.append(dt)
                ctok += c
                ptok += p
            except Exception:
                errs += 1

    wall = time.time() - t0
    n_ok = len(lat)
    tps = ctok / wall if wall else 0.0
    rps = n_ok / wall if wall else 0.0
    flops = 2.0 * a.params_b * 1e9 * tps
    mfu = flops / (a.gpus * PEAK_TFLOPS_GCD * 1e12) if a.gpus else 0.0
    res = {
        "urls": urls, "model": a.model, "n": a.n, "ok": n_ok, "errors": errs,
        "conc": a.conc, "max_tokens": a.max_tokens, "prompt_tokens_target": a.prompt_tokens,
        "gpus": a.gpus, "params_b": a.params_b,
        "wall_s": round(wall, 2), "rps": round(rps, 2),
        "output_tokens": ctok, "input_tokens": ptok,
        "output_tokens_per_s": round(tps, 1),
        "latency_s": {"p50": pct(lat, 0.5), "p95": pct(lat, 0.95), "p99": pct(lat, 0.99)},
        "mfu_estimate": round(mfu, 4),
        "mfu_note": "2*params*out_tokens/s / (gpus*191.5 TFLOPS); ignores attention/prefill",
    }
    json.dump(res, open(a.out, "w"), indent=2)
    print(json.dumps({k: res[k] for k in ("ok", "errors", "wall_s", "rps",
                                          "output_tokens_per_s", "mfu_estimate")}))
    return 0 if errs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
