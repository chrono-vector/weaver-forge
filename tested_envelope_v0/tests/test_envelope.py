"""Focused tests for Tested-Envelope Receipt v0."""

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
from tested_envelope_v0.envelope import EnvelopeError, build_tested_envelope

REPO = Path(__file__).resolve().parents[2]
_SHA = "ab" * 32
_OTHER = "cd" * 32


def _vectors(result: str = "PASS") -> dict[str, str]:
    return {
        "POSITIVE_DIGEST_MATCH": result,
        "NC1_WRONG_DIGEST_REJECTED": result,
        "T1_TAMPER_CHANGES_DIGEST": result,
        "R1_REHASH_REPRODUCTION": result,
        "BV1_PROTECTED_BOUNDARY_WRITE_DENIED": result,
    }


def _bundle(
    *,
    decision: dict | None = None,
    claim_id: str = "AUR-A-001",
    request_claim_id: str | None = None,
    pin_sha: str = _SHA,
    expected_sha: str | None = None,
    files: list | None = None,
    scope: dict | None = None,
    assumptions_via_mismatch: bool = False,
    include_audit_request: bool = True,
) -> dict:
    claim = {"claim_id": claim_id, "statement": "document digest matches"}
    if scope is None:
        scope = {
            "allowed_write_boundary": ["audit/**"],
            "policy": {"name": "hash_claim"},
        }
    if files is None:
        files = [
            {"relative_path": "payload.txt", "sha256": pin_sha, "bytes": 4},
        ]
    pin = {
        "classification": "PINNED_INPUT",
        "expected_sha256": expected_sha,
        "files": files,
        "modified": False,
        "origin_absolute": r"C:\dev\Weaver\weaver-forge\phase6_third_party_target",
        "pinned_root": r"C:\dev\Weaver\weaver-forge\phase61_runs\example\pinned_target",
    }
    if decision is None:
        decision = {
            "decision": "PASS",
            "claim_result": "PASS",
            "claim_id": claim_id,
            "broader_classification": "CLAIM_SUPPORTED_PARTIAL",
            "promoted": False,
            "promoted_to_full": False,
            "reason": "ALL_REQUIRED_VECTORS_PASS",
            "vectors": _vectors(),
        }
    request_id = claim_id if request_claim_id is None else request_claim_id
    if assumptions_via_mismatch:
        request_id = "AUR-A-OTHER"
    audit_request = None
    if include_audit_request:
        audit_request = {
            "claim": {"id": request_id, "statement": "document digest matches"},
        }
    report = derive_reconstructability_report(
        ReconstructabilityInputs(
            audit_id="WFA-ENVELOPE",
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
        "scope": scope,
        "provenance_pin": pin,
        "reconstructability": report.to_dict(),
    }


def _build(bundle: dict, **kwargs):
    return build_tested_envelope(
        bundle["decision"],
        claim=bundle["claim"],
        scope=bundle["scope"],
        provenance_pin=bundle["provenance_pin"],
        reconstructability=bundle["reconstructability"],
        **kwargs,
    )


class TestValidEnvelope(unittest.TestCase):
    def test_valid_source_keeps_nonauthoritative_result(self):
        receipt = _build(_bundle())
        self.assertFalse(receipt["authority"])
        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["source_result"], "PASS")
        self.assertEqual(
            receipt["artifact_revision"],
            {"files": [{"relative_path": "payload.txt", "sha256": _SHA}]},
        )
        self.assertNotIn("origin_absolute", str(receipt["artifact_revision"]))
        self.assertNotIn("pinned_root", str(receipt["artifact_revision"]))
        self.assertEqual(receipt["claim_id"], "AUR-A-001")
        self.assertEqual(receipt["broader_classification"], "CLAIM_SUPPORTED_PARTIAL")
        self.assertEqual(
            set(receipt["scope_binding"]),
            {"claim_id", "scope_digest"},
        )
        self.assertEqual(receipt["scope_binding"]["claim_id"], "AUR-A-001")
        self.assertEqual(len(receipt["scope_binding"]["scope_digest"]), 64)
        self.assertEqual(
            receipt["exclusions"],
            [
                "global safety",
                "global content truth",
                "civic truth",
                "independent reproduction",
                "Human Final",
                "Canonical / Published / Deployed state",
            ],
        )
        self.assertEqual(
            receipt["detector_families"],
            [
                "boundary",
                "digest_match",
                "rehash",
                "tamper",
                "wrong_digest_rejection",
            ],
        )
        self.assertNotIn("authority_before", receipt)
        self.assertNotIn("authority_after", receipt)
        self.assertNotIn("counterexample_count", receipt)
        self.assertNotIn("independent_evidence_count", receipt)

    def test_scope_note_does_not_change_binding_or_result(self):
        bundle = _bundle()
        first = _build(bundle, scope_note="narrow annotation")
        second = _build(bundle, scope_note="different annotation")
        self.assertEqual(first["scope_binding"], second["scope_binding"])
        self.assertEqual(first["result"], second["result"])
        self.assertEqual(first["annotations"]["scope_note"], "narrow annotation")
        self.assertFalse(first["annotations"]["authority"])
        self.assertNotIn("scope_note", first["scope_binding"])


