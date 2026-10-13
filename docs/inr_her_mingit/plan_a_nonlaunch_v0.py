"""Plan A public entry. NONLAUNCH only.

Every path stops before process creation and before the first inheritable
handle duplication. Refusal reasons are fixed codes. This module does not
call a native API, create a Job, duplicate a handle, or launch MinGit.

N4, N5, ownership, the operational pin, launch identity, file identity,
reparse inspection, and compatibility stay open. A PROPOSED environment
block or command string is not execution authorization. PATH may match the
IMAGE parent by ASCII code units and still leave those gates open. C-7
ordering and C-9 argv checks stay inside the existing proposal functions.
"""

from __future__ import annotations

from typing import NamedTuple

from docs.inr_her_mingit.ascii_env_argv_v0 import (
    MINGIT_CRT_COMPATIBLE,
    WINDOWS_ENVIRONMENT_SORT_CLOSED,
    Proposal,
    propose_ascii_command_line,
    propose_utf16le_environment_block,
)

PLAN_A = "NONLAUNCH"
PLAN_B = "UNSELECTED"
PLAN_C = "UNSELECTED"
N4 = "OPEN"
N5 = "OPEN"
OWNERSHIP_EXCLUSIVE = "OPEN"
OPERATIONAL_MINGIT_PIN = "UNRATIFIED"
LAUNCH_IDENTITY = "UNBOUND_AT_LAUNCH"
FILE_IDENTITY_UNPROVED = "UNPROVED"
REPARSE_UNINSPECTED = "UNINSPECTED"
EXECUTION_BINDING_REAL = "UNEXECUTED"
REAL_WINDOWS_EXECUTION = "NOT_AUTHORIZED"
FULL_INR_READY = False
EXECUTION_AUTHORIZED = False
CREATE_PROCESS_W = "NOT_REACHED"
INHERITABLE_HANDLE_DUPLICATE = "NOT_REACHED"

_SCHEMA = "her.limited_git.request.v0"
_REQUEST_KEYS = frozenset({"schema_version", "operation_id"})
_PREPARATION_KEYS = frozenset({"environment_snapshot", "image"})
_AUTHORITY_KEYS = frozenset({
    "claimed_status",
    "execution_authorized",
    "execution_binding_real",
    "freshness_pass",
    "full_inr_ready",
    "isolation_pass",
    "launch_identity",
    "mingit_crt_compatible",
    "n4",
    "n5",
    "operational_mingit_pin",
    "operational_pin_authorized",
    "ownership_exclusive",
    "pass",
    "plan_b",
    "plan_c",
    "windows_environment_sort_closed",
})
_OPERATION_SUFFIX = {
    "VERSION": ("--version",),
    "EXEC_PATH": ("--exec-path",),
    "CONFIG_SCOPES": ("config", "--list", "--show-scope", "-z"),
}
_REASONS = frozenset({
    "AUTHORITY_CLAIM_REJECTED",
    "INPUT_REJECTED",
    "POLICY_UNAPPROVED",
    "UNCONFIRMED",
    "NUL_REJECTED",
    "ISOLATED_SURROGATE",
    "WHITESPACE",
    "CONTROL_CHARACTER",
    "QUOTE",
    "WILDCARD",
    "NON_ASCII",
    "INVALID_KEY",
    "DUPLICATE_KEY",
    "FORBIDDEN_KEY",
    "UNAUTHORIZED_KEY",
    "MISSING_REQUIRED_KEY",
    "INVALID_VALUE",
    "INCONSISTENT_VALUE",
    "RAW_COMMAND_LINE",
    "UNSUPPORTED_ARGV",
})


class NonlaunchDecision(NamedTuple):
    status: str
    reason: str
    transitions: tuple[str, ...]
    create_process_w: str
    inheritable_handle_duplicate: str
    execution_authorized: bool
    launch_identity: str
    n4: str
    n5: str
    ownership_exclusive: str
    operational_mingit_pin: str
    mingit_crt_compatible: bool
    windows_environment_sort_closed: bool
    environment_proposal: Proposal | None
    command_proposal: Proposal | None
    plan_a: str
    plan_b: str
    plan_c: str
    full_inr_ready: bool
    file_identity: str
    reparse: str


