# E-A replikacija — Mistral-7B (job 23659521, 11.11.2026)

**Ista pre-registracija** (`PREREG_E_A_2026-11-11.md`), isti prompt set i protokol;
model **Mistral-7B-Instruct-v0.3** (`/scratch/project_465003647/models/mistral-7b-instruct-v0.3`).
Trajanje 32 min, 4 GCD. **Dokaz:** `results/eA-mistral-2026-11-11/` + SHA256SUMS.

## 1. Varijacija kroz 3 ponavljanja (B=1)

| Arm | TP=1 | TP=4 |
|---|---|---|
| default | **4/16 = 25,0%** (Wilson 10,2–49,5%) | **4/16** |
| BI=1 | **0/16** | **0/16** |
| TRITON_ATTN | **4/16** | **4/16** |
| BI+TRITON | **0/16** | **0/16** |

## 2. Batch efekat (vs B=1, 48 zahtjeva)

| Arm | TP=1 B=2/8/32 | TP=4 B=2/8/32 |
|---|---|---|
| default | 0,7292 / 0,8125 / 0,7708 | 0,8333 / 0,6875 / 0,7917 |
| BI=1 | **1,0000 / 1,0000 / 1,0000** | **1,0000 / 1,0000 / 1,0000** |
| TRITON_ATTN | 0,7708 / 0,8125 / 0,8542 | 0,8333 / 0,6875 / 0,7917 |
| BI+TRITON | **1,0000 / 1,0000 / 1,0000** | **1,0000 / 1,0000 / 1,0000** |

Default batch nepodudaranje: do **31,25%** (TP4, B=8) — veće nego kod Qwen (18,8%).

## 3. Cross-TP i backend

- `BI` TP1 vs TP4: **36/48 = 75,0%** — BI nije TP-invariantan (potvrđeno i na Mistralu).
- `default` TP1 vs TP4: 38/48 = 79,2%.
- `default` TP1 == `TRITON` TP1: **48/48**; `default` TP4 == `TRITON` TP4: **48/48** —
  TRITON_ATTN na ovom workloadu ne mijenja izlaz i ne uklanja varijaciju.
- `BI` TP1 vs `BI+TRITON` TP1: **45/48 = 93,75%** — za razliku od Qwena (48/48),
  na Mistralu kombinacija mijenja 3/48 izlaza.

## 4. Zaključak
Replikacija potvrđuje glavne nalaze na drugoj familiji: run-to-run nedeterminizam bez
batcha, BI kao dovoljan uslov za batch/order invarijantu unutar TP, i **odsustvo
TP-invarijante**. Pokazuje i da je veličina efekta model-zavisna (Mistral veći batch efekat).

## 5. Ograničenja
16 promptova × 3 reps, 128 tokena, jedan čvor, jedan seed; stope imaju široke CI.
