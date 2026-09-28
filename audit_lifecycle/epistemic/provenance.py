"""Provenance lineage model and independent-origin accounting (R4-A).

ArtifactCount ≠ IndependentEvidenceCount.

IndependentEvidenceCount is gated by a code-defined admission status.
While INDEPENDENT_EVIDENCE_ADMISSION_STATUS is NOT_CONFIGURED:

  - independent_evidence_count is always 0
  - zero means "no trusted independent-evidence admission mechanism is
    configured" — NOT that evidence was disproven, and NOT that independent
    evidence does not exist in reality
  - no claimant-controlled value (basis_kind, refs, graph contents, digests,
    lineage, reciprocal refs, apparently independent roots, Campaign/policy/
    metadata inputs) may raise the count above zero

IndependenceBasis remains descriptive/advisory metadata only under
NOT_CONFIGURED; is_qualified() never returns a positive qualification.

Provenance graph validation, derivation, parent typing, cycle detection,
lineage continuity, and duplicate/source analysis are preserved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .authority import enforce_non_authority
from .records import EpistemicStatusError
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.provenance.v1"

# Code-defined — not configurable from claim/provenance/request/Campaign/
# policy/metadata/graph inputs.
INDEPENDENT_EVIDENCE_ADMISSION_STATUS = "NOT_CONFIGURED"

PARENT_KIND_ARTIFACT = "ARTIFACT"
PARENT_KIND_SOURCE = "SOURCE"
PARENT_KINDS = frozenset({PARENT_KIND_ARTIFACT, PARENT_KIND_SOURCE})

# Independence bases kept as descriptive metadata only under NOT_CONFIGURED.
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


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    """R1-N1: structured identifiers must already be nonempty strings."""
    if not isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    text = value.strip()
    if not text:
        raise ValueError(f"{field_name} must be a nonempty string")
    return text


def _require_optional_nonempty_str(value: Any, *, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_nonempty_str(value, field_name=field_name)


def _coerce_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
    """Strict collection typing for present reference fields.

    A present field must already be a list/tuple. Falsey non-collections
    (None / False / 0 / "") are rejected — they must not become ().
    Absent optional fields are handled by callers via documented defaults.
    """
    if isinstance(value, str):
        raise ValueError(
            f"{field_name} must be a list/tuple of refs, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"{field_name} must be a list/tuple of refs; "
            f"got {type(value).__name__}"
        )
    out: list[str] = []
    for item in value:
        out.append(_require_nonempty_str(item, field_name=f"{field_name} entry"))
    # Deterministic set-like normalization for stored refs.
    return tuple(sorted(dict.fromkeys(out)))


@dataclass(frozen=True)
class ValidatedBasisRef:
    """Defensible basis reference bound to accepted provenance structure."""

    ref_kind: str
    ref_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.ref_kind, str) or self.ref_kind not in VALIDATED_BASIS_REF_KINDS:
            raise ValueError(
                f"unsupported validated basis ref_kind: {self.ref_kind!r}"
            )
        if not isinstance(self.ref_id, str) or not self.ref_id.strip():
            raise ValueError("validated basis ref_id must be non-empty string")

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
        return cls(
            ref_kind=_require_nonempty_str(data["ref_kind"], field_name="ref_kind"),
            ref_id=_require_nonempty_str(data["ref_id"], field_name="ref_id"),
        )


def _coerce_basis_refs(value: Any) -> tuple[ValidatedBasisRef, ...]:
    """
    Parse independence basis refs.

    Only structured ValidatedBasisRef mappings are accepted.
    Bare strings / scalars / falsey non-collections cannot create a
    defensible basis and must not coerce to an empty collection.
    """
    if isinstance(value, str):
        raise ValueError("refs must be a list/tuple of validated basis refs, not a string")
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            "refs must be a list/tuple of validated basis refs; "
            f"got {type(value).__name__}"
        )
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
    """Descriptive independence metadata. Not an admission signal under NOT_CONFIGURED."""

    basis_id: str
    basis_kind: str
    refs: tuple[ValidatedBasisRef, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.basis_id, str) or not self.basis_id.strip():
            raise ValueError("independence basis_id must be non-empty string")
        if not isinstance(self.basis_kind, str) or not self.basis_kind.strip():
            raise ValueError("independence basis_kind must be non-empty string")
        if not isinstance(self.refs, tuple):
            raise ValueError(
                "refs must be a tuple of ValidatedBasisRef; "
                f"got {type(self.refs).__name__}"
            )
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
        Positive qualification is disabled while admission status is
        NOT_CONFIGURED. IndependenceBasis remains descriptive only.

        Zero admission does not mean evidence was disproven.
        """
        if INDEPENDENT_EVIDENCE_ADMISSION_STATUS == "NOT_CONFIGURED":
            return False
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
            basis_id = data["basis_id"]
            basis_kind = data["basis_kind"]
        except KeyError as e:
            raise ValueError(
                f"independence basis missing required field: {e.args[0]}"
            ) from e
        notes = data.get("notes", "")
        if notes is None:
            notes = ""
        if not isinstance(notes, str):
            raise ValueError("independence basis notes must be a string when set")
        if "refs" in data:
            refs = _coerce_basis_refs(data["refs"])
        else:
            refs = ()
        return cls(
            basis_id=_require_nonempty_str(basis_id, field_name="basis_id"),
            basis_kind=_require_nonempty_str(basis_kind, field_name="basis_kind"),
            refs=refs,
            notes=notes,
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
        for name in ("artifact_id", "digest", "source_id", "lineage_id"):
            val = getattr(self, name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(
                    "provenance requires nonempty string artifact_id, digest, "
                    "source_id, lineage_id"
                )
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(
                f"provenance schema_version must be {SCHEMA_VERSION!r}"
            )
        if self.derived_from is not None and (
            not isinstance(self.derived_from, str) or not self.derived_from.strip()
        ):
            raise ValueError("derived_from must be a nonempty string when set")
        if not isinstance(self.parent_sources, tuple):
            raise ValueError(
                "parent_sources must be a tuple of strings; "
                f"got {type(self.parent_sources).__name__}"
            )
        for ps in self.parent_sources:
            if not isinstance(ps, str) or not ps.strip():
                raise ValueError("parent_sources entries must be nonempty strings")
        if not isinstance(self.independence_basis_refs, tuple):
            raise ValueError(
                "independence_basis_refs must be a tuple of IndependenceBasis; "
                f"got {type(self.independence_basis_refs).__name__}"
            )
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
        if "authority" not in data or data["authority"] is not False:
            raise ValueError("authority must be Boolean false")
        if "independence_basis_refs" in data:
            bases_raw = data["independence_basis_refs"]
            if isinstance(bases_raw, str):
                raise ValueError(
                    "independence_basis_refs must be a list/tuple, not a string"
                )
            if not isinstance(bases_raw, (list, tuple)):
                raise ValueError(
                    "independence_basis_refs must be a list/tuple of mappings; "
                    f"got {type(bases_raw).__name__}"
                )
            bases = tuple(_parse_independence_basis_member(b) for b in bases_raw)
        else:
            bases = ()
        notes = data.get("notes", "")
        if notes is None:
            notes = ""
        if not isinstance(notes, str):
            raise ValueError("notes must be a string when set")
        extra = data["extra"] if "extra" in data else {}
        if extra is None:
            extra = {}
        if not isinstance(extra, Mapping):
            raise ValueError("extra must be a mapping when set")
        if "parent_sources" in data:
            parent_sources = _coerce_str_refs(
                data["parent_sources"], field_name="parent_sources"
            )
        else:
            parent_sources = ()
        return cls(
            artifact_id=_require_nonempty_str(
                data["artifact_id"], field_name="artifact_id"
            ),
            digest=_require_nonempty_str(data["digest"], field_name="digest"),
            source_id=_require_nonempty_str(data["source_id"], field_name="source_id"),
            lineage_id=_require_nonempty_str(
                data["lineage_id"], field_name="lineage_id"
            ),
            schema_version=SCHEMA_VERSION,
            authority=False,
            parent_sources=parent_sources,
            independence_basis_refs=bases,
            derived_from=_require_optional_nonempty_str(
                data.get("derived_from"), field_name="derived_from"
            ),
            notes=notes,
            extra=dict(extra),
        )


@dataclass(frozen=True)
class ResolvedParentEdge:
    """One resolved parent edge in the unified provenance graph."""

    from_artifact_id: str
    parent_kind: str
    parent_id: str

    def __post_init__(self) -> None:
        if self.parent_kind not in PARENT_KINDS:
            raise ProvenanceGraphError(
                f"unsupported parent_kind: {self.parent_kind!r}"
            )


@dataclass(frozen=True)
class IndependentOriginAccounting:
    artifact_count: int
    independent_evidence_count: int
    lineage_ids: tuple[str, ...]
    qualified_lineage_ids: tuple[str, ...]
    rejected_self_declared: tuple[str, ...] = ()
    independent_evidence_admission_status: str = (
        INDEPENDENT_EVIDENCE_ADMISSION_STATUS
    )

    def __post_init__(self) -> None:
        # Local invariant under NOT_CONFIGURED: no alternate admission path.
        if self.independent_evidence_count != 0:
            raise ValueError(
                "independent_evidence_count must be 0 while admission is "
                "NOT_CONFIGURED"
            )
        if self.qualified_lineage_ids != ():
            raise ValueError(
                "qualified_lineage_ids must be empty while admission is "
                "NOT_CONFIGURED"
            )
        if (
            self.independent_evidence_admission_status
            != INDEPENDENT_EVIDENCE_ADMISSION_STATUS
        ):
            raise ValueError(
                "independent_evidence_admission_status must be "
                f"{INDEPENDENT_EVIDENCE_ADMISSION_STATUS!r}"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_count": self.artifact_count,
            "independent_evidence_count": self.independent_evidence_count,
            "lineage_ids": list(self.lineage_ids),
            "qualified_lineage_ids": list(self.qualified_lineage_ids),
            "rejected_self_declared": list(self.rejected_self_declared),
            "independent_evidence_admission_status": (
                self.independent_evidence_admission_status
            ),
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
    resolved_edges: tuple[ResolvedParentEdge, ...]

    @classmethod
    def build(cls, records: Sequence[ProvenanceRecord]) -> "ProvenanceGraphIndex":
        by_artifact: dict[str, ProvenanceRecord] = {}
        for r in records:
            if r.artifact_id in by_artifact:
                raise ProvenanceGraphError(
                    f"duplicate artifact_id: {r.artifact_id!r}"
                )
            by_artifact[r.artifact_id] = r
        by_source: dict[str, list[str]] = {}
        for r in records:
            by_source.setdefault(r.source_id, []).append(r.artifact_id)
        index_partial = cls(
            by_artifact=by_artifact,
            artifact_ids=frozenset(by_artifact),
            source_ids=frozenset(r.source_id for r in records),
            digests=frozenset(r.digest for r in records),
            by_source={k: tuple(v) for k, v in by_source.items()},
            resolved_edges=(),
        )
        edges = tuple(resolve_parent_edges(records, index_partial))
        return cls(
            by_artifact=index_partial.by_artifact,
            artifact_ids=index_partial.artifact_ids,
            source_ids=index_partial.source_ids,
            digests=index_partial.digests,
            by_source=index_partial.by_source,
            resolved_edges=edges,
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


def _resolve_parent_id(
    parent_id: str,
    index: ProvenanceGraphIndex,
    *,
    field_name: str,
) -> tuple[str, str]:
    """Resolve an untyped parent id to (parent_kind, parent_id). Fail closed.

    SOURCE parent resolution requires exactly one canonical artifact:
      0 matches  => missing
      1 match    => valid
      >1 matches => ambiguous (no first/last/arbitrary selection)
    """
    in_artifacts = parent_id in index.artifact_ids
    in_sources = parent_id in index.source_ids
    if in_artifacts and in_sources:
        raise ProvenanceGraphError(
            f"ambiguous source parent: {parent_id!r} matches both ARTIFACT and SOURCE"
        )
    if in_artifacts:
        return PARENT_KIND_ARTIFACT, parent_id
    if in_sources:
        arts = index.by_source.get(parent_id, ())
        if len(arts) == 0:
            raise ProvenanceGraphError(
                f"nonexistent {field_name} SOURCE reference: {parent_id!r}"
            )
        if len(arts) > 1:
            raise ProvenanceGraphError(
                f"ambiguous SOURCE parent: {parent_id!r} resolves to "
                f"{len(arts)} artifacts; exactly one required"
            )
        return PARENT_KIND_SOURCE, parent_id
    raise ProvenanceGraphError(
        f"nonexistent {field_name} reference: {parent_id!r}"
    )


def resolve_parent_edges(
    records: Sequence[ProvenanceRecord],
    index: ProvenanceGraphIndex,
) -> list[ResolvedParentEdge]:
    """
    Normalize derived_from + parent_sources into one typed resolved edge set.

    Parent kinds are ARTIFACT or SOURCE. Ambiguous / missing resolution fails.
    """
    edges: list[ResolvedParentEdge] = []
    for r in records:
        if r.derived_from is not None:
            kind, pid = _resolve_parent_id(
                r.derived_from, index, field_name="derived_from"
            )
            if kind != PARENT_KIND_ARTIFACT:
                raise ProvenanceGraphError(
                    f"derived_from must resolve to ARTIFACT; got SOURCE {pid!r}"
                )
            if pid == r.artifact_id:
                raise ProvenanceGraphError(
                    f"self-edge forbidden: {r.artifact_id!r}"
                )
            edges.append(
                ResolvedParentEdge(
                    from_artifact_id=r.artifact_id,
                    parent_kind=PARENT_KIND_ARTIFACT,
                    parent_id=pid,
                )
            )
        for ps in r.parent_sources:
            kind, pid = _resolve_parent_id(ps, index, field_name="parent_sources")
            if kind == PARENT_KIND_ARTIFACT and pid == r.artifact_id:
                raise ProvenanceGraphError(
                    f"self-edge forbidden: {r.artifact_id!r}"
                )
            if kind == PARENT_KIND_SOURCE and pid == r.source_id:
                raise ProvenanceGraphError(
                    f"self-edge forbidden: {r.artifact_id!r} -> SOURCE {pid!r}"
                )
            edges.append(
                ResolvedParentEdge(
                    from_artifact_id=r.artifact_id,
                    parent_kind=kind,
                    parent_id=pid,
                )
            )
    return edges


def _cycle_nodes_and_adjacency(
    records: Sequence[ProvenanceRecord],
    edges: Sequence[ResolvedParentEdge],
) -> tuple[set[tuple[str, str]], dict[tuple[str, str], list[tuple[str, str]]]]:
    """
    Unified directed graph over ARTIFACT and SOURCE nodes for cycle detection.

    Edges from the same resolved parent set:
      - ARTIFACT parent: ARTIFACT(from) → ARTIFACT(parent)
      - SOURCE parent:   ARTIFACT(from) → SOURCE(parent)
      - production:      SOURCE(source_id) → ARTIFACT(artifact_id)

    Production edges expose source cycles and mixed artifact/source cycles.
    """
    nodes: set[tuple[str, str]] = set()
    adjacency: dict[tuple[str, str], list[tuple[str, str]]] = {}

    def add_edge(src: tuple[str, str], dst: tuple[str, str]) -> None:
        nodes.add(src)
        nodes.add(dst)
        adjacency.setdefault(src, []).append(dst)

    for r in records:
        art = (PARENT_KIND_ARTIFACT, r.artifact_id)
        src = (PARENT_KIND_SOURCE, r.source_id)
        nodes.add(art)
        nodes.add(src)
        add_edge(src, art)

    for e in edges:
        src = (PARENT_KIND_ARTIFACT, e.from_artifact_id)
        dst = (e.parent_kind, e.parent_id)
        add_edge(src, dst)

    return nodes, adjacency


def validate_provenance_graph(records: Sequence[ProvenanceRecord]) -> ProvenanceGraphIndex:
    """
    Bounded cross-record provenance validation (single validated set/graph).

    Builds ONE resolved edge set used for cycle detection, lineage continuity,
    root selection, and origin collapse support.

    Rejects: duplicate artifact_id, self-edge, nonexistent parent, ambiguous
    source parent, artifact/source/mixed cycles of any length, and derived
    lineage manufacturing.

    Does not federate across campaigns (R4-B).
    """
    index = ProvenanceGraphIndex.build(records)
    by_artifact = index.by_artifact
    edges = index.resolved_edges

    for r in records:
        if r.derived_from is not None:
            parent = by_artifact[r.derived_from]
            if r.lineage_id != parent.lineage_id:
                raise ProvenanceGraphError(
                    "derived artifact cannot manufacture a new independent lineage"
                )

    nodes, adjacency = _cycle_nodes_and_adjacency(records, edges)
    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()

    def dfs(node: tuple[str, str]) -> None:
        if node in visiting:
            raise ProvenanceGraphError("provenance cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for nxt in adjacency.get(node, ()):
            dfs(nxt)
        visiting.remove(node)
        visited.add(node)

    for start in nodes:
        dfs(start)

    return index


def _origin_identity(record: ProvenanceRecord) -> tuple[str, str]:
    """Source identity used to collapse duplicate/claimed-lineage inflation."""
    return (record.digest, record.source_id)


def account_independent_origins(
    records: Sequence[ProvenanceRecord],
) -> IndependentOriginAccounting:
    """
    Account artifacts and lineages on the validated provenance graph.

    Under NOT_CONFIGURED admission status:
      independent_evidence_count is always 0
      qualified_lineage_ids is always ()
      no claimant-controlled basis/graph value may raise the count

    Zero means admission is not configured — not that evidence was disproven.
    Graph validation, lineage ids, and self-declared rejection metadata remain.
    """
    index: ProvenanceGraphIndex | None = None
    if records:
        index = validate_provenance_graph(records)

    lineage_ids = tuple(sorted({r.lineage_id for r in records}))

    rejected_self: list[str] = []
    if index is not None and records:
        # Preserve descriptive self-declared tracking and collapse analysis on
        # the same resolved edge set — without admitting independent evidence.
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
        for edge in index.resolved_edges:
            if edge.parent_kind == PARENT_KIND_ARTIFACT:
                if edge.parent_id in uf:
                    union(edge.from_artifact_id, edge.parent_id)
            elif edge.parent_kind == PARENT_KIND_SOURCE:
                for art_id in index.by_source.get(edge.parent_id, ()):
                    if art_id in uf:
                        union(edge.from_artifact_id, art_id)

        groups: dict[str, list[ProvenanceRecord]] = {}
        for r in records:
            groups.setdefault(find(r.artifact_id), []).append(r)

        for group in groups.values():
            root_records = [
                r
                for r in group
                if r.derived_from is None
                and not any(
                    e.from_artifact_id == r.artifact_id
                    and e.parent_kind == PARENT_KIND_ARTIFACT
                    for e in index.resolved_edges
                )
            ]
            root_bases = [
                b for r in root_records for b in r.independence_basis_refs
            ]
            has_self = any(b.is_self_declared() for b in root_bases)
            # is_qualified is always False under NOT_CONFIGURED.
            has_qualified = any(
                b.is_qualified(graph_index=index, claimant=r)
                for r in root_records
                for b in r.independence_basis_refs
            )
            lineage_labels = sorted({r.lineage_id for r in group})
            if has_self and not has_qualified:
                rejected_self.extend(lineage_labels)

    # Admission gate: code-defined zero-count model.
    return IndependentOriginAccounting(
        artifact_count=len(records),
        independent_evidence_count=0,
        lineage_ids=lineage_ids,
        qualified_lineage_ids=(),
        rejected_self_declared=tuple(sorted(set(rejected_self))),
        independent_evidence_admission_status=INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
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
    if provenance_refs is None:
        refs: list[str] = []
    elif isinstance(provenance_refs, str):
        raise EpistemicStatusError(
            "provenance_refs must be a list/tuple of refs, not a string"
        )
    else:
        refs = list(provenance_refs)
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