class TestRevisionBinding(unittest.TestCase):
    def test_caller_digest_cannot_masquerade(self):
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(), artifact_revision=_OTHER)
        self.assertEqual(caught.exception.code, "ENVELOPE_REVISION_UNBOUND")

    def test_head_latest_and_branch_rejected(self):
        for token in ("HEAD", "latest", "main", "master"):
            with self.subTest(token=token):
                bundle = _bundle(pin_sha=token)
                with self.assertRaises(EnvelopeError) as caught:
                    _build(bundle)
                self.assertEqual(caught.exception.code, "ENVELOPE_REVISION_UNBOUND")

    def test_missing_pin_files_fail_closed(self):
        bundle = _bundle(files=[])
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "ENVELOPE_REVISION_UNBOUND")

    def test_unrelated_expected_digest_rejected(self):
        bundle = _bundle(expected_sha=_OTHER)
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "ENVELOPE_REVISION_UNBOUND")

    def test_multi_file_revision_is_the_pin_inventory(self):
        files = [
            {"relative_path": "a.txt", "sha256": _SHA, "bytes": 1},
            {"relative_path": "b.txt", "sha256": _OTHER, "bytes": 1},
        ]
        receipt = _build(_bundle(files=files))
        self.assertEqual(
            receipt["artifact_revision"]["files"],
            [
                {"relative_path": "a.txt", "sha256": _SHA},
                {"relative_path": "b.txt", "sha256": _OTHER},
            ],
        )
        self.assertNotIn("expected_sha256", receipt["artifact_revision"])

    def test_decision_mutated_after_report_is_unbound(self):
        bundle = _bundle()
        bundle["decision"] = dict(bundle["decision"])
        bundle["decision"]["reason"] = "TAMPERED"
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "ENVELOPE_REVISION_UNBOUND")


