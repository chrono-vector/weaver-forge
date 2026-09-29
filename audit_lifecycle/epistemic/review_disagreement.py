"""R4-B Immutable Reviewer Disagreement Records — non-authoritative.

Disagreement records are never rewritten into "resolved".
Resolution creates a NEW successor record that references the prior digest.

AMBIGUOUS and UNRESOLVED are valid outcomes. Do not force consensus.
Reviewer positions remain explicit — no synthetic winner, no authority.
"""

from __future__ import annotations

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

# Statuses allowed on a freshly constructed (non-successor) record.
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


class ReviewDisagreementError(ValueError):
    """Malformed disagreement record or immutability violation."""


def _require_nonempty_str(value: Any, *, field_name: str) -> str:
    if not isinstance(value, str):
        raise ReviewDisagreementError(
            f"{field_name} must be a nonempty string; got {type(value).__name__}"
        )
    text = value.strip()
    if not text:
        raise ReviewDisagreementError(f"{field_name} must be a nonempty string")
    return text


def _coerce_str_refs(value: Any, *, field_name: str) -> tuple[str, ...]:
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


def _parse_reviewer_position(item: Any) -> dict[str, Any]:
    """Parse one explicit reviewer position — never collapse to consensus."""
    if not isinstance(item, Mapping):
        raise ReviewDisagreementError(
            "reviewer_positions entries must be mappings; "
            f"got {type(item).__name__}"
        )
    reviewer_id = _require_nonempty_str(
        item.get("reviewer_id"), field_name="reviewer_id"
    )
    position = item.get("position")
    if not isinstance(position, str) or position not in REVIEWER_POSITION_VALUES:
        raise ReviewDisagreementError(
            f"malformed reviewer position value: {position!r}"
        )
    out: dict[str, Any] = {
        "reviewer_id": reviewer_id,
        "position": position,
    }
    label = item.get("label")
    if label is not None:
        if not isinstance(label, str):
            raise ReviewDisagreementError("reviewer label must be a string when set")
        out["label"] = label
    notes = item.get("notes")
    if notes is not None:
        if not isinstance(notes, str):
            raise ReviewDisagreementError("reviewer notes must be a string when set")
        out["notes"] = notes
    # Reject nested authority keys via enforce on a synthetic envelope later;
    # forbid reserved keys inside the position mapping itself.
    for forbidden in (
        "authority",
        "human_final",
        "execution_authorized",
        "weaver_pass",
        "weaver_fail",
    ):
        if forbidden in item:
            raise ReviewDisagreementError(
                f"reviewer_positions must not carry authority key {forbidden!r}"
            )
    return out


