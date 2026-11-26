"""TOOL_CONFORMANCE_V1 — dataset ne smije trenirati pozive koje policy gate odbija."""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.datasets.conformance import (  # noqa: E402
    ALLOWLIST_PATH, check_files, default_targets, load_allowlist)
from agentmujo_training.policy import PolicyEngine  # noqa: E402
from agentmujo_training.tools import ToolRegistry  # noqa: E402


def _reg():
    return ToolRegistry.from_yaml(REPO / "configs" / "tools.yaml")


def _row(tool, arguments):
    return {"id": "t-1", "version": "0.0.1", "language": "bs", "task": "function-calling",
            "messages": [{"role": "user", "content": "x"},
                         {"role": "assistant", "content": "ok",
                          "tool_calls": [{"name": tool, "arguments": arguments}]}],
            "metadata": {}}


def test_every_dataset_tool_is_registered():
    reg = _reg()
    rep = check_files(default_targets(REPO), reg, load_allowlist(REPO / ALLOWLIST_PATH))
    assert rep["ok"], f"skew: {rep['violations'][:5]}"
    assert rep["unknown_tool_calls"] == 0
    assert rep["calls"] > 1000


def test_allowlist_is_empty_by_default():
    """Konformansa mora prolaziti bez izuzetaka; svaki izuzetak je svjesna odluka."""
    assert load_allowlist(REPO / ALLOWLIST_PATH) == set()


def test_policy_engine_accepts_every_tool_used_in_data():
    """Bas ono sto je bio bug: dataset trenira pozive koje PolicyEngine odbija."""
    reg = _reg()
    engine = PolicyEngine(reg)
    used = set()
    for path in default_targets(REPO):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            for m in json.loads(line).get("messages") or []:
                for tc in m.get("tool_calls") or []:
                    used.add(tc.get("name"))
    assert used
    denied = sorted(t for t in used if engine.decide(t, {}).verdict == "deny")
    assert not denied, f"policy odbija alate iz dataseta: {denied}"


def test_unknown_tool_is_detected(tmp_path):
    p = tmp_path / "skew.jsonl"
    p.write_text(json.dumps(_row("sql", {"query": "SELECT 1"})) + "\n", encoding="utf-8")
    rep = check_files([p], _reg())
    assert not rep["ok"]
    assert rep["unknown_tool_calls"] == 1
    assert "nepoznat alat" in rep["violations"][0]["error"]


def test_bad_arguments_are_detected(tmp_path):
    p = tmp_path / "args.jsonl"
    p.write_text(json.dumps(_row("port_check", {"port": "80"})) + "\n", encoding="utf-8")
    rep = check_files([p], _reg())
    assert not rep["ok"]
    assert any("port" in v["error"] for v in rep["violations"])


def test_allowlist_is_an_explicit_escape_hatch(tmp_path):
    p = tmp_path / "ext.jsonl"
    p.write_text(json.dumps(_row("mcp_ext_tool", {"x": 1})) + "\n", encoding="utf-8")
    assert not check_files([p], _reg())["ok"]
    assert check_files([p], _reg(), {"mcp_ext_tool"})["ok"]  # samo uz eksplicitni allowlist
