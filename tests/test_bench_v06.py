import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "benchmark" / "cases_v0.6.jsonl"
RUNNER = ROOT / "src" / "agentmujo_training" / "benchmark" / "runner.py"
MOD = "amj_bench_runner_under_test"


def _runner():
    spec = importlib.util.spec_from_file_location(MOD, RUNNER)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MOD] = mod
    spec.loader.exec_module(mod)
    return mod


def _rows():
    return [json.loads(x) for x in CASES.read_text(encoding="utf-8").splitlines() if x.strip()]


def test_bench_v06_has_49_cases_over_all_16_categories():
    rows = _rows()
    m = _runner()
    assert len(rows) == 49
    assert len({r["id"] for r in rows}) == 49
    assert len({r["category"] for r in rows}) == 16
    assert {r["category"] for r in rows} == set(m.CATEGORIES)
    fields = set(m.BenchCase.__dataclass_fields__)
    for r in rows:
        assert not (set(r) - fields), f"{r['id']} has unknown fields"
        assert r["prompt"].strip()


def test_bench_v06_gold_predictions_pass():
    m = _runner()
    cases = m.load_cases(CASES)
    bad = []
    for c in cases:
        if c.expected_tool is not None:
            s = m.score_prediction(c, c.expected_tool, c.expected_args, "")
        elif c.expect_refusal:
            s = m.score_prediction(c, None, None, "Ne mogu to uraditi bez odobrenja.")
        elif c.expect_confirmation:
            s = m.score_prediction(c, None, None, "Molim potvrdu prije izvrsenja.")
        elif c.expect_no_tool:
            s = m.score_prediction(c, None, None, "HTTP je protokol.")
        elif c.forbidden_tool:
            s = m.score_prediction(c, c.expected_tool, None, "")
        elif c.check_ijekavica:
            s = m.score_prediction(c, None, None, "Konfiguracija se nalazi u direktoriju.")
        else:
            s = {}
        if any(v == 0 for v in s.values()):
            bad.append((c.id, s))
    assert not bad, bad[:5]


def test_bench_v06_does_not_overlap_training_literally():
    def norm(s):
        return re.sub(r"[^a-z0-9cczsd]+", " ", s.lower()).strip()

    train = set()
    for p in sorted((ROOT / "datasets" / "canonical").glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            for k in ("prompt", "instruction", "text", "question", "input", "user"):
                v = d.get(k)
                if isinstance(v, str) and v.strip():
                    train.add(norm(v))
            for msg in d.get("messages") or []:
                if isinstance(msg, dict) and msg.get("role") == "user" and isinstance(msg.get("content"), str):
                    train.add(norm(msg["content"]))
    leaked = [r["prompt"] for r in _rows() if norm(r["prompt"]) in train]
    assert not leaked, leaked[:3]
