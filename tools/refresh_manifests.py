#!/usr/bin/env python3
"""Recompute the counts and sha256 in datasets/manifests/*.json from the files.

The manifests had drifted: three of nine declared 381/670/672 rows while the files
held 749/1178/1389, and none of them carried a hash, so nothing could be checked.
This script rewrites `counts.by_task`, `counts.total` and `sha256` from the data and
leaves every other field untouched.

    python3 tools/refresh_manifests.py          # rewrite
    python3 tools/refresh_manifests.py --check  # exit 1 if anything is stale
"""
from __future__ import annotations

import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "datasets" / "manifests"


def measure(path: pathlib.Path) -> dict:
    digest = hashlib.sha256()
    by_task: collections.Counter[str] = collections.Counter()
    total = 0
    with path.open("rb") as fh:
        for raw in fh:
            digest.update(raw)
            line = raw.strip()
            if not line:
                continue
            total += 1
            try:
                by_task[str(json.loads(line).get("task"))] += 1
            except json.JSONDecodeError:
                by_task["<invalid-json>"] += 1
    return {"total": total,
            "by_task": dict(sorted(by_task.items())),
            "sha256": digest.hexdigest()}


def main(argv: list[str]) -> int:
    check = "--check" in argv[1:]
    stale = 0
    for manifest_path in sorted(MANIFESTS.glob("*.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not manifest.get("file"):
            # provenance manifests (e.g. wikipedia_sources) describe a source, not a dataset file
            print(f"{manifest_path.name}: not a dataset manifest, skipped")
            continue
        target = ROOT / manifest.get("file", "")
        if not target.is_file():
            print(f"{manifest_path.name}: file {manifest.get('file')!r} missing")
            stale += 1
            continue
        measured = measure(target)
        before = (manifest.get("counts", {}).get("total"),
                  manifest.get("counts", {}).get("by_task"),
                  manifest.get("sha256"))
        after = (measured["total"], measured["by_task"], measured["sha256"])
        if before == after:
            print(f"{manifest_path.name}: ok ({measured['total']} rows)")
            continue
        stale += 1
        print(f"{manifest_path.name}: {before[0]} -> {measured['total']} rows, sha256 {measured['sha256'][:12]}")
        if not check:
            manifest["counts"] = {"total": measured["total"], "by_task": measured["by_task"]}
            manifest["sha256"] = measured["sha256"]
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    if check and stale:
        print(f"{stale} manifest(s) stale: run python3 tools/refresh_manifests.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
