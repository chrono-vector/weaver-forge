from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from .boundary import BoundaryManager
from .request import sha256_file, write_json


def pin_target(
    boundary: BoundaryManager,
    audit_root: Path,
    target_path: Path,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Copy target into audit workspace and bind digests (fail on mismatch)."""
    target_path = target_path.resolve()
    if not target_path.exists():
        raise FileNotFoundError(target_path)

    pinned_root = audit_root / "pinned_target"
    boundary.assert_writable(pinned_root / ".keep")

    if target_path.is_file():
        dest = pinned_root / target_path.name
        boundary.assert_writable(dest)
        pinned_root.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_path, dest)
        files = [dest]
    else:
        if pinned_root.exists():
            shutil.rmtree(pinned_root)
        shutil.copytree(target_path, pinned_root)
        files = [p for p in pinned_root.rglob("*") if p.is_file()]

    inventory = []
    for f in sorted(files):
        digest = sha256_file(f)
        rel = str(f.relative_to(pinned_root)).replace("\\", "/")
        inventory.append({"relative_path": rel, "sha256": digest, "bytes": f.stat().st_size})

    if expected_sha256:
        # If pinning a single file, compare that file; else compare a declared primary file name
        primary = files[0] if len(files) == 1 else None
        if primary is None:
            raise ValueError("expected_sha256 provided but target is a directory without single-file pin")
        actual = sha256_file(primary)
        if actual != expected_sha256.lower():
            raise RuntimeError(
                f"SOURCE_DIGEST_MISMATCH expected={expected_sha256} actual={actual}"
            )

    provenance = {
        "origin_absolute": str(target_path),
        "pinned_root": str(pinned_root.resolve()),
        "expected_sha256": expected_sha256,
        "files": inventory,
        "modified": False,
        "classification": "PINNED_INPUT",
    }
    write_json(audit_root / "PROVENANCE.json", provenance)
    return provenance
