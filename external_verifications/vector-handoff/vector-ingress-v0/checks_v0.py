"""Manifest, digest, completeness, binding, and boundary checks for Ingress v0."""

from __future__ import annotations

import json
import re
from typing import Any

from package_reader_v0 import REQUIRED_MEMBERS, REQUIRED_SET, sha256_bytes

DIGEST_LINE_RE = re.compile(r"^[0-9a-f]{64}  [A-Za-z0-9._-]+$")
DIGESTS_NAME = "DIGESTS.sha256"
MANIFEST_NAME = "HANDOFF_MANIFEST.json"
INSTRUCTION_NAME = "WEAVER_REVIEW_INSTRUCTION.md"

ACCEPTED_SCHEMA_ID = "vector-weaver-materialized-handoff-package-v0"
ACCEPTED_TARGET = "WEAVER_FORGE"
ACCEPTED_OPERATION = "INDEPENDENT_REVIEW_OF_VECTOR_PREHANDOFF_PACKAGE"

PAYLOAD_BY_FILENAME = {
    "verification_pre_handoff_envelope.json": "verification_pre_handoff_envelope",
    "decision_trace.json": "decision_trace",
    "verification_result_record.json": "vector_verification_result_record",
    "replay_contract.json": "vector_replay_contract",
    "replay_eligibility_result.json": "decision_trace_replay_eligibility_result",
}

DIGEST_LISTED = tuple(n for n in REQUIRED_MEMBERS if n != DIGESTS_NAME)

LIMIT_L1 = "L1_approved_request_bytes_absent"
LIMIT_L2 = "L2_payload_digest_not_recomputed"
LIMIT_L3 = "L3_pinned_bytes_not_checked"
LIMIT_NESTED = "nested_verification_result_content_sha256_unresolved"


