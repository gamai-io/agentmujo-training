# Correction: adapter attribution in earlier MuJo evaluation notes (2026-11-06)

## What was wrong
Earlier evaluation sbatch files pointed at the `run_v5` adapter path, not at the newer adapters. Figures quoted as `v5e3` and `v6` (for example tool 46/63 = 73.0% and 81/86 = 94.2%) were therefore produced by the `run_v5` adapter and must not be attributed to v5e3 or v6.

## Corrected figures
Re-run with explicit per-adapter paths in one job. Full table with denominators and Wilson 95% intervals: `benchmarks/results/lumi-mujo-2026-11-06-devset.json`.

- v5e3 on v24: tool 46/63, arguments exact 24/54.
- v6 on v24: tool 51/63, arguments exact 31/54, parse 60/63.
- v5e3 on v25: tool 84/86, arguments exact 77/83.
- v6 on v25: tool 83/86, arguments exact 77/83, parse 84/86.
- v5e3 on v26: 31/50; v6 on v26: 36/50 (v26 is not an independent holdout).

## What this means
- v6 improves tool selection on the v24 development set by 5 items and arguments by 7 items versus v5e3, but parses 3 fewer items on v24 and 1 fewer on v25. These differences are within sampling noise at these sizes; no significance is claimed.
- Any earlier report or screenshot citing the old attribution is superseded by this note.

## Method
All runs use `benchmark/eval_text3.py`, greedy decoding, max 256 new tokens. `tool_ok` is a matching heuristic (including multi-call and refusal rules); it does not prove tool execution. `args_sem` is only lowercase/whitespace normalisation.
