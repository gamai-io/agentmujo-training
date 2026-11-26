#!/usr/bin/env python3
"""Fail on personal data or credentials in a dataset repository.

The dataset is public and Apache-2.0. Three things must never appear in it:
real e-mail addresses, personal identifiers (JMBG, IBAN), and credentials.
Placeholder addresses on `example.com`/`example.org`/`invalid` are allowed and
are what the synthetic rows use.

Usage:
    python3 tools/pii_scan.py [paths...]      # default: datasets/ releases/ docs/ tests/
Exit codes: 0 clean, 1 findings, 2 nothing to scan.
"""
from __future__ import annotations

import pathlib
import re
import sys

DEFAULT_PATHS = ("datasets", "releases", "docs", "tests", "benchmarks", "benchmark", "README.md")

# Placeholder domains used by the synthetic rows, plus the project's own published
# contact addresses (they are deliberately in the docs, not leaked customer data).
ALLOWED_DOMAINS = ("example.com", "example.org", "example.net", "example.invalid",
                   "invalid", "gamai.io", "gamatrade.ba")

PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
    "jmbg": re.compile(r"\b\d{13}\b"),
    "iban": re.compile(r"\bBA\d{2}\s?(?:\d{3}\s?){5}\d{2}\b"),
    "private_key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    "api_key": re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16})\b"),
    "password_literal": re.compile(r"(?i)\b(?:password|lozinka|l.ozinka)\s*[:=]\s*['\"][^'\"]{6,}['\"]"),
}

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", "dist", "build"}
SKIP_SUFFIX = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".gguf", ".safetensors", ".bin"}
MAX_BYTES = 4_000_000


def scan_file(path: pathlib.Path) -> list[tuple[int, str, str]]:
    hits = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        for name, rx in PATTERNS.items():
            for match in rx.finditer(line):
                value = match.group(0)
                if name == "email" and match.group(1).lower() in ALLOWED_DOMAINS:
                    continue
                if name == "jmbg" and not _looks_like_jmbg(value):
                    continue
                hits.append((lineno, name, value[:80]))
    return hits


def _looks_like_jmbg(value: str) -> bool:
    """A JMBG starts with a valid date (ddmmYYY) and is not an ordinary 13-digit number."""
    day, month, year = int(value[0:2]), int(value[2:4]), int(value[4:7])
    if year >= 800:      # 3-digit year code: 996 -> 1996
        year += 1000
    elif year < 100:
        year += 2000
    return 1 <= day <= 31 and 1 <= month <= 12 and value[12].isdigit()


def iter_files(targets: list[pathlib.Path]):
    for target in targets:
        if target.is_file():
            yield target
            continue
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in SKIP_SUFFIX or path.stat().st_size > MAX_BYTES:
                continue
            yield path


def main(argv: list[str]) -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    targets = [root / a for a in argv[1:]] or [root / p for p in DEFAULT_PATHS]
    found = 0
    scanned = 0
    for path in iter_files(targets):
        scanned += 1
        for lineno, kind, value in scan_file(path):
            found += 1
            try:
                shown = path.relative_to(root)
            except ValueError:
                shown = path
            print(f"{shown}:{lineno}: {kind}: {value}")
    if not scanned:
        print("nothing to scan", file=sys.stderr)
        return 2
    print(f"scanned {scanned} files, {found} findings")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
