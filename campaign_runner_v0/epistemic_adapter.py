"""Optional R4-A bridge: Campaign Runner claim rows ↔ epistemic records.

Does NOT rewrite Campaign Runner intake.
Does NOT merge workflow CLAIM_STATES into epistemic_status.
Does NOT backfill legacy claims with stronger epistemic status.

Explicit R4 epistemic blocks pass through the complete R4 validator
(validate_claim_dict) — never a permissive from_dict-only path.
"""

from __future__ import annotations

from typing import Any, Mapping

from audit_lifecycle.epistemic.compat import LegacyClaimView, read_claim_record
from audit_lifecycle.epistemic.records import EpistemicClaimRecord
from audit_lifecycle.epistemic.validation import (
    EpistemicValidationError,
    validate_claim_dict,
)


def adapt_campaign_claim(row: Mapping[str, Any]) -> EpistemicClaimRecord | LegacyClaimView:
    """
    Map a campaign claim row to an epistemic view.

    - If an explicit R4 epistemic block with schema + status is present, validate it.
    - Otherwise return LegacyClaimView with no synthetic status.
    Workflow state (row['state']) is never copied into epistemic_status.
    """
    epi = row.get("epistemic")
    if (
        isinstance(epi, dict)
        and epi.get("schema_version") == "r4.epistemic.claim.v1"
        and epi.get("epistemic_status") is not None
        and epi.get("claim_kind") is not None
    ):
        payload = dict(epi)
        payload.setdefault("claim_id", row.get("claim_id") or row.get("id"))
        payload.setdefault("statement", row.get("statement") or "")
        payload.setdefault("scope", epi.get("scope") or row.get("scope") or "")
        payload["authority"] = False
        # Never pull workflow state into epistemic_status.
        # Full validator — rejects provenance-free VERIFIED_SCOPE, unknown kinds, etc.
        try:
            return validate_claim_dict(payload)
        except EpistemicValidationError:
            raise

    return read_claim_record(
        {
            "claim_id": row.get("claim_id") or row.get("id"),
            "statement": row.get("statement") or "",
        }
    )
