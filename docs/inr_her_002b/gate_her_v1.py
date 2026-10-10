"""Phase 2B gate for privileges, claimed_status, and check inventory.

Supported Phase 2A inputs are delegated from an owned mapping snapshot.
Invalid privilege and claimed_status inputs are refused here, before that
delegation. A returned Phase 2A object is copied once into owned plain data.
Later checks read that copy. Check-list uniqueness is a runtime invariant.
Schema validation does not establish it. This module does not edit accepted
files, create a token or Job, or emit PASS.
"""

from __future__ import annotations

import json
from pathlib import Path

from docs.inr_001.schema_check import check as schema_check
from docs.inr_her_001.validate_her_v1 import assert_schema_contract
from docs.inr_her_002a.preflight_her_v1 import (
    CHECK_IDS as PHASE2A_CHECK_IDS,
    PRIORITY as PHASE2A_PRIORITY,
    RESULT_SCHEMA as PHASE2A_RESULT_SCHEMA,
    _PASS_CLAIMS,
    evaluate_phase2a,
)

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "inr_her_phase2b_result_v0.schema.json"
RESULT_SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
assert_schema_contract(RESULT_SCHEMA)

PHASE2B_CHECK_IDS = (
    "n3_privileges",
    "n3_claimed_status",
    "n4_check_inventory",
    "phase2a_delegation",
    "isolation_boundary",
)
SUPPORTED_PRIVILEGES = frozenset({
    "ABSENT",
    "UNOBSERVED",
    "PRESENT_UNEXERCISED",
    "ENABLED",
})
_CHECK_KEYS = frozenset({"check_id", "status", "reason"})
_PHASE2A_STATUSES = frozenset({"FAIL", "BLOCKED", "UNCONFIRMED"})
_EMITTED_PAIRS = {
    "schema_version": frozenset({
        ("BLOCKED", "HER_EVENT_ABSENT"),
        ("BLOCKED", "HER_SCHEMA_REJECTED"),
        ("BLOCKED", "HER_SCHEMA_VERSION"),
        ("UNCONFIRMED", "HER_SCHEMA_VERSION_HASHABLE"),
    }),
    "platform": frozenset({
        ("UNCONFIRMED", "HER_PLATFORM_OBSERVED"),
        ("BLOCKED", "HER_PLATFORM_UNSUPPORTED"),
    }),
    "cpython_identity": frozenset({
        ("BLOCKED", "HER_RUNTIME_ABSENT"),
        ("BLOCKED", "HER_PYTHON_IDENTITY_MISMATCH"),
        ("UNCONFIRMED", "HER_PYTHON_IDENTITY_OBSERVED"),
    }),
    "cpython_pin": frozenset({
        ("FAIL", "HER_CONTRADICTION"),
        ("BLOCKED", "HER_PYTHON_PIN_PENDING"),
    }),
    "mingit_identity": frozenset({
        ("BLOCKED", "HER_GIT_RUNTIME_ABSENT"),
        ("UNCONFIRMED", "HER_GIT_IDENTITY_OBSERVED"),
    }),
    "mingit_pin": frozenset({
        ("FAIL", "HER_CONTRADICTION"),
        ("BLOCKED", "HER_GIT_PIN_UNRATIFIED"),
    }),
    "privileges": frozenset({
        ("UNCONFIRMED", "HER_PRIVILEGE_OBSERVATION_UNAVAILABLE"),
        ("BLOCKED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"),
        ("BLOCKED", "HER_TOKEN_PRIVILEGE_UNAVAILABLE"),
    }),
    "git_execution_path": frozenset({
        ("BLOCKED", "HER_GIT_RUNTIME_ABSENT"),
        ("BLOCKED", "HER_GIT_PIN_UNRATIFIED"),
        ("BLOCKED", "HER_GIT_SOURCE_NOT_SNAPSHOT"),
    }),
    "git_config": frozenset({
        ("BLOCKED", "HER_GIT_CONFIG_UNCLOSED"),
        ("BLOCKED", "HER_GIT_CONFIG_UNVERIFIED"),
    }),
    "event_freshness": frozenset({
        ("FAIL", "HER_CONTRADICTION"),
        ("FAIL", "HER_EVENT_REPLAY_UNAUTHENTICATED"),
        ("FAIL", "HER_EVENT_RELABEL_NOT_FRESH"),
        ("FAIL", "HER_SUBSTITUTED_HEAD_NOT_FRESH"),
        ("BLOCKED", "HER_FRESHNESS_UNPROVEN"),
        ("BLOCKED", "HER_EVENT_ABSENT"),
    }),
    "claim_boundary": frozenset({
        ("FAIL", "HER_CONTRADICTION"),
        ("UNCONFIRMED", "HER_NO_PASS_CLAIM"),
    }),
}
_PROBLEM_ORDER = ("not_list", "malformed", "repeated", "missing", "unexpected", "status", "reason")
_MISSING = object()
_PHASE2A_STRING_FIELDS = (
    "schema_version",
    "overall_status",
    "overall_reason",
    "n1_phase1_edit",
    "phase1_overall_status",
    "phase1_overall_reason",
    "freshness_procedure",
    "pin_procedure",
)
_PIN_STRING_FIELDS = ("python_pin_status", "git_pin_status")
_PIN_NULL_FIELDS = ("python_sha256", "git_sha256")
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
    "n1_phase1_typeerror_fixed",
    "n2_freshness_binding",
    "schema_only_check_uniqueness",
    "isolation_evidence",
    "accepted_history_reopened",
)


