# E-C — TP=8 na jednom čvoru (job 23661013, 11.11.2026)

**Pre-registracija:** `PREREG_E_C_TP8_2026-11-11.md` + Amendman 1 (Qwen 28 glava → TP8
nije djeljiv; prebačeno na Mistral-7B, 32 glave). Trajanje 12 min, **8 GCD (pun čvor)**.
**Dokaz:** `results/eC-tp8-2026-11-11/` + SHA256SUMS.

## 1. Izvodljivost
- Qwen2.5-7B: **TP=8 odbijen prije serviranja** —
  „Total number of attention heads (28) must be divisible by tensor parallel size (8)".
- Mistral-7B-Instruct-v0.3 (32 glave): TP=8 radi na jednom čvoru (8 GCD, 512 GB HBM).

## 2. Varijacija i batch (Mistral, B=1 referenca)

| Arm | Varijacija B=1 | B=2 | B=8 | B=32 |
|---|---|---|---|---|
| default | **1/16** | 0,8542 | 0,8333 | 0,7708 |
| BI=1 | **0/16** | **1,0000** | **1,0000** | **1,0000** |

Default batch nepodudaranje do **22,9%** (B=32). BI uklanja batch efekat i unutar TP=8.

## 3. Restart na TP=8 — BI **nije** cross-process deterministički
- BI run1: 0/16 varijacija; run2 poslije restarta: 0/16 varijacija,
  ali **36/48 = 75,0%** poklapanja sa run1.
- Na TP=1 i TP=4 isto je bilo **48/48 = 100%**.
- Zaključak: na TP=8 se između procesa mijenja nešto što BI ne pokriva
  (najvjerovatnije RCCL/kolektivna redukcija ili izbor kernela pri startu).
  Ovo je novi negativan nalaz; ne tvrdi se uzrok bez daljeg testa.

## 4. TP-invarijanta (B=1, Mistral)
| Poređenje | Poklapanje |
|---|---|
| default TP4 vs TP8 | 39/48 = 81,25% |
| BI TP4 vs TP8 | **36/48 = 75,0%** |

TP=8 nije izlazno ekvivalentan TP=4; BI ne uspostavlja TP-invarijantu (isto kao TP1 vs TP4).

## 5. Throughput (indikativno: 48 zahtjeva, B=32, jedan run)
| Arm | tok/s |
|---|---|
| default TP4 | 1.418 |
| **default TP8** | **1.898** (+34%) |
| BI TP4 | 769 |
| BI TP8 | 756 |

TP=8 donosi ~34% na default putu, ali BI košta ~50% i na TP=8 nema dobiti.
Ovo nije benchmark protoka (jedan batch, kratki izlazi); koristiti samo kao signal.

## 6. Ograničenja
Jedan model, 16 promptova × 3 reps, 48 zahtjeva po ćeliji, jedan seed, jedan čvor.
Uzrok TP8 restart razlike nije izolovan (RCCL ALGO/PROTO sweep je sljedeći korak).
