"""Phase 1 real Aurora one-invocation acceptance tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

from campaign_runner_v0.models import KNOWN_REUSE_AUDITS
from campaign_runner_v0.runner import run_campaign


EXPECTED_COUNTS = {
    "PASS": 2,
    "FAIL": 0,
    "INCONCLUSIVE": 4,
    "BLOCKED_HUMAN": 1,
    "BLOCKED_EVIDENCE": 2,
    "IMPLEMENTATION_REQUIRED": 8,
    "NORMATIVE_NOT_FACTUAL": 3,
    "SYMBOLIC_NOT_EMPIRICAL": 2,
    "HISTORICAL_CORROBORATION_REQUIRED": 1,
}


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_one_invocation_processes_all_23(aurora_workspace, policy_path):
    # Use dedicated campaign id for acceptance so re-runs are clean-ish;
    # real operational id also exercised by CLI later.
    campaign_id = "aurora_operational_v1"
    # Snapshot frozen packages.
    frozen_digests = {}
    for meta in KNOWN_REUSE_AUDITS.values():
        sums = aurora_workspace / meta["frozen_relpath"] / "SHA256SUMS.txt"
        frozen_digests[str(sums)] = _digest(sums)
        for name in ("MANIFEST.json", "FINAL_DECISION.json"):
            p = aurora_workspace / meta["frozen_relpath"] / name
            frozen_digests[str(p)] = _digest(p)

    result = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
        dry_run=False,
    )
    assert result["ok"] is True
    assert result["claim_count"] == 23
    counts = result["state_counts"]
    for k, v in EXPECTED_COUNTS.items():
        assert counts.get(k, 0) == v, f"{k}: expected {v} got {counts.get(k)}"

    claims = result["campaign_state"]["claims"]
    assert claims["AUR-A-001"]["state"] == "PASS"
    assert claims["AUR-A-002"]["state"] == "PASS"
    assert claims["AUR-A-005"]["state"] == "INCONCLUSIVE"
    assert claims["AUR-A-009"]["state"] == "INCONCLUSIVE"
    assert claims["AUR-A-012"]["state"] == "INCONCLUSIVE"
    assert claims["AUR-A-018"]["state"] == "INCONCLUSIVE"
    assert claims["AUR-A-021"]["state"] == "BLOCKED_HUMAN"
    assert claims["AUR-A-003"]["state"] == "BLOCKED_EVIDENCE"
    assert claims["AUR-A-008"]["state"] == "BLOCKED_EVIDENCE"
    assert claims["AUR-A-006"]["state"] == "IMPLEMENTATION_REQUIRED"
    assert claims["AUR-B-REL-001"]["state"] == "HISTORICAL_CORROBORATION_REQUIRED"

    cdir = aurora_workspace / "campaigns" / campaign_id
    for name in (
        "CAMPAIGN_STATE.json",
        "EVIDENCE_REGISTER.json",
        "BLOCKER_QUEUE.json",
        "CAMPAIGN_REPORT.json",
        "VERIFICATION_PLAN.json",
        "CAMPAIGN_MATRIX.md",
        "CAMPAIGN_INDEX.md",
    ):
        assert (cdir / name).is_file(), name

    assert result["blocker_queue"]["finite"] is True
    assert result["blocker_queue"]["count"] >= 1

    # Frozen packages unchanged.
    for path, dig in frozen_digests.items():
        assert _digest(Path(path)) == dig

    # No false epistemic promotion flags.
    for row in claims.values():
        assert row.get("protocol_promoted_to_civic_pass") is not True
        assert row.get("promotes_content_truth") is not True
        assert row.get("treated_proposal_as_implemented") is not True
