"""Evaluate supplied INR-HER-001 Phase 1 evidence.

Phase 1 does not create a Windows token, Job, ACL, or Git snapshot.
A narrow hash-agreement result is not an isolation PASS.
"""

from __future__ import annotations

import hashlib
import json

from docs.inr_her_001.validate_her_v1 import (
    EVENT_SCHEMA_VERSION,
    R3_SCHEMA_VERSIONS,
    DuplicateJsonKey,
    output_errors,
    parse_json,
    schema_errors,
)

ACCEPTED_SUPERVISOR = "docs/inr_001/supervisor_inr_v0.py"
ACCEPTED_R3_HEAD = "7c2a0e733aa782270e98abb3fa3012f98881a486"
SOURCE_HEAD = "38131191710aad087c274fc3ffc95e80f1c140cf"
PHASE1_CEILING = "ISOLATION_PASS_UNAVAILABLE"
PYTHON_PIN_RATIFIED = False
PRIVILEGED_EXECUTED = False
WRITERS_OUTSIDE_T_SUPPORTED = False
RATIFIED_GIT_SHA256 = None
RATIFIED_PYTHON_SHA256 = None

SURFACE_ROLES = (
    "execution_cwd",
    "staged_validator",
    "case_inputs",
    "probe",
    "interpreter_tree",
    "git_runtime_tree",
    "git_snapshot",
    "git_config_closure",
    "ledger",
)
PREDICATE_IDS = (
    "her_surface_hash_agreement",
    "her_u_vs_p",
    "her_child_contained",
    "her_git_snapshot_sole_source",
    "her_git_config_closed",
    "her_runtime_pinned",
    "her_git_pin",
    "writers_outside_t_excluded",
    "independent_external_witness",
    "all_writer_isolation_bounded_v1",
)
TRUST_BASE = (
    "Windows kernel on the selected host, including the NTFS ACL and mandatory integrity enforcement used for the event.",
    "SYSTEM, TrustedInstaller, and the services present in the hosted image at job start. Declared, not censused.",
    "GitHub-hosted job administrator account with UAC disabled, including the runner agent and earlier steps started by that account. Declared unexcludable writer inside T.",
    "HER controller in supervisor_her_v1.py from the completed pin check through POST_MEASUREMENT.",
    "Collector in collect_bundle_her_v1.py after POST_MEASUREMENT, only for the mutable export outside P.",
    "GitHub Actions hosting and the hypervisor under that VM. Declared, not attested.",
    "Publisher of the selected runner image. Declared, not attested.",
    "Pinned CPython 3.11.9 bytes after an authenticated SHA-256 exists. Phase 1 status PIN_PENDING.",
    "Pinned MinGit bytes that build and read the snapshot. Phase 1 status UNRATIFIED.",
    "SHA-pinned workflow actions only after a workflow file is separately approved. No workflow is part of Phase 1.",
)
NONCLAIMS = (
    "literal_all_writer_isolation",
    "writers_outside_t_measured",
    "independent_external_witness",
    "full_inr_pass",
    "human_final",
    "production_authority",
    "external_run",
    "python_3_11_9_sha256_ratified",
    "mingit_digest_ratified",
    "privileged_windows_tests_executed",
)
BLOCKER_PRIORITY = (
    "HER_PLATFORM_UNSUPPORTED",
    "HER_SCHEMA_VERSION",
    "HER_SCHEMA_REJECTED",
    "HER_SUPERVISOR_EDIT_REQUIRED",
    "HER_PYTHON_PIN_PENDING",
    "HER_GIT_PIN_UNRATIFIED",
    "HER_GIT_PIN_MISMATCH",
    "HER_TRUST_BASE_MISMATCH",
    "HER_GIT_OWNERSHIP_REFUSED",
    "HER_TOKEN_PRIVILEGE_UNAVAILABLE",
    "HER_PHASE1_PASS_FORBIDDEN",
)
_ALLOWED_VERSIONS = frozenset({
    "inr.event.v0.r4",
    "inr.supervisor.result.v0.r4",
    "inr.her.surface_record.v0",
})
_PIN_PREFIXES = (
    "$.python_pin_status:",
    "$.python_pin_sha256:",
    "$.git_pin_status:",
    "$.git_pin_sha256:",
)
_PASS_CLAIM_EXACT = frozenset({
    "pass",
    "isolation_pass",
    "full_inr_pass",
    "all_writer_pass",
    "all_writer_isolation_bounded_v1",
    "independent_witness",
    "human_final",
})


