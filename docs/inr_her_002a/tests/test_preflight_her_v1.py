"""Fail-closed tests for the INR-HER-001 Phase 2A preflight gate."""

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

from docs.inr_her_001.supervisor_her_v1 import synthetic_event
from docs.inr_her_002a.preflight_her_v1 import (
    collect_readonly_observation,
    config_scopes,
    evaluate_phase2a,
    freshness_procedure,
    n1_stopped_patch,
    pin_procedure,
)

HUMAN_FINAL = "fccd128ec37a8cfb940c572a1bf566449abddb25"
FAKE_DIGEST = "ab" * 32


def _quiet(**overrides) -> dict:
    observation = {
        "platform": "WINDOWS_X64",
        "python_version": "3.11.9",
        "python_executable": "C:/pinned/python.exe",
        "python_sha256_authenticated": False,
        "python_distribution_sha256": FAKE_DIGEST,
        "mingit_version": "mingit-test",
        "mingit_executable": "C:/pinned/mingit/cmd/git.exe",
        "mingit_sha256_authenticated": False,
        "mingit_distribution_sha256": FAKE_DIGEST,
        "git_execution_path": "C:/pinned/mingit/cmd/git.exe",
        "git_source": "UNEXPECTED",
        "git_config_closed": None,
        "privileges": "ABSENT",
    }
    observation.update(overrides)
    return observation


def _check(result: dict, check_id: str) -> dict:
    found = [item for item in result["checks"] if item["check_id"] == check_id]
    if len(found) != 1:
        raise AssertionError(check_id)
    return found[0]


