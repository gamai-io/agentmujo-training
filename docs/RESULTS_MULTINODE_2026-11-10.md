# Multi-node (data-parallel) skaliranje — 2 i 4 čvora (10.–11.11.2026)

Cilj: izmjeriti da li se propusnost skalira linearno sa čvorovima i koliko to košta
u GPU-satima. Model: Mistral-7B-Instruct, jedan vLLM replica po čvoru, TP=8 (pun čvor).

## Postavka

- Jedna replica = 1 čvor = 8 GCD, `--tensor-parallel-size 8`.
- Klijent šalje na sve replike round-robin (`loadgen.py --url h1,h2,...`).
- Workload: `N=2048`, ~256 prompt tokena, tačno 128 izlaznih (`ignore_eos`).
- **Ključno:** ukupni concurrency se skalira sa brojem replika (256 po replici), inače
  mjeriš zasićenje klijenta, a ne skaliranje.
- Poslovi: 23625077 (1 čvor), 23626081 (2), 23626364 (4). Svi: 0 grešaka.

## Rezultati (256 concurrency po replici)

| čvorova | GCD | ukupni conc | rps | tok/s | ubrzanje | rps/GCD | MFU |
|---|---|---|---|---|---|---|---|
| 1 | 8 | 256 | 70,49 | 9.023 | 1,00× | 8,81 | 8,48% |
| 2 | 16 | 512 | 140,37 | 17.968 | **1,99×** | 8,77 | 8,44% |
| 4 | 32 | 1.024 | 269,55 | 34.503 | **3,82×** | 8,42 | 8,11% |

Efikasnost paralelizacije: **99,5% (2 čvora), 95,6% (4 čvora)**.

Kontrolni test (isti ukupni conc, bez skaliranja po replici): 2 čvora na conc 256 daju
samo 93,98 rps (1,33×), jer svaka replica dobije 128 umjesto 256 konkurentnih zahtjeva.
To nije kvar skaliranja, nego pogrešna mjerna postavka.

## Nalazi

1. **Data-parallel skaliranje je praktično linearno** dok se concurrency drži po replici:
   1,99× na 2 i 3,82× na 4 čvora, uz nepromijenjen rps/GCD (8,81 → 8,42).
2. **Mreža između čvorova ne škodi**: nema pada po GCD-u, nema dodatnih grešaka.
3. **Praktična brojka za planiranje kvote:** ~8,4 rps po GCD za 7B na MI250X u TP=8
   konfiguraciji, tj. **~30.000 zahtjeva po GCD-satu** (8,4 × 3600).
4. **TP=8 nije najbolji po GCD-u.** U intra-node tabeli (isti model, conc 256):
   TP=1 daje 32,0 rps/GCD, TP=2 24,5, TP=4 12,9, TP=8 8,8. Dakle za maksimalnu propusnost
   po kvoti treba **više replika sa manjim TP** (TP=1–2), a TP=8 ima smisla samo za
   latenciju. Ovo je izvedeno iz izmjerenih tačaka; DP sa TP=1 replikama **nije direktno
   mjeren** u ovoj rundi.
5. **Latencija raste sa opterećenjem, ne sa čvorovima**: p50 3,19 s na 4 čvora (conc 1024)
   vs 3,14 s na 1 čvor (conc 256) — po replici je isto.

## Ograničenja

- Samo Mistral-7B (32 glave, TP=8 moguć); Qwen2.5-7B ne podržava TP=8.
- Jedan seed/postavka; nema mjerenja sa TP=1/2 replikama preko čvorova (samo izvedba).
- MFU je procjena (bez attention/prefill) i opada sa TP jer se rad dijeli.

## Reprodukcija

```bash
sbatch --nodes=2 --export=ALL,N=2048,CONCS='256 512'   benchmark/e5_multinode.sbatch
sbatch --nodes=4 --export=ALL,N=2048,CONCS='256 512 1024' benchmark/e5_multinode.sbatch
```

Artefakti: LUMI `out/e5_multinode_{23626081,23626364}.json`, `out/mnode_*_<job>.json`;
sažetak u repou `benchmark/multinode_2026-11-10.json`.