def trust_base_digest() -> str:
    """Digest the code-owned T list. P is not an entry."""
    payload = json.dumps(list(TRUST_BASE), ensure_ascii=True, separators=(",", ":"), sort_keys=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify_python_pin() -> tuple[str, str]:
    """Phase 1 has no authenticated CPython 3.11.9 SHA-256."""
    return ("BLOCKED", "HER_PYTHON_PIN_PENDING")


def classify_git_pin(digest: object) -> tuple[str, str]:
    """Unratified MinGit stays blocked. A ratified mismatch uses the contract reason."""
    ratified = RATIFIED_GIT_SHA256
    if ratified is None:
        return ("BLOCKED", "HER_GIT_PIN_UNRATIFIED")
    if not isinstance(digest, str) or digest != ratified:
        return ("BLOCKED", "HER_GIT_PIN_MISMATCH")
    return ("BLOCKED", "HER_PHASE1_PASS_FORBIDDEN")


def synthetic_event() -> dict:
    """Schema-valid Phase 1 fixture. It must not produce an isolation PASS."""
    event_id = "evt-1"
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "accepted_r3_head": ACCEPTED_R3_HEAD,
        "source_head": SOURCE_HEAD,
        "host_class": "WINDOWS_X64",
        "runner_flags": [],
        "trust_base_digest": trust_base_digest(),
        "python_pin_status": "PIN_PENDING",
        "python_pin_sha256": None,
        "git_pin_status": "UNRATIFIED",
        "git_pin_sha256": None,
        "supervisor_result": _synthetic_supervisor(event_id),
        "surface_records": [_surface(role, event_id) for role in SURFACE_ROLES],
    }


def request_supervisor_change(_detail: str = "") -> dict:
    """Refuse an edit to the accepted r3 supervisor and return a blocker."""
    reason = "HER_SUPERVISOR_EDIT_REQUIRED"
    return _emit("UNPARSED", _blocked_predicates(reason), "BLOCKED", reason)


def validate_event(document: object) -> dict:
    """Accept a dict or JSON text and return a fail-closed predicate result."""
    return evaluate_event(document)


def evaluate_event(document: object) -> dict:
    """Validate one supplied event. Schema-invalid input returns a result."""
    if isinstance(document, (str, bytes)):
        try:
            parsed = parse_json(document)
        except (DuplicateJsonKey, UnicodeError, ValueError):
            return _emit("UNPARSED", _blocked_predicates("HER_SCHEMA_REJECTED"), "BLOCKED", "HER_SCHEMA_REJECTED")
    else:
        parsed = document
    if type(parsed) is not dict:
        return _emit("UNPARSED", _blocked_predicates("HER_SCHEMA_REJECTED"), "BLOCKED", "HER_SCHEMA_REJECTED")

    event_id = _event_id(parsed)
    version_reason = _version_reason(parsed)
    if version_reason is not None or parsed.get("schema_version") != EVENT_SCHEMA_VERSION:
        reason = _schema_block_reason(parsed, [], version_reason or "HER_SCHEMA_VERSION")
        if parsed.get("schema_version") is None and version_reason is None:
            reason = _schema_block_reason(parsed, ["$.schema_version: missing"], None)
        return _emit(event_id, _blocked_predicates(reason or "HER_SCHEMA_REJECTED"), "BLOCKED", reason or "HER_SCHEMA_REJECTED")

    errors = schema_errors(parsed)
    schema_reason = _schema_block_reason(parsed, errors, None)
    predicates = _downgrade(_core_predicates(parsed), schema_reason)
    predicates.append(_all_writer(predicates, parsed, schema_reason))
    status, reason = _combine(predicates, parsed, schema_reason)
    return _emit(event_id, predicates, status, reason)


