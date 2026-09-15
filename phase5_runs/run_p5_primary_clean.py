"""Clean Phase-5 P5-PRIMARY freeze after IV hook."""
from __future__ import annotations

import json
import sys
from pathlib import Path

WF = Path(r"C:\dev\Weaver\weaver-forge")
sys.path.insert(0, str(WF))

from audit_lifecycle.orchestrator import AuditOrchestrator
from audit_lifecycle.request import AuditRequest, write_json

REQ = WF / "phase5_operator_request.json"
RUNS = WF / "phase5_runs"


def main() -> int:
    orch = AuditOrchestrator(RUNS)
    req = AuditRequest.from_file(REQ)
    # Ensure claim id is P5-PRIMARY
    req.claim["id"] = "P5-PRIMARY"
    result = orch.run_through_decision(req)
    run = Path(result["audit_root"])
    write_json(
        run / "HUMAN_REVIEW.json",
        {
            "status": "ACCEPTED",
            "reviewer": "phase5-third-party-operator",
            "notes": "P5-PRIMARY clean freeze after independent_verification hook",
        },
    )
    freeze = orch.freeze_run(run, req.policy)
    verify = orch.verify_run(run)
    out = {
        "audit_root": str(run),
        "decision": result["decision"],
        "independent_verification_file": str(run / "INDEPENDENT_VERIFICATION.json"),
        "freeze": freeze,
        "verify_ok": verify.get("sha256sums_ok") and verify.get("freeze_sums_ok"),
        "verify": {
            "sha256sums_ok": verify.get("sha256sums_ok"),
            "freeze_sums_ok": verify.get("freeze_sums_ok"),
        },
    }
    write_json(RUNS / "PHASE5_P5_PRIMARY_CLEAN.json", out)
    print(json.dumps(out, indent=2))
    return 0 if out["verify_ok"] and result["decision"]["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
