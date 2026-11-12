# AgentMujo v1.8.1 — correction release (2026-11-12)

v1.8.0 recorded the wrong `git_commit` in MANIFEST.json (`8c9468c…`, a stale local clone).
The correct commit is **`d2529c9786146c2fbad2b19049e8802147e64796`** (HEAD of
`github.com/gamai-io/agentmujo-training` at release time). File contents are unchanged except
README/CITATION DOI. This release corrects provenance only.

Adds E-D/E-E (TP=8 intermittency) and E-F (false-success pilot) to v1.7.
DOI `10.5281/zenodo.24160949` (concept `10.5281/zenodo.24118912`).

## New in v1.8

### E-D — RCCL sweep at TP=8 (Mistral-7B, BI=1)
- Baseline (no pinning) and four pinned configs {Ring,Tree}x{Simple,LL128} with
  `LAUNCH_ORDER_IMPLICIT=0`: **all 48/48 across a restart**, 0/16 variation.
- `LAUNCH_ORDER_IMPLICIT=1` configurations **fail to start** on this RCCL/ROCm stack.
- The 36/48 mismatch seen in job 23661013 was not reproduced; no evidence that pinning
  changes the outcome.

### E-E — intermittency (5 restarts per config)
- **15/15 restarts bit-identical** (baseline, Ring/Simple, Tree/Simple), 48/48.
- Combined with 23661013: **1 mismatch in 16 restarts** (~6.25%, Wilson 1.1-28.3%).
- Conclusion: the TP=8 restart difference is rare and intermittent, not systematic;
  a cause cannot be attributed from these data.

### E-F — false-success pilot (Qwen2.5-7B, Mistral-7B; 10 deterministic file tasks)
- Qwen: **0/20 false successes**. The two DONE claims were on nonzero-exit tasks and the probe
  passed (true successes). Floor effect: the hypothesis (evidence contract reduces false
  success) is not testable at n=20 with no events.
- Mistral rollouts are **invalid** (no JSON tool calls, 0-0.3 steps) and are excluded.
- Not a cross-lab test: GLM/DeepSeek were not available locally.

## What this deposit does not claim
No cause for the TP=8 restart mismatch; no TP=16 multi-node; no cross-lab false-success rate;
no human kappa yet (kit included, CSVs not returned); no peer review. E-F is a 10-task pilot
with a floor effect and one invalid model arm.
