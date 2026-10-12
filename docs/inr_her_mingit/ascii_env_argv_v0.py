"""Proposed ASCII environment block and argv serialization.

Two pure functions only. They do not read the host environment, launch a
process, or call a native API. A PROPOSED result is a serialization
candidate. It is not execution authorization.

MINGIT_CRT_COMPATIBLE is false. The command string is space-separated text
for the narrow profile below. It is not a MinGit CRT or wmain claim.

WINDOWS_ENVIRONMENT_SORT_CLOSED is false. Entries are ordered by an
ASCII-uppercase key name, and the original key spelling is kept. That is
the procedure used by this module. It does not close the unspecified
reviewed Windows sort procedure.

ASCII and no-space restrictions are fixture-only proposals. They are not
approved EB-14/F5 operational policy.
"""

from __future__ import annotations

from typing import NamedTuple

EXECUTION_AUTHORIZED = False
MINGIT_CRT_COMPATIBLE = False
WINDOWS_ENVIRONMENT_SORT_CLOSED = False

_ASCII_UPPER = str.maketrans(
    "abcdefghijklmnopqrstuvwxyz",
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
)
_APPROVED_KEYS = frozenset({
    "PATH",
    "GIT_NO_REPLACE_OBJECTS",
    "GIT_TERMINAL_PROMPT",
    "GIT_OPTIONAL_LOCKS",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_GLOBAL",
    "HOME",
    "USERPROFILE",
    "XDG_CONFIG_HOME",
    "SystemRoot",
    "WINDIR",
})
_FLAG_VALUES = {
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_CONFIG_NOSYSTEM": "1",
}
_PATH_KEYS = frozenset({
    "PATH",
    "GIT_CONFIG_GLOBAL",
    "HOME",
    "USERPROFILE",
    "XDG_CONFIG_HOME",
    "SystemRoot",
    "WINDIR",
})
_FORBIDDEN_EXACT = frozenset({
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_EXEC_PATH",
    "GIT_CONFIG",
    "GIT_CONFIG_SYSTEM",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_ASKPASS",
    "PAGER",
    "GIT_PAGER",
    "LESS",
    "TEMP",
    "TMP",
})
_FIXED_SUFFIXES = frozenset({
    ("--version",),
    ("--exec-path",),
    ("config", "--list", "--show-scope", "-z"),
})
_WHITESPACE = frozenset(" \t\v\f\r\n")
_IMAGE_SUFFIX = ("ucrt64", "bin", "git.exe")
_PATH_SUFFIX = ("ucrt64", "bin")


class Proposal(NamedTuple):
    status: str
    reason: str
    proposed: bytes | str | None
    execution_authorized: bool


def _refused(reason: str) -> Proposal:
    return Proposal("REFUSED", reason, None, EXECUTION_AUTHORIZED)


def _accepted(payload: bytes | str) -> Proposal:
    return Proposal("PROPOSED", "PROPOSED", payload, EXECUTION_AUTHORIZED)


def _ascii_upper(text: str) -> str:
    return text.translate(_ASCII_UPPER)


def _defect(text: str) -> str | None:
    if "\x00" in text:
        return "NUL_REJECTED"
    for char in text:
        code = ord(char)
        if 0xD800 <= code <= 0xDFFF:
            return "ISOLATED_SURROGATE"
        if char in _WHITESPACE:
            return "WHITESPACE"
        if code < 32 or code == 127:
            return "CONTROL_CHARACTER"
        if char in "\"'":
            return "QUOTE"
        if char in "*?":
            return "WILDCARD"
        if code > 127:
            return "NON_ASCII"
    return None


def _valid_key(key: str) -> bool:
    if key == "":
        return False
    first = key[0]
    if not (("A" <= first <= "Z") or ("a" <= first <= "z") or first == "_"):
        return False
    for char in key[1:]:
        if ("A" <= char <= "Z") or ("a" <= char <= "z") or ("0" <= char <= "9") or char == "_":
            continue
        return False
    return True


def _forbidden(upper: str) -> bool:
    if upper in _FORBIDDEN_EXACT:
        return True
    if upper.startswith("GIT_CONFIG_KEY_") or upper.startswith("GIT_CONFIG_VALUE_"):
        return True
    return upper.startswith("GIT_SSH")


