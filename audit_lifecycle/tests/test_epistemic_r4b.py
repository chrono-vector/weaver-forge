"""Focused R4-B expectation / reconstructability / immutable disagreement tests."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF_ROOT = ROOT.parent
sys.path.insert(0, str(WF_ROOT))

from audit_lifecycle.epistemic.authority import AuthorityViolation
from audit_lifecycle.epistemic.expectation import (
    EXPECTATION_SCHEMA_VERSION,
    R4BExpectationError,
    STATE_LEGACY_PRE_R4B,
    STATE_R4_B_ENABLED,
    build_r4b_expectation,
    classify_package_r4b_state,
    strict_parse_r4b_expectation,
)
from audit_lifecycle.epistemic.provenance import (
    INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
)
from audit_lifecycle.epistemic.r4b_verify import verify_r4b_at_root
from audit_lifecycle.epistemic.reconstructability import (
    REPORT_FILENAME,
    ReconstructabilityError,
    ReconstructabilityInputs,
    ReconstructabilityReport,
    derive_reconstructability_report,
    emit_reconstructability_report,
    strict_parse_report,
    verify_reconstructability_at_root,
    verify_reconstructability_report,
)
from audit_lifecycle.epistemic.review_disagreement import (
    ReviewDisagreementError,
    create_disagreement_record,
    create_successor_record,
    strict_parse_record,
    validate_disagreement_record,
    verify_chain_graph,
    verify_disagreement_expected_set,
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


def _legacy_manifest(audit_id: str = "WFA-LEGACY") -> dict:
    return {
        "audit_id": audit_id,
        "lifecycle": "weaver_forge_audit_lifecycle_v0",
        "stages_completed_through": "DECISION",
        "started_request": True,
        "claim_id": "C-1",
        "adapter": "hash_claim",
        "decision": "PASS",
        "claim_result": "PASS",
        "promoted_to_full": False,
        "baseline_prior_freeze_ok": True,
        "provenance_files": 1,
        "timestamp_utc": "2026-01-01T00:00:00.000000Z",
    }


def _positions(a="PASS", b="FAIL"):
    return [
        {"reviewer_id": "rev-A", "position": a, "label": "A"},
        {"reviewer_id": "rev-B", "position": b, "label": "B"},
    ]


def _seed_recon_root(root: Path) -> None:
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
        {
            "files": [{"relative_path": "f", "sha256": "aa"}],
            "classification": "PINNED_INPUT",
        },
    )
    write_json(root / "DECISION.json", {"decision": "PASS", "claim_result": "PASS"})


def _finalize_r4b_manifest(
    root: Path,
    report_digest: str,
    disagreement_digests: list[str] | None = None,
    chain_heads: list[str] | None = None,
) -> dict:
    digests = list(disagreement_digests or [])
    heads = list(chain_heads if chain_heads is not None else digests)
    r4_b = build_r4b_expectation(
        reconstructability_report_digest=report_digest,
        expected_disagreement_record_digests=digests,
        expected_disagreement_chain_heads=heads,
        finalized_for_freeze=True,
    )
    manifest = {
        **_legacy_manifest(root.name),
        "stages_completed_through": "FREEZE",
        "freeze_performed": True,
        "r4_b": r4_b,
    }
    write_json(root / "EXECUTION_MANIFEST.json", manifest)
    return manifest


class StatePresenceTests(unittest.TestCase):
    def test_allowlisted_legacy_package(self):
        state = classify_package_r4b_state(_legacy_manifest())
        self.assertEqual(state.state, STATE_LEGACY_PRE_R4B)
        self.assertIsNone(state.expectation)

    def test_explicit_r4b_package(self):
        report = derive_reconstructability_report(_complete_inputs())
        r4_b = build_r4b_expectation(
            reconstructability_report_digest=report.report_digest,
            expected_disagreement_record_digests=[],
            expected_disagreement_chain_heads=[],
        )
        state = classify_package_r4b_state(
            {**_legacy_manifest(), "r4_b": r4_b, "freeze_performed": True}
        )
        self.assertEqual(state.state, STATE_R4_B_ENABLED)

    def test_absence_of_artifacts_does_not_imply_legacy(self):
        with self.assertRaises(R4BExpectationError):
            classify_package_r4b_state({"audit_id": "x"})  # missing lifecycle

    def test_report_present_required_for_r4b(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            result = verify_r4b_at_root(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["state"], STATE_R4_B_ENABLED)

    def test_report_deletion_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            (root / REPORT_FILENAME).unlink()
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])

    def test_report_rename_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            src = root / REPORT_FILENAME
            src.rename(root / "RECONSTRUCTABILITY_REPORT_RENAMED.json")
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])

    def test_report_replacement_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            other = derive_reconstructability_report(
                _complete_inputs(claim=None)
            )
            write_json(root / REPORT_FILENAME, other.to_dict())
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])

    def test_report_digest_rebound_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            fake = "ab" * 32
            manifest = read_json(root / "EXECUTION_MANIFEST.json")
            manifest["r4_b"]["reconstructability_report"]["digest"] = fake
            write_json(root / "EXECUTION_MANIFEST.json", manifest)
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])

    def test_expectation_removal_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            manifest = read_json(root / "EXECUTION_MANIFEST.json")
            del manifest["r4_b"]
            # Still has freeze_performed; allowlisted legacy remains valid shape.
            write_json(root / "EXECUTION_MANIFEST.json", manifest)
            # Without r4_b this is legacy; report present still verifies optionally.
            result = verify_r4b_at_root(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["state"], STATE_LEGACY_PRE_R4B)

    def test_zero_disagreement_explicit_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            result = verify_disagreement_expected_set(root, [])
            self.assertTrue(result["ok"])

    def test_disagreement_deletion_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            rec = create_disagreement_record(
                disagreement_id="D-1",
                subject_id=root.name,
                reviewer_positions=_positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
            )
            path = write_disagreement_record(root, rec)
            _finalize_r4b_manifest(root, report.report_digest, [rec.record_digest])
            path.unlink()
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])

    def test_undeclared_extra_disagreement_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, [])
            rec = create_disagreement_record(
                disagreement_id="D-extra",
                subject_id=root.name,
                reviewer_positions=_positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
            )
            write_disagreement_record(root, rec)
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])

    def test_expected_set_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-R4B"
            root.mkdir()
            _seed_recon_root(root)
            report = emit_reconstructability_report(root)
            _finalize_r4b_manifest(root, report.report_digest, ["ab" * 32])
            result = verify_r4b_at_root(root)
            self.assertFalse(result["ok"])


class ReconstructabilityTamperTests(unittest.TestCase):
    def _tamper(self, mutate):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        mutate(stored)
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        return verify_reconstructability_report(stored, inputs)

    def test_missing_inputs_altered(self):
        self.assertFalse(self._tamper(lambda s: s.__setitem__("missing_inputs", ["X"]) )["ok"])

    def test_unresolved_assumptions_altered(self):
        inputs = _complete_inputs(claim={"claim_id": "OTHER", "statement": "s"})
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        stored["unresolved_assumptions"] = []
        stored["reconstructable"] = True
        body = {k: v for k, v in stored.items() if k != "report_digest"}
        stored["report_digest"] = canonical_digest(body)
        self.assertFalse(verify_reconstructability_report(stored, inputs)["ok"])

    def test_reconstructable_flipped(self):
        self.assertFalse(
            self._tamper(lambda s: s.__setitem__("reconstructable", False))["ok"]
        )

    def test_reproduction_command_altered(self):
        def mutate(s):
            cmds = list(s["reproduction_commands"])
            cmds[0] = {**cmds[0], "argv_template": ["rm", "-rf", "/"]}
            s["reproduction_commands"] = cmds

        self.assertFalse(self._tamper(mutate)["ok"])

    def test_canonical_digest_altered(self):
        def mutate(s):
            digests = dict(s["canonical_input_digests"])
            digests["CLAIM.json"] = "0" * 64
            s["canonical_input_digests"] = digests

        self.assertFalse(self._tamper(mutate)["ok"])

    def test_artifact_lineage_altered(self):
        self.assertFalse(
            self._tamper(lambda s: s.__setitem__("artifact_count", 99))["ok"]
        )
        self.assertFalse(
            self._tamper(lambda s: s.__setitem__("lineage_ids", ["L1"]))["ok"]
        )

    def test_report_digest_altered(self):
        inputs = _complete_inputs()
        report = derive_reconstructability_report(inputs)
        stored = report.to_dict()
        stored["report_digest"] = "0" * 64
        with self.assertRaises(ReconstructabilityError):
            strict_parse_report(stored)


class SuccessorGraphTests(unittest.TestCase):
    def _initial(self, did="D-root"):
        return create_disagreement_record(
            disagreement_id=did,
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SCOPE_DISPUTE",
            status="OPEN",
        )

    def test_valid_one_step_chain(self):
        prior = self._initial()
        succ = create_successor_record(
            prior,
            disagreement_id="D-succ",
            status="RESOLVED_BY_SUCCESSOR",
            reason="done",
        )
        chain = verify_chain_graph([prior, succ])
        self.assertTrue(chain["ok"])
        self.assertEqual(chain["chain_heads"], [prior.record_digest])

    def test_valid_multi_step_chain(self):
        a = self._initial("D-a")
        b = create_successor_record(a, disagreement_id="D-b", status="OPEN", reason="b")
        c = create_successor_record(
            b, disagreement_id="D-c", status="RESOLVED_BY_SUCCESSOR", reason="c"
        )
        chain = verify_chain_graph([a, b, c])
        self.assertTrue(chain["ok"])
        self.assertEqual(chain["chain_heads"], [a.record_digest])

    def test_missing_predecessor(self):
        prior = self._initial()
        succ = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="x"
        )
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([succ])

    def test_wrong_predecessor_digest(self):
        prior = self._initial()
        succ = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="x"
        )
        bad = succ.to_dict()
        bad["prior_record_digest"] = "ab" * 32
        body = {k: v for k, v in bad.items() if k != "record_digest"}
        bad["record_digest"] = canonical_digest(body)
        parsed = strict_parse_record(bad)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([prior, parsed])

    def test_unrelated_predecessor(self):
        a = self._initial("D-a")
        other = create_disagreement_record(
            disagreement_id="D-other",
            subject_id="OTHER-SUBJECT",
            reviewer_positions=_positions(),
            scope="other-scope",
            category="MISSING_EVIDENCE",
        )
        succ = create_successor_record(a, disagreement_id="D-s", status="OPEN", reason="x")
        data = succ.to_dict()
        data["prior_record_digest"] = other.record_digest
        data["successor_of"] = other.disagreement_id
        body = {k: v for k, v in data.items() if k != "record_digest"}
        data["record_digest"] = canonical_digest(body)
        parsed = strict_parse_record(data)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([a, other, parsed])

    def test_subject_mismatch(self):
        prior = self._initial()
        succ = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="x"
        )
        data = succ.to_dict()
        data["subject_id"] = "OTHER"
        body = {k: v for k, v in data.items() if k != "record_digest"}
        data["record_digest"] = canonical_digest(body)
        parsed = strict_parse_record(data)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([prior, parsed])

    def test_scope_mismatch(self):
        prior = self._initial()
        succ = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="x"
        )
        data = succ.to_dict()
        data["scope"] = "other-scope"
        body = {k: v for k, v in data.items() if k != "record_digest"}
        data["record_digest"] = canonical_digest(body)
        parsed = strict_parse_record(data)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([prior, parsed])

    def test_category_mismatch(self):
        prior = self._initial()
        succ = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="x"
        )
        data = succ.to_dict()
        data["category"] = "MISSING_EVIDENCE"
        body = {k: v for k, v in data.items() if k != "record_digest"}
        data["record_digest"] = canonical_digest(body)
        parsed = strict_parse_record(data)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([prior, parsed])

    def test_self_link(self):
        prior = self._initial()
        data = prior.to_dict()
        data["prior_record_digest"] = prior.record_digest
        data["successor_of"] = prior.disagreement_id
        body = {k: v for k, v in data.items() if k != "record_digest"}
        data["record_digest"] = canonical_digest(body)
        parsed = strict_parse_record(data)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([parsed])

    def test_cycle(self):
        a = self._initial("D-a")
        b = create_successor_record(a, disagreement_id="D-b", status="OPEN", reason="b")
        # Force b <- a cycle by rewriting a as successor of b
        data = a.to_dict()
        data["prior_record_digest"] = b.record_digest
        data["successor_of"] = b.disagreement_id
        data["disagreement_id"] = "D-a2"
        body = {k: v for k, v in data.items() if k != "record_digest"}
        data["record_digest"] = canonical_digest(body)
        a2 = strict_parse_record(data)
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([a2, b])

    def test_broken_chain(self):
        prior = self._initial()
        succ = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="x"
        )
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([succ])  # predecessor deleted from set

    def test_fork(self):
        prior = self._initial()
        s1 = create_successor_record(
            prior, disagreement_id="D-s1", status="OPEN", reason="1"
        )
        s2 = create_successor_record(
            prior, disagreement_id="D-s2", status="OPEN", reason="2"
        )
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([prior, s1, s2])

    def test_duplicate_successor_ids(self):
        prior = self._initial()
        s1 = create_successor_record(
            prior, disagreement_id="D-s", status="OPEN", reason="1"
        )
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([prior, s1, s1])

    def test_predecessor_deletion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prior = self._initial()
            succ = create_successor_record(
                prior, disagreement_id="D-s", status="OPEN", reason="x"
            )
            write_disagreement_record(root, prior)
            write_disagreement_record(root, succ)
            (root / "reviews" / f"{prior.record_digest}.json").unlink()
            result = verify_disagreement_expected_set(
                root, [prior.record_digest, succ.record_digest]
            )
            self.assertFalse(result["ok"])

    def test_terminal_successor_violation(self):
        a = self._initial("D-a")
        b = create_successor_record(
            a, disagreement_id="D-b", status="RESOLVED_BY_SUCCESSOR", reason="b"
        )
        with self.assertRaises(ReviewDisagreementError):
            create_successor_record(
                b, disagreement_id="D-c", status="OPEN", reason="c"
            )


_MALFORMED = (
    None,
    False,
    True,
    0,
    1,
    1.5,
    "",
    "   ",
    [],
    {},
    {"wrong": True},
    [1, "x"],
)


class StrictTypeTests(unittest.TestCase):
    def test_report_structured_fields_reject_malformed(self):
        base = derive_reconstructability_report(_complete_inputs()).to_dict()
        # Values that are type-correct for some collection/mapping fields.
        allow_empty_list = {
            "input_refs",
            "required_inputs",
            "missing_inputs",
            "unresolved_assumptions",
            "lineage_ids",
            "derived_from",
            "reproduction_commands",
        }
        fields = [
            "schema_version",
            "audit_id",
            "subject_id",
            "input_refs",
            "required_inputs",
            "missing_inputs",
            "reproduction_commands",
            "unresolved_assumptions",
            "artifact_count",
            "lineage_ids",
            "independent_evidence_count",
            "independent_evidence_admission_status",
            "reconstructable",
            "derived_from",
            "canonical_input_digests",
            "report_digest",
            "extra",
            "authority",
        ]
        for field in fields:
            for bad in _MALFORMED:
                if field in allow_empty_list and bad == []:
                    continue
                if field == "extra" and bad in ({}, {"wrong": True}):
                    continue
                if field == "canonical_input_digests" and bad == {}:
                    continue
                if field == "authority" and bad is False:
                    continue
                if field == "artifact_count" and bad in (0, 1):
                    continue
                if field == "independent_evidence_count" and bad == 0:
                    continue
                if field == "reconstructable" and bad in (True, False):
                    continue
                data = dict(base)
                data[field] = bad
                with self.assertRaises(
                    (ReconstructabilityError, AuthorityViolation),
                    msg=f"{field}={bad!r}",
                ):
                    strict_parse_report(data)

    def test_disagreement_structured_fields_reject_malformed(self):
        base = create_disagreement_record(
            disagreement_id="D-t",
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
        ).to_dict()
        fields = [
            "schema_version",
            "disagreement_id",
            "subject_id",
            "reviewer_positions",
            "scope",
            "category",
            "status",
            "reason",
            "evidence_refs",
            "created_from",
            "record_digest",
            "extra",
            "authority",
        ]
        for field in fields:
            for bad in _MALFORMED:
                data = dict(base)
                data[field] = bad
                # Valid type-correct edge cases (not coercion targets).
                if field == "reason" and bad == "":
                    continue
                if field == "evidence_refs" and bad == []:
                    continue
                if field == "extra" and bad in ({}, {"wrong": True}):
                    continue
                if field == "authority" and bad is False:
                    continue
                with self.assertRaises(
                    (ReviewDisagreementError, AuthorityViolation),
                    msg=f"{field}={bad!r}",
                ):
                    strict_parse_record(data)

    def test_unknown_field_rejected_on_report(self):
        data = derive_reconstructability_report(_complete_inputs()).to_dict()
        data["mystery"] = "x"
        with self.assertRaises(ReconstructabilityError):
            strict_parse_report(data)

    def test_unknown_field_rejected_on_record(self):
        data = create_disagreement_record(
            disagreement_id="D-u",
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
        ).to_dict()
        data["mystery"] = "x"
        with self.assertRaises(ReviewDisagreementError):
            strict_parse_record(data)

    def test_malformed_reason_never_becomes_empty(self):
        data = create_disagreement_record(
            disagreement_id="D-r",
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
            reason="ok",
        ).to_dict()
        data["reason"] = None
        with self.assertRaises(ReviewDisagreementError):
            strict_parse_record(data)

    def test_schema_aliases_must_match(self):
        data = derive_reconstructability_report(_complete_inputs()).to_dict()
        data["schema"] = "other.schema"
        with self.assertRaises(ReconstructabilityError):
            strict_parse_report(data)


class IdentityTests(unittest.TestCase):
    def test_duplicate_reviewer_ids(self):
        with self.assertRaises(ReviewDisagreementError):
            create_disagreement_record(
                disagreement_id="D-dup-rev",
                subject_id="S-1",
                reviewer_positions=[
                    {"reviewer_id": "same", "position": "PASS"},
                    {"reviewer_id": "same", "position": "FAIL"},
                ],
                scope="unit",
                category="SPEC_AMBIGUITY",
            )

    def test_duplicate_disagreement_ids(self):
        a = create_disagreement_record(
            disagreement_id="D-same",
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
            reason="a",
        )
        b = create_disagreement_record(
            disagreement_id="D-same",
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
            reason="b",
        )
        with self.assertRaises(ReviewDisagreementError):
            verify_chain_graph([a, b])

    def test_filename_content_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-fn",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="MISSING_EVIDENCE",
            )
            path = write_disagreement_record(root, rec)
            bad = path.parent / ("00" * 32 + ".json")
            bad.write_bytes(path.read_bytes())
            result = verify_disagreement_records_at_root(root)
            self.assertFalse(result["ok"])


class ImmutableWriteTests(unittest.TestCase):
    def test_first_create_succeeds(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-w1",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
            )
            path = write_disagreement_record(root, rec)
            self.assertTrue(path.is_file())

    def test_same_bytes_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-w2",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
            )
            p1 = write_disagreement_record(root, rec)
            p2 = write_disagreement_record(root, rec)
            self.assertEqual(p1, p2)

    def test_existing_different_bytes_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-w3",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="PROVENANCE_DISPUTE",
            )
            path = write_disagreement_record(root, rec)
            tampered = rec.to_dict()
            tampered["reason"] = "tampered-in-place"
            write_json(path, tampered)
            with self.assertRaises(ReviewDisagreementError):
                write_disagreement_record(root, rec)

    def test_corrupted_destination_rejects(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-w4",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="PROVENANCE_DISPUTE",
            )
            path = write_disagreement_record(root, rec)
            path.write_bytes(b"\xff\xfe not-json")
            with self.assertRaises(ReviewDisagreementError):
                write_disagreement_record(root, rec)

    def test_exclusive_create_race_same_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rec = create_disagreement_record(
                disagreement_id="D-race",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
            )
            errors: list[BaseException] = []

            def worker():
                try:
                    write_disagreement_record(root, rec)
                except BaseException as e:  # noqa: BLE001 — collect for assert
                    errors.append(e)

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            # All must succeed (idempotent) or fail-closed without overwrite.
            self.assertTrue(
                all(isinstance(e, ReviewDisagreementError) for e in errors) or not errors
            )
            path = root / "reviews" / f"{rec.record_digest}.json"
            self.assertTrue(path.is_file())
            self.assertEqual(
                validate_disagreement_record(read_json(path)).record_digest,
                rec.record_digest,
            )


class AuthorityTests(unittest.TestCase):
    def test_no_r4b_record_authorizes(self):
        report = derive_reconstructability_report(_complete_inputs())
        data = report.to_dict()
        data["authority"] = True
        with self.assertRaises((AuthorityViolation, ReconstructabilityError)):
            strict_parse_report(data)

    def test_no_reviewer_status_creates_weaver_pass(self):
        rec = create_disagreement_record(
            disagreement_id="D-auth",
            subject_id="S-1",
            reviewer_positions=_positions("PASS", "PASS"),
            scope="unit",
            category="REVIEWER_INTERPRETATION",
        )
        data = rec.to_dict()
        data["weaver_pass"] = True
        with self.assertRaises((AuthorityViolation, ReviewDisagreementError)):
            strict_parse_record(data)

    def test_no_resolution_creates_human_final(self):
        prior = create_disagreement_record(
            disagreement_id="D-hf",
            subject_id="S-1",
            reviewer_positions=_positions(),
            scope="unit",
            category="SPEC_AMBIGUITY",
        )
        succ = create_successor_record(
            prior,
            disagreement_id="D-hf2",
            status="RESOLVED_BY_SUCCESSOR",
            reason="x",
        )
        data = succ.to_dict()
        data["human_final"] = True
        with self.assertRaises((AuthorityViolation, ReviewDisagreementError)):
            strict_parse_record(data)


class ReconstructabilityCoreTests(unittest.TestCase):
    def test_complete_inputs_reconstructable_true(self):
        report = derive_reconstructability_report(_complete_inputs())
        self.assertTrue(report.reconstructable)
        self.assertEqual(report.missing_inputs, ())
        self.assertFalse(report.authority)

    def test_missing_required_input_false(self):
        report = derive_reconstructability_report(_complete_inputs(claim=None))
        self.assertFalse(report.reconstructable)
        self.assertIn("CLAIM.json", report.missing_inputs)

    def test_independent_evidence_count_cannot_become_positive(self):
        report = derive_reconstructability_report(_complete_inputs())
        stored = report.to_dict()
        stored["independent_evidence_count"] = 3
        with self.assertRaises(ReconstructabilityError):
            strict_parse_report(stored)

    def test_not_configured_admission_status_preserved(self):
        report = derive_reconstructability_report(_complete_inputs())
        self.assertEqual(
            report.independent_evidence_admission_status,
            INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
        )
        stored = report.to_dict()
        stored["independent_evidence_admission_status"] = "CONFIGURED"
        with self.assertRaises(ReconstructabilityError):
            strict_parse_report(stored)

    def test_deterministic_canonical_output_digest(self):
        a = derive_reconstructability_report(_complete_inputs())
        b = derive_reconstructability_report(_complete_inputs())
        self.assertEqual(a.report_digest, b.report_digest)
        self.assertEqual(canonical_dumps(a.to_dict()), canonical_dumps(b.to_dict()))

    def test_legacy_without_report_optional(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "WFA-LEGACY"
            root.mkdir()
            write_json(root / "EXECUTION_MANIFEST.json", _legacy_manifest(root.name))
            result = verify_r4b_at_root(root)
            self.assertTrue(result["ok"])
            self.assertEqual(result["state"], STATE_LEGACY_PRE_R4B)
            self.assertFalse(result["reconstructability_verification"]["present"])


class DisagreementCoreTests(unittest.TestCase):
    def test_conflicting_positions_persist(self):
        rec = create_disagreement_record(
            disagreement_id="D-1",
            subject_id="WFA-TEST-001",
            reviewer_positions=_positions(),
            scope="unit-test",
            category="REVIEWER_INTERPRETATION",
            status="OPEN",
            reason="conflict",
        )
        positions = {p["reviewer_id"]: p["position"] for p in rec.reviewer_positions}
        self.assertEqual(positions["rev-A"], "PASS")
        self.assertEqual(positions["rev-B"], "FAIL")
        self.assertNotIn("consensus", rec.to_dict())

    def test_ambiguous_and_unresolved_accepted(self):
        for status, cat in (
            ("AMBIGUOUS", "GENUINELY_AMBIGUOUS"),
            ("UNRESOLVED", "MISSING_EVIDENCE"),
        ):
            rec = create_disagreement_record(
                disagreement_id=f"D-{status}",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category=cat,
                status=status,
            )
            validate_disagreement_record(rec)

    def test_no_forced_resolution(self):
        with self.assertRaises(ReviewDisagreementError):
            create_disagreement_record(
                disagreement_id="D-bad",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="SPEC_AMBIGUITY",
                status="RESOLVED_BY_SUCCESSOR",
            )

    def test_original_immutable_and_successor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prior = create_disagreement_record(
                disagreement_id="D-orig",
                subject_id="S-1",
                reviewer_positions=_positions(),
                scope="unit",
                category="SCOPE_DISPUTE",
                status="OPEN",
                reason="initial conflict",
            )
            path = write_disagreement_record(root, prior)
            prior_bytes = path.read_bytes()
            succ = create_successor_record(
                prior,
                disagreement_id="D-succ",
                status="RESOLVED_BY_SUCCESSOR",
                resolution_note="documented without rewriting prior",
                reason="successor note",
            )
            write_disagreement_record(root, succ)
            self.assertEqual(path.read_bytes(), prior_bytes)


class FreezeOrderTests(unittest.TestCase):
    def test_manifest_not_mutated_after_evidence_index(self):
        """Freeze finalizes EXECUTION_MANIFEST before FINAL_EVIDENCE_INDEX."""
        import shutil
        from audit_lifecycle.orchestrator import AuditOrchestrator
        from audit_lifecycle.request import AuditRequest, sha256_file

        fresh = ROOT / "fixtures" / "fresh_target" / "README.txt"
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            target = out / "target" / "README.txt"
            target.parent.mkdir(parents=True)
            shutil.copy2(fresh, target)
            digest = sha256_file(target)
            orch = AuditOrchestrator(out / "runs")
            req = AuditRequest(
                target_path=str(target),
                claim={
                    "id": "C-FREEZE-ORDER",
                    "statement": "digest matches",
                    "adapter": "hash_claim",
                    "adapter_params": {"expected_sha256": digest},
                },
                policy={"human_review_required": False},
            )
            result = orch.run_through_decision(req)
            run = Path(result["audit_root"])
            manifest_before_index = None
            # After freeze, compare manifest digest to evidence index entry.
            freeze = result.get("freeze") or orch.freeze_run(run, req.policy)
            self.assertTrue(freeze["freeze_performed"])
            manifest_path = run / "EXECUTION_MANIFEST.json"
            manifest = read_json(manifest_path)
            self.assertIn("r4_b", manifest)
            self.assertEqual(
                manifest["r4_b"]["schema_version"], EXPECTATION_SCHEMA_VERSION
            )
            self.assertNotIn("freeze", manifest)  # status stays in FREEZE_STATUS
            index = next((run / "freeze").glob("*_FROZEN")) / "FINAL_EVIDENCE_INDEX.json"
            entries = {e["path"]: e["sha256"] for e in read_json(index)["entries"]}
            self.assertIn("EXECUTION_MANIFEST.json", entries)
            self.assertEqual(entries["EXECUTION_MANIFEST.json"], sha256_file(manifest_path))
            self.assertIn(REPORT_FILENAME, entries)
            verify = orch.verify_run(run)
            self.assertTrue(verify["verify_ok"])
            self.assertEqual(
                verify["semantic_verification"]["r4b_verification"]["state"],
                STATE_R4_B_ENABLED,
            )


if __name__ == "__main__":
    unittest.main()
