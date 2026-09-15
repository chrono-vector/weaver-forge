"""Load and validate workspace intake / source artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .bindings import CampaignBindings
from .safety import SafetyError, load_json, resolve_confined, sha256_file


REQUIRED_INTAKE = {
    "claim_register": "intake/CLAIM_REGISTER.json",
    "verification_routing": "intake/VERIFICATION_ROUTING.json",
    "weaver_compatibility": "intake/WEAVER_COMPATIBILITY.json",
    "source_inventory": "intake/SOURCE_INVENTORY.json",
    "source_manifest": "frozen_sources/SOURCE_MANIFEST.json",
    "campaign_bindings": "intake/CAMPAIGN_BINDINGS.json",
}


def load_workspace_artifacts(workspace: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, rel in REQUIRED_INTAKE.items():
        path = resolve_confined(workspace, rel)
        if not path.is_file():
            raise SafetyError(f"missing required artifact: {rel}")
        out[key] = load_json(path)
        out[f"{key}_path"] = path
    return out


def validate_claim_register(
    register: dict[str, Any],
    *,
    bindings: CampaignBindings | None = None,
) -> list[dict[str, Any]]:
    claims = register.get("claims")
    if not isinstance(claims, list) or not claims:
        raise SafetyError("CLAIM_REGISTER.claims missing or empty")
    ids = [c.get("claim_id") for c in claims]
    if any(not i for i in ids):
        raise SafetyError("CLAIM_REGISTER contains claim without claim_id")
    if len(ids) != len(set(ids)):
        raise SafetyError("CLAIM_REGISTER has duplicate claim_id values")

    expected = bindings.expected_claim_count if bindings is not None else None
    if expected is not None and len(claims) != expected:
        raise SafetyError(f"expected {expected} claims, found {len(claims)}")

    extracted = register.get("atomic_claims_extracted")
    if extracted is not None:
        if expected is not None and extracted != expected:
            raise SafetyError(
                f"atomic_claims_extracted ({extracted}) must equal expected_claim_count ({expected})"
            )
        if extracted != len(claims):
            raise SafetyError(
                f"atomic_claims_extracted ({extracted}) must equal claim register length ({len(claims)})"
            )
    return claims


def validate_routing(routing: dict[str, Any], claim_ids: set[str]) -> dict[str, dict[str, Any]]:
    routes = routing.get("routes")
    if not isinstance(routes, list):
        raise SafetyError("VERIFICATION_ROUTING.routes missing")
    by_id: dict[str, dict[str, Any]] = {}
    for r in routes:
        cid = r.get("claim_id")
        if not cid or "route" not in r:
            raise SafetyError("invalid routing entry")
        if cid in by_id:
            raise SafetyError(f"duplicate routing for {cid}")
        by_id[cid] = r
    missing = claim_ids - set(by_id)
    extra = set(by_id) - claim_ids
    if missing or extra:
        raise SafetyError(f"routing mismatch missing={sorted(missing)} extra={sorted(extra)}")
    return by_id


def validate_compatibility(
    compat: dict[str, Any], claim_ids: set[str]
) -> dict[str, dict[str, Any]]:
    rows = compat.get("compatibility_assessments")
    if not isinstance(rows, list):
        raise SafetyError("WEAVER_COMPATIBILITY.compatibility_assessments missing")
    by_id = {r["claim_id"]: r for r in rows if "claim_id" in r}
    if set(by_id) != claim_ids:
        raise SafetyError("compatibility assessments do not cover all claims")
    return by_id


def verify_source_integrity(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Recompute source file hashes and compare to SOURCE_MANIFEST expected digests."""
    sources = manifest.get("sources") or {}
    if not isinstance(sources, dict) or not sources:
        raise SafetyError("SOURCE_MANIFEST.sources missing or empty")
    results: dict[str, Any] = {"status": "SOURCE_IDENTITY_VERIFIED", "sources": {}}
    for key, src in sources.items():
        if not isinstance(src, dict):
            raise SafetyError(f"SOURCE_MANIFEST source {key} invalid")
        expected = src.get("expected_sha256")
        if not expected or not isinstance(expected, str):
            raise SafetyError(f"SOURCE_MANIFEST missing expected_sha256 for {key}")
        rel = src.get("filename") or Path(src.get("path", "")).name
        if not rel:
            raise SafetyError(f"SOURCE_MANIFEST missing filename/path for {key}")
        path = resolve_confined(workspace, f"frozen_sources/{rel}")
        if not path.is_file():
            raise SafetyError(f"frozen source missing: {rel}")
        observed = sha256_file(path)
        match = observed == expected
        if not match:
            results["status"] = "SOURCE_IDENTITY_FAILURE"
        results["sources"][key] = {
            "path": f"frozen_sources/{rel}",
            "expected_sha256": expected,
            "observed_sha256": observed,
            "match": match,
            "byte_length": path.stat().st_size,
        }
    if results["status"] != "SOURCE_IDENTITY_VERIFIED":
        raise SafetyError("source hash mismatch — fail closed")
    return results
