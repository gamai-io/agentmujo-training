# Results index — what has been measured (updated 2026-11-11)

Evidence pack v1.8.1: DOI `10.5281/zenodo.24161031` (concept `10.5281/zenodo.24118912`).

One page, every number with its artifact. Machine: LUMI-G (AMD MI250X, project 465003647).
Unless stated otherwise: `temperature=0`, `seed=42`, 4 GCDs per job.

## Claims and gates

| Result | Number | Artifact |
|---|---|---|
| Scale guard requests (E1/E5) | 36,550 requests, 0 errors, 0 false successes | `docs/SUMMARY_v1.5_2026-11-10.md` §1, §5 |
| Bench v2 (700 items, 4 blocks) | best gpt-oss-120b 66.7%; Qwen2.5-7B 60.6–61.7% | `docs/RESULTS_BENCH_V2_2026-11-10.md` |
| Template correction (24 templates) | design effect 4.7–21.9; effective N 32–149 | `docs/RESULTS_STATS_2026-11-10.md` |
| Accuracy is template-driven | Qwen `b1_sub` 0/114, `b1_total` 0/79 | same |
| Cross-family | Mistral-7B 38.4/38.3/38.6%; Phi-3.5 37.7/35.9/36.0% | `docs/RESULTS_CROSSFAM_2026-11-10.md` |
| Honesty, fictional entities (b4) | Qwen 73–81%, bal6 41% (SFT hurt) | `docs/SUMMARY_v1.5_2026-11-10.md` §8 |
| Honesty, real obscure entities (500) | forced: 94.8 / 74.4 / 71.4% fabrication; allowed to refuse: 21.6–22.0 / 17.0–18.0 / 11.4–13.0% | `docs/RESULTS_HONESTY_REAL_2026-11-10.md` |
| SFT dose-response (bal7) | 2→4 epochs: no further change (bench 63.4%, b4 41/100, honesty_real 82.8→83.0%); on real entities SFT raised correct answers 26→86/500 | `docs/RESULTS_BAL7_2026-11-11.md` |
| E3 injection, in-sample | V1 33.0%/35.0% · V2 90.1%/2.5% (detection/FP) | `docs/RESULTS_E3_2026-11-10.md` |
| E3 out-of-distribution (independent generator) | **46.8%** detection, 6/48 false blocks | `docs/RESULTS_E3_OOS_2026-11-10.md` |
| Invoice gate (E6) | recall 1,109/1,109 = 100%, FP 0/391 | `benchmark/e6_check.json` |
| Probe sensitivity (E13) | same data: 0% / 30.2% / 47.8% / 49.1% / **100%** recall by probe depth | `docs/RESULTS_E13_2026-11-11.md` |
| RiskGate v1 vs v2 (1,000 attacks / 500 benign) | 52.6% → **100%**, 0/500 false blocks | `docs/RESULTS_RISKGATE_STRESS_2026-11-10.md` |
| Encoded (white-box) evasion | v2 100% only via fail-closed; with `terminal` allowlisted 45/56 (11 bypasses) | same |
| Verifier economics (E12) | no-evidence: 1.4% (self) / 0% (cross); with reference: 98.6% but 44% false alarms; Mistral approves 177 while 18 correct | `docs/RESULTS_E12_2026-11-11.md` |
| Adaptive adversary (E10) | v2 fail-closed 0% ASR; with shell allowlisted **100% at the first mutation**; decode-aware v3 0% on the 8-mutation set | `docs/RESULTS_E10_2026-11-11.md` |
| Attribution error (E14) | system self-heals: Qwen claims credit **75%**, Phi **87%** (94–100% correct when causal); Mistral abstains 73% | `docs/RESULTS_E14_2026-11-11.md` |

## Reproducibility / determinism