def phase2a_inventory_errors(checks: object) -> tuple[str, ...]:
    """Return runtime inventory problems. An empty tuple means the exact inventory."""
    return _inventory_errors(checks, PHASE2A_CHECK_IDS)


def phase2b_inventory_errors(checks: object) -> tuple[str, ...]:
    """Return runtime problems for the Phase 2B check list."""
    return _inventory_errors(checks, PHASE2B_CHECK_IDS)


def evaluate_phase2b(document: object = None, observation: object = None, freshness: object = None) -> dict:
    """Return a structured non-PASS verdict.

    Unhashable, hostile, or unsupported privileges and claimed_status values
    never reach Phase 2A. The observation mapping is snapshotted before
    delegation. A Phase 2A check list that is missing, repeated, unexpected,
    or malformed is discarded even when the Phase 2A schema accepts it.
    Inventory, schema checks, and output use one owned plain snapshot of the
    Phase 2A result. BaseException is not caught.
    """
    privileges_state, claimed_state, rejection, delegated_observation = _classify_n3(observation)
    if rejection:
        return _seal(_result(
            overall_status="BLOCKED",
            overall_reason=rejection,
            delegated=False,
            privileges_state=privileges_state,
            claimed_state=claimed_state,
            n4_state="NOT_RUN",
            phase2a_status="NOT_DELEGATED",
            phase2a_reason="NOT_DELEGATED",
            phase2a_checks=[],
            delegation_status="BLOCKED",
            delegation_reason="HER_PHASE2A_NOT_DELEGATED",
        ))
    try:
        produced = evaluate_phase2a(document, delegated_observation, freshness)
    except Exception:
        return _seal(_result(
            overall_status="BLOCKED",
            overall_reason="HER_PHASE2A_UNSTRUCTURED_ERROR",
            delegated=False,
            privileges_state="ACCEPTED",
            claimed_state="ACCEPTED",
            n4_state="NOT_RUN",
            phase2a_status="NOT_DELEGATED",
            phase2a_reason="NOT_DELEGATED",
            phase2a_checks=[],
            delegation_status="BLOCKED",
            delegation_reason="HER_PHASE2A_UNSTRUCTURED_ERROR",
        ))
    decision = _assess_phase2a(produced)
    return _seal(_result(
        overall_status=decision["overall_status"],
        overall_reason=decision["overall_reason"],
        delegated=True,
        privileges_state="ACCEPTED",
        claimed_state="ACCEPTED",
        n4_state=decision["n4"],
        phase2a_status=decision["phase2a_status"],
        phase2a_reason=decision["phase2a_reason"],
        phase2a_checks=decision["checks"],
        delegation_status="UNCONFIRMED",
        delegation_reason="HER_PHASE2A_DELEGATED",
    ))


