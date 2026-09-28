"""Provenance lineage model and qualified independent-origin accounting (R4-A).

ArtifactCount ≠ IndependentEvidenceCount.
Self-declared independence does not increase IndependentEvidenceCount.
Derived copies retain lineage.
Missing provenance must prevent VERIFIED_SCOPE where provenance is required.

Independence qualification requires a known basis_kind AND defensible
validated basis reference(s) that resolve against the accepted provenance
graph. basis_kind + nonempty self-asserted strings never qualify.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .authority import enforce_non_authority
from .records import EpistemicStatusError
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.provenance.v1"

# Independence bases that may qualify an origin when backed by validated refs.
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

# Structured basis-ref kinds accepted inside the bounded R4-A provenance model.
# These bind to entities already present in the validated provenance graph —
# not external attestation infrastructure.
VALIDATED_BASIS_REF_KINDS = frozenset(
    {
        "PROVENANCE_ARTIFACT",
        "PROVENANCE_SOURCE",
        "PROVENANCE_DIGEST",
    }
)


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
class ValidatedBasisRef:
    """Defensible basis reference bound to accepted provenance structure."""

    ref_kind: str
    ref_id: str

    def __post_init__(self) -> None:
        if self.ref_kind not in VALIDATED_BASIS_REF_KINDS:
            raise ValueError(
                f"unsupported validated basis ref_kind: {self.ref_kind!r}"
            )
        if not str(self.ref_id).strip():
            raise ValueError("validated basis ref_id must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        return {"ref_kind": self.ref_kind, "ref_id": self.ref_id}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ValidatedBasisRef":
        if not isinstance(data, Mapping):
            raise ValueError("validated basis ref must be a mapping")
        if "ref_kind" not in data or "ref_id" not in data:
            raise ValueError(
                "validated basis ref requires ref_kind and ref_id"
            )
        return cls(ref_kind=str(data["ref_kind"]), ref_id=str(data["ref_id"]).strip())


def _coerce_basis_refs(value: Any) -> tuple[ValidatedBasisRef, ...]:
    """
    Parse independence basis refs.

    Only structured ValidatedBasisRef mappings are accepted.
    Bare strings / scalars / arrays cannot create a defensible basis.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        raise ValueError("refs must be a list/tuple of validated basis refs, not a string")
    if not isinstance(value, (list, tuple)):
        raise ValueError("refs must be a list/tuple of validated basis refs")
    out: list[ValidatedBasisRef] = []
    seen: set[tuple[str, str]] = set()
    for item in value:
        if isinstance(item, ValidatedBasisRef):
            ref = item
        elif isinstance(item, Mapping):
            ref = ValidatedBasisRef.from_dict(item)
        else:
            raise ValueError(
                "refs entries must be validated basis ref mappings "
                f"(ref_kind/ref_id); got {type(item).__name__}"
            )
        key = (ref.ref_kind, ref.ref_id)
        if key in seen:
            continue
        seen.add(key)
        out.append(ref)
    return tuple(sorted(out, key=lambda r: (r.ref_kind, r.ref_id)))


