import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "benchmarks" / "results"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FREE_TEXT_KEYS = {"goal", "messages", "tool_calls", "content", "refusal", "success_criteria", "verification"}


def _files():
    files = sorted(RESULTS.glob("*.json"))
    assert len(files) >= 2
    return files


def test_agentic_eval_results():
    """Legacy tool-selection results keep their strict schema."""
    seen = 0
    for f in _files():
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
    for f in _files():
        d = json.loads(f.read_text(encoding="utf-8"))
        if "benchmark" in d:
            continue
        seen += 1
        assert d["title"] and d["date"] and d["status"]
        rows = d["results"]
        assert rows, f"{f.name}: empty results"
        for r in rows:
            assert 0 <= r["tool_ok"] <= r["n"], (f.name, r)
            assert 0 <= r["parse_ok"] <= r["n"], (f.name, r)
            assert 0 <= r["args_exact_ok"] <= r["args_n"] <= r["n"], (f.name, r)
            if r.get("args_casefold_ok") is not None:
                assert r["args_exact_ok"] <= r["args_casefold_ok"] <= r["args_n"], (f.name, r)
            if "tool_ci95" in r:
                lo, hi = r["tool_ci95"]
                assert 0.0 <= lo <= hi <= 1.0, (f.name, r)
        for h in d.get("source_summary_sha256", {}).values():
            assert SHA256.match(h), f"{f.name}: bad source hash"
        assert d.get("limitations") or d.get("caveats"), f"{f.name}: no limitations"
    assert seen >= 2


def test_results_contain_no_free_text_or_held_out_items():
    """Result files are aggregates: no prompts, no held-out item text, no long strings."""
    for f in _files():
        d = json.loads(f.read_text(encoding="utf-8"))
        rows = d.get("results")
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            leaked = FREE_TEXT_KEYS & set(r)
            assert not leaked, f"{f.name}: item has {sorted(leaked)}"
            for v in r.values():
                if isinstance(v, str):
                    assert len(v) <= 200, f"{f.name}: long free-text value ({len(v)})"


def test_no_host_or_secret_material():
    banned = ("/home/", "BEGIN OPENSSH", "192.168.", "ghp_", "github_pat_", "hf_")
    for f in _files():
        text = f.read_text(encoding="utf-8")
        for b in banned:
            assert b not in text, f"{f.name}: contains {b!r}"
