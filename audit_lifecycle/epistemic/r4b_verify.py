"""R4-B package verification entry — expectation-driven canonical paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .expectation import (
    FREEZE_STATE_FROZEN,
    FREEZE_STATE_PRE,
    R4BExpectationError,
    STATE_LEGACY_PRE_R4B,
    STATE_R4_B_ENABLED,
    classify_audit_root,
    classify_frozen_r4b_state,
    load_execution_manifest,
    validate_freeze_transaction,
)
from .reconstructability import verify_reconstructability_at_root
from .review_disagreement import verify_disagreement_records_at_root
from audit_lifecycle.request import read_json


def verify_r4b_at_root(audit_root: Path) -> dict[str, Any]:
    """
    Expectation-first R4-B verification.

    When any freeze marker exists, freeze-transaction consistency is required
    before classifying legacy vs R4-B. Frozen classification cross-binds root
    manifest, frozen MANIFEST, and FREEZE_STATUS. Never infers enabled/disabled
    from artifact presence alone.
    """
    audit_root = audit_root.resolve()

    freeze_txn = validate_freeze_transaction(audit_root)
    if not freeze_txn.get("ok"):
        return {
            "ok": False,
            "status": "R4_B_FREEZE_TRANSACTION_FAIL",
            "error": freeze_txn.get("error"),
            "state": None,
            "freeze_transaction": freeze_txn,
            "reconstructability_verification": None,
            "review_disagreement_verification": None,
        }

    if freeze_txn.get("state") == FREEZE_STATE_FROZEN:
        try:
            root_manifest = load_execution_manifest(audit_root)
            frozen_manifest = freeze_txn.get("frozen_manifest")
            freeze_status = freeze_txn.get("freeze_status")
            if frozen_manifest is None:
                frozen_path = (
                    Path(str(freeze_txn["freeze_directory"])) / "MANIFEST.json"
                )
                frozen_manifest = read_json(frozen_path)
            state = classify_frozen_r4b_state(
                root_manifest, frozen_manifest, freeze_status
            )
        except R4BExpectationError as e:
            return {
                "ok": False,
                "status": "R4_B_STATE_CLASSIFICATION_FAIL",
                "error": str(e),
                "state": None,
                "freeze_transaction": freeze_txn,
                "reconstructability_verification": None,
                "review_disagreement_verification": None,
            }
    else:
        # PRE_FREEZE — classify from root EXECUTION_MANIFEST only.
        assert freeze_txn.get("state") == FREEZE_STATE_PRE
        try:
            state = classify_audit_root(audit_root)
        except R4BExpectationError as e:
            return {
                "ok": False,
                "status": "R4_B_STATE_CLASSIFICATION_FAIL",
                "error": str(e),
                "state": None,
                "freeze_transaction": freeze_txn,
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
            "freeze_transaction": freeze_txn,
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
        "freeze_transaction": freeze_txn,
        "reconstructability_verification": recon,
        "review_disagreement_verification": disagree,
    }
