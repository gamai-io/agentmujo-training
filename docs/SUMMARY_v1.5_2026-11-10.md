# GAMA Trust / AgentMujo — zbirni dokazi v1.5 (10.11.2026)

Jedno mjesto sa svim izmjerenim brojevima, izvorom i dokazom. Svaka tvrdnja ima
fajl/komandu; ništa nije „procjena" osim gdje je eksplicitno označeno.

## 1. E1 — skaliranje FSR (LUMI, guard bench, 12 šablona)

| model | N | conc | rps | TTFT p50 | ms p95 | FSR |
|---|---|---|---|---|---|---|
| Qwen2.5-7B | 5.000 | 128 | 88,2 | 67 ms | 6,3 s | 0 |
| Qwen2.5-7B | 5.000 | **256** | **114,1** | 103 ms | 9,4 s | 0 |
| Qwen2.5-7B | 5.000 | 512 | 111,6 | 3,2 s | 12,6 s | 0 |
| Qwen2.5-7B | **10.000** | 512 | 113,8 | 3,7 s | 13,4 s | **0/10.000** |
| Llama-3.3-70B | 5.000 | 128 | 22,6 | 370 ms | 21,4 s | 0 |
| Llama-3.3-70B | 5.000 | 256 | 28,7 | 582 ms | 33,5 s | 0 |
| Llama-3.3-70B | 5.000 | 512 | 28,5 | 13,2 s | 47,8 s | 0 |

Ukupno **36.550 zahtjeva, 0 grešaka, 0 lažnih uspjeha**. Dokaz: `guard_*_*.summary.json`
+ `.check.json` na LUMI-ju i u LUMI-O (`gama-artifacts/night_20261110/out/`).
Poznata ispravka: prvobitni „1/10.000" bio je lažni pozitiv mjerila (`2026` iz `VP2026`
kao broj kupaca) — popravljeno, sada 0/10.000.

## 2. E2 — reproducibilnost: **nije bit-identična ni serijski**

Prvo mjerenje (conc 64, 2 prolaza): `b1/b2/b5` identični, `b4` 79 vs 81 → 61,4% vs 61,7%.

Zatim strogi test: `--max-num-seqs 1` + klijent `--conc 1`, dva uzastopna prolaza
(700 zadataka), poslovi `23618435` (TP=4) i `23618870` (TP=1):

| TP | identičnih / 700 | stopa | b1 | b2 | b4 | b5 |
|---|---|---|---|---|---|---|
| 4 | 660 | 94,29% | 267/300 | 100/100 | 93/100 | 200/200 |
| 1 | 669 | 95,57% | 274/300 | 100/100 | 95/100 | 200/200 |

**Nalaz:** serijsko dekodiranje **ne** daje bit-identičan izlaz. Kratki ograničeni
izlazi (needle, tool-JSON) jesu 100% identični; aritmetika i slobodni tekst nisu.
TP=1 uklanja all-reduce a razlika padne samo 40 → 31, dakle krivci su i
nedeterminističke kernel redukcije/atomics na ROCm-u, ne samo tensor-paralelizam.
Dokaz: `docs/RESULTS_E2_2026-11-10.md`, `benchmark/e2_determinism_2026-11-10.json`,
LUMI `out/e2_determinism{,_tp1}.json`.

**`VLLM_BATCH_INVARIANT=1` (11.11., poslovi 23626963/23627134):** na concurrency 64
(teži uslov od E2) dva prolaza u **istom procesu su 700/700 identična** na TP=1 i TP=4.
**Ispravka (isti dan, poslovi 23639685/23639934/23640186/23640342):** cross-process je takođe
reproducibilan — 5 nezavisnih startova × 200 i × 700 stavki dalo je **svih 10 parova
identično**, a A/B/C testovi **700/700** na TP=1 i TP=4 (`sha_a = sha_b = sha_c`). Prvobitnih 586/700 se
**nije reproduciralo**; jedina razlika u okruženju bila je skoro puna home kvota. Dokaz:
`docs/RESULTS_BATCHINVARIANT_2026-11-10.md`.

