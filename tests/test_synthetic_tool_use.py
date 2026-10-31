import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_synthetic_tool_use_rows():
    rows = [json.loads(x) for x in (ROOT / "datasets" / "canonical" / "function_calling_synthetic_v0.4.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(rows) == 500
    assert len({r["id"] for r in rows}) == 500
    assert {r["metadata"]["focus"] for r in rows} == {"sql","tool-selection","argument-generation","multi-step","verification","data"}
    for r in rows:
        assert r["task"] == "function-calling"
        assert r["metadata"]["synthetic"] is True
        assert r["metadata"]["verification_status"] == "schema-validated"
        assert r["messages"][0]["role"] == "user"
        assert r["messages"][1].get("tool_calls")
