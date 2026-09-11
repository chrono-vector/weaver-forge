from __future__ import annotations
import sys, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
MOD = HERE.parent
if str(MOD) not in sys.path:
    sys.path.insert(0, str(MOD))
from runtime_path_synthesizer_v0 import SCHEMA_VERSION, synthesize_runtime_paths_v0, validate_runtime_path_synthesizer_result_v0


def req(**over):
    t = "a" * 40
    sv = {
        "schema_version": "weaver-external-repo-source-verifier-v0",
        "result_id": "wersv-v0-" + "1" * 32,
        "target_commit": t,
        "repo_path": "/tmp/repo",
        "audit_source_valid": True,
        "evidence_critical_results": [],
    }
    ri = {
        "schema_version": "weaver-runtime-surface-inventory-v0",
        "result_id": "wrsi-v0-" + "2" * 32,
        "target_commit": t,
        "runtime_execution_verified": False,
        "surface_results": [
            {"category": "signer_private_key_loading", "file": "svc.ts", "line_start": 5, "line_end": 5, "symbol": "signer", "analysis_mode": "DETERMINISTIC", "evidence_status": "CONFIRMED", "source_origin": "WORKTREE"},
            {"category": "rpc_provider_initialization", "file": "svc.ts", "line_start": 6, "line_end": 6, "symbol": "provider", "analysis_mode": "DETERMINISTIC", "evidence_status": "CONFIRMED", "source_origin": "WORKTREE"},
            {"category": "receipt_confirmation", "file": "svc.ts", "line_start": 20, "line_end": 20, "symbol": "wait", "analysis_mode": "DETERMINISTIC", "evidence_status": "CONFIRMED", "source_origin": "WORKTREE"},
            {"category": "retry_logic", "file": "svc.ts", "line_start": 30, "line_end": 30, "symbol": "retry", "analysis_mode": "DETERMINISTIC", "evidence_status": "CONFIRMED", "source_origin": "WORKTREE"},
        ],
    }
    mc = {
        "schema_version": "weaver-mutating-callsite-analyzer-v0",
        "result_id": "wmca-v0-" + "3" * 32,
        "target_commit": t,
        "runtime_execution_verified": False,
        "signer_sources_mapped": "YES",
        "contract_address_sources_mapped": "YES",
        "generated_dependency_findings": [],
        "callsite_results": [{
            "callsite_id": "wmca-v0-c0001",
            "file": "svc.ts",
            "line_start": 10,
            "line_end": 12,
            "caller_symbol": "process",
            "symbol": "sendTransaction",
            "target_method": "sendTransaction",
            "actor_role": "validator",
            "signer_source": "validator signer",
            "contract_address_source": "generated address",
            "authority_status": "CONFIRMED",
            "analysis_mode": "DETERMINISTIC",
            "evidence_status": "CONFIRMED",
            "capability_status": "CONFIRMED",
            "source_origin": "WORKTREE",
        }],
    }
    qs = {
        "schema_version": "weaver-queue-state-transition-analyzer-v0",
        "result_id": "wqsta-v0-" + "4" * 32,
        "target_commit": t,
        "dynamic_execution_verified": False,
        "queue_models": [{"file": "schema.prisma", "line_start": 1, "line_end": 3, "symbol": "TxQueue", "model_name": "TxQueue", "analysis_mode": "DETERMINISTIC", "evidence_status": "CONFIRMED", "source_origin": "WORKTREE"}],
        "transitions": [{"file": "svc.ts", "line_start": 40, "line_end": 41, "to_state": "done", "analysis_mode": "DETERMINISTIC", "evidence_status": "CONFIRMED"}],
        "summary": {"partial_findings": 0, "unresolved_count": 0},
    }
    r = {
        "schema_version": SCHEMA_VERSION,
        "source_verifier_result": sv,
        "runtime_inventory_result": ri,
        "mutating_callsite_result": mc,
        "queue_state_transition_result": qs,
        "repo_path": "/tmp/repo",
        "target_commit": t,
        "notes": "test",
    }
    r.update(over)
    return r


def _rec(**kw):
    base = {
        "schema_version": "weaver-static-evidence-record-v0",
        "evidence_id": kw.pop("evidence_id", "wser-v0-" + "a" * 32),
        "producer_module": "weaver-config-address-provenance-analyzer-v0",
        "producer_version": "v0",
        "target_commit": "a" * 40,
        "subject_type": "CALLSITE",
        "subject_id": "wmca-v0-c0001",
        "relation_type": "RESOLVES_ADDRESS",
        "from_entity": {"entity_type": "CALLSITE", "entity_id": "wmca-v0-c0001", "file": "svc.ts", "line_start": 10, "line_end": 12, "symbol": "process"},
        "to_entity": {"entity_type": "ADDRESS_SOURCE", "entity_id": "config/address", "file": "deployments.ts", "line_start": 1, "line_end": 1, "symbol": "Caw"},
        "source_file": "svc.ts",
        "line_start": 10,
        "line_end": 12,
        "source_symbol": "process",
        "analysis_mode": "DETERMINISTIC",
        "evidence_status": "CONFIRMED",
        "chain_context": "mainnet",
        "contract_name": "Caw",
        "callsite_id": "wmca-v0-c0001",
        "config_key": "CAW_ADDRESS",
        "generated_dependency": "NO",
        "human_review_required": "NO",
        "confidence_boundary": "STATIC_PROVENANCE",
        "limitations": [],
        "orphan_type": "MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS",
    }
    base.update(kw)
    return base


def evidence_graph(**over):
    t = "a" * 40
    records = over.pop("normalized_records", None)
    conflicts = over.pop("conflicts", [])
    not_found = over.pop("not_found_records", [])
    updates = over.pop("path_blocker_updates", [])
    if records is None:
        records = [_rec()]
    g = {
        "schema_version": "weaver-static-evidence-graph-v0",
        "result_id": "wsei-v0-" + "b" * 32,
        "graph_id": "wseg-v0-" + "c" * 32,
        "target_commit": t,
        "normalized_records": records,
        "nodes": [],
        "edges": [],
        "conflicts": conflicts,
        "not_found_records": not_found,
        "orphan_report": [],
        "producer_coverage": [],
        "path_synthesizer_contract": {
            "schema_version": "weaver-runtime-path-synthesizer-evidence-contract-v0",
            "consumable_by": "weaver-runtime-path-synthesizer-v1-or-adapter",
            "does_not_modify": "weaver-runtime-path-synthesizer-v0",
            "join_keys": ["callsite_id"],
            "path_blocker_updates": updates,
            "conflict_evidence_ids": [c.get("evidence_id") for c in conflicts],
            "not_found_evidence_ids": [n.get("evidence_id") for n in not_found],
            "consumption_rule": "refine only",
        },
        "summary": {},
        "runtime_execution_verified": False,
        "live_match_verified": False,
        "execution_authorized": False,
        "runtime_path_synthesizer_modified": False,
        "created_at": "2026-01-01T00:00:00Z",
    }
    g.update(over)
    return g


