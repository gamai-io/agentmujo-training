import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "benchmarks" / "holdout_v0.2.manifest.json"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_KEYS = {"goal", "messages", "success_criteria", "verification", "prompt"}
SKIP_SUBTREES = {"categories"}


def _keys(obj, skip=SKIP_SUBTREES):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip:
                continue
            yield k
            yield from _keys(v, skip)
    elif isinstance(obj, list):
        for v in obj:
            yield from _keys(v, skip)


def test_holdout_manifest_is_metadata_only():
    d = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert d["benchmark"] == "agentic_eval_v0.2"
    assert d["status"] == "private-holdout"
    assert d["items"] == 60
    assert len(d["ids"]) == 60 and len(set(d["ids"])) == 60
    assert all(i.startswith("amj-ev2-") for i in d["ids"])
    assert sum(d["categories"].values()) == 60
    assert len(d["categories"]) == 10
    assert all(v == 6 for v in d["categories"].values())
    assert SHA256.match(d["sha256"])
    assert d["bytes"] > 0
    leaked = set(_keys(d)) & FORBIDDEN_KEYS
    assert not leaked, f"manifest has item-text keys: {sorted(leaked)}"


def test_holdout_items_are_not_in_repository():
    ids = json.loads(MANIFEST.read_text(encoding="utf-8"))["ids"]
    hits = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts:
            continue
        if p.suffix.lower() not in {".json", ".jsonl", ".md", ".py", ".txt", ".yaml", ".yml"}:
            continue
        if p == MANIFEST:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i in ids:
            if i in text:
                hits.append((str(p.relative_to(ROOT)), i))
    assert not hits, f"holdout ids leaked outside the manifest: {hits[:5]}"
