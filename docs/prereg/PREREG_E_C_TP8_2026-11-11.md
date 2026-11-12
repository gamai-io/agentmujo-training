# Pre-registracija E-C — TP=8 na jednom čvoru (8 GCD)

**Datum:** 2026-11-11 · **Status:** zamrznuto prije runa · **Hash:** `PREREG_E_C_TP8.sha256`
**Ključna činjenica:** LUMI-G čvor = 4× MI250X = **8 GCD**, pa TP=8 staje na **jedan čvor**
(512 GB HBM). Ovo nije multi-node; multi-node TP=16 je odvojen test.

## Pitanje
Da li TP=8 (a) daje bit-identične izlaze kroz restart, (b) uklanja batch efekat sa BI=1,
(c) daje iste izlaze kao TP=4/TP=1 (TP-invarijansa), i (d) koliki je throughput?

## Hipoteze
- **H1:** default TP=8 nije deterministički (run-to-run varijacija > 0).
- **H2:** BI=1 TP=8 daje 48/48 kroz restart i 100% batch match.
- **H3:** BI=1 TP=8 **nije** jednak TP=4 (TP-invarijansa odsutna), kao ni TP=4 vs TP=1.
- **H4:** TP=8 nema throughput prednost nad TP=4 za 7B (kao TP=4 vs TP=2 ranije).

## Dizajn
Qwen2.5-7B, greedy, 16 promptova × 3 reps, max 128 tokena, `--max-num-seqs 64`.
TP=8, 8 GCD, čvor u dev-g. Armovi: default i BI=1; B ∈ {1,2,8,32}; + restart (run2 vs run1).
Referenca za TP-invarijantu: sačuvani TP=4 i TP=1 B=1 JSONL iz jobova 23658816/23659521.

## Metrike
exact match (SHA256) vs B=1 i vs TP=4 referenca; unique outputs; prva razlika; tokens/s ukupno
i po GCD. Nikakva tvrdnja o TP-invarijanti bez 48/48.

## Artefakti
JSONL + summary + logovi + SHA256SUMS; rezultat u `docs/RESULTS_E_C_TP8_2026-11-11.md`.

## Amendman 1 (11.11.2026 23:15 UTC, prije uspješnog GPU runa)
Prvi pokušaj sa Qwen2.5-7B je odbijen prije serviranja: **28 attention glava nije djeljivo sa 8**
(vLLM: "Total number of attention heads (28) must be divisible by tensor parallel size (8)").
Zato se E-C izvodi na **Mistral-7B-Instruct-v0.3** (32 glave → TP=8 validan).
Ovo je i nalaz o ograničenju modela, ne greška mjerenja. Qwen TP=8 nije izvediv.
Referenca za TP-invarijantu: Mistral TP=4 B=1 iz joba 23659521.
