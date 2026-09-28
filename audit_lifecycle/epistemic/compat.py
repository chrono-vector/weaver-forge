"""Legacy compatibility — read existing Weaver claims without synthetic backfill.

Integration entry paths delegate nested `epistemic` containers to the canonical
parser in audit_lifecycle.epistemic.validation.parse_optional_epistemic_container.
"""

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
    """True when the payload declares/contains R4 epistemic structure at top level."""
    sv = data.get("schema_version")
    if isinstance(sv, str) and sv.startswith("r4.epistemic."):
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
    claim_id = data.get("claim_id")
    if claim_id is None:
        claim_id = data.get("id")
    statement = data.get("statement")
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise ValueError("legacy claim requires id/claim_id and statement")
    if not isinstance(statement, str) or not statement.strip():
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

    Nested `epistemic` containers use the canonical optional-container parser.
    Top-level explicit R4 structure fails closed on invalid/incomplete records.
    Legacy compatibility remains only for records with no R4 epistemic contract.
    """
    from .validation import (
        EpistemicValidationError,
        parse_optional_epistemic_container,
        validate_claim_dict,
    )

    if "epistemic" in data:
        result = parse_optional_epistemic_container(
            True,
            data.get("epistemic"),
            identity=data,
        )
        if result.record is None:
            raise EpistemicValidationError("explicit epistemic container failed closed")
        return result.record

    if _has_r4_fields(data):
        return validate_claim_dict(data)
    return legacy_claim_view(data)
