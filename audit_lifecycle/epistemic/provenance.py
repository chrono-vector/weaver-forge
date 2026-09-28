"""Provenance lineage model and qualified independent-origin accounting (R4-A).

ArtifactCount ≠ IndependentEvidenceCount.
Self-declared independence does not increase IndependentEvidenceCount.
Derived copies retain lineage.
Missing provenance must prevent VERIFIED_SCOPE where provenance is required.

Independence qualification requires a known basis_kind AND non-empty
defensible reference(s). basis_kind alone never qualifies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .authority import enforce_non_authority
from .records import EpistemicStatusError
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.provenance.v1"

# Independence bases that may qualify an origin when backed by refs.
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

KNOWN_INDEPENDENCE_BASIS_KINDS = QUALIFIED_INDEPENDENCE_BASES | {
    SELF_DECLARED_INDEPENDENCE
}


class ProvenanceGraphError(ValueError):
    """Cross-record provenance graph validation failure."""


def _coerce_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
    """Reject string-as-iterable and malformed reference collections."""
    if value is None:
        return ()
    if isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a list/tuple of refs, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a list/tuple of refs")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} entries must be strings")
        text = item.strip()
        if not text:
            raise ValueError(f"{field_name} entries must be non-empty strings")
        out.append(text)
    # Deterministic set-like normalization for stored refs.
    return tuple(sorted(dict.fromkeys(out)))


@dataclass(frozen=True)
class IndependenceBasis:
    basis_id: str
    basis_kind: str
    refs: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not str(self.basis_id).strip():
            raise ValueError("independence basis_id must be non-empty")
        if not str(self.basis_kind).strip():
            raise ValueError("independence basis_kind must be non-empty")

    def is_self_declared(self) -> bool:
        return self.basis_kind == SELF_DECLARED_INDEPENDENCE

    def is_supported_kind(self) -> bool:
        return self.basis_kind in KNOWN_INDEPENDENCE_BASIS_KINDS

    def is_qualified(self) -> bool:
        """
        Qualify only with a known non-self-declared basis_kind AND
        non-empty defensible refs. basis_kind alone never qualifies.
        Unsupported / self-declared / empty-refs remain unqualified.
        """
        if self.is_self_declared():
            return False
        if self.basis_kind not in QUALIFIED_INDEPENDENCE_BASES:
            return False
        return bool(self.refs)

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
            refs=_coerce_str_refs(data.get("refs") or (), field_name="refs"),
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
        if isinstance(bases_raw, str):
            raise ValueError(
                "independence_basis_refs must be a list/tuple, not a string"
            )
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
            parent_sources=_coerce_str_refs(
                data.get("parent_sources") or (), field_name="parent_sources"
            ),
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


def validate_provenance_graph(records: Sequence[ProvenanceRecord]) -> None:
    """
    Bounded cross-record provenance validation (single validated set/graph).

    - derived_from parent must exist
    - derived artifact cannot manufacture a new lineage_id
    - parent_sources must resolve to source_id or artifact_id in the graph
    - derived_from cycles are rejected
    Does not federate across campaigns (R4-B).
    """
    by_artifact: dict[str, ProvenanceRecord] = {}
    for r in records:
        # Last write wins for lookup; duplicates handled in accounting.
        by_artifact[r.artifact_id] = r

    source_ids = {r.source_id for r in records}
    artifact_ids = set(by_artifact)

    for r in records:
        if r.derived_from is not None:
            if r.derived_from not in by_artifact:
                raise ProvenanceGraphError(
                    f"nonexistent parent reference: {r.derived_from!r}"
                )
            parent = by_artifact[r.derived_from]
            if r.lineage_id != parent.lineage_id:
                raise ProvenanceGraphError(
                    "derived artifact cannot manufacture a new independent lineage"
                )
        for ps in r.parent_sources:
            if ps not in source_ids and ps not in artifact_ids:
                raise ProvenanceGraphError(
                    f"nonexistent parent_sources reference: {ps!r}"
                )

    # Cycle detection along derived_from edges.
    for start in by_artifact:
        seen: set[str] = set()
        cur: str | None = start
        while cur is not None:
            if cur in seen:
                raise ProvenanceGraphError("provenance cycle detected")
            seen.add(cur)
            node = by_artifact.get(cur)
            if node is None:
                break
            cur = node.derived_from


def _origin_identity(record: ProvenanceRecord) -> tuple[str, str]:
    """Source identity used to collapse duplicate/claimed-lineage inflation."""
    return (record.digest, record.source_id)


def account_independent_origins(
    records: Sequence[ProvenanceRecord],
) -> IndependentOriginAccounting:
    """
    Multiple artifacts from one lineage / identical source identity count as one origin.
    Self-declared or empty-ref independence does not increase IndependentEvidenceCount.
    Counting operates only on qualified bases after graph validation.
    """
    if records:
        validate_provenance_graph(records)

    by_artifact = {r.artifact_id: r for r in records}
    lineage_ids = tuple(sorted({r.lineage_id for r in records}))

    # Union-find: same lineage_id, same (digest, source_id), or derived_from edge
    # all collapse to one origin — prevents lineage_id rename inflation.
    uf: dict[str, str] = {r.artifact_id: r.artifact_id for r in records}

    def find(x: str) -> str:
        while uf[x] != x:
            uf[x] = uf[uf[x]]
            x = uf[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            uf[rb] = ra

    by_lineage: dict[str, list[str]] = {}
    by_identity: dict[tuple[str, str], list[str]] = {}
    for r in records:
        by_lineage.setdefault(r.lineage_id, []).append(r.artifact_id)
        by_identity.setdefault(_origin_identity(r), []).append(r.artifact_id)
    for ids in by_lineage.values():
        for other in ids[1:]:
            union(ids[0], other)
    for ids in by_identity.values():
        for other in ids[1:]:
            union(ids[0], other)
    for r in records:
        if r.derived_from is not None and r.derived_from in by_artifact:
            union(r.artifact_id, r.derived_from)

    groups: dict[str, list[ProvenanceRecord]] = {}
    for r in records:
        groups.setdefault(find(r.artifact_id), []).append(r)

    qualified_lineages: list[str] = []
    rejected_self: list[str] = []
    qualified_roots = 0

    for group in groups.values():
        # Only root-level (non-derived) bases can qualify an origin.
        root_bases = [
            b
            for r in group
            if r.derived_from is None
            for b in r.independence_basis_refs
        ]
        has_qualified = any(b.is_qualified() for b in root_bases)
        has_self = any(b.is_self_declared() for b in root_bases)
        lineage_labels = sorted({r.lineage_id for r in group})

        if has_self and not has_qualified:
            rejected_self.extend(lineage_labels)
            continue
        if has_qualified:
            qualified_roots += 1
            qualified_lineages.append(lineage_labels[0])

    return IndependentOriginAccounting(
        artifact_count=len(records),
        independent_evidence_count=qualified_roots,
        lineage_ids=lineage_ids,
        qualified_lineage_ids=tuple(qualified_lineages),
        rejected_self_declared=tuple(sorted(set(rejected_self))),
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
