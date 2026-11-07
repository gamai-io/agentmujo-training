import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "src" / "agentmujo_training" / "guard" / "risk_gate.py"
MOD = "amj_risk_gate_under_test"


def _gate():
    spec = importlib.util.spec_from_file_location(MOD, MOD_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[MOD] = mod
    spec.loader.exec_module(mod)
    return mod


def test_every_destructive_tool_requires_confirmation():
    mod = _gate()
    gate = mod.RiskGate()
    assert len(mod.DESTRUCTIVE_TOOLS) >= 12
    for tool in sorted(mod.DESTRUCTIVE_TOOLS):
        d = gate.classify(tool, {"x": "y"})
        assert d.verdict == "confirm", tool
        assert d.requires_approval is True


def test_approval_allows_destructive_tool():
    mod = _gate()
    tool = sorted(mod.DESTRUCTIVE_TOOLS)[0]
    gate = mod.RiskGate(approved={tool})
    assert gate.classify(tool, {}).verdict == "allow"


def test_safe_tools_are_allowed():
    mod = _gate()
    gate = mod.RiskGate()
    for tool in ("service_status", "disk_usage", "file_list", "package_query", "port_check"):
        assert gate.classify(tool, {}).verdict == "allow"
        assert gate.classify(tool, {}).requires_approval is False


def test_forbidden_arguments_are_denied_even_when_approved():
    mod = _gate()
    tool = "package_install"
    gate = mod.RiskGate(approved={tool})
    for payload in ("/etc/" + "sha" + "dow", "mk" + "fs.ext4 /dev/sdb", "rm" + " -rf /"):
        d = gate.classify("fs_write", {"path": payload})
        assert d.verdict == "deny", payload


def test_execute_blocks_unapproved_and_runs_approved():
    mod = _gate()
    calls = []

    def runner(tool, args):
        calls.append((tool, args))
        return "done"

    gate = mod.RiskGate()
    r1 = gate.execute("service_restart", {"service": "nginx"}, runner)
    assert r1["executed"] is False and r1["verdict"] == "confirm"
    assert calls == []

    gate2 = mod.RiskGate(approved={"service_restart"})
    r2 = gate2.execute("service_restart", {"service": "nginx"}, runner)
    assert r2["executed"] is True and r2["result"] == "done"
    assert calls == [("service_restart", {"service": "nginx"})]

    r3 = gate2.execute("disk_usage", {"path": "/var"}, runner)
    assert r3["executed"] is True


def test_gate_is_deterministic():
    mod = _gate()
    gate = mod.RiskGate()
    tool = sorted(mod.DESTRUCTIVE_TOOLS)[0]
    verdicts = {gate.classify(tool, {}).verdict for _ in range(100)}
    assert verdicts == {"confirm"}
