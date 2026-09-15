"""Safety primitives: path confinement, locks, redaction, fail-closed I/O."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

DEFAULT_LOCK_STALE_SECONDS = 3600


class SafetyError(RuntimeError):
    """Fail-closed safety violation."""


def resolve_confined(root: Path, rel: str | Path) -> Path:
    """Resolve path under root; reject traversal / absolute escapes."""
    root = root.resolve()
    raw = Path(rel)
    if raw.is_absolute():
        # Allow absolute only if it still resolves under root.
        candidate = raw.resolve()
    else:
        # Reject obvious traversal tokens before join.
        parts = raw.parts
        if any(p == ".." for p in parts):
            raise SafetyError(f"path traversal rejected: {rel}")
        candidate = (root / raw).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SafetyError(f"path escapes workspace root: {rel}") from exc
    return candidate


def sha256_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise SafetyError(f"failed to load JSON (fail-closed): {path}: {exc}") from exc


def write_json(path: Path, data: Any, *, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


def append_jsonl(path: Path, record: dict[str, Any], *, dry_run: bool = False) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, ensure_ascii=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")


def redact_secrets(obj: Any) -> Any:
    """Redact values whose keys look secret-bearing."""
    secret_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "private_key",
        "credential",
        "authorization",
    }
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower().replace("-", "_") in secret_keys:
                out[k] = "[REDACTED]"
            else:
                out[k] = redact_secrets(v)
        return out
    if isinstance(obj, list):
        return [redact_secrets(x) for x in obj]
    return obj


class CampaignLock:
    """Simple exclusive lock with stale detection (fail-closed)."""

    def __init__(
        self,
        lock_path: Path,
        *,
        owner: str,
        stale_seconds: int = DEFAULT_LOCK_STALE_SECONDS,
        dry_run: bool = False,
    ) -> None:
        self.lock_path = lock_path
        self.owner = owner
        self.stale_seconds = stale_seconds
        self.dry_run = dry_run
        self._held = False

    def acquire(self) -> None:
        if self.dry_run:
            self._held = True
            return
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if self.lock_path.exists():
            try:
                meta = load_json(self.lock_path)
            except SafetyError as exc:
                raise SafetyError(f"corrupted campaign lock: {exc}") from exc
            acquired_at = float(meta.get("acquired_at_epoch", 0))
            age = time.time() - acquired_at
            if age < self.stale_seconds and meta.get("owner") != self.owner:
                raise SafetyError(
                    f"campaign lock held by {meta.get('owner')} age={age:.0f}s"
                )
            # Stale or same-owner: allow takeover after recording.
        payload = {
            "owner": self.owner,
            "acquired_at_epoch": time.time(),
            "pid": os.getpid(),
        }
        write_json(self.lock_path, payload)
        self._held = True

    def release(self) -> None:
        if self.dry_run:
            self._held = False
            return
        if not self._held:
            return
        if self.lock_path.exists():
            try:
                meta = load_json(self.lock_path)
                if meta.get("owner") == self.owner:
                    self.lock_path.unlink()
            except SafetyError:
                # Fail closed on release anomalies: leave lock for operator.
                pass
        self._held = False

    def __enter__(self) -> "CampaignLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def assert_not_frozen_write(workspace: Path, target: Path) -> None:
    """Refuse writes into frozen package directories."""
    rel = str(target.resolve()).replace("\\", "/")
    ws = str(workspace.resolve()).replace("\\", "/")
    if "/freeze/" in rel and rel.startswith(ws) and "_FROZEN" in rel:
        raise SafetyError(f"refusing write into frozen package: {target}")


def safe_relative(path: Path, root: Path) -> str:
    """Portable relative path using forward slashes."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        # Outside root — return basename only to avoid absolute leakage.
        return path.name