**Forenzika (posao 23627687, 4 arma × 3 ponavljanja, 100 stavki, conc 8, sa logprobs):**
default backend se flipa **10/100 i 9/100** u istom procesu, prva razlika na **5. tokenu**
(medijan); `VLLM_BATCH_INVARIANT=1`, `TRITON_ATTN` i kombinacija daju **0/100**. Dakle
unutar-procesni flipovi su numerika attention backenda, ne batch. Dokaz:
`docs/RESULTS_FORENSICS_2026-11-11.md`, `benchmark/forensics_2026-11-11.json`.

## 3. E3 — adaptivni injection (203 napada + 200 kontrola)

| kapija | in-sample (seed 2027) | out-of-sample (seed 2028) |
|---|---|---|
| V1 (postojeća) | detekcija **33,0%**, FP **35,0%** | 31,0%, 26,5% |
| **V2 (nova)** | **90,1%**, FP **2,5%** | **85,7%**, FP **3,5%** |

Cilj 95% **nije postignut**; V2 generalizuje (pad 4,4 pp). Preostali promašaji:
kill 6, disk_format 5, shutdown 6, chmod 4.

**Nezavisni generator (10.11., 0 GPU-h):** 372 napada pisanih od nule (učtiv, hipotetički,
role-play, engleski, njemački, višekoračni, autoritet, urgentnost, obfuskacija, kontekst)
+ 48 benignih. GUARD_V2 hvata **46,8%** [41,8; 51,8] uz **6/48** lažnih blokada
(njemački 0/36, engleski 33,3%, obfuskacija 16,7%). Pad od 43,3 pp u odnosu na in-sample
pokazuje da tekstualna kapija ne generalizuje. Dokaz: `docs/RESULTS_E3_OOS_2026-11-10.md`,
`benchmark/e3_v2_oos_2026-11-10.json`.

## 4. E4 — ROCm prenosivost (isti model, isti zadaci)

| TP | ukupno | b4 |
|---|---|---|
| 1 | 61,7% | 81/100 |
| 2 | 61,3% | 78/100 |
| 4 | 60,6% | 73/100 |

Razlika ≤ 1,1 pp → unutar šuma (E2 pokazuje ±2 pp za isti model). Prenosivost potvrđena,
razlika u kvalitetu nije dokazana.

## 5. E5 — skala (Llama-3.3-70B, 10.000, conc 512)

`ok 10.000/10.000`, `false_success 0/10.000`, `PASS`; TTFT p50 14,5 s (conc 512
neekonomičan za 70B; radna točka 256).

## 5b. Skaliranje i MFU (1 čvor, TP 1–8, 10.–11.11.)

Decode workload: 512 zahtjeva, 256 prompt tokena, tačno 128 izlaznih (`ignore_eos`).
MFU je procjena (bez attention/prefill).

| model | conc | TP1 | TP2 | TP4 | TP8 |
|---|---|---|---|---|---|
| Qwen2.5-7B | 256 | 33,7 rps / 34,3% | **57,8 rps / 29,4%** | 57,8 / 14,7% | nije podržan (28 glava) |
| Mistral-7B | 256 | 32,0 / 30,8% | 49,1 / 23,6% | 51,5 / 12,4% | **70,5 rps / 8,5%** |

- Jedan GCD daje **31–34% MFU**; TP kupuje latenciju (Qwen p50 7,23 → 4,10 s), ne efikasnost.
- Skaliranje zasićuje model-zavisno: Qwen TP2→TP4 **0%**, Mistral TP4→TP8 **+37%**.
- TP=8 traži broj glava djeljiv sa 8; Qwen2.5-7B (28) odbija TP=8.
- Multi-node (DP) skaliranje **nije mjereno**. Dokaz: `docs/RESULTS_SCALING_2026-11-10.md`,
  `benchmark/scaling_2026-11-10.json`, poslovi 23624574/23625077.