def _components(text: str) -> tuple[str, ...] | None:
    if len(text) < 3:
        return None
    drive = text[0]
    if not (("A" <= drive <= "Z") or ("a" <= drive <= "z")):
        return None
    if text[1] != ":" or text[2] not in "\\/":
        return None
    parts: list[str] = []
    buf: list[str] = []
    for char in text[3:]:
        if char in "\\/":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(char)
    parts.append("".join(buf))
    for part in parts:
        if part in ("", ".", ".."):
            return None
        if part.endswith("."):
            return None
        for char in part:
            if ("A" <= char <= "Z") or ("a" <= char <= "z") or ("0" <= char <= "9") or char in "._-":
                continue
            return None
    return tuple(parts)


def _utf16le_block(pairs: list[tuple[str, str]]) -> bytes:
    ordered = sorted(pairs, key=lambda item: _ascii_upper(item[0]))
    out = bytearray()
    for key, value in ordered:
        out += f"{key}={value}".encode("utf-16-le")
        out += b"\x00\x00"
    out += b"\x00\x00"
    return bytes(out)


def propose_utf16le_environment_block(snapshot: object) -> Proposal:
    """Validate one controller-owned ASCII snapshot and propose UTF-16LE bytes."""
    if type(snapshot) is not dict:
        return _refused("INPUT_REJECTED")
    pairs: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key, value in snapshot.items():
        if type(key) is not str or type(value) is not str:
            return _refused("INPUT_REJECTED")
        key_defect = _defect(key)
        if key_defect is not None:
            return _refused(key_defect)
        if not _valid_key(key):
            return _refused("INVALID_KEY")
        value_defect = _defect(value)
        if value_defect is not None:
            return _refused(value_defect)
        upper = _ascii_upper(key)
        if upper in seen:
            return _refused("DUPLICATE_KEY")
        seen.add(upper)
        pairs.append((key, value))
    for key, _value in pairs:
        if _forbidden(_ascii_upper(key)):
            return _refused("FORBIDDEN_KEY")
    for key, _value in pairs:
        if key not in _APPROVED_KEYS:
            return _refused("UNAUTHORIZED_KEY")
    if {key for key, _value in pairs} != _APPROVED_KEYS:
        return _refused("MISSING_REQUIRED_KEY")
    values = {key: value for key, value in pairs}
    for key, expected in _FLAG_VALUES.items():
        if values[key] != expected:
            return _refused("INVALID_VALUE")
    for key in _PATH_KEYS:
        parts = _components(values[key])
        if parts is None:
            return _refused("INVALID_VALUE")
        if key == "PATH" and (len(parts) < 2 or parts[-2:] != _PATH_SUFFIX):
            return _refused("INVALID_VALUE")
    if values["HOME"] != values["USERPROFILE"]:
        return _refused("INCONSISTENT_VALUE")
    if values["SystemRoot"] != values["WINDIR"]:
        return _refused("INCONSISTENT_VALUE")
    return _accepted(_utf16le_block(pairs))


def propose_ascii_command_line(argv: object) -> Proposal:
    """Validate one fixed ASCII argv sequence and propose a command string."""
    if type(argv) is str or type(argv) is bytes:
        return _refused("RAW_COMMAND_LINE")
    if type(argv) is not list and type(argv) is not tuple:
        return _refused("INPUT_REJECTED")
    items: list[str] = []
    for arg in argv:
        if type(arg) is not str:
            return _refused("INPUT_REJECTED")
        defect = _defect(arg)
        if defect is not None:
            return _refused(defect)
        items.append(arg)
    if not items:
        return _refused("UNSUPPORTED_ARGV")
    image = items[0]
    suffix = tuple(items[1:])
    if suffix not in _FIXED_SUFFIXES:
        return _refused("UNSUPPORTED_ARGV")
    parts = _components(image)
    if parts is None or len(parts) < 3 or parts[-3:] != _IMAGE_SUFFIX:
        return _refused("UNSUPPORTED_ARGV")
    return _accepted(" ".join(items))
