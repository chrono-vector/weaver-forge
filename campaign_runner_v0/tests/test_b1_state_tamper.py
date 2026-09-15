"""B1 adversarial tests: CAMPAIGN_STATE must never mint PASS/FAIL alone."""

from __future__ import annotations

import json
from pathlib import Path

from campaign_runner_v0.runner import run_campaign
from campaign_runner_v0.state_revalidation import compute_state_integrity_digest

FIXTURE = (
    Path(__file__).resolve().parent / "fixtures" / "synthetic_aur_a_008_TEST_ONLY.json"
)


def _tamper_claim(cdir: Path, claim_id: str, **fields) -> None:
    path = cdir / "CAMPAIGN_STATE.json"
    st = json.loads(path.read_text(encoding="utf-8"))
    row = dict(st["claims"][claim_id])
    row.update(fields)
    st["claims"][claim_id] = row
    path.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tamper_and_recompute_digest(cdir: Path, claim_id: str, **fields) -> None:
    path = cdir / "CAMPAIGN_STATE.json"
    st = json.loads(path.read_text(encoding="utf-8"))
    row = dict(st["claims"][claim_id])
    row.update(fields)
    st["claims"][claim_id] = row
    digest = compute_state_integrity_digest(st["claims"], st["evidence_register"])
    st["state_integrity"] = {
        "digest": digest,
        "algorithm": "sha256",
        "covers": ["claims", "evidence_register.entries"],
        "note": "attacker-recomputed",
    }
    path.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_b1_a_false_aur_a_003_pass_rejected(aurora_workspace, policy_path):
    campaign_id = "b1_a_false_pass_003"
    first = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert first["state_counts"]["PASS"] == 2
    assert first["campaign_state"]["claims"]["AUR-A-003"]["state"] == "BLOCKED_EVIDENCE"

    cdir = aurora_workspace / "campaigns" / campaign_id
    _tamper_claim(
        cdir,
        "AUR-A-003",
        state="PASS",
        reason="TAMPERED_FALSE_PASS",
    )
    second = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert second["campaign_state"]["claims"]["AUR-A-003"]["state"] == "BLOCKED_EVIDENCE"
    assert second["state_counts"]["PASS"] == 2
    rejected = {r["claim_id"] for r in second["revalidation"]["rejected_terminals"]}
    assert "AUR-A-003" in rejected


def test_b1_b_civic_protocol_false_pass_rejected(aurora_workspace, policy_path):
    campaign_id = "b1_b_civic_false_pass"
    first = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert first["campaign_state"]["claims"]["AUR-A-005"]["state"] == "INCONCLUSIVE"
    cdir = aurora_workspace / "campaigns" / campaign_id
    _tamper_claim(cdir, "AUR-A-005", state="PASS", reason="TAMPERED_PROTOCOL_AS_CIVIC")
    second = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert second["campaign_state"]["claims"]["AUR-A-005"]["state"] == "INCONCLUSIVE"
    assert second["state_counts"]["PASS"] == 2


def test_b1_c_implementation_required_false_pass_rejected(aurora_workspace, policy_path):
    campaign_id = "b1_c_impl_false_pass"
    run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    cdir = aurora_workspace / "campaigns" / campaign_id
    _tamper_claim(cdir, "AUR-A-006", state="PASS", reason="TAMPERED_IMPL_PASS")
    second = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert second["campaign_state"]["claims"]["AUR-A-006"]["state"] == "IMPLEMENTATION_REQUIRED"
    assert second["state_counts"]["PASS"] == 2


def test_b1_d_human_blocked_false_pass_rejected(aurora_workspace, policy_path):
    campaign_id = "b1_d_human_false_pass"
    run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    cdir = aurora_workspace / "campaigns" / campaign_id
    _tamper_claim(cdir, "AUR-A-021", state="PASS", reason="TAMPERED_HUMAN_PASS")
    second = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert second["campaign_state"]["claims"]["AUR-A-021"]["state"] == "BLOCKED_HUMAN"
    assert second["state_counts"]["PASS"] == 2


def test_b1_e_tamper_plus_recomputed_digest_still_rejected(aurora_workspace, policy_path):
    campaign_id = "b1_e_digest_recomputed"
    run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    cdir = aurora_workspace / "campaigns" / campaign_id
    _tamper_and_recompute_digest(
        cdir,
        "AUR-A-003",
        state="PASS",
        reason="TAMPERED_FALSE_PASS",
    )
    second = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert second["campaign_state"]["claims"]["AUR-A-003"]["state"] == "BLOCKED_EVIDENCE"
    assert second["state_counts"]["PASS"] == 2
    assert any(
        r["claim_id"] == "AUR-A-003" for r in second["revalidation"]["rejected_terminals"]
    )


def test_b1_f_legitimate_completed_reuse_efficient(aurora_workspace, policy_path):
    campaign_id = "b1_f_legitimate_reuse"
    first = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert first["campaign_state"]["claims"]["AUR-A-001"]["state"] == "PASS"
    assert first["campaign_state"]["claims"]["AUR-A-002"]["state"] == "PASS"
    second = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert second["state_counts"]["PASS"] == 2
    actions = {
        r["action"]
        for r in second["receipts"]
        if r["claim_id"] in {"AUR-A-001", "AUR-A-002"}
    }
    assert "SKIP_VALIDATED_REUSE" in actions
    assert "REUSE_FROZEN_AUDIT" not in actions


def test_b1_resume_plus_false_state_tamper(aurora_workspace, policy_path):
    import shutil

    campaign_id = "b1_resume_plus_tamper"
    cdir = aurora_workspace / "campaigns" / campaign_id
    if cdir.exists():
        shutil.rmtree(cdir)
    run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    resumed = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
        synthetic_evidence_paths=[FIXTURE],
    )
    assert resumed["campaign_state"]["claims"]["AUR-A-008"]["state"] == "INCONCLUSIVE"
    assert resumed["campaign_state"]["claims"]["AUR-A-001"]["state"] == "PASS"

    cdir = aurora_workspace / "campaigns" / campaign_id
    _tamper_claim(cdir, "AUR-A-003", state="PASS", reason="TAMPERED_FALSE_PASS")
    third = run_campaign(
        workspace=aurora_workspace, campaign_id=campaign_id, policy_path=policy_path
    )
    assert third["campaign_state"]["claims"]["AUR-A-008"]["state"] == "INCONCLUSIVE"
    assert third["campaign_state"]["claims"]["AUR-A-001"]["state"] == "PASS"
    assert third["campaign_state"]["claims"]["AUR-A-003"]["state"] == "BLOCKED_EVIDENCE"
    assert third["state_counts"]["PASS"] == 2
