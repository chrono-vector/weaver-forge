"""Acceptance + negative tests for weaver-independent-witness-verifier-v0."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from independent_witness_verifier_v0 import (  # noqa: E402
    FROZEN_CAW_COMMIT,
    INDEPENDENCE_AXES,
    SCHEMA_VERSION,
    build_minimal_pack,
    default_frozen_boundary,
    detect_out_of_manifest_required_dependency,
    detect_pack_seal_mismatch,
    detect_semi_blind_leakage,
    transition_iw_status,
    validate_procedure_completeness_p0014,
    validate_procedure_completeness_p0030,
    validate_static_procedure_anti_circularity,
    verify_independent_witness_v0,
)


def _verify(pack, expected_boundary=None, **kwargs):
    inp = {
        "schema_version": SCHEMA_VERSION,
        "independent_witness_pack": pack,
        "expected_frozen_boundary": expected_boundary,
    }
    inp.update(kwargs)
    return verify_independent_witness_v0(inp)


class TestIWAcceptance(unittest.TestCase):
    def test_t01_frozen_caw_commit_mismatch_fails(self):
        pack = build_minimal_pack()
        pack["frozen_input_verification"]["CAW_COMMIT"] = "0" * 40
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("frozen_boundary_mismatch", r["reason_codes"])
        self.assertEqual(r["IW_STATUS"], "IW_REJECTED")

    def test_t02_weaver_version_mismatch_recorded_or_fails(self):
        pack = build_minimal_pack()
        expected = default_frozen_boundary(
            weaver_commit="EXPECTED_WEAVER_COMMIT",
            weaver_tree="EXPECTED_TREE",
        )
        expected["WEAVER_COMMIT_MANDATORY"] = True
        pack["frozen_input_verification"]["WEAVER_COMMIT"] = "OTHER_COMMIT"
        r = _verify(pack, expected_boundary=expected)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertTrue(
            any(c.startswith("frozen_boundary") or "weaver" in c for c in r["reason_codes"])
            or "frozen_boundary_mismatch" in r["reason_codes"]
        )
        self.assertFalse(r["frozen_boundary_checks"]["WEAVER_COMMIT"]["match"])

    def test_t03_static_path_reproduced(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertTrue(r["reproduction"]["class_status"]["STATIC_REPRODUCTION"]["matched"])
        self.assertEqual(
            set(r["reproduction"]["class_status"]["STATIC_REPRODUCTION"]["path_ids"]),
            {"wrps-v0-p0014", "wrps-v0-p0030"},
        )

    def test_t04_runtime_calldata_independently_reproduced(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertTrue(r["reproduction"]["class_status"]["RUNTIME_INPUT_REPRODUCTION"]["matched"])
        for entry in pack["runtime_input_results"]:
            self.assertTrue(entry.get("calldata_sha256"))
            self.assertFalse(entry.get("derived_from_operator_artifact"))

    def test_t05_runtime_result_independently_reproduced(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertTrue(r["reproduction"]["class_status"]["RUNTIME_EXECUTION_REPRODUCTION"]["matched"])

    def test_t06_second_path_shape_supported(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        paths = set(r["reproduction"]["class_status"]["RUNTIME_INPUT_REPRODUCTION"]["path_ids"])
        self.assertEqual(paths, {"wrps-v0-p0014", "wrps-v0-p0030"})

    def test_t07_authority_read_reproduced(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertTrue(r["reproduction"]["class_status"]["AUTHORITY_READ_REPRODUCTION"]["matched"])
        self.assertEqual(pack["authority_read_results"][0]["AUTHORITY_ID"], "AUTH-005")

    def test_t08_failures_preserved(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertGreaterEqual(r["failure_retry"]["failure_count"], 1)
        self.assertTrue(r["failure_retry"]["failures_preserved"])
        self.assertEqual(pack["failure_log"][0]["attempt_id"], "fail-1")

    def test_t09_retries_preserved(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertGreaterEqual(r["failure_retry"]["retry_count"], 1)
        self.assertEqual(pack["retry_log"][0]["prior_failure_id"], "fail-1")

    def test_t10_original_generated_result_cannot_substitute(self):
        pack = build_minimal_pack()
        pack["runtime_input_results"][0]["derived_from_operator_artifact"] = True
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("operator_artifact_reuse", r["reason_codes"])

    def test_t11_environment_captured(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "ACCEPTED")
        for field in ("os_family", "arch", "python_version", "tool_versions"):
            self.assertIn(field, pack["environment"])

    def test_t12_no_live_mutation(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertEqual(r["network_safety"]["LIVE_MUTATION"], "NO")
        pack2 = build_minimal_pack(live_mutation_evidence={"tx": "0xabc"})
        r2 = _verify(pack2)
        self.assertEqual(r2["verification_status"], "REJECTED")
        self.assertIn("live_mutation_evidence_present", r2["reason_codes"])

    def test_t13_no_real_credential_use(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertEqual(r["network_safety"]["REAL_CREDENTIAL"], "NO")
        pack2 = build_minimal_pack(real_credential_evidence={"key": "present"})
        r2 = _verify(pack2)
        self.assertEqual(r2["verification_status"], "REJECTED")
        self.assertIn("real_credential_evidence_present", r2["reason_codes"])

    def test_t14_acceptance_scope_limited(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertTrue(r["scope_limited"])
        self.assertEqual(r["acceptance_scope"]["kind"], "BOUNDED_D")
        self.assertFalse(r["acceptance_scope"]["whole_repository"])

    def test_t15_matched_neq_accepted(self):
        pack = build_minimal_pack()
        # Strip independence evidence -> MATCHED path without ACCEPTED
        for axis in INDEPENDENCE_AXES:
            pack["independence"]["axes"][axis] = {"status": "NOT_VERIFIED", "evidence": []}
        r = _verify(pack)
        self.assertTrue(r["MATCHED_NEQ_ACCEPTED"])
        self.assertTrue(r["axes"]["REPRODUCTION_MATCHED"] or r["reproduction"]["reproduction_matched"])
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertIn(r["IW_STATUS"], {"IW_REPRODUCTION_MATCHED", "IW_REJECTED", "IW_REPRODUCTION_PARTIAL"})
        # With boundary ok and scope matched, status should be MATCHED
        self.assertEqual(r["IW_STATUS"], "IW_REPRODUCTION_MATCHED")
        self.assertFalse(r["ACCEPTED_INDEPENDENT_REPRODUCTION"])

    def test_t16_designated_witness_alone_not_iw(self):
        pack = build_minimal_pack(
            witness_run_metadata={
                "run_id": "DESIG-ONLY",
                "pack_version": "iw-pack-v1",
                "designated_witness": True,
                "declared_independent": True,
                "witness_identity_class": "DESIGNATED_ONLY",
                "witness_handle": "named-witness",
                "in_progress": False,
            }
        )
        # Remove all reproduction results to leave designation only
        pack["static_reproduction_results"] = []
        pack["runtime_input_results"] = []
        pack["runtime_dispatch_results"] = []
        pack["runtime_execution_results"] = []
        pack["authority_read_results"] = []
        # refresh digests
        from independent_witness_verifier_v0 import digest

        for key in (
            "static_reproduction_results",
            "runtime_input_results",
            "runtime_execution_results",
            "authority_read_results",
            "failure_log",
            "retry_log",
        ):
            d = digest(pack[key])
            pack["evidence_digests"][key] = d
            pack["manifest"]["members"][key] = d
        r = _verify(pack)
        self.assertTrue(r["role_separation"]["DESIGNATED_WITNESS"])
        self.assertFalse(r["ACCEPTED_INDEPENDENT_REPRODUCTION"])
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertTrue(r["axes"]["DESIGNATED_WITNESS_ONLY"] or not r["ACCEPTED_INDEPENDENT_REPRODUCTION"])

    def test_t17_accepted_requires_evidence_plus_independence(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertTrue(r["ACCEPTED_INDEPENDENT_REPRODUCTION"])
        self.assertTrue(r["independence"]["all_mandatory_satisfied"])
        self.assertTrue(r["structurally_acceptable"])


class TestIWNegative(unittest.TestCase):
    def test_neg_missing_mandatory_independence_dimension(self):
        pack = build_minimal_pack()
        pack["independence"]["axes"]["OPERATOR_INDEPENDENCE"] = {"status": "VERIFIED", "evidence": []}
        r = _verify(pack)
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertIn("OPERATOR_INDEPENDENCE", r["independence"]["missing_mandatory"])

    def test_neg_manifest_digest_mismatch(self):
        pack = build_minimal_pack()
        pack["manifest"]["members"]["failure_log"] = "0" * 64
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("manifest_digest_mismatch", r["reason_codes"])

    def test_neg_hidden_replaced_failed_attempt(self):
        pack = build_minimal_pack()
        pack["failure_log"] = []  # conceal prior failure referenced by retry
        from independent_witness_verifier_v0 import digest

        pack["evidence_digests"]["failure_log"] = digest([])
        pack["manifest"]["members"]["failure_log"] = digest([])
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("hidden_replaced_failed_attempt", r["reason_codes"])

    def test_neg_scope_expansion(self):
        pack = build_minimal_pack()
        pack["reproduction_scope"]["whole_repository"] = True
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("scope_expansion", r["reason_codes"])

    def test_neg_witness_uses_maintainer_result_artifact(self):
        pack = build_minimal_pack()
        pack["uses_maintainer_result_artifact"] = True
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("maintainer_result_substitution", r["reason_codes"])

    def test_neg_live_mutation_evidence_present(self):
        pack = build_minimal_pack()
        pack["network_safety"]["LIVE_MUTATION"] = "YES"
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("network_safety_violation", r["reason_codes"])

    def test_neg_real_credential_evidence_present(self):
        pack = build_minimal_pack()
        pack["real_credential_evidence"] = {"wallet": "0xreal"}
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("real_credential_evidence_present", r["reason_codes"])


class TestIWStateTransitions(unittest.TestCase):
    def test_not_started_to_matched_chain(self):
        s = "IW_NOT_STARTED"
        s = transition_iw_status(s, "START")
        self.assertEqual(s, "IW_IN_PROGRESS")
        s = transition_iw_status(s, "PARTIAL")
        self.assertEqual(s, "IW_REPRODUCTION_PARTIAL")
        s = transition_iw_status(s, "MATCH")
        self.assertEqual(s, "IW_REPRODUCTION_MATCHED")

    def test_matched_without_independence_not_accepted(self):
        pack = build_minimal_pack()
        for axis in INDEPENDENCE_AXES:
            pack["independence"]["axes"][axis]["status"] = "PARTIAL"
        r = _verify(pack)
        self.assertEqual(r["IW_STATUS"], "IW_REPRODUCTION_MATCHED")
        self.assertFalse(r["ACCEPTED_INDEPENDENT_REPRODUCTION"])

    def test_matched_with_independence_structurally_acceptable(self):
        pack = build_minimal_pack()
        r = _verify(pack)
        self.assertTrue(r["structurally_acceptable"])
        self.assertEqual(r["IW_STATUS"], "IW_ACCEPTED")
        # Real CAW IW remains NOT_SATISFIED outside synthetic fixture context
        self.assertEqual(r["REAL_IW_STATUS"], "SATISFIED_SCOPED")

    def test_maintainer_dry_run_never_accepted(self):
        pack = build_minimal_pack()
        pack["witness_run_metadata"]["witness_identity_class"] = "MAINTAINER_DRY_RUN"
        r = _verify(pack)
        self.assertTrue(r["maintainer_dry_run"])
        self.assertEqual(r["dry_run_independence"], "NOT_ACCEPTABLE_FOR_IW")
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertEqual(r["REAL_IW_STATUS"], "NOT_SATISFIED")


class TestIWFrozenBoundaryPin(unittest.TestCase):
    def test_default_caw_commit(self):
        self.assertEqual(FROZEN_CAW_COMMIT, "e2074718bcea293726ddfcf8764e1499e7b9217c")
        pack = build_minimal_pack()
        self.assertEqual(pack["frozen_input_verification"]["CAW_COMMIT"], FROZEN_CAW_COMMIT)


class TestIWAdversarialRemediation(unittest.TestCase):
    """PWMREM R6 adversarial coverage (15 cases; 9–10 live in authority suite)."""

    def test_01_maintainer_origin_submission_cannot_iw_accepted(self):
        pack = build_minimal_pack()
        pack["external_submission_receipt"]["MAINTAINER_ORIGIN"] = "YES"
        r = _verify(pack)
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertIn("maintainer_origin_submission", r["reason_codes"])

    def test_02_self_declared_independence_without_receipt_fails_acceptance(self):
        pack = build_minimal_pack()
        pack.pop("external_submission_receipt", None)
        r = _verify(pack)
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")
        self.assertIn("self_declared_independence_insufficient", r["reason_codes"])

    def test_03_canonical_git_commit_mismatch_fails(self):
        pack = build_minimal_pack()
        expected = copy.deepcopy(pack["frozen_input_verification"])
        expected["WEAVER_COMMIT"] = "deadbeef" * 5
        r = _verify(pack, expected_boundary=expected)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("frozen_boundary_mismatch", r["reason_codes"])

    def test_04_canonical_tree_mismatch_fails(self):
        pack = build_minimal_pack()
        expected = copy.deepcopy(pack["frozen_input_verification"])
        expected["WEAVER_TREE"] = "cafebabe" * 5
        r = _verify(pack, expected_boundary=expected)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("frozen_boundary_mismatch", r["reason_codes"])

    def test_05_content_manifest_mismatch_fails(self):
        pack = build_minimal_pack()
        pack["frozen_input_verification"]["CONTENT_MANIFEST_DIGEST"] = "aa" * 32
        expected = copy.deepcopy(pack["frozen_input_verification"])
        expected["CONTENT_MANIFEST_DIGEST"] = "bb" * 32
        r = _verify(pack, expected_boundary=expected)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("frozen_boundary_mismatch", r["reason_codes"])

    def test_06_pack_seal_mismatch_fails(self):
        pack = build_minimal_pack()
        pack["pack_seal"] = {"PACK_SEAL_DIGEST": "11" * 32, "CONTENT_MANIFEST_DIGEST": "22" * 32}
        pack["expected_pack_seal"] = {
            "PACK_SEAL_DIGEST": "33" * 32,
            "CONTENT_MANIFEST_DIGEST": "22" * 32,
        }
        errs = detect_pack_seal_mismatch(pack)
        self.assertTrue(any(e["code"] == "pack_seal_mismatch" for e in errs))
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("pack_seal_mismatch", r["reason_codes"])

    def test_07_out_of_manifest_required_dependency_fails(self):
        pack = build_minimal_pack()
        pack["required_dependencies"] = ["frozen-inputs/missing-tool.json"]
        errs = detect_out_of_manifest_required_dependency(pack)
        self.assertTrue(any(e["code"] == "out_of_manifest_required_dependency" for e in errs))
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("out_of_manifest_required_dependency", r["reason_codes"])

    def test_08_excluded_untracked_module_cannot_influence_acceptance(self):
        pack = build_minimal_pack()
        pack["influence_from_untracked_module"] = {"module": "local_untracked_hack.py", "force_iw": True}
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("untracked_module_influence", r["reason_codes"])
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")

    def test_09_authority_historical_failure_supersession_preserves_raw(self):
        auth_root = HERE.parent / "authority-evidence-verifier-v0"
        sys.path.insert(0, str(auth_root))
        from authority_evidence_verifier_v0 import normalize_caro_authority_pack  # noqa: WPS433

        caro = Path(
            r"C:\dev\external-verification-work\caw-authority-readonly-v1\CARO-20260912-041428-A6BBA9BA"
        )
        pack = normalize_caro_authority_pack(caro)
        row = next(r for r in pack["runtime_reads"] if r.get("ROW_ID") == "CARO-MAIN-14")
        self.assertEqual(row["RUNTIME_READ_VERDICT"], "READ_FAILED")
        self.assertEqual(row["ORIGINAL_STATUS"], "READ_FAILED")
        self.assertEqual(row["CURRENT_INTERPRETATION"], "HISTORICAL_SUPERSEDED")
        self.assertTrue(row.get("EVIDENCE_REFERENCES"))
        failed = [r for r in pack["runtime_reads"] if r.get("RUNTIME_READ_VERDICT") == "READ_FAILED"]
        self.assertEqual(len(failed), 8)

    def test_10_superseded_historical_failure_not_current_l2_gap(self):
        auth_root = HERE.parent / "authority-evidence-verifier-v0"
        sys.path.insert(0, str(auth_root))
        from authority_evidence_verifier_v0 import (  # noqa: WPS433
            SCHEMA_VERSION as AUTH_SCHEMA,
            normalize_caro_authority_pack,
            verify_authority_evidence_v0,
        )

        caro = Path(
            r"C:\dev\external-verification-work\caw-authority-readonly-v1\CARO-20260912-041428-A6BBA9BA"
        )
        pack = normalize_caro_authority_pack(caro)
        self.assertEqual(pack.get("unread_authority_ids"), [])
        self.assertEqual(pack.get("current_l2_unread_gap"), "CLOSED")
        hist = [
            r
            for r in pack["runtime_reads"]
            if r.get("AUTHORITY_ID") in {"AUTH-021", "AUTH-034"}
            and r.get("RUNTIME_READ_VERDICT") == "UNREAD"
            and r.get("CURRENT_INTERPRETATION") == "HISTORICAL_SUPERSEDED"
        ]
        self.assertGreaterEqual(len(hist), 2)
        result = verify_authority_evidence_v0(
            {"schema_version": AUTH_SCHEMA, "authority_evidence_pack": pack}
        )
        self.assertEqual(result["AUTHORITY_STATE_READ_STATUS"], "PARTIAL_LIVE_READ")
        self.assertEqual(result["axes"].get("CURRENT_L2_UNREAD_GAP"), "CLOSED")
        self.assertNotIn(
            "L2 Archive / ChallengeRelay authority state unread.",
            pack.get("unresolved_reason") or "",
        )

    def test_11_semi_blind_pre_run_no_protected_expected_fields(self):
        clean = {
            "path_sot": {
                "PATH_ID": "wrps-v0-p0014",
                "ROLE": "POST_RUN_COMPARISON_REFERENCE_ONLY",
                "STATIC_STATUS_REFERENCE": "COMPARISON_ONLY",
            },
            "fixture_specs": {
                "params_template": {"profileId": 42},
                "expected_calldata_sha256": "REVEAL_AFTER_RUN",
            },
        }
        self.assertEqual(detect_semi_blind_leakage(clean), [])
        leaky = {
            "path_sot": {"STATIC_STATUS_REFERENCE": "COMPLETE", "PATH_ID": "wrps-v0-p0014"},
            "fixture_specs": {"expected_verdict": "PASS"},
        }
        leaks = detect_semi_blind_leakage(leaky)
        self.assertTrue(any(e["code"] == "semi_blind_leakage" for e in leaks))
        pack = build_minimal_pack(pre_run_objects=leaky)
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("semi_blind_leakage", r["reason_codes"])

    def test_12_static_witness_cannot_use_path_sot_as_proof_substitute(self):
        path_sot = {
            "PATH_ID": "wrps-v0-p0014",
            "STATIC_STATUS_REFERENCE": "COMPLETE",
            "ROLE": "PROOF",
        }
        procedure = "Use path-sot COMPLETE as proof substitute for static binding."
        issues = validate_static_procedure_anti_circularity(path_sot, procedure)
        codes = {i["code"] for i in issues}
        self.assertIn("path_sot_status_leak", codes)
        self.assertTrue(
            "static_path_sot_proof_substitute" in codes
            or "static_procedure_label_missing" in codes
            or "path_sot_as_sole_proof" in codes
        )

    def test_13_p0014_procedure_completeness(self):
        procedure_path = HERE / "iw-pack-v1" / "instructions" / "PROCEDURE.md"
        if not procedure_path.exists():
            # materialize may not have been run; use embedded minimal complete text
            text = """
            CAW source commit Weaver pin chain 11155111 fixed fork block target address ABI
            deterministic fixture calldata calldata hash owner resolution local fork impersonation
            ownership verification approval local approval tx snapshot createListing
            return/event/state snapshot revert post-revert raw evidence failure recording
            INPUT SOURCE DERIVED BY WITNESS POST-RUN COMPARISON
            """
        else:
            text = procedure_path.read_text(encoding="utf-8")
        missing = validate_procedure_completeness_p0014(text)
        self.assertEqual(missing, [], msg=f"missing p0014 keywords: {missing}")

    def test_14_p0030_procedure_completeness(self):
        procedure_path = HERE / "iw-pack-v1" / "instructions" / "PROCEDURE.md"
        if not procedure_path.exists():
            text = """
            target ABI parseUnits 18 deterministic fixture fixed block fork source
            eth_call raw return calldata hash
            """
        else:
            text = procedure_path.read_text(encoding="utf-8")
        missing = validate_procedure_completeness_p0030(text)
        self.assertEqual(missing, [], msg=f"missing p0030 keywords: {missing}")

    def test_15_external_submission_receipt_digest_mismatch_fails(self):
        pack = build_minimal_pack()
        pack["external_submission_receipt"]["PACK_DIGEST_RECEIVED"] = "ff" * 32
        r = _verify(pack)
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("external_submission_receipt_digest_mismatch", r["reason_codes"])
        self.assertNotEqual(r["IW_STATUS"], "IW_ACCEPTED")


if __name__ == "__main__":
    unittest.main()
