# Archive split — reference audit and decisions (2026-11-26)

The premise "`benchmark/` and `results/` are just archival logs" was **half true**.
`results/` is pure run output, but `benchmark/` is a mixed directory: it holds the
AgentMujo-Bench case sets, the eval/reproducer scripts that tests import, *and* the run
dumps. Only the dumps were moved. Everything the suite or the release manifest reads
stayed, and the suite is green before and after the move.

- Base commit: `159482c7c2ebf5e2b1edb439cb92fc7cbb94780e`
- Moved: 213 files / 8,064,202 B (7.69 MiB) → release tag `archive-2026-11-26`
- Kept: everything else, including 79 `benchmark/results_*.json` dumps that are *not*
  archival — `registry/index.py` reads them.
- Tarball hashes and restore steps: [`archive/ARCHIVE.md`](../archive/ARCHIVE.md)

## Classification rules

- **(A) load-bearing** — read by a test, the CLI default, `registry/index.py`, a
  committed generator script, or it is the small evidence JSON that a doc's number
  points at. **Stays in git.** Moving one of these would either fail a test or silently
  change a committed, generated artifact.
- **(B) citation only** — the doc names it so a human can open the log, but no code
  path opens it, and re-running the claim regenerates it from the `.py`/`.sbatch` pair
  that stays. **Moved to the release asset**, with a one-line note in the citing doc.

## Reference table

`Refs` is the number of citing files; the commands behind it are in the last section.

