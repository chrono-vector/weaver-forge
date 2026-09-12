"""Acceptance + negative tests for weaver-runtime-evidence-verifier-v0."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parent
SYNTH = MOD.parent / "runtime-path-synthesizer-v0"
for p in (MOD, SYNTH):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from runtime_evidence_verifier_v0 import (  # noqa: E402
    SCHEMA_VERSION,
    attach_runtime_evidence_to_synthesizer_paths_v0,
    build_p0014_runtime_evidence_pack,
    build_p0030_runtime_evidence_pack,
    pack_subset,
    validate_runtime_evidence_verifier_result_v0,
    verify_runtime_evidence_v0,
)


def req(pack, **kw):
    r = {
        "schema_version": SCHEMA_VERSION,
        "runtime_evidence_pack": pack,
        "design_run_id": "WREID-20260912-113817-2D2509C8",
        "notes": "test",
    }
    r.update(kw)
    return r


class RuntimeEvidenceVerifierTests(unittest.TestCase):
    def setUp(self):
        self.full = build_p0014_runtime_evidence_pack()

    def test_at01_vr0_only(self):
        pack = pack_subset(self.full, ["R0"])
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["RUNTIME_INPUT_STATUS"], "ALIGNED")
        self.assertEqual(r["highest_runtime_level"], "R0_INPUT_ALIGNED")
        self.assertEqual(r["RUNTIME_DISPATCH_STATUS"], "UNVERIFIED")
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "UNVERIFIED")
        self.assertEqual(r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertEqual(validate_runtime_evidence_verifier_result_v0(r), [])

    def test_at02_vr1_ownership_revert(self):
        pack = pack_subset(self.full, ["R0", "R1"])
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["RUNTIME_DISPATCH_STATUS"], "ALIGNED")
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "BLOCKED")
        self.assertEqual(r["highest_runtime_level"], "R1_DISPATCH_ALIGNED")
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "EXECUTION_PARTIAL")
        gates = r["precondition_chain"]
        self.assertTrue(any(g["PRECONDITION_ID"].endswith("ownership.gate") for g in gates))

    def test_at03_vr2_ownership_cleared_approval_revert(self):
        pack = pack_subset(self.full, ["R0", "R1", "R2"])
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "PROGRESSING")
        self.assertEqual(r["highest_runtime_level"], "R2_PRECONDITION_PATH_ALIGNED")
        own = next(g for g in r["precondition_chain"] if "ownership" in g["PRECONDITION_ID"])
        appr = next(g for g in r["precondition_chain"] if "approval" in g["PRECONDITION_ID"])
        self.assertEqual(own["RESULT"], "CLEARED")
        self.assertEqual(appr["RESULT"], "BLOCKED")
        self.assertNotEqual(r["AUTHORITY_STATUS"], "VERIFIED")
        self.assertFalse(r["nonclaim_gates"]["AUTHORITY_VERIFIED"])

    def test_at04_vr3_local_execution_success(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["highest_runtime_level"], "R3_LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["execution_evidence_source_stage"], "VR3")
        self.assertEqual(r["result_event"]["return_value"]["decoded"]["listingId"], 74)
        self.assertEqual(r["result_event"]["events"][0]["name"], "Listed")
        self.assertEqual(r["result_event"]["scope"], "BOUNDED_LOCAL_FORK_SAMPLE")
        self.assertEqual(r["RUNTIME_STATE_TRANSITION_STATUS"], "OBSERVED_LOCAL")
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "CLEARED")

    def test_at05_local_fork_ne_live_mutation(self):
        r = verify_runtime_evidence_v0(req(self.full))
        muts = r["local_fork_mutations"]
        self.assertTrue(any(m["type"] == "LOCAL_STATE_MUTATION" for m in muts))
        self.assertTrue(all(m.get("mutation_scope") == "LOCAL_FORK_ONLY" for m in muts))
        self.assertEqual(r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertFalse(r["nonclaim_gates"]["LIVE_TRANSACTION_VERIFIED"])

    def test_at06_snapshot_revert_verification(self):
        r = verify_runtime_evidence_v0(req(self.full))
        types = {m["type"] for m in r["local_fork_mutations"]}
        self.assertIn("SNAPSHOT", types)
        self.assertIn("REVERT", types)
        self.assertIn("FORK_DISPOSED", types)
        disposed = next(m for m in r["local_fork_mutations"] if m["type"] == "FORK_DISPOSED")
        self.assertTrue(disposed["disposed"])
        self.assertFalse(disposed["public_rpc_mutation"])
        revert = next(m for m in r["local_fork_mutations"] if m["type"] == "REVERT")
        self.assertTrue(revert["reverted"])

    def test_at07_no_live_transaction(self):
        r = verify_runtime_evidence_v0(req(self.full))
        live = self.full["live_transaction"]
        self.assertFalse(live["public_transaction"])
        self.assertIsNone(live["live_tx_hash"])
        self.assertEqual(r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertFalse(r["runtime_execution_verified"])  # NG-5

    def test_at08_authority_stays_unverified(self):
        pack = json.loads(json.dumps(self.full))
        pack["prior_axes"]["AUTHORITY_STATUS"] = "NOT_VERIFIED"
        # Attempt illicit promotion via pack field.
        pack["promote_authority"] = True
        r = verify_runtime_evidence_v0(req(pack))
        self.assertNotEqual(r["AUTHORITY_STATUS"], "VERIFIED")
        self.assertFalse(r["nonclaim_gates"]["AUTHORITY_VERIFIED"])

    def test_at09_signer_identity_stays_unverified(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertNotEqual(r["SIGNER_IDENTITY_STATUS"], "VERIFIED")
        self.assertFalse(r["nonclaim_gates"]["RUNTIME_SIGNER_IDENTITY_VERIFIED"])
        self.assertTrue(any(m["type"] == "ACCOUNT_IMPERSONATION" for m in r["local_fork_mutations"]))

    def test_at10_iw_stays_unsatisfied(self):
        pack = json.loads(json.dumps(self.full))
        pack["force_iw_satisfied"] = True
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["INDEPENDENT_WITNESS_STATUS"], "NOT_SATISFIED")
        self.assertFalse(r["nonclaim_gates"]["INDEPENDENT_WITNESS_VERIFIED"])

    def test_at11_caw_verdict_unchanged(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertFalse(r["nonclaim_gates"]["CAW_VERDICT_CHANGED"])
        self.assertFalse(r["execution_authorized"])

    def test_at12_path_id_and_calldata_linkage(self):
        r = verify_runtime_evidence_v0(req(self.full))
        link = r["static_runtime_link"]
        self.assertEqual(link["PATH_ID"], "wrps-v0-p0014")
        self.assertEqual(
            link["CALLDATA_SHA256"],
            "b267246aafdc5c0672fb008cb9611e1e36bf0465b8d0116a5d66ba925bd856ea",
        )

    def test_neg_mismatched_path_id(self):
        pack = json.loads(json.dumps(self.full))
        pack["records"][2]["PATH_ID"] = "wrps-v0-p9999"
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("mismatched_PATH_ID", r["reason_codes"])

    def test_neg_mismatched_target(self):
        pack = json.loads(json.dumps(self.full))
        pack["records"][1]["TARGET_ADDRESS"] = "0x0000000000000000000000000000000000000001"
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("mismatched_target", r["reason_codes"])

    def test_neg_mismatched_selector(self):
        pack = json.loads(json.dumps(self.full))
        pack["records"][0]["SELECTOR"] = "0xdeadbeef"
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("mismatched_selector", r["reason_codes"])

    def test_neg_mismatched_calldata_hash(self):
        pack = json.loads(json.dumps(self.full))
        pack["records"][3]["CALLDATA_SHA256"] = "a" * 64
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("mismatched_calldata_hash", r["reason_codes"])

    def test_neg_out_of_order_chain(self):
        pack = json.loads(json.dumps(self.full))
        pack["records"] = [pack["records"][1], pack["records"][0], pack["records"][2], pack["records"][3]]
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("out_of_order_runtime_chain", r["reason_codes"])

    def test_neg_contradictory_live_local(self):
        pack = json.loads(json.dumps(self.full))
        pack["claim_live_from_local_fork"] = True
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "REJECTED")
        self.assertIn("contradictory_live_local_mutation", r["reason_codes"])

    def test_r3_does_not_imply_live(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertEqual(r["highest_runtime_level"], "R3_LOCAL_EXECUTION_ALIGNED")
        self.assertNotEqual(r["highest_runtime_level"], "LIVE_TRANSACTION_VERIFIED")
        self.assertEqual(r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")

    def test_synthesizer_consumer_attach_by_path_id(self):
        r = verify_runtime_evidence_v0(req(self.full))
        synth = {
            "schema_version": "weaver-runtime-path-synthesizer-v0",
            "result_id": "wrps-v0-" + ("a" * 32),
            "runtime_execution_verified": False,
            "paths": [
                {
                    "path_id": "wrps-v0-p0014",
                    "path_status": "COMPLETE",
                    "STATIC_PATH_STATUS": "COMPLETE",
                    "RUNTIME_EXECUTION_STATUS": "UNVERIFIED",
                    "AUTHORITY_STATUS": "PARTIAL",
                    "SIGNER_IDENTITY_STATUS": "UNVERIFIED",
                    "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
                },
                {
                    "path_id": "wrps-v0-p0001",
                    "path_status": "PARTIAL",
                    "STATIC_PATH_STATUS": "PARTIAL",
                    "RUNTIME_EXECUTION_STATUS": "UNVERIFIED",
                    "AUTHORITY_STATUS": "UNVERIFIED",
                    "SIGNER_IDENTITY_STATUS": "UNVERIFIED",
                    "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
                },
            ],
            "summary": {},
        }
        out = attach_runtime_evidence_to_synthesizer_paths_v0(synth, r)
        p14 = next(p for p in out["paths"] if p["path_id"] == "wrps-v0-p0014")
        other = next(p for p in out["paths"] if p["path_id"] == "wrps-v0-p0001")
        self.assertEqual(p14["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(p14["path_status"], "COMPLETE")
        self.assertEqual(p14["RUNTIME_INPUT_STATUS"], "ALIGNED")
        self.assertEqual(p14["RUNTIME_DISPATCH_STATUS"], "ALIGNED")
        self.assertEqual(p14["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(p14["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertNotEqual(p14["AUTHORITY_STATUS"], "VERIFIED")
        self.assertEqual(p14["INDEPENDENT_WITNESS_STATUS"], "NOT_SATISFIED")
        self.assertNotIn("RUNTIME_INPUT_STATUS", other)
        self.assertFalse(out["runtime_execution_verified"])
        self.assertEqual(out["runtime_evidence_attach"]["status"], "ATTACHED")

    def test_generalization_structural_shapes(self):
        """Schema/verifier can structurally represent non-p0014 path classes (no execution)."""
        base_link = {
            "PATH_ID": "wrps-v0-demo",
            "TARGET_ADDRESS": "0x6404d1D3D878407a0977d99C832453f235DA67C3",
            "METHOD_SIGNATURE": "balanceOf(address)",
            "SELECTOR": "0x70a08231",
            "CALLDATA_SHA256": "b" * 64,
            "CHAIN_ID": 11155111,
            "FORK_BLOCK": 1,
        }

        def pack_for(records, **extra):
            return {
                "schema_version": "weaver-runtime-evidence-pack-v0",
                "static_runtime_link": base_link,
                "records": records,
                "prior_axes": {
                    "STATIC_PATH_STATUS": "PARTIAL",
                    "AUTHORITY_STATUS": "NOT_VERIFIED",
                    "SIGNER_IDENTITY_STATUS": "NOT_VERIFIED",
                    "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
                },
                "caw_verdict_snapshot": {"CAW_VERDICT_CHANGED": False},
                "live_transaction": {"verified": False},
                **extra,
            }

        # deterministic revert path
        revert_pack = pack_for(
            [
                {
                    "level": "R0",
                    "run_id": "X0",
                    "status": "RUNTIME_INPUT_ALIGNMENT_VERIFIED",
                    "PATH_ID": "wrps-v0-demo",
                    "TARGET_ADDRESS": base_link["TARGET_ADDRESS"],
                    "SELECTOR": base_link["SELECTOR"],
                    "CALLDATA_SHA256": base_link["CALLDATA_SHA256"],
                    "METHOD_SIGNATURE": base_link["METHOD_SIGNATURE"],
                },
                {
                    "level": "R1",
                    "run_id": "X1",
                    "status": "RUNTIME_DISPATCH_ALIGNMENT_VERIFIED",
                    "PATH_ID": "wrps-v0-demo",
                    "TARGET_ADDRESS": base_link["TARGET_ADDRESS"],
                    "SELECTOR": base_link["SELECTOR"],
                    "CALLDATA_SHA256": base_link["CALLDATA_SHA256"],
                    "METHOD_SIGNATURE": base_link["METHOD_SIGNATURE"],
                    "CHAIN_ID": 11155111,
                    "FORK_BLOCK": 1,
                    "precondition_class": "OWNERSHIP_PRECONDITION",
                },
            ]
        )
        rr = verify_runtime_evidence_v0(req(revert_pack))
        self.assertEqual(rr["highest_runtime_level"], "R1_DISPATCH_ALIGNED")

        # read-only / no-state-mutation
        ro = pack_for(
            [
                {
                    "level": "R0",
                    "run_id": "Y0",
                    "status": "RUNTIME_INPUT_ALIGNMENT_VERIFIED",
                    "PATH_ID": "wrps-v0-demo",
                    "TARGET_ADDRESS": base_link["TARGET_ADDRESS"],
                    "SELECTOR": base_link["SELECTOR"],
                    "CALLDATA_SHA256": base_link["CALLDATA_SHA256"],
                    "METHOD_SIGNATURE": base_link["METHOD_SIGNATURE"],
                }
            ],
            precondition_chain=[],
            local_fork_mutations=[],
        )
        ro_r = verify_runtime_evidence_v0(req(ro))
        self.assertEqual(ro_r["highest_runtime_level"], "R0_INPUT_ALIGNED")
        self.assertEqual(ro_r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")

        # local-success + bounded setup already covered by full p0014
        self.assertEqual(
            verify_runtime_evidence_v0(req(self.full))["highest_runtime_level"],
            "R3_LOCAL_EXECUTION_ALIGNED",
        )

    def test_gen01_success_at_vr1_without_vr2_vr3(self):
        pack = build_p0030_runtime_evidence_pack()
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["RUNTIME_INPUT_STATUS"], "ALIGNED")
        self.assertEqual(r["RUNTIME_DISPATCH_STATUS"], "ALIGNED")
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "NO_BLOCKING_PRECONDITION_OBSERVED")
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["highest_runtime_level"], "R3_LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["execution_evidence_source_stage"], "VR1")
        self.assertEqual(r["run_stage_meta"]["max_run_stage"], "VR1")
        self.assertNotIn("VR2", r["run_stage_meta"]["run_stages_present"])
        self.assertNotIn("VR3", r["run_stage_meta"]["run_stages_present"])

    def test_gen02_deterministic_revert_at_vr1(self):
        pack = pack_subset(self.full, ["R0", "R1"])
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["RUNTIME_DISPATCH_STATUS"], "ALIGNED")
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "EXECUTION_PARTIAL")
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "BLOCKED")
        self.assertEqual(r["highest_runtime_level"], "R1_DISPATCH_ALIGNED")

    def test_gen03_success_at_vr3_after_preconditions(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "CLEARED")
        self.assertEqual(r["execution_evidence_source_stage"], "VR3")
        self.assertEqual(r["run_stage_meta"]["run_stages_present"], ["VR0", "VR1", "VR2", "VR3"])

    def test_gen04_empty_precondition_chain_allowed(self):
        pack = build_p0030_runtime_evidence_pack()
        self.assertEqual(pack["precondition_chain"], [])
        r = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["precondition_chain"], [])
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "NO_BLOCKING_PRECONDITION_OBSERVED")

    def test_gen05_eth_call_success_not_live_tx(self):
        r = verify_runtime_evidence_v0(req(build_p0030_runtime_evidence_pack()))
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertFalse(r["nonclaim_gates"]["LIVE_TRANSACTION_VERIFIED"])
        self.assertFalse(r["runtime_execution_verified"])

    def test_gen06_eth_call_success_not_persistent_state(self):
        r = verify_runtime_evidence_v0(req(build_p0030_runtime_evidence_pack()))
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["RUNTIME_STATE_TRANSITION_STATUS"], "SIMULATED_ONLY")
        self.assertFalse(r["run_stage_meta"]["persistent_state_commit_observed"])

    def test_gen07_local_tx_with_state_implies_observed_local(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertEqual(r["RUNTIME_STATE_TRANSITION_STATUS"], "OBSERVED_LOCAL")
        self.assertTrue(r["run_stage_meta"]["persistent_state_commit_observed"])

    def test_gen08_run_ordinal_does_not_determine_semantic_level(self):
        p30 = verify_runtime_evidence_v0(req(build_p0030_runtime_evidence_pack()))
        p14 = verify_runtime_evidence_v0(req(self.full))
        self.assertEqual(p30["RUNTIME_EXECUTION_STATUS"], p14["RUNTIME_EXECUTION_STATUS"])
        self.assertEqual(p30["highest_runtime_level"], p14["highest_runtime_level"])
        self.assertEqual(p30["execution_evidence_source_stage"], "VR1")
        self.assertEqual(p14["execution_evidence_source_stage"], "VR3")
        self.assertNotEqual(p30["run_stage_meta"]["max_run_stage"], p14["run_stage_meta"]["max_run_stage"])

    def test_gen09_authority_unverified(self):
        for pack in (self.full, build_p0030_runtime_evidence_pack()):
            r = verify_runtime_evidence_v0(req(pack))
            self.assertEqual(r["AUTHORITY_STATUS"], "NOT_VERIFIED")
            self.assertFalse(r["nonclaim_gates"]["AUTHORITY_VERIFIED"])

    def test_gen10_signer_identity_unverified(self):
        for pack in (self.full, build_p0030_runtime_evidence_pack()):
            r = verify_runtime_evidence_v0(req(pack))
            self.assertEqual(r["SIGNER_IDENTITY_STATUS"], "NOT_VERIFIED")
            self.assertFalse(r["nonclaim_gates"]["RUNTIME_SIGNER_IDENTITY_VERIFIED"])

    def test_gen11_iw_unsatisfied(self):
        for pack in (self.full, build_p0030_runtime_evidence_pack()):
            r = verify_runtime_evidence_v0(req(pack))
            self.assertEqual(r["INDEPENDENT_WITNESS_STATUS"], "NOT_SATISFIED")
            self.assertFalse(r["nonclaim_gates"]["INDEPENDENT_WITNESS_VERIFIED"])

    def test_gen12_p0014_regression_unchanged(self):
        r = verify_runtime_evidence_v0(req(self.full))
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["RUNTIME_INPUT_STATUS"], "ALIGNED")
        self.assertEqual(r["RUNTIME_DISPATCH_STATUS"], "ALIGNED")
        self.assertEqual(r["RUNTIME_PRECONDITION_STATUS"], "CLEARED")
        self.assertEqual(r["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(r["RUNTIME_STATE_TRANSITION_STATUS"], "OBSERVED_LOCAL")
        self.assertEqual(r["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertEqual(r["AUTHORITY_STATUS"], "NOT_VERIFIED")
        self.assertEqual(r["SIGNER_IDENTITY_STATUS"], "NOT_VERIFIED")
        self.assertEqual(r["INDEPENDENT_WITNESS_STATUS"], "NOT_SATISFIED")
        self.assertEqual(r["highest_runtime_level"], "R3_LOCAL_EXECUTION_ALIGNED")
        self.assertFalse(r["runtime_execution_verified"])
        self.assertEqual(validate_runtime_evidence_verifier_result_v0(r), [])

    def test_gen_synthesizer_consumer_p0030_axes_independent(self):
        r = verify_runtime_evidence_v0(req(build_p0030_runtime_evidence_pack()))
        synth = {
            "schema_version": "weaver-runtime-path-synthesizer-v0",
            "result_id": "wrps-v0-" + ("b" * 32),
            "runtime_execution_verified": False,
            "paths": [
                {
                    "path_id": "wrps-v0-p0030",
                    "path_status": "COMPLETE",
                    "STATIC_PATH_STATUS": "COMPLETE",
                    "RUNTIME_EXECUTION_STATUS": "UNVERIFIED",
                    "AUTHORITY_STATUS": "NOT_VERIFIED",
                    "SIGNER_IDENTITY_STATUS": "NOT_VERIFIED",
                    "INDEPENDENT_WITNESS_STATUS": "NOT_SATISFIED",
                }
            ],
            "summary": {},
        }
        out = attach_runtime_evidence_to_synthesizer_paths_v0(synth, r)
        p = out["paths"][0]
        self.assertEqual(p["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(p["path_status"], "COMPLETE")
        self.assertEqual(p["RUNTIME_EXECUTION_STATUS"], "LOCAL_EXECUTION_ALIGNED")
        self.assertEqual(p["RUNTIME_STATE_TRANSITION_STATUS"], "SIMULATED_ONLY")
        self.assertEqual(p["LIVE_TRANSACTION_STATUS"], "NOT_VERIFIED")
        self.assertEqual(p["execution_evidence_source_stage"], "VR1")
        self.assertFalse(out["runtime_execution_verified"])

    def test_optional_authority_link_refuses_promotion(self):
        pack = build_p0014_runtime_evidence_pack()
        r = verify_runtime_evidence_v0(
            req(
                pack,
                authority_link={
                    "PATH_ID": "wrps-v0-p0014",
                    "AUTHORITY_CLASS": "USER_ASSET_AUTHORIZATION",
                    "CALLER_GATE_CLASS": "TOKEN_OWNER_GATED",
                    "AUTHORITY_STATUS": "VERIFIED",
                    "promote_authority_verified": True,
                    "EVIDENCE_DIGEST": "deadbeef",
                },
            )
        )
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertIsNotNone(r.get("authority_link_attach"))
        self.assertTrue(r["authority_link_attach"]["authority_promotion_refused"])
        self.assertTrue(r["authority_link_attach"]["runtime_completion_promotion_refused"])
        self.assertNotEqual(r["AUTHORITY_STATUS"], "VERIFIED")
        self.assertEqual(
            r["authority_link_attach"]["link"]["AUTHORITY_CLASS"],
            "USER_ASSET_AUTHORIZATION",
        )

    def test_optional_authority_pack_digest_backward_compatible(self):
        pack = build_p0030_runtime_evidence_pack()
        r = verify_runtime_evidence_v0(req(pack, authority_pack_digest="abc123"))
        self.assertEqual(r["verification_status"], "ACCEPTED")
        self.assertEqual(r["authority_link_attach"]["status"], "REFERENCE_RECORDED")
        self.assertEqual(r["authority_link_attach"]["authority_pack_digest"], "abc123")
        # Absent authority_link still works
        r2 = verify_runtime_evidence_v0(req(pack))
        self.assertEqual(r2["verification_status"], "ACCEPTED")
        self.assertIsNone(r2.get("authority_link_attach"))


if __name__ == "__main__":
    unittest.main()
