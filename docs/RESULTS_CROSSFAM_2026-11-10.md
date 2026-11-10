# Cross-family replikacija bench v2 (LUMI, 10.11.2026)

Cilj: provjeriti da nalazi ne vise na jednoj model-familiji. Dvije ne-Qwen familije,
3 seeda, istih 700 stavki, `temperature=0`, `max_tokens=256`, conc 64, TP=4.
Poslovi: `23621892` (Phi-3.5), `23622412` (Mistral, `NO_THINK=0`). Svi runovi: **0 grešaka**.

## Rezultati

| model | seed 42 | seed 43 | seed 44 | flips vs s42 | b1 | b2 | b4 | b5 |
|---|---|---|---|---|---|---|---|---|
| Mistral-7B-Instruct-v0.3 | 38,4% | 38,3% | 38,6% | 5 / 9 | 0,7–1,0% | 99% | 25–27% | 70,5% |
| Phi-3.5-mini-instruct | 37,7% | 35,9% | 36,0% | 23 / 22 | 10,7–15,0% | 87–88% | 0–1% | 63,5–65,5% |
| Qwen2.5-7B (referenca, s42) | 60,6% | — | — | — | 17,3% | 99% | 73–81%* | 100% |

\* Qwen2.5-7B honesty varira 73–81% između runova (E2).

## Nalazi

1. **Red veličine se drži van Qwen familije**: 36–39% za oba modela, ispod Qwen2.5-7B
   (60,6%) i blizu gpt-oss-120b (66,7% je iznad). Nije „Qwen je poseban slučaj".
2. **Isti obrazac po blokovima**: needle je lak (87–99%), tool-JSON srednji (63–71%),
   aritmetika katastrofalna (0,7–15%), honesty niska (0–27%).
   To je konzistentno sa nalazom da su zadaci šablonski, a ne domen-specifični.
3. **Mistral je gotovo pa stabilan između seedova** (5 i 9 od 700 = 0,7–1,3% flipova),
   Phi-3.5 znatno manje (23 i 22 = 3,3%). Dakle nestabilnost izlaza je
   **model-zavisna**, ne univerzalna — dodatni argument protiv tvrdnji o „bit-identical".
4. **Honesty se ne popravlja familijom**: Phi-3.5 praktično nikad ne hedžuje (0–1%),
   Mistral 25–27%, Qwen 73–81%. Raspon 80 pp između modela iste veličine klase.

## Ograničenja

- Jedan seed-set (42/43/44) i jedan concurrency (64).
- Phi-3.5 i Mistral su Instruct modeli bez thinking režima; Qwen2.5-7B je base — poređenje
  je familijsko, ne „isti tip modela".
- Mistral run je morao ići sa `NO_THINK=0`: `chat_template_kwargs.enable_thinking`
  izaziva HTTP 400 na Mistral tokenizeru (dokumentovano u `e2_crossfamily.sbatch`).

## Reprodukcija

```bash
sbatch --export=ALL,MODEL_PATH=/scratch/project_465003647/models/mistral-7b-instruct-v0.3,MODEL_TAG=mistral,NO_THINK=0 \
  -p dev-g /project/project_465003647/gama/e2_crossfamily.sbatch
```

Artefakti: LUMI `out/e2_crossfamily_23621892.json`, `out/e2_crossfamily_23622412.json`,
`out/v2cf_{mistral,phi35}_s{42,43,44}_<job>.jsonl`. Skripta:
`benchmark/e2_crossfamily.sbatch`.
