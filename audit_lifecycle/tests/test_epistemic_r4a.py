"""Focused R4-A epistemic contract tests.

Covers claim/relation/provenance contracts, non-authority invariants,
legacy compatibility, and canonical serialization stability.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF_ROOT = ROOT.parent
sys.path.insert(0, str(WF_ROOT))

from audit_lifecycle.epistemic.authority import (
    AuthorityViolation,
    assert_authority_false,
    assert_confidence_cannot_authorize,
    assert_epistemic_cannot_change_execution_authorization,
    assert_epistemic_cannot_create_human_final,
)
from audit_lifecycle.epistemic.compat import LegacyClaimView, legacy_claim_view, read_claim_record
from audit_lifecycle.epistemic.provenance import (
    IndependenceBasis,
    ProvenanceRecord,
    SELF_DECLARED_INDEPENDENCE,
    account_independent_origins,
    require_provenance_for_verified_scope,
    status_for_insufficient_provenance,
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
from audit_lifecycle.epistemic.serialize import canonical_digest, canonical_dumps
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


if __name__ == "__main__":
    unittest.main()
