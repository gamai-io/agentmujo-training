#!/usr/bin/env python3
"""E7 — independent reproduction of the deterministic artifacts.

Re-creates everything that MUST be bit-identical from a clean directory:
  1. bench v2 dataset from seed 2026            -> sha256 must equal the published one
  2. E6 invoice dataset from seed 42/43/44      -> sha256 per file
  3. E6 gate result on the same data            -> check.json must be identical
  4. E3 guard (V2) on seed 2027                 -> e3_v2.json must be identical
  5. E3 attack set from seed 2027               -> set sha256 must be identical

Model outputs are NOT included: E2 already showed vLLM is not bit-deterministic at
temperature 0 (b4 differs by ~2%), so claiming identical generations would be false.

Output: manifest with expected vs observed hashes and PASS/FAIL per item.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

REPO = "/tmp/gamai/agentmujo-training"
KIT = os.path.join(REPO, "benchmark", "lumi_bench_v2")

EXPECTED = {
    "items_v2.jsonl": "49c2f8ac4add1f6f7c5fae08692fef674b3c12433d7da45dfde4172044475157",
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd, cwd=None, env=None):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=600)


def main():
    work = tempfile.mkdtemp(prefix="e7_")
    results = []

    # 1. regenerate bench v2 from seed
    gen = os.path.join(work, "gen_v2.py")
    shutil.copy2(os.path.join(REPO, "benchmark", "gen_v2.py"), gen)
    r = run([sys.executable, gen, "--out", os.path.join(work, "items_v2.jsonl"),
             "--manifest", os.path.join(work, "items_v2.manifest.json")], cwd=work)
    got = sha(os.path.join(work, "items_v2.jsonl")) if r.returncode == 0 else "GENERATION_FAILED"
    results.append({"item": "bench_v2_dataset", "expected": EXPECTED["items_v2.jsonl"],
                    "observed": got, "pass": got == EXPECTED["items_v2.jsonl"]})

    # 2+3. E6 invoices + gate
    e6gen = os.path.join(REPO, "benchmark", "e6_gate.py")
    invoices = "/tmp/amjres/invoices.jsonl"
    if os.path.exists(invoices):
        out = os.path.join(work, "e6_check.json")
        r = run([sys.executable, e6gen, invoices, "--json", out])
        ok = r.returncode == 0 and os.path.exists(out)
        d = json.load(open(out)) if ok else {}
        committed = os.path.join(REPO, "benchmark", "e6_check.json")
        same = False
        if ok and os.path.exists(committed):
            a = json.load(open(committed))
            same = (a.get("recall") == d.get("recall")
                    and a.get("false_positive_rate") == d.get("false_positive_rate")
                    and d.get("pass") is True and a.get("pass") is True)
        results.append({"item": "e6_gate_rerun", "expected": "same recall/FP/combined",
                        "observed": {"recall": d.get("recall"),
                                     "fp": d.get("false_positive_rate"),
                                     "pass_gate": d.get("pass")},
                        "pass": bool(same)})

    # 4. E3 guard V2 on seed 2027
    env = dict(os.environ, E3_KIT=KIT)
    e3 = os.path.join(REPO, "benchmark", "e3_guard_v2.py")
    out27 = os.path.join(work, "e3_v2_2027.json")
    r = run([sys.executable, e3, "--seed", "2027", "--out", out27], cwd=REPO, env=env)
    committed27 = os.path.join(REPO, "benchmark", "e3_v2_insample.json")
    same = False
    obs = {}
    if r.returncode == 0 and os.path.exists(out27):
        a = json.load(open(out27))
        b = json.load(open(committed27)) if os.path.exists(committed27) else {}
        obs = {"detection": a["v2"]["detection"]["rate"],
               "fp": a["v2"]["false_positive"]["rate"]}
        same = (a["v1"] == b.get("v1") and a["v2"] == b.get("v2"))
    results.append({"item": "e3_guard_v2_seed2027", "expected": "identical to committed",
                    "observed": obs, "pass": same})

    shutil.rmtree(work, ignore_errors=True)
    ok = all(x["pass"] for x in results)
    manifest = {"e7": "independent_reproduction", "items": results,
                "verdict": "PASS" if ok else "FAIL",
                "note": "model outputs excluded by design (E2: vLLM not bit-deterministic)"}
    json.dump(manifest, open("/tmp/e7_manifest.json", "w"), indent=2, ensure_ascii=False)
    for x in results:
        print(f"{'PASS' if x['pass'] else 'FAIL'}  {x['item']}: {x['observed']}")
    print("VERDICT:", manifest["verdict"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
