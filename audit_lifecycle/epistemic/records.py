"""Versioned Claim + Epistemic Status contract (R4-A).

workflow state != epistemic status.
Campaign Runner CLAIM_STATES must not be merged into epistemic_status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .authority import enforce_non_authority
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.claim.v1"

CLAIM_KINDS = frozenset(
    {
        "DOCUMENT_IDENTITY",
        "FORMAL",
        "IMPLEMENTATION",
        "EMPIRICAL",
        "NORMATIVE",
        "SYMBOLIC",
        "HISTORICAL",
    }
)

EPISTEMIC_STATUSES = frozenset(
    {
        "REPORTED",
        "SPECIFIED",
        "OBSERVED",
        "REPRODUCED",
        "VERIFIED_SCOPE",
        "AMBIGUOUS",
        "UNRESOLVED",
    }
)

# Statuses that may never be reached by silent promotion from REPORTED.
_SILENT_PROMOTION_TARGETS = frozenset({"OBSERVED", "REPRODUCED", "VERIFIED_SCOPE"})


class EpistemicStatusError(ValueError):
    """Raised on forbidden epistemic status transitions or invalid status values."""


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    """R1-N1: structured identifiers must already be nonempty strings."""
    if not isinstance(value, str):
        raise EpistemicStatusError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    text = value.strip()
    if not text:
        raise EpistemicStatusError(f"{field_name} must be a nonempty string")
    return text


def _coerce_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
    """Strict collection typing for present reference fields.

    Present fields must already be list/tuple. Falsey non-collections must
    not coerce to empty collections.
    """
    if isinstance(value, str):
        raise EpistemicStatusError(
            f"{field_name} must be a list/tuple of refs, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise EpistemicStatusError(
            f"{field_name} must be a list/tuple of refs; "
            f"got {type(value).__name__}"
        )
    out: list[str] = []
    for item in value:
        out.append(_require_nonempty_str(item, field_name=f"{field_name} entry"))
    return tuple(sorted(dict.fromkeys(out)))


@dataclass(frozen=True)
class EpistemicClaimRecord:
    """Additive versioned epistemic claim record. Non-authoritative."""

    claim_id: str
    statement: str
    claim_kind: str
    epistemic_status: str
    scope: str
    schema_version: str = SCHEMA_VERSION
    authority: bool = False
    evidence_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    confidence: float | None = None
    notes: str = ""
    workflow_state: str | None = None  # advisory mirror only; never drives status
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.claim_id, str) or not self.claim_id.strip():
            raise EpistemicStatusError("claim_id must be non-empty")
        if self.claim_kind not in CLAIM_KINDS:
            raise EpistemicStatusError(f"unknown claim_kind: {self.claim_kind!r}")
        if self.epistemic_status not in EPISTEMIC_STATUSES:
            raise EpistemicStatusError(
                f"unknown epistemic_status: {self.epistemic_status!r}"
            )
        if self.authority is not False:
            raise EpistemicStatusError("authority must be false")
        if not isinstance(self.evidence_refs, tuple):
            raise EpistemicStatusError(
                "evidence_refs must be a tuple of strings; "
                f"got {type(self.evidence_refs).__name__}"
            )
        if not isinstance(self.provenance_refs, tuple):
            raise EpistemicStatusError(
                "provenance_refs must be a tuple of strings; "
                f"got {type(self.provenance_refs).__name__}"
            )
        if self.confidence is not None and not (0.0 <= float(self.confidence) <= 1.0):
            raise EpistemicStatusError("confidence must be in [0.0, 1.0] when set")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "claim_id": self.claim_id,
            "statement": self.statement,
            "claim_kind": self.claim_kind,
            "epistemic_status": self.epistemic_status,
            "scope": self.scope,
            "authority": False,
            "evidence_refs": list(self.evidence_refs),
            "provenance_refs": list(self.provenance_refs),
            "notes": self.notes,
        }
        if self.confidence is not None:
            d["confidence"] = float(self.confidence)
        if self.workflow_state is not None:
            d["workflow_state"] = self.workflow_state
        if self.extra:
            d["extra"] = dict(self.extra)
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "EpistemicClaimRecord":
        enforce_non_authority(data)
        if data.get("schema_version") != SCHEMA_VERSION:
            raise EpistemicStatusError(
                f"claim schema_version must be {SCHEMA_VERSION!r}"
            )
        if "authority" not in data or data["authority"] is not False:
            raise EpistemicStatusError("authority must be Boolean false")
        claim_kind = data["claim_kind"]
        epistemic_status = data["epistemic_status"]
        if not isinstance(claim_kind, str) or claim_kind not in CLAIM_KINDS:
            raise EpistemicStatusError(f"unknown claim_kind: {claim_kind!r}")
        if (
            not isinstance(epistemic_status, str)
            or epistemic_status not in EPISTEMIC_STATUSES
        ):
            raise EpistemicStatusError(
                f"unknown epistemic_status: {epistemic_status!r}"
            )
        notes = data.get("notes", "")
        if notes is None:
            notes = ""
        if not isinstance(notes, str):
            raise EpistemicStatusError("notes must be a string when set")
        workflow_state = data.get("workflow_state")
        if workflow_state is not None and not isinstance(workflow_state, str):
            raise EpistemicStatusError("workflow_state must be a string when set")
        confidence = data.get("confidence")
        if confidence is not None and not isinstance(confidence, (int, float)):
            raise EpistemicStatusError("confidence must be a number when set")
        evidence_refs = (
            _coerce_str_refs(data["evidence_refs"], field_name="evidence_refs")
            if "evidence_refs" in data
            else ()
        )
        provenance_refs = (
            _coerce_str_refs(data["provenance_refs"], field_name="provenance_refs")
            if "provenance_refs" in data
            else ()
        )
        extra = data["extra"] if "extra" in data else {}
        if extra is None:
            extra = {}
        if not isinstance(extra, Mapping):
            raise EpistemicStatusError("extra must be a mapping when set")
        return cls(
            claim_id=_require_nonempty_str(data["claim_id"], field_name="claim_id"),
            statement=_require_nonempty_str(data["statement"], field_name="statement"),
            claim_kind=claim_kind,
            epistemic_status=epistemic_status,
            scope=_require_nonempty_str(data["scope"], field_name="scope"),
            schema_version=SCHEMA_VERSION,
            authority=False,
            evidence_refs=evidence_refs,
            provenance_refs=provenance_refs,
            confidence=(float(confidence) if confidence is not None else None),
            notes=notes,
            workflow_state=workflow_state,
            extra=dict(extra),
        )


def assert_no_silent_status_promotion(
    from_status: str,
    to_status: str,
    *,
    explicit_promotion: bool = False,
    evidence_present: bool = False,
) -> None:
    """REPORTED must not silently become OBSERVED or VERIFIED_SCOPE (etc.)."""
    if from_status not in EPISTEMIC_STATUSES:
        raise EpistemicStatusError(f"unknown from_status: {from_status!r}")
    if to_status not in EPISTEMIC_STATUSES:
        raise EpistemicStatusError(f"unknown to_status: {to_status!r}")
    if from_status == to_status:
        return
    if from_status == "REPORTED" and to_status in _SILENT_PROMOTION_TARGETS:
        if not explicit_promotion or not evidence_present:
            raise EpistemicStatusError(
                f"forbidden silent promotion {from_status} → {to_status}"
            )
    # Never auto-promote to VERIFIED_SCOPE without explicit promotion + evidence.
    if to_status == "VERIFIED_SCOPE" and (not explicit_promotion or not evidence_present):
        raise EpistemicStatusError(
            f"forbidden silent promotion {from_status} → VERIFIED_SCOPE"
        )


def formal_and_symbolic_are_distinct(a: str, b: str) -> bool:
    """FORMAL and SYMBOLIC remain distinct claim kinds."""
    return a in CLAIM_KINDS and b in CLAIM_KINDS and a != b
