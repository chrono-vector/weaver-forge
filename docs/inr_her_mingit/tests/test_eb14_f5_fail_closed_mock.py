"""Fixture tests for the EB-14/F5 fail-closed mock.

These tests inject a logical port. They do not launch a process.
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_her_mingit import eb14_f5_fail_closed_mock as mock
from docs.inr_her_mingit.eb14_f5_fail_closed_mock import (
    FORBIDDEN_PORT_NAMES,
    HANDLE_LIST_WIN32_ENCODING,
    HYPOTHETICAL_CLOSED_STDIN_FIXTURE,
    MOCK_ONLY_NON_IDENTITY_SCOPE,
    FailClosedMockMachine,
    MockWin32Port,
)

_MODULE = Path(__file__).resolve().parents[1] / "eb14_f5_fail_closed_mock.py"
_FORBIDDEN_IMPORTS = frozenset({"ctypes", "cffi", "subprocess"})
_PASS_MARKERS = frozenset({"PASS", "HOST_PASS", "FULL_INR_READY=YES", "operational success"})


def _ready() -> dict:
    return {
        "selected_approach": "J0+J1",
        "ownership_proven": True,
        "ownership_proof": "FIXTURE_ONLY",
        "job_list_supported": True,
        "job_compatible": True,
        "supervisor_independence_guaranteed": True,
        "pin_approved": True,
        "approved_limit_tokens_present": True,
        "closed_stdin": HYPOTHETICAL_CLOSED_STDIN_FIXTURE,
        "stdout_reader_started": True,
        "stderr_reader_started": True,
        "controller_deadline_armed": True,
        "supervisor_monitor_armed": True,
        "supervisor_readiness_source": "SUPERVISOR",
        "creation_flags": frozenset({
            "EXTENDED_STARTUPINFO_PRESENT",
            "CREATE_SUSPENDED",
            "CREATE_UNICODE_ENVIRONMENT",
        }),
        "handle_list": HANDLE_LIST_WIN32_ENCODING,
        "job_configuration": {
            "kill_on_job_close": True,
            "breakaway_ok": False,
            "silent_breakaway_ok": False,
        },
    }


def _machine(port: object, **kwargs: object) -> FailClosedMockMachine:
    kwargs.setdefault("controller_scope", MOCK_ONLY_NON_IDENTITY_SCOPE)
    return FailClosedMockMachine(port, **kwargs)


_SUCCESS_CALLS = [
    "prepare_job:J0",
    "create_suspended_with_job_list:J0:J0",
    "prepare_job:J1",
    "create_suspended_with_job_list:J1:J1",
    "query_membership:J1",
    "resume_primary_thread",
]


class FailClosedMockTests(unittest.TestCase):
    def test_module_states_the_logical_fixture_limits(self) -> None:
        text = mock.__doc__ or ""
        self.assertIn("logical fixture model", text)
        self.assertIn("not a full two-process host proof", text)
        self.assertIn("does not sandbox", text)
        self.assertIn("Win32 encoding stays unresolved", text)

    def test_prelaunch_refusals_do_not_create(self) -> None:
        cases = (
            ({"ownership_proven": False}, "UNPROVEN_OWNERSHIP"),
            ({"ownership_proven": True, "ownership_proof": "DACL"}, "UNPROVEN_OWNERSHIP"),
            ({"ownership_proof": "UNNAMED_HANDLE"}, "UNPROVEN_OWNERSHIP"),
            ({"ownership_proof": "NON_INHERITABLE"}, "UNPROVEN_OWNERSHIP"),
            ({"job_compatible": False}, "JOB_COMPATIBILITY"),
            ({"job_list_supported": False}, "JOB_COMPATIBILITY"),
            ({"supervisor_independence_guaranteed": False}, "SUPERVISOR_INDEPENDENCE"),
            ({"cpu_time_backstop_is_monitor": True}, "SUPERVISOR_INDEPENDENCE"),
            ({"pin_approved": False}, "UNAPPROVED_PIN"),
            ({"approved_limit_tokens_present": False}, "ABSENT_APPROVED_LIMIT_TOKENS"),
            ({"closed_stdin": None}, "ABSENT_CLOSED_STDIN"),
            ({"closed_stdin": "DEVNULL"}, "ABSENT_CLOSED_STDIN"),
            ({"closed_stdin": "EB5_CLOSED_STDIN"}, "ABSENT_CLOSED_STDIN"),
            ({"selected_approach": None}, "APPROACH_NOT_SELECTED"),
            ({"selected_approach": "J1"}, "APPROACH_NOT_SELECTED"),
            ({"selected_approach": "J0"}, "APPROACH_NOT_SELECTED"),
            ({"creation_flags": None}, "CREATION_FLAGS_REJECTED"),
            ({"creation_flags": frozenset()}, "CREATION_FLAGS_REJECTED"),
            ({"creation_flags": ["EXTENDED_STARTUPINFO_PRESENT", "CREATE_SUSPENDED", "CREATE_UNICODE_ENVIRONMENT"]}, "CREATION_FLAGS_REJECTED"),
            ({"creation_flags": frozenset({
                "EXTENDED_STARTUPINFO_PRESENT",
                "CREATE_SUSPENDED",
                "CREATE_UNICODE_ENVIRONMENT",
                "CREATE_BREAKAWAY_FROM_JOB",
            })}, "CREATION_FLAGS_REJECTED"),
            ({"handle_list": None}, "HANDLE_LIST_REJECTED"),
            ({"handle_list": ("EB5_CLOSED_STDIN", "STDOUT_WRITE", "STDERR_WRITE")}, "HANDLE_LIST_REJECTED"),
            ({"handle_list": (HYPOTHETICAL_CLOSED_STDIN_FIXTURE, "STDOUT_WRITE", "STDERR_WRITE")}, "HANDLE_LIST_REJECTED"),
            ({"handle_list": "EB5_CLOSED_STDIN"}, "HANDLE_LIST_REJECTED"),
            ({"job_configuration": None}, "JOB_CONFIGURATION"),
            ({"job_configuration": {"kill_on_job_close": True, "breakaway_ok": True, "silent_breakaway_ok": False}}, "JOB_CONFIGURATION"),
            ({"job_configuration": {"kill_on_job_close": False, "breakaway_ok": False, "silent_breakaway_ok": False}}, "JOB_CONFIGURATION"),
            ({"job_configuration": {"kill_on_job_close": True, "breakaway_ok": False, "silent_breakaway_ok": True}}, "JOB_CONFIGURATION"),
        )
        for patch, reason in cases:
            port = MockWin32Port()
            fixture = _ready()
            fixture.update(patch)
            result = _machine(port).run(fixture)
            self.assertEqual(result["disposition"], "REFUSED", reason)
            self.assertEqual(result["reason"], reason)
            self.assertEqual(result["resume_count"], 0)
            self.assertEqual(result["launch_identity"], "UNBOUND_AT_LAUNCH", reason)
            self.assertFalse(result["scope_gate_is_operational_authority"], reason)
            self.assertFalse(any(call.startswith("create_suspended") for call in port.calls), reason)
            self.assertFalse(port.real_process_launched)

    def test_omitted_required_proof_refuses_before_create(self) -> None:
        omissions = (
            ("selected_approach", "APPROACH_NOT_SELECTED"),
            ("creation_flags", "CREATION_FLAGS_REJECTED"),
            ("handle_list", "HANDLE_LIST_REJECTED"),
            ("job_configuration", "JOB_CONFIGURATION"),
            ("closed_stdin", "ABSENT_CLOSED_STDIN"),
        )
        for key, reason in omissions:
            port = MockWin32Port()
            fixture = _ready()
            del fixture[key]
            result = _machine(port).run(fixture)
            self.assertEqual(result["disposition"], "REFUSED", reason)
            self.assertEqual(result["reason"], reason)
            self.assertEqual(result["cleanup"], "NOT_APPLICABLE", reason)
            self.assertEqual(result["resume_count"], 0)
            self.assertEqual(port.calls, [], reason)
            self.assertEqual(port.resume_calls, 0)

    def test_scope_omission_and_unknown_scope_refuse_before_spawn(self) -> None:
        cases = (
            {},
            {"controller_scope": None},
            {"controller_scope": "UNKNOWN"},
            {"controller_scope": ""},
            {"controller_scope": False},
            {"controller_scope": "OBSERVATIONAL"},
        )
        for kwargs in cases:
            port = MockWin32Port()
            fixture = _ready()
            fixture["launch_identity"] = "CALLER_ASSERTED_IMAGE"
            fixture["identity_required_scope"] = False
            fixture["controller_scope"] = MOCK_ONLY_NON_IDENTITY_SCOPE
            result = FailClosedMockMachine(port, **kwargs).run(fixture)
            self.assertEqual(result["disposition"], "REFUSED", repr(kwargs))
            self.assertEqual(result["reason"], "LAUNCH_IDENTITY_REQUIRED_UNPROVEN", repr(kwargs))
            self.assertEqual(result["launch_identity"], "UNBOUND_AT_LAUNCH", repr(kwargs))
            self.assertFalse(result["scope_gate_is_operational_authority"], repr(kwargs))
            self.assertEqual(result["cleanup"], "NOT_APPLICABLE", repr(kwargs))
            self.assertEqual(port.calls, [], repr(kwargs))
            self.assertEqual(port.resume_calls, 0, repr(kwargs))
            self.assertFalse(port.real_process_launched)

    def test_caller_launch_identity_does_not_authorize(self) -> None:
        port = MockWin32Port()
        fixture = _ready()
        fixture["launch_identity"] = "CALLER_ASSERTED_IMAGE"
        fixture["identity_required_scope"] = False
        result = _machine(port).run(fixture)
        self.assertEqual(result["disposition"], "UNEXECUTED")
        self.assertEqual(result["launch_identity"], "UNBOUND_AT_LAUNCH")
        self.assertFalse(result["scope_gate_is_operational_authority"])
        self.assertEqual(result["execution_binding_real"], "UNEXECUTED")
        self.assertEqual(result["full_inr_ready"], "NO")
        self.assertEqual(result["operational_mingit_pin"], "UNRATIFIED")
        self.assertEqual(result["closed_stdin_win32_encoding"], "UNRESOLVED")
        self.assertEqual(result["host_model"], "LOGICAL_FIXTURE_NOT_TWO_PROCESS_HOST_PROOF")
        self.assertEqual(port.calls, _SUCCESS_CALLS)
        self.assertFalse(port.real_process_launched)

    def test_missing_resume_gates_do_not_resume(self) -> None:
        cases = (
            ({"stdout_reader_started": False}, "READERS_NOT_STARTED"),
            ({"stderr_reader_started": False}, "READERS_NOT_STARTED"),
            ({"controller_deadline_armed": False}, "CONTROLLER_DEADLINE_UNARMED"),
            ({"supervisor_monitor_armed": False}, "SUPERVISOR_NOT_READY"),
            ({"supervisor_readiness_source": "CONTROLLER"}, "SUPERVISOR_SELF_ATTESTATION_INSUFFICIENT"),
            ({"supervisor_readiness_source": None}, "SUPERVISOR_NOT_READY"),
        )
        for patch, reason in cases:
            port = MockWin32Port()
            fixture = _ready()
            fixture.update(patch)
            result = _machine(port).run(fixture)
            self.assertEqual(result["disposition"], "UNCONFIRMED", reason)
            self.assertEqual(result["reason"], reason)
            self.assertEqual(result["resume_count"], 0)
            self.assertEqual(port.resume_calls, 0)
            self.assertEqual(
                port.calls,
                [
                    "prepare_job:J0",
                    "create_suspended_with_job_list:J0:J0",
                    "prepare_job:J1",
                    "create_suspended_with_job_list:J1:J1",
                    "query_membership:J1",
                    "terminate_job:J1",
                    "confirm_owned_membership:J1",
                    "close_owner_handles:J1",
                ],
                reason,
            )
            self.assertNotIn("resume_primary_thread", port.calls)

    def test_creation_failure_confirms_owned_membership_and_does_not_retry(self) -> None:
        port = MockWin32Port(target_create=False, signalled=True, remaining_members=0)
        machine = _machine(port)
        result = machine.run(_ready())
        self.assertEqual(result["disposition"], "REFUSED")
        self.assertEqual(result["reason"], "J1_CREATION_FAILED")
        self.assertEqual(result["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")
        self.assertFalse(result["terminate_return_is_cleanup_success"])
        self.assertEqual(port.resume_calls, 0)
        self.assertNotIn("AssignProcessToJobObject", port.calls)
        self.assertEqual(port.calls.count("create_suspended_with_job_list:J1:J1"), 1)
        again = machine.run(_ready())
        self.assertEqual(again["disposition"], "REFUSED")
        self.assertEqual(again["reason"], "RETRY_PROHIBITED")
        self.assertEqual(port.calls.count("create_suspended_with_job_list:J1:J1"), 1)
        self.assertEqual(port.resume_calls, 0)

    def test_terminate_return_with_leftover_members_is_unconfirmed(self) -> None:
        port = MockWin32Port(
            target_create=False,
            terminate_return=True,
            signalled=False,
            remaining_members=2,
        )
        result = _machine(port).run(_ready())
        self.assertEqual(result["disposition"], "UNCONFIRMED")
        self.assertEqual(result["cleanup"], "UNCONFIRMED")
        self.assertTrue(port.terminate_return)
        self.assertIn("confirm_owned_membership:J1", port.calls)
        self.assertNotIn("resume_primary_thread", port.calls)

    def test_default_cleanup_evidence_stays_unconfirmed(self) -> None:
        port = MockWin32Port(target_create=False)
        result = _machine(port).run(_ready())
        self.assertEqual(port.signalled, "UNKNOWN")
        self.assertEqual(port.remaining_members, "UNKNOWN")
        self.assertEqual(result["disposition"], "UNCONFIRMED")
        self.assertEqual(result["reason"], "J1_CREATION_FAILED")
        self.assertEqual(result["cleanup"], "UNCONFIRMED")
        self.assertNotEqual(result["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")
        self.assertFalse(result["terminate_return_is_cleanup_success"])
        self.assertEqual(
            port.calls,
            [
                "prepare_job:J0",
                "create_suspended_with_job_list:J0:J0",
                "prepare_job:J1",
                "create_suspended_with_job_list:J1:J1",
                "terminate_job:J1",
                "confirm_owned_membership:J1",
                "close_owner_handles:J1",
            ],
        )

    def test_boolean_remaining_members_are_not_empty_proof(self) -> None:
        cases = (False, True, 0.0)
        for remaining in cases:
            port = MockWin32Port(target_create=False, signalled=True, remaining_members=remaining)
            result = _machine(port).run(_ready())
            self.assertEqual(result["disposition"], "UNCONFIRMED", repr(remaining))
            self.assertEqual(result["cleanup"], "UNCONFIRMED", repr(remaining))
            self.assertEqual(result["reason"], "J1_CREATION_FAILED")
            self.assertNotIn("resume_primary_thread", port.calls)

    def test_double_resume_does_not_call_the_port_again(self) -> None:
        port = MockWin32Port()
        machine = _machine(port)
        first = machine.run(_ready())
        second = machine.request_resume()
        self.assertEqual(first["disposition"], "UNEXECUTED")
        self.assertEqual(first["resume_count"], 1)
        self.assertEqual(first["full_inr_ready"], "NO")
        self.assertEqual(first["execution_binding_real"], "UNEXECUTED")
        self.assertEqual(first["operational_mingit_pin"], "UNRATIFIED")
        self.assertEqual(first["numeric_limits"], "UNSET")
        self.assertEqual(first["launch_identity"], "UNBOUND_AT_LAUNCH")
        self.assertFalse(first["scope_gate_is_operational_authority"])
        self.assertEqual(second["disposition"], "REFUSED")
        self.assertEqual(second["reason"], "DOUBLE_RESUME")
        self.assertEqual(port.resume_calls, 1)
        self.assertEqual(port.calls, _SUCCESS_CALLS)
        self._assert_creation_time_order(port.calls)
        self.assertFalse(port.real_process_launched)
        self.assertFalse(port.assigned_after_create)

    def test_resume_failure_exception_and_reentrancy_lock_before_retry(self) -> None:
        false_port = MockWin32Port()
        false_machine = _machine(false_port)

        def false_resume(port: MockWin32Port) -> bool:
            port.nested = false_machine.run(_ready())
            return False

        false_port.observers["resume"] = false_resume
        false_result = false_machine.run(_ready())
        self.assertEqual(false_port.nested["disposition"], "REFUSED")
        self.assertEqual(false_port.nested["reason"], "RETRY_PROHIBITED")
        self.assertEqual(false_result["disposition"], "UNCONFIRMED")
        self.assertEqual(false_result["reason"], "RESUME_FAILED")
        self.assertNotEqual(false_result["disposition"], "UNEXECUTED")
        self.assertEqual(false_result["resume_count"], 1)
        self.assertEqual(false_result["cleanup"], "UNCONFIRMED")
        self.assertEqual(false_port.resume_calls, 1)
        self.assertEqual(false_port.calls[-4:], [
            "resume_primary_thread",
            "terminate_job:J1",
            "confirm_owned_membership:J1",
            "close_owner_handles:J1",
        ])
        false_again = false_machine.run(_ready())
        false_second_request = false_machine.request_resume()
        self.assertEqual(false_again["reason"], "RETRY_PROHIBITED")
        self.assertEqual(false_second_request["reason"], "DOUBLE_RESUME")
        self.assertEqual(false_port.resume_calls, 1)
        self.assertEqual(false_port.calls.count("resume_primary_thread"), 1)

        raising_port = MockWin32Port()
        raising_port.errors["resume"] = RuntimeError("injected resume failure")
        raising_machine = _machine(raising_port)
        raising_result = raising_machine.run(_ready())
        self.assertEqual(raising_result["disposition"], "UNCONFIRMED")
        self.assertEqual(raising_result["reason"], "RESUME_FAILED")
        self.assertNotEqual(
            raising_result["reason"],
            "MOCK_RESUME_RECORDED_REAL_BINDING_UNEXECUTED",
        )
        self.assertEqual(raising_result["cleanup"], "UNCONFIRMED")
        self.assertEqual(raising_port.resume_calls, 1)
        self.assertEqual(raising_port.calls[-4:], [
            "resume_primary_thread",
            "terminate_job:J1",
            "confirm_owned_membership:J1",
            "close_owner_handles:J1",
        ])
        raising_again = raising_machine.run(_ready())
        self.assertEqual(raising_again["disposition"], "REFUSED")
        self.assertEqual(raising_again["reason"], "RETRY_PROHIBITED")
        self.assertEqual(raising_machine.request_resume()["reason"], "DOUBLE_RESUME")
        self.assertEqual(raising_port.resume_calls, 1)
        self.assertEqual(raising_port.calls.count("resume_primary_thread"), 1)

    def test_resume_interruption_is_not_success_and_blocks_retry(self) -> None:
        for interruption in (KeyboardInterrupt(), SystemExit(1)):
            port = MockWin32Port()
            port.errors["resume"] = interruption
            machine = _machine(port)
            with self.assertRaises(type(interruption)):
                machine.run(_ready())
            self.assertEqual(port.resume_calls, 1)
            self.assertEqual(port.calls.count("resume_primary_thread"), 1)
            self.assertEqual(
                port.calls,
                [
                    "prepare_job:J0",
                    "create_suspended_with_job_list:J0:J0",
                    "prepare_job:J1",
                    "create_suspended_with_job_list:J1:J1",
                    "query_membership:J1",
                    "resume_primary_thread",
                    "terminate_job:J1",
                    "confirm_owned_membership:J1",
                    "close_owner_handles:J1",
                ],
            )
            self.assertFalse(port.real_process_launched)
            again = machine.run(_ready())
            self.assertEqual(again["disposition"], "REFUSED")
            self.assertEqual(again["reason"], "RETRY_PROHIBITED")
            self.assertEqual(again["launch_identity"], "UNBOUND_AT_LAUNCH")
            self.assertEqual(port.resume_calls, 1)
            self.assertEqual(machine.request_resume()["reason"], "DOUBLE_RESUME")
            self.assertEqual(port.calls.count("resume_primary_thread"), 1)

    def test_unsupported_job_configuration_does_not_create_or_resume(self) -> None:
        flagged = MockWin32Port(configuration_ok=False)
        flagged_result = _machine(flagged).run(_ready())
        self.assertEqual(flagged_result["reason"], "JOB_CONFIGURATION")
        self.assertEqual(flagged_result["disposition"], "UNCONFIRMED")
        self.assertEqual(flagged.resume_calls, 0)
        self.assertFalse(any(call.startswith("create_suspended") for call in flagged.calls))
        self.assertEqual(flagged.calls[0], "prepare_job:J0")
        self.assertIn("terminate_job:J0", flagged.calls)

        breakaway = MockWin32Port()
        breakaway.breakaway_jobs.add("J1")
        breakaway_result = _machine(breakaway).run(_ready())
        self.assertEqual(breakaway_result["reason"], "JOB_CONFIGURATION")
        self.assertEqual(breakaway_result["disposition"], "UNCONFIRMED")
        self.assertNotIn("create_suspended_with_job_list:J1:J1", breakaway.calls)
        self.assertNotIn("resume_primary_thread", breakaway.calls)
        self.assertIn("terminate_job:J1", breakaway.calls)
        self.assertEqual(breakaway.resume_calls, 0)
        self.assertLess(
            breakaway.calls.index("create_suspended_with_job_list:J0:J0"),
            breakaway.calls.index("prepare_job:J1"),
        )

    def test_membership_failure_does_not_resume(self) -> None:
        port = MockWin32Port(creation_time_member=False)
        result = _machine(port).run(_ready())
        self.assertEqual(result["reason"], "MEMBERSHIP_UNVERIFIED")
        self.assertEqual(result["disposition"], "UNCONFIRMED")
        self.assertEqual(port.resume_calls, 0)
        self.assertIn("terminate_job:J1", port.calls)
        self.assertNotIn("resume_primary_thread", port.calls)

    def test_injected_ports_and_forbidden_names_are_refused(self) -> None:
        tree = ast.parse(_MODULE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        defined: set[str] = set()
        called: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined.add(node.name)
            elif isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    called.add(func.id)
                elif isinstance(func, ast.Attribute):
                    called.add(func.attr)
        self.assertTrue(_FORBIDDEN_IMPORTS.isdisjoint(imported))
        absent = {
            "AssignProcessToJobObject",
            "assign_process_to_job_object",
            "Popen",
            "popen",
            "CreateProcessW",
            "LoadLibrary",
            "WinDLL",
            "CDLL",
            "system",
        }
        self.assertTrue(absent.isdisjoint(defined))
        self.assertTrue(absent.isdisjoint(called))

        class SubclassPort(MockWin32Port):
            pass

        class RealShapedPort:
            def __init__(self) -> None:
                self.calls: list[str] = []
                self.resume_calls = 0
                self.real_process_launched = False

            def prepare_job(self, name: str) -> bool:
                self.calls.append("prepare_job:" + name)
                return True

            def create_suspended_with_job_list(self, hop: str, job_name: str) -> bool:
                self.calls.append("create:" + hop)
                return True

            def query_membership(self, job_name: str) -> dict[str, bool]:
                return {"creation_time_member": True, "configuration_ok": True}

            def terminate_job(self, job_name: str) -> bool:
                return True

            def confirm_owned_membership(self, job_name: str) -> dict[str, object]:
                return {"signalled": True, "remaining": 0}

            def close_owner_handles(self, job_name: str) -> None:
                return None

            def resume_primary_thread(self) -> bool:
                self.resume_calls += 1
                return True

        for port in (SubclassPort(), RealShapedPort()):
            result = _machine(port).run(_ready())
            self.assertEqual(result["disposition"], "REFUSED")
            self.assertEqual(result["reason"], "PORT_REJECTED")
            self.assertEqual(result["cleanup"], "NOT_APPLICABLE")
            self.assertEqual(port.calls, [])
            self.assertEqual(port.resume_calls, 0)
            self.assertFalse(port.real_process_launched)

        named = MockWin32Port()
        setattr(named, "AssignProcessToJobObject", lambda *_args: True)
        setattr(named, "Popen", lambda *_args: None)
        named_result = _machine(named).run(_ready())
        self.assertEqual(named_result["disposition"], "REFUSED")
        self.assertEqual(named_result["reason"], "FORBIDDEN_API_PRESENT")
        self.assertEqual(named.calls, [])
        self.assertTrue(FORBIDDEN_PORT_NAMES.isdisjoint(set(MockWin32Port.__dict__)))

    def test_non_bool_and_exceptional_port_results_do_not_resume_or_retry(self) -> None:
        truthy = MockWin32Port(signalled=True, remaining_members=0)
        truthy.results["prepare:J0"] = 1
        truthy_machine = _machine(truthy)
        truthy_result = truthy_machine.run(_ready())
        self.assertEqual(truthy_result["disposition"], "UNCONFIRMED")
        self.assertEqual(truthy_result["reason"], "J0_PREPARATION_FAILED")
        self.assertEqual(truthy_result["cleanup"], "UNCONFIRMED")
        self.assertEqual(truthy.calls[0], "prepare_job:J0")
        self.assertFalse(any(call.startswith("create_suspended") for call in truthy.calls))
        self.assertNotIn("resume_primary_thread", truthy.calls)
        self.assertEqual(truthy_machine.run(_ready())["reason"], "RETRY_PROHIBITED")
        self.assertEqual(truthy.calls.count("prepare_job:J0"), 1)

        created = MockWin32Port(signalled=True, remaining_members=0)
        created.results["create:J1"] = {"ok": True}
        created_machine = _machine(created)
        created_result = created_machine.run(_ready())
        self.assertEqual(created_result["disposition"], "UNCONFIRMED")
        self.assertEqual(created_result["reason"], "J1_CREATION_FAILED")
        self.assertEqual(created_result["cleanup"], "UNCONFIRMED")
        self.assertNotEqual(created_result["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")
        self.assertEqual(created.calls.count("create_suspended_with_job_list:J0:J0"), 1)
        self.assertEqual(created.calls.count("create_suspended_with_job_list:J1:J1"), 1)
        self.assertNotIn("resume_primary_thread", created.calls)
        self.assertEqual(created_machine.run(_ready())["reason"], "RETRY_PROHIBITED")
        self.assertEqual(created.calls.count("create_suspended_with_job_list:J1:J1"), 1)

        prepare_error = MockWin32Port()
        prepare_error.errors["prepare:J0"] = RuntimeError("prepare failed")
        prepare_machine = _machine(prepare_error)
        prepare_result = prepare_machine.run(_ready())
        self.assertEqual(prepare_result["disposition"], "UNCONFIRMED")
        self.assertEqual(prepare_result["reason"], "J0_PREPARATION_FAILED")
        self.assertNotIn("create_suspended_with_job_list:J0:J0", prepare_error.calls)
        self.assertNotIn("resume_primary_thread", prepare_error.calls)
        self.assertIn("terminate_job:J0", prepare_error.calls)
        self.assertEqual(prepare_machine.run(_ready())["reason"], "RETRY_PROHIBITED")
        self.assertEqual(prepare_error.calls.count("prepare_job:J0"), 1)

        create_error = MockWin32Port()
        create_error.errors["create:J0"] = RuntimeError("create failed")
        create_machine = _machine(create_error)
        create_result = create_machine.run(_ready())
        self.assertEqual(create_result["disposition"], "UNCONFIRMED")
        self.assertEqual(create_result["reason"], "J0_CREATION_FAILED")
        self.assertEqual(create_result["cleanup"], "UNCONFIRMED")
        self.assertNotIn("prepare_job:J1", create_error.calls)
        self.assertNotIn("resume_primary_thread", create_error.calls)
        self.assertEqual(create_error.calls.count("create_suspended_with_job_list:J0:J0"), 1)
        self.assertEqual(create_machine.run(_ready())["reason"], "RETRY_PROHIBITED")
        self.assertEqual(create_error.calls.count("create_suspended_with_job_list:J0:J0"), 1)

        membership_error = MockWin32Port()
        membership_error.errors["membership:J1"] = RuntimeError("membership failed")
        membership_result = _machine(membership_error).run(_ready())
        self.assertEqual(membership_result["disposition"], "UNCONFIRMED")
        self.assertEqual(membership_result["reason"], "MEMBERSHIP_UNVERIFIED")
        self.assertNotIn("resume_primary_thread", membership_error.calls)
        self.assertIn("terminate_job:J1", membership_error.calls)

        membership_port = MockWin32Port(signalled=True, remaining_members=0)
        membership_port.results["membership:J1"] = ["creation_time_member", "configuration_ok"]
        membership_shape = _machine(membership_port).run(_ready())
        self.assertEqual(membership_shape["reason"], "MEMBERSHIP_UNVERIFIED")
        self.assertEqual(membership_shape["disposition"], "REFUSED")
        self.assertEqual(membership_shape["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")
        self.assertNotIn("resume_primary_thread", membership_port.calls)

    def test_cleanup_uncertainty_is_not_confirmed_empty(self) -> None:
        terminate_port = MockWin32Port(target_create=False, signalled=True, remaining_members=0)
        terminate_port.errors["terminate:J1"] = RuntimeError("terminate failed")
        terminate_result = _machine(terminate_port).run(_ready())
        self.assertEqual(terminate_result["disposition"], "UNCONFIRMED")
        self.assertEqual(terminate_result["reason"], "J1_CREATION_FAILED")
        self.assertEqual(terminate_result["cleanup"], "UNCONFIRMED")
        self.assertNotEqual(terminate_result["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")
        self.assertFalse(terminate_result["terminate_return_is_cleanup_success"])
        self.assertIn("confirm_owned_membership:J1", terminate_port.calls)
        self.assertIn("close_owner_handles:J1", terminate_port.calls)
        self.assertNotIn("resume_primary_thread", terminate_port.calls)

        confirm_port = MockWin32Port(target_create=False, signalled=True, remaining_members=0)
        confirm_port.errors["confirm:J1"] = RuntimeError("confirm failed")
        confirm_result = _machine(confirm_port).run(_ready())
        self.assertEqual(confirm_result["cleanup"], "UNCONFIRMED")
        self.assertEqual(confirm_result["disposition"], "UNCONFIRMED")
        self.assertIn("close_owner_handles:J1", confirm_port.calls)

        close_port = MockWin32Port(target_create=False, signalled=True, remaining_members=0)
        close_port.errors["close:J1"] = RuntimeError("close failed")
        close_result = _machine(close_port).run(_ready())
        self.assertEqual(close_result["cleanup"], "UNCONFIRMED")
        self.assertNotEqual(close_result["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")
        self.assertIn("confirm_owned_membership:J1", close_port.calls)

        shaped = MockWin32Port(target_create=False, signalled=True, remaining_members=0)
        shaped.results["confirm:J1"] = ["signalled", True, "remaining", 0]
        shaped_result = _machine(shaped).run(_ready())
        self.assertEqual(shaped_result["disposition"], "UNCONFIRMED")
        self.assertEqual(shaped_result["cleanup"], "UNCONFIRMED")

        odd_terminate = MockWin32Port(target_create=False, signalled=True, remaining_members=0)
        odd_terminate.results["terminate:J1"] = 1
        odd_result = _machine(odd_terminate).run(_ready())
        self.assertEqual(odd_result["cleanup"], "UNCONFIRMED")
        self.assertNotEqual(odd_result["cleanup"], "OWNED_JOB_MEMBERSHIP_EMPTY")

    def test_reentrancy_during_prepare_does_not_start_a_second_sequence(self) -> None:
        port = MockWin32Port()
        machine = _machine(port)

        def reenter(observed: MockWin32Port, name: str) -> None:
            if name == "J0":
                observed.nested = machine.run(_ready())

        port.observers["prepare"] = reenter
        result = machine.run(_ready())
        self.assertEqual(port.nested["disposition"], "REFUSED")
        self.assertEqual(port.nested["reason"], "RETRY_PROHIBITED")
        self.assertEqual(port.nested["cleanup"], "NOT_APPLICABLE")
        self.assertEqual(result["disposition"], "UNEXECUTED")
        self.assertEqual(result["resume_count"], 1)
        self.assertEqual(port.calls.count("prepare_job:J0"), 1)
        self.assertEqual(port.calls.count("create_suspended_with_job_list:J0:J0"), 1)
        self.assertEqual(port.calls.count("resume_primary_thread"), 1)
        self.assertEqual(port.resume_calls, 1)
        self._assert_creation_time_order(port.calls)
        again = machine.run(_ready())
        self.assertEqual(again["reason"], "RETRY_PROHIBITED")
        self.assertEqual(port.resume_calls, 1)

    def test_no_actual_process_launch_and_no_pass_claim(self) -> None:
        port = MockWin32Port()
        result = _machine(port).run(_ready())
        self.assertFalse(port.real_process_launched)
        self.assertFalse(result["real_process_launched"])
        self.assertEqual(port.calls, _SUCCESS_CALLS)
        self._assert_creation_time_order(port.calls)
        self.assertEqual(result["disposition"], "UNEXECUTED")
        self.assertNotIn(result["disposition"], _PASS_MARKERS)
        self.assertEqual(result["host_qualification"], "OPEN")
        self.assertEqual(result["host_model"], "LOGICAL_FIXTURE_NOT_TWO_PROCESS_HOST_PROOF")
        self.assertNotIn("popen", [call.lower() for call in port.calls])
        self.assertFalse(port.assigned_after_create)

    def _assert_creation_time_order(self, calls: list[str]) -> None:
        self.assertLess(
            calls.index("prepare_job:J0"),
            calls.index("create_suspended_with_job_list:J0:J0"),
        )
        self.assertLess(
            calls.index("create_suspended_with_job_list:J0:J0"),
            calls.index("prepare_job:J1"),
        )
        self.assertLess(
            calls.index("prepare_job:J1"),
            calls.index("create_suspended_with_job_list:J1:J1"),
        )
        self.assertLess(
            calls.index("create_suspended_with_job_list:J1:J1"),
            calls.index("query_membership:J1"),
        )
        self.assertLess(calls.index("query_membership:J1"), calls.index("resume_primary_thread"))
        self.assertEqual(calls.count("resume_primary_thread"), 1)


if __name__ == "__main__":
    unittest.main()