class LegacyT(unittest.TestCase):
    def test_t1_complete_queue_service_write_state_update_path(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(validate_runtime_path_synthesizer_result_v0(r), [])

    def test_t2_missing_signer_source_partial(self):
        x = req()
        x["mutating_callsite_result"]["callsite_results"][0]["signer_source"] = "unknown signer source"
        x["mutating_callsite_result"]["signer_sources_mapped"] = "PARTIAL"
        x["runtime_inventory_result"]["surface_results"] = [s for s in x["runtime_inventory_result"]["surface_results"] if s["category"] != "signer_private_key_loading"]
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["path_status"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "SIGNER_SOURCE_PARTIAL" for g in r["path_gaps"]))

    def test_t3_missing_address_source_partial(self):
        x = req()
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["path_status"], "PARTIAL")

    def test_t4_receipt_path_absent_does_not_block_static_complete(self):
        x = req()
        x["runtime_inventory_result"]["surface_results"] = [s for s in x["runtime_inventory_result"]["surface_results"] if s["category"] != "receipt_confirmation"]
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["receipt_handling_present"], "NO")
        self.assertEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(r["paths"][0]["RUNTIME_EXECUTION_STATUS"], "UNVERIFIED")

    def test_t5_unsupported_semantic_edge_not_fabricated(self):
        x = req()
        x["queue_state_transition_result"]["transitions"] = []
        r = synthesize_runtime_paths_v0(x)
        self.assertFalse(any(e["edge_type"] == "UPDATES_QUEUE" for e in r["edges"]))

    def test_t6_multiple_actor_paths_separated(self):
        x = req()
        c = dict(x["mutating_callsite_result"]["callsite_results"][0])
        c["actor_role"] = "frontend wallet user"
        c["file"] = "fe.tsx"
        x["mutating_callsite_result"]["callsite_results"].append(c)
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["summary"]["paths_total"], 2)
        self.assertGreaterEqual(r["summary"]["frontend_paths"], 1)

    def test_t7_failure_retry_edge_included(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertTrue(any(e["edge_type"] == "RETRIES" for e in r["edges"]))

    def test_t8_generated_config_dependency_preserved(self):
        x = req()
        x["mutating_callsite_result"]["generated_dependency_findings"] = [{"path": "client/src/abi/addresses.ts", "classification": "GENERATED_DEPENDENCY"}]
        r = synthesize_runtime_paths_v0(x)
        self.assertTrue(any(g["gap_type"] == "GENERATED_CONFIG_DEPENDENCY" for g in r["path_gaps"]))

    def test_t9_commit_mismatch_fail_closed(self):
        x = req()
        x["queue_state_transition_result"]["target_commit"] = "b" * 40
        r = synthesize_runtime_paths_v0(x)
        self.assertIn("target_commit_mismatch", r["reason_codes"])

    def test_t10_incidental_heuristic_queue_edge_does_not_block_static_complete(self):
        x = req()
        x["queue_state_transition_result"]["transitions"][0]["analysis_mode"] = "HEURISTIC"
        x["queue_state_transition_result"]["transitions"][0]["evidence_status"] = "PARTIAL"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")

    def test_t10b_heuristic_address_edge_blocks_static_complete(self):
        x = req()
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertNotEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "PARTIAL")
    def test_t11_no_runtime_execution_proof(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertFalse(r["runtime_execution_verified"])
        self.assertFalse(r["paths"][0]["runtime_execution_verified"])

    def test_t12_broken_expected_path_safely(self):
        x = req()
        x["mutating_callsite_result"]["callsite_results"] = []
        x["expected_paths"] = [{"path_name": "expected validator", "actor_role": "validator"}]
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["path_status"], "BROKEN")


