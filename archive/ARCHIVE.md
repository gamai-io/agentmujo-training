# Archived run artifacts

On **2026-11-26** the raw benchmark/eval run dumps were moved out of git into GitHub
release assets, so a clone carries the product (datasets, source, release manifests)
instead of the log history. Base commit before the split:
`159482c7c2ebf5e2b1edb439cb92fc7cbb94780e`.

Nothing was deleted: every byte listed here is inside the tarballs below, and the
per-file sha256 manifests (`MANIFEST-benchmark.txt`, `MANIFEST-results.txt`) let you
verify a restored tree.

## Assets

| Asset | Files | Uncompressed | Size | sha256 |
|---|---|---|---|---|
| `benchmark-archive-2026-11-26.tar.gz` | 12 | 3,225,471 B | 434,794 B | `aeda19d8e7cd02ad95d15638b273a2123262b39c9816a4f5d5c2543b05568e4f` |
| `results-archive-2026-11-26.tar.gz` | 201 | 4,838,731 B | 977,802 B | `b44e36e91273652e05f7f5c7f106e52e9fb1e6fd3840bd4ac50201bdf32ec308` |

`SHA256SUMS` in this directory is the same two hashes in `sha256sum -c` format.

## What moved

### `benchmark-archive-2026-11-26.tar.gz`

Orphaned/superseded dumps inside `benchmark/` — no test, script, release manifest or
generated doc reads them:

- `benchmark/results_lumi_with_bal.jsonl`
- `benchmark/results_lumi_with_bal3.jsonl`
- `benchmark/results_lumi_tf_multi2.jsonl`
- `benchmark/results_base_fixed.jsonl`
- `benchmark/human_eval/items_200_run.jsonl` (the 200-item run cited in
  `benchmark/human_eval/PROTOCOL.md`; the derived annotation sets stay in git)
- `benchmark/v2_results/night_night_queue.log`, `night_night_queue2.log`, `night_night_queue3.log`
- `benchmark/v2_results/v2_bal5_23603294.jsonl`
- `benchmark/v2_results/v2_bal6_23613126.jsonl`
- `benchmark/v2_results/v2_llama70b.jsonl`
- `benchmark/v2_results/v2_qwen27b_t1024_23586736.summary.json`

### `results-archive-2026-11-26.tar.gz`

The whole `results/` tree (201 files, 12 run directories: `eA-pilot`, `eA-full`,
`eA-mistral`, `eA-restart`, `eB-crossnode`, `eC-tp8`, `eD-rccl`, `eE-intermittency`,
`eF-pilot`, `eF-v2`, `eF-v3`, `big-30b`). These are per-run JSONL/summary output and
vLLM/sbatch logs. Docs cite them as evidence (`Dokaz: results/<run>/`); the reproducer
for each claim is the `.sbatch`/`.py` pair in `benchmark/`, which stays in git.

## Why

- Every file above is output, not input: removing it cannot change a test result or a
  release-manifest check (`releases/*/RELEASE.json` only references paths under
  `releases/`).
- They were 8,064,202 B (7.69 MiB) of 48.00 MiB of tracked content (16% of the clone) for data that is
  read by humans, not by code.
- History is preserved: the tarballs are cut from the base commit with `git archive`,
  and the pre-split commit still holds the blobs.

## What deliberately stayed

Kept in git because something reads them — see `docs/ARCHIVE_DECISIONS.md`:

- `benchmark/cases_v0.{1,3,4,5,6}.jsonl` — read by `tests/` and the CLI default `--cases`.
- `benchmark/{metrics,score_suite,e6_gate,e3_guard_v2,e10_adversary,...}.py`,
  `*.sbatch`, `*.md`, `human_eval/*.html` — importable modules used by tests, and the
  only way to reproduce a claim.
- `benchmark/results_*.json` (79 files) — `src/agentmujo_training/registry/index.py`
  globs them to build the "Benchmark izvještaji" table committed in `docs/REGISTRY.md`.
  Moving them would silently empty a generated, committed doc.
- `benchmark/v2_results/v2_qwen7b.jsonl` — read as an input by
  `benchmark/human_eval/make_annot_pilot.py`.
- `benchmark/items_*.jsonl`, `benchmark/human_eval/items_*` / `annotations_*` — item
  sets and human annotations whose content/md5 the docs pin.
- `benchmark/e6_invoices.jsonl`, `benchmark/e6_check.json` and the other small
  `*_2026-*.json` evidence summaries — inputs to gates and the artifacts quoted in
  `docs/RESULTS_INDEX_2026-11-11.md`.

## How to fetch it back

```bash
gh release download archive-2026-11-26 -R gamai-io/agentmujo-training \
  -p 'benchmark-archive-2026-11-26.tar.gz' \
  -p 'results-archive-2026-11-26.tar.gz' \
  -p 'SHA256SUMS' -p 'MANIFEST-*.txt' -D archive/

cd archive && sha256sum -c SHA256SUMS

# restore into the tree (paths are stored relative to the repo root)
tar -xzf benchmark-archive-2026-11-26.tar.gz -C ..
tar -xzf results-archive-2026-11-26.tar.gz   -C ..

# verify every restored file against the archive manifest
cd .. && sha256sum -c archive/MANIFEST-results.txt
```

Without `gh`, the browser equivalent is
`https://github.com/gamai-io/agentmujo-training/releases/tag/archive-2026-11-26`.

Restoring is meant to be safe to do in a scratch clone: the release tag is a snapshot of
the pre-split tree, so `git status` will show the restored files as untracked rather than
as modifications.

## Reproducing the tarballs

```bash
git archive --format=tar.gz -o benchmark-archive-2026-11-26.tar.gz \
  159482c7c2ebf5e2b1edb439cb92fc7cbb94780e -- $(cat archive/MANIFEST-benchmark.txt | awk '{print $2}')
git archive --format=tar.gz -o results-archive-2026-11-26.tar.gz \
  159482c7c2ebf5e2b1edb439cb92fc7cbb94780e -- results/
```
