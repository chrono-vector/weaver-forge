"""Pure, fail-closed consumer of T1 structural-evaluation stdout v1.

consume_stdout_v1 validates supplied bytes/context/exit, NOT execution, capture
completion, provenance, filesystem identity or nonce freshness. The Host must
supply independently established expectations and a fresh request per invocation.
Identical inputs deliberately yield identical observations (there is no replay
cache). A returned FAIL is a valid failure observation, not a successful gate.
No observation is a complete Contract result or a machine_verdict_ceiling.

Local resource budgets: stdout <= 1 MiB, JSON line <= 64 KiB, integer tokens <=
20 decimal digits. These are consumer limits, not changes to T1 wire authority.
Diagnostics are opaque except that reserved frame words outside the final frame
are rejected conservatively. LF/CRLF are framing syntax only; bytes aren't
rewritten. Absolute paths are checked lexically, never resolved or opened.
"""

from dataclasses import dataclass
import json
from pathlib import PurePosixPath, PureWindowsPath
import re

__all__ = ["ExpectedBinding", "ExpectedContext", "StructuralObservation",
           "ConsumerRejected", "consume_stdout_v1"]

_BEGIN = "WEAVER_FORGE_VALIDATOR_RESULT_BEGIN v1"
_END = "WEAVER_FORGE_VALIDATOR_RESULT_END v1"
_RESERVED = "WEAVER_FORGE_VALIDATOR_RESULT_"
_MAX_STDOUT = 1024 * 1024
_MAX_JSON = 64 * 1024
_BINDING_KEYS = frozenset(("evidence_dir", "run_id", "manifest_sha256",
                           "final_binding_sha256", "validator_script_sha256",
                           "schema_register_version", "schema_register_sha256"))
_KEYS = frozenset(("format_version", "result_scope", "mode", "request_id",
                   "binding_status", "binding", "structural_status", "error_count",
                   "ceiling_state", "computed_ceiling"))
_HASH_KEYS = ("manifest_sha256", "final_binding_sha256", "validator_script_sha256",
              "schema_register_sha256")
_MODES = ("host-preliminary", "final-submission")
_CEILINGS = ("PASS", "PARTIAL", "FAIL", "INDETERMINATE")


