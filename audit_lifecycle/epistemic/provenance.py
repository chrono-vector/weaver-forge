"""Provenance lineage model and qualified independent-origin accounting (R4-A).

ArtifactCount ≠ IndependentEvidenceCount.
Self-declared independence does not increase IndependentEvidenceCount.
Derived copies retain lineage.
Missing provenance must prevent VERIFIED_SCOPE where provenance is required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .authority import enforce_non_authority
from .records import EpistemicStatusError
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.provenance.v1"

# Independence bases that qualify an origin. Self-declared alone does not qualify.
QUALIFIED_INDEPENDENCE_BASES = frozenset(
    {
        "DISTINCT_CUSTODY_CHAIN",
        "DISTINCT_OBSERVER",
        "DISTINCT_INSTRUMENT",
        "DISTINCT_METHOD",
        "EXTERNAL_WITNESS_RECEIPT",
        "INDEPENDENT_REPRODUCTION",
    }
)

SELF_DECLARED_INDEPENDENCE = "SELF_DECLARED"


@dataclass(frozen=True)
class IndependenceBasis:
    basis_id: str
    basis_kind: str
    refs: tuple[str, ...] = ()
    notes: str = ""

    def is_self_declared(self) -> bool:
        return self.basis_kind == SELF_DECLARED_INDEPENDENCE

    def is_qualified(self) -> bool:
        return self.basis_kind in QUALIFIED_INDEPENDENCE_BASES and not self.is_self_declared()

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis_id": self.basis_id,
            "basis_kind": self.basis_kind,
            "refs": list(self.refs),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IndependenceBasis":
        return cls(
            basis_id=str(data["basis_id"]),
            basis_kind=str(data["basis_kind"]),
            refs=tuple(data.get("refs") or ()),
            notes=str(data.get("notes") or ""),
        )


@dataclass(frozen=True)
class ProvenanceRecord:
    """Evidence metadata — not authority."""

    artifact_id: str
    digest: str
    source_id: str
    lineage_id: str
    schema_version: str = SCHEMA_VERSION
    authority: bool = False
    parent_sources: tuple[str, ...] = ()
    independence_basis_refs: tuple[IndependenceBasis, ...] = ()
    derived_from: str | None = None
    notes: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.authority is not False:
            raise ValueError("authority must be false")
        if not self.artifact_id or not self.digest or not self.source_id or not self.lineage_id:
            raise ValueError("provenance requires artifact_id, digest, source_id, lineage_id")

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "artifact_id": self.artifact_id,
            "digest": self.digest,
            "source_id": self.source_id,
            "lineage_id": self.lineage_id,
            "authority": False,
            "parent_sources": list(self.parent_sources),
            "independence_basis_refs": [b.to_dict() for b in self.independence_basis_refs],
            "notes": self.notes,
        }
        if self.derived_from is not None:
            d["derived_from"] = self.derived_from
        if self.extra:
            d["extra"] = dict(self.extra)
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def digest_of_record(self) -> str:
        return canonical_digest(self.to_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProvenanceRecord":
        enforce_non_authority(data)
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ValueError(
                f"provenance schema_version must be {SCHEMA_VERSION!r}"
            )
        bases_raw = data.get("independence_basis_refs") or ()
        bases = tuple(
            IndependenceBasis.from_dict(b) if isinstance(b, Mapping) else b
            for b in bases_raw
        )
        return cls(
            artifact_id=str(data["artifact_id"]),
            digest=str(data["digest"]),
            source_id=str(data["source_id"]),
            lineage_id=str(data["lineage_id"]),
            schema_version=SCHEMA_VERSION,
            authority=False,
            parent_sources=tuple(data.get("parent_sources") or ()),
            independence_basis_refs=bases,
            derived_from=(
                str(data["derived_from"]) if data.get("derived_from") is not None else None
            ),
            notes=str(data.get("notes") or ""),
            extra=dict(data.get("extra") or {}),
        )


@dataclass(frozen=True)
class IndependentOriginAccounting:
    artifact_count: int
    independent_evidence_count: int
    lineage_ids: tuple[str, ...]
    qualified_lineage_ids: tuple[str, ...]
    rejected_self_declared: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_count": self.artifact_count,
            "independent_evidence_count": self.independent_evidence_count,
            "lineage_ids": list(self.lineage_ids),
            "qualified_lineage_ids": list(self.qualified_lineage_ids),
            "rejected_self_declared": list(self.rejected_self_declared),
            "authority": False,
        }


def account_independent_origins(
    records: Sequence[ProvenanceRecord],
) -> IndependentOriginAccounting:
    """
    Multiple artifacts from one lineage count as one origin.
    Self-declared independence does not increase IndependentEvidenceCount.
    """
    by_lineage: dict[str, list[ProvenanceRecord]] = {}
    for r in records:
        by_lineage.setdefault(r.lineage_id, []).append(r)

    lineage_ids = tuple(sorted(by_lineage))
    qualified: list[str] = []
    rejected_self: list[str] = []

    for lid, group in sorted(by_lineage.items()):
        bases = [b for r in group for b in r.independence_basis_refs]
        if any(b.is_self_declared() for b in bases) and not any(b.is_qualified() for b in bases):
            rejected_self.append(lid)
            continue
        if any(b.is_qualified() for b in bases):
            qualified.append(lid)

    return IndependentOriginAccounting(
        artifact_count=len(records),
        independent_evidence_count=len(qualified),
        lineage_ids=lineage_ids,
        qualified_lineage_ids=tuple(qualified),
        rejected_self_declared=tuple(rejected_self),
    )


def require_provenance_for_verified_scope(
    epistemic_status: str,
    provenance_refs: Iterable[str] | None,
    *,
    provenance_required: bool = True,
) -> None:
    """Missing required provenance must prevent VERIFIED_SCOPE."""
    if epistemic_status != "VERIFIED_SCOPE":
        return
    if not provenance_required:
        return
    refs = list(provenance_refs or ())
    if not refs:
        raise EpistemicStatusError(
            "missing required provenance prevents VERIFIED_SCOPE"
        )


def status_for_insufficient_provenance(
    *,
    has_any_provenance: bool,
    ambiguous: bool = False,
) -> str:
    """Missing/insufficient provenance may produce AMBIGUOUS or UNRESOLVED."""
    if ambiguous:
        return "AMBIGUOUS"
    if not has_any_provenance:
        return "UNRESOLVED"
    return "AMBIGUOUS"