def enforce_phase1_ceiling(status: str, reason: str, predicates: list[dict]) -> tuple[str, str, list[dict]]:
    """Stop an isolation PASS while pins, privilege, or non-T writers are open."""
    if PYTHON_PIN_RATIFIED and PRIVILEGED_EXECUTED and WRITERS_OUTSIDE_T_SUPPORTED:
        return status, reason, predicates
    rewritten: list[dict] = []
    for predicate in predicates:
        if predicate["predicate_id"] == "all_writer_isolation_bounded_v1" and predicate["status"] == "PASS":
            rewritten.append(_pred(predicate["predicate_id"], "BLOCKED", "HER_PHASE1_PASS_FORBIDDEN"))
        else:
            rewritten.append(predicate)
    if status == "PASS":
        return "BLOCKED", "HER_PHASE1_PASS_FORBIDDEN", rewritten
    return status, reason, rewritten


def _synthetic_supervisor(event_id: str) -> dict:
    return {
        "schema_version": "inr.supervisor.result.v0.r4",
        "event_id": event_id,
        "evidence_origin": "CURRENT_EVENT",
        "child_sid": "",
        "child_integrity_claim": "UNVERIFIED",
        "child_in_job": "UNVERIFIED",
        "job_observation": "UNVERIFIED",
        "breakaway_requested": False,
        "git_config_self_test": "UNVERIFIED",
        "git_ownership_observation": "UNVERIFIED",
        "uses_live_checkout_git": False,
        "config_outside_closure": False,
        "provider_metadata_as_isolation": False,
        "requests_supervisor_edit": False,
        "writers_outside_t": "UNCONFIRMED",
        "independent_external_witness": "NOT_CLAIMED",
    }


def _surface(role: str, event_id: str) -> dict:
    body = hashlib.sha256(role.encode("utf-8")).hexdigest()
    listing = hashlib.sha256((role + ":listing").encode("utf-8")).hexdigest()
    return {
        "schema_version": "inr.her.surface_record.v0",
        "event_id": event_id,
        "surface_role": role,
        "evidence_origin": "CURRENT_EVENT",
        "freeze_sha256": body,
        "post_sha256": body,
        "listing_sha256": listing,
        "u_write_denied": True,
        "extra_entries": False,
        "reparse_escape": False,
    }


def _pred(predicate_id: str, status: str, reason: str) -> dict[str, str]:
    return {"predicate_id": predicate_id, "status": status, "reason": reason}


def _blocked_predicates(reason: str) -> list[dict]:
    return [_pred(predicate_id, "BLOCKED", reason) for predicate_id in PREDICATE_IDS]


def _event_id(document: dict) -> str:
    value = document.get("event_id")
    if isinstance(value, str) and value:
        return value
    return "UNPARSED"


def _as_dict(value: object) -> dict:
    if type(value) is dict:
        return value
    return {}


def _as_list(value: object) -> list:
    if type(value) is list:
        return value
    return []


def _index(records: list) -> tuple[dict, list]:
    found: dict = {}
    duplicates: list = []
    for record in records:
        if type(record) is not dict:
            continue
        role = record.get("surface_role")
        if not isinstance(role, str):
            continue
        if role in found:
            duplicates.append(role)
            continue
        found[role] = record
    return found, duplicates


def _version_reason(document: dict) -> str | None:
    versions: list = []
    if "schema_version" in document:
        versions.append(document.get("schema_version"))
    supervisor = document.get("supervisor_result")
    if type(supervisor) is dict and "schema_version" in supervisor:
        versions.append(supervisor.get("schema_version"))
    for record in _as_list(document.get("surface_records")):
        if type(record) is dict and "schema_version" in record:
            versions.append(record.get("schema_version"))
    if any(item in R3_SCHEMA_VERSIONS for item in versions):
        return "HER_SCHEMA_VERSION"
    if any(item not in _ALLOWED_VERSIONS for item in versions):
        return "HER_SCHEMA_VERSION"
    if "schema_version" in document and document.get("schema_version") != EVENT_SCHEMA_VERSION:
        return "HER_SCHEMA_VERSION"
    return None


