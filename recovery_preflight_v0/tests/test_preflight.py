"""Focused tests for Recovery Preflight v0."""

from __future__ import annotations

import subprocess
import unittest
from collections.abc import Mapping
from pathlib import Path

from audit_lifecycle.epistemic.reconstructability import (
    ReconstructabilityInputs,
    derive_reconstructability_report,
)
from audit_lifecycle.epistemic.serialize import canonical_digest
from recovery_preflight_v0 import RecoveryError, build_recovery_preflight

REPO = Path(__file__).resolve().parents[2]
_SHA = "ab" * 32
_PRIOR = "ab" * 32
_OTHER = "cd" * 32
_NOTE = "STATE≠EVIDENCE; digest alone never restores PASS/FAIL"
_COVERS = ["claims", "evidence_register.entries"]
_LIMITATIONS = [
    "restore execution",
    "verified restore",
    "rollback completion",
    "recovered state",
    "independent reproduction",
    "operational hardening",
    "Human Final",
    "Canonical / Published / Deployed state",
]
_LEAF_TYPES = (str, bool, int, float)


def _decision(
    token: str = "PASS",
    *,
    claim_id: str | None = "AUR-A-001",
    claim_result: str | None = None,
    include_claim_result: bool = True,
) -> dict:
    body = {
        "decision": token,
        "promoted": False,
        "reason": "ALL_REQUIRED_VECTORS_PASS" if token == "PASS" else "ADAPTER_CLAIM_NOT_PASS",
    }
    if claim_id is not None:
        body["claim_id"] = claim_id
    if include_claim_result:
        body["claim_result"] = token if claim_result is None else claim_result
    if token == "PASS":
        body["broader_classification"] = "CLAIM_SUPPORTED_PARTIAL"
        body["promoted_to_full"] = False
    return body


def _bundle(
    decision: dict | None = None,
    *,
    claim_id: str = "AUR-A-001",
    request_claim_id: str | None = None,
    include_audit_request: bool = True,
) -> dict:
    if decision is None:
        decision = _decision(claim_id=claim_id)
    claim = {"claim_id": claim_id, "statement": "document digest matches"}
    scope = {
        "allowed_write_boundary": ["audit/**"],
        "policy": {"name": "hash_claim"},
    }
    pin = {
        "classification": "PINNED_INPUT",
        "expected_sha256": None,
        "files": [{"relative_path": "payload.txt", "sha256": _SHA, "bytes": 4}],
        "modified": False,
        "origin_absolute": r"C:\dev\Weaver\weaver-forge\phase6_third_party_target",
        "pinned_root": r"C:\dev\Weaver\weaver-forge\phase61_runs\example\pinned_target",
    }
    request_id = claim_id if request_claim_id is None else request_claim_id
    audit_request = None
    if include_audit_request:
        audit_request = {"claim": {"id": request_id, "statement": "document digest matches"}}
    report = derive_reconstructability_report(
        ReconstructabilityInputs(
            audit_id="WFA-RECOVERY",
            claim=claim,
            scope=scope,
            audit_request=audit_request,
            provenance_pin=pin,
            decision=decision,
        )
    )
    return {"decision": decision, "reconstructability": report.to_dict()}


def _revalidation(
    *,
    matched: bool | None = True,
    terminals: list | None = None,
    reuse: list | None = None,
    note: str | None = _NOTE,
    include_note: bool = True,
) -> dict:
    if terminals is None:
        terminals = [
            {"claim_id": "AUR-A-001", "prior_state": "PASS", "reason": "missing_plan"},
        ]
    record = {
        "integrity_digest_matched": matched,
        "rejected_terminals": terminals,
        "validated_reuse_claims": [] if reuse is None else reuse,
    }
    if include_note and note is not None:
        record["note"] = note
    return record


def _state_integrity(digest: str = _PRIOR) -> dict:
    return {
        "digest": digest,
        "algorithm": "sha256",
        "covers": list(_COVERS),
    }


