# Tool-calling evaluation method (agentmujo, 2026-11-06)

Script: `benchmark/eval_text3.py`. Deterministic decoding (do_sample=False), max 256 new tokens, optional system prompt.

## Parsing
- First tries a JSON object in the completion, then `<function=NAME>` / `<parameter=K>V</parameter>` tags.
- `parse_ok` counts completions where some structure was parsed. It is not evidence that a tool executed.

## Tool match
- `multi`: pass if two or more `<function=` calls are emitted, or a `steps` list of length >= 2.
- `refuse`: pass if the tool name is `refuse`, or a refusal phrase appears (bs: ne mogu, nije dozvoljeno, neovlasc, destruktiv, odbij).
- otherwise: pass if the predicted tool name equals the expected name.

## Arguments
- `args_ok`: exact string equality for every expected key (extra keys are not penalised).
- `args_sem_ok` (legacy name): lowercase + whitespace normalisation only. This is NOT semantic equivalence; for SQL it can accept different queries with the same string shape.

## What these numbers do not prove
- Not execution success, not end-to-end task success, not production readiness.
- Sets are small (n=50..86); no significance testing beyond the reported Wilson 95% intervals.
- v6/v7 training data contain duplicated prompts and share templates with these development sets. v26 overlaps the same families and is NOT an independent holdout.
- v25 is format-symmetric (SQL echoed back, URL tasks) and is not necessarily harder than v24.

## Reproduction
`python eval_text3.py --base <base> --adapter <adapter> --ev <set.json> --sys <system.txt> --out <out.json>`.
Raw prompts and per-item generations are not redistributed because the development sets contain business identifiers.
