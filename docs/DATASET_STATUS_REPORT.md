# DATASET_STATUS_REPORT — v0.4.0

**Datum:** 2026-10-31 · **Repo:** gamai-io/agentmujo-training · **HF:** https://huggingface.co/datasets/renatoschust/agentmujo-dataset · **Testovi:** 51/51

## Release v0.4.0

- **Trening:** 4.496 redova, 10 datasetova, 13 kategorija, **gapovi 0**.
- bosnian-language 1.178 · safety 60 · reasoning 75 · function-calling 1.374 · **synthetic-tool-use 500** · agentic-tasks 739 · knowledge 200 · coding 100 · RAG 100 · preference-dpo 170.
- Cross-dataset dedup: 25 uklonjeno.
- **Benchmark:** 50 held-out zadataka (10 × 5), nije trening.
- **Eval rezultati (tool-selection, Aitta/LUMI AI Factory):**
  - `Qwen/Qwen3.6-35B-A3B` — **25/50 (50%)**
  - `openai/gpt-oss-120b` — **28/50 (56%)**
  - fajlovi: `benchmarks/results/aitta_*_v0.1.json`.

## Sintetički tool-use (v0.4)

- 500 uzoraka, 6 fokusa: sql 100, tool-selection 180, argument-generation 80, multi-step 60, verification 40, data 40.
- **Deterministički šabloni + schema validacija**, ne LLM halucinacija; `verification_status=schema-validated`, `license=Apache-2.0`.
- Nije trenirano na benchmarku; benchmark ostaje held-out.

## Izvori i licence

- `wikipedia-bs` = approved, CC BY-SA 4.0 (knowledge 200 + RAG 100).
- `own` = approved; coding 100 (Apache-2.0), safety/internal, synthetic (Apache-2.0), benchmark (Apache-2.0).
- HF/OSCAR/CulturaX/OPUS/Wikimedia(generic)/BigCode/BFCL = pending; nisu korišteni bez provjere.

## GPU / LUMI

- Eval je rađen preko **Aitta (LUMI AI Factory)** API-ja; nije korišten GPU za trening.
- LUMI ostaje za CPU/Slurm streaming i opravdanu sintetičku generaciju/eval/trening.
