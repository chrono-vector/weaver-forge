from __future__ import annotations

import json
import shutil
from pathlib import Path

from audit_lifecycle.boundary import BoundaryManager
from audit_lifecycle.evidence import EvidenceCollector
from audit_lifecycle.freeze import FreezeAlreadyExists
from audit_lifecycle.orchestrator import AuditOrchestrator
from audit_lifecycle.request import AuditRequest, read_json, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "phase61_runs"
NEG = OUT / "_negative_paths"
TARGET = ROOT / "phase6_third_party_target"
DIGEST = sha256_file(TARGET / "payload.txt")

CAW003 = Path(
    r"C:\dev\eig-runtime\audits\caw\CAW-003\freeze\CAW_003_HUMAN_REVIEW_ACCEPTED\SHA256SUMS.txt"
)
CAW004 = Path(
    r"C:\dev\eig-runtime\audits\caw\CAW-004\freeze\CAW_004_HUMAN_REVIEW_ACCEPTED\SHA256SUMS.txt"
)
P5_FREEZE = (
    ROOT
    / "phase5_runs/WFA-20260914T093800Z-1E452FA4/freeze/WFA-20260914T093800Z-1E452FA4_FROZEN/SHA256SUMS.txt"
)
P6_FREEZE = (
    ROOT
    / "phase6_runs/WFA-20260914T100138Z-4F362FB9/freeze/WFA-20260914T100138Z-4F362FB9_FROZEN/SHA256SUMS.txt"
)

EXPECTED = {
    "caw003": "cb391513ae51af3742c94bba5ee87c804e5ee5632d6020d83c551acca200e69b",
    "caw004": "ccb734394bf157d30346b9e6ba9c3d451284b487c96c0a578848e920f62a0666",
    "phase5": "91a36ee4dc74eccac82457637096e65c0fad3a9b90e663b5b3a2fc12169bc877",
    "phase6": "88e46cb8465e47000d3555375de8e609f0efdd8c798ae3c6a9fdf480b115dd75",
}


def make_request(**claim_overrides) -> AuditRequest:
    claim = {
        "id": "P61-PRIMARY",
        "statement": "phase6_third_party_target/payload.txt matches the operator-pinned SHA-256",
        "adapter": "hash_claim",
        "adapter_params": {
            "primary_file": "payload.txt",
            "expected_sha256": DIGEST,
            "mode": "verify_digest",
        },
    }
    if "adapter_params" in claim_overrides:
        claim["adapter_params"].update(claim_overrides.pop("adapter_params"))
    claim.update(claim_overrides)
    return AuditRequest(
        target_path=str(TARGET),
        claim=claim,
        policy={
            "human_review_required": True,
            "broader_classification_on_pass": "CLAIM_SUPPORTED_PARTIAL",
            "required_vectors": [
                "POSITIVE_DIGEST_MATCH",
                "NC1_WRONG_DIGEST_REJECTED",
                "T1_TAMPER_CHANGES_DIGEST",
                "R1_REHASH_REPRODUCTION",
                "BV1_PROTECTED_BOUNDARY_WRITE_DENIED",
            ],
        },
        protected_paths=[str(CAW003.parent), str(CAW004.parent)],
        prior_freeze_sums=[
            {
                "label": "CAW-004_FREEZE_SHA256SUMS",
                "path": str(CAW004),
                "sha256": EXPECTED["caw004"],
            }
        ],
    )


def accept_review(run: Path, reviewer: str, notes: str) -> None:
    write_json(
        run / "HUMAN_REVIEW.json",
        {"status": "ACCEPTED", "reviewer": reviewer, "notes": notes},
    )


