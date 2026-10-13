"""Pure tests for the Plan B non-launch entry.

These tests call pure functions only. They do not launch a process.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_her_mingit import plan_a_nonlaunch_v0
from docs.inr_her_mingit import plan_b_nonlaunch_v0
from docs.inr_her_mingit.plan_a_nonlaunch_v0 import enter_plan_a_nonlaunch
from docs.inr_her_mingit.plan_b_nonlaunch_v0 import (
    ATTRIBUTE_LIST,
    CONTROLLER_ABI_PIN,
    CONTROLLER_SELF_REPORT_SUBSTITUTE,
    CREATE_PROCESS_W,
    HANDLE_DUPLICATE,
    J0_HOP,
    J1_HOP,
    JOB_API,
    JOB_CPU_TIME_SUBSTITUTE,
    JOB_J0,
    JOB_J1,
    PLAN_B,
    REAL_PROCESS,
    RESUME_THREAD,
    SUPERVISOR_PREPARATION_SOURCE,
    WALL_CLOCK_MONITOR,
    WALL_CLOCK_MONITOR_ASSURED,
    WALL_CLOCK_MONITOR_REQUIRED,
    enter_plan_b_nonlaunch,
)

_MODULE = Path(__file__).resolve().parents[1] / "plan_b_nonlaunch_v0.py"
_IMAGE = r"C:\tree\ucrt64\bin\git.exe"
_SENTINEL = "SENTINEL_EXTERNAL_INPUT"
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
_NATIVE_CALLS = frozenset({
    "CreateProcessW",
    "CreateJobObjectW",
    "AssignProcessToJobObject",
    "SetInformationJobObject",
    "QueryInformationJobObject",
    "TerminateJobObject",
    "InitializeProcThreadAttributeList",
    "UpdateProcThreadAttribute",
    "DeleteProcThreadAttributeList",
    "DuplicateHandle",
    "ResumeThread",
    "Popen",
    "system",
    "WinDLL",
    "CDLL",
    "windll",
})


def _snapshot() -> dict[str, str]:
    return {
        "WINDIR": r"C:\Windows",
        "SystemRoot": r"C:\Windows",
        "XDG_CONFIG_HOME": r"C:\xdg",
        "USERPROFILE": r"C:\home",
        "HOME": r"C:\home",
        "GIT_CONFIG_GLOBAL": r"C:\cfg\empty",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "PATH": r"C:\tree\ucrt64\bin",
    }


def _request(operation: str = "VERSION") -> dict[str, str]:
    return {
        "schema_version": "her.limited_git.request.v0",
        "operation_id": operation,
    }


def _preparation(snapshot: object = None, image: object = _IMAGE) -> dict[str, object]:
    return {
        "environment_snapshot": _snapshot() if snapshot is None else snapshot,
        "image": image,
    }


class PlanBNonlaunchTests(unittest.TestCase):
    def assert_stopped_before_spawn(self, decision: object) -> None:
        self.assertIn(decision.status, {"REFUSED", "BLOCKED"})
        self.assertIn(decision.reason, _FIXED_REASONS)
        self.assertNotIn(_SENTINEL, decision.reason)
        self.assertEqual(decision.transitions[-1], "REFUSED_BEFORE_SPAWN")
        self.assertTrue(decision.stopped_before_spawn)
        self.assertFalse(decision.execution_authorized)
        self.assertFalse(decision.full_inr_ready)
        self.assertEqual(decision.plan_b, "HUMAN_SELECTED_NEXT_DESIGN_CANDIDATE")
        self.assertEqual(decision.plan_a.plan_b, "UNSELECTED")
        self.assertEqual(decision.j0_hop, "NOT_REACHED")
        self.assertEqual(decision.j1_hop, "NOT_REACHED")
        self.assertEqual(decision.job_j0, "NOT_CREATED")
        self.assertEqual(decision.job_j1, "NOT_CREATED")
        self.assertEqual(decision.wall_clock_monitor, "REQUIRED_UNASSURED")
        self.assertTrue(decision.wall_clock_monitor_required)
        self.assertFalse(decision.wall_clock_monitor_assured)
        self.assertEqual(decision.supervisor_preparation_source, "ABSENT")
        self.assertFalse(decision.controller_self_report_substitute)
        self.assertFalse(decision.job_cpu_time_substitute)
        self.assertEqual(decision.controller_abi_pin, "NOT_RATIFIED")
        self.assertEqual(decision.n4, "OPEN")
        self.assertEqual(decision.n5, "OPEN")
        self.assertEqual(decision.ownership_exclusive, "OPEN")
        self.assertEqual(decision.operational_mingit_pin, "UNRATIFIED")
        self.assertEqual(decision.launch_identity, "UNBOUND_AT_LAUNCH")
        self.assertEqual(decision.file_identity, "UNPROVED")
        self.assertEqual(decision.reparse, "UNINSPECTED")
        self.assertFalse(decision.mingit_crt_compatible)
        self.assertFalse(decision.windows_environment_sort_closed)
        self.assertEqual(decision.create_process_w, "NOT_REACHED")
        self.assertEqual(decision.job_api, "NOT_REACHED")
        self.assertEqual(decision.attribute_list, "NOT_REACHED")
        self.assertEqual(decision.handle_duplicate, "NOT_REACHED")
        self.assertEqual(decision.resume_thread, "NOT_REACHED")
        self.assertEqual(decision.real_process, "NOT_REACHED")

    def test_plan_b_records_selection_without_changing_plan_a(self) -> None:
        self.assertEqual(PLAN_B, "HUMAN_SELECTED_NEXT_DESIGN_CANDIDATE")
        self.assertEqual(plan_a_nonlaunch_v0.PLAN_B, "UNSELECTED")
        decision = enter_plan_b_nonlaunch(_request(), _preparation())
        self.assertEqual(plan_a_nonlaunch_v0.PLAN_B, "UNSELECTED")
        self.assertEqual(decision.plan_a.plan_b, "UNSELECTED")
        self.assertEqual(decision.plan_b, PLAN_B)

    def test_plan_a_result_is_reused_for_proposals(self) -> None:
        request = _request("CONFIG_SCOPES")
        preparation = _preparation()
        decision = enter_plan_b_nonlaunch(request, preparation)
        plan_a = enter_plan_a_nonlaunch(request, preparation)
        self.assertEqual(decision.plan_a, plan_a)
        self.assertIs(decision.environment_proposal, decision.plan_a.environment_proposal)
        self.assertIs(decision.command_proposal, decision.plan_a.command_proposal)
        self.assertEqual(decision.environment_proposal, plan_a.environment_proposal)
        self.assertEqual(decision.command_proposal, plan_a.command_proposal)
        self.assertEqual(decision.status, plan_a.status)
        self.assertEqual(decision.reason, plan_a.reason)
        self.assertEqual(decision.transitions[:-1], plan_a.transitions)
        self.assert_stopped_before_spawn(decision)

    def test_refused_and_blocked_both_stop_before_spawn(self) -> None:
        refused = enter_plan_b_nonlaunch(_request(), None)
        self.assert_stopped_before_spawn(refused)
        self.assertEqual(refused.status, "REFUSED")
        self.assertEqual(refused.reason, "POLICY_UNAPPROVED")
        self.assertIsNone(refused.environment_proposal)
        self.assertIsNone(refused.command_proposal)

        blocked = enter_plan_b_nonlaunch(_request(), _preparation())
        self.assert_stopped_before_spawn(blocked)
        self.assertEqual(blocked.status, "BLOCKED")
        self.assertEqual(blocked.reason, "UNCONFIRMED")
        self.assertEqual(blocked.environment_proposal.status, "PROPOSED")
        self.assertEqual(blocked.command_proposal.status, "PROPOSED")

        tainted = _request()
        tainted["operation_id"] = _SENTINEL
        rejected = enter_plan_b_nonlaunch(tainted, _preparation())
        self.assert_stopped_before_spawn(rejected)
        self.assertEqual(rejected.status, "REFUSED")
        self.assertEqual(rejected.reason, "INPUT_REJECTED")

        claimed = _preparation()
        claimed["launch_identity"] = _SENTINEL
        authority = enter_plan_b_nonlaunch(_request(), claimed)
        self.assert_stopped_before_spawn(authority)
        self.assertEqual(authority.reason, "AUTHORITY_CLAIM_REJECTED")

    def test_hops_jobs_and_wall_clock_stay_unreached(self) -> None:
        self.assertEqual(J0_HOP, "NOT_REACHED")
        self.assertEqual(J1_HOP, "NOT_REACHED")
        self.assertEqual(JOB_J0, "NOT_CREATED")
        self.assertEqual(JOB_J1, "NOT_CREATED")
        self.assertEqual(WALL_CLOCK_MONITOR, "REQUIRED_UNASSURED")
        self.assertTrue(WALL_CLOCK_MONITOR_REQUIRED)
        self.assertFalse(WALL_CLOCK_MONITOR_ASSURED)
        self.assertEqual(SUPERVISOR_PREPARATION_SOURCE, "ABSENT")
        self.assertFalse(CONTROLLER_SELF_REPORT_SUBSTITUTE)
        self.assertFalse(JOB_CPU_TIME_SUBSTITUTE)
        for request, preparation in (
            (_SENTINEL, None),
            (_request(), None),
            (_request(), _preparation()),
        ):
            decision = enter_plan_b_nonlaunch(request, preparation)
            self.assert_stopped_before_spawn(decision)

    def test_open_gates_stay_at_plan_a_values(self) -> None:
        self.assertEqual(CONTROLLER_ABI_PIN, "NOT_RATIFIED")
        decision = enter_plan_b_nonlaunch(_request(), _preparation())
        self.assertEqual(decision.n4, decision.plan_a.n4)
        self.assertEqual(decision.n5, decision.plan_a.n5)
        self.assertEqual(decision.ownership_exclusive, decision.plan_a.ownership_exclusive)
        self.assertEqual(
            decision.operational_mingit_pin,
            decision.plan_a.operational_mingit_pin,
        )
        self.assertEqual(decision.launch_identity, decision.plan_a.launch_identity)
        self.assertEqual(decision.file_identity, decision.plan_a.file_identity)
        self.assertEqual(decision.reparse, decision.plan_a.reparse)
        self.assertEqual(
            decision.mingit_crt_compatible,
            decision.plan_a.mingit_crt_compatible,
        )
        self.assertEqual(
            decision.windows_environment_sort_closed,
            decision.plan_a.windows_environment_sort_closed,
        )
        self.assertEqual(decision.controller_abi_pin, "NOT_RATIFIED")
        self.assert_stopped_before_spawn(decision)

    def test_reasons_stay_fixed_codes(self) -> None:
        snapshot = _snapshot()
        snapshot["PATH"] = _SENTINEL
        cases = (
            (_SENTINEL, None),
            (_request(), {"environment_snapshot": snapshot, "image": _SENTINEL}),
            (
                {"schema_version": _SENTINEL, "operation_id": "VERSION"},
                _preparation(),
            ),
        )
        for request, preparation in cases:
            decision = enter_plan_b_nonlaunch(request, preparation)
            self.assert_stopped_before_spawn(decision)
            self.assertEqual(decision.reason, decision.plan_a.reason)
            self.assertNotIn(_SENTINEL, decision.reason)

    def test_module_reaches_no_native_api(self) -> None:
        self.assertEqual(CREATE_PROCESS_W, "NOT_REACHED")
        self.assertEqual(JOB_API, "NOT_REACHED")
        self.assertEqual(ATTRIBUTE_LIST, "NOT_REACHED")
        self.assertEqual(HANDLE_DUPLICATE, "NOT_REACHED")
        self.assertEqual(RESUME_THREAD, "NOT_REACHED")
        self.assertEqual(REAL_PROCESS, "NOT_REACHED")
        tree = ast.parse(_MODULE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        calls: set[str] = set()
        numbers: list[object] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    calls.add(func.id)
                elif isinstance(func, ast.Attribute):
                    calls.add(func.attr)
            elif isinstance(node, ast.Constant) and type(node.value) in {int, float}:
                numbers.append(node.value)
        self.assertEqual(imported, {"__future__", "typing", "docs"})
        public = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]
        self.assertEqual(public, ["enter_plan_b_nonlaunch"])
        self.assertIn("enter_plan_a_nonlaunch", calls)
        self.assertTrue(calls <= {
            "enter_plan_a_nonlaunch",
            "PlanBNonlaunchDecision",
            "frozenset",
            "type",
            "_fixed_reason",
        })
        self.assertTrue(calls.isdisjoint(_NATIVE_CALLS))
        self.assertEqual(numbers, [])
        self.assertFalse(hasattr(plan_b_nonlaunch_v0, "CreateProcessW"))


if __name__ == "__main__":
    unittest.main()
