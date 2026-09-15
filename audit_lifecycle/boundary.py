from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


class BoundaryViolation(RuntimeError):
    """Raised when a write would escape the allowed boundary (fail-closed)."""


class BoundaryManager:
    """Enforces allowed-write and protected-path rules for an audit run."""

    def __init__(self, allowed_root: Path, protected_paths: Iterable[str | Path]):
        self.allowed_root = allowed_root.resolve()
        self.protected = [Path(p).resolve() for p in protected_paths]

    def is_under(self, path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root)
            return True
        except ValueError:
            return False

    def assert_writable(self, path: Path) -> Path:
        resolved = path.resolve()
        if not self.is_under(resolved, self.allowed_root):
            raise BoundaryViolation(
                f"WRITE_DENIED_OUTSIDE_ALLOWED_ROOT: {resolved} not under {self.allowed_root}"
            )
        for prot in self.protected:
            if resolved == prot or self.is_under(resolved, prot):
                raise BoundaryViolation(
                    f"WRITE_DENIED_PROTECTED_PATH: {resolved} intersects {prot}"
                )
            # Also deny writing *into* a protected file's parent freeze dir listed as file
            if prot.is_file() and resolved == prot:
                raise BoundaryViolation(f"WRITE_DENIED_PROTECTED_FILE: {resolved}")
        return resolved

    def open_write(self, path: Path, data: bytes | str, encoding: str = "utf-8") -> Path:
        target = self.assert_writable(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            target.write_text(data, encoding=encoding)
        else:
            target.write_bytes(data)
        return target

    def probe_protected_write(self, attempted: Path) -> dict:
        """Attempt classification for a protected path without writing."""
        try:
            self.assert_writable(attempted)
            return {
                "attempted": str(attempted),
                "fail_closed": False,
                "would_allow": True,
                "result": "FAIL",
                "detail": "UNEXPECTED_ALLOW",
            }
        except BoundaryViolation as e:
            created = attempted.exists()
            return {
                "attempted": str(attempted),
                "fail_closed": True,
                "would_allow": False,
                "file_created": created,
                "result": "PASS" if not created else "FAIL",
                "detail": str(e),
            }
