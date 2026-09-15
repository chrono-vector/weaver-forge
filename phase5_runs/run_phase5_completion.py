"""Phase 5 third-party-style completion runner for Weaver Forge audit_lifecycle."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

WF = Path(r"C:\dev\Weaver\weaver-forge")
sys.path.insert(0, str(WF))

from audit_lifecycle.orchestrator import AuditOrchestrator
from audit_lifecycle.request import AuditRequest, sha256_file, write_json

RUNS = WF / "phase5_runs"
TARGET = WF / "phase5_third_party_target"
REQ = WF / "phase5_operator_request.json"
CAW004_SUMS = Path(
    r"C:\dev\eig-runtime\audits\caw\CAW-004\freeze\CAW_004_HUMAN_REVIEW_ACCEPTED\SHA256SUMS.txt"
)


def load_base_request() -> dict:
    return json.loads(REQ.read_text(encoding="utf-8"))


def main() -> int:
    report = {"paths": {}}
    orch = AuditOrchestrator(RUNS)

    # --- 1 already partially done: find existing PASS run or create ---
    existing = sorted(RUNS.glob("WFA-*"), key=lambda p: p.name)
    happy = None
    for d in existing:
        dec = d / "DECISION.json"
        if dec.is_file():
            data = json.loads(dec.read_text(encoding="utf-8"))
            if data.get("decision") == "PASS" and not (d / "FREEZE_STATUS.json").is_file():
                happy = d
                break
    if happy is None:
        result = orch.run_through_decision(AuditRequest.from_file(REQ))
        happy = Path(result["audit_root"])
        report["paths"]["happy_created"] = str(happy)
    else:
        report["paths"]["happy_existing"] = str(happy)

    write_json(
        happy / "HUMAN_REVIEW.json",
        {
            "status": "ACCEPTED",
            "reviewer": "phase5-third-party-operator",
            "notes": "Explicit policy human_review_required gate",
        },
    )
    req = AuditRequest.from_file(REQ)
    freeze = orch.freeze_run(happy, req.policy)
    verify = orch.verify_run(happy)
    report["happy"] = {
        "freeze": freeze,
        "verify": verify,
        "decision": json.loads((happy / "DECISION.json").read_text(encoding="utf-8")),
    }

    caw004_digest = sha256_file(CAW004_SUMS)
    report["caw004_freeze_digest"] = caw004_digest
    report["caw004_unchanged_expected"] = "ccb734394bf157d30346b9e6ba9c3d451284b487c96c0a578848e920f62a0666"
    report["caw004_unchanged"] = caw004_digest == report["caw004_unchanged_expected"]

    # --- 2 failing ---
    fail_data = load_base_request()
    fail_data["claim"]["id"] = "P5-FAIL"
    fail_data["claim"]["adapter_params"]["mode"] = "force_fail"
    fail_req = AuditRequest.from_dict(fail_data)
    fail_result = orch.run_through_decision(fail_req)
    report["failing"] = fail_result["decision"]

    # --- 3 incomplete ---
    inc_data = load_base_request()
    inc_data["claim"]["id"] = "P5-INCOMPLETE"
    inc_data["claim"]["adapter_params"]["mode"] = "incomplete"
    inc_result = orch.run_through_decision(AuditRequest.from_dict(inc_data))
    report["incomplete"] = inc_result["decision"]

    # --- 4 evidence tamper ---
    tamper_data = load_base_request()
    tamper_data["claim"]["id"] = "P5-TAMPER"
    tamper_result = orch.run_through_decision(AuditRequest.from_dict(tamper_data))
    tamper_run = Path(tamper_result["audit_root"])
    victim = tamper_run / "DECISION.json"
    victim.write_text(victim.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    tamper_verify = orch.verify_run(tamper_run)
    report["tamper"] = {
        "pre_tamper_decision": tamper_result["decision"]["decision"],
        "verify_after_tamper": tamper_verify,
    }

    # --- 5 boundary probe absence in protected freeze ---
    prot = Path(
        r"C:\dev\eig-runtime\audits\caw\CAW-004\freeze\CAW_004_HUMAN_REVIEW_ACCEPTED"
    )
    probes = list(prot.glob("**/*weaver_forge*")) + list(prot.glob("**/__wf_deny__*"))
    report["boundary"] = {
        "probe_files_in_caw004_freeze": [str(p) for p in probes],
        "fail_closed": len(probes) == 0,
        "happy_bv": report["happy"]["decision"]["vectors"].get(
            "BV1_PROTECTED_BOUNDARY_WRITE_DENIED"
        ),
    }

    # Aggregate gate
    report["phase5_checks"] = {
        "normal_success_frozen": bool(report["happy"]["freeze"].get("freeze_performed"))
        and report["happy"]["verify"].get("sha256sums_ok")
        and report["happy"]["verify"].get("freeze_sums_ok")
        and report["happy"]["decision"]["decision"] == "PASS",
        "failing_audit_no_false_pass": report["failing"]["decision"] == "FAIL",
        "incomplete_no_false_pass": report["incomplete"]["decision"] == "INCONCLUSIVE",
        "tamper_detected": report["tamper"]["verify_after_tamper"].get("sha256sums_ok")
        is False,
        "boundary_fail_closed": report["boundary"]["fail_closed"]
        and report["boundary"]["happy_bv"] == "PASS",
        "prior_freeze_unmutated": report["caw004_unchanged"],
    }
    report["phase5_pass"] = all(report["phase5_checks"].values())

    out = RUNS / "PHASE5_COMPLETION_REPORT.json"
    write_json(out, report)
    print(json.dumps(report, indent=2))
    print("PHASE5_PASS" if report["phase5_pass"] else "PHASE5_FAIL", flush=True)
    return 0 if report["phase5_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
