# E-A pilot — MI250X determinizam (job 23658572, 11.11.2026)

**Pre-registracija:** `PREREG_E_A_2026-11-11.md` (sha256 `dea58fd4…`).
**Postavka:** Qwen2.5-7B-Instruct, greedy (`temperature=0`, `seed=42`), max 128 tokena,
16 fiksnih promptova × 3 ponavljanja; TP=1; vLLM 0.26.0+lumi_aif_gfx90a, ROCm 7.2;
klijent B=1 (strogo sekvencijalno) i B=8; arm default vs `VLLM_BATCH_INVARIANT=1`.
**Dokaz:** `results/eA-pilot-2026-11-11/` (JSONL + summary + server log + SHA256SUMS).

## Rezultat 1 — default nije deterministički ni pri B=1

4/16 promptova daje **semantički različit** izlaz kroz 3 sekvencijalna greedy poziva:

| Prompt | rep0 | rep1/rep2 | Prva razlika |
|---|---|---|---|
| `arith3` | `25` | `45` | char 0 |
| `free1` | „…rezultati su poboljšane u determinističkim sistemima…" | „…rezultati determinističkih sistema pomaže…" | char 212 |
| `free2` | „…status zadatka u sistemu, poslati mu pitanje…" | „…status zadatka u upravljačkoj consoli sistema…" | char 84 |
| `free4` | „…na kojima se model primjenjuje…" | „…duž如您需要中文翻译…" | char 138 |

Nije truncation artefakt: svi `finish_reason=stop` (osim free1, gdje su oba izlaza
prekinuta na 128 tokena ali se razlikuju na char 212). **Stopa: 4/16 = 25%** (Wilson 95% CI
7,3–52,4%). Pilot, n=48 zahtjeva — ne generalizovati prije punog atlasa.

## Rezultat 2 — batch efekat pri default backendu

B=8 vs B=1 referenca: **39/48 = 81,25%** tačnih poklapanja (9/48 razlika).
`arith3` se poklopi 1/3, `free1` 1/3, `free2` 1/3.

## Rezultat 3 — `VLLM_BATCH_INVARIANT=1` uklanja oba efekta

- B=1: **0/16** promptova varira (vs 4/16 default).
- B=8 vs BI B=1: **48/48 = 100%** poklapanje.
- Server log potvrđuje `batch_invariant.py` (`matmul_persistent`) na ROCm buildu.

## Ograničenja
- Jedan model, jedan čvor, TP=1; n=3 ponavljanja; 128 tokena.
- Nije mjeren TP=4, TRITON_ATTN, B=2/32, restart; slijedi u punom E-A.
- „25% varijacije" je iz 16 promptova; interval je širok i ne tvrdi se stopa za sve zadatke.

## Sljedeće
Puni E-A: TP∈{1,4} × B∈{1,2,8,32} × arm∈{default, BI, TRITON_ATTN, BI+TRITON},
16 promptova × 3 reps; očekivano ~80 min na dev-g.
