"""Phase 2B gate for privileges, claimed_status, and check inventory.

Supported Phase 2A inputs are delegated unchanged. Invalid privilege and
claimed_status inputs are refused here, before that delegation. Check-list
uniqueness is a runtime invariant. Schema validation does not establish it.
This module does not edit accepted files, create a token or Job, or emit PASS.
"""

from __future__ import annotations

import json
from pathlib import Path

from docs.inr_001.schema_check import check as schema_check
from docs.inr_her_001.validate_her_v1 import assert_schema_contract
from docs.inr_her_002a.preflight_her_v1 import (
    CHECK_IDS as PHASE2A_CHECK_IDS,
    RESULT_SCHEMA as PHASE2A_RESULT_SCHEMA,
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
_PROBLEM_ORDER = ("not_list", "malformed", "repeated", "missing", "unexpected", "status", "reason")
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

    Unhashable or unsupported privileges and claimed_status values never reach
    Phase 2A. A Phase 2A check list that is missing, repeated, unexpected, or
    malformed is discarded even when the Phase 2A schema accepts it.
    """
    privileges_state, claimed_state, rejection = _classify_n3(observation)
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
        produced = evaluate_phase2a(document, observation, freshness)
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


def _classify_n3(observation: object) -> tuple[str, str, str]:
    if observation is None:
        return "ACCEPTED", "ACCEPTED", ""
    if type(observation) is not dict:
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
    status = produced.get("overall_status")
    reason = produced.get("overall_reason")
    valid_status = type(status) is str and status in _PHASE2A_STATUSES
    valid_reason = type(reason) is str and bool(reason)
    if phase2a_inventory_errors(produced.get("checks")):
        return _rejected(
            "HER_CHECK_INVENTORY_REJECTED",
            "REJECTED",
            status if valid_status else "BLOCKED",
            reason if valid_reason else "HER_CHECK_INVENTORY_REJECTED",
        )
    if not valid_status:
        return _rejected("HER_PHASE2A_PASS_FORBIDDEN", "ACCEPTED", "BLOCKED", "HER_PHASE2A_PASS_FORBIDDEN")
    if schema_check(produced, PHASE2A_RESULT_SCHEMA) or not valid_reason:
        return _rejected(
            "HER_PHASE2A_RESULT_REJECTED",
            "ACCEPTED",
            status,
            reason if valid_reason else "HER_PHASE2A_RESULT_REJECTED",
        )
    return {
        "overall_status": status,
        "overall_reason": reason,
        "n4": "ACCEPTED",
        "phase2a_status": status,
        "phase2a_reason": reason,
        "checks": [
            {"check_id": item["check_id"], "status": item["status"], "reason": item["reason"]}
            for item in produced["checks"]
        ],
    }


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
