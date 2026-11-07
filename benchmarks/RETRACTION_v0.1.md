# Retraction notice — agentic_eval v0.1 (2026-11-07)

## Sta se dogodilo

`benchmarks/agentic_eval_v0.1.jsonl` je bio objavljen u ovom repozitoriju od **2026-10-31** do **2026-11-07**, iako su njegove stavke oznacene `held_out: true`. Iste stavke su bile i u `releases/v0.3.0/` i `releases/v0.4.0/`, a dva fajla sa rezultatima (`aitta_*_v0.1.json`) su sadrzavala pune promptove, ukljucujuci jedan generisani poslovni email i polja tipa `invoice_id`.

Objavljivanje holdout skupa znaci da on vise nije holdout: svako mjerenje na v0.1 je **public-set** mjerenje, bez obzira kako je originalno oznaceno.

## Sta je uradjeno

- Sva tri primjerka `agentic_eval_v0.1.jsonl` (korijen + `releases/v0.3.0/` + `releases/v0.4.0/`) zamijenjena su **redigovanom verzijom**: zadrzani su `id`, `category`, `difficulty`, `allowed_tools`, `expected_tools`, `requires_confirmation`; uklonjeni su `goal`, `messages`, `success_criteria`, `verification`; svaka stavka nosi `withheld: true`, `status: "retired-compromised"`, `metadata.held_out: false`, `metadata.public_set: true`.
- Rezultati u `benchmarks/results/` i `releases/v0.4.0/benchmarks/results/` svedeni su na agregate (ID, kategorija, pozvani/ocekivani alati, prolaz, latencija). Brojevi nisu mijenjani (28/50 i 25/50, provjereno).
- `tests/test_agentic_eval.py` sada **dokazuje** da su stavke redigovane; `tests/test_holdout_privacy.py` sprecava ponovno objavljivanje promptova.
- `scripts/run_agentic_eval.py` odbija da pokrene redigovani skup (osim uz `--allow-retired`, sto daje upozorenje da rezultat nije holdout).

## Sta ovo ne znaci

- Brisanje sadrzaja iz trenutnog stabla **ne brise** ga iz git historije. Svako ko je klonirao repo prije 2026-11-07 ima kopiju. Zato se v0.1 trajno tretira kao javni skup.
- Brojevi 28/50 (gpt-oss-120b) i 25/50 (Qwen3.6-35B-A3B) ostaju tacni kao **tool-selection na javnom skupu**, ali se ne smiju navoditi kao holdout rezultat.
- Novi holdout mora biti izradjen interno, ne objavljivan, i oznacen kao `v0.2-private`. Do tada, za javno poredjenje koristiti `benchmark/cases_v0.5.jsonl` (48 stavki, `prompt` polje — namjerno javni skup).

## Rok i odgovornost

Uoceno i ispravljeno 2026-11-07. Nema dokaza da je skup koristen za trening; `benchmarks/README.md` je od pocetka zabranjivao trening na njemu. Prijavu problema: security@gamai.io.
