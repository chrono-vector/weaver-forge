#!/usr/bin/env python3
"""Validate daily receipt Markdown files in receipts/."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "## What I built / shipped today",
    "## Evidence",
    "## What this proves",
    "## What this does NOT prove",
    "## Next step",
]

HEADING_PATTERN = re.compile(r"^##\s+(.+)$", re.MULTILINE)
COMMIT_PATTERN = re.compile(r"Commit:\s*\S+")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def validate_receipt(path: Path) -> list[str]:
    """Return a list of missing requirements for a receipt file."""
    missing: list[str] = []
    text = path.read_text(encoding="utf-8")

    headings = {f"## {match.group(1).strip()}" for match in HEADING_PATTERN.finditer(text)}
    for section in REQUIRED_SECTIONS:
        if section not in headings:
            missing.append(section)

    if not COMMIT_PATTERN.search(text):
        missing.append("Commit: line")

    return missing


def main() -> int:
    receipts_dir = repo_root() / "receipts"
    if not receipts_dir.is_dir():
        print(f"FAIL: receipts directory not found: {receipts_dir}")
        return 1

    receipt_files = sorted(receipts_dir.glob("*.md"))
    if not receipt_files:
        print("FAIL: no Markdown receipts found in receipts/")
        return 1

    all_passed = True
    for path in receipt_files:
        missing = validate_receipt(path)
        if missing:
            all_passed = False
            fields = ", ".join(missing)
            print(f"FAIL {path.name}: missing {fields}")
        else:
            print(f"PASS {path.name}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
