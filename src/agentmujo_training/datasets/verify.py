"""RELEASE_VERIFY_V1 — provjeri da svaki fajl zapisan u RELEASE.json odgovara svom sha256.

Repo kojem je proizvod verifikacija ne smije isporuciti release koji ne moze
verificirati. `verify_release` ponovno racuna sha256 (i broj redova) za svaki
dataset, benchmark i benchmark rezultat naveden u `releases/<verzija>/RELEASE.json`
i vraca `ok=False` sa tacnim mismatchom. Brzo: samo hash + brojanje linija.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .release import release_dir


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _count_rows(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _resolve(repo: Path, path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo / p


def verify_release(repo: str | Path, version: str) -> dict[str, Any]:
    """Vrati {"ok": bool, "version": ..., "files": n, "checks": [...], "mismatches": [...]}."""
    repo = Path(repo)
    out = release_dir(repo, version)
    release_path = out / "RELEASE.json"
    if not release_path.exists():
        return {"ok": False, "version": version, "files": 0, "checks": [],
                "mismatches": [{"path": str(release_path), "error": "nema RELEASE.json"}]}
    release = json.loads(release_path.read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []

    def check(kind: str, path: str | Path, expected_sha: str, expected_rows: int | None = None) -> None:
        p = _resolve(repo, path)
        shown = str(p.relative_to(repo)) if p.is_relative_to(repo) else str(p)
        if not p.exists():
            mismatches.append({"kind": kind, "path": shown, "error": "fajl ne postoji",
                               "expected_sha256": expected_sha})
            return
        actual = _sha(p)
        item: dict[str, Any] = {"kind": kind, "path": shown, "sha256": actual,
                                "expected_sha256": expected_sha, "ok": actual == expected_sha}
        if actual != expected_sha:
            mismatches.append({"kind": kind, "path": shown, "error": "sha256",
                               "expected_sha256": expected_sha, "actual_sha256": actual})
        if expected_rows is not None:
            rows = _count_rows(p)
            item["rows"], item["expected_rows"] = rows, int(expected_rows)
            if rows != int(expected_rows):
                item["ok"] = False
                mismatches.append({"kind": kind, "path": shown, "error": "broj redova",
                                   "expected_rows": int(expected_rows), "actual_rows": rows})
        checks.append(item)

    for d in release.get("datasets", []):
        manifest_path = d.get("manifest") or (out / d["name"] / "manifest.json").as_posix()
        mp = _resolve(repo, manifest_path)
        data_file = out / d["name"] / "data.jsonl"
        if mp.exists():
            man = json.loads(mp.read_text(encoding="utf-8"))
            if man.get("data"):
                data_file = _resolve(repo, man["data"])
            if man.get("data_sha256") != d["sha256"]:
                mismatches.append({"kind": "manifest", "path": str(manifest_path),
                                   "error": "data_sha256 se ne slaze sa RELEASE.json",
                                   "expected_sha256": d["sha256"],
                                   "actual_sha256": man.get("data_sha256")})
            if int((man.get("counts") or {}).get("rows", -1)) != int(d.get("rows", -2)):
                mismatches.append({"kind": "manifest", "path": str(manifest_path),
                                   "error": "counts.rows se ne slaze sa RELEASE.json"})
        else:
            mismatches.append({"kind": "manifest", "path": str(manifest_path),
                               "error": "nema manifest.json"})
        check("dataset", data_file, d["sha256"], d.get("rows"))

    for b in release.get("benchmarks", []):
        check("benchmark", b["path"], b["sha256"], b.get("rows"))

    for r in release.get("benchmark_results", []):
        check("benchmark_result", out / "benchmarks" / "results" / r["file"], r["sha256"])

    total = sum(int(d.get("rows") or 0) for d in release.get("datasets", []))
    if release.get("total_rows") != total:
        mismatches.append({"kind": "release", "path": str(release_path), "error": "total_rows",
                           "expected_rows": int(release.get("total_rows") or 0),
                           "actual_rows": total})

    return {"ok": not mismatches, "version": version, "files": len(checks),
            "total_rows": total, "checks": checks, "mismatches": mismatches}
