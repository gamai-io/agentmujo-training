# TP=1 farm: 8 replika na jednom čvoru (11.11.2026)

**Pitanje:** da li je bolje imati 8 nezavisnih TP=1 replika (jedna po GCD) nego jedan
TP=8 server? Ovo provjerava extrapolaciju iz `RESULTS_SCALING` (TP=1 = 32 rps/GCD).

## Postavka

- 1 čvor, 8 GCD; **8 vLLM replika**, svaka `--tensor-parallel-size 1`,
  `--max-model-len 4096`, `--max-num-seqs 64`, pinovana na svoj GCD
  (`HIP_VISIBLE_DEVICES=i`), portovi 8000–8007.
- Model Mistral-7B, workload 2048 zahtjeva, 256 prompt tokena, 128 izlaznih (`ignore_eos`).
- Posao **23638569**; skripta `benchmark/e5_tp1_farm.sbatch`.

## Rezultat

| konfiguracija | ukupni conc | rps | tok/s | p50 | MFU |
|---|---|---|---|---|---|
| 1× TP=8 (posao 23625077) | 256 | 70,49 | 9.023 | 3,14 s | 8,5% |
| **8× TP=1 farm** | 256 | **74,82** | 9.577 | 3,12 s | **9,0%** |
| **8× TP=1 farm** | 512 | **131,39** | 16.818 | 3,58 s | **15,8%** |

## Nalazi (i ispravka)

1. **Extrapolacija „32 rps/GCD × 8 = 256 rps" je bila pogrešna.** Dobili smo 74,8 rps na
   conc 256 — jer se tih 32 rps/GCD mjeri kada **sav** concurrency ide na jedan GCD.
   Sa 8 replika, svaka dobije 32 zahtjeva i radi na nižoj radnoj točki.
2. **Na istom ukupnom concurrency (256) farm nije bolji od TP=8** (74,8 vs 70,5 rps).
3. **Farm skalira sa concurrency**: na 512 daje 131,4 rps uz MFU 15,8%, dok TP=8 na 256
   daje 70,5 rps uz 8,5%. Dakle prednost farma je **efikasnost po GCD na visokom
   concurrency**, ne sirova brzina na istoj točki.
4. **Praktično:** ako posao može držati visok concurrency, TP=1 farm troši manje GCD-a po
   zahtjevu; ako je concurrency nizak, TP=8 je jednostavniji i jednako dobar.

## Ograničenja

- Jedan čvor, jedan model; nije mjereno na 2–4 čvora.
- `max-model-len 4096` (niže od 8192) da KV stane uz 0,85 utilization po GCD.
- Farm je osjetljiv na start: 8 paralelnih loadova; prvi pokušaji pali su na home kvotu
  (`~/.cache/vllm`) i na `srun` step konflikt — rješenja: `VLLM_CACHE_ROOT` na `/scratch`
  i `--overlap` + `HIP_VISIBLE_DEVICES` po replici.

## Reprodukcija

```bash
sbatch -p dev-g --export=ALL,VLLM_CACHE_ROOT=/scratch/project_465003647/vllm_cache,\
SINGULARITYENV_VLLM_CACHE_ROOT=/scratch/project_465003647/vllm_cache \
  /project/project_465003647/gama/e5_tp1_farm.sbatch
```

Artefakti: LUMI `out/farm_c{256,512}_23638569.json`; skripta u repou.
