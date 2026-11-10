# arXiv submission — paket v0.3 (10.11.2026)

## Status

- PDF: `docs/PREPRINT_v0.3_2026-11-10.pdf` (generisan 10.11.2026, 46 KB).
- Izvor: `docs/PREPRINT_v0.3_2026-11-10.md`.
- **Nije poslano**: arXiv traži nalog + (za prvi submit u cs.SE) endorsement. Nema
  sačuvanih arXiv kredencijala u memoriji — potreban login korisnika.

## Metadata za formu

**Title**
False Success Is an Architecture Problem: Evidence Gate and Deterministic Verification for LLM Agents on HPC

**Authors**
Renato Šuster (GAMA TRADE / gamAI)

**Abstract (plain text, ≤1920 znakova)**

Agents built on language models are increasingly allowed to run actions (restart services,
delete tables, send mail). Two failure modes are invisible to text-level benchmarks: the
agent reports success for work that never happened (false success), and the agent executes
a destructive action without approval. We report a measurement campaign on LUMI (AMD
MI250X) covering 36,550 guard requests across two model families and four concurrency
levels, an objectively scorable 700-item benchmark, a deterministic document verification
gate, and an adaptive prompt-injection evaluation. False success is not eliminated by
scale: no model resisted fabricating specific facts about non-existent entities, and
supervised fine-tuning made honesty worse (73% to 41%). Text-level guards are ineffective:
a keyword guard detected 33.0% of paraphrased attacks while blocking 35.0% of legitimate
questions; an intent guard reached 90.1%/2.5% in-sample and 85.7%/3.5% out-of-sample,
still short of 95%. An action-level deterministic gate blocked 119/119 destructive calls
with zero false blocks on 108 read-only calls. A template-level re-analysis shows the 700
items come from 24 prompt templates (design effect 4.7-21.9, effective N 32-149) and that
accuracy is decided by the template, not the item. Model output is not bit-identical even
under strictly serial decoding. We conclude that truthfulness must be enforced
architecturally, by an action-level gate plus deterministic verification, rather than
learned.

**Categories**
- Primary: `cs.SE` (Software Engineering)
- Cross-list: `cs.DC` (Distributed, Parallel, and Cluster Computing), `cs.LG`

**Comments**
5 pages, 6 tables. Evidence pack: DOI 10.5281/zenodo.24118913. Code:
https://github.com/gamai-io/agentmujo-training (tag v1.5.0).

**License**
arXiv perpetual, non-exclusive license (default). Repo code is Apache-2.0.

## Checklist prije submita

- [ ] arXiv nalog (ili pristup postojećem) + endorsement za cs.SE ako je prvi submit.
- [ ] Provjeriti da PDF nema reference na interne fajlove/pune putanje.
- [ ] Odlučiti: PDF-only ili LaTeX izvor (arXiv preferira izvor; `.tex` nije pripremljen).
- [ ] Nakon objave: dodati arXiv ID u README badge, CITATION.cff (`preferred-citation`)
      i u Zenodo `related_identifiers`.
- [ ] Ne mijenjati brojeve u apstraktu bez ponovnog pokretanja skripti.

## Napomena o tvrdnjama

Apstrakt navodi samo izmjerene brojeve. Namjerno **nema** tvrdnji o bit-identičnom
generisanju, o honesty poboljšanju SFT-om, ni o guardu ≥95%. Ako recenzent traži
„state-of-the-art", odgovor je: ovo je mjerni i arhitektonski rad, ne SOTA trka.
