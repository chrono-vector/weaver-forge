"""R4-B Immutable Reviewer Disagreement Records — non-authoritative.

Disagreement records are never rewritten into "resolved".
Resolution creates a NEW successor record that references the prior digest.

Canonical verification path:

  strict_parse_record → filename/content binding → expected-set equality
  → verify_chain_graph

AMBIGUOUS and UNRESOLVED are valid outcomes. Do not force consensus.
Reviewer positions remain explicit — no synthetic winner, no authority.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .authority import enforce_non_authority
from .serialize import canonical_digest, canonical_dumps

SCHEMA_VERSION = "r4.epistemic.review-disagreement.v1"
REVIEWS_DIRNAME = "reviews"

DISAGREEMENT_STATUSES = frozenset(
    {
        "OPEN",
        "AMBIGUOUS",
        "UNRESOLVED",
        "RESOLVED_BY_SUCCESSOR",
    }
)

INITIAL_STATUSES = frozenset({"OPEN", "AMBIGUOUS", "UNRESOLVED"})

DISAGREEMENT_CATEGORIES = frozenset(
    {
        "SPEC_AMBIGUITY",
        "CATEGORY_OVERLAP",
        "MISSING_EVIDENCE",
        "PROVENANCE_DISPUTE",
        "RELATION_DISPUTE",
        "SCOPE_DISPUTE",
        "REVIEWER_INTERPRETATION",
        "GENUINELY_AMBIGUOUS",
    }
)

REVIEWER_POSITION_VALUES = frozenset(
    {
        "PASS",
        "FAIL",
        "INCONCLUSIVE",
        "BLOCKED",
        "ABSTAIN",
        "AMBIGUOUS",
        "UNRESOLVED",
    }
)

RECORD_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "schema",
        "authority",
        "disagreement_id",
        "subject_id",
        "reviewer_positions",
        "scope",
        "category",
        "status",
        "reason",
        "evidence_refs",
        "created_from",
        "prior_record_digest",
        "successor_of",
        "resolution_note",
        "record_digest",
        "extra",
    }
)

POSITION_ALLOWED_KEYS = frozenset(
    {"reviewer_id", "position", "label", "notes"}
)

_SHA256_HEX = frozenset("0123456789abcdef")


class ReviewDisagreementError(ValueError):
    """Malformed disagreement record or immutability violation."""


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ReviewDisagreementError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    if not value.strip():
        raise ReviewDisagreementError(f"{field_name} must be a nonempty string")
    return value


def _require_sha256(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ReviewDisagreementError(
            f"{field_name} must be a lowercase sha256 hex digest; "
            f"got {type(value).__name__}"
        )
    if len(value) != 64 or any(c not in _SHA256_HEX for c in value):
        raise ReviewDisagreementError(
            f"{field_name} must be a lowercase sha256 hex digest"
        )
    return value


def _require_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        raise ReviewDisagreementError(
            f"{field_name} must be a list/tuple of refs, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise ReviewDisagreementError(
            f"{field_name} must be a list/tuple of refs; "
            f"got {type(value).__name__}"
        )
    out: list[str] = []
    for item in value:
        out.append(_require_nonempty_str(item, field_name=f"{field_name} entry"))
    return tuple(sorted(dict.fromkeys(out)))


def _require_schema_aliases(data: Mapping[str, Any]) -> str:
    has_sv = "schema_version" in data
    has_schema = "schema" in data
    if not has_sv and not has_schema:
        raise ReviewDisagreementError("schema_version is required")
    sv = data["schema_version"] if has_sv else None
    schema = data["schema"] if has_schema else None
    if has_sv and not isinstance(sv, str):
        raise ReviewDisagreementError(
            f"schema_version must be a string; got {type(sv).__name__}"
        )
    if has_schema and not isinstance(schema, str):
        raise ReviewDisagreementError(
            f"schema must be a string; got {type(schema).__name__}"
        )
    if has_sv and has_schema and sv != schema:
        raise ReviewDisagreementError(
            "schema_version and schema must be exactly equal when both present"
        )
    resolved = sv if has_sv else schema
    if resolved != SCHEMA_VERSION:
        raise ReviewDisagreementError(
            f"schema_version must be {SCHEMA_VERSION!r}"
        )
    return SCHEMA_VERSION


def _parse_reviewer_position(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping):
        raise ReviewDisagreementError(
            "reviewer_positions entries must be mappings; "
            f"got {type(item).__name__}"
        )
    unknown = set(item) - POSITION_ALLOWED_KEYS
    if unknown:
        raise ReviewDisagreementError(
            f"reviewer_positions entry has unknown fields: {sorted(unknown)}"
        )
    if "reviewer_id" not in item or "position" not in item:
        raise ReviewDisagreementError(
            "reviewer_positions entries require reviewer_id and position"
        )
    reviewer_id = _require_nonempty_str(
        item["reviewer_id"], field_name="reviewer_id"
    )
    position = item["position"]
    if not isinstance(position, str) or position not in REVIEWER_POSITION_VALUES:
        raise ReviewDisagreementError(
            f"malformed reviewer position value: {position!r}"
        )
    out: dict[str, Any] = {
        "reviewer_id": reviewer_id,
        "position": position,
    }
    if "label" in item:
        label = item["label"]
        if not isinstance(label, str):
            raise ReviewDisagreementError("reviewer label must be a string when set")
        out["label"] = label
    if "notes" in item:
        notes = item["notes"]
        if not isinstance(notes, str):
            raise ReviewDisagreementError("reviewer notes must be a string when set")
        out["notes"] = notes
    return out


def _parse_reviewer_positions(value: Any) -> tuple[dict[str, Any], ...]:
    if isinstance(value, str):
        raise ReviewDisagreementError(
            "reviewer_positions must be a list/tuple, not a string"
        )
    if not isinstance(value, (list, tuple)):
        raise ReviewDisagreementError(
            "reviewer_positions must be a list/tuple of mappings; "
            f"got {type(value).__name__}"
        )
    if len(value) < 1:
        raise ReviewDisagreementError(
            "reviewer_positions must contain at least one position"
        )
    parsed = [_parse_reviewer_position(item) for item in value]
    ids = [p["reviewer_id"] for p in parsed]
    if len(ids) != len(set(ids)):
        raise ReviewDisagreementError("duplicate reviewer_id within record")
    return tuple(
        sorted(parsed, key=lambda p: (p["reviewer_id"], p["position"]))
    )


def _parse_predecessor_pair(
    data: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    has_prior = "prior_record_digest" in data
    has_succ = "successor_of" in data
    if not has_prior and not has_succ:
        return None, None
    if has_prior ^ has_succ:
        raise ReviewDisagreementError(
            "prior_record_digest and successor_of must both be absent or both valid"
        )
    prior = _require_sha256(
        data["prior_record_digest"], field_name="prior_record_digest"
    )
    successor_of = _require_nonempty_str(
        data["successor_of"], field_name="successor_of"
    )
    return prior, successor_of


@dataclass(frozen=True)
class ReviewDisagreementRecord:
    """Immutable disagreement evidence. authority:false always."""

    schema_version: str
    authority: bool
    disagreement_id: str
    subject_id: str
    reviewer_positions: tuple[Mapping[str, Any], ...]
    scope: str
    category: str
    status: str
    reason: str
    evidence_refs: tuple[str, ...]
    created_from: str
    prior_record_digest: str | None = None
    successor_of: str | None = None
    resolution_note: str | None = None
    record_digest: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.authority is not False:
            raise ReviewDisagreementError("authority must be false")
        if self.schema_version != SCHEMA_VERSION:
            raise ReviewDisagreementError(
                f"schema_version must be {SCHEMA_VERSION!r}"
            )
        if self.status not in DISAGREEMENT_STATUSES:
            raise ReviewDisagreementError(f"unknown status: {self.status!r}")
        if self.category not in DISAGREEMENT_CATEGORIES:
            raise ReviewDisagreementError(f"unknown category: {self.category!r}")
        if not self.reviewer_positions:
            raise ReviewDisagreementError("reviewer_positions must be non-empty")
        has_prior = self.prior_record_digest is not None
        has_succ = self.successor_of is not None
        if has_prior ^ has_succ:
            raise ReviewDisagreementError(
                "prior_record_digest and successor_of must both be absent or both valid"
            )
        if not has_prior and self.status == "RESOLVED_BY_SUCCESSOR":
            raise ReviewDisagreementError(
                "RESOLVED_BY_SUCCESSOR requires predecessor fields"
            )
        if has_prior and self.status in INITIAL_STATUSES:
            # Successor may keep OPEN/AMBIGUOUS/UNRESOLVED; that is allowed.
            pass

    def body_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "schema_version": self.schema_version,
            "schema": self.schema_version,
            "authority": False,
            "disagreement_id": self.disagreement_id,
            "subject_id": self.subject_id,
            "reviewer_positions": [dict(p) for p in self.reviewer_positions],
            "scope": self.scope,
            "category": self.category,
            "status": self.status,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "created_from": self.created_from,
        }
        if self.prior_record_digest is not None:
            d["prior_record_digest"] = self.prior_record_digest
        if self.successor_of is not None:
            d["successor_of"] = self.successor_of
        if self.resolution_note is not None:
            d["resolution_note"] = self.resolution_note
        if self.extra:
            d["extra"] = dict(self.extra)
        return d

    def to_dict(self) -> dict[str, Any]:
        d = self.body_dict()
        if not self.record_digest:
            raise ReviewDisagreementError(
                "record_digest must be set before serialization"
            )
        d["record_digest"] = self.record_digest
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def compute_digest(self) -> str:
        return canonical_digest(self.body_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReviewDisagreementRecord":
        return strict_parse_record(data)


def strict_parse_record(data: Any) -> ReviewDisagreementRecord:
    """Canonical stored-record parser. NO COERCION. record_digest required."""
    if not isinstance(data, Mapping):
        raise ReviewDisagreementError(
            f"disagreement record must be a mapping; got {type(data).__name__}"
        )
    enforce_non_authority(data)
    unknown = set(data) - RECORD_ALLOWED_KEYS
    if unknown:
        raise ReviewDisagreementError(
            f"disagreement record has unknown fields: {sorted(unknown)}"
        )

    _require_schema_aliases(data)
    if "authority" not in data or data["authority"] is not False:
        raise ReviewDisagreementError("authority must be Boolean false")

    for required in (
        "disagreement_id",
        "subject_id",
        "reviewer_positions",
        "scope",
        "category",
        "status",
        "created_from",
        "record_digest",
    ):
        if required not in data:
            raise ReviewDisagreementError(f"{required} is required")

    status = data["status"]
    if not isinstance(status, str) or status not in DISAGREEMENT_STATUSES:
        raise ReviewDisagreementError(f"unknown status: {status!r}")
    category = data["category"]
    if not isinstance(category, str) or category not in DISAGREEMENT_CATEGORIES:
        raise ReviewDisagreementError(f"unknown category: {category!r}")

    prior, successor_of = _parse_predecessor_pair(data)
    if prior is None and status == "RESOLVED_BY_SUCCESSOR":
        raise ReviewDisagreementError(
            "RESOLVED_BY_SUCCESSOR requires predecessor fields"
        )

    if "reason" in data:
        reason = data["reason"]
        if not isinstance(reason, str):
            raise ReviewDisagreementError(
                f"reason must be a string when present; got {type(reason).__name__}"
            )
    else:
        reason = ""

    if "resolution_note" in data:
        resolution_note = data["resolution_note"]
        if not isinstance(resolution_note, str):
            raise ReviewDisagreementError(
                "resolution_note must be a string when present"
            )
    else:
        resolution_note = None

    created_from = _require_nonempty_str(
        data["created_from"], field_name="created_from"
    )
    record_digest = _require_sha256(data["record_digest"], field_name="record_digest")

    if "evidence_refs" in data:
        evidence_refs = _require_str_refs(
            data["evidence_refs"], field_name="evidence_refs"
        )
    else:
        evidence_refs = ()

    if "extra" in data:
        extra = data["extra"]
        if not isinstance(extra, Mapping):
            raise ReviewDisagreementError(
                f"extra must be a mapping when present; got {type(extra).__name__}"
            )
        extra_map = dict(extra)
    else:
        extra_map = {}

    rec = ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=_require_nonempty_str(
            data["disagreement_id"], field_name="disagreement_id"
        ),
        subject_id=_require_nonempty_str(
            data["subject_id"], field_name="subject_id"
        ),
        reviewer_positions=_parse_reviewer_positions(data["reviewer_positions"]),
        scope=_require_nonempty_str(data["scope"], field_name="scope"),
        category=category,
        status=status,
        reason=reason,
        evidence_refs=evidence_refs,
        created_from=created_from,
        prior_record_digest=prior,
        successor_of=successor_of,
        resolution_note=resolution_note,
        record_digest=record_digest,
        extra=extra_map,
    )
    expected = rec.compute_digest()
    if record_digest != expected:
        raise ReviewDisagreementError(
            "record_digest does not match canonical body digest"
        )
    return rec


def create_disagreement_record(
    *,
    disagreement_id: str,
    subject_id: str,
    reviewer_positions: Sequence[Mapping[str, Any]],
    scope: str,
    category: str,
    status: str = "OPEN",
    reason: str = "",
    evidence_refs: Sequence[str] | None = None,
    created_from: str = "explicit_review",
    extra: Mapping[str, Any] | None = None,
) -> ReviewDisagreementRecord:
    """ONE constructor for initial disagreement records (no prior digest)."""
    if status not in INITIAL_STATUSES:
        raise ReviewDisagreementError(
            f"initial disagreement status must be one of {sorted(INITIAL_STATUSES)}; "
            f"got {status!r}"
        )
    if not isinstance(reason, str):
        raise ReviewDisagreementError("reason must be a string")
    if category not in DISAGREEMENT_CATEGORIES:
        raise ReviewDisagreementError(f"unknown category: {category!r}")
    if evidence_refs is None:
        refs: tuple[str, ...] = ()
    else:
        refs = _require_str_refs(list(evidence_refs), field_name="evidence_refs")
    if extra is None:
        extra_map: dict[str, Any] = {}
    else:
        if not isinstance(extra, Mapping):
            raise ReviewDisagreementError("extra must be a mapping when set")
        extra_map = dict(extra)

    body = ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=_require_nonempty_str(
            disagreement_id, field_name="disagreement_id"
        ),
        subject_id=_require_nonempty_str(subject_id, field_name="subject_id"),
        reviewer_positions=_parse_reviewer_positions(list(reviewer_positions)),
        scope=_require_nonempty_str(scope, field_name="scope"),
        category=category,
        status=status,
        reason=reason,
        evidence_refs=refs,
        created_from=_require_nonempty_str(created_from, field_name="created_from"),
        prior_record_digest=None,
        successor_of=None,
        resolution_note=None,
        record_digest="",
        extra=extra_map,
    )
    digest = body.compute_digest()
    return ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=body.disagreement_id,
        subject_id=body.subject_id,
        reviewer_positions=body.reviewer_positions,
        scope=body.scope,
        category=body.category,
        status=body.status,
        reason=body.reason,
        evidence_refs=body.evidence_refs,
        created_from=body.created_from,
        prior_record_digest=None,
        successor_of=None,
        resolution_note=None,
        record_digest=digest,
        extra=body.extra,
    )


def create_successor_record(
    prior: ReviewDisagreementRecord | Mapping[str, Any],
    *,
    disagreement_id: str,
    status: str,
    reason: str = "",
    resolution_note: str | None = None,
    reviewer_positions: Sequence[Mapping[str, Any]] | None = None,
    evidence_refs: Sequence[str] | None = None,
    created_from: str = "successor_resolution",
    extra: Mapping[str, Any] | None = None,
) -> ReviewDisagreementRecord:
    """
    ONE successor constructor.

    Does NOT mutate prior. New record references prior digest / disagreement_id.
    Category/subject/scope are preserved from the predecessor (immutable across chain).
    """
    if isinstance(prior, Mapping):
        prior_rec = strict_parse_record(prior)
    else:
        prior_rec = prior
    prior_digest = prior_rec.record_digest
    if not prior_digest:
        prior_digest = prior_rec.compute_digest()
    prior_digest = _require_sha256(prior_digest, field_name="prior record_digest")

    if prior_rec.status == "RESOLVED_BY_SUCCESSOR":
        raise ReviewDisagreementError(
            "terminal RESOLVED_BY_SUCCESSOR must not have another successor"
        )

    if not isinstance(reason, str):
        raise ReviewDisagreementError("reason must be a string")
    if resolution_note is not None and not isinstance(resolution_note, str):
        raise ReviewDisagreementError("resolution_note must be a string when set")
    if status not in DISAGREEMENT_STATUSES:
        raise ReviewDisagreementError(f"unknown status: {status!r}")

    new_id = _require_nonempty_str(disagreement_id, field_name="disagreement_id")
    if new_id == prior_rec.disagreement_id:
        raise ReviewDisagreementError(
            "successor disagreement_id must differ from predecessor"
        )

    positions = (
        list(reviewer_positions)
        if reviewer_positions is not None
        else [dict(p) for p in prior_rec.reviewer_positions]
    )
    if evidence_refs is None:
        refs = list(prior_rec.evidence_refs)
    else:
        refs = list(evidence_refs)
    if extra is None:
        extra_map: dict[str, Any] = {}
    else:
        if not isinstance(extra, Mapping):
            raise ReviewDisagreementError("extra must be a mapping when set")
        extra_map = dict(extra)

    body = ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=new_id,
        subject_id=prior_rec.subject_id,
        reviewer_positions=_parse_reviewer_positions(positions),
        scope=prior_rec.scope,
        category=prior_rec.category,
        status=status,
        reason=reason,
        evidence_refs=_require_str_refs(refs, field_name="evidence_refs"),
        created_from=_require_nonempty_str(created_from, field_name="created_from"),
        prior_record_digest=prior_digest,
        successor_of=prior_rec.disagreement_id,
        resolution_note=resolution_note,
        record_digest="",
        extra=extra_map,
    )
    digest = body.compute_digest()
    if digest == prior_digest:
        raise ReviewDisagreementError(
            "successor record_digest must differ from predecessor"
        )
    return ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=body.disagreement_id,
        subject_id=body.subject_id,
        reviewer_positions=body.reviewer_positions,
        scope=body.scope,
        category=body.category,
        status=body.status,
        reason=body.reason,
        evidence_refs=body.evidence_refs,
        created_from=body.created_from,
        prior_record_digest=body.prior_record_digest,
        successor_of=body.successor_of,
        resolution_note=body.resolution_note,
        record_digest=digest,
        extra=body.extra,
    )


def validate_disagreement_record(
    data: Mapping[str, Any] | ReviewDisagreementRecord,
) -> ReviewDisagreementRecord:
    """ONE validator for disagreement records."""
    if isinstance(data, ReviewDisagreementRecord):
        return strict_parse_record(data.to_dict())
    return strict_parse_record(data)


def disagreement_storage_path(audit_root: Path, record_digest: str) -> Path:
    return audit_root.resolve() / REVIEWS_DIRNAME / f"{record_digest}.json"


def _payload_bytes(payload: Mapping[str, Any]) -> bytes:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def write_disagreement_record(
    audit_root: Path,
    record: ReviewDisagreementRecord | Mapping[str, Any],
) -> Path:
    """
    Content-addressed immutable exclusive create to reviews/<record-digest>.json.

    - create new path only if absent (O_EXCL)
    - existing same-path/same-bytes => idempotent
    - existing different bytes => FAIL CLOSED
    - never overwrite a disagreement record
    """
    rec = validate_disagreement_record(record)
    digest = rec.record_digest
    path = disagreement_storage_path(audit_root, digest)
    payload = rec.to_dict()
    desired = _payload_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file():
        existing = path.read_bytes()
        if existing == desired:
            return path
        # Also reject canonical-equivalent but differently serialized conflicts
        # by comparing canonical digests of parsed JSON when possible.
        try:
            existing_obj = json.loads(existing.decode("utf-8"))
            if canonical_digest(existing_obj) == canonical_digest(payload):
                # Same semantic payload, different bytes → still fail closed
                # because immutable write must preserve exact bytes once sealed.
                raise ReviewDisagreementError(
                    "overwrite-in-place of disagreement record rejected; "
                    f"path={path.as_posix()} (canonical-equal different bytes)"
                )
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            raise ReviewDisagreementError(
                "corrupted existing disagreement destination rejected; "
                f"path={path.as_posix()}"
            ) from e
        raise ReviewDisagreementError(
            "overwrite-in-place of disagreement record rejected; "
            f"path={path.as_posix()}"
        )

    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as e:
        # Race: another writer created the path between check and open.
        existing = path.read_bytes()
        if existing == desired:
            return path
        raise ReviewDisagreementError(
            "overwrite-in-place of disagreement record rejected "
            f"(exclusive-create race); path={path.as_posix()}"
        ) from e
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(desired)
    except Exception:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return path


def read_disagreement_record(path: Path) -> ReviewDisagreementRecord:
    from audit_lifecycle.request import read_json

    data = read_json(path)
    rec = validate_disagreement_record(data)
    expected_name = f"{rec.record_digest}.json"
    if path.name != expected_name:
        raise ReviewDisagreementError(
            f"disagreement filename {path.name!r} does not match "
            f"record_digest {rec.record_digest!r}"
        )
    return rec


def list_disagreement_records_at_root(
    audit_root: Path,
) -> list[ReviewDisagreementRecord]:
    root = audit_root.resolve() / REVIEWS_DIRNAME
    if not root.is_dir():
        return []
    records: list[ReviewDisagreementRecord] = []
    for path in sorted(p for p in root.glob("*.json") if p.is_file()):
        records.append(read_disagreement_record(path))
    return records


def verify_chain_graph(
    records: Sequence[ReviewDisagreementRecord],
) -> dict[str, Any]:
    """
    ONE canonical complete-set successor-chain verifier.

    Rejects missing/fake/unrelated predecessors, subject/scope/category mismatch,
    self-links, cycles, forks, duplicate successors, duplicate IDs, and terminal
    RESOLVED_BY_SUCCESSOR having another successor.
    """
    by_digest: dict[str, ReviewDisagreementRecord] = {}
    by_id: dict[str, ReviewDisagreementRecord] = {}
    for rec in records:
        digest = rec.record_digest
        if digest in by_digest:
            raise ReviewDisagreementError(
                f"duplicate record_digest in expected set: {digest}"
            )
        if rec.disagreement_id in by_id:
            raise ReviewDisagreementError(
                f"duplicate disagreement_id in expected set: {rec.disagreement_id}"
            )
        by_digest[digest] = rec
        by_id[rec.disagreement_id] = rec

    # Map predecessor digest -> list of successors.
    successors_of: dict[str, list[ReviewDisagreementRecord]] = {}
    for rec in records:
        if rec.prior_record_digest is None:
            if rec.successor_of is not None:
                raise ReviewDisagreementError("inconsistent predecessor fields")
            continue
        if rec.prior_record_digest == rec.record_digest:
            raise ReviewDisagreementError("self-link via prior_record_digest")
        if rec.successor_of == rec.disagreement_id:
            raise ReviewDisagreementError("self-link via successor_of")
        if rec.prior_record_digest not in by_digest:
            raise ReviewDisagreementError(
                "predecessor missing from expected set: "
                f"{rec.prior_record_digest}"
            )
        prior = by_digest[rec.prior_record_digest]
        if prior.disagreement_id != rec.successor_of:
            raise ReviewDisagreementError(
                "successor_of does not match predecessor disagreement_id"
            )
        if prior.subject_id != rec.subject_id:
            raise ReviewDisagreementError("subject_id mismatch across successor chain")
        if prior.scope != rec.scope:
            raise ReviewDisagreementError("scope mismatch across successor chain")
        if prior.category != rec.category:
            raise ReviewDisagreementError("category mismatch across successor chain")
        if prior.status == "RESOLVED_BY_SUCCESSOR":
            raise ReviewDisagreementError(
                "terminal RESOLVED_BY_SUCCESSOR must not have another successor"
            )
        successors_of.setdefault(rec.prior_record_digest, []).append(rec)

    for pred_digest, succs in successors_of.items():
        if len(succs) > 1:
            raise ReviewDisagreementError(
                f"fork: multiple successors for predecessor {pred_digest}"
            )

    # Cycle detection via walk to root.
    for rec in records:
        seen: set[str] = set()
        cur = rec
        while cur.prior_record_digest is not None:
            if cur.record_digest in seen:
                raise ReviewDisagreementError("cycle detected in successor chain")
            seen.add(cur.record_digest)
            cur = by_digest[cur.prior_record_digest]

    heads = [
        rec.record_digest
        for rec in records
        if rec.prior_record_digest is None
    ]
    return {
        "ok": True,
        "records": len(records),
        "chain_heads": sorted(heads),
        "authority": False,
    }


def verify_disagreement_expected_set(
    audit_root: Path,
    expected_digests: Sequence[str],
    *,
    expected_chain_heads: Sequence[str] | None = None,
) -> dict[str, Any]:
    """
    Actual disagreement digest set under reviews/ must equal expected set exactly.
    """
    root = audit_root.resolve() / REVIEWS_DIRNAME
    expected = list(expected_digests)
    expected_set = set(expected)
    if len(expected) != len(expected_set):
        return {
            "ok": False,
            "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
            "error": "EXPECTED_SET_HAS_DUPLICATE_DIGESTS",
            "present": True,
        }

    actual_files = []
    if root.is_dir():
        actual_files = sorted(p for p in root.glob("*.json") if p.is_file())

    actual_digests: list[str] = []
    records: list[ReviewDisagreementRecord] = []
    for path in actual_files:
        try:
            rec = read_disagreement_record(path)
        except (ReviewDisagreementError, ValueError, OSError) as e:
            return {
                "ok": False,
                "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
                "error": str(e),
                "path": path.name,
                "present": True,
            }
        actual_digests.append(rec.record_digest)
        records.append(rec)

    actual_set = set(actual_digests)
    if len(actual_digests) != len(actual_set):
        return {
            "ok": False,
            "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
            "error": "DUPLICATE_RECORD_DIGEST_ON_DISK",
            "present": True,
        }
    if actual_set != expected_set:
        return {
            "ok": False,
            "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
            "error": "EXPECTED_SET_MISMATCH",
            "expected": sorted(expected_set),
            "actual": sorted(actual_set),
            "missing": sorted(expected_set - actual_set),
            "extra": sorted(actual_set - expected_set),
            "present": bool(actual_files) or bool(expected_set),
        }

    try:
        chain = verify_chain_graph(records)
    except ReviewDisagreementError as e:
        return {
            "ok": False,
            "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
            "error": f"CHAIN_GRAPH:{e}",
            "present": True,
            "records": len(records),
        }

    if expected_chain_heads is not None:
        if sorted(chain["chain_heads"]) != sorted(expected_chain_heads):
            return {
                "ok": False,
                "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
                "error": "CHAIN_HEADS_MISMATCH",
                "expected_chain_heads": list(expected_chain_heads),
                "actual_chain_heads": chain["chain_heads"],
                "present": True,
            }

    return {
        "ok": True,
        "status": "REVIEW_DISAGREEMENT_VERIFICATION_PASS",
        "present": bool(records),
        "records": len(records),
        "chain_heads": chain["chain_heads"],
        "checked": [
            {
                "record_digest": r.record_digest,
                "status": r.status,
                "disagreement_id": r.disagreement_id,
            }
            for r in records
        ],
    }


def verify_disagreement_records_at_root(
    audit_root: Path,
    *,
    expected_digests: Sequence[str] | None = None,
    expected_chain_heads: Sequence[str] | None = None,
    require_expected_set: bool = False,
) -> dict[str, Any]:
    """
    Disagreement verification hook.

    Legacy (require_expected_set=False): absent => optional; present => validate
    each file + chain graph over present set.
    R4_B_ENABLED: expected set must be explicit (including []) and match exactly.
    """
    if require_expected_set:
        if expected_digests is None:
            return {
                "ok": False,
                "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
                "error": "EXPECTED_DISAGREEMENT_SET_REQUIRED",
                "present": False,
            }
        return verify_disagreement_expected_set(
            audit_root,
            expected_digests,
            expected_chain_heads=expected_chain_heads,
        )

    root = audit_root.resolve() / REVIEWS_DIRNAME
    if not root.is_dir():
        return {
            "ok": True,
            "status": "REVIEW_DISAGREEMENT_ABSENT_OPTIONAL",
            "present": False,
            "records": 0,
        }
    files = sorted(p for p in root.glob("*.json") if p.is_file())
    if not files:
        return {
            "ok": True,
            "status": "REVIEW_DISAGREEMENT_ABSENT_OPTIONAL",
            "present": False,
            "records": 0,
        }
    records: list[ReviewDisagreementRecord] = []
    for path in files:
        try:
            records.append(read_disagreement_record(path))
        except (ReviewDisagreementError, ValueError, OSError) as e:
            return {
                "ok": False,
                "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
                "present": True,
                "error": str(e),
                "path": path.name,
                "records": len(files),
            }
    try:
        chain = verify_chain_graph(records)
    except ReviewDisagreementError as e:
        return {
            "ok": False,
            "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
            "present": True,
            "error": f"CHAIN_GRAPH:{e}",
            "records": len(records),
        }
    return {
        "ok": True,
        "status": "REVIEW_DISAGREEMENT_VERIFICATION_PASS",
        "present": True,
        "records": len(records),
        "chain_heads": chain["chain_heads"],
        "checked": [
            {
                "path": f"{r.record_digest}.json",
                "ok": True,
                "record_digest": r.record_digest,
                "status": r.status,
            }
            for r in records
        ],
    }


def collect_disagreement_expectation(audit_root: Path) -> dict[str, list[str]]:
    """Collect actual digests / chain heads for freeze-time expectation binding."""
    records = list_disagreement_records_at_root(audit_root)
    # Validate graph before binding.
    chain = verify_chain_graph(records)
    return {
        "expected_disagreement_record_digests": sorted(
            r.record_digest for r in records
        ),
        "expected_disagreement_chain_heads": list(chain["chain_heads"]),
    }
