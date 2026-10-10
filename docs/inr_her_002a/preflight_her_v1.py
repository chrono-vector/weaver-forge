"""Read-only Phase 2A gate for INR-HER-001.

The accepted Phase 1 supervisor is called only after schema_version values are
hashable. This module does not edit that supervisor, create a token or Job,
download a runtime, or ratify a digest.
"""

from __future__ import annotations

import ctypes
import json
import os
import platform
import shutil
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

from docs.inr_001.schema_check import check as schema_check
from docs.inr_her_001.supervisor_her_v1 import evaluate_event
from docs.inr_her_001.validate_her_v1 import assert_schema_contract

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "inr_her_phase2a_result_v0.schema.json"
ROOT = Path(__file__).resolve().parents[2]
RESULT_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
assert_schema_contract(RESULT_SCHEMA)

PYTHON_PIN_STATUS = "PIN_PENDING"
GIT_PIN_STATUS = "UNRATIFIED"
REQUIRED_PYTHON = "3.11.9"
N1_PHASE1_EDIT = "STOPPED"
N1_PHASE1_SITE = "docs/inr_her_001/supervisor_her_v1.py:_version_reason"
FRESHNESS_PROCEDURE_ID = "N2_EXTERNAL_BINDING_UNEXECUTED"
PIN_PROCEDURE_ID = "AUTHENTICATED_SHA256_UNEXECUTED"
REQUIRED_PRIVILEGES = (
    "SeAssignPrimaryTokenPrivilege",
    "SeIncreaseQuotaPrivilege",
)
CHECK_IDS = (
    "schema_version",
    "platform",
    "cpython_identity",
    "cpython_pin",
    "mingit_identity",
    "mingit_pin",
    "privileges",
    "git_execution_path",
    "git_config",
    "event_freshness",
    "claim_boundary",
)
NONCLAIMS = (
    "phase1_source_edited",
    "restricted_token_isolation",
    "job_containment",
    "event_freshness",
    "independent_external_witness",
    "full_inr_pass",
    "human_final",
    "production_authority",
    "external_run",
    "python_3_11_9_sha256_ratified",
    "mingit_digest_ratified",
    "privileged_windows_tests_executed",
)
PRIORITY = (
    "HER_CONTRADICTION",
    "HER_EVENT_RELABEL_NOT_FRESH",
    "HER_EVENT_REPLAY_UNAUTHENTICATED",
    "HER_SUBSTITUTED_HEAD_NOT_FRESH",
    "HER_SCHEMA_VERSION",
    "HER_SCHEMA_REJECTED",
    "HER_PLATFORM_UNSUPPORTED",
    "HER_RUNTIME_ABSENT",
    "HER_PYTHON_IDENTITY_MISMATCH",
    "HER_PYTHON_PIN_PENDING",
    "HER_GIT_RUNTIME_ABSENT",
    "HER_GIT_SOURCE_NOT_SNAPSHOT",
    "HER_GIT_PIN_UNRATIFIED",
    "HER_GIT_CONFIG_UNCLOSED",
    "HER_GIT_CONFIG_UNVERIFIED",
    "HER_TOKEN_PRIVILEGE_UNAVAILABLE",
    "HER_PRIVILEGED_OBSERVATION_UNVERIFIED",
    "HER_PRIVILEGE_OBSERVATION_UNAVAILABLE",
    "HER_FRESHNESS_UNPROVEN",
    "HER_EVENT_ABSENT",
    "HER_SCHEMA_VERSION_HASHABLE",
    "HER_PLATFORM_OBSERVED",
    "HER_PYTHON_IDENTITY_OBSERVED",
    "HER_GIT_IDENTITY_OBSERVED",
    "HER_NO_PASS_CLAIM",
    "HER_PHASE1_PASS_FORBIDDEN",
    "HER_PHASE2A_PASS_FORBIDDEN",
)
_PASS_CLAIMS = frozenset({
    "PASS",
    "HASH_AGREEMENT_ONLY",
    "FRESH",
    "ISOLATION_PASS",
    "FULL_INR_PASS",
})
_CONFIG_SCOPES = frozenset({"system", "global", "local", "command", "worktree"})
PIN_PROCEDURE = {
    "id": PIN_PROCEDURE_ID,
    "executed": False,
    "python": {
        "product": "CPython 3.11.9 Windows x86-64 official distribution",
        "status": PYTHON_PIN_STATUS,
        "sha256": None,
        "steps": (
            "Obtain the exact official Windows x86-64 artifact over authenticated HTTPS from python.org.",
            "Verify the publisher signature and the SHA-256 published for that exact filename in the same authenticated session.",
            "Compute SHA-256 over those downloaded bytes locally.",
            "Ratify only when the local digest equals that authenticated published digest.",
            "Leave the pin PIN_PENDING until that comparison is done on the authentic bytes.",
        ),
    },
    "mingit": {
        "product": "MinGit Windows x86-64 build that would read the Git snapshot",
        "status": GIT_PIN_STATUS,
        "sha256": None,
        "steps": (
            "Name the exact MinGit version and filename before any digest is considered.",
            "Obtain those bytes over authenticated HTTPS from the Git for Windows release.",
            "Verify the publisher-attested SHA-256 for that exact asset.",
            "Compute SHA-256 locally and ratify only when the digests are equal.",
            "Bind later Git execution to that pinned tree.",
            "Leave the digest UNRATIFIED until that comparison is done on the authentic bytes.",
        ),
    },
}
FRESHNESS_PROCEDURE = {
    "id": FRESHNESS_PROCEDURE_ID,
    "executed": False,
    "accepts_hash_agreement_as_freshness": False,
    "accepts_relabeled_event_id_as_freshness": False,
    "steps": (
        "An issuer outside the HER supervisor signs one binding of a new nonce, the issue time, the event_id, the source head, and each surface freeze hash.",
        "The verifier checks that signature with a key the supervisor does not hold.",
        "The verifier rejects a nonce that is already recorded, an event_id that differs from the binding, and a head string that differs from the bound head.",
        "Uniform relabeling of every event_id, a replayed binding, and a substituted head remain failures.",
        "Hash agreement without that binding stays HER_FRESHNESS_UNPROVEN.",
    ),
}


