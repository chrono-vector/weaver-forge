"""Canonical JSON serialization and digest helpers for R4-A epistemic records.

Reuses the deterministic sort_keys + compact separators pattern already used
by campaign_runner_v0.state_revalidation — no duplicate hash infrastructure.

Sequence-field order semantics (R4-A):
  SET-LIKE  — membership only; normalized (sorted, deduped) before hash
  ORDERED   — sequence is semantically meaningful; order preserved

Do not normalize ORDERED sequences. Do not scan arbitrary prose.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

# Shared absent sentinel for optional constructor parameters.
# Omitted (ABSENT) may default; explicit None / wrong type must reject.
ABSENT = object()

# Membership collections — order of declaration must not affect digest.
SET_LIKE_SEQUENCE_FIELDS = frozenset(
    {
        "evidence_refs",
        "provenance_refs",
        "parent_sources",
        "independence_basis_refs",
        "refs",  # IndependenceBasis.refs
        "lineage_ids",
        "qualified_lineage_ids",
        "rejected_self_declared",
        # R4-B reconstructability / disagreement membership fields
        "input_refs",
        "required_inputs",
        "missing_inputs",
        "unresolved_assumptions",
        "derived_from",
        "reviewer_positions",
    }
)

# Sequences whose order is semantically meaningful.
# R4-B: reproduction_commands are ordered derivation steps.
ORDERED_SEQUENCE_FIELDS = frozenset(
    {
        "reproduction_commands",
    }
)


def _stable_item_key(item: Any) -> str:
    """Sort/dedupe key without re-entering canonical_dumps normalization."""
    if isinstance(item, str):
        return item
    return json.dumps(item, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _dedupe_preserve_sorted(items: list[Any]) -> list[Any]:
    """Deterministic dedupe: first-seen wins for ties, then sort by canonical form."""
    seen: set[str] = set()
    unique: list[Any] = []
    for item in items:
        key = _stable_item_key(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return sorted(unique, key=_stable_item_key)


def normalize_sequences(obj: Any, *, parent_key: str | None = None) -> Any:
    """
    Deep-normalize SET-LIKE sequence fields; leave ORDERED and unknown sequences intact.
    """
    if isinstance(obj, Mapping):
        return {
            str(k): normalize_sequences(v, parent_key=str(k)) for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        items = [normalize_sequences(x, parent_key=None) for x in obj]
        if parent_key in SET_LIKE_SEQUENCE_FIELDS:
            return _dedupe_preserve_sorted(items)
        # ORDERED or unknown: preserve order, still normalize nested mappings.
        return items
    return obj


def canonical_dumps(obj: Any) -> str:
    """Deterministic JSON: set-like normalized, sorted keys, compact separators."""
    normalized = normalize_sequences(obj)
    return json.dumps(
        normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )


def canonical_loads(text: str) -> Any:
    return json.loads(text)


def canonical_digest(obj: Any) -> str:
    """SHA-256 hex digest of canonical_dumps(obj)."""
    blob = canonical_dumps(obj).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
