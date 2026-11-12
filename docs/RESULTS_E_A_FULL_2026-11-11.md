# E-A full — MI250X determinizam atlas (job 23658816, 11.11.2026)

**Pre-registracija:** `PREREG_E_A_2026-11-11.md` (sha256 `dea58fd4…`).
**Postavka:** Qwen2.5-7B-Instruct, greedy (`temperature=0`, `seed=42`), max 128 tokena,
16 fiksnih promptova × 3 ponavljanja; **TP ∈ {1,4}**; **B ∈ {1,2,8,32}**;
armovi: `default`, `VLLM_BATCH_INVARIANT=1` (BI), `TRITON_ATTN`, `BI+TRITON`.
vLLM 0.26.0+lumi_aif_gfx90a, ROCm 7.2, LUMI-G MI250X. Trajanje 18 min, 4 GCD.
**Dokaz:** `results/eA-full-2026-11-11/` (32 summary + 8 B=1 JSONL + SHA256SUMS).

## 1. Varijacija kroz 3 ponavljanja (B=1, isti prompt)

| Arm | TP=1 | TP=4 |
|---|---|---|
| default | **3/16** (18,8%, Wilson 6,6–43,0%) | **3/16** |
| BI=1 | **0/16** | **0/16** |
| TRITON_ATTN | **3/16** | **2/16** |
| BI+TRITON | **0/16** | **0/16** |

Default greedy nije deterministički ni pri strogo sekvencijalnim zahtjevima.
BI uklanja varijaciju unutar procesa na oba TP.

## 2. Batch efekat (B>1 vs B=1, 48 zahtjeva)

| Arm | TP=1 B=2/8/32 | TP=4 B=2/8/32 |
|---|---|---|
| default | 0,8542 / 0,8333 / 0,8542 | 0,8125 / 0,8333 / 0,8125 |
| BI=1 | **1,0000 / 1,0000 / 1,0000** | **1,0000 / 1,0000 / 1,0000** |
| TRITON_ATTN | 0,8542 / 0,8125 / 0,8750 | 0,8750 / 0,8125 / 0,8333 |
| BI+TRITON | **1,0000 / 1,0000 / 1,0000** | **1,0000 / 1,0000 / 1,0000** |

Default: 9/48 = 18,8% razlika (Wilson 10,2–31,9%). BI: 0/48 na svim ćelijama.

## 3. Cross-TP (B=1, 48 zahtjeva)

- `BI` TP1 vs TP4: **39/48 = 81,25%** — **BI nije TP-invariantan** (H3 potvrđen).
- `default` TP1 vs TP4: 40/48 = 83,3%.
- `BI` TP1 == `BI+TRITON` TP1: **48/48** (TRITON ne mijenja izlaz kad je BI uključen).
- `default` TP1 == `TRITON` TP1: **48/48** — na ovom workloadu TRITON_ATTN daje iste izlaze
  kao default, ali **ne uklanja** run-to-run varijaciju (H4 **nije** potvrđen).

## 4. Interpretacija

1. **Run-to-run nedeterminizam na MI250X je realan i bez batcha** (3/16 promptova), što se
   ne vidi u jednom pokretanju. Svaki eval koji prijavljuje jedan run ima neizmjeren šum.
2. **BI je neophodan i dovoljan za batch/order invarijantu unutar TP** na ovom buildu.
3. **TP-invarijansa je odvojen problem** — potvrđeno na AMD hardveru, kao i na NVIDIA
   (arXiv 2511.17826). Za TP=4 bez TP-invarijante, BI ne pomaže cross-TP.
4. **TRITON_ATTN nije univerzalni fix** — ranija forenzika (0/100 na TP1) nije reprodukovana
   na ovom prompt setu; razlika je workload-zavisna. Ovo je nalaz, ne greška.

## 5. Ograničenja
- Jedan model (7B), 16 promptova, 3 reps, 128 tokena, jedan čvor.
- Nije mjeren restart (cross-process) u ovom jobu; pilot ima 3 reps u jednom procesu.
- „3/16" ima širok CI (6,6–43,0%); stopa nije populacijska.
- Cross-TP 39/48 miješa numeričke razlike s razlikama u tokenizaciji/dužini.

## 6. Sljedeće
- Replikacija na Mistral-7B (1 čvor, ~20 min).
- Restart test (cross-process) za BI TP1/TP4.
- E-B multi-node RCCL (2–4 čvora, standard-g) — odvojen job.
