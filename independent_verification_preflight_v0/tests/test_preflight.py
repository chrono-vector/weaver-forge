"""Focused tests for Independent Verification Preflight v0."""

from __future__ import annotations

import copy
import json
import unittest
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

from audit_lifecycle.epistemic.provenance import (
    INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
)
from audit_lifecycle.epistemic.reconstructability import (
    ReconstructabilityInputs,
    derive_reconstructability_report,
)
from audit_lifecycle.epistemic.serialize import canonical_digest
from independent_verification_preflight_v0 import (
    IndependentVerificationPreflightError,
    build_independent_verification_preflight,
)
from independent_verification_preflight_v0 import preflight as preflight_module

CLAIM_ID = "AUR-A-001"
_SHA = "ab" * 32
_OTHER = "cd" * 32
_LIMITATIONS = [
    "admitted independent evidence",
    "accepted independent reproduction",
    "truth",
    "global safety",
    "observer authority",
    "Human Final",
    "canonical status",
    "published status",
    "deployed status",
    "recovery",
    "rollback",
    "external witness admission",
]
_UNPINNED = (
    "HEAD",
    "latest",
    "main",
    "master",
    "origin/main",
    "origin/master",
    "current",
    "same as above",
    " Head ",
)
_LEAF_TYPES = (str, bool, int, float)
_FORBIDDEN_RECEIPT_KEYS = {
    "independent_evidence_count",
    "claims_iw_acceptance",
    "claims_independent_witness",
    "independent",
    "independence_score",
    "human_final",
    "human_final_status",
    "is_human_final",
    "creates_human_final",
    "promotes_to_human_final",
    "promoted",
    "decision",
}


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
        return iter(("claim_id",))

    def __len__(self) -> int:
        return 2

    def items(self):
        return [("claim_id", CLAIM_ID), ("claim_id", "OTHER")]


class _BadKey(Mapping):
    def __getitem__(self, key: str):
        raise AssertionError("live lookup")

    def __iter__(self):
        return iter(())

    def __len__(self) -> int:
        return 1

    def items(self):
        return [(1, "a")]


def _decision(claim_id: str = CLAIM_ID, token: str = "PASS") -> dict:
    return {
        "decision": token,
        "claim_id": claim_id,
        "promoted": False,
        "reason": "ALL_REQUIRED_VECTORS_PASS",
        "broader_classification": "CLAIM_SUPPORTED_PARTIAL",
        "promoted_to_full": False,
        "claim_result": token,
    }


def _pin(sha: str = _SHA, relative: str = "payload.txt") -> dict:
    return {
        "classification": "PINNED_INPUT",
        "expected_sha256": None,
        "files": [{"relative_path": relative, "sha256": sha, "bytes": 4}],
        "modified": False,
        "origin_absolute": r"C:\dev\Weaver\weaver-forge\phase6_third_party_target",
        "pinned_root": r"C:\dev\Weaver\weaver-forge\phase61_runs\example\pinned_target",
    }


def _cited(
    *,
    pin: dict | None = None,
    decision: dict | None = None,
    claim: dict | None = None,
    include_audit_request: bool = True,
    claim_id: str = CLAIM_ID,
) -> dict:
    if decision is None:
        decision = _decision(claim_id=claim_id)
    if claim is None:
        claim = {"claim_id": claim_id, "statement": "document digest matches"}
    if pin is None:
        pin = _pin()
    scope = {
        "allowed_write_boundary": ["audit/**"],
        "policy": {"name": "hash_claim"},
    }
    audit_request = None
    if include_audit_request:
        audit_request = {
            "claim": {"id": claim["claim_id"], "statement": "document digest matches"}
        }
    report = derive_reconstructability_report(
        ReconstructabilityInputs(
            audit_id="WFA-IVP",
            claim=claim,
            scope=scope,
            audit_request=audit_request,
            provenance_pin=pin,
            decision=decision,
        )
    )
    return {
        "decision": decision,
        "claim": claim,
        "pin": pin,
        "report": report.to_dict(),
    }


def _evidence(body: dict, *, digest: str | None = None, label: str | None = None) -> dict:
    record = {"body": body}
    if digest is not None:
        record["digest"] = digest
    if label is not None:
        record["label"] = label
    return record


def _environment(
    record: dict,
    *,
    fingerprint: str | None = None,
    label: str | None = None,
) -> dict:
    wrapped = {"record": record}
    if fingerprint is not None:
        wrapped["fingerprint"] = fingerprint
    if label is not None:
        wrapped["label"] = label
    return wrapped


def _execution(
    execution_id: str,
    runner: str,
    payload: str,
    *,
    env: dict | None = None,
    body: dict | None = None,
    label: str | None = None,
    env_label: str | None = None,
    digest: str | None = None,
    fingerprint: str | None = None,
) -> dict:
    return {
        "execution_id": execution_id,
        "environment": _environment(
            {"runner": runner} if env is None else env,
            fingerprint=fingerprint,
            label=env_label,
        ),
        "evidence": _evidence(
            {"payload": payload} if body is None else body,
            digest=digest,
            label=label,
        ),
    }


