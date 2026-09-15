"""Phase 0 planner / safety / dry-run gate tests."""

from __future__ import annotations

import json
from pathlib import Path

from campaign_runner_v0.loaders import (
    load_workspace_artifacts,
    validate_claim_register,
    validate_compatibility,
    validate_routing,
    verify_source_integrity,
)
from campaign_runner_v0.models import EXPECTED_SOURCE_HASHES, KNOWN_REUSE_AUDITS
from campaign_runner_v0.planner import build_verification_plan
from campaign_runner_v0.runner import run_campaign


def test_all_23_claims_in_plan(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    claims = validate_claim_register(arts["claim_register"])
    ids = {c["claim_id"] for c in claims}
    assert len(ids) == 23
    routes = validate_routing(arts["verification_routing"], ids)
    compat = validate_compatibility(arts["weaver_compatibility"], ids)
    plan = build_verification_plan(claims, routes, compat, campaign_id="t")
    assert plan["claim_count"] == 23
    plan_ids = [c["claim_id"] for c in plan["claims"]]
    assert sorted(plan_ids) == sorted(ids)
    assert len(plan_ids) == len(set(plan_ids))


def test_routing_deterministic(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    claims = validate_claim_register(arts["claim_register"])
    ids = {c["claim_id"] for c in claims}
    routes = validate_routing(arts["verification_routing"], ids)
    compat = validate_compatibility(arts["weaver_compatibility"], ids)
    p1 = build_verification_plan(claims, routes, compat, campaign_id="t")
    p2 = build_verification_plan(claims, routes, compat, campaign_id="t")
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)


def test_source_hashes_match(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    result = verify_source_integrity(aurora_workspace, arts["source_manifest"])
    assert result["status"] == "SOURCE_IDENTITY_VERIFIED"
    assert result["sources"]["SOURCE_A"]["observed_sha256"] == EXPECTED_SOURCE_HASHES["SOURCE_A"]
    assert result["sources"]["SOURCE_B"]["observed_sha256"] == EXPECTED_SOURCE_HASHES["SOURCE_B"]


def test_aur_001_002_identified_for_reuse(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    claims = validate_claim_register(arts["claim_register"])
    ids = {c["claim_id"] for c in claims}
    routes = validate_routing(arts["verification_routing"], ids)
    compat = validate_compatibility(arts["weaver_compatibility"], ids)
    plan = build_verification_plan(claims, routes, compat, campaign_id="t")
    by_id = {c["claim_id"]: c for c in plan["claims"]}
    assert by_id["AUR-A-001"]["reuse_existing_audit"] is True
    assert by_id["AUR-A-002"]["reuse_existing_audit"] is True
    assert by_id["AUR-A-001"]["planned_state"] == "PASS"
    assert by_id["AUR-A-002"]["planned_state"] == "PASS"
    for cid, meta in KNOWN_REUSE_AUDITS.items():
        assert (aurora_workspace / meta["frozen_relpath"]).is_dir()


def test_dry_run_writes_nothing_to_frozen(aurora_workspace, policy_path, tmp_path):
    # Snapshot frozen SHA256SUMS digests before dry-run.
    frozen_files = list(aurora_workspace.glob("runs/*/freeze/*_FROZEN/SHA256SUMS.txt"))
    before = {str(p): p.read_bytes() for p in frozen_files}
    # Also ensure dry-run does not create campaign dir when using unique id under campaigns
    # — dry_run skips writes entirely.
    campaign_id = "dry_run_phase0_test"
    result = run_campaign(
        workspace=aurora_workspace,
        campaign_id=campaign_id,
        policy_path=policy_path,
        dry_run=True,
    )
    assert result["ok"] is True
    assert result["claim_count"] == 23
    assert result["dry_run"] is True
    cdir = aurora_workspace / "campaigns" / campaign_id
    assert not cdir.exists()
    after = {str(p): p.read_bytes() for p in frozen_files}
    assert before == after