def _classify_n3(observation: object) -> tuple[str, str, str, dict | None]:
    """Classify privileges from an owned mapping. The fourth value is delegated."""
    if observation is None:
        return "ACCEPTED", "ACCEPTED", "", None
    if type(observation) is not dict:
        return "REJECTED", "REJECTED", "HER_OBSERVATION_INPUT_REJECTED", None
    try:
        copied = _snapshot_observation(observation)
    except Exception:
        return "REJECTED", "REJECTED", "HER_OBSERVATION_INPUT_REJECTED", None
    if copied is None:
        return "REJECTED", "REJECTED", "HER_OBSERVATION_INPUT_REJECTED", None
    try:
        privileges_state, claimed_state, rejection = _classify_observation_dict(copied)
    except Exception:
        return "REJECTED", "REJECTED", "HER_OBSERVATION_INPUT_REJECTED", None
    if rejection:
        return privileges_state, claimed_state, rejection, None
    return privileges_state, claimed_state, "", copied


def _snapshot_observation(observation: dict) -> dict | None:
    """Copy an exact dict by items. Caller values stay as they are.

    A non-string key is rejected here, before any key comparison. The new
    mapping is what Phase 2A receives, so a later write to the caller's dict
    is not visible. Value objects are not deep-copied.
    """
    copied = {}
    for key, value in observation.items():
        if type(key) is not str:
            return None
        copied[key] = value
    return copied


def _classify_observation_dict(observation: dict) -> tuple[str, str, str]:
    """Classify one exact dict. Callers catch Exception from its key probes."""
    for key in observation:
        if type(key) is not str:
            return "REJECTED", "REJECTED", "HER_OBSERVATION_INPUT_REJECTED"
    privileges_state = "ACCEPTED"
    claimed_state = "ACCEPTED"
    if "privileges" in observation:
        value = observation["privileges"]
        if type(value) is not str or value not in SUPPORTED_PRIVILEGES:
            privileges_state = "REJECTED"
    if "claimed_status" in observation:
        value = observation["claimed_status"]
        if type(value) is not str:
            claimed_state = "REJECTED"
    if privileges_state == "REJECTED":
        return privileges_state, claimed_state, "HER_PRIVILEGE_INPUT_REJECTED"
    if claimed_state == "REJECTED":
        return privileges_state, claimed_state, "HER_CLAIMED_STATUS_INPUT_REJECTED"
    return "ACCEPTED", "ACCEPTED", ""