def pin_procedure() -> dict:
    """Return the unexecuted authenticated-digest procedure."""
    return json.loads(json.dumps(PIN_PROCEDURE))


def freshness_procedure() -> dict:
    """Return the unexecuted N2 binding procedure."""
    return json.loads(json.dumps(FRESHNESS_PROCEDURE))


def n1_stopped_patch() -> str:
    """Minimal Phase 1 change. It is recorded here and is not applied."""
    return (
        "File: docs/inr_her_001/supervisor_her_v1.py\n"
        "Function: _version_reason\n"
        "Insert immediately above `if any(item in R3_SCHEMA_VERSIONS for item in versions):`\n"
        "    for item in versions:\n"
        "        try:\n"
        "            hash(item)\n"
        "        except TypeError:\n"
        "            return \"HER_SCHEMA_VERSION\"\n"
        "Status: STOPPED pending separate authorization.\n"
    )


def config_scopes(raw: str) -> list[str]:
    """Return Git config scope names. Values are discarded."""
    if type(raw) is not str:
        return []
    found = []
    for record in raw.split("\0"):
        if not record:
            continue
        scope = record.split("\n", 1)[0]
        if scope in _CONFIG_SCOPES:
            found.append(scope)
    return sorted(set(found))


def collect_readonly_observation() -> dict:
    """Read platform, interpreter, Git path, config scope names, and token privileges.

    The function does not elevate, install, download, or change Git config.
    """
    git_path = shutil.which("git")
    version = _git_text(["--version"]) if git_path else None
    exec_path = _git_text(["--exec-path"]) if git_path else None
    scopes = config_scopes(_git_text(["config", "--list", "--show-scope", "-z"]) or "") if git_path else []
    if git_path and scopes:
        config_closed = False
    else:
        config_closed = None
    return {
        "platform": _platform_name(),
        "python_version": ".".join(str(part) for part in sys.version_info[:3]),
        "python_executable": sys.executable or None,
        "python_sha256_authenticated": False,
        "python_distribution_sha256": None,
        "mingit_version": version,
        "mingit_executable": git_path,
        "mingit_sha256_authenticated": False,
        "mingit_distribution_sha256": None,
        "git_execution_path": exec_path or git_path,
        "git_source": "UNEXPECTED" if git_path else None,
        "git_config_closed": config_closed,
        "git_config_scopes": scopes,
        "privileges": _privilege_observation(),
    }


