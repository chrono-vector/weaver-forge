"""Pure tests for the Plan A non-launch entry.

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

from docs.inr_her_mingit.ascii_env_argv_v0 import (
    propose_ascii_command_line,
    propose_utf16le_environment_block,
)
from docs.inr_her_mingit.plan_a_nonlaunch_v0 import (
    CREATE_PROCESS_W,
    EXECUTION_BINDING_REAL,
    FILE_IDENTITY_UNPROVED,
    FULL_INR_READY,
    INHERITABLE_HANDLE_DUPLICATE,
    LAUNCH_IDENTITY,
    MINGIT_CRT_COMPATIBLE,
    N4,
    N5,
    OPERATIONAL_MINGIT_PIN,
    OWNERSHIP_EXCLUSIVE,
    PLAN_A,
    PLAN_B,
    PLAN_C,
    REAL_WINDOWS_EXECUTION,
    REPARSE_UNINSPECTED,
    WINDOWS_ENVIRONMENT_SORT_CLOSED,
    enter_plan_a_nonlaunch,
)

_MODULE = Path(__file__).resolve().parents[1] / "plan_a_nonlaunch_v0.py"
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


class PlanANonlaunchTests(unittest.TestCase):
    def assert_refused_before_creation(self, decision: object) -> None:
        self.assertNotIn(decision.status, {"PASS", "PROPOSED", "LAUNCHED", "EXECUTED"})
        self.assertIn(decision.reason, _FIXED_REASONS)
        self.assertNotIn(_SENTINEL, decision.reason)
        self.assertEqual(decision.transitions[-1], "REFUSED_BEFORE_CREATE")
        self.assertNotIn("CREATE_PROCESS_W", decision.transitions)
        self.assertNotIn("DUPLICATE_INHERITABLE_HANDLE", decision.transitions)
        self.assertEqual(decision.create_process_w, "NOT_REACHED")
        self.assertEqual(decision.inheritable_handle_duplicate, "NOT_REACHED")
        self.assertFalse(decision.execution_authorized)
        self.assertEqual(decision.launch_identity, "UNBOUND_AT_LAUNCH")
        self.assertEqual(decision.file_identity, "UNPROVED")
        self.assertEqual(decision.reparse, "UNINSPECTED")
        self.assertEqual(decision.n4, "OPEN")
        self.assertEqual(decision.n5, "OPEN")
        self.assertEqual(decision.ownership_exclusive, "OPEN")
        self.assertEqual(decision.operational_mingit_pin, "UNRATIFIED")
        self.assertFalse(decision.mingit_crt_compatible)
        self.assertFalse(decision.windows_environment_sort_closed)
        self.assertEqual(decision.plan_a, "NONLAUNCH")
        self.assertEqual(decision.plan_b, "UNSELECTED")
        self.assertEqual(decision.plan_c, "UNSELECTED")
        self.assertFalse(decision.full_inr_ready)

    def test_open_conditions_stay_unapproved(self) -> None:
        self.assertEqual(PLAN_A, "NONLAUNCH")
        self.assertEqual(PLAN_B, "UNSELECTED")
        self.assertEqual(PLAN_C, "UNSELECTED")
        self.assertEqual(N4, "OPEN")
        self.assertEqual(N5, "OPEN")
        self.assertEqual(OWNERSHIP_EXCLUSIVE, "OPEN")
        self.assertEqual(OPERATIONAL_MINGIT_PIN, "UNRATIFIED")
        self.assertEqual(LAUNCH_IDENTITY, "UNBOUND_AT_LAUNCH")
        self.assertEqual(FILE_IDENTITY_UNPROVED, "UNPROVED")
        self.assertEqual(REPARSE_UNINSPECTED, "UNINSPECTED")
        self.assertFalse(MINGIT_CRT_COMPATIBLE)
        self.assertFalse(WINDOWS_ENVIRONMENT_SORT_CLOSED)
        self.assertEqual(EXECUTION_BINDING_REAL, "UNEXECUTED")
        self.assertEqual(REAL_WINDOWS_EXECUTION, "NOT_AUTHORIZED")
        self.assertFalse(FULL_INR_READY)
        self.assertEqual(CREATE_PROCESS_W, "NOT_REACHED")
        self.assertEqual(INHERITABLE_HANDLE_DUPLICATE, "NOT_REACHED")

    def test_every_request_path_refuses_before_creation(self) -> None:
        cases = (
            None,
            [],
            _SENTINEL,
            {},
            {"schema_version": _SENTINEL, "operation_id": "VERSION"},
            {"schema_version": "her.limited_git.request.v0", "operation_id": _SENTINEL},
            {"schema_version": "her.limited_git.request.v0", "operation_id": "VERSION", "note": _SENTINEL},
            {_SENTINEL: "VERSION", "schema_version": "her.limited_git.request.v0"},
        )
        for request in cases:
            with self.subTest(request=type(request).__name__):
                decision = enter_plan_a_nonlaunch(request)
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.status, "REFUSED")
                self.assertEqual(decision.reason, "INPUT_REJECTED")
                self.assertIsNone(decision.environment_proposal)
                self.assertIsNone(decision.command_proposal)
                self.assertEqual(decision.transitions, ("RECEIVED", "REFUSED_BEFORE_CREATE"))

    def test_authority_claims_use_a_fixed_reason(self) -> None:
        request = _request()
        request["n4"] = "PASS"
        request["operational_mingit_pin"] = _SENTINEL
        decision = enter_plan_a_nonlaunch(request, _preparation())
        self.assert_refused_before_creation(decision)
        self.assertEqual(decision.reason, "AUTHORITY_CLAIM_REJECTED")
        self.assertIsNone(decision.environment_proposal)
        preparation = _preparation()
        preparation["launch_identity"] = "BOUND"
        decision = enter_plan_a_nonlaunch(_request(), preparation)
        self.assert_refused_before_creation(decision)
        self.assertEqual(decision.reason, "AUTHORITY_CLAIM_REJECTED")

    def test_missing_preparation_stays_unapproved(self) -> None:
        decision = enter_plan_a_nonlaunch(_request(), None)
        self.assert_refused_before_creation(decision)
        self.assertEqual(decision.status, "REFUSED")
        self.assertEqual(decision.reason, "POLICY_UNAPPROVED")
        self.assertEqual(
            decision.transitions,
            ("RECEIVED", "REQUEST_CLASSIFIED", "REFUSED_BEFORE_CREATE"),
        )

    def test_proposer_refusal_is_the_entry_reason(self) -> None:
        bad_env = {"PATH": _SENTINEL}
        decision = enter_plan_a_nonlaunch(_request(), _preparation(bad_env))
        self.assert_refused_before_creation(decision)
        self.assertEqual(
            decision.environment_proposal,
            propose_utf16le_environment_block(bad_env),
        )
        self.assertEqual(decision.reason, decision.environment_proposal.reason)
        self.assertEqual(decision.status, "REFUSED")
        bad_image = _SENTINEL
        decision = enter_plan_a_nonlaunch(_request(), _preparation(image=bad_image))
        self.assert_refused_before_creation(decision)
        self.assertEqual(
            decision.command_proposal,
            propose_ascii_command_line([bad_image, "--version"]),
        )
        self.assertEqual(decision.reason, "UNSUPPORTED_ARGV")
        self.assertEqual(decision.command_proposal.status, "REFUSED")

    def test_accepted_proposals_still_block_on_open_gates(self) -> None:
        operations = {
            "VERSION": ("--version",),
            "EXEC_PATH": ("--exec-path",),
            "CONFIG_SCOPES": ("config", "--list", "--show-scope", "-z"),
        }
        snapshot = _snapshot()
        for operation, suffix in operations.items():
            with self.subTest(operation=operation):
                decision = enter_plan_a_nonlaunch(_request(operation), _preparation(snapshot))
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.status, "BLOCKED")
                self.assertEqual(decision.reason, "UNCONFIRMED")
                self.assertEqual(
                    decision.environment_proposal,
                    propose_utf16le_environment_block(snapshot),
                )
                self.assertEqual(
                    decision.command_proposal,
                    propose_ascii_command_line([_IMAGE, *suffix]),
                )
                self.assertEqual(decision.environment_proposal.status, "PROPOSED")
                self.assertEqual(decision.command_proposal.status, "PROPOSED")
                self.assertFalse(decision.environment_proposal.execution_authorized)
                self.assertFalse(decision.command_proposal.execution_authorized)
                self.assertEqual(
                    decision.transitions,
                    (
                        "RECEIVED",
                        "REQUEST_CLASSIFIED",
                        "PROPOSALS_CONSULTED",
                        "REFUSED_BEFORE_CREATE",
                    ),
                )

    def test_schema_and_keys_reject_inexact_types_and_comparison_errors(self) -> None:
        class EqBoom:
            def __eq__(self, other: object) -> bool:
                raise RuntimeError(_SENTINEL)

        class EqTrue:
            def __eq__(self, other: object) -> bool:
                return True

        class Collide:
            def __hash__(self) -> int:
                return hash("schema_version")

            def __eq__(self, other: object) -> bool:
                return other == "schema_version"

        class SubStr(str):
            pass

        class HashOnce:
            def __init__(self) -> None:
                self.calls = 0

            def __hash__(self) -> int:
                self.calls += 1
                if self.calls > 1:
                    raise RuntimeError(_SENTINEL)
                return 1

            def __eq__(self, other: object) -> bool:
                return other is self

        requests = (
            {"schema_version": EqBoom(), "operation_id": "VERSION"},
            {"schema_version": EqTrue(), "operation_id": "VERSION"},
            {"schema_version": SubStr("her.limited_git.request.v0"), "operation_id": "VERSION"},
            {Collide(): "her.limited_git.request.v0", "operation_id": "VERSION"},
            {SubStr("schema_version"): "her.limited_git.request.v0", SubStr("operation_id"): "VERSION"},
            {"schema_version": "her.limited_git.request.v0", SubStr("operation_id"): "VERSION"},
            {"schema_version": "her.limited_git.request.v0", HashOnce(): "VERSION"},
            {"schema_version": "her.limited_git.request.v0", "operation_id": EqTrue()},
        )
        for request in requests:
            with self.subTest(request=tuple(type(key).__name__ for key in request)):
                decision = enter_plan_a_nonlaunch(request, _preparation())
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.reason, "INPUT_REJECTED")
                self.assertIsNone(decision.environment_proposal)
                self.assertIsNone(decision.command_proposal)

    def test_preparation_rejects_abnormal_types_and_keys(self) -> None:
        class OddKey:
            def __hash__(self) -> int:
                return 0

            def __eq__(self, other: object) -> bool:
                return other is self

        class Collide:
            def __hash__(self) -> int:
                return hash("image")

            def __eq__(self, other: object) -> bool:
                return other == "image"

        class SubStr(str):
            pass

        abnormal = ([], _SENTINEL, 1, b"image", object())
        for preparation in abnormal:
            with self.subTest(preparation=type(preparation).__name__):
                decision = enter_plan_a_nonlaunch(_request(), preparation)
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.status, "REFUSED")
                self.assertEqual(decision.reason, "INPUT_REJECTED")
                self.assertIsNone(decision.environment_proposal)
                self.assertIsNone(decision.command_proposal)
                self.assertEqual(
                    decision.transitions,
                    ("RECEIVED", "REQUEST_CLASSIFIED", "REFUSED_BEFORE_CREATE"),
                )
        bad_keys = (
            {"environment_snapshot": _snapshot()},
            {"environment_snapshot": _snapshot(), "image": _IMAGE, "note": _SENTINEL},
            {OddKey(): _snapshot(), "image": _IMAGE},
            {"environment_snapshot": _snapshot(), Collide(): _IMAGE},
            {SubStr("environment_snapshot"): _snapshot(), SubStr("image"): _IMAGE},
        )
        for preparation in bad_keys:
            with self.subTest(keys=tuple(type(key).__name__ for key in preparation)):
                decision = enter_plan_a_nonlaunch(_request(), preparation)
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.reason, "INPUT_REJECTED")
                self.assertIsNone(decision.environment_proposal)
                self.assertIsNone(decision.command_proposal)

    def test_image_rejects_non_str_and_ignores_input_arrays(self) -> None:
        supplied = [_IMAGE, "--version", _SENTINEL]
        images = (
            supplied,
            (_IMAGE, "--version"),
            _IMAGE.encode("ascii"),
            1,
            type("ImageStr", (str,), {})(_IMAGE),
        )
        for image in images:
            with self.subTest(image=type(image).__name__):
                decision = enter_plan_a_nonlaunch(_request(), _preparation(image=image))
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.reason, "INPUT_REJECTED")
                self.assertIsNone(decision.environment_proposal)
                self.assertIsNone(decision.command_proposal)
                self.assertNotEqual(
                    decision.command_proposal,
                    propose_ascii_command_line(supplied),
                )

    def test_path_matches_only_exact_image_parent_code_units(self) -> None:
        image = r"C:\tree\ucrt64\bin\git.exe"
        parent = r"C:\tree\ucrt64\bin"
        slash_image = "C:/tree/ucrt64/bin/git.exe"
        slash_parent = "C:/tree/ucrt64/bin"
        exact = (
            (image, parent),
            (slash_image, slash_parent),
        )
        for candidate, path in exact:
            with self.subTest(path=path):
                snapshot = _snapshot()
                snapshot["PATH"] = path
                decision = enter_plan_a_nonlaunch(
                    _request(),
                    _preparation(snapshot, candidate),
                )
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.status, "BLOCKED")
                self.assertEqual(decision.reason, "UNCONFIRMED")
                self.assertNotIn(path, decision.reason)
                self.assertNotIn(candidate, decision.reason)
        refused = (
            (image, r"C:\Tree\ucrt64\bin", "INCONSISTENT_VALUE"),
            (image, r"C:/tree/ucrt64/bin", "INCONSISTENT_VALUE"),
            (image, r"C:\other\ucrt64\bin", "INCONSISTENT_VALUE"),
            (image, parent + "\\", "INVALID_VALUE"),
            (image, r"tree\ucrt64\bin", "INVALID_VALUE"),
            (image, r"C:\tree\..\ucrt64\bin", "INVALID_VALUE"),
            (image, parent + r";C:\other\ucrt64\bin", "INVALID_VALUE"),
            (image, r"C:\tree\extra\ucrt64\bin", "INCONSISTENT_VALUE"),
            (r"C:\Tree\ucrt64\bin\git.exe", parent, "INCONSISTENT_VALUE"),
            (slash_image, parent, "INCONSISTENT_VALUE"),
            (r"C:\other\ucrt64\bin\git.exe", parent, "INCONSISTENT_VALUE"),
            (parent + "\\", parent, "UNSUPPORTED_ARGV"),
            (r"ucrt64\bin\git.exe", parent, "UNSUPPORTED_ARGV"),
            (r"C:\tree\..\ucrt64\bin\git.exe", parent, "UNSUPPORTED_ARGV"),
        )
        for candidate, path, reason in refused:
            with self.subTest(path=path, image=candidate, reason=reason):
                snapshot = _snapshot()
                snapshot["PATH"] = path
                decision = enter_plan_a_nonlaunch(
                    _request(),
                    _preparation(snapshot, candidate),
                )
                self.assert_refused_before_creation(decision)
                self.assertEqual(decision.status, "REFUSED")
                self.assertEqual(decision.reason, reason)
                self.assertNotIn(path, decision.reason)
                self.assertNotIn(candidate, decision.reason)

    def test_module_has_no_process_api(self) -> None:
        tree = ast.parse(_MODULE.read_text(encoding="utf-8"))
        imported: set[str] = set()
        calls: set[str] = set()
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
        self.assertEqual(imported, {"__future__", "typing", "docs"})
        public = [
            node.name
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ]
        self.assertEqual(public, ["enter_plan_a_nonlaunch"])
        self.assertTrue(calls.isdisjoint({
            "CreateProcessW",
            "DuplicateHandle",
            "Popen",
            "system",
            "WinDLL",
            "CDLL",
        }))


if __name__ == "__main__":
    unittest.main()
