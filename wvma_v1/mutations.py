"""Closed mutation application primitives for WVMA-V1 Batch A2."""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from wvma_v1.canonical import canonical_bytes
from wvma_v1.models import ALLOWED_OPERATION_ENUMS, MutationSpec, loads_strict_json
from wvma_v1.workspace import WorkspaceError, resolve_under_root, validate_relative_path

_SHA256_HEX_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_POINTER_RE = re.compile(r"\A(/[^/~]*(?:~[01][^/~]*)*)*\Z")
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()


class MutationError(ValueError):
    """Closed mutation rejection or apply failure."""


@dataclass(frozen=True)
class MutationApplication:
    """Structured proof that a closed mutation was (or was not) applied."""

    case_id: str
    operation_enum: str
    target_relative_path: str
    preimage_sha256: str
    postimage_sha256: str
    applied: bool

    def to_proof_dict(self) -> dict[str, bool]:
        return {"applied": self.applied}


def _require_mapping(value: Any, field: str) -> dict[str, Any]:
    if value is None:
        raise MutationError(f"{field} is PRESENT-invalid: null")
    if isinstance(value, bool) or not isinstance(value, Mapping):
        raise MutationError(f"{field} must be a mapping; got {type(value).__name__}")
    return {str(k): v for k, v in value.items()}


def _require_str(value: Any, field: str) -> str:
    if value is None:
        raise MutationError(f"{field} is PRESENT-invalid: null")
    if isinstance(value, bool) or not isinstance(value, str):
        raise MutationError(f"{field} must be str; got {type(value).__name__}")
    if value == "":
        raise MutationError(f"{field} must be non-empty str")
    return value


def _require_sha256(value: Any, field: str) -> str:
    text = _require_str(value, field)
    if _SHA256_HEX_RE.match(text) is None:
        raise MutationError(f"{field} must be lowercase sha256 hex")
    return text


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decode_hex(value: Any, field: str) -> bytes:
    text = _require_str(value, field)
    if len(text) % 2 != 0 or any(c not in "0123456789abcdef" for c in text):
        raise MutationError(f"{field} must be lowercase hex")
    try:
        return bytes.fromhex(text)
    except ValueError as exc:
        raise MutationError(f"{field} is not valid hex") from exc


def _decode_b64(value: Any, field: str) -> bytes:
    text = _require_str(value, field)
    try:
        return base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise MutationError(f"{field} is not valid base64") from exc


def _parse_json_pointer(pointer: Any, field: str) -> list[str]:
    text = _require_str(pointer, field)
    if text == "":
        raise MutationError(f"{field} must be non-empty JSON pointer")
    if not text.startswith("/"):
        raise MutationError(f"{field} must start with '/'")
    if _POINTER_RE.match(text) is None:
        raise MutationError(f"{field} is not a valid JSON pointer")
    parts: list[str] = []
    for raw in text.split("/")[1:]:
        parts.append(raw.replace("~1", "/").replace("~0", "~"))
    return parts


def _reject_unknown(data: Mapping[str, Any], allowed: set[str], label: str) -> None:
    unknown = sorted(set(data.keys()) - allowed)
    if unknown:
        raise MutationError(f"{label} has unknown fields: {unknown}")