def evaluate_phase2a(document: object = None, observation: object = None, freshness: object = None) -> dict:
    """Return a structured non-PASS verdict.

    Unhashable schema_version values are refused here. Phase 1 is not called
    for those values, because the accepted supervisor raises TypeError.
    """
    observed = observation if type(observation) is dict else {}
    claimed = freshness if type(freshness) is dict else {}
    unhashable = type(document) is dict and _has_unhashable_version(document)
    checks = [
        _schema_check(document, unhashable),
        _platform_check(observed),
        *_python_checks(observed),
        *_mingit_checks(observed),
        _privilege_check(observed),
        _git_path_check(observed),
        _git_config_check(observed),
        _freshness_check(document, claimed),
        _claim_check(observed),
    ]
    if [item["check_id"] for item in checks] != list(CHECK_IDS):
        raise RuntimeError("phase 2A check inventory drifted")
    phase1, contribution = _delegate(document, unhashable)
    pool = list(checks)
    if contribution is not None:
        pool.append(contribution)
    status, reason = _rank(pool)
    if phase1 is None:
        phase1_status, phase1_reason = "NOT_DELEGATED", "NOT_DELEGATED"
    else:
        phase1_status = contribution["status"]
        phase1_reason = contribution["reason"]
    result = {
        "schema_version": "inr.her.phase2a.result.v0",
        "overall_status": status,
        "overall_reason": reason,
        "checks": checks,
        "pins": {
            "python_pin_status": PYTHON_PIN_STATUS,
            "git_pin_status": GIT_PIN_STATUS,
            "python_sha256": None,
            "git_sha256": None,
        },
        "nonclaims": list(NONCLAIMS),
        "n1_source_edited": False,
        "n1_phase1_edit": N1_PHASE1_EDIT,
        "phase1_overall_status": phase1_status,
        "phase1_overall_reason": phase1_reason,
        "freshness_procedure": FRESHNESS_PROCEDURE_ID,
        "pin_procedure": PIN_PROCEDURE_ID,
    }
    errors = schema_check(result, RESULT_SCHEMA)
    if errors:
        raise RuntimeError("phase 2A result failed its schema: " + "; ".join(errors))
    return result


def _delegate(document: object, unhashable: bool) -> tuple[dict | None, dict | None]:
    if document is None or unhashable:
        return None, None
    result = evaluate_event(document)
    status = result.get("overall_status")
    reason = result.get("overall_reason")
    if status == "PASS" or status not in {"FAIL", "BLOCKED", "UNCONFIRMED"} or type(reason) is not str or not reason:
        return result, {"status": "BLOCKED", "reason": "HER_PHASE2A_PASS_FORBIDDEN"}
    return result, {"status": status, "reason": reason}


def _schema_check(document: object, unhashable: bool) -> dict:
    if document is None:
        return _check("schema_version", "BLOCKED", "HER_EVENT_ABSENT")
    if type(document) is not dict:
        return _check("schema_version", "BLOCKED", "HER_SCHEMA_REJECTED")
    if unhashable:
        return _check("schema_version", "BLOCKED", "HER_SCHEMA_VERSION")
    return _check("schema_version", "UNCONFIRMED", "HER_SCHEMA_VERSION_HASHABLE")


def _platform_check(observation: dict) -> dict:
    if observation.get("platform") == "WINDOWS_X64":
        return _check("platform", "UNCONFIRMED", "HER_PLATFORM_OBSERVED")
    return _check("platform", "BLOCKED", "HER_PLATFORM_UNSUPPORTED")


def _python_checks(observation: dict) -> list[dict]:
    version = observation.get("python_version")
    executable = observation.get("python_executable")
    if type(version) is not str or not version or type(executable) is not str or not executable:
        identity = _check("cpython_identity", "BLOCKED", "HER_RUNTIME_ABSENT")
    elif version != REQUIRED_PYTHON:
        identity = _check("cpython_identity", "BLOCKED", "HER_PYTHON_IDENTITY_MISMATCH")
    else:
        identity = _check("cpython_identity", "UNCONFIRMED", "HER_PYTHON_IDENTITY_OBSERVED")
    if observation.get("python_sha256_authenticated") is True:
        pin = _check("cpython_pin", "FAIL", "HER_CONTRADICTION")
    else:
        pin = _check("cpython_pin", "BLOCKED", "HER_PYTHON_PIN_PENDING")
    return [identity, pin]


