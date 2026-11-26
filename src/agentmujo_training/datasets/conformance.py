"""TOOL_CONFORMANCE_V1 — svaki tool poziv u datasetima mora postojati u registryju.

`configs/tools.yaml` je Single Source of Truth, a `policy/engine.py` odbija (deny)
svaki alat koji nije u njemu. Dataset koji poziva neregistrovane alate trenira
model da emitira pozive koje gate odbija — train/serve skew. Ovaj modul to hvata
prije isporuke: imena moraju biti u registryju ili u eksplicitnom allowlistu
(`configs/dataset_tool_allowlist.yaml`, prazan po defaultu), a argumenti moraju
proci `ToolRegistry.validate_call`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml

ALLOWLIST_PATH = "configs/dataset_tool_allowlist.yaml"


def load_allowlist(path: str | Path) -> set[str]:
    p = Path(path)
    if not p.exists():
        return set()
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return {str(x) for x in (data.get("allowed_tools") or [])}


def default_targets(repo: str | Path) -> list[Path]:
    """Kanonski dataseti + svi isporuceni release fajlovi."""
    repo = Path(repo)
    files = sorted((repo / "datasets" / "canonical").glob("*.jsonl"))
    files += sorted((repo / "releases").glob("*/agentmujo-*/data.jsonl"))
    return [p for p in files if p.is_file()]


def _iter_calls(path: Path):
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        for m in row.get("messages") or []:
            if not isinstance(m, dict):
                continue
            for tc in m.get("tool_calls") or []:
                if isinstance(tc, dict):
                    yield n, str(tc.get("name") or ""), tc.get("arguments") or {}


def check_files(paths: Iterable[str | Path], registry, allowlist: set[str] | None = None,
                validate_args: bool = True) -> dict[str, Any]:
    """Vrati {"ok": bool, "files": n, "calls": n, "unknown_tool_calls": n, "violations": [...]}."""
    allowlist = set(allowlist or ())
    known = set(registry.names()) | allowlist
    violations: list[dict[str, Any]] = []
    files = calls = unknown_calls = 0
    for path in paths:
        p = Path(path)
        files += 1
        for line_no, name, arguments in _iter_calls(p):
            calls += 1
            if name not in known:
                unknown_calls += 1
                violations.append({"file": str(p), "line": line_no, "tool": name,
                                   "error": "nepoznat alat (nije u configs/tools.yaml ni u allowlistu)"})
                continue
            if validate_args and registry.get(name) is not None:
                errors = registry.validate_call(name, arguments if isinstance(arguments, dict) else {})
                for e in errors:
                    violations.append({"file": str(p), "line": line_no, "tool": name, "error": e})
    return {"ok": not violations, "files": files, "calls": calls,
            "unknown_tool_calls": unknown_calls, "violation_count": len(violations),
            "violations": violations[:50], "allowlist": sorted(allowlist)}
