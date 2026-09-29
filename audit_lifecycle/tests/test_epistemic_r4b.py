"""Focused R4-B reconstructability + immutable review-disagreement tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF_ROOT = ROOT.parent
sys.path.insert(0, str(WF_ROOT))

from audit_lifecycle.epistemic.authority import (
    AuthorityViolation,
)
from audit_lifecycle.epistemic.provenance import (
    INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
)
from audit_lifecycle.epistemic.reconstructability import (
    ReconstructabilityError,
    ReconstructabilityInputs,
    ReconstructabilityReport,
    derive_reconstructability_report,
    emit_reconstructability_report,
    verify_reconstructability_at_root,
    verify_reconstructability_report,
)
from audit_lifecycle.epistemic.review_disagreement import (
    ReviewDisagreementError,
    create_disagreement_record,
    create_successor_record,
    validate_disagreement_record,
    verify_disagreement_records_at_root,
    write_disagreement_record,
)
from audit_lifecycle.epistemic.serialize import canonical_digest, canonical_dumps
from audit_lifecycle.request import read_json, write_json


def _complete_inputs(**overrides) -> ReconstructabilityInputs:
    base = dict(
        audit_id="WFA-TEST-001",
        audit_request={
            "audit_id": "WFA-TEST-001",
            "claim": {"id": "C-1", "statement": "s"},
            "target_path": "/t",
        },
        claim={"claim_id": "C-1", "statement": "s", "adapter": "hash_claim"},
        scope={"audit_id": "WFA-TEST-001", "policy": {}},
        provenance_pin={
            "files": [{"relative_path": "a.txt", "sha256": "abc"}],
            "classification": "PINNED_INPUT",
        },
        decision={"decision": "PASS", "claim_result": "PASS"},
    )
    base.update(overrides)
    return ReconstructabilityInputs(**base)


class ReconstructabilityTests(unittest.TestCase):
    def test_complete_inputs_reconstructable_true(self):
        report = derive_reconstructability_report(_complete_inputs())
        self.assertTrue(report.reconstructable)
        self.assertEqual(report.missing_inputs, ())
        self.assertFalse(report.authority)
        self.assertEqual(report.schema_version, "r4.epistemic.reconstructability.v1")

    def test_missing_required_input_false(self):
        report = derive_reconstructability_report(
            _complete_inputs(claim=None)
        )
        self.assertFalse(report.reconstructable)
        self.assertIn("CLAIM.json", report.missing_inputs)

    def test_unresolved_assumption_preserved(self):
        report = derive_reconstructability_report(
            _complete_inputs(
                claim={"claim_id": "OTHER", "statement": "s"},
            )
        )
        self.assertIn("CLAIM_ID_MISMATCH_REQUEST_VS_CLAIM", report.unresolved_assumptions)
        self.assertFalse(report.reconstructable)
        # Verification preserves assumptions — stripping them fails.
        stored = report.to_dict()
        stored["unresolved_assumptions"] = []
        stored["reconstructable"] = True
        # Rebind outer digest to mimic naive rehash
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        result = verify_reconstructability_report(stored, _complete_inputs(
            claim={"claim_id": "OTHER", "statement": "s"},
        ))
        self.assertFalse(result["ok"])

    def test_missing_inputs_manually_removed_fails(self):
        inputs = _complete_inputs(claim=None)
        report = derive_reconstructability_report(inputs)
        self.assertFalse(report.reconstructable)
        stored = report.to_dict()
        stored["missing_inputs"] = []
        stored["reconstructable"] = True
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        self.assertFalse(verify_reconstructability_report(stored, inputs)["ok"])

    def test_reconstructable_manually_flipped_fails(self):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        stored["reconstructable"] = False
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        self.assertFalse(verify_reconstructability_report(stored, inputs)["ok"])

    def test_reproduction_command_changed_fails(self):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        cmds = list(stored["reproduction_commands"])
        cmds[0] = {**cmds[0], "argv_template": ["rm", "-rf", "/"]}
        stored["reproduction_commands"] = cmds
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        self.assertFalse(verify_reconstructability_report(stored, inputs)["ok"])

    def test_input_digest_changed_fails(self):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        digests = dict(stored["canonical_input_digests"])
        digests["CLAIM.json"] = "0" * 64
        stored["canonical_input_digests"] = digests
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        self.assertFalse(verify_reconstructability_report(stored, inputs)["ok"])

    def test_rebound_rehashed_but_semantically_altered_fails(self):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        stored["artifact_count"] = report.artifact_count + 99
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        result = verify_reconstructability_report(stored, inputs)
        self.assertFalse(result["ok"])
        self.assertIn("artifact_count", result.get("mismatched_fields", []))

    def test_independent_evidence_count_cannot_become_positive(self):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        self.assertEqual(report.independent_evidence_count, 0)
        stored = report.to_dict()
        stored["independent_evidence_count"] = 3
        with self.assertRaises(ReconstructabilityError):
            ReconstructabilityReport.from_dict(stored)

    def test_not_configured_admission_status_preserved(self):
        report = derive_reconstructability_report(_complete_inputs())
        self.assertEqual(
            report.independent_evidence_admission_status,
            INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
        )
        self.assertEqual(report.independent_evidence_admission_status, "NOT_CONFIGURED")
        stored = report.to_dict()
        stored["independent_evidence_admission_status"] = "CONFIGURED"
        with self.assertRaises(ReconstructabilityError):
            ReconstructabilityReport.from_dict(stored)

    def test_report_cannot_create_human_final(self):
        report = derive_reconstructability_report(_complete_inputs())
        stored = report.to_dict()
        stored["human_final"] = True
        with self.assertRaises((AuthorityViolation, ReconstructabilityError)):
            ReconstructabilityReport.from_dict(stored)

    def test_report_cannot_authorize_execution(self):
        report = derive_reconstructability_report(_complete_inputs())
        stored = report.to_dict()
        stored["authority"] = True
        with self.assertRaises((AuthorityViolation, ReconstructabilityError)):
            ReconstructabilityReport.from_dict(stored)
        stored2 = report.to_dict()
        stored2["execution_authorized"] = True
        with self.assertRaises((AuthorityViolation, ReconstructabilityError)):
            ReconstructabilityReport.from_dict(stored2)

    def test_report_cannot_change_weaver_pass_fail(self):
        report = derive_reconstructability_report(_complete_inputs())
        stored = report.to_dict()
        stored["weaver_pass"] = True
        with self.assertRaises((AuthorityViolation, ReconstructabilityError)):
            ReconstructabilityReport.from_dict(stored)
        stored2 = report.to_dict()
        stored2["weaver_fail"] = True
        with self.assertRaises((AuthorityViolation, ReconstructabilityError)):
            ReconstructabilityReport.from_dict(stored2)

    def test_deterministic_canonical_output_digest(self):
        a = derive_reconstructability_report(_complete_inputs())
        b = derive_reconstructability_report(_complete_inputs())
        self.assertEqual(a.report_digest, b.report_digest)
        self.assertEqual(canonical_dumps(a.to_dict()), canonical_dumps(b.to_dict()))
        self.assertTrue(verify_reconstructability_report(a, _complete_inputs())["ok"])

    def test_legacy_without_report_optional(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-LEGACY"
            root.mkdir()
            result = verify_reconstructability_at_root(root)
            self.assertTrue(result["ok"])
            self.assertFalse(result["present"])
            self.assertEqual(result["status"], "RECONSTRUCTABILITY_ABSENT_OPTIONAL")


class DisagreementTests(unittest.TestCase):
    def _positions(self, a="PASS", b="FAIL"):
        return [
            {"reviewer_id": "rev-A", "position": a, "label": "A"},
            {"reviewer_id": "rev-B", "position": b, "label": "B"},
        ]

    def test_conflicting_positions_persist(self):
        rec = create_disagreement_record(
            disagreement_id="D-1",
            subject_id="WFA-TEST-001",
            reviewer_positions=self._positions(),
            scope="unit-test",
            category="REVIEWER_INTERPRETATION",
            status="OPEN",
            reason="conflict",
        )
        positions = {p["reviewer_id"]: p["position"] for p in rec.reviewer_positions}
        self.assertEqual(positions["rev-A"], "PASS")
        self.assertEqual(positions["rev-B"], "FAIL")
        # No synthetic consensus field
        self.assertNotIn("consensus", rec.to_dict())

    def test_ambiguous_accepted(self):
        rec = create_disagreement_record(
            disagreement_id="D-amb",
            subject_id="S-1",
            reviewer_positions=self._positions("AMBIGUOUS", "AMBIGUOUS"),
            scope="unit",
            category="GENUINELY_AMBIGUOUS",
            status="AMBIGUOUS",
        )
        self.assertEqual(rec.status, "AMBIGUOUS")
        validate_disagreement_record(rec)

    def test_unresolved_accepted(self):
        rec = create_disagreement_record(
            disagreement_id="D-unr",
            subject_id="S-1",
            reviewer_positions=self._positions(),
            scope="unit",
            category="MISSING_EVIDENCE",
            status="UNRESOLVED",
        )
        self.assertEqual(rec.status, "UNRESOLVED")

    def test_no_forced_resolution(self):
        rec = create_disagreement_record(
            disagreement_id="D-open",
            subject_id="S-1",
            reviewer_positions=self._positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
            status="OPEN",
        )
        # Initial constructor rejects RESOLVED_BY_SUCCESSOR
        with self.assertRaises(ReviewDisagreementError):
            create_disagreement_record(
                disagreement_id="D-bad",
                subject_id="S-1",
                reviewer_positions=self._positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
                status="RESOLVED_BY_SUCCESSOR",
            )
        self.assertEqual(rec.status, "OPEN")

    def test_original_immutable_and_successor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prior = create_disagreement_record(
                disagreement_id="D-orig",
                subject_id="S-1",
                reviewer_positions=self._positions(),
                scope="unit",
                category="SCOPE_DISPUTE",
                status="OPEN",
                reason="initial conflict",
            )
            path = write_disagreement_record(root, prior)
            prior_bytes = path.read_bytes()
            prior_digest = prior.record_digest

            succ = create_successor_record(
                prior,
                disagreement_id="D-succ",
                status="RESOLVED_BY_SUCCESSOR",
                resolution_note="documented without rewriting prior",
                reason="successor note",
            )
            self.assertEqual(succ.prior_record_digest, prior_digest)
            self.assertEqual(succ.successor_of, "D-orig")
            write_disagreement_record(root, succ)

            # Prior unchanged byte-for-byte
            self.assertEqual(path.read_bytes(), prior_bytes)
            self.assertEqual(
                validate_disagreement_record(read_json(path)).record_digest,
                prior_digest,
            )

    def test_overwrite_in_place_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-ow",
                subject_id="S-1",
                reviewer_positions=self._positions(),
                scope="unit",
                category="PROVENANCE_DISPUTE",
                status="OPEN",
            )
            path = write_disagreement_record(root, rec)
            # Corrupt on-disk bytes while keeping filename
            tampered = rec.to_dict()
            tampered["reason"] = "tampered-in-place"
            write_json(path, tampered)
            with self.assertRaises(ReviewDisagreementError):
                write_disagreement_record(root, rec)

    def test_reviewer_agreement_does_not_create_human_final(self):
        rec = create_disagreement_record(
            disagreement_id="D-agree",
            subject_id="S-1",
            reviewer_positions=self._positions("PASS", "PASS"),
            scope="unit",
            category="REVIEWER_INTERPRETATION",
            status="OPEN",
        )
        data = rec.to_dict()
        self.assertNotIn("human_final", data)
        data["human_final"] = True
        with self.assertRaises((AuthorityViolation, ReviewDisagreementError)):
            validate_disagreement_record(data)

    def test_reviewer_count_does_not_authorize_execution(self):
        positions = [
            {"reviewer_id": f"r{i}", "position": "PASS"} for i in range(5)
        ]
        rec = create_disagreement_record(
            disagreement_id="D-count",
            subject_id="S-1",
            reviewer_positions=positions,
            scope="unit",
            category="REVIEWER_INTERPRETATION",
            status="OPEN",
        )
        data = rec.to_dict()
        self.assertFalse(data["authority"])
        data["execution_authorized"] = True
        with self.assertRaises((AuthorityViolation, ReviewDisagreementError)):
            validate_disagreement_record(data)

    def test_malformed_reviewer_position_rejects(self):
        with self.assertRaises(ReviewDisagreementError):
            create_disagreement_record(
                disagreement_id="D-badpos",
                subject_id="S-1",
                reviewer_positions=[{"reviewer_id": "r1", "position": "WINNER"}],
                scope="unit",
                category="SPEC_AMBIGUITY",
            )
        with self.assertRaises(ReviewDisagreementError):
            create_disagreement_record(
                disagreement_id="D-badpos2",
                subject_id="S-1",
                reviewer_positions=["PASS"],
                scope="unit",
                category="SPEC_AMBIGUITY",
            )

    def test_malformed_predecessor_digest_rejects(self):
        prior = create_disagreement_record(
            disagreement_id="D-p",
            subject_id="S-1",
            reviewer_positions=self._positions(),
            scope="unit",
            category="RELATION_DISPUTE",
            status="OPEN",
        )
        data = prior.to_dict()
        data["prior_record_digest"] = "not-a-digest"
        # Injecting malformed prior onto a non-successor body
        with self.assertRaises(ReviewDisagreementError):
            validate_disagreement_record(data)

    def test_deterministic_canonical_serialization(self):
        kwargs = dict(
            disagreement_id="D-det",
            subject_id="S-1",
            reviewer_positions=self._positions(),
            scope="unit",
            category="CATEGORY_OVERLAP",
            status="OPEN",
            reason="x",
        )
        a = create_disagreement_record(**kwargs)
        b = create_disagreement_record(**kwargs)
        self.assertEqual(a.record_digest, b.record_digest)
        self.assertEqual(canonical_dumps(a.to_dict()), canonical_dumps(b.to_dict()))

    def test_tampered_record_fails_verification(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-tamp",
                subject_id="S-1",
                reviewer_positions=self._positions(),
                scope="unit",
                category="MISSING_EVIDENCE",
                status="UNRESOLVED",
            )
            path = write_disagreement_record(root, rec)
            payload = read_json(path)
            payload["reason"] = "mutated"
            # Keep filename / claimed digest — content no longer matches
            write_json(path, payload)
            result = verify_disagreement_records_at_root(root)
            self.assertFalse(result["ok"])

    def test_unresolved_may_remain_permanently(self):
        rec = create_disagreement_record(
            disagreement_id="D-perm",
            subject_id="S-1",
            reviewer_positions=self._positions(),
            scope="unit",
            category="GENUINELY_AMBIGUOUS",
            status="UNRESOLVED",
            reason="no consensus required",
        )
        # No API forces resolution; record validates as terminal UNRESOLVED.
        validate_disagreement_record(rec)
        self.assertEqual(rec.status, "UNRESOLVED")
        self.assertIsNone(rec.prior_record_digest)
        self.assertIsNone(rec.successor_of)


class R4BFreezeBindingSmoke(unittest.TestCase):
    def test_emit_and_verify_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B-SMOKE"
            root.mkdir()
            write_json(
                root / "AUDIT_REQUEST.json",
                {"claim": {"id": "C-1", "statement": "s"}, "target_path": "/t"},
            )
            write_json(
                root / "CLAIM.json",
                {"claim_id": "C-1", "statement": "s", "adapter": "hash_claim"},
            )
            write_json(root / "SCOPE.json", {"policy": {}})
            write_json(
                root / "PROVENANCE.json",
                {"files": [{"relative_path": "f", "sha256": "aa"}], "classification": "PINNED_INPUT"},
            )
            write_json(
                root / "DECISION.json",
                {"decision": "PASS", "claim_result": "PASS"},
            )
            report = emit_reconstructability_report(root)
            self.assertTrue(report.reconstructable)
            self.assertTrue((root / "RECONSTRUCTABILITY_REPORT.json").is_file())
            self.assertTrue(verify_reconstructability_at_root(root)["ok"])

            rec = create_disagreement_record(
                disagreement_id="D-smoke",
                subject_id=root.name,
                reviewer_positions=[
                    {"reviewer_id": "a", "position": "PASS"},
                    {"reviewer_id": "b", "position": "FAIL"},
                ],
                scope="smoke",
                category="REVIEWER_INTERPRETATION",
                status="OPEN",
            )
            write_disagreement_record(root, rec)
            self.assertTrue(verify_disagreement_records_at_root(root)["ok"])


if __name__ == "__main__":
    unittest.main()
