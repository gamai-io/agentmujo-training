# Bench registar (v1, 09.11.2026)

Jedno mjesto gdje piše **šta je javno, šta privatno, koji je hash i čemu služi**.
Pravilo: svaki rezultat u `docs/` mora navesti ime bencha + verziju + hash iz ove tabele.

## Javni setovi (u repou)

| Set | Fajl | n | Šta mjeri | SHA-256 | Status |
|---|---|---|---|---|---|
| AgentMujo Bench v0.6 | `cases_v0.6.jsonl` | 49 (16 kategorija) | tool selection, args, task, multi-step, verification, ijekavica, sigurnost | `4cf02da2445b590dcb9b279ab702f91be57e9b711dbe046af001748301fba636` | stabilan |
| Confirmation-14 | `cases_conf14.jsonl` | 14 | rizičan zahtjev bez odobrenja: traži li model potvrdu i izvršava li | `abf86dc9b393c041928c1b1a72d66600728fa9421fd2ef5105cc7aa5ae4e1c6b` | stabilan |
| Confirmation-50 | `cases_conf50.jsonl` | 50 (10 familija × 5) | isto, statistički upotrebljivo (Wilson CI) | `3eb407bc66efc8391868f6fc7d71a533cd841237324e24a7293a071093d5d013` | **novo** |
| Metrički paket | `metrics.py` | 15 testova | hallucination, over-refusal, schema, determinism, paraphrase, injection, secrets, latency, gate | `bac5b588fa4aff8f96e4d0d125576414875853b3d572397aea793a09eebc5c2d` | stabilan |

## Privatni setovi (NIKAD ne objavljivati stavke)

| Set | Lokacija | n | Šta mjeri | Objavljuje se |
|---|---|---|---|---|
| Holdout v0.2 | `/root/gamaos/private/holdout_v0.2/items.jsonl` | 60 | finalna provjera bez kontaminacije | samo agregat + SHA manifest |
| Guard bench (12 šablona) | `/project/project_465003647/gama/bench_v2/prompts_v1.json` | 12 šablona × N | false-success na skali | šabloni javni, sirovi rezultati po jobu |

## Kako se koriste

1. **Razvoj i regresija:** v0.6 + conf14 (brzo, 63 upita).
2. **Tvrdnje u radu:** conf50 (n=50, Wilson CI) + v0.6.
3. **Finalna tvrdnja prije objave:** privatni holdout v0.2 (jednom, bez iteriranja).
4. **Skala (LUMI):** guard bench, 12 šablona; u tekstu uvijek „12 šablona × ~N ponavljanja", nikad „N različitih zadataka".

## Dvije metrike koje se od sada prijavljuju zajedno

- **strict:** tačno jedan `tool_call` i ništa poslije.
- **first-call:** tekst se odsiječe na prvom `</tool_call>` pa se parsira.

Razlika između njih mjeri **terminaciju** (da li model stane), a ne selekciju alata.
Primjer (09.11.2026): bal2 strict 4/25, first-call 20/25 → problem je terminacija, ne izbor alata.

## Verzionisanje

- v0.6 i conf setovi se **zamrzavaju**; izmjena = nova verzija (`v0.7`, `conf50-v2`) + novi hash.
- Rezultati stariji od izmjene ostaju vezani za stari hash.
- Nijedan set se ne mijenja „u mjestu" nakon što je objavljen neki rezultat.