def _assess_phase2a(produced: object) -> dict:
    if type(produced) is not dict:
        return _rejected("HER_PHASE2A_RESULT_REJECTED", "REJECTED", "BLOCKED", "HER_PHASE2A_RESULT_REJECTED")
    try:
        snap = _snapshot_phase2a(produced)
    except Exception:
        return _rejected("HER_PHASE2A_RESULT_REJECTED", "REJECTED", "BLOCKED", "HER_PHASE2A_RESULT_REJECTED")
    if snap["unconfirmed"]:
        return _rejected("HER_PHASE2A_RESULT_REJECTED", "REJECTED", "BLOCKED", "HER_PHASE2A_RESULT_REJECTED")
    if snap["checks_kind"] != "plain" or phase2a_inventory_errors(snap["checks"]):
        return _rejected(
            "HER_CHECK_INVENTORY_REJECTED",
            "REJECTED",
            "BLOCKED",
            "HER_CHECK_INVENTORY_REJECTED",
        )
    if snap["status"] not in _PHASE2A_STATUSES:
        return _rejected("HER_PHASE2A_PASS_FORBIDDEN", "ACCEPTED", "BLOCKED", "HER_PHASE2A_PASS_FORBIDDEN")
    plain = snap["plain"]
    reason = "" if plain is None else plain.get("overall_reason")
    if snap["unsupported"] or plain is None or type(reason) is not str or not reason:
        return _rejected(
            "HER_PHASE2A_RESULT_REJECTED",
            "ACCEPTED",
            "BLOCKED",
            "HER_PHASE2A_RESULT_REJECTED",
        )
    schema_errors = _phase2a_schema_errors(plain)
    if schema_errors is None or schema_errors:
        return _rejected(
            "HER_PHASE2A_RESULT_REJECTED",
            "ACCEPTED",
            "BLOCKED",
            "HER_PHASE2A_RESULT_REJECTED",
        )
    if _phase2a_contradiction(plain):
        return _rejected(
            "HER_PHASE2A_RESULT_CONTRADICTION",
            "ACCEPTED",
            "BLOCKED",
            "HER_PHASE2A_RESULT_CONTRADICTION",
        )
    return {
        "overall_status": plain["overall_status"],
        "overall_reason": plain["overall_reason"],
        "n4": "ACCEPTED",
        "phase2a_status": plain["overall_status"],
        "phase2a_reason": plain["overall_reason"],
        "checks": plain["checks"],
    }


def _snapshot_phase2a(produced: dict) -> dict:
    """Read the untrusted result once into owned plain values.

    This is the only read of that object. Keys are accepted only when
    type(key) is str. The walk does not call a caller-defined equality or
    hash method, and it does not follow a value whose type is not the schema
    leaf. Dict and list copies are new objects. Strings, booleans, and None
    are immutable and may be reused.
    """
    fields: dict[str, object] = {}
    unsupported_top = False
    for key, value in produced.items():
        if type(key) is not str:
            unsupported_top = True
            continue
        fields[key] = value
    status = fields.get("overall_status")
    checks_kind, checks = _snapshot_checks(fields.get("checks", _MISSING))
    plain, unsupported_nested = _snapshot_phase2a_body(fields, checks)
    unconfirmed = unsupported_top and checks_kind == "absent"
    return {
        "unconfirmed": unconfirmed,
        "checks_kind": checks_kind,
        "checks": checks,
        "status": status if type(status) is str else "",
        "unsupported": unsupported_top or unsupported_nested or plain is None,
        "plain": None if unsupported_top or unsupported_nested else plain,
    }


def _snapshot_checks(value: object) -> tuple[str, list]:
    if value is _MISSING:
        return "absent", []
    if type(value) is not list:
        return "not_list", []
    plain = []
    for item in list(value):
        if type(item) is not dict:
            plain.append({"check_id": None, "status": None, "reason": None})
            continue
        copied: dict[str, str | None] = {}
        for key, field in item.items():
            if type(key) is not str:
                return "unsupported", []
            copied[key] = field if type(field) is str else None
        plain.append(copied)
    return "plain", plain


def _snapshot_phase2a_body(fields: dict[str, object], checks: list) -> tuple[dict | None, bool]:
    plain: dict[str, object] = {"checks": checks}
    unsupported = False
    for key, value in fields.items():
        if key == "checks":
            continue
        if key in _PHASE2A_STRING_FIELDS:
            if type(value) is str:
                plain[key] = value
            continue
        if key == "n1_source_edited":
            if type(value) is bool:
                plain[key] = value
            continue
        if key == "pins":
            pins, bad = _snapshot_pins(value)
            if bad:
                unsupported = True
            elif pins is not None:
                plain["pins"] = pins
            continue
        if key == "nonclaims":
            copied, bad = _snapshot_string_list(value)
            if bad:
                unsupported = True
            elif copied is not None:
                plain["nonclaims"] = copied
            continue
        if type(value) is str:
            plain[key] = value
        else:
            unsupported = True
    if unsupported:
        return None, True
    return plain, False


