"""Legacy compatibility — read existing Weaver claims without synthetic backfill."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .records import EpistemicClaimRecord


@dataclass(frozen=True)
class LegacyClaimView:
    """View of a pre-R4 claim. No epistemic fields invented."""

    claim_id: str
    statement: str
    raw: Mapping[str, Any]
    has_r4_epistemic: bool

    @property
    def epistemic_status(self) -> None:
        """Legacy records do not receive synthesized epistemic_status."""
        return None

    @property
    def claim_kind(self) -> None:
        return None


def _has_r4_fields(data: Mapping[str, Any]) -> bool:
    return bool(
        data.get("schema_version", "").startswith("r4.epistemic.")
        or "claim_kind" in data
        or "epistemic_status" in data
        or "provenance_refs" in data
    )


def legacy_claim_view(data: Mapping[str, Any]) -> LegacyClaimView:
    """
    Accept legacy claim dicts (id/statement or claim_id/statement).
    Does NOT synthesize/backfill stronger epistemic status.
    """
    claim_id = str(data.get("claim_id") or data.get("id") or "")
    statement = str(data.get("statement") or "")
    if not claim_id or not statement:
        raise ValueError("legacy claim requires id/claim_id and statement")
    return LegacyClaimView(
        claim_id=claim_id,
        statement=statement,
        raw=dict(data),
        has_r4_epistemic=_has_r4_fields(data),
    )


def read_claim_record(
    data: Mapping[str, Any],
) -> EpistemicClaimRecord | LegacyClaimView:
    """
    Read a claim dict as R4 EpistemicClaimRecord when R4 fields present;
    otherwise return LegacyClaimView without backfill.
    """
    if _has_r4_fields(data) and data.get("schema_version", "").startswith(
        "r4.epistemic.claim"
    ):
        return EpistemicClaimRecord.from_dict(data)
    # Partial R4-looking fields without schema: still no silent backfill to full record
    # unless schema_version is the claim contract.
    if data.get("schema_version") == "r4.epistemic.claim.v1":
        return EpistemicClaimRecord.from_dict(data)
    return legacy_claim_view(data)