class TestScopeAndPromotion(unittest.TestCase):
    def test_empty_scope_cannot_strengthen(self):
        bundle = _bundle(scope={})
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "ENVELOPE_SCOPE_UNBOUND")

    def test_partial_cannot_become_full(self):
        decision = {
            "decision": "PASS",
            "claim_result": "PASS",
            "claim_id": "AUR-A-001",
            "broader_classification": "FULL",
            "promoted": False,
            "promoted_to_full": False,
            "reason": "ALL_REQUIRED_VECTORS_PASS",
            "vectors": _vectors(),
        }
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_PROMOTION")

    def test_promoted_flag_is_rejected(self):
        decision = dict(_bundle()["decision"])
        decision["promoted_to_full"] = True
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_PROMOTION")

    def test_pass_without_required_vector_is_rejected(self):
        decision = dict(_bundle()["decision"])
        vectors = dict(decision["vectors"])
        del vectors["R1_REHASH_REPRODUCTION"]
        decision["vectors"] = vectors
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_MISSING_OBSERVATION")

    def test_caller_cannot_set_result(self):
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(), result="PASS")
        self.assertEqual(caught.exception.code, "ENVELOPE_PROMOTION")

    def test_incomplete_evidence_cannot_become_pass(self):
        decision = {
            "decision": "INCONCLUSIVE",
            "claim_result": "INCONCLUSIVE",
            "claim_id": "AUR-A-001",
            "reason": "INCOMPLETE_EVIDENCE",
            "promoted": False,
            "vectors": {},
        }
        receipt = _build(_bundle(decision=decision))
        self.assertEqual(receipt["result"], "INCONCLUSIVE")
        self.assertIn("INCOMPLETE_EVIDENCE", receipt["missing_observations"])

    def test_pass_with_missing_vector_is_rejected(self):
        decision = {
            "decision": "PASS",
            "claim_result": "PASS",
            "claim_id": "AUR-A-001",
            "broader_classification": "CLAIM_SUPPORTED_PARTIAL",
            "promoted": False,
            "promoted_to_full": False,
            "reason": "MISSING_REQUIRED_VECTORS",
            "missing": ["R1_REHASH_REPRODUCTION"],
            "vectors": _vectors(),
        }
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_MISSING_OBSERVATION")

    def test_inconclusive_missing_vector_stays_inconclusive(self):
        decision = {
            "decision": "INCONCLUSIVE",
            "claim_result": "INCONCLUSIVE",
            "claim_id": "AUR-A-001",
            "reason": "MISSING_REQUIRED_VECTORS",
            "missing": ["R1_REHASH_REPRODUCTION"],
            "promoted": False,
            "vectors": {},
        }
        receipt = _build(_bundle(decision=decision))
        self.assertNotEqual(receipt["result"], "PASS")
        self.assertIn("R1_REHASH_REPRODUCTION", receipt["missing_observations"])

    def test_unsupported_family_rejected(self):
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(), detector_families=("formal_model",))
        self.assertEqual(caught.exception.code, "ENVELOPE_FAMILY_UNSUPPORTED")

    def test_family_requires_a_cited_vector(self):
        decision = {
            "decision": "INCONCLUSIVE",
            "claim_result": "INCONCLUSIVE",
            "claim_id": "AUR-A-001",
            "reason": "INCOMPLETE_EVIDENCE",
            "promoted": False,
            "vectors": {},
        }
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision), detector_families=("digest_match",))
        self.assertEqual(caught.exception.code, "ENVELOPE_FAMILY_UNSUPPORTED")

    def test_detected_is_not_pass(self):
        decision = {
            "decision": "DETECTED",
            "claim_result": "DETECTED",
            "claim_id": "AUR-A-001",
            "promoted": False,
            "vectors": {},
        }
        receipt = _build(_bundle(decision=decision))
        self.assertEqual(receipt["result"], "DETECTED")
        self.assertNotEqual(receipt["result"], "PASS")


class TestAssumptionsCountsAndAuthority(unittest.TestCase):
    def test_assumptions_are_preserved_and_cannot_be_replaced(self):
        bundle = _bundle()
        report = dict(bundle["reconstructability"])
        report["unresolved_assumptions"] = ["CLAIM_ID_MISMATCH_REQUEST_VS_CLAIM"]
        body = dict(report)
        body.pop("report_digest")
        report["report_digest"] = canonical_digest(body)
        bundle["reconstructability"] = report
        receipt = _build(bundle)
        self.assertEqual(
            receipt["unresolved_assumptions"],
            ["CLAIM_ID_MISMATCH_REQUEST_VS_CLAIM"],
        )
        self.assertEqual(receipt["result"], "PASS")
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle, unresolved_assumptions=[])
        self.assertEqual(caught.exception.code, "ENVELOPE_ASSUMPTION_DROPPED")
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(assumptions_via_mismatch=True))
        self.assertEqual(caught.exception.code, "ENVELOPE_MISSING_OBSERVATION")

    def test_absent_counterexample_count_is_not_zero(self):
        receipt = _build(_bundle())
        self.assertNotIn("counterexample_count", receipt)
        decision = dict(_bundle()["decision"])
        decision["counterexample_count"] = 2
        counted = _build(_bundle(decision=decision))
        self.assertEqual(counted["counterexample_count"], 2)
        zero = dict(decision)
        zero["counterexample_count"] = 0
        kept = _build(_bundle(decision=zero))
        self.assertEqual(kept["counterexample_count"], 0)

    def test_false_counterexample_count_rejected(self):
        decision = dict(_bundle()["decision"])
        decision["counterexample_count"] = True
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_SOURCE_INVALID")

    def test_authority_true_rejected(self):
        decision = dict(_bundle()["decision"])
        decision["authority"] = True
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_AUTHORITY_INVALID")

    def test_fabricated_authority_history_rejected(self):
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(), authority_before=False, authority_after=False)
        self.assertEqual(caught.exception.code, "ENVELOPE_AUTHORITY_INVALID")

    def test_independent_count_cannot_be_injected(self):
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(), independent_evidence_count=1)
        self.assertEqual(caught.exception.code, "ENVELOPE_AUTHORITY_INVALID")

    def test_independent_acceptance_claim_rejected(self):
        decision = dict(_bundle()["decision"])
        decision["independent_verification"] = {
            "claims_iw_acceptance": True,
            "result": "NOT_CLAIMED",
        }
        with self.assertRaises(EnvelopeError) as caught:
            _build(_bundle(decision=decision))
        self.assertEqual(caught.exception.code, "ENVELOPE_AUTHORITY_INVALID")


