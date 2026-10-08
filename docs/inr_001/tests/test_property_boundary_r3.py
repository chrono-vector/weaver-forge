"""INR-001 r3 property boundary tests (Codex material issue B).

The INR target property must equal what the pinned PSM validator executes:
P_verified = P_executed. The pinned validator refuses Human Final inference through
its _HUMAN_ACCEPTANCE source rule and checks production only through its
required-nonclaims rule; it has no rule rejecting a positive production-permission
assertion, so INR must not claim one.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inr_r3_support as s  # noqa: E402
from docs.inr_001 import input_cases  # noqa: E402
from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402

EXPECTED_CASES = [
    "PSM_POSITIVE_ACCEPTED_RECORD", "PSM_NEG_UNSUPPORTED_STRONGER_EARNED", "PSM_NEG_SOURCE_BINDING_MISMATCH",
    "PSM_NEG_BLOCKER_DEBT_REMOVAL", "PSM_NEG_COUNTEREXAMPLE_DELETION", "PSM_NEG_HISTORY_COLLAPSE",
    "PSM_NEG_UNKNOWN_CLAIM_CLASS", "PSM_NEG_INDEPENDENT_REPRODUCTION_INFERENCE", "PSM_NEG_HUMAN_FINAL_INFERENCE",
    "PSM_REQUIRED_PRODUCTION_NONCLAIM", "PSM_NEG_MUTATED_ARCHIVE_OR_INPUT"]
HF_ERROR = "source_records[1] does not resolve to an accepted Human Final record"
PN_ERROR = "required nonclaims are missing: does_not_grant_production_permission"
NONCLAIM_TOKEN = "does_not_grant_production_permission"
# Case identifiers that would claim an unsupported property.
FORBIDDEN_IDS = ("PSM_NEG_PRODUCTION_PERMISSION_GRANTED", "PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE")
R3_DOCS = ("INR_001_PROFILE_REFREEZE_R3.md", "INR_001_IMPLEMENTATION_MATRIX_R3.md")
BOUNDARY_MARKER = "POSITIVE_PRODUCTION_PERMISSION_GRANT_REFUSAL: NOT_CLAIMED"


def _claim_text(spec):
    return " ".join((spec["case_id"], spec["required_property"], spec["intended_refusal"]))


class ProfilePropertyBoundaryTests(unittest.TestCase):
    def test_profile_case_set_is_exactly_the_executed_property_set(self):
        profile = s.profile()
        self.assertEqual([c["case_id"] for c in profile["required_cases"]], EXPECTED_CASES)
        self.assertEqual([c["case_id"] for c in profile["command_inventory"]], EXPECTED_CASES)
        self.assertTrue(all(c["mandatory_execution"] is True for c in profile["required_cases"]))
        self.assertEqual([c["sequence"] for c in profile["command_inventory"]], list(range(1, len(EXPECTED_CASES) + 1)))

    def test_human_final_property_is_precise(self):
        spec = s.spec(s.HF)
        self.assertEqual(spec["expected_errors"], [HF_ERROR])
        self.assertEqual(spec["expected_classification"], "FAIL")
        self.assertIn("_HUMAN_ACCEPTANCE", spec["intended_refusal"])
        self.assertNotIn("production", _claim_text(spec).lower())
        self.assertNotIn("nonclaim", _claim_text(spec).lower())

    def test_production_nonclaim_property_is_precise(self):
        spec = s.spec(s.PN)
        self.assertEqual(spec["expected_errors"], [PN_ERROR])
        self.assertIn("_REQUIRED_NONCLAIMS", spec["intended_refusal"])
        self.assertNotIn("human final", _claim_text(spec).lower().replace("_", " "))

    def test_unsupported_production_grant_claim_absent_from_profile_and_docs(self):
        profile = s.profile()
        for spec in profile["required_cases"]:
            # The only allowed production wording is the required-nonclaim token itself.
            text = _claim_text(spec).lower().replace("_", " ")
            text = text.replace("does not grant production permission", "").replace(
                "psm required production nonclaim", "")
            self.assertNotRegex(text, r"\bproduction\b", spec["case_id"])
            self.assertNotRegex(text, r"\bgrant", spec["case_id"])
            self.assertNotIn(spec["case_id"], FORBIDDEN_IDS)
        self.assertNotIn("production", profile["profile_purpose"].lower())
        self.assertIn("profile does not claim that the pinned validator rejects a positive "
                      "production-permission assertion", profile["nonclaims"])
        raw_profile = (sup.ROOT / "profiles/psm_001_inr_target_profile_v0.json").read_text(encoding="utf-8")
        source = (sup.ROOT / "input_cases.py").read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_IDS:
            self.assertNotIn(forbidden, raw_profile)
            self.assertNotIn(forbidden, source)
        for name in R3_DOCS:
            doc = (sup.ROOT / name).read_text(encoding="utf-8")
            self.assertIn(BOUNDARY_MARKER, doc, name)
            self.assertNotIn("PSM_NEG_PRODUCTION_PERMISSION_GRANTED", doc, name)

    def test_human_final_input_mutates_only_the_record_kind(self):
        accepted = json.loads(s.pinned_bytes("docs/portfolio_state/portfolio_state_v0.example.json")) \
            if s.LIVE else None
        if accepted is None:
            self.skipTest("pinned Git / target repository unavailable")
        raw = json.dumps(accepted).encode()
        value = input_cases.case_value(s.HF, raw)
        self.assertEqual(accepted["source_records"][1]["record_kind"], "verification")
        self.assertEqual(value["source_records"][1]["record_kind"], "human_final")
        value["source_records"][1]["record_kind"] = "verification"
        self.assertEqual(value, accepted)  # nonclaims and everything else untouched

    def test_production_nonclaim_input_drops_exactly_one_nonclaim(self):
        if not s.LIVE:
            self.skipTest("pinned Git / target repository unavailable")
        accepted = json.loads(s.pinned_bytes("docs/portfolio_state/portfolio_state_v0.example.json"))
        value = input_cases.case_value(s.PN, json.dumps(accepted).encode())
        self.assertEqual(set(accepted["nonclaims"]) - set(value["nonclaims"]), {NONCLAIM_TOKEN})
        self.assertEqual(len(value["nonclaims"]), len(accepted["nonclaims"]) - 1)
        value["nonclaims"] = accepted["nonclaims"]
        self.assertEqual(value, accepted)


@unittest.skipUnless(s.LIVE, "pinned Git / target repository unavailable")
class PinnedSourceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = s.pinned_bytes("docs/portfolio_state/validate_psm_v0.py")
        cls.source = cls.source_bytes.decode("utf-8")
        cls.lines = cls.source.split("\n")

    def test_source_is_the_pinned_target(self):
        self.assertEqual(sup.digest(self.source_bytes), s.profile()["target_file_digests"]["validate_psm_v0.py"])

    def test_pinned_source_has_no_positive_production_grant_rule(self):
        # "production" as a word or token part (not inside "reproduction")
        mentions = [(n, line.strip()) for n, line in enumerate(self.lines, 1)
                    if re.search(r"(?<![a-z])production", line.lower())]
        self.assertEqual(mentions, [(6, "Final, witness status, or production permission."),
                                    (72, '"does_not_grant_production_permission",')])

    def test_pinned_rules_behind_the_narrowed_cases(self):
        self.assertIn('    if kind == "human_final" and _HUMAN_ACCEPTANCE.search(', self.lines)
        self.assertIn('        errors.append(f"{field} does not resolve to an accepted Human Final record")', self.lines)
        self.assertIn('    missing_nonclaims = _REQUIRED_NONCLAIMS - set(nonclaims)', self.lines)
        self.assertIn('''        errors.append(f"required nonclaims are missing: {', '.join(sorted(missing_nonclaims))}")''',
                      self.lines)
        self.assertTrue(re.search(r"_HUMAN_ACCEPTANCE = re\.compile\(\n\s+r\"Decision:", self.source))

    def test_every_case_executes_exactly_its_frozen_refusal(self):
        """P_verified = P_executed: each claimed property is what the pinned validator does."""
        accepted = s.pinned_bytes("docs/portfolio_state/portfolio_state_v0.example.json")
        for spec in s.profile()["required_cases"]:
            rc, errors = s.run_pinned_probe(input_cases.case_bytes(spec["case_id"], accepted))
            self.assertEqual(errors, spec["expected_errors"], spec["case_id"])
            self.assertIn(rc, spec["accepted_return_codes"], spec["case_id"])

    def test_pinned_validator_accepts_a_positive_production_statement(self):
        """Boundary evidence: a positive production-permission statement is NOT refused."""
        value = json.loads(s.pinned_bytes("docs/portfolio_state/portfolio_state_v0.example.json"))
        value["limitations"] = value["limitations"] + ["production permission granted"]
        rc, errors = s.run_pinned_probe(json.dumps(value).encode())
        self.assertEqual((rc, errors), (0, []))


if __name__ == "__main__":
    unittest.main()
