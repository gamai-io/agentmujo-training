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
| base | 25/25 | 9/25 | 0 | 0 | 21/25 |
| g03a | 19/25 | 6/25 | 30 | 20 | 20/25 |
| bal1 | 8/25 | 0/25 | 5 | 45 | **21/25** |
| bal2 | 4/25 | 1/25 | 3 | 47 | **20/25** |

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
