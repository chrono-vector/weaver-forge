"""Failure / interruption fail-closed tests."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest import mock

import pytest

from campaign_runner_v0.bindings import load_campaign_bindings
from campaign_runner_v0.capabilities import require_capability
from campaign_runner_v0.evidence import load_synthetic_test_evidence, verify_frozen_audit_reuse
from campaign_runner_v0.loaders import verify_source_integrity, load_workspace_artifacts
from campaign_runner_v0.runner import run_campaign
from campaign_runner_v0.safety import SafetyError, resolve_confined


def test_source_hash_mismatch_fail_closed(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    with mock.patch(
        "campaign_runner_v0.loaders.sha256_file",
        return_value="0" * 64,
    ):
        with pytest.raises(SafetyError, match="source hash mismatch"):
            verify_source_integrity(aurora_workspace, arts["source_manifest"])


def test_corrupted_campaign_state_fail_closed(aurora_workspace, policy_path):
    campaign_id = "aurora_corrupt_state_test"
    cdir = aurora_workspace / "campaigns" / campaign_id
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "CAMPAIGN_STATE.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(SafetyError, match="corrupted campaign state"):
        run_campaign(
            workspace=aurora_workspace,
            campaign_id=campaign_id,
            policy_path=policy_path,
        )


def test_path_traversal_rejected(aurora_workspace):
    with pytest.raises(SafetyError, match="path traversal"):
        resolve_confined(aurora_workspace, "../audit_lifecycle/cli.py")


def test_malicious_metadata_absolute_escape(aurora_workspace):
    with pytest.raises(SafetyError):
        resolve_confined(aurora_workspace, r"C:\Windows\System32\drivers\etc\hosts")


def test_unsupported_capability():
    with pytest.raises(KeyError, match="unsupported capability"):
        require_capability("nonexistent_worker_fleet")


def test_missing_frozen_package(aurora_workspace):
    bindings = load_campaign_bindings(aurora_workspace)
    with mock.patch(
        "campaign_runner_v0.evidence.resolve_confined",
        side_effect=lambda root, rel: Path("/nonexistent/frozen"),
    ):
        with pytest.raises(SafetyError, match="missing referenced frozen package"):
            verify_frozen_audit_reuse(aurora_workspace, "AUR-A-001", bindings)


def test_missing_evidence_harness(aurora_workspace, tmp_path):
    from campaign_runner_v0.evidence import bind_protocol_harness

    bindings = load_campaign_bindings(aurora_workspace)
    with mock.patch(
        "campaign_runner_v0.evidence.resolve_confined",
        return_value=tmp_path / "missing.json",
    ):
        with pytest.raises(SafetyError, match="missing protocol harness"):
            bind_protocol_harness(aurora_workspace, "AUR-A-005", bindings)


def test_duplicate_invocation_idempotent(aurora_workspace, policy_path):
    campaign_id = "aurora_dup_invocation_test"
    r1 = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    r2 = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert r1["state_counts"] == r2["state_counts"]
    assert r2["campaign_state"]["claims"]["AUR-A-001"]["state"] == "PASS"
    reuse = [
        e
        for e in r2["evidence_register"]["entries"]
        if e.get("kind") == "FROZEN_WEAVER_AUDIT_REUSE"
    ]
    assert len(reuse) == 2


def test_stale_lock_takeover_and_fresh_lock_blocks(aurora_workspace, policy_path):
    campaign_id = "aurora_lock_test"
    cdir = aurora_workspace / "campaigns" / campaign_id
    cdir.mkdir(parents=True, exist_ok=True)
    lock_path = cdir / "campaign.lock"
    lock_path.write_text(
        json.dumps({"owner": "other", "acquired_at_epoch": time.time(), "pid": 1}),
        encoding="utf-8",
    )
    with pytest.raises(SafetyError, match="campaign lock held"):
        run_campaign(
            workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
        )
    lock_path.write_text(
        json.dumps(
            {"owner": "other", "acquired_at_epoch": time.time() - 99999, "pid": 1}
        ),
        encoding="utf-8",
    )
    result = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
        force_unlock_stale=True,
    )
    assert result["ok"] is True


def test_human_denial_remains_blocked(aurora_workspace, policy_path):
    result = run_campaign(
        workspace=aurora_workspace,
        campaign_id="aurora_human_denial_test",
        policy_path=policy_path,
    )
    assert result["campaign_state"]["claims"]["AUR-A-021"]["state"] == "BLOCKED_HUMAN"
    assert any(
        b["claim_id"] == "AUR-A-021" for b in result["blocker_queue"]["blockers"]
    )


def test_authorization_expiry_policy_still_denies_network(policy_path):
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert policy["network"] == "denied"
    assert policy["external_services"] == "denied"
    assert policy["target_code_execution"] == "denied"


def test_synthetic_without_markers_rejected(tmp_path, aurora_workspace):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"claim_id": "AUR-A-008", "evidence_id": "x"}), encoding="utf-8")
    with pytest.raises(SafetyError, match="TEST_ONLY"):
        load_synthetic_test_evidence(bad, aurora_workspace)


def test_worker_failure_fail_closed(aurora_workspace, policy_path):
    campaign_id = "aurora_worker_fail_test"
    with mock.patch(
        "campaign_runner_v0.runner.verify_frozen_audit_reuse",
        side_effect=SafetyError("simulated worker failure"),
    ):
        result = run_campaign(
            workspace=aurora_workspace,
            campaign_id=campaign_id,
            policy_path=policy_path,
        )
    claims = result["campaign_state"]["claims"]
    assert claims["AUR-A-001"]["state"] in {"BLOCKED_EVIDENCE", "BLOCKED_AUTHORITY"}
    assert claims["AUR-A-005"]["state"] == "INCONCLUSIVE"
    assert len(claims) == 23


def test_mid_run_interruption_recovery(aurora_workspace, policy_path):
    campaign_id = "aurora_interrupt_recovery_test"
    run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    cdir = aurora_workspace / "campaigns" / campaign_id
    lock_path = cdir / "campaign.lock"
    lock_path.write_text(
        json.dumps(
            {
                "owner": "crashed-worker",
                "acquired_at_epoch": time.time() - 99999,
                "pid": 999,
            }
        ),
        encoding="utf-8",
    )
    result = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
        force_unlock_stale=True,
    )
    assert result["ok"] is True
    assert result["claim_count"] == 23
    assert result["campaign_state"]["claims"]["AUR-A-001"]["state"] == "PASS"


def test_report_generation_failure_fail_closed(aurora_workspace, policy_path):
    bindings = load_campaign_bindings(aurora_workspace)
    with mock.patch(
        "campaign_runner_v0.runner.build_campaign_report",
        side_effect=RuntimeError("report boom"),
    ):
        with pytest.raises(RuntimeError, match="report boom"):
            run_campaign(
                workspace=aurora_workspace,
                campaign_id="aurora_report_fail_test",
                policy_path=policy_path,
            )
    for meta in bindings.reuse_audits.values():
        assert (aurora_workspace / meta["frozen_relpath"] / "SHA256SUMS.txt").is_file()


def test_policy_cannot_enable_frozen_rewrite(aurora_workspace, tmp_path):
    bad_policy = tmp_path / "bad_policy.json"
    bad_policy.write_text(
        json.dumps(
            {
                "network": "denied",
                "allow_frozen_rewrite": True,
                "allow_audit_lifecycle_write": False,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(SafetyError, match="frozen package rewrites"):
        run_campaign(
            workspace=aurora_workspace,
            campaign_id="aurora_bad_policy_test",
            policy_path=bad_policy,
        )
