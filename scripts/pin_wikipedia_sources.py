#!/usr/bin/env python3
"""Pin the Wikipedia revisions behind the wikipedia-derived rows.

The rows were harvested with `generator=random`, so re-running the ingester cannot
reproduce them, and the dataset files carry no revision id. This script records, for
every row, the revision that was current at `retrieved_at` together with the
revision timestamp and MediaWiki's own sha1 of the revision content. Anyone can then
fetch that exact revision and check it against `rev_sha1` without trusting us.

    python3 scripts/pin_wikipedia_sources.py            # fetch and write the manifest
    python3 scripts/pin_wikipedia_sources.py --check    # offline: ids/titles match
    python3 scripts/pin_wikipedia_sources.py --verify   # network: re-fetch rev_sha1

The dataset files are not modified: their hashes are in a published release.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = {
    "knowledge": ROOT / "datasets/canonical/knowledge_wikipedia_bs_v0.2.jsonl",
    "rag": ROOT / "datasets/canonical/rag_wikipedia_bs_v0.2.jsonl",
}
OUT = ROOT / "datasets/manifests/wikipedia_sources_v0.2.json"
API = "https://bs.wikipedia.org/w/api.php"
UA = ("AgentMujoDatasetFactory/0.2 "
      "(https://github.com/gamai-io/agentmujo-training; dataset@agentmujo.ai)")


def title_from_url(url: str) -> str:
    """Titles can contain '/', so take everything after /wiki/, not after the last slash."""
    if not url:
        return ""
    tail = url.split("/wiki/", 1)[-1] if "/wiki/" in url else url.rsplit("/", 1)[-1]
    return urllib.parse.unquote(tail).replace("_", " ").strip()


def title_of(row: dict) -> str:
    return title_from_url((row.get("metadata") or {}).get("url") or "")


def rows() -> dict[str, list[dict]]:
    """RAG rows have no URL: they are derived from a knowledge row, so the source
    title and retrieval date come from that row."""
    knowledge = [json.loads(line) for line in FILES["knowledge"].open(encoding="utf-8") if line.strip()]
    by_id = {r["id"]: r for r in knowledge}
    out = {"knowledge": [{"id": r["id"], "title": title_of(r),
                          "retrieved_at": (r.get("metadata") or {}).get("retrieved_at")}
                         for r in knowledge]}
    rag = []
    for line in FILES["rag"].open(encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        meta = r.get("metadata") or {}
        parent = by_id.get(meta.get("derived_from", ""))
        url = (parent or {}).get("metadata", {}).get("url")
        rag.append({"id": r["id"],
                    "title": title_from_url(url),
                    "retrieved_at": (parent or {}).get("metadata", {}).get("retrieved_at"),
                    "derived_from": meta.get("derived_from")})
    out["rag"] = rag
    return out


def api(params: dict) -> dict:
    params = dict(params, format="json", formatversion="2")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params),
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch(entries: list[dict]) -> list[dict]:
    """Attach the revision current at `retrieved_at` to each entry.

    MediaWiki rejects `rvstart` when several titles are sent in one request
    (invalidparammix), so this is one request per row. Slow, but it is a pinning run,
    not something CI does.
    """
    pinned = []
    for index, entry in enumerate(entries, 1):
        date = entry["retrieved_at"]
        params = {"action": "query", "prop": "revisions", "titles": entry["title"],
                  "rvprop": "ids|timestamp|sha1", "rvlimit": "1", "rvdir": "older",
                  "rvstart": f"{date}T23:59:59Z", "redirects": "1"}
        try:
            data = api(params)
        except Exception as exc:                      # noqa: BLE001 - network
            print(f"{entry['id']}: {exc}", file=sys.stderr)
            entry.update(status="error")
            pinned.append(entry)
            continue
        pages = data.get("query", {}).get("pages") or []
        revs = (pages[0].get("revisions") if pages else None) or []
        if not revs:
            entry.update(status="missing")
            print(f"{entry['id']}: no revision for {entry['title']!r}", file=sys.stderr)
        else:
            rev = revs[0]
            entry.update(revid=rev["revid"], rev_timestamp=rev["timestamp"],
                         rev_sha1=rev["sha1"], status="pinned")
        pinned.append(entry)
        if index % 50 == 0:
            print(f"  {index}/{len(entries)}", file=sys.stderr)
        time.sleep(0.15)
    return pinned


def verify(manifest: dict) -> int:
    bad = 0
    revids = [e["revid"] for group in manifest["files"].values() for e in group]
    for start in range(0, len(revids), 25):
        batch = revids[start:start + 25]
        data = api({"action": "query", "prop": "revisions", "revids": "|".join(map(str, batch)),
                    "rvprop": "ids|timestamp|sha1"})
        seen = {}
        for page in (data.get("query", {}).get("pages") or []):
            for rev in page.get("revisions") or []:
                seen[rev["revid"]] = rev
        for entry in (e for group in manifest["files"].values() for e in group
                      if e["revid"] in batch):
            rev = seen.get(entry["revid"])
            if rev is None or rev["sha1"] != entry["rev_sha1"]:
                print(f"revision {entry['revid']} does not match the manifest", file=sys.stderr)
                bad += 1
        time.sleep(0.2)
    print(f"verified {len(revids)} revisions, {bad} mismatches")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="offline: manifest covers every row")
    ap.add_argument("--verify", action="store_true", help="network: re-fetch rev_sha1")
    args = ap.parse_args(argv[1:])
    local = rows()
    if args.check or args.verify:
        manifest = json.loads(OUT.read_text(encoding="utf-8"))
        problems = 0
        for name, entries in local.items():
            pinned = {e["id"]: e for e in manifest["files"].get(name, [])}
            if len(pinned) != len(entries):
                print(f"{name}: manifest has {len(pinned)} entries, file has {len(entries)}")
                problems += 1
            for entry in entries:
                p = pinned.get(entry["id"])
                if p is None or p["title"] != entry["title"]:
                    print(f"{name}:{entry['id']} title mismatch or missing")
                    problems += 1
                elif not p.get("revid") or not p.get("rev_sha1"):
                    print(f"{name}:{entry['id']} has no pinned revision")
                    problems += 1
        print(f"coverage: {sum(len(v) for v in local.values())} rows, {problems} problems")
        if problems:
            return 1
        return verify(manifest) if args.verify else 0

    manifest = {"version": "0.2", "api": API,
                "note": "Revision current at retrieved_at; rev_sha1 is MediaWiki's own "
                        "content hash, so the source can be re-checked without trusting us.",
                "files": {}}
    for name, entries in local.items():
        manifest["files"][name] = fetch(entries)
        print(f"{name}: {len(manifest['files'][name])} rows pinned")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