def _only_pin(errors: list[str]) -> bool:
    return bool(errors) and all(error.startswith(_PIN_PREFIXES) for error in errors)


def _pin_schema_reason(errors: list[str]) -> str:
    if any("python_pin_" in error for error in errors):
        return "HER_PYTHON_PIN_PENDING"
    if any("git_pin_" in error for error in errors):
        return "HER_GIT_PIN_UNRATIFIED"
    return "HER_SCHEMA_REJECTED"


def _schema_block_reason(document: dict, errors: list[str], version_reason: str | None) -> str | None:
    if not errors and version_reason is None:
        return None
    host = document.get("host_class")
    if isinstance(host, str) and host != "WINDOWS_X64":
        return "HER_PLATFORM_UNSUPPORTED"
    if version_reason is not None:
        return version_reason
    if _only_pin(errors):
        return _pin_schema_reason(errors)
    if errors:
        return "HER_SCHEMA_REJECTED"
    return None


def _downgrade(predicates: list[dict], schema_reason: str | None) -> list[dict]:
    if schema_reason is None:
        return predicates
    downgraded = []
    for predicate in predicates:
        if predicate["status"] == "PASS":
            downgraded.append(_pred(predicate["predicate_id"], "BLOCKED", schema_reason))
        else:
            downgraded.append(predicate)
    return downgraded


def _combine(predicates: list[dict], document: object, schema_reason: str | None) -> tuple[str, str]:
    fails = [predicate for predicate in predicates if predicate["status"] == "FAIL"]
    if fails:
        return "FAIL", fails[0]["reason"]
    reasons = [predicate["reason"] for predicate in predicates if predicate["status"] == "BLOCKED"]
    if schema_reason is not None:
        reasons.append(schema_reason)
    if type(document) is dict:
        host = document.get("host_class")
        if isinstance(host, str) and host != "WINDOWS_X64":
            reasons.append("HER_PLATFORM_UNSUPPORTED")
        supervisor = document.get("supervisor_result")
        if type(supervisor) is dict and supervisor.get("requests_supervisor_edit") is True:
            reasons.append("HER_SUPERVISOR_EDIT_REQUIRED")
    for token in BLOCKER_PRIORITY:
        if token in reasons:
            return "BLOCKED", token
    unconfirmed = [predicate for predicate in predicates if predicate["status"] == "UNCONFIRMED"]
    if unconfirmed:
        return "UNCONFIRMED", unconfirmed[0]["reason"]
    return "PASS", "HER_PHASE1_PASS_FORBIDDEN"


def _all_writer(predicates: list[dict], document: object, schema_reason: str | None) -> dict:
    status, reason = _combine(predicates, document, schema_reason)
    if status == "PASS":
        status, reason = "BLOCKED", "HER_PHASE1_PASS_FORBIDDEN"
    return _pred("all_writer_isolation_bounded_v1", status, reason)


def _core_predicates(document: dict) -> list[dict]:
    return [
        _pred("her_surface_hash_agreement", *_hash_agreement(document)),
        _pred("her_u_vs_p", *_u_vs_p(document)),
        _pred("her_child_contained", *_child(document)),
        _pred("her_git_snapshot_sole_source", *_snapshot(document)),
        _pred("her_git_config_closed", *_config(document)),
        _pred("her_runtime_pinned", *classify_python_pin()),
        _pred("her_git_pin", *classify_git_pin(document.get("git_pin_sha256"))),
        _pred("writers_outside_t_excluded", *_writers(document)),
        _pred("independent_external_witness", *_witness(document)),
    ]


def _pick(outcomes: list[tuple[str, int, str]], default: tuple[str, str]) -> tuple[str, str]:
    grouped = {"FAIL": [], "BLOCKED": [], "UNCONFIRMED": []}
    for status, priority, reason in outcomes:
        grouped[status].append((priority, reason))
    for status in ("FAIL", "BLOCKED", "UNCONFIRMED"):
        if grouped[status]:
            grouped[status].sort()
            return status, grouped[status][0][1]
    return default


