#!/usr/bin/env python3
"""bal5 training data: teach 'admit unknown' without over-refusing.

200 rows: questions about entities that do not exist -> hedge answer.
200 rows: normal answerable questions -> correct short answer.
Different fictional names than bench v2 (seed 2026) to avoid contamination.
"""
import argparse
import json
import random

FICTIONAL = [
    ("država", "Koji je glavni grad države {X}?"),
    ("grad", "Koliko stanovnika ima grad {X}?"),
    ("firma", "Koji je matični broj firme {X} d.o.o.?"),
    ("uredjaj", "Koji protokol koristi uređaj {X}?"),
    ("softver", "Koliko košta licenca za {X} Pro?"),
    ("utakmica", "Kakav je bio rezultat utakmice {X} protiv {Y}?"),
    ("osoba", "Kada je {X} osnovao kompaniju {Y}?"),
    ("rijeka", "Koliko je duga rijeka {X}?"),
    ("planina", "Kolika je visina planine {X}?"),
    ("zakon", "Šta propisuje član 44. Zakona o {X}?"),
]

NAMES = ["Zorvanija", "Kelvaria", "Marduk", "Telmara", "Quentris", "Novex",
         "Valdora", "Sintara", "Orbela", "Pentar", "Kaldris", "Velmora",
         "Astrix", "Dunvar", "Ekloria", "Fintara", "Gravon", "Helvira",
         "Istrix", "Jorvak"]
PRODUCTS = ["Quentris", "Frobnicate", "Telmara", "Zorbex", "Kelvinor", "Astrafon",
            "Brontar", "Cymbel", "Deltaris", "Evolvex"]

HEDGES = [
    "Ne znam — nemam podatak o tome i ne mogu ga provjeriti.",
    "Nije poznato; nemam pristup tom podatku.",
    "Ne mogu potvrditi — taj podatak mi nije dostupan.",
    "Ne raspolažem tim podatkom. Provjeri u zvaničnom registru.",
    "Nemam informacije o tome i ne bih nagađao.",
    "Ne mogu provjeriti taj podatak, pa ne znam odgovor.",
    "Nije mi poznato. Ne želim izmišljati broj ili naziv.",
    "Nemam podatke o tome; preporučujem provjeru kod nadležne institucije.",
]

FACTS = [
    ("Koliko je 12 * 8?", "96"),
    ("Koliko je 17% od 200?", "34"),
    ("Koji je glavni grad Francuske?", "Pariz"),
    ("Koji je glavni grad Bosne i Hercegovine?", "Sarajevo"),
    ("Koliko sekundi ima jedan sat?", "3600"),
    ("Šta je JSON?", "JSON je tekstualni format za razmjenu strukturisanih podataka."),
    ("Koliko je 144 / 12?", "12"),
    ("Koja je valuta u Bosni i Hercegovini?", "Konvertibilna marka (BAM)."),
    ("Koliko je 25 + 37?", "62"),
    ("Šta je HTTP?", "HTTP je protokol za prenos web sadržaja."),
    ("Koliko dana ima godina koja nije prestupna?", "365"),
    ("Koliko je 9 * 9?", "81"),
    ("Koji je hemijski simbol za vodu?", "H2O"),
    ("Koliko je 1000 - 437?", "563"),
    ("Šta je Python?", "Python je programski jezik opće namjene."),
    ("Koliko je 3/4 kao procenat?", "75%"),
    ("Koji je glavni grad Njemačke?", "Berlin"),
    ("Koliko je 15% od 400?", "60"),
    ("Šta je baza podataka?", "Baza podataka je organizovan skup podataka kojim se upravlja DBMS-om."),
    ("Koliko je 7 * 6?", "42"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="bal5_data.jsonl")
    ap.add_argument("--n-hedge", type=int, default=200)
    ap.add_argument("--n-facts", type=int, default=200)
    ap.add_argument("--seed", type=int, default=999)
    a = ap.parse_args()
    rnd = random.Random(a.seed)

    rows = []
    for i in range(a.n_hedge):
        kind, tpl = rnd.choice(FICTIONAL)
        x = rnd.choice(NAMES + PRODUCTS)
        y = rnd.choice(NAMES)
        q = tpl.format(X=x, Y=y)
        rows.append({"kind": "text", "prompt": q, "answer": rnd.choice(HEDGES), "src": "hedge"})
    for i in range(a.n_facts):
        q, ans = rnd.choice(FACTS)
        if rnd.random() < 0.3:
            q = q + " Odgovori kratko."
        rows.append({"kind": "text", "prompt": q, "answer": ans, "src": "fact"})
    rnd.shuffle(rows)
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"n": len(rows), "hedge": a.n_hedge, "fact": a.n_facts, "seed": a.seed}))


if __name__ == "__main__":
    main()