class ConsumerRejected(ValueError):
    """Rejected input/context; code is stable and contains no untrusted text."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ExpectedBinding:
    evidence_dir: str
    run_id: str
    manifest_sha256: str
    final_binding_sha256: str
    validator_script_sha256: str
    schema_register_version: str
    schema_register_sha256: str


@dataclass(frozen=True)
class ExpectedContext:
    request_id: str
    mode: str
    binding: ExpectedBinding


@dataclass(frozen=True)
class StructuralObservation:
    """T1-only, fully bound observation; structural_status may be FAIL."""

    format_version: int
    result_scope: str
    mode: str
    request_id: str
    binding_status: str
    binding: ExpectedBinding
    structural_status: str
    error_count: int
    ceiling_state: str
    computed_ceiling: str | None


def _reject(code):
    raise ConsumerRejected(code)


def _matches(value, pattern):
    return type(value) is str and re.fullmatch(pattern, value) is not None


def _absolute_path(value):
    if type(value) is not str or not value:
        return False
    if any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value):
        return False
    # Do not normalize caller expectations or consult the host OS/filesystem.
    if value.startswith("/"):
        return PurePosixPath(value).is_absolute() and not any(
            p in (".", "..") for p in value.split("/"))
    return PureWindowsPath(value).is_absolute() and not any(
        p in (".", "..") for p in value.replace("\\", "/").split("/"))


def _validate_binding(binding):
    if type(binding) is not dict or binding.keys() != _BINDING_KEYS:
        _reject("binding_fields")
    if not _absolute_path(binding["evidence_dir"]):
        _reject("binding_path")
    if type(binding["schema_register_version"]) is not str or binding["schema_register_version"] != "rc6.5":
        _reject("binding_version")
    run = binding["run_id"]
    if run is not None and (not _matches(run, r"[A-Za-z0-9_.-]+") or ".." in run):
        _reject("binding_run_id")
    for name in _HASH_KEYS:
        value = binding[name]
        if value is not None and not _matches(value, r"[0-9a-f]{64}"):
            _reject("binding_hash")
    return "BOUND" if all(v is not None for v in binding.values()) else "UNAVAILABLE"


def _validate_expected(expected):
    if type(expected) is not ExpectedContext or type(expected.binding) is not ExpectedBinding:
        _reject("expected_context")
    if not _matches(expected.request_id, r"[0-9a-f]{32}"):
        _reject("expected_context")
    if type(expected.mode) is not str or expected.mode not in _MODES:
        _reject("expected_context")
    values = {name: getattr(expected.binding, name) for name in _BINDING_KEYS}
    try:
        available = _validate_binding(values)
    except ConsumerRejected:
        _reject("expected_context")
    if available != "BOUND":
        _reject("expected_context")
    return values


def _frame_payload(raw):
    if type(raw) is not bytes:
        _reject("stdout_type")
    if len(raw) > _MAX_STDOUT:
        _reject("stdout_size")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError:
        _reject("stdout_encoding")
    if not text.endswith("\n"):
        _reject("frame_boundary")
    lines = text[:-1].split("\n")
    lines = [line[:-1] if line.endswith("\r") else line for line in lines]
    if any("\r" in line for line in lines):
        _reject("frame_boundary")
    if len(lines) < 3 or lines[-3] != _BEGIN or lines[-1] != _END:
        _reject("frame_boundary")
    if any(_RESERVED in line for line in lines[:-3]):
        _reject("frame_ambiguous")
    payload = lines[-2]
    if len(payload.encode("utf-8")) > _MAX_JSON:
        _reject("json_size")
    return payload


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _reject("json_duplicate_key")
        result[key] = value
    return result


def _integer(token):
    # Avoid dependence on sys.set_int_max_str_digits for hostile giant numbers.
    if len(token.lstrip("-")) > 20:
        _reject("json_integer_size")
    return int(token)


def _nonfinite(_token):
    _reject("json_nonfinite")


def _json_object(payload):
    try:
        obj = json.loads(payload, object_pairs_hook=_unique_object,
                         parse_int=_integer, parse_constant=_nonfinite)
    except ConsumerRejected:
        raise
    except (ValueError, RecursionError):
        _reject("json_syntax")
    if type(obj) is not dict or obj.keys() != _KEYS:
        _reject("result_fields")
    return obj


def _validate_result(obj, process_exit):
    if type(obj["format_version"]) is not int or obj["format_version"] != 1:
        _reject("format_version")
    if type(obj["result_scope"]) is not str or obj["result_scope"] != "structural-evaluation":
        _reject("result_scope")
    if type(obj["mode"]) is not str or obj["mode"] not in _MODES:
        _reject("mode")
    if not _matches(obj["request_id"], r"[0-9a-f]{32}"):
        _reject("request_id")
    availability = _validate_binding(obj["binding"])
    if type(obj["binding_status"]) is not str or obj["binding_status"] != availability:
        _reject("binding_status")
    count = obj["error_count"]
    if type(count) is not int or count < 0:
        _reject("error_count")
    status = obj["structural_status"]
    if type(status) is not str or status != ("FAIL" if count else "PASS"):
        _reject("structural_status")
    if process_exit != (1 if count else 0):
        _reject("exit_consistency")
    state, ceiling = obj["ceiling_state"], obj["computed_ceiling"]
    if type(state) is not str:
        _reject("ceiling_state")
    if state == "COMPUTED":
        if type(ceiling) is not str or ceiling not in _CEILINGS:
            _reject("computed_ceiling")
    elif state == "NOT_COMPUTED":
        if ceiling is not None or count == 0:
            _reject("computed_ceiling")
    else:
        _reject("ceiling_state")
    if availability != "BOUND":
        _reject("binding_unavailable")


def consume_stdout_v1(raw_stdout: bytes, expected: ExpectedContext,
                      process_exit: int) -> StructuralObservation:
    """Return a bound T1 observation or raise ConsumerRejected.

    A normal supplied exit must be exact int 0 or 1. No timeout/signal/spawn
    inference, nonce generation/history, file/capture verification or Host gate
    is performed. Expected binding must be independently established by caller.
    Unknown/missing/duplicate fields and any mismatch reject without repair.
    """
    expected_binding = _validate_expected(expected)
    if type(process_exit) is not int or process_exit not in (0, 1):
        _reject("process_exit")
    obj = _json_object(_frame_payload(raw_stdout))
    _validate_result(obj, process_exit)
    if obj["request_id"] != expected.request_id:
        _reject("request_mismatch")
    if obj["mode"] != expected.mode:
        _reject("mode_mismatch")
    if obj["binding"] != expected_binding:
        _reject("binding_mismatch")
    # All members are now exact immutable scalar values, not caller dictionaries.
    return StructuralObservation(
        format_version=obj["format_version"], result_scope=obj["result_scope"],
        mode=obj["mode"], request_id=obj["request_id"],
        binding_status=obj["binding_status"], binding=ExpectedBinding(**obj["binding"]),
        structural_status=obj["structural_status"], error_count=obj["error_count"],
        ceiling_state=obj["ceiling_state"], computed_ceiling=obj["computed_ceiling"])
