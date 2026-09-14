from __future__ import annotations

from pathlib import Path
from typing import Any

from .request import sha256_file, utc_now, write_json


def snapshot_baseline(
    audit_root: Path,
    audit_id: str,
    protected_paths: list[str],
    prior_freeze_sums: list[dict[str, str]],
) -> dict[str, Any]:
    """Capture baseline + verify prior freeze SHA256SUMS digests if provided."""
    checks: dict[str, Any] = {}
    all_ok = True
    for item in prior_freeze_sums:
        label = item["label"]
        path = Path(item["path"])
        expected = item["sha256"].lower()
        if not path.is_file():
            checks[label] = {"ok": False, "error": "MISSING", "path": str(path)}
            all_ok = False
            continue
        digest = sha256_file(path)
        ok = digest == expected
        if not ok:
            all_ok = False
        checks[label] = {
            "ok": ok,
            "path": str(path.resolve()),
            "digest": digest,
            "expected": expected,
        }

    protected_meta = []
    for p in protected_paths:
        pp = Path(p)
        protected_meta.append(
            {
                "path": str(pp.resolve()) if pp.exists() else str(pp),
                "exists": pp.exists(),
                "is_file": pp.is_file() if pp.exists() else False,
                "is_dir": pp.is_dir() if pp.exists() else False,
            }
        )

    doc = {
        "audit_id": audit_id,
        "baseline_at_utc": utc_now(),
        "allowed_write_root": str(audit_root.resolve()),
        "protected_paths": protected_meta,
        "prior_freeze_integrity": {
            "all_ok": all_ok,
            "checks": checks,
        },
    }
    write_json(audit_root / "BASELINE.json", doc)
    if prior_freeze_sums and not all_ok:
        raise RuntimeError("PRIOR_FREEZE_INTEGRITY_MISMATCH: baseline verification failed")
    return doc
