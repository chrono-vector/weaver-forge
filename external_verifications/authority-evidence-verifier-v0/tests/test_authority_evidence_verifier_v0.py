"""Acceptance + negative tests for weaver-authority-evidence-verifier-v0."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from authority_evidence_verifier_v0 import (  # noqa: E402
    KNOWN_SHARED_OWNER,
    SCHEMA_VERSION,
    attach_authority_evidence_to_synthesizer_paths_v0,
    attach_authority_link_to_runtime_verifier_result_v0,
    generalization_structural_check,
    normalize_caro_authority_pack,
    verify_authority_evidence_v0,
)

CARO_DIR = Path(
    r"C:\dev\external-verification-work\caw-authority-readonly-v1\CARO-20260912-041428-A6BBA9BA"
)


def _verify_caro():
    pack = normalize_caro_authority_pack(CARO_DIR)
    return pack, verify_authority_evidence_v0(
        {"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack}
    )


class TestAuthorityEvidenceVerifierAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack, cls.result = _verify_caro()
        assert cls.result["verification_status"] == "ACCEPTED", cls.result.get("errors")

    def test_at01_ownable_holder_address_verified(self):
        r = self.result
        self.assertIn(r["AUTHORITY_HOLDER_ADDRESS_STATUS"], {"PARTIAL_VERIFIED", "VERIFIED"})
        owners = {
            norm_addr(h["HOLDER_ADDRESS"])
            for h in self.pack["holder_addresses"]
            if str(h.get("HOLDER_ADDRESS", "")).startswith("0x")
        }
        self.assertIn(KNOWN_SHARED_OWNER.lower(), {a.lower() for a in owners})

    def test_at02_holder_identity_unverified(self):
        self.assertEqual(self.result["AUTHORITY_HOLDER_IDENTITY_STATUS"], "NOT_VERIFIED")
        self.assertEqual(self.result["HOLDER_IDENTITY"], "NOT_VERIFIED")

    def test_at03_user_asset_not_protocol_admin(self):
        self.assertEqual(self.result["P0014_AUTHORITY_CLASS"], "USER_ASSET_AUTHORIZATION")
        link = next(l for l in self.pack["runtime_authority_links"] if l["PATH_ID"] == "wrps-v0-p0014")
        self.assertFalse(link.get("inherits_protocol_admin"))
        self.assertNotEqual(link["AUTHORITY_CLASS"], "PROTOCOL_ADMIN_AUTHORITY")

    def test_at04_permissionless_function_not_system(self):
        self.assertEqual(self.result["P0030_AUTHORITY_CLASS"], "PERMISSIONLESS_FUNCTION")
        self.assertFalse(self.result["SYSTEM_PERMISSIONLESS"])
        for s in self.pack["permissionless_surfaces"]:
            self.assertEqual(s["SCOPE"], "FUNCTION")
            self.assertFalse(s.get("SYSTEM_PERMISSIONLESS"))

    def test_at05_scope_mapping_preserved(self):
        scopes = {s["SCOPE"] for s in self.pack["scope_records"]}
        for expected in {
            "MULTI_FUNCTION_ADMIN",
            "FEE_CONTROL",
            "USER_ASSET_CONTROL",
            "MINT_CONTROL",
            "ARCHIVE_CONTROL",
            "SLASH_CONTROL",
        }:
            self.assertIn(expected, scopes)
        self.assertTrue(all(s.get("SYSTEM_WIDE") is False for s in self.pack["scope_records"]))
        self.assertEqual(self.result["AUTHORITY_SCOPE_STATUS"], "MAPPED")

    def test_at06_mutability_preserved(self):
        classes = {m["MUTABILITY_CLASS"] for m in self.pack["mutability_records"]}
        self.assertTrue({"MUTABLE_BY_OWNER", "IMMUTABLE", "NO_MUTATOR_FOUND"} & classes)
        self.assertTrue(
            all(m.get("RUNTIME_EXECUTION_STATUS") == "NOT_EXECUTED" for m in self.pack["mutability_records"])
        )
        self.assertEqual(self.result["AUTHORITY_MUTABILITY_STATUS"], "MAPPED")

    def test_at07_partial_runtime_reads_remain_partial(self):
        self.assertEqual(self.result["AUTHORITY_STATE_READ_STATUS"], "PARTIAL_LIVE_READ")
        self.assertNotEqual(self.result["AUTHORITY_STATE_READ_STATUS"], "LIVE_READ_VERIFIED")

    def test_at08_historical_l2_unread_superseded_gap_closed(self):
        unread = set(self.pack["unread_authority_ids"])
        self.assertEqual(unread, set())
        self.assertEqual(self.pack.get("current_l2_unread_gap"), "CLOSED")
        unread_reads = [
            r
            for r in self.pack["runtime_reads"]
            if r.get("AUTHORITY_ID") in {"AUTH-021", "AUTH-034"} and r.get("RUNTIME_READ_VERDICT") == "UNREAD"
        ]
        self.assertGreaterEqual(len(unread_reads), 2)
        for r in unread_reads:
            self.assertEqual(r.get("CURRENT_INTERPRETATION"), "HISTORICAL_SUPERSEDED")
            self.assertFalse(r.get("CURRENT_BLOCKER"))
        self.assertEqual(self.result["AUTHORITY_STATE"], "PARTIAL_LIVE_READ")
        self.assertNotEqual(self.result["AUTHORITY_STATE"], "VERIFIED")
        self.assertEqual(self.result["axes"].get("CURRENT_L2_UNREAD_GAP"), "CLOSED")
        failed = [r for r in self.pack["runtime_reads"] if r.get("RUNTIME_READ_VERDICT") == "READ_FAILED"]
        self.assertEqual(len(failed), 8)

    def test_at08b_supersession_preserves_raw_failure(self):
        row = next(
            r
            for r in self.pack["runtime_reads"]
            if r.get("ROW_ID") == "CARO-MAIN-14"
        )
        self.assertEqual(row["RUNTIME_READ_VERDICT"], "READ_FAILED")
        self.assertEqual(row["CURRENT_INTERPRETATION"], "HISTORICAL_SUPERSEDED")
        self.assertEqual(row["ORIGINAL_STATUS"], "READ_FAILED")
        self.assertIn("EVIDENCE_REFERENCES", row)
        self.assertTrue(row["EVIDENCE_REFERENCES"])

    def test_at08c_superseded_not_current_l2_gap(self):
        hist_unread = [
            r
            for r in self.pack["runtime_reads"]
            if r.get("AUTHORITY_ID") in {"AUTH-021", "AUTH-034"}
            and r.get("CURRENT_INTERPRETATION") == "HISTORICAL_SUPERSEDED"
        ]
        self.assertGreaterEqual(len(hist_unread), 2)
        self.assertEqual(self.pack.get("unread_authority_ids"), [])
        self.assertEqual(self.pack.get("current_l2_unread_gap"), "CLOSED")
        self.assertNotIn("L2 Archive / ChallengeRelay authority state unread.", self.pack.get("unresolved_reason") or "")
        self.assertIn("ABI", self.pack.get("unresolved_reason") or "")
        self.assertEqual(self.result["AUTHORITY_STATE_READ_STATUS"], "PARTIAL_LIVE_READ")

    def test_at09_privileged_execution_not_verified(self):
        self.assertEqual(self.result["PRIVILEGED_EXECUTION_STATUS"], "NOT_VERIFIED")
        self.assertFalse(self.result["axes"]["PRIVILEGED_EXECUTION_VERIFIED"])

    def test_at10_live_authority_action_not_verified(self):
        self.assertEqual(self.result["LIVE_AUTHORITY_ACTION_STATUS"], "NOT_VERIFIED")
        self.assertFalse(self.result["axes"]["LIVE_AUTHORITY_ACTION_VERIFIED"])

    def test_at11_authority_does_not_promote_iw(self):
        self.assertEqual(self.result["INDEPENDENT_WITNESS_STATUS"], "NOT_SATISFIED")
        self.assertTrue(self.result["nonclaim_gates"]["NG-AUTH-05"])
        self.assertFalse(self.result["nonclaim_gates"]["IW_SATISFIED"])

    def test_at12_authority_does_not_promote_trustless_decentralized(self):
        self.assertFalse(self.result["TRUSTLESS_VERIFIED"])
        self.assertFalse(self.result["DECENTRALIZED_VERIFIED"])
        self.assertTrue(self.result["nonclaim_gates"]["NG-AUTH-01"])
        self.assertTrue(self.result["nonclaim_gates"]["NG-AUTH-02"])

    def test_at13_p0014_classification_preserved(self):
        link = next(l for l in self.result["runtime_authority_links"] if l["PATH_ID"] == "wrps-v0-p0014")
        self.assertEqual(link["AUTHORITY_CLASS"], "USER_ASSET_AUTHORIZATION")

    def test_at14_p0030_classification_preserved(self):
        link = next(l for l in self.result["runtime_authority_links"] if l["PATH_ID"] == "wrps-v0-p0030")
        self.assertEqual(link["AUTHORITY_CLASS"], "PERMISSIONLESS_FUNCTION")
        self.assertFalse(link.get("SYSTEM_PERMISSIONLESS"))

    def test_at15_claim_reassessment_confirmed_caw_unchanged(self):
        claims = self.result["claim_reassessments"]
        self.assertTrue(claims)
        c = claims[0]
        self.assertEqual(c["ASSESSMENT"], "CONFIRMED")
        self.assertEqual(c["OVERALL_CAW_VERDICT_IMPACT"], "NONE")
        self.assertFalse(self.result["caw_verdict_changed"])


class TestAuthorityEvidenceNegative(unittest.TestCase):
    def setUp(self):
        self.pack = normalize_caro_authority_pack(CARO_DIR)

    def test_neg_holder_address_not_identity(self):
        pack = copy.deepcopy(self.pack)
        pack["holder_identities"] = [
            {
                "HOLDER_ADDRESS": KNOWN_SHARED_OWNER,
                "IDENTITY_STATUS": "VERIFIED",
                "IDENTITY_ASSERTION": "inferred_from_address",
                "IDENTITY_EVIDENCE_REFERENCES": [],
                "INFERENCE_FORBIDDEN": True,
            }
        ]
        r = verify_authority_evidence_v0({"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack})
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("holder_identity_without_evidence", r["reason_codes"])

    def test_neg_permissionless_promoted_to_system(self):
        pack = copy.deepcopy(self.pack)
        pack["permissionless_surfaces"][0]["SYSTEM_PERMISSIONLESS"] = True
        r = verify_authority_evidence_v0({"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack})
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("system_permissionless_promotion_forbidden", r["reason_codes"])

    def test_neg_user_asset_promoted_to_admin(self):
        pack = copy.deepcopy(self.pack)
        for link in pack["runtime_authority_links"]:
            if link["PATH_ID"] == "wrps-v0-p0014":
                link["inherits_protocol_admin"] = True
        r = verify_authority_evidence_v0({"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack})
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("user_asset_promoted_to_admin", r["reason_codes"])

    def test_neg_partial_reads_promoted_to_full(self):
        pack = copy.deepcopy(self.pack)
        pack["force_full_state_verified"] = True
        r = verify_authority_evidence_v0({"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack})
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("partial_reads_promoted_to_full", r["reason_codes"])

    def test_neg_architecture_promoted_to_execution(self):
        pack = copy.deepcopy(self.pack)
        pack["declared_axes"]["PRIVILEGED_EXECUTION_STATUS"] = "VERIFIED"
        # No privileged_execution_evidence → validate_separations rejects
        r = verify_authority_evidence_v0({"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack})
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("privileged_execution_without_evidence", r["reason_codes"])

    def test_neg_execution_promoted_to_live_action(self):
        pack = copy.deepcopy(self.pack)
        pack["privileged_execution_evidence"] = {"note": "synthetic local privileged call"}
        pack["declared_axes"]["PRIVILEGED_EXECUTION_STATUS"] = "VERIFIED"
        pack["declared_axes"]["LIVE_AUTHORITY_ACTION_STATUS"] = "VERIFIED"
        # live without evidence → reject
        r = verify_authority_evidence_v0({"schema_version": SCHEMA_VERSION, "authority_evidence_pack": pack})
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("live_authority_action_without_evidence", r["reason_codes"])

    def test_architecture_does_not_imply_execution_when_accepted(self):
        r = verify_authority_evidence_v0(
            {"schema_version": SCHEMA_VERSION, "authority_evidence_pack": self.pack}
        )
        self.assertTrue(r["axes"]["AUTHORITY_ARCHITECTURE_MAPPED"])
        self.assertFalse(r["axes"]["PRIVILEGED_EXECUTION_VERIFIED"])
        self.assertFalse(r["axes"]["LIVE_AUTHORITY_ACTION_VERIFIED"])


class TestAuthorityLinkConsumers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack, cls.auth = _verify_caro()

    def test_runtime_link_p0014(self):
        runtime = {
            "schema_version": "weaver-runtime-evidence-verifier-v0",
            "verification_status": "ACCEPTED",
            "path_id": "wrps-v0-p0014",
            "RUNTIME_EXECUTION_STATUS": "LOCAL_EXECUTION_ALIGNED",
            "AUTHORITY_STATUS": "NOT_VERIFIED",
            "nonclaim_gates": {"AUTHORITY_VERIFIED": False},
        }
        out = attach_authority_link_to_runtime_verifier_result_v0(runtime, self.auth)
        self.assertEqual(out["authority_link"]["AUTHORITY_CLASS"], "USER_ASSET_AUTHORIZATION")
        self.assertFalse(out["authority_link"]["PROTOCOL_ADMIN_AUTHORITY"])
        self.assertEqual(out["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertNotEqual(out.get("AUTHORITY_STATUS"), "VERIFIED")

    def test_runtime_link_p0030(self):
        runtime = {
            "schema_version": "weaver-runtime-evidence-verifier-v0",
            "verification_status": "ACCEPTED",
            "path_id": "wrps-v0-p0030",
            "RUNTIME_EXECUTION_STATUS": "LOCAL_EXECUTION_ALIGNED",
            "AUTHORITY_STATUS": "NOT_VERIFIED",
        }
        out = attach_authority_link_to_runtime_verifier_result_v0(runtime, self.auth)
        self.assertEqual(out["authority_link"]["AUTHORITY_CLASS"], "PERMISSIONLESS_FUNCTION")
        self.assertFalse(out["authority_link"]["SYSTEM_PERMISSIONLESS"])

    def test_synthesizer_attach_preserves_static(self):
        synth = {
            "schema_version": "weaver-runtime-path-synthesizer-v0",
            "paths": [
                {
                    "path_id": "wrps-v0-p0014",
                    "STATIC_PATH_STATUS": "COMPLETE",
                    "path_status": "COMPLETE",
                    "AUTHORITY_STATUS": "NOT_VERIFIED",
                },
                {
                    "path_id": "wrps-v0-p0030",
                    "STATIC_PATH_STATUS": "COMPLETE",
                    "path_status": "COMPLETE",
                    "AUTHORITY_STATUS": "NOT_VERIFIED",
                },
            ],
        }
        out = attach_authority_evidence_to_synthesizer_paths_v0(synth, self.auth)
        p14 = next(p for p in out["paths"] if p["path_id"] == "wrps-v0-p0014")
        p30 = next(p for p in out["paths"] if p["path_id"] == "wrps-v0-p0030")
        self.assertEqual(p14["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(p14["AUTHORITY_CLASS"], "USER_ASSET_AUTHORIZATION")
        self.assertEqual(p30["AUTHORITY_CLASS"], "PERMISSIONLESS_FUNCTION")
        self.assertEqual(p14["AUTHORITY_MECHANISM_STATUS"], "MAPPED")
        self.assertEqual(p14["AUTHORITY_STATE_READ_STATUS"], "PARTIAL_LIVE_READ")

    def test_generalization_structural(self):
        g = generalization_structural_check()
        self.assertFalse(g["empirically_verified_all"])
        cases = {c["case"] for c in g["structural_support"]}
        for need in {
            "OWNABLE",
            "TOKEN_OWNER_GATE",
            "PROFILE_OWNER_GATE",
            "PERMISSIONLESS_FUNCTION",
            "CUSTOM_ROLE",
            "CONTRACT_GATE",
            "SIGNATURE_GATE",
            "VALIDATOR_GATE",
            "PARTIAL_LIVE_READ",
            "UNREAD_AUTHORITY_STATE",
            "FUTURE_L2_AUTHORITY_READS",
        }:
            self.assertIn(need, cases)


def norm_addr(a: str) -> str:
    return "0x" + a[2:].lower() if a.startswith("0x") else a.lower()


class TestCounts(unittest.TestCase):
    def test_mechanism_and_surface_counts(self):
        pack = normalize_caro_authority_pack(CARO_DIR)
        self.assertEqual(len(pack["mechanisms"]), 23)
        self.assertEqual(len(pack["privileged_surfaces"]), 11)
        self.assertEqual(len(pack["permissionless_surfaces"]), 8)


if __name__ == "__main__":
    unittest.main()