class Phase2APreflightTests(unittest.TestCase):
    def test_unhashable_schema_versions_are_structured_refusals(self) -> None:
        for value in ([], {}, set()):
            result = evaluate_phase2a({"schema_version": value, "event_id": "evt-1"}, _quiet())
            self.assertEqual("BLOCKED", result["overall_status"])
            self.assertEqual("HER_SCHEMA_VERSION", result["overall_reason"])
            self.assertEqual("NOT_DELEGATED", result["phase1_overall_status"])
            self.assertNotIn(FAKE_DIGEST, json.dumps(result))

    def test_nested_unhashable_versions_do_not_call_phase1(self) -> None:
        event = synthetic_event()
        event["supervisor_result"]["schema_version"] = []
        surface = synthetic_event()
        surface["surface_records"][0]["schema_version"] = {}
        with mock.patch("docs.inr_her_002a.preflight_her_v1.evaluate_event") as gate:
            gate.side_effect = AssertionError("phase1 called")
            supervisor = evaluate_phase2a(event, _quiet())
            record = evaluate_phase2a(surface, _quiet())
        self.assertFalse(gate.called)
        self.assertEqual("HER_SCHEMA_VERSION", supervisor["overall_reason"])
        self.assertEqual("HER_SCHEMA_VERSION", record["overall_reason"])
        self.assertEqual("BLOCKED", _check(supervisor, "schema_version")["status"])

    def test_hashable_r3_version_delegates_and_stays_non_pass(self) -> None:
        event = synthetic_event()
        event["schema_version"] = "inr.event.v0.r3"
        result = evaluate_phase2a(event, _quiet())
        self.assertEqual("BLOCKED", result["overall_status"])
        self.assertEqual("HER_SCHEMA_VERSION", result["overall_reason"])
        self.assertEqual("HER_SCHEMA_VERSION", result["phase1_overall_reason"])
        self.assertIn(result["overall_status"], {"FAIL", "BLOCKED", "UNCONFIRMED"})

    def test_missing_python_is_not_a_git_or_hash_reason(self) -> None:
        observation = _quiet()
        observation["python_version"] = None
        observation["python_executable"] = None
        result = evaluate_phase2a(synthetic_event(), observation)
        self.assertEqual("BLOCKED", result["overall_status"])
        self.assertEqual("HER_RUNTIME_ABSENT", result["overall_reason"])
        self.assertEqual("HER_RUNTIME_ABSENT", _check(result, "cpython_identity")["reason"])
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", _check(result, "git_execution_path")["reason"])
        self.assertNotEqual("HASH_AGREEMENT_ONLY", result["overall_reason"])
        self.assertNotEqual("PASS", _check(result, "cpython_identity")["status"])

    def test_missing_mingit_and_unverified_pin_keep_digest_empty(self) -> None:
        observation = _quiet()
        observation["mingit_version"] = None
        observation["mingit_executable"] = None
        observation["git_execution_path"] = None
        observation["git_source"] = None
        result = evaluate_phase2a(synthetic_event(), observation)
        self.assertEqual("BLOCKED", _check(result, "mingit_identity")["status"])
        self.assertEqual("HER_GIT_RUNTIME_ABSENT", _check(result, "mingit_identity")["reason"])
        self.assertEqual("HER_GIT_RUNTIME_ABSENT", _check(result, "git_execution_path")["reason"])
        self.assertEqual("PIN_PENDING", result["pins"]["python_pin_status"])
        self.assertEqual("UNRATIFIED", result["pins"]["git_pin_status"])
        self.assertIsNone(result["pins"]["python_sha256"])
        self.assertIsNone(result["pins"]["git_sha256"])
        self.assertNotIn(FAKE_DIGEST, json.dumps(result))

    def test_exact_python_without_bytes_stays_pin_pending(self) -> None:
        result = evaluate_phase2a(synthetic_event(), _quiet())
        self.assertEqual("BLOCKED", result["overall_status"])
        self.assertEqual("HER_PYTHON_PIN_PENDING", result["overall_reason"])
        self.assertEqual("UNCONFIRMED", _check(result, "cpython_identity")["status"])
        self.assertEqual("BLOCKED", _check(result, "cpython_pin")["status"])
        self.assertEqual("HER_FRESHNESS_UNPROVEN", _check(result, "event_freshness")["reason"])

    def test_wrong_python_identity_is_not_reported_as_a_ratified_pin(self) -> None:
        result = evaluate_phase2a(synthetic_event(), _quiet(python_version="3.14.0"))
        self.assertEqual("HER_PYTHON_IDENTITY_MISMATCH", result["overall_reason"])
        self.assertEqual("HER_PYTHON_PIN_PENDING", _check(result, "cpython_pin")["reason"])
        self.assertNotEqual("PASS", result["overall_status"])

    def test_claimed_authenticated_digest_is_a_contradiction(self) -> None:
        result = evaluate_phase2a(
            synthetic_event(),
            _quiet(python_sha256_authenticated=True, mingit_sha256_authenticated=True),
        )
        self.assertEqual("FAIL", result["overall_status"])
        self.assertEqual("HER_CONTRADICTION", result["overall_reason"])
        self.assertIsNone(result["pins"]["python_sha256"])
        self.assertIsNone(result["pins"]["git_sha256"])

    def test_unexpected_and_claimed_pinned_git_stay_non_pass(self) -> None:
        unexpected = evaluate_phase2a(synthetic_event(), _quiet(git_source="LIVE_CHECKOUT"))
        pinned = evaluate_phase2a(synthetic_event(), _quiet(git_source="MINGIT_PINNED"))
        self.assertEqual("HER_GIT_SOURCE_NOT_SNAPSHOT", _check(unexpected, "git_execution_path")["reason"])
        self.assertEqual("HER_GIT_PIN_UNRATIFIED", _check(pinned, "git_execution_path")["reason"])
        self.assertNotEqual("PASS", unexpected["overall_status"])
        self.assertNotEqual("HASH_AGREEMENT_ONLY", pinned["overall_reason"])

    def test_permissions_and_platform_fail_closed(self) -> None:
        absent = evaluate_phase2a(synthetic_event(), _quiet(privileges="ABSENT"))
        unknown = evaluate_phase2a(synthetic_event(), _quiet(privileges="UNOBSERVED"))
        present = evaluate_phase2a(synthetic_event(), _quiet(privileges="PRESENT_UNEXERCISED"))
        other = evaluate_phase2a(synthetic_event(), _quiet(platform="LINUX"))
        self.assertEqual("HER_TOKEN_PRIVILEGE_UNAVAILABLE", _check(absent, "privileges")["reason"])
        self.assertEqual("UNCONFIRMED", _check(unknown, "privileges")["status"])
        self.assertEqual("HER_PRIVILEGE_OBSERVATION_UNAVAILABLE", _check(unknown, "privileges")["reason"])
        self.assertEqual("HER_PRIVILEGED_OBSERVATION_UNVERIFIED", _check(present, "privileges")["reason"])
        self.assertEqual("HER_PLATFORM_UNSUPPORTED", other["overall_reason"])
        for result in (absent, unknown, present, other):
            self.assertNotEqual("PASS", result["overall_status"])

    def test_pass_claim_does_not_hide_a_missing_runtime(self) -> None:
        observation = _quiet(claimed_status="PASS")
        observation["python_executable"] = ""
        result = evaluate_phase2a(synthetic_event(), observation)
        self.assertEqual("FAIL", result["overall_status"])
        self.assertEqual("HER_CONTRADICTION", result["overall_reason"])
        self.assertEqual("BLOCKED", _check(result, "cpython_identity")["status"])
        self.assertEqual("HER_RUNTIME_ABSENT", _check(result, "cpython_identity")["reason"])

    def test_uniform_relabel_and_hash_agreement_are_not_freshness(self) -> None:
        event = synthetic_event()
        event["event_id"] = "evt-2"
        event["supervisor_result"]["event_id"] = "evt-2"
        for record in event["surface_records"]:
            record["event_id"] = "evt-2"
        quiet = evaluate_phase2a(event, _quiet(), {})
        declared = evaluate_phase2a(event, _quiet(), {"relabel": "UNIFORM"})
        self.assertEqual("HER_FRESHNESS_UNPROVEN", _check(quiet, "event_freshness")["reason"])
        self.assertEqual("FAIL", _check(declared, "event_freshness")["status"])
        self.assertEqual("HER_EVENT_RELABEL_NOT_FRESH", _check(declared, "event_freshness")["reason"])
        self.assertEqual("FAIL", declared["overall_status"])
        self.assertNotEqual("HASH_AGREEMENT_ONLY", quiet["overall_reason"])
        self.assertNotEqual("HASH_AGREEMENT_ONLY", declared["overall_reason"])

    def test_replay_substituted_head_and_false_binding(self) -> None:
        event = synthetic_event()
        replay = evaluate_phase2a(event, _quiet(), {"replay": True})
        substituted = evaluate_phase2a(event, _quiet(), {"authenticated_head": "0" * 40})
        same_head = evaluate_phase2a(event, _quiet(), {"authenticated_head": event["source_head"]})
        claimed = evaluate_phase2a(event, _quiet(), {"binding_authenticated": True})
        mismatched = synthetic_event()
        mismatched["supervisor_result"]["event_id"] = "evt-other"
        conflict = evaluate_phase2a(mismatched, _quiet(), {})
        self.assertEqual("HER_EVENT_REPLAY_UNAUTHENTICATED", _check(replay, "event_freshness")["reason"])
        self.assertEqual("HER_SUBSTITUTED_HEAD_NOT_FRESH", _check(substituted, "event_freshness")["reason"])
        self.assertEqual("HER_FRESHNESS_UNPROVEN", _check(same_head, "event_freshness")["reason"])
        self.assertEqual("HER_CONTRADICTION", _check(claimed, "event_freshness")["reason"])
        self.assertEqual("HER_EVENT_RELABEL_NOT_FRESH", _check(conflict, "event_freshness")["reason"])
        for result in (replay, substituted, same_head, claimed, conflict):
            self.assertNotEqual("PASS", result["overall_status"])
            self.assertNotEqual("HASH_AGREEMENT_ONLY", result["overall_reason"])

    def test_pin_and_freshness_procedures_are_unexecuted(self) -> None:
        pins = pin_procedure()
        freshness = freshness_procedure()
        self.assertFalse(pins["executed"])
        self.assertEqual("PIN_PENDING", pins["python"]["status"])
        self.assertEqual("UNRATIFIED", pins["mingit"]["status"])
        self.assertIsNone(pins["python"]["sha256"])
        self.assertIsNone(pins["mingit"]["sha256"])
        self.assertFalse(freshness["executed"])
        self.assertFalse(freshness["accepts_hash_agreement_as_freshness"])
        self.assertFalse(freshness["accepts_relabeled_event_id_as_freshness"])
        self.assertIn("STOPPED", n1_stopped_patch())
        self.assertIn("hash(item)", n1_stopped_patch())

    def test_config_parser_discards_values(self) -> None:
        raw = "local\nuser.name\nAda Lovelace\0global\ncore.autocrlf\ntrue\0"
        scopes = config_scopes(raw)
        self.assertEqual(["global", "local"], scopes)
        self.assertNotIn("Ada Lovelace", scopes)

    def test_open_git_config_is_unclosed(self) -> None:
        result = evaluate_phase2a(synthetic_event(), _quiet(git_config_closed=False))
        self.assertEqual("BLOCKED", _check(result, "git_config")["status"])
        self.assertEqual("HER_GIT_CONFIG_UNCLOSED", _check(result, "git_config")["reason"])
        claimed = evaluate_phase2a(synthetic_event(), _quiet(git_config_closed=True))
        self.assertEqual("HER_GIT_CONFIG_UNVERIFIED", _check(claimed, "git_config")["reason"])
        self.assertNotEqual("PASS", claimed["overall_status"])

    def test_accepted_phase1_and_r3_bytes_match_human_final(self) -> None:
        completed = subprocess.run(
            ["git", "diff", "--exit-code", HUMAN_FINAL, "--", "docs/inr_her_001", "docs/inr_001"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, completed.returncode, completed.stdout + completed.stderr)

    def test_host_observation_does_not_ratify_or_pass(self) -> None:
        observation = collect_readonly_observation()
        result = evaluate_phase2a(synthetic_event(), observation)
        self.assertFalse(observation["python_sha256_authenticated"])
        self.assertFalse(observation["mingit_sha256_authenticated"])
        self.assertIsNone(observation["python_distribution_sha256"])
        self.assertIsNone(observation["mingit_distribution_sha256"])
        self.assertNotEqual("MINGIT_PINNED", observation["git_source"])
        self.assertIsNot(True, observation["git_config_closed"])
        self.assertEqual("PIN_PENDING", result["pins"]["python_pin_status"])
        self.assertEqual("UNRATIFIED", result["pins"]["git_pin_status"])
        self.assertFalse(result["n1_source_edited"])
        self.assertEqual("STOPPED", result["n1_phase1_edit"])
        self.assertEqual("N2_EXTERNAL_BINDING_UNEXECUTED", result["freshness_procedure"])
        self.assertIn(result["overall_status"], {"FAIL", "BLOCKED", "UNCONFIRMED"})
        self.assertTrue(all(item["status"] != "PASS" for item in result["checks"]))
        self.assertNotEqual("HASH_AGREEMENT_ONLY", _check(result, "event_freshness")["reason"])


if __name__ == "__main__":
    unittest.main()