| Result | Number | Artifact |
|---|---|---|
| Serial decoding is not bit-identical | 660/700 (TP=4), 669/700 (TP=1) | `docs/RESULTS_E2_2026-11-10.md` |
| `VLLM_BATCH_INVARIANT=1` | within process **700/700** (TP=1 and TP=4); across independent restarts **700/700** in repeated tests (Qwen and Mistral, TP=1 and TP=4) (earlier 586/700 did not reproduce; see correction) | `docs/RESULTS_BATCHINVARIANT_2026-11-10.md` |
| Qwen3-VL-30B-A3B on LUMI (bench v2) | **576/700 = 82.3%** (toolargs 200/200, honesty 47/100); E-F **0/50** false success; invoice supplier/invoice/total 20/20, date 14/20 | `docs/RESULTS_BIG_30B_2026-11-13.md` |
| MI250X full atlas: run-to-run nondeterminism at B=1 | **3/16** prompts (TP1 and TP4); `BI=1` **0/16** | `docs/RESULTS_E_A_FULL_2026-11-11.md` |
| MI250X full atlas: batch match vs B=1 | default 0.81-0.85; `BI=1` **1.0000** (B=2/8/32, TP1/TP4) | same |
| MI250X full atlas: BI is not TP-invariant | TP1 vs TP4 **39/48 = 81.25%** | same |
| MI250X full atlas: TRITON_ATTN at TP1 | **48/48 identical to default**; does not remove variation | same |
| False-success v3: identical limits (8/400) | Apertus **22/50 base (44%, CI 31.2-57.7)**; Llama **11/50 (22%) -> 14/50 evidence (28%)**; config-dependent vs 6/250 | `docs/RESULTS_E_F_V3_2026-11-12.md` |
| False-success v3: strict-policy ablation | Apertus **18/50 -> 10/50 -> 2/50**; Llama **5/50 -> 1/50 -> 0/50** (base/evidence/strict) | `docs/RESULTS_E_F_V3_2026-11-12.md` |
| False-success v3: Llama-3.3-70B and local Qwen2.5-7B at n=50 | Llama **5/50 base (10%) -> 1/50 evidence (2%)**; Qwen2.5-7B **2/50 (4%) -> 0/50** | `docs/RESULTS_E_F_V3_2026-11-12.md` |
| False-success v3 Apertus-70B at n=50 | **18/50 base (36%, CI 24.1-49.9)** vs **10/50 evidence (20%, CI 11.2-33.0)**; missing 8->2, impossible 6->6 | `docs/RESULTS_E_F_V3_2026-11-12.md` |
| False-success v3 (n=50; DeepSeek/Qwen3.8/gpt-oss) | DeepSeek **1/50 base, 1/50 evidence**; Qwen3.8 0/43, 0/19; gpt-oss **5/50 base**, 0/17 evidence (429s) | `docs/RESULTS_E_F_V3_2026-11-12.md` |
| False-success v2 (E-F v2, 5 modela, n=11/arm) | **Apertus-70B 4/11 base vs 1/11 evidence**; Qwen-72B 2/11; Qwen3.8 1/11; DeepSeek 0/11; gpt-oss 0/9 | `docs/RESULTS_E_F_V2_2026-11-12.md` |
| False-success pilot (E-F, Qwen2.5-7B) | **0/20** false success (floor); 2 DONE both true successes; Mistral rollouts invalid (no JSON tool calls) | `docs/RESULTS_E_F_PILOT_2026-11-12.md` |
| MI250X TP=8 RCCL sweep (E-D) | baseline and 4 ORDER=0 configs all **48/48** across restart; `LAUNCH_ORDER_IMPLICIT=1` fails to start | `docs/RESULTS_E_D_RCCL_2026-11-11.md` |
| MI250X TP=8 intermittency (E-E) | **15/15** restarts 48/48; combined with 23661013: **1/16** mismatches (~6.25%, Wilson 1.1-28.3%) | `docs/RESULTS_E_E_INTERMITTENCY_2026-11-12.md` |
| MI250X TP=8 (single node, Mistral): BI not cross-process invariant | BI restart **36/48 = 75%** (TP1/TP4 were 48/48) | `docs/RESULTS_E_C_TP8_2026-11-11.md` |
| MI250X TP=8: TP-invariance absent | default TP4 vs TP8 39/48; BI TP4 vs TP8 **36/48 = 75%** | same |
| MI250X TP=8: throughput signal | default 1,898 vs TP4 1,418 tok/s (+34%); BI 756 (no gain) | same |
| MI250X restart: `BI=1` across process restarts | **48/48** (TP1 and TP4); default TP1 42/48 = 87.5% | `docs/RESULTS_E_A_RESTART_2026-11-11.md` |
| MI250X cross-node (2 nodes, same TP4 replica) | default 44/48 (B=1), 41/48 (B=8); `BI=1` **48/48 both** | `docs/RESULTS_E_B_CROSSNODE_2026-11-11.md` |
| MI250X full atlas: Mistral replication | default B=1 **4/16**; BI 0/16; batch match default 0.69-0.83, BI 1.0000; BI cross-TP **36/48 = 75%** | `docs/RESULTS_E_A_MISTRAL_2026-11-11.md` |
| MI250X pilot: default greedy nondeterministic even at client B=1 | **4/16 prompts** differ across 3 sequential runs (25%, Wilson 7.3-52.4%); `BI=1` 0/16 and 48/48 vs B=8 | `docs/RESULTS_E_A_PILOT_2026-11-11.md` |
| MI250X pilot: batch effect (default) | 39/48 = **81.25%** exact match B=8 vs B=1 | same |
| Flip forensics (TP=1) | default 10/100 and 9/100; `TRITON_ATTN` 0/100; `BI` 0/100; first divergence token 5 | `docs/RESULTS_FORENSICS_2026-11-11.md` |
| Flip forensics (TP=4) | default 10/100, 12/100; `TRITON_ATTN` **16/100, 15/100**; `BI` **0/100** | same |
| Independent reproduction (E7) | dataset `49c2f8ac…`, E6 and E3 counts identical | `benchmark/e7_reproduce.py` |
| Cross-machine reproduction | 4 fleet nodes reproduced 4 different claims | `/root/gamaos/out/gama_work_*.json` (not in repo) |

