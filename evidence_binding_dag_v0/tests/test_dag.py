"""Focused tests for Evidence Binding DAG v0."""

from __future__ import annotations

import copy
import json
import subprocess
import unittest
from collections.abc import Mapping
from pathlib import Path

from audit_lifecycle.epistemic.serialize import canonical_digest
from conducting_receipt_v0.tests.test_receipt import _build as _cr_build
from evidence_binding_dag_v0 import EvidenceBindingDagError, build_evidence_binding_dag
from independent_verification_preflight_v0.tests.test_preflight import (
    _build as _ivp_build,
)
from recovery_execution_receipt_v0.tests.test_receipt import _build as _rer_build
from recovery_preflight_v0.tests.test_preflight import _build as _rp_build
from recovery_preflight_v0.tests.test_preflight import _bundle as _rp_bundle
from tested_envelope_v0.tests.test_envelope import _build as _te_build
from tested_envelope_v0.tests.test_envelope import _bundle as _te_bundle

REPO = Path(__file__).resolve().parents[2]
_LEAF_TYPES = (str, bool, int, float)
_VERDICT_KEYS = (
    "PASS",
    "SAFE",
    "TRUSTED",
    "VERIFIED",
    "RECOVERED",
    "ACCEPTED",
    "HUMAN_REVIEW_ACCEPTED",
)
_ADMISSION_KEYS = (
    "admission_status",
    "independent_evidence_count",
    "structural_candidate",
    "claims_iw_acceptance",
    "claims_independent_witness",
    "human_final",
    "human_final_status",
    "Human Final",
)


class _SplitView(Mapping):
    """Bound iteration is the record. Live lookup is the attack."""

    def __init__(self, bound: dict, live: dict) -> None:
        self._bound = bound
        self._live = live

    def __getitem__(self, key: str):
        return self._live[key]

    def __iter__(self):
        return iter(self._bound)

    def __len__(self) -> int:
        return len(self._bound)

    def items(self):
        return self._bound.items()

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class _SplitDict(dict):
    def __init__(self, bound: dict, live: dict) -> None:
        super().__init__(bound)
        self._live = live

    def __getitem__(self, key: str):
        return self._live[key]

    def get(self, key: str, default=None):
        return self._live.get(key, default)


class _HostileStr(str):
    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return hash("PASS")


class _HostileInt(int):
    def __eq__(self, other: object) -> bool:
        return other is True or int.__eq__(self, other)

    def __hash__(self) -> int:
        return hash(True)


class _Rows(list):
    """Caller-owned list subclass."""


class _Reuse(tuple):
    """Caller-owned tuple subclass."""


class _DupKeys(Mapping):
    def __getitem__(self, key: str):
        return "x"

    def __iter__(self):
        return iter(("nodes",))

    def __len__(self) -> int:
        return 2

    def items(self):
        return [("nodes", []), ("nodes", [{"node_id": "x"}])]


def _expect(test: unittest.TestCase, code: str, fn) -> None:
    with test.assertRaises(EvidenceBindingDagError) as caught:
        fn()
    test.assertEqual(caught.exception.code, code)


def _artifact_body(payload: str = "blob") -> dict:
    return {"payload": payload}


def _artifact_node(node_id: str, body: dict | None = None, **over: object) -> dict:
    record = {
        "node_id": node_id,
        "kind": "ARTIFACT",
        "body": _artifact_body() if body is None else body,
    }
    record.update(over)
    return record


def _external(node_id: str, digest: str, **over: object) -> dict:
    record = {"node_id": node_id, "kind": "EXTERNAL_REF", "digest": digest}
    record.update(over)
    return record


def _hand_rp(**over: object) -> dict:
    body = {
        "schema_version": "recovery_preflight.v0",
        "authority": False,
        "recovered": False,
        "classification": "NOT_RECOVERED",
        "cited_decision": {"claim_id": "AUR-A-001", "decision": "PASS"},
        "limitations": ["restore execution"],
    }
    body.update(over)
    return body


def _hand_te(*, scope_digest: str, file_digest: str, claim_id: str = "AUR-A-001", **over: object) -> dict:
    body = {
        "schema_version": "tested_envelope.v0",
        "authority": False,
        "claim_id": claim_id,
        "artifact_revision": {
            "files": [{"relative_path": "payload.txt", "sha256": file_digest}]
        },
        "source_result": "PASS",
        "result": "PASS",
        "detector_families": ["digest_match"],
        "scope_binding": {"claim_id": claim_id, "scope_digest": scope_digest},
        "exclusions": ["global safety"],
        "unresolved_assumptions": [],
        "missing_observations": [],
    }
    body.update(over)
    return body


def _hand_ivp(
    *,
    file_digest: str,
    source_evidence: str,
    source_input: str,
    independent_evidence: str,
    independent_input: str,
    **over: object,
) -> dict:
    body = {
        "schema_version": "independent_verification_preflight.v0",
        "authority": False,
        "admission_status": "NOT_CONFIGURED",
        "verification_kind": "REPRODUCTION",
        "claim_id": "AUR-A-001",
        "artifact_revision_binding": {
            "files": [{"relative_path": "payload.txt", "sha256": file_digest}]
        },
        "classification": "BOUND_CANDIDATE",
        "structural_candidate": True,
        "source_execution_summary": {
            "execution_id": "run-source",
            "environment_fingerprint": "aa" * 32,
            "evidence_digest": source_evidence,
            "input_digest": source_input,
            "result_token": "PASS",
        },
        "independent_execution_summary": {
            "execution_id": "run-independent",
            "environment_fingerprint": "bb" * 32,
            "evidence_digest": independent_evidence,
            "input_digest": independent_input,
            "result_token": "PASS",
        },
        "limitations": ["admitted independent evidence"],
    }
    body.update(over)
    return body


def _hand_rer(
    *,
    expected_digest: str,
    environment_digest: str,
    iv_digest: str | None = None,
    **over: object,
) -> dict:
    body: dict[str, object] = {
        "schema_version": "recovery_execution_receipt.v0",
        "authority": False,
        "recovered": False,
        "recovery_session_id": "rec-1",
        "target_scope": "ARTIFACT_ONLY",
        "target_artifact_id": "artifact-1",
        "target_environment": {"name": "lab", "environment_digest": environment_digest},
        "pre_state": [],
        "stop": {"stop_id": "stop-1", "result": "OBSERVED_PASS"},
        "isolation": {"isolation_id": "iso-1", "result": "NOT_APPLICABLE"},
        "restore_target": {
            "target_id": "restore-target-1",
            "binding_kind": "content_digest",
            "binding_value": expected_digest,
            "source": "pinned-artifact-store",
            "event_order": 3,
            "body": {"artifact": "pinned-v1"},
            "expected_digest": expected_digest,
        },
        "attempts": [],
        "independent_verification_refs": [],
        "unresolved_risks": [],
        "classification": "NOT_RECOVERED",
        "limitations": ["restore execution"],
    }
    if iv_digest is not None:
        body["independent_verification_refs"] = [
            {
                "ref_id": "iv-1",
                "source_kind": "INDEPENDENT_VERIFICATION_PREFLIGHT",
                "claim": "independent package cited",
                "receipt_digest": iv_digest,
            }
        ]
    body.update(over)
    sealed = {key: value for key, value in body.items() if key != "receipt_digest"}
    body["receipt_digest"] = canonical_digest(sealed)
    return body


