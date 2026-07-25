#!/usr/bin/env python3
"""Read-only recursive evidence inventory helper (Phase 4-S2/S3).

Provides deterministic normalized relative-path enumeration with fail-closed
rejection of symlinks, special objects, path escapes, and duplicate normalized
paths. Phase 4-S3 adds deterministic SHA-256 manifest generation used by host
preliminary finalization and synthetic final-submission test helpers.

Manifest checksum lines exclude EVIDENCE_MANIFEST.sha256 itself and
WEAVER_FORGE_FINAL_BINDING.txt (RC6-R3: final binding contains
final_manifest_sha256 and must not be listed in the manifest it seals).

Does not set Independent Witness PASS, READY, or evidence_inventory_complete=yes
on behalf of a Witness. Completeness field transitions remain owned by the
canonical POST_BUILD / HOST_OUTCOME authorities and are applied by callers
before manifest generation.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import sys
from pathlib import Path

MANIFEST_NAME = "EVIDENCE_MANIFEST.sha256"
FINAL_BINDING_NAME = "WEAVER_FORGE_FINAL_BINDING.txt"

# Files excluded from EVIDENCE_MANIFEST.sha256 checksum lines.
MANIFEST_CHECKSUM_EXCLUDES = frozenset({MANIFEST_NAME, FINAL_BINDING_NAME})


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest_lines(evidence_dir: Path, *, exclude_manifest: bool = True) -> list[str]:
    """Build deterministic SHA-256 manifest lines for every regular evidence file.

    When exclude_manifest is True (default), checksum lines omit
    EVIDENCE_MANIFEST.sha256 and WEAVER_FORGE_FINAL_BINDING.txt.
    Paths are './'-prefixed, byte-order sorted by the normalized relative path
    used in enumeration.
    """
    root = Path(evidence_dir)
    lines: list[str] = []
    for rel in enumerate_evidence_files(root):
        if exclude_manifest and rel in MANIFEST_CHECKSUM_EXCLUDES:
            continue
        digest = sha256_file(root / rel)
        lines.append(f"{digest}  ./{rel}")
    return lines


def write_evidence_manifest(
    evidence_dir: Path,
    *,
    manifest_name: str = MANIFEST_NAME,
) -> Path:
    """Write deterministic SHA-256 manifest excluding the manifest and final binding."""
    root = Path(evidence_dir)
    if manifest_name != MANIFEST_NAME:
        raise EvidenceInventoryError(
            f"unsupported manifest_name {manifest_name!r}; only {MANIFEST_NAME} is authorized"
        )
    lines = build_manifest_lines(root, exclude_manifest=True)
    target = root / manifest_name
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enumerate or write a deterministic SHA-256 evidence manifest using the "
            "fail-closed recursive inventory helper. Excludes EVIDENCE_MANIFEST.sha256 "
            "and WEAVER_FORGE_FINAL_BINDING.txt from checksum lines. Does not claim "
            "Independent Witness PASS or READY."
        )
    )
    parser.add_argument("evidence_dir", type=Path)
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help=(
            "Write EVIDENCE_MANIFEST.sha256 (excludes itself and "
            "WEAVER_FORGE_FINAL_BINDING.txt)"
        ),
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print enumerated relative paths (default when not writing)",
    )
    args = parser.parse_args(argv)
    evidence_dir = args.evidence_dir.resolve()
    try:
        if args.write_manifest:
            path = write_evidence_manifest(evidence_dir)
            print(str(path))
            return 0
        for rel in enumerate_evidence_files_with_prefix(evidence_dir):
            print(rel)
        return 0
    except EvidenceInventoryError as exc:
        print(f"EVIDENCE_INVENTORY: FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
