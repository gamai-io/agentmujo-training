#!/usr/bin/env python3
"""E-A MI250X determinism atlas runner (stdlib only, thread pool).

Sends the same fixed prompts at a given client concurrency B and records the
exact output bytes + hash (+ token logprobs when available). The B=1 run is the
reference; later runs are compared prompt-by-prompt.

  python3 eA_atlas.py --url http://127.0.0.1:8000 --model qwen --batch 8 \
      --reps 5 --max-tokens 128 --out out.jsonl --summary sum.json
  python3 eA_atlas.py ... --reference out_b1.jsonl   # adds match metrics
"""
from __future__ import annotations

import argparse, hashlib, json, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

PROMPTS = [
    ("arith1", "Izračunaj tačno: 847 * 39 - 1288. Odgovori samo brojem."),
    ("arith2", "Koliko je 17.5% od 2.480? Odgovori samo brojem."),
    ("arith3", "Zbir brojeva 19, 23, 29 i 31 podijeli sa 4. Odgovori samo brojem."),
    ("arith4", "Ako 7 radnika završi posao za 12 dana, za koliko dana će 21 radnik? Odgovori samo brojem."),
    ("free1", "Objasni u 3 rečenice zašto je determinizam važan za evaluaciju AI sistema."),
    ("free2", "Napiši kratak opis (3 rečenice) kako provjeriti da li je agent zaista završio zadatak."),
    ("free3", "Navedi tri razloga zašto mjerenje na jednoj grafičkoj kartici nije dovoljno."),
    ("free4", "Šta je batch-invariant inference? Objasni u 3 rečenice."),
    ("json1", "Vrati JSON {\"status\":\"ok\",\"count\":<broj>} gdje je count 3+4. Bez teksta izvan JSON-a."),
    ("json2", "Vrati JSON sa poljima tool i args: tool=\"read_file\", args={\"path\":\"/tmp/a.txt\"}. Samo JSON."),
    ("json3", "Vrati JSON {\"sum\":<broj>} za 123+456. Samo JSON."),
    ("json4", "Vrati JSON {\"ok\":true,\"items\":[1,2,3]} tačno kako je napisano. Samo JSON."),
    ("needle1", "Dokument: ALFA BETA GAMA DELTA. Koja riječ je treća? Odgovori jednom riječju."),
    ("needle2", "Niz: 5, 9, 13, 17, 21. Koji je peti broj? Odgovori samo brojem."),
    ("needle3", "U rečenici 'Marko je kupio 3 kruha i 2 mlijeka' koliko je kruhova? Odgovori brojem."),
    ("needle4", "Ponovi tačno ovu oznaku: XK-4471-QZ. Odgovori samo oznakom."),
]

def sha(s):
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()

def one(url, model, pid, prompt, rep, max_tokens, timeout):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0, "top_p": 1.0, "n": 1,
        "max_tokens": max_tokens, "seed": 42,
        "logprobs": True, "top_logprobs": 1,
    }
    t0 = time.time()
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.loads(r.read().decode())
        ch = d["choices"][0]
        text = ch.get("message", {}).get("content") or ""
        lp = ch.get("logprobs") or {}
        toks = []
        for c in (lp.get("content") or []):
            toks.append({"t": c.get("token"), "lp": c.get("logprob")})
        return {"prompt_id": pid, "rep": rep, "text": text, "sha256": sha(text),
                "tokens": toks, "finish_reason": ch.get("finish_reason"),
                "ms": round((time.time() - t0) * 1000, 1), "error": None}
    except Exception as e:
        return {"prompt_id": pid, "rep": rep, "text": "", "sha256": None,
                "tokens": [], "finish_reason": None,
                "ms": round((time.time() - t0) * 1000, 1), "error": repr(e)[:300]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000")
    ap.add_argument("--model", default="qwen")
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--max-tokens", type=int, default=128)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary", required=True)
    ap.add_argument("--reference", default=None)
    ap.add_argument("--tag", default="")
    a = ap.parse_args()

    tasks = []
    for rep in range(a.reps):
        for pid, p in PROMPTS:
            tasks.append((pid, p, rep))
    out = []
    with ThreadPoolExecutor(max_workers=max(1, a.batch)) as ex:
        futs = [ex.submit(one, a.url, a.model, pid, p, rep, a.max_tokens, a.timeout)
                for (pid, p, rep) in tasks]
        for f in futs:
            out.append(f.result())
    order = {pid: i for i, (pid, _) in enumerate(PROMPTS)}
    out.sort(key=lambda r: (r["rep"], order.get(r["prompt_id"], 99)))
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # summary: unique hashes per prompt; optional reference comparison
    ref = {}
    if a.reference:
        for line in open(a.reference, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("rep") == 0 and not r.get("error"):
                ref[r["prompt_id"]] = r
    per = {}
    for pid, _ in PROMPTS:
        rows = [r for r in out if r["prompt_id"] == pid and not r.get("error")]
        hashes = [r["sha256"] for r in rows]
        entry = {"n": len(rows), "unique": len(set(hashes)) if hashes else 0,
                 "hashes": hashes}
        if ref and pid in ref:
            base = ref[pid]
            entry["ref_sha256"] = base["sha256"]
            entry["match_ref"] = sum(1 for r in rows if r["sha256"] == base["sha256"])
            first = None
            for r in rows:
                if r["sha256"] == base["sha256"]:
                    continue
                x, y = base["text"], r["text"]
                i = 0
                for i in range(min(len(x), len(y))):
                    if x[i] != y[i]:
                        break
                first = i
                break
            entry["first_divergence_char"] = first
        per[pid] = entry
    total = sum(v["n"] for v in per.values())
    uniq = sum(v["unique"] > 1 for v in per.values())
    summ = {"tag": a.tag, "batch": a.batch, "reps": a.reps,
            "model": a.model, "max_tokens": a.max_tokens,
            "requests": total, "prompts_with_variation": uniq,
            "per_prompt": per}
    if ref:
        denom = sum(v["n"] for v in per.values() if "match_ref" in v)
        num = sum(v["match_ref"] for v in per.values() if "match_ref" in v)
        summ["ref_exact_match_rate"] = round(num / denom, 4) if denom else None
        summ["ref_compared_requests"] = denom
    json.dump(summ, open(a.summary, "w"), indent=2, ensure_ascii=False)
    print(json.dumps({k: summ[k] for k in summ if k != "per_prompt"}, ensure_ascii=False))

if __name__ == "__main__":
    main()
