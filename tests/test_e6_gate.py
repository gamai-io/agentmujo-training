"""Tests for the deterministic E6 invoice gate."""
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "benchmark"))
from e6_gate import detect, run, wilson  # noqa: E402


def invoice(**kw):
    it = {"desc": "Lezaj 6204", "qty": 2, "unit_price": 10.0, "vat_rate": 0.17,
          "line_total": 20.0}
    base = {"id": "inv-test", "items": [it], "subtotal": 20.0,
            "vat_total": 3.40, "total": 23.40, "planted_errors": []}
    base.update(kw)
    return base


def test_clean_invoice_not_flagged():
    assert detect(invoice()) == []


def test_vat_rate_flagged():
    inv = invoice()
    inv["items"][0]["vat_rate"] = 0.20
    assert "vat_rate" in detect(inv)


def test_line_total_flagged():
    inv = invoice()
    inv["items"][0]["line_total"] = 25.0
    assert "line_total" in detect(inv)


def test_subtotal_flagged():
    assert "sum_items" in detect(invoice(subtotal=25.0))


def test_vat_amount_flagged():
    assert "vat_amount" in detect(invoice(vat_total=4.0))


def test_total_flagged():
    assert "total" in detect(invoice(total=30.0))


def test_missing_field_flagged():
    inv = invoice()
    del inv["items"][0]["unit_price"]
    assert "missing_field" in detect(inv)


def test_run_pass_and_fail(tmp_path):
    clean = invoice()
    dirty = invoice()
    dirty["id"] = "inv-dirty"
    dirty["items"][0]["vat_rate"] = 0.20
    dirty["planted_errors"] = [{"kind": "vat_rate"}]
    p = tmp_path / "x.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in [clean, dirty]) + "\n")
    out = run(str(p))
    assert out["n"] == 2 and out["dirty"] == 1 and out["clean"] == 1
    assert out["recall"] == 1.0 and out["false_positive_rate"] == 0.0
    assert out["pass"] is True


def test_wilson_bounds():
    p, lo, hi = wilson(381, 381)
    assert p == 1.0 and lo < 1.0 and hi == 1.0