def _claim_body(claim_id: str = "CLAIM-1", **over: object) -> dict:
    body = {
        "schema_version": "r4.epistemic.claim.v1",
        "claim_id": claim_id,
        "statement": "bytes are well formed",
        "claim_kind": "FORMAL",
        "epistemic_status": "REPORTED",
        "scope": "unit-test",
        "authority": False,
        "evidence_refs": [],
        "provenance_refs": [],
        "notes": "",
    }
    body.update(over)
    return body


def _receipt_node(node_id: str, body: dict, **over: object) -> dict:
    record = {"node_id": node_id, "kind": "RECEIPT", "body": body}
    record.update(over)
    return record


def _claim_node(node_id: str, body: dict | None = None, **over: object) -> dict:
    record = {
        "node_id": node_id,
        "kind": "CLAIM",
        "body": _claim_body() if body is None else body,
    }
    record.update(over)
    return record


def _build(nodes: list[dict], edges: list[dict] | None = None, **kwargs: object) -> dict:
    record: dict[str, object] = {"nodes": nodes}
    if edges is not None:
        record["edges"] = edges
    return build_evidence_binding_dag(record, **kwargs)


def _complete_te_graph() -> tuple[list[dict], dict, dict]:
    scope_body = {"allowed_write_boundary": ["audit/**"], "policy": {"name": "hash_claim"}}
    file_body = {"blob": "payload-bytes"}
    scope_digest = canonical_digest(scope_body)
    file_digest = canonical_digest(file_body)
    te = _hand_te(scope_digest=scope_digest, file_digest=file_digest)
    nodes = [
        _receipt_node("te-1", te),
        _artifact_node("scope-1", scope_body),
        _artifact_node("file-1", file_body),
    ]
    return nodes, scope_body, file_body


def _assert_plain(test: unittest.TestCase, value, *, key: str | None = None) -> None:
    if value is None or type(value) in _LEAF_TYPES:
        return
    if type(value) is dict:
        for child_key, child in value.items():
            test.assertIs(type(child_key), str)
            _assert_plain(test, child, key=child_key)
        return
    if type(value) is list:
        for child in value:
            _assert_plain(test, child)
        return
    test.fail(f"unstable type {type(value).__name__} at {key}")


def _dag_public(dag: Mapping[str, object]) -> dict:
    return {key: value for key, value in dag.items() if key != "nodes"}


class TestTrustBoundary(unittest.TestCase):
    def test_01_top_level_split_view_neutralized(self) -> None:
        rp = _hand_rp()
        bound = {"nodes": [_receipt_node("rp-1", rp)]}
        live = {
            "nodes": [_receipt_node("rp-1", rp)],
            "structure_status": "GRAPH_COMPLETE",
            "PASS": True,
        }
        dag = build_evidence_binding_dag(_SplitView(bound, live))
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        self.assertNotIn("PASS", dag)
        dag = build_evidence_binding_dag(_SplitDict(bound, live))
        self.assertEqual(dag["schema_version"], "evidence_binding_dag.v0")

    def test_02_nested_split_view_neutralized(self) -> None:
        rp = _hand_rp()
        live_body = dict(rp)
        live_body["recovered"] = True
        node = {
            "node_id": "rp-1",
            "kind": "RECEIPT",
            "body": _SplitView(rp, live_body),
        }
        dag = _build([node])
        recovered = next(item["body"]["recovered"] for item in dag["nodes"] if item["kind"] == "RECEIPT")
        self.assertIs(recovered, False)
        self.assertIs(dag["authority"], False)

    def test_03_scalar_subclass_rejected(self) -> None:
        rp = _hand_rp()
        node = _receipt_node(_HostileStr("rp-1"), rp)
        _expect(self, "DAG_SOURCE_INVALID", lambda: _build([node]))
        node = _receipt_node("rp-1", rp)
        record = {"nodes": [node]}
        record_count = {"nodes": [_HostileInt(1)]}
        _expect(self, "DAG_SOURCE_INVALID", lambda: build_evidence_binding_dag(record_count))

    def test_04_container_subclass_rejected(self) -> None:
        rp = _hand_rp()
        _expect(self, "DAG_SOURCE_INVALID", lambda: _build(_Rows([_receipt_node("rp-1", rp)])))
        node = _receipt_node("rp-1", rp)
        node["body"] = dict(rp)
        node["body"]["limitations"] = _Reuse(("restore execution",))
        _expect(self, "DAG_SOURCE_INVALID", lambda: _build([node]))

    def test_05_unknown_kwargs_rejected(self) -> None:
        _expect(self, "DAG_SOURCE_INVALID", lambda: _build([_receipt_node("rp-1", _hand_rp())], extra=True))

    def test_06_caller_global_verdict_keys_rejected(self) -> None:
        nodes = [_receipt_node("rp-1", _hand_rp())]
        for key in _VERDICT_KEYS:
            _expect(self, "DAG_FORBIDDEN", lambda key=key: _build(nodes, **{key: True}))

    def test_07_caller_admission_and_human_final_rejected(self) -> None:
        nodes = [_receipt_node("rp-1", _hand_rp())]
        for key in _ADMISSION_KEYS:
            _expect(self, "DAG_FORBIDDEN", lambda key=key: _build(nodes, **{key: True}))
        _expect(self, "DAG_FORBIDDEN", lambda: _build(nodes, independent_evidence_count=1))
        _expect(self, "DAG_SOURCE_INVALID", lambda: build_evidence_binding_dag(_DupKeys()))


