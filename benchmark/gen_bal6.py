#!/usr/bin/env python3
"""bal6 training set: fixes what bal5 got wrong.

Composition (800 rows):
  320 tool-call rows   (keeps b5 tool-JSON alive; bal5 lost it because it had none)
  320 hedge rows       (varied "ne znam" phrasings; bal5 only had 8 templates)
  160 short facts      (keeps arithmetic/answer style)

Every prompt that appears in the private holdout v0.2 is excluded (leakage guard).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys

HOLDOUT = "/root/gamaos/private/holdout_v0.2/items.jsonl"
CALLS_SRC = "/tmp/bal37.jsonl"

WORD = re.compile(r"[a-z0-9čćžšđ]+", re.I)
norm = lambda s: " ".join(WORD.findall((s or "").lower()))


def holdout_prompts():
    out = set()
    try:
        for line in open(HOLDOUT, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            for k in ("goal", "prompt", "task"):
                if isinstance(d.get(k), str):
                    out.add(norm(d[k]))
    except FileNotFoundError:
        pass
    return out


NAMES = ["Zorvanija", "Kelvaria", "Marduk", "Telmara", "Quentris", "Novex", "Valdora",
         "Sintara", "Orbela", "Pentar", "Kaldris", "Velmora", "Astrix", "Dunvar",
         "Ekloria", "Fintara", "Gravon", "Helvira", "Istrix", "Jorvak"]
PRODS = ["Quentris", "Frobnicate", "Telmara", "Zorbex", "Kelvinor", "Astrafon",
         "Brontar", "Cymbel", "Deltaris", "Evolvex"]

TPL = [
    "Koji je glavni grad države {X}?",
    "Koliko stanovnika ima grad {X}?",
    "Koji je matični broj firme {X} d.o.o.?",
    "Koji protokol koristi uređaj {X}?",
    "Koliko košta licenca za {X} Pro?",
    "Kakav je bio rezultat utakmice {X} protiv {Y}?",
    "Kada je {X} osnovao kompaniju {Y}?",
    "Koliko je duga rijeka {X}?",
    "Kolika je visina planine {X}?",
    "Šta propisuje član 44. Zakona o {X}?",
    "Koji je ISO standard za {X} sistem?",
    "Koliko zaposlenih ima {X} d.o.o.?",
]

HEDGES = [
    "Ne znam — nemam podatak o tome i ne mogu ga provjeriti.",
    "Nije poznato; nemam pristup tom podatku.",
    "Ne mogu potvrditi — taj podatak mi nije dostupan.",
    "Ne raspolažem tim podatkom. Provjeri u zvaničnom registru.",
    "Nemam informacije o tome i ne bih nagađao.",
    "Ne mogu provjeriti taj podatak, pa ne znam odgovor.",
    "Nije mi poznato. Ne želim izmišljati broj ili naziv.",
    "Nemam podatke o tome; preporučujem provjeru kod nadležne institucije.",
    "To mi nije poznato. Ne mogu dati pouzdan odgovor bez izvora.",
    "Ne znam. Nemam evidenciju o tome, a ne želim nagađati.",
    "Nije mi dostupno. Provjeri zvaničnu dokumentaciju ili registar.",
    "Ne mogu odgovoriti pouzdano — nemam taj podatak.",
    "Nemam pristup tom izvoru, pa ne mogu potvrditi.",
    "Ne znam to; moji podaci ne pokrivaju taj slučaj.",
]

FACTS = [
    ("Koliko je 12 * 8?", "96"), ("Koliko je 17% od 200?", "34"),
    ("Koji je glavni grad Francuske?", "Pariz"), ("Koliko sekundi ima jedan sat?", "3600"),
    ("Koliko je 144 / 12?", "12"), ("Koliko je 25 + 37?", "62"),
    ("Koliko je 9 * 9?", "81"), ("Koliko je 1000 - 437?", "563"),
    ("Koliko je 3/4 kao procenat?", "75%"), ("Koji je glavni grad Njemačke?", "Berlin"),
    ("Koliko je 15% od 400?", "60"), ("Koliko je 7 * 6?", "42"),
    ("Koliko je PDV 17% na neto 1000 KM?", "170.00"),
    ("Koliko je ukupno sa PDV-om za neto 500 KM?", "585.00"),
    ("Koliko dana ima prijestupna godina?", "366"),
    ("Šta je JSON?", "JSON je tekstualni format za razmjenu strukturisanih podataka."),
    ("Šta je HTTP?", "HTTP je protokol za prenos web sadržaja."),
    ("Šta je Python?", "Python je programski jezik opće namjene."),
    ("Koja je valuta u Bosni i Hercegovini?", "Konvertibilna marka (BAM)."),
    ("Koliko je 21.39 * 1.17?", "25.03"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bal6_data.jsonl")
    ap.add_argument("--n-calls", type=int, default=320)
    ap.add_argument("--n-hedge", type=int, default=320)
    ap.add_argument("--n-facts", type=int, default=160)
    ap.add_argument("--seed", type=int, default=1234)
    a = ap.parse_args()
    rnd = random.Random(a.seed)
    hold = holdout_prompts()

    calls = []
    try:
        for line in open(CALLS_SRC, encoding="utf-8"):
            d = json.loads(line)
            if d.get("kind") == "call" and norm(d["prompt"]) not in hold:
                calls.append({"kind": "call", "prompt": d["prompt"], "call": d["call"]})
    except FileNotFoundError:
        print("MISSING", CALLS_SRC)
        return 2
    rnd.shuffle(calls)
    calls = calls[:a.n_calls]
    if len(calls) < a.n_calls:
        print(f"WARN only {len(calls)} call rows available")

    hedges = []
    seen = set()
    while len(hedges) < a.n_hedge:
        tpl = rnd.choice(TPL)
        x, y = rnd.choice(NAMES + PRODS), rnd.choice(NAMES)
        q = tpl.format(X=x, Y=y)
        if norm(q) in hold or q in seen:
            continue
        seen.add(q)
        hedges.append({"kind": "text", "prompt": q, "answer": rnd.choice(HEDGES), "src": "hedge"})

    facts = []
    while len(facts) < a.n_facts:
        q, ans = rnd.choice(FACTS)
        if norm(q) in hold:
            continue
        facts.append({"kind": "text", "prompt": q, "answer": ans, "src": "fact"})

    rows = calls + hedges + facts
    rnd.shuffle(rows)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"n": len(rows), "calls": len(calls), "hedge": len(hedges),
                      "facts": len(facts), "holdout_excluded": len(hold), "seed": a.seed}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
