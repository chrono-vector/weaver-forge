"""Fail-closed tests for the INR-HER-001 Phase 2B input and inventory gate."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_001.schema_check import check as schema_check
from docs.inr_her_001.supervisor_her_v1 import synthetic_event
from docs.inr_her_001.validate_her_v1 import ALLOWED_SCHEMA_KEYS
from docs.inr_her_002a.preflight_her_v1 import (
    CHECK_IDS as PHASE2A_CHECK_IDS,
    RESULT_SCHEMA as PHASE2A_RESULT_SCHEMA,
    evaluate_phase2a,
)
from docs.inr_her_002b.gate_her_v1 import (
    PHASE2B_CHECK_IDS,
    RESULT_SCHEMA,
    evaluate_phase2b,
    phase2a_inventory_errors,
    phase2b_inventory_errors,
)

PHASE2A_HUMAN_FINAL = "95ec95fd2273c303123ed5a42ba98a786ae0a679"
SUPPORTED_PRIVILEGES = ("ABSENT", "UNOBSERVED", "PRESENT_UNEXERCISED", "ENABLED")
PASS_CLAIMS = ("PASS", "HASH_AGREEMENT_ONLY", "FRESH", "ISOLATION_PASS", "FULL_INR_PASS")


class StrClaim(str):
    """Hashable string subclass. It is not an exact supported string type."""


def _quiet(**overrides) -> dict:
    observation = {
        "platform": "WINDOWS_X64",
        "python_version": "3.11.9",
        "python_executable": "C:/pinned/python.exe",
        "python_sha256_authenticated": False,
        "python_distribution_sha256": None,
        "mingit_version": "mingit-test",
        "mingit_executable": "C:/pinned/mingit/cmd/git.exe",
        "mingit_sha256_authenticated": False,
        "mingit_distribution_sha256": None,
        "git_execution_path": "C:/pinned/mingit/cmd/git.exe",
        "git_source": "UNEXPECTED",
        "git_config_closed": None,
        "privileges": "ABSENT",
    }
    observation.update(overrides)
    return observation


def _phase2a_copy() -> dict:
    return json.loads(json.dumps(evaluate_phase2a(synthetic_event(), _quiet())))


class Phase2BCommon(unittest.TestCase):
    def assert_blocked(self, result: dict, reason: str) -> None:
        self.assertEqual("BLOCKED", result["overall_status"])
        self.assertEqual(reason, result["overall_reason"])
        self.assertNotEqual("PASS", result["overall_status"])
        self.assertFalse(result["full_inr_ready"])
        self.assertFalse(result["human_final"])
        self.assertEqual("NOT_ESTABLISHED", result["isolation_evidence"])
        self.assertEqual("NOT_ESTABLISHED", result["schema_uniqueness"])
        self.assertEqual("RUNTIME", result["inventory_authority"])
        self.assertEqual("STOPPED", result["n1_phase1_edit"])
        self.assertEqual("UNEXECUTED", result["n2_binding"])
        self.assertTrue(all(item["status"] != "PASS" for item in result["checks"]))
        self.assertEqual([], schema_check(result, RESULT_SCHEMA))
        self.assertEqual((), phase2b_inventory_errors(result["checks"]))
        json.dumps(result)

    def assert_not_delegated(self, result: dict) -> None:
        self.assertFalse(result["phase2a_delegated"])
        self.assertEqual("NOT_DELEGATED", result["phase2a_overall_status"])
        self.assertEqual("NOT_RUN", result["n4_inventory"])
        self.assertEqual([], result["phase2a_checks"])


class Phase2BN3Tests(Phase2BCommon):
    def test_unhashable_and_unsupported_privileges_are_structured_refusals(self) -> None:
        values = (
            [],
            ["ENABLED"],
            {},
            {"ENABLED"},
            set(),
            {"ENABLED"},
            bytearray(b"ENABLED"),
            ("ENABLED",),
            ("ABSENT",),
            None,
            1,
            True,
            False,
            b"ABSENT",
            "enabled",
            "ABSENT ",
            "MAYBE",
            "",
            StrClaim("ABSENT"),
        )
        seen = []
        for value in values:
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a") as gate:
                gate.side_effect = AssertionError("phase2a delegated")
                result = evaluate_phase2b(synthetic_event(), _quiet(privileges=value))
            self.assertFalse(gate.called)
            self.assert_blocked(result, "HER_PRIVILEGE_INPUT_REJECTED")
            self.assert_not_delegated(result)
            self.assertEqual("REJECTED", result["n3_privileges"])
            self.assertEqual("ACCEPTED", result["n3_claimed_status"])
            seen.append(json.dumps(result, sort_keys=True))
        self.assertEqual(1, len(set(seen)))

    def test_unhashable_claimed_status_is_not_a_missing_claim(self) -> None:
        values = (
            [],
            ["PASS"],
            {},
            {"PASS": True},
            set(),
            {"PASS"},
            ("PASS",),
            None,
            1,
            True,
            b"PASS",
            bytearray(b"PASS"),
            StrClaim("PASS"),
        )
        for value in values:
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a") as gate:
                gate.side_effect = AssertionError("phase2a delegated")
                result = evaluate_phase2b(synthetic_event(), _quiet(claimed_status=value))
            self.assertFalse(gate.called)
            self.assert_blocked(result, "HER_CLAIMED_STATUS_INPUT_REJECTED")
            self.assert_not_delegated(result)
            self.assertEqual("ACCEPTED", result["n3_privileges"])
            self.assertEqual("REJECTED", result["n3_claimed_status"])
            self.assertNotEqual("HER_NO_PASS_CLAIM", result["overall_reason"])
            self.assertNotIn("PASS", result["overall_reason"])

    def test_non_dict_observation_is_not_coerced(self) -> None:
        for value in ([], set(), "ABSENT", 1, True, b"{}"):
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a") as gate:
                gate.side_effect = AssertionError("phase2a delegated")
                result = evaluate_phase2b(synthetic_event(), value)
            self.assertFalse(gate.called)
            self.assert_blocked(result, "HER_OBSERVATION_INPUT_REJECTED")
            self.assert_not_delegated(result)
            self.assertEqual("REJECTED", result["n3_privileges"])
            self.assertEqual("REJECTED", result["n3_claimed_status"])

    def test_privilege_rejection_outranks_a_bad_claim(self) -> None:
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a") as gate:
            result = evaluate_phase2b(
                synthetic_event(),
                _quiet(privileges=["ENABLED"], claimed_status=["PASS"]),
            )
        self.assertFalse(gate.called)
        self.assert_blocked(result, "HER_PRIVILEGE_INPUT_REJECTED")
        self.assertEqual("REJECTED", result["n3_privileges"])
        self.assertEqual("REJECTED", result["n3_claimed_status"])

    def test_phase2a_exception_stays_structured(self) -> None:
        with mock.patch(
            "docs.inr_her_002b.gate_her_v1.evaluate_phase2a",
            side_effect=TypeError("cannot use 'list' as a set element"),
        ):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_UNSTRUCTURED_ERROR")
        self.assert_not_delegated(result)
        self.assertNotIn("list", json.dumps(result))


class Phase2BN4Tests(Phase2BCommon):
    def test_schema_vocabulary_cannot_state_uniqueness(self) -> None:
        self.assertNotIn("uniqueItems", ALLOWED_SCHEMA_KEYS)
        self.assertNotIn("maxItems", ALLOWED_SCHEMA_KEYS)
        self.assertNotIn("uniqueItems", json.dumps(PHASE2A_RESULT_SCHEMA))
        self.assertNotIn("uniqueItems", json.dumps(RESULT_SCHEMA))

    def test_repeated_phase2a_checks_are_schema_valid_and_runtime_rejected(self) -> None:
        mutated = _phase2a_copy()
        mutated["checks"] = [mutated["checks"][0]] * len(PHASE2A_CHECK_IDS)
        self.assertEqual([], schema_check(mutated, PHASE2A_RESULT_SCHEMA))
        self.assertIn("repeated", phase2a_inventory_errors(mutated["checks"]))
        self.assertIn("missing", phase2a_inventory_errors(mutated["checks"]))
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_CHECK_INVENTORY_REJECTED")
        self.assertTrue(result["phase2a_delegated"])
        self.assertEqual("REJECTED", result["n4_inventory"])
        self.assertEqual([], result["phase2a_checks"])

    def test_reordered_checks_are_schema_valid_and_runtime_rejected(self) -> None:
        mutated = _phase2a_copy()
        mutated["checks"] = list(reversed(mutated["checks"]))
        self.assertEqual([], schema_check(mutated, PHASE2A_RESULT_SCHEMA))
        self.assertIn("unexpected", phase2a_inventory_errors(mutated["checks"]))
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_CHECK_INVENTORY_REJECTED")

    def test_unexpected_missing_and_malformed_checks_are_rejected(self) -> None:
        unexpected = _phase2a_copy()
        unexpected["checks"][0]["check_id"] = "isolation_pass"
        missing = _phase2a_copy()
        missing["checks"] = missing["checks"][:-1]
        item = _phase2a_copy()
        item["checks"][0] = ["privileges"]
        extra = _phase2a_copy()
        extra["checks"][0]["extra"] = "x"
        blank = _phase2a_copy()
        blank["checks"][0]["reason"] = ""
        passed = _phase2a_copy()
        passed["checks"][0]["status"] = "PASS"
        not_list = _phase2a_copy()
        not_list["checks"] = {entry["check_id"]: entry for entry in not_list["checks"]}
        for mutated in (unexpected, missing, item, extra, blank, passed, not_list):
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
                result = evaluate_phase2b(synthetic_event(), _quiet())
            self.assert_blocked(result, "HER_CHECK_INVENTORY_REJECTED")
            self.assertEqual("REJECTED", result["n4_inventory"])
            self.assertEqual([], result["phase2a_checks"])

    def test_pass_status_with_a_unique_inventory_is_not_accepted(self) -> None:
        mutated = _phase2a_copy()
        mutated["overall_status"] = "PASS"
        self.assertEqual((), phase2a_inventory_errors(mutated["checks"]))
        self.assertTrue(schema_check(mutated, PHASE2A_RESULT_SCHEMA))
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_PASS_FORBIDDEN")
        self.assertTrue(result["phase2a_delegated"])
        self.assertEqual("ACCEPTED", result["n4_inventory"])
        self.assertEqual([], result["phase2a_checks"])
        self.assertEqual("BLOCKED", result["phase2a_overall_status"])

    def test_non_inventory_schema_defect_stays_distinct(self) -> None:
        mutated = _phase2a_copy()
        mutated["pins"]["python_pin_status"] = "RATIFIED"
        self.assertEqual((), phase2a_inventory_errors(mutated["checks"]))
        self.assertTrue(schema_check(mutated, PHASE2A_RESULT_SCHEMA))
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_REJECTED")
        self.assertEqual("ACCEPTED", result["n4_inventory"])
        self.assertEqual([], result["phase2a_checks"])

    def test_phase2b_schema_also_allows_duplicate_checks(self) -> None:
        accepted = evaluate_phase2b(synthetic_event(), _quiet())
        mutated = json.loads(json.dumps(accepted))
        mutated["checks"] = [mutated["checks"][0]] * len(PHASE2B_CHECK_IDS)
        self.assertEqual([], schema_check(mutated, RESULT_SCHEMA))
        self.assertIn("repeated", phase2b_inventory_errors(mutated["checks"]))
        self.assertEqual((), phase2b_inventory_errors(accepted["checks"]))


class Phase2BCompatibilityTests(Phase2BCommon):
    def assert_preserves(self, observation: dict, freshness: object = None) -> None:
        event = synthetic_event()
        expected = evaluate_phase2a(event, observation, freshness)
        actual = evaluate_phase2b(event, observation, freshness)
        self.assertEqual(expected["overall_status"], actual["overall_status"])
        self.assertEqual(expected["overall_reason"], actual["overall_reason"])
        self.assertEqual(expected["checks"], actual["phase2a_checks"])
        self.assertEqual(expected["overall_status"], actual["phase2a_overall_status"])
        self.assertEqual(expected["overall_reason"], actual["phase2a_overall_reason"])
        self.assertTrue(actual["phase2a_delegated"])
        self.assertEqual("ACCEPTED", actual["n3_privileges"])
        self.assertEqual("ACCEPTED", actual["n3_claimed_status"])
        self.assertEqual("ACCEPTED", actual["n4_inventory"])
        self.assertIn(actual["overall_status"], {"FAIL", "BLOCKED", "UNCONFIRMED"})
        self.assertEqual([], schema_check(actual, RESULT_SCHEMA))
        self.assertEqual((), phase2b_inventory_errors(actual["checks"]))
        self.assertFalse(actual["full_inr_ready"])
        self.assertEqual("NOT_ESTABLISHED", actual["isolation_evidence"])

    def test_supported_privilege_values_delegate(self) -> None:
        for value in SUPPORTED_PRIVILEGES:
            self.assert_preserves(_quiet(privileges=value))

    def test_omitted_observation_and_omitted_fields_delegate(self) -> None:
        self.assert_preserves(_quiet())
        omitted = _quiet()
        del omitted["privileges"]
        self.assert_preserves(omitted)
        self.assertEqual(
            evaluate_phase2a(synthetic_event(), None)["overall_reason"],
            evaluate_phase2b(synthetic_event(), None)["overall_reason"],
        )
        self.assertTrue(evaluate_phase2b(synthetic_event(), None)["phase2a_delegated"])

    def test_string_claims_delegate_and_do_not_pass(self) -> None:
        for value in PASS_CLAIMS + ("no", ""):
            actual_event = synthetic_event()
            expected = evaluate_phase2a(actual_event, _quiet(claimed_status=value))
            actual = evaluate_phase2b(actual_event, _quiet(claimed_status=value))
            self.assertEqual(expected["overall_status"], actual["overall_status"])
            self.assertEqual(expected["overall_reason"], actual["overall_reason"])
            self.assertNotEqual("PASS", actual["overall_status"])
            self.assertTrue(actual["phase2a_delegated"])

    def test_n1_unhashable_version_still_delegates_only_to_phase2a(self) -> None:
        event = {"schema_version": [], "event_id": "evt-1"}
        with mock.patch("docs.inr_her_002a.preflight_her_v1.evaluate_event") as phase1:
            phase1.side_effect = AssertionError("phase1 called")
            result = evaluate_phase2b(event, _quiet())
        self.assertFalse(phase1.called)
        expected = evaluate_phase2a(event, _quiet())
        self.assertEqual("NOT_DELEGATED", expected["phase1_overall_status"])
        self.assertEqual(expected["overall_status"], result["overall_status"])
        self.assertEqual(expected["overall_reason"], result["overall_reason"])
        self.assertEqual("HER_SCHEMA_VERSION", result["overall_reason"])
        self.assertTrue(result["phase2a_delegated"])
        self.assertEqual("STOPPED", result["n1_phase1_edit"])

    def test_hash_agreement_is_not_freshness(self) -> None:
        event = synthetic_event()
        result = evaluate_phase2b(event, _quiet(), {})
        self.assertEqual("HER_FRESHNESS_UNPROVEN", evaluate_phase2a(event, _quiet(), {})["checks"][9]["reason"])
        freshness = [item for item in result["phase2a_checks"] if item["check_id"] == "event_freshness"]
        self.assertEqual(1, len(freshness))
        self.assertEqual("HER_FRESHNESS_UNPROVEN", freshness[0]["reason"])
        self.assertNotEqual("HASH_AGREEMENT_ONLY", result["overall_reason"])
        self.assertEqual("UNEXECUTED", result["n2_binding"])


class Phase2BRepairTests(Phase2BCommon):
    def test_m1_top_level_non_string_key_is_structured(self) -> None:
        mutated = _phase2a_copy()
        mutated[1] = "M1-TOP-SENTINEL"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_REJECTED")
        self.assertTrue(result["phase2a_delegated"])
        self.assertEqual("ACCEPTED", result["n4_inventory"])
        self.assertEqual([], result["phase2a_checks"])
        self.assertNotIn("M1-TOP-SENTINEL", json.dumps(result))

    def test_m1_nested_non_string_keys_are_structured(self) -> None:
        pins = _phase2a_copy()
        pins["pins"][None] = "M1-PINS-SENTINEL"
        checks = _phase2a_copy()
        checks["checks"][0][b"extra"] = "M1-CHECK-SENTINEL"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=pins):
            pin_result = evaluate_phase2b(synthetic_event(), _quiet())
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=checks):
            check_result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(pin_result, "HER_PHASE2A_RESULT_REJECTED")
        self.assertEqual([], pin_result["phase2a_checks"])
        self.assertNotIn("M1-PINS-SENTINEL", json.dumps(pin_result))
        self.assert_blocked(check_result, "HER_CHECK_INVENTORY_REJECTED")
        self.assertEqual("REJECTED", check_result["n4_inventory"])
        self.assertNotIn("M1-CHECK-SENTINEL", json.dumps(check_result))
        self.assertNotEqual("PASS", pin_result["overall_status"])
        self.assertNotEqual("PASS", check_result["overall_status"])

    def test_nm1_fail_check_cannot_carry_unconfirmed_overall(self) -> None:
        mutated = _phase2a_copy()
        mutated["checks"][10]["status"] = "FAIL"
        mutated["checks"][10]["reason"] = "HER_CONTRADICTION"
        mutated["overall_status"] = "UNCONFIRMED"
        mutated["overall_reason"] = "HER_NO_PASS_CLAIM"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_CONTRADICTION")
        self.assertEqual("ACCEPTED", result["n4_inventory"])
        self.assertEqual([], result["phase2a_checks"])

    def test_nm1_pass_like_reason_is_not_rank_consistent_acceptance(self) -> None:
        mutated = _phase2a_copy()
        mutated["phase1_overall_status"] = "BLOCKED"
        mutated["phase1_overall_reason"] = "HASH_AGREEMENT_ONLY"
        mutated["overall_status"] = "BLOCKED"
        mutated["overall_reason"] = "HASH_AGREEMENT_ONLY"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_CONTRADICTION")
        self.assertNotIn("HASH_AGREEMENT_ONLY", json.dumps(result))
        self.assertNotEqual("PASS", result["overall_status"])

    def test_nm1_impossible_check_pair_is_rejected(self) -> None:
        mutated = _phase2a_copy()
        mutated["checks"][3]["status"] = "UNCONFIRMED"
        mutated["checks"][3]["reason"] = "HER_PYTHON_PIN_PENDING"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_CONTRADICTION")
        self.assertEqual([], result["phase2a_checks"])

    def test_nm1_legal_nonwinning_check_edit_stays_compatible(self) -> None:
        event = synthetic_event()
        observation = _quiet()
        expected = evaluate_phase2a(event, observation)
        forged = json.loads(json.dumps(expected))
        forged["checks"][8]["reason"] = "HER_GIT_CONFIG_UNCLOSED"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=forged):
            result = evaluate_phase2b(event, observation)
        self.assertEqual(forged["overall_status"], result["overall_status"])
        self.assertEqual(forged["overall_reason"], result["overall_reason"])
        self.assertEqual(forged["checks"], result["phase2a_checks"])
        self.assertNotEqual("PASS", result["overall_status"])


class _CollidingKey:
    """Dict key whose hash collides with a string and whose equality can raise."""

    def __init__(self, target: str, exc: type[BaseException]) -> None:
        self._target = target
        self._exc = exc
        self.armed = False

    def __hash__(self) -> int:
        return hash(self._target)

    def __eq__(self, other: object) -> bool:
        if self.armed:
            raise self._exc("R3-BOOM")
        return False


def _collide(mapping: dict, target: str, exc: type[BaseException], sentinel: str) -> None:
    key = _CollidingKey(target, exc)
    mapping[key] = sentinel
    key.armed = True


class Phase2BR3Tests(Phase2BCommon):
    def test_r3_m1_top_level_colliding_keys_are_structured(self) -> None:
        for exc in (TypeError, ValueError, RecursionError):
            only = {}
            _collide(only, "overall_status", exc, "R3-TOP-ONLY")
            alongside = _phase2a_copy()
            _collide(alongside, "overall_status", exc, "R3-TOP-ALONGSIDE")
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=only):
                only_result = evaluate_phase2b(synthetic_event(), _quiet())
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=alongside):
                alongside_result = evaluate_phase2b(synthetic_event(), _quiet())
            self.assert_blocked(only_result, "HER_PHASE2A_RESULT_REJECTED")
            self.assertEqual("REJECTED", only_result["n4_inventory"])
            self.assert_blocked(alongside_result, "HER_PHASE2A_RESULT_REJECTED")
            self.assertEqual("ACCEPTED", alongside_result["n4_inventory"])
            for result in (only_result, alongside_result):
                encoded = json.dumps(result)
                self.assertNotIn("R3-TOP", encoded)
                self.assertNotIn("R3-BOOM", encoded)
                self.assertEqual([], result["phase2a_checks"])
                self.assertNotEqual("PASS", result["overall_status"])

    def test_r3_m1_nested_colliding_keys_are_structured(self) -> None:
        for exc in (TypeError, ValueError, RecursionError):
            pins = _phase2a_copy()
            _collide(pins["pins"], "python_pin_status", exc, "R3-PINS")
            checks = _phase2a_copy()
            _collide(checks["checks"][0], "check_id", exc, "R3-CHECK")
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=pins):
                pin_result = evaluate_phase2b(synthetic_event(), _quiet())
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=checks):
                check_result = evaluate_phase2b(synthetic_event(), _quiet())
            self.assert_blocked(pin_result, "HER_PHASE2A_RESULT_REJECTED")
            self.assertEqual("ACCEPTED", pin_result["n4_inventory"])
            self.assert_blocked(check_result, "HER_PHASE2A_RESULT_REJECTED")
            self.assertEqual("REJECTED", check_result["n4_inventory"])
            for result, sentinel in ((pin_result, "R3-PINS"), (check_result, "R3-CHECK")):
                encoded = json.dumps(result)
                self.assertNotIn(sentinel, encoded)
                self.assertNotIn("R3-BOOM", encoded)
                self.assertEqual([], result["phase2a_checks"])
                self.assertNotEqual("PASS", result["overall_status"])

    def test_r3_m2_observation_colliding_keys_are_rejected_before_delegation(self) -> None:
        cases = []
        for exc in (TypeError, ValueError, RecursionError):
            privileges_only = _quiet()
            del privileges_only["privileges"]
            _collide(privileges_only, "privileges", exc, "R3-OBS-PRIV")
            claimed = _quiet()
            _collide(claimed, "claimed_status", exc, "R3-OBS-CLAIM")
            alongside = _quiet()
            _collide(alongside, "privileges", exc, "R3-OBS-BOTH")
            cases.extend((privileges_only, claimed, alongside))
        for observation in cases:
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a") as gate:
                gate.side_effect = AssertionError("phase2a delegated")
                result = evaluate_phase2b(synthetic_event(), observation)
            self.assertFalse(gate.called)
            self.assert_blocked(result, "HER_OBSERVATION_INPUT_REJECTED")
            self.assert_not_delegated(result)
            self.assertEqual("REJECTED", result["n3_privileges"])
            self.assertEqual("REJECTED", result["n3_claimed_status"])
            encoded = json.dumps(result)
            self.assertNotIn("R3-OBS", encoded)
            self.assertNotIn("R3-BOOM", encoded)
            self.assertNotEqual("PASS", result["overall_status"])

    def test_r3_json_shaped_input_stays_compatible(self) -> None:
        event = synthetic_event()
        observation = _quiet()
        expected = evaluate_phase2a(event, observation)
        direct = evaluate_phase2b(event, observation)
        forged = json.loads(json.dumps(expected))
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=forged):
            replayed = evaluate_phase2b(event, json.loads(json.dumps(observation)))
        for result in (direct, replayed):
            self.assertEqual(expected["overall_status"], result["overall_status"])
            self.assertEqual(expected["overall_reason"], result["overall_reason"])
            self.assertEqual(expected["checks"], result["phase2a_checks"])
            self.assertNotEqual("PASS", result["overall_status"])
            self.assertTrue(result["phase2a_delegated"])
            self.assertEqual("ACCEPTED", result["n4_inventory"])

    def test_r3_base_exceptions_still_propagate(self) -> None:
        for exc in (SystemExit, KeyboardInterrupt):
            forged = {}
            _collide(forged, "overall_status", exc, "R3-BASE")
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=forged):
                with self.assertRaises(exc):
                    evaluate_phase2b(synthetic_event(), _quiet())


class Phase2BR4Tests(Phase2BCommon):
    def test_r4_rejected_inventory_does_not_copy_untrusted_fields(self) -> None:
        leaked = ("ISOLATION_PASS", "FULL_INR_PASS", "PASS", "HASH_AGREEMENT_ONLY", "R4-ARBITRARY-SENTINEL")
        for reason in leaked:
            for status in ("FAIL", "BLOCKED", "UNCONFIRMED", "PASS"):
                mutated = _phase2a_copy()
                mutated["checks"] = mutated["checks"][:-1]
                mutated["overall_status"] = status
                mutated["overall_reason"] = reason
                with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
                    result = evaluate_phase2b(synthetic_event(), _quiet())
                self.assert_blocked(result, "HER_CHECK_INVENTORY_REJECTED")
                self.assertEqual("REJECTED", result["n4_inventory"])
                self.assertEqual("BLOCKED", result["phase2a_overall_status"])
                self.assertEqual("HER_CHECK_INVENTORY_REJECTED", result["phase2a_overall_reason"])
                self.assertEqual([], result["phase2a_checks"])
                self.assertNotIn(reason, json.dumps(result))

    def test_r4_rejected_schema_does_not_copy_untrusted_fields(self) -> None:
        for reason in ("ISOLATION_PASS", "FULL_INR_PASS", "PASS", "HASH_AGREEMENT_ONLY", "R4-SCHEMA-SENTINEL"):
            mutated = _phase2a_copy()
            mutated["pins"]["python_pin_status"] = "RATIFIED"
            mutated["overall_status"] = "FAIL"
            mutated["overall_reason"] = reason
            with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
                result = evaluate_phase2b(synthetic_event(), _quiet())
            self.assert_blocked(result, "HER_PHASE2A_RESULT_REJECTED")
            self.assertEqual("ACCEPTED", result["n4_inventory"])
            self.assertEqual("BLOCKED", result["phase2a_overall_status"])
            self.assertEqual("HER_PHASE2A_RESULT_REJECTED", result["phase2a_overall_reason"])
            self.assertEqual([], result["phase2a_checks"])
            self.assertNotIn(reason, json.dumps(result))
            self.assertNotIn("FAIL", json.dumps(result["phase2a_overall_status"]))

    def test_r4_hostile_nested_key_does_not_copy_phase2a_reason(self) -> None:
        mutated = _phase2a_copy()
        mutated["overall_status"] = "UNCONFIRMED"
        mutated["overall_reason"] = "FULL_INR_PASS"
        _collide(mutated["pins"], "python_pin_status", ValueError, "R4-HOSTILE-VALUE")
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_REJECTED")
        self.assertEqual("ACCEPTED", result["n4_inventory"])
        self.assertEqual("BLOCKED", result["phase2a_overall_status"])
        self.assertEqual("HER_PHASE2A_RESULT_REJECTED", result["phase2a_overall_reason"])
        encoded = json.dumps(result)
        self.assertNotIn("FULL_INR_PASS", encoded)
        self.assertNotIn("UNCONFIRMED", result["phase2a_overall_status"])
        self.assertNotIn("UNCONFIRMED", result["phase2a_overall_reason"])
        self.assertNotIn("R4-HOSTILE-VALUE", encoded)
        self.assertNotIn("R3-BOOM", encoded)

    def test_r4_invalid_status_reason_combination_is_not_copied(self) -> None:
        mutated = _phase2a_copy()
        mutated["overall_status"] = "UNCONFIRMED"
        mutated["overall_reason"] = "ISOLATION_PASS"
        with mock.patch("docs.inr_her_002b.gate_her_v1.evaluate_phase2a", return_value=mutated):
            result = evaluate_phase2b(synthetic_event(), _quiet())
        self.assert_blocked(result, "HER_PHASE2A_RESULT_CONTRADICTION")
        self.assertEqual("BLOCKED", result["phase2a_overall_status"])
        self.assertEqual("HER_PHASE2A_RESULT_CONTRADICTION", result["phase2a_overall_reason"])
        self.assertNotIn("ISOLATION_PASS", json.dumps(result))
        self.assertNotIn("UNCONFIRMED", result["phase2a_overall_status"])
        self.assertNotIn("UNCONFIRMED", result["phase2a_overall_reason"])

    def test_r4_accepted_phase2a_result_is_unchanged(self) -> None:
        event = synthetic_event()
        observation = _quiet()
        expected = evaluate_phase2a(event, observation)
        result = evaluate_phase2b(event, observation)
        self.assertEqual(expected["overall_status"], result["overall_status"])
        self.assertEqual(expected["overall_reason"], result["overall_reason"])
        self.assertEqual(expected["overall_status"], result["phase2a_overall_status"])
        self.assertEqual(expected["overall_reason"], result["phase2a_overall_reason"])
        self.assertEqual(expected["checks"], result["phase2a_checks"])
        self.assertNotEqual("PASS", result["overall_status"])

    def test_r4_seal_failure_still_propagates(self) -> None:
        with mock.patch(
            "docs.inr_her_002b.gate_her_v1.phase2b_inventory_errors",
            return_value=("malformed",),
        ):
            with self.assertRaises(RuntimeError) as caught:
                evaluate_phase2b(synthetic_event(), _quiet())
        self.assertIn("phase 2B check inventory drifted", str(caught.exception))


class Phase2BPreservationTests(unittest.TestCase):
    def test_accepted_phase1_phase2a_and_r3_bytes_are_unchanged(self) -> None:
        completed = subprocess.run(
            [
                "git", "diff", "--exit-code", PHASE2A_HUMAN_FINAL, "--",
                "docs/inr_her_001", "docs/inr_her_002a", "docs/inr_001",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_phase2b_inventory_names_are_exact(self) -> None:
        self.assertEqual(
            (
                "n3_privileges",
                "n3_claimed_status",
                "n4_check_inventory",
                "phase2a_delegation",
                "isolation_boundary",
            ),
            PHASE2B_CHECK_IDS,
        )


if __name__ == "__main__":
    unittest.main()
