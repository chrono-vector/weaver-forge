"""Phase 0 planner / safety / dry-run gate tests."""

from __future__ import annotations

import json

from campaign_runner_v0.bindings import load_campaign_bindings
from campaign_runner_v0.loaders import (
    load_workspace_artifacts,
    validate_claim_register,
    validate_compatibility,
    validate_routing,
    verify_source_integrity,
)
from campaign_runner_v0.planner import build_verification_plan
from campaign_runner_v0.runner import run_campaign


def test_all_claims_in_plan_from_register(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    bindings = load_campaign_bindings(aurora_workspace)
    claims = validate_claim_register(arts["claim_register"], bindings=bindings)
    ids = {c["claim_id"] for c in claims}
    assert len(ids) == bindings.expected_claim_count == 23
    routes = validate_routing(arts["verification_routing"], ids)
    compat = validate_compatibility(arts["weaver_compatibility"], ids)
    plan = build_verification_plan(
        claims, routes, compat, campaign_id="t", bindings=bindings
    )
    assert plan["claim_count"] == len(ids)
    plan_ids = [c["claim_id"] for c in plan["claims"]]
    assert sorted(plan_ids) == sorted(ids)
    assert len(plan_ids) == len(set(plan_ids))


def test_routing_deterministic(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    bindings = load_campaign_bindings(aurora_workspace)
    claims = validate_claim_register(arts["claim_register"], bindings=bindings)
    ids = {c["claim_id"] for c in claims}
    routes = validate_routing(arts["verification_routing"], ids)
    compat = validate_compatibility(arts["weaver_compatibility"], ids)
    p1 = build_verification_plan(
        claims, routes, compat, campaign_id="t", bindings=bindings
    )
    p2 = build_verification_plan(
        claims, routes, compat, campaign_id="t", bindings=bindings
    )
    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)


def test_source_hashes_match_manifest(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    result = verify_source_integrity(aurora_workspace, arts["source_manifest"])
    assert result["status"] == "SOURCE_IDENTITY_VERIFIED"
    for key, src in arts["source_manifest"]["sources"].items():
        assert result["sources"][key]["observed_sha256"] == src["expected_sha256"]


def test_reuse_bindings_identified(aurora_workspace):
    arts = load_workspace_artifacts(aurora_workspace)
    bindings = load_campaign_bindings(aurora_workspace)
    claims = validate_claim_register(arts["claim_register"], bindings=bindings)
    ids = {c["claim_id"] for c in claims}
    routes = validate_routing(arts["verification_routing"], ids)
    compat = validate_compatibility(arts["weaver_compatibility"], ids)
    plan = build_verification_plan(
        claims, routes, compat, campaign_id="t", bindings=bindings
    )
    by_id = {c["claim_id"]: c for c in plan["claims"]}
    for cid, meta in bindings.reuse_audits.items():
        assert by_id[cid]["reuse_existing_audit"] is True
        assert by_id[cid]["planned_state"] == "PASS"
        assert (aurora_workspace / meta["frozen_relpath"]).is_dir()


def test_dry_run_writes_nothing_to_frozen(aurora_workspace, policy_path):
    frozen_files = list(aurora_workspace.glob("runs/*/freeze/*_FROZEN/SHA256SUMS.txt"))
    before = {str(p): p.read_bytes() for p in frozen_files}
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
