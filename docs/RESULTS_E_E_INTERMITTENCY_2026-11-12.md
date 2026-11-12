# E-E — intermitencija TP=8 restart razlike (job 23671823, 12.11.2026)

**Pre-registracija:** `PREREG_E_E_INTERMITTENCY_2026-11-12.md`. Mistral-7B, TP=8, BI=1,
B=1, 16 promptova × 1 rep (48 zahtjeva); run1 referenca + **5 restartova** po konfiguraciji.
3 konfiguracije × 6 procesa = 18. Trajanje 31 min, 8 GCD. **Dokaz:** `results/eE-intermittency-2026-11-12/`.

## Rezultati

| Konfiguracija | Restartovi sa 48/48 | Neuspjeli restartovi |
|---|---|---|
| baseline (auto) | **5/5** | 0 |
| Ring / Simple | **5/5** | 0 |
| Tree / Simple | **5/5** | 0 |

Svi restartovi: 0/16 varijacija unutar runa, 48/48 vs run1.

## Interpretacija
- U kontrolisanom nizu **15/15 restartova je bit-identično**; raniji 36/48 (job 23661013)
  nije reproduciran. Spojeno: **1 nepodudaranje u 16 restartova** (~6,25%, Wilson 1,1–28,3%).
- **Pinning ALGO/PROTO nije mogao biti razlučen** jer baseline nije griješio; nema dokaza
  da pinning pomaže ili odmаже.
- Zaključak: TP8 restart razlika je **rijedak, intermitentan događaj**, ne sistematska
  posljedica RCCL izbora. Za stopu treba više restartova (n≥50) ili hvatanje stanja kad se desi.

## Ograničenja
15 restartova, jedan model, jedan čvor (nid005011), 48 zahtjeva; ne mjeri multi-node TP=16.