def _has_origin(records: list, supervisor: dict, origin: str) -> bool:
    if supervisor.get("evidence_origin") == origin:
        return True
    return any(type(record) is dict and record.get("evidence_origin") == origin for record in records)


def _mutated(record: dict) -> bool:
    freeze = record.get("freeze_sha256")
    post = record.get("post_sha256")
    if isinstance(freeze, str) and isinstance(post, str) and freeze != post:
        return True
    if record.get("extra_entries") is True or record.get("reparse_escape") is True:
        return True
    return record.get("planted_runtime") is True


def _all_hashes_agree(found: dict) -> bool:
    for role in SURFACE_ROLES:
        record = found.get(role)
        if type(record) is not dict:
            return False
        freeze = record.get("freeze_sha256")
        post = record.get("post_sha256")
        if not isinstance(freeze, str) or freeze != post:
            return False
    return True


def _origins_current(records: list, supervisor: dict) -> bool:
    if supervisor.get("evidence_origin") != "CURRENT_EVENT":
        return False
    if not records:
        return False
    return all(type(record) is dict and record.get("evidence_origin") == "CURRENT_EVENT" for record in records)


def _id_conflict(document: dict) -> bool:
    event_id = document.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        return False
    supervisor = document.get("supervisor_result")
    if type(supervisor) is dict and "event_id" in supervisor and supervisor.get("event_id") != event_id:
        return True
    for record in _as_list(document.get("surface_records")):
        if type(record) is dict and "event_id" in record and record.get("event_id") != event_id:
            return True
    return False


def _trust_ok(document: dict) -> bool:
    return document.get("trust_base_digest") == trust_base_digest()


def _hash_agreement(document: dict) -> tuple[str, str]:
    records = _as_list(document.get("surface_records"))
    supervisor = _as_dict(document.get("supervisor_result"))
    found, duplicates = _index(records)
    outcomes: list[tuple[str, int, str]] = []
    if duplicates:
        outcomes.append(("FAIL", 0, "HER_CONTRADICTION"))
    if _id_conflict(document):
        outcomes.append(("FAIL", 1, "HER_CONTRADICTION"))
    if _has_origin(records, supervisor, "FORGED"):
        outcomes.append(("FAIL", 2, "HER_FORGED_EVIDENCE"))
    if any(type(record) is dict and _mutated(record) for record in records):
        outcomes.append(("FAIL", 3, "HER_SURFACE_MUTATED"))
    if not _all_hashes_agree(found):
        outcomes.append(("UNCONFIRMED", 0, "HER_SURFACE_RECORD_ABSENT"))
    if not _origins_current(records, supervisor):
        if _has_origin(records, supervisor, "HISTORICAL_R3"):
            outcomes.append(("UNCONFIRMED", 1, "HER_HISTORICAL_R3"))
        elif _has_origin(records, supervisor, "RUNNER_FLAG"):
            outcomes.append(("UNCONFIRMED", 2, "HER_RUNNER_FLAG_ONLY"))
        elif not _has_origin(records, supervisor, "FORGED"):
            outcomes.append(("UNCONFIRMED", 3, "HER_HISTORICAL_R3"))
    if not _trust_ok(document):
        outcomes.append(("BLOCKED", 0, "HER_TRUST_BASE_MISMATCH"))
    return _pick(outcomes, ("PASS", "HASH_AGREEMENT_ONLY"))


def _pass_claim(flag: object) -> bool:
    if not isinstance(flag, str):
        return False
    token = flag.strip().casefold().replace("-", "_")
    if token in _PASS_CLAIM_EXACT:
        return True
    return token.endswith("_pass") or token.endswith("=pass") or token.startswith("pass=")


def _pass_flags(flags: object) -> bool:
    return type(flags) is list and any(_pass_claim(flag) for flag in flags)


def _other_flags(flags: object) -> bool:
    if type(flags) is not list:
        return False
    return any(isinstance(flag, str) and flag != "" and not _pass_claim(flag) for flag in flags)


