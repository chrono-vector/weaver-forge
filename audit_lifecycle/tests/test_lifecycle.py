from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WF_ROOT = ROOT.parent
sys.path.insert(0, str(WF_ROOT))

from audit_lifecycle.boundary import BoundaryManager, BoundaryViolation
from audit_lifecycle.evidence import EvidenceCollector
from audit_lifecycle.freeze import FreezeAlreadyExists
from audit_lifecycle.orchestrator import AuditOrchestrator
from audit_lifecycle.request import AuditRequest, read_json, sha256_file, write_json
from audit_lifecycle.review_gate import HumanReviewRequired


FRESH = ROOT / "fixtures" / "fresh_target" / "README.txt"


class TestBoundary(unittest.TestCase):
    def test_outside_root_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            root.mkdir()
            outside = Path(td) / "outside.txt"
            bm = BoundaryManager(root, [])
            with self.assertRaises(BoundaryViolation):
                bm.open_write(outside, "x")
            self.assertFalse(outside.exists())

    def test_protected_dir_denied(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "run"
            prot = Path(td) / "protected"
            root.mkdir()
            prot.mkdir()
            bm = BoundaryManager(root, [prot])
            with self.assertRaises(BoundaryViolation):
                bm.open_write(prot / "evil.txt", "x")
            self.assertFalse((prot / "evil.txt").exists())


class TestLifecycleE2E(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory()
        self.out = Path(self._td.name)
        self.target = self.out / "target" / "README.txt"
        self.target.parent.mkdir(parents=True)
        shutil.copy2(FRESH, self.target)
        self.digest = sha256_file(self.target)
        self.protected = self.out / "prior_freeze"
        self.protected.mkdir()
        (self.protected / "SHA256SUMS.txt").write_text(
            f"{self.digest}  README.txt\n", encoding="utf-8"
        )
        self.prot_sums = sha256_file(self.protected / "SHA256SUMS.txt")

    def tearDown(self):
        self._td.cleanup()

    def _request(self, **claim_overrides):
        claim = {
            "id": "FRESH-PRIMARY",
            "statement": "Fresh target README.txt matches pinned SHA-256",
            "adapter": "hash_claim",
            "adapter_params": {
                "primary_file": "README.txt",
                "expected_sha256": self.digest,
                "mode": "verify_digest",
            },
        }
        claim.update(claim_overrides)
        # deep-merge adapter_params if provided
        if "adapter_params" in claim_overrides:
            params = {
                "primary_file": "README.txt",
                "expected_sha256": self.digest,
                "mode": "verify_digest",
            }
            params.update(claim_overrides["adapter_params"])
            claim["adapter_params"] = params
        return AuditRequest(
            target_path=str(self.target.parent),
            claim=claim,
            policy={
                "human_review_required": True,
                "required_vectors": [
                    "POSITIVE_DIGEST_MATCH",
                    "NC1_WRONG_DIGEST_REJECTED",
                    "T1_TAMPER_CHANGES_DIGEST",
                    "R1_REHASH_REPRODUCTION",
                    "BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
                ],
            },
            protected_paths=[str(self.protected)],
            prior_freeze_sums=[
                {
                    "label": "PRIOR_DUMMY_FREEZE",
                    "path": str(self.protected / "SHA256SUMS.txt"),
                    "sha256": self.prot_sums,
                }
            ],
        )

    def test_happy_path_freeze(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        self.assertEqual(result["decision"]["decision"], "PASS")
        self.assertFalse(result["frozen"])
        run = Path(result["audit_root"])
        write_json(
            run / "HUMAN_REVIEW.json",
            {
                "status": "ACCEPTED",
                "reviewer": "phase5-operator",
                "notes": "Defined workflow human gate",
            },
        )
        freeze = orch.freeze_run(run, req.policy)
        self.assertTrue(freeze["freeze_performed"])
        verify = orch.verify_run(run)
        self.assertTrue(verify["sha256sums_ok"])
        self.assertTrue(verify["freeze_sums_ok"])
        self.assertTrue(verify["semantic_ok"])
        self.assertTrue(verify["verify_ok"])
        self.assertTrue((run / "freeze").exists())
        # prior protected freeze untouched
        self.assertEqual(sha256_file(self.protected / "SHA256SUMS.txt"), self.prot_sums)

    def test_T9_freeze_second_attempt_denied(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        run = Path(result["audit_root"])
        write_json(
            run / "HUMAN_REVIEW.json",
            {
                "status": "ACCEPTED",
                "reviewer": "phase6-t9",
                "notes": "first freeze only",
            },
        )
        freeze = orch.freeze_run(run, req.policy)
        self.assertTrue(freeze["freeze_performed"])
        freeze_dir = Path(freeze["freeze_directory"])
        before = {
            p.name: sha256_file(p)
            for p in freeze_dir.iterdir()
            if p.is_file()
        }
        with self.assertRaises(FreezeAlreadyExists) as ctx:
            orch.freeze_run(run, req.policy)
        self.assertIn("FREEZE_ALREADY_EXISTS", str(ctx.exception))
        after = {
            p.name: sha256_file(p)
            for p in freeze_dir.iterdir()
            if p.is_file()
        }
        self.assertEqual(before, after)
        for name, digest in before.items():
            self.assertEqual(sha256_file(freeze_dir / name), digest)

    def test_T10_stored_pass_edit_rebound_rejected(self):
        """Stored FAIL→PASS with rebound hashes must fail semantic verify (pre-freeze)."""
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request(adapter_params={"mode": "force_fail", "expected_sha256": self.digest})
        result = orch.run_through_decision(req)
        self.assertEqual(result["decision"]["decision"], "FAIL")
        run = Path(result["audit_root"])
        decision = read_json(run / "DECISION.json")
        decision["decision"] = "PASS"
        decision["claim_result"] = "PASS"
        decision["reason"] = "TAMPERED_FALSE_PASS"
        write_json(run / "DECISION.json", decision)
        EvidenceCollector(BoundaryManager(run, []), run).bind_sha256sums()
        verify = orch.verify_run(run)
        self.assertTrue(verify["sha256sums_ok"])
        self.assertFalse(verify["semantic_ok"])
        self.assertFalse(verify["verify_ok"])
        self.assertFalse(verify["semantic_verification"]["match"])
        self.assertEqual(
            verify["semantic_verification"]["recomputed_decision"]["decision"],
            "FAIL",
        )

    def test_T11_raw_evidence_semantic_mismatch_rejected(self):
        """Hash-integrity-consistent package whose PASS conflicts with recomputed digest facts."""
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        self.assertEqual(result["decision"]["decision"], "PASS")
        run = Path(result["audit_root"])
        pinned = run / "pinned_target" / "README.txt"
        pinned.write_bytes(pinned.read_bytes() + b"\nTAMPER\n")
        # Keep stored PASS; rebind so SHA lists are internally consistent.
        EvidenceCollector(BoundaryManager(run, []), run).bind_sha256sums()
        verify = orch.verify_run(run)
        self.assertTrue(verify["sha256sums_ok"])
        self.assertFalse(verify["semantic_ok"])
        self.assertFalse(verify["verify_ok"])
        self.assertNotEqual(
            verify["semantic_verification"]["recomputed_decision"]["decision"],
            "PASS",
        )

    def test_T12_valid_frozen_hash_claim_still_verifies(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        run = Path(result["audit_root"])
        write_json(
            run / "HUMAN_REVIEW.json",
            {
                "status": "ACCEPTED",
                "reviewer": "phase6-t12",
                "notes": "clean path",
            },
        )
        orch.freeze_run(run, req.policy)
        verify = orch.verify_run(run)
        self.assertTrue(verify["sha256sums_ok"])
        self.assertTrue(verify["freeze_sums_ok"])
        self.assertTrue(verify["semantic_ok"])
        self.assertTrue(verify["verify_ok"])
        self.assertTrue(verify["semantic_verification"]["match"])
        self.assertTrue(verify["semantic_verification"]["decision_match"])
        self.assertTrue(verify["semantic_verification"]["final_decision_match"])
        self.assertEqual(
            verify["semantic_verification"]["recomputed_decision"]["decision"],
            "PASS",
        )

    def test_T13_FINAL_DECISION_false_promotion_rebound_rejected(self):
        """Frozen FINAL_DECISION false FULL promotion + rebound hashes must fail semantic verify."""
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        self.assertEqual(result["decision"]["decision"], "PASS")
        run = Path(result["audit_root"])
        write_json(
            run / "HUMAN_REVIEW.json",
            {
                "status": "ACCEPTED",
                "reviewer": "phase6.1-t13",
                "notes": "legitimate freeze then disposable FINAL_DECISION tamper",
            },
        )
        orch.freeze_run(run, req.policy)

        clean = orch.verify_run(run)
        self.assertTrue(clean["sha256sums_ok"])
        self.assertTrue(clean["freeze_sums_ok"])
        self.assertTrue(clean["semantic_ok"])
        self.assertTrue(clean["verify_ok"])
        self.assertTrue(clean["semantic_verification"]["final_decision_match"])

        # Disposable fixture copy: alter FINAL_DECISION semantics, keep DECISION honest,
        # rebind SHA manifests so hash integrity is internally consistent.
        fixture = self.out / "t13_fixture_copy"
        shutil.copytree(run, fixture)
        fd = next((fixture / "freeze").glob("*_FROZEN")) / "FINAL_DECISION.json"
        final_doc = read_json(fd)
        final_doc["decision"]["promoted_to_full"] = True
        final_doc["decision"]["broader_classification"] = "CRYPTO_SUPPORTED_E2E_FULL"
        final_doc["decision"]["promotion_note"] = "TAMPERED_FULL_PROMOTION"
        write_json(fd, final_doc)

        freeze_dir = fd.parent
        freeze_lines = []
        for p in sorted(freeze_dir.iterdir()):
            if p.is_file() and p.name != "SHA256SUMS.txt":
                freeze_lines.append(f"{sha256_file(p)}  {p.name}")
        (freeze_dir / "SHA256SUMS.txt").write_text(
            "\n".join(freeze_lines) + "\n", encoding="utf-8"
        )
        EvidenceCollector(BoundaryManager(fixture, []), fixture).bind_sha256sums()

        verify = orch.verify_run(fixture)
        self.assertTrue(verify["sha256sums_ok"])
        self.assertTrue(verify["freeze_sums_ok"])
        self.assertFalse(verify["semantic_ok"])
        self.assertFalse(verify["verify_ok"])
        self.assertTrue(verify["semantic_verification"]["decision_match"])
        self.assertFalse(verify["semantic_verification"]["final_decision_match"])
        self.assertEqual(
            verify["semantic_verification"]["recomputed_decision"]["promoted_to_full"],
            False,
        )
        self.assertNotEqual(
            verify["semantic_verification"]["final_decision_stored"]["broader_classification"],
            verify["semantic_verification"]["recomputed_decision"]["broader_classification"],
        )

    def test_failing_audit_preserved(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request(adapter_params={"mode": "force_fail", "expected_sha256": self.digest})
        result = orch.run_through_decision(req)
        self.assertEqual(result["decision"]["decision"], "FAIL")
        run = Path(result["audit_root"])
        self.assertTrue((run / "DECISION.json").is_file())
        self.assertFalse(result.get("frozen"))
        # no false PASS
        self.assertNotEqual(result["decision"]["claim_result"], "PASS")

    def test_incomplete_evidence(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request(adapter_params={"mode": "incomplete", "expected_sha256": self.digest})
        result = orch.run_through_decision(req)
        self.assertEqual(result["decision"]["decision"], "INCONCLUSIVE")
        self.assertEqual(result["decision"]["reason"], "INCOMPLETE_EVIDENCE")

    def test_human_review_blocks_freeze(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        run = Path(result["audit_root"])
        with self.assertRaises(HumanReviewRequired):
            orch.freeze_run(run, req.policy)

    def test_evidence_tamper_detected(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        run = Path(result["audit_root"])
        # Tamper an evidence file after binding
        victim = run / "DECISION.json"
        victim.write_text(victim.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        verify = orch.verify_run(run)
        self.assertFalse(verify["sha256sums_ok"])

    def test_boundary_fail_closed(self):
        orch = AuditOrchestrator(self.out / "runs")
        req = self._request()
        result = orch.run_through_decision(req)
        run = Path(result["audit_root"])
        vectors = json.loads((run / "evidence" / "raw" / "vectors.json").read_text(encoding="utf-8"))
        bv = next(v for v in vectors if v["id"] == "BV1_PROTECTED_BOUNDARY_WRITE_DENIED")
        self.assertEqual(bv["result"], "PASS")
        # Ensure nothing landed in protected dir
        evil = list(self.protected.glob("**/__weaver_forge_should_not_write__*"))
        self.assertEqual(evil, [])


if __name__ == "__main__":
    unittest.main()
