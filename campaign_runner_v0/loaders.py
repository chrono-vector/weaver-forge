"""Load and validate existing Aurora intake / source artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import EXPECTED_SOURCE_HASHES
from .safety import SafetyError, load_json, resolve_confined, sha256_file


REQUIRED_INTAKE = {
    "claim_register": "intake/CLAIM_REGISTER.json",
    "verification_routing": "intake/VERIFICATION_ROUTING.json",
    "weaver_compatibility": "intake/WEAVER_COMPATIBILITY.json",
    "source_inventory": "intake/SOURCE_INVENTORY.json",
    "source_manifest": "frozen_sources/SOURCE_MANIFEST.json",
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


def validate_claim_register(register: dict[str, Any]) -> list[dict[str, Any]]:
    claims = register.get("claims")
    if not isinstance(claims, list) or not claims:
        raise SafetyError("CLAIM_REGISTER.claims missing or empty")
    ids = [c.get("claim_id") for c in claims]
    if any(not i for i in ids):
        raise SafetyError("CLAIM_REGISTER contains claim without claim_id")
    if len(ids) != len(set(ids)):
        raise SafetyError("CLAIM_REGISTER has duplicate claim_id values")
    if len(claims) != 23:
        raise SafetyError(f"expected 23 claims, found {len(claims)}")
    if register.get("atomic_claims_extracted") not in (None, 23):
        if register.get("atomic_claims_extracted") != 23:
            raise SafetyError("atomic_claims_extracted must be 23")
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
    """Recompute Source A/B hashes and compare to expected digests."""
    sources = manifest.get("sources") or {}
    results: dict[str, Any] = {"status": "SOURCE_IDENTITY_VERIFIED", "sources": {}}
    for key, expected in EXPECTED_SOURCE_HASHES.items():
        src = sources.get(key)
        if not src:
            raise SafetyError(f"SOURCE_MANIFEST missing {key}")
        rel = src.get("filename") or Path(src.get("path", "")).name
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