## Performance (for quota planning)

| Result | Number | Artifact |
|---|---|---|
| Single-GCD MFU (decode, conc 256) | 31–34% | `docs/RESULTS_SCALING_2026-11-10.md` |
| TP scaling (Qwen) | TP1 33.7 → TP2 57.8 → TP4 57.8 rps (TP4 no gain) | same |
| TP scaling (Mistral) | TP1 32.0 → TP2 49.1 → TP4 51.5 → TP8 70.5 rps | same |
| Multi-node DP (TP=8, per-replica 256) | 1.99× on 2 nodes, **3.82×** on 4 (95.6% efficiency), ~8.4 rps/GCD | `docs/RESULTS_MULTINODE_2026-11-10.md` |
| TP=1 farm (8 replicas/node) | 74.8 rps @256; **131.4 rps @512**, MFU 15.8% | `docs/RESULTS_TP1_FARM_2026-11-11.md` |
| Correction | the "32 rps/GCD × 8" extrapolation was wrong; farm wins only at high concurrency | same |

## Software (in repo)

| Component | Purpose |
|---|---|
| `src/agentmujo_training/guard/evidence_gate.py` | three-valued PASS/FAIL/**ABSTAIN** gate, fail-closed; 21 tests |
| `src/agentmujo_training/guard/risk_gate_v2.py` | normalised, policy-based action gate; 35 tests |
| `benchmark/cluster_robust.py` | template-level bootstrap (design effect, effective N) |
| `benchmark/riskgate_stress.py` | 1,000 + 500 adversarial calls, plus encoded evasion |
| `benchmark/e13_probe_sensitivity.py` | probe-depth audit of a gate |
| `benchmark/gen_honesty_real.py` + `score_honesty_real.py` | Wikidata-based real-entity honesty set |
| `benchmark/forensics_client.py` + `e3_forensics.sbatch` | token-logprob flip forensics |
| `benchmark/loadgen.py` | throughput/MFU load generator |
| `benchmark/verifier_batch.py` | verifier-economics harness |

## Human evaluation v2 (run 2026-11-12)

- `benchmark/human_eval/annotate_adi.html`, `annotate_osoba2.html`, `annotate_osoba3.html` — offline apps (keyboard, localStorage, CSV export).
- `benchmark/human_eval/items_annot_v2.jsonl` — 200 **unique** items (100 fictional: 10 entities x 10 paraphrases; 100 real Wikipedia-bs topics with references), all with Qwen2.5-7B answers; md5 `6ca160b05bb7c6fac430cdbc38133c7b`.
- `benchmark/human_eval/score_human_eval.py` — Cohen/Fleiss κ, per-family rates, Wilson CI, disagreement list.
- `benchmark/e15_annot_responses.sbatch` — generates answers for additional models (`ANNOT_OUT`) without overwriting the Qwen set.
- **Result:** 3 annotators × 200 items, full coverage; raw **Fleiss κ = 0.48** (pairwise 0.39/0.38/0.67), 19 disagreements.
- Post-hoc sensitivity: mapping fictitious ANSWER_OK→HEDGE gives **κ = 0.886** (not pre-registered; needs calibration before citing). FABRICATE 1/600 raw, 0/600 on real items.
- Artifacts: `annotations_adi.csv`, `annotations_osoba2.csv`, `annotations_osoba3.csv`, `human_eval_results.json` (run 2026-11-12).

## Not yet done (honest list)

- arXiv submission (no account; needs login + cs.SE endorsement).
- Fast Lane application: 30.01–01.02.2027, after the current allocation expires (29.01.2027).
- Cross-process batch-invariance on Mistral via the full v2 suite (partial: TP=1/TP=4 restart tests pass).