def _dup_hook(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def load_json_strict(raw: bytes) -> Any:
    text = raw.decode("utf-8")
    return json.loads(text, object_pairs_hook=_dup_hook)


def _g(obj: Any, *keys: str) -> Any:
    cur = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _sha(files: dict[str, bytes], name: str) -> str:
    return sha256_bytes(files[name])


def parse_digests_file(raw: bytes) -> tuple[dict[str, str], list[tuple[str, str]]]:
    reasons: list[tuple[str, str]] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        reasons.append(("digest_grammar", "DIGESTS.sha256 is not UTF-8"))
        return {}, reasons
    mapping_d: dict[str, str] = {}
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line == "":
            continue
        if not DIGEST_LINE_RE.fullmatch(line):
            reasons.append(
                (
                    "digest_grammar",
                    f"DIGESTS.sha256:{line_no}: expected '<64 lowercase hex><two spaces><filename>'",
                )
            )
            continue
        digest, name = line.split("  ", 1)
        if name == DIGESTS_NAME:
            reasons.append(("digest_inventory", "DIGESTS.sha256 must not list itself"))
            continue
        if name in mapping_d:
            reasons.append(("digest_inventory", f"duplicate digest line for {name}"))
            continue
        mapping_d[name] = digest
    return mapping_d, reasons


def check_manifest_and_identity(
    files: dict[str, bytes], zip_path_name: str
) -> dict[str, Any]:
    reasons: list[tuple[str, str]] = []
    limitations: list[tuple[str, str]] = []
    manifest_digest = _sha(files, MANIFEST_NAME) if MANIFEST_NAME in files else ""
    package_id = ""
    manifest: Any = None
    artifacts: dict[str, Any] = {}

    try:
        manifest = load_json_strict(files[MANIFEST_NAME])
    except UnicodeDecodeError:
        reasons.append(("json_malformed", "HANDOFF_MANIFEST.json is not UTF-8"))
        return _pack(reasons, limitations, package_id, manifest_digest, manifest, artifacts)
    except ValueError as exc:
        msg = str(exc)
        if "duplicate key" in msg:
            reasons.append(("json_duplicate_key", f"HANDOFF_MANIFEST.json: {msg}"))
        else:
            reasons.append(("json_malformed", f"HANDOFF_MANIFEST.json: {msg}"))
        return _pack(reasons, limitations, package_id, manifest_digest, manifest, artifacts)
    except json.JSONDecodeError as exc:
        reasons.append(("json_malformed", f"HANDOFF_MANIFEST.json: {exc}"))
        return _pack(reasons, limitations, package_id, manifest_digest, manifest, artifacts)

    if not isinstance(manifest, dict):
        reasons.append(("json_type_mismatch", "HANDOFF_MANIFEST.json must be an object"))
        return _pack(reasons, limitations, package_id, manifest_digest, manifest, artifacts)

    if manifest.get("schema_id") != ACCEPTED_SCHEMA_ID:
        reasons.append(
            (
                "schema_unsupported",
                f"schema_id {manifest.get('schema_id')!r} is not {ACCEPTED_SCHEMA_ID}",
            )
        )
    version = manifest.get("schema_version")
    if version not in (0, "0"):
        reasons.append(
            ("schema_unsupported", f"schema_version {version!r} is not v0")
        )
    if manifest.get("target_system") != ACCEPTED_TARGET:
        reasons.append(
            (
                "identity_mismatch",
                f"target_system {manifest.get('target_system')!r} is not {ACCEPTED_TARGET}",
            )
        )
    if manifest.get("requested_operation") != ACCEPTED_OPERATION:
        reasons.append(
            (
                "identity_mismatch",
                f"requested_operation {manifest.get('requested_operation')!r} is not {ACCEPTED_OPERATION}",
            )
        )

    package_id = manifest.get("package_id")
    request_id = manifest.get("approved_core04_request_id")
    if not isinstance(package_id, str) or not package_id:
        reasons.append(("identity_mismatch", "package_id missing"))
        package_id = ""
    if not isinstance(request_id, str) or not request_id:
        reasons.append(("identity_mismatch", "approved_core04_request_id missing"))
    elif package_id and request_id != package_id:
        reasons.append(
            (
                "identity_mismatch",
                "package_id != approved_core04_request_id",
            )
        )

    if package_id:
        allowed = {
            f"{package_id}.zip",
            f"VECTOR_WEAVER_HANDOFF_{package_id}.zip",
        }
        if zip_path_name not in allowed:
            reasons.append(
                (
                    "identity_mismatch",
                    "ZIP basename is not an approved exact form "
                    f"(<package_id>.zip or VECTOR_WEAVER_HANDOFF_<package_id>.zip)",
                )
            )

    payload = manifest.get("payload")
    if not isinstance(payload, list) or len(payload) != 5:
        reasons.append(("json_type_mismatch", "payload must be a list of 5 artifacts"))
        payload = []
    seen_names: set[str] = set()
    for entry in payload:
        if not isinstance(entry, dict):
            reasons.append(("json_type_mismatch", "payload entry must be an object"))
            continue
        filename = entry.get("filename")
        if filename not in PAYLOAD_BY_FILENAME:
            reasons.append(
                ("container_undeclared_or_missing_member", f"unexpected payload filename {filename!r}")
            )
            continue
        if filename in seen_names:
            reasons.append(("identity_mismatch", f"duplicate payload filename {filename}"))
        seen_names.add(filename)
        expected_class = PAYLOAD_BY_FILENAME[filename]
        if entry.get("artifact_class") != expected_class:
            reasons.append(
                (
                    "binding_mismatch",
                    f"{filename}: artifact_class {entry.get('artifact_class')!r} != {expected_class}",
                )
            )
        for key in ("content_sha256", "observed_sha256"):
            val = entry.get(key)
            if not isinstance(val, str) or not re.fullmatch(r"[0-9a-f]{64}", val or ""):
                reasons.append(("digest_grammar", f"{filename}: {key} is not lowercase sha256"))
        if entry.get("content_sha256") != entry.get("observed_sha256"):
            reasons.append(
                ("digest_mismatch", f"{filename}: content_sha256 != observed_sha256")
            )
        if filename in files:
            actual = _sha(files, filename)
            if entry.get("content_sha256") != actual or entry.get("observed_sha256") != actual:
                reasons.append(
                    (
                        "digest_mismatch",
                        f"{filename}: payload SHA != actual file SHA",
                    )
                )

    missing_payload = sorted(set(PAYLOAD_BY_FILENAME) - seen_names)
    if missing_payload:
        reasons.append(
            (
                "container_undeclared_or_missing_member",
                f"payload missing {missing_payload}",
            )
        )

    if isinstance(manifest.get("approved_request_sha256"), str) and "approved_handoff_request.json" not in files:
        limitations.append(
            (LIMIT_L1, "approved request SHA is referenced; request bytes are not in the package")
        )
    if manifest.get("payload_digest_sha256"):
        limitations.append(
            (LIMIT_L2, "payload_digest_sha256 is not recomputed; no canonical aggregate rule in v0")
        )

    return _pack(reasons, limitations, package_id if isinstance(package_id, str) else "", manifest_digest, manifest, artifacts)


def _pack(reasons, limitations, package_id, manifest_digest, manifest, artifacts):
    return {
        "reasons": reasons,
        "limitations": limitations,
        "package_id": package_id,
        "manifest_digest": manifest_digest,
        "manifest": manifest,
        "artifacts": artifacts,
    }


def check_digests(files: dict[str, bytes]) -> list[tuple[str, str]]:
    reasons: list[tuple[str, str]] = []
    mapping, parse_reasons = parse_digests_file(files[DIGESTS_NAME])
    reasons.extend(parse_reasons)
    listed = set(mapping)
    required = set(DIGEST_LISTED)
    extra = sorted(listed - required)
    missing = sorted(required - listed)
    if extra or missing:
        reasons.append(
            ("digest_inventory", f"digest extra={extra} missing={missing}")
        )
    for name in DIGEST_LISTED:
        if name not in files or name not in mapping:
            continue
        actual = _sha(files, name)
        if actual != mapping[name]:
            reasons.append(("digest_mismatch", f"DIGESTS mismatch for {name}"))
    return reasons


def _load_artifact(files: dict[str, bytes], name: str) -> tuple[Any, list[tuple[str, str]]]:
    reasons: list[tuple[str, str]] = []
    try:
        obj = load_json_strict(files[name])
    except UnicodeDecodeError:
        reasons.append(("json_malformed", f"{name} is not UTF-8"))
        return None, reasons
    except ValueError as exc:
        msg = str(exc)
        code = "json_duplicate_key" if "duplicate key" in msg else "json_malformed"
        reasons.append((code, f"{name}: {msg}"))
        return None, reasons
    except json.JSONDecodeError as exc:
        reasons.append(("json_malformed", f"{name}: {exc}"))
        return None, reasons
    if not isinstance(obj, dict):
        reasons.append(("json_type_mismatch", f"{name} must be an object"))
        return None, reasons
    return obj, reasons


def check_bindings(files: dict[str, bytes], manifest: Any) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    reasons: list[tuple[str, str]] = []
    limitations: list[tuple[str, str]] = []
    if not isinstance(manifest, dict):
        return reasons, limitations

    loaded: dict[str, Any] = {}
    for name in PAYLOAD_BY_FILENAME:
        obj, load_reasons = _load_artifact(files, name)
        reasons.extend(load_reasons)
        if obj is not None:
            loaded[name] = obj

    if len(loaded) != 5:
        return reasons, limitations

    dt = loaded["decision_trace.json"]
    rc = loaded["replay_contract.json"]
    elig = loaded["replay_eligibility_result.json"]
    env = loaded["verification_pre_handoff_envelope.json"]
    vr = loaded["verification_result_record.json"]

    dt_id = _g(dt, "identity", "decision_trace_id")
    dt_sha = _sha(files, "decision_trace.json")
    vr_id = vr.get("record_id")
    vr_sha = _sha(files, "verification_result_record.json")
    rc_id = rc.get("replay_contract_id")
    env_id = env.get("envelope_id")

    payload = manifest.get("payload") if isinstance(manifest.get("payload"), list) else []
    payload_by_name = {
        e.get("filename"): e for e in payload if isinstance(e, dict)
    }

    def payload_id(name: str) -> Any:
        entry = payload_by_name.get(name) or {}
        return entry.get("artifact_id")

    def payload_sha(name: str) -> Any:
        entry = payload_by_name.get(name) or {}
        return entry.get("content_sha256")

    if dt_id != payload_id("decision_trace.json"):
        reasons.append(("binding_mismatch", "Decision Trace artifact_id != identity.decision_trace_id"))
    for other in (rc.get("decision_trace_id"), elig.get("decision_trace_id"), vr.get("decision_trace_id")):
        if other != dt_id:
            reasons.append(("binding_mismatch", "Decision Trace ID is not consistent across artifacts"))
            break
    if rc.get("decision_trace_content_sha256") != dt_sha or vr.get("decision_trace_content_sha256") != dt_sha:
        reasons.append(("binding_mismatch", "Decision Trace file SHA is not consistent"))
    for payload_name in PAYLOAD_BY_FILENAME:
        actual = _sha(files, payload_name)
        declared = payload_sha(payload_name)
        observed = (payload_by_name.get(payload_name) or {}).get("observed_sha256")
        if declared != actual or observed != actual:
            reasons.append(
                ("digest_mismatch", f"{payload_name}: payload SHA != actual file SHA")
            )

    if rc_id != payload_id("replay_contract.json") or rc_id != elig.get("replay_contract_id"):
        reasons.append(("binding_mismatch", "Replay Contract ID is not consistent"))

    if elig.get("record_class") != "DecisionTraceReplayEligibilityResult":
        reasons.append(("binding_mismatch", "eligibility record_class mismatch"))

    if vr_id != payload_id("verification_result_record.json"):
        reasons.append(("binding_mismatch", "Verification Result artifact_id != record_id"))
    if _g(rc, "verification_result_reference", "record_id") != vr_id:
        reasons.append(("binding_mismatch", "Replay Contract verification_result_reference.record_id mismatch"))
    if _g(env, "source_reference", "content_address") != vr_sha:
        reasons.append(("binding_mismatch", "envelope source_reference.content_address != Verification Result file SHA"))
    if _g(rc, "verification_result_reference", "content_address") != vr_sha:
        reasons.append(("binding_mismatch", "Replay Contract verification_result_reference.content_address mismatch"))

    if env_id != payload_id("verification_pre_handoff_envelope.json"):
        reasons.append(("binding_mismatch", "Envelope ID mismatch"))

    # (artifact_class, artifact_id) => same bytes
    class_id_bytes: dict[tuple[str, str], str] = {}
    for name, obj in loaded.items():
        entry = payload_by_name.get(name) or {}
        aclass = entry.get("artifact_class")
        aid = entry.get("artifact_id")
        if not isinstance(aclass, str) or not isinstance(aid, str):
            continue
        digest = _sha(files, name)
        key = (aclass, aid)
        if key in class_id_bytes and class_id_bytes[key] != digest:
            reasons.append(
                (
                    "same_class_id_different_bytes",
                    f"{key} maps to different bytes",
                )
            )
        class_id_bytes[key] = digest

    nested = vr.get("verification_result_content_sha256")
    if isinstance(nested, str) and nested and nested != vr_sha:
        limitations.append(
            (
                LIMIT_NESTED,
                "verification_result_content_sha256 is not a file digest and is not bound in v0",
            )
        )

    return reasons, limitations


def check_boundaries(files: dict[str, bytes], manifest: Any) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    reasons: list[tuple[str, str]] = []
    limitations: list[tuple[str, str]] = []
    loaded: dict[str, Any] = {}
    for name in PAYLOAD_BY_FILENAME:
        obj, load_reasons = _load_artifact(files, name)
        # load errors already reported in bindings; skip duplicates if any
        if load_reasons and obj is None:
            continue
        if obj is not None:
            loaded[name] = obj
    if len(loaded) != 5:
        return reasons, limitations

    dt = loaded["decision_trace.json"]
    rc = loaded["replay_contract.json"]
    env = loaded["verification_pre_handoff_envelope.json"]
    vr = loaded["verification_result_record.json"]

    inflation_paths = [
        ("manifest.admission_status", isinstance(manifest, dict) and manifest.get("admission_status") == "admitted"),
        ("manifest.authority_limitations.truth_verification_claimed", _g(manifest, "authority_limitations", "truth_verification_claimed") is True),
        ("manifest.authority_limitations.evidence_admission_authorized", _g(manifest, "authority_limitations", "evidence_admission_authorized") is True),
        ("manifest.authority_limitations.replay_execution_authorized", _g(manifest, "authority_limitations", "replay_execution_authorized") is True),
        ("manifest.authority_limitations.stage6_entered", _g(manifest, "authority_limitations", "stage6_entered") is True),
        ("vr.truth_verified", vr.get("truth_verified") is True),
        ("vr.evidence_admitted", vr.get("evidence_admitted") is True),
        ("vr.execution_authorized", vr.get("execution_authorized") is True),
        ("vr.replay_authorized", vr.get("replay_authorized") is True),
        ("vr.stage6_entered", vr.get("stage6_entered") is True),
        ("vr.weaver_invocation_authorized", vr.get("weaver_invocation_authorized") is True),
        ("rc.authority.truth_verified", _g(rc, "authority", "truth_verified") is True),
        ("rc.authority.evidence_admitted", _g(rc, "authority", "evidence_admitted") is True),
        ("rc.authority.execution_authorized", _g(rc, "authority", "execution_authorized") is True),
        ("rc.authority.replay_execution_authorized", _g(rc, "authority", "replay_execution_authorized") is True),
        ("rc.authority.stage6_entered", _g(rc, "authority", "stage6_entered") is True),
        ("rc.authority.weaver_invocation_authorized", _g(rc, "authority", "weaver_invocation_authorized") is True),
        ("dt.trace_verified", _g(dt, "assurance", "verification_status", "trace_verified") is True),
    ]
    for path, flagged in inflation_paths:
        if flagged:
            reasons.append(("authority_inflation", f"{path} is true"))

    pinned_paths = [
        ("vr.pinned_bytes.status", _g(vr, "verification_result", "checks", "pinned_bytes", "status")),
        ("env.pinned_bytes.status", _g(env, "verification_result", "checks", "pinned_bytes", "status")),
        ("env.content_identity.status", _g(env, "content_identity", "status")),
    ]
    saw_not_checked = False
    for path, status in pinned_paths:
        if status is None:
            continue
        if status == "not_checked":
            saw_not_checked = True
        else:
            reasons.append(
                (
                    "boundary_upgrade_forbidden",
                    f"{path}={status!r} must remain not_checked in v0",
                )
            )
    if saw_not_checked:
        limitations.append(
            (LIMIT_L3, "Chronicle/pinned bytes are not_checked and must not be upgraded")
        )

    return reasons, limitations


def run_logical_checks(files: dict[str, bytes], zip_path_name: str) -> dict[str, Any]:
    reasons: list[tuple[str, str]] = []
    limitations: list[tuple[str, str]] = []
    checks = {
        "container": "ok",
        "manifest": "ok",
        "digests": "ok",
        "completeness": "ok",
        "bindings": "ok",
        "boundaries": "ok",
    }

    missing = [n for n in REQUIRED_MEMBERS if n not in files]
    extra = [n for n in files if n not in REQUIRED_SET]
    if missing or extra:
        reasons.append(
            (
                "container_undeclared_or_missing_member",
                f"completeness extra={extra} missing={missing}",
            )
        )
        checks["completeness"] = "failed"

    ident = check_manifest_and_identity(files, zip_path_name)
    ident_reasons = ident["reasons"]
    reasons.extend(ident_reasons)
    limitations.extend(ident["limitations"])
    if any(c in {"schema_unsupported", "identity_mismatch", "json_malformed", "json_duplicate_key", "json_type_mismatch"} for c, _ in ident_reasons):
        checks["manifest"] = "failed"
    if any(c.startswith("digest_") for c, _ in ident_reasons):
        checks["digests"] = "failed"

    digest_reasons = check_digests(files)
    reasons.extend(digest_reasons)
    if digest_reasons:
        checks["digests"] = "failed"

    bind_reasons, bind_limits = check_bindings(files, ident["manifest"])
    reasons.extend(bind_reasons)
    limitations.extend(bind_limits)
    if bind_reasons:
        checks["bindings"] = "failed"

    bound_reasons, bound_limits = check_boundaries(files, ident["manifest"])
    reasons.extend(bound_reasons)
    limitations.extend(bound_limits)
    if bound_reasons:
        checks["boundaries"] = "failed"

    # Dedupe reason list while keeping first-seen order of (code, message)
    seen: set[tuple[str, str]] = set()
    uniq: list[tuple[str, str]] = []
    for item in reasons:
        if item in seen:
            continue
        seen.add(item)
        uniq.append(item)

    seen_l: set[tuple[str, str]] = set()
    uniq_l: list[tuple[str, str]] = []
    for item in limitations:
        if item in seen_l:
            continue
        seen_l.add(item)
        uniq_l.append(item)

    return {
        "checks": checks,
        "reasons": uniq,
        "limitations": uniq_l,
        "package_id": ident["package_id"],
        "manifest_digest": ident["manifest_digest"],
    }
