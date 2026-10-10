"""Focused refusal tests for the Phase 1 r4 verifier."""

from __future__ import annotations

import inspect
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_her_001.supervisor_her_v1 import (
    ACCEPTED_SUPERVISOR,
    NONCLAIMS,
    PREDICATE_IDS,
    PRIVILEGED_EXECUTED,
    PYTHON_PIN_RATIFIED,
    RATIFIED_GIT_SHA256,
    SURFACE_ROLES,
    TRUST_BASE,
    WRITERS_OUTSIDE_T_SUPPORTED,
    enforce_phase1_ceiling,
    evaluate_event,
    request_supervisor_change,
    synthetic_event,
    trust_base_digest,
    validate_event,
)
from docs.inr_her_001.validate_her_v1 import R3_SCHEMA_VERSIONS, output_errors

EXPECTED = {
    "her_surface_hash_agreement": ("PASS", "HASH_AGREEMENT_ONLY"),
    "her_u_vs_p": ("UNCONFIRMED", "HER_ACL_SNAPSHOT_OMITTED"),
    "her_child_contained": ("UNCONFIRMED", "HER_U_SID_ABSENT"),
    "her_git_snapshot_sole_source": ("UNCONFIRMED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"),
    "her_git_config_closed": ("UNCONFIRMED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"),
    "her_runtime_pinned": ("BLOCKED", "HER_PYTHON_PIN_PENDING"),
    "her_git_pin": ("BLOCKED", "HER_GIT_PIN_UNRATIFIED"),
    "writers_outside_t_excluded": ("UNCONFIRMED", "HER_WRITERS_OUTSIDE_T_UNCONFIRMED"),
    "independent_external_witness": ("UNCONFIRMED", "INDEPENDENT_WITNESS_NOT_CLAIMED"),
    "all_writer_isolation_bounded_v1": ("BLOCKED", "HER_PYTHON_PIN_PENDING"),
}


def _by_id(result: dict) -> dict[str, dict]:
    return {item["predicate_id"]: item for item in result["predicates"]}


