"""B2 second-campaign generalization: Aurora is fixture, not algorithm."""

from __future__ import annotations

import shutil
from pathlib import Path

from campaign_runner_v0.runner import run_campaign

FIXTURE_WS = (
    Path(__file__).resolve().parent / "fixtures" / "second_campaign_workspace_TEST_ONLY"
)


def test_second_campaign_one_invocation_without_product_edits(policy_path, tmp_path):
    assert FIXTURE_WS.is_dir()
    ws = tmp_path / "second_campaign_workspace_TEST_ONLY"
    shutil.copytree(FIXTURE_WS, ws)

    result = run_campaign(
        workspace=ws,
        campaign_id="second_campaign_operational_v1",
        policy_path=policy_path,
    )
    assert result["ok"] is True
    assert result["claim_count"] == 23
    counts = {k: v for k, v in result["state_counts"].items() if v}
    assert counts.get("PASS") == 2
    assert result["state_counts"].get("FAIL", 0) == 0
    assert counts.get("INCONCLUSIVE") == 4
    assert counts.get("BLOCKED_HUMAN") == 1
    assert counts.get("BLOCKED_EVIDENCE") == 2
    assert counts.get("IMPLEMENTATION_REQUIRED") == 8
    assert counts.get("NORMATIVE_NOT_FACTUAL") == 3
    assert counts.get("SYMBOLIC_NOT_EMPIRICAL") == 2
    assert counts.get("HISTORICAL_CORROBORATION_REQUIRED") == 1

    claims = result["campaign_state"]["claims"]
    assert set(claims) == {f"TST-{i:03d}" for i in range(1, 24)}
    assert claims["TST-001"]["state"] == "PASS"
    assert claims["TST-002"]["state"] == "PASS"
    assert claims["TST-005"]["state"] == "INCONCLUSIVE"
    assert claims["TST-021"]["state"] == "BLOCKED_HUMAN"
    assert claims["TST-006"]["state"] == "IMPLEMENTATION_REQUIRED"
    assert claims["TST-003"]["state"] == "BLOCKED_EVIDENCE"

    cdir = ws / "campaigns" / "second_campaign_operational_v1"
    for name in (
        "CAMPAIGN_STATE.json",
        "EVIDENCE_REGISTER.json",
        "BLOCKER_QUEUE.json",
        "CAMPAIGN_REPORT.json",
        "VERIFICATION_PLAN.json",
    ):
        assert (cdir / name).is_file()

    assert result["blocker_queue"]["count"] >= 1
    assert any(e.get("kind") == "FROZEN_WEAVER_AUDIT_REUSE" for e in result["evidence_register"]["entries"])
    assert any(e.get("kind") == "PROTOCOL_HARNESS_BIND" for e in result["evidence_register"]["entries"])

    # No Aurora claim IDs in this fixture run.
    assert not any(cid.startswith("AUR-A-") for cid in claims)