class TestNodeModel(unittest.TestCase):
    def test_08_valid_known_receipt_accepted(self) -> None:
        dag = _build([_receipt_node("rp-1", _hand_rp())])
        self.assertEqual(dag["nodes"][0]["kind"], "RECEIPT")
        self.assertEqual(dag["nodes"][0]["schema_version"], "recovery_preflight.v0")
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")

    def test_09_unknown_schema_cannot_be_receipt(self) -> None:
        body = {"schema_version": "unknown.v9", "authority": False, "payload": "x"}
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("u-1", body)]))

    def test_10_unknown_schema_body_can_be_artifact(self) -> None:
        body = {"schema_version": "unknown.v9", "authority": False, "payload": "x"}
        dag = _build([_artifact_node("a-1", body)])
        self.assertEqual(dag["nodes"][0]["kind"], "ARTIFACT")
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")

    def test_11_digest_only_must_be_external_ref(self) -> None:
        digest = canonical_digest({"x": 1})
        _expect(
            self,
            "DAG_NODE_INVALID",
            lambda: _build([{"node_id": "a-1", "kind": "ARTIFACT", "digest": digest}]),
        )
        dag = _build([_external("ext-1", digest)])
        self.assertEqual(dag["nodes"][0]["kind"], "EXTERNAL_REF")

    def test_12_external_ref_cannot_carry_classification(self) -> None:
        digest = canonical_digest({"x": 1})
        _expect(
            self,
            "DAG_NODE_INVALID",
            lambda: _build(
                [
                    {
                        "node_id": "ext-1",
                        "kind": "EXTERNAL_REF",
                        "digest": digest,
                        "classification": "PASS",
                    }
                ]
            ),
        )
        _expect(
            self,
            "DAG_NODE_INVALID",
            lambda: _build(
                [
                    {
                        "node_id": "ext-1",
                        "kind": "EXTERNAL_REF",
                        "digest": digest,
                        "schema_version": "tested_envelope.v0",
                    }
                ]
            ),
        )

    def test_13_duplicate_body_under_new_node_id_rejected(self) -> None:
        rp = _hand_rp()
        _expect(
            self,
            "DAG_DUPLICATE",
            lambda: _build([_receipt_node("rp-1", rp), _receipt_node("rp-2", copy.deepcopy(rp))]),
        )

    def test_14_same_node_id_conflicting_body_rejected(self) -> None:
        _expect(
            self,
            "DAG_DUPLICATE",
            lambda: _build(
                [
                    _receipt_node("rp-1", _hand_rp()),
                    _receipt_node("rp-1", _hand_rp(cited_decision={"claim_id": "OTHER", "decision": "PASS"})),
                ]
            ),
        )

    def test_15_mutable_alias_label_does_not_resolve_identity(self) -> None:
        nodes, _, _ = _complete_te_graph()
        te = nodes[0]["body"]
        dangling = dict(te)
        dangling["scope_binding"] = {
            "claim_id": "AUR-A-001",
            "scope_digest": te["scope_binding"]["scope_digest"],
        }
        alias_node = _artifact_node("head-1", {"alias": "HEAD"})
        alias_node["artifact_id"] = "HEAD"
        dag = _build(
            [
                _receipt_node("te-1", dangling),
                alias_node,
            ]
        )
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        self.assertTrue(any(item["reason"] == "MISSING" for item in dag["unresolved_references"]))
        kinds = {item["label_kind"] for item in dag["label_only_refs"]}
        self.assertIn("claim_id", kinds)


class TestReceiptDigestRules(unittest.TestCase):
    def test_16_cr_valid_self_digest_accepted(self) -> None:
        receipt = _cr_build()
        dag = _build([_receipt_node("cr-1", receipt)])
        node = dag["nodes"][0]
        self.assertEqual(node["kind"], "RECEIPT")
        self.assertEqual(node["source_reported_digest"], receipt["receipt_digest"])
        stripped = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        self.assertEqual(node["source_reported_digest"], canonical_digest(stripped))
        self.assertEqual(node["node_digest"], canonical_digest(receipt))

    def test_17_cr_full_body_hash_is_not_receipt_digest(self) -> None:
        receipt = _cr_build()
        full = canonical_digest(receipt)
        self.assertNotEqual(receipt["receipt_digest"], full)
        tampered = dict(receipt)
        tampered["receipt_digest"] = full
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("cr-1", tampered)]))
        dag = _build([_receipt_node("cr-1", receipt)])
        self.assertNotEqual(dag["nodes"][0]["source_reported_digest"], full)

    def test_18_cr_bad_receipt_digest_rejected(self) -> None:
        receipt = _cr_build()
        receipt = dict(receipt)
        receipt["receipt_digest"] = "ab" * 32
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("cr-1", receipt)]))

    def test_19_rer_valid_self_digest_accepted(self) -> None:
        receipt = _rer_build()
        dag = _build([_receipt_node("rer-1", receipt)])
        node = dag["nodes"][0]
        stripped = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        self.assertEqual(node["source_reported_digest"], canonical_digest(stripped))
        self.assertEqual(node["source_reported_digest"], receipt["receipt_digest"])

    def test_20_rer_bad_receipt_digest_rejected(self) -> None:
        receipt = dict(_rer_build())
        receipt["receipt_digest"] = "cd" * 32
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("rer-1", receipt)]))

    def test_21_te_with_receipt_digest_rejected(self) -> None:
        receipt = dict(_te_build(_te_bundle()))
        receipt["receipt_digest"] = "ab" * 32
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("te-1", receipt)]))

    def test_22_rp_with_receipt_digest_rejected(self) -> None:
        receipt = dict(_rp_build(_rp_bundle()))
        receipt["receipt_digest"] = "ab" * 32
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("rp-1", receipt)]))

    def test_23_ivp_with_receipt_digest_rejected(self) -> None:
        receipt = dict(_ivp_build())
        receipt["receipt_digest"] = "ab" * 32
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", receipt)]))


