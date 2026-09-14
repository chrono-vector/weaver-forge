from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def write_json(path: Path, obj: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return sha256_text(text)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_run_id(prefix: str = "WFA") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nonce = sha256_text(f"{stamp}|{os.getpid()}|{os.urandom(8).hex()}")[:8].upper()
    return f"{prefix}-{stamp}-{nonce}"


@dataclass
class AuditRequest:
    """Operator-supplied inputs only (target + claim/question + policy)."""

    target_path: str
    claim: dict[str, Any]
    policy: dict[str, Any] = field(default_factory=dict)
    protected_paths: list[str] = field(default_factory=list)
    prior_freeze_sums: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditRequest":
        if "target_path" not in data or "claim" not in data:
            raise ValueError("AuditRequest requires target_path and claim")
        claim = data["claim"]
        if not isinstance(claim, dict) or "id" not in claim or "statement" not in claim:
            raise ValueError("claim must include id and statement")
        return cls(
            target_path=str(data["target_path"]),
            claim=claim,
            policy=dict(data.get("policy") or {}),
            protected_paths=list(data.get("protected_paths") or []),
            prior_freeze_sums=list(data.get("prior_freeze_sums") or []),
        )

    @classmethod
    def from_file(cls, path: Path) -> "AuditRequest":
        return cls.from_dict(read_json(path))


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def validate_claim_id(claim_id: str) -> None:
    if not _SAFE_ID.match(claim_id):
        raise ValueError(f"invalid claim id: {claim_id!r}")
