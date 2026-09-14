from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .boundary import BoundaryManager
from .request import sha256_file, write_json


class EvidenceCollector:
    def __init__(self, boundary: BoundaryManager, audit_root: Path):
        self.boundary = boundary
        self.audit_root = audit_root
        self.raw = audit_root / "evidence" / "raw"
        self.logs = audit_root / "evidence" / "logs"
        self.boundary.assert_writable(self.raw / ".keep")
        self.raw.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def write_raw_json(self, name: str, obj: Any) -> Path:
        path = self.raw / name
        self.boundary.open_write(path, "")  # assert then overwrite via write_json
        write_json(path, obj)
        return path

    def write_log(self, name: str, text: str) -> Path:
        path = self.logs / name
        self.boundary.open_write(path, text if text.endswith("\n") else text + "\n")
        return path

    def bind_sha256sums(self, relative_globs: Iterable[str] | None = None) -> Path:
        """Write SHA256SUMS.txt for all evidence-bound files under audit_root (excl. the sums file itself)."""
        lines: list[str] = []
        skip_names = {"SHA256SUMS.txt", "SHA256SUMS_EXECUTION.txt"}
        for p in sorted(self.audit_root.rglob("*")):
            if not p.is_file():
                continue
            if p.name in skip_names:
                continue
            if p.suffix == ".pyc" or "__pycache__" in p.parts:
                continue
            rel = p.relative_to(self.audit_root).as_posix()
            lines.append(f"{sha256_file(p)}  {rel}")
        sums_path = self.audit_root / "SHA256SUMS.txt"
        self.boundary.open_write(sums_path, "\n".join(lines) + "\n")
        return sums_path

    def verify_sha256sums(self, sums_path: Path | None = None) -> dict[str, Any]:
        sums_path = sums_path or (self.audit_root / "SHA256SUMS.txt")
        ok = 0
        fail = 0
        details = []
        for line in sums_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            digest, rel = line.split(None, 1)
            path = self.audit_root / rel
            if not path.is_file():
                fail += 1
                details.append({"path": rel, "ok": False, "error": "MISSING"})
                continue
            actual = sha256_file(path)
            match = actual == digest.lower()
            if match:
                ok += 1
            else:
                fail += 1
            details.append({"path": rel, "ok": match, "expected": digest.lower(), "actual": actual})
        return {"ok": fail == 0, "matched": ok, "mismatched": fail, "details": details}
