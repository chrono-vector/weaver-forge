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


def _coerce_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        raise EpistemicStatusError(
            f"{field_name} must be a list/tuple of refs, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise EpistemicStatusError(f"{field_name} must be a list/tuple of refs")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise EpistemicStatusError(f"{field_name} entries must be strings")
        text = item.strip()
        if not text:
            raise EpistemicStatusError(f"{field_name} entries must be non-empty")
        out.append(text)
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
        if not str(self.claim_id).strip():
            raise EpistemicStatusError("claim_id must be non-empty")
        if self.claim_kind not in CLAIM_KINDS:
            raise EpistemicStatusError(f"unknown claim_kind: {self.claim_kind!r}")
        if self.epistemic_status not in EPISTEMIC_STATUSES:
            raise EpistemicStatusError(
                f"unknown epistemic_status: {self.epistemic_status!r}"
            )
        if self.authority is not False:
            raise EpistemicStatusError("authority must be false")
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
        if data.get("schema_version") not in {SCHEMA_VERSION, None}:
            # Accept only this version for R4-A parsed records; None rejected below.
            if data.get("schema_version") != SCHEMA_VERSION:
                raise EpistemicStatusError(
                    f"unsupported claim schema_version: {data.get('schema_version')!r}"
                )
        if data.get("schema_version") != SCHEMA_VERSION:
            raise EpistemicStatusError(
                f"claim schema_version must be {SCHEMA_VERSION!r}"
            )
        return cls(
            claim_id=str(data["claim_id"]),
            statement=str(data["statement"]),
            claim_kind=str(data["claim_kind"]),
            epistemic_status=str(data["epistemic_status"]),
            scope=str(data["scope"]),
            schema_version=SCHEMA_VERSION,
            authority=False,
            evidence_refs=_coerce_str_refs(
                data.get("evidence_refs") or (), field_name="evidence_refs"
            ),
            provenance_refs=_coerce_str_refs(
                data.get("provenance_refs") or (), field_name="provenance_refs"
            ),
            confidence=(
                float(data["confidence"]) if data.get("confidence") is not None else None
            ),
            notes=str(data.get("notes") or ""),
            workflow_state=(
                str(data["workflow_state"])
                if data.get("workflow_state") is not None
                else None
            ),
            extra=dict(data.get("extra") or {}),
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