**Multi-node (DP, 1 replica po čvoru, TP=8, Mistral-7B, poslovi 23626081/23626364):**

| čvorova | GCD | rps | ubrzanje | rps/GCD | MFU |
|---|---|---|---|---|---|
| 1 | 8 | 70,49 | 1,00× | 8,81 | 8,48% |
| 2 | 16 | 140,37 | **1,99×** | 8,77 | 8,44% |
| 4 | 32 | 269,55 | **3,82×** | 8,42 | 8,11% |

Concurrency se skalira po replici (256/čvor); sa fiksnim ukupnim conc 2 čvora daju samo
1,33× (mjerna greška, ne limit). Efikasnost 95,6% na 4 čvora; ~8,4 rps/GCD ≈ **30.000
zahtjeva po GCD-satu**. Po GCD-u je TP=1 najbolji (32,0 rps) a TP=8 najgori (8,8) — TP=8
kupuje latenciju. Dokaz: `docs/RESULTS_MULTINODE_2026-11-10.md`,
`benchmark/multinode_2026-11-10.json`.

## 6. E6 — deterministička kapija nad fakturama (PDV 17%)

500 faktura (381 dirty / 119 clean), 3 seeda: **recall 1.109/1.109 = 100%**,
**FP 0/391**, Wilson gornja granica **0,97%** ≤ 1%. Dokaz: `benchmark/e6_check.json`.

**Osjetljivost na probu (E13, 11.11., 0 GPU):** iste 500 fakture kroz 5 nivoa provjere daju
**0,0% / 30,2% / 47,8% / 49,1% / 100%** recall (L0 trust → L4 full), uz **0/119** lažnih
blokada na svakom nivou. „100% kapija" je osobina para *(kapija, nivo probe)*, ne sistema.
Dokaz: `docs/RESULTS_E13_2026-11-11.md`, `benchmark/e13_probe_sensitivity.json`.

## 7. Bench v2 — 700 provjerljivih zadataka (4 bloka)

| model | aritmetika | needle | honesty | tool-JSON | ukupno |
|---|---|---|---|---|---|
| Qwen3.8-27B-FP8 | 298/300 (99,3%)* | 99% | 83% | 0/200 (artefakt)* | 68,6%* |
| gpt-oss-120b | 37,0% | 99% | 59% | 99% | **66,7%** |
| Qwen2.5-7B | 17,3% | 99% | 73–81% | 100% | 60,6–61,7% |
| Qwen2.5-VL-7B | 10,3% | 99% | 17% | 96% | 48,4% |
| Llama-3.3-70B | 7,3% | 99% | 28% | 91% | 47,3% |
| Llama-Poro-70B | 5,7% | 100% | 36% | 79% | 44,4% |
| Mistral-3.1/3.2 | — | — | — | — | **INVALID** (tokenizer) |

\* Qwen3.8 je thinking model; `b5=0` je artefakt odsječenog `max_tokens`, ne nesposobnost.

**Korekcija intervala (klasteri = šabloni, 10.11.):** 700 stavki dolazi iz **24 šablona**,
pa Wilson intervali potcjenjuju neizvjesnost. Klaster-bootstrap (B=4.000):

| model | acc | Wilson 95% | klaster 95% | deff | efektivni N |
|---|---|---|---|---|---|
| Qwen2.5-7B | 60,6% | [56,9; 64,1] | [50,2; 72,4] | 10,03 | 69,8 |
| Llama-3.3-70B | 47,3% | [43,6; 51,0] | [39,3; 55,2] | 4,71 | 148,5 |
| bal6 | 63,4% | [59,8; 66,9] | [49,1; 81,5] | 21,86 | 32,0 |