class TestRequiredReferenceDerivation(unittest.TestCase):
    def test_24_caller_cannot_suppress_schema_derived_dependency(self) -> None:
        te = _hand_te(scope_digest="ab" * 32, file_digest="cd" * 32)
        dag = _build([_receipt_node("te-1", te)], edges=[])
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        paths = {item["source_path"] for item in dag["unresolved_references"]}
        self.assertIn("scope_binding.scope_digest", paths)
        self.assertIn("artifact_revision.files[0].sha256", paths)

    def test_25_no_declared_deps_still_incomplete_when_required_missing(self) -> None:
        te = _hand_te(scope_digest="11" * 32, file_digest="22" * 32)
        dag = _build([_receipt_node("te-1", te)])
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        self.assertGreaterEqual(len(dag["unresolved_references"]), 1)

    def test_26_body_backed_matching_digest_resolves(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(nodes)
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        self.assertEqual(dag["unresolved_references"], [])

    def test_27_external_ref_only_is_digest_only_external(self) -> None:
        scope_digest = "ab" * 32
        file_digest = "cd" * 32
        te = _hand_te(scope_digest=scope_digest, file_digest=file_digest)
        dag = _build(
            [
                _receipt_node("te-1", te),
                _external("ext-scope", scope_digest),
                _external("ext-file", file_digest),
            ]
        )
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        reasons = {item["reason"] for item in dag["unresolved_references"]}
        self.assertEqual(reasons, {"DIGEST_ONLY_EXTERNAL"})

    def test_28_missing_target_is_missing(self) -> None:
        te = _hand_te(scope_digest="33" * 32, file_digest="44" * 32)
        dag = _build([_receipt_node("te-1", te)])
        reasons = {item["reason"] for item in dag["unresolved_references"]}
        self.assertEqual(reasons, {"MISSING"})

    def test_29_label_only_claim_never_resolves_by_label(self) -> None:
        te = _hand_te(scope_digest="55" * 32, file_digest="66" * 32, claim_id="AUR-A-001")
        dag = _build(
            [
                _receipt_node("te-1", te),
                _claim_node("claim-1", _claim_body("AUR-A-001")),
            ]
        )
        relations = {item["relation"] for item in dag["edges"]}
        self.assertNotIn("BOUNDS", relations)
        labels = [item["label"] for item in dag["label_only_refs"]]
        self.assertIn("AUR-A-001", labels)
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")


class TestTestedEnvelopeBounds(unittest.TestCase):
    def test_30_te_scope_digest_bounds_matching_scope_artifact(self) -> None:
        nodes, scope_body, _ = _complete_te_graph()
        dag = _build(nodes)
        bounds = [item for item in dag["edges"] if item["relation"] == "BOUNDS"]
        self.assertEqual(len(bounds), 1)
        self.assertEqual(bounds[0]["basis"], "SOURCE_DERIVED")
        self.assertEqual(bounds[0]["target_digest"], canonical_digest(scope_body))

    def test_31_te_claim_id_does_not_bounds_claim(self) -> None:
        nodes, _, _ = _complete_te_graph()
        nodes.append(_claim_node("claim-1", _claim_body("AUR-A-001")))
        dag = _build(nodes)
        claim_digest = canonical_digest(_claim_body("AUR-A-001"))
        for item in dag["edges"]:
            if item["relation"] == "BOUNDS":
                self.assertNotEqual(item["target_digest"], claim_digest)

    def test_32_wrong_scope_digest_unresolved(self) -> None:
        scope_body = {"allowed_write_boundary": ["audit/**"]}
        file_body = {"blob": "payload-bytes"}
        te = _hand_te(
            scope_digest="77" * 32,
            file_digest=canonical_digest(file_body),
        )
        dag = _build(
            [
                _receipt_node("te-1", te),
                _artifact_node("scope-wrong", scope_body),
                _artifact_node("file-1", file_body),
            ]
        )
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        self.assertTrue(
            any(
                item["source_path"] == "scope_binding.scope_digest" and item["reason"] == "MISSING"
                for item in dag["unresolved_references"]
            )
        )
        self.assertFalse(any(item["relation"] == "BOUNDS" for item in dag["edges"]))

    def test_33_te_pass_remains_source_local(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(nodes)
        self.assertNotIn("result", dag)
        self.assertNotIn("PASS", dag)
        te_node = next(item for item in dag["nodes"] if item["node_id"] == "te-1")
        self.assertEqual(te_node["body"]["result"], "PASS")


class TestInternalPolicy(unittest.TestCase):
    def test_34_cr_internals_are_not_first_class_nodes(self) -> None:
        receipt = _cr_build()
        dag = _build([_receipt_node("cr-1", receipt)])
        kinds = {item["kind"] for item in dag["nodes"]}
        self.assertEqual(kinds, {"RECEIPT"})
        self.assertEqual(len(dag["nodes"]), 1)
        self.assertIn("proposal", dag["nodes"][0]["body"])
        self.assertIn("challenges", dag["nodes"][0]["body"])
        self.assertIn("revisions", dag["nodes"][0]["body"])
        self.assertIn("human_selection", dag["nodes"][0]["body"])

    def test_35_selects_challenges_responds_to_rejected(self) -> None:
        nodes = [
            _receipt_node("rp-1", _hand_rp()),
            _artifact_node("a-1"),
        ]
        for relation in ("SELECTS", "CHALLENGES", "RESPONDS_TO", "SUPPORTS", "VERIFIES"):
            _expect(
                self,
                "DAG_EDGE_INVALID",
                lambda relation=relation: _build(
                    nodes,
                    [
                        {
                            "edge_id": "e-1",
                            "relation": relation,
                            "basis": "CALLER_DECLARED",
                            "source_node_id": "rp-1",
                            "target_node_id": "a-1",
                        }
                    ],
                ),
            )

    def test_36_rer_recovered_bounded_not_promoted(self) -> None:
        receipt = _rer_build()
        dag = _build([_receipt_node("rer-1", receipt)])
        self.assertNotIn("recovered", dag)
        self.assertNotIn("classification", dag)
        self.assertNotEqual(dag.get("structure_status"), "RECOVERED_BOUNDED")
        rer_node = next(item for item in dag["nodes"] if item["node_id"] == "rer-1")
        self.assertIs(rer_node["body"]["recovered"], False)
        self.assertEqual(rer_node["body"]["classification"], receipt["classification"])


class TestEdgeBasis(unittest.TestCase):
    def test_37_caller_cannot_claim_source_derived_depends_on(self) -> None:
        nodes = [_receipt_node("rp-1", _hand_rp()), _artifact_node("a-1")]
        _expect(
            self,
            "DAG_EDGE_INVALID",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "e-1",
                        "relation": "DEPENDS_ON",
                        "basis": "SOURCE_DERIVED",
                        "source_node_id": "rp-1",
                        "target_node_id": "a-1",
                    }
                ],
            ),
        )

    def test_38_depends_on_source_derived_only(self) -> None:
        nodes = [_receipt_node("rp-1", _hand_rp()), _artifact_node("a-1")]
        _expect(
            self,
            "DAG_EDGE_INVALID",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "e-1",
                        "relation": "DEPENDS_ON",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "rp-1",
                        "target_node_id": "a-1",
                    }
                ],
            ),
        )

    def test_39_bounds_source_derived_only(self) -> None:
        nodes, _, _ = _complete_te_graph()
        _expect(
            self,
            "DAG_EDGE_INVALID",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "e-1",
                        "relation": "BOUNDS",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "te-1",
                        "target_node_id": "scope-1",
                    }
                ],
            ),
        )

    def test_40_cites_caller_declared_allowed(self) -> None:
        nodes = [_receipt_node("rp-1", _hand_rp()), _artifact_node("a-1")]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "cite-1",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "rp-1",
                    "target_node_id": "a-1",
                }
            ],
        )
        cites = [item for item in dag["edges"] if item["relation"] == "CITES"]
        self.assertEqual(len(cites), 1)
        self.assertEqual(cites[0]["basis"], "CALLER_DECLARED")

    def test_41_successor_of_caller_declared_allowed(self) -> None:
        nodes = [_artifact_node("old", {"v": 1}), _artifact_node("new", {"v": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "succ-1",
                    "relation": "SUCCESSOR_OF",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "new",
                    "target_node_id": "old",
                }
            ],
        )
        self.assertEqual(dag["edges"][0]["relation"], "SUCCESSOR_OF")
        ids = {item["node_id"] for item in dag["nodes"]}
        self.assertEqual(ids, {"old", "new"})

    def test_42_contradicts_requires_rationale(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        _expect(
            self,
            "DAG_EDGE_INVALID",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "c-1",
                        "relation": "CONTRADICTS",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "a-1",
                        "target_node_id": "a-2",
                    }
                ],
            ),
        )
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                    "rationale_body": {"note": "disagreement"},
                }
            ],
        )
        self.assertTrue(dag["contradiction_present"])


