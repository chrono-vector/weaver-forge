"""Validation entry points for R4-A epistemic records.

Canonical R4 parser/validator boundary:

  parse_optional_epistemic_container(present, value, identity)

Invariant:
  - key `epistemic` ABSENT  => legacy path
  - key `epistemic` PRESENT => explicit R4; value MUST be a mapping and MUST
    pass the complete exact-version R4 claim parser; malformed/partial/
    unsupported values FAIL CLOSED

Explicit R4 never downgrades to legacy, strips invalid fields, overwrites
authority, synthesizes missing required fields, or retries through legacy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .authority import AuthorityViolation, enforce_non_authority
from .provenance import (
    ProvenanceGraphError,
    ProvenanceRecord,
    require_provenance_for_verified_scope,
)
from .records import (
    CLAIM_KINDS,
    EPISTEMIC_STATUSES,
    EpistemicClaimRecord,
    EpistemicStatusError,
)
from .relations import (
    RELATION_TYPES,
    RelationAsClaim,
    RelationSatisfactionError,
    analogous_to_cannot_satisfy_causes,
)


class EpistemicValidationError(ValueError):
    """Malformed epistemic / relation / provenance record."""


@dataclass(frozen=True)
class OptionalEpistemicParseResult:
    """Result of the canonical optional-epistemic container parse."""

    mode: str  # "legacy" | "r4"
    record: EpistemicClaimRecord | None = None


def _as_mapping(record: Any) -> Mapping[str, Any]:
    if hasattr(record, "to_dict"):
        return record.to_dict()
    if isinstance(record, Mapping):
        return record
    raise EpistemicValidationError(f"unsupported record type: {type(record)!r}")


def validate_claim_dict(data: Mapping[str, Any]) -> EpistemicClaimRecord:
    try:
        enforce_non_authority(data)
        rec = EpistemicClaimRecord.from_dict(data)
        require_provenance_for_verified_scope(
            rec.epistemic_status,
            rec.provenance_refs,
            provenance_required=True,
        )
        return rec
    except (EpistemicStatusError, AuthorityViolation, KeyError, TypeError, ValueError) as e:
        raise EpistemicValidationError(str(e)) from e


def parse_optional_epistemic_container(
    present: bool,
    value: Any,
    identity: Mapping[str, Any] | None = None,
) -> OptionalEpistemicParseResult:
    """
    Canonical R4 vs legacy fail-closed parser boundary.

    present=False (key absent) => legacy.
    present=True  => value must be a non-empty mapping that passes the
    complete exact-version R4 claim parser. Never downgrades to legacy.
    """
    if not present:
        return OptionalEpistemicParseResult(mode="legacy", record=None)

    if value is None or isinstance(value, (str, bytes, list, tuple, int, float, bool)):
        raise EpistemicValidationError(
            "explicit epistemic container must be a mapping; "
            f"got {type(value).__name__}"
        )
    if not isinstance(value, Mapping):
        raise EpistemicValidationError(
            "explicit epistemic container must be a mapping; "
            f"got {type(value).__name__}"
        )
    if not value:
        raise EpistemicValidationError(
            "explicit epistemic container must not be an empty mapping"
        )

    payload = dict(value)
    identity = identity or {}
    # Identity glue only — never synthesize claim_kind / epistemic_status /
    # schema_version / authority / provenance.
    if "claim_id" not in payload:
        cid = identity.get("claim_id")
        if cid is None:
            cid = identity.get("id")
        if cid is not None:
            payload["claim_id"] = cid
    if "statement" not in payload and identity.get("statement") is not None:
        payload["statement"] = identity.get("statement")
    if "scope" not in payload:
        scope = value.get("scope") if isinstance(value, Mapping) else None
        if scope is None:
            scope = identity.get("scope")
        if scope is not None:
            payload["scope"] = scope

    try:
        rec = validate_claim_dict(payload)
    except EpistemicValidationError:
        raise
    return OptionalEpistemicParseResult(mode="r4", record=rec)


def validate_relation_dict(data: Mapping[str, Any]) -> RelationAsClaim:
    try:
        enforce_non_authority(data)
        if not data.get("evidence_refs"):
            raise EpistemicValidationError(
                "malformed relation: missing required evidence_refs"
            )
        scope = data.get("scope")
        if not isinstance(scope, str) or not scope.strip():
            raise EpistemicValidationError(
                "malformed relation: missing required scope"
            )
        rtype = data.get("relation_type")
        if rtype not in RELATION_TYPES:
            raise EpistemicValidationError(f"malformed relation: bad relation_type {rtype!r}")
        rec = RelationAsClaim.from_dict(data)
        analogous_to_cannot_satisfy_causes(rec)
        return rec
    except (
        RelationSatisfactionError,
        EpistemicStatusError,
        AuthorityViolation,
        KeyError,
        TypeError,
        ValueError,
        EpistemicValidationError,
    ) as e:
        if isinstance(e, EpistemicValidationError):
            raise
        raise EpistemicValidationError(str(e)) from e


def validate_provenance_dict(data: Mapping[str, Any]) -> ProvenanceRecord:
    try:
        enforce_non_authority(data)
        required = ("artifact_id", "digest", "source_id", "lineage_id", "schema_version")
        missing = [k for k in required if k not in data or data.get(k) in (None, "")]
        if missing:
            raise EpistemicValidationError(
                f"malformed provenance: missing {missing}"
            )
        return ProvenanceRecord.from_dict(data)
    except (
        AuthorityViolation,
        KeyError,
        TypeError,
        ValueError,
        ProvenanceGraphError,
        EpistemicValidationError,
    ) as e:
        if isinstance(e, EpistemicValidationError):
            raise
        raise EpistemicValidationError(str(e)) from e


def validate_epistemic_record(record: Any, *, kind: str | None = None) -> Any:
    """
    Validate a claim, relation, or provenance record.

    kind: "claim" | "relation" | "provenance" | None (auto-detect)
    """
    data = _as_mapping(record)
    detected = kind
    if detected is None:
        if "relation_type" in data or "relation_id" in data:
            detected = "relation"
        elif "lineage_id" in data and "artifact_id" in data:
            detected = "provenance"
        elif "claim_kind" in data or "epistemic_status" in data:
            detected = "claim"
        else:
            raise EpistemicValidationError("cannot detect epistemic record kind")

    if detected == "claim":
        if data.get("claim_kind") not in CLAIM_KINDS and "claim_kind" in data:
            raise EpistemicValidationError(
                f"malformed claim: bad claim_kind {data.get('claim_kind')!r}"
            )
        if (
            data.get("epistemic_status") not in EPISTEMIC_STATUSES
            and "epistemic_status" in data
        ):
            raise EpistemicValidationError(
                f"malformed claim: bad epistemic_status {data.get('epistemic_status')!r}"
            )
        return validate_claim_dict(data)
    if detected == "relation":
        return validate_relation_dict(data)
    if detected == "provenance":
        return validate_provenance_dict(data)
    raise EpistemicValidationError(f"unknown kind: {detected!r}")