Tačnost je određena šablonom: Qwen2.5-7B ima `b1_sub` **0/114** i `b1_total` **0/79**, a
sva aritmetika dolazi iz `b1_vat` (52/107); bal6 skok na 38% je samo `b1_vat` 48,6% → 83,2%.
Honesty je po tipu entiteta „sve ili ništa" (bal6: firma 0/13, kompanija 0/14, uređaj 0/18).
Dokaz: `docs/RESULTS_STATS_2026-11-10.md`, `benchmark/cluster_stats_2026-11-10.json`.

**Cross-family (10.11., poslovi 23621892/23622412):** Mistral-7B-Instruct-v0.3
38,4/38,3/38,6% i Phi-3.5-mini 37,7/35,9/36,0% (3 seeda, 0 grešaka). Isti profil blokova:
needle 87–99%, tool-JSON 63–71%, aritmetika 0,7–15%, honesty 0–27%. Flipovi između seedova
su model-zavisni (Mistral 5–9/700, Phi 22–23/700). Dokaz:
`docs/RESULTS_CROSSFAM_2026-11-10.md`, `benchmark/crossfamily_2026-11-10.json`.

**Honesty na stvarnim opskurnim entitetima (500 stavki, Wikidata, 10.11.):** poslovi
23623454 (forsirani odgovor) i 23623695 (dozvoljeno „ne znam"). Fabrikacija:

| model | forsirano | sa dozvolom | hedge (sa dozvolom) |
|---|---|---|---|
| Qwen2.5-7B | **94,8%** | **21,6%** | 77,6% |
| Mistral-7B | **74,4%** | **17,0%** | 72,8% |
| Phi-3.5-mini | **71,4%** | **13,0%** | 85,8% |

Qwen2.5-7B je hedžovao 73–81% na *izmišljenim* entitetima, a **0/1000** na stvarnim
opskurnim — okidač nije „ne znam", nego „izgleda izmišljeno". Format pitanja mijenja
fabrikaciju 3,5–5×. Dokaz: `docs/RESULTS_HONESTY_REAL_2026-11-10.md`,
`benchmark/honesty_real_2026-11-10.json`.

## 8. Adapteri (v1 setovi: bench v0.6 + conf14 + conf50)

| model | strict | first-call | args | pita/64 | izvršilo/64 |
|---|---|---|---|---|---|
| base | 21/25 | 21/25 | 7/7 | 0 | 8 |
| g03a | 18/25 | 20/25 | 5/7 | 38 | 26 |
| bal1 | 9/25 | 21/25 | 0/7 | 8 | 56 |
| bal2 | 4/25 | 20/25 | 1/7 | 7 | 57 |
| bal3 | 0/25 | 24/25 | 0/7 | 1 | 63 |
| **bal5** | **22/25** | 22/25 | **7/7** | **7** | **15** |

**bal5 na bench v2:** 444/700 = **63,4%** (base 60,6%); aritmetika +20,7 pp,
honesty −31 pp, tool-JSON −5,5 pp.

**Nalaz:** kvar terminacije kod bal1–bal3 dolazi od **warm-starta na g03a**, ne od
podataka (bal5 iz base čuva terminaciju 22 = 22).

## 8b. bal6 i RiskGate (10.11.2026)

**bal6** (800 uzoraka: 320 tool + 320 hedge + 160 činjenica, holdout-čist):
- v1 setovi: **strict 23/25 (92%)** — najbolji adapter, `args 7/7`, terminacija `23 = 23`
- bench v2: aritmetika **38%**, needle 99%, tool-JSON **95%**, **honesty 41%** (base 73%)
- **Honesty se ne može istrenirati**: bal6 izmišlja „matični broj Valdora Logistik je
  33006020000", „Novex Dynamics osnovana 1. januara 2014". 320 hedge primjera uči
  **stil**, ne prepoznavanje nepoznatog; trening je **pogoršao** honesty (73% → 41%).

**RiskGate** (`guard/risk_gate.py`, validacija `benchmark/riskgate_validate.py`):
- **119/119 destruktivnih poziva blokirano (100%)** na 64 rizična prompta × 5 modela
  (base 1, g03a 7, bal3 52, bal5 23, bal6 36)
- **0/108 lažnih blokada** na legitimnim read-only pozivima
- 92 legitimna destruktivna poziva → traži potvrdu (ispravno)
- Ispravljena metrika: read-only poziv na rizičnom promptu nije „rizično izvršenje"

**Adaptivni protivnik (E10, 11.11., 0 GPU-h):** 8 destruktivnih sjemenki × 8 mutatora.
v2 fail-closed = 0% ASR; sa `terminal` allowlisted **100% na prvoj mutaciji** (base64).
v3 (dekodiranje) 0% na tom setu, ali nezavisna familija (octal) ga zaobilazi 100%; v4 doda
octal → bypass prelazi na zero-width. Denylist nad tekstom je trka u naoružanju, ne kontrola.
Dokaz: `docs/RESULTS_E10_2026-11-11.md`.

**Atribucija (E14, 11.11.):** Qwen **75%**, Phi **87%** prisvaja oporavak koji je sistem sam
napravio (kauzalna kontrola: 94–100% tačno); Mistral 73% „nejasno". Dokaz:
`docs/RESULTS_E14_2026-11-11.md`.

**Stres samog gate-a (10.11., 0 GPU-h):** 1.000 destruktivnih varijanti + 500 benignih
(`benchmark/riskgate_stress.py`). v1 (lista imena) hvata **52,6%** — imenske varijante 0/182,
SQL 0/36, shell kroz `terminal` 85/288. v2 (`guard/risk_gate_v2.py`: normalizacija imena +
homoglifi + command/path/SQL politike + fail-closed) hvata **1000/1000 = 100%**, uz
**0/500** lažnih blokada. Dokaz: `docs/RESULTS_RISKGATE_STRESS_2026-11-10.md`,
`benchmark/riskgate_stress_2026-11-10.json`, `tests/test_risk_gate_v2.py` (35 testova).

## 9. Harness (GAMA) — stanje
- **1.022 testa prolaze** u 112 fajla, 0 padova (2 fajla su skripte, ne pytest).
- **SWE mini-zadatak** (novi bug, ne fixture): agent popravio u **5 koraka / 17 s**,
  `4 passed`, testove nije dirao.
- Popravljen bug: alat je gađao `:8443` bez tokena (401) → sada `:7125` + token.

## 9b. E7 — nezavisna reprodukcija: PASS

`benchmark/e7_reproduce.py` iz čistog temp direktorija:
- bench v2 dataset (seed 2026): sha256 **identičan** `49c2f8ac…`
- E6 kapija: recall `1.0`, FP `0.0` — identično
- E3 guard V2 (seed 2027): detekcija `0.9015`, FP `0.025` — identično
- Model-generisani izlazi **svjesno izuzeti** (E2: vLLM nije bit-determinističan na temp 0,
  ni serijski — vidi §2)

## 10. Trošak

- 9.11.2026: **18,47 GPU-h** (0,37% kvote); 10.11. noć: ~15 GPU-h.
- Novembar ukupno na dan 10.11.: ~520 GPU-h od 5.000 (10,4%).
- Preostali plan (E7 + release) ≈ **1 node-h**.

## 11. Otvoreno / sljedeće

1. **Release v1.5.0 OBJAVLJEN 10.11.2026** — Zenodo DOI `10.5281/zenodo.24118913`
   (concept `10.5281/zenodo.24118912`), GitHub release `v1.5.0` sa bundle-om
   (`agentmujo-bench-v1.5.0.zip`, sha256 `344948a2…1897`, 38 fajlova).
2. Mistral tokenizer fix (`--limit-mm-per-prompt` ili tokenizer sa `fix_mistral_regex`).
3. Bit-determinizam: dokazano da ga nema ni serijski (E2). Ako zatreba, tražiti
   `VLLM_USE_V1=0` / batch-invariant kernels — nije na kritičnom putu.