def _snapshot_pins(value: object) -> tuple[dict | None, bool]:
    if type(value) is not dict:
        return None, False
    plain: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            return None, True
        if key in _PIN_NULL_FIELDS and item is None:
            plain[key] = None
        elif key in _PIN_STRING_FIELDS and type(item) is str:
            plain[key] = item
        elif type(item) is str:
            plain[key] = item
        else:
            return None, True
    return plain, False


def _snapshot_string_list(value: object) -> tuple[list[str] | None, bool]:
    if type(value) is not list:
        return None, False
    copied = []
    for item in list(value):
        if type(item) is not str or not item:
            return None, True
        copied.append(item)
    return copied, False


def _phase2a_schema_errors(produced: dict) -> list[str] | None:
    """Return schema errors. None means schema_check raised Exception on the snapshot."""
    try:
        return schema_check(produced, PHASE2A_RESULT_SCHEMA)
    except Exception:
        return None


def _phase2a_contradiction(produced: dict) -> bool:
    """True when a schema-valid result cannot be a Phase 2A ranking."""
    for item in produced["checks"]:
        pair = (item["status"], item["reason"])
        if pair not in _EMITTED_PAIRS.get(item["check_id"], ()):
            return True
        if item["reason"] in _PASS_CLAIMS:
            return True
    phase1_status = produced["phase1_overall_status"]
    phase1_reason = produced["phase1_overall_reason"]
    if phase1_reason in _PASS_CLAIMS or produced["overall_reason"] in _PASS_CLAIMS:
        return True
    if phase1_status == "NOT_DELEGATED":
        contribution = None
        if phase1_reason != "NOT_DELEGATED":
            return True
    else:
        contribution = {"status": phase1_status, "reason": phase1_reason}
    expected_status, expected_reason = _rank_phase2a(produced["checks"], contribution)
    return produced["overall_status"] != expected_status or produced["overall_reason"] != expected_reason


def _rank_phase2a(checks: list, contribution: dict | None) -> tuple[str, str]:
    """Same order and priority rule as accepted Phase 2A `_rank`."""
    pool = [{"status": item["status"], "reason": item["reason"]} for item in checks]
    if contribution is not None:
        pool.append(contribution)
    grouped: dict[str, list[tuple[str, int]]] = {"FAIL": [], "BLOCKED": [], "UNCONFIRMED": []}
    for index, item in enumerate(pool):
        status = item["status"]
        if status not in grouped:
            return "BLOCKED", "HER_PHASE2A_PASS_FORBIDDEN"
        grouped[status].append((item["reason"], index))
    for status in ("FAIL", "BLOCKED", "UNCONFIRMED"):
        if grouped[status]:
            reason, _index = sorted(grouped[status], key=_reason_order)[0]
            return status, reason
    return "BLOCKED", "HER_PHASE2A_PASS_FORBIDDEN"


def _reason_order(item: tuple[str, int]) -> tuple[int, int]:
    reason, index = item
    try:
        rank = PHASE2A_PRIORITY.index(reason)
    except ValueError:
        rank = -1
    return (rank, index)


def _rejected(overall_reason: str, n4: str, phase2a_status: str, phase2a_reason: str) -> dict:
    return {
        "overall_status": "BLOCKED",
        "overall_reason": overall_reason,
        "n4": n4,
        "phase2a_status": phase2a_status,
        "phase2a_reason": phase2a_reason,
        "checks": [],
    }


def _inventory_errors(checks: object, expected: tuple[str, ...]) -> tuple[str, ...]:
    if type(checks) is not list:
        return ("not_list",)
    problems: set[str] = set()
    identifiers: list[str] = []
    if len(checks) != len(expected):
        problems.add("missing")
        if len(checks) > len(expected):
            problems.add("unexpected")
    for index, item in enumerate(checks):
        if type(item) is not dict or set(item) != _CHECK_KEYS:
            problems.add("malformed")
            continue
        check_id = item["check_id"]
        status = item["status"]
        reason = item["reason"]
        if type(check_id) is not str:
            problems.add("malformed")
        else:
            identifiers.append(check_id)
            if index >= len(expected) or check_id != expected[index]:
                problems.add("unexpected")
        if type(status) is not str or status not in _PHASE2A_STATUSES:
            problems.add("malformed")
            problems.add("status")
        if type(reason) is not str or not reason:
            problems.add("malformed")
            problems.add("reason")
    if len(identifiers) != len(set(identifiers)):
        problems.add("repeated")
    if set(expected) - set(identifiers):
        problems.add("missing")
    if set(identifiers) - set(expected):
        problems.add("unexpected")
    return tuple(tag for tag in _PROBLEM_ORDER if tag in problems)


