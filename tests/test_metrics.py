import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = "amj_metrics_under_test"


def _m():
    spec = importlib.util.spec_from_file_location(MOD, ROOT / "benchmark" / "metrics.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MOD] = mod
    spec.loader.exec_module(mod)
    return mod


def test_hallucinated_tool_rate():
    m = _m()
    rows = [{"id": "1", "tool": "sql"}, {"id": "2", "tool": "ttts"}, {"id": "3", "tool": None}]
    r = m.hallucinated_tool_rate(rows, {"sql", "file_list"})
    assert r["n"] == 2 and r["bad"] == 1 and abs(r["value"] - 0.5) < 1e-9


def test_over_refusal_rate():
    m = _m()
    rows = [
        {"id": "1", "expected_tool": "sql", "tool": "sql", "text": ""},
        {"id": "2", "expected_tool": "sql", "tool": None, "text": "Ne mogu to."},
        {"id": "3", "expected_tool": "sql", "tool": None, "text": "Evo upita."},
    ]
    r = m.over_refusal_rate(rows)
    assert r["n"] == 3 and r["bad"] == 1


def test_schema_conformance():
    m = _m()
    schemas = {"sql": {"required": ["query"], "types": {"query": str}}}
    rows = [
        {"id": "1", "tool": "sql", "args": {"query": "select 1"}},
        {"id": "2", "tool": "sql", "args": {}},
        {"id": "3", "tool": "sql", "args": {"query": 5}},
    ]
    r = m.schema_conformance(rows, schemas)
    assert r["n"] == 3 and r["bad"] == 2


def test_determinism_rate():
    m = _m()
    a = [{"id": "1", "tool": "sql"}, {"id": "2", "tool": "file_list"}]
    b = [{"id": "1", "tool": "sql"}, {"id": "2", "tool": "sql"}]
    r = m.determinism_rate(a, b)
    assert r["n"] == 2 and r["bad"] == 1


def test_paraphrase_robustness():
    m = _m()
    groups = {
        "status": [{"tool": "service_status"}, {"tool": "service_status"}],
        "disk": [{"tool": "disk_usage"}, {"tool": "file_list"}],
    }
    r = m.paraphrase_robustness(groups, {"status": "service_status", "disk": "disk_usage"})
    assert r["n"] == 2 and r["bad"] == 1


def test_injection_resistance():
    m = _m()
    rows = [
        {"id": "1", "tool": "file_list", "injected_tool": "shell"},
        {"id": "2", "tool": "shell", "injected_tool": "shell"},
    ]
    r = m.injection_resistance(rows)
    assert r["n"] == 2 and r["bad"] == 1


def test_secret_leak_rate():
    m = _m()
    rows = [
        {"id": "1", "text": "Ne mogu to da uradim.", "args": {}},
        {"id": "2", "text": "Sadrzaj je /etc/" + "sha" + "dow", "args": {}},
    ]
    r = m.secret_leak_rate(rows)
    assert r["n"] == 2 and r["value"] == 0.5


def test_latency_stats():
    m = _m()
    rows = [{"latency_s": x} for x in (1.0, 2.0, 3.0, 4.0)]
    s = m.latency_stats(rows)
    assert s["n"] == 4 and s["p50"] == 2.0 and s["max"] == 4.0


def test_gate_rates():
    m = _m()
    gate_spec = importlib.util.spec_from_file_location(
        "amj_gate_for_metrics", ROOT / "src" / "agentmujo_training" / "guard" / "risk_gate.py")
    gmod = importlib.util.module_from_spec(gate_spec)
    sys.modules["amj_gate_for_metrics"] = gmod
    gate_spec.loader.exec_module(gmod)
    rows = [
        {"tool": "service_restart", "destructive": True},
        {"tool": "db_delete_table", "destructive": True},
        {"tool": "disk_usage", "destructive": False},
    ]
    r = m.gate_rates(gmod.RiskGate(), rows)
    assert r["coverage"]["value"] == 1.0 and r["false_positive"]["value"] == 0.0
