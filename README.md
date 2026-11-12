# AgentMujo Training Framework

> **Dataset Factory v0.4.0** (2026-10-31): 4.496 train rows, 10 datasets, 500 synthetic tool-use, retired public eval 50 (was published; see benchmarks/RETRACTION_v0.1.md), gaps 0.
> HF: https://huggingface.co/datasets/renatoschust/agentmujo-dataset · Canonical repo: https://github.com/gamai-io/agentmujo-training

[![CI](https://github.com/gamai-io/agentmujo-training/actions/workflows/ci.yml/badge.svg)](https://github.com/gamai-io/agentmujo-training/actions)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24161031.svg)](https://doi.org/10.5281/zenodo.24161031)

## Evidence release v1.8.1 (2026-11-12)

Zenodo DOI **[10.5281/zenodo.24161031](https://doi.org/10.5281/zenodo.24161031)**
(concept `10.5281/zenodo.24118912`) · GitHub release v1.8.1.

Contents: 700-item verifiable benchmark (dataset `sha256 49c2f8ac…`, regenerates
bit-identically), scale runs (36,550 guard requests, 0 false successes), E6 invoice gate
(100% recall, 0/391 FP), RiskGate (119/119 destructive calls blocked, 0/108 false blocks),
E3 adaptive injection (90.1%/2.5% in-sample, 85.7%/3.5% out-of-sample — below the 95%
target), and two negative results: honesty drops under SFT (73% → 41%), and model output is
**not** bit-identical even with strictly serial decoding (40/700 and 31/700 differ).
Numbers and sources: [`docs/SUMMARY_v1.5_2026-11-10.md`](docs/SUMMARY_v1.5_2026-11-10.md).

## Measured results (index)

Full table with artifacts: [`docs/RESULTS_INDEX_2026-11-11.md`](docs/RESULTS_INDEX_2026-11-11.md).

- **False success at scale:** 36,550 guard requests, 0 false successes; the guard's failure mode is text-level generalization, not throughput.
- **Text guards do not generalize:** 90.1% detection in-sample → **46.8%** on an independently written attack set (German 0/36).
- **Action gates do, if they are policies:** exact tool-name matching caught 52.6% of 1,000 attacks; a normalized, fail-closed gate caught **100%** with 0/500 false blocks — but encoded payloads bypass it at **19.6%** once the shell tool is allowlisted.
- **Gates are only as good as their probes:** the same 500 invoices yield **0% → 100%** recall depending on probe depth.
- **Honesty is prompt-bound:** 71–95% fabrication on real obscure entities when the prompt demands a number, 11–22% when refusal is allowed; models hedge 73–81% on *fictional* entities but **0/1000** on real obscure ones.
- **Model-side verification fails:** 0–1.4% detection without evidence; with a reference, 44–72% false accusations (Qwen) or near-total approval (Mistral).
- **Determinism:** not bit-identical even serially (660/700); `VLLM_BATCH_INVARIANT=1` gives 700/700 within a process **and across restarts** (TP=1 and TP=4); on TP=1 the cause is the attention backend (`TRITON_ATTN` fixes it), on TP=4 only batch-invariant mode holds.
- **Quota planning:** 1.99× on 2 nodes, 3.82× on 4 at constant per-replica concurrency; single-GCD MFU 31–34%; TP=1 farms win only at high concurrency.

## Status and evidence (English)

- Development results with denominators and Wilson intervals: [`benchmarks/results/lumi-mujo-2026-11-06-devset.json`](benchmarks/results/lumi-mujo-2026-11-06-devset.json)
- Evaluation method and exact scoring rules: [`benchmark/EVAL_METHOD.md`](benchmark/EVAL_METHOD.md)
- Correction of an earlier adapter-attribution error: [`docs/CORRECTION-2026-11-06.md`](docs/CORRECTION-2026-11-06.md)
- LUMI-G grounding and tool-calling benchmark: [gamai-evals/docs/LUMI_BENCHMARK_2026-11-06.md](https://github.com/gamai-io/gamai-evals/blob/main/docs/LUMI_BENCHMARK_2026-11-06.md)

**What this does not prove:** the evaluation sets are development sets (63 / 86 / 50 items) whose wording overlaps training templates; the newest set is not an independent holdout. `tool_ok` is a matching heuristic, not proof that a tool executed. Argument scores are string comparisons, not semantic or SQL equivalence. No field rate, production-readiness, or safety guarantee is claimed.

Reproducibilan sistem za fine-tuning **malih bosanskojezičnih modela**
koji znaju koristiti alate, raditi višekoračne zadatke i provjeravati
rezultate — jezgra AgentMujo AI agenta.

> Status: **v0.5 live (joint-23 Q8, gate 6W-2T nad v0.4).**
> Dataseti: 2911 uzoraka (FC 1252 + AG 541 + BC 1118 + thinking 45).
> Trening pauziran nakon 30 joint runova (eval 1.067→0.873);
> Svi testovi zeleni (51/51); think-profil ostaje v0.4.

## Razumijevanje za 5 minuta

1. **Baza:** `alphaedge-ai/Qwen3.5-2B-bos-32768` (Apache-2.0, 1.77B, vokabular
   32k, nativni kontekst 262k). Bosanska adaptacija je gotova — ne trenirati
   jezik od nule dok benchmark ne pokaže potrebu.
2. **Thinking/non-thinking = JEDAN model.** `enable_thinking` zastavica chat
   templatea prebacuje režim; 4 deployment profila dijele iste težine.
3. **Alati:** `configs/tools.yaml` je Single Source of Truth (14 definicija alata:
   `service_*`, `disk/memory/cpu`, `process_list`, `network_status`,
   `port_check`, `package_*`, `file_*`, `terminal` kao fallback). Model MORA preferirati
   high-level alat nad sirovom terminal komandom.
4. **Sigurnost:** `MODEL → TOOL → POLICY ENGINE → LINUX`. Fine-tuning nije
   zaštita; `allow / confirmation_required / deny` odlučuje izvršavanje.
5. **Linija:** baza → Function-Calling SFT → Agentic SFT → Bench →
   najbolji adapter → Q8 → 4 profila.

## Brzi start

```bash
uv pip install -e ".[dev]"   # ili: pip install -e .
amj doctor                    # provjera okruženja (bez ispisa tajni)
amj model list                # pinovane revizije baze
amj tools validate            # 10 registrovanih alata (registry)
amj dataset validate --input datasets/canonical/function_calling_v0.1.jsonl
amj dataset validate --input datasets/canonical/agentic_terminal_v0.1.jsonl
amj benchmark run --cases benchmark/cases_v0.5.jsonl
amj registry build           # lineage + eval tablice u docs/REGISTRY.md
pytest -q                     # 51 testova
```

## Struktura

- `configs/` — project, models (pinovane revizije), datasets, tools, training
- `src/agentmujo_training/` — cli (`amj`), tools, datasets, benchmark,
  context, registry, policy (Policy Engine + Executor), training/, evaluation/
- `schemas/` — dataset, tool, experiment, model JSON Scheme
- `datasets/canonical/` — 1252 function-calling + 541 agentic-terminal +
  1118 bosnian-core + 45 thinking + DPO parovi; sirovi podaci na HF Hubu
- `datasets/splits/` — zamrznuti train/valid/test + leakage_report.json
- `benchmark/` — AgentMujo-Bench (16 kategorija, 48 slučajeva v0.5) + agent_eval.py + format-probe + bosanska proba
- `quantization/` — GGUF Q8 pipeline (convert --no-mtp + block_count patch protokol)
- `workers/kaggle/` — T4 worker (SFT + DPO + smoke), notebook generator, 40 jobova
- `deployment/` — Ollama Modelfile profili (thinking/non-thinking, zajednički GGUF)
- `docs/` — PROJECT_SPEC, TEST_PLAN, HF_PUBLISHING
- `tests/` — registry, validator (+safety), benchmark

## Pravila

- Bez tajni u gitu (`hf auth login`, env/credential storage).
- GPU runovi samo uz eksplicitno odobrenje (kvota!) i pinovane revizije.
- Kvalitet > količina: GOLD/SILVER/BRONZE/REJECT, bez leakagea train/test.
- Uske alignment nastavke ne objavljivati bez joint provjere (osciliraju).

Detalji: `docs/PROJECT_SPEC.md` · Test gate: `docs/TEST_PLAN.md` ·
Sigurnost: `SECURITY.md` · Publish: `docs/HF_PUBLISHING.md`

## Objavljeno na Hugging Face Hubu

- Dataseti: function-calling (1252) · agentic-terminal (541) ·
  bosnian-core (1118) · thinking (45) · dpo-01 (140 parova) ·
  joint-01 (mixevi) · svi pod `shaban2024/agentmujo-*`
- Modeli: [Q8 v0.5](https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Q8-NonThinking)
  (joint-23, gate 6W-2T; v0.4 backup) · think-profil ostaje v0.4 ·
  [Non-Thinking full v0.1](https://huggingface.co/shaban2024/Qwen3.5-2B-BOS-Non-Thinking)
