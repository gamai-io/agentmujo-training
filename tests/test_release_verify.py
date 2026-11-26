"""RELEASE_VERIFY_V1 — isporuceni release mora biti provjerljiv, bez izuzetaka."""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from agentmujo_training.datasets.release import build_release, release_dir  # noqa: E402
from agentmujo_training.datasets.verify import verify_release  # noqa: E402

VERSION = "0.4.0"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_shipped_release_verifies():
    r = verify_release(REPO, VERSION)
    assert r["ok"], f"RELEASE.json se ne slaze sa isporucenim fajlovima: {r['mismatches']}"
    assert r["files"] >= 13  # 10 dataseta + 1 benchmark + 2 benchmark rezultata
    assert r["total_rows"] == 4496


def test_every_release_json_dataset_hash_matches_file():
    rel = json.loads((release_dir(REPO, VERSION) / "RELEASE.json").read_text(encoding="utf-8"))
    assert rel["datasets"], "release bez dataseta"
    for d in rel["datasets"]:
        data = release_dir(REPO, VERSION) / d["name"] / "data.jsonl"
        assert _sha(data) == d["sha256"], f"{d['name']}: sha256 u RELEASE.json ne odgovara fajlu"


def test_verify_detects_tampered_file(tmp_path):
    rel = tmp_path / "releases" / "v9.9.9"
    ddir = rel / "amj-x"
    ddir.mkdir(parents=True)
    data = ddir / "data.jsonl"
    data.write_text('{"id": "a"}\n', encoding="utf-8")
    sha = _sha(data)
    (ddir / "manifest.json").write_text(
        json.dumps({"name": "amj-x", "version": "9.9.9", "data_sha256": sha,
                    "counts": {"rows": 1}}), encoding="utf-8")
    (rel / "RELEASE.json").write_text(json.dumps({
        "schema": "agentmujo.release.v0", "version": "9.9.9", "total_rows": 1,
        "datasets": [{"name": "amj-x", "rows": 1, "sha256": sha,
                      "manifest": "releases/v9.9.9/amj-x/manifest.json"}],
        "benchmarks": [], "benchmark_results": []}), encoding="utf-8")
    assert verify_release(tmp_path, "9.9.9")["ok"]
    data.write_text('{"id": "b"}\n', encoding="utf-8")  # jedan bajt promijenjen
    r = verify_release(tmp_path, "9.9.9")
    assert not r["ok"]
    assert any(m.get("error") == "sha256" for m in r["mismatches"])


def test_rebuild_reproduces_shipped_hashes(tmp_path):
    """Builder iz izvora mora dati iste hasheve kao isporuceni release (ne rucni patch)."""
    r = build_release(REPO, VERSION, tmp_path / "rel")
    assert r["ok"] and r["total_rows"] == 4496
    shipped = json.loads((release_dir(REPO, VERSION) / "RELEASE.json").read_text(encoding="utf-8"))
    expected = {d["name"]: d["sha256"] for d in shipped["datasets"]}
    assert {d["name"]: d["sha256"] for d in r["datasets"]} == expected
    assert r["errors"] == []