class TestContradictionHandling(unittest.TestCase):
    def test_43_contradiction_both_endpoints_preserved(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                    "rationale_body": {"note": "conflict"},
                }
            ],
        )
        ids = {item["node_id"] for item in dag["nodes"]}
        self.assertEqual(ids, {"a-1", "a-2"})
        self.assertEqual(len(dag["nodes"]), 2)

    def test_44_contradiction_does_not_alter_structure_status(self) -> None:
        rp_nodes = [_receipt_node("rp-1", _hand_rp()), _artifact_node("a-1", {"x": 1})]
        complete = _build(rp_nodes)
        contradicted = _build(
            rp_nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "rp-1",
                    "target_node_id": "a-1",
                    "rationale_body": {"note": "conflict"},
                }
            ],
        )
        self.assertEqual(complete["structure_status"], contradicted["structure_status"])
        self.assertEqual(complete["structure_status"], "GRAPH_COMPLETE")

    def test_45_complete_and_contradiction_present(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "te-1",
                    "target_node_id": "scope-1",
                    "rationale_body": {"note": "scope dispute"},
                }
            ],
        )
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        self.assertIs(dag["contradiction_present"], True)

    def test_46_reversed_duplicate_contradiction_rejected(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        rationale = {"note": "same"}
        _expect(
            self,
            "DAG_DUPLICATE",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "c-1",
                        "relation": "CONTRADICTS",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "a-1",
                        "target_node_id": "a-2",
                        "rationale_body": rationale,
                    },
                    {
                        "edge_id": "c-2",
                        "relation": "CONTRADICTS",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "a-2",
                        "target_node_id": "a-1",
                        "rationale_body": copy.deepcopy(rationale),
                    },
                ],
            ),
        )

    def test_47_same_pair_different_rationale_allowed(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                    "rationale_body": {"note": "one"},
                },
                {
                    "edge_id": "c-2",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                    "rationale_body": {"note": "two"},
                },
            ],
        )
        self.assertEqual(len(dag["contradictions"]), 2)

    def test_48_no_majority_or_winner_field(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                    "rationale_body": {"note": "conflict"},
                }
            ],
        )
        public = _dag_public(dag)
        blob = json.dumps(public)
        self.assertNotIn("winner", blob)
        self.assertNotIn("majority", blob)
        self.assertNotIn("resolved_by", public)


class TestAcyclicity(unittest.TestCase):
    def test_49_depends_on_cycle_rejected(self) -> None:
        nodes, _, file_body = _complete_te_graph()
        _expect(
            self,
            "DAG_CYCLE",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "s-1",
                        "relation": "SUCCESSOR_OF",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "file-1",
                        "target_node_id": "te-1",
                    }
                ],
            ),
        )

    def test_50_bounds_successor_combined_cycle_rejected(self) -> None:
        nodes, _, _ = _complete_te_graph()
        _expect(
            self,
            "DAG_CYCLE",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "s-1",
                        "relation": "SUCCESSOR_OF",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "scope-1",
                        "target_node_id": "te-1",
                    }
                ],
            ),
        )

    def test_51_reciprocal_contradicts_allowed(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                    "rationale_body": {"note": "left"},
                },
                {
                    "edge_id": "c-2",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-2",
                    "target_node_id": "a-1",
                    "rationale_body": {"note": "right"},
                },
            ],
        )
        self.assertEqual(len(dag["contradictions"]), 2)
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")

    def test_52_cites_cycle_allowed(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                },
                {
                    "edge_id": "c-2",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-2",
                    "target_node_id": "a-1",
                },
            ],
        )
        self.assertEqual(len(dag["edges"]), 2)

    def test_53_self_loop_rejected_for_every_relation(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1})]
        for relation in ("CITES", "SUCCESSOR_OF", "CONTRADICTS"):
            edge = {
                "edge_id": f"e-{relation}",
                "relation": relation,
                "basis": "CALLER_DECLARED",
                "source_node_id": "a-1",
                "target_node_id": "a-1",
            }
            if relation == "CONTRADICTS":
                edge["rationale_body"] = {"note": "self"}
            _expect(self, "DAG_EDGE_INVALID", lambda edge=edge: _build(nodes, [edge]))


class TestStructuralStatus(unittest.TestCase):
    def test_54_all_required_refs_resolved_is_complete(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(nodes)
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")

    def test_55_any_required_ref_missing_is_incomplete(self) -> None:
        nodes, scope_body, _ = _complete_te_graph()
        dag = _build([nodes[0], _artifact_node("scope-1", scope_body)])
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")

    def test_56_unresolved_refs_full_list_preserved(self) -> None:
        te = _hand_te(scope_digest="aa" * 32, file_digest="bb" * 32)
        dag = _build([_receipt_node("te-1", te)])
        paths = [item["source_path"] for item in dag["unresolved_references"]]
        self.assertEqual(paths, sorted(paths))
        self.assertIn("scope_binding.scope_digest", paths)
        self.assertIn("artifact_revision.files[0].sha256", paths)
        for item in dag["unresolved_references"]:
            self.assertEqual(set(item), {"source_node_digest", "source_path", "digest", "reason"})

    def test_57_label_only_refs_do_not_affect_completeness(self) -> None:
        dag = _build([_receipt_node("rp-1", _hand_rp())])
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        self.assertGreaterEqual(len(dag["label_only_refs"]), 1)

    def test_58_contradiction_flag_orthogonal(self) -> None:
        incomplete = _build([_receipt_node("te-1", _hand_te(scope_digest="aa" * 32, file_digest="bb" * 32))])
        self.assertEqual(incomplete["structure_status"], "GRAPH_INCOMPLETE")
        self.assertIs(incomplete["contradiction_present"], False)
        nodes, _, _ = _complete_te_graph()
        complete = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CONTRADICTS",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "file-1",
                    "target_node_id": "scope-1",
                    "rationale_body": {"note": "conflict"},
                }
            ],
        )
        self.assertEqual(complete["structure_status"], "GRAPH_COMPLETE")
        self.assertIs(complete["contradiction_present"], True)


