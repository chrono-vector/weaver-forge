"""ZIP container reader for VECTOR Package Ingress v0.

Owner-authorized Option B limits. Never extractall. Never execute package bytes.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

MAX_ZIP_ENTRY_COUNT = 32
MAX_ZIP_FILE_BYTES = 262144
MAX_UNCOMPRESSED_PER_ENTRY = 131072
MAX_TOTAL_UNCOMPRESSED = 262144
MAX_RATIO_PER_ENTRY = 50.0
MAX_AGGREGATE_RATIO = 30.0

ALLOWED_COMPRESS = frozenset({zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED})
FILENAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
UNIX_FMT = 0o170000
UNIX_SYMLINK = 0o120000
UNIX_REGULAR = 0o100000
UNIX_EXECUTE = 0o111
DOS_DIRECTORY = 0x10
ZIP64_EXTRA = 0x0001
FLAG_ENCRYPTED = 0x1

REQUIRED_MEMBERS = (
    "HANDOFF_MANIFEST.json",
    "DIGESTS.sha256",
    "WEAVER_REVIEW_INSTRUCTION.md",
    "decision_trace.json",
    "replay_contract.json",
    "replay_eligibility_result.json",
    "verification_pre_handoff_envelope.json",
    "verification_result_record.json",
)
REQUIRED_SET = frozenset(REQUIRED_MEMBERS)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file_streamed(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _note(reasons: list[tuple[str, str]], code: str, message: str) -> None:
    reasons.append((code, message))


def _extra_headers(extra: bytes) -> list[int]:
    headers: list[int] = []
    i = 0
    while i + 4 <= len(extra):
        header_id = int.from_bytes(extra[i : i + 2], "little")
        data_size = int.from_bytes(extra[i + 2 : i + 4], "little")
        headers.append(header_id)
        i += 4 + data_size
        if data_size < 0:
            break
    return headers


def _unix_mode(info: zipfile.ZipInfo) -> int:
    return (info.external_attr >> 16) & 0xFFFF


def _name_candidates(info: zipfile.ZipInfo) -> list[str]:
    names = [info.filename]
    orig = getattr(info, "orig_filename", None)
    if isinstance(orig, str) and orig not in names:
        names.append(orig)
    return names


def _name_unsafe(name: str) -> str | None:
    if not isinstance(name, str) or name == "":
        return "empty name"
    try:
        name.encode("utf-8")
    except UnicodeEncodeError:
        return "non-utf name"
    if "\x00" in name:
        return "nul in name"
    if "\\" in name:
        return "backslash alias"
    if name.startswith("/") or name.startswith("\\"):
        return "absolute path"
    if re.match(r"^[A-Za-z]:", name):
        return "windows drive prefix"
    if name.endswith("/"):
        return "directory entry"
    parts = name.replace("\\", "/").split("/")
    if len(parts) != 1:
        return "nested path"
    if any(p in ("", ".", "..") for p in parts):
        return "path traversal"
    if FILENAME_RE.fullmatch(name) is None:
        return "name outside allow-list"
    return None


def read_vector_zip_v0(zip_path: Path) -> dict[str, Any]:
    """Read a ZIP after fail-closed container checks.

    Returns dict with keys: ok, reason_codes, messages, files, zip_sha256, zip_file_bytes.
    """
    reasons: list[tuple[str, str]] = []
    empty: dict[str, Any] = {
        "ok": False,
        "reason_codes": [],
        "messages": [],
        "files": {},
        "zip_sha256": "",
        "zip_file_bytes": 0,
    }

    path = Path(zip_path)
    if path.is_dir():
        _note(reasons, "container_path_unsafe", "directory input is not a v0 public input")
        empty["reason_codes"] = [c for c, _ in reasons]
        empty["messages"] = [m for _, m in reasons]
        return empty
    if not path.is_file():
        _note(reasons, "container_path_unsafe", f"not a file: {path}")
        empty["reason_codes"] = [c for c, _ in reasons]
        empty["messages"] = [m for _, m in reasons]
        return empty

    zip_file_bytes = path.stat().st_size
    empty["zip_file_bytes"] = zip_file_bytes

    if zip_file_bytes > MAX_ZIP_FILE_BYTES:
        _note(
            reasons,
            "container_limit_exceeded",
            f"zip file {zip_file_bytes} bytes exceeds {MAX_ZIP_FILE_BYTES}",
        )
        empty["reason_codes"] = [c for c, _ in reasons]
        empty["messages"] = [m for _, m in reasons]
        return empty

    zip_sha256 = sha256_file_streamed(path)
    empty["zip_sha256"] = zip_sha256

    try:
        zf = zipfile.ZipFile(path, "r")
    except (OSError, zipfile.BadZipFile) as exc:
        _note(reasons, "container_path_unsafe", f"not a readable zip: {exc}")
        empty["reason_codes"] = [c for c, _ in reasons]
        empty["messages"] = [m for _, m in reasons]
        return empty

    with zf:
        infos = list(zf.infolist())
        if len(infos) > MAX_ZIP_ENTRY_COUNT:
            _note(
                reasons,
                "container_limit_exceeded",
                f"entry count {len(infos)} exceeds {MAX_ZIP_ENTRY_COUNT}",
            )

        raw_seen: set[str] = set()
        norm_seen: dict[str, str] = {}
        declared_total = 0
        member_names: list[str] = []

        for info in infos:
            for cand in _name_candidates(info):
                why = _name_unsafe(cand)
                if why is not None:
                    _note(reasons, "container_path_unsafe", f"{cand!r}: {why}")

            name = info.filename
            if name in raw_seen:
                _note(reasons, "container_duplicate_name", f"duplicate raw name {name!r}")
            raw_seen.add(name)

            folded = unicodedata.normalize("NFC", name).casefold()
            if folded in norm_seen and norm_seen[folded] != name:
                _note(
                    reasons,
                    "container_duplicate_name",
                    f"normalized collision {name!r} vs {norm_seen[folded]!r}",
                )
            elif folded in norm_seen:
                _note(reasons, "container_duplicate_name", f"duplicate normalized name {name!r}")
            else:
                norm_seen[folded] = name

            if info.flag_bits & FLAG_ENCRYPTED:
                _note(
                    reasons,
                    "container_encrypted_or_unsupported_compression",
                    f"{name}: encrypted entry",
                )
            if info.compress_type not in ALLOWED_COMPRESS:
                _note(
                    reasons,
                    "container_encrypted_or_unsupported_compression",
                    f"{name}: unsupported compression {info.compress_type}",
                )
            if ZIP64_EXTRA in _extra_headers(info.extra or b""):
                _note(
                    reasons,
                    "container_encrypted_or_unsupported_compression",
                    f"{name}: ZIP64 extra field",
                )

            unix_mode = _unix_mode(info)
            file_type = unix_mode & UNIX_FMT
            if file_type == UNIX_SYMLINK:
                _note(reasons, "container_path_unsafe", f"{name}: symlink")
            elif file_type not in (0, UNIX_REGULAR):
                _note(reasons, "container_path_unsafe", f"{name}: unsafe special file type")
            if unix_mode & UNIX_EXECUTE:
                _note(reasons, "container_path_unsafe", f"{name}: execute bit")
            if info.external_attr & DOS_DIRECTORY:
                _note(reasons, "container_path_unsafe", f"{name}: directory attribute")

            if info.file_size > MAX_UNCOMPRESSED_PER_ENTRY:
                _note(
                    reasons,
                    "container_limit_exceeded",
                    f"{name}: uncompressed {info.file_size} exceeds {MAX_UNCOMPRESSED_PER_ENTRY}",
                )
            declared_total += info.file_size
            if info.compress_size == 0 and info.file_size > 0 and info.compress_type != zipfile.ZIP_STORED:
                _note(
                    reasons,
                    "container_limit_exceeded",
                    f"{name}: zero compressed size with nonzero uncompressed size",
                )
            elif info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_RATIO_PER_ENTRY:
                    _note(
                        reasons,
                        "container_limit_exceeded",
                        f"{name}: compression ratio {ratio:.3f} exceeds {MAX_RATIO_PER_ENTRY}",
                    )
            member_names.append(name)

        if declared_total > MAX_TOTAL_UNCOMPRESSED:
            _note(
                reasons,
                "container_limit_exceeded",
                f"total uncompressed {declared_total} exceeds {MAX_TOTAL_UNCOMPRESSED}",
            )
        if zip_file_bytes > 0:
            aggregate = declared_total / zip_file_bytes
            if aggregate > MAX_AGGREGATE_RATIO:
                _note(
                    reasons,
                    "container_limit_exceeded",
                    f"aggregate compression ratio {aggregate:.3f} exceeds {MAX_AGGREGATE_RATIO}",
                )

        present = set(member_names)
        extra = sorted(present - REQUIRED_SET)
        missing = sorted(REQUIRED_SET - present)
        if extra or missing:
            _note(
                reasons,
                "container_undeclared_or_missing_member",
                f"extra={extra} missing={missing}",
            )

        if reasons:
            return {
                "ok": False,
                "reason_codes": [c for c, _ in reasons],
                "messages": [m for _, m in reasons],
                "files": {},
                "zip_sha256": zip_sha256,
                "zip_file_bytes": zip_file_bytes,
            }

        files: dict[str, bytes] = {}
        for info in infos:
            name = info.filename
            try:
                with zf.open(info, "r") as handle:
                    buf = bytearray()
                    while True:
                        chunk = handle.read(65536)
                        if not chunk:
                            break
                        buf.extend(chunk)
                        if len(buf) > MAX_UNCOMPRESSED_PER_ENTRY:
                            _note(
                                reasons,
                                "container_limit_exceeded",
                                f"{name}: streamed size exceeds {MAX_UNCOMPRESSED_PER_ENTRY}",
                            )
                            break
            except RuntimeError as exc:
                _note(
                    reasons,
                    "container_encrypted_or_unsupported_compression",
                    f"{name}: {exc}",
                )
                continue
            actual = bytes(buf)
            if len(actual) != info.file_size:
                _note(
                    reasons,
                    "container_byte_length_mismatch",
                    f"{name}: declared {info.file_size} actual {len(actual)}",
                )
            if len(actual) > MAX_TOTAL_UNCOMPRESSED:
                _note(
                    reasons,
                    "container_limit_exceeded",
                    f"{name}: actual size exceeds total uncompressed limit",
                )
            files[name] = actual

        total_actual = sum(len(v) for v in files.values())
        if total_actual > MAX_TOTAL_UNCOMPRESSED:
            _note(
                reasons,
                "container_limit_exceeded",
                f"actual total uncompressed {total_actual} exceeds {MAX_TOTAL_UNCOMPRESSED}",
            )

        if reasons:
            return {
                "ok": False,
                "reason_codes": [c for c, _ in reasons],
                "messages": [m for _, m in reasons],
                "files": {},
                "zip_sha256": zip_sha256,
                "zip_file_bytes": zip_file_bytes,
            }

        return {
            "ok": True,
            "reason_codes": [],
            "messages": [],
            "files": files,
            "zip_sha256": zip_sha256,
            "zip_file_bytes": zip_file_bytes,
        }
