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


def binding_commit_hash(text: str) -> str | None:
    """Return the first Commit: hash in the receipt (primary binding commit)."""
    for commit_hash in extract_commit_hashes(text):
        if commit_hash is not None:
            return commit_hash
    return None


def commit_exists(commit_hash: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{commit_hash}^{{commit}}"],
        cwd=repo_root(),
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def resolve_commit_hash(commit_hash: str) -> str | None:
    """Return the full commit hash when reachable locally, else None."""
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"{commit_hash}^{{commit}}"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def validate_receipt(path: Path) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return missing sections, missing commit fields, malformed hashes, unreachable hashes."""
    missing_sections: list[str] = []
    missing_commit_fields: list[str] = []
    malformed_hashes: list[str] = []
    unreachable_hashes: list[str] = []
    text = path.read_text(encoding="utf-8")

    headings = {f"## {match.group(1).strip()}" for match in HEADING_PATTERN.finditer(text)}
    for section in REQUIRED_SECTIONS:
        if section not in headings:
            missing_sections.append(section)

    commit_lines = list(COMMIT_LINE_PATTERN.finditer(text))
    if not commit_lines:
        missing_commit_fields.append("Commit: line")
    else:
        for match in commit_lines:
            value = match.group(1).strip()
            if not value:
                missing_commit_fields.append("(empty Commit: line)")
                continue
            token = value.split()[0]
            if not HASH_PATTERN.fullmatch(token):
                malformed_hashes.append(value)
                continue
            if not commit_exists(token):
                unreachable_hashes.append(token)

    return missing_sections, missing_commit_fields, malformed_hashes, unreachable_hashes


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
        missing_sections, missing_commit_fields, malformed_hashes, unreachable_hashes = (
            validate_receipt(path)
        )
        issues = (
            missing_sections
            or missing_commit_fields
            or malformed_hashes
            or unreachable_hashes
        )
        if issues:
            all_passed = False
            if missing_sections:
                fields = ", ".join(missing_sections)
                print(f"FAIL {path.name}: missing {fields}")
            if missing_commit_fields:
                fields = ", ".join(missing_commit_fields)
                print(f"FAIL {path.name}: missing Commit field ({fields})")
            for value in malformed_hashes:
                print(f"FAIL {path.name}: malformed commit hash ({value})")
            for commit_hash in unreachable_hashes:
                print(f"FAIL {path.name}: commit not in git ({commit_hash})")
        else:
            print(f"PASS {path.name}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
