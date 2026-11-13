# Qwen3-VL-30B-A3B on LUMI MI250X — Base vs LoRA v1/v2/v3 (2026-11-13)

**Setup:** `Qwen/Qwen3-VL-30B-A3B-Instruct` (31B total, 3B active), LUMI-G 1 node (8 GCD, 512 GB HBM),
vLLM TP=8, 16k context, greedy decoding (`temperature=0`). Artifacts in `results/big-30b-2026-11-13/`.

## 1. Ablation across training mixtures

- **Base (`23705237`):** unmodified `Qwen/Qwen3-VL-30B-A3B-Instruct`.
- **LoRA v1 (`23707677`):** `r=16`, `lr=1e-4`, 1,929 samples (1,629 text tool/thinking + 300 synthetic invoice images).
- **LoRA v2 (`23710233`):** `r=8`, `lr=5e-5`, 2,729 text-only samples (1,629 canonical + 800 synthetic arithmetic + 300 fictional-entity refusal/honesty; 0 images).
- **LoRA v3 (`23710970`):** continues from v2 with a 120-step multimodal micro-pass at `lr=2e-5` (50 synthetic invoice images + 40 tool-call + 15 arithmetic + 15 honesty replay samples).

| Metric | Base 30B | LoRA v1 (r=16, 1e-4, +300 img) | LoRA v2 (r=8, 5e-5, text+arith+hon) | **LoRA v3 (+120-step mm micro-pass)** |
|---|---:|---:|---:|---:|
| **Bench v2 overall (700)** | 576/700 = 82.3% | 477/700 = 68.1% | 606/700 = 86.6% | **617/700 = 88.1%** (CI 85.5–90.3%) |
| `b1_arith` (300) | **229/300 = 76.3%** | 178/300 = 59.3% | **229/300 = 76.3%** | 226/300 = **75.3%** |
| `b2_needle` (100) | **100/100 = 100%** | 99/100 = 99.0% | 99/100 = 99.0% | **99/100 = 99.0%** |
| `b4_honesty` (100) | 47/100 = 47.0% | 0/100 = 0.0% | 86/100 = 86.0% | **100/100 = 100.0%** |
| `b5_toolargs` (200) | **200/200 = 100%** | **200/200 = 100%** | 192/200 = 96.0% | **192/200 = 96.0%** |
| **Invoice supplier (20)** | 20/20 | 20/20 | 18/20 | **20/20 (100%)** |
| **Invoice number (20)** | 20/20 | 20/20 | 20/20 | **20/20 (100%)** |
| **Invoice date (20)** | 14/20 | 20/20 | 0/20 | **20/20 (100%)** |
| **Invoice total (20)** | 20/20 | 20/20 | 18/20 | **18/20 (90%)** |
| **E-F false-success (50)** | **0/50** (19 DONE) | **0/50** (20 DONE) | 9/50 (11 DONE) | **6/50 = 12%** (12 DONE, 14 probe pass) |
| Throughput (rps, 8 GCD) | 8.73 | 19.63 | 16.68 | **17.03** |

## 2. Key findings

1. **Naive multimodal SFT (v1) causes catastrophic forgetting on reasoning:** mixing 300 invoice JSON targets at `lr=1e-4` without arithmetic/refusal replay achieved 20/20 invoice extraction but dropped `b1_arith` from 76.3% to 59.3% and `b4_honesty` from 47% to 0%.
2. **Text+replay SFT (v2) recovers arithmetic and boosts honesty (+39 pp),** reaching 86.6% on Bench v2, but loses invoice date formatting (0/20).
3. **A 120-step multimodal micro-pass with replay (v3, `lr=2e-5`) resolves both:** Bench v2 reaches **617/700 = 88.1%** (`b1_arith` 75.3%, `b2_needle` 99%, `b4_honesty` 100%, `b5_toolargs` 96%) while restoring **20/20** on invoice supplier, number, and date (18/20 total).
4. **Trade-off:** on the 50-task E-F file-agent benchmark (base policy, 6 steps / 250 tokens), v3 has 6/50 (12%) false successes vs 0/50 for the base model.

## 3. Limitations

Single seed/run per checkpoint; invoices are synthetic (generic suppliers, BAM, 17% VAT); honesty training used disjoint fictional entity names (`Kaledrija`, `Vantoria`, etc.) from Bench v2 (`b4_honesty`).
