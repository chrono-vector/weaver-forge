"""R4-B package verification entry — expectation-driven canonical paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .expectation import (
    R4BExpectationError,
    STATE_LEGACY_PRE_R4B,
    STATE_R4_B_ENABLED,
    classify_audit_root,
)
from .reconstructability import verify_reconstructability_at_root
from .review_disagreement import verify_disagreement_records_at_root


def verify_r4b_at_root(audit_root: Path) -> dict[str, Any]:
    """
    Expectation-first R4-B verification.

    Strictly validates EXECUTION_MANIFEST.r4_b (when present) before inspecting
    artifacts. Never infers enabled/disabled from artifact presence alone.
    """
    audit_root = audit_root.resolve()
    try:
        state = classify_audit_root(audit_root)
    except R4BExpectationError as e:
        return {
            "ok": False,
            "status": "R4_B_STATE_CLASSIFICATION_FAIL",
            "error": str(e),
            "state": None,
            "reconstructability_verification": None,
            "review_disagreement_verification": None,
        }

    if state.state == STATE_LEGACY_PRE_R4B:
        recon = verify_reconstructability_at_root(audit_root, required=False)
        disagree = verify_disagreement_records_at_root(
            audit_root, require_expected_set=False
        )
        ok = bool(recon.get("ok")) and bool(disagree.get("ok"))
        return {
            "ok": ok,
            "status": "R4_B_LEGACY_PRE_R4B" if ok else "R4_B_VERIFICATION_FAIL",
            "state": STATE_LEGACY_PRE_R4B,
            "reconstructability_verification": recon,
            "review_disagreement_verification": disagree,
        }

    assert state.state == STATE_R4_B_ENABLED
    assert state.expectation is not None
    exp = state.expectation
    recon = verify_reconstructability_at_root(
        audit_root,
        required=True,
        expected_path=exp.reconstructability_report.path,
        expected_digest=exp.reconstructability_report.digest,
    )
    disagree = verify_disagreement_records_at_root(
        audit_root,
        expected_digests=exp.expected_disagreement_record_digests,
        expected_chain_heads=exp.expected_disagreement_chain_heads,
        require_expected_set=True,
    )
    ok = bool(recon.get("ok")) and bool(disagree.get("ok"))
    return {
        "ok": ok,
        "status": "R4_B_ENABLED_VERIFICATION_PASS" if ok else "R4_B_VERIFICATION_FAIL",
        "state": STATE_R4_B_ENABLED,
        "expectation": exp.to_dict(),
        "reconstructability_verification": recon,
        "review_disagreement_verification": disagree,
    }
