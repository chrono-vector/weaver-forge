"""P0 adversarial and false-green controls for INR-HER-001 Phase 1.

Privileged Windows observations are asserted UNVERIFIED. They are not executed.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_001.schema_check import check as schema_check
from docs.inr_her_001.collect_bundle_her_v1 import collect_export
from docs.inr_her_001.supervisor_her_v1 import (
    RATIFIED_GIT_SHA256,
    classify_git_pin,
    evaluate_event,
    synthetic_event,
)
from docs.inr_her_001 import supervisor_her_v1 as supervisor


def _by_id(result: dict) -> dict[str, dict]:
    return {item["predicate_id"]: item for item in result["predicates"]}


def _closed(test: unittest.TestCase, event: object) -> tuple[dict, dict]:
    result = evaluate_event(event)
    test.assertNotEqual(result["overall_status"], "PASS")
    found = _by_id(result)
    test.assertNotEqual(found["all_writer_isolation_bounded_v1"]["status"], "PASS")
    test.assertEqual(result["phase1_ceiling"], "ISOLATION_PASS_UNAVAILABLE")
    test.assertEqual(
        result["privileged_tests"],
        {"token": "UNVERIFIED", "job": "UNVERIFIED", "acl": "UNVERIFIED", "git_ownership": "UNVERIFIED"},
    )
    return result, found


def _role(event: dict, role: str) -> dict:
    for record in event["surface_records"]:
        if record["surface_role"] == role:
            return record
    raise AssertionError(role)


def _origin(origin: str) -> dict:
    event = synthetic_event()
    event["supervisor_result"]["evidence_origin"] = origin
    for record in event["surface_records"]:
        record["evidence_origin"] = origin
    return event


class AdversarialHerTests(unittest.TestCase):
    def test_granted_u_write_fails(self) -> None:
        event = synthetic_event()
        event["surface_records"][0]["u_write_denied"] = False
        result, found = _closed(self, event)
        self.assertEqual(result["overall_status"], "FAIL")
        self.assertEqual(result["overall_reason"], "HER_U_WRITE_GRANTED")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_U_WRITE_GRANTED")

    def test_missing_surface_record_is_unconfirmed(self) -> None:
        event = synthetic_event()
        event["surface_records"] = [record for record in event["surface_records"] if record["surface_role"] != "ledger"]
        result, found = _closed(self, event)
        self.assertEqual(found["her_u_vs_p"]["status"], "UNCONFIRMED")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_SURFACE_RECORD_ABSENT")
        self.assertEqual(found["her_surface_hash_agreement"]["reason"], "HER_SURFACE_RECORD_ABSENT")
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_PYTHON_PIN_PENDING")

    def test_staged_validator_swap_fails(self) -> None:
        event = synthetic_event()
        _role(event, "staged_validator")["post_sha256"] = "cd" * 32
        result, found = _closed(self, event)
        self.assertEqual(result["overall_reason"], "HER_SURFACE_MUTATED")
        self.assertEqual(found["her_surface_hash_agreement"]["status"], "FAIL")

    def test_planted_runtime_in_interpreter_and_git_tree_fails(self) -> None:
        event = synthetic_event()
        _role(event, "interpreter_tree")["planted_runtime"] = True
        _role(event, "git_runtime_tree")["planted_runtime"] = True
        result, _found = _closed(self, event)
        self.assertEqual(result["overall_status"], "FAIL")
        self.assertEqual(result["overall_reason"], "HER_SURFACE_MUTATED")

    def test_planted_runtime_in_execution_cwd_fails(self) -> None:
        event = synthetic_event()
        _role(event, "execution_cwd")["planted_runtime"] = True
        result, _found = _closed(self, event)
        self.assertEqual(result["overall_reason"], "HER_SURFACE_MUTATED")

    def test_git_config_self_test_claim_does_not_pass(self) -> None:
        unverified = synthetic_event()
        _result, found = _closed(self, unverified)
        self.assertNotEqual(found["her_git_config_closed"]["status"], "PASS")

        failed = synthetic_event()
        failed["supervisor_result"]["git_config_self_test"] = "FAILED"
        failed_result, _found = _closed(self, failed)
        self.assertEqual(failed_result["overall_reason"], "HER_GIT_CONFIG_SELF_TEST_FAILED")

        claimed = synthetic_event()
        claimed["supervisor_result"]["git_config_self_test"] = "CLAIMED_PASS"
        claimed_result, _found = _closed(self, claimed)
        self.assertEqual(claimed_result["overall_status"], "FAIL")
        self.assertEqual(claimed_result["overall_reason"], "HER_CONTRADICTION")

    def test_git_config_outside_closure_fails(self) -> None:
        event = synthetic_event()
        event["supervisor_result"]["config_outside_closure"] = True
        result, found = _closed(self, event)
        self.assertEqual(result["overall_reason"], "HER_GIT_CONFIG_SCOPE_OPEN")
        self.assertEqual(found["her_git_config_closed"]["reason"], "HER_GIT_CONFIG_SCOPE_OPEN")

    def test_snapshot_extra_entries_fail(self) -> None:
        event = synthetic_event()
        _role(event, "git_snapshot")["extra_entries"] = True
        result, found = _closed(self, event)
        self.assertEqual(result["overall_reason"], "HER_SURFACE_MUTATED")
        self.assertEqual(found["her_git_snapshot_sole_source"]["status"], "FAIL")
        self.assertEqual(found["her_git_snapshot_sole_source"]["reason"], "HER_GIT_SOURCE_NOT_SNAPSHOT")

    def test_live_checkout_git_fails_while_snapshot_exists(self) -> None:
        event = synthetic_event()
        self.assertIn("git_snapshot", {record["surface_role"] for record in event["surface_records"]})
        event["supervisor_result"]["uses_live_checkout_git"] = True
        result, found = _closed(self, event)
        self.assertEqual(result["overall_reason"], "HER_GIT_SOURCE_NOT_SNAPSHOT")
        self.assertEqual(found["her_git_snapshot_sole_source"]["reason"], "HER_GIT_SOURCE_NOT_SNAPSHOT")

    def test_job_breakaway_fails_and_privilege_stays_unverified(self) -> None:
        for field, value in (
            ("breakaway_requested", True),
            ("child_in_job", "OUTSIDE"),
            ("job_observation", "BREAKAWAY"),
        ):
            event = synthetic_event()
            event["supervisor_result"][field] = value
            result, found = _closed(self, event)
            self.assertEqual(result["overall_reason"], "HER_JOB_ESCAPE", field)
            self.assertEqual(found["her_child_contained"]["reason"], "HER_JOB_ESCAPE")
            self.assertEqual(result["privileged_tests"]["job"], "UNVERIFIED")

    def test_runner_flags_do_not_pass(self) -> None:
        flagged = synthetic_event()
        flagged["runner_flags"] = ["RUNNER_ISOLATED"]
        result, found = _closed(self, flagged)
        self.assertEqual(found["her_u_vs_p"]["status"], "UNCONFIRMED")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_RUNNER_FLAG_ONLY")
        self.assertEqual(result["overall_status"], "BLOCKED")

        claiming = synthetic_event()
        claiming["runner_flags"] = ["ISOLATION_PASS"]
        claimed, found = _closed(self, claiming)
        self.assertEqual(claimed["overall_status"], "FAIL")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_CONTRADICTION")

        empty = {"schema_version": "inr.event.v0.r4", "event_id": "evt-flags", "runner_flags": ["ISOLATION_PASS"]}
        refused, _found = _closed(self, empty)
        self.assertNotEqual(refused["overall_status"], "PASS")

    def test_forged_origin_fails(self) -> None:
        result, found = _closed(self, _origin("FORGED"))
        self.assertEqual(result["overall_status"], "FAIL")
        self.assertEqual(result["overall_reason"], "HER_FORGED_EVIDENCE")
        self.assertEqual(found["her_surface_hash_agreement"]["reason"], "HER_FORGED_EVIDENCE")

    def test_historical_r3_origin_does_not_satisfy_r4(self) -> None:
        result, found = _closed(self, _origin("HISTORICAL_R3"))
        self.assertEqual(found["her_surface_hash_agreement"]["status"], "UNCONFIRMED")
        self.assertEqual(found["her_surface_hash_agreement"]["reason"], "HER_HISTORICAL_R3")
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertNotEqual(found["her_surface_hash_agreement"]["status"], "PASS")

    def test_child_restriction_claims_do_not_pass(self) -> None:
        other = synthetic_event()
        other["supervisor_result"]["child_sid"] = "S-1-5-99"
        other["supervisor_result"]["child_integrity_claim"] = "OTHER"
        other_result, _found = _closed(self, other)
        self.assertEqual(other_result["overall_reason"], "HER_CHILD_TOKEN_NOT_RESTRICTED")

        low = synthetic_event()
        low["supervisor_result"]["child_sid"] = "S-1-5-99"
        low["supervisor_result"]["child_integrity_claim"] = "LOW_IL"
        low["supervisor_result"]["child_in_job"] = "INSIDE"
        low["supervisor_result"]["job_observation"] = "CLAIMED_CONTAINED"
        low["supervisor_result"]["acl_observation"] = "CLAIMED_DENY"
        low_result, found = _closed(self, low)
        self.assertEqual(low_result["overall_status"], "BLOCKED")
        self.assertEqual(low_result["overall_reason"], "HER_PYTHON_PIN_PENDING")
        self.assertEqual(found["her_child_contained"]["status"], "UNCONFIRMED")
        self.assertEqual(found["her_child_contained"]["reason"], "HER_PRIVILEGED_OBSERVATION_UNVERIFIED")
        self.assertEqual(result_status(found, "her_u_vs_p"), "UNCONFIRMED")

    def test_acl_omission_mismatch_and_reparse(self) -> None:
        omitted = synthetic_event()
        _result, found = _closed(self, omitted)
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_ACL_SNAPSHOT_OMITTED")

        explicit = synthetic_event()
        explicit["supervisor_result"]["acl_observation"] = "OMITTED"
        _result, found = _closed(self, explicit)
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_ACL_SNAPSHOT_OMITTED")

        granted = synthetic_event()
        granted["supervisor_result"]["acl_observation"] = "CLAIMED_GRANT"
        grant_result, found = _closed(self, granted)
        self.assertEqual(grant_result["overall_reason"], "HER_U_WRITE_GRANTED")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_U_WRITE_GRANTED")

        swapped = synthetic_event()
        _role(swapped, "probe")["post_sha256"] = "ef" * 32
        swap_result, _found = _closed(self, swapped)
        self.assertEqual(swap_result["overall_status"], "FAIL")
        self.assertEqual(swap_result["overall_reason"], "HER_SURFACE_MUTATED")

        escaped = synthetic_event()
        _role(escaped, "case_inputs")["reparse_escape"] = True
        escape_result, found = _closed(self, escaped)
        self.assertEqual(escape_result["overall_status"], "FAIL")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_REPARSE_ESCAPE")
        self.assertEqual(found["her_surface_hash_agreement"]["reason"], "HER_SURFACE_MUTATED")

    def test_provider_metadata_is_not_isolation_proof(self) -> None:
        event = synthetic_event()
        event["supervisor_result"]["provider_metadata_as_isolation"] = True
        result, found = _closed(self, event)
        self.assertEqual(found["her_u_vs_p"]["status"], "UNCONFIRMED")
        self.assertEqual(found["her_u_vs_p"]["reason"], "HER_PROVIDER_METADATA_NOT_PROOF")
        self.assertEqual(result["overall_status"], "BLOCKED")

    def test_boolean_integer_coercion_is_rejected(self) -> None:
        event = synthetic_event()
        event["surface_records"][0]["u_write_denied"] = 1
        result, _found = _closed(self, event)
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_SCHEMA_REJECTED")
        self.assertEqual(schema_check(1, {"type": "boolean", "const": True}), ["$: wrong type"])

    def test_collector_export_mutation_stays_outside_p(self) -> None:
        event = synthetic_event()
        original = {
            record["surface_role"]: (record["freeze_sha256"], record["post_sha256"])
            for record in event["surface_records"]
        }
        protected = {record["surface_role"]: record["post_sha256"] for record in event["surface_records"]}
        exported = collect_export(event["event_id"], protected)
        self.assertFalse(exported["protected_execution_member"])
        self.assertTrue(exported["mutable_collector_output"])
        self.assertEqual(exported["network"], "NOT_USED")
        exported["protected_hashes"]["execution_cwd"] = "00" * 32
        exported["mutable_collector_output"] = False
        self.assertEqual(
            {record["surface_role"]: (record["freeze_sha256"], record["post_sha256"]) for record in event["surface_records"]},
            original,
        )
        export_result, _found = _closed(self, exported)
        self.assertEqual(export_result["overall_status"], "BLOCKED")
        self.assertEqual(export_result["overall_reason"], "HER_SCHEMA_VERSION")
        event_result, _found = _closed(self, event)
        self.assertEqual(event_result["overall_status"], "BLOCKED")
        self.assertNotEqual(event_result["overall_status"], "PASS")

    def test_git_ownership_failure_is_not_a_pass_and_not_executed(self) -> None:
        failed = synthetic_event()
        failed["supervisor_result"]["git_ownership_observation"] = "FAILED"
        result, found = _closed(self, failed)
        self.assertEqual(found["her_git_config_closed"]["status"], "BLOCKED")
        self.assertEqual(found["her_git_config_closed"]["reason"], "HER_GIT_OWNERSHIP_REFUSED")
        self.assertEqual(result["overall_reason"], "HER_PYTHON_PIN_PENDING")
        self.assertEqual(result["privileged_tests"]["git_ownership"], "UNVERIFIED")

        claimed = synthetic_event()
        claimed["supervisor_result"]["git_ownership_observation"] = "CLAIMED_PASS"
        claimed_result, _found = _closed(self, claimed)
        self.assertEqual(claimed_result["overall_status"], "FAIL")
        self.assertEqual(claimed_result["overall_reason"], "HER_CONTRADICTION")

    def test_writers_outside_t_and_witness_cannot_be_promoted(self) -> None:
        writers = synthetic_event()
        writers["supervisor_result"]["writers_outside_t"] = "EXCLUDED"
        writers_result, found = _closed(self, writers)
        self.assertEqual(writers_result["overall_status"], "FAIL")
        self.assertEqual(found["writers_outside_t_excluded"]["reason"], "HER_CONTRADICTION")

        witness = synthetic_event()
        witness["supervisor_result"]["independent_external_witness"] = "ADMITTED"
        witness_result, found = _closed(self, witness)
        self.assertEqual(witness_result["overall_status"], "FAIL")
        self.assertEqual(found["independent_external_witness"]["reason"], "HER_CONTRADICTION")

    def test_duplicate_roles_and_event_ids_conflict(self) -> None:
        duplicate = synthetic_event()
        duplicate["surface_records"].append(dict(duplicate["surface_records"][0]))
        duplicate_result, _found = _closed(self, duplicate)
        self.assertEqual(duplicate_result["overall_reason"], "HER_CONTRADICTION")

        mismatch = synthetic_event()
        mismatch["surface_records"][1]["event_id"] = "evt-other"
        mismatch_result, _found = _closed(self, mismatch)
        self.assertEqual(mismatch_result["overall_reason"], "HER_CONTRADICTION")

    def test_linux_host_string_is_platform_blocked(self) -> None:
        event = synthetic_event()
        event["host_class"] = "LINUX"
        result, _found = _closed(self, event)
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_PLATFORM_UNSUPPORTED")

    def test_git_pin_mismatch_branch_blocks(self) -> None:
        original = supervisor.RATIFIED_GIT_SHA256
        try:
            supervisor.RATIFIED_GIT_SHA256 = "ab" * 32
            self.assertEqual(classify_git_pin("cd" * 32), ("BLOCKED", "HER_GIT_PIN_MISMATCH"))
            matched = classify_git_pin("ab" * 32)
            self.assertNotEqual(matched[0], "PASS")
            self.assertEqual(matched, ("BLOCKED", "HER_PHASE1_PASS_FORBIDDEN"))
        finally:
            supervisor.RATIFIED_GIT_SHA256 = original
        self.assertIsNone(RATIFIED_GIT_SHA256)

    def test_no_fixture_yields_overall_pass(self) -> None:
        cases = [
            synthetic_event(),
            _origin("FORGED"),
            _origin("HISTORICAL_R3"),
            _origin("RUNNER_FLAG"),
        ]
        granted = synthetic_event()
        granted["surface_records"][0]["u_write_denied"] = False
        cases.append(granted)
        other = synthetic_event()
        other["host_class"] = "OTHER"
        cases.append(other)
        edit = synthetic_event()
        edit["supervisor_result"]["requests_supervisor_edit"] = True
        cases.append(edit)
        cases.append({"schema_version": "inr.event.v0.r3"})
        cases.append(collect_export("evt-1", {"execution_cwd": "ab" * 32}))
        for event in cases:
            result, _found = _closed(self, event)
            self.assertIn(result["overall_status"], {"FAIL", "BLOCKED", "UNCONFIRMED"})


def result_status(found: dict, predicate_id: str) -> str:
    return found[predicate_id]["status"]


if __name__ == "__main__":
    unittest.main()
