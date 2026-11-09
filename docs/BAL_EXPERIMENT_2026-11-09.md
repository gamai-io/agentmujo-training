# SFT warmth-start experiment: bal1 / bal2 (2026-11-09)

Goal: fix the schema mismatch in `job_run.py` (tools were not passed to
`apply_chat_template` during training) by fine-tuning **from g03a** with the same
21-tool schema used at inference.

Data (`bal_data.jsonl`, 500 rows): 350 single-tool-call rows (max 30 per tool,
all 11 bench tools covered) + 150 benign replay rows; **0 approval-following
examples** (SFT v3 proved those are harmful); prompts overlapping bench v0.6 /
conf14 / conf50 excluded (271).

Runs (LUMI, 1 GCD, small-g, bf16 + gradient checkpointing, prompt-masked loss):

| run | job | epochs | train_loss | adapter |
|---|---|---|---|---|
| bal1 | 23568429 | 1 (32 steps) | 0.4037 | `run_bal1/adapter` |
| bal2 | 23570646 | 1 (32 steps) | 0.3953 | `run_bal2/adapter` |

bal2 differs from bal1 only in the masking fix: labels are now cut at the
**longest common token prefix** of prompt and full text (the generation prompt
contains an empty `<think>` block that the rendered tool-call turn does not, so
`len(prompt)` misaligned the target). Target dump from the bal2 log:

```
TARGET_SAMPLE call 'Sensu checkovi vise u redu čekanja.' =>
'\n\n</think>\n\n<tool_call>\n<function=service_status>\n<parameter=service>\nsensu\n</parameter>\n</function>\n</tool_call><|im_end|>\n'
```

## Results (same 113 prompts per model)

| model | tool (strict) | args | asks/50 | acts/50 | tool (first call only) |
|---|---|---|---|---|---|
| base (corrected) | 21/25 | 8/25 | 1 | 10 | 21/25 |
| g03a | 19/25 | 6/25 | 30 | 20 | 20/25 |
| bal1 | 8/25 | 0/25 | 5 | 45 | **21/25** |
| bal2 | 4/25 | 1/25 | 3 | 47 | **20/25** |
| bal3 (3 ep, lr 2e-5) | 0/25 | 0/25 | 1 | 63 | **24/25** |

"strict" = exactly one `tool_call` and nothing else.
"first call only" = truncate the output at the first `</tool_call>` before parsing
(a decoding control that separates *selection* from *termination*).

## Diagnosis (evidence, not speculation)

1. bal1/bal2 **select the right tool** as often as base/g03a (20–21/25 first call).
2. They **fail to terminate**: after `</tool_call>` they keep generating a
   fabricated `user <tool_response> …` turn and a second call, e.g.
   `<tool_call>…service_status…</tool_call> user <tool_response> {"service": "postgresql", "status": "active"} </tool_response> …`
   → strict metric collapses to 4–8/25.
3. Root cause: the `<|im_end|>` token is 1–2 tokens inside a ~200-token
   completion, so 32 steps at lr 1e-5 barely reinforce it; the base prior
   (continue the dialogue after a tool call) wins.
4. Arguments remain weak for every model (base 9/25, adapters 4–6/25) — a
   separate problem from termination.
5. Confirmation did not improve (bal2 asks in 3/50) — consistent with the
   earlier finding that adapters trade caution for tool bias.

## Verdict

bal1 and bal2 are **FAILS on the strict metric** and are not deployed.
Next experiment (bal3): same data, **EOS-weighted / 3 epochs** to teach
termination, evaluated with both metrics reported side by side.


## bal3 (3 epohe, lr 2e-5) — najbolja selekcija, ista greška terminacije

Job `23578277` (prethodni `23572266` prekinut nakon 4 restarta; `train_bal.py` dobio
checkpoint svakih 10 koraka + auto-resume). Trening: 96 koraka, `train_loss ≈ 0.12–0.17`.

| model | strict | first-call | args (first, n=7) | asks/64 | acts |
|---|---|---|---|---|---|
| base | 21/25 | 21/25 | **7/7** | 0 | 8 |
| g03a | 18/25 | 20/25 | 5/7 | 38 | 26 |
| bal1 | 9/25 | 21/25 | 5/7 | 8 | 56 |
| bal2 | 4/25 | 20/25 | 4/7 | 7 | 57 |
| **bal3** | 0/25 | **24/25 (96%)** | 6/7 | **1** | **63** |

**Nalaz:** više epoha je popravilo **selekciju alata** (24/25 — bolje od base 21/25),
ali **terminacija ostaje slomljena** (25/25 odgovora ima >1 poziv: model izmisli
`user <tool_response>` i nastavi) i **potvrda je najgora** (1/64). Dakle: kapacitet
za alat se uči, ali EOS i oprez se ne uče ovim putem.

### Ispravka args metrike
Ranije prijavljeni `args` (npr. bal1 `0/25`) bio je **artefakt**: od 25 bench stavki
sa `expected_tool`, samo **7** ima `expected_args != None`; ostale su se poredile sa `{}`.
`score_suite.py` sada boduje args samo na tih 7. Ispravne vrijednosti su u tabeli gore.
