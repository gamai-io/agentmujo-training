# Pre-registracija E-D — RCCL sweep za TP=8 restart razliku

**Datum:** 2026-11-11 · **Status:** zamrznuto prije runa · **Hash:** `PREREG_E_D_RCCL.sha256`
**Pitanje:** je li razlika od 12/48 između dva TP=8 BI procesa (job 23661013) uzrokovana
izborom RCCL kolektivne redukcije, i može li se pinningom ukloniti?

## Hipoteze
- **H1:** pinning `NCCL_ALGO`/`NCCL_PROTO` mijenja cross-restart poklapanje na TP=8.
- **H2:** barem jedna kombinacija daje **48/48** kroz restart uz BI=1.
- **H3:** `NCCL_LAUNCH_ORDER_IMPLICIT=1` mijenja rezultat (redoslijed kernela).
- **H4:** pinning ima mjerljivu cijenu u tok/s.

## Dizajn
Mistral-7B, TP=8 (8 GCD, jedan čvor), BI=1, greedy, 16 promptova × **1 rep** (48 zahtjeva)
po runu; dva odvojena procesa po konfiguraciji (run1 referenca, run2 poredi).
Konfiguracije (9): baseline (bez env) + {Ring,Tree} × {Simple,LL128} × {LAUNCH_ORDER 0,1}.
`NCCL_ALGO`, `NCCL_PROTO`, `NCCL_LAUNCH_ORDER_IMPLICIT` se postavljaju i u host i u
`SINGULARITYENV_*`. Metrika: exact match run2 vs run1 (48), varijacija unutar runa, tok/s.

## Zašto 1 rep
Cilj je cross-process poklapanje, ne unutrašnja varijacija (već izmjerena). 1 rep × 16
promptova = 48 zahtjeva je dovoljno za binarni signal; ako config pokaže 48/48, ponoviti
sa 3 reps u follow-upu.

## Artefakti
JSONL + summary po konfiguraciji/runu, env log, SHA256SUMS, `docs/RESULTS_E_D_RCCL_2026-11-11.md`.

## Rizik
RCCL može ignorisati neke vrijednosti; ako server ne digne, konfiguracija se preskače i
bilježi kao FAIL (ne kao negativan rezultat).
