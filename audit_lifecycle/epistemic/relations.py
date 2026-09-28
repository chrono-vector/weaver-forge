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

DIRECTIONALITIES = frozenset({"directed", "bidirectional"})


class RelationSatisfactionError(ValueError):
    """Raised when a relation is used to satisfy an incompatible relation type."""


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    """Structured relation IDs/enums must already be nonempty strings."""
    if not isinstance(value, str):
        raise RelationSatisfactionError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    text = value.strip()
    if not text:
        raise RelationSatisfactionError(f"{field_name} must be a nonempty string")
    return text


def _require_optional_str(
    data: Mapping[str, Any],
    key: str,
    *,
    default: str,
) -> str:
    """Absent => default; present => must already be a string (no falsey coerce)."""
    if key not in data:
        return default
    value = data[key]
    if not isinstance(value, str):
        raise RelationSatisfactionError(
            f"{key} must be a string when set; got {type(value).__name__}"
        )
    return value


def _coerce_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
    """Strict collection typing — no None/False/0 → empty coercion."""
    if isinstance(value, str):
        raise RelationSatisfactionError(
            f"{field_name} must be a list/tuple of refs, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise RelationSatisfactionError(
            f"{field_name} must be a list/tuple of refs; "
            f"got {type(value).__name__}"
        )
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise RelationSatisfactionError(
                f"{field_name} entries must be strings; got {type(item).__name__}"
            )
        text = item.strip()
        if not text:
            raise RelationSatisfactionError(f"{field_name} entries must be non-empty")
        out.append(text)
    return tuple(sorted(dict.fromkeys(out)))


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
        if not isinstance(self.relation_id, str) or not self.relation_id.strip():
            raise RelationSatisfactionError("relation_id must be non-empty")
        if (
            not isinstance(self.source_claim_id, str)
            or not self.source_claim_id.strip()
            or not isinstance(self.target_claim_id, str)
            or not self.target_claim_id.strip()
        ):
            raise RelationSatisfactionError(
                "source_claim_id and target_claim_id must be non-empty"
            )
        if not isinstance(self.relation_type, str) or self.relation_type not in RELATION_TYPES:
            raise RelationSatisfactionError(
                f"unknown relation_type: {self.relation_type!r}"
            )
        if (
            not isinstance(self.epistemic_status, str)
            or self.epistemic_status not in EPISTEMIC_STATUSES
        ):
            raise EpistemicStatusError(
                f"unknown epistemic_status: {self.epistemic_status!r}"
            )
        if self.authority is not False:
            raise RelationSatisfactionError("authority must be false")
        if (
            not isinstance(self.directionality, str)
            or self.directionality not in DIRECTIONALITIES
        ):
            raise RelationSatisfactionError(
                f"unknown directionality: {self.directionality!r}"
            )
        if not isinstance(self.evidence_refs, tuple):
            raise RelationSatisfactionError(
                "evidence_refs must be a tuple of strings; "
                f"got {type(self.evidence_refs).__name__}"
            )
        if not self.evidence_refs:
            raise RelationSatisfactionError(
                "relation requires evidence_refs; missing evidence must not promote"
            )
        if not isinstance(self.scope, str) or not self.scope.strip():
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
        if "authority" not in data or data["authority"] is not False:
            raise RelationSatisfactionError("authority must be Boolean false")

        relation_type = data["relation_type"]
        if not isinstance(relation_type, str) or relation_type not in RELATION_TYPES:
            raise RelationSatisfactionError(
                f"unknown relation_type: {relation_type!r}"
            )
        epistemic_status = data["epistemic_status"]
        if (
            not isinstance(epistemic_status, str)
            or epistemic_status not in EPISTEMIC_STATUSES
        ):
            raise EpistemicStatusError(
                f"unknown epistemic_status: {epistemic_status!r}"
            )

        if "evidence_refs" not in data:
            raise RelationSatisfactionError(
                "relation requires evidence_refs; missing evidence must not promote"
            )
        evidence_refs = _coerce_str_refs(
            data["evidence_refs"], field_name="evidence_refs"
        )

        if "directionality" in data:
            directionality = data["directionality"]
            if not isinstance(directionality, str):
                raise RelationSatisfactionError(
                    "directionality must be a string when set; "
                    f"got {type(directionality).__name__}"
                )
        else:
            directionality = "directed"

        if "extra" in data:
            extra = data["extra"]
            if not isinstance(extra, Mapping):
                raise RelationSatisfactionError(
                    f"extra must be a mapping when set; got {type(extra).__name__}"
                )
        else:
            extra = {}

        confidence = data.get("confidence")
        if confidence is not None and not isinstance(confidence, (int, float)):
            raise RelationSatisfactionError("confidence must be a number when set")
        if isinstance(confidence, bool):
            raise RelationSatisfactionError("confidence must be a number when set")

        return cls(
            relation_id=_require_nonempty_str(
                data["relation_id"], field_name="relation_id"
            ),
            source_claim_id=_require_nonempty_str(
                data["source_claim_id"], field_name="source_claim_id"
            ),
            target_claim_id=_require_nonempty_str(
                data["target_claim_id"], field_name="target_claim_id"
            ),
            relation_type=relation_type,
            evidence_refs=evidence_refs,
            scope=_require_nonempty_str(data["scope"], field_name="scope"),
            epistemic_status=epistemic_status,
            schema_version=SCHEMA_VERSION,
            authority=False,
            confidence=(float(confidence) if confidence is not None else None),
            directionality=directionality,
            revision_condition=_require_optional_str(
                data, "revision_condition", default=""
            ),
            falsifier_condition=_require_optional_str(
                data, "falsifier_condition", default=""
            ),
            notes=_require_optional_str(data, "notes", default=""),
            extra=dict(extra),
        )


def analogous_to_cannot_satisfy_causes(relation: RelationAsClaim | Mapping[str, Any]) -> None:
    """Hard requirement: ANALOGOUS_TO must never satisfy CAUSES."""
    if isinstance(relation, RelationAsClaim):
        rtype = relation.relation_type
        claimed = (relation.extra or {}).get("satisfies") if relation.extra else None
    else:
        rtype = relation.get("relation_type")
        if not isinstance(rtype, str):
            rtype = ""
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
