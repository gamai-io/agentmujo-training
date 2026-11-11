# VLLM_BATCH_INVARIANT na MI250X — da li rješava flips? (11.11.2026)

**Pitanje:** vLLM nudi `VLLM_BATCH_INVARIANT=1` (beta; podržano na gfx90a = MI250X).
Garantuje li to reproducibilnost na LUMI-ju, gdje smo bez flaga imali 660/700 (TP=4) i
669/700 (TP=1) identičnih izlaza u serijskom režimu?

## Postavka

- Model: Qwen2.5-7B, bench v2 (700 stavki), `temperature=0`, `seed=42`.
- **Teži uslov nego E2:** `--conc 64`, `--max-num-seqs 256` (BI je tvrđenje o nezavisnosti
  od batcha, pa se testira sa batchom, ne serijski).
- Tri prolaza: **A** i **B** u istom serverskom procesu; **C** poslije restarta servera.
- Poslovi: **23626963** (TP=1), **23627134** (TP=4). Skripta: `benchmark/e2_batchinvariant.sbatch`.

## Rezultat

| TP | A vs B (isti proces) | A vs C (novi proces) | sha(A)=sha(B) | sha(A)=sha(C) |
|---|---|---|---|---|
| 1 | **700/700 = 100%** | 586/700 = 83,71% | da | ne |
| 4 | **700/700 = 100%** | 593/700 = 84,71% | da | ne |

Bez flaga (E2, serijski: `--max-num-seqs 1`, `conc 1`): TP=4 660/700 (94,29%),
TP=1 669/700 (95,57%).

## Nalazi

1. **Batch invariance radi na MI250X.** U istom procesu, na concurrency 64 i sa
   `max-num-seqs 256`, dva prolaza su **bit-identična (700/700)** — i na TP=1 i na TP=4.
   To je bolje od baseline-a koji je bio *stroži* po batchu (serijski) a ipak imao 31–40
   razlika.
2. **Garancija se NE prenosi na novi proces.** Poslije restarta servera razlikuje se
   **107–114 od 700 stavki (15–16%)**. Dakle `VLLM_BATCH_INVARIANT=1` daje
   *unutar-procesnu* determinaciju, ne *cross-process* reproducibilnost.
3. **TP ne kvari unutar-procesnu garanciju** (TP=1 i TP=4 oba 700/700), uprkos upozorenju
   iz dokumentacije o all-reduce veličinama.
4. **Praktična preporuka:** za evaluacije koje porede modele u istoj sesiji — uključiti
   flag (uklanja šum od batcha). Za „isti rezultat poslije restarta" — flag nije dovoljan;
   treba fiksirati i okruženje procesa (alokator/workspace/autotune), što je sljedeći
   eksperiment.

## Ograničenja

- Jedan model (Qwen2.5-7B) i jedan concurrency (64); TP=8 nije testiran (28 glava).
- „Cross-process" je jedan restart (A vs C), ne više njih; ne mjeri se *koji* se tokeni
  mijenjaju (forenzika je sljedeći korak).
- vLLM batch invariance je beta; ponašanje može zavisiti od verzije kontejnera.

## Reprodukcija

```bash
sbatch -p dev-g --export=ALL,TP=1,OUTJSON=$OUT/e2_batchinvariant_tp1.json \
  /project/project_465003647/gama/e2_batchinvariant.sbatch
```

Artefakti: LUMI `out/e2_batchinvariant_tp{1,4}.json`, `out/bi_{a,b,c}_tp*_<job>.jsonl`;
sažetak u repou `benchmark/batchinvariant_2026-11-10.json`.