def _reproduction(**overrides) -> dict:
    candidate = {
        "verification_kind": "REPRODUCTION",
        "claim_id": CLAIM_ID,
        "input_record": {"payload": "input"},
        "result_token": "PASS",
        "source_execution": _execution("run-source", "alpha", "left"),
        "independent_execution": _execution("run-independent", "beta", "right"),
    }
    candidate.update(overrides)
    return candidate


def _challenge(
    cited: dict,
    *,
    present: bool = False,
    counterexample: dict | None = None,
    assumptions: list | None = None,
    evidence: dict | None = None,
) -> dict:
    if assumptions is None:
        assumptions = [cited["report"]["canonical_input_digests"]["CLAIM.json"]]
    candidate = {
        "verification_kind": "CHALLENGE",
        "claim_id": cited["claim"]["claim_id"],
        "challenge_evidence": evidence or {"body": {"payload": "challenge"}},
        "assumptions_attacked": assumptions,
        "counterexample_present": present,
    }
    if counterexample is not None:
        candidate["counterexample"] = counterexample
    return candidate


def _build(candidate: dict | None = None, cited: dict | None = None, **kwargs):
    if cited is None:
        cited = _cited()
    if candidate is None:
        candidate = _reproduction()
    return build_independent_verification_preflight(
        cited["decision"],
        cited["claim"],
        cited["pin"],
        cited["report"],
        candidate,
        **kwargs,
    )


def _expect(test: unittest.TestCase, code: str, fn) -> None:
    with test.assertRaises(IndependentVerificationPreflightError) as caught:
        fn()
    test.assertEqual(caught.exception.code, code)


def _assert_plain(test: unittest.TestCase, value, *, key: str | None = None) -> None:
    if value is None or type(value) in _LEAF_TYPES:
        return
    if type(value) is dict:
        for child_key, child in value.items():
            test.assertIs(type(child_key), str)
            _assert_plain(test, child, key=child_key)
        return
    if type(value) is list:
        for child in value:
            _assert_plain(test, child)
        return
    test.fail(f"unstable type {type(value).__name__} at {key}")


def _assert_closed(test: unittest.TestCase, receipt: dict) -> None:
    test.assertIs(type(receipt), dict)
    test.assertEqual(receipt["schema_version"], "independent_verification_preflight.v0")
    test.assertIs(receipt["authority"], False)
    test.assertEqual(receipt["admission_status"], "NOT_CONFIGURED")
    test.assertEqual(receipt["admission_status"], INDEPENDENT_EVIDENCE_ADMISSION_STATUS)
    test.assertEqual(receipt["limitations"], _LIMITATIONS)
    test.assertTrue(_FORBIDDEN_RECEIPT_KEYS.isdisjoint(receipt))
    _assert_plain(test, receipt)


def _report_with_assumption(report: dict, text: str) -> dict:
    body = {key: value for key, value in report.items() if key != "report_digest"}
    assumptions = sorted(set([*body["unresolved_assumptions"], text]))
    body["unresolved_assumptions"] = assumptions
    stored = dict(body)
    stored["report_digest"] = canonical_digest(body)
    return stored


