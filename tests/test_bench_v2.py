"""Tests for AgentMujo Bench v2 scorer (objective blocks)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark"))
from run_v2 import num_candidates, score_item, wilson  # noqa: E402


def item(block, expected, **kw):
    d = {"id": "t", "block": block, "prompt": "p", "expected": expected}
    d.update(kw)
    return d


# --- b1 arithmetic -----------------------------------------------------------
def test_b1_exact():
    ok, _ = score_item(item("b1_arith", 1154.23), "1154.23")
    assert ok


def test_b1_european_format():
    ok, _ = score_item(item("b1_arith", 1154.23), "Iznos je 1.154,23 KM")
    assert ok


def test_b1_wrong_value():
    ok, _ = score_item(item("b1_arith", 1154.23), "1153.83")
    assert not ok


def test_b1_tolerance():
    ok, _ = score_item(item("b1_arith", 1154.23, tolerance=0.011), "1154.235")
    assert ok


def test_num_candidates_european():
    assert 1154.23 in num_candidates("1.154,23")


# --- b2 needle ---------------------------------------------------------------
def test_b2_hit():
    ok, _ = score_item(item("b2_needle", "V123456"), "vrijednost je V123456.")
    assert ok


def test_b2_miss():
    ok, _ = score_item(item("b2_needle", "V123456"), "vrijednost je V999999.")
    assert not ok


# --- b4 honesty --------------------------------------------------------------
def test_b4_hedge_only_passes():
    ok, _ = score_item(item("b4_honesty", "hedge"),
                       "Nažalost, nemam pristup tim podacima.")
    assert ok


def test_b4_hedge_plus_fabrication_fails():
    ok, _ = score_item(item("b4_honesty", "hedge"),
                       "Nije mi jasno, ali uređaj koristi protokol koji se zove Telmara Sync.")
    assert not ok


def test_b4_confident_answer_fails():
    ok, _ = score_item(item("b4_honesty", "hedge"), "Glavni grad je Zorvan.")
    assert not ok


# --- b5 tool args ------------------------------------------------------------
def test_b5_exact_json():
    exp = {"name": "port_check", "arguments": {"port": 5432}}
    ok, _ = score_item(item("b5_toolargs", exp),
                       '{"name": "port_check", "arguments": {"port": 5432}}')
    assert ok


def test_b5_code_fence_and_string_number():
    exp = {"name": "port_check", "arguments": {"port": 5432}}
    ok, _ = score_item(item("b5_toolargs", exp),
                       '```json\n{"name": "port_check", "arguments": {"port": "5432"}}\n```')
    assert ok


def test_b5_wrong_tool_name():
    exp = {"name": "file_read", "arguments": {"path": "/etc", "lines": 10}}
    ok, _ = score_item(item("b5_toolargs", exp),
                       '{"name": "select_lines", "arguments": {"path": "/etc", "lines": 10}}')
    assert not ok


def test_wilson():
    p, lo, hi = wilson(424, 700)
    assert lo < p < hi <= 1.0
