"""Focused tests for Recovery Execution Receipt v0."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest
from collections.abc import Mapping
from pathlib import Path

from audit_lifecycle.epistemic.serialize import canonical_digest
from recovery_execution_receipt_v0 import (
    RecoveryExecutionError,
    build_recovery_execution_receipt,
)

REPO = Path(__file__).resolve().parents[2]
_OTHER = "cd" * 32
_GIT = "ab" * 20
_AUTHORITY_FACTS = {
    "authority": False,
    "independent_evidence_admitted": False,
    "human_final": False,
    "r4_vector_eig_mutated": False,
}
_UNPINNED = (
    "HEAD",
    "latest",
    "current",
    "main",
    "master",
    "production",
    "origin/main",
    "origin/master",
)
_PROOF_TOKENS = (
    "PROVEN_TRUE",
    "HUMAN_REVIEW_ACCEPTED",
    "independent_evidence_count",
    "structural_candidate",
    "admission_status",
)


class _SplitView(Mapping):
    """Bound iteration is the record. Live lookup is the attack."""

    def __init__(self, bound: dict, live: dict) -> None:
        self._bound = bound
        self._live = live

    def __getitem__(self, key: str):
        return self._live[key]

    def __iter__(self):
        return iter(self._bound)

    def __len__(self) -> int:
        return len(self._bound)

    def items(self):
        return self._bound.items()

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class _SplitDict(dict):
    def __init__(self, bound: dict, live: dict) -> None:
        super().__init__(bound)
        self._live = live

    def __getitem__(self, key: str):
        return self._live[key]

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class _HostileStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return hash("PASS")


class _HostileInt(int):
    def __eq__(self, other: object) -> bool:
        return other is True or int.__eq__(self, other)

    def __hash__(self) -> int:
        return hash(True)


class _Rows(list):
    """Caller-owned list subclass."""


class _Reuse(tuple):
    """Caller-owned tuple subclass."""


class _DupKeys(Mapping):
    def __getitem__(self, key: str):
        return "x"

    def __iter__(self):
        return iter(("recovery_session_id",))

    def __len__(self) -> int:
        return 2

    def items(self):
        return [
            ("recovery_session_id", "rec-1"),
            ("recovery_session_id", "other"),
        ]


def _digest_check(
    check_id: str,
    kind: str,
    body: object,
    event_order: int,
    *,
    result: str = "OBSERVED_PASS",
    critical: bool = True,
    target: str = "restore-target-1",
    **over: object,
) -> dict:
    digest = canonical_digest(body)
    record = {
        "check_id": check_id,
        "check_kind": kind,
        "target": target,
        "expected": digest,
        "observed": digest,
        "result": result,
        "critical": critical,
        "event_order": event_order,
        "evidence_body": body,
    }
    record.update(over)
    return record


def _authority_check(event_order: int = 6, **over: object) -> dict:
    facts = dict(_AUTHORITY_FACTS)
    record = {
        "check_id": "chk-auth",
        "check_kind": "AUTHORITY_BOUNDARY_CHECK",
        "target": "receipt",
        "expected": facts,
        "observed": facts,
        "result": "OBSERVED_PASS",
        "critical": True,
        "event_order": event_order,
        "evidence_body": dict(facts),
    }
    record.update(over)
    return record


def _health_check(event_order: int = 7, **over: object) -> dict:
    record = {
        "check_id": "chk-health",
        "check_kind": "SERVICE_HEALTH",
        "target": "svc-1",
        "expected": {"healthy": True},
        "observed": {"healthy": True},
        "result": "OBSERVED_PASS",
        "critical": True,
        "event_order": event_order,
        "evidence_body": {"probe": "healthz", "status": 200},
    }
    record.update(over)
    return record


def _isolation_na() -> dict:
    return {
        "isolation_id": "iso-1",
        "isolation_kind": "ARTIFACT_SCOPE",
        "result": "NOT_APPLICABLE",
        "justification": "artifact-only restore has no runtime blast radius",
        "event_order": 2,
    }


def _isolation_pass(body: object | None = None) -> dict:
    return {
        "isolation_id": "iso-1",
        "isolation_kind": "RUNTIME_FENCE",
        "body": {"fence": "runtime-isolated"} if body is None else body,
        "result": "OBSERVED_PASS",
        "event_order": 2,
    }


def _attempt(
    target_digest: str,
    checks: list[dict],
    **over: object,
) -> dict:
    record = {
        "attempt_id": "att-1",
        "action_type": "RESTORE",
        "target_id": "restore-target-1",
        "target_binding_kind": "content_digest",
        "target_binding_value": target_digest,
        "executor_id": "external-operator",
        "event_order": 4,
        "result_token": "exit-0",
        "action_result": "OBSERVED_PASS",
        "changed_object_refs": ["artifact:restore-target-1"],
        "verification_checks": checks,
    }
    record.update(over)
    return record


def _artifact(**over: object) -> dict:
    target_body = {"artifact": "pinned-v1"}
    target_digest = canonical_digest(target_body)
    restored = {"artifact": "pinned-v1"}
    record = {
        "recovery_session_id": "rec-1",
        "target_scope": "ARTIFACT_ONLY",
        "target_artifact_id": "artifact-1",
        "target_environment": {"name": "lab", "role": "restore-lab"},
        "pre_state": [
            {
                "evidence_id": "pre-1",
                "evidence_kind": "ARTIFACT",
                "body": {"state": "incident-bytes"},
                "event_order": 0,
            }
        ],
        "stop": {
            "stop_id": "stop-1",
            "mechanism_kind": "PROCESS_HALT",
            "body": {"halt": "action-path-stopped"},
            "result": "OBSERVED_PASS",
            "event_order": 1,
        },
        "isolation": _isolation_na(),
        "restore_target": {
            "target_id": "restore-target-1",
            "binding_kind": "content_digest",
            "binding_value": target_digest,
            "body": target_body,
            "source": "pinned-artifact-store",
            "event_order": 3,
        },
        "attempts": [
            _attempt(
                target_digest,
                [
                    _digest_check("chk-content", "CONTENT_DIGEST_MATCH", restored, 5),
                    _authority_check(6),
                ],
            )
        ],
    }
    record.update(over)
    return record


def _config(**over: object) -> dict:
    record = _artifact()
    record["target_scope"] = "CONFIG"
    record["isolation"] = _isolation_pass({"fence": "config-isolated"})
    record["attempts"][0]["verification_checks"].append(
        _digest_check(
            "chk-config",
            "CONFIG_DIGEST_MATCH",
            {"config": "pinned-config"},
            7,
        )
    )
    record.update(over)
    return record


def _runtime(**over: object) -> dict:
    record = _artifact()
    record["target_scope"] = "SERVICE_RUNTIME"
    record["isolation"] = _isolation_pass()
    record["attempts"][0]["verification_checks"].extend(
        [
            _health_check(7),
            _digest_check(
                "chk-sig",
                "SIGNATURE_CHECK",
                {"signature": "detached-sig"},
                8,
            ),
        ]
    )
    record.update(over)
    return record


def _build(record: Mapping[str, object] | None = None, **kwargs: object) -> dict:
    if record is None:
        record = _artifact()
    return build_recovery_execution_receipt(record, **kwargs)


def _expect(test: unittest.TestCase, code: str, fn) -> None:
    with test.assertRaises(RecoveryExecutionError) as caught:
        fn()
    test.assertEqual(caught.exception.code, code)


def _assert_closed(test: unittest.TestCase, receipt: Mapping[str, object]) -> None:
    test.assertIs(receipt["authority"], False)
    test.assertIs(receipt["recovered"], False)
    test.assertEqual(receipt["schema_version"], "recovery_execution_receipt.v0")
    test.assertNotEqual(receipt["classification"], "RECOVERED")
    blob = json.dumps(receipt)
    for token in _PROOF_TOKENS:
        test.assertNotIn(token, blob)
    test.assertNotIn("independent_evidence_count", receipt)
    test.assertNotIn("admission_status", receipt)
    test.assertNotIn("structural_candidate", receipt)
    test.assertNotIn("human_final", receipt)
    test.assertNotIn("human_final_status", receipt)


def _review_digest(receipt: Mapping[str, object]) -> str:
    latest = receipt["attempts"][-1] if receipt["attempts"] else None
    checks = []
    attempt_id = None
    attempt_digest = None
    if latest is not None:
        attempt_id = latest["attempt_id"]
        attempt_digest = latest["action_digest"]
        checks = [
            {
                "check_id": item["check_id"],
                "check_kind": item["check_kind"],
                "result": item["result"],
                "evidence_digest": item.get("evidence_digest"),
            }
            for item in latest["verification_checks"]
        ]
    open_critical = [
        item for item in receipt["unresolved_risks"] if item["severity"] == "CRITICAL"
    ]
    payload = {
        "latest_attempt_id": attempt_id,
        "latest_attempt_digest": attempt_digest,
        "verification_summary_digest": canonical_digest(checks),
        "unresolved_critical_risk_summary_digest": canonical_digest(
            [
                {
                    "risk_id": item["risk_id"],
                    "statement": item["statement"],
                    "severity": item["severity"],
                }
                for item in open_critical
            ]
        ),
        "classification": receipt["classification"],
    }
    return canonical_digest(payload)


class TestTrustBoundary(unittest.TestCase):
    def test_01_mapping_split_view_neutralized(self) -> None:
        bound = _artifact()
        live = _artifact()
        live["recovery_session_id"] = "attack-session"
        live["recovered"] = True
        live["classification"] = "RECOVERED"
        live["independent_evidence_count"] = 3
        receipt = _build(_SplitView(bound, live))
        self.assertEqual(receipt["recovery_session_id"], "rec-1")
        self.assertIs(receipt["recovered"], False)
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")
        _assert_closed(self, receipt)

    def test_02_nested_split_view_neutralized(self) -> None:
        bound_body = {"state": "incident-bytes"}
        live_body = {"state": "attacker"}
        record = _artifact()
        record["pre_state"][0]["body"] = _SplitView(bound_body, live_body)
        receipt = _build(record)
        self.assertEqual(receipt["pre_state"][0]["body"], bound_body)
        self.assertEqual(receipt["pre_state"][0]["digest"], canonical_digest(bound_body))
        self.assertNotEqual(receipt["pre_state"][0]["body"], live_body)

    def test_03_scalar_subclass_rejected(self) -> None:
        record = _artifact()
        record["recovery_session_id"] = _HostileStr("rec-1")
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(record))
        counted = _artifact()
        counted["pre_state"][0]["event_order"] = _HostileInt(0)
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(counted))

    def test_04_container_subclass_rejected(self) -> None:
        record = _artifact()
        record["pre_state"] = _Rows(record["pre_state"])
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(record))
        record = _artifact()
        record["attempts"] = _Rows(record["attempts"])
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(record))
        record = _artifact()
        record["attempts"][0]["changed_object_refs"] = _Reuse(
            ("artifact:restore-target-1",)
        )
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(record))

    def test_05_unknown_kwargs_rejected(self) -> None:
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(extra=True))

    def test_06_forbidden_caller_assertions_rejected(self) -> None:
        for key in (
            "recovered",
            "restored",
            "verified_restore",
            "rollback_complete",
            "classification",
            "independent_evidence_count",
            "admission_status",
            "structural_candidate",
            "claims_iw_acceptance",
            "claims_independent_witness",
            "human_final",
            "Human Final",
            "human_final_status",
            "verified",
            "canonical",
            "published",
            "deployed",
            "VECTOR",
            "EIG",
        ):
            _expect(
                self,
                "RER_SCOPE_VIOLATION",
                lambda key=key: _build(**{key: True}),
            )
            record = _artifact()
            record[key] = True
            _expect(
                self,
                "RER_SCOPE_VIOLATION",
                lambda record=record: _build(record),
            )

    def test_07_hidden_chain_of_thought_rejected(self) -> None:
        for key in (
            "chain_of_thought",
            "private_reasoning",
            "hidden_reasoning",
            "scratchpad",
        ):
            record = _artifact()
            record[key] = "secret"
            _expect(
                self,
                "RER_COT_FORBIDDEN",
                lambda record=record: _build(record),
            )
        nested = _artifact()
        nested["pre_state"][0]["body"] = {
            "state": "incident-bytes",
            "scratchpad": "secret",
        }
        _expect(self, "RER_COT_FORBIDDEN", lambda: _build(nested))


class TestPreState(unittest.TestCase):
    def test_08_valid_pre_state_body_digest(self) -> None:
        receipt = _build()
        body = {"state": "incident-bytes"}
        self.assertEqual(receipt["pre_state"][0]["body"], body)
        self.assertEqual(receipt["pre_state"][0]["digest"], canonical_digest(body))
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_09_digest_only_pre_state_rejected(self) -> None:
        record = _artifact()
        record["pre_state"][0].pop("body")
        record["pre_state"][0]["digest"] = _OTHER
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(record))

    def test_10_wrong_pre_state_digest_rejected(self) -> None:
        record = _artifact()
        record["pre_state"][0]["digest"] = _OTHER
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_11_empty_pre_state_blocks_recovery(self) -> None:
        record = _artifact()
        record["pre_state"] = []
        record["stop"]["event_order"] = 0
        record["isolation"]["event_order"] = 1
        record["restore_target"]["event_order"] = 2
        record["attempts"][0]["event_order"] = 3
        record["attempts"][0]["verification_checks"][0]["event_order"] = 4
        record["attempts"][0]["verification_checks"][1]["event_order"] = 5
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "NOT_RECOVERED")
        self.assertIs(receipt["recovered"], False)

    def test_12_pre_state_after_restore_rejected(self) -> None:
        record = _artifact()
        record["stop"]["event_order"] = 0
        record["isolation"]["event_order"] = 1
        record["restore_target"]["event_order"] = 2
        record["attempts"][0]["event_order"] = 3
        record["pre_state"][0]["event_order"] = 4
        record["attempts"][0]["verification_checks"][0]["event_order"] = 5
        record["attempts"][0]["verification_checks"][1]["event_order"] = 6
        _expect(self, "RER_LINEAGE_INVALID", lambda: _build(record))


class TestStopIsolation(unittest.TestCase):
    def test_13_stop_pass_required_for_bounded(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["stop"]["result"], "OBSERVED_PASS")
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_14_stop_not_observed_blocks(self) -> None:
        record = _artifact()
        record["stop"]["result"] = "NOT_OBSERVED"
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")
        self.assertIs(receipt["recovered"], False)

    def test_15_service_runtime_isolation_not_observed_blocks(self) -> None:
        record = _runtime()
        record["isolation"]["result"] = "NOT_OBSERVED"
        record["isolation"].pop("body")
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")
        self.assertIs(receipt["recovered"], False)

    def test_16_artifact_only_isolation_na_with_justification(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["isolation"]["result"], "NOT_APPLICABLE")
        self.assertTrue(receipt["isolation"]["justification"].strip())
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_17_artifact_only_na_without_justification_rejected(self) -> None:
        record = _artifact()
        record["isolation"].pop("justification")
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(record))

    def test_18_collapsed_stop_isolation_body_rejected(self) -> None:
        shared = {"halt": "one-body"}
        record = _artifact()
        record["stop"]["body"] = shared
        record["isolation"] = _isolation_pass(shared)
        _expect(self, "RER_LINEAGE_INVALID", lambda: _build(record))


class TestRestoreTarget(unittest.TestCase):
    def test_19_valid_content_digest_target(self) -> None:
        receipt = _build()
        body = {"artifact": "pinned-v1"}
        self.assertEqual(receipt["restore_target"]["binding_kind"], "content_digest")
        self.assertEqual(
            receipt["restore_target"]["binding_value"],
            canonical_digest(body),
        )
        self.assertEqual(receipt["restore_target"]["body"], body)

    def test_20_unpinned_alias_rejected(self) -> None:
        for alias in _UNPINNED:
            record = _artifact()
            record["restore_target"] = {
                "target_id": "restore-target-1",
                "binding_kind": "git_commit",
                "binding_value": alias,
                "source": "git",
                "event_order": 3,
            }
            record["attempts"][0]["target_binding_kind"] = "git_commit"
            record["attempts"][0]["target_binding_value"] = alias
            _expect(
                self,
                "RER_UNBOUND",
                lambda record=record: _build(record),
            )
            versioned = _artifact()
            versioned["restore_target"] = {
                "target_id": "restore-target-1",
                "binding_kind": "immutable_version",
                "binding_value": alias,
                "source": "registry",
                "event_order": 3,
            }
            versioned["attempts"][0]["target_binding_kind"] = "immutable_version"
            versioned["attempts"][0]["target_binding_value"] = alias
            _expect(
                self,
                "RER_UNBOUND",
                lambda record=versioned: _build(record),
            )

    def test_21_wrong_target_digest_rejected(self) -> None:
        record = _artifact()
        record["restore_target"]["binding_value"] = _OTHER
        record["attempts"][0]["target_binding_value"] = _OTHER
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_22_action_target_drift_rejected(self) -> None:
        record = _artifact()
        record["attempts"][0]["target_binding_value"] = _OTHER
        _expect(self, "RER_UNBOUND", lambda: _build(record))
        drifted = _artifact()
        drifted["attempts"][0]["target_id"] = "other-target"
        _expect(self, "RER_UNBOUND", lambda: _build(drifted))

    def test_23_known_good_assertion_rejected(self) -> None:
        record = _artifact()
        record["restore_target"]["known_good"] = True
        _expect(self, "RER_SCOPE_VIOLATION", lambda: _build(record))


class TestAttempts(unittest.TestCase):
    def test_24_valid_restore_action(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["attempts"][0]["action_type"], "RESTORE")
        self.assertEqual(receipt["attempts"][0]["action_result"], "OBSERVED_PASS")
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_25_rollback_does_not_imply_recovered(self) -> None:
        record = _artifact()
        record["attempts"][0]["action_type"] = "ROLLBACK"
        receipt = _build(record)
        self.assertEqual(receipt["attempts"][0]["action_type"], "ROLLBACK")
        self.assertIs(receipt["recovered"], False)
        self.assertNotEqual(receipt["classification"], "RECOVERED")

    def test_26_action_failure_restore_attempted(self) -> None:
        record = _artifact()
        record["attempts"][0]["action_result"] = "OBSERVED_FAIL"
        record["attempts"][0]["result_token"] = "exit-1"
        record["attempts"][0]["verification_checks"] = []
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORE_ATTEMPTED")
        self.assertIs(receipt["recovered"], False)

    def test_27_duplicate_attempt_id_rejected(self) -> None:
        record = _artifact()
        first = copy.deepcopy(record["attempts"][0])
        first["verification_checks"] = []
        second = copy.deepcopy(record["attempts"][0])
        second["event_order"] = 5
        second["result_token"] = "exit-0-retry"
        second["verification_checks"][0]["event_order"] = 6
        second["verification_checks"][1]["event_order"] = 7
        record["attempts"] = [first, second]
        _expect(self, "RER_REPLAY", lambda: _build(record))

    def test_28_same_action_replay_under_new_id_rejected(self) -> None:
        record = _artifact()
        first = copy.deepcopy(record["attempts"][0])
        first["verification_checks"] = []
        second = copy.deepcopy(record["attempts"][0])
        second["attempt_id"] = "att-2"
        second["event_order"] = 5
        second["verification_checks"][0]["event_order"] = 6
        second["verification_checks"][1]["event_order"] = 7
        record["attempts"] = [first, second]
        _expect(self, "RER_REPLAY", lambda: _build(record))

    def test_29_earlier_failed_attempt_preserved_after_later_success(self) -> None:
        record = _artifact()
        failed = copy.deepcopy(record["attempts"][0])
        failed["attempt_id"] = "att-fail"
        failed["action_result"] = "OBSERVED_FAIL"
        failed["result_token"] = "exit-1"
        failed["verification_checks"] = []
        success = copy.deepcopy(record["attempts"][0])
        success["attempt_id"] = "att-ok"
        success["event_order"] = 5
        success["result_token"] = "exit-0-retry"
        success["verification_checks"][0]["event_order"] = 6
        success["verification_checks"][1]["event_order"] = 7
        record["attempts"] = [failed, success]
        receipt = _build(record)
        self.assertEqual(receipt["attempts"][0]["attempt_id"], "att-fail")
        self.assertEqual(receipt["attempts"][0]["action_result"], "OBSERVED_FAIL")
        self.assertEqual(receipt["attempts"][1]["action_result"], "OBSERVED_PASS")
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")
        self.assertIs(receipt["recovered"], False)


class TestVerification(unittest.TestCase):
    def test_30_content_digest_match_valid(self) -> None:
        receipt = _build()
        check = receipt["attempts"][0]["verification_checks"][0]
        self.assertEqual(check["check_kind"], "CONTENT_DIGEST_MATCH")
        self.assertEqual(check["result"], "OBSERVED_PASS")
        self.assertEqual(check["expected"], check["observed"])
        self.assertEqual(check["evidence_digest"], canonical_digest(check["evidence_body"]))

    def test_31_wrong_observed_digest_is_fail(self) -> None:
        record = _artifact()
        wrong = {"artifact": "not-the-target"}
        record["attempts"][0]["verification_checks"][0] = {
            "check_id": "chk-content",
            "check_kind": "CONTENT_DIGEST_MATCH",
            "target": "restore-target-1",
            "expected": canonical_digest({"artifact": "pinned-v1"}),
            "result": "OBSERVED_FAIL",
            "critical": True,
            "event_order": 5,
            "evidence_body": wrong,
        }
        receipt = _build(record)
        check = receipt["attempts"][0]["verification_checks"][0]
        self.assertEqual(check["result"], "OBSERVED_FAIL")
        self.assertEqual(receipt["classification"], "VERIFICATION_FAILED")

    def test_32_caller_pass_contradicting_bytes_rejected(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"][0]["evidence_body"] = {
            "artifact": "not-the-target"
        }
        record["attempts"][0]["verification_checks"][0].pop("observed")
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_33_not_observed_never_pass(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"][0]["result"] = "NOT_OBSERVED"
        record["attempts"][0]["verification_checks"][0].pop("evidence_body")
        record["attempts"][0]["verification_checks"][0].pop("observed")
        receipt = _build(record)
        check = receipt["attempts"][0]["verification_checks"][0]
        self.assertEqual(check["result"], "NOT_OBSERVED")
        self.assertNotEqual(check["result"], "OBSERVED_PASS")
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")

    def test_34_critical_fail_verification_failed(self) -> None:
        record = _artifact()
        wrong = {"artifact": "not-the-target"}
        record["attempts"][0]["verification_checks"][0] = {
            "check_id": "chk-content",
            "check_kind": "CONTENT_DIGEST_MATCH",
            "target": "restore-target-1",
            "expected": canonical_digest({"artifact": "pinned-v1"}),
            "result": "OBSERVED_FAIL",
            "critical": True,
            "event_order": 5,
            "evidence_body": wrong,
        }
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "VERIFICATION_FAILED")

    def test_35_missing_critical_check_restored_unverified(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"] = [
            record["attempts"][0]["verification_checks"][0]
        ]
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")

    def test_36_verify_before_restore_rejected(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"][0]["event_order"] = 3
        record["restore_target"]["event_order"] = 2
        record["isolation"]["event_order"] = 1
        record["stop"]["event_order"] = 0
        record["pre_state"][0]["event_order"] = 5
        _expect(self, "RER_LINEAGE_INVALID", lambda: _build(record))

        ordered = _artifact()
        ordered["attempts"][0]["verification_checks"][0]["event_order"] = 4
        ordered["attempts"][0]["event_order"] = 5
        ordered["attempts"][0]["verification_checks"][1]["event_order"] = 6
        _expect(self, "RER_LINEAGE_INVALID", lambda: _build(ordered))

    def test_37_stale_pre_state_reused_as_post_check_rejected(self) -> None:
        record = _artifact()
        pre_body = record["pre_state"][0]["body"]
        record["attempts"][0]["verification_checks"][0] = _digest_check(
            "chk-content",
            "CONTENT_DIGEST_MATCH",
            pre_body,
            5,
        )
        _expect(self, "RER_LINEAGE_INVALID", lambda: _build(record))

    def test_38_duplicate_check_id_rejected(self) -> None:
        record = _artifact()
        extra = _authority_check(7)
        extra["check_id"] = "chk-content"
        record["attempts"][0]["verification_checks"].append(extra)
        _expect(self, "RER_REPLAY", lambda: _build(record))

    def test_39_check_replay_under_new_id_rejected(self) -> None:
        record = _artifact()
        body = {"artifact": "pinned-v1"}
        record["attempts"][0]["verification_checks"].insert(
            1,
            _digest_check("chk-content-2", "CONTENT_DIGEST_MATCH", body, 6),
        )
        record["attempts"][0]["verification_checks"][2]["event_order"] = 7
        _expect(self, "RER_REPLAY", lambda: _build(record))

    def test_40_config_scope_requires_config_digest_match(self) -> None:
        record = _config()
        record["attempts"][0]["verification_checks"] = [
            item
            for item in record["attempts"][0]["verification_checks"]
            if item["check_kind"] != "CONFIG_DIGEST_MATCH"
        ]
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")
        complete = _build(_config())
        self.assertEqual(complete["classification"], "RECOVERED_BOUNDED")

    def test_41_service_runtime_requires_runtime_critical_pass(self) -> None:
        record = _runtime()
        record["attempts"][0]["verification_checks"] = [
            item
            for item in record["attempts"][0]["verification_checks"]
            if item["check_kind"] != "SERVICE_HEALTH"
        ]
        record["attempts"][0]["verification_checks"][2]["event_order"] = 7
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")
        complete = _build(_runtime())
        self.assertEqual(complete["classification"], "RECOVERED_BOUNDED")


class TestAuthority(unittest.TestCase):
    def test_42_authority_boundary_check_code_derived(self) -> None:
        receipt = _build()
        check = [
            item
            for item in receipt["attempts"][0]["verification_checks"]
            if item["check_kind"] == "AUTHORITY_BOUNDARY_CHECK"
        ][0]
        self.assertEqual(check["observed"], _AUTHORITY_FACTS)
        self.assertEqual(check["expected"], _AUTHORITY_FACTS)
        self.assertEqual(check["result"], "OBSERVED_PASS")

    def test_43_caller_text_cannot_satisfy_authority_check(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"][1]["observed"] = (
            "authority boundary passed"
        )
        _expect(self, "RER_UNBOUND", lambda: _build(record))
        expected = _artifact()
        expected["attempts"][0]["verification_checks"][1]["expected"] = (
            "authority boundary passed"
        )
        _expect(self, "RER_UNBOUND", lambda: _build(expected))

    def test_44_receipt_authority_false_always(self) -> None:
        receipt = _build()
        self.assertIs(receipt["authority"], False)
        runtime = _build(_runtime())
        self.assertIs(runtime["authority"], False)

    def test_45_no_admission_count_or_human_final_output(self) -> None:
        receipt = _build()
        _assert_closed(self, receipt)
        self.assertNotIn("independent_evidence_admitted", receipt)


class TestRisks(unittest.TestCase):
    def test_46_critical_open_blocks_recovered_bounded(self) -> None:
        record = _artifact()
        record["attempts"][0]["unresolved_risks"] = [
            {
                "risk_id": "risk-1",
                "statement": "unsigned artifact",
                "severity": "CRITICAL",
                "status": "OPEN",
                "introduced_event_order": 4,
            }
        ]
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")
        self.assertEqual(receipt["unresolved_risks"][0]["risk_id"], "risk-1")

    def test_47_noncritical_open_retained_in_limitations(self) -> None:
        record = _artifact()
        record["attempts"][0]["unresolved_risks"] = [
            {
                "risk_id": "risk-n",
                "statement": "operator note incomplete",
                "severity": "NONCRITICAL",
                "status": "OPEN",
                "introduced_event_order": 4,
            }
        ]
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")
        self.assertTrue(
            any("operator note incomplete" in item for item in receipt["limitations"])
        )
        self.assertEqual(receipt["unresolved_risks"][0]["severity"], "NONCRITICAL")

    def test_48_risk_resolution_ref_must_bind(self) -> None:
        record = _artifact()
        record["attempts"][0]["unresolved_risks"] = [
            {
                "risk_id": "risk-1",
                "statement": "unsigned artifact",
                "severity": "CRITICAL",
                "status": "RESOLVED",
                "introduced_event_order": 4,
                "resolved_event_order": 4,
                "resolution_ref": _OTHER,
            }
        ]
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_49_open_risk_silent_drop_rejected(self) -> None:
        record = _artifact()
        first = copy.deepcopy(record["attempts"][0])
        first["verification_checks"] = []
        first["result_token"] = "exit-0-first"
        first["unresolved_risks"] = [
            {
                "risk_id": "risk-1",
                "statement": "unsigned artifact",
                "severity": "CRITICAL",
                "status": "OPEN",
                "introduced_event_order": 4,
            }
        ]
        second = copy.deepcopy(record["attempts"][0])
        second["attempt_id"] = "att-2"
        second["event_order"] = 5
        second["result_token"] = "exit-0-retry"
        second["verification_checks"][0]["event_order"] = 6
        second["verification_checks"][1]["event_order"] = 7
        record["attempts"] = [first, second]
        _expect(self, "RER_RISK_DROPPED", lambda: _build(record))

    def test_50_resolved_risk_remains_preserved(self) -> None:
        record = _artifact()
        first = copy.deepcopy(record["attempts"][0])
        first["verification_checks"] = []
        first["result_token"] = "exit-0-first"
        first["unresolved_risks"] = [
            {
                "risk_id": "risk-1",
                "statement": "unsigned artifact",
                "severity": "CRITICAL",
                "status": "OPEN",
                "introduced_event_order": 4,
            }
        ]
        second = copy.deepcopy(record["attempts"][0])
        second["attempt_id"] = "att-2"
        second["event_order"] = 5
        second["result_token"] = "exit-0-retry"
        second["action_output_body"] = {"restored": True}
        second["verification_checks"][0]["event_order"] = 6
        second["verification_checks"][1]["event_order"] = 7
        second["unresolved_risks"] = [
            {
                "risk_id": "risk-1",
                "statement": "unsigned artifact",
                "severity": "CRITICAL",
                "status": "RESOLVED",
                "introduced_event_order": 4,
                "resolved_event_order": 5,
                "resolution_ref": canonical_digest({"restored": True}),
            }
        ]
        record["attempts"] = [first, second]
        receipt = _build(record)
        self.assertEqual(
            receipt["attempts"][0]["unresolved_risks"][0]["status"],
            "OPEN",
        )
        self.assertEqual(
            receipt["attempts"][1]["unresolved_risks"][0]["status"],
            "RESOLVED",
        )
        self.assertEqual(receipt["unresolved_risks"], [])
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")


class TestClassification(unittest.TestCase):
    def test_51_no_action_not_recovered(self) -> None:
        record = _artifact()
        record["attempts"] = []
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "NOT_RECOVERED")
        self.assertIs(receipt["recovered"], False)

    def test_52_successful_action_no_checks_restored_unverified(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"] = []
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")

    def test_53_critical_fail_verification_failed(self) -> None:
        record = _artifact()
        wrong = {"artifact": "not-the-target"}
        record["attempts"][0]["verification_checks"][0] = {
            "check_id": "chk-content",
            "check_kind": "CONTENT_DIGEST_MATCH",
            "target": "restore-target-1",
            "expected": canonical_digest({"artifact": "pinned-v1"}),
            "result": "OBSERVED_FAIL",
            "critical": True,
            "event_order": 5,
            "evidence_body": wrong,
        }
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "VERIFICATION_FAILED")

    def test_54_all_required_checks_pass_recovered_bounded(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_55_recovered_field_remains_false(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")
        self.assertIs(receipt["recovered"], False)

    def test_56_prior_failed_attempt_preserved_after_bounded_recovery(self) -> None:
        record = _artifact()
        failed = copy.deepcopy(record["attempts"][0])
        failed["attempt_id"] = "att-fail"
        failed["action_result"] = "OBSERVED_FAIL"
        failed["result_token"] = "exit-1"
        failed["verification_checks"] = []
        success = copy.deepcopy(record["attempts"][0])
        success["attempt_id"] = "att-ok"
        success["event_order"] = 5
        success["result_token"] = "exit-0-retry"
        success["verification_checks"][0]["event_order"] = 6
        success["verification_checks"][1]["event_order"] = 7
        record["attempts"] = [failed, success]
        receipt = _build(record)
        self.assertEqual(len(receipt["attempts"]), 2)
        self.assertEqual(receipt["attempts"][0]["action_result"], "OBSERVED_FAIL")
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")


class TestIndependentVerification(unittest.TestCase):
    def test_57_absent_iv_allowed_with_limitation(self) -> None:
        receipt = _build()
        self.assertEqual(receipt["independent_verification_refs"], [])
        self.assertIn(
            "independent verification not established",
            receipt["limitations"],
        )

    def test_58_label_only_iv_rejected(self) -> None:
        record = _artifact()
        record["independent_verification_refs"] = [
            {
                "ref_id": "iv-1",
                "source_kind": "INDEPENDENT_VERIFICATION_PREFLIGHT",
                "claim": "looks independently verified",
            }
        ]
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_59_bound_iv_ref_accepted_as_citation(self) -> None:
        record = _artifact()
        record["independent_verification_refs"] = [
            {
                "ref_id": "iv-1",
                "source_kind": "INDEPENDENT_VERIFICATION_PREFLIGHT",
                "claim": "preflight citation only",
                "receipt_digest": _OTHER,
            }
        ]
        receipt = _build(record)
        self.assertEqual(len(receipt["independent_verification_refs"]), 1)
        self.assertEqual(
            receipt["independent_verification_refs"][0]["receipt_digest"],
            _OTHER,
        )
        self.assertIn(
            "independent verification cited but not admitted",
            receipt["limitations"],
        )
        self.assertNotIn(
            "independent verification not established",
            receipt["limitations"],
        )

    def test_60_no_admission_or_count_mutation(self) -> None:
        record = _artifact()
        record["independent_verification_refs"] = [
            {
                "ref_id": "iv-1",
                "source_kind": "EXTERNAL_WITNESS",
                "claim": "external citation",
                "evidence_digest": _OTHER,
            }
        ]
        receipt = _build(record)
        _assert_closed(self, receipt)
        self.assertNotIn("independent_evidence_count", receipt)
        self.assertNotIn("admission_status", receipt)


class TestHumanReview(unittest.TestCase):
    def test_61_human_review_absent_allowed(self) -> None:
        receipt = _build()
        self.assertNotIn("human_review", receipt)
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_62_review_target_digest_recomputed(self) -> None:
        base = _build()
        digest = _review_digest(base)
        record = _artifact()
        record["human_review"] = {
            "selector_is_human": True,
            "review_target_digest": digest,
            "review_outcome": "ACCEPT",
            "authority": False,
        }
        receipt = _build(record)
        self.assertEqual(receipt["human_review"]["review_target_digest"], digest)
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_63_wrong_review_target_digest_rejected(self) -> None:
        record = _artifact()
        record["human_review"] = {
            "selector_is_human": True,
            "review_target_digest": _OTHER,
            "review_outcome": "ACCEPT",
        }
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_64_selector_is_human_exact_true(self) -> None:
        base = _build()
        digest = _review_digest(base)
        record = _artifact()
        record["human_review"] = {
            "selector_is_human": False,
            "review_target_digest": digest,
            "review_outcome": "ACCEPT",
        }
        _expect(self, "RER_UNBOUND", lambda: _build(record))
        numbered = _artifact()
        numbered["human_review"] = {
            "selector_is_human": 1,
            "review_target_digest": digest,
            "review_outcome": "ACCEPT",
        }
        _expect(self, "RER_UNBOUND", lambda: _build(numbered))

    def test_65_human_accept_does_not_change_classification(self) -> None:
        record = _artifact()
        record["attempts"][0]["verification_checks"] = [
            record["attempts"][0]["verification_checks"][0]
        ]
        unverified = _build(record)
        self.assertEqual(unverified["classification"], "RESTORED_UNVERIFIED")
        digest = _review_digest(unverified)
        record["human_review"] = {
            "selector_is_human": True,
            "review_target_digest": digest,
            "review_outcome": "ACCEPT",
            "authority": False,
        }
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")
        self.assertEqual(receipt["human_review"]["review_outcome"], "ACCEPT")
        self.assertIs(receipt["human_review"]["authority"], False)
        self.assertIs(receipt["recovered"], False)

    def test_66_no_circular_receipt_digest_binding(self) -> None:
        base = _build()
        digest = _review_digest(base)
        record = _artifact()
        record["human_review"] = {
            "selector_is_human": True,
            "review_target_digest": digest,
            "review_outcome": "ACCEPT",
        }
        receipt = _build(record)
        self.assertNotEqual(receipt["receipt_digest"], digest)
        self.assertEqual(
            receipt["human_review"]["review_target_digest"],
            digest,
        )
        material = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        self.assertEqual(receipt["receipt_digest"], canonical_digest(material))
        self.assertIn("human_review", material)


class TestSameClassReview(unittest.TestCase):
    def test_split_dict_lookup_cannot_replace_session(self) -> None:
        bound = _artifact()
        live = copy.deepcopy(bound)
        live["recovery_session_id"] = "live-session"
        live["recovered"] = True
        receipt = _build(_SplitDict(bound, live))
        self.assertEqual(receipt["recovery_session_id"], "rec-1")
        self.assertIs(receipt["recovered"], False)

    def test_duplicate_mapping_keys_rejected(self) -> None:
        _expect(self, "RER_SOURCE_INVALID", lambda: _build(_DupKeys()))

    def test_exact_tuple_copied_into_plain_list(self) -> None:
        record = _artifact()
        record["pre_state"] = tuple(record["pre_state"])
        record["attempts"] = tuple(record["attempts"])
        receipt = _build(record)
        self.assertIs(type(receipt["pre_state"]), list)
        self.assertIs(type(receipt["attempts"]), list)
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_caller_owned_list_does_not_survive_into_output(self) -> None:
        record = _artifact()
        original_refs = record["attempts"][0]["changed_object_refs"]
        receipt = _build(record)
        original_refs.append("mutated")
        self.assertEqual(
            receipt["attempts"][0]["changed_object_refs"],
            ["artifact:restore-target-1"],
        )

    def test_out_of_order_attempts_still_carry_risks(self) -> None:
        record = _artifact()
        first = copy.deepcopy(record["attempts"][0])
        first["verification_checks"] = []
        first["result_token"] = "exit-0-first"
        first["unresolved_risks"] = [
            {
                "risk_id": "risk-1",
                "statement": "unsigned artifact",
                "severity": "CRITICAL",
                "status": "OPEN",
                "introduced_event_order": 4,
            }
        ]
        second = copy.deepcopy(record["attempts"][0])
        second["attempt_id"] = "att-2"
        second["event_order"] = 5
        second["result_token"] = "exit-0-retry"
        second["verification_checks"][0]["event_order"] = 6
        second["verification_checks"][1]["event_order"] = 7
        record["attempts"] = [second, first]
        _expect(self, "RER_RISK_DROPPED", lambda: _build(record))

    def test_duplicate_event_order_rejected(self) -> None:
        record = _artifact()
        record["stop"]["event_order"] = 0
        _expect(self, "RER_LINEAGE_INVALID", lambda: _build(record))

    def test_git_commit_target_accepted(self) -> None:
        record = _artifact()
        record["restore_target"] = {
            "target_id": "restore-target-1",
            "binding_kind": "git_commit",
            "binding_value": _GIT,
            "source": "git",
            "event_order": 3,
        }
        record["attempts"][0]["target_binding_kind"] = "git_commit"
        record["attempts"][0]["target_binding_value"] = _GIT
        receipt = _build(record)
        self.assertEqual(receipt["restore_target"]["binding_value"], _GIT)
        self.assertEqual(receipt["classification"], "RECOVERED_BOUNDED")

    def test_service_runtime_auto_custody_gap_is_single_critical_open(self) -> None:
        record = _runtime()
        record["attempts"][0]["verification_checks"] = [
            item
            for item in record["attempts"][0]["verification_checks"]
            if item["check_kind"] != "SIGNATURE_CHECK"
        ]
        receipt = _build(record)
        custody = [
            item
            for item in receipt["unresolved_risks"]
            if item["risk_id"] == "custody-gap"
        ]
        self.assertEqual(len(custody), 1)
        self.assertEqual(custody[0]["severity"], "CRITICAL")
        self.assertEqual(custody[0]["status"], "OPEN")
        self.assertEqual(receipt["classification"], "RESTORED_UNVERIFIED")

    def test_conflicting_iv_digests_rejected(self) -> None:
        record = _artifact()
        record["independent_verification_refs"] = [
            {
                "ref_id": "iv-1",
                "source_kind": "EXTERNAL_WITNESS",
                "claim": "conflict",
                "receipt_digest": _OTHER,
                "evidence_digest": "ef" * 32,
            }
        ]
        _expect(self, "RER_UNBOUND", lambda: _build(record))

    def test_stop_fail_is_verification_failed(self) -> None:
        record = _artifact()
        record["stop"]["result"] = "OBSERVED_FAIL"
        receipt = _build(record)
        self.assertEqual(receipt["classification"], "VERIFICATION_FAILED")

    def test_human_review_authority_true_rejected(self) -> None:
        base = _build()
        digest = _review_digest(base)
        record = _artifact()
        record["human_review"] = {
            "selector_is_human": True,
            "review_target_digest": digest,
            "review_outcome": "ACCEPT",
            "authority": True,
        }
        _expect(self, "RER_SCOPE_VIOLATION", lambda: _build(record))


class TestNoAcceptedWrites(unittest.TestCase):
    def test_generation_does_not_write_accepted_trees(self) -> None:
        before = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        _build()
        after = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        self.assertEqual(before, after)
        for line in after.splitlines():
            path = line[3:].strip().strip('"')
            self.assertTrue(path.startswith("recovery_execution_receipt_v0"), path)


if __name__ == "__main__":
    unittest.main()