class RefusalHerTests(unittest.TestCase):
    def test_phase1_constants_stay_closed(self) -> None:
        self.assertFalse(PYTHON_PIN_RATIFIED)
        self.assertFalse(PRIVILEGED_EXECUTED)
        self.assertFalse(WRITERS_OUTSIDE_T_SUPPORTED)
        self.assertIsNone(RATIFIED_GIT_SHA256)
        self.assertEqual(ACCEPTED_SUPERVISOR, "docs/inr_001/supervisor_inr_v0.py")
        self.assertEqual(len(TRUST_BASE), 10)
        self.assertEqual(len(trust_base_digest()), 64)
        for role in SURFACE_ROLES:
            self.assertNotIn(role, "\n".join(TRUST_BASE))
        self.assertNotIn("open(", inspect.getsource(request_supervisor_change))

    def test_synthetic_fixture_is_blocked_on_the_python_pin(self) -> None:
        result = evaluate_event(synthetic_event())
        self.assertEqual(output_errors(result), [])
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_PYTHON_PIN_PENDING")
        self.assertEqual(result["phase1_ceiling"], "ISOLATION_PASS_UNAVAILABLE")
        self.assertEqual(result["nonclaims"], list(NONCLAIMS))
        self.assertEqual(
            result["privileged_tests"],
            {"token": "UNVERIFIED", "job": "UNVERIFIED", "acl": "UNVERIFIED", "git_ownership": "UNVERIFIED"},
        )
        found = _by_id(result)
        self.assertEqual(tuple(found), PREDICATE_IDS)
        for predicate_id, expected in EXPECTED.items():
            self.assertEqual((found[predicate_id]["status"], found[predicate_id]["reason"]), expected)
        self.assertEqual(
            [item["status"] for item in result["predicates"] if item["status"] == "PASS"],
            ["PASS"],
        )

    def test_json_round_trip_matches_the_dict_event(self) -> None:
        event = synthetic_event()
        left = evaluate_event(event)
        right = validate_event(json.dumps(event))
        self.assertEqual(left, right)

    def test_malformed_input_is_schema_rejected(self) -> None:
        samples = ["{", "[]", "null", b"\xff", '{"a": NaN}', '{"a": 1, "a": 2}', 1, None]
        for sample in samples:
            result = validate_event(sample)
            self.assertEqual(result["overall_status"], "BLOCKED", sample)
            self.assertEqual(result["overall_reason"], "HER_SCHEMA_REJECTED", sample)
            self.assertNotEqual(result["overall_status"], "PASS")

    def test_r3_versions_are_blocked(self) -> None:
        for version in sorted(R3_SCHEMA_VERSIONS):
            result = validate_event({"schema_version": version, "event_id": "evt-r3"})
            self.assertEqual(result["overall_status"], "BLOCKED")
            self.assertEqual(result["overall_reason"], "HER_SCHEMA_VERSION")
            self.assertTrue(all(item["status"] == "BLOCKED" for item in result["predicates"]))

    def test_nested_r3_supervisor_is_blocked(self) -> None:
        event = synthetic_event()
        event["supervisor_result"]["schema_version"] = "inr.supervisor.result.v0.r3"
        result = evaluate_event(event)
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_SCHEMA_VERSION")

    def test_supervisor_edit_request_is_blocked(self) -> None:
        result = request_supervisor_change("add a job object")
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_SUPERVISOR_EDIT_REQUIRED")
        event = synthetic_event()
        event["supervisor_result"]["requests_supervisor_edit"] = True
        flagged = evaluate_event(event)
        self.assertEqual(flagged["overall_status"], "BLOCKED")
        self.assertEqual(flagged["overall_reason"], "HER_SUPERVISOR_EDIT_REQUIRED")

    def test_non_windows_host_is_platform_blocked(self) -> None:
        event = synthetic_event()
        event["host_class"] = "OTHER"
        result = evaluate_event(event)
        found = _by_id(result)
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_PLATFORM_UNSUPPORTED")
        self.assertEqual(found["her_runtime_pinned"]["reason"], "HER_PYTHON_PIN_PENDING")
        self.assertEqual(found["all_writer_isolation_bounded_v1"]["reason"], "HER_PLATFORM_UNSUPPORTED")

    def test_trust_mismatch_blocks_hash_agreement(self) -> None:
        event = synthetic_event()
        event["trust_base_digest"] = "ab" * 32
        result = evaluate_event(event)
        found = _by_id(result)
        self.assertEqual(found["her_surface_hash_agreement"]["status"], "BLOCKED")
        self.assertEqual(found["her_surface_hash_agreement"]["reason"], "HER_TRUST_BASE_MISMATCH")
        self.assertEqual(result["overall_reason"], "HER_PYTHON_PIN_PENDING")
        self.assertNotEqual(result["overall_status"], "PASS")

    def test_wrong_python_pin_constant_stays_pin_pending(self) -> None:
        event = synthetic_event()
        event["python_pin_status"] = "AUTHENTICATED"
        result = evaluate_event(event)
        self.assertEqual(result["overall_status"], "BLOCKED")
        self.assertEqual(result["overall_reason"], "HER_PYTHON_PIN_PENDING")

    def test_ceiling_rewrites_an_isolation_pass(self) -> None:
        predicates = [
            {"predicate_id": "her_surface_hash_agreement", "status": "PASS", "reason": "HASH_AGREEMENT_ONLY"},
            {"predicate_id": "all_writer_isolation_bounded_v1", "status": "PASS", "reason": "PASS"},
        ]
        status, reason, rewritten = enforce_phase1_ceiling("PASS", "PASS", predicates)
        self.assertEqual((status, reason), ("BLOCKED", "HER_PHASE1_PASS_FORBIDDEN"))
        self.assertEqual(rewritten[0]["status"], "PASS")
        self.assertEqual(rewritten[0]["reason"], "HASH_AGREEMENT_ONLY")
        self.assertEqual(rewritten[1]["status"], "BLOCKED")
        self.assertEqual(rewritten[1]["reason"], "HER_PHASE1_PASS_FORBIDDEN")

    def test_package_import_exports_the_phase1_api(self) -> None:
        import docs.inr_her_001 as her

        self.assertEqual(
            set(her.__all__),
            {"collect_export", "evaluate_event", "request_supervisor_change", "validate_event"},
        )


if __name__ == "__main__":
    unittest.main()
