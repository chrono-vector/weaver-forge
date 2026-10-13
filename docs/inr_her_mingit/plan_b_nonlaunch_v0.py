"""Plan B public entry. NONLAUNCH only.

The single public entry calls the existing Plan A entry and returns before
spawn. C-7 and C-9 environment and argv proposals stay inside Plan A. This
module records that Plan B is the Human-selected next design candidate.
Plan A's PLAN_B value stays UNSELECTED.

Both hops stay unreached and both Jobs stay uncreated. The independent
wall-clock monitor is required and unassured. No Supervisor preparation
source is present. Controller self-report and Job CPU time are not
substitutes for that monitor. Open gates stay at the Plan A values,
including the unratified Controller ABI pin. This module adds no deadline.

No path calls CreateProcessW, a Job API, an attribute list, handle
duplication, or ResumeThread, and no path launches a process. F5, EB-14,
C-1 through C-9, and the Supervisor full-stop guarantee are untouched.
"""

from __future__ import annotations

from typing import NamedTuple

from docs.inr_her_mingit.plan_a_nonlaunch_v0 import (
    NonlaunchDecision,
    enter_plan_a_nonlaunch,
)

PLAN_B = "HUMAN_SELECTED_NEXT_DESIGN_CANDIDATE"
J0_HOP = "NOT_REACHED"
J1_HOP = "NOT_REACHED"
JOB_J0 = "NOT_CREATED"
JOB_J1 = "NOT_CREATED"
WALL_CLOCK_MONITOR = "REQUIRED_UNASSURED"
WALL_CLOCK_MONITOR_REQUIRED = True
WALL_CLOCK_MONITOR_ASSURED = False
SUPERVISOR_PREPARATION_SOURCE = "ABSENT"
CONTROLLER_SELF_REPORT_SUBSTITUTE = False
JOB_CPU_TIME_SUBSTITUTE = False
CONTROLLER_ABI_PIN = "NOT_RATIFIED"
CREATE_PROCESS_W = "NOT_REACHED"
JOB_API = "NOT_REACHED"
ATTRIBUTE_LIST = "NOT_REACHED"
HANDLE_DUPLICATE = "NOT_REACHED"
RESUME_THREAD = "NOT_REACHED"
REAL_PROCESS = "NOT_REACHED"

_PLAN_A_STOPS = frozenset({"REFUSED", "BLOCKED"})
_FIXED_REASONS = frozenset({
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


class PlanBNonlaunchDecision(NamedTuple):
    status: str
    reason: str
    transitions: tuple[str, ...]
    plan_a: NonlaunchDecision
    plan_b: str
    j0_hop: str
    j1_hop: str
    job_j0: str
    job_j1: str
    wall_clock_monitor: str
    wall_clock_monitor_required: bool
    wall_clock_monitor_assured: bool
    supervisor_preparation_source: str
    controller_self_report_substitute: bool
    job_cpu_time_substitute: bool
    controller_abi_pin: str
    n4: str
    n5: str
    ownership_exclusive: str
    operational_mingit_pin: str
    launch_identity: str
    file_identity: str
    reparse: str
    mingit_crt_compatible: bool
    windows_environment_sort_closed: bool
    environment_proposal: object
    command_proposal: object
    create_process_w: str
    job_api: str
    attribute_list: str
    handle_duplicate: str
    resume_thread: str
    real_process: str
    execution_authorized: bool
    full_inr_ready: bool
    stopped_before_spawn: bool


def enter_plan_b_nonlaunch(
    request: object,
    preparation: object = None,
) -> PlanBNonlaunchDecision:
    """Refuse Plan B before spawn. Plan A supplies the only proposal result."""
    plan_a = enter_plan_a_nonlaunch(request, preparation)
    status = plan_a.status if plan_a.status in _PLAN_A_STOPS else "REFUSED"
    reason = plan_a.reason if _fixed_reason(plan_a.reason) else "INPUT_REJECTED"
    return PlanBNonlaunchDecision(
        status,
        reason,
        plan_a.transitions + ("REFUSED_BEFORE_SPAWN",),
        plan_a,
        PLAN_B,
        J0_HOP,
        J1_HOP,
        JOB_J0,
        JOB_J1,
        WALL_CLOCK_MONITOR,
        WALL_CLOCK_MONITOR_REQUIRED,
        WALL_CLOCK_MONITOR_ASSURED,
        SUPERVISOR_PREPARATION_SOURCE,
        CONTROLLER_SELF_REPORT_SUBSTITUTE,
        JOB_CPU_TIME_SUBSTITUTE,
        CONTROLLER_ABI_PIN,
        plan_a.n4,
        plan_a.n5,
        plan_a.ownership_exclusive,
        plan_a.operational_mingit_pin,
        plan_a.launch_identity,
        plan_a.file_identity,
        plan_a.reparse,
        plan_a.mingit_crt_compatible,
        plan_a.windows_environment_sort_closed,
        plan_a.environment_proposal,
        plan_a.command_proposal,
        CREATE_PROCESS_W,
        JOB_API,
        ATTRIBUTE_LIST,
        HANDLE_DUPLICATE,
        RESUME_THREAD,
        REAL_PROCESS,
        plan_a.execution_authorized,
        plan_a.full_inr_ready,
        True,
    )


def _fixed_reason(reason: object) -> bool:
    return type(reason) is str and reason in _FIXED_REASONS
