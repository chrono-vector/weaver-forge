#!/usr/bin/env python3
"""Report receipt coverage inventory for the current repository.

Enumerates commits on HEAD and Markdown files under receipts/.
Compares receipt-bound commits against repository history and reports drift.
Does not assert that every commit has a receipt, or that commit-to-receipt
mapping is complete or enforceable.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from validate_receipts import binding_commit_hash, resolve_commit_hash


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


def collect_binding_commits(receipts: list[Path]) -> list[tuple[str, str | None]]:
    """Return (filename, resolved full hash or None) for each receipt binding commit."""
    bindings: list[tuple[str, str | None]] = []
    for path in receipts:
        text = path.read_text(encoding="utf-8")
        raw_hash = binding_commit_hash(text)
        if raw_hash is None:
            bindings.append((path.name, None))
            continue
        bindings.append((path.name, resolve_commit_hash(raw_hash)))
    return bindings


def latest_binding_commit(
    bindings: list[tuple[str, str | None]], commits: list[str]
) -> tuple[str | None, str | None]:
    """Return (receipt filename, full hash) for the newest binding commit on HEAD."""
    commit_index = {commit_hash: index for index, commit_hash in enumerate(commits)}
    latest_name: str | None = None
    latest_hash: str | None = None
    latest_index = -1
    for name, commit_hash in bindings:
        if commit_hash is None:
            continue
        index = commit_index.get(commit_hash)
        if index is None or index <= latest_index:
            continue
        latest_index = index
        latest_name = name
        latest_hash = commit_hash
    return latest_name, latest_hash


def collect_warnings(
    commits: list[str],
    receipts: list[Path],
    bindings: list[tuple[str, str | None]],
) -> list[str]:
    """Return advisory warnings for inventory drift and stale receipt binding."""
    warnings: list[str] = []
    head = commits[-1] if commits else None
    latest_receipt_name, latest_receipt_commit = latest_binding_commit(bindings, commits)

    if len(commits) != len(receipts):
        warnings.append(
            f"Inventory drift: {len(commits)} commits on HEAD vs "
            f"{len(receipts)} receipt files (exact one-to-one mapping not yet enforceable)"
        )

    receipts_without_binding = [name for name, commit_hash in bindings if commit_hash is None]
    if receipts_without_binding:
        names = ", ".join(receipts_without_binding)
        warnings.append(f"Receipts without a resolvable binding commit: {names}")

    if head and latest_receipt_commit and head != latest_receipt_commit:
        head_short = head[:7]
        receipt_short = latest_receipt_commit[:7]
        receipt_label = latest_receipt_name or "(unknown receipt)"
        warnings.append(
            f"HEAD ({head_short}) is newer than the latest receipt binding commit "
            f"({receipt_short} in {receipt_label})"
        )
        try:
            head_index = commits.index(head)
            receipt_index = commits.index(latest_receipt_commit)
            gap = head_index - receipt_index
            if gap > 0:
                warnings.append(
                    f"{gap} commit(s) on HEAD since the latest receipt binding commit "
                    f"(no receipt required for each commit; mapping not yet enforceable)"
                )
        except ValueError:
            pass

    return warnings


def main() -> int:
    try:
        commits = list_commits()
        receipts = list_receipts()
        bindings = collect_binding_commits(receipts)
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"FAIL: {exc}")
        return 1

    latest_commit = latest_commit_summary() if commits else "(none)"
    latest_receipt = receipts[-1].name if receipts else "(none)"
    latest_receipt_name, latest_receipt_commit = latest_binding_commit(bindings, commits)
    if latest_receipt_commit:
        latest_binding = f"{latest_receipt_commit[:7]} ({latest_receipt_name})"
    else:
        latest_binding = "(none)"

    # Exact commit-to-receipt mapping is not defined or enforced yet.
    coverage_status = "not yet enforceable"
    warnings = collect_warnings(commits, receipts, bindings)

    print("Receipt Coverage Checker")
    print("========================")
    print(f"Total commits:              {len(commits)}")
    print(f"Total receipt files:        {len(receipts)}")
    print(f"Latest commit (HEAD):       {latest_commit}")
    print(f"Latest receipt file:        {latest_receipt}")
    print(f"Latest receipt binding:     {latest_binding}")
    print(f"Coverage status:            {coverage_status}")
    print()
    print("Notes:")
    print("- Counts are inventory only (commits on HEAD, *.md under receipts/).")
    print("- Binding commit is the first `Commit:` line in each receipt.")
    print("- Exact commit-to-receipt mapping is not yet enforceable.")
    print("- This report does not claim complete coverage or full traceability.")

    if warnings:
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"WARN {warning}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
