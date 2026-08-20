"""Ingress result construction and structural self-check for v0."""

from __future__ import annotations

import hashlib
import json
from typing import Any

SCHEMA_ID = "weaver-vector-ingress-result-v0"
SCHEMA_VERSION = "0"
SOURCE_SYSTEM = "VECTOR"
CHECK_NAMES = (
    "container",
    "manifest",
    "digests",
    "completeness",
    "bindings",
    "boundaries",
)
CHECK_STATUSES = frozenset({"ok", "failed", "not_evaluated"})
DISPOSITIONS = frozenset({"INGRESS_READY", "INGRESS_HOLD", "INGRESS_REJECT"})
AUTHORITY_KEYS = (
    "truth_verified",
    "evidence_admitted",
    "replay_authorized",
    "downstream_execution_authorized",
    "stage6_authorized",
)
ID_PREFIX_LEN = 32


def always_false_authority() -> dict[str, bool]:
    return {k: False for k in AUTHORITY_KEYS}


def _semantic_for_id(result: dict[str, Any]) -> dict[str, Any]:
    checks = result.get("checks") or {}
    ordered_checks = {name: checks.get(name, "not_evaluated") for name in CHECK_NAMES}
    return {
        "schema_id": result.get("schema_id"),
        "schema_version": result.get("schema_version"),
        "source_system": result.get("source_system"),
        "source_package_id": result.get("source_package_id"),
        "package_digest": result.get("package_digest"),
        "manifest_digest": result.get("manifest_digest"),
        "checks": ordered_checks,
        "final_disposition": result.get("final_disposition"),
        "reason_codes": sorted(set(result.get("reason_codes") or [])),
        "limitation_codes": sorted(set(result.get("limitation_codes") or [])),
        "authority": always_false_authority(),
    }


def compute_ingress_result_id(result: dict[str, Any]) -> str:
    payload = _semantic_for_id(result)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return "wvir-v0-" + digest[:ID_PREFIX_LEN]


def build_ingress_result_v0(
    *,
    source_package_id: str,
    package_digest: str,
    manifest_digest: str,
    checks: dict[str, str],
    reason_codes: list[str],
    limitation_codes: list[str],
    reason_messages: list[tuple[str, str]] | None = None,
    limitation_messages: list[tuple[str, str]] | None = None,
    operational: dict[str, Any] | None = None,
) -> dict[str, Any]:
    codes = sorted(set(reason_codes))
    limits = sorted(set(limitation_codes))
    ordered_checks = {name: checks.get(name, "not_evaluated") for name in CHECK_NAMES}
    failed = any(ordered_checks[name] == "failed" for name in CHECK_NAMES) or bool(codes)
    disposition = "INGRESS_REJECT" if failed else "INGRESS_READY"
    reasons = [{"code": c, "message": m} for c, m in (reason_messages or [])]
    limitations = [{"code": c, "message": m} for c, m in (limitation_messages or [])]
    result: dict[str, Any] = {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "source_system": SOURCE_SYSTEM,
        "source_package_id": source_package_id,
        "package_digest": package_digest,
        "manifest_digest": manifest_digest,
        "checks": ordered_checks,
        "final_disposition": disposition,
        "reason_codes": codes,
        "limitation_codes": limits,
        "reasons": reasons,
        "limitations": limitations,
        "authority": always_false_authority(),
        "operational": operational or {},
    }
    result["ingress_result_id"] = compute_ingress_result_id(result)
    return result


def validate_vector_ingress_result_v0(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(result, dict):
        return ["result is not an object"]
    if result.get("schema_id") != SCHEMA_ID:
        errors.append(f"schema_id must be {SCHEMA_ID!r}")
    if result.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if result.get("source_system") != SOURCE_SYSTEM:
        errors.append("source_system must be VECTOR")
    if result.get("final_disposition") not in DISPOSITIONS:
        errors.append("final_disposition is not a legal value")
    auth = result.get("authority")
    if not isinstance(auth, dict):
        errors.append("authority missing")
    else:
        for key in AUTHORITY_KEYS:
            if auth.get(key) is not False:
                errors.append(f"authority.{key} must be false")
    checks = result.get("checks")
    if not isinstance(checks, dict):
        errors.append("checks missing")
    else:
        for name in CHECK_NAMES:
            if checks.get(name) not in CHECK_STATUSES:
                errors.append(f"checks.{name} has illegal status")
    rid = result.get("ingress_result_id")
    expected = compute_ingress_result_id(result)
    if rid != expected:
        errors.append("ingress_result_id does not match semantic payload hash")
    if not isinstance(result.get("reason_codes"), list):
        errors.append("reason_codes must be a list")
    if not isinstance(result.get("limitation_codes"), list):
        errors.append("limitation_codes must be a list")
    return errors
