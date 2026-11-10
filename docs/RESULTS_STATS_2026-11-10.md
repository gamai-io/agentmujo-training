# Statistička korekcija bench v2 — klasteri (šabloni), ne stavke (10.11.2026)

**Zašto:** bench v2 ima 700 stavki, ali samo **24 šablona** (b1: 3, b2: 1, b4: 8, b5: 12).
Stavke unutar šablona nisu nezavisne, pa Wilson intervali potcjenjuju neizvjesnost.
Ovo je ponovna analiza postojećih izlaza — **0 GPU-h**, bez novih generisanja.

Metoda: `benchmark/cluster_robust.py`; klaster = šablon; klaster-bootstrap B=4.000
(resample šablona unutar bloka, sa vraćanjem); design effect (deff) = varijansa
klaster-bootstrapa / binomna varijansa; efektivni N = n / deff. Tekstovi su ponovno
skorovani trenutnim `run_v2.score_item` (ista verzija kao objavljeni brojevi).

## 1. Intervali

| model | acc | Wilson 95% (objavljeno) | **klaster 95%** | deff | **efektivni N** |
|---|---|---|---|---|---|
| Qwen2.5-7B | 60,6% | [56,9; 64,1] | **[50,2; 72,4]** | 10,03 | 69,8 |
| Llama-3.3-70B | 47,3% | [43,6; 51,0] | **[39,3; 55,2]** | 4,71 | 148,5 |
| bal6 (adapter) | 63,4% | [59,8; 66,9] | **[49,1; 81,5]** | 21,86 | 32,0 |

Intervali su **2–3× širi**; efektivni N je 32–149, ne 700. `b2_needle` ima jedan šablon,
pa se njegova klaster-varijansa **ne može procijeniti** (označeno u JSON-u).

## 2. Tačnost je određena šablonom, ne stavkom

| model | b1_sub | b1_total | b1_vat | b2_needle |
|---|---|---|---|---|
| Qwen2.5-7B | **0/114** | **0/79** | 52/107 (48,6%) | 99/100 |
| Llama-3.3-70B | 2/114 (1,8%) | 6/79 (7,6%) | 14/107 (13,1%) | 99/100 |
| bal6 | 25/114 (21,9%) | **0/79** | 89/107 (83,2%) | 99/100 |

- „17,3% aritmetike" za Qwen2.5-7B je zapravo **0% na dva od tri šablona**; sve dolazi iz
  `b1_vat`. Isto važi za bal6: njegov skok (38%) je **samo** `b1_vat` 48,6% → 83,2%,
  dok je `b1_total` i dalje 0/79.
- Zato „aritmetika 5,7–37%" u preprintu treba čitati kao: modeli uče **jedan** obrazac
  (obračun PDV-a naprijed), a ne inverz (osnovica iz bruto iznosa) ni lančano množenje.

## 3. Honesty je „sve ili ništa" po tipu entiteta

bal6 po tipu (identično ponašanje na svim stavkama unutar tipa):

| tip | bal6 | Qwen2.5-7B | Llama-70B |
|---|---|---|---|
| firma (matični broj) | **0/13** | 13/13 | 13/13 |
| kompanija (datum osnivanja) | **0/14** | 10/14 | 0/14 |
| uređaj (protokol) | **0/18** | 12/18 | 0/18 |
| utakmica (rezultat) | **0/6** | 6/6 | 6/6 |
| grad (stanovništvo) | 10/10 | 10/10 | 0/10 |
| softver (cijena licence) | 9/9 | **0/9** | 9/9 |
| funkcija (API) | 11/11 | 11/11 | 0/11 |
| država (glavni grad) | 11/19 | 11/19 | 0/19 |

Pad honesty-a kod bal6 (73% → 41%) nije „model je postao manje iskren po stavci", nego
**izgubio je hedge na tri tipa** (firma, kompanija, uređaj) koje je base imao. To je
mnogo precizniji nalaz i lakše ga je popraviti (ciljani podaci po tipu).

## 4. Jedan šablon može srušiti cijeli blok

Llama-3.3-70B: `b5_service_logs` **0/18**, dok je ostalih 11 tool šablona 182/182.
Ukupno 91% tool-JSON tačnosti je posljedica **jednog** šablona, ne „slabog tool callinga".

## 5. Posljedice za tvrdnje i prijavu

1. U rad izvještavati **klaster intervale** (ili oba), uz eksplicitno `n_clusters=24`.
2. Aritmetiku prijavljivati **po šablonu**; ukupni procenat skriva 0/114.
3. Honesty prijavljivati **po tipu entiteta**, ne samo kao sumu.
4. Za prijavu resursa: „700 zadataka" → „700 stavki / 24 šablona, efektivni N 32–149".
   Pošteno, i evaluatorima pokazuje da razumijemo ograničenje.

## 6. Reprodukcija

```bash
cd benchmark
python3 cluster_robust.py --items items_v2.jsonl --rescore \
  --results v2_results/v2_qwen7b.jsonl v2_results/v2_llama70b.jsonl \
            v2_results/v2_bal6_23613126.jsonl \
  --out cluster_stats_2026-11-10.json
```

Napomena: lokalni `v2_results/v2_bal5_23603294.jsonl` je run **prije** `NO_THINK` popravke
(b4=0, b5=0) i nije korišten; objavljeni bal5 (444/700) dolazi iz kasnijeg runa.
