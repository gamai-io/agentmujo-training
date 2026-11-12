# Pre-registracija E-E — intermitencija TP=8 restart razlike (5 restartova)

**Datum:** 2026-11-12 · **Status:** zamrznuto prije runa · **Hash:** `PREREG_E_E.sha256`
**Pitanje:** kolika je stopa nepodudaranja kroz restart na TP=8 sa BI=1, i smanjuje li je
pinning RCCL ALGO/PROTO? Jedan par (23661013) je dao 36/48, drugi (23662047 baseline) 48/48.

## Hipoteze
- **H1:** baseline ima >0 nepodudaranja u 5 restartova (intermitencija postoji).
- **H2:** barem jedna pinning konfiguracija ima nižu stopu od baseline (uz široke CI).
- **H3:** nepodudaranja su ograničena (nekoliko tokena), ne cijeli izlaz.

## Dizajn
Mistral-7B, TP=8, BI=1, B=1, 16 promptova × 1 rep (48 zahtjeva). Run1 = referenca;
zatim **5 restartova** po konfiguraciji; svaki se poredi sa run1.
Konfiguracije (3): baseline (auto), `NCCL_ALGO=Ring NCCL_PROTO=Simple`, `Tree/Simple`.
Ukupno 18 procesa (~45 min, 8 GCD). `LAUNCH_ORDER_IMPLICIT=1` se ne koristi (E-D: ne startuje).

## Metrike
Broj restartova sa 48/48 po konfiguraciji (0–5); stopa = mismatches/5 sa Wilson CI;
prva razlika po promptu; tok/s po runu. Nikakav zaključak o uzroku bez ponovljivog obrasca.

## Artefakti
JSONL + summary po runu, logovi, SHA256SUMS, `docs/RESULTS_E_E_INTERMITTENCY_2026-11-12.md`.
