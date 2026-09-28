"""Optional R4-A bridge: Campaign Runner claim rows ↔ epistemic records.

Does NOT rewrite Campaign Runner intake.
Does NOT merge workflow CLAIM_STATES into epistemic_status.
Does NOT backfill legacy claims with stronger epistemic status.
"""

from __future__ import annotations

from typing import Mapping

from audit_lifecycle.epistemic.compat import LegacyClaimView, read_claim_record
from audit_lifecycle.epistemic.records import EpistemicClaimRecord


def adapt_campaign_claim(row: Mapping[str, Any]) -> EpistemicClaimRecord | LegacyClaimView:
    """
    Map a campaign claim row to an epistemic view.

    - If an explicit R4 epistemic block with schema + status is present, parse it.
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
        return EpistemicClaimRecord.from_dict(payload)

    return read_claim_record(
        {
            "claim_id": row.get("claim_id") or row.get("id"),
            "statement": row.get("statement") or "",
        }
    )
