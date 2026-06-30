#!/usr/bin/env python3
"""Validate daily receipt Markdown files in receipts/."""

from __future__ import annotations

import re
import subprocess
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
COMMIT_LINE_PATTERN = re.compile(r"^(?:-\s+)?Commit:\s*(.*)$", re.MULTILINE)
HASH_PATTERN = re.compile(r"^[0-9a-fA-F]{4,40}$")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def extract_commit_hashes(text: str) -> list[str | None]:
    """Return one entry per Commit: line; None when the line has no valid hash."""
    hashes: list[str | None] = []
    for match in COMMIT_LINE_PATTERN.finditer(text):
        value = match.group(1).strip()
        if not value:
            hashes.append(None)
            continue
        token = value.split()[0]
        if HASH_PATTERN.fullmatch(token):
            hashes.append(token)
        else:
            hashes.append(None)
    return hashes


def commit_exists(commit_hash: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit_hash}^{{commit}}"],
        cwd=repo_root(),
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def validate_receipt(path: Path) -> tuple[list[str], list[str]]:
    """Return missing requirements and invalid commit hashes for a receipt file."""
    missing: list[str] = []
    invalid_commits: list[str] = []
    text = path.read_text(encoding="utf-8")

    headings = {f"## {match.group(1).strip()}" for match in HEADING_PATTERN.finditer(text)}
    for section in REQUIRED_SECTIONS:
        if section not in headings:
            missing.append(section)

    commit_hashes = extract_commit_hashes(text)
    if not commit_hashes:
        missing.append("Commit: line")
    else:
        for commit_hash in commit_hashes:
            if commit_hash is None:
                invalid_commits.append("(missing)")
            elif not commit_exists(commit_hash):
                invalid_commits.append(commit_hash)

    return missing, invalid_commits


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
        missing, invalid_commits = validate_receipt(path)
        if missing or invalid_commits:
            all_passed = False
            if missing:
                fields = ", ".join(missing)
                print(f"FAIL {path.name}: missing {fields}")
            for commit_hash in invalid_commits:
                print(f"FAIL {path.name}")
                print(f"Invalid commit: {commit_hash}")
        else:
            print(f"PASS {path.name}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
