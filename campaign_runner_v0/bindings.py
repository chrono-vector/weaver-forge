"""Campaign-specific bindings loaded from workspace artifacts (not product constants)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .safety import SafetyError, load_json, resolve_confined

BINDINGS_RELPATH = "intake/CAMPAIGN_BINDINGS.json"


@dataclass(frozen=True)
class CampaignBindings:
    """Campaign-specific facts derived from validated workspace config."""

    expected_claim_count: int | None
    reuse_audits: dict[str, dict[str, Any]]
    protocol_bound_claims: frozenset[str]
    human_auth_required_claims: frozenset[str]
    protocol_harness_relpath: str
    raw: dict[str, Any]

    def reuse_meta(self, claim_id: str) -> dict[str, Any] | None:
        return self.reuse_audits.get(claim_id)

    def is_protocol_bound(self, claim_id: str) -> bool:
        return claim_id in self.protocol_bound_claims

    def requires_human_auth(self, claim_id: str) -> bool:
        return claim_id in self.human_auth_required_claims


def load_campaign_bindings(workspace: Path) -> CampaignBindings:
    path = resolve_confined(workspace, BINDINGS_RELPATH)
    if not path.is_file():
        raise SafetyError(f"missing required artifact: {BINDINGS_RELPATH}")
    data = load_json(path)
    if not isinstance(data, dict):
        raise SafetyError("CAMPAIGN_BINDINGS must be a JSON object")

    reuse_raw = data.get("reuse_audits") or {}
    if not isinstance(reuse_raw, dict):
        raise SafetyError("CAMPAIGN_BINDINGS.reuse_audits must be an object")
    reuse_audits: dict[str, dict[str, Any]] = {}
    for cid, meta in reuse_raw.items():
        if not isinstance(meta, dict):
            raise SafetyError(f"reuse_audits[{cid}] must be an object")
        for req in (
            "audit_id",
            "run_relpath",
            "frozen_relpath",
            "expected_sha256sums_digest",
            "scope",
        ):
            if req not in meta:
                raise SafetyError(f"reuse_audits[{cid}] missing {req}")
        reuse_audits[str(cid)] = dict(meta)

    protocol = data.get("protocol_bound_claims") or []
    human = data.get("human_auth_required_claims") or []
    if not isinstance(protocol, list) or not isinstance(human, list):
        raise SafetyError("protocol/human claim lists must be arrays")

    expected = data.get("expected_claim_count")
    if expected is not None and not isinstance(expected, int):
        raise SafetyError("expected_claim_count must be an integer when present")

    harness = data.get("protocol_harness_relpath") or (
        "sandbox_harness/results/HARNESS_RESULT_LATEST.json"
    )
    if not isinstance(harness, str) or not harness.strip():
        raise SafetyError("protocol_harness_relpath must be a non-empty string")

    overlap = set(map(str, protocol)) & set(map(str, human))
    if overlap:
        raise SafetyError(f"claim cannot be both protocol-bound and human-auth: {sorted(overlap)}")

    return CampaignBindings(
        expected_claim_count=expected,
        reuse_audits=reuse_audits,
        protocol_bound_claims=frozenset(str(x) for x in protocol),
        human_auth_required_claims=frozenset(str(x) for x in human),
        protocol_harness_relpath=harness,
        raw=data,
    )
