"""Canonical JSON serialization and digest helpers for R4-A epistemic records.

Reuses the deterministic sort_keys + compact separators pattern already used
by campaign_runner_v0.state_revalidation — no duplicate hash infrastructure.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_dumps(obj: Any) -> str:
    """Deterministic JSON: sorted keys, compact separators, ASCII-safe."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_loads(text: str) -> Any:
    return json.loads(text)


def canonical_digest(obj: Any) -> str:
    """SHA-256 hex digest of canonical_dumps(obj)."""
    blob = canonical_dumps(obj).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()