def _with_digest(
    record: dict,
    *,
    expected: str = _PRIOR,
    actual: str = _PRIOR,
    matched: bool | None = None,
) -> dict:
    bound = dict(record)
    bound["prior_integrity_digest"] = expected
    bound["state_integrity"] = _state_integrity(actual)
    bound["integrity_digest_matched"] = expected == actual if matched is None else matched
    return bound


def _build(bundle: dict | None = None, **kwargs):
    if bundle is None:
        bundle = _bundle()
    return build_recovery_preflight(
        bundle["decision"],
        reconstructability=bundle["reconstructability"],
        **kwargs,
    )


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


def _assert_not_recovered(test: unittest.TestCase, receipt: dict) -> None:
    test.assertIs(type(receipt), dict)
    test.assertEqual(receipt["schema_version"], "recovery_preflight.v0")
    test.assertIs(receipt["authority"], False)
    test.assertIs(receipt["recovered"], False)
    test.assertEqual(receipt["classification"], "NOT_RECOVERED")
    test.assertEqual(receipt["limitations"], _LIMITATIONS)
    _assert_plain(test, receipt)


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
    """items() stays on the bound row. Lookup returns the live row."""

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


class _HostileFloat(float):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return hash(0.0)


class _Rows(list):
    """Caller-owned list subclass."""


class _Reuse(tuple):
    """Caller-owned tuple subclass."""


class _Note(str):
    """Caller-owned annotation subclass."""


class _DupKeys(Mapping):
    def __getitem__(self, key: str):
        return 1

    def __iter__(self):
        return iter(("a",))

    def __len__(self) -> int:
        return 2

    def items(self):
        return (("a", 1), ("a", 2))


