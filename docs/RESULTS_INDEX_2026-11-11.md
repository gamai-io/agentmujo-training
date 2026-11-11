# Results index — what has been measured (updated 2026-11-11)

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
| E3 injection, in-sample | V1 33.0%/35.0% · V2 90.1%/2.5% (detection/FP) | `docs/RESULTS_E3_2026-11-10.md` |
| E3 out-of-distribution (independent generator) | **46.8%** detection, 6/48 false blocks | `docs/RESULTS_E3_OOS_2026-11-10.md` |
| Invoice gate (E6) | recall 1,109/1,109 = 100%, FP 0/391 | `benchmark/e6_check.json` |
| Probe sensitivity (E13) | same data: 0% / 30.2% / 47.8% / 49.1% / **100%** recall by probe depth | `docs/RESULTS_E13_2026-11-11.md` |
| RiskGate v1 vs v2 (1,000 attacks / 500 benign) | 52.6% → **100%**, 0/500 false blocks | `docs/RESULTS_RISKGATE_STRESS_2026-11-10.md` |
| Encoded (white-box) evasion | v2 100% only via fail-closed; with `terminal` allowlisted 45/56 (11 bypasses) | same |
| Verifier economics (E12) | no-evidence: 1.4% (self) / 0% (cross); with reference: 98.6% but 44% false alarms; Mistral approves 177 while 18 correct | `docs/RESULTS_E12_2026-11-11.md` |
| Attribution error (E14) | system self-heals: Qwen claims credit **75%**, Phi **87%** (94–100% correct when causal); Mistral abstains 73% | `docs/RESULTS_E14_2026-11-11.md` |

## Reproducibility / determinism

| Result | Number | Artifact |
|---|---|---|
| Serial decoding is not bit-identical | 660/700 (TP=4), 669/700 (TP=1) | `docs/RESULTS_E2_2026-11-10.md` |
| `VLLM_BATCH_INVARIANT=1` | within process **700/700** (TP=1 and TP=4); across independent restarts **700/700** in three repeated tests (earlier 586/700 did not reproduce; see correction) | `docs/RESULTS_BATCHINVARIANT_2026-11-10.md` |
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

## Not yet done (honest list)

- E10 adaptive adversary loop (beyond the encoded-payload family).
- E14 attribution error (self-healing environments).
- Human evaluation (kit prepared in `benchmark/human_eval/`, not run).
- arXiv submission (no account; needs login).
- Fast Lane application: 30.01–01.02.2027, after the current allocation expires (29.01.2027).
