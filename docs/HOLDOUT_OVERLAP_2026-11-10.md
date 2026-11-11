# Holdout v0.2 — provjera curenja (10.11.2026)

Alat: `benchmark/holdout_overlap.py` — za svaki od 60 privatnih holdout zadataka računa
maksimalnu Jaccard sličnost token-skupa prema **svim** dev/eval promptovima koje koristimo
(bench v0.6, conf14, conf50, items_v2, bal5/bal6 treninzi, eval promptovi sa LUMI-ja).

## Rezultat

| set | n | max sličnost | egzaktni duplikati | status |
|---|---|---|---|---|
| `bal5_data.jsonl` | 400 | **1,000** | **1** | **curenje** |
| `bal6_data.jsonl` | 800 | **0,500** | **0** | čist |
| svi ostali (bench/conf/v2) | ~2000 | ≤ 0,43 | 0 | čist |

**Nađeni duplikat:** holdout `amj-ev2-****` (sadržaj redigovan) pojavljuje se **identično**
u bal5 trening setu (u listi „kratkih činjenica" koja je dodata u bal5). Posljedica: bal5
rezultati na tom jednom zadatku nisu validni kao generalizacija (1/60 = 1,7% holdouta).

## Šta je urađeno

1. `benchmark/gen_bal6.py` sada **isključuje svaki prompt iz holdouta** (normalizovano
   poređenje) — isključen 61 prompt pri generisanju.
2. bal6 je ponovo provjeren: `max_sim 0,500`, `0` duplikata → **PASS**.
3. Provjera je deo rutine prije svakog novog treninga (ne ide u CI jer holdout ostaje
   privatan i van repozitorija).

## Napomena

Prag: `max_sim < 0,8` = prihvatljivo; `≥ 0,999` = egzaktan duplikat (blokira). Sličnosti
0,4–0,5 su posljedica zajedničkog vokabulara (npr. „provjeri da li … postoji …"), ne
curenja sadržaja.
