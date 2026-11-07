import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_agentic_eval.py"
FORBIDDEN = {"goal", "messages", "success_criteria", "verification", "content", "tool_calls", "refusal"}


def _load():
    spec = importlib.util.spec_from_file_location("run_agentic_eval", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_result_rows_are_aggregate_only():
    mod = _load()
    item = {
        "id": "amj-ev2-0001", "category": "sql", "difficulty": "easy",
        "expected_tools": ["sql"], "goal": "SECRET TASK TEXT",
        "messages": [{"role": "user", "content": "SECRET"}],
        "success_criteria": "SECRET", "verification": "SECRET",
        "metadata": {"private": True},
    }
    row = mod._row(item, ["sql"], [], [], True, 1.23, None)
    assert not FORBIDDEN & set(row), sorted(FORBIDDEN & set(row))
    assert "SECRET" not in json.dumps(row)
    assert row["id"] == "amj-ev2-0001" and row["pass"] is True


def test_script_never_spreads_item_into_results():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "{**item" not in text, "results must not be built by spreading the item"
    assert "def _row(" in text
