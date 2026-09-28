"""Focused R4-A epistemic contract tests.

Covers claim/relation/provenance contracts, non-authority invariants,
legacy compatibility, canonical serialization stability, and adversarial
remediation coverage for Codex material findings R4A-M1..M5.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF_ROOT = ROOT.parent
sys.path.insert(0, str(WF_ROOT))

from audit_lifecycle.claim_scope import compile_claim_and_scope
from audit_lifecycle.epistemic.authority import (
    AuthorityViolation,
    assert_authority_false,
    assert_confidence_cannot_authorize,
    assert_epistemic_cannot_change_execution_authorization,
    assert_epistemic_cannot_create_human_final,
    enforce_non_authority,
)
from audit_lifecycle.epistemic.compat import LegacyClaimView, legacy_claim_view, read_claim_record
from audit_lifecycle.epistemic.provenance import (
    IndependenceBasis,
    ProvenanceGraphError,
    ProvenanceRecord,
    SELF_DECLARED_INDEPENDENCE,
    account_independent_origins,
    require_provenance_for_verified_scope,
    status_for_insufficient_provenance,
    validate_provenance_graph,
)
from audit_lifecycle.epistemic.records import (
    CLAIM_KINDS,
    EpistemicClaimRecord,
    EpistemicStatusError,
    assert_no_silent_status_promotion,
    formal_and_symbolic_are_distinct,
)
from audit_lifecycle.epistemic.relations import (
    RelationAsClaim,
    RelationSatisfactionError,
    analogous_to_cannot_satisfy_causes,
    relation_may_satisfy,
)
from audit_lifecycle.epistemic.serialize import (
    ORDERED_SEQUENCE_FIELDS,
    SET_LIKE_SEQUENCE_FIELDS,
    canonical_digest,
    canonical_dumps,
    normalize_sequences,
)
from audit_lifecycle.epistemic.validation import (
    EpistemicValidationError,
    validate_epistemic_record,
)
from audit_lifecycle.request import AuditRequest
from campaign_runner_v0.epistemic_adapter import adapt_campaign_claim


def _claim(**overrides):
    base = {
        "schema_version": "r4.epistemic.claim.v1",
        "claim_id": "C-1",
        "statement": "example",
        "claim_kind": "FORMAL",
        "epistemic_status": "REPORTED",
        "scope": "unit-test",
        "authority": False,
        "evidence_refs": ["e1"],
        "provenance_refs": [],
    }
    base.update(overrides)
    return base


def _relation(**overrides):
    base = {
        "schema_version": "r4.epistemic.relation.v1",
        "relation_id": "R-1",
        "source_claim_id": "C-1",
        "target_claim_id": "C-2",
        "relation_type": "SUPPORTS",
        "evidence_refs": ["ev-1"],
        "scope": "unit-test",
        "epistemic_status": "REPORTED",
        "authority": False,
    }
    base.update(overrides)
    return base


def _prov(artifact_id: str, lineage_id: str, bases=(), **overrides):
    base = {
        "schema_version": "r4.epistemic.provenance.v1",
        "artifact_id": artifact_id,
        "digest": "abc" + artifact_id,
        "source_id": "src-" + artifact_id,
        "lineage_id": lineage_id,
        "authority": False,
        "parent_sources": [],
        "independence_basis_refs": [b.to_dict() if hasattr(b, "to_dict") else b for b in bases],
    }
    base.update(overrides)
    return ProvenanceRecord.from_dict(base)


class TestClaimKindsAndStatus(unittest.TestCase):
    def test_formal_and_symbolic_remain_distinct(self):
        self.assertTrue(formal_and_symbolic_are_distinct("FORMAL", "SYMBOLIC"))
        self.assertIn("FORMAL", CLAIM_KINDS)
        self.assertIn("SYMBOLIC", CLAIM_KINDS)
        a = EpistemicClaimRecord.from_dict(_claim(claim_kind="FORMAL"))
        b = EpistemicClaimRecord.from_dict(_claim(claim_id="C-2", claim_kind="SYMBOLIC"))
        self.assertNotEqual(a.claim_kind, b.claim_kind)

    def test_reported_cannot_silently_become_observed(self):
        with self.assertRaises(EpistemicStatusError):
            assert_no_silent_status_promotion("REPORTED", "OBSERVED")

    def test_reported_cannot_silently_become_verified_scope(self):
        with self.assertRaises(EpistemicStatusError):
            assert_no_silent_status_promotion("REPORTED", "VERIFIED_SCOPE")

    def test_ambiguous_accepted(self):
        rec = EpistemicClaimRecord.from_dict(_claim(epistemic_status="AMBIGUOUS"))
        self.assertEqual(rec.epistemic_status, "AMBIGUOUS")
        validate_epistemic_record(rec.to_dict(), kind="claim")

    def test_unresolved_accepted(self):
        rec = EpistemicClaimRecord.from_dict(_claim(epistemic_status="UNRESOLVED"))
        self.assertEqual(rec.epistemic_status, "UNRESOLVED")
        validate_epistemic_record(rec.to_dict(), kind="claim")


class TestRelationContract(unittest.TestCase):
    def test_analogous_to_cannot_satisfy_causes(self):
        rel = RelationAsClaim.from_dict(
            _relation(relation_type="ANALOGOUS_TO", extra={"satisfies": "CAUSES"})
        )
        with self.assertRaises(RelationSatisfactionError):
            analogous_to_cannot_satisfy_causes(rel)
        self.assertFalse(relation_may_satisfy("ANALOGOUS_TO", "CAUSES"))

    def test_malformed_relation_missing_evidence_fails(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _relation(evidence_refs=[]), kind="relation"
            )

    def test_malformed_relation_missing_scope_fails(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(_relation(scope=""), kind="relation")


class TestProvenanceAndOrigins(unittest.TestCase):
    def test_several_artifacts_one_lineage_count_as_one_origin(self):
        basis = IndependenceBasis(
            basis_id="b1",
            basis_kind="DISTINCT_OBSERVER",
            refs=["obs-1"],
        )
        records = [
            _prov("a1", "L1", bases=(basis,)),
            _prov("a2", "L1", bases=(basis,)),
            _prov("a3", "L1", bases=(basis,)),
        ]
        acct = account_independent_origins(records)
        self.assertEqual(acct.artifact_count, 3)
        self.assertEqual(acct.independent_evidence_count, 1)

    def test_self_asserted_independence_does_not_increase_count(self):
        self_decl = IndependenceBasis(
            basis_id="sd1",
            basis_kind=SELF_DECLARED_INDEPENDENCE,
            refs=[],
        )
        records = [
            _prov("a1", "L1", bases=(self_decl,)),
            _prov("a2", "L2", bases=(self_decl,)),
        ]
        acct = account_independent_origins(records)
        self.assertEqual(acct.artifact_count, 2)
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(set(acct.rejected_self_declared), {"L1", "L2"})

    def test_missing_provenance_prevents_verified_scope(self):
        with self.assertRaises(EpistemicStatusError):
            require_provenance_for_verified_scope("VERIFIED_SCOPE", [])
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _claim(epistemic_status="VERIFIED_SCOPE", provenance_refs=[]),
                kind="claim",
            )
        # With provenance refs present, VERIFIED_SCOPE validates.
        validate_epistemic_record(
            _claim(epistemic_status="VERIFIED_SCOPE", provenance_refs=["p1"]),
            kind="claim",
        )

    def test_insufficient_provenance_status_helpers(self):
        self.assertEqual(
            status_for_insufficient_provenance(has_any_provenance=False),
            "UNRESOLVED",
        )
        self.assertEqual(
            status_for_insufficient_provenance(has_any_provenance=True, ambiguous=True),
            "AMBIGUOUS",
        )

    def test_malformed_provenance_fails(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                {
                    "schema_version": "r4.epistemic.provenance.v1",
                    "artifact_id": "a1",
                    "authority": False,
                    # missing digest/source_id/lineage_id
                },
                kind="provenance",
            )


class TestLegacyCompatibility(unittest.TestCase):
    def test_legacy_records_remain_readable(self):
        legacy = {"id": "LEGACY-1", "statement": "old claim without r4 fields"}
        view = legacy_claim_view(legacy)
        self.assertIsInstance(view, LegacyClaimView)
        self.assertEqual(view.claim_id, "LEGACY-1")
        self.assertFalse(view.has_r4_epistemic)

    def test_no_synthetic_epistemic_backfill_for_legacy(self):
        legacy = {"claim_id": "LEGACY-2", "statement": "still legacy", "state": "PASS"}
        view = read_claim_record(legacy)
        self.assertIsInstance(view, LegacyClaimView)
        self.assertIsNone(view.epistemic_status)
        self.assertIsNone(view.claim_kind)
        # Campaign adapter must not invent status from workflow state.
        adapted = adapt_campaign_claim(
            {"claim_id": "LEGACY-2", "statement": "still legacy", "state": "PASS"}
        )
        self.assertIsInstance(adapted, LegacyClaimView)
        self.assertIsNone(adapted.epistemic_status)

    def test_audit_request_accepts_legacy_claim(self):
        req = AuditRequest.from_dict(
            {
                "target_path": ".",
                "claim": {"id": "LEGACY-3", "statement": "no epistemic block"},
            }
        )
        self.assertNotIn("epistemic", req.claim)


class TestNonAuthority(unittest.TestCase):
    def test_authority_always_false(self):
        rec = EpistemicClaimRecord.from_dict(_claim())
        self.assertIs(rec.authority, False)
        assert_authority_false(rec.to_dict())
        with self.assertRaises(AuthorityViolation):
            assert_authority_false({"authority": True})
        with self.assertRaises(AuthorityViolation):
            assert_authority_false({})
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(_claim(authority=True), kind="claim")

    def test_confidence_cannot_authorize(self):
        with self.assertRaises(AuthorityViolation):
            assert_confidence_cannot_authorize({"authority": False, "confidence_authorizes": True})
        # High confidence alone is fine (advisory).
        assert_confidence_cannot_authorize({"authority": False, "confidence": 0.99})

    def test_epistemic_status_cannot_create_human_final(self):
        with self.assertRaises(AuthorityViolation):
            assert_epistemic_cannot_create_human_final(
                {"authority": False, "creates_human_final": True}
            )
        with self.assertRaises(AuthorityViolation):
            assert_epistemic_cannot_create_human_final(
                {"authority": False, "epistemic_status": "HUMAN_FINAL"}
            )

    def test_epistemic_metadata_cannot_change_execution_authorization(self):
        with self.assertRaises(AuthorityViolation):
            assert_epistemic_cannot_change_execution_authorization(
                {"authority": False, "authorizes_execution": True}
            )


class TestCanonicalSerialization(unittest.TestCase):
    def test_deterministic_canonical_serialization(self):
        a = EpistemicClaimRecord.from_dict(_claim(notes="n", confidence=0.5))
        b = EpistemicClaimRecord.from_dict(_claim(confidence=0.5, notes="n"))
        self.assertEqual(a.canonical_json(), b.canonical_json())
        self.assertEqual(canonical_dumps(a.to_dict()), canonical_dumps(b.to_dict()))

    def test_digest_stability(self):
        a = EpistemicClaimRecord.from_dict(_claim())
        d1 = a.digest()
        d2 = canonical_digest(a.to_dict())
        d3 = EpistemicClaimRecord.from_dict(a.to_dict()).digest()
        self.assertEqual(d1, d2)
        self.assertEqual(d1, d3)
        self.assertEqual(len(d1), 64)


# ---------------------------------------------------------------------------
# Adversarial remediation: R4A-M1 .. R4A-M5
# ---------------------------------------------------------------------------


class TestR4AM1IndependentOriginSelfAssertion(unittest.TestCase):
    """R4A-M1: independence must not qualify from basis_kind alone."""

    def test_distinct_observer_empty_refs_does_not_increase_count(self):
        empty = IndependenceBasis(
            basis_id="b-empty",
            basis_kind="DISTINCT_OBSERVER",
            refs=(),
        )
        self.assertFalse(empty.is_qualified())
        acct = account_independent_origins([_prov("a1", "L-empty", bases=(empty,))])
        self.assertEqual(acct.independent_evidence_count, 0)

    def test_basis_kind_only_does_not_qualify(self):
        kind_only = IndependenceBasis(
            basis_id="b-kind",
            basis_kind="DISTINCT_METHOD",
            refs=(),
        )
        self.assertFalse(kind_only.is_qualified())
        acct = account_independent_origins([_prov("a1", "L-kind", bases=(kind_only,))])
        self.assertEqual(acct.independent_evidence_count, 0)

    def test_unsupported_basis_does_not_increase_count(self):
        unsupported = IndependenceBasis(
            basis_id="b-bad",
            basis_kind="TELEPATHY_DECLARED",
            refs=["somehow"],
        )
        self.assertFalse(unsupported.is_qualified())
        self.assertFalse(unsupported.is_supported_kind())
        acct = account_independent_origins(
            [_prov("a1", "L-bad", bases=(unsupported,))]
        )
        self.assertEqual(acct.independent_evidence_count, 0)

    def test_self_declared_without_evidence_does_not_increase_count(self):
        self_decl = IndependenceBasis(
            basis_id="sd",
            basis_kind=SELF_DECLARED_INDEPENDENCE,
            refs=(),
        )
        self.assertFalse(self_decl.is_qualified())
        acct = account_independent_origins([_prov("a1", "L-sd", bases=(self_decl,))])
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertIn("L-sd", acct.rejected_self_declared)

    def test_qualified_basis_with_refs_does_count(self):
        ok = IndependenceBasis(
            basis_id="b-ok",
            basis_kind="DISTINCT_OBSERVER",
            refs=["observer-receipt-1"],
        )
        self.assertTrue(ok.is_qualified())
        acct = account_independent_origins([_prov("a1", "L-ok", bases=(ok,))])
        self.assertEqual(acct.independent_evidence_count, 1)


class TestR4AM2DerivedLineageInflation(unittest.TestCase):
    """R4A-M2: derived artifacts cannot manufacture new independent lineages."""

    def test_derived_artifact_with_new_lineage_id_rejected(self):
        parent = _prov("parent", "L-root")
        derived = _prov(
            "child",
            "L-NEW",
            derived_from="parent",
            digest="abcparent",
            source_id="src-parent",
        )
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([parent, derived])
        with self.assertRaises(ProvenanceGraphError):
            account_independent_origins([parent, derived])

    def test_nonexistent_parent_rejected(self):
        orphan = _prov("orphan", "L1", derived_from="missing-parent")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([orphan])

    def test_provenance_cycle_rejected(self):
        a = _prov("a", "L1", derived_from="b")
        b = _prov("b", "L1", derived_from="a", digest="abca", source_id="src-a")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_same_source_digest_multiple_claimed_lineages_do_not_inflate(self):
        basis = IndependenceBasis(
            basis_id="b1",
            basis_kind="DISTINCT_OBSERVER",
            refs=["obs-1"],
        )
        r1 = _prov(
            "a1",
            "L-claim-1",
            bases=(basis,),
            digest="same-digest",
            source_id="same-source",
        )
        r2 = _prov(
            "a2",
            "L-claim-2",
            bases=(basis,),
            digest="same-digest",
            source_id="same-source",
        )
        acct = account_independent_origins([r1, r2])
        self.assertEqual(acct.artifact_count, 2)
        self.assertEqual(acct.independent_evidence_count, 1)

    def test_repeated_derivative_artifacts_do_not_inflate(self):
        basis = IndependenceBasis(
            basis_id="b1",
            basis_kind="EXTERNAL_WITNESS_RECEIPT",
            refs=["wit-1"],
        )
        root = _prov(
            "root",
            "L-root",
            bases=(basis,),
            digest="d-root",
            source_id="src-root",
        )
        d1 = _prov(
            "d1",
            "L-root",
            derived_from="root",
            digest="d-root",
            source_id="src-root",
            parent_sources=["src-root"],
        )
        d2 = _prov(
            "d2",
            "L-root",
            derived_from="root",
            digest="d-root",
            source_id="src-root",
            parent_sources=["src-root"],
        )
        acct = account_independent_origins([root, d1, d2])
        self.assertEqual(acct.artifact_count, 3)
        self.assertEqual(acct.independent_evidence_count, 1)


class TestR4AM3VerifiedScopeValidationBypass(unittest.TestCase):
    """R4A-M3: integration hooks must use the complete R4 validator."""

    def test_adapter_rejects_provenance_free_verified_scope(self):
        with self.assertRaises(EpistemicValidationError):
            adapt_campaign_claim(
                {
                    "claim_id": "C-VS",
                    "statement": "should fail",
                    "epistemic": {
                        "schema_version": "r4.epistemic.claim.v1",
                        "claim_kind": "FORMAL",
                        "epistemic_status": "VERIFIED_SCOPE",
                        "scope": "adapter-test",
                        "authority": False,
                        "provenance_refs": [],
                    },
                }
            )

    def test_request_path_rejects_unknown_claim_kind(self):
        with self.assertRaises(ValueError):
            AuditRequest.from_dict(
                {
                    "target_path": ".",
                    "claim": {
                        "id": "REQ-BAD-KIND",
                        "statement": "bad kind",
                        "epistemic": {
                            "schema_version": "r4.epistemic.claim.v1",
                            "claim_kind": "NOT_A_REAL_KIND",
                            "epistemic_status": "REPORTED",
                            "scope": "req-test",
                            "authority": False,
                        },
                    },
                }
            )

    def test_request_path_does_not_persist_invalid_verified_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_root = Path(tmp)
            bad = {
                "id": "REQ-BAD-VS",
                "statement": "no provenance",
                "epistemic": {
                    "schema_version": "r4.epistemic.claim.v1",
                    "claim_kind": "EMPIRICAL",
                    "epistemic_status": "VERIFIED_SCOPE",
                    "scope": "req-test",
                    "authority": False,
                    "provenance_refs": [],
                },
            }
            with self.assertRaises(ValueError):
                AuditRequest.from_dict({"target_path": ".", "claim": bad})
            # Direct dataclass bypass still blocked at compile/persist.
            bypass = AuditRequest(target_path=".", claim=bad)
            with self.assertRaises(ValueError):
                compile_claim_and_scope(bypass, audit_root, "AUDIT-BAD")
            self.assertFalse((audit_root / "CLAIM.json").exists())

    def test_valid_legacy_request_still_works(self):
        req = AuditRequest.from_dict(
            {
                "target_path": ".",
                "claim": {"id": "LEGACY-OK", "statement": "legacy still fine"},
            }
        )
        self.assertEqual(req.claim["id"], "LEGACY-OK")
        self.assertNotIn("epistemic", req.claim)

    def test_valid_r4_request_still_works(self):
        req = AuditRequest.from_dict(
            {
                "target_path": ".",
                "claim": {
                    "id": "R4-OK",
                    "statement": "valid r4",
                    "epistemic": {
                        "schema_version": "r4.epistemic.claim.v1",
                        "claim_kind": "FORMAL",
                        "epistemic_status": "REPORTED",
                        "scope": "req-test",
                        "authority": False,
                        "evidence_refs": ["e1"],
                    },
                },
            }
        )
        self.assertEqual(req.claim["epistemic"]["epistemic_status"], "REPORTED")
        adapted = adapt_campaign_claim(
            {
                "claim_id": "R4-OK",
                "statement": "valid r4",
                "epistemic": req.claim["epistemic"],
            }
        )
        self.assertIsInstance(adapted, EpistemicClaimRecord)
        self.assertEqual(adapted.epistemic_status, "REPORTED")


class TestR4AM4RecursiveNonAuthority(unittest.TestCase):
    """R4A-M4: nested authority-like keys must be rejected."""

    def test_nested_extra_execution_authorized_rejected(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _claim(extra={"execution_authorized": True}),
                kind="claim",
            )

    def test_nested_human_final_assertion_rejected(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _claim(extra={"human_final": True}),
                kind="claim",
            )
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {"nested": {"human_final_status": "FINAL"}},
                }
            )

    def test_deeply_nested_authority_true_rejected(self):
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {"a": {"b": {"c": {"authority": True}}}},
                }
            )

    def test_arrays_objects_with_authority_like_assertions_rejected(self):
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {
                        "events": [
                            {"note": "ok"},
                            {"approved": True},
                        ]
                    },
                }
            )
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {"vector_authorized": "AUTHORIZED"},
                }
            )

    def test_benign_non_authoritative_metadata_accepted(self):
        rec = validate_epistemic_record(
            _claim(
                extra={
                    "observer": "lab-1",
                    "method": "hash-compare",
                    "notes_prose": "this text mentions approved and human final casually",
                }
            ),
            kind="claim",
        )
        self.assertEqual(rec.extra["observer"], "lab-1")
        enforce_non_authority(rec.to_dict())


class TestR4AM5CanonicalDigestOrderSemantics(unittest.TestCase):
    """R4A-M5: set-like refs normalize; ordered fields preserve order."""

    def test_reversed_set_like_refs_identical_digest(self):
        a = EpistemicClaimRecord.from_dict(
            _claim(evidence_refs=["e1", "e2", "e3"], provenance_refs=["p2", "p1"])
        )
        b = EpistemicClaimRecord.from_dict(
            _claim(evidence_refs=["e3", "e2", "e1"], provenance_refs=["p1", "p2"])
        )
        self.assertEqual(a.digest(), b.digest())
        self.assertEqual(a.canonical_json(), b.canonical_json())
        self.assertEqual(
            canonical_digest({"evidence_refs": ["b", "a"], "authority": False}),
            canonical_digest({"evidence_refs": ["a", "b"], "authority": False}),
        )

    def test_duplicate_refs_handled_deterministically(self):
        a = EpistemicClaimRecord.from_dict(
            _claim(evidence_refs=["e1", "e1", "e2"])
        )
        b = EpistemicClaimRecord.from_dict(
            _claim(evidence_refs=["e2", "e1"])
        )
        self.assertEqual(a.evidence_refs, ("e1", "e2"))
        self.assertEqual(a.digest(), b.digest())
        norm = normalize_sequences({"parent_sources": ["s2", "s1", "s2"]})
        self.assertEqual(norm["parent_sources"], ["s1", "s2"])

    def test_ordered_fields_preserve_order_semantics(self):
        # R4-A currently has no ORDERED sequence fields; SET-LIKE are documented.
        self.assertIn("evidence_refs", SET_LIKE_SEQUENCE_FIELDS)
        self.assertIn("provenance_refs", SET_LIKE_SEQUENCE_FIELDS)
        self.assertIn("parent_sources", SET_LIKE_SEQUENCE_FIELDS)
        self.assertIn("independence_basis_refs", SET_LIKE_SEQUENCE_FIELDS)
        self.assertIn("refs", SET_LIKE_SEQUENCE_FIELDS)
        # Unknown / non-set-like sequences preserve declaration order.
        payload = {"steps": ["z", "a", "m"]}
        self.assertNotIn("steps", SET_LIKE_SEQUENCE_FIELDS)
        self.assertNotIn("steps", ORDERED_SEQUENCE_FIELDS)
        self.assertEqual(normalize_sequences(payload)["steps"], ["z", "a", "m"])


class TestNonmaterialLocalGuards(unittest.TestCase):
    """Local nonmaterial closures supporting material fixes."""

    def test_reject_string_as_iterable_refs(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _claim(evidence_refs="not-a-list"),
                kind="claim",
            )

    def test_reject_unknown_directionality(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _relation(directionality="sideways"),
                kind="relation",
            )

    def test_reject_empty_claim_id(self):
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(_claim(claim_id=""), kind="claim")


if __name__ == "__main__":
    unittest.main()
