import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_eval_results_present():
    files = sorted((ROOT / "benchmarks" / "results").glob("*.json"))
    assert len(files) >= 2
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["benchmark"] == "agentic_eval_v0.1"
        assert d["mode"] == "tool-selection-only"
        assert d["total"] == 50
        assert d["passed"] + d["failed"] == 50
        assert "model" in d and "by_category" in d
