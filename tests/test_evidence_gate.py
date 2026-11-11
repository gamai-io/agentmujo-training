"""Tests for the three-valued evidence gate: ABSTAIN is never PASS."""
from __future__ import annotations

import hashlib
import sys

sys.path.insert(0, "src")

import pytest

from agentmujo_training.guard.evidence_gate import (
    ABSTAIN, FAIL, PASS, Claim, claims_from_dicts, evaluate, gate)


@pytest.fixture()
def artifact(tmp_path):
    p = tmp_path / "out.json"
    p.write_text('{"n": 700}', encoding="utf-8")
    return p


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_no_claims_is_abstain():
    r = gate([])
    assert r.verdict == ABSTAIN
    assert not r.ok


def test_unknown_kind_is_abstain():
    r = gate([Claim("x", "quantum_teleport", {})])
    assert r.verdict == ABSTAIN


def test_claim_without_expectation_is_abstain():
    r = gate([Claim("x", "file", {})])
    assert r.verdict == ABSTAIN


def test_file_with_matching_sha_passes(artifact):
    r = gate([Claim("artifact written", "file",
                    {"path": str(artifact), "sha256": sha(artifact)})])
    assert r.verdict == PASS


def test_file_with_wrong_sha_fails(artifact):
    r = gate([Claim("artifact written", "file",
                    {"path": str(artifact), "sha256": "0" * 64})])
    assert r.verdict == FAIL


def test_missing_claimed_file_fails(tmp_path):
    r = gate([Claim("log written", "file", {"path": str(tmp_path / "nope.log")})])
    assert r.verdict == FAIL


def test_expected_absent_file_passes(tmp_path):
    r = gate([Claim("no dump left behind", "file",
                    {"path": str(tmp_path / "dump.bin"), "exists": False})])
    assert r.verdict == PASS


def test_unreadable_path_abstains(tmp_path):
    r = gate([Claim("artifact written", "file", {"path": str(tmp_path)})])
    assert r.verdict == ABSTAIN


def test_run_exit_zero_passes():
    r = gate([Claim("cmd succeeded", "run", {"exit_code": 0})],
             {"run": {"exit_code": 0}})
    assert r.verdict == PASS


def test_run_nonzero_fails():
    r = gate([Claim("cmd succeeded", "run", {"exit_code": 0})],
             {"run": {"exit_code": 2}})
    assert r.verdict == FAIL


def test_run_unobserved_abstains():
    r = gate([Claim("cmd succeeded", "run", {"exit_code": 0})],
             {"run": {"exit_code": None}})
    assert r.verdict == ABSTAIN


def test_missing_run_record_abstains():
    assert gate([Claim("cmd succeeded", "run", {"exit_code": 0})]).verdict == ABSTAIN


def test_sql_rowcount_mismatch_fails():
    r = gate([Claim("deleted 5 rows", "sql", {"rowcount": 5})],
             {"sql": {"rowcount": 0}})
    assert r.verdict == FAIL


def test_sql_error_abstains():
    r = gate([Claim("deleted 5 rows", "sql", {"rowcount": 5})],
             {"sql": {"error": "timeout"}})
    assert r.verdict == ABSTAIN


def test_http_status():
    ok = gate([Claim("service up", "http", {"status": 200})], {"http": {"status": 200}})
    bad = gate([Claim("service up", "http", {"status": 200})], {"http": {"status": 503}})
    none = gate([Claim("service up", "http", {"status": 200})], {})
    assert (ok.verdict, bad.verdict, none.verdict) == (PASS, FAIL, ABSTAIN)


def test_json_nested_key():
    art = {"json": {"result": {"false_success": 0}}}
    assert gate([Claim("fs zero", "json", {"key": "result.false_success", "equals": 0})],
                art).verdict == PASS
    assert gate([Claim("fs zero", "json", {"key": "result.false_success", "equals": 1})],
                art).verdict == FAIL
    assert gate([Claim("fs zero", "json", {"key": "result.missing", "equals": 0})],
                art).verdict == ABSTAIN


def test_text_contains():
    art = {"text": "SMOKE_OK ROCm True"}
    assert gate([Claim("smoke", "text", {"contains": ["SMOKE_OK", "ROCm"]})], art).verdict == PASS
    assert gate([Claim("smoke", "text", {"contains": "CUDA"})], art).verdict == FAIL


def test_mixed_pass_and_abstain_is_abstain(artifact):
    r = gate([Claim("file ok", "file", {"path": str(artifact)}),
              Claim("run ok", "run", {"exit_code": 0})],
             {"run": {}})
    assert r.verdict == ABSTAIN
    assert r.n_pass == 1 and r.n_abstain == 1


def test_fail_dominates_abstain(artifact):
    r = gate([Claim("file wrong", "file", {"path": str(artifact), "sha256": "0" * 64}),
              Claim("run ok", "run", {"exit_code": 0})], {})
    assert r.verdict == FAIL


def test_checker_exception_abstains(monkeypatch):
    import agentmujo_training.guard.evidence_gate as eg

    def boom(claim, artifacts):
        raise RuntimeError("bug")

    monkeypatch.setitem(eg.CHECKERS, "file", boom)
    assert evaluate(Claim("x", "file", {"path": "/tmp"})).verdict == ABSTAIN


def test_claims_from_dicts():
    cs = claims_from_dicts([{"text": "a", "kind": "file", "expect": {"path": "/tmp"}}])
    assert cs[0].kind == "file" and cs[0].id == "c0"
