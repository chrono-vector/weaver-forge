"""Generic external checkpoint verification interface v0.

The verifier compares local history with exact checkpoint bytes retained
outside the local history. A match is lineage consistency only. It is not
truth, authority, trusted time, freshness, evidence admission, Human Final,
or production permission.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Mapping
from typing import Any


CHECKPOINT_MATCH_CURRENT = "CHECKPOINT_MATCH_CURRENT"
CHECKPOINT_MATCH_STALE = "CHECKPOINT_MATCH_STALE"
LOCAL_HISTORY_BEHIND_CHECKPOINT = "LOCAL_HISTORY_BEHIND_CHECKPOINT"
LINEAGE_MISMATCH = "LINEAGE_MISMATCH"
EXTERNAL_MATERIAL_MISSING = "EXTERNAL_MATERIAL_MISSING"
UNVERIFIABLE_LOCAL_STATE = "UNVERIFIABLE_LOCAL_STATE"
UNSUPPORTED_VERIFICATION_METHOD = "UNSUPPORTED_VERIFICATION_METHOD"
INVALID_CHECKPOINT = "INVALID_CHECKPOINT"

RESULTS = frozenset(
    {
        CHECKPOINT_MATCH_CURRENT,
        CHECKPOINT_MATCH_STALE,
        LOCAL_HISTORY_BEHIND_CHECKPOINT,
        LINEAGE_MISMATCH,
        EXTERNAL_MATERIAL_MISSING,
        UNVERIFIABLE_LOCAL_STATE,
        UNSUPPORTED_VERIFICATION_METHOD,
        INVALID_CHECKPOINT,
    }
)

_SCHEMA_VERSION = "ecp.checkpoint.v0"
_VERIFICATION_METHOD = "retained_checkpoint_bytes.v0"
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CHECKPOINT_KEYS = frozenset(
    {
        "schema_version",
        "subject_log_id",
        "checkpoint_sequence",
        "committed_head_digest",
        "holder_id",
        "holder_basis",
        "verification_method",
        "provider_receipt_digest",
        "limitations",
        "nonclaims",
    }
)
_DIGEST_KEYS = frozenset({"algorithm", "value"})


class _InvalidCheckpoint(ValueError):
    pass


def _nonempty_string(value: Any, field: str) -> str:
    if type(value) is not str or not value.strip():
        raise _InvalidCheckpoint(f"{field} must be a non-empty string")
    return value


def _digest_value(value: Any, field: str) -> str:
    if type(value) is not dict or set(value) != _DIGEST_KEYS:
        raise _InvalidCheckpoint(f"{field} must be an exact digest object")
    if value.get("algorithm") != "sha256":
        raise _InvalidCheckpoint(f"{field} algorithm must be sha256")
    digest = value.get("value")
    if type(digest) is not str or _DIGEST.fullmatch(digest) is None:
        raise _InvalidCheckpoint(f"{field} value must be lowercase SHA-256")
    return digest


def _string_list(value: Any, field: str) -> list[str]:
    if type(value) is not list:
        raise _InvalidCheckpoint(f"{field} must be a list")
    if any(type(item) is not str or not item.strip() for item in value):
        raise _InvalidCheckpoint(f"{field} entries must be non-empty strings")
    if len(value) != len(set(value)):
        raise _InvalidCheckpoint(f"{field} entries must be unique")
    return value


def _validate_checkpoint(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _CHECKPOINT_KEYS:
        raise _InvalidCheckpoint("checkpoint fields do not match the v0 schema")
    if value.get("schema_version") != _SCHEMA_VERSION:
        raise _InvalidCheckpoint("unsupported checkpoint schema")
    _nonempty_string(value.get("subject_log_id"), "subject_log_id")
    sequence = value.get("checkpoint_sequence")
    if type(sequence) is not int or sequence < 0:
        raise _InvalidCheckpoint("checkpoint_sequence must be a non-negative integer")
    _digest_value(value.get("committed_head_digest"), "committed_head_digest")
    _nonempty_string(value.get("holder_id"), "holder_id")
    _nonempty_string(value.get("holder_basis"), "holder_basis")
    method = value.get("verification_method")
    if type(method) is not str or not method.strip():
        raise _InvalidCheckpoint("verification_method must be an unambiguous string")
    provider_digest = value.get("provider_receipt_digest")
    if provider_digest is not None:
        _digest_value(provider_digest, "provider_receipt_digest")
    _string_list(value.get("limitations"), "limitations")
    _string_list(value.get("nonclaims"), "nonclaims")
    return value


def canonical_checkpoint_bytes(checkpoint: Mapping[str, Any]) -> bytes:
    """Return strict canonical UTF-8 JSON bytes with one trailing LF."""
    value = _validate_checkpoint(checkpoint)
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise _InvalidCheckpoint("checkpoint is not canonical JSON") from exc
    return (text + "\n").encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise _InvalidCheckpoint("checkpoint contains a duplicate or invalid key")
        result[key] = value
    return result


def _reject_constant(token: str) -> Any:
    raise _InvalidCheckpoint(f"invalid JSON constant: {token}")


def parse_checkpoint_bytes(retained_bytes: bytes) -> dict[str, Any]:
    """Parse exact canonical retained checkpoint bytes."""
    if type(retained_bytes) is not bytes:
        raise _InvalidCheckpoint("retained checkpoint material must be exact bytes")
    try:
        text = retained_bytes.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _InvalidCheckpoint("retained checkpoint bytes are not strict UTF-8 JSON") from exc
    value = _validate_checkpoint(value)
    if retained_bytes != canonical_checkpoint_bytes(value):
        raise _InvalidCheckpoint("retained checkpoint bytes are not canonical")
    return value


def _local_digest(value: Any) -> str:
    try:
        return _digest_value(value, "local head digest")
    except _InvalidCheckpoint as exc:
        raise ValueError from exc


def verify_checkpoint(
    checkpoint: Mapping[str, Any],
    retained_checkpoint_bytes: bytes | None,
    *,
    subject_log_id: str,
    current_sequence: int,
    current_head_digest: Mapping[str, str],
    head_digest_at_sequence: Callable[[int], Mapping[str, str] | None] | None = None,
) -> str:
    """Compare local history with one externally retained checkpoint.

    ``head_digest_at_sequence`` is a local history lookup supplied by the
    embedding system. Returning ``None`` or raising means the checkpoint-era
    local state cannot be established.
    """
    if type(checkpoint) is dict and set(checkpoint) == _CHECKPOINT_KEYS:
        method = checkpoint.get("verification_method")
        if type(method) is not str or not method.strip() or method != _VERIFICATION_METHOD:
            return UNSUPPORTED_VERIFICATION_METHOD
    try:
        record = _validate_checkpoint(checkpoint)
    except (TypeError, ValueError, _InvalidCheckpoint):
        return INVALID_CHECKPOINT

    if type(subject_log_id) is not str or not subject_log_id.strip():
        return UNVERIFIABLE_LOCAL_STATE
    if record["subject_log_id"] != subject_log_id:
        return INVALID_CHECKPOINT
    if retained_checkpoint_bytes is None:
        return EXTERNAL_MATERIAL_MISSING

    try:
        retained = parse_checkpoint_bytes(retained_checkpoint_bytes)
        if retained != record or retained_checkpoint_bytes != canonical_checkpoint_bytes(record):
            return INVALID_CHECKPOINT
    except (TypeError, ValueError, _InvalidCheckpoint):
        return INVALID_CHECKPOINT

    if type(current_sequence) is not int or current_sequence < 0:
        return UNVERIFIABLE_LOCAL_STATE
    try:
        current_digest = _local_digest(current_head_digest)
    except (TypeError, ValueError):
        return UNVERIFIABLE_LOCAL_STATE

    checkpoint_sequence = record["checkpoint_sequence"]
    checkpoint_digest = record["committed_head_digest"]["value"]
    if current_sequence < checkpoint_sequence:
        return LOCAL_HISTORY_BEHIND_CHECKPOINT
    if current_sequence == checkpoint_sequence:
        return (
            CHECKPOINT_MATCH_CURRENT
            if current_digest == checkpoint_digest
            else LINEAGE_MISMATCH
        )
    if not callable(head_digest_at_sequence):
        return UNVERIFIABLE_LOCAL_STATE
    try:
        historical = head_digest_at_sequence(checkpoint_sequence)
        if historical is None:
            return UNVERIFIABLE_LOCAL_STATE
        historical_digest = _local_digest(historical)
    except Exception:
        return UNVERIFIABLE_LOCAL_STATE
    return (
        CHECKPOINT_MATCH_STALE
        if historical_digest == checkpoint_digest
        else LINEAGE_MISMATCH
    )