def _u_vs_p(document: dict) -> tuple[str, str]:
    records = _as_list(document.get("surface_records"))
    supervisor = _as_dict(document.get("supervisor_result"))
    _found, duplicates = _index(records)
    outcomes: list[tuple[str, int, str]] = []
    if duplicates:
        outcomes.append(("FAIL", 0, "HER_CONTRADICTION"))
    if _pass_flags(document.get("runner_flags")):
        outcomes.append(("FAIL", 1, "HER_CONTRADICTION"))
    if _has_origin(records, supervisor, "FORGED"):
        outcomes.append(("FAIL", 2, "HER_FORGED_EVIDENCE"))
    if any(type(record) is dict and record.get("u_write_denied") is False for record in records):
        outcomes.append(("FAIL", 3, "HER_U_WRITE_GRANTED"))
    if any(type(record) is dict and record.get("reparse_escape") is True for record in records):
        outcomes.append(("FAIL", 4, "HER_REPARSE_ESCAPE"))
    if supervisor.get("acl_observation") == "CLAIMED_GRANT":
        outcomes.append(("FAIL", 5, "HER_U_WRITE_GRANTED"))
    if any(type(record) is dict and record.get("planted_runtime") is True for record in records):
        outcomes.append(("FAIL", 6, "HER_SURFACE_MUTATED"))
    if any(role not in _found for role in SURFACE_ROLES):
        outcomes.append(("UNCONFIRMED", 0, "HER_SURFACE_RECORD_ABSENT"))
    if _has_origin(records, supervisor, "RUNNER_FLAG") or _other_flags(document.get("runner_flags")):
        outcomes.append(("UNCONFIRMED", 1, "HER_RUNNER_FLAG_ONLY"))
    if _has_origin(records, supervisor, "HISTORICAL_R3"):
        outcomes.append(("UNCONFIRMED", 2, "HER_HISTORICAL_R3"))
    if supervisor.get("provider_metadata_as_isolation") is True:
        outcomes.append(("UNCONFIRMED", 3, "HER_PROVIDER_METADATA_NOT_PROOF"))
    if "acl_observation" not in supervisor or supervisor.get("acl_observation") == "OMITTED":
        outcomes.append(("UNCONFIRMED", 4, "HER_ACL_SNAPSHOT_OMITTED"))
    outcomes.append(("UNCONFIRMED", 5, "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))
    return _pick(outcomes, ("UNCONFIRMED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))


def _child(document: dict) -> tuple[str, str]:
    records = _as_list(document.get("surface_records"))
    supervisor = _as_dict(document.get("supervisor_result"))
    outcomes: list[tuple[str, int, str]] = []
    if _has_origin(records, supervisor, "FORGED"):
        outcomes.append(("FAIL", 0, "HER_FORGED_EVIDENCE"))
    if supervisor.get("child_integrity_claim") == "OTHER":
        outcomes.append(("FAIL", 1, "HER_CHILD_TOKEN_NOT_RESTRICTED"))
    escaped = (
        supervisor.get("child_in_job") == "OUTSIDE"
        or supervisor.get("breakaway_requested") is True
        or supervisor.get("job_observation") == "BREAKAWAY"
    )
    if escaped:
        outcomes.append(("FAIL", 2, "HER_JOB_ESCAPE"))
    sid = supervisor.get("child_sid")
    if not isinstance(sid, str) or sid == "":
        outcomes.append(("UNCONFIRMED", 0, "HER_U_SID_ABSENT"))
    outcomes.append(("UNCONFIRMED", 1, "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))
    return _pick(outcomes, ("UNCONFIRMED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))


def _snapshot(document: dict) -> tuple[str, str]:
    records = _as_list(document.get("surface_records"))
    supervisor = _as_dict(document.get("supervisor_result"))
    found, duplicates = _index(records)
    snap = found.get("git_snapshot")
    outcomes: list[tuple[str, int, str]] = []
    if duplicates:
        outcomes.append(("FAIL", 0, "HER_CONTRADICTION"))
    if _has_origin(records, supervisor, "FORGED"):
        outcomes.append(("FAIL", 1, "HER_FORGED_EVIDENCE"))
    if supervisor.get("uses_live_checkout_git") is True:
        outcomes.append(("FAIL", 2, "HER_GIT_SOURCE_NOT_SNAPSHOT"))
    if type(snap) is dict and (snap.get("extra_entries") is True or snap.get("planted_runtime") is True):
        outcomes.append(("FAIL", 3, "HER_GIT_SOURCE_NOT_SNAPSHOT"))
    if type(snap) is not dict:
        outcomes.append(("UNCONFIRMED", 0, "HER_SURFACE_RECORD_ABSENT"))
    elif snap.get("evidence_origin") == "HISTORICAL_R3":
        outcomes.append(("UNCONFIRMED", 1, "HER_HISTORICAL_R3"))
    elif snap.get("evidence_origin") == "RUNNER_FLAG":
        outcomes.append(("UNCONFIRMED", 2, "HER_RUNNER_FLAG_ONLY"))
    outcomes.append(("UNCONFIRMED", 3, "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))
    return _pick(outcomes, ("UNCONFIRMED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))


def _config(document: dict) -> tuple[str, str]:
    records = _as_list(document.get("surface_records"))
    supervisor = _as_dict(document.get("supervisor_result"))
    outcomes: list[tuple[str, int, str]] = []
    if _has_origin(records, supervisor, "FORGED"):
        outcomes.append(("FAIL", 0, "HER_FORGED_EVIDENCE"))
    if supervisor.get("git_config_self_test") == "CLAIMED_PASS":
        outcomes.append(("FAIL", 1, "HER_CONTRADICTION"))
    if supervisor.get("git_ownership_observation") == "CLAIMED_PASS":
        outcomes.append(("FAIL", 2, "HER_CONTRADICTION"))
    if supervisor.get("config_outside_closure") is True:
        outcomes.append(("FAIL", 3, "HER_GIT_CONFIG_SCOPE_OPEN"))
    if supervisor.get("git_config_self_test") == "FAILED":
        outcomes.append(("FAIL", 4, "HER_GIT_CONFIG_SELF_TEST_FAILED"))
    if supervisor.get("git_ownership_observation") == "FAILED":
        outcomes.append(("BLOCKED", 0, "HER_GIT_OWNERSHIP_REFUSED"))
    if not supervisor:
        outcomes.append(("UNCONFIRMED", 0, "HER_SURFACE_RECORD_ABSENT"))
    outcomes.append(("UNCONFIRMED", 1, "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))
    return _pick(outcomes, ("UNCONFIRMED", "HER_PRIVILEGED_OBSERVATION_UNVERIFIED"))


def _writers(document: dict) -> tuple[str, str]:
    value = _as_dict(document.get("supervisor_result")).get("writers_outside_t")
    if isinstance(value, str) and value != "UNCONFIRMED":
        return "FAIL", "HER_CONTRADICTION"
    return "UNCONFIRMED", "HER_WRITERS_OUTSIDE_T_UNCONFIRMED"


def _witness(document: dict) -> tuple[str, str]:
    value = _as_dict(document.get("supervisor_result")).get("independent_external_witness")
    if isinstance(value, str) and value != "NOT_CLAIMED":
        return "FAIL", "HER_CONTRADICTION"
    return "UNCONFIRMED", "INDEPENDENT_WITNESS_NOT_CLAIMED"


def _privileged() -> dict[str, str]:
    return {
        "token": "UNVERIFIED",
        "job": "UNVERIFIED",
        "acl": "UNVERIFIED",
        "git_ownership": "UNVERIFIED",
    }


def _emit(event_id: str, predicates: list[dict], status: str, reason: str) -> dict:
    status, reason, predicates = enforce_phase1_ceiling(status, reason, predicates)
    result = {
        "schema_version": "inr.her.predicate_result.v0",
        "event_id": event_id,
        "phase1_ceiling": PHASE1_CEILING,
        "privileged_tests": _privileged(),
        "nonclaims": list(NONCLAIMS),
        "predicates": predicates,
        "overall_status": status,
        "overall_reason": reason,
    }
    problems = output_errors(result)
    if problems:
        raise RuntimeError("HER predicate result failed its schema: " + "; ".join(problems))
    return result
