# LUMI guard bench v2 — E1 priprema (09.11.2026)

## Šta je popravljeno

| Problem | Dokaz | Popravka |
|---|---|---|
| 116/200 `TimeoutError` na LAIF Mistral-24B (`23580437`) | `guard_200_23580437.summary.json`: `ok 84, err 116, errors {TimeoutError: 116}`, `rps 0,058` | payload nije imao `max_tokens` → vLLM generiše do `max_model_len` (8192) i prelazi `--timeout 120` |
| `run_bench.py` bez ograničenja dužine | linija payloada: `{"model", "messages", "temperature", "seed", "stream"}` | dodato `"max_tokens": args.max_tokens`, novi `--max-tokens` (default `512`), `--timeout` default `120 → 300` |
| sbatch nije prosljeđivao parametre | `serve_and_bench_guard.sbatch`, `laif_smoke.sbatch` | dodato `--timeout ${TIMEOUT:-300} --max-tokens ${MAXTOK:-512}` |

Backup originala: `run_bench.py.bak_maxtok`, `*.sbatch.bak_maxtok`.

## Validacija (Qwen2.5-7B, job `23582040`)

```
n=50, conc=16, wall 4,078 s
ok 50 / err 0            (prije: 116/200 timeout)
rps 12,26
ms_p50 81,48  ms_p95 3.094,57  ms_p99 3.572,43
ttft_p50 37,03  ttft_p95 75,26
false_success 0/50
verdict PASS
```

## Ponovni LAIF test

- Job `23582100`: Mistral-Small-3.2-24B, `N=200`, `CONC=32`, isti set → cilj `err 0`
  (poređenje sa `23580437`: `err 116`).

## Šta ovo znači za E1

- Fiksan budžet generisanja (`max_tokens 512`) → mjerljiv, ponovljiv FSR i latencije.
- `p95` kod malog modela ~3 s pri `conc=16`; za `conc=128/256/512` treba izmjeriti
  (planirane ćelije) i na osnovu toga korigovati `node-h` u `budget_2026-11-09.json`.
- Timeout se više neće miješati sa „false success" (u `check_results.py` `TimeoutError`
  je `err`, ne `false_success`).


## VAŽNO: LAIF Mistral-3.2 nalaz je NEVAŽEĆ (tokenizer bug)

Job `23582100` (Mistral-Small-3.2-24B, N=200, conc=32, **sa** `max_tokens=512`):

```
wall 55,0 s | ok 200 | err 0 | rps 3,635 | ttft_p50 110 ms | ms_p50 13,4 s
false_success 99/200 = 49,5 %  -> check verdict FAIL
```

**Ali:** 116/200 izlaza (58 %) je **byte-salad** (`Ġ`, `Ñ`, `Ċ`), i **svih 99
„false success" su byte-salad**. vLLM/transformers log eksplicitno kaže:

> "The tokenizer you are loading from '/appl/local/laifs/models/Mistral-Small-3.2-24B-Instruct-2506'
> **with an incorrect regex pattern** ... This will lead to incorrect tokenization.
> You should set the `fix_mistral_regex=True` flag ..."

Dodatno: `config.json` → `model_type: mistral3`, `architectures: Mistral3ForConditionalGeneration`,
`tokenizer_mode: auto`.

**Zaključak:** 49,5 % **nije** false-success rate; to je mjerenje pokvarenog dekodiranja.
Ne objavljivati. Mistral-3.2 se **isključuje iz E1** dok se ne riješi tokenizer
(`--tokenizer-mode mistral` uz `mistral-common`, ili lokalna kopija modela sa
`fix_mistral_regex=True`). Za E1 koristiti modele sa ispravnim tokenizerom:
**Qwen2.5-7B** (validiran) i **Llama-3.3-70B** (LAIF, sljedeći test).

### Kako izbjeći istu grešku
- Prije svakog E1 runa: ako >1 % izlaza sadrži `Ġ`/`Ċ`/`Ñ`, run je **INVALID** (ne FSR).
- Dodati u `check_results.py` provjeru `bytey_rate`; ako >1 % → `verdict: INVALID`.


## Rezultati nakon popravke (09.11.2026, 23:5x UTC)

| Model | N | conc | rps | TTFT p50 | ms p50 | ms p95 | FSR | bytey | verdict |
|---|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B (`23582040`) | 50 | 16 | 12,26 | 37 ms | 81 ms | 3,09 s | 0/50 | 0 | **PASS** |
| Llama-3.3-70B (LAIF, `23582381`) | 50 | 16 | 3,10 | 240 ms | 360 ms | 12,67 s | **0/50** | 0 | **PASS** |
| Mistral-3.2-24B (LAIF, `23582100`) | 200 | 32 | 3,64 | 110 ms | 13,4 s | 13,9 s | 99/200 | **58 %** | **INVALID** |

- **Llama-3.3-70B je validan** (TP4, 4 GCD, `max_model_len 8192`, KV cache 25,15 GiB,
  329.696 tokena): `false_success 0/50`, `bytey 0`, `PASS`.
- Mistral je bio pogrešan zbog tokenizera; retest sa `TOKENIZER_MODE=mistral`
  (container ima `mistral_common 1.13.0`) → job **`23582725`**.
- **Account limit:** `sbatch` vraća `MaxSubmitJobsPerAccount` već pri 2 aktivna joba →
  runovi moraju **serijski** (jedan po jedan), ne paralelno.

## Mistral: tri pokušaja, sva tri neupotrebljiva (10.11.2026)

| # | postavke | rezultat |
|---|---|---|
| 1 | `--tokenizer-mode auto` | **byte-salad** (`Ġ`, `Ñ`, `Ċ`) u 100% izlaza |
| 2 | `mistral` (bez MM) | `ValueError: Failed to apply PixtralProcessor on data={'text': '[IMG]'}` |
| 3 | `mistral` + `--limit-mm-per-prompt '{"image":0,"video":0}'` (job `23608526`) | vLLM se digao (`VLLM_READY`), `bytey 0`, ali **degenerirano ponavljanje**: `"richtigelcome }. Feed homeostasis definite definitely definitely definitely..."`, `ok 0/700` |

**Zaključak:** Mistral-Small-3.1/3.2 se ne može korektno servirati ovim putem
(nedostaje `--config-format mistral` / native Mistral chat template za Tekken).
**Isključen iz svih tabela**; nijedan njegov FSR se ne objavljuje. Za buduće pokušaje:
konverzija preko `mistral_common` u Mistral-native format ili `--config-format mistral`.

### Nove environment varijable (`serve_and_bench_guard.sbatch`)
- `TOKENIZER_MODE` (default `auto`) → `--tokenizer-mode`
- `READY_TRIES` (default `150`, tj. 300 s) → za 70B treba `450` (900 s)
- `MAXTOK` (default `512`), `TIMEOUT` (default `300`)

### Procjena za E1 (realno)
- 7B: `12,26 rps` pri `conc=16`; 5.000 zahtjeva ≈ 7 min po ćeliji.
- 70B: `3,10 rps` pri `conc=16`; 5.000 zahtjeva ≈ 27 min + ~6 min load.
- Sa 2 modela × {128, 256, 512} × 5k + jedan 10k: realno **~40–60 node-h**,
  dakle znatno manje od planiranih 200 — budžet treba korigovati **naniže**.
