#!/usr/bin/env python3
"""Structural synthetic final-submission helper for Phase 4-S3 tests only.

This module is NOT the production host automation and does NOT pretend to be a
Witness. It finalizes completeness fields on a disposable evidence tree and
then writes the final manifest exactly once via the inventory helper.

Sequence (non-circular):
1. Ensure required final structural inputs are present
2. Set evidence_inventory_complete=yes and evidence_completeness_status=COMPLETE
3. Write final manifest
4. Caller may validate immutably

Does not set Independent Witness PASS, READY, or rc5 readiness.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import evidence_inventory as ei  # noqa: E402

FINAL_REQUIRED = (
    "WITNESS_STATEMENT.md",
    "WITNESS_VERDICT.md",
    "DEVIATIONS.txt",
    "REDACTIONS.md",
    "POST_BUILD_INTEGRITY.txt",
)


class SyntheticFinalizationError(ValueError):
    """Fail-closed synthetic finalization error."""


def _replace_kv(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    if not pattern.search(text):
        raise SyntheticFinalizationError(f"missing field {key}")
    return pattern.sub(f"{key}={value}", text, count=1)


def finalize_completeness_fields(evidence_dir: Path) -> None:
    """Set completeness authorities before manifest generation."""
    root = Path(evidence_dir)
    for name in FINAL_REQUIRED:
        if not (root / name).is_file():
            raise SyntheticFinalizationError(f"missing required final structural input: {name}")

    post_path = root / "POST_BUILD_INTEGRITY.txt"
    post = post_path.read_text(encoding="utf-8")
    post = _replace_kv(post, "evidence_inventory_complete", "yes")
    # four-yes may become yes when inventory is yes and other fields already yes;
    # leave computation to caller/tests; set conservatively when source fields yes.
    if (
        "source_head_unchanged=yes" in post
        and "cargo_lock_unchanged=yes" in post
        and "cargo_lock_post_matches_expected=yes" in post
    ):
        post = _replace_kv(post, "full_integrity_gate_all_four_yes", "yes")
    post_path.write_text(post, encoding="utf-8", newline="\n")

    host_path = root / "HOST_OUTCOME_INGESTION.txt"
    if host_path.is_file():
        host = host_path.read_text(encoding="utf-8")
        host = _replace_kv(host, "evidence_completeness_status", "COMPLETE")
        host = _replace_kv(host, "preliminary_success_eligible", "NO")
        host_path.write_text(host, encoding="utf-8", newline="\n")


def write_final_manifest(evidence_dir: Path) -> Path:
    """Generate final manifest exactly once after completeness finalization."""
    return ei.write_evidence_manifest(Path(evidence_dir))


def synthesize_final_submission_package(evidence_dir: Path) -> Path:
    """Apply completeness finalization then write the final manifest."""
    finalize_completeness_fields(evidence_dir)
    return write_final_manifest(evidence_dir)
