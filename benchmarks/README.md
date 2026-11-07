# AgentMujo Agentic Evaluation

> **RETRACTED (2026-11-07):** `agentic_eval_v0.1.jsonl` je bio javno objavljen, pa nije holdout. Stavke su redigovane (`withheld: true`), a sva v0.1 mjerenja su **public-set**, ne holdout. Detalji: [`RETRACTION_v0.1.md`](RETRACTION_v0.1.md). Za javno poredjenje koristi `benchmark/cases_v0.5.jsonl`.

## Sta ostaje u fajlu

`agentic_eval_v0.1.jsonl` (50 linija) sada nosi samo metapodatke:

- `id` — `amj-ev-NNNN`
- `category` — sql/files/web/office/security/multi-step/bosnian/data/tool-selection/verification (10 × 5)
- `difficulty`, `allowed_tools`, `expected_tools`, `requires_confirmation`
- `withheld: true`, `status: "retired-compromised"`, `metadata.held_out: false`

Polja `goal`, `messages`, `success_criteria` i `verification` su uklonjena i nece biti vracena u ovaj fajl.

## Zasto

Skup je objavljen 2026-10-31 uz `held_out: true`. Objavljivanje ukida holdout svojstvo; mjerenja na njemu mjere public-set, ne generalizaciju. Redigovanje sprecava dalje sirenje, ali ne ponistava ranije kopije (git historija, klonovi, arhive).

## Rezultati (tool-selection, 2026-10-31, Aitta/LUMI AI Factory) — public-set

| Model | Pass | Ukupno |
| --- | --- | --- |
| openai/gpt-oss-120b | 28 | 50 |
| Qwen/Qwen3.6-35B-A3B | 25 | 50 |

Ovi brojevi su tacni za javni skup; **nisu** holdout rezultat i ne smiju se tako navoditi.

## Pravila za buduce skupove

- Holdout se ne objavljuje; u repou stoji samo manifest (ID, kategorija, broj stavki) i SHA256.
- Javni skupovi koriste `benchmark/cases_v*.jsonl` i smiju sadrzavati `prompt`.
- Nikad ne mijenjati verziju prepravkom; novi skup = novi fajl.
- Testovi (`tests/test_agentic_eval.py`, `tests/test_holdout_privacy.py`) moraju ostati zeleni prije objave.
