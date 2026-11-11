# bal7 — doza-odgovor SFT-a: 2 vs 4 epohe (11.11.2026)

**Pitanje:** pošto je bal6 (2 epohe na 800 uzoraka) pogoršao „honesty" na fiktivnim
entitetima (73% → 41%), da li **duplo više treninga pogoršava dalje**?

## Postavka

- Isti podaci i pipeline kao bal6, samo **4 epohe** (job `23641061`, 54:59, adapter 461 MB).
- Evaluacija (job `23646596`): bench v2 (700) + honesty_real (500 stvarnih opskurnih entiteta).
- Baza za poređenje: **bal6** (2 epohe) — bench v2 od ranije + honesty_real pušten sada
  (job `23649992`) da poređenje bude na istom testu.

## Rezultat

| metrika | base (bez SFT) | bal6 (2 epohe) | **bal7 (4 epohe)** |
|---|---|---|---|
| bench v2 ukupno | 60,6% | 63,4% | **63,4%** |
| b1 aritmetika | 17,3% | 38,0% | **38,3%** |
| b4 honesty (fiktivni, „hedge" tačno) | 73–81% | 41% | **41%** |
| b5 tool-JSON | 100% | 95,0% | **94,5%** |
| honesty_real: fabrikacija | **94,8%** | **82,8%** | **83,0%** |
| honesty_real: tačnih odgovora | 26/500 | 86/500 | 85/500 |

## Nalazi

1. **Plato, ne monotono pogoršanje.** 2 → 4 epohe: bench isti (63,4%), b4 isti (41/100),
   honesty_real 82,8% → 83,0% (Δ 0,2 pp). Više SFT-a **ne** kvari dalje.
2. **Reinterpretacija ranije tvrdnje.** „SFT pogoršava honesty" mjereno je **samo na
   fiktivnim entitetima** (b4: hedge 73% → 41%). Na **stvarnim** opskurnim entitetima SFT
   je **poboljšao** tačnost: 26 → 86 tačnih od 500, fabrikacija 94,8% → 82,8%.
3. **Šta se stvarno naučilo:** model je pomjeren ka **kratkom konkretnom odgovoru**. To na
   stvarnim entitetima daje više tačnih odgovora, a na fiktivnim daje manje odbijanja.
   Dakle „honesty" na fiktivnim stavkama miješa **stil odbijanja** sa **istinitošću**.
4. **Za rad:** tvrdnju treba formulisati kao „SFT mijenja kalibraciju odbijanja; na
   fiktivnim entitetima smanjuje hedge (73→41%), na stvarnim povećava tačnost
   (26→86/500), a fabrikacija ostaje visoka (83%)". To je preciznije i odbrambeno.

## Ograničenja

- Jedan model (9B base familija), jedan dataset (800 uzoraka), jedan seed po konfiguraciji.
- honesty_real referenca je Wikidata (može biti pogrešna).
- „4 epohe" je jedina tačka poslije 2; kriva ima dvije tačke, ne četiri.

## Reprodukcija

```bash
sbatch benchmark/bal7.sbatch          # 4 epohe
sbatch benchmark/bal7_v2.sbatch       # merge + bench v2 + honesty_real
sbatch benchmark/bal6_honesty_real.sbatch  # bal6 baseline na istom testu
```

Artefakti: LUMI `out/v2_bal7_23646596.summary.json`, `out/honesty_real_bal7_23646596.json`,
`out/honesty_real_bal6_23649992.json`.
