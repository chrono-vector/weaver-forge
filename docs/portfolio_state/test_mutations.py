from __future__ import annotations

import copy
import unittest

from docs.portfolio_state import validate_psm_v0 as psm
from docs.portfolio_state.test_validate_psm_v0 import ROOT, record


class PSMMutationTests(unittest.TestCase):
    def assert_killed(self, mutation):
        value = record()
        mutation(value)
        self.assertEqual(psm.INVALID, psm.validation_status(value, ROOT))

    def test_m1_not_yet_to_earned_without_accepted_source_is_killed(self):
        def mutation(value):
            item = value["not_yet_earned"].pop(0)
            value["validation_debt"].pop(0)
            value["earned"].append(
                {
                    "claim_id": item["claim_id"],
                    "description": item["description"],
                    "status": "EARNED",
                    "source_assertions": [],
                }
            )
        self.assert_killed(mutation)

    def test_m2_remove_blocking_debt_is_killed(self):
        self.assert_killed(lambda value: value["validation_debt"].pop(0))

    def test_m3_convert_limitation_into_authority_is_killed(self):
        def mutation(value):
            value["nonclaims"].remove("does_not_create_authority")
            value["nonclaims"].append("creates_authority")
        self.assert_killed(mutation)

    def test_m4_erase_counterexample_history_is_killed(self):
        self.assert_killed(lambda value: value["counterexamples"][0].update(outcome_history=[]))

    def test_m5_unknown_to_pass_is_killed(self):
        self.assert_killed(lambda value: value["assumptions"][0].update(status="PASS"))

    def test_m6_infer_human_final_is_killed(self):
        self.assert_killed(lambda value: value.update(human_final="INFERRED"))

    def test_m7_infer_production_permission_from_earned_is_killed(self):
        self.assert_killed(lambda value: value["earned"][0].update(production_permission="GRANTED"))

    def test_m8_infer_independent_reproduction_from_replayability_is_killed(self):
        self.assert_killed(
            lambda value: value["replayability"].update(
                status="REPLAYABLE", independent_reproduction="ESTABLISHED"
            )
        )

    def test_m9_replace_source_with_unresolved_path_is_killed(self):
        self.assert_killed(lambda value: value["source_records"][0].update(path="docs/missing.md"))


if __name__ == "__main__":
    unittest.main()
