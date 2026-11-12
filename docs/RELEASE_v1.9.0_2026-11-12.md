# AgentMujo v1.9.0 — evidence pack (2026-11-12)

Adds the E-F v3 false-success campaign (n=50, six models), the human evaluation, and the grant
audit corrections. DOI `10.5281/zenodo.24178790` (concept `10.5281/zenodo.24118912`).

## E-F v3 — false success at n=50 and policy ablations

| Model | base | evidence | strict |
|---|---|---|---|
| Apertus-70B (LUMI Aitta) | 18/50 = 36.0% (6/250); **22/50 = 44.0% (8/400)** | 10/50 = 20.0% (6/250) | 2/50 = 4.0% |
| Llama-3.3-70B (LUMI Aitta) | 5/50 = 10.0% (6/250); **11/50 = 22.0% (8/400)** | 1/50 = 2.0% (6/250); **14/50 = 28.0% (8/400)** | 0/50 |
| gpt-oss-120b | 5/50 = 10.0% | 0/17 (33x 429) | — |
| DeepSeek-chat | 1/50 = 2.0% | 1/50 = 2.0% | — |
| Qwen3.8-27B | 0/43 | 0/19 (429) | — |
| Qwen2.5-7B (local LUMI) | 2/50 = 4.0% | 0/50 | — |

**Central negative result:** the false-success rate and the effect of the evidence contract depend
on the step/token budget. At 6 steps/250 tokens Apertus 36% and Llama 10% (evidence 2%); at
8/400 Apertus 44% and Llama 22% (evidence 28%). A strict prompt that forbids inventing missing
inputs cut Apertus to 4% and Llama to 0% at 6/250. Every false success was adjudicated in the
sandbox: fabricated preconditions, empty sandboxes, stale files, wrong exit codes, wrong paths.

## Human evaluation

Three annotators x 200 unique items, full coverage. Raw Fleiss kappa 0.48 (pairwise 0.39/0.38/0.67,
19 discrepancies); a post-hoc mapping of fictitious ANSWER_OK to HEDGE gives kappa 0.886 (sensitivity
only, not pre-registered). FABRICATE 1/600 raw, 0/600 on real items. CSVs and scorer output included.

## Grant-audit corrections

- **Quota accounting fixed:** 838.70 GCD-h = 419.35 GPU-h = 104.8 node-h = **8.4%** of the award
  (5,000 GPU-h = 1,250 node-h = 10,000 GCD-h); the earlier 16.2% was a unit error (4 vs 8 GCD/node).
- Double-awarding: AI Factories/AI-for-Science Terms reject proposals that are currently running;
  Fast Lane/AI for Science are not submitted before 2027-01-29. Benchmark rules carry no such
  clause; written confirmation is required before 2026-12-01.
- Novelty positioning: false success (2606.09863), evidence contracts (2609.35732) and batch
  invariance on MI250X (vLLM PR #52231) are prior art; the defensible contribution is the link
  between inference nondeterminism and false-success audit variance.

## What this deposit does not claim
No causal explanation for the TP=8 restart mismatch; no multi-node TP=16; no calibrated probe
false-rejection; no peer review. Apertus/Llama strict arms use 6 steps/250 tokens; the 8/400
Apertus evidence arm was still running at freeze time. The human-evaluation post-hoc kappa is a
sensitivity analysis, not a pre-registered result.