class TestGlobalVerdictBoundary(unittest.TestCase):
    def test_59_no_dag_level_pass(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(nodes)
        self.assertNotIn("PASS", dag)
        self.assertNotEqual(dag["structure_status"], "PASS")

    def test_60_no_safe_trusted_verified_recovered_accepted(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(nodes)
        for key in ("SAFE", "TRUSTED", "VERIFIED", "RECOVERED", "ACCEPTED"):
            self.assertNotIn(key, dag)
            self.assertNotEqual(dag["structure_status"], key)

    def test_61_no_human_final_output(self) -> None:
        dag = _build([_receipt_node("rp-1", _hand_rp())])
        self.assertNotIn("human_final", dag)
        self.assertNotIn("human_final_status", dag)
        self.assertNotIn("HUMAN_REVIEW_ACCEPTED", dag)

    def test_62_no_admission_or_count_output(self) -> None:
        receipt = _ivp_build()
        dag = _build([_receipt_node("ivp-1", receipt)])
        self.assertNotIn("admission_status", dag)
        self.assertNotIn("independent_evidence_count", dag)
        self.assertNotIn("structural_candidate", dag)
        self.assertEqual(dag["nodes"][0]["body"]["admission_status"], "NOT_CONFIGURED")

    def test_63_quoted_source_local_pass_only_inside_body(self) -> None:
        nodes, _, _ = _complete_te_graph()
        dag = _build(nodes)
        te_node = next(item for item in dag["nodes"] if item["node_id"] == "te-1")
        self.assertEqual(te_node["body"]["result"], "PASS")
        self.assertNotIn("result", dag)
        self.assertNotIn("source_result", dag)
        self.assertNotEqual(dag["structure_status"], "PASS")


class TestHumanFinalProvenance(unittest.TestCase):
    def test_64_human_final_artifact_citation_does_not_change_status(self) -> None:
        nodes, _, _ = _complete_te_graph()
        baseline = _build(nodes)
        nodes = nodes + [
            _artifact_node(
                "hf-1",
                {"document": "HUMAN_FINAL", "status": "HUMAN_REVIEW_ACCEPTED"},
            )
        ]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "cite-hf",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "te-1",
                    "target_node_id": "hf-1",
                }
            ],
        )
        self.assertEqual(dag["structure_status"], baseline["structure_status"])
        self.assertEqual(dag["contradiction_present"], baseline["contradiction_present"])

    def test_65_implementation_sha_citation_does_not_change_status(self) -> None:
        nodes, _, _ = _complete_te_graph()
        baseline = _build(nodes)
        sha_body = {"implementation_sha": "ab" * 32}
        nodes = nodes + [_artifact_node("sha-1", sha_body)]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "cite-sha",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "te-1",
                    "target_node_id": "sha-1",
                }
            ],
        )
        self.assertEqual(dag["structure_status"], baseline["structure_status"])


class TestCanonicalization(unittest.TestCase):
    def test_66_input_node_order_does_not_change_dag_digest(self) -> None:
        nodes, _, _ = _complete_te_graph()
        first = _build(nodes)
        second = _build(list(reversed(nodes)))
        self.assertEqual(first["dag_digest"], second["dag_digest"])
        self.assertEqual(
            [item["node_digest"] for item in first["nodes"]],
            [item["node_digest"] for item in second["nodes"]],
        )

    def test_67_input_edge_order_does_not_change_dag_digest(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2}), _artifact_node("a-3", {"x": 3})]
        edges = [
            {
                "edge_id": "c-1",
                "relation": "CITES",
                "basis": "CALLER_DECLARED",
                "source_node_id": "a-1",
                "target_node_id": "a-2",
            },
            {
                "edge_id": "c-2",
                "relation": "CITES",
                "basis": "CALLER_DECLARED",
                "source_node_id": "a-2",
                "target_node_id": "a-3",
            },
        ]
        first = _build(nodes, edges)
        second = _build(nodes, list(reversed(edges)))
        self.assertEqual(first["dag_digest"], second["dag_digest"])

    def test_68_deterministic_unresolved_and_label_order(self) -> None:
        te = _hand_te(scope_digest="aa" * 32, file_digest="bb" * 32)
        first = _build([_receipt_node("te-1", te)])
        second = _build([_receipt_node("te-1", copy.deepcopy(te))])
        self.assertEqual(first["unresolved_references"], second["unresolved_references"])
        self.assertEqual(first["label_only_refs"], second["label_only_refs"])
        paths = [item["source_path"] for item in first["unresolved_references"]]
        self.assertEqual(paths, sorted(paths))

    def test_69_dag_digest_recomputable_excluding_itself(self) -> None:
        dag = _build([_receipt_node("rp-1", _hand_rp())])
        body = {key: value for key, value in dag.items() if key != "dag_digest"}
        self.assertEqual(dag["dag_digest"], canonical_digest(body))
        self.assertNotEqual(dag["dag_digest"], canonical_digest(dag))


class TestSameClassReview(unittest.TestCase):
    def test_caller_node_digest_must_match_recompute(self) -> None:
        rp = _hand_rp()
        node = _receipt_node("rp-1", rp)
        node["node_digest"] = "ab" * 32
        _expect(self, "DAG_NODE_INVALID", lambda: _build([node]))
        node["node_digest"] = canonical_digest(rp)
        dag = _build([node])
        self.assertEqual(dag["nodes"][0]["node_digest"], canonical_digest(rp))

    def test_duplicate_external_ref_digest_rejected(self) -> None:
        digest = canonical_digest({"x": 1})
        _expect(
            self,
            "DAG_DUPLICATE",
            lambda: _build([_external("e-1", digest), _external("e-2", digest)]),
        )

    def test_duplicate_edge_digest_new_id_rejected(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        edge = {
            "relation": "CITES",
            "basis": "CALLER_DECLARED",
            "source_node_id": "a-1",
            "target_node_id": "a-2",
        }
        _expect(
            self,
            "DAG_DUPLICATE",
            lambda: _build(
                nodes,
                [
                    {**edge, "edge_id": "c-1"},
                    {**edge, "edge_id": "c-2"},
                ],
            ),
        )

    def test_same_edge_id_different_body_rejected(self) -> None:
        nodes = [
            _artifact_node("a-1", {"x": 1}),
            _artifact_node("a-2", {"x": 2}),
            _artifact_node("a-3", {"x": 3}),
        ]
        _expect(
            self,
            "DAG_DUPLICATE",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "c-1",
                        "relation": "CITES",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "a-1",
                        "target_node_id": "a-2",
                    },
                    {
                        "edge_id": "c-1",
                        "relation": "CITES",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "a-1",
                        "target_node_id": "a-3",
                    },
                ],
            ),
        )

    def test_contradicts_rejects_external_ref_endpoint(self) -> None:
        digest = canonical_digest({"x": 1})
        nodes = [_artifact_node("a-1", {"x": 2}), _external("ext-1", digest)]
        _expect(
            self,
            "DAG_EDGE_INVALID",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "c-1",
                        "relation": "CONTRADICTS",
                        "basis": "CALLER_DECLARED",
                        "source_node_id": "a-1",
                        "target_node_id": "ext-1",
                        "rationale_body": {"note": "no"},
                    }
                ],
            ),
        )

    def test_source_derived_successor_from_caller_rejected(self) -> None:
        nodes = [_artifact_node("a-1", {"v": 1}), _artifact_node("a-2", {"v": 2})]
        _expect(
            self,
            "DAG_EDGE_INVALID",
            lambda: _build(
                nodes,
                [
                    {
                        "edge_id": "s-1",
                        "relation": "SUCCESSOR_OF",
                        "basis": "SOURCE_DERIVED",
                        "source_node_id": "a-2",
                        "target_node_id": "a-1",
                    }
                ],
            ),
        )

    def test_challenge_node_kind_rejected(self) -> None:
        _expect(
            self,
            "DAG_NODE_INVALID",
            lambda: _build(
                [{"node_id": "c-1", "kind": "CHALLENGE", "body": {"x": 1}}]
            ),
        )

    def test_output_is_plain_and_authority_false(self) -> None:
        dag = _build([_receipt_node("rp-1", _hand_rp())])
        self.assertIs(type(dag), dict)
        self.assertIs(dag["authority"], False)
        self.assertEqual(dag["schema_version"], "evidence_binding_dag.v0")
        _assert_plain(self, dag)
        allowed = {
            "schema_version",
            "authority",
            "structure_status",
            "unresolved_references",
            "label_only_refs",
            "contradiction_present",
            "contradictions",
            "nodes",
            "edges",
            "limitations",
            "dag_digest",
        }
        self.assertEqual(set(dag), allowed)

    def test_source_schema_drift_accepts_current_builders(self) -> None:
        te = _te_build(_te_bundle())
        rp = _rp_build(_rp_bundle())
        ivp = _ivp_build()
        cr = _cr_build()
        rer = _rer_build()
        for node_id, body in (
            ("te-1", te),
            ("rp-1", rp),
            ("ivp-1", ivp),
            ("cr-1", cr),
            ("rer-1", rer),
        ):
            dag = _build([_receipt_node(node_id, body)])
            self.assertEqual(dag["nodes"][0]["kind"], "RECEIPT")
            self.assertIs(dag["authority"], False)
            self.assertIs(dag["nodes"][0]["body"]["authority"], False)

    def test_cr_source_reported_digest_resolves_required_ref(self) -> None:
        cr = _cr_build()
        reported = cr["receipt_digest"]
        te = _hand_te(scope_digest=reported, file_digest=reported)
        dag = _build(
            [
                _receipt_node("te-1", te),
                _receipt_node("cr-1", cr),
            ]
        )
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        depends = [item for item in dag["edges"] if item["relation"] == "DEPENDS_ON"]
        self.assertTrue(depends)

    def test_output_does_not_retain_caller_list(self) -> None:
        nodes = [_receipt_node("rp-1", _hand_rp())]
        dag = _build(nodes)
        nodes.append(_artifact_node("later", {"x": 1}))
        self.assertEqual(len(dag["nodes"]), 1)

    def test_same_pair_different_allowed_relation(self) -> None:
        nodes = [_artifact_node("a-1", {"x": 1}), _artifact_node("a-2", {"x": 2})]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "c-1",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                },
                {
                    "edge_id": "s-1",
                    "relation": "SUCCESSOR_OF",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "a-1",
                    "target_node_id": "a-2",
                },
            ],
        )
        self.assertEqual({item["relation"] for item in dag["edges"]}, {"CITES", "SUCCESSOR_OF"})