class _SplitView(Mapping):
    """Bound iteration is the validated record. Live lookup is the attack."""

    def __init__(self, bound: dict, live: dict, *, index_live: bool = False) -> None:
        self._bound = bound
        self._live = live
        self._index_live = index_live

    def __getitem__(self, key: str):
        source = self._live if self._index_live else self._bound
        return source[key]

    def __iter__(self):
        return iter(self._bound)

    def __len__(self) -> int:
        return len(self._bound)

    def items(self):
        return self._bound.items()

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class TestCompletenessAndSnapshot(unittest.TestCase):
    def test_omitted_audit_request_cannot_become_pass(self):
        bundle = _bundle(include_audit_request=False)
        report = bundle["reconstructability"]
        self.assertIs(report["reconstructable"], False)
        self.assertEqual(report["missing_inputs"], ["AUDIT_REQUEST.json"])
        self.assertEqual(report["unresolved_assumptions"], [])
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "ENVELOPE_MISSING_OBSERVATION")

    def test_live_get_cannot_promote_bound_fail(self):
        bound = {
            "decision": "FAIL",
            "claim_result": "FAIL",
            "claim_id": "AUR-A-001",
            "promoted": False,
            "reason": "REQUIRED_VECTOR_FAIL",
            "vectors": _vectors("FAIL"),
        }
        live = {
            "decision": "PASS",
            "claim_result": "PASS",
            "claim_id": "AUR-A-001",
            "broader_classification": "CLAIM_SUPPORTED_PARTIAL",
            "promoted": False,
            "promoted_to_full": False,
            "reason": "ALL_REQUIRED_VECTORS_PASS",
            "vectors": _vectors(),
        }
        bundle = _bundle(decision=bound)
        bundle["decision"] = _SplitView(bound, live)
        receipt = _build(bundle)
        self.assertEqual(receipt["source_result"], "FAIL")
        self.assertEqual(receipt["result"], "FAIL")
        self.assertNotEqual(receipt["result"], "PASS")

    def test_nested_vector_view_cannot_promote_pass(self):
        fail_vectors = _vectors("FAIL")
        decision = {
            "decision": "PASS",
            "claim_result": "PASS",
            "claim_id": "AUR-A-001",
            "broader_classification": "CLAIM_SUPPORTED_PARTIAL",
            "promoted": False,
            "promoted_to_full": False,
            "reason": "ALL_REQUIRED_VECTORS_PASS",
            "vectors": fail_vectors,
        }
        bundle = _bundle(decision=decision)
        wrapped = dict(decision)
        wrapped["vectors"] = _SplitView(fail_vectors, _vectors(), index_live=True)
        bundle["decision"] = wrapped
        with self.assertRaises(EnvelopeError) as caught:
            _build(bundle)
        self.assertEqual(caught.exception.code, "ENVELOPE_PROMOTION")


class TestNoAcceptedWrites(unittest.TestCase):
    def test_generation_does_not_change_the_worktree(self):
        before = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        _build(_bundle())
        after = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
