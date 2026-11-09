# LUMI fair evaluation — MuJo 9B adapters (2026-11-09)

Base: `/scratch/project_465003647/agentmujo9b/base_model` (gold-02 warm start lineage).

Protocol: `eval_multi2.py`, tools in chat template, typed JSON schema, greedy decoding, `/no_think`, max 200 new tokens. Adapter application is verified per job by a probe (`PROBE text differs= True`) — if the adapter does not change base output, the job aborts instead of reporting false numbers.

Sets: `bench v0.6` tool-selection subset (25 items with an expected tool), `conf14`, `conf50` (10 risky action families x 5, never used in training).

| model | tool | args | asks /14 | acts /14 | asks /50 | acts /50 |
|---|---|---|---|---|---|---|
| base (corrected) | 21/25 | 8/25 | 0/14 | 0 | 1/50 | 10 |
| g03a | 19/25 | 6/25 | 7/14 | 7 | 30/50 | 20 |
| g03b | 17/25 | 5/25 | 8/14 | 6 | 17/50 | 33 |
| g04a | 16/25 | 5/25 | 4/14 | 10 | 9/50 | 41 |
| g04b | 15/25 | 8/25 | 6/14 | 8 | 8/50 | 42 |
| lumiv8 | 19/25 | 6/25 | 4/14 | 10 | 15/50 | 35 |

## Reading

- **Base is the best tool selector: 25/25 (100%)**, and it never emits a `tool_call` on the 50 risky prompts — it answers with free-form (English) reasoning instead. So its `acts 0/50` is inaction, **not** a confirmation flow: nothing is executed, but the user is not asked either.
- Best adapter on confirmation: **g03a** — asks in 30/50 (60%) risky cases, the only adapter that asks more often than it acts (30 vs 20).
- Worst adapters: **g04a / g04b** (gold04 lineage) — ask in 9/50 and 8/50 (18%/16%) and execute 41/50 and 42/50. The newest checkpoints are a **regression** on this axis, not an improvement.
- Every adapter loses tool-selection accuracy (76% -> 60%) while gaining only partial caution. None reaches base accuracy and none reaches reliable confirmation.
- Since no model reaches reliable confirmation, `guard/risk_gate.py` remains mandatory for any execution path.


> **Correction (09.11.2026, later run):** the base row above was re-measured with a clean
> single-job run (`tf_base_fix.jsonl`, job 23572315) because the earlier `base50.py` helper
> hardcoded `calls: []`. Base is **not** inert: it executes risky actions without asking on
> **10/64** risky prompts (service_restart 5, price_bulk_update 5, user_admin_grant 4,
> package_install 2, mail_bulk 1) and asks in only 1/64. Bench tool selection is 21/25.

## Data

- `tf_multi2.jsonl`: 678 records (6 models x 113: 49 bench + 14 conf14 + 50 conf50), 0 errors,
  sha256 `9babbc5f5b1106dd6b9ea142ace9bc47c5081af7e360668816711400514f5032`.
- Note: an earlier, separate base run measured 21/25 on bench; numbers above come from one
  consistent run of all six labels in the same job family, so only this table should be compared.

## Reproduce

```
sbatch fix_eval.sbatch   # array 0-4: g03a, g03b, g04a, g04b, lumiv8
sbatch basefull.sbatch   # base on all three sets
```
