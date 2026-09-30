"""Canonical JSON serialization and digest helpers for WVMA-V1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _assert_canonical_value(obj: Any) -> None:
    """Reject containers that JSON would silently coerce or cannot encode."""
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(
                    f"canonical JSON keys must be str; got {type(key).__name__}"
                )
            _assert_canonical_value(value)
        return
    if isinstance(obj, list):
        for item in obj:
            _assert_canonical_value(item)
        return
    if isinstance(obj, (tuple, set, frozenset)):
        raise TypeError(
            f"canonical JSON does not normalize {type(obj).__name__}; "
            "use a schema-declared parser for set-like fields"
        )
    if isinstance(obj, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"canonical JSON does not accept {type(obj).__name__}"
        )


def canonical_bytes(obj: Any) -> bytes:
    """UTF-8 canonical JSON: sorted keys, compact separators, ASCII, no NaN."""
    _assert_canonical_value(obj)
    text = json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return text.encode("utf-8")


def canonical_digest(obj: Any) -> str:
    """SHA-256 hex digest of canonical_bytes(obj)."""
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def sha256_file(path: str | Path) -> str:
    """SHA-256 hex digest of raw file bytes."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def digest_excluding_field(obj: Mapping[str, Any], field: str) -> str:
    """Self-digest helper: hash canonical JSON excluding exactly one field."""
    if not isinstance(obj, Mapping):
        raise TypeError("digest_excluding_field requires a mapping")
    if not isinstance(field, str) or not field:
        raise TypeError("field must be a non-empty str")
    body = {str(k): v for k, v in obj.items() if k != field}
    return canonical_digest(body)
