---
language:
  - bs
license: other
task_categories:
  - text-generation
pretty_name: AgentMujo Dataset
---

# AgentMujo Dataset

Sve verzije AgentMujo dataset factoryja na jednom mjestu. Kanonski kod: https://github.com/gamai-io/agentmujo-training

| Verzija | Trening redova | Datasetovi | Kategorije | Benchmark | Gapovi |
|---|---:|---:|---:|---:|---|
| v0.1.0 | 3.536 | 5 | 9 | — | knowledge, coding, rag-memory, safety, agentic-evaluation |
| v0.2.0 | 3.716 | 9 | 12 | — | agentic-evaluation |
| v0.3.0 | 3.996 | 9 | 13 | 50 (held-out) | — |
| v0.4.0 | 4.496 | 10 | 13 | 50 (held-out) | — |

## v0.4.0

- **synthetic-tool-use 500** (schema-validated; sql/tool-selection/argument-generation/multi-step/verification/data).
- Eval (tool-selection, Aitta/LUMI): Qwen3.6-35B-A3B **25/50**, gpt-oss-120b **28/50**.
- Ostalo kao v0.3.0: safety 60, knowledge 200, coding 100, RAG 100.
- Vidi `v0.4.0/RELEASE.json` i `benchmarks/results/`.

## v0.3.0

- safety 60, knowledge 200 (bs Wikipedia, CC BY-SA 4.0), coding 100 (Apache-2.0), RAG 100, function-calling 1.374, agentic-tasks 739, bosnian 1.178, reasoning 75, preference-dpo 170.
- Held-out agentic benchmark 50 (10 kategorija × 5); nije trening.
- Manifesti i SHA256 u `v0.3.0/`, `RELEASE.json`.

## Licence

- knowledge/RAG: CC BY-SA 4.0 (Wikipedia; attribution URL u metadata).
- coding/benchmark: Apache-2.0.
- safety/preference/ostalo: interno/Apache-2.0 po evidenciji.
