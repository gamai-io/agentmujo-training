import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COPIES = [
    ROOT / "benchmarks" / "agentic_eval_v0.1.jsonl",
    ROOT / "releases" / "v0.3.0" / "benchmarks" / "agentic_eval_v0.1.jsonl",
    ROOT / "releases" / "v0.4.0" / "benchmarks" / "agentic_eval_v0.1.jsonl",
]
FORBIDDEN = {"goal", "messages", "success_criteria", "verification", "content", "tool_calls"}
BANNED = ("BEGIN OPENSSH", "192.168.", "/home/", "ghp_", "github_pat_", "hf_")


def test_all_benchmark_copies_are_redacted_and_identical():
    digests = set()
    for p in COPIES:
        text = p.read_text(encoding="utf-8")
        digests.add(hashlib.sha256(text.encode()).hexdigest())
        rows = [json.loads(x) for x in text.splitlines() if x.strip()]
        assert len(rows) == 50, p
        for r in rows:
            assert not FORBIDDEN & set(r), f"{p}: {r['id']} leaks item text"
            assert r["withheld"] is True and r["metadata"]["held_out"] is False
    assert len(digests) == 1, "release copies diverged from the redacted benchmark"


def test_published_results_are_aggregate_only():
    files = sorted((ROOT / "benchmarks" / "results").glob("*.json"))
    files += sorted((ROOT / "releases" / "v0.4.0" / "benchmarks" / "results").glob("*.json"))
    assert files
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        rows = d.get("results")
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            assert not FORBIDDEN & set(r), f"{f.name}: item leaks {sorted(FORBIDDEN & set(r))}"
            for v in r.values():
                if isinstance(v, str):
                    assert len(v) <= 200, f"{f.name}: long free text ({len(v)})"
        text = f.read_text(encoding="utf-8")
        for b in BANNED:
            assert b not in text, f"{f.name}: contains {b!r}"
