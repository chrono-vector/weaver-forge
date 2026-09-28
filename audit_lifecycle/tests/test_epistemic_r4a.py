"""Focused R4-A epistemic contract tests.

Covers claim/relation/provenance contracts, non-authority invariants,
legacy compatibility, canonical serialization stability, and adversarial
remediation coverage for Codex material findings R4A-M1..M5 and R4A-R1-N1.
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
    IndependentOriginAccounting,
    ProvenanceGraphError,
    ProvenanceGraphIndex,
    ProvenanceRecord,
    SELF_DECLARED_INDEPENDENCE,
    ValidatedBasisRef,
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
    validate_provenance_dict,
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


def _vref(ref_kind: str, ref_id: str) -> ValidatedBasisRef:
    return ValidatedBasisRef(ref_kind=ref_kind, ref_id=ref_id)


def _qualified_basis(
    basis_id: str = "b1",
    *,
    kind: str = "DISTINCT_OBSERVER",
    ref_kind: str = "PROVENANCE_SOURCE",
    ref_id: str = "obs-1",
) -> IndependenceBasis:
    return IndependenceBasis(
        basis_id=basis_id,
        basis_kind=kind,
        refs=(_vref(ref_kind, ref_id),),
    )


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


def _anchor(
    *,
    artifact_id: str = "anchor",
    source_id: str = "obs-1",
    lineage_id: str = "L-anchor",
    digest: str | None = None,
) -> ProvenanceRecord:
    """Accepted provenance entity that validates a basis ref target."""
    return _prov(
        artifact_id,
        lineage_id,
        digest=digest or f"d-{artifact_id}",
        source_id=source_id,
    )


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
        basis = _qualified_basis()
        records = [
            _anchor(),
            _prov("a1", "L1", bases=(basis,)),
            _prov("a2", "L1", bases=(basis,)),
            _prov("a3", "L1", bases=(basis,)),
        ]
        acct = account_independent_origins(records)
        self.assertEqual(acct.artifact_count, 4)
        # M1 zero-count admission model: count stays 0 under NOT_CONFIGURED.
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(acct.qualified_lineage_ids, ())
        self.assertEqual(
            acct.independent_evidence_admission_status, "NOT_CONFIGURED"
        )
        self.assertEqual(set(acct.lineage_ids), {"L-anchor", "L1"})

    def test_self_asserted_independence_does_not_increase_count(self):
        self_decl = IndependenceBasis(
            basis_id="sd1",
            basis_kind=SELF_DECLARED_INDEPENDENCE,
            refs=(),
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
# Adversarial remediation: R4A-M1 .. R4A-M5 + R4A-R1-N1
# ---------------------------------------------------------------------------


class TestR4AM1IndependentOriginSelfAssertion(unittest.TestCase):
    """R4A-M1: independence must not qualify from self-asserted refs."""

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

    def test_arbitrary_nonempty_self_asserted_ref_does_not_qualify(self):
        """DISTINCT_OBSERVER + arbitrary nonempty string must not count."""
        with self.assertRaises((ValueError, EpistemicValidationError)):
            IndependenceBasis(
                basis_id="b-arb",
                basis_kind="DISTINCT_OBSERVER",
                refs=("self-asserted-ref",),  # type: ignore[arg-type]
            )
        # Even if smuggled via raw dict construction path:
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(
                {
                    "schema_version": "r4.epistemic.provenance.v1",
                    "artifact_id": "a1",
                    "digest": "d1",
                    "source_id": "s1",
                    "lineage_id": "L1",
                    "authority": False,
                    "independence_basis_refs": [
                        {
                            "basis_id": "b-arb",
                            "basis_kind": "DISTINCT_OBSERVER",
                            "refs": ["self-asserted-ref"],
                        }
                    ],
                }
            )

    def test_self_referential_ref_does_not_qualify(self):
        basis = IndependenceBasis(
            basis_id="b-self",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_ARTIFACT", "a1"),),
        )
        rec = _prov("a1", "L-self", bases=(basis,))
        index = ProvenanceGraphIndex.build([rec])
        self.assertFalse(basis.is_qualified(graph_index=index, claimant=rec))
        acct = account_independent_origins([rec])
        self.assertEqual(acct.independent_evidence_count, 0)

    def test_unrelated_ref_does_not_qualify(self):
        basis = IndependenceBasis(
            basis_id="b-unrel",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_SOURCE", "not-in-this-graph"),),
        )
        rec = _prov("a1", "L-unrel", bases=(basis,))
        index = ProvenanceGraphIndex.build([rec])
        self.assertFalse(basis.is_qualified(graph_index=index, claimant=rec))
        acct = account_independent_origins([rec])
        self.assertEqual(acct.independent_evidence_count, 0)

    def test_unsupported_ref_kind_rejected(self):
        with self.assertRaises(ValueError):
            ValidatedBasisRef(ref_kind="TELEPATHY_RECEIPT", ref_id="x")
        with self.assertRaises((ValueError, EpistemicValidationError)):
            IndependenceBasis.from_dict(
                {
                    "basis_id": "b-bad-ref",
                    "basis_kind": "DISTINCT_OBSERVER",
                    "refs": [{"ref_kind": "TELEPATHY_RECEIPT", "ref_id": "x"}],
                }
            )

    def test_unsupported_basis_does_not_increase_count(self):
        unsupported = IndependenceBasis(
            basis_id="b-bad",
            basis_kind="TELEPATHY_DECLARED",
            refs=(_vref("PROVENANCE_SOURCE", "obs-1"),),
        )
        self.assertFalse(unsupported.is_qualified())
        self.assertFalse(unsupported.is_supported_kind())
        acct = account_independent_origins(
            [_anchor(), _prov("a1", "L-bad", bases=(unsupported,))]
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

    def test_valid_defensible_basis_reference_does_count(self):
        ok = _qualified_basis()
        anchor = _anchor()
        subject = _prov("a1", "L-ok", bases=(ok,))
        index = ProvenanceGraphIndex.build([anchor, subject])
        # Under NOT_CONFIGURED, descriptive basis never positively qualifies.
        self.assertFalse(ok.is_qualified(graph_index=index, claimant=subject))
        self.assertFalse(ok.is_qualified())
        acct = account_independent_origins([anchor, subject])
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(acct.qualified_lineage_ids, ())
        self.assertEqual(
            acct.independent_evidence_admission_status, "NOT_CONFIGURED"
        )
        # Basis metadata remains descriptive on the record.
        self.assertEqual(subject.independence_basis_refs[0].basis_kind, "DISTINCT_OBSERVER")
        self.assertEqual(len(subject.independence_basis_refs[0].refs), 1)


class TestR4AM2DerivedLineageInflation(unittest.TestCase):
    """R4A-M2: derived/parent graph semantics and origin collapsing."""

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

    def test_nonexistent_parent_sources_rejected(self):
        orphan = _prov("orphan", "L1", parent_sources=["missing-parent"])
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([orphan])

    def test_provenance_cycle_rejected(self):
        a = _prov("a", "L1", derived_from="b")
        b = _prov("b", "L1", derived_from="a", digest="abca", source_id="src-a")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_two_node_parent_sources_cycle_rejected(self):
        a = _prov("a", "L1", parent_sources=["b"])
        b = _prov("b", "L2", parent_sources=["a"])
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])
        with self.assertRaises(ProvenanceGraphError):
            account_independent_origins(
                [
                    _prov(
                        "a",
                        "L1",
                        bases=(_qualified_basis(ref_id="obs-a"),),
                        parent_sources=["b"],
                        source_id="obs-b",
                    ),
                    _prov(
                        "b",
                        "L2",
                        bases=(_qualified_basis(basis_id="b2", ref_id="obs-b"),),
                        parent_sources=["a"],
                        source_id="obs-a",
                    ),
                ]
            )

    def test_longer_parent_cycle_rejected(self):
        a = _prov("a", "L1", parent_sources=["b"])
        b = _prov("b", "L1", parent_sources=["c"])
        c = _prov("c", "L1", parent_sources=["a"])
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b, c])

    def test_parent_derived_mixed_cycle_rejected(self):
        a = _prov("a", "L1", derived_from="b")
        b = _prov("b", "L1", parent_sources=["a"], digest="abca", source_id="src-a")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_parent_linked_records_claiming_separate_lineages_do_not_inflate(self):
        basis_a = _qualified_basis(basis_id="ba", ref_id="obs-shared")
        basis_b = _qualified_basis(basis_id="bb", kind="DISTINCT_METHOD", ref_id="obs-shared")
        anchor = _anchor(source_id="obs-shared")
        a = _prov("a", "L-claim-1", bases=(basis_a,), parent_sources=["b"])
        b = _prov("b", "L-claim-2", bases=(basis_b,))
        acct = account_independent_origins([anchor, a, b])
        self.assertEqual(acct.artifact_count, 3)
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(
            acct.independent_evidence_admission_status, "NOT_CONFIGURED"
        )
        # Graph accepts the acyclic parent link; lineages remain recorded.
        validate_provenance_graph([anchor, a, b])
        self.assertIn("L-claim-1", acct.lineage_ids)
        self.assertIn("L-claim-2", acct.lineage_ids)

    def test_repeated_parent_chain_does_not_inflate_origin_count(self):
        basis = _qualified_basis(kind="EXTERNAL_WITNESS_RECEIPT", ref_id="wit-1")
        anchor = _anchor(source_id="wit-1", artifact_id="wit-art")
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
            digest="d-d1",
            source_id="src-d1",
            parent_sources=["root"],
        )
        d2 = _prov(
            "d2",
            "L-root",
            digest="d-d2",
            source_id="src-d2",
            parent_sources=["d1"],
        )
        acct = account_independent_origins([anchor, root, d1, d2])
        self.assertEqual(acct.artifact_count, 4)
        self.assertEqual(acct.independent_evidence_count, 0)
        validate_provenance_graph([anchor, root, d1, d2])

    def test_same_source_digest_multiple_claimed_lineages_do_not_inflate(self):
        basis = _qualified_basis()
        anchor = _anchor()
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
        acct = account_independent_origins([anchor, r1, r2])
        self.assertEqual(acct.artifact_count, 3)
        self.assertEqual(acct.independent_evidence_count, 0)
        validate_provenance_graph([anchor, r1, r2])

    def test_repeated_derivative_artifacts_do_not_inflate(self):
        basis = _qualified_basis(kind="EXTERNAL_WITNESS_RECEIPT", ref_id="wit-1")
        anchor = _anchor(source_id="wit-1", artifact_id="wit-art")
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
        )
        d2 = _prov(
            "d2",
            "L-root",
            derived_from="root",
            digest="d-root",
            source_id="src-root",
        )
        acct = account_independent_origins([anchor, root, d1, d2])
        self.assertEqual(acct.artifact_count, 4)
        self.assertEqual(acct.independent_evidence_count, 0)
        validate_provenance_graph([anchor, root, d1, d2])


class TestR4AM3VerifiedScopeValidationBypass(unittest.TestCase):
    """R4A-M3: explicit R4 must fail closed; legacy remains legacy."""

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

    def test_adapter_explicit_r4_missing_claim_kind_rejected(self):
        with self.assertRaises(EpistemicValidationError):
            adapt_campaign_claim(
                {
                    "claim_id": "C-MISS",
                    "statement": "missing kind",
                    "epistemic": {
                        "schema_version": "r4.epistemic.claim.v1",
                        "epistemic_status": "REPORTED",
                        "scope": "adapter-test",
                        "authority": False,
                    },
                }
            )

    def test_adapter_explicit_r4_unsupported_version_rejected(self):
        with self.assertRaises(EpistemicValidationError):
            adapt_campaign_claim(
                {
                    "claim_id": "C-VER",
                    "statement": "bad version",
                    "epistemic": {
                        "schema_version": "r4.epistemic.claim.v99",
                        "claim_kind": "FORMAL",
                        "epistemic_status": "REPORTED",
                        "scope": "adapter-test",
                        "authority": False,
                    },
                }
            )

    def test_adapter_explicit_authority_true_rejected_not_overwritten(self):
        with self.assertRaises(EpistemicValidationError):
            adapt_campaign_claim(
                {
                    "claim_id": "C-AUTH",
                    "statement": "authority true",
                    "epistemic": {
                        "schema_version": "r4.epistemic.claim.v1",
                        "claim_kind": "FORMAL",
                        "epistemic_status": "REPORTED",
                        "scope": "adapter-test",
                        "authority": True,
                    },
                }
            )

    def test_read_claim_explicit_r4_missing_claim_kind_rejected(self):
        with self.assertRaises(EpistemicValidationError):
            read_claim_record(
                {
                    "schema_version": "r4.epistemic.claim.v1",
                    "claim_id": "C",
                    "statement": "s",
                    "epistemic_status": "REPORTED",
                    "scope": "x",
                    "authority": False,
                }
            )

    def test_read_claim_explicit_r4_unsupported_version_rejected(self):
        with self.assertRaises(EpistemicValidationError):
            read_claim_record(
                {
                    "schema_version": "r4.epistemic.claim.v99",
                    "claim_id": "C",
                    "statement": "s",
                    "claim_kind": "FORMAL",
                    "epistemic_status": "REPORTED",
                    "scope": "x",
                    "authority": False,
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

    def test_request_path_rejects_missing_claim_kind(self):
        with self.assertRaises(ValueError):
            AuditRequest.from_dict(
                {
                    "target_path": ".",
                    "claim": {
                        "id": "REQ-MISS-KIND",
                        "statement": "missing kind",
                        "epistemic": {
                            "schema_version": "r4.epistemic.claim.v1",
                            "epistemic_status": "REPORTED",
                            "scope": "req-test",
                            "authority": False,
                        },
                    },
                }
            )

    def test_request_path_rejects_unsupported_version(self):
        with self.assertRaises(ValueError):
            AuditRequest.from_dict(
                {
                    "target_path": ".",
                    "claim": {
                        "id": "REQ-BAD-VER",
                        "statement": "bad ver",
                        "epistemic": {
                            "schema_version": "r4.epistemic.claim.v99",
                            "claim_kind": "FORMAL",
                            "epistemic_status": "REPORTED",
                            "scope": "req-test",
                            "authority": False,
                        },
                    },
                }
            )

    def test_request_path_rejects_authority_true(self):
        with self.assertRaises(ValueError):
            AuditRequest.from_dict(
                {
                    "target_path": ".",
                    "claim": {
                        "id": "REQ-AUTH",
                        "statement": "auth true",
                        "epistemic": {
                            "schema_version": "r4.epistemic.claim.v1",
                            "claim_kind": "FORMAL",
                            "epistemic_status": "REPORTED",
                            "scope": "req-test",
                            "authority": True,
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

    def test_claim_scope_does_not_overwrite_authority_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            audit_root = Path(tmp)
            (audit_root / "target.txt").write_text("t", encoding="utf-8")
            bad = AuditRequest(
                target_path=str(audit_root / "target.txt"),
                claim={
                    "id": "SCOPE-AUTH",
                    "statement": "auth true",
                    "epistemic": {
                        "schema_version": "r4.epistemic.claim.v1",
                        "claim_kind": "FORMAL",
                        "epistemic_status": "REPORTED",
                        "scope": "scope-test",
                        "authority": True,
                    },
                },
            )
            with self.assertRaises(ValueError):
                compile_claim_and_scope(bad, audit_root, "AUDIT-AUTH")
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
        adapted = adapt_campaign_claim(
            {"claim_id": "LEGACY-OK", "statement": "legacy still fine"}
        )
        self.assertIsInstance(adapted, LegacyClaimView)

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
        view = read_claim_record(_claim())
        self.assertIsInstance(view, EpistemicClaimRecord)


class TestR4AM4RecursiveNonAuthority(unittest.TestCase):
    """R4A-M4: nested authority-like / Weaver decision keys must be rejected."""

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

    def test_extra_weaver_pass_true_rejected(self):
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {"authority": False, "extra": {"weaver_pass": True}}
            )
        with self.assertRaises(EpistemicValidationError):
            validate_epistemic_record(
                _claim(extra={"weaver_pass": True}),
                kind="claim",
            )

    def test_nested_weaver_status_pass_rejected(self):
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {"nested": {"weaver_status": "PASS"}},
                }
            )

    def test_nested_final_status_rejected(self):
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {"decision": {"final_status": "FINAL"}},
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
        with self.assertRaises(AuthorityViolation):
            enforce_non_authority(
                {
                    "authority": False,
                    "extra": {
                        "layers": [
                            {"meta": {"weaver_fail": True}},
                        ]
                    },
                }
            )

    def test_benign_non_authoritative_metadata_accepted(self):
        rec = validate_epistemic_record(
            _claim(
                extra={
                    "observer": "lab-1",
                    "method": "hash-compare",
                    "notes_prose": "this text mentions approved and human final casually",
                    "description": "pipeline pass rate noted for humans; not a weaver_pass key",
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

    def test_validated_basis_ref_set_like_digest_stable(self):
        a = IndependenceBasis(
            basis_id="b1",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_SOURCE", "obs-1"), _vref("PROVENANCE_DIGEST", "d1")),
        )
        b = IndependenceBasis(
            basis_id="b1",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_DIGEST", "d1"), _vref("PROVENANCE_SOURCE", "obs-1")),
        )
        self.assertEqual(
            canonical_digest({"independence_basis_refs": [a.to_dict()]}),
            canonical_digest({"independence_basis_refs": [b.to_dict()]}),
        )


class TestR4AR1N1IndependenceBasisMemberShape(unittest.TestCase):
    """R4A-R1-N1: independence_basis_refs members must be mappings/records."""

    def _base(self, members):
        return {
            "schema_version": "r4.epistemic.provenance.v1",
            "artifact_id": "a1",
            "digest": "d1",
            "source_id": "s1",
            "lineage_id": "L1",
            "authority": False,
            "independence_basis_refs": members,
        }

    def test_integer_member_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(self._base([42]))
        with self.assertRaises(EpistemicValidationError):
            validate_provenance_dict(self._base([42]))

    def test_string_member_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(self._base(["not-a-mapping"]))

    def test_null_member_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(self._base([None]))

    def test_array_member_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(self._base([[{"basis_id": "x"}]]))

    def test_scalar_bool_member_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(self._base([True]))

    def test_malformed_mapping_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(self._base([{"basis_kind": "DISTINCT_OBSERVER"}]))

    def test_valid_mapping_member_accepted(self):
        rec = ProvenanceRecord.from_dict(
            self._base(
                [
                    {
                        "basis_id": "b1",
                        "basis_kind": "DISTINCT_OBSERVER",
                        "refs": [
                            {"ref_kind": "PROVENANCE_SOURCE", "ref_id": "obs-1"}
                        ],
                    }
                ]
            )
        )
        self.assertEqual(len(rec.independence_basis_refs), 1)
        self.assertIsInstance(rec.independence_basis_refs[0], IndependenceBasis)


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


# ---------------------------------------------------------------------------
# Root-cause final remediation invariants (M1–M4 + R1-N1; M5 preserved)
# ---------------------------------------------------------------------------


class TestRootM1ZeroCountAdmissionModel(unittest.TestCase):
    """M1: independent_evidence_count is always 0 under NOT_CONFIGURED."""

    def _assert_zero(self, records):
        acct = account_independent_origins(records)
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(acct.qualified_lineage_ids, ())
        self.assertEqual(
            acct.independent_evidence_admission_status, "NOT_CONFIGURED"
        )
        from audit_lifecycle.epistemic.provenance import (
            INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
        )

        self.assertEqual(INDEPENDENT_EVIDENCE_ADMISSION_STATUS, "NOT_CONFIGURED")
        return acct

    def test_arbitrary_claimant_only_graphs_always_count_zero(self):
        records = [
            _prov(
                "a1",
                "L1",
                bases=(_qualified_basis(ref_id="obs-x"),),
                source_id="obs-x",
            ),
            _prov(
                "a2",
                "L2",
                bases=(_qualified_basis(basis_id="b2", kind="DISTINCT_METHOD", ref_id="obs-y"),),
                source_id="obs-y",
            ),
        ]
        acct = self._assert_zero(records)
        self.assertEqual(acct.artifact_count, 2)

    def test_self_reference_counts_zero(self):
        basis = IndependenceBasis(
            basis_id="b-self",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_ARTIFACT", "a1"),),
        )
        self._assert_zero([_prov("a1", "L-self", bases=(basis,))])

    def test_unrelated_existing_ref_counts_zero(self):
        basis = IndependenceBasis(
            basis_id="b-unrel",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_SOURCE", "other"),),
        )
        self._assert_zero(
            [
                _anchor(source_id="other", artifact_id="other-art"),
                _prov("a1", "L1", bases=(basis,)),
            ]
        )

    def test_reciprocal_refs_count_zero(self):
        a_basis = IndependenceBasis(
            basis_id="ba",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_ARTIFACT", "b"),),
        )
        b_basis = IndependenceBasis(
            basis_id="bb",
            basis_kind="DISTINCT_OBSERVER",
            refs=(_vref("PROVENANCE_ARTIFACT", "a"),),
        )
        self._assert_zero(
            [
                _prov("a", "La", bases=(a_basis,)),
                _prov("b", "Lb", bases=(b_basis,)),
            ]
        )

    def test_fabricated_valid_looking_basis_counts_zero(self):
        fabricated = _qualified_basis(
            kind="INDEPENDENT_REPRODUCTION",
            ref_kind="PROVENANCE_DIGEST",
            ref_id="d-anchor",
        )
        self._assert_zero(
            [_anchor(digest="d-anchor"), _prov("subj", "L-fab", bases=(fabricated,))]
        )

    def test_graph_resolved_basis_counts_zero(self):
        ok = _qualified_basis()
        self._assert_zero([_anchor(), _prov("a1", "L-ok", bases=(ok,))])

    def test_valid_looking_basis_metadata_remains_descriptive(self):
        ok = _qualified_basis()
        rec = _prov("a1", "L-desc", bases=(ok,))
        self.assertEqual(rec.independence_basis_refs[0].basis_kind, "DISTINCT_OBSERVER")
        self.assertTrue(rec.independence_basis_refs[0].refs)
        self.assertFalse(rec.independence_basis_refs[0].is_qualified())
        self._assert_zero([_anchor(), rec])

    def test_admission_status_always_not_configured(self):
        acct = account_independent_origins([])
        self.assertEqual(acct.independent_evidence_admission_status, "NOT_CONFIGURED")
        self.assertEqual(acct.to_dict()["independent_evidence_admission_status"], "NOT_CONFIGURED")


class TestRootM2UnifiedProvenanceGraph(unittest.TestCase):
    """M2: one validated typed provenance graph before accounting."""

    def test_artifact_cycle_rejects(self):
        a = _prov("a", "L1", derived_from="b")
        b = _prov("b", "L1", derived_from="a", digest="abca", source_id="src-a")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_source_cycle_rejects(self):
        a = _prov("a", "L1", parent_sources=["src-b"], source_id="src-a")
        b = _prov("b", "L2", parent_sources=["src-a"], source_id="src-b")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_mixed_cycle_rejects(self):
        a = _prov("a", "L1", derived_from="b")
        b = _prov(
            "b",
            "L1",
            parent_sources=["src-a"],
            digest="abca",
            source_id="src-b",
        )
        # Need a with source src-a for production edge src-a -> a.
        a = _prov("a", "L1", derived_from="b", source_id="src-a")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_self_edge_rejects(self):
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph(
                [_prov("a", "L1", derived_from="a")]
            )
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph(
                [_prov("a", "L1", parent_sources=["a"])]
            )
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph(
                [_prov("a", "L1", parent_sources=["src-a"], source_id="src-a")]
            )

    def test_missing_source_parent_rejects(self):
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph(
                [_prov("a", "L1", parent_sources=["missing-src"])]
            )

    def test_ambiguous_source_parent_rejects(self):
        # artifact_id "shared" also used as another record's source_id.
        a = _prov("shared", "L1", source_id="src-a")
        b = _prov("b", "L2", parent_sources=["shared"], source_id="shared")
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([a, b])

    def test_valid_acyclic_chain_accepted(self):
        root = _prov("root", "L1", digest="d0", source_id="s0")
        mid = _prov("mid", "L1", derived_from="root", digest="d1", source_id="s1")
        leaf = _prov("leaf", "L1", parent_sources=["mid"], digest="d2", source_id="s2")
        index = validate_provenance_graph([root, mid, leaf])
        self.assertEqual(len(index.resolved_edges), 2)
        acct = account_independent_origins([root, mid, leaf])
        self.assertEqual(acct.artifact_count, 3)
        self.assertEqual(acct.independent_evidence_count, 0)

    def test_related_lineage_collapses_consistently_count_remains_zero(self):
        a = _prov("a", "L-claim-1", parent_sources=["b"], digest="d", source_id="s")
        b = _prov("b", "L-claim-2", digest="d", source_id="s")
        acct = account_independent_origins([a, b])
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(set(acct.lineage_ids), {"L-claim-1", "L-claim-2"})

    def test_unrelated_roots_remain_graph_distinct(self):
        a = _prov("a", "La", digest="da", source_id="sa")
        b = _prov("b", "Lb", digest="db", source_id="sb")
        index = validate_provenance_graph([a, b])
        self.assertEqual(len(index.resolved_edges), 0)
        acct = account_independent_origins([a, b])
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(set(acct.lineage_ids), {"La", "Lb"})


class TestRootM3ExplicitParserBoundary(unittest.TestCase):
    """M3: present epistemic key => fail-closed R4; absent => legacy."""

    def test_absent_epistemic_legacy_across_paths(self):
        from audit_lifecycle.epistemic.validation import parse_optional_epistemic_container

        result = parse_optional_epistemic_container(False, None, identity={})
        self.assertEqual(result.mode, "legacy")
        self.assertIsNone(result.record)
        req = AuditRequest.from_dict(
            {"target_path": ".", "claim": {"id": "L", "statement": "legacy"}}
        )
        self.assertNotIn("epistemic", req.claim)
        adapted = adapt_campaign_claim({"claim_id": "L", "statement": "legacy"})
        self.assertIsInstance(adapted, LegacyClaimView)

    def _reject_request(self, epi):
        with self.assertRaises(ValueError):
            AuditRequest.from_dict(
                {
                    "target_path": ".",
                    "claim": {"id": "X", "statement": "s", "epistemic": epi},
                }
            )

    def _reject_adapter(self, epi):
        with self.assertRaises(EpistemicValidationError):
            adapt_campaign_claim(
                {"claim_id": "X", "statement": "s", "epistemic": epi}
            )

    def _reject_claim_scope(self, epi):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "t.txt").write_text("t", encoding="utf-8")
            bypass = AuditRequest(
                target_path=str(root / "t.txt"),
                claim={"id": "X", "statement": "s", "epistemic": epi},
            )
            with self.assertRaises(ValueError):
                compile_claim_and_scope(bypass, root, "A1")

    def test_present_null_rejects(self):
        self._reject_request(None)
        self._reject_adapter(None)
        self._reject_claim_scope(None)

    def test_present_scalar_rejects(self):
        self._reject_request("not-a-mapping")
        self._reject_adapter(42)
        self._reject_claim_scope(True)

    def test_present_array_rejects(self):
        self._reject_request([])
        self._reject_adapter([{"claim_kind": "FORMAL"}])

    def test_empty_mapping_rejects(self):
        self._reject_request({})
        self._reject_adapter({})

    def test_partial_mapping_rejects(self):
        partial = {"schema_version": "r4.epistemic.claim.v1", "authority": False}
        self._reject_request(partial)
        self._reject_adapter(partial)

    def test_unsupported_version_rejects(self):
        bad = {
            "schema_version": "r4.epistemic.claim.v99",
            "claim_kind": "FORMAL",
            "epistemic_status": "REPORTED",
            "scope": "x",
            "authority": False,
        }
        self._reject_request(bad)
        self._reject_adapter(bad)

    def test_authority_true_rejects(self):
        bad = {
            "schema_version": "r4.epistemic.claim.v1",
            "claim_kind": "FORMAL",
            "epistemic_status": "REPORTED",
            "scope": "x",
            "authority": True,
        }
        self._reject_request(bad)
        self._reject_adapter(bad)

    def test_valid_r4_accepts(self):
        good = {
            "schema_version": "r4.epistemic.claim.v1",
            "claim_kind": "FORMAL",
            "epistemic_status": "REPORTED",
            "scope": "x",
            "authority": False,
        }
        req = AuditRequest.from_dict(
            {
                "target_path": ".",
                "claim": {"id": "R4", "statement": "ok", "epistemic": good},
            }
        )
        self.assertEqual(req.claim["epistemic"]["claim_kind"], "FORMAL")
        adapted = adapt_campaign_claim(
            {"claim_id": "R4", "statement": "ok", "epistemic": good}
        )
        self.assertIsInstance(adapted, EpistemicClaimRecord)

    def test_valid_legacy_accepts_without_backfill(self):
        view = read_claim_record({"claim_id": "L", "statement": "legacy only"})
        self.assertIsInstance(view, LegacyClaimView)
        self.assertIsNone(view.epistemic_status)


class TestRootM4CategoricalStructuralKeys(unittest.TestCase):
    """M4: reserved keys forbidden regardless of value; prose remains valid."""

    RESERVED = (
        "authority",
        "authorized",
        "execution_authorized",
        "execution_permission",
        "human_final",
        "human_final_status",
        "final_accepted",
        "vector_authorized",
        "eig_authorized",
        "weaver_pass",
        "weaver_fail",
        "weaver_status",
        "final_status",
        "approval",
        "approved",
    )

    VALUES = (
        True,
        False,
        None,
        "PASS",
        "INCONCLUSIVE",
        "ACCEPTED",
        "REJECTED",
        "PENDING",
        0,
        1,
        [],
        {},
    )

    def test_reserved_keys_case_separator_nested_array_all_reject(self):
        for key in self.RESERVED:
            variants = {
                key,
                key.upper(),
                key.replace("_", "-"),
                key.replace("_", " "),
                "".join(p.capitalize() for p in key.split("_")),
            }
            for variant in variants:
                for value in self.VALUES:
                    if variant.lower().replace("-", "").replace(" ", "") == "authority" and value is False:
                        # top-level authority:false is the sole allowed form;
                        # nested still rejects.
                        with self.assertRaises(AuthorityViolation):
                            enforce_non_authority(
                                {"authority": False, "extra": {variant: value}}
                            )
                        continue
                    with self.assertRaises(AuthorityViolation):
                        enforce_non_authority(
                            {"authority": False, "extra": {variant: value}}
                        )
                    with self.assertRaises(AuthorityViolation):
                        enforce_non_authority(
                            {
                                "authority": False,
                                "extra": {"nested": {variant: value}},
                            }
                        )
                    with self.assertRaises(AuthorityViolation):
                        enforce_non_authority(
                            {
                                "authority": False,
                                "extra": {"events": [{variant: value}]},
                            }
                        )

    def test_explicit_examples_reject(self):
        cases = [
            {"weaver_status": "PASS"},
            {"weaver_status": "INCONCLUSIVE"},
            {"human_final_status": "ACCEPTED"},
            {"human_final_status": "REJECTED"},
            {"final_status": "PENDING"},
            {"approved": False},
        ]
        for extra in cases:
            with self.assertRaises(AuthorityViolation):
                enforce_non_authority({"authority": False, "extra": extra})

    def test_benign_prose_remains_valid(self):
        rec = validate_epistemic_record(
            _claim(
                extra={
                    "review_note": (
                        "reviewer wrote that the prior run was approved"
                    ),
                }
            ),
            kind="claim",
        )
        self.assertIn("approved", rec.extra["review_note"])


class TestRootR1N1StrictStructuredTypes(unittest.TestCase):
    """R1-N1: no coercion of malformed structured evidence values."""

    def _prov_base(self, **overrides):
        base = {
            "schema_version": "r4.epistemic.provenance.v1",
            "artifact_id": "a1",
            "digest": "d1",
            "source_id": "s1",
            "lineage_id": "L1",
            "authority": False,
        }
        base.update(overrides)
        return base

    def test_cartesian_type_rejections_for_ids(self):
        bad_values = [None, True, False, 1, 1.5, [], {}, "   "]
        for field in ("artifact_id", "digest", "source_id", "lineage_id"):
            for bad in bad_values:
                payload = self._prov_base(**{field: bad})
                with self.assertRaises((ValueError, EpistemicValidationError)):
                    ProvenanceRecord.from_dict(payload)

    def test_schema_version_bool_number_rejected(self):
        for bad in [True, 1, None, ["r4.epistemic.provenance.v1"]]:
            with self.assertRaises((ValueError, EpistemicValidationError)):
                ProvenanceRecord.from_dict(self._prov_base(schema_version=bad))

    def test_derived_from_wrong_types_rejected(self):
        for bad in [True, 1, [], {}, ""]:
            with self.assertRaises((ValueError, EpistemicValidationError)):
                ProvenanceRecord.from_dict(self._prov_base(derived_from=bad))

    def test_parent_sources_wrong_shapes_rejected(self):
        for bad in ["src", 1, True, {}, [1], [None], ["  "], ["ok", 2]]:
            with self.assertRaises((ValueError, EpistemicValidationError)):
                ProvenanceRecord.from_dict(self._prov_base(parent_sources=bad))

    def test_basis_kind_and_ref_fields_no_coercion(self):
        for bad_kind in [None, True, 1, [], {}]:
            with self.assertRaises((ValueError, EpistemicValidationError)):
                IndependenceBasis.from_dict(
                    {"basis_id": "b1", "basis_kind": bad_kind, "refs": []}
                )
        for bad_ref in [None, True, 1, [], {}]:
            with self.assertRaises((ValueError, EpistemicValidationError)):
                ValidatedBasisRef.from_dict(
                    {"ref_kind": "PROVENANCE_SOURCE", "ref_id": bad_ref}
                )
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ValidatedBasisRef.from_dict(
                {"ref_kind": True, "ref_id": "x"}
            )

    def test_authority_must_be_boolean_false(self):
        for bad in [0, "false", None, True]:
            with self.assertRaises((ValueError, EpistemicValidationError, AuthorityViolation)):
                ProvenanceRecord.from_dict(self._prov_base(authority=bad))

    def test_mixed_valid_invalid_basis_list_rejected(self):
        with self.assertRaises((ValueError, EpistemicValidationError)):
            ProvenanceRecord.from_dict(
                self._prov_base(
                    independence_basis_refs=[
                        {
                            "basis_id": "b1",
                            "basis_kind": "DISTINCT_OBSERVER",
                            "refs": [
                                {
                                    "ref_kind": "PROVENANCE_SOURCE",
                                    "ref_id": "obs-1",
                                }
                            ],
                        },
                        42,
                    ]
                )
            )


class TestRootM5AdmissionStatusFieldPreserved(unittest.TestCase):
    """M5: serialization preserved; admission status field is stable."""

    def test_accounting_dict_round_trip_stable(self):
        acct = account_independent_origins(
            [_anchor(), _prov("a1", "L1", bases=(_qualified_basis(),))]
        )
        d1 = acct.to_dict()
        d2 = acct.to_dict()
        self.assertEqual(canonical_digest(d1), canonical_digest(d2))
        self.assertEqual(d1["independent_evidence_admission_status"], "NOT_CONFIGURED")
        self.assertEqual(d1["independent_evidence_count"], 0)
        self.assertIn("lineage_ids", SET_LIKE_SEQUENCE_FIELDS)


# ---------------------------------------------------------------------------
# R4-A final strictness remediation: F1 / F2 / F3
# ---------------------------------------------------------------------------


class TestFinalF1SourceResolutionExactlyOne(unittest.TestCase):
    """F1: SOURCE parent resolution must be exactly one canonical artifact."""

    def test_source_resolves_to_zero_artifacts_rejects(self):
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph(
                [_prov("a", "L1", parent_sources=["missing-src"])]
            )

    def test_source_resolves_to_one_artifact_accepts(self):
        root = _prov("root", "L1", source_id="solo-src", digest="d0")
        leaf = _prov(
            "leaf",
            "L2",
            parent_sources=["solo-src"],
            source_id="src-leaf",
            digest="d1",
        )
        index = validate_provenance_graph([root, leaf])
        self.assertEqual(len(index.resolved_edges), 1)
        self.assertEqual(index.resolved_edges[0].parent_kind, "SOURCE")
        self.assertEqual(index.resolved_edges[0].parent_id, "solo-src")

    def test_source_resolves_to_two_artifacts_rejects(self):
        a = _prov("a", "L1", source_id="dup-src", digest="da")
        b = _prov("b", "L2", source_id="dup-src", digest="db")
        leaf = _prov(
            "leaf",
            "L3",
            parent_sources=["dup-src"],
            source_id="src-leaf",
            digest="dl",
        )
        with self.assertRaises(ProvenanceGraphError) as ctx:
            validate_provenance_graph([a, b, leaf])
        self.assertIn("ambiguous SOURCE", str(ctx.exception))

    def test_source_resolves_to_several_artifacts_rejects(self):
        arts = [
            _prov(f"a{i}", f"L{i}", source_id="many-src", digest=f"d{i}")
            for i in range(4)
        ]
        leaf = _prov(
            "leaf",
            "L9",
            parent_sources=["many-src"],
            source_id="src-leaf",
            digest="dl",
        )
        with self.assertRaises(ProvenanceGraphError) as ctx:
            validate_provenance_graph([*arts, leaf])
        self.assertIn("ambiguous SOURCE", str(ctx.exception))

    def test_mixed_graph_with_one_ambiguous_source_edge_rejects_entire_graph(self):
        # Valid ARTIFACT edge + one ambiguous SOURCE edge => whole graph fails.
        root = _prov("root", "L1", source_id="s0", digest="d0")
        mid = _prov(
            "mid", "L1", derived_from="root", source_id="s1", digest="d1"
        )
        twin_a = _prov("twin-a", "L2", source_id="ambig-src", digest="dta")
        twin_b = _prov("twin-b", "L3", source_id="ambig-src", digest="dtb")
        leaf = _prov(
            "leaf",
            "L4",
            parent_sources=["ambig-src"],
            source_id="s-leaf",
            digest="dl",
        )
        with self.assertRaises(ProvenanceGraphError):
            validate_provenance_graph([root, mid, twin_a, twin_b, leaf])

    def test_duplicate_source_ids_without_source_parent_edge_still_ok(self):
        # Ambiguity applies to SOURCE *references*, not mere co-presence.
        a = _prov("a", "L1", source_id="shared", digest="da")
        b = _prov("b", "L2", source_id="shared", digest="db")
        index = validate_provenance_graph([a, b])
        self.assertEqual(len(index.resolved_edges), 0)


class TestFinalF2NoFalseyCollectionCoercion(unittest.TestCase):
    """F2: present collection fields must not coerce falsey values to empty."""

    FALSEY_INVALID = (None, False, 0, "", {})

    def _prov_base(self, **overrides):
        base = {
            "schema_version": "r4.epistemic.provenance.v1",
            "artifact_id": "a1",
            "digest": "d1",
            "source_id": "s1",
            "lineage_id": "L1",
            "authority": False,
        }
        base.update(overrides)
        return base

    def test_refs_absent_defaults_empty_present_falsey_rejects(self):
        ok = IndependenceBasis.from_dict(
            {"basis_id": "b1", "basis_kind": "DISTINCT_OBSERVER"}
        )
        self.assertEqual(ok.refs, ())
        empty = IndependenceBasis.from_dict(
            {"basis_id": "b1", "basis_kind": "DISTINCT_OBSERVER", "refs": []}
        )
        self.assertEqual(empty.refs, ())
        for bad in self.FALSEY_INVALID:
            with self.assertRaises(ValueError):
                IndependenceBasis.from_dict(
                    {
                        "basis_id": "b1",
                        "basis_kind": "DISTINCT_OBSERVER",
                        "refs": bad,
                    }
                )

    def test_parent_sources_absent_vs_present_falsey(self):
        absent = ProvenanceRecord.from_dict(self._prov_base())
        self.assertEqual(absent.parent_sources, ())
        empty = ProvenanceRecord.from_dict(self._prov_base(parent_sources=[]))
        self.assertEqual(empty.parent_sources, ())
        for bad in self.FALSEY_INVALID:
            with self.assertRaises(ValueError):
                ProvenanceRecord.from_dict(self._prov_base(parent_sources=bad))

    def test_independence_basis_refs_absent_vs_present_falsey(self):
        absent = ProvenanceRecord.from_dict(self._prov_base())
        self.assertEqual(absent.independence_basis_refs, ())
        empty = ProvenanceRecord.from_dict(
            self._prov_base(independence_basis_refs=[])
        )
        self.assertEqual(empty.independence_basis_refs, ())
        for bad in self.FALSEY_INVALID:
            with self.assertRaises(ValueError):
                ProvenanceRecord.from_dict(
                    self._prov_base(independence_basis_refs=bad)
                )

    def test_claim_provenance_and_evidence_refs_falsey_present_rejects(self):
        for field in ("evidence_refs", "provenance_refs"):
            absent_key = _claim()
            del absent_key[field]
            ok = EpistemicClaimRecord.from_dict(absent_key)
            self.assertEqual(getattr(ok, field), ())
            empty = EpistemicClaimRecord.from_dict(_claim(**{field: []}))
            self.assertEqual(getattr(empty, field), ())
            for bad in self.FALSEY_INVALID:
                with self.assertRaises(EpistemicStatusError):
                    EpistemicClaimRecord.from_dict(_claim(**{field: bad}))

    def test_relation_evidence_refs_falsey_present_rejects(self):
        for bad in self.FALSEY_INVALID:
            with self.assertRaises(
                (RelationSatisfactionError, EpistemicValidationError)
            ):
                RelationAsClaim.from_dict(_relation(evidence_refs=bad))


class TestFinalF3NoRelationFieldCoercion(unittest.TestCase):
    """F3: relation structured fields must already have schema-required types."""

    def test_integer_relation_id_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(relation_id=123))

    def test_boolean_relation_id_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(relation_id=True))

    def test_float_relation_id_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(relation_id=1.5))

    def test_integer_source_claim_id_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(source_claim_id=42))

    def test_boolean_target_claim_id_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(target_claim_id=False))

    def test_numeric_relation_type_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(relation_type=7))

    def test_boolean_directionality_rejects(self):
        with self.assertRaises(RelationSatisfactionError):
            RelationAsClaim.from_dict(_relation(directionality=True))

    def test_numeric_epistemic_status_rejects(self):
        with self.assertRaises((RelationSatisfactionError, EpistemicStatusError)):
            RelationAsClaim.from_dict(_relation(epistemic_status=1))

    def test_whitespace_only_ids_reject(self):
        for field in ("relation_id", "source_claim_id", "target_claim_id", "scope"):
            with self.assertRaises(RelationSatisfactionError):
                RelationAsClaim.from_dict(_relation(**{field: "   "}))

    def test_valid_relation_still_accepts(self):
        rel = RelationAsClaim.from_dict(_relation())
        self.assertEqual(rel.relation_id, "R-1")
        self.assertEqual(rel.directionality, "directed")


class TestOptionalAccountingHardening(unittest.TestCase):
    """Optional local invariant on IndependentOriginAccounting."""

    def test_positive_count_direct_construction_rejected(self):
        with self.assertRaises(ValueError):
            IndependentOriginAccounting(
                artifact_count=1,
                independent_evidence_count=1,
                lineage_ids=("L1",),
                qualified_lineage_ids=(),
            )

    def test_alternate_admission_status_rejected(self):
        with self.assertRaises(ValueError):
            IndependentOriginAccounting(
                artifact_count=0,
                independent_evidence_count=0,
                lineage_ids=(),
                qualified_lineage_ids=(),
                independent_evidence_admission_status="CONFIGURED",
            )

    def test_canonical_zero_path_still_ok(self):
        acct = account_independent_origins([])
        self.assertEqual(acct.independent_evidence_count, 0)
        self.assertEqual(acct.independent_evidence_admission_status, "NOT_CONFIGURED")


if __name__ == "__main__":
    unittest.main()
