"""Mutable INR-HER-001 collector export.

The export is outside P. It is not an r4 event and not witness evidence.
"""

from __future__ import annotations

import hashlib
import json


def collect_export(event_id: str, protected_hashes: dict[str, str]) -> dict[str, object]:
    """Copy protected hashes into a mutable export. This function uses no network."""
    if not isinstance(event_id, str) or event_id == "":
        raise ValueError("event_id is required")
    if type(protected_hashes) is not dict:
        raise TypeError("protected_hashes must be a dict")
    copied = {str(key): str(value) for key, value in protected_hashes.items()}
    body = {
        "schema_version": "inr.her.collector_export.v0",
        "event_id": event_id,
        "protected_execution_member": False,
        "mutable_collector_output": True,
        "network": "NOT_USED",
        "protected_hashes": copied,
    }
    payload = json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    exported = dict(body)
    exported["protected_hashes"] = dict(copied)
    exported["export_sha256"] = hashlib.sha256(payload).hexdigest()
    return exported