def _coerce_reviewer_positions(value: Any) -> tuple[dict[str, Any], ...]:
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
    # Deterministic set-like order by reviewer_id then position.
    return tuple(
        sorted(parsed, key=lambda p: (p["reviewer_id"], p["position"]))
    )


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
        digest = self.record_digest or canonical_digest(d)
        d["record_digest"] = digest
        return d

    def canonical_json(self) -> str:
        return canonical_dumps(self.to_dict())

    def compute_digest(self) -> str:
        return canonical_digest(self.body_dict())

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ReviewDisagreementRecord":
        enforce_non_authority(data)
        schema = data.get("schema_version") or data.get("schema")
        if schema != SCHEMA_VERSION:
            raise ReviewDisagreementError(
                f"schema_version must be {SCHEMA_VERSION!r}"
            )
        if "authority" not in data or data["authority"] is not False:
            raise ReviewDisagreementError("authority must be Boolean false")
        status = data.get("status")
        if status not in DISAGREEMENT_STATUSES:
            raise ReviewDisagreementError(f"unknown status: {status!r}")
        category = data.get("category") or data.get("reason_category")
        if category not in DISAGREEMENT_CATEGORIES:
            raise ReviewDisagreementError(f"unknown category: {category!r}")
        prior = data.get("prior_record_digest")
        if prior is not None:
            prior = _require_nonempty_str(prior, field_name="prior_record_digest")
            if len(prior) != 64 or any(c not in "0123456789abcdef" for c in prior):
                raise ReviewDisagreementError(
                    "prior_record_digest must be a sha256 hex digest"
                )
        successor_of = data.get("successor_of")
        if successor_of is not None:
            successor_of = _require_nonempty_str(
                successor_of, field_name="successor_of"
            )
        resolution_note = data.get("resolution_note")
        if resolution_note is not None and not isinstance(resolution_note, str):
            raise ReviewDisagreementError(
                "resolution_note must be a string when set"
            )
        reason = data.get("reason")
        if reason is None:
            reason = ""
        if not isinstance(reason, str):
            raise ReviewDisagreementError("reason must be a string")
        created_from = _require_nonempty_str(
            data.get("created_from") or "explicit_review",
            field_name="created_from",
        )
        extra = data["extra"] if "extra" in data else {}
        if extra is None:
            extra = {}
        if not isinstance(extra, Mapping):
            raise ReviewDisagreementError("extra must be a mapping when set")
        rec = cls(
            schema_version=SCHEMA_VERSION,
            authority=False,
            disagreement_id=_require_nonempty_str(
                data["disagreement_id"], field_name="disagreement_id"
            ),
            subject_id=_require_nonempty_str(
                data["subject_id"], field_name="subject_id"
            ),
            reviewer_positions=_coerce_reviewer_positions(
                data.get("reviewer_positions")
            ),
            scope=_require_nonempty_str(data["scope"], field_name="scope"),
            category=category,
            status=status,
            reason=reason,
            evidence_refs=(
                _coerce_str_refs(data["evidence_refs"], field_name="evidence_refs")
                if "evidence_refs" in data
                else ()
            ),
            created_from=created_from,
            prior_record_digest=prior,
            successor_of=successor_of,
            resolution_note=resolution_note,
            record_digest=str(data.get("record_digest") or ""),
            extra=dict(extra),
        )
        expected = rec.compute_digest()
        stored = data.get("record_digest")
        if stored is not None and stored != expected:
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
    if status == "RESOLVED_BY_SUCCESSOR":
        raise ReviewDisagreementError(
            "RESOLVED_BY_SUCCESSOR is only valid on successor records"
        )
    body = ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=_require_nonempty_str(
            disagreement_id, field_name="disagreement_id"
        ),
        subject_id=_require_nonempty_str(subject_id, field_name="subject_id"),
        reviewer_positions=_coerce_reviewer_positions(list(reviewer_positions)),
        scope=_require_nonempty_str(scope, field_name="scope"),
        category=category,
        status=status,
        reason=reason if isinstance(reason, str) else "",
        evidence_refs=_coerce_str_refs(
            list(evidence_refs or ()), field_name="evidence_refs"
        ),
        created_from=_require_nonempty_str(created_from, field_name="created_from"),
        prior_record_digest=None,
        successor_of=None,
        resolution_note=None,
        record_digest="",
        extra=dict(extra or {}),
    )
    # Validate category via __post_init__ path
    if category not in DISAGREEMENT_CATEGORIES:
        raise ReviewDisagreementError(f"unknown category: {category!r}")
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
    category: str | None = None,
    evidence_refs: Sequence[str] | None = None,
    created_from: str = "successor_resolution",
    extra: Mapping[str, Any] | None = None,
) -> ReviewDisagreementRecord:
    """
    ONE successor constructor.

    Does NOT mutate prior. New record references prior digest / disagreement_id.
    """
    if isinstance(prior, Mapping):
        prior_rec = ReviewDisagreementRecord.from_dict(prior)
    else:
        prior_rec = prior
    prior_digest = prior_rec.record_digest or prior_rec.compute_digest()
    if not prior_digest or len(prior_digest) != 64:
        raise ReviewDisagreementError("prior record lacks a valid record_digest")

    positions = (
        list(reviewer_positions)
        if reviewer_positions is not None
        else [dict(p) for p in prior_rec.reviewer_positions]
    )
    cat = category if category is not None else prior_rec.category
    if status not in DISAGREEMENT_STATUSES:
        raise ReviewDisagreementError(f"unknown status: {status!r}")

    refs = (
        list(evidence_refs)
        if evidence_refs is not None
        else list(prior_rec.evidence_refs)
    )
    body = ReviewDisagreementRecord(
        schema_version=SCHEMA_VERSION,
        authority=False,
        disagreement_id=_require_nonempty_str(
            disagreement_id, field_name="disagreement_id"
        ),
        subject_id=prior_rec.subject_id,
        reviewer_positions=_coerce_reviewer_positions(positions),
        scope=prior_rec.scope,
        category=cat,
        status=status,
        reason=reason if isinstance(reason, str) else "",
        evidence_refs=_coerce_str_refs(refs, field_name="evidence_refs"),
        created_from=_require_nonempty_str(created_from, field_name="created_from"),
        prior_record_digest=prior_digest,
        successor_of=prior_rec.disagreement_id,
        resolution_note=resolution_note,
        record_digest="",
        extra=dict(extra or {}),
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
        # Re-parse via dict to enforce digest integrity.
        return ReviewDisagreementRecord.from_dict(data.to_dict())
    if not isinstance(data, Mapping):
        raise ReviewDisagreementError(
            f"disagreement record must be a mapping; got {type(data).__name__}"
        )
    return ReviewDisagreementRecord.from_dict(data)


def disagreement_storage_path(audit_root: Path, record_digest: str) -> Path:
    return audit_root.resolve() / REVIEWS_DIRNAME / f"{record_digest}.json"


def write_disagreement_record(
    audit_root: Path,
    record: ReviewDisagreementRecord | Mapping[str, Any],
) -> Path:
    """
    Content-addressed immutable write to reviews/<record-digest>.json.

    Rejects overwrite-in-place: existing file with different bytes fails.
    Same digest / same bytes is idempotent.
    """
    from audit_lifecycle.request import read_json, write_json

    rec = validate_disagreement_record(record)
    digest = rec.record_digest or rec.compute_digest()
    path = disagreement_storage_path(audit_root, digest)
    payload = rec.to_dict()
    if path.is_file():
        existing = read_json(path)
        if canonical_digest(existing) != canonical_digest(payload):
            raise ReviewDisagreementError(
                "overwrite-in-place of disagreement record rejected; "
                f"path={path.as_posix()}"
            )
        # Idempotent same-content write: leave bytes untouched.
        return path
    write_json(path, payload)
    return path


def read_disagreement_record(path: Path) -> ReviewDisagreementRecord:
    from audit_lifecycle.request import read_json

    data = read_json(path)
    rec = validate_disagreement_record(data)
    # Filename must match content digest (content-addressed binding).
    expected_name = f"{rec.record_digest}.json"
    if path.name != expected_name:
        raise ReviewDisagreementError(
            f"disagreement filename {path.name!r} does not match "
            f"record_digest {rec.record_digest!r}"
        )
    return rec


def verify_disagreement_records_at_root(audit_root: Path) -> dict[str, Any]:
    """
    Optional verification of reviews/*.json.

    Absent directory/files => skipped (legacy compatible).
    Present files => each must validate and match content-addressed name.
    """
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
    checked: list[dict[str, Any]] = []
    for path in files:
        try:
            rec = read_disagreement_record(path)
            checked.append(
                {
                    "path": path.name,
                    "ok": True,
                    "record_digest": rec.record_digest,
                    "status": rec.status,
                }
            )
        except (ReviewDisagreementError, ValueError, OSError) as e:
            return {
                "ok": False,
                "status": "REVIEW_DISAGREEMENT_VERIFICATION_FAIL",
                "present": True,
                "error": str(e),
                "path": path.name,
                "records": len(files),
            }
    return {
        "ok": True,
        "status": "REVIEW_DISAGREEMENT_VERIFICATION_PASS",
        "present": True,
        "records": len(checked),
        "checked": checked,
    }
