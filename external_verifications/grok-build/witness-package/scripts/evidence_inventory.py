#!/usr/bin/env python3
"""Read-only recursive evidence inventory helper (Phase 4-S2).

Provides deterministic normalized relative-path enumeration with fail-closed
rejection of symlinks, special objects, path escapes, and duplicate normalized
paths. Does not implement final manifest cryptographic closure or
evidence_inventory_complete transitions (S3).
"""

from __future__ import annotations

import os
import stat
from pathlib import Path


class EvidenceInventoryError(ValueError):
    """Fail-closed inventory enumeration error."""


def _is_special_file(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise EvidenceInventoryError(f"cannot lstat {path}: {exc}") from exc
    if (
        stat.S_ISFIFO(mode)
        or stat.S_ISSOCK(mode)
        or stat.S_ISCHR(mode)
        or stat.S_ISBLK(mode)
    ):
        return True
    is_door = getattr(stat, "S_ISDOOR", None)
    return bool(is_door and is_door(mode))


def normalize_relative_path(rel: str) -> str:
    """Normalize a relative path to POSIX form without leading './'."""
    if not isinstance(rel, str) or not rel:
        raise EvidenceInventoryError("relative path must be a non-empty string")
    cleaned = rel.replace("\\", "/").strip()
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    if cleaned.startswith("/") or cleaned.startswith("../") or cleaned == "..":
        raise EvidenceInventoryError(f"path escape rejected: {rel!r}")
    parts = []
    for part in cleaned.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise EvidenceInventoryError(f"path escape rejected: {rel!r}")
        parts.append(part)
    if not parts:
        raise EvidenceInventoryError(f"empty normalized path from {rel!r}")
    return "/".join(parts)


def enumerate_evidence_files(evidence_dir: Path) -> list[str]:
    """Recursively enumerate regular files under evidence_dir.

    Returns deterministic sorted normalized relative paths (POSIX, no './').
    Does not follow symlinks. Rejects symlinks, special files, escapes, and
    duplicate normalized paths.
    """
    root = Path(evidence_dir).resolve()
    if not root.is_dir():
        raise EvidenceInventoryError(f"evidence_dir is not a directory: {root}")

    found: list[str] = []
    seen: set[str] = set()

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current = Path(dirpath)

        # Reject symlink directories encountered via walk parents.
        if current != root and current.is_symlink():
            raise EvidenceInventoryError(f"symlink rejected: {current}")

        # Do not descend into symlinked directories.
        keep_dirs: list[str] = []
        for name in list(dirnames):
            child = current / name
            if child.is_symlink():
                raise EvidenceInventoryError(f"symlink rejected: {child}")
            if _is_special_file(child):
                raise EvidenceInventoryError(f"special object rejected: {child}")
            keep_dirs.append(name)
        dirnames[:] = sorted(keep_dirs)

        for name in sorted(filenames):
            child = current / name
            if child.is_symlink():
                raise EvidenceInventoryError(f"symlink rejected: {child}")
            if _is_special_file(child):
                raise EvidenceInventoryError(f"special object rejected: {child}")
            if not child.is_file():
                raise EvidenceInventoryError(f"non-regular file rejected: {child}")
            try:
                child.resolve().relative_to(root)
            except ValueError as exc:
                raise EvidenceInventoryError(f"path escape rejected: {child}") from exc
            rel = normalize_relative_path(str(child.relative_to(root)))
            if rel in seen:
                raise EvidenceInventoryError(f"duplicate normalized path rejected: {rel}")
            seen.add(rel)
            found.append(rel)

    return sorted(found)


def enumerate_evidence_files_with_prefix(evidence_dir: Path) -> list[str]:
    """Same as enumerate_evidence_files but returns './'-prefixed paths."""
    return [f"./{p}" for p in enumerate_evidence_files(evidence_dir)]