def _result(
    *,
    overall_status: str,
    overall_reason: str,
    delegated: bool,
    privileges_state: str,
    claimed_state: str,
    n4_state: str,
    phase2a_status: str,
    phase2a_reason: str,
    phase2a_checks: list,
    delegation_status: str,
    delegation_reason: str,
) -> dict:
    if overall_reason == "HER_OBSERVATION_INPUT_REJECTED":
        privilege_reason = "HER_OBSERVATION_INPUT_REJECTED"
        claimed_reason = "HER_OBSERVATION_INPUT_REJECTED"
    else:
        privilege_reason = "HER_PRIVILEGE_INPUT_REJECTED"
        claimed_reason = "HER_CLAIMED_STATUS_INPUT_REJECTED"
    if n4_state == "ACCEPTED":
        inventory_status, inventory_reason = "UNCONFIRMED", "HER_CHECK_INVENTORY_ACCEPTED"
    elif n4_state == "REJECTED":
        inventory_status, inventory_reason = "BLOCKED", "HER_CHECK_INVENTORY_REJECTED"
    else:
        inventory_status, inventory_reason = "BLOCKED", "HER_CHECK_INVENTORY_NOT_RUN"
    return {
        "schema_version": "inr.her.phase2b.result.v0",
        "overall_status": overall_status,
        "overall_reason": overall_reason,
        "checks": [
            _state_check("n3_privileges", privileges_state, privilege_reason, "HER_PRIVILEGE_INPUT_ACCEPTED"),
            _state_check("n3_claimed_status", claimed_state, claimed_reason, "HER_CLAIMED_STATUS_INPUT_ACCEPTED"),
            _check("n4_check_inventory", inventory_status, inventory_reason),
            _check("phase2a_delegation", delegation_status, delegation_reason),
            _check("isolation_boundary", "BLOCKED", "HER_ISOLATION_NOT_ESTABLISHED"),
        ],
        "phase2a_delegated": delegated,
        "phase2a_overall_status": phase2a_status,
        "phase2a_overall_reason": phase2a_reason,
        "phase2a_checks": phase2a_checks,
        "n3_privileges": privileges_state,
        "n3_claimed_status": claimed_state,
        "n4_inventory": n4_state,
        "inventory_authority": "RUNTIME",
        "schema_uniqueness": "NOT_ESTABLISHED",
        "isolation_evidence": "NOT_ESTABLISHED",
        "full_inr_ready": False,
        "human_final": False,
        "n1_phase1_edit": "STOPPED",
        "n2_binding": "UNEXECUTED",
        "nonclaims": list(NONCLAIMS),
    }


def _state_check(check_id: str, state: str, rejected_reason: str, accepted_reason: str) -> dict[str, str]:
    if state == "REJECTED":
        return _check(check_id, "BLOCKED", rejected_reason)
    return _check(check_id, "UNCONFIRMED", accepted_reason)


def _check(check_id: str, status: str, reason: str) -> dict[str, str]:
    return {"check_id": check_id, "status": status, "reason": reason}


def _seal(result: dict) -> dict:
    inventory = phase2b_inventory_errors(result["checks"])
    if inventory:
        raise RuntimeError("phase 2B check inventory drifted: " + ",".join(inventory))
    errors = schema_check(result, RESULT_SCHEMA)
    if errors:
        raise RuntimeError("phase 2B result failed its schema: " + "; ".join(errors))
    return result