def _read_file_bytes(path: Path) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def _write_exclusive_or_replace(path: Path, data: bytes, *, replace: bool) -> None:
    """Write bytes; replace=False requires exclusive create, True replaces existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if replace:
        if not path.is_file():
            raise MutationError(f"replace target missing: {path}")
        # Write via temp sibling then atomic replace within same directory.
        tmp = path.with_name(path.name + ".wvma-tmp")
        if tmp.exists():
            raise MutationError(f"temp write path exists: {tmp}")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(str(tmp), flags, 0o644)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(str(tmp), str(path))
        return
    if path.exists():
        raise MutationError(f"add target already exists: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)


def _load_json_object(data: bytes, field: str) -> dict[str, Any]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MutationError(f"{field} is not UTF-8 JSON") from exc
    try:
        obj = loads_strict_json(text)
    except Exception as exc:  # SchemaError
        raise MutationError(f"{field} JSON parse failed: {exc}") from exc
    if not isinstance(obj, dict):
        raise MutationError(f"{field} JSON root must be object")
    return obj


def _json_get(root: dict[str, Any], parts: list[str], field: str) -> tuple[Any, Any, str | None]:
    """Return (parent, current, last_key). parent is mapping/list holding last_key."""
    if not parts:
        raise MutationError(f"{field} cannot target document root")
    current: Any = root
    for i, part in enumerate(parts[:-1]):
        if isinstance(current, dict):
            if part not in current:
                raise MutationError(f"{field} pointer missing at {part}")
            current = current[part]
        elif isinstance(current, list):
            if not part.isdigit():
                raise MutationError(f"{field} list index must be digits")
            idx = int(part)
            if idx >= len(current):
                raise MutationError(f"{field} list index out of range")
            current = current[idx]
        else:
            raise MutationError(f"{field} cannot traverse non-container")
    last = parts[-1]
    return current, current, last


def _json_set(root: dict[str, Any], parts: list[str], value: Any, field: str) -> None:
    parent, _, last = _json_get(root, parts, field)
    if isinstance(parent, dict):
        parent[last] = value
        return
    if isinstance(parent, list):
        if not last.isdigit():
            raise MutationError(f"{field} list index must be digits")
        idx = int(last)
        if idx >= len(parent):
            raise MutationError(f"{field} list index out of range")
        parent[idx] = value
        return
    raise MutationError(f"{field} cannot set into non-container")


def _json_delete(root: dict[str, Any], parts: list[str], field: str) -> None:
    parent, _, last = _json_get(root, parts, field)
    if isinstance(parent, dict):
        if last not in parent:
            raise MutationError(f"{field} pointer missing for delete")
        del parent[last]
        return
    if isinstance(parent, list):
        if not last.isdigit():
            raise MutationError(f"{field} list index must be digits")
        idx = int(last)
        if idx >= len(parent):
            raise MutationError(f"{field} list index out of range")
        del parent[idx]
        return
    raise MutationError(f"{field} cannot delete from non-container")


def _compute_set_json(data: bytes, args: Mapping[str, Any]) -> bytes:
    _reject_unknown(args, {"pointer", "value"}, "SET_JSON_POINTER.arguments")
    if "pointer" not in args or "value" not in args:
        raise MutationError("SET_JSON_POINTER requires pointer and value")
    parts = _parse_json_pointer(args["pointer"], "pointer")
    root = _load_json_object(data, "target")
    _json_set(root, parts, args["value"], "pointer")
    return canonical_bytes(root)


def _compute_delete_json(data: bytes, args: Mapping[str, Any]) -> bytes:
    _reject_unknown(args, {"pointer"}, "DELETE_JSON_POINTER.arguments")
    if "pointer" not in args:
        raise MutationError("DELETE_JSON_POINTER requires pointer")
    parts = _parse_json_pointer(args["pointer"], "pointer")
    root = _load_json_object(data, "target")
    _json_delete(root, parts, "pointer")
    return canonical_bytes(root)


def _compute_replace_bytes(data: bytes, args: Mapping[str, Any]) -> bytes:
    _reject_unknown(args, {"find_hex", "replace_hex"}, "REPLACE_EXACT_BYTES.arguments")
    if "find_hex" not in args or "replace_hex" not in args:
        raise MutationError("REPLACE_EXACT_BYTES requires find_hex and replace_hex")
    find = _decode_hex(args["find_hex"], "find_hex")
    repl = _decode_hex(args["replace_hex"], "replace_hex")
    if find == b"":
        raise MutationError("find_hex must be non-empty")
    count = data.count(find)
    if count != 1:
        raise MutationError(
            f"REPLACE_EXACT_BYTES requires exactly one match; found {count}"
        )
    return data.replace(find, repl, 1)


def _compute_rebind_hashes(data: bytes, args: Mapping[str, Any]) -> bytes:
    """Rebind only explicitly declared JSON-pointer hash fields."""
    _reject_unknown(args, {"bindings"}, "REBIND_DECLARED_HASHES.arguments")
    if "bindings" not in args:
        raise MutationError("REBIND_DECLARED_HASHES requires bindings")
    bindings = args["bindings"]
    if not isinstance(bindings, list) or not bindings:
        raise MutationError("bindings must be a non-empty list")
    root = _load_json_object(data, "target")
    seen_pointers: set[str] = set()
    for i, item in enumerate(bindings):
        entry = _require_mapping(item, f"bindings[{i}]")
        _reject_unknown(entry, {"pointer", "sha256"}, f"bindings[{i}]")
        if "pointer" not in entry or "sha256" not in entry:
            raise MutationError(f"bindings[{i}] requires pointer and sha256")
        pointer = _require_str(entry["pointer"], f"bindings[{i}].pointer")
        if pointer in seen_pointers:
            raise MutationError(f"duplicate binding pointer: {pointer}")
        seen_pointers.add(pointer)
        digest = _require_sha256(entry["sha256"], f"bindings[{i}].sha256")
        parts = _parse_json_pointer(pointer, f"bindings[{i}].pointer")
        _json_set(root, parts, digest, f"bindings[{i}].pointer")
    return canonical_bytes(root)


def _content_from_add_args(args: Mapping[str, Any]) -> bytes:
    _reject_unknown(args, {"content_hex", "content_b64"}, "ADD_DECLARED_FILE.arguments")
    has_hex = "content_hex" in args
    has_b64 = "content_b64" in args
    if has_hex == has_b64:
        raise MutationError(
            "ADD_DECLARED_FILE requires exactly one of content_hex or content_b64"
        )
    if has_hex:
        return _decode_hex(args["content_hex"], "content_hex")
    return _decode_b64(args["content_b64"], "content_b64")


def apply_mutation(
    workspace_root: Path | str,
    spec: MutationSpec,
) -> MutationApplication:
    """Apply one closed mutation inside ``workspace_root`` only.

    Validates path confinement, preimage, and expected postimage in memory
    before any mutating write. On validation failure, the workspace file is
    left unchanged.
    """
    if not isinstance(spec, MutationSpec):
        raise MutationError("spec must be MutationSpec")
    op = spec.operation_enum
    if op not in ALLOWED_OPERATION_ENUMS:
        raise MutationError(f"unsupported operation_enum: {op}")

    try:
        rel = validate_relative_path(spec.target_relative_path, "target_relative_path")
    except WorkspaceError as exc:
        raise MutationError(str(exc)) from exc

    expected_pre = _require_sha256(spec.expected_preimage_sha256, "expected_preimage_sha256")
    expected_post = _require_sha256(
        spec.expected_postimage_sha256, "expected_postimage_sha256"
    )
    args = _require_mapping(spec.operation_arguments, "operation_arguments")

    try:
        target = resolve_under_root(workspace_root, rel)
    except WorkspaceError as exc:
        raise MutationError(str(exc)) from exc

    if op == "ADD_DECLARED_FILE":
        if target.exists():
            raise MutationError("ADD_DECLARED_FILE target already exists")
        new_bytes = _content_from_add_args(args)
        pre = EMPTY_SHA256
        if pre != expected_pre:
            raise MutationError("ADD_DECLARED_FILE preimage mismatch (expected empty)")
        post = _sha256_bytes(new_bytes)
        if post != expected_post:
            raise MutationError("postimage digest mismatch before write")
        _write_exclusive_or_replace(target, new_bytes, replace=False)
        return MutationApplication(
            case_id=spec.case_id,
            operation_enum=op,
            target_relative_path=rel,
            preimage_sha256=pre,
            postimage_sha256=post,
            applied=True,
        )

    if op == "DELETE_DECLARED_FILE":
        _reject_unknown(args, set(), "DELETE_DECLARED_FILE.arguments")
        if not target.is_file():
            raise MutationError("DELETE_DECLARED_FILE target missing")
        current = _read_file_bytes(target)
        pre = _sha256_bytes(current)
        if pre != expected_pre:
            raise MutationError("preimage digest mismatch")
        if expected_post != EMPTY_SHA256:
            raise MutationError(
                "DELETE_DECLARED_FILE expected_postimage_sha256 must be empty digest"
            )
        # Validate complete; then mutate.
        target.unlink()
        if target.exists():
            raise MutationError("DELETE_DECLARED_FILE failed to remove target")
        return MutationApplication(
            case_id=spec.case_id,
            operation_enum=op,
            target_relative_path=rel,
            preimage_sha256=pre,
            postimage_sha256=EMPTY_SHA256,
            applied=True,
        )

    # In-place content ops require an existing file.
    if not target.is_file():
        raise MutationError(f"{op} target missing")
    current = _read_file_bytes(target)
    pre = _sha256_bytes(current)
    if pre != expected_pre:
        raise MutationError("preimage digest mismatch")

    if op == "SET_JSON_POINTER":
        new_bytes = _compute_set_json(current, args)
    elif op == "DELETE_JSON_POINTER":
        new_bytes = _compute_delete_json(current, args)
    elif op == "REPLACE_EXACT_BYTES":
        new_bytes = _compute_replace_bytes(current, args)
    elif op == "REBIND_DECLARED_HASHES":
        new_bytes = _compute_rebind_hashes(current, args)
    else:  # pragma: no cover - guarded by ALLOWED_OPERATION_ENUMS
        raise MutationError(f"unsupported operation_enum: {op}")

    post = _sha256_bytes(new_bytes)
    if post != expected_post:
        raise MutationError("postimage digest mismatch before write")
    if post == pre:
        raise MutationError("mutation is a no-op; refusing equivalent write")

    _write_exclusive_or_replace(target, new_bytes, replace=True)
    verify = _sha256_bytes(_read_file_bytes(target))
    if verify != post:
        raise MutationError("post-write digest verification failed")

    return MutationApplication(
        case_id=spec.case_id,
        operation_enum=op,
        target_relative_path=rel,
        preimage_sha256=pre,
        postimage_sha256=post,
        applied=True,
    )


__all__ = [
    "MutationError",
    "MutationApplication",
    "apply_mutation",
    "EMPTY_SHA256",
]