def _mingit_checks(observation: dict) -> list[dict]:
    version = observation.get("mingit_version")
    executable = observation.get("mingit_executable")
    if type(version) is not str or not version or type(executable) is not str or not executable:
        identity = _check("mingit_identity", "BLOCKED", "HER_GIT_RUNTIME_ABSENT")
    else:
        identity = _check("mingit_identity", "UNCONFIRMED", "HER_GIT_IDENTITY_OBSERVED")
    if observation.get("mingit_sha256_authenticated") is True:
        pin = _check("mingit_pin", "FAIL", "HER_CONTRADICTION")
    else:
        pin = _check("mingit_pin", "BLOCKED", "HER_GIT_PIN_UNRATIFIED")
    return [identity, pin]


def _privilege_check(observation: dict) -> dict:
    privileges = observation.get("privileges")
    if privileges == "UNOBSERVED":
        return _check("privileges", "UNCONFIRMED", "HER_PRIVILEGE_OBSERVATION_UNAVAILABLE")
    if privileges in {"PRESENT_UNEXERCISED", "ENABLED"}:
        return _check("privileges", "BLOCKED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED")
    return _check("privileges", "BLOCKED", "HER_TOKEN_PRIVILEGE_UNAVAILABLE")


def _git_path_check(observation: dict) -> dict:
    path = observation.get("git_execution_path")
    source = observation.get("git_source")
    if type(path) is not str or not path:
        return _check("git_execution_path", "BLOCKED", "HER_GIT_RUNTIME_ABSENT")
    if source == "MINGIT_PINNED":
        return _check("git_execution_path", "BLOCKED", "HER_GIT_PIN_UNRATIFIED")
    return _check("git_execution_path", "BLOCKED", "HER_GIT_SOURCE_NOT_SNAPSHOT")


def _git_config_check(observation: dict) -> dict:
    closed = observation.get("git_config_closed")
    if closed is False:
        return _check("git_config", "BLOCKED", "HER_GIT_CONFIG_UNCLOSED")
    return _check("git_config", "BLOCKED", "HER_GIT_CONFIG_UNVERIFIED")


def _freshness_check(document: object, freshness: dict) -> dict:
    if freshness.get("binding_authenticated") is True or freshness.get("claimed_fresh") is True:
        return _check("event_freshness", "FAIL", "HER_CONTRADICTION")
    if freshness.get("replay") is True:
        return _check("event_freshness", "FAIL", "HER_EVENT_REPLAY_UNAUTHENTICATED")
    if freshness.get("relabel") == "UNIFORM":
        return _check("event_freshness", "FAIL", "HER_EVENT_RELABEL_NOT_FRESH")
    if type(document) is dict and _ids_conflict(document):
        return _check("event_freshness", "FAIL", "HER_EVENT_RELABEL_NOT_FRESH")
    bound_head = freshness.get("authenticated_head")
    if type(document) is dict and type(bound_head) is str:
        if document.get("source_head") != bound_head:
            return _check("event_freshness", "FAIL", "HER_SUBSTITUTED_HEAD_NOT_FRESH")
        return _check("event_freshness", "BLOCKED", "HER_FRESHNESS_UNPROVEN")
    if document is None:
        return _check("event_freshness", "BLOCKED", "HER_EVENT_ABSENT")
    return _check("event_freshness", "BLOCKED", "HER_FRESHNESS_UNPROVEN")


def _claim_check(observation: dict) -> dict:
    if observation.get("claimed_status") in _PASS_CLAIMS:
        return _check("claim_boundary", "FAIL", "HER_CONTRADICTION")
    return _check("claim_boundary", "UNCONFIRMED", "HER_NO_PASS_CLAIM")


def _rank(checks: list[dict]) -> tuple[str, str]:
    grouped = {"FAIL": [], "BLOCKED": [], "UNCONFIRMED": []}
    for item in checks:
        status = item["status"]
        if status not in grouped:
            return "BLOCKED", "HER_PHASE2A_PASS_FORBIDDEN"
        grouped[status].append(item["reason"])
    for status in ("FAIL", "BLOCKED", "UNCONFIRMED"):
        if grouped[status]:
            reason = sorted(grouped[status], key=_reason_key)[0]
            return status, reason
    return "BLOCKED", "HER_PHASE2A_PASS_FORBIDDEN"