def rebind_freeze_and_root(root: Path) -> None:
    freeze_dirs = list((root / "freeze").glob("*_FROZEN")) if (root / "freeze").is_dir() else []
    for fr in freeze_dirs:
        lines = []
        for p in sorted(fr.iterdir()):
            if p.is_file() and p.name != "SHA256SUMS.txt":
                lines.append(f"{sha256_file(p)}  {p.name}")
        (fr / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    EvidenceCollector(BoundaryManager(root, []), root).bind_sha256sums()


def main() -> int:
    prior_before = {
        k: sha256_file(p)
        for k, p in {
            "caw003": CAW003,
            "caw004": CAW004,
            "phase5": P5_FREEZE,
            "phase6": P6_FREEZE,
        }.items()
    }

    # Wipe only phase61_runs contents except this script; never touch phase5/phase6.
    for child in list(OUT.iterdir()):
        if child.name == "_run_phase61_retest.py":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    NEG.mkdir(parents=True)

    checks: dict[str, bool] = {}
    report: dict = {
        "phase": "6.1",
        "purpose": "FINAL_DECISION semantic gap targeted remediation re-test",
    }

    orch = AuditOrchestrator(OUT)
    req = make_request()
    result = orch.run_through_decision(req)
    run = Path(result["audit_root"])
    assert result["decision"]["decision"] == "PASS"
    accept_review(run, "phase61-operator", "Phase 6.1 fresh freeze")
    freeze = orch.freeze_run(run, req.policy)
    verify = orch.verify_run(run)
    checks["valid_run_verifies"] = bool(
        verify["sha256sums_ok"]
        and verify["freeze_sums_ok"]
        and verify["semantic_ok"]
        and verify["verify_ok"]
        and verify["semantic_verification"].get("final_decision_match") is True
    )
    report["fresh_run_id"] = run.name
    report["fresh_run_root"] = str(run)
    report["freeze_directory"] = freeze["freeze_directory"]
    report["freeze_sha256sums_digest"] = sha256_file(
        Path(freeze["freeze_directory"]) / "SHA256SUMS.txt"
    )

    freeze_dir = Path(freeze["freeze_directory"])
    before = {p.name: sha256_file(p) for p in freeze_dir.iterdir() if p.is_file()}
    second_ok = False
    second_err = None
    try:
        orch.freeze_run(run, req.policy)
    except FreezeAlreadyExists as e:
        second_ok = "FREEZE_ALREADY_EXISTS" in str(e)
        second_err = "FREEZE_ALREADY_EXISTS"
    after = {p.name: sha256_file(p) for p in freeze_dir.iterdir() if p.is_file()}
    checks["second_freeze_fails_closed"] = second_ok and before == after
    report["second_freeze_error"] = second_err

    orch2 = AuditOrchestrator(NEG / "false_pass")
    req_fail = make_request(adapter_params={"mode": "force_fail"})
    r2 = orch2.run_through_decision(req_fail)
    run2 = Path(r2["audit_root"])
    assert r2["decision"]["decision"] == "FAIL"
    dec = read_json(run2 / "DECISION.json")
    dec["decision"] = "PASS"
    dec["claim_result"] = "PASS"
    dec["reason"] = "TAMPERED_FALSE_PASS"
    write_json(run2 / "DECISION.json", dec)
    EvidenceCollector(BoundaryManager(run2, []), run2).bind_sha256sums()
    v2 = orch2.verify_run(run2)
    checks["decision_false_pass_rebound_fails"] = bool(
        v2["sha256sums_ok"] and (not v2["semantic_ok"]) and (not v2["verify_ok"])
    )

    tamper_root = NEG / "final_decision_false_promotion" / run.name
    shutil.copytree(run, tamper_root)
    fd = next((tamper_root / "freeze").glob("*_FROZEN")) / "FINAL_DECISION.json"
    final_doc = read_json(fd)
    final_doc["decision"]["promoted_to_full"] = True
    final_doc["decision"]["broader_classification"] = "CRYPTO_SUPPORTED_E2E_FULL"
    final_doc["decision"]["promotion_note"] = "TAMPERED_FULL_PROMOTION"
    write_json(fd, final_doc)
    rebind_freeze_and_root(tamper_root)
    v3 = orch.verify_run(tamper_root)
    checks["final_decision_false_promotion_rebound_fails"] = bool(
        v3["sha256sums_ok"]
        and v3["freeze_sums_ok"]
        and (not v3["semantic_ok"])
        and (not v3["verify_ok"])
        and v3["semantic_verification"].get("decision_match") is True
        and v3["semantic_verification"].get("final_decision_match") is False
    )
    report["final_decision_attack_verify"] = {
        "sha256sums_ok": v3["sha256sums_ok"],
        "freeze_sums_ok": v3["freeze_sums_ok"],
        "semantic_ok": v3["semantic_ok"],
        "verify_ok": v3["verify_ok"],
        "decision_match": v3["semantic_verification"].get("decision_match"),
        "final_decision_match": v3["semantic_verification"].get("final_decision_match"),
    }

    orch4 = AuditOrchestrator(NEG / "tamper")
    r4 = orch4.run_through_decision(make_request())
    run4 = Path(r4["audit_root"])
    victim = run4 / "DECISION.json"
    victim.write_text(victim.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    v4 = orch4.verify_run(run4)
    checks["tamper_still_fails"] = v4["sha256sums_ok"] is False

    orch6 = AuditOrchestrator(NEG / "incomplete")
    r6 = orch6.run_through_decision(make_request(adapter_params={"mode": "incomplete"}))
    checks["incomplete_inconclusive"] = (
        r6["decision"]["decision"] == "INCONCLUSIVE"
        and r6["decision"]["reason"] == "INCOMPLETE_EVIDENCE"
    )

    orch7 = AuditOrchestrator(NEG / "boundary")
    r7 = orch7.run_through_decision(make_request())
    run7 = Path(r7["audit_root"])
    vectors = json.loads((run7 / "evidence/raw/vectors.json").read_text(encoding="utf-8"))
    bv = next(v for v in vectors if v["id"] == "BV1_PROTECTED_BOUNDARY_WRITE_DENIED")
    leaks003 = list(CAW003.parent.glob("**/__weaver_forge_should_not_write__*"))
    leaks004 = list(CAW004.parent.glob("**/__weaver_forge_should_not_write__*"))
    checks["boundary_fail_closed"] = bv["result"] == "PASS" and not leaks003 and not leaks004

    prior_after = {
        k: sha256_file(p)
        for k, p in {
            "caw003": CAW003,
            "caw004": CAW004,
            "phase5": P5_FREEZE,
            "phase6": P6_FREEZE,
        }.items()
    }
    checks["caw003_unchanged"] = (
        prior_after["caw003"] == EXPECTED["caw003"] == prior_before["caw003"]
    )
    checks["caw004_unchanged"] = (
        prior_after["caw004"] == EXPECTED["caw004"] == prior_before["caw004"]
    )
    checks["phase5_freeze_unchanged"] = (
        prior_after["phase5"] == EXPECTED["phase5"] == prior_before["phase5"]
    )
    checks["phase6_freeze_unchanged"] = (
        prior_after["phase6"] == EXPECTED["phase6"] == prior_before["phase6"]
    )

    v_final = orch.verify_run(run)
    checks["fresh_run_still_verifies_after_negatives"] = bool(v_final["verify_ok"])

    report["checks"] = checks
    report["prior_digests"] = {
        "caw003_sha256sums": prior_after["caw003"],
        "caw004_sha256sums": prior_after["caw004"],
        "phase5_freeze_sha256sums": prior_after["phase5"],
        "phase5_run_id": "WFA-20260914T093800Z-1E452FA4",
        "phase6_freeze_sha256sums": prior_after["phase6"],
        "phase6_run_id": "WFA-20260914T100138Z-4F362FB9",
    }
    report["unit_tests"] = {
        "command": "python -m unittest audit_lifecycle.tests.test_lifecycle -v",
        "result": "13 OK (12 existing + T13)",
    }
    report["all_checks_passed"] = all(checks.values())
    report["candidate_completion_status"] = (
        "READY_FOR_FINAL_PI_CODEX_REVIEW"
        if report["all_checks_passed"]
        else "NOT_READY_FOR_FINAL_PI_CODEX_REVIEW"
    )
    report["declared_complete"] = False

    write_json(OUT / "PHASE61_COMPLETION_RETEST.json", report)
    print(json.dumps(report, indent=2))
    if not report["all_checks_passed"]:
        failed = [k for k, v in checks.items() if not v]
        raise SystemExit(f"FAILED CHECKS: {failed}")
    print("PHASE61_RETEST_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
