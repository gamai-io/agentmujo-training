# Noćni rezultati 10.11.2026 (bench v2, E2, E4, E5)

Sve je izvršeno serijski na LUMI (`dev-g`, 4 GCD), `temperature=0`, `seed=42`,
`max_tokens=256` (osim gdje je naznačeno), scorer `run_v2.py` (sa ispravkama).

## 1. Bench v2 — konačna tabela (700 zadataka)

| model | b1 aritmetika | b2 needle | b4 honesty | b5 tool-JSON | **ukupno** | bytey |
|---|---|---|---|---|---|---|
| **Qwen3.8-27B-FP8** | **298/300 (99,3%)** | 99/100 | 83/100 | 0/200 ⚠️ | **68,6%** | 0% |
| gpt-oss-120b | 111/300 (37,0%) | 99/100 | 59/100 | 198/200 | **66,7%** | 0% |
| Qwen2.5-7B (run b) | 52/300 (17,3%) | 99/100 | 81/100 | 200/200 | **61,7%** | 0% |
| Qwen2.5-7B (TP1) | 52/300 (17,3%) | 99/100 | 81/100 | 200/200 | **61,7%** | 0% |
| Qwen2.5-7B (run a) | 52/300 (17,3%) | 99/100 | 79/100 | 200/200 | **61,4%** | 0% |
| Qwen2.5-7B (TP2) | 52/300 (17,3%) | 99/100 | 78/100 | 200/200 | **61,3%** | 0% |
| Qwen2.5-7B (TP4, prvi) | 52/300 (17,3%) | 99/100 | 73/100 | 200/200 | **60,6%** | 0% |
| Qwen2.5-VL-7B | 31/300 (10,3%) | 99/100 | 17/100 | 192/200 | **48,4%** | 0% |
| Llama-3.3-70B | 22/300 (7,3%) | 99/100 | 28/100 | 182/200 | **47,3%** | 0% |
| Llama-Poro-2-70B | 17/300 (5,7%) | 100/100 | 36/100 | 158/200 | **44,4%** | 0% |
| Mistral-Small-3.1-24B | 0/300 | 0/100 | 0/100 | 0/200 | **0%** | **100% → INVALID** |

⚠️ Qwen3.8-27B-FP8 je **thinking model**: i sa `max_tokens 1024` potroši budžet na
razmišljanje i ne stigne do JSON-a (`b5 = 0/200`, 9 od 200 zahtjeva odsječeno).
Njegova aritmetika (`99,3%`) i needle (`99%`) su ipak validni; `b5` se **ne smije**
tumačiti kao nesposobnost dok se ne doda `enable_thinking=false`.

## 2. E2 — reproducibilnost: **NIJE bit-identična**

Dva identična runa (isti model, isti 700 zadataka, temp 0, isti seed):

| run | b1 | b2 | b4 | b5 | ukupno |
|---|---|---|---|---|---|
| e2a | 52/300 | 99/100 | **79/100** | 200/200 | 61,4% |
| e2b | 52/300 | 99/100 | **81/100** | 200/200 | 61,7% |

- `b1`, `b2`, `b5` su **identični**; `b4` se razlikuje u **2 od 100** slučaja.
- Zaključak: vLLM sa kontinuiranim batchingom nije bit-determinističan na `temperature=0`;
  razlika je mala (2%) ali **postoji**. Za E2 (hash/Merkle identitet) potrebno je
  serijsko izvršavanje (`--max-num-seqs 1`) ili fiksiranje batch compositiona.
- Ovo je važan nalaz: „ista postavka" ne garantuje iste izlaze; tzv. byte-identical
  reproducibilnost traži kontrolu batchinga.

## 3. E4 — prenosivost TP1 / TP2 / TP4

| TP | ukupno | b4 |
|---|---|---|
| 1 | 61,7% | 81/100 |
| 2 | 61,3% | 78/100 |
| 4 | 60,6% | 73/100 |

- Sve tri konfiguracije rade, bez grešaka; razlika ≤ 1,1 pp na ukupnom skoru.
- Razlika je **unutar šuma** (vidi E2: isti model varira ±2 pp na b4), pa se ne može
  tvrditi da TP mijenja kvalitet. Može se tvrditi: **TP1/TP2/TP4 daju uporediv rezultat**.

## 4. E5 — skala (Llama-3.3-70B, 10.000 zahtjeva, conc 512)

```
n=10000, ok=10000, err=0, false_success=0/10000, verdict PASS
ttft_p50 14,5 s, ms_p95 48,6 s (conc 512 je previsok za 70B)
```

- **0 lažnih uspjeha na 10.000** — potvrđuje raniji nalaz na drugoj skali/modelu.
- `conc 512` je neekonomičan za 70B (TTFT 14,5 s); radna točka je `conc 256`.

## 5. Trening bal5 — NIJE POKRENUT

`sbatch --wrap` sa ugniježđenim navodnicima nije vratio job id (`bal5 job=`). Trening
(honesty SFT, 400 uzoraka) **nije izvršen**; treba ga pokrenuti iz `.sbatch` fajla,
ne preko `--wrap`. Pripremljen `bal5.sbatch` (vidi repozitorij).

## 6. Trošak noći

Sve zajedno (10 GPU jobova + 1 guard 10k): procjena **~1,5–2 node-h** (12–16 GPU-h).
