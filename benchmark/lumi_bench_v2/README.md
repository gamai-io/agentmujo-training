# LUMI guard bench v2 (snapshot 09.11.2026)

Preslika radnog kita sa LUMI-ja (`/project/project_465003647/gama/bench_v2/`) radi verzionisanja.

## Izmjena 09.11.2026 (timeout fix)
- `run_bench.py`: `payload` sada nosi `"max_tokens": args.max_tokens`; novi `--max-tokens`
  (default `512`); `--timeout` default `120 -> 300`.
- `serve_and_bench_guard.sbatch`: dodato `--timeout ${TIMEOUT:-300} --max-tokens ${MAXTOK:-512}`.
- Razlog: 116/200 `TimeoutError` na Mistral-Small-3.2-24B jer nije bilo ograničenja dužine
  generisanja (vLLM je išao do `max_model_len`), pa je prelazio timeout od 120 s.
- Validacija (Qwen2.5-7B, job `23582040`): `n=50, conc=16`, `ok 50, err 0`, `rps 12.26`,
  `ttft_p50 37 ms`, `ms_p95 3.09 s`, `false_success 0/50`, `verdict PASS`.

Pokretanje:
```bash
sbatch --partition=dev-g --export=ALL,N=50,CONC=16,MODEL=/scratch/project_465003647/models/qwen25-7b \
  serve_and_bench_guard.sbatch
```
