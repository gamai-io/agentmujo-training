"""Three-valued evidence gate (PASS / FAIL / ABSTAIN), fail-closed.

Why this exists: the harness's earlier verifier returned a boolean and defaulted unknown
tools to PASS. A check that cannot be performed is not a success. This module ports the
cascade idea (gama_verify_cascade) into the training repo with one rule:

    no evidence  ->  ABSTAIN, never PASS

Aggregation
    any FAIL        -> FAIL
    else any ABSTAIN -> ABSTAIN
    all PASS (and at least one check) -> PASS
    no claims at all -> ABSTAIN

Evidence kinds are offline and deterministic: file, text, run, sql, http, json.
Unknown kinds ABSTAIN (fail-closed), they never pass.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterable

PASS, FAIL, ABSTAIN = "pass", "fail", "abstain"


@dataclass(frozen=True)
class Claim:
    """A statement that must be backed by evidence."""
    text: str
    kind: str
    expect: dict = field(default_factory=dict)
    id: str = ""


@dataclass(frozen=True)
class Check:
    claim: str
    verdict: str
    reason: str
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GateResult:
    verdict: str
    reason: str
    checks: tuple = ()
    n_pass: int = 0
    n_fail: int = 0
    n_abstain: int = 0

    @property
    def ok(self) -> bool:
        return self.verdict == PASS


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _check_file(claim: Claim, artifacts: dict) -> Check:
    exp = claim.expect
    path = exp.get("path") or artifacts.get("path")
    if not path:
        return Check(claim.text, ABSTAIN, "no path given, cannot check")
    if exp.get("exists") is False:
        return Check(claim.text, PASS if not os.path.exists(path) else FAIL,
                     "expected absent" if not os.path.exists(path) else "file exists",
                     {"path": path})
    if not os.path.exists(path):
        return Check(claim.text, FAIL, "claimed artifact does not exist", {"path": path})
    try:
        size = os.path.getsize(path)
        sha = _sha256(path)
    except OSError as e:
        return Check(claim.text, ABSTAIN, f"cannot read artifact: {e}", {"path": path})
    want_sha = exp.get("sha256")
    if want_sha and sha != want_sha:
        return Check(claim.text, FAIL, "sha256 mismatch", {"path": path, "sha256": sha,
                                                          "expected": want_sha})
    min_bytes = exp.get("min_bytes")
    if min_bytes is not None and size < int(min_bytes):
        return Check(claim.text, FAIL, "artifact smaller than claimed",
                     {"path": path, "bytes": size, "min_bytes": min_bytes})
    return Check(claim.text, PASS, "artifact present",
                 {"path": path, "bytes": size, "sha256": sha})


def _check_text(claim: Claim, artifacts: dict) -> Check:
    body = artifacts.get("text")
    if body is None:
        return Check(claim.text, ABSTAIN, "no text supplied")
    contains = claim.expect.get("contains")
    equals = claim.expect.get("equals")
    if equals is not None:
        return Check(claim.text, PASS if body == equals else FAIL, "text equality",
                     {"len": len(body)})
    if contains:
        missing = [c for c in ([contains] if isinstance(contains, str) else contains)
                   if c not in body]
        return Check(claim.text, FAIL if missing else PASS,
                     f"missing: {missing}" if missing else "all substrings present",
                     {"len": len(body), "missing": missing})
    return Check(claim.text, ABSTAIN, "claim has no testable expectation")


def _check_run(claim: Claim, artifacts: dict) -> Check:
    run = artifacts.get("run")
    if not isinstance(run, dict) or "exit_code" not in run:
        return Check(claim.text, ABSTAIN, "no run record with exit_code")
    want = claim.expect.get("exit_code", 0)
    got = run["exit_code"]
    if got is None:
        return Check(claim.text, ABSTAIN, "exit_code unknown (not observed)")
    return Check(claim.text, PASS if got == want else FAIL,
                 f"exit_code {got} (expected {want})", {"exit_code": got})


def _check_sql(claim: Claim, artifacts: dict) -> Check:
    sql = artifacts.get("sql")
    if not isinstance(sql, dict):
        return Check(claim.text, ABSTAIN, "no sql record")
    if sql.get("error"):
        return Check(claim.text, ABSTAIN, f"sql error: {sql['error']}")
    if "rowcount" not in sql:
        return Check(claim.text, ABSTAIN, "rowcount not observed")
    want = claim.expect.get("rowcount")
    if want is None:
        return Check(claim.text, ABSTAIN, "claim has no rowcount expectation")
    return Check(claim.text, PASS if sql["rowcount"] == want else FAIL,
                 f"rowcount {sql['rowcount']} (expected {want})",
                 {"rowcount": sql["rowcount"]})


def _check_http(claim: Claim, artifacts: dict) -> Check:
    http = artifacts.get("http")
    if not isinstance(http, dict) or "status" not in http:
        return Check(claim.text, ABSTAIN, "no http record")
    want = claim.expect.get("status", 200)
    return Check(claim.text, PASS if http["status"] == want else FAIL,
                 f"http {http['status']} (expected {want})", {"status": http["status"]})


def _check_json(claim: Claim, artifacts: dict) -> Check:
    body = artifacts.get("json")
    if body is None:
        return Check(claim.text, ABSTAIN, "no json record")
    key = claim.expect.get("key")
    if key is None:
        return Check(claim.text, ABSTAIN, "claim has no key expectation")
    got = body
    for part in str(key).split("."):
        if not isinstance(got, dict) or part not in got:
            return Check(claim.text, ABSTAIN, f"key {key} missing in json")
        got = got[part]
    want = claim.expect.get("equals")
    if want is None:
        return Check(claim.text, ABSTAIN, "claim has no value expectation")
    return Check(claim.text, PASS if got == want else FAIL,
                 f"{key}={got!r} (expected {want!r})", {"value": got})


CHECKERS = {
    "file": _check_file,
    "text": _check_text,
    "run": _check_run,
    "sql": _check_sql,
    "http": _check_http,
    "json": _check_json,
}


def evaluate(claim: Claim, artifacts: dict | None = None) -> Check:
    artifacts = artifacts or {}
    fn = CHECKERS.get(claim.kind)
    if fn is None:
        return Check(claim.text, ABSTAIN, f"unknown evidence kind: {claim.kind!r}")
    try:
        return fn(claim, artifacts)
    except Exception as e:  # a broken checker is not a pass
        return Check(claim.text, ABSTAIN, f"checker error: {type(e).__name__}: {e}")


def gate(claims: Iterable[Claim], artifacts: dict | None = None) -> GateResult:
    claims = list(claims or [])
    artifacts = artifacts or {}
    if not claims:
        return GateResult(ABSTAIN, "no claims to verify", (), 0, 0, 0)
    checks = tuple(evaluate(c, artifacts) for c in claims)
    n_pass = sum(c.verdict == PASS for c in checks)
    n_fail = sum(c.verdict == FAIL for c in checks)
    n_abstain = sum(c.verdict == ABSTAIN for c in checks)
    if n_fail:
        return GateResult(FAIL, f"{n_fail} failed check(s)", checks, n_pass, n_fail, n_abstain)
    if n_abstain:
        return GateResult(ABSTAIN, f"{n_abstain} unverifiable check(s)", checks,
                          n_pass, n_fail, n_abstain)
    return GateResult(PASS, f"all {n_pass} checks passed", checks, n_pass, n_fail, n_abstain)


def claims_from_dicts(items) -> list:
    out = []
    for i, it in enumerate(items or []):
        out.append(Claim(text=it.get("text", ""), kind=it.get("kind", ""),
                         expect=it.get("expect") or {}, id=it.get("id") or f"c{i}"))
    return out
