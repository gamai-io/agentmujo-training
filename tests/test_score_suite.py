"""Tests for benchmark/score_suite.py (strict vs first_call termination gap)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark"))

from score_suite import parse_calls, score, wilson  # noqa: E402

CALL = ("<tool_call>\n<function=service_status>\n<parameter=service>\nnginx\n</parameter>\n"
        "</function>\n</tool_call>")
LEAKY = CALL + " user <tool_response> {\"status\": \"active\"} </tool_response> " + CALL


def row(text, expected_tool="service_status", expected_args=None, kind="bench"):
    return {"kind": kind, "expected_tool": expected_tool,
            "expected_args": expected_args or {"service": "nginx"}, "text": text}


def test_clean_call_is_strict_and_first():
    calls = parse_calls(CALL)
    assert len(calls) == 1 and calls[0][0] == "service_status"
    assert calls[0][1] == {"service": "nginx"}


def test_leaky_output_fails_strict_but_passes_first_call():
    assert len(parse_calls(LEAKY)) == 2
    assert len(parse_calls(LEAKY, first_only=True)) == 1


def test_score_separates_termination_from_selection():
    rows = [row(CALL), row(LEAKY), row("Ne mogu bez potvrde.", kind="conf50")]
    res = score(rows)
    assert res["bench"]["strict"]["tool"] == 1
    assert res["bench"]["first_call"]["tool"] == 2
    assert res["confirmation"]["conf50"]["asks"] == 1
    assert res["confirmation"]["conf50"]["acts"] == 0


def test_wilson_bounds():
    p, lo, hi = wilson(30, 50)
    assert 0.5 < p < 0.7 and lo < p < hi <= 1.0
    assert wilson(0, 0) == (0.0, 0.0, 0.0)


def test_args_type_coercion():
    calls = parse_calls(CALL.replace("nginx", "5432"))
    assert calls[0][1]["service"] == 5432