class TestR1F1ReceiptDowngrade(unittest.TestCase):
    def test_f1a_ivp_receipt_incomplete_same_body_artifact_rejected(self) -> None:
        target = canonical_digest({"blob": "ivp-target"})
        ivp = _hand_ivp(
            file_digest=target,
            source_evidence=target,
            source_input=target,
            independent_evidence=target,
            independent_input=target,
        )
        dag = _build([_receipt_node("ivp-1", ivp)])
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        paths = {item["source_path"] for item in dag["unresolved_references"]}
        self.assertIn("artifact_revision_binding.files[0].sha256", paths)
        self.assertIn("source_execution_summary.evidence_digest", paths)
        _expect(self, "DAG_NODE_INVALID", lambda: _build([_artifact_node("ivp-as-artifact", ivp)]))

    def test_f1b_invalid_ivp_as_artifact_rejected_for_schema_downgrade(self) -> None:
        body = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
            authority=True,
            admission_status="ADMITTED",
        )
        _expect(self, "DAG_NODE_INVALID", lambda: _build([_artifact_node("ivp-bad", body)]))

    def test_f1c_cr_bad_digest_as_artifact_rejected(self) -> None:
        receipt = dict(_cr_build())
        receipt["receipt_digest"] = "ab" * 32
        _expect(self, "DAG_NODE_INVALID", lambda: _build([_artifact_node("cr-bad", receipt)]))

    def test_f1d_rer_bad_digest_as_artifact_rejected(self) -> None:
        receipt = dict(_rer_build())
        receipt["receipt_digest"] = "cd" * 32
        _expect(self, "DAG_NODE_INVALID", lambda: _build([_artifact_node("rer-bad", receipt)]))

    def test_f1e_recognized_receipt_schema_under_claim_rejected(self) -> None:
        bodies = [
            _hand_te(scope_digest="ab" * 32, file_digest="cd" * 32),
            _hand_rp(),
            _hand_ivp(
                file_digest="ab" * 32,
                source_evidence="cd" * 32,
                source_input="11" * 32,
                independent_evidence="22" * 32,
                independent_input="33" * 32,
            ),
            _cr_build(),
            _rer_build(),
        ]
        for body in bodies:
            _expect(
                self,
                "DAG_NODE_INVALID",
                lambda body=body: _build([_claim_node("claim-1", body)]),
            )

    def test_f1f_unknown_schema_artifact_allowed_without_node_schema(self) -> None:
        body = {"schema_version": "unknown.v9", "authority": False, "payload": "x"}
        dag = _build([_artifact_node("a-1", body)])
        node = dag["nodes"][0]
        self.assertEqual(node["kind"], "ARTIFACT")
        self.assertNotIn("schema_version", node)
        self.assertEqual(node["body"]["schema_version"], "unknown.v9")
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")


class TestR1F2SchemaHardening(unittest.TestCase):
    def test_te_verified_result_rejected(self) -> None:
        te = _hand_te(scope_digest="ab" * 32, file_digest="cd" * 32, result="VERIFIED")
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("te-1", te)]))

    def test_rp_recovered_classification_rejected(self) -> None:
        rp = _hand_rp(classification="RECOVERED")
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("rp-1", rp)]))

    def test_ivp_admitted_status_rejected(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
            admission_status="ADMITTED",
        )
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", ivp)]))

    def test_ivp_structural_candidate_string_rejected(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
            structural_candidate="YES",
        )
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", ivp)]))

    def test_ivp_authority_true_rejected(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
            authority=True,
        )
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", ivp)]))

    def test_ivp_missing_evidence_digest_rejected(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
        )
        del ivp["source_execution_summary"]["evidence_digest"]
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", ivp)]))

    def test_ivp_empty_files_rejected(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
        )
        ivp["artifact_revision_binding"]["files"] = []
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", ivp)]))

    def test_ivp_files_scalar_rejected(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
        )
        ivp["artifact_revision_binding"]["files"] = "ab" * 32
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("ivp-1", ivp)]))

    def test_rer_recovered_classification_rejected(self) -> None:
        target = canonical_digest({"artifact": "pinned-v1"})
        env = canonical_digest({"name": "lab"})
        rer = _hand_rer(expected_digest=target, environment_digest=env, classification="RECOVERED")
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("rer-1", rer)]))

    def test_rer_content_digest_without_expected_digest_rejected(self) -> None:
        target = canonical_digest({"artifact": "pinned-v1"})
        env = canonical_digest({"name": "lab"})
        rer = _hand_rer(expected_digest=target, environment_digest=env)
        del rer["restore_target"]["expected_digest"]
        rer["receipt_digest"] = canonical_digest(
            {key: value for key, value in rer.items() if key != "receipt_digest"}
        )
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("rer-1", rer)]))

    def test_cr_invalid_sequence_status_rejected(self) -> None:
        receipt = dict(_cr_build())
        receipt["sequence_status"] = "VERIFIED"
        receipt["receipt_digest"] = canonical_digest(
            {key: value for key, value in receipt.items() if key != "receipt_digest"}
        )
        _expect(self, "DAG_RECEIPT_INVALID", lambda: _build([_receipt_node("cr-1", receipt)]))


