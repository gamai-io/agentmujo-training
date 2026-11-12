# E-A restart — cross-process reproducibilnost (job 23660473, 11.11.2026)

**Postavka:** Qwen2.5-7B, greedy, 16 promptova × 3 reps, B=1; dva odvojena vLLM procesa
(restart) po armu; drugi run poređen sa prvim. Trajanje 13 min, 4 GCD.
**Dokaz:** `results/eA-restart-2026-11-11/` + SHA256SUMS.

| Arm | Varijacija unutar runa | Poklapanje poslije restarta |
|---|---|---|
| BI=1, TP=1 | 0/16 | **48/48 = 100%** |
| BI=1, TP=4 | 0/16 | **48/48 = 100%** |
| default, TP=1 (kontrola) | 3/16 | **42/48 = 87,5%** |

Zaključak: `VLLM_BATCH_INVARIANT=1` daje bit-identične izlaze **i kroz restart procesa**
na oba TP; default ne (6/48 razlika između dva procesa). Ovo je jače od ranijeg nalaza
„700/700 kroz restarte" jer koristi fiksni prompt set i eksplicitnu referencu.
