"""Resume tests with TEST_ONLY synthetic evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from campaign_runner_v0.models import KNOWN_REUSE_AUDITS
from campaign_runner_v0.runner import run_campaign

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "synthetic_aur_a_008_TEST_ONLY.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_resume_with_synthetic_advances_only_affected_branch(
    aurora_workspace, policy_path, tmp_path
):
    campaign_id = "aurora_resume_test_v1"

    # Baseline run.
    first = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
    )
    assert first["campaign_state"]["claims"]["AUR-A-008"]["state"] == "BLOCKED_EVIDENCE"
    assert first["campaign_state"]["claims"]["AUR-A-001"]["state"] == "PASS"

    frozen_before = {}
    for meta in KNOWN_REUSE_AUDITS.values():
        for name in ("SHA256SUMS.txt", "MANIFEST.json", "FINAL_DECISION.json"):
            p = aurora_workspace / meta["frozen_relpath"] / name
            frozen_before[str(p)] = _digest(p)

    # Capture unaffected claim updated_at before resume.
    before_states = {
        cid: dict(row)
        for cid, row in first["campaign_state"]["claims"].items()
        if cid != "AUR-A-008"
    }

    second = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
        synthetic_evidence_paths=[FIXTURE],
    )

    claims = second["campaign_state"]["claims"]
    assert claims["AUR-A-008"]["state"] == "INCONCLUSIVE"
    assert claims["AUR-A-008"].get("TEST_ONLY") is True
    assert claims["AUR-A-008"].get("NOT_REAL_AURORA_EVIDENCE") is True
    assert claims["AUR-A-001"]["state"] == "PASS"
    assert claims["AUR-A-002"]["state"] == "PASS"

    # Unaffected immutable / furthest claims remain same state.
    for cid, prev in before_states.items():
        assert claims[cid]["state"] == prev["state"]

    # Synthetic evidence present; not admitted as canonical Aurora.
    entries = second["evidence_register"]["entries"]
    syn = [e for e in entries if e.get("TEST_ONLY")]
    assert syn, "expected synthetic evidence entry"
    assert all(e.get("canonical_aurora_admission") is False for e in syn)

    # Frozen untouched.
    for path, dig in frozen_before.items():
        assert _digest(Path(path)) == dig

    # No duplicate freeze / rebind of frozen packages — reuse entries still single.
    reuse = [e for e in entries if e.get("kind") == "FROZEN_WEAVER_AUDIT_REUSE"]
    assert len(reuse) == 2

    # Receipts show skip for unaffected immutable.
    receipts_path = (
        aurora_workspace / "campaigns" / campaign_id / "worker_receipts.jsonl"
    )
    lines = receipts_path.read_text(encoding="utf-8").strip().splitlines()
    actions = [json.loads(x) for x in lines]
    skip_001 = [
        r
        for r in actions
        if r.get("claim_id") == "AUR-A-001"
        and r.get("action") == "SKIP_IMMUTABLE_COMPLETED"
    ]
    assert skip_001, "AUR-A-001 should be skipped on resume"
    syn_actions = [
        r for r in actions if r.get("action") == "APPLY_TEST_ONLY_SYNTHETIC"
    ]
    assert syn_actions

    # Synthetic must never appear under canonical audits/runs as real evidence file.
    assert not (aurora_workspace / "audits" / "AUR-A-008" / "SYNTHETIC.json").exists()