class TestR1FalseGreen(unittest.TestCase):
    def test_ivp_extractor_missing_targets_incomplete(self) -> None:
        target = canonical_digest({"blob": "ivp-target"})
        ivp = _hand_ivp(
            file_digest=target,
            source_evidence=target,
            source_input=target,
            independent_evidence=target,
            independent_input=target,
        )
        dag = _build([_receipt_node("ivp-1", ivp)])
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        paths = {item["source_path"] for item in dag["unresolved_references"]}
        self.assertIn("artifact_revision_binding.files[0].sha256", paths)
        self.assertIn("source_execution_summary.evidence_digest", paths)
        self.assertIn("source_execution_summary.input_digest", paths)
        self.assertIn("independent_execution_summary.evidence_digest", paths)
        self.assertIn("independent_execution_summary.input_digest", paths)
        self.assertFalse(any(item["relation"] == "DEPENDS_ON" for item in dag["edges"]))

    def test_ivp_extractor_matching_targets_resolve(self) -> None:
        blob = {"blob": "ivp-target"}
        target = canonical_digest(blob)
        ivp = _hand_ivp(
            file_digest=target,
            source_evidence=target,
            source_input=target,
            independent_evidence=target,
            independent_input=target,
        )
        dag = _build(
            [
                _receipt_node("ivp-1", ivp),
                _artifact_node("target-1", blob),
            ]
        )
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        depends = [item for item in dag["edges"] if item["relation"] == "DEPENDS_ON"]
        self.assertTrue(depends)
        self.assertTrue(all(item["target_digest"] == target for item in depends))
        self.assertEqual(dag["unresolved_references"], [])

    def test_rer_extractor_missing_targets_incomplete(self) -> None:
        expected = canonical_digest({"artifact": "pinned-v1"})
        env = canonical_digest({"name": "lab"})
        iv = canonical_digest({"iv": "receipt"})
        rer = _hand_rer(expected_digest=expected, environment_digest=env, iv_digest=iv)
        dag = _build([_receipt_node("rer-1", rer)])
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        paths = {item["source_path"] for item in dag["unresolved_references"]}
        self.assertIn("restore_target.expected_digest", paths)
        self.assertIn("target_environment.environment_digest", paths)
        self.assertIn("independent_verification_refs[0].receipt_digest", paths)

    def test_rer_extractor_matching_targets_resolve(self) -> None:
        expected_body = {"artifact": "pinned-v1"}
        env_body = {"name": "lab"}
        iv_body = {"iv": "receipt"}
        expected = canonical_digest(expected_body)
        env = canonical_digest(env_body)
        iv = canonical_digest(iv_body)
        rer = _hand_rer(expected_digest=expected, environment_digest=env, iv_digest=iv)
        dag = _build(
            [
                _receipt_node("rer-1", rer),
                _artifact_node("restore-1", expected_body),
                _artifact_node("env-1", env_body),
                _artifact_node("iv-1", iv_body),
            ]
        )
        self.assertEqual(dag["structure_status"], "GRAPH_COMPLETE")
        depends = [item for item in dag["edges"] if item["relation"] == "DEPENDS_ON"]
        self.assertTrue(depends)
        cites = [item for item in dag["edges"] if item["relation"] == "CITES"]
        self.assertTrue(cites)
        self.assertEqual(dag["unresolved_references"], [])

    def test_cites_cannot_force_completeness(self) -> None:
        te = _hand_te(scope_digest="aa" * 32, file_digest="bb" * 32)
        extra = _artifact_node("note-1", {"note": "citation"})
        dag = _build(
            [_receipt_node("te-1", te), extra],
            [
                {
                    "edge_id": "cite-1",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_node_id": "te-1",
                    "target_node_id": "note-1",
                }
            ],
        )
        self.assertEqual(dag["structure_status"], "GRAPH_INCOMPLETE")
        self.assertTrue(dag["unresolved_references"])

    def test_nested_wrapper_is_not_recognized_receipt(self) -> None:
        ivp = _hand_ivp(
            file_digest="ab" * 32,
            source_evidence="cd" * 32,
            source_input="11" * 32,
            independent_evidence="22" * 32,
            independent_input="33" * 32,
        )
        dag = _build([_artifact_node("wrapped", {"wrapped": ivp})])
        self.assertEqual(dag["nodes"][0]["kind"], "ARTIFACT")
        self.assertNotIn("schema_version", dag["nodes"][0])


class TestDigestLabelShadow(unittest.TestCase):
    def test_source_digest_does_not_resolve_by_node_id(self) -> None:
        real_body = {"payload": "real"}
        real_digest = canonical_digest(real_body)
        shadow_body = {"payload": "shadow"}
        other_body = {"payload": "other"}
        nodes = [
            {
                "node_id": real_digest,
                "kind": "ARTIFACT",
                "body": shadow_body,
            },
            _artifact_node("real-a", real_body),
            _artifact_node("other", other_body),
        ]
        dag = _build(
            nodes,
            [
                {
                    "edge_id": "cite-1",
                    "relation": "CITES",
                    "basis": "CALLER_DECLARED",
                    "source_digest": real_digest,
                    "target_node_id": "other",
                }
            ],
        )
        cites = [item for item in dag["edges"] if item["relation"] == "CITES"]
        self.assertEqual(len(cites), 1)
        self.assertEqual(cites[0]["source_digest"], real_digest)
        self.assertNotEqual(cites[0]["source_digest"], canonical_digest(shadow_body))


class TestNoAcceptedWrites(unittest.TestCase):
    def test_generation_does_not_write_accepted_trees(self) -> None:
        before = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        _build([_receipt_node("rp-1", _hand_rp())])
        after = subprocess.check_output(
            ["git", "-C", str(REPO), "status", "--porcelain"],
            text=True,
        )
        self.assertEqual(before, after)
        for line in after.splitlines():
            path = line[3:].strip().strip('"')
            self.assertTrue(path.startswith("evidence_binding_dag_v0"), path)


if __name__ == "__main__":
    unittest.main()
