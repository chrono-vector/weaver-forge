"""In-memory synthetic VECTOR handoff ZIP builder for Ingress v0 tests."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any, Callable

PACKAGE_ID = "vwh-v0-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
DT_ID = "vector-synthetic-dt-v0"
VR_ID = "vvr-v0-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
RC_ID = "vrc-v0-cccccccccccccccccccccccccccccccc"
ENV_ID = "SYNTHETIC-PREHANDOFF"
APPROVED_REQUEST_SHA = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
DUMMY_PAYLOAD_DIGEST = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"


def dumps(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _instruction() -> bytes:
    return (
        "# Weaver Independent Review Instruction\n\n"
        "Requested operation: INDEPENDENT_REVIEW_OF_VECTOR_PREHANDOFF_PACKAGE\n"
    ).encode("utf-8")


def _decision_trace() -> dict[str, Any]:
    return {
        "schema_id": "vector-decision-trace-schema-v0",
        "schema_version": 0,
        "artifact_class": "DecisionTrace",
        "identity": {"decision_trace_id": DT_ID, "producer": {"producer_id": "synthetic"}},
        "assurance": {
            "verification_status": {"trace_verified": False},
            "evidence_assurance": {"provenance_status": "claimed"},
        },
        "artifact_non_claims": {
            "records_process_not_external_truth": True,
            "not_an_execution_trigger": True,
        },
        "subject": {"decision_subject": "synthetic"},
    }


def _verification_result(dt_sha: str) -> dict[str, Any]:
    return {
        "schema_id": "vector-verification-result-record-v0",
        "schema_version": "0",
        "artifact_class": "vector_verification_result_record",
        "record_id": VR_ID,
        "decision_trace_id": DT_ID,
        "decision_trace_content_sha256": dt_sha,
        "truth_verified": False,
        "evidence_admitted": False,
        "execution_authorized": False,
        "replay_authorized": False,
        "stage6_entered": False,
        "weaver_invocation_authorized": False,
        "verification_kind": "STRUCTURAL_DECISION_TRACE_VERIFICATION",
        "verification_result_content_sha256": "1111111111111111111111111111111111111111111111111111111111111111",
        "locator": f"vector-verification-result-local-v0:{VR_ID}",
        "verification_result": {
            "checks": {
                "pinned_bytes": {
                    "status": "not_checked",
                    "hash_match_is_not_truth": True,
                }
            }
        },
        "non_claims": {
            "structural_check_passed_is_not_truth_verified": True,
            "does_not_claim_stage6_authority": True,
        },
    }


def _envelope(vr_sha: str) -> dict[str, Any]:
    return {
        "record_class": "VerificationPreHandoffEnvelope",
        "envelope_id": ENV_ID,
        "envelope_disposition": "PRE_HANDOFF_ENVELOPE_ASSEMBLED",
        "content_identity": {"status": "not_checked"},
        "source_reference": {
            "content_address": vr_sha,
            "content_address_algorithm": "sha256",
            "locator": f"vector-verification-result-local-v0:{VR_ID}",
        },
        "verification_result": {
            "checks": {"pinned_bytes": {"status": "not_checked"}}
        },
        "non_claims": {"does_not_claim_truth": True, "not_a_witness_package": True},
        "unchecked": ["replay", "independent_witness"],
    }


def _replay_contract(dt_sha: str, vr_sha: str) -> dict[str, Any]:
    return {
        "schema_id": "vector-replay-contract-v0",
        "schema_version": "0",
        "artifact_class": "vector_replay_contract",
        "replay_contract_id": RC_ID,
        "decision_trace_id": DT_ID,
        "decision_trace_content_sha256": dt_sha,
        "locator": f"vector-replay-contract-local-v0:{RC_ID}",
        "authority": {
            "evidence_admitted": False,
            "execution_authorized": False,
            "replay_execution_authorized": False,
            "stage6_entered": False,
            "truth_verified": False,
            "weaver_invocation_authorized": False,
            "human_replay_authorization_required": True,
        },
        "verification_result_reference": {
            "record_id": VR_ID,
            "content_address": vr_sha,
            "content_address_algorithm": "sha256",
            "locator": f"vector-verification-result-local-v0:{VR_ID}",
        },
        "non_claims": {
            "replay_contract_is_not_replay_execution": True,
            "replay_eligibility_is_not_replay_authorization": True,
        },
    }


def _eligibility() -> dict[str, Any]:
    return {
        "record_class": "DecisionTraceReplayEligibilityResult",
        "decision_trace_id": DT_ID,
        "replay_contract_id": RC_ID,
        "eligibility_disposition": "REPLAY_ELIGIBLE_BY_CONTRACT",
        "missing_requirements": [],
        "unresolved_requirements": [],
        "non_claims": {
            "replay_not_executed": True,
            "execution_not_authorized": True,
            "truth_not_verified": True,
        },
        "checks": {},
    }


def _payload_entry(filename: str, artifact_class: str, artifact_id: str, digest: str) -> dict[str, Any]:
    return {
        "admission_status": "not_admitted",
        "artifact_class": artifact_class,
        "artifact_id": artifact_id,
        "canonical_status": "noncanonical",
        "content_sha256": digest,
        "filename": filename,
        "observed_sha256": digest,
        "locator": None,
        "materialization_source": "synthetic",
    }


def _manifest(
    *,
    dt_sha: str,
    vr_sha: str,
    rc_sha: str,
    elig_sha: str,
    env_sha: str,
    package_id: str = PACKAGE_ID,
    schema_id: str = "vector-weaver-materialized-handoff-package-v0",
    schema_version: Any = "0",
    target_system: str = "WEAVER_FORGE",
    requested_operation: str = "INDEPENDENT_REVIEW_OF_VECTOR_PREHANDOFF_PACKAGE",
) -> dict[str, Any]:
    return {
        "schema_id": schema_id,
        "schema_version": schema_version,
        "package_id": package_id,
        "approved_core04_request_id": package_id,
        "approved_request_locator": f"vector-weaver-handoff-local-v0:{package_id}",
        "approved_request_sha256": APPROVED_REQUEST_SHA,
        "target_system": target_system,
        "requested_operation": requested_operation,
        "admission_status": "not_admitted",
        "canonical_status": "noncanonical",
        "payload_digest_sha256": DUMMY_PAYLOAD_DIGEST,
        "authority_limitations": {
            "evidence_admission_authorized": False,
            "replay_execution_authorized": False,
            "stage6_entered": False,
            "truth_verification_claimed": False,
        },
        "payload": [
            _payload_entry(
                "verification_pre_handoff_envelope.json",
                "verification_pre_handoff_envelope",
                ENV_ID,
                env_sha,
            ),
            _payload_entry("decision_trace.json", "decision_trace", DT_ID, dt_sha),
            _payload_entry(
                "verification_result_record.json",
                "vector_verification_result_record",
                VR_ID,
                vr_sha,
            ),
            _payload_entry("replay_contract.json", "vector_replay_contract", RC_ID, rc_sha),
            _payload_entry(
                "replay_eligibility_result.json",
                "decision_trace_replay_eligibility_result",
                RC_ID,
                elig_sha,
            ),
        ],
    }


def build_file_map(mutate: Callable[[dict[str, Any]], None] | None = None) -> dict[str, bytes]:
    dt_obj = _decision_trace()
    dt_bytes = dumps(dt_obj)
    dt_sha = sha256_bytes(dt_bytes)
    vr_obj = _verification_result(dt_sha)
    env_obj = _envelope("PENDING")
    rc_obj = _replay_contract(dt_sha, "PENDING")
    elig_obj = _eligibility()
    objects: dict[str, Any] = {
        "decision_trace": dt_obj,
        "verification_result_record": vr_obj,
        "envelope": env_obj,
        "replay_contract": rc_obj,
        "eligibility": elig_obj,
        "package_id": PACKAGE_ID,
        "schema_id": "vector-weaver-materialized-handoff-package-v0",
        "schema_version": "0",
        "target_system": "WEAVER_FORGE",
        "requested_operation": "INDEPENDENT_REVIEW_OF_VECTOR_PREHANDOFF_PACKAGE",
    }
    if mutate is not None:
        mutate(objects)

    dt_bytes = dumps(objects["decision_trace"])
    dt_sha = sha256_bytes(dt_bytes)
    objects["verification_result_record"]["decision_trace_content_sha256"] = dt_sha
    objects["replay_contract"]["decision_trace_content_sha256"] = dt_sha
    vr_bytes = dumps(objects["verification_result_record"])
    vr_sha = sha256_bytes(vr_bytes)
    objects["envelope"]["source_reference"]["content_address"] = vr_sha
    objects["replay_contract"]["verification_result_reference"]["content_address"] = vr_sha
    env_bytes = dumps(objects["envelope"])
    rc_bytes = dumps(objects["replay_contract"])
    elig_bytes = dumps(objects["eligibility"])
    env_sha = sha256_bytes(env_bytes)
    rc_sha = sha256_bytes(rc_bytes)
    elig_sha = sha256_bytes(elig_bytes)
    instr = _instruction()
    manifest_obj = _manifest(
        dt_sha=dt_sha,
        vr_sha=vr_sha,
        rc_sha=rc_sha,
        elig_sha=elig_sha,
        env_sha=env_sha,
        package_id=objects["package_id"],
        schema_id=objects["schema_id"],
        schema_version=objects["schema_version"],
        target_system=objects["target_system"],
        requested_operation=objects["requested_operation"],
    )
    if "manifest_patch" in objects and callable(objects["manifest_patch"]):
        objects["manifest_patch"](manifest_obj)
    manifest_bytes = dumps(manifest_obj)
    files = {
        "decision_trace.json": dt_bytes,
        "verification_result_record.json": vr_bytes,
        "verification_pre_handoff_envelope.json": env_bytes,
        "replay_contract.json": rc_bytes,
        "replay_eligibility_result.json": elig_bytes,
        "WEAVER_REVIEW_INSTRUCTION.md": instr,
        "HANDOFF_MANIFEST.json": manifest_bytes,
    }
    digest_lines = []
    for name in sorted(files):
        digest_lines.append(f"{sha256_bytes(files[name])}  {name}")
    files["DIGESTS.sha256"] = ("\n".join(digest_lines) + "\n").encode("utf-8")
    if "files_patch" in objects and callable(objects["files_patch"]):
        objects["files_patch"](files)
    return files


def zip_bytes(
    files: dict[str, bytes],
    *,
    compress: int = zipfile.ZIP_DEFLATED,
    extra_infos: list[zipfile.ZipInfo] | None = None,
    extra_payloads: dict[str, bytes] | None = None,
    name_overrides: dict[str, str] | None = None,
) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            arcname = (name_overrides or {}).get(name, name)
            info = zipfile.ZipInfo(filename=arcname)
            info.compress_type = compress
            zf.writestr(info, data)
        if extra_infos:
            for info in extra_infos:
                payload = (extra_payloads or {}).get(info.filename, b"x")
                zf.writestr(info, payload)
    return buf.getvalue()


def write_zip(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def valid_zip_bytes() -> bytes:
    return zip_bytes(build_file_map())
