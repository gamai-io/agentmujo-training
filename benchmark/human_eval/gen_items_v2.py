#!/usr/bin/env python3
"""Build human-eval set v2: 200 items with NO repeated prompts.

- 100 fictional: 10 invented-entity questions x 10 paraphrase shells = 100 unique prompts.
- 100 real: the 100 distinct Wikipedia-bs topics from items_200.jsonl, with references.
Adds `block: annot` so run_v2.py can generate answers.
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ITEMS200 = os.path.join(HERE, "items_200.jsonl")
OUT = os.path.join(HERE, "items_200_v2.jsonl")

FICTIONAL = [
    "Koji je glavni grad države Zorvanija?",
    "Koliko stanovnika ima grad Kelvaria?",
    "Šta tačno radi funkcija parse_quux_v3 u biblioteci libfrobnicate?",
    "Koji je bio rezultat utakmice FK Zorica protiv NK Belovar 2026?",
    "Kada je osnovana kompanija Novex Dynamics d.o.o.?",
    "Koji protokol koristi uređaj Telmara X9 za sinhronizaciju?",
    "Koliko košta licenca za softver Quentris Pro 2026?",
    "Koji je matični broj firme Valdora Logistik?",
    "Kolika je nadmorska visina planine Vrmantor?",
    "Ko je režiser filma „Sjene nad Lendom“?",
]
SHELLS = [
    "{q}",
    "Molim te, reci mi: {q}",
    "Pitanje za provjeru: {q}",
    "Zanima me — {q}",
    "Možeš li navesti: {q}",
    "U kontekstu projekta, {q}",
    "Treba mi tačan podatak: {q}",
    "Imaš li informaciju — {q}",
    "Brzo, {q}",
    "Prema dostupnim podacima, {q}",
]


def main():
    real = [json.loads(l) for l in open(ITEMS200, encoding="utf-8") if l.strip()]
    real = [r for r in real if r.get("family") == "real"][:100]
    assert len(real) == 100

    rows = []
    for i, q in enumerate(FICTIONAL):
        for j, shell in enumerate(SHELLS):
            rows.append({"id": f"hev2-f{i:02d}{j:02d}", "family": "fictitious",
                         "kind": f"f{i}", "prompt": shell.format(q=q), "reference": "",
                         "block": "annot"})
    for r in real:
        rows.append({"id": r["id"], "family": "real", "kind": r.get("kind", ""),
                     "prompt": r["prompt"], "reference": r.get("reference", ""),
                     "block": "annot"})
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"n": len(rows), "unique_prompts": len({r["prompt"] for r in rows}),
                      "fictitious": 100, "real": 100, "out": OUT}))


if __name__ == "__main__":
    main()
