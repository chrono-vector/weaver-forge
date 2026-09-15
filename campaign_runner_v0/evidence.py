"""Evidence register: reuse frozen audits and bind protocol harness results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import KNOWN_REUSE_AUDITS, PROTOCOL_BOUND_CLAIMS
from .safety import SafetyError, load_json, resolve_confined, sha256_file, safe_relative


def verify_frozen_audit_reuse(workspace: Path, claim_id: str) -> dict[str, Any]:
    """Verify existing AUR-A-001/002 frozen evidence without modifying it."""
    meta = KNOWN_REUSE_AUDITS.get(claim_id)
    if not meta:
        raise SafetyError(f"no known reusable audit for {claim_id}")

    run_dir = resolve_confined(workspace, meta["run_relpath"])
    frozen_dir = resolve_confined(workspace, meta["frozen_relpath"])
    freeze_status_path = resolve_confined(workspace, f"{meta['run_relpath']}/FREEZE_STATUS.json")
    decision_path = resolve_confined(workspace, f"{meta['run_relpath']}/DECISION.json")
    sums_path = resolve_confined(frozen_dir, "SHA256SUMS.txt")
    manifest_path = resolve_confined(frozen_dir, "MANIFEST.json")

    for p in (run_dir, frozen_dir, freeze_status_path, decision_path, sums_path, manifest_path):
        if not p.exists():
            raise SafetyError(f"missing referenced frozen package artifact: {p}")

    freeze_status = load_json(freeze_status_path)
    decision = load_json(decision_path)
    if not freeze_status.get("freeze_performed"):
        raise SafetyError(f"freeze not performed for {claim_id}")
    observed_sums_digest = sha256_file(sums_path)
    expected = meta["expected_sha256sums_digest"]
    if observed_sums_digest != expected:
        raise SafetyError(
            f"frozen SHA256SUMS digest mismatch for {claim_id}: "
            f"{observed_sums_digest} != {expected}"
        )
    if decision.get("decision") != "PASS" and decision.get("claim_result") != "PASS":
        raise SafetyError(f"expected PASS decision for reusable audit {claim_id}")

    return {
        "evidence_id": f"reuse:{meta['audit_id']}",
        "claim_id": claim_id,
        "kind": "FROZEN_WEAVER_AUDIT_REUSE",
        "immutable": True,
        "modified": False,
        "rerun": False,
        "audit_id": meta["audit_id"],
        "run_path": meta["run_relpath"],
        "frozen_path": meta["frozen_relpath"],
        "audit_record_path": meta["audit_record_relpath"],
        "sha256sums_digest": observed_sums_digest,
        "scope": meta["scope"],
        "verdict": "PASS",
        "pass_kind": meta["scope"],
        "epistemic_notes": [
            "HASH MATCH ≠ CONTENT TRUTH",
            "INDIVIDUAL AUDIT PASS ≠ AURORA COMPLETE",
            "Reuse only; no refreeze; no rewrite",
        ],
    }


def bind_protocol_harness(workspace: Path, claim_id: str) -> dict[str, Any]:
    """Bind existing protocol harness result; civic remains INCONCLUSIVE."""
    if claim_id not in PROTOCOL_BOUND_CLAIMS:
        raise SafetyError(f"{claim_id} is not a protocol-bound claim")
    harness_path = resolve_confined(
        workspace, "sandbox_harness/results/HARNESS_RESULT_LATEST.json"
    )
    if not harness_path.is_file():
        raise SafetyError("missing protocol harness result")
    harness = load_json(harness_path)
    scenarios = harness.get("scenarios") or {}
    row = scenarios.get(claim_id)
    if not row:
        raise SafetyError(f"harness missing scenario for {claim_id}")
    protocol_check = row.get("protocol_check")
    civic_state = row.get("civic_claim_state")
    if protocol_check == "PASS" and civic_state == "PASS":
        raise SafetyError("protocol harness illegally promotes civic PASS")
    if civic_state not in {"INCONCLUSIVE", None}:
        # Accept INCONCLUSIVE only for these four.
        if claim_id in PROTOCOL_BOUND_CLAIMS and civic_state != "INCONCLUSIVE":
            raise SafetyError(f"unexpected civic_claim_state for {claim_id}: {civic_state}")

    return {
        "evidence_id": f"protocol:{harness.get('harness_id', 'aurora_protocol_harness_v0')}:{claim_id}",
        "claim_id": claim_id,
        "kind": "PROTOCOL_HARNESS_BIND",
        "immutable": True,
        "modified": False,
        "harness_path": "sandbox_harness/results/HARNESS_RESULT_LATEST.json",
        "harness_sha256": sha256_file(harness_path),
        "protocol_check": protocol_check,
        "civic_claim_state": "INCONCLUSIVE",
        "civic_claim_verdict": None,
        "epistemic_boundary": harness.get(
            "epistemic_boundary", "PROTOCOL_SIMULATION_ONLY_NOT_CIVIC_TRUTH"
        ),
        "epistemic_notes": [
            "PROTOCOL HARNESS PASS ≠ CIVIC / REAL-WORLD PASS",
            "Bound existing authorized protocol evidence only",
        ],
    }


def load_synthetic_test_evidence(path: Path, workspace: Path) -> dict[str, Any]:
    """Load TEST_ONLY synthetic evidence; never treat as real Aurora evidence."""
    data = load_json(path)
    markers = {
        data.get("marker"),
        data.get("evidence_class"),
        *(data.get("labels") or []),
    }
    required = {"TEST_ONLY", "SYNTHETIC", "NOT_REAL_AURORA_EVIDENCE"}
    if not required.issubset({str(x) for x in markers if x}):
        # Also accept boolean flags.
        flags_ok = (
            data.get("TEST_ONLY") is True
            and data.get("SYNTHETIC") is True
            and data.get("NOT_REAL_AURORA_EVIDENCE") is True
        )
        if not flags_ok:
            raise SafetyError(
                "synthetic evidence missing TEST_ONLY/SYNTHETIC/NOT_REAL_AURORA_EVIDENCE markers"
            )
    claim_id = data.get("claim_id")
    if not claim_id:
        raise SafetyError("synthetic evidence missing claim_id")
    return {
        "evidence_id": data.get("evidence_id") or f"synthetic-test:{claim_id}",
        "claim_id": claim_id,
        "kind": "TEST_ONLY_SYNTHETIC",
        "TEST_ONLY": True,
        "SYNTHETIC": True,
        "NOT_REAL_AURORA_EVIDENCE": True,
        "path": safe_relative(path, workspace.parent if workspace.name == "aurora_audit" else workspace),
        "payload": data,
        "canonical_aurora_admission": False,
        "notes": [
            "Synthetic fixture for resume testing only",
            "Must never enter canonical Aurora evidence as real evidence",
        ],
    }


def empty_evidence_register(campaign_id: str) -> dict[str, Any]:
    return {
        "schema": "weaver.campaign_runner_v0.evidence_register.v0",
        "campaign_id": campaign_id,
        "entries": [],
        "notes": [
            "Aggregate register only; not a substitute for underlying evidence.",
            "Frozen packages remain authoritative and immutable.",
        ],
    }
