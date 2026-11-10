# Skaliranje i MFU na LUMI-G (10.–11.11.2026)

Cilj: izmjeriti propusnost, latenciju i MFU po GCD-u za tipičan decode workload,
i naći radnu točku za planiranje kvote.

## Postavka

- Čvor: LUMI-G, 8 GCD (4× MI250X), `dev-g`, jedan posao.
- Workload: 512 zahtjeva, ~256 prompt tokena, **tačno 128 generisanih** tokena
  (`ignore_eos`), `temperature=0`, concurrency 64 i 256.
- MFU = `2 × params × output_tokens/s / (GCD × 191,5 TFLOPS)`; **procjena** —
  zanemaruje attention i prefill (stvarni MFU je niži).
- Skripte: `benchmark/loadgen.py`, `benchmark/e5_scaling.sbatch`.
- Poslovi: **23624574** (Qwen2.5-7B, TP 1/2/4; TP=8 odbijen jer 28 glava nije djeljivo sa 8),
  **23625077** (Mistral-7B, TP 1/2/4/8). Svi runovi: 0 grešaka.

## Rezultati

**Qwen2.5-7B (7,6B, 28 glava)** — job 23624574:

| conc | TP | rps | tok/s | p50 (s) | p95 (s) | MFU |
|---|---|---|---|---|---|---|
| 64 | 1 | 19,2 | 2.458 | 3,27 | 3,61 | 19,5% |
| 64 | 2 | 28,7 | 3.674 | 2,16 | 2,42 | 14,6% |
| 64 | 4 | 30,6 | 3.918 | 2,03 | 2,30 | 7,8% |
| 256 | 1 | 33,7 | 4.315 | 7,23 | 7,54 | **34,3%** |
| 256 | 2 | **57,8** | **7.396** | 4,19 | 4,59 | 29,4% |
| 256 | 4 | 57,8 | 7.393 | 4,10 | 4,46 | 14,7% |

**Mistral-7B-Instruct (7,2B, 32 glave)** — job 23625077:

| conc | TP | rps | tok/s | p50 (s) | p95 (s) | MFU |
|---|---|---|---|---|---|---|
| 64 | 1 | 19,1 | 2.440 | 3,30 | 3,37 | 18,4% |
| 64 | 2 | 27,5 | 3.515 | 2,27 | 2,55 | 13,2% |
| 64 | 4 | 28,8 | 3.691 | 2,17 | 2,34 | 6,9% |
| 64 | 8 | 31,2 | 3.999 | 1,97 | 2,29 | 3,8% |
| 256 | 1 | 32,0 | 4.091 | 7,76 | 8,13 | **30,8%** |
| 256 | 2 | 49,1 | 6.282 | 4,87 | 5,31 | 23,6% |
| 256 | 4 | 51,5 | 6.586 | 4,58 | 4,99 | 12,4% |
| 256 | 8 | **70,5** | **9.023** | 3,14 | 3,75 | 8,5% |

## Nalazi

1. **Jedan GCD daje ~31–34% MFU** na conc 256 (Qwen 34,3%, Mistral 30,8%). To je
   realna gornja granica za ovaj decode workload; preko toga ne ide bez batch-invariant
   kernela ili većeg batcha.
2. **Skaliranje zasićuje, i to model-zavisno.** Qwen: TP2 → TP4 daje **0%** više
   (57,8 rps oba). Mistral: TP4 → TP8 daje **+37%** (51,5 → 70,5 rps). Razlika je u broju
   glava (28 vs 32) i raspodjeli po GCD-ovima — TP se ne smije planirati „po navici".
3. **MFU po GCD-u pada sa TP** (Qwen 34,3% → 14,7%; Mistral 30,8% → 8,5%), jer se isti
   posao dijeli na više GCD-a. TP kupuje **latenciju**, ne efikasnost: p50 pada
   7,23 → 4,10 s (Qwen), 7,76 → 3,14 s (Mistral TP=8).
4. **TP=8 nije univerzalan**: Qwen2.5-7B ima 28 attention glava, pa vLLM odbija TP=8
   (`28 must be divisible by 8`). Za pun čvor treba model sa 32 glave (Mistral) ili TP=7.
5. **Radna točka za kvotu:** Qwen na TP=2/conc 256 (57,8 rps) je najbolji odnos
   propusnost/GPU; TP=4 je bacanje 2 GCD-a. Za latenciju <4 s treba TP=4–8, uz cijenu MFU.

## Ograničenja

- MFU je procjena (bez attention/prefill); apsolutne vrijednosti su gornja granica.
- Samo decode workload sa fiksnim 128 izlaznih tokena; prefill-heavy zadaci se skaliraju drugačije.
- Mjereno na jednom čvoru; **multi-node (DP) skaliranje nije mjereno** u ovoj rundi.

## Reprodukcija

```bash
sbatch benchmark/e5_scaling.sbatch                                   # Qwen, TP 1/2/4
sbatch --export=ALL,MODEL=/scratch/project_465003647/models/mistral-7b-instruct-v0.3,PARAMS_B=7.2 \
       benchmark/e5_scaling.sbatch                                   # Mistral, TP 1/2/4/8
```

Artefakti: LUMI `out/e5_scaling_{23624574,23625077}.json`, `out/scal_tp*_c*_<job>.json`;
sažetak u repou `benchmark/scaling_2026-11-10.json`.