@dataclass(frozen=True)
class IndependenceBasis:
    basis_id: str
    basis_kind: str
    refs: tuple[ValidatedBasisRef, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not str(self.basis_id).strip():
            raise ValueError("independence basis_id must be non-empty")
        if not str(self.basis_kind).strip():
            raise ValueError("independence basis_kind must be non-empty")
        # Normalize accidental raw tuples of dicts from direct construction.
        if self.refs and not all(isinstance(r, ValidatedBasisRef) for r in self.refs):
            object.__setattr__(self, "refs", _coerce_basis_refs(list(self.refs)))

    def is_self_declared(self) -> bool:
        return self.basis_kind == SELF_DECLARED_INDEPENDENCE

    def is_supported_kind(self) -> bool:
        return self.basis_kind in KNOWN_INDEPENDENCE_BASIS_KINDS

    def is_qualified(
        self,
        *,
        graph_index: "ProvenanceGraphIndex | None" = None,
        claimant: "ProvenanceRecord | None" = None,
    ) -> bool:
        """
        Qualify only with a known non-self-declared basis_kind AND
        defensible validated refs that resolve in the provenance graph
        to entities other than the claimant itself.

        basis_kind + nonempty self-asserted strings/refs alone never qualify.
        Without graph resolution context, returns False.
        """
        if self.is_self_declared():
            return False
        if self.basis_kind not in QUALIFIED_INDEPENDENCE_BASES:
            return False
        if not self.refs:
            return False
        if graph_index is None or claimant is None:
            return False
        return graph_index.basis_refs_resolve(self.refs, claimant=claimant)

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis_id": self.basis_id,
            "basis_kind": self.basis_kind,
            "refs": [r.to_dict() for r in self.refs],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "IndependenceBasis":
        if not isinstance(data, Mapping):
            raise ValueError("independence basis must be a mapping")
        try:
            basis_id = str(data["basis_id"])
            basis_kind = str(data["basis_kind"])
        except KeyError as e:
            raise ValueError(
                f"independence basis missing required field: {e.args[0]}"
            ) from e
        return cls(
            basis_id=basis_id,
            basis_kind=basis_kind,
            refs=_coerce_basis_refs(data.get("refs") or ()),
            notes=str(data.get("notes") or ""),
        )


def _parse_independence_basis_member(item: Any) -> IndependenceBasis:
    """R4A-R1-N1: every independence_basis_refs member must be a mapping/record."""
    if isinstance(item, IndependenceBasis):
        return item
    if isinstance(item, Mapping):
        return IndependenceBasis.from_dict(item)
    raise ValueError(
        "independence_basis_refs members must be mappings/records; "
        f"got {type(item).__name__}"
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
        for b in self.independence_basis_refs:
            if not isinstance(b, IndependenceBasis):
                raise ValueError(
                    "independence_basis_refs members must be IndependenceBasis records"
                )

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
        if not isinstance(bases_raw, (list, tuple)):
            raise ValueError(
                "independence_basis_refs must be a list/tuple of mappings"
            )
        bases = tuple(_parse_independence_basis_member(b) for b in bases_raw)
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


@dataclass(frozen=True)
class ProvenanceGraphIndex:
    """Accepted provenance entities available for basis-ref resolution."""

    by_artifact: Mapping[str, ProvenanceRecord]
    artifact_ids: frozenset[str]
    source_ids: frozenset[str]
    digests: frozenset[str]
    by_source: Mapping[str, tuple[str, ...]]

    @classmethod
    def build(cls, records: Sequence[ProvenanceRecord]) -> "ProvenanceGraphIndex":
        by_artifact: dict[str, ProvenanceRecord] = {}
        for r in records:
            by_artifact[r.artifact_id] = r
        by_source: dict[str, list[str]] = {}
        for r in records:
            by_source.setdefault(r.source_id, []).append(r.artifact_id)
        return cls(
            by_artifact=by_artifact,
            artifact_ids=frozenset(by_artifact),
            source_ids=frozenset(r.source_id for r in records),
            digests=frozenset(r.digest for r in records),
            by_source={k: tuple(v) for k, v in by_source.items()},
        )

    def claimant_forbidden_ids(self, claimant: ProvenanceRecord) -> frozenset[str]:
        """Self-identity tokens that cannot defend the claimant's independence."""
        return frozenset(
            {
                claimant.artifact_id,
                claimant.source_id,
                claimant.digest,
                claimant.lineage_id,
            }
        )

    def basis_refs_resolve(
        self,
        refs: Sequence[ValidatedBasisRef],
        *,
        claimant: ProvenanceRecord,
    ) -> bool:
        """True when every ref resolves to a non-self accepted graph entity."""
        if not refs:
            return False
        forbidden = self.claimant_forbidden_ids(claimant)
        for ref in refs:
            if ref.ref_id in forbidden:
                return False
            if ref.ref_kind == "PROVENANCE_ARTIFACT":
                if ref.ref_id not in self.artifact_ids:
                    return False
            elif ref.ref_kind == "PROVENANCE_SOURCE":
                if ref.ref_id not in self.source_ids:
                    return False
            elif ref.ref_kind == "PROVENANCE_DIGEST":
                if ref.ref_id not in self.digests:
                    return False
            else:
                return False
        return True


def _derivation_edges(
    records: Sequence[ProvenanceRecord],
    index: ProvenanceGraphIndex,
    *,
    for_cycles: bool,
) -> list[tuple[str, str]]:
    """
    Edges for cycle detection / origin collapsing.

    - derived_from always participates
    - parent_sources targeting an artifact_id always participates
    - parent_sources targeting a source_id collapses origins (union) but does
      not create sibling cycle edges among co-sourced artifacts
    """
    edges: list[tuple[str, str]] = []
    for r in records:
        if r.derived_from is not None:
            edges.append((r.artifact_id, r.derived_from))
        for ps in r.parent_sources:
            if ps in index.artifact_ids:
                edges.append((r.artifact_id, ps))
            elif ps in index.by_source and not for_cycles:
                for art_id in index.by_source[ps]:
                    if art_id != r.artifact_id:
                        edges.append((r.artifact_id, art_id))
    return edges


def validate_provenance_graph(records: Sequence[ProvenanceRecord]) -> None:
    """
    Bounded cross-record provenance validation (single validated set/graph).

    - derived_from parent must exist
    - derived artifact cannot manufacture a new lineage_id
    - parent_sources must resolve to source_id or artifact_id in the graph
    - cycles across derived_from and parent_sources→artifact edges are rejected
    Does not federate across campaigns (R4-B).
    """
    index = ProvenanceGraphIndex.build(records)
    by_artifact = index.by_artifact

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
            if ps not in index.source_ids and ps not in index.artifact_ids:
                raise ProvenanceGraphError(
                    f"nonexistent parent_sources reference: {ps!r}"
                )
            # parent_sources edges collapse origins during accounting; they do
            # not permit silent lineage manufacturing via derived_from rules.
            # Separate claimed lineage_ids linked by parent_sources are unified
            # rather than counted as independent origins.

    # Cycle detection along derived_from + parent_sources→artifact edges.
    edges = _derivation_edges(records, index, for_cycles=True)
    adjacency: dict[str, list[str]] = {r.artifact_id: [] for r in records}
    for src, dst in edges:
        if src in adjacency:
            adjacency[src].append(dst)

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> None:
        if node in visiting:
            raise ProvenanceGraphError("provenance cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for nxt in adjacency.get(node, ()):
            if nxt in adjacency or nxt in by_artifact:
                dfs(nxt)
        visiting.remove(node)
        visited.add(node)

    for start in list(adjacency):
        dfs(start)


def _origin_identity(record: ProvenanceRecord) -> tuple[str, str]:
    """Source identity used to collapse duplicate/claimed-lineage inflation."""
    return (record.digest, record.source_id)


def account_independent_origins(
    records: Sequence[ProvenanceRecord],
) -> IndependentOriginAccounting:
    """
    Multiple artifacts from one lineage / identical source identity count as one origin.
    Self-declared or empty/self-asserted independence does not increase
    IndependentEvidenceCount.
    Counting operates only on graph-resolved qualified bases after validation.
    parent_sources participate in origin collapsing (same as derived_from).
    """
    if records:
        validate_provenance_graph(records)

    index = ProvenanceGraphIndex.build(records)
    by_artifact = index.by_artifact
    lineage_ids = tuple(sorted({r.lineage_id for r in records}))

    # Union-find: same lineage_id, same (digest, source_id), derived_from, or
    # parent_sources edges all collapse to one origin.
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
    for src, dst in _derivation_edges(records, index, for_cycles=False):
        if src in uf and dst in uf:
            union(src, dst)

    groups: dict[str, list[ProvenanceRecord]] = {}
    for r in records:
        groups.setdefault(find(r.artifact_id), []).append(r)

    qualified_lineages: list[str] = []
    rejected_self: list[str] = []
    qualified_roots = 0

    for group in groups.values():
        # Only root-level (non-derived, no parent artifact edge) bases qualify.
        # Records linked solely via parent_sources source_id still participate
        # in the collapsed group; roots are those without outbound derivation.
        root_records = [
            r
            for r in group
            if r.derived_from is None
            and not any(ps in by_artifact for ps in r.parent_sources)
        ]
        if not root_records:
            # Fully derived group: inherit non-qualification (copies retain lineage).
            root_records = []

        root_bases = [
            b
            for r in root_records
            for b in r.independence_basis_refs
        ]
        has_qualified = any(
            b.is_qualified(graph_index=index, claimant=r)
            for r in root_records
            for b in r.independence_basis_refs
        )
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
