# Forenzika flips na MI250X: koji backend je kriv (11.11.2026)

**Pitanje:** gdje nastaje prva razlika između dva identična prolaza — i koji je prekidač
dovoljan da je ukloni? 4 "arma", 3 ponavljanja, 100 stavki, `temperature=0`, `seed=42`,
`conc 8`, `max_tokens=64`, sa **token logprobs** (top-5).

Armovi (server se restartuje između armova):
`base` (default kerneli), `bi` (`VLLM_BATCH_INVARIANT=1`), `triton` (`--attention-backend TRITON_ATTN`), `bi_triton`.

## Rezultat (TP=1, posao 23627687)

| arm | flipovi r1↔r2 | flipovi r1↔r3 | prva divergencija (medijan) | |Δlogprob| na divergenciji |
|---|---|---|---|---|
| base | **10/100** | **9/100** | **5** tokena (max 42) | 0,41 |
| bi | **0/100** | **0/100** | — | — |
| triton | **0/100** | **0/100** | — | — |
| bi_triton | **0/100** | **0/100** | — | — |

## Nalazi

1. **Default backend se flipa i u istom procesu** — 9–10% stavki, na samo `conc 8`.
   To nije batch-composition problem (isti batch): numerika kernela.
2. **Prva razlika je rano**: medijan na **5. tokenu** (3–5), maksimum 42. Da je kriv
   split-K/dugi kontekst, očekivali bismo kasnije granice (256/512/1024). Rano pokazuje
   na prefill/attention numeriku.
3. **`TRITON_ATTN` sam uklanja flips** (0/100), kao i `BI` i kombinacija. Dakle na ovom
   stacku je dovoljno izabrati deterministički attention backend; BI flag nije jedini put.
4. **Δlogprob ≈ 0,4** na mjestu prve razlike: to nije šum zadnjeg decimala, nego dovoljno
   velika numerička razlika da promijeni token.
5. **Van procesa ostaje problem** (prethodni posao: 83,7% / 84,7% identičnih poslije
   restarta). Dakle *unutar-procesna* determinacija = backend; *cross-process* = još
   nešto u okruženju procesa (alokator/workspace/autotune).

## TP=4 (isti protokol, 100 stavki)

| arm | flipovi r1↔r2 | flipovi r1↔r3 | prva divergencija |
|---|---|---|---|
| base (posao 23627821) | 10/100 | 12/100 | — |
| triton (posao 23637250) | **16/100** | **15/100** | medijan 9. token |
| **bi** (posao 23637371) | **0/100** | **0/100** | — |

**Ključno:** `TRITON_ATTN` **ne pomaže na TP=4** (16/100 i 15/100, čak i gore od defaulta),
dok `VLLM_BATCH_INVARIANT=1` drži **0/100**. Dakle popravka backendom važi samo za TP=1;
TP all-reduce put vraća nedeterminizam, a batch-invariant mod ga pokriva.

## Ograničenja

- 100 stavki, jedan model (Qwen2.5-7B), `conc 8`.
- „Prva divergencija" je pozicija tokena, ne ULP analiza logita.
- Mjeri se samo tekstualni izlaz + logprobs, ne interni tenzori.

**Operativna lekcija:** `TRITON_ATTN` na TP=4 pokreće torch.compile / Triton autotune i
piše u `~/.cache/vllm` — prvi pokušaj je udario **home kvotu 22 GiB**
(`Disk quota exceeded`). Sa `VLLM_CACHE_ROOT` i `TRITON_CACHE_DIR` na `/scratch`, drugi
pokušaj se digao u ~1 min (keš topao).

## Reprodukcija

```bash
sbatch -p dev-g --export=ALL,ARMS='base bi triton bi_triton',TP=1 \
  /project/project_465003647/gama/e3_forensics.sbatch
```

Artefakti: LUMI `out/e2_forensics_<job>.json`, `out/fx_<arm>_r{1,2,3}_<job>.jsonl`;
sažetak u repou `benchmark/forensics_2026-11-11.json`.