class EvidenceIntegrationT(unittest.TestCase):
    def test_ei_t1_legacy_input_without_graph_preserves_behavior(self):
        legacy = synthesize_runtime_paths_v0(req())
        self.assertEqual(legacy["summary"]["evidence_graph_consumed"], "NO")
        self.assertEqual(legacy["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(legacy["summary"]["paths_complete"], 1)
        self.assertFalse(any("evidence_ids" in g for g in legacy["path_gaps"]))

    def test_ei_t2_config_address_graph_evidence_consumed(self):
        g = evidence_graph(
            normalized_records=[_rec(evidence_id="wser-v0-" + "1" * 32, evidence_status="PARTIAL", analysis_mode="DETERMINISTIC")],
            path_blocker_updates=[{
                "update_id": "wsei-bu-1",
                "gap_type": "ADDRESS_SOURCE_PARTIAL",
                "callsite_id": "wmca-v0-c0001",
                "refinement": "STATIC_ADDRESS_PROVENANCE_LINKED",
                "evidence_ids": ["wser-v0-" + "1" * 32],
                "evidence_status": "PARTIAL",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "YES",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        # Force address gap so consumption is visible
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["summary"]["evidence_graph_consumed"], "YES")
        self.assertTrue(r["paths"][0]["evidence_refs"])
        self.assertEqual(r["paths"][0]["static_evidence_join_mode"], "DETERMINISTIC")
        addr_gaps = [g for g in r["path_gaps"] if g["gap_type"] == "ADDRESS_SOURCE_PARTIAL"]
        self.assertTrue(addr_gaps)
        self.assertEqual(addr_gaps[0].get("refinement"), "STATIC_ADDRESS_PROVENANCE_LINKED")
        self.assertIn("wser-v0-" + "1" * 32, addr_gaps[0]["evidence_ids"])

    def test_ei_t3_generated_config_partial_remains_partial(self):
        nf = _rec(
            evidence_id="wser-v0-" + "2" * 32,
            subject_type="GENERATED_ARTIFACT",
            subject_id="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
            source_file="client/src/abi/addresses.ts",
            generated_dependency="YES",
            analysis_mode="DETERMINISTIC",
        )
        example = _rec(
            evidence_id="wser-v0-" + "3" * 32,
            subject_type="SOURCE_FILE",
            subject_id="client/src/abi/addresses.ts.example",
            relation_type="DECLARES",
            evidence_status="CONFIRMED",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
            source_file="client/src/abi/addresses.ts.example",
            generated_dependency="NO",
        )
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL"), nf, example], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(r["paths"][0]["path_status"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "GENERATED_CONFIG_DEPENDENCY" for g in r["path_gaps"]))
        self.assertTrue(any(g["gap_type"] == "NOT_FOUND_DEPENDENCY" for g in r["path_gaps"]))

    def test_ei_t4_missing_addresses_ts_blocks_complete(self):
        nf = _rec(
            evidence_id="wser-v0-" + "4" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
            generated_dependency="YES",
        )
        g = evidence_graph(
            normalized_records=[_rec(evidence_status="CONFIRMED", analysis_mode="DETERMINISTIC"), nf],
            not_found_records=[nf],
        )
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertNotEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertTrue(any(g["gap_type"] == "NOT_FOUND_DEPENDENCY" for g in r["path_gaps"]))

    def test_ei_t5_deterministic_address_join_removes_address_blocker(self):
        addr = _rec(evidence_id="wser-v0-" + "5" * 32, evidence_status="CONFIRMED", analysis_mode="DETERMINISTIC")
        g = evidence_graph(
            normalized_records=[addr],
            path_blocker_updates=[{
                "update_id": "wsei-bu-addr",
                "gap_type": "ADDRESS_SOURCE_PARTIAL",
                "callsite_id": "wmca-v0-c0001",
                "refinement": "STATIC_ADDRESS_PROVENANCE_LINKED",
                "evidence_ids": ["wser-v0-" + "5" * 32],
                "evidence_status": "CONFIRMED",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "NO",
                "removes_blocker": True,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertFalse(any(g["gap_type"] == "ADDRESS_SOURCE_PARTIAL" for g in r["path_gaps"]))
        self.assertTrue(r["paths"][0].get("evidence_refs"))

    def test_ei_t6_heuristic_join_preserves_human_review(self):
        # No callsite_id / file+line match → heuristic symbol join
        heur = _rec(
            evidence_id="wser-v0-" + "6" * 32,
            callsite_id="",
            source_file="other.ts",
            line_start=99,
            source_symbol="sendTransaction",
            from_entity={"entity_type": "CALLSITE", "entity_id": "x", "file": "other.ts", "line_start": 99, "line_end": 99, "symbol": "sendTransaction"},
            evidence_status="PARTIAL",
            analysis_mode="HEURISTIC",
            human_review_required="YES",
        )
        g = evidence_graph(normalized_records=[heur])
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["callsite_results"][0]["callsite_id"] = "wmca-v0-c9999"
        x["mutating_callsite_result"]["callsite_results"][0]["file"] = "nomatch.ts"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["human_review_required"], "YES")
        self.assertEqual(r["paths"][0]["static_evidence_join_mode"], "HEURISTIC")
        self.assertTrue(any(g["gap_type"] == "CALLER_CHAIN_HEURISTIC" for g in r["path_gaps"]))

    def test_ei_t7_conflict_blocks_completion(self):
        conf = _rec(
            evidence_id="wser-v0-" + "7" * 32,
            subject_type="OTHER",
            subject_id="conflict-1",
            relation_type="CONFLICTS_WITH",
            evidence_status="CONFLICT",
            orphan_type="PROVENANCE_CONFLICTS",
            callsite_id="",
            analysis_mode="DETERMINISTIC",
        )
        g = evidence_graph(
            normalized_records=[_rec(evidence_status="CONFIRMED"), conf],
            conflicts=[conf],
            path_blocker_updates=[{
                "update_id": "wsei-bu-c",
                "gap_type": "ADDRESS_SOURCE_CONFLICT",
                "callsite_id": "",
                "refinement": "STATIC_CONFLICT_PRESERVED",
                "evidence_ids": ["wser-v0-" + "7" * 32],
                "evidence_status": "CONFLICT",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "YES",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(r["paths"][0]["path_status"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "PROVENANCE_CONFLICT" for g in r["path_gaps"]))
        self.assertGreaterEqual(r["summary"]["conflict_blocked_paths"], 1)

    def test_ei_t8_not_found_blocks_completion(self):
        nf = _rec(
            evidence_id="wser-v0-" + "8" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
            generated_dependency="YES",
        )
        g = evidence_graph(normalized_records=[_rec(), nf], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(r["paths"][0]["path_status"], "PARTIAL")
        nf_gaps = [g for g in r["path_gaps"] if g["gap_type"] == "NOT_FOUND_DEPENDENCY"]
        self.assertTrue(nf_gaps)
        self.assertNotEqual(nf_gaps[0].get("refinement"), "UNKNOWN")
        self.assertGreaterEqual(r["summary"]["not_found_blocked_paths"], 1)

    def test_ei_t9_queue_evidence_attached_to_path(self):
        q = _rec(
            evidence_id="wser-v0-" + "9" * 32,
            subject_type="QUEUE_STATE",
            subject_id="TxQueue",
            relation_type="TRANSITIONS_TO",
            orphan_type="QUEUE_TRANSITIONS",
            evidence_status="CONFIRMED",
            analysis_mode="DETERMINISTIC",
            source_file="svc.ts",
            line_start=40,
            callsite_id="",
        )
        g = evidence_graph(
            normalized_records=[_rec(evidence_status="PARTIAL"), q],
            path_blocker_updates=[{
                "update_id": "wsei-bu-q",
                "gap_type": "QUEUE_TRANSITION_DETAIL",
                "callsite_id": "",
                "refinement": "QUEUE_EVIDENCE_NORMALIZED",
                "evidence_ids": ["wser-v0-" + "9" * 32],
                "evidence_status": "CONFIRMED",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "NO",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        x["queue_state_transition_result"]["summary"] = {"partial_findings": 1, "unresolved_count": 1}
        r = synthesize_runtime_paths_v0(x)
        self.assertTrue(r["paths"][0].get("queue_evidence_ids"))
        self.assertIn("wser-v0-" + "9" * 32, r["paths"][0]["queue_evidence_ids"])

    def test_ei_t10_mutating_callsite_evidence_attached(self):
        m = _rec(
            evidence_id="wser-v0-" + "d" * 32,
            producer_module="weaver-mutating-callsite-analyzer-v0",
            subject_type="CALLSITE",
            relation_type="SUBMITS_TO",
            orphan_type="MUTATING_CALLSITES",
            evidence_status="PARTIAL",
            analysis_mode="HEURISTIC",
        )
        g = evidence_graph(normalized_records=[m, _rec(evidence_id="wser-v0-" + "e" * 32, evidence_status="PARTIAL")])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertTrue(r["paths"][0].get("mutating_evidence_ids"))
        self.assertIn("wser-v0-" + "d" * 32, r["paths"][0]["mutating_evidence_ids"])

    def test_ei_t11_evidence_references_remain_traceable(self):
        eid = "wser-v0-" + "f" * 32
        g = evidence_graph(normalized_records=[_rec(evidence_id=eid, evidence_status="PARTIAL")])
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertIn(eid, r["paths"][0]["evidence_refs"])
        self.assertTrue(any(eid in (g.get("evidence_ids") or []) for g in r["path_gaps"]))
        self.assertEqual(r["static_evidence_graph_result_id"], g["result_id"])

    def test_ei_t12_no_automatic_promotion_partial_to_complete(self):
        # PARTIAL address evidence must not promote an otherwise-incomplete address gap path to COMPLETE
        g = evidence_graph(
            normalized_records=[_rec(evidence_status="PARTIAL", analysis_mode="DETERMINISTIC")],
            path_blocker_updates=[{
                "update_id": "wsei-bu-p",
                "gap_type": "ADDRESS_SOURCE_PARTIAL",
                "callsite_id": "wmca-v0-c0001",
                "refinement": "STATIC_ADDRESS_PROVENANCE_LINKED",
                "evidence_ids": ["wser-v0-" + "a" * 32],
                "evidence_status": "PARTIAL",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "YES",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["path_status"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "ADDRESS_SOURCE_PARTIAL" for g in r["path_gaps"]))

    def test_ei_t13_deterministic_signer_join_removes_signer_blocker(self):
        sig = _rec(
            evidence_id="wser-v0-" + "s" * 32,
            subject_type="CALLSITE",
            subject_id="wmca-v0-c0001",
            relation_type="USES_SIGNER",
            to_entity={"entity_type": "SIGNER", "entity_id": "sig1", "file": "", "line_start": None, "line_end": None, "symbol": ""},
            evidence_status="CONFIRMED",
            analysis_mode="DETERMINISTIC",
            orphan_type="MUTATING_CALLSITE_SIGNER_REFINEMENTS",
            human_review_required="NO",
            limitations=["removes_signer_blocker=YES", "Capability ≠ Authority"],
        )
        g = evidence_graph(
            normalized_records=[sig],
            path_blocker_updates=[{
                "update_id": "wsei-bu-sig",
                "gap_type": "SIGNER_SOURCE_PARTIAL",
                "callsite_id": "wmca-v0-c0001",
                "refinement": "STATIC_SIGNER_PROVENANCE_LINKED",
                "evidence_ids": ["wser-v0-" + "s" * 32],
                "evidence_status": "CONFIRMED",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "NO",
                "removes_blocker": True,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["signer_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["signer_source"] = "unknown signer source"
        r = synthesize_runtime_paths_v0(x)
        self.assertFalse(any(g["gap_type"] == "SIGNER_SOURCE_PARTIAL" for g in r["path_gaps"]))

    def test_ei_t14_remaining_blockers_prevent_complete_after_signer_clear(self):
        sig = _rec(
            evidence_id="wser-v0-" + "t" * 32,
            evidence_status="CONFIRMED",
            analysis_mode="DETERMINISTIC",
            orphan_type="MUTATING_CALLSITE_SIGNER_REFINEMENTS",
            relation_type="USES_SIGNER",
            limitations=["removes_signer_blocker=YES"],
        )
        g = evidence_graph(
            normalized_records=[sig],
            path_blocker_updates=[{
                "update_id": "wsei-bu-sig2",
                "gap_type": "SIGNER_SOURCE_PARTIAL",
                "callsite_id": "wmca-v0-c0001",
                "refinement": "STATIC_SIGNER_PROVENANCE_LINKED",
                "evidence_ids": ["wser-v0-" + "t" * 32],
                "evidence_status": "CONFIRMED",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "NO",
                "removes_blocker": True,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["signer_sources_mapped"] = "YES"
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        x["mutating_callsite_result"]["generated_dependency_findings"] = [
            {"path": "client/src/abi/addresses.ts", "classification": "GENERATED_DEPENDENCY"}
        ]
        r = synthesize_runtime_paths_v0(x)
        self.assertFalse(any(g["gap_type"] == "SIGNER_SOURCE_PARTIAL" for g in r["path_gaps"]))
        self.assertNotEqual(r["paths"][0]["path_status"], "COMPLETE")

    def test_ei_t15_deterministic_callgraph_clears_caller_chain_not_complete(self):
        cg = _rec(
            evidence_id="wser-v0-" + "g" * 32,
            producer_module="weaver-static-callgraph-linker-v0",
            subject_type="CALLSITE",
            relation_type="CALLS",
            orphan_type="CALLSITE_ANCESTRY_REFINEMENTS",
            evidence_status="CONFIRMED",
            analysis_mode="DETERMINISTIC",
            human_review_required="NO",
            limitations=["removes_caller_chain_blocker=YES", "mutating callsite ancestry from static callgraph"],
        )
        addr = _rec(
            evidence_id="wser-v0-" + "h" * 32,
            evidence_status="PARTIAL",
            analysis_mode="HEURISTIC",
            orphan_type="MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS",
        )
        g = evidence_graph(
            normalized_records=[cg, addr],
            path_blocker_updates=[{
                "update_id": "wsei-bu-cg",
                "gap_type": "CALLER_CHAIN_HEURISTIC",
                "callsite_id": "wmca-v0-c0001",
                "refinement": "STATIC_CALLGRAPH_ANCESTRY_LINKED",
                "evidence_ids": ["wser-v0-" + "g" * 32],
                "evidence_status": "CONFIRMED",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "NO",
                "removes_blocker": True,
                "refines_blocker": True,
            }],
        )
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertFalse(any(gap["gap_type"] == "CALLER_CHAIN_HEURISTIC" for gap in r["path_gaps"]))
        self.assertNotEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(r["paths"][0]["human_review_required"], "YES")
        self.assertEqual(r["summary"].get("caller_chain_heuristic_blocker_paths", -1), 0)


def _conflict_rec(**kw):
    """Provenance conflict evidence record for attach tests."""
    base = {
        "schema_version": "weaver-static-evidence-record-v0",
        "evidence_id": kw.pop("evidence_id", "wser-v0-" + "c" * 32),
        "producer_module": "weaver-config-address-provenance-analyzer-v0",
        "producer_version": "v0",
        "target_commit": "a" * 40,
        "subject_type": "OTHER",
        "subject_id": kw.pop("subject_id", "wcap-v0-x9999"),
        "relation_type": "CONFLICTS_WITH",
        "from_entity": {"entity_type": "OTHER", "entity_id": "conflict", "file": "", "line_start": None, "line_end": None, "symbol": ""},
        "to_entity": kw.pop(
            "to_entity",
            {"entity_type": "OTHER", "entity_id": "conflict-sources", "file": "", "line_start": None, "line_end": None, "symbol": ""},
        ),
        "source_file": "",
        "line_start": None,
        "line_end": None,
        "source_symbol": "",
        "analysis_mode": "DETERMINISTIC",
        "evidence_status": "CONFLICT",
        "chain_context": kw.pop("chain_context", "UNKNOWN"),
        "contract_name": kw.pop("contract_name", ""),
        "callsite_id": kw.pop("callsite_id", ""),
        "config_key": "",
        "generated_dependency": "NO",
        "human_review_required": "YES",
        "confidence_boundary": "STATIC_PROVENANCE",
        "limitations": ["RUNTIME_TARGET_AMBIGUITY", "same_contract_multiple_addresses"],
        "orphan_type": "PROVENANCE_CONFLICTS",
    }
    base.update(kw)
    return base


def _addr_source(**kw):
    sid = kw.pop("source_id", "wcap-v0-a9999")
    contract = kw.pop("contract_name", "CawActionsArchive")
    return _rec(
        evidence_id=kw.pop("evidence_id", "wser-v0-" + "e" * 32),
        subject_type="ADDRESS_SOURCE",
        subject_id=sid,
        source_record_id=sid,
        relation_type="USES_ADDRESS",
        orphan_type="ADDRESS_SOURCES",
        callsite_id="",
        contract_name=contract,
        config_key=kw.pop("config_key", contract),
        source_file=kw.pop("source_file", "client/src/abi/deployments.ts"),
        source_symbol=kw.pop("source_symbol", "deployments"),
        to_entity={
            "entity_type": "CONTRACT",
            "entity_id": contract,
            "file": "",
            "line_start": None,
            "line_end": None,
            "symbol": "",
        },
        **kw,
    )


def _consumer(**kw):
    return _rec(
        evidence_id=kw.pop("evidence_id", "wser-v0-" + "u" * 32),
        subject_type="ADDRESS_CONSUMER",
        subject_id=kw.pop("subject_id", "wcap-v0-u9999"),
        relation_type="USES_ADDRESS",
        orphan_type="ADDRESS_CONSUMERS",
        callsite_id="",
        contract_name=kw.pop(
            "contract_name",
            "CAW_ACTIONS_ADDRESS, CAW_ACTIONS_ARCHIVE_ADDRESS, CAW_CHALLENGE_RELAY_ADDRESS",
        ),
        source_file=kw.pop("source_file", "client/src/services/ValidatorService/index.ts"),
        **kw,
    )


class ConflictPropagationT(unittest.TestCase):
    def test_cp_t1_repo_level_conflict_does_not_attach_to_every_path(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "1" * 32,
            subject_id="wcap-v0-x0001",
            contract_name="",
            to_entity={
                "entity_type": "OTHER",
                "entity_id": "wcap-v0-a0001",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        addr = _addr_source(
            evidence_id="wser-v0-" + "2" * 32,
            source_id="wcap-v0-a0001",
            contract_name="UnrelatedToken",
            config_key="UnrelatedToken",
            source_file="other/deployments.ts",
        )
        g = evidence_graph(
            normalized_records=[_rec(), conf, addr],
            conflicts=[conf],
            path_blocker_updates=[{
                "update_id": "wsei-bu-c1",
                "gap_type": "ADDRESS_SOURCE_CONFLICT",
                "callsite_id": "",
                "refinement": "STATIC_CONFLICT_PRESERVED",
                "evidence_ids": ["wser-v0-" + "1" * 32],
                "evidence_status": "CONFLICT",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "YES",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertFalse(any(gap["gap_type"] == "PROVENANCE_CONFLICT" for gap in r["path_gaps"]))
        self.assertEqual(r["summary"]["conflict_blocked_paths"], 0)
        self.assertEqual(len(g["conflicts"]), 1)

    def test_cp_t2_exact_subject_match_attaches_conflict(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "3" * 32,
            subject_id="wmca-v0-c0001",
            contract_name="",
        )
        g = evidence_graph(normalized_records=[_rec()], conflicts=[conf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertTrue(any(gap["gap_type"] == "PROVENANCE_CONFLICT" for gap in r["path_gaps"]))
        self.assertIn("wser-v0-" + "3" * 32, r["paths"][0]["conflict_evidence_ids"])

    def test_cp_t3_contract_name_match_attaches_conflict(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "4" * 32,
            subject_id="wcap-v0-x0003",
            contract_name="",
            to_entity={
                "entity_type": "OTHER",
                "entity_id": "wcap-v0-a0038,wcap-v0-a0042",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        a1 = _addr_source(evidence_id="wser-v0-" + "5" * 32, source_id="wcap-v0-a0038", contract_name="CawActionsArchive")
        a2 = _addr_source(evidence_id="wser-v0-" + "6" * 32, source_id="wcap-v0-a0042", contract_name="CawActionsArchive")
        cons = _consumer(
            evidence_id="wser-v0-" + "7" * 32,
            source_file="svc.ts",
            contract_name="CAW_ACTIONS_ARCHIVE_ADDRESS",
        )
        g = evidence_graph(normalized_records=[_rec(), conf, a1, a2, cons], conflicts=[conf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertTrue(any(gap["gap_type"] == "PROVENANCE_CONFLICT" for gap in r["path_gaps"]))
        self.assertGreaterEqual(r["summary"]["conflict_blocked_paths"], 1)

    def test_cp_t4_callsite_linked_conflict_attaches(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "8" * 32,
            subject_id="wcap-v0-x0099",
            callsite_id="wmca-v0-c0001",
            contract_name="",
        )
        g = evidence_graph(normalized_records=[_rec()], conflicts=[conf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertIn("wser-v0-" + "8" * 32, r["paths"][0]["conflict_evidence_ids"])

    def test_cp_t5_chain_context_mismatch_does_not_attach(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "9" * 32,
            subject_id="wmca-v0-c0001",
            callsite_id="wmca-v0-c0001",
            chain_context="base-sepolia",
            contract_name="Caw",
        )
        path_rec = _rec(chain_context="mainnet")
        g = evidence_graph(normalized_records=[path_rec], conflicts=[conf])
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["callsite_results"][0]["chain_source"] = "mainnet"
        r = synthesize_runtime_paths_v0(x)
        self.assertNotIn("wser-v0-" + "9" * 32, r["paths"][0].get("conflict_evidence_ids") or [])
        self.assertFalse(any(gap["gap_type"] == "PROVENANCE_CONFLICT" for gap in r["path_gaps"]))

    def test_cp_t6_unrelated_path_does_not_receive_archive_conflict(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "a" * 32,
            subject_id="wcap-v0-x0003",
            to_entity={
                "entity_type": "OTHER",
                "entity_id": "wcap-v0-a0038",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        addr = _addr_source(
            evidence_id="wser-v0-" + "b" * 32,
            source_id="wcap-v0-a0038",
            contract_name="CawActionsArchive",
            source_file="client/src/abi/deployments.ts",
        )
        # Frontend path with no Archive consumer / file / contract relation
        fe = _rec(
            evidence_id="wser-v0-" + "d" * 32,
            contract_name="Caw",
            source_file="fe.tsx",
            callsite_id="wmca-v0-c0001",
        )
        g = evidence_graph(normalized_records=[fe, conf, addr], conflicts=[conf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertNotIn("wser-v0-" + "a" * 32, r["paths"][0].get("conflict_evidence_ids") or [])

    def test_cp_t7_unrelated_path_does_not_receive_relay_conflict(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "e" * 32,
            subject_id="wcap-v0-x0004",
            to_entity={
                "entity_type": "OTHER",
                "entity_id": "wcap-v0-a0039",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        addr = _addr_source(
            evidence_id="wser-v0-" + "f" * 32,
            source_id="wcap-v0-a0039",
            contract_name="CawChallengeRelay",
            config_key="CawChallengeRelay",
            source_file="client/src/abi/deployments.ts",
        )
        fe = _rec(
            evidence_id="wser-v0-" + "0" * 32,
            contract_name="Caw",
            source_file="fe.tsx",
            callsite_id="wmca-v0-c0001",
        )
        g = evidence_graph(normalized_records=[fe, conf, addr], conflicts=[conf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertNotIn("wser-v0-" + "e" * 32, r["paths"][0].get("conflict_evidence_ids") or [])

    def test_cp_t8_zero_source_conflict_preserved_but_not_globally_blocking(self):
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "z" * 32,
            subject_id="wcap-v0-x0002",
            contract_name="",
            to_entity={
                "entity_type": "OTHER",
                "entity_id": "conflict-sources",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        g = evidence_graph(
            normalized_records=[_rec()],
            conflicts=[conf],
            path_blocker_updates=[{
                "update_id": "wsei-bu-z",
                "gap_type": "ADDRESS_SOURCE_CONFLICT",
                "callsite_id": "",
                "refinement": "STATIC_CONFLICT_PRESERVED",
                "evidence_ids": ["wser-v0-" + "z" * 32],
                "evidence_status": "CONFLICT",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "YES",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(len(g["conflicts"]), 1)
        self.assertEqual(r["summary"]["conflict_blocked_paths"], 0)
        self.assertNotIn("wser-v0-" + "z" * 32, r["paths"][0].get("conflict_evidence_ids") or [])

    def test_cp_t9_target_commit_mismatch_fails_closed(self):
        conf = _conflict_rec(evidence_id="wser-v0-" + "m" * 32, subject_id="wmca-v0-c0001")
        g = evidence_graph(normalized_records=[_rec()], conflicts=[conf])
        g["target_commit"] = "b" * 40
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertTrue(r.get("reason_codes"))
        self.assertIn("static_evidence_graph_commit_mismatch", r["reason_codes"])

    def test_cp_t10_conflict_record_remains_preserved(self):
        confs = [
            _conflict_rec(evidence_id="wser-v0-" + "p" * 32, subject_id="wcap-v0-x0001"),
            _conflict_rec(evidence_id="wser-v0-" + "q" * 32, subject_id="wcap-v0-x0002"),
            _conflict_rec(evidence_id="wser-v0-" + "r" * 32, subject_id="wcap-v0-x0003", contract_name="CawActionsArchive"),
            _conflict_rec(evidence_id="wser-v0-" + "s" * 32, subject_id="wcap-v0-x0004", contract_name="CawChallengeRelay"),
        ]
        g = evidence_graph(normalized_records=[_rec()] + confs, conflicts=confs)
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(len(g["conflicts"]), 4)
        self.assertEqual(r["static_evidence_graph_result_id"], g["result_id"])

    def test_cp_t11_legacy_without_evidence_graph_backward_compatible(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(r["summary"]["evidence_graph_consumed"], "NO")
        self.assertEqual(r["summary"]["conflict_blocked_paths"], 0)
        self.assertEqual(validate_runtime_path_synthesizer_result_v0(r), [])

    def test_cp_t12_no_complete_promotion_from_conflict_attribution_change(self):
        # Zero-source conflict no longer blocks, but addresses.ts NOT_FOUND remains
        # when the path actually depends on the generated artifact.
        conf = _conflict_rec(
            evidence_id="wser-v0-" + "n" * 32,
            subject_id="wcap-v0-x0002",
            to_entity={
                "entity_type": "OTHER",
                "entity_id": "conflict-sources",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        nf = _rec(
            evidence_id="wser-v0-" + "o" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
            generated_dependency="YES",
        )
        consumer = _rec(
            evidence_id="wser-v0-" + "u" * 32,
            subject_id="svc.ts",
            source_file="svc.ts",
            relation_type="CONSUMES",
            orphan_type="ADDRESS_CONSUMERS",
            callsite_id="",
            to_entity={
                "entity_type": "MODULE",
                "entity_id": "../../abi/addresses",
                "file": "client/src/abi/addresses.ts",
                "line_start": 1,
                "line_end": 1,
                "symbol": "",
            },
            evidence_status="PARTIAL",
        )
        g = evidence_graph(
            normalized_records=[_rec(evidence_status="PARTIAL"), conf, nf, consumer],
            conflicts=[conf],
            not_found_records=[nf],
        )
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertNotEqual(r["paths"][0]["path_status"], "COMPLETE")
        self.assertEqual(r["summary"]["paths_complete"], 0)
        self.assertTrue(any(gap["gap_type"] == "NOT_FOUND_DEPENDENCY" for gap in r["path_gaps"]))


class NotFoundPropagationT(unittest.TestCase):
    """Subject-scoped NOT_FOUND / generated-config attach (v9)."""

    def test_nf_t1_unrelated_not_found_does_not_block_path(self):
        nf = _rec(
            evidence_id="wser-v0-" + "1" * 32,
            subject_id="wqsta-v0-nf0001",
            source_file="",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="CONCURRENCY_CONTROLS",
            callsite_id="",
            generated_dependency="NO",
        )
        g = evidence_graph(normalized_records=[_rec()], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(r["summary"]["not_found_blocked_paths"], 0)
        self.assertNotIn("wser-v0-" + "1" * 32, r["paths"][0].get("not_found_evidence_ids") or [])

    def test_nf_t2_exact_generated_artifact_dependency_blocks_path(self):
        nf = _rec(
            evidence_id="wser-v0-" + "2" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
            generated_dependency="YES",
        )
        consumer = _rec(
            evidence_id="wser-v0-" + "c" * 32,
            source_file="svc.ts",
            relation_type="CONSUMES",
            orphan_type="ADDRESS_CONSUMERS",
            callsite_id="",
            to_entity={
                "entity_type": "MODULE",
                "entity_id": "../../abi/addresses",
                "file": "client/src/abi/addresses.ts",
                "line_start": 1,
                "line_end": 1,
                "symbol": "CAW_ADDRESS",
            },
            evidence_status="PARTIAL",
        )
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL"), nf, consumer], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertGreaterEqual(r["summary"]["not_found_blocked_paths"], 1)
        self.assertTrue(any(g["gap_type"] == "NOT_FOUND_DEPENDENCY" for g in r["path_gaps"]))
        self.assertIn("wser-v0-" + "2" * 32, r["paths"][0].get("not_found_evidence_ids") or [])

    def test_nf_t3_derived_not_found_does_not_duplicate_root_blocker_summary(self):
        root = _rec(
            evidence_id="wser-v0-" + "r" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        derived = _rec(
            evidence_id="wser-v0-" + "d" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts.example",
            relation_type="DEPENDS_ON_GENERATED_ARTIFACT",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        consumer = _rec(
            evidence_id="wser-v0-" + "c" * 32,
            source_file="svc.ts",
            relation_type="CONSUMES",
            orphan_type="ADDRESS_CONSUMERS",
            callsite_id="",
            to_entity={
                "entity_type": "MODULE",
                "entity_id": "../../abi/addresses",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        g = evidence_graph(
            normalized_records=[_rec(evidence_status="PARTIAL"), root, derived, consumer],
            not_found_records=[root, derived],
            path_blocker_updates=[{
                "update_id": "wsei-bu-gen",
                "gap_type": "GENERATED_CONFIG_DEPENDENCY",
                "callsite_id": "",
                "refinement": "GENERATED_ARTIFACT_ABSENT_WITH_PROVENANCE",
                "evidence_ids": ["wser-v0-" + "d" * 32],
                "evidence_status": "NOT_FOUND",
                "analysis_mode": "DETERMINISTIC",
                "human_review_required": "YES",
                "removes_blocker": False,
                "refines_blocker": True,
            }],
        )
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        nf_gaps = [g for g in r["path_gaps"] if g["gap_type"] == "NOT_FOUND_DEPENDENCY"]
        self.assertEqual(len(nf_gaps), 1)
        self.assertIn("wser-v0-" + "r" * 32, nf_gaps[0].get("evidence_ids") or [])
        self.assertNotIn("wser-v0-" + "d" * 32, nf_gaps[0].get("evidence_ids") or [])
        gen = [g for g in r["path_gaps"] if g["gap_type"] == "GENERATED_CONFIG_DEPENDENCY"]
        self.assertTrue(gen)
        self.assertEqual(gen[0].get("root_cause"), "NOT_FOUND_DEPENDENCY")

    def test_nf_t4_address_consumer_dependency_attaches_correctly(self):
        nf = _rec(
            evidence_id="wser-v0-" + "4" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        consumer = _rec(
            evidence_id="wser-v0-" + "e" * 32,
            source_file="svc.ts",
            relation_type="CONSUMES",
            orphan_type="ADDRESS_CONSUMERS",
            callsite_id="",
            config_key="CAW_NAMES_L2_ADDRESS",
            to_entity={
                "entity_type": "MODULE",
                "entity_id": "../../abi/addresses",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL"), nf, consumer], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertGreaterEqual(r["summary"]["not_found_blocked_paths"], 1)
        self.assertIn("wser-v0-" + "4" * 32, r["paths"][0].get("not_found_evidence_ids") or [])

    def test_nf_t5_chain_context_mismatch_does_not_attach(self):
        nf = _rec(
            evidence_id="wser-v0-" + "5" * 32,
            subject_id="wmca-v0-c0001",
            source_file="other.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="SIGNER_SOURCE_STATUS",
            callsite_id="wmca-v0-c0001",
            chain_context="testnet",
        )
        path_rec = _rec(chain_context="mainnet", evidence_status="PARTIAL")
        g = evidence_graph(normalized_records=[path_rec], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertNotIn("wser-v0-" + "5" * 32, r["paths"][0].get("not_found_evidence_ids") or [])

    def test_nf_t6_signer_not_found_only_attaches_to_signer_dependent_path(self):
        nf_a = _rec(
            evidence_id="wser-v0-" + "6" * 32,
            subject_id="wmca-v0-c0001",
            source_file="svc.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="SIGNER_SOURCE_STATUS",
            callsite_id="wmca-v0-c0001",
            generated_dependency="NO",
        )
        nf_b = _rec(
            evidence_id="wser-v0-" + "7" * 32,
            subject_id="wmca-v0-c0099",
            source_file="other.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="SIGNER_SOURCE_STATUS",
            callsite_id="wmca-v0-c0099",
            generated_dependency="NO",
        )
        g = evidence_graph(normalized_records=[_rec()], not_found_records=[nf_a, nf_b])
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["signer_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["signer_source"] = "unknown signer source"
        r = synthesize_runtime_paths_v0(x)
        eids = r["paths"][0].get("not_found_evidence_ids") or []
        self.assertIn("wser-v0-" + "6" * 32, eids)
        self.assertNotIn("wser-v0-" + "7" * 32, eids)

    def test_nf_t7_missing_generated_artifact_remains_preserved(self):
        nf = _rec(
            evidence_id="wser-v0-" + "8" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        g = evidence_graph(normalized_records=[_rec()], not_found_records=[nf])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertEqual(len(g["not_found_records"]), 1)
        self.assertEqual(r["static_evidence_graph_result_id"], g["result_id"])

    def test_nf_t8_alternate_static_source_not_blocked_solely_by_addresses_ts(self):
        nf = _rec(
            evidence_id="wser-v0-" + "9" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        # Path resolves via deployments.ts only — no addresses consumer.
        addr = _rec(
            evidence_id="wser-v0-" + "a" * 32,
            relation_type="RESOLVES_ADDRESS",
            orphan_type="MUTATING_CALLSITE_ADDRESS_SOURCE_REFINEMENTS",
            evidence_status="CONFIRMED",
            analysis_mode="DETERMINISTIC",
            generated_dependency="NO",
            to_entity={
                "entity_type": "ADDRESS_SOURCE",
                "entity_id": "deployments.ts::Caw",
                "file": "client/src/abi/deployments.ts",
                "line_start": 10,
                "line_end": 10,
                "symbol": "Caw",
            },
        )
        g = evidence_graph(normalized_records=[addr], not_found_records=[nf])
        x = req(static_evidence_graph=g)
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "deployments.ts literal"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["summary"]["not_found_blocked_paths"], 0)
        self.assertFalse(any(g["gap_type"] == "NOT_FOUND_DEPENDENCY" for g in r["path_gaps"]))

    def test_nf_t9_target_commit_mismatch_fails_closed(self):
        nf = _rec(
            evidence_id="wser-v0-" + "b" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
        )
        g = evidence_graph(normalized_records=[_rec()], not_found_records=[nf])
        g["target_commit"] = "b" * 40
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        self.assertIn("static_evidence_graph_commit_mismatch", r["reason_codes"])

    def test_nf_t10_legacy_without_evidence_graph_remains_compatible(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertEqual(r["summary"]["evidence_graph_consumed"], "NO")
        self.assertEqual(r["summary"]["not_found_blocked_paths"], 0)
        self.assertEqual(validate_runtime_path_synthesizer_result_v0(r), [])

    def test_nf_t11_no_path_promoted_to_complete_merely_by_propagation_refinement(self):
        nf = _rec(
            evidence_id="wser-v0-" + "f" * 32,
            subject_id="wqsta-v0-nf0099",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="CONCURRENCY_CONTROLS",
            callsite_id="",
        )
        # Unrelated NF cleared, but address still partial / unknown → not COMPLETE.
        x = req(static_evidence_graph=evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL")], not_found_records=[nf]))
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["summary"]["paths_complete"], 0)
        self.assertNotEqual(r["paths"][0]["path_status"], "COMPLETE")

    def test_nf_t12_root_derived_reporting_remains_traceable(self):
        root = _rec(
            evidence_id="wser-v0-" + "g" * 32,
            subject_id="client/src/abi/addresses.ts",
            source_file="client/src/abi/addresses.ts",
            relation_type="NOT_FOUND_FOR",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        derived = _rec(
            evidence_id="wser-v0-" + "h" * 32,
            subject_id="wcap-v0-g0001",
            source_file="client/src/abi/addresses.ts.example",
            relation_type="DEPENDS_ON_GENERATED_ARTIFACT",
            evidence_status="NOT_FOUND",
            orphan_type="GENERATED_ARTIFACTS",
            callsite_id="",
        )
        consumer = _rec(
            evidence_id="wser-v0-" + "i" * 32,
            source_file="svc.ts",
            relation_type="CONSUMES",
            orphan_type="ADDRESS_CONSUMERS",
            to_entity={
                "entity_type": "MODULE",
                "entity_id": "../../abi/addresses",
                "file": "",
                "line_start": None,
                "line_end": None,
                "symbol": "",
            },
        )
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL"), root, derived, consumer], not_found_records=[root, derived])
        r = synthesize_runtime_paths_v0(req(static_evidence_graph=g))
        nf_gaps = [g for g in r["path_gaps"] if g["gap_type"] == "NOT_FOUND_DEPENDENCY"]
        gen = [g for g in r["path_gaps"] if g["gap_type"] == "GENERATED_CONFIG_DEPENDENCY"]
        self.assertTrue(nf_gaps)
        self.assertTrue(gen)
        self.assertEqual(gen[0].get("root_cause"), "NOT_FOUND_DEPENDENCY")
        self.assertTrue(any("root_not_found_subject=client/src/abi/addresses.ts" in lim for lim in (nf_gaps[0].get("limitations") or [])))
        self.assertTrue(any("derived_from_root=NOT_FOUND_DEPENDENCY" in lim for lim in (gen[0].get("limitations") or [])))


class StaticCompletionAxisT(unittest.TestCase):
    """STATIC_PATH_COMPLETE axis split + path-SoT clearance regression tests."""

    def _sot(self, path_id="wrps-v0-p0001", target="CawActionsArchive", classification="PATH_SOT_DUAL_VALID", conflict="CLEARED"):
        return {
            "schema_version": "weaver-path-specific-sot-evidence-v0",
            "global_canonical_status": "UNRESOLVED",
            "multi_generation_status": "OVERLAY_INGESTED_FIXTURE",
            "records": [{
                "path_id": path_id,
                "target_contract_role": target,
                "supported_addresses": {"A": "0x1", "B": "0x2"},
                "generation_family": "A_AND_B_SEQUENTIAL_COEXISTENCE",
                "source_artifact_commit": {"A": "a" * 40, "B": "b" * 40},
                "live_bytecode_binding_classification": {"A": "IMMUTABLE_AWARE_MATCH"},
                "dual_valid": classification == "PATH_SOT_DUAL_VALID",
                "conflict_status": conflict,
                "path_specific_sot_classification": classification,
                "evidence_references": ["s7-fixture"],
                "global_canonical_required": False,
            }],
        }

    def test_sc1_global_canonical_unresolved_path_sot_allows_static_complete(self):
        sot = self._sot()
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL")])
        x = req(static_evidence_graph=g, path_specific_sot_evidence=sot)
        # Force address/authority/retry informational gaps in base evidence
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        x["mutating_callsite_result"]["callsite_results"][0]["authority_status"] = "PARTIAL"
        r = synthesize_runtime_paths_v0(x)
        p = r["paths"][0]
        self.assertEqual(p["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(p["path_status"], "COMPLETE")
        self.assertEqual(p["SOT_STATUS"], "PATH_SPECIFIC_DUAL_VALID")
        self.assertEqual(p["address_axes"]["GLOBAL_CANONICAL_STATUS"], "UNRESOLVED")
        self.assertEqual(p["address_axes"]["PATH_USABLE_ADDRESS_STATUS"], "ESTABLISHED")

    def test_sc2_path_sot_unresolved_static_partial(self):
        x = req()
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "PARTIAL")
        self.assertEqual(r["paths"][0]["SOT_STATUS"], "NOT_ESTABLISHED")

    def test_sc3_authority_partial_does_not_block_static_complete(self):
        x = req()
        x["mutating_callsite_result"]["callsite_results"][0]["authority_status"] = "PARTIAL"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(r["paths"][0]["AUTHORITY_STATUS"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "AUTHORITY_CONDITION_PARTIAL" for g in r["path_gaps"]))

    def test_sc4_runtime_execution_unverified_does_not_block(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(r["paths"][0]["RUNTIME_EXECUTION_STATUS"], "UNVERIFIED")
        self.assertFalse(r["runtime_execution_verified"])

    def test_sc5_runtime_signer_identity_unknown_does_not_block(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertIn(r["paths"][0]["SIGNER_IDENTITY_STATUS"], {
            "PARTIAL", "DYNAMIC_BY_DESIGN_UNRESOLVED", "UNVERIFIED",
        })

    def test_sc6_iw_unsatisfied_does_not_block(self):
        r = synthesize_runtime_paths_v0(req())
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(r["paths"][0]["INDEPENDENT_WITNESS_STATUS"], "NOT_SATISFIED")

    def test_sc7_unresolved_address_conflict_blocks_static_complete(self):
        sot = self._sot(conflict="UNRESOLVED")
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL")])
        x = req(static_evidence_graph=g, path_specific_sot_evidence=sot)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "PROVENANCE_CONFLICT" for g in r["path_gaps"]))

    def test_sc8_unresolved_static_target_blocks(self):
        sot = self._sot(target="MULTI_LITERAL_UNLABELED_CLUSTER")
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL")])
        x = req(static_evidence_graph=g, path_specific_sot_evidence=sot)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "PARTIAL")
        self.assertTrue(any(g["gap_type"] == "STATIC_TARGET_UNRESOLVED" for g in r["path_gaps"]))

    def test_sc9_informational_retry_does_not_block(self):
        x = req()
        x["queue_state_transition_result"]["summary"]["partial_findings"] = 3
        x["queue_state_transition_result"]["summary"]["unresolved_count"] = 2
        r = synthesize_runtime_paths_v0(x)
        self.assertEqual(r["paths"][0]["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertTrue(any(g["gap_type"] == "RETRY_PATH_PARTIAL" for g in r["path_gaps"]))
        self.assertTrue(any(g["gap_type"] == "CONCURRENCY_UNRESOLVED" for g in r["path_gaps"]))

    def test_sc10_dual_valid_without_global_canonical(self):
        sot = self._sot(classification="PATH_SOT_DUAL_VALID")
        g = evidence_graph(normalized_records=[_rec(evidence_status="PARTIAL")])
        x = req(static_evidence_graph=g, path_specific_sot_evidence=sot)
        x["mutating_callsite_result"]["contract_address_sources_mapped"] = "PARTIAL"
        x["mutating_callsite_result"]["callsite_results"][0]["contract_address_source"] = "unknown"
        r = synthesize_runtime_paths_v0(x)
        p = r["paths"][0]
        self.assertEqual(p["STATIC_PATH_STATUS"], "COMPLETE")
        self.assertEqual(p["SOT_STATUS"], "PATH_SPECIFIC_DUAL_VALID")
        self.assertEqual(p["address_axes"]["MULTI_GENERATION_STATUS"], "DUAL_VALID_OVERLAY")
        self.assertNotEqual(p["address_axes"]["GLOBAL_CANONICAL_STATUS"], "BOUND")


if __name__ == "__main__":
    unittest.main()
