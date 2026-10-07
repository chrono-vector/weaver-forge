from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from docs.portfolio_state import validate_psm_v0 as psm


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = ROOT / "docs" / "portfolio_state" / "portfolio_state_v0.example.json"


def record():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class PSMValidationTests(unittest.TestCase):
    def assert_invalid(self, value):
        self.assertEqual(psm.INVALID, psm.validation_status(value, ROOT))

    def test_representative_record_is_valid(self):
        self.assertEqual((), psm.validate_record(record(), ROOT))
        self.assertEqual(psm.VALID, psm.validation_status(record(), ROOT))

    def test_unknown_cannot_become_pass(self):
        value = record()
        value["assumptions"][0]["status"] = "PASS"
        self.assert_invalid(value)

    def test_metadata_cannot_create_authority(self):
        value = record()
        value["authority"] = "GRANTED"
        self.assert_invalid(value)

    def test_human_final_cannot_be_inferred(self):
        value = record()
        value["earned"][0]["human_final"] = True
        self.assert_invalid(value)

    def test_production_permission_cannot_be_inferred(self):
        value = record()
        value["earned"][0]["production_permission"] = "GRANTED"
        self.assert_invalid(value)

    def test_earned_requires_resolved_human_final_linkage(self):
        value = record()
        value["source_records"][0]["record_kind"] = "verification"
        self.assert_invalid(value)

    def test_missing_source_record_is_rejected(self):
        value = record()
        value["source_records"].pop(0)
        self.assert_invalid(value)

    def test_earned_claim_ref_must_match_specific_claim(self):
        value = record()
        value["earned"][0]["source_claim_refs"] = ["ecp-001:closed-bounded-v0"]
        self.assert_invalid(value)

    def test_bound_claim_description_cannot_assert_stronger_state(self):
        value = record()
        value["earned"][2]["description"] = "ECP-001 grants production authorization."
        self.assert_invalid(value)

    def test_missing_git_path_is_rejected(self):
        value = record()
        value["source_records"][0]["path"] = "docs/missing.md"
        self.assert_invalid(value)

    def test_promotion_style_metadata_is_rejected(self):
        value = record()
        value["earned"][0]["promote_to"] = "production-authorization"
        self.assert_invalid(value)

    def test_fail_remediation_pass_history_must_remain_visible(self):
        value = record()
        value["counterexamples"][0]["outcome_history"] = ["PASS"]
        self.assert_invalid(value)

    def test_contradictory_earned_and_not_yet_earned_is_rejected(self):
        value = record()
        value["not_yet_earned"][0]["claim_id"] = value["earned"][0]["claim_id"]
        self.assert_invalid(value)

    def test_replayability_does_not_imply_independent_reproduction(self):
        value = record()
        value["replayability"]["status"] = "REPLAYABLE"
        value["replayability"]["independent_reproduction"] = "ESTABLISHED"
        self.assert_invalid(value)

    def test_debt_deletion_leaves_detectable_unresolved_reference(self):
        value = record()
        value["validation_debt"] = value["validation_debt"][1:]
        self.assert_invalid(value)

    def test_psm_cannot_override_epistemic_ceiling(self):
        value = record()
        value["epistemic_ceiling"]["override"] = "UNBOUNDED"
        self.assert_invalid(value)

    def test_self_declared_human_final_source_is_rejected(self):
        value = record()
        value["source_records"][0]["record_kind"] = "verification"
        value["source_records"][1]["record_kind"] = "human_final"
        self.assert_invalid(value)

    def test_r1_unrelated_accepted_source_cannot_support_stronger_claim(self):
        value = record()
        value["earned"].append({
            "claim_id": "independent-reproduction",
            "description": "Unsupported stronger claim.",
            "status": "EARNED",
            "source_claim_refs": ["wacp-001:closed-bounded-v0"],
        })
        self.assert_invalid(value)

    def test_r2_ecp_closure_cannot_support_production_authority(self):
        value = record()
        value["earned"].append({
            "claim_id": "production-authorization",
            "description": "Unsupported production authority.",
            "status": "EARNED",
            "source_claim_refs": ["ecp-001:closed-bounded-v0"],
        })
        self.assert_invalid(value)

    def test_r3_blocker_removal_does_not_support_stronger_claim(self):
        value = record()
        value["not_yet_earned"] = [
            item for item in value["not_yet_earned"]
            if item["claim_id"] != "production-authorization"
        ]
        value["validation_debt"] = [
            item for item in value["validation_debt"]
            if item["debt_id"] != "debt-production-authorization"
        ]
        value["earned"].append({
            "claim_id": "production-authorization",
            "description": "Unsupported production authority.",
            "status": "EARNED",
            "source_claim_refs": ["ecp-001:closed-bounded-v0"],
        })
        self.assert_invalid(value)

    def test_r4_deleting_all_blockers_does_not_create_evidence(self):
        value = record()
        value["not_yet_earned"] = []
        value["validation_debt"] = []
        value["earned"].append({
            "claim_id": "production-authorization",
            "description": "Unsupported production authority.",
            "status": "EARNED",
            "source_claim_refs": ["ecp-001:closed-bounded-v0"],
        })
        self.assert_invalid(value)

    def test_r5_correctly_bound_earned_claim_is_accepted(self):
        self.assertEqual(psm.VALID, psm.validation_status(record(), ROOT))

    def test_r6_required_counterexample_cannot_be_deleted(self):
        value = record()
        value["counterexamples"] = []
        self.assert_invalid(value)

    def test_r7_negative_evidence_and_remediation_links_cannot_be_erased(self):
        value = record()
        value["counterexamples"][0]["source_record_ids"] = ["seic-001-human-final"]
        value["counterexamples"][0]["outcome_history"] = ["PASS"]
        self.assert_invalid(value)

    def test_r8_complete_failure_remediation_pass_chain_is_accepted(self):
        self.assertEqual(psm.VALID, psm.validation_status(record(), ROOT))

    def test_unresolved_revision_commit_is_rejected(self):
        value = record()
        value["revision_provenance"][0]["git_commit"] = "0" * 40
        self.assert_invalid(value)

    def test_canonical_serialization_is_deterministic(self):
        value = record()
        self.assertEqual(psm.canonical_bytes(value), psm.canonical_bytes(copy.deepcopy(value)))
        self.assertTrue(psm.canonical_bytes(value).endswith(b"\n"))

    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"schema_version":"a","schema_version":"b"}', encoding="utf-8")
            with self.assertRaises(psm.DuplicateKeyError):
                psm.load_record(path)


if __name__ == "__main__":
    unittest.main()
