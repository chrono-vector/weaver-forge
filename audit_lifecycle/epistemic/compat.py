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
    """True when the payload declares/contains R4 epistemic structure."""
    sv = str(data.get("schema_version") or "")
    if sv.startswith("r4.epistemic."):
        return True
    return any(
        k in data for k in ("claim_kind", "epistemic_status", "provenance_refs")
    )


def is_explicit_r4_epistemic(data: Mapping[str, Any]) -> bool:
    """Public helper: explicit R4 epistemic structure (fail-closed path)."""
    return _has_r4_fields(data)


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

    Explicit R4 epistemic structure fails closed on invalid/incomplete records.
    Legacy compatibility remains only for records with no R4 epistemic contract.
    """
    if _has_r4_fields(data):
        from .validation import validate_claim_dict

        return validate_claim_dict(data)
    return legacy_claim_view(data)
