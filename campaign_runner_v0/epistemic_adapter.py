"""Optional R4-A bridge: Campaign Runner claim rows ↔ epistemic records.

Does NOT rewrite Campaign Runner intake.
Does NOT merge workflow CLAIM_STATES into epistemic_status.
Does NOT backfill legacy claims with stronger epistemic status.

Explicit R4 epistemic blocks pass through the canonical
parse_optional_epistemic_container boundary — never a permissive
from_dict-only path and never a silent downgrade to LegacyClaimView.
"""

from __future__ import annotations

from typing import Any, Mapping

from audit_lifecycle.epistemic.compat import LegacyClaimView, read_claim_record
from audit_lifecycle.epistemic.records import EpistemicClaimRecord
from audit_lifecycle.epistemic.validation import (
    EpistemicValidationError,
    parse_optional_epistemic_container,
)


def adapt_campaign_claim(row: Mapping[str, Any]) -> EpistemicClaimRecord | LegacyClaimView:
    """
    Map a campaign claim row to an epistemic view.

    - If key `epistemic` is present, validate fail-closed via the canonical parser.
    - Otherwise return LegacyClaimView with no synthetic status.
    Workflow state (row['state']) is never copied into epistemic_status.
    Explicit authority:true is rejected (never overwritten to false).
    """
    if "epistemic" in row:
        result = parse_optional_epistemic_container(
            True,
            row.get("epistemic"),
            identity=row,
        )
        if result.record is None:
            raise EpistemicValidationError("explicit epistemic container failed closed")
        return result.record

    return read_claim_record(
        {
            "claim_id": row.get("claim_id") or row.get("id"),
            "statement": row.get("statement") or "",
        }
    )