class IndependentVerificationPreflightTests(unittest.TestCase):
    def test_01_wrong_claim_id_rejected(self) -> None:
        cited = _cited()
        _expect(
            self,
            "IVP_CLAIM_MISMATCH",
            lambda: _build(_reproduction(claim_id="AUR-A-002"), cited),
        )
        mismatched = _cited(
            decision=_decision(claim_id="AUR-A-002"),
            claim={"claim_id": CLAIM_ID, "statement": "document digest matches"},
        )
        _expect(self, "IVP_CLAIM_MISMATCH", lambda: _build(cited=mismatched))
        drifted = _cited()
        drifted["claim"] = {
            "claim_id": CLAIM_ID,
            "statement": "a different statement",
        }
        _expect(self, "IVP_CLAIM_MISMATCH", lambda: _build(cited=drifted))

    def test_02_mutable_revision_name_rejected(self) -> None:
        for name in _UNPINNED:
            pin = _pin(sha=name)
            cited = _cited(pin=pin)
            _expect(self, "IVP_REVISION_UNBOUND", lambda cited=cited: _build(cited=cited))
        pin = _pin(relative="latest")
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=_cited(pin=pin)))
        pin = _pin()
        pin["expected_sha256"] = "HEAD"
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=_cited(pin=pin)))

    def test_03_mismatched_pin_rejected(self) -> None:
        cited = _cited()
        cited["pin"] = _pin(sha=_OTHER)
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=cited))
        cited = _cited()
        cited["pin"] = _pin(relative="../payload.txt")
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=cited))

    def test_04_caller_digest_mismatch_rejected(self) -> None:
        bad = _execution("run-source", "alpha", "left", digest=_OTHER)
        candidate = _reproduction(source_execution=bad)
        _expect(self, "IVP_EVIDENCE_DIGEST_INVALID", lambda: _build(candidate))
        upper = canonical_digest({"payload": "left"}).upper()
        upper_execution = _execution("run-source", "alpha", "left", digest=upper)
        _expect(
            self,
            "IVP_EVIDENCE_DIGEST_INVALID",
            lambda: _build(_reproduction(source_execution=upper_execution)),
        )

    def test_05_digest_strings_without_bodies_rejected(self) -> None:
        candidate = _reproduction()
        candidate["source_evidence_digest"] = _SHA
        candidate["evidence_digest"] = _OTHER
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(candidate))
        naked = _reproduction(
            source_execution={
                "execution_id": "run-source",
                "environment": _environment({"runner": "alpha"}),
                "evidence": {"digest": _SHA},
            }
        )
        _expect(self, "IVP_EVIDENCE_DIGEST_INVALID", lambda: _build(naked))
        string_body = _reproduction(
            source_execution=_execution("run-source", "alpha", "left", body=_SHA)
        )
        _expect(self, "IVP_EVIDENCE_DIGEST_INVALID", lambda: _build(string_body))

    def test_06_same_evidence_different_labels_duplicate(self) -> None:
        candidate = _reproduction(
            source_execution=_execution("run-source", "alpha", "left", label="source"),
            independent_execution=_execution(
                "run-independent",
                "beta",
                "left",
                label="independent",
            ),
        )
        receipt = _build(candidate)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertEqual(
            receipt["source_execution_summary"]["evidence_digest"],
            receipt["independent_execution_summary"]["evidence_digest"],
        )
        _assert_closed(self, receipt)

    def test_07_evidence_container_subclass_rejected(self) -> None:
        class _EvidenceList(list):
            pass

        class _BodyMap(dict):
            def __getitem__(self, key):
                return "attack"

            def items(self):
                return [("payload", "left")]

        attacked = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                body=_EvidenceList([{"payload": "left"}]),
            )
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(attacked))
        neutralized = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                body=_BodyMap({"payload": "attack"}),
            )
        )
        receipt = _build(neutralized)
        self.assertEqual(
            receipt["source_execution_summary"]["evidence_digest"],
            canonical_digest({"payload": "left"}),
        )
        self.assertNotEqual(
            receipt["source_execution_summary"]["evidence_digest"],
            canonical_digest({"payload": "attack"}),
        )

    def test_08_fingerprint_mismatch_rejected(self) -> None:
        bad = _execution("run-source", "alpha", "left", fingerprint=_OTHER)
        _expect(
            self,
            "IVP_ENVIRONMENT_UNBOUND",
            lambda: _build(_reproduction(source_execution=bad)),
        )
        upper = canonical_digest({"runner": "alpha"}).upper()
        upper_execution = _execution("run-source", "alpha", "left", fingerprint=upper)
        _expect(
            self,
            "IVP_ENVIRONMENT_UNBOUND",
            lambda: _build(_reproduction(source_execution=upper_execution)),
        )

    def test_09_fingerprint_strings_without_records_rejected(self) -> None:
        candidate = _reproduction()
        candidate["source_environment_fingerprint"] = _SHA
        candidate["environment_fingerprint"] = _OTHER
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(candidate))
        naked = _reproduction(
            source_execution={
                "execution_id": "run-source",
                "environment": {"fingerprint": _SHA},
                "evidence": _evidence({"payload": "left"}),
            }
        )
        _expect(self, "IVP_ENVIRONMENT_UNBOUND", lambda: _build(naked))
        prose = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                env="different machine",
            )
        )
        _expect(self, "IVP_ENVIRONMENT_UNBOUND", lambda: _build(prose))

    def test_10_same_environment_different_labels_not_independent(self) -> None:
        candidate = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                env_label="machine-a",
            ),
            independent_execution=_execution(
                "run-independent",
                "alpha",
                "right",
                env_label="machine-b",
            ),
        )
        receipt = _build(candidate)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertEqual(
            receipt["source_execution_summary"]["environment_fingerprint"],
            receipt["independent_execution_summary"]["environment_fingerprint"],
        )

    def test_11_hostile_environment_rejected(self) -> None:
        unknown = _execution(
            "run-source",
            "alpha",
            "left",
            env={"runner": "alpha", "machine": "different machine"},
        )
        _expect(
            self,
            "IVP_ENVIRONMENT_UNBOUND",
            lambda: _build(_reproduction(source_execution=unknown)),
        )
        class _EnvList(list):
            pass

        nested = _execution(
            "run-source",
            "alpha",
            "left",
            env={"runner": _EnvList(["alpha"])},
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(_reproduction(source_execution=nested)))
        bound = {"runner": "alpha"}
        live = {"runner": "attacker", "machine": "different machine"}
        split = _execution(
            "run-source",
            "alpha",
            "left",
            env=_SplitView(bound, live),
            fingerprint=canonical_digest({"runner": "alpha"}),
        )
        receipt = _build(_reproduction(source_execution=split))
        self.assertEqual(
            receipt["source_execution_summary"]["environment_fingerprint"],
            canonical_digest({"runner": "alpha"}),
        )

    def test_12_execution_ids_alone_insufficient(self) -> None:
        candidate = _reproduction(
            source_execution=_execution("run-source", "alpha", "left"),
            independent_execution=_execution("run-independent", "alpha", "left"),
        )
        receipt = _build(candidate)
        self.assertNotEqual(
            receipt["source_execution_summary"]["execution_id"],
            receipt["independent_execution_summary"]["execution_id"],
        )
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)
        _assert_closed(self, receipt)

    def test_13_same_execution_id_duplicate(self) -> None:
        candidate = _reproduction(
            source_execution=_execution("same-run", "alpha", "left"),
            independent_execution=_execution("same-run", "beta", "right"),
        )
        receipt = _build(candidate)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)

    def test_14_caller_cannot_inject_independent_true(self) -> None:
        candidate = _reproduction()
        candidate["independent"] = True
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(candidate))
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(independent=True))
        nested = _reproduction(
            source_execution={
                "execution_id": "run-source",
                "environment": _environment({"runner": "alpha"}),
                "evidence": _evidence({"payload": "left"}),
                "independent": True,
            }
        )
        _expect(self, "IVP_EXECUTION_INVALID", lambda: _build(nested))

    def test_15_fully_bound_reproduction(self) -> None:
        cited = _cited()
        first = _build(cited=cited)
        second = _build(cited=cited)
        self.assertEqual(first, second)
        self.assertEqual(first["verification_kind"], "REPRODUCTION")
        self.assertEqual(first["classification"], "BOUND_CANDIDATE")
        self.assertIs(first["structural_candidate"], True)
        self.assertEqual(first["claim_id"], CLAIM_ID)
        self.assertEqual(
            first["artifact_revision_binding"],
            {"files": [{"relative_path": "payload.txt", "sha256": _SHA}]},
        )
        blob = json.dumps(first)
        self.assertNotIn("phase6_third_party_target", blob)
        self.assertNotIn("pinned_root", blob)
        self.assertNotIn("expected_sha256", blob)
        source = first["source_execution_summary"]
        independent = first["independent_execution_summary"]
        self.assertEqual(source["execution_id"], "run-source")
        self.assertEqual(independent["execution_id"], "run-independent")
        self.assertEqual(source["evidence_digest"], canonical_digest({"payload": "left"}))
        self.assertEqual(
            independent["evidence_digest"],
            canonical_digest({"payload": "right"}),
        )
        self.assertEqual(
            source["environment_fingerprint"],
            canonical_digest({"runner": "alpha"}),
        )
        self.assertEqual(
            independent["environment_fingerprint"],
            canonical_digest({"runner": "beta"}),
        )
        self.assertEqual(source["input_digest"], canonical_digest({"payload": "input"}))
        self.assertEqual(source["result_token"], "PASS")
        self.assertEqual(independent["result_token"], "PASS")
        self.assertNotIn("record_digest", source)
        _assert_closed(self, first)

    def test_16_result_token_mismatch_not_independent(self) -> None:
        receipt = _build(_reproduction(result_token="FAIL"))
        self.assertEqual(receipt["classification"], "NOT_INDEPENDENT")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertEqual(receipt["source_execution_summary"]["result_token"], "FAIL")
        folded = _build(_reproduction(result_token="pass"))
        self.assertEqual(folded["classification"], "NOT_INDEPENDENT")
        self.assertIs(folded["structural_candidate"], False)

    def test_17_same_evidence_or_environment_not_candidate(self) -> None:
        same_evidence = _reproduction(
            independent_execution=_execution("run-independent", "beta", "left")
        )
        same_environment = _reproduction(
            independent_execution=_execution("run-independent", "alpha", "right")
        )
        for candidate in (same_evidence, same_environment):
            receipt = _build(candidate)
            self.assertIs(receipt["structural_candidate"], False)
            self.assertEqual(receipt["classification"], "DUPLICATE")

    def test_18_provider_or_model_alone_insufficient(self) -> None:
        alone = _reproduction(
            source_execution=_execution("run-source", "alpha", "left"),
            independent_execution=_execution("run-independent", "alpha", "left"),
            backend_provider="other-provider",
            model="other-model",
            observer_basis="DISTINCT_OBSERVER",
        )
        receipt = _build(alone)
        self.assertIs(receipt["structural_candidate"], False)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertEqual(receipt["descriptive"]["backend_provider"], "other-provider")
        self.assertIs(receipt["descriptive"]["authority"], False)
        self.assertIs(receipt["observer"]["authority"], False)
        backend_only = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                env={"runner": "alpha", "backend": "alpha-backend"},
            ),
            independent_execution=_execution(
                "run-independent",
                "beta",
                "left",
                env={"runner": "alpha", "backend": "beta-backend"},
            ),
        )
        backend_receipt = _build(backend_only)
        self.assertIs(backend_receipt["structural_candidate"], False)
        self.assertEqual(backend_receipt["classification"], "DUPLICATE")

    def test_19_challenge_never_sets_structural_candidate(self) -> None:
        cited = _cited()
        body = {"payload": "counter"}
        candidate = _challenge(
            cited,
            present=True,
            counterexample={"body": body},
        )
        candidate["observer_basis"] = "INDEPENDENT_REPRODUCTION"
        candidate["model"] = "other-model"
        receipt = _build(candidate, cited)
        self.assertEqual(receipt["verification_kind"], "CHALLENGE")
        self.assertEqual(receipt["classification"], "CHALLENGE_RECORDED")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertIs(receipt["observer"]["authority"], False)
        self.assertIs(receipt["descriptive"]["authority"], False)
        _assert_closed(self, receipt)

    def test_20_counterexample_required_when_present(self) -> None:
        cited = _cited()
        _expect(
            self,
            "IVP_CHALLENGE_INVALID",
            lambda: _build(_challenge(cited, present=True), cited),
        )

    def test_21_counterexample_forbidden_when_absent(self) -> None:
        cited = _cited()
        candidate = _challenge(
            cited,
            present=False,
            counterexample={"body": {"payload": "counter"}},
        )
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(candidate, cited))

    def test_22_prose_assumptions_rejected(self) -> None:
        cited = _cited()
        for prose in (
            "the claim is false",
            "different machine",
            "independent environment",
            CLAIM_ID,
            "HEAD",
        ):
            candidate = _challenge(cited, assumptions=[prose])
            _expect(
                self,
                "IVP_CHALLENGE_INVALID",
                lambda candidate=candidate: _build(candidate, cited),
            )
        unknown = _challenge(cited, assumptions=["12" * 32])
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(unknown, cited))

    def test_23_failed_challenge_does_not_strengthen_decision(self) -> None:
        cited = _cited()
        before = copy.deepcopy(cited["decision"])
        receipt = _build(_challenge(cited, present=False), cited)
        self.assertEqual(cited["decision"], before)
        self.assertEqual(receipt["classification"], "CHALLENGE_RECORDED")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertIs(
            receipt["independent_execution_summary"]["counterexample_present"],
            False,
        )
        self.assertNotIn(
            "counterexample_body",
            receipt["independent_execution_summary"],
        )
        self.assertNotIn("counterexample_digest", receipt["independent_execution_summary"])
        _assert_closed(self, receipt)

    def test_24_bound_challenge_preserved(self) -> None:
        cited = _cited()
        body = {"payload": "counter", "claims_iw_acceptance": True}
        claim_digest = cited["report"]["canonical_input_digests"]["CLAIM.json"]
        decision_digest = cited["report"]["canonical_input_digests"]["DECISION.json"]
        pin_digest = cited["report"]["canonical_input_digests"]["PROVENANCE.json"]
        entry_digest = canonical_digest(
            {"relative_path": "payload.txt", "sha256": _SHA}
        )
        assumptions = [claim_digest, decision_digest, pin_digest, entry_digest]
        candidate = _challenge(
            cited,
            present=True,
            assumptions=assumptions,
            counterexample={"body": body, "label": "counter-label"},
        )
        receipt = _build(candidate, cited)
        summary = receipt["independent_execution_summary"]
        self.assertEqual(summary["counterexample_present"], True)
        self.assertEqual(summary["counterexample_digest"], canonical_digest(body))
        self.assertEqual(summary["counterexample_body"], body)
        self.assertNotIn("label", summary["counterexample_body"])
        self.assertEqual(
            receipt["source_execution_summary"]["assumptions_attacked"],
            assumptions,
        )
        self.assertEqual(
            receipt["source_execution_summary"]["evidence_digest"],
            canonical_digest({"payload": "challenge"}),
        )
        self.assertIs(receipt["structural_candidate"], False)
        self.assertIs(receipt["authority"], False)
        self.assertNotIn("claims_iw_acceptance", receipt)
        bare_file_hash = _challenge(cited, assumptions=[_SHA])
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(bare_file_hash, cited))

    def test_25_admission_status_always_not_configured(self) -> None:
        self.assertEqual(INDEPENDENT_EVIDENCE_ADMISSION_STATUS, "NOT_CONFIGURED")
        cited = _cited()
        reproduction = _build(cited=cited)
        challenge = _build(_challenge(cited), cited)
        duplicate = _build(
            _reproduction(
                independent_execution=_execution("run-independent", "beta", "left")
            )
        )
        for receipt in (reproduction, challenge, duplicate):
            self.assertEqual(receipt["admission_status"], "NOT_CONFIGURED")
            self.assertNotIn("independent_evidence_count", receipt)
            _assert_closed(self, receipt)

    def test_26_count_cannot_be_supplied(self) -> None:
        candidate = _reproduction()
        candidate["independent_evidence_count"] = 1
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(candidate))
        zero = _reproduction()
        zero["independent_evidence_count"] = 0
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(zero))
        _expect(
            self,
            "IVP_SCOPE_VIOLATION",
            lambda: _build(independent_evidence_count=1),
        )

    def test_27_claims_iw_acceptance_rejected(self) -> None:
        candidate = _reproduction()
        candidate["claims_iw_acceptance"] = True
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(candidate))
        witness = _reproduction()
        witness["claims_independent_witness"] = True
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(witness))
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(claims_iw_acceptance=True))

    def test_28_authority_true_rejected(self) -> None:
        candidate = _reproduction()
        candidate["authority"] = True
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(candidate))
        false_authority = _reproduction()
        false_authority["authority"] = False
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(false_authority))
        _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(authority=True))

    def test_29_human_final_rejected(self) -> None:
        for key in (
            "human_final",
            "human_final_status",
            "is_human_final",
            "creates_human_final",
            "promotes_to_human_final",
        ):
            candidate = _reproduction()
            candidate[key] = True
            _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(candidate))
            _expect(self, "IVP_SCOPE_VIOLATION", lambda: _build(**{key: True}))

    def test_30_hook_not_invoked(self) -> None:
        source = Path(preflight_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("run_independent_verification_hook", source)
        self.assertNotIn("is_qualified", source)
        self.assertNotIn("QUALIFIED_INDEPENDENCE_BASES", source)
        self.assertNotIn("external_verifications", source)
        self.assertNotIn("INDEPENDENT_VERIFICATION.json", source)
        self.assertNotIn("campaign_runner", source)
        self.assertFalse(hasattr(preflight_module, "run_independent_verification_hook"))

        def _boom(*_args, **_kwargs):
            raise AssertionError("hook invoked")

        with patch(
            "audit_lifecycle.independent_verification.run_independent_verification_hook",
            _boom,
        ):
            receipt = _build()
        self.assertIs(receipt["structural_candidate"], True)
        self.assertNotIn("independent_evidence_count", receipt)

    def test_31_duplicate_evidence_digest_detected(self) -> None:
        candidate = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                digest=canonical_digest({"payload": "left"}),
            ),
            independent_execution=_execution(
                "run-independent",
                "beta",
                "left",
                digest=canonical_digest({"payload": "left"}),
            ),
        )
        receipt = _build(candidate)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertNotIn("independent_evidence_count", receipt)

    def test_32_duplicate_execution_record_detected(self) -> None:
        shared = _execution("same-run", "alpha", "left")
        candidate = _reproduction(
            source_execution=copy.deepcopy(shared),
            independent_execution=copy.deepcopy(shared),
        )
        receipt = _build(candidate)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertNotIn("independent_evidence_count", receipt)

    def test_33_duplicate_package_entries_do_not_inflate(self) -> None:
        duplicate_rows = _reproduction(
            package_entries=[
                {"body": {"payload": "extra"}},
                {"body": {"payload": "extra"}, "label": "renamed"},
            ]
        )
        receipt = _build(duplicate_rows)
        self.assertEqual(receipt["classification"], "DUPLICATE")
        self.assertIs(receipt["structural_candidate"], False)
        self.assertNotIn("independent_evidence_count", receipt)
        self.assertNotIn("package_entries", receipt)
        overlaps_source = _reproduction(
            package_entries=[{"body": {"payload": "left"}, "label": "copied"}]
        )
        overlap = _build(overlaps_source)
        self.assertEqual(overlap["classification"], "DUPLICATE")
        self.assertNotIn("independent_evidence_count", overlap)
        unique = _reproduction(package_entries=[{"body": {"payload": "extra"}}])
        unique_receipt = _build(unique)
        self.assertEqual(unique_receipt["classification"], "BOUND_CANDIDATE")
        self.assertIs(unique_receipt["structural_candidate"], True)
        self.assertNotIn("independent_evidence_count", unique_receipt)
        self.assertNotIn("package_entries", unique_receipt)

    def test_34_split_mapping_neutralized(self) -> None:
        cited = _cited()
        bound = _reproduction()
        live = _reproduction()
        live["independent"] = True
        live["classification"] = "BOUND_CANDIDATE"
        live["claim_id"] = "OTHER"
        live["structural_candidate"] = True
        receipt = _build(_SplitView(bound, live), cited)
        self.assertEqual(receipt["classification"], "BOUND_CANDIDATE")
        self.assertEqual(receipt["claim_id"], CLAIM_ID)
        self.assertNotIn("independent", receipt)
        attacked_pin = _pin(sha="latest")
        pinned = build_independent_verification_preflight(
            cited["decision"],
            cited["claim"],
            _SplitView(cited["pin"], attacked_pin),
            cited["report"],
            _reproduction(),
        )
        self.assertEqual(
            pinned["artifact_revision_binding"]["files"][0]["sha256"],
            _SHA,
        )

    def test_35_scalar_subclass_rejected(self) -> None:
        for candidate in (
            _reproduction(
                source_execution=_execution(_HostileStr("run-source"), "alpha", "left")
            ),
            _reproduction(result_token=_HostileStr("PASS")),
            _reproduction(claim_id=_HostileStr(CLAIM_ID)),
        ):
            _expect(self, "IVP_SOURCE_INVALID", lambda candidate=candidate: _build(candidate))
        hostile_bool = _reproduction(
            source_execution=_execution(_HostileInt(1), "alpha", "left")
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(hostile_bool))
        cited = _cited()
        cited["decision"]["reason"] = _HostileStr("ALL_REQUIRED_VECTORS_PASS")
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(cited=cited))

    def test_36_container_subclass_rejected(self) -> None:
        rows = _reproduction(package_entries=_Rows([{"body": {"payload": "extra"}}]))
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(rows))
        reused = _reproduction(
            package_entries=_Reuse(({"body": {"payload": "extra"}},))
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(reused))
        cited = _cited()
        assumptions = _Rows([cited["report"]["canonical_input_digests"]["CLAIM.json"]])
        _expect(
            self,
            "IVP_SOURCE_INVALID",
            lambda: _build(_challenge(cited, assumptions=assumptions), cited),
        )
        pin = _pin()
        pin["files"] = _Rows(pin["files"])
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(cited=_cited(pin=pin)))

    def test_37_caller_containers_do_not_survive(self) -> None:
        cited = _cited()
        source_body = {"payload": "left"}
        independent_body = {"payload": "right"}
        source_env = {"runner": "alpha"}
        independent_env = {"runner": "beta"}
        input_record = {"payload": "input"}
        candidate = _reproduction(
            input_record=input_record,
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                env=source_env,
                body=source_body,
            ),
            independent_execution=_execution(
                "run-independent",
                "beta",
                "right",
                env=independent_env,
                body=independent_body,
            ),
        )
        before = copy.deepcopy(cited["decision"])
        receipt = _build(candidate, cited)
        source_body["payload"] = "changed"
        independent_body["payload"] = "changed"
        source_env["runner"] = "changed"
        independent_env["os"] = "changed"
        input_record["payload"] = "changed"
        candidate["result_token"] = "FAIL"
        cited["decision"]["decision"] = "FAIL"
        self.assertEqual(receipt["classification"], "BOUND_CANDIDATE")
        self.assertEqual(
            receipt["source_execution_summary"]["evidence_digest"],
            canonical_digest({"payload": "left"}),
        )
        self.assertEqual(
            receipt["source_execution_summary"]["environment_fingerprint"],
            canonical_digest({"runner": "alpha"}),
        )
        self.assertEqual(
            receipt["source_execution_summary"]["input_digest"],
            canonical_digest({"payload": "input"}),
        )
        self.assertEqual(receipt["source_execution_summary"]["result_token"], "PASS")
        self.assertEqual(before["decision"], "PASS")
        self.assertIsNot(receipt["artifact_revision_binding"], cited["pin"])
        self.assertIsNot(receipt["limitations"], _LIMITATIONS)
        counter_body = {"payload": "counter"}
        challenge_cited = _cited()
        challenge = _challenge(
            challenge_cited,
            present=True,
            counterexample={"body": counter_body},
        )
        challenge_receipt = _build(challenge, challenge_cited)
        stored = challenge_receipt["independent_execution_summary"]["counterexample_body"]
        self.assertIsNot(stored, counter_body)
        self.assertIs(type(stored), dict)
        counter_body["payload"] = "mutated"
        self.assertEqual(stored["payload"], "counter")
        _assert_plain(self, challenge_receipt)

    def test_same_class_binding_and_replay_priority(self) -> None:
        _expect(
            self,
            "IVP_BINDING_UNAVAILABLE",
            lambda: _build(cited=_cited(include_audit_request=False)),
        )
        drifted = _cited()
        drifted["decision"]["decision"] = "FAIL"
        _expect(self, "IVP_BINDING_UNAVAILABLE", lambda: _build(cited=drifted))
        pin = _pin()
        pin["expected_sha256"] = _OTHER
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=_cited(pin=pin)))
        pin = _pin()
        pin["files"] = [
            {"relative_path": "payload.txt", "sha256": _SHA, "bytes": 4},
            {"relative_path": "payload.txt", "sha256": _OTHER, "bytes": 4},
        ]
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=_cited(pin=pin)))
        pin = _pin()
        pin["files"] = [
            {"relative_path": "../payload.txt", "sha256": _SHA, "bytes": 4}
        ]
        _expect(self, "IVP_REVISION_UNBOUND", lambda: _build(cited=_cited(pin=pin)))
        bound_pin = _pin()
        bound_pin["expected_sha256"] = _SHA
        receipt = _build(cited=_cited(pin=bound_pin))
        self.assertEqual(receipt["artifact_revision_binding"]["expected_sha256"], _SHA)
        bad_input = _reproduction(input_digest=_OTHER)
        _expect(self, "IVP_BINDING_UNAVAILABLE", lambda: _build(bad_input))
        matching = _reproduction(input_digest=canonical_digest({"payload": "input"}))
        self.assertEqual(_build(matching)["classification"], "BOUND_CANDIDATE")
        replay = _reproduction(
            result_token="FAIL",
            independent_execution=_execution("run-independent", "beta", "left"),
        )
        replay_receipt = _build(replay)
        self.assertEqual(replay_receipt["classification"], "DUPLICATE")
        self.assertIs(replay_receipt["structural_candidate"], False)
        for kind in ("reproduction", "REPRO", "challenge", "Challenge"):
            _expect(
                self,
                "IVP_SOURCE_INVALID",
                lambda kind=kind: _build(_reproduction(verification_kind=kind)),
            )
        malformed = _cited()
        malformed["report"]["authority"] = True
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(cited=malformed))

    def test_same_class_challenge_and_descriptive_limits(self) -> None:
        cited = _cited()
        upgraded = _challenge(cited)
        upgraded["source_execution"] = _execution("run-source", "alpha", "left")
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(upgraded, cited))
        claim_digest = cited["report"]["canonical_input_digests"]["CLAIM.json"]
        duplicated = _challenge(cited, assumptions=[claim_digest, claim_digest])
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(duplicated, cited))
        empty = _challenge(cited, assumptions=[])
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(empty, cited))
        bad_counter = _challenge(
            cited,
            present=True,
            counterexample={"body": {"payload": "counter"}, "digest": _OTHER},
        )
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(bad_counter, cited))
        bad_evidence = _challenge(
            cited,
            evidence={"body": {"payload": "challenge"}, "digest": _OTHER},
        )
        _expect(self, "IVP_EVIDENCE_DIGEST_INVALID", lambda: _build(bad_evidence, cited))
        assumed = _report_with_assumption(cited["report"], "pinned-assumption")
        assumed_cited = dict(cited)
        assumed_cited["report"] = assumed
        raw = _challenge(assumed_cited, assumptions=["pinned-assumption"])
        _expect(self, "IVP_CHALLENGE_INVALID", lambda: _build(raw, assumed_cited))
        bound = _challenge(
            assumed_cited,
            assumptions=[canonical_digest("pinned-assumption")],
        )
        bound_receipt = _build(bound, assumed_cited)
        self.assertEqual(bound_receipt["classification"], "CHALLENGE_RECORDED")
        self.assertEqual(
            bound_receipt["source_execution_summary"]["assumptions_attacked"],
            [canonical_digest("pinned-assumption")],
        )
        described = _reproduction(
            observer_id="observer-1",
            observer_basis="SELF_DECLARED",
            backend_provider="local",
            model="model-a",
            annotation="structural_candidate=true",
        )
        described_receipt = _build(described)
        self.assertEqual(described_receipt["classification"], "BOUND_CANDIDATE")
        self.assertIs(described_receipt["structural_candidate"], True)
        self.assertIs(described_receipt["observer"]["authority"], False)
        self.assertEqual(described_receipt["observer"]["observer_basis"], "SELF_DECLARED")
        self.assertIs(described_receipt["descriptive"]["authority"], False)
        self.assertEqual(
            described_receipt["annotations"],
            {"annotation": "structural_candidate=true", "authority": False},
        )
        self.assertIs(described_receipt["authority"], False)
        _expect(
            self,
            "IVP_SOURCE_INVALID",
            lambda: _build(_reproduction(observer_basis="independent")),
        )
        _expect(
            self,
            "IVP_EXECUTION_INVALID",
            lambda: _build(
                _reproduction(
                    source_execution=_execution(True, "alpha", "left")
                )
            ),
        )
        _expect(
            self,
            "IVP_EXECUTION_INVALID",
            lambda: _build(
                _reproduction(source_execution=_execution("   ", "alpha", "left"))
            ),
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(note="extra"))

    def test_same_class_snapshot_edges(self) -> None:
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(cited=_cited() | {"claim": _DupKeys()}))
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(candidate=_BadKey()))
        node = "x"
        for _ in range(33):
            node = {"n": node}
        deep = _reproduction(
            source_execution=_execution("run-source", "alpha", "left", body=node)
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(deep))
        binary = _reproduction(
            source_execution=_execution(
                "run-source",
                "alpha",
                "left",
                body={"payload": b"abc"},
            )
        )
        _expect(self, "IVP_SOURCE_INVALID", lambda: _build(binary))
        empty_env = _reproduction(
            source_execution=_execution("run-source", "alpha", "left", env={}),
            independent_execution=_execution("run-independent", "beta", "right", env={}),
        )
        empty_receipt = _build(empty_env)
        self.assertEqual(empty_receipt["classification"], "DUPLICATE")
        self.assertIs(empty_receipt["structural_candidate"], False)

    def test_same_class_output_has_no_unbound_classification(self) -> None:
        self.assertNotIn(
            'classification = "UNBOUND"',
            Path(preflight_module.__file__).read_text(encoding="utf-8"),
        )
        self.assertNotIn(
            '"UNBOUND"',
            Path(preflight_module.__file__).read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