class TestBoundDecisions(unittest.TestCase):
    def test_pass_decision_stays_not_recovered(self):
        receipt = _build()
        _assert_not_recovered(self, receipt)
        self.assertEqual(
            receipt["cited_decision"],
            {"claim_id": "AUR-A-001", "decision": "PASS", "claim_result": "PASS"},
        )
        self.assertNotIn("revalidation_observation", receipt)
        self.assertNotIn("rejected_terminals", receipt)
        self.assertNotIn("digest_observation", receipt)
        self.assertNotIn("annotations", receipt)
        self.assertEqual(
            set(receipt),
            {
                "schema_version",
                "authority",
                "recovered",
                "classification",
                "cited_decision",
                "limitations",
            },
        )

    def test_non_pass_tokens_stay_not_recovered(self):
        for token in ("FAIL", "INCONCLUSIVE", "BLOCKED"):
            with self.subTest(token=token):
                decision = _decision(token, claim_result="INCONCLUSIVE")
                bundle = _bundle(decision)
                receipt = _build(bundle)
                _assert_not_recovered(self, receipt)
                self.assertEqual(receipt["cited_decision"]["decision"], token)
                self.assertEqual(receipt["cited_decision"]["claim_result"], "INCONCLUSIVE")
                self.assertNotEqual(receipt["cited_decision"]["decision"], receipt["classification"])

    def test_missing_claim_identity_fails_closed(self):
        decision = _decision("FAIL", claim_id=None)
        bundle = _bundle(decision, claim_id="AUR-A-001")
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

    def test_incomplete_report_is_not_a_receipt(self):
        bundle = _bundle(include_audit_request=False)
        self.assertIs(bundle["reconstructability"]["reconstructable"], False)
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_BINDING_UNAVAILABLE")

    def test_assumptions_keep_the_citation_unbound(self):
        decision = _decision()
        bundle = _bundle(decision, request_claim_id="AUR-A-OTHER")
        self.assertIn(
            "CLAIM_ID_MISMATCH_REQUEST_VS_CLAIM",
            bundle["reconstructability"]["unresolved_assumptions"],
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_BINDING_UNAVAILABLE")

    def test_forged_complete_flag_cannot_hide_assumptions(self):
        bundle = _bundle(request_claim_id="AUR-A-OTHER")
        forged = dict(bundle["reconstructability"])
        forged["reconstructable"] = True
        forged["missing_inputs"] = []
        body = {key: value for key, value in forged.items() if key != "report_digest"}
        forged["report_digest"] = canonical_digest(body)
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight(bundle["decision"], reconstructability=forged)
        self.assertEqual(caught.exception.code, "RECOVERY_BINDING_UNAVAILABLE")

    def test_digest_mismatch_fails_closed(self):
        bundle = _bundle()
        changed = dict(bundle["decision"])
        changed["reason"] = "TAMPERED"
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight(
                changed,
                reconstructability=bundle["reconstructability"],
            )
        self.assertEqual(caught.exception.code, "RECOVERY_BINDING_UNAVAILABLE")

    def test_unbound_decision_digest_fails_closed(self):
        bundle = _bundle()
        forged = dict(bundle["reconstructability"])
        digests = dict(forged["canonical_input_digests"])
        digests["DECISION.json"] = None
        forged["canonical_input_digests"] = digests
        body = {key: value for key, value in forged.items() if key != "report_digest"}
        forged["report_digest"] = canonical_digest(body)
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight(bundle["decision"], reconstructability=forged)
        self.assertEqual(caught.exception.code, "RECOVERY_BINDING_UNAVAILABLE")

    def test_malformed_decision_and_report_fail_closed(self):
        bundle = _bundle()
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight("PASS", reconstructability=bundle["reconstructability"])
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight(bundle["decision"], reconstructability=[])
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight(bundle["decision"], reconstructability={})
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")


class TestRevalidation(unittest.TestCase):
    def test_bound_digest_match_is_copied_and_is_not_recovery(self):
        receipt = _build(revalidation=_with_digest(_revalidation(matched=True, terminals=[])))
        _assert_not_recovered(self, receipt)
        self.assertEqual(
            receipt["digest_observation"],
            {
                "algorithm": "sha256",
                "covers": _COVERS,
                "prior_integrity_digest": _PRIOR,
                "digest": _PRIOR,
                "integrity_digest_matched": True,
            },
        )
        self.assertNotIn("integrity_digest_matched", receipt["revalidation_observation"])
        self.assertEqual(receipt["cited_decision"]["decision"], "PASS")
        self.assertNotIn("note", receipt["revalidation_observation"])

    def test_bound_digest_mismatch_is_an_observation_only(self):
        receipt = _build(
            revalidation=_with_digest(
                _revalidation(matched=False, terminals=[]),
                expected=_PRIOR,
                actual=_OTHER,
            )
        )
        _assert_not_recovered(self, receipt)
        self.assertIs(receipt["digest_observation"]["integrity_digest_matched"], False)
        self.assertEqual(receipt["digest_observation"]["prior_integrity_digest"], _PRIOR)
        self.assertEqual(receipt["digest_observation"]["digest"], _OTHER)
        self.assertEqual(receipt["rejected_terminals"], [])

    def test_bare_digest_flag_is_not_emitted(self):
        for matched in (True, False, None):
            with self.subTest(matched=matched):
                receipt = _build(revalidation=_revalidation(matched=matched, terminals=[]))
                _assert_not_recovered(self, receipt)
                self.assertNotIn("digest_observation", receipt)
                self.assertNotIn(
                    "integrity_digest_matched",
                    receipt["revalidation_observation"],
                )

    def test_rejected_terminal_is_copied_without_becoming_recovery(self):
        terminal = {
            "claim_id": "AUR-A-001",
            "prior_state": "PASS",
            "reason": "missing_plan",
        }
        receipt = _build(revalidation=_revalidation(matched=True, terminals=[terminal]))
        _assert_not_recovered(self, receipt)
        self.assertEqual(receipt["rejected_terminals"], [terminal])
        self.assertEqual(receipt["cited_decision"]["claim_id"], "AUR-A-001")
        self.assertNotIn("digest_observation", receipt)

    def test_same_claim_fail_terminal_is_copied(self):
        terminal = {
            "claim_id": "AUR-A-001",
            "prior_state": "FAIL",
            "reason": "FAIL_without_validated_evidence_path",
        }
        receipt = _build(revalidation=_revalidation(terminals=[terminal], reuse=[]))
        _assert_not_recovered(self, receipt)
        self.assertEqual(receipt["rejected_terminals"], [terminal])

    def test_reuse_claims_do_not_recover(self):
        receipt = _build(
            revalidation=_revalidation(matched=False, terminals=[], reuse=["AUR-A-001"])
        )
        _assert_not_recovered(self, receipt)
        self.assertEqual(
            receipt["revalidation_observation"]["validated_reuse_claims"],
            ["AUR-A-001"],
        )
        self.assertNotIn("digest_observation", receipt)

    def test_note_text_does_not_change_structured_facts(self):
        first = _build(revalidation=_revalidation(note=_NOTE))
        second = _build(revalidation=_revalidation(note="RECOVERED"))
        _assert_not_recovered(self, first)
        _assert_not_recovered(self, second)
        self.assertEqual(first["revalidation_observation"], second["revalidation_observation"])
        self.assertEqual(first["rejected_terminals"], second["rejected_terminals"])
        self.assertNotIn("digest_observation", first)
        self.assertNotIn("digest_observation", second)
        self.assertEqual(first["annotations"]["revalidation_note"], _NOTE)
        self.assertEqual(second["annotations"]["revalidation_note"], "RECOVERED")
        self.assertIs(first["annotations"]["authority"], False)
        self.assertNotIn("note", first["revalidation_observation"])

    def test_note_only_record_is_unbound(self):
        for note in (_NOTE, "RECOVERED", "digest matched so PASS is restored"):
            with self.subTest(note=note):
                with self.assertRaises(RecoveryError) as caught:
                    _build(revalidation={"note": note})
                self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_annotation_argument_is_not_revalidation(self):
        receipt = _build(annotation=_NOTE)
        _assert_not_recovered(self, receipt)
        self.assertNotIn("revalidation_observation", receipt)
        self.assertEqual(receipt["annotations"]["annotation"], _NOTE)
        self.assertIs(receipt["annotations"]["authority"], False)

    def test_malformed_revalidation_fails_closed(self):
        cases = (
            ([], "RECOVERY_SOURCE_INVALID"),
            ("STATE", "RECOVERY_SOURCE_INVALID"),
            ({}, "RECOVERY_REVALIDATION_UNBOUND"),
            (
                {
                    "integrity_digest_matched": True,
                    "rejected_terminals": [],
                    "validated_reuse_claims": [],
                    "extra": True,
                },
                "RECOVERY_SOURCE_INVALID",
            ),
            (
                {
                    "integrity_digest_matched": 1,
                    "rejected_terminals": [],
                    "validated_reuse_claims": [],
                },
                "RECOVERY_SOURCE_INVALID",
            ),
            (
                {
                    "integrity_digest_matched": "true",
                    "rejected_terminals": [],
                    "validated_reuse_claims": [],
                },
                "RECOVERY_SOURCE_INVALID",
            ),
            (
                {
                    "integrity_digest_matched": True,
                    "rejected_terminals": ["PASS"],
                    "validated_reuse_claims": [],
                },
                "RECOVERY_REVALIDATION_UNBOUND",
            ),
            (
                {
                    "integrity_digest_matched": True,
                    "rejected_terminals": [{"claim_id": "AUR-A-001", "prior_state": "PASS"}],
                    "validated_reuse_claims": [],
                },
                "RECOVERY_REVALIDATION_UNBOUND",
            ),
            (
                {
                    "integrity_digest_matched": True,
                    "rejected_terminals": [],
                    "validated_reuse_claims": [""],
                },
                "RECOVERY_REVALIDATION_UNBOUND",
            ),
            (
                {
                    "integrity_digest_matched": True,
                    "rejected_terminals": [],
                    "validated_reuse_claims": [],
                    "note": 1,
                },
                "RECOVERY_SOURCE_INVALID",
            ),
        )
        for record, code in cases:
            with self.subTest(record=record):
                with self.assertRaises(RecoveryError) as caught:
                    _build(revalidation=record)
                self.assertEqual(caught.exception.code, code)


class TestRevalidationBinding(unittest.TestCase):
    def test_unrelated_terminal_claim_is_rejected(self):
        record = _revalidation(
            terminals=[
                {"claim_id": "AUR-A-002", "prior_state": "FAIL", "reason": "missing_plan"},
            ]
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_unrelated_reuse_claim_is_rejected(self):
        record = _revalidation(terminals=[], reuse=["AUR-A-009"])
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_same_claim_cannot_be_rejected_and_reused(self):
        record = _revalidation(
            terminals=[
                {"claim_id": "AUR-A-001", "prior_state": "PASS", "reason": "missing_plan"},
            ],
            reuse=["AUR-A-001"],
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_recovery_like_prior_state_is_rejected(self):
        for token in ("RECOVERED", "RESTORED", "VERIFIED_RESTORE", "ROLLBACK_COMPLETE", "NEW"):
            with self.subTest(token=token):
                record = _revalidation(
                    terminals=[
                        {
                            "claim_id": "AUR-A-001",
                            "prior_state": token,
                            "reason": "missing_plan",
                        },
                    ]
                )
                with self.assertRaises(RecoveryError) as caught:
                    _build(revalidation=record)
                self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_asserted_match_with_unequal_digests_is_rejected(self):
        record = _with_digest(
            _revalidation(terminals=[]),
            expected=_PRIOR,
            actual=_OTHER,
            matched=True,
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

        record = _with_digest(
            _revalidation(terminals=[]),
            expected=_PRIOR,
            actual=_PRIOR,
            matched=False,
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_partial_digest_evidence_is_rejected(self):
        prior_only = _revalidation(terminals=[])
        prior_only["prior_integrity_digest"] = _PRIOR
        state_only = _revalidation(terminals=[])
        state_only["state_integrity"] = _state_integrity()
        noted = _with_digest(_revalidation(terminals=[]))
        noted["state_integrity"]["note"] = _NOTE
        shifted = _with_digest(_revalidation(terminals=[]))
        shifted["state_integrity"]["covers"] = ["AUR-A-001"]
        for record in (prior_only, state_only, noted, shifted):
            with self.subTest(record=sorted(record)):
                with self.assertRaises(RecoveryError) as caught:
                    _build(revalidation=record)
                self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_mixed_scope_terminals_fail_closed(self):
        record = _revalidation(
            terminals=[
                {"claim_id": "AUR-A-001", "prior_state": "PASS", "reason": "missing_plan"},
                {"claim_id": "AUR-A-002", "prior_state": "FAIL", "reason": "missing_plan"},
            ]
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")

    def test_duplicate_claim_rows_fail_closed(self):
        repeated = {
            "claim_id": "AUR-A-001",
            "prior_state": "PASS",
            "reason": "missing_plan",
        }
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=_revalidation(terminals=[repeated, dict(repeated)]))
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=_revalidation(terminals=[], reuse=["AUR-A-001", "AUR-A-001"]))
        self.assertEqual(caught.exception.code, "RECOVERY_REVALIDATION_UNBOUND")


class TestCallerAssertions(unittest.TestCase):
    def test_recovery_keywords_are_forbidden(self):
        keywords = (
            "recovered",
            "restored",
            "verified_restore",
            "rollback_complete",
            "rejected_terminals",
            "digest_observation",
            "classification",
            "revalidation_observation",
        )
        for name in keywords:
            with self.subTest(name=name):
                with self.assertRaises(RecoveryError) as caught:
                    _build(**{name: True})
                self.assertEqual(caught.exception.code, "RECOVERY_ASSERTION_FORBIDDEN")

    def test_resume_keywords_are_out_of_scope(self):
        for name in ("campaign_resume", "resume", "resume_result"):
            with self.subTest(name=name):
                with self.assertRaises(RecoveryError) as caught:
                    _build(**{name: {"continued": True}})
                self.assertEqual(caught.exception.code, "RECOVERY_SCOPE_VIOLATION")

    def test_embedded_assertion_and_resume_fail_closed(self):
        decision = _decision()
        decision["recovered"] = True
        bundle = _bundle(decision)
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_ASSERTION_FORBIDDEN")

        decision = _decision()
        decision["resume"] = {"campaign_id": "C"}
        bundle = _bundle(decision)
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SCOPE_VIOLATION")

        record = _revalidation()
        record["restored"] = True
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_ASSERTION_FORBIDDEN")

        record = _revalidation()
        record["campaign_resume"] = True
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_SCOPE_VIOLATION")

    def test_decision_cannot_smuggle_terminal_or_digest_facts(self):
        decision = _decision()
        decision["rejected_terminals"] = [
            {"claim_id": "AUR-A-009", "prior_state": "PASS", "reason": "missing_plan"},
        ]
        bundle = _bundle(decision)
        receipt = _build(bundle)
        _assert_not_recovered(self, receipt)
        self.assertNotIn("rejected_terminals", receipt)

        decision = _decision()
        decision["digest_observation"] = {"integrity_digest_matched": True}
        bundle = _bundle(decision)
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_ASSERTION_FORBIDDEN")

    def test_unexpected_keyword_is_invalid(self):
        with self.assertRaises(RecoveryError) as caught:
            _build(authority=True)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")


class TestSnapshotBoundary(unittest.TestCase):
    def test_split_view_cannot_replace_the_decision_token(self):
        bound = _decision("FAIL")
        live = _decision("PASS")
        bundle = _bundle(bound)
        receipt = build_recovery_preflight(
            _SplitView(bound, live),
            reconstructability=bundle["reconstructability"],
        )
        _assert_not_recovered(self, receipt)
        self.assertEqual(receipt["cited_decision"]["decision"], "FAIL")
        self.assertNotEqual(receipt["cited_decision"]["decision"], "PASS")

    def test_split_dict_lookup_cannot_replace_the_decision_token(self):
        bound = _decision("FAIL")
        live = _decision("PASS")
        bundle = _bundle(bound)
        receipt = build_recovery_preflight(
            _SplitDict(bound, live),
            reconstructability=bundle["reconstructability"],
        )
        _assert_not_recovered(self, receipt)
        self.assertEqual(receipt["cited_decision"]["decision"], "FAIL")

    def test_split_view_cannot_flip_the_digest_observation(self):
        bound = _revalidation(matched=False, terminals=[])
        live = _revalidation(matched=True, terminals=[])
        receipt = _build(revalidation=_SplitView(bound, live))
        _assert_not_recovered(self, receipt)
        self.assertNotIn("digest_observation", receipt)

    def test_split_view_cannot_replace_bound_digest_evidence(self):
        bound = _with_digest(_revalidation(matched=True, terminals=[]))
        live = _with_digest(
            _revalidation(matched=False, terminals=[]),
            expected=_PRIOR,
            actual=_OTHER,
        )
        receipt = _build(revalidation=_SplitView(bound, live))
        _assert_not_recovered(self, receipt)
        self.assertIs(receipt["digest_observation"]["integrity_digest_matched"], True)
        self.assertEqual(receipt["digest_observation"]["digest"], _PRIOR)

    def test_scalar_subclasses_are_rejected(self):
        hostile_decision = _decision()
        hostile_decision["decision"] = _HostileStr("FAIL")
        self.assertEqual(hostile_decision["decision"], "PASS")
        bundle = _bundle()
        bundle["decision"] = hostile_decision
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

        counted = _decision()
        counted["width"] = _HostileInt(1)
        self.assertEqual(counted["width"], True)
        bundle = _bundle()
        bundle["decision"] = counted
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

        sized = _decision()
        sized["width"] = _HostileFloat(1.0)
        bundle = _bundle()
        bundle["decision"] = sized
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

        keyed = _decision()
        keyed[_HostileStr("note")] = "ignored"
        bundle = _bundle()
        bundle["decision"] = keyed
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

        with self.assertRaises(RecoveryError) as caught:
            _build(annotation=_Note("annotation"))
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

    def test_container_subclasses_are_rejected(self):
        record = _revalidation()
        record["rejected_terminals"] = _Rows(
            [{"claim_id": "AUR-A-001", "prior_state": "PASS", "reason": "missing_plan"}]
        )
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

        record = _revalidation(terminals=[])
        record["validated_reuse_claims"] = _Reuse(("AUR-A-009",))
        with self.assertRaises(RecoveryError) as caught:
            _build(revalidation=record)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

    def test_exact_tuple_is_copied_into_a_plain_list(self):
        record = _revalidation(terminals=[])
        record["validated_reuse_claims"] = ("AUR-A-001",)
        receipt = _build(revalidation=record)
        _assert_not_recovered(self, receipt)
        self.assertEqual(
            receipt["revalidation_observation"]["validated_reuse_claims"],
            ["AUR-A-001"],
        )
        self.assertIs(
            type(receipt["revalidation_observation"]["validated_reuse_claims"]),
            list,
        )

    def test_duplicate_mapping_keys_are_rejected(self):
        bundle = _bundle()
        with self.assertRaises(RecoveryError) as caught:
            build_recovery_preflight(
                _DupKeys(),
                reconstructability=bundle["reconstructability"],
            )
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

    def test_excessive_nesting_is_rejected(self):
        nested: dict = {"claim_id": "AUR-A-001"}
        for _ in range(40):
            nested = {"wrap": nested}
        decision = _decision()
        decision["wrapped"] = nested
        bundle = _bundle()
        bundle["decision"] = decision
        with self.assertRaises(RecoveryError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "RECOVERY_SOURCE_INVALID")

    def test_later_mutation_does_not_change_the_receipt(self):
        decision = _decision()
        bundle = _bundle(decision)
        terminals = [
            {"claim_id": "AUR-A-001", "prior_state": "PASS", "reason": "missing_plan"},
        ]
        record = _revalidation(terminals=terminals)
        receipt = _build(bundle, revalidation=record)
        decision["decision"] = "FAIL"
        terminals.append({"claim_id": "AUR-A-009", "prior_state": "FAIL", "reason": "tampered"})
        terminals[0]["prior_state"] = "FAIL"
        record["integrity_digest_matched"] = False
        self.assertEqual(receipt["cited_decision"]["decision"], "PASS")
        self.assertEqual(len(receipt["rejected_terminals"]), 1)
        self.assertEqual(receipt["rejected_terminals"][0]["prior_state"], "PASS")
        self.assertNotIn("digest_observation", receipt)
        _assert_plain(self, receipt)


class TestNoAcceptedWrites(unittest.TestCase):
    def test_generation_does_not_write_accepted_trees(self):
        before = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        _build(_bundle(), revalidation=_revalidation())
        after = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        self.assertEqual(before, after)
        for line in after.splitlines():
            path = line[3:].strip().strip('"')
            self.assertTrue(
                path.startswith("recovery_preflight_v0"),
                path,
            )


if __name__ == "__main__":
    unittest.main()
