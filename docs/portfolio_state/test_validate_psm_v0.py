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
        value["earned"][0]["source_assertions"][0]["source_record_id"] = "seic-001-verification"
        self.assert_invalid(value)

    def test_missing_source_record_is_rejected(self):
        value = record()
        value["earned"][0]["source_assertions"][0]["source_record_id"] = "missing"
        self.assert_invalid(value)

    def test_earned_assertion_must_exist_verbatim_in_source(self):
        value = record()
        value["earned"][0]["source_assertions"][0]["exact_text"] = "Production authorization granted"
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
        value["source_records"][1]["record_kind"] = "human_final"
        value["earned"][0]["source_assertions"][0]["source_record_id"] = "seic-001-verification"
        self.assert_invalid(value)

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