def enter_plan_a_nonlaunch(
    request: object,
    preparation: object = None,
) -> NonlaunchDecision:
    """Refuse Plan A before creation. No path continues past that refusal."""
    transitions = ["RECEIVED"]
    if _authority(request) or _authority(preparation):
        return _decision("REFUSED", "AUTHORITY_CLAIM_REJECTED", transitions, None, None)
    if type(request) is not dict or not _exact_keyset(request, _REQUEST_KEYS):
        return _decision("REFUSED", "INPUT_REJECTED", transitions, None, None)
    schema = request.get("schema_version")
    operation = request.get("operation_id")
    if not _exact_schema(schema) or not _known_operation(operation):
        return _decision("REFUSED", "INPUT_REJECTED", transitions, None, None)
    transitions.append("REQUEST_CLASSIFIED")
    if preparation is None:
        return _decision("REFUSED", "POLICY_UNAPPROVED", transitions, None, None)
    if type(preparation) is not dict or not _exact_keyset(preparation, _PREPARATION_KEYS):
        return _decision("REFUSED", "INPUT_REJECTED", transitions, None, None)
    image = preparation.get("image")
    if type(image) is not str:
        return _decision("REFUSED", "INPUT_REJECTED", transitions, None, None)
    argv = [image, *_OPERATION_SUFFIX[operation]]
    environment = propose_utf16le_environment_block(preparation.get("environment_snapshot"))
    command = propose_ascii_command_line(argv)
    transitions.append("PROPOSALS_CONSULTED")
    if environment.status != "PROPOSED":
        return _decision("REFUSED", environment.reason, transitions, environment, command)
    if command.status != "PROPOSED":
        return _decision("REFUSED", command.reason, transitions, environment, command)
    relation = _path_parent_relation(preparation.get("environment_snapshot"), image)
    if relation != "MATCH":
        return _decision("REFUSED", relation, transitions, environment, command)
    return _decision("BLOCKED", "UNCONFIRMED", transitions, environment, command)


def _exact_keyset(mapping: dict, expected: frozenset[str]) -> bool:
    try:
        found: list[str] = []
        for key in mapping:
            if type(key) is not str:
                return False
            found.append(key)
        return set(found) == expected
    except Exception:
        return False


def _exact_schema(value: object) -> bool:
    try:
        return type(value) is str and value == _SCHEMA
    except Exception:
        return False


def _known_operation(value: object) -> bool:
    try:
        return type(value) is str and value in _OPERATION_SUFFIX
    except Exception:
        return False


def _image_parent(image: str) -> str | None:
    last = -1
    for index, char in enumerate(image):
        if char in "\\/":
            last = index
    if last < 0:
        return None
    return image[:last]


def _path_parent_relation(snapshot: object, image: str) -> str:
    if type(snapshot) is not dict or type(image) is not str:
        return "INPUT_REJECTED"
    path = snapshot.get("PATH")
    if type(path) is not str:
        return "INPUT_REJECTED"
    parent = _image_parent(image)
    if parent is None:
        return "INPUT_REJECTED"
    if len(path) != len(parent):
        return "INCONSISTENT_VALUE"
    for left, right in zip(path, parent):
        if left != right:
            return "INCONSISTENT_VALUE"
    return "MATCH"


def _authority(value: object) -> bool:
    if type(value) is not dict:
        return False
    for key in value:
        if type(key) is str and key in _AUTHORITY_KEYS:
            return True
    return False


def _decision(
    status: str,
    reason: str,
    transitions: list[str],
    environment: Proposal | None,
    command: Proposal | None,
) -> NonlaunchDecision:
    if reason not in _REASONS:
        reason = "INPUT_REJECTED"
    transitions.append("REFUSED_BEFORE_CREATE")
    return NonlaunchDecision(
        status,
        reason,
        tuple(transitions),
        CREATE_PROCESS_W,
        INHERITABLE_HANDLE_DUPLICATE,
        EXECUTION_AUTHORIZED,
        LAUNCH_IDENTITY,
        N4,
        N5,
        OWNERSHIP_EXCLUSIVE,
        OPERATIONAL_MINGIT_PIN,
        MINGIT_CRT_COMPATIBLE,
        WINDOWS_ENVIRONMENT_SORT_CLOSED,
        environment,
        command,
        PLAN_A,
        PLAN_B,
        PLAN_C,
        FULL_INR_READY,
        FILE_IDENTITY_UNPROVED,
        REPARSE_UNINSPECTED,
    )