| Target | Refs | Cited from | Class | Action |
|---|---|---|---|---|
| `benchmark/EVAL_METHOD.md` | 1 | `README.md` | **A** — metod/protokol/alat za anotaciju — dio proizvoda | kept |
| `benchmark/bal6_honesty_real.sbatch` | 1 | `docs/RESULTS_BAL7_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/bal7.sbatch` | 1 | `docs/RESULTS_BAL7_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/bal7_v2.sbatch` | 1 | `docs/RESULTS_BAL7_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/batchinvariant_2026-11-10.json` | 1 | `docs/RESULTS_BATCHINVARIANT_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/bosnian_probe.py` | 1 | `docs/BOSNIAN_PROBE.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/cases_v0.3.jsonl` | 1 | `scripts/training/evaluate.sh` | **A** — čita `tests/test_benchmark.py`/`test_bench_v06.py` + CLI default `--cases` | kept |
| `benchmark/cases_v0.4.jsonl` | 1 | `docs/TEST_PLAN.md` | **A** — čita `tests/test_benchmark.py`/`test_bench_v06.py` + CLI default `--cases` | kept |
| `benchmark/cases_v0.5.jsonl` | 4 | `README.md`, `benchmarks/README.md`, `benchmarks/RETRACTION_v0.1.md` +1 | **A** — čita `tests/test_benchmark.py`/`test_bench_v06.py` + CLI default `--cases` | kept |
| `benchmark/cases_v0.6.jsonl` | 1 | `docs/PROJECT_SPEC.md` | **A** — čita `tests/test_benchmark.py`/`test_bench_v06.py` + CLI default `--cases` | kept |
| `benchmark/cluster_robust.py` | 3 | `docs/PREPRINT_v0.3_2026-11-10.md`, `docs/RESULTS_INDEX_2026-11-11.md`, `docs/RESULTS_STATS_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/cluster_stats_2026-11-10.json` | 2 | `docs/PREPRINT_v0.3_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/crossfamily_2026-11-10.json` | 1 | `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e10_adversary.json` | 1 | `docs/RESULTS_E10_2026-11-11.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e10_adversary.py` | 1 | `docs/RESULTS_E10_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e10_adversary_2026-11-11.json` | 1 | `docs/RESULTS_E10_2026-11-11.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e12_verifier.sbatch` | 1 | `docs/RESULTS_E12_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e13_probe_sensitivity.json` | 2 | `docs/RESULTS_E13_2026-11-11.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e13_probe_sensitivity.py` | 2 | `docs/RESULTS_E13_2026-11-11.md`, `docs/RESULTS_INDEX_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e15_annot_responses.sbatch` | 1 | `docs/RESULTS_INDEX_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e2_batchinvariant.sbatch` | 1 | `docs/RESULTS_BATCHINVARIANT_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e2_crossfamily.sbatch` | 1 | `docs/RESULTS_CROSSFAM_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e2_determinism.sbatch` | 1 | `docs/RESULTS_E2_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e2_determinism_2026-11-10.json` | 2 | `docs/RESULTS_E2_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e3_guard_v2.py` | 1 | `docs/RESULTS_E3_2026-11-10.md` | **A** — importa `tests/test_e3_guard.py` | kept |
| `benchmark/e3_injection.py` | 1 | `docs/RESULTS_E3_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e3_oos.py` | 1 | `docs/RESULTS_E3_OOS_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e3_v2_oos_2026-11-10.json` | 2 | `docs/RESULTS_E3_OOS_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e4_honesty_real.sbatch` | 1 | `docs/RESULTS_HONESTY_REAL_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e5_multinode.sbatch` | 1 | `docs/RESULTS_MULTINODE_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e5_scaling.sbatch` | 1 | `docs/RESULTS_SCALING_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e5_tp1_farm.sbatch` | 1 | `docs/RESULTS_TP1_FARM_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/e6_check.json` | 3 | `docs/RESULTS_E6_2026-11-09.md`, `docs/RESULTS_INDEX_2026-11-11.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e6_gate.py` | 1 | `docs/RESULTS_E6_2026-11-09.md` | **A** — importa `tests/test_e6_gate.py` | kept |
| `benchmark/e6_invoices.jsonl` | 1 | `docs/RESULTS_E13_2026-11-11.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/e7_reproduce.py` | 2 | `docs/RESULTS_INDEX_2026-11-11.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/eF_agent_v2.py` | 2 | `docs/RESULTS_E_F_V2_2026-11-12.md`, `docs/RESULTS_E_F_V3_2026-11-12.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/eval_text3.py` | 1 | `docs/CORRECTION-2026-11-06.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/forensics_2026-11-11.json` | 2 | `docs/RESULTS_FORENSICS_2026-11-11.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/forensics_client.py` | 1 | `docs/RESULTS_INDEX_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/gen_bal6.py` | 1 | `docs/HOLDOUT_OVERLAP_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/gen_e14_attribution.py` | 1 | `docs/RESULTS_E14_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/gen_honesty_real.py` | 2 | `docs/RESULTS_HONESTY_REAL_2026-11-10.md`, `docs/RESULTS_INDEX_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/holdout_overlap.py` | 1 | `docs/HOLDOUT_OVERLAP_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/honesty_real_2026-11-10.json` | 2 | `docs/RESULTS_HONESTY_REAL_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/human_eval/` | 2 | `docs/PREPRINT_v0.3_2026-11-10.md`, `docs/RESULTS_INDEX_2026-11-11.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/items_e14.jsonl` | 1 | `docs/RESULTS_E14_2026-11-11.md` | **A** — item set / anotacije; docs pinuju sadržaj i md5 | kept |
| `benchmark/loadgen.py` | 2 | `docs/RESULTS_INDEX_2026-11-11.md`, `docs/RESULTS_SCALING_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/multinode_2026-11-10.json` | 2 | `docs/RESULTS_MULTINODE_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/results_bosnian_probe.json` | 1 | `docs/BOSNIAN_PROBE.md` | **A** — `registry/index.py` gradi tablicu u `docs/REGISTRY.md` (53 reda) | kept |
| `benchmark/riskgate_stress.py` | 4 | `docs/RESULTS_INDEX_2026-11-11.md`, `docs/RESULTS_RISKGATE_STRESS_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` +1 | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/riskgate_stress_2026-11-10.json` | 2 | `docs/RESULTS_RISKGATE_STRESS_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/riskgate_validate.py` | 2 | `docs/RESULTS_RISKGATE_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/run_baseline.py` | 1 | `docs/QUANT_EVAL.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/scaling_2026-11-10.json` | 2 | `docs/RESULTS_SCALING_2026-11-10.md`, `docs/SUMMARY_v1.5_2026-11-10.md` | **A** — mali dokaz-JSON koji doc citira kao artefakt broja | kept |
| `benchmark/score_honesty_real.py` | 1 | `docs/RESULTS_HONESTY_REAL_2026-11-10.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/score_suite.py` | 1 | `tests/test_score_suite.py` | **A** — importa `tests/test_score_suite.py` | kept |
| `benchmark/two_step_eval.py` | 1 | `docs/PROJECT_SPEC.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `benchmark/v2_results/` | 1 | `docs/RESULTS_INDEX_2026-11-11.md` | **B** — sirovi run dump (log/JSONL) bez čitaoca u kodu; docs ga navode kao ulaz za ručni obračun | moved |
| `benchmark/verifier_batch.py` | 2 | `docs/RESULTS_E12_2026-11-11.md`, `docs/RESULTS_INDEX_2026-11-11.md` | **A** — reproducer za broj koji doc tvrdi | kept |
| `results/big-30b-2026-11-13/` | 1 | `docs/RESULTS_BIG_30B_2026-11-13.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eA-full-2026-11-11/` | 1 | `docs/RESULTS_E_A_FULL_2026-11-11.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eA-mistral-2026-11-11/` | 1 | `docs/RESULTS_E_A_MISTRAL_2026-11-11.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eA-pilot-2026-11-11/` | 1 | `docs/RESULTS_E_A_PILOT_2026-11-11.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eA-restart-2026-11-11/` | 1 | `docs/RESULTS_E_A_RESTART_2026-11-11.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eB-crossnode-2026-11-11/` | 1 | `docs/RESULTS_E_B_CROSSNODE_2026-11-11.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eC-tp8-2026-11-11/` | 1 | `docs/RESULTS_E_C_TP8_2026-11-11.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eE-intermittency-2026-11-12/` | 1 | `docs/RESULTS_E_E_INTERMITTENCY_2026-11-12.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eF-pilot-2026-11-12/` | 1 | `docs/RESULTS_E_F_PILOT_2026-11-12.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eF-v2-2026-11-12/` | 1 | `docs/RESULTS_E_F_V2_2026-11-12.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `results/eF-v3-2026-11-12/` | 1 | `docs/RESULTS_E_F_V3_2026-11-12.md` | **B** — run artefakt; nijedan test, CLI ni `RELEASE.json` ga ne čita | moved |
| `v2_results/v2_bal5_23603294.jsonl` | 1 | `docs/RESULTS_STATS_2026-11-10.md` | **B** — sirovi run dump (log/JSONL) bez čitaoca u kodu; docs ga navode kao ulaz za ručni obračun | moved |
| `v2_results/v2_bal6_23613126.jsonl` | 1 | `docs/RESULTS_STATS_2026-11-10.md` | **B** — sirovi run dump (log/JSONL) bez čitaoca u kodu; docs ga navode kao ulaz za ručni obračun | moved |
| `v2_results/v2_llama70b.jsonl` | 1 | `docs/RESULTS_STATS_2026-11-10.md` | **B** — sirovi run dump (log/JSONL) bez čitaoca u kodu; docs ga navode kao ulaz za ručni obračun | moved |
| `v2_results/v2_qwen7b.jsonl` | 1 | `docs/RESULTS_STATS_2026-11-10.md` | **A** — ulaz skripte `benchmark/human_eval/make_annot_pilot.py` | kept |

## Kept on purpose — not a size decision

| Kept | Why it could not move |
|---|---|
| `benchmark/results_*.json` (79 files, 3.19 MB) | `src/agentmujo_training/registry/index.py` globs them to render the "Benchmark izvještaji" table that is committed in `docs/REGISTRY.md` (53 rows). Moving them would make `amj registry build` quietly emit an empty table and leave a stale committed doc. This is the single largest block left in `benchmark/` and it stays. |
| `benchmark/v2_results/v2_qwen7b.jsonl` | Input of `benchmark/human_eval/make_annot_pilot.py` (hardcoded `RESP` path). |
| `benchmark/cases_v0.1–0.6.jsonl` | `tests/test_benchmark.py`, `tests/test_bench_v06.py`, CLI default `--cases benchmark/cases_v0.5.jsonl`. |
| `benchmark/{metrics,score_suite,e6_gate,e3_guard_v2,run_v2}.py` | Imported by `tests/test_metrics.py`, `test_score_suite.py`, `test_e6_gate.py`, `test_e3_guard.py`, `test_bench_v2.py`. |
| `benchmark/items_*.jsonl`, `human_eval/items_*`, `human_eval/annotations_2026-11-12/` | Item sets and human annotations; docs pin their counts and md5. |
| `benchmark/*.sbatch`, `benchmark/*.py` reproducers | They are the reproduction path; a claim without them is a dead number. |

## Verification

```bash
git show 159482c7c2ebf5e2b1edb439cb92fc7cbb94780e >/dev/null   # pre-move tree
pytest -q                                                         # 191 passed, before and after
PYTHONPATH=src python -m agentmujo_training.cli.main dataset verify --version 0.4.0
# {"ok": true, "version": "0.4.0", "files": 13, "total_rows": 4496, "mismatches": []}
```

## Reproducing this table

```bash
git grep -n -I -e 'results/' -e 'benchmark/' -e 'v2_results/' -- \
  docs/ README.md HF_README.md benchmarks/ releases/ tests/ src/ scripts/ workers/ Makefile
```

## Caveat found during verification (pre-existing, not caused by the move)

`docs/REGISTRY.md` was already out of date at the base commit: regenerating it from the
base tree yields 23 more adapter rows and 24 more benchmark rows than the committed
file. The split itself is behaviour-neutral — `build()` over the pre-move tree and over
the post-move tree produces byte-identical output (both differ from the committed
`docs/REGISTRY.md` in the same way). Refresh it separately with `amj registry build`
when the lineage table is next touched.
