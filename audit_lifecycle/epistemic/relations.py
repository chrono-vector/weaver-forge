"""Explicit Relation-as-Claim contract (R4-A).

ANALOGOUS_TO must never satisfy CAUSES.
Missing required evidence/scope must not silently promote anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from .authority import enforce_non_authority
from .records import EPISTEMIC_STATUSES, EpistemicStatusError
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.relation.v1"

RELATION_TYPES = frozenset(
    {
        "SUPPORTS",
        "CONTRADICTS",
        "DEPENDS_ON",
        "ANALOGOUS_TO",
        "CAUSES",
        "REFINES",
        "SUPERSEDES",
    }
)


class RelationSatisfactionError(ValueError):
    """Raised when a relation is used to satisfy an incompatible relation type."""


@dataclass(frozen=True)
class RelationAsClaim:
    """Relation record carrying its own epistemic status. Non-authoritative."""

    relation_id: str
    source_claim_id: str
    target_claim_id: str
    relation_type: str
    evidence_refs: tuple[str, ...]
    scope: str
    epistemic_status: str
    schema_version: str = SCHEMA_VERSION
    authority: bool = False
    confidence: float | None = None
    directionality: str = "directed"  # directed | bidirectional
    revision_condition: str = ""
    falsifier_condition: str = ""
    notes: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.relation_type not in RELATION_TYPES:
            raise RelationSatisfactionError(
                f"unknown relation_type: {self.relation_type!r}"
            )
        if self.epistemic_status not in EPISTEMIC_STATUSES:
            raise EpistemicStatusError(
                f"unknown epistemic_status: {self.epistemic_status!r}"
            )
        if self.authority is not False:
            raise RelationSatisfactionError("authority must be false")
        if not self.evidence_refs:
            raise RelationSatisfactionError(
                "relation requires evidence_refs; missing evidence must not promote"
            )
        if not str(self.scope).strip():
            raise RelationSatisfactionError(
                "relation requires non-empty scope; missing scope must not promote"
            )
        if self.confidence is not None and not (0.0 <= float(self.confidence) <= 1.0):
            raise RelationSatisfactionError("confidence must be in [0.0, 1.0] when set")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "relation_id": self.relation_id,
            "source_claim_id": self.source_claim_id,
            "target_claim_id": self.target_claim_id,
            "relation_type": self.relation_type,
            "evidence_refs": list(self.evidence_refs),
            "scope": self.scope,
            "epistemic_status": self.epistemic_status,
            "authority": False,
            "directionality": self.directionality,
            "revision_condition": self.revision_condition,
            "falsifier_condition": self.falsifier_condition,
            "notes": self.notes,
        }
        if self.confidence is not None:
            d["confidence"] = float(self.confidence)
        if self.extra:
            d["extra"] = dict(self.extra)
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def digest(self) -> str:
        return canonical_digest(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RelationAsClaim":
        enforce_non_authority(data)
        if data.get("schema_version") != SCHEMA_VERSION:
            raise RelationSatisfactionError(
                f"relation schema_version must be {SCHEMA_VERSION!r}"
            )
        evidence = data.get("evidence_refs") or ()
        return cls(
            relation_id=str(data["relation_id"]),
            source_claim_id=str(data["source_claim_id"]),
            target_claim_id=str(data["target_claim_id"]),
            relation_type=str(data["relation_type"]),
            evidence_refs=tuple(evidence),
            scope=str(data.get("scope") or ""),
            epistemic_status=str(data["epistemic_status"]),
            schema_version=SCHEMA_VERSION,
            authority=False,
            confidence=(
                float(data["confidence"]) if data.get("confidence") is not None else None
            ),
            directionality=str(data.get("directionality") or "directed"),
            revision_condition=str(data.get("revision_condition") or ""),
            falsifier_condition=str(data.get("falsifier_condition") or ""),
            notes=str(data.get("notes") or ""),
            extra=dict(data.get("extra") or {}),
        )


def analogous_to_cannot_satisfy_causes(relation: RelationAsClaim | Mapping[str, Any]) -> None:
    """Hard requirement: ANALOGOUS_TO must never satisfy CAUSES."""
    if isinstance(relation, RelationAsClaim):
        rtype = relation.relation_type
        claimed = (relation.extra or {}).get("satisfies") if relation.extra else None
    else:
        rtype = str(relation.get("relation_type") or "")
        claimed = relation.get("satisfies")
        if claimed is None and isinstance(relation.get("extra"), Mapping):
            claimed = relation["extra"].get("satisfies")
    if rtype == "ANALOGOUS_TO" and (
        claimed == "CAUSES" or relation_claims_causes_satisfaction(relation)
    ):
        raise RelationSatisfactionError("ANALOGOUS_TO must never satisfy CAUSES")


def relation_claims_causes_satisfaction(relation: RelationAsClaim | Mapping[str, Any]) -> bool:
    if isinstance(relation, RelationAsClaim):
        flags = relation.extra or {}
        return bool(
            flags.get("satisfies_causes")
            or flags.get("satisfies") == "CAUSES"
            or flags.get("treated_as_causes")
        )
    return bool(
        relation.get("satisfies_causes")
        or relation.get("satisfies") == "CAUSES"
        or relation.get("treated_as_causes")
        or (
            isinstance(relation.get("extra"), Mapping)
            and (
                relation["extra"].get("satisfies_causes")
                or relation["extra"].get("satisfies") == "CAUSES"
                or relation["extra"].get("treated_as_causes")
            )
        )
    )


def relation_may_satisfy(observed_type: str, required_type: str) -> bool:
    """Type identity only — no cross-satisfaction (esp. ANALOGOUS_TO ↛ CAUSES)."""
    if observed_type not in RELATION_TYPES or required_type not in RELATION_TYPES:
        return False
    if observed_type == "ANALOGOUS_TO" and required_type == "CAUSES":
        return False
    return observed_type == required_type
