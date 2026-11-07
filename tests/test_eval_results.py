import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks" / "results"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _load():
    files = sorted(RESULTS.glob("*.json"))
    assert len(files) >= 2
    return files


def test_agentic_eval_results():
    """Legacy tool-selection results keep their strict schema."""
    seen = 0
    for f in _load():
        d = json.loads(f.read_text(encoding="utf-8"))
        if "benchmark" not in d:
            continue
        seen += 1
        assert d["benchmark"] == "agentic_eval_v0.1"
        assert d["mode"] == "tool-selection-only"
        assert d["total"] == 50
        assert d["passed"] + d["failed"] == 50
        assert "model" in d and "by_category" in d
    assert seen >= 2


def test_lumi_devset_results_schema():
    """LUMI development-set reports carry denominators and provenance."""
    seen = 0
    for f in _load():
        d = json.loads(f.read_text(encoding="utf-8"))
        if "benchmark" in d:
            continue
        seen += 1
        assert d["title"] and d["date"] and d["status"]
        rows = d["results"]
        assert rows, f"{f.name}: empty results"
        for r in rows:
            assert 0 <= r["tool_ok"] <= r["n"]
            assert 0 <= r["parse_ok"] <= r["n"]
            assert r["args_ok"] <= r["args_n"] <= r["n"]
            assert r["tool_ci95"][0] <= r["tool_ci95"][1] <= 1.0
        for h in d.get("source_summary_sha256", {}).values():
            assert SHA256.match(h), f"{f.name}: bad source hash"
        assert d.get("limitations") or d.get("caveats"), f"{f.name}: no limitations"


def test_no_private_content_in_results():
    """Published reports are aggregates only: no prompts, hosts or identifiers."""
    banned = ("prompt", "customer", "invoice_id", "/home/", "BEGIN OPENSSH", "192.168.")
    for f in _load():
        text = f.read_text(encoding="utf-8").lower()
        for b in banned:
            assert b not in text, f"{f.name}: contains {b!r}"
