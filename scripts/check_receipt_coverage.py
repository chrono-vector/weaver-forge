#!/usr/bin/env python3
"""Report receipt coverage inventory for the current repository.

Enumerates commits on HEAD and Markdown files under receipts/.
Does not assert that every commit has a receipt, or that commit-to-receipt
mapping is complete or enforceable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def list_commits() -> list[str]:
    """Return full commit hashes on HEAD, oldest first (deterministic)."""
    result = subprocess.run(
        ["git", "rev-list", "--reverse", "HEAD"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "git rev-list failed").strip()
        raise RuntimeError(detail)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def latest_commit_summary() -> str:
    """Return short hash and subject for HEAD."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%h %s"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "git log failed").strip()
        raise RuntimeError(detail)
    return result.stdout.strip()


def list_receipts() -> list[Path]:
    """Return receipt Markdown paths, sorted by filename (deterministic)."""
    receipts_dir = repo_root() / "receipts"
    if not receipts_dir.is_dir():
        raise FileNotFoundError(f"receipts directory not found: {receipts_dir}")
    return sorted(receipts_dir.glob("*.md"))


def main() -> int:
    try:
        commits = list_commits()
        receipts = list_receipts()
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}")
        return 1

    latest_commit = latest_commit_summary() if commits else "(none)"
    latest_receipt = receipts[-1].name if receipts else "(none)"

    # Exact commit-to-receipt mapping is not defined or enforced yet.
    coverage_status = "not yet enforceable"

    print("Receipt Coverage Checker")
    print("========================")
    print(f"Total commits:       {len(commits)}")
    print(f"Total receipt files: {len(receipts)}")
    print(f"Latest commit:       {latest_commit}")
    print(f"Latest receipt:      {latest_receipt}")
    print(f"Coverage status:     {coverage_status}")
    print()
    print("Notes:")
    print("- Counts are inventory only (commits on HEAD, *.md under receipts/).")
    print("- Exact commit-to-receipt mapping is not yet enforceable.")
    print("- This report does not claim complete coverage.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
