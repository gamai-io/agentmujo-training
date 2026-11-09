# AgentMujo Bench v2 — prvi rezultati (10.11.2026, LUMI)

## Šta je v2

Generisan, **objektivno provjerljiv** bench — nema ljudskog ocjenjivanja ni „judge" modela.
700 zadataka, 4 bloka, deterministički seed (`2026`), SHA-256 dataseta
**`49c2f8ac4add1f6f7c5fae08692fef674b3c12433d7da45dfde4172044475157`**
(isti hash i na Contabu i na LUMI-ju → generator je reproducibilan).

| Blok | n | Šta mjeri | Provjera |
|---|---|---|---|
| `b1_arith` | 300 | tačna aritmetika sa PDV 17% (ukupno / PDV / osnovica) | broj u toleranciji ±0,011 |
| `b2_needle` | 100 | dugi kontekst (120–200 zapisa), pronalaženje tačne vrijednosti | tačna vrijednost u odgovoru |
| `b4_honesty` | 100 | pitanja o **nepostojećim** entitetima | traži priznanje neznanja **i** odsustvo izmišljene tvrdnje |
| `b5_toolargs` | 200 | tačan JSON poziv alata (ime + tipizirani argumenti) | egzaktno poređenje JSON-a |

## Rezultati (temperature 0, seed 42, `max_tokens 256`)

| model | b1 arith | b2 needle | b4 honesty | b5 toolargs | **ukupno** |
|---|---|---|---|---|---|
| Qwen2.5-7B | 52/300 (17,3%) | 99/100 (99%) | **73/100 (73%)** | **200/200 (100%)** | **424/700 = 60,6%** CI[56,9–64,1] |
| Llama-3.3-70B | 22/300 (7,3%) | 99/100 (99%) | **28/100 (28%)** | 182/200 (91%) | **331/700 = 47,3%** CI[43,6–51,0] |

## Nalazi (neprijatni, ali provjerljivi)

1. **Veći model je gori na ovom benchnu**: 7B (60,6%) pobjeđuje 70B (47,3%),
   i to na dvije stavke — aritmetika (17,3% vs 7,3%) i **honesty (73% vs 28%)**.
2. **Aritmetika je katastrofa kod oba**: tačan decimalni obračun sa PDV-om
   (17%) pogađaju u **7–17%** slučajeva. To je jak argument za determinističku
   kalkulaciju umjesto oslanjanja na model (i za E6 kapiju).
3. **Honesty se raspada sa veličinom**: Llama-3.3-70B izmišlja odgovore o
   nepostojećim državama/firmama/protokolima u **72%** slučajeva; Qwen-7B u 27%.
4. **Alati su im jača strana**: JSON poziv 100% (7B) i 91% (70B); 70B je griješio
   uglavnom izmišljajući imena alata (`select_lines`) — ista klasa greške kao b4.
5. **Dugi kontekst im je dobar** (99% oba) — needle nije problem, zaključivanje jeste.

## Ispravke mjerenja tokom rada (dokaz da nije bilo „friziranja")

1. Prva verzija `HEDGE` regexa nije prepoznala „nemam pristup" / „nisam u mogućnosti"
   → honesty je lažno bio 10/100 (7B) i 0/100 (70B). Popravljeno, dodato i pravilo
   da **izmišljena tvrdnja ruši** odgovor čak i ako sadrži ogradu. Re-score je urađen
   offline iz sačuvanih izlaza (isti JSONL), bez ponovnog pokretanja modela.
2. `b1` sada prihvata i evropski format (`1.154,23`).

14 testova scorera prolazi (`tests/test_bench_v2.py`).

## Ograničenja

- 2 modela (7B lokalni, 70B iz LAIF-a); Mistral-3.2 je isključen (tokenizer bug).
- `b4` mjeri ponašanje na **izmišljenim** entitetima; to je donja granica
  „ne izmišljaj", ne dokaz tačnosti na stvarnim podacima.
- 700 zadataka je malo za tvrdnje o „skali"; E1 (36.550 zahtjeva) pokriva skalu,
  v2 pokriva **kvalitet po kategorijama**.

## Kako se pokreće

```bash
bash -lc 'python3 gen_v2.py --out items_v2.jsonl --manifest items_v2.manifest.json'
sbatch --partition=dev-g --export=ALL,MODEL=<path>,N=0,CONC=64,TAG=<tag> serve_and_bench_v2.sbatch
python3 scoreboard_v2.py        # tabela iz svih v2_*.summary.json
```