def _reason_key(reason: str) -> int:
    try:
        return PRIORITY.index(reason)
    except ValueError:
        return -1


def _check(check_id: str, status: str, reason: str) -> dict[str, str]:
    return {"check_id": check_id, "status": status, "reason": reason}


def _has_unhashable_version(document: dict) -> bool:
    return any(_unhashable(item) for item in _version_values(document))


def _unhashable(value: object) -> bool:
    try:
        hash(value)
    except TypeError:
        return True
    return False


def _version_values(document: dict) -> list:
    values = []
    if "schema_version" in document:
        values.append(document.get("schema_version"))
    supervisor = document.get("supervisor_result")
    if type(supervisor) is dict and "schema_version" in supervisor:
        values.append(supervisor.get("schema_version"))
    records = document.get("surface_records")
    if type(records) is list:
        for record in records:
            if type(record) is dict and "schema_version" in record:
                values.append(record.get("schema_version"))
    return values


def _ids_conflict(document: dict) -> bool:
    event_id = document.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        return False
    supervisor = document.get("supervisor_result")
    if type(supervisor) is dict and "event_id" in supervisor and supervisor.get("event_id") != event_id:
        return True
    records = document.get("surface_records")
    if type(records) is not list:
        return False
    for record in records:
        if type(record) is dict and "event_id" in record and record.get("event_id") != event_id:
            return True
    return False


def _platform_name() -> str:
    machine = platform.machine().lower()
    if os.name == "nt" and machine in {"amd64", "x86_64"}:
        return "WINDOWS_X64"
    if os.name == "nt":
        return "WINDOWS_OTHER"
    return "NON_WINDOWS"


def _git_text(args: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def _privilege_observation() -> str:
    """Read the current token. Do not enable or assign privileges."""
    if os.name != "nt":
        return "UNOBSERVED"
    token = wintypes.HANDLE()
    opened = False
    try:
        advapi = ctypes.WinDLL("advapi32", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        advapi.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
        advapi.OpenProcessToken.restype = wintypes.BOOL
        advapi.GetTokenInformation.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
        ]
        advapi.GetTokenInformation.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        if not advapi.OpenProcessToken(kernel.GetCurrentProcess(), 0x0008, ctypes.byref(token)):
            return "UNOBSERVED"
        opened = True
        needed = wintypes.DWORD(0)
        advapi.GetTokenInformation(token, 3, None, 0, ctypes.byref(needed))
        if needed.value <= 0:
            return "UNOBSERVED"
        buffer = ctypes.create_string_buffer(needed.value)
        if not advapi.GetTokenInformation(token, 3, buffer, needed.value, ctypes.byref(needed)):
            return "UNOBSERVED"

        class LUID(ctypes.Structure):
            _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

        class LUID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

        if ctypes.sizeof(LUID_AND_ATTRIBUTES) != 12:
            return "UNOBSERVED"
        count = int.from_bytes(buffer.raw[:4], "little")
        enabled = set()
        advapi.LookupPrivilegeNameW.argtypes = [
            wintypes.LPCWSTR, ctypes.POINTER(LUID), wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
        ]
        advapi.LookupPrivilegeNameW.restype = wintypes.BOOL
        for index in range(count):
            start = 4 + (index * 12)
            if start + 12 > len(buffer):
                return "UNOBSERVED"
            entry = LUID_AND_ATTRIBUTES.from_buffer(buffer, start)
            if not entry.Attributes & 0x00000002:
                continue
            name = ctypes.create_unicode_buffer(96)
            size = wintypes.DWORD(96)
            if advapi.LookupPrivilegeNameW(None, ctypes.byref(entry.Luid), name, ctypes.byref(size)):
                enabled.add(name.value)
        if set(REQUIRED_PRIVILEGES) <= enabled:
            return "PRESENT_UNEXERCISED"
        return "ABSENT"
    except (OSError, AttributeError, ValueError, BufferError, ctypes.ArgumentError):
        return "UNOBSERVED"
    finally:
        if opened:
            ctypes.WinDLL("kernel32", use_last_error=True).CloseHandle(token)
