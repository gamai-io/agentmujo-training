# E-B — cross-node replica determinizam (job 23660474, 11.11.2026)

**Opseg:** dva **identična** TP=4 servera na **dva različita čvora**
(`nid007874`, `nid007890`), isti model i konfiguracija; čvor B poređen sa čvorom A.
**Nije** TP=8 preko čvorova (to je odvojen, skuplji test).
Trajanje 11 min, 2 čvora × 4 GCD. **Dokaz:** `results/eB-crossnode-2026-11-11/`.

| Arm | B=1 (48 zahtjeva) | B=8 (48 zahtjeva) |
|---|---|---|
| default | **44/48 = 91,67%** | **41/48 = 85,42%** |
| BI=1 | **48/48 = 100%** | **48/48 = 100%** |

- **Bez BI**, ista replika na drugom čvoru daje različite izlaze već pri B=1 (4/48),
  a batching povećava razliku (7/48 pri B=8).
- **Sa BI=1**, izlazi su bit-identični **preko čvorova**, u oba batch režima.
- Unutar čvora A: default 2/16 promptova varira (B=1), BI 0/16.

Zaključak: batch-invariant mod uklanja i cross-node varijaciju za fiksni TP; to je prvi
ovakav nalaz na MI250X/Slingshot u našem artefaktu. Ograničenje: 2 čvora, jedan model,
jedan seed, 16 promptova; TP=8/Ray nije mjeren.
