import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "benchmarks" / "agentic_eval_v0.1.jsonl"
FORBIDDEN = {"goal", "messages", "success_criteria", "verification"}


def _rows():
    return [json.loads(x) for x in BENCH.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_agentic_eval_benchmark_file():
    rows = _rows()
    assert len(rows) == 50
    assert len({r["id"] for r in rows}) == 50
    assert {r["category"] for r in rows} == {
        "sql", "files", "web", "office", "security", "multi-step",
        "bosnian", "data", "tool-selection", "verification",
    }
    for r in rows:
        assert r["task"] == "agentic-evaluation"
        assert isinstance(r["allowed_tools"], list) and isinstance(r["expected_tools"], list)
        assert not FORBIDDEN & set(r), f"{r['id']} still contains item text"
        assert r["withheld"] is True
        assert r["status"] == "retired-compromised"
        assert r["metadata"]["held_out"] is False
        assert r["metadata"]["public_set"] is True
        assert r["metadata"]["license"] == "Apache-2.0"


def test_agentic_eval_security_requires_no_silent_tool():
    sec = [r for r in _rows() if r["category"] == "security"]
    assert len(sec) == 5
    for r in sec:
        assert r["allowed_tools"] == [] and r["expected_tools"] == []
