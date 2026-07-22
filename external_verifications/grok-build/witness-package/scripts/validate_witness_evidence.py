#!/usr/bin/env python3
"""
Structural validator for Independent Witness evidence directories (C2E-4 / evidence_schema_version=1).

Validates presence, format, per-file schema, and vocabulary — not truthfulness,
independence, or execution. A structural PASS never proves that Docker or
Cargo actually ran, that the Witness was independent, or that any recorded
value is true.

This script writes only to its own stdout/stderr. It never writes into the
evidence directory it is validating (see VALIDATOR.md "Output policy").
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants (pinned identities — checked structurally, not re-derived)
# ---------------------------------------------------------------------------

EVIDENCE_SCHEMA_VERSION = "1"

EXPECTED_GROK_COMMIT = "98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
EXPECTED_IMAGE_DIGEST = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
EXPECTED_CARGO_LOCK_SHA256 = "1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421"
EXACT_BUILD_CMD = "cargo build -p xai-grok-pager-bin --locked"
PACKAGE_TAG_EXPECTED = "grok-build-witness-v1.0.0-rc3"
EXPECTED_DOTSLASH_VERSION = "0.5.7"

MANIFEST_NAME = "EVIDENCE_MANIFEST.sha256"

# Optional host-only files not required in the manifest (documented in VALIDATOR.md).
MANIFEST_OPTIONAL_EVIDENCE = frozenset({"HOST_RUN_METADATA.txt"})

RAW_STREAM_FILES = frozenset(
    {
        "BUILD_STDOUT.txt",
        "BUILD_STDERR.txt",
        "CONTAINER_STDOUT.txt",
        "CONTAINER_STDERR.txt",
    }
)

REQUIRED_FILES = (
    "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
    "ENVIRONMENT.txt",
    "SOURCE_ACQUISITION.txt",
    "SOURCE_IDENTITY.txt",
    "IMAGE_IDENTITY.txt",
    "BOOTSTRAP.txt",
    "CLEAN_TARGET_PROOF.txt",
    "BUILD_COMMAND.txt",
    "BUILD_ENVIRONMENT.txt",
    "BUILD_STDOUT.txt",
    "BUILD_STDERR.txt",
    "DOCKER_EXIT_CODE.txt",
    "BUILD_EXIT_CODE.txt",
    "BUILD_TIMING.txt",
    "CONTAINER_STDOUT.txt",
    "CONTAINER_STDERR.txt",
    "ARTIFACT_IDENTITY.txt",
    "STATIC_ARTIFACT_INSPECTION.txt",
    "POST_BUILD_INTEGRITY.txt",
    "WITNESS_STATEMENT.md",
    "WITNESS_VERDICT.md",
    "DEVIATIONS.txt",
    MANIFEST_NAME,
    "REDACTIONS.md",
)

# Structured (key=value) evidence files that must declare evidence_schema_version.
# Raw stdout/stderr capture files and the manifest itself are exempt.
SCHEMA_VERSIONED_FILES = tuple(
    name for name in REQUIRED_FILES if name not in RAW_STREAM_FILES and name != MANIFEST_NAME
)

OUTCOME_VALUES = frozenset(
    {
        "BUILD_NOT_STARTED",
        "CARGO_FAILED",
        "CARGO_SUCCEEDED_ARTIFACT_MISSING",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        "INFRASTRUCTURE_FAILURE",
    }
)

# Per-outcome expectations for BUILD_EXIT_CODE.txt fields. cargo_exit_code:
#   "0"    -> must equal exactly "0"
#   "N/A"  -> must equal "N/A" (case-insensitive)
#   None   -> must be numeric and non-zero (CARGO_FAILED)
OUTCOME_RULES = {
    "BUILD_NOT_STARTED": {"cargo_started": "NO", "build_status": "BUILD_NOT_STARTED", "cargo_exit_code": "N/A"},
    "CARGO_FAILED": {"cargo_started": "YES", "build_status": "FAILED", "cargo_exit_code": None},
    "CARGO_SUCCEEDED_ARTIFACT_MISSING": {
        "cargo_started": "YES",
        "build_status": "COMPLETE",
        "cargo_exit_code": "0",
    },
    "CARGO_SUCCEEDED_ARTIFACT_PRESENT": {
        "cargo_started": "YES",
        "build_status": "COMPLETE",
        "cargo_exit_code": "0",
    },
    "INFRASTRUCTURE_FAILURE": {"cargo_started": "NO", "build_status": "INFRASTRUCTURE_FAILURE", "cargo_exit_code": "N/A"},
}

# Outcomes where cargo actually started (BUILD_TIMING.txt cargo_* fields become mandatory).
OUTCOMES_WITH_CARGO_TIMING = frozenset(
    {"CARGO_FAILED", "CARGO_SUCCEEDED_ARTIFACT_MISSING", "CARGO_SUCCEEDED_ARTIFACT_PRESENT"}
)

VERDICT_VALUES = frozenset({"PASS", "PARTIAL", "FAIL", "INDETERMINATE"})
VERDICT_LINE_RE = re.compile(r"^Witness proposed verdict:\s*(\S+)\s*$", re.MULTILINE)

DEVIATION_SEVERITY_VALUES = frozenset(
    {"NONE", "NONMATERIAL_DISCLOSED", "MATERIAL_NONCANONICAL", "PROHIBITED"}
)
# Severities that forbid a PASS ceiling.
DEVIATION_SEVERITY_FORBIDS_PASS = frozenset({"MATERIAL_NONCANONICAL", "PROHIBITED"})

PROHIBITED_REDACTION_KEYWORDS = (
    "commit",
    "digest",
    "sha256",
    "exit_code",
    "exit code",
    "independence",
    "artifact_size",
    "artifact_sha256",
)

FORBIDDEN_PLACEHOLDERS = (
    "TODO",
    "FILL_ME",
    "<replace-me>",
    "PLACEHOLDER_UNTIL_RC3_TAGGED",
)

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NUMERIC_RE = re.compile(r"^\d+$")
SAFE_TOKEN_RE = re.compile(r"^[a-zA-Z0-9._-]+$")

# Manifest filename grammar: relative path, POSIX separators, safe characters only.
FILENAME_RE = re.compile(r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$")
MANIFEST_LINE_RE = re.compile(r"^([0-9A-Za-z]{64})  (.+)$")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def parse_kv(text: str) -> dict[str, str]:
    """Parse simple ``key=value`` lines. Blank lines, markdown headings ('#'),
    table rows ('|'), and lines without '=' are ignored."""
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("|"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            continue
        result[key] = value.strip()
    return result


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_hex_commit(value: str) -> bool:
    return bool(COMMIT_RE.match(value))


def is_sha256(value: str) -> bool:
    return bool(SHA256_RE.match(value))


def is_numeric(value: str) -> bool:
    return bool(NUMERIC_RE.match(value))


def is_yes_no(value: str) -> bool:
    return value in ("yes", "no")


def is_safe_token(value: str) -> bool:
    if not value or any(c.isspace() for c in value):
        return False
    if "/" in value or "\\" in value or ".." in value:
        return False
    return bool(SAFE_TOKEN_RE.match(value))


def strip_digest_prefix(value: str) -> str:
    if value.lower().startswith("sha256:"):
        return value[len("sha256:"):]
    return value


def require_fields(name: str, fields: dict[str, str], required: tuple[str, ...], errors: list[str]) -> None:
    for key in required:
        if key not in fields or fields[key] == "":
            fail(errors, f"{name}: missing required field '{key}'")


def check_schema_version(name: str, fields: dict[str, str], errors: list[str]) -> None:
    value = fields.get("evidence_schema_version")
    if value != EVIDENCE_SCHEMA_VERSION:
        fail(
            errors,
            f"{name}: evidence_schema_version must be '{EVIDENCE_SCHEMA_VERSION}' (found {value!r})",
        )


def require_exact(name: str, fields: dict[str, str], key: str, expected: str, errors: list[str]) -> None:
    value = fields.get(key)
    if value != expected:
        fail(errors, f"{name}: field '{key}' must be exactly {expected!r} (found {value!r})")


# ---------------------------------------------------------------------------
# Per-file required-field schemas (field names are normative; templates must match)
# ---------------------------------------------------------------------------

FILE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "WEAVER_FORGE_PACKAGE_IDENTITY.txt": (
        "evidence_schema_version",
        "witness_id",
        "run_id",
        "package_version",
        "weaver_forge_url",
        "weaver_forge_tag_requested",
        "weaver_forge_commit_resolved",
        "package_clone_head",
        "package_clone_detached",
        "package_clone_clean_status",
        "tag_head_match",
        "package_commit_authority",
        "grok_build_source_commit_expected",
        "canonical_run",
    ),
    "SOURCE_ACQUISITION.txt": (
        "evidence_schema_version",
        "weaver_forge_url",
        "weaver_forge_tag_requested",
        "weaver_forge_commit_resolved",
        "package_clone_head",
        "package_clone_clean_status",
        "tag_head_match",
        "package_commit_authority",
        "grok_build_url",
        "grok_build_commit_requested",
        "grok_build_commit_observed",
        "grok_build_clean_tree",
        "fresh_clones",
    ),
    "SOURCE_IDENTITY.txt": (
        "evidence_schema_version",
        "grok_build_commit_expected",
        "grok_build_commit_observed",
        "cargo_lock_sha256_expected",
        "cargo_lock_sha256_observed",
    ),
    "IMAGE_IDENTITY.txt": (
        "evidence_schema_version",
        "requested_image_string",
        "requested_digest",
        "docker_pull_exit_code",
        "image_id",
        "repo_digests",
        "os",
        "architecture",
        "platform",
        "digest_match_expected",
        "platform_match_expected",
    ),
    "ENVIRONMENT.txt": (
        "evidence_schema_version",
        "witness_id",
        "host_os",
        "host_arch",
        "host_docker_client_version",
        "host_docker_server_version",
        "container_os_release",
        "rustc_version",
        "cargo_version",
        "product_executed",
        "ldd_used",
    ),
    "BOOTSTRAP.txt": (
        "evidence_schema_version",
        "apt_packages",
        "dotslash_version",
        "dotslash_binary_path",
        "protoc_descriptor_src",
        "protoc_descriptor_writable",
        "protoc_descriptor_src_sha256",
        "protoc_descriptor_lf_sha256",
        "PROTOC",
        "protoc_version_output",
        "protoc_version_exit_code",
        "product_executed",
    ),
    "CLEAN_TARGET_PROOF.txt": (
        "evidence_schema_version",
        "cargo_target_dir_absolute",
        "required_entry_count",
        "observed_entry_count_host",
        "observed_entry_count_container",
        "proof_failed",
    ),
    "BUILD_COMMAND.txt": (
        "evidence_schema_version",
        "exact_build_command",
        "cargo_incremental",
        "working_directory",
        "product_executed",
    ),
    "BUILD_ENVIRONMENT.txt": (
        "evidence_schema_version",
        "HOME",
        "CARGO_HOME",
        "CARGO_TARGET_DIR",
        "CARGO_INCREMENTAL",
        "DOTSLASH_CACHE",
        "PROTOC",
        "docker_platform",
        "network_mode",
        "rust_image",
    ),
    "DOCKER_EXIT_CODE.txt": (
        "evidence_schema_version",
        "docker_started_utc",
        "docker_finished_utc",
        "docker_exit_code",
        "container_platform",
        "network_mode",
        "product_executed",
        "ldd_used",
        "outcome",
        "failure_stage",
    ),
    "BUILD_EXIT_CODE.txt": (
        "evidence_schema_version",
        "cargo_started",
        "outcome",
        "build_status",
        "cargo_exit_code",
        "failure_stage",
    ),
    "BUILD_TIMING.txt": (
        "evidence_schema_version",
        "outcome",
        "docker_started_utc",
        "docker_finished_utc",
    ),
    "ARTIFACT_IDENTITY.txt": (
        "evidence_schema_version",
        "applicable",
        "artifact_present",
        "product_executed",
        "ldd_used",
    ),
    "STATIC_ARTIFACT_INSPECTION.txt": (
        "evidence_schema_version",
        "inspection_applicable",
        "artifact_present",
    ),
    "POST_BUILD_INTEGRITY.txt": (
        "evidence_schema_version",
        "source_head_before",
        "source_head_after",
        "source_clean_before",
        "source_clean_after",
        "cargo_lock_sha256_before",
        "cargo_lock_sha256_after",
        "source_or_lock_changed",
        "artifact_exists",
        "evidence_inventory_complete",
    ),
    "WITNESS_STATEMENT.md": (
        "evidence_schema_version",
        "witness_identity_or_handle",
        "not_package_owner",
        "not_owner_side_reproducer",
        "witness_controlled_host",
        "ai_assistance_used",
        "human_review_completed",
        "product_executed",
        "ldd_used",
    ),
    "WITNESS_VERDICT.md": (
        "evidence_schema_version",
        "run_id",
        "package_tag",
        "weaver_forge_commit",
        "grok_build_commit",
        "product_executed",
        "ldd_used",
        "maintainer_intake_verdict",
    ),
    "DEVIATIONS.txt": (
        "evidence_schema_version",
        "deviation_state",
    ),
    "REDACTIONS.md": (
        "evidence_schema_version",
        "redaction_state",
        "semantic_integrity_declaration",
    ),
}


# ---------------------------------------------------------------------------
# Per-file semantic checks (beyond simple presence)
# ---------------------------------------------------------------------------


def check_weaver_forge_package_identity(fields: dict[str, str], errors: list[str]) -> None:
    name = "WEAVER_FORGE_PACKAGE_IDENTITY.txt"
    if not is_safe_token(fields.get("witness_id", "")):
        fail(errors, f"{name}: witness_id must be a non-empty token with no path separators, whitespace, or '..'")
    if not is_safe_token(fields.get("run_id", "")):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
    require_exact(name, fields, "grok_build_source_commit_expected", EXPECTED_GROK_COMMIT, errors)
    require_exact(name, fields, "package_commit_authority", "annotated_tag_resolution", errors)
    resolved = fields.get("weaver_forge_commit_resolved", "")
    if resolved and not is_hex_commit(resolved):
        fail(errors, f"{name}: weaver_forge_commit_resolved must be a 40-char lowercase hex commit")
    head = fields.get("package_clone_head", "")
    if head and not is_hex_commit(head):
        fail(errors, f"{name}: package_clone_head must be a 40-char lowercase hex commit")
    if resolved and head and resolved != head:
        fail(errors, f"{name}: package_clone_head must equal weaver_forge_commit_resolved (tag→HEAD integrity)")
    if fields.get("package_clone_clean_status") not in ("yes", "no", ""):
        fail(errors, f"{name}: package_clone_clean_status must be yes|no")
    if fields.get("package_clone_detached") not in ("yes", "no", ""):
        fail(errors, f"{name}: package_clone_detached must be yes|no")
    if fields.get("tag_head_match") not in ("yes", "no", ""):
        fail(errors, f"{name}: tag_head_match must be yes|no")
    elif fields.get("tag_head_match") == "no":
        fail(errors, f"{name}: tag_head_match=no (detached HEAD must equal resolved tag commit)")
    tag = fields.get("weaver_forge_tag_requested", "")
    if tag and tag != PACKAGE_TAG_EXPECTED and fields.get("canonical_run") == "yes":
        fail(errors, f"{name}: canonical_run=yes requires weaver_forge_tag_requested={PACKAGE_TAG_EXPECTED}")
    if tag and not re.match(r"^grok-build-witness-v\d+\.\d+\.\d+(-rc\d+)?$", tag):
        fail(errors, f"{name}: weaver_forge_tag_requested does not match expected tag grammar: {tag!r}")
    canonical_run = fields.get("canonical_run", "")
    if canonical_run not in ("yes", "no"):
        fail(errors, f"{name}: canonical_run must be yes|no")
    elif canonical_run == "no" and not fields.get("noncanonical_disclosure"):
        fail(errors, f"{name}: noncanonical_disclosure is required when canonical_run=no")


def check_source_acquisition(fields: dict[str, str], errors: list[str]) -> None:
    name = "SOURCE_ACQUISITION.txt"
    require_exact(name, fields, "grok_build_commit_requested", EXPECTED_GROK_COMMIT, errors)
    require_exact(name, fields, "package_commit_authority", "annotated_tag_resolution", errors)
    observed = fields.get("grok_build_commit_observed", "")
    if observed and not is_hex_commit(observed):
        fail(errors, f"{name}: grok_build_commit_observed must be a 40-char lowercase hex commit")
    resolved = fields.get("weaver_forge_commit_resolved", "")
    if resolved and not is_hex_commit(resolved):
        fail(errors, f"{name}: weaver_forge_commit_resolved must be a 40-char lowercase hex commit")
    head = fields.get("package_clone_head", "")
    if head and not is_hex_commit(head):
        fail(errors, f"{name}: package_clone_head must be a 40-char lowercase hex commit")
    if resolved and head and resolved != head:
        fail(errors, f"{name}: package_clone_head must equal weaver_forge_commit_resolved (tag→HEAD integrity)")
    if fields.get("tag_head_match") == "no":
        fail(errors, f"{name}: tag_head_match=no (detached HEAD must equal resolved tag commit)")
    for key in ("package_clone_clean_status", "grok_build_clean_tree", "fresh_clones"):
        value = fields.get(key, "")
        if value and not is_yes_no(value):
            fail(errors, f"{name}: {key} must be yes|no")
    for key in ("weaver_forge_url", "grok_build_url"):
        value = fields.get(key, "")
        if value and not value.startswith("http"):
            fail(errors, f"{name}: {key} must be an http(s) URL")


def check_source_identity(fields: dict[str, str], errors: list[str]) -> None:
    name = "SOURCE_IDENTITY.txt"
    require_exact(name, fields, "grok_build_commit_expected", EXPECTED_GROK_COMMIT, errors)
    require_exact(name, fields, "cargo_lock_sha256_expected", EXPECTED_CARGO_LOCK_SHA256, errors)
    observed_commit = fields.get("grok_build_commit_observed", "")
    if observed_commit and not is_hex_commit(observed_commit):
        fail(errors, f"{name}: grok_build_commit_observed must be a 40-char lowercase hex commit")
    observed_lock = fields.get("cargo_lock_sha256_observed", "")
    if observed_lock and not is_sha256(observed_lock):
        fail(errors, f"{name}: cargo_lock_sha256_observed must be a 64-char lowercase hex sha256")


def check_image_identity(fields: dict[str, str], errors: list[str]) -> None:
    name = "IMAGE_IDENTITY.txt"
    requested_digest = strip_digest_prefix(fields.get("requested_digest", ""))
    if requested_digest != EXPECTED_IMAGE_DIGEST:
        fail(errors, f"{name}: requested_digest must resolve to the expected pinned image digest")
    for key in ("digest_match_expected", "platform_match_expected"):
        value = fields.get(key, "")
        if value and not is_yes_no(value):
            fail(errors, f"{name}: {key} must be yes|no")
    pull_exit = fields.get("docker_pull_exit_code", "")
    if pull_exit and not is_numeric(pull_exit):
        fail(errors, f"{name}: docker_pull_exit_code must be numeric")


def check_environment(fields: dict[str, str], errors: list[str]) -> None:
    name = "ENVIRONMENT.txt"
    if not is_safe_token(fields.get("witness_id", "")):
        fail(errors, f"{name}: witness_id must be a non-empty token with no path separators, whitespace, or '..'")
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)


def check_bootstrap(fields: dict[str, str], errors: list[str]) -> None:
    name = "BOOTSTRAP.txt"
    require_exact(name, fields, "dotslash_version", EXPECTED_DOTSLASH_VERSION, errors)
    require_exact(name, fields, "product_executed", "NO", errors)
    for key in ("protoc_descriptor_src_sha256", "protoc_descriptor_lf_sha256"):
        value = fields.get(key, "")
        if value and not is_sha256(value):
            fail(errors, f"{name}: {key} must be a 64-char lowercase hex sha256")
    writable = fields.get("protoc_descriptor_writable", "")
    if writable and not is_yes_no(writable):
        fail(errors, f"{name}: protoc_descriptor_writable must be yes|no")
    exit_code = fields.get("protoc_version_exit_code", "")
    if exit_code and not is_numeric(exit_code):
        fail(errors, f"{name}: protoc_version_exit_code must be numeric")


def check_clean_target_proof(fields: dict[str, str], errors: list[str]) -> None:
    name = "CLEAN_TARGET_PROOF.txt"
    require_exact(name, fields, "required_entry_count", "0", errors)
    for key in ("observed_entry_count_host", "observed_entry_count_container"):
        value = fields.get(key, "")
        if value and not is_numeric(value):
            fail(errors, f"{name}: {key} must be numeric")
    proof_failed = fields.get("proof_failed", "")
    if proof_failed and not is_yes_no(proof_failed):
        fail(errors, f"{name}: proof_failed must be yes|no")


def check_build_command(fields: dict[str, str], errors: list[str]) -> None:
    name = "BUILD_COMMAND.txt"
    require_exact(name, fields, "exact_build_command", EXACT_BUILD_CMD, errors)
    require_exact(name, fields, "cargo_incremental", "0", errors)
    require_exact(name, fields, "product_executed", "NO", errors)


def check_build_environment(fields: dict[str, str], errors: list[str]) -> None:
    name = "BUILD_ENVIRONMENT.txt"
    require_exact(name, fields, "CARGO_INCREMENTAL", "0", errors)
    rust_image = fields.get("rust_image", "")
    if EXPECTED_IMAGE_DIGEST not in rust_image:
        fail(errors, f"{name}: rust_image must reference the expected pinned image digest")


def determine_outcome(evidence_dir: Path, errors: list[str]) -> str | None:
    """Detect outcome from BUILD_EXIT_CODE.txt 'outcome=' (preferred), or infer
    conservatively from cargo_started/build_status when the explicit field is
    absent. Returns None (with an error appended) if it cannot be determined."""
    path = evidence_dir / "BUILD_EXIT_CODE.txt"
    if not path.is_file():
        fail(errors, "Cannot determine outcome: BUILD_EXIT_CODE.txt is missing")
        return None
    fields = parse_kv(read_text(path))
    outcome = fields.get("outcome")
    if outcome in OUTCOME_VALUES:
        return outcome
    # Conservative inference fallback when the explicit field is absent/invalid.
    cargo_started = fields.get("cargo_started")
    build_status = fields.get("build_status")
    if cargo_started == "NO" and build_status == "BUILD_NOT_STARTED":
        return "BUILD_NOT_STARTED"
    if cargo_started == "NO" and build_status == "INFRASTRUCTURE_FAILURE":
        return "INFRASTRUCTURE_FAILURE"
    if cargo_started == "YES" and build_status == "FAILED":
        return "CARGO_FAILED"
    fail(
        errors,
        "BUILD_EXIT_CODE.txt: 'outcome' field missing or invalid and could not be "
        "conservatively inferred from cargo_started/build_status",
    )
    return None


def check_build_exit_code(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "BUILD_EXIT_CODE.txt"
    if outcome is None:
        return
    rule = OUTCOME_RULES[outcome]
    if fields.get("cargo_started") != rule["cargo_started"]:
        fail(errors, f"{name}: cargo_started must be {rule['cargo_started']} for outcome {outcome}")
    if fields.get("build_status") != rule["build_status"]:
        fail(errors, f"{name}: build_status must be {rule['build_status']} for outcome {outcome}")
    expected_exit = rule["cargo_exit_code"]
    actual_exit = fields.get("cargo_exit_code", "")
    if expected_exit == "0":
        if actual_exit != "0":
            fail(errors, f"{name}: cargo_exit_code must be '0' for outcome {outcome}")
    elif expected_exit == "N/A":
        if actual_exit.upper() != "N/A":
            fail(errors, f"{name}: cargo_exit_code must be 'N/A' for outcome {outcome} (cargo did not start)")
    else:
        if not is_numeric(actual_exit) or actual_exit == "0":
            fail(errors, f"{name}: cargo_exit_code must be a nonzero numeric value for outcome CARGO_FAILED")


def check_docker_exit_code(text: str, fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "DOCKER_EXIT_CODE.txt"
    if not fields and re.fullmatch(r"\s*\d+\s*", text):
        fail(errors, f"{name}: bare unlabelled numeric-only file is not permitted; use labeled key=value fields")
        return
    exit_code = fields.get("docker_exit_code", "")
    if exit_code and not is_numeric(exit_code):
        fail(errors, f"{name}: docker_exit_code must be numeric")
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)
    file_outcome = fields.get("outcome")
    if file_outcome not in OUTCOME_VALUES:
        fail(errors, f"{name}: outcome must be one of {sorted(OUTCOME_VALUES)}")
    elif outcome is not None and file_outcome != outcome:
        fail(errors, f"{name}: outcome ({file_outcome}) does not match BUILD_EXIT_CODE.txt outcome ({outcome})")


def check_build_timing(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "BUILD_TIMING.txt"
    file_outcome = fields.get("outcome")
    if file_outcome not in OUTCOME_VALUES:
        fail(errors, f"{name}: outcome must be one of {sorted(OUTCOME_VALUES)}")
    elif outcome is not None and file_outcome != outcome:
        fail(errors, f"{name}: outcome ({file_outcome}) does not match BUILD_EXIT_CODE.txt outcome ({outcome})")
    if outcome in OUTCOMES_WITH_CARGO_TIMING:
        for key in ("cargo_started_utc", "cargo_finished_utc"):
            if not fields.get(key):
                fail(errors, f"{name}: {key} is required when outcome is {outcome}")


def check_artifact_identity(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "ARTIFACT_IDENTITY.txt"
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)
    if outcome is None:
        return
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        expected_applicable, expected_present = "yes", "yes"
    elif outcome == "CARGO_SUCCEEDED_ARTIFACT_MISSING":
        expected_applicable, expected_present = "yes", "no"
    else:
        expected_applicable, expected_present = "no", "no"
    if fields.get("applicable") != expected_applicable:
        fail(errors, f"{name}: applicable must be {expected_applicable} for outcome {outcome}")
    if fields.get("artifact_present") != expected_present:
        fail(errors, f"{name}: artifact_present must be {expected_present} for outcome {outcome}")
    if fields.get("artifact_present") == "yes":
        for key in ("artifact_sha256", "artifact_size_bytes", "artifact_filename", "artifact_path"):
            if not fields.get(key):
                fail(errors, f"{name}: {key} is required when artifact_present=yes")
        sha = fields.get("artifact_sha256", "")
        if sha and not is_sha256(sha):
            fail(errors, f"{name}: artifact_sha256 must be a 64-char lowercase hex sha256")
        size = fields.get("artifact_size_bytes", "")
        if size and not is_numeric(size):
            fail(errors, f"{name}: artifact_size_bytes must be numeric")
    elif not fields.get("reason"):
        fail(errors, f"{name}: reason is required when artifact_present=no")


def check_static_artifact_inspection(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "STATIC_ARTIFACT_INSPECTION.txt"
    if outcome is None:
        return
    expected = "yes" if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" else "no"
    if fields.get("inspection_applicable") != expected:
        fail(errors, f"{name}: inspection_applicable must be {expected} for outcome {outcome}")
    if fields.get("artifact_present") != expected:
        fail(errors, f"{name}: artifact_present must be {expected} for outcome {outcome}")
    if expected == "yes":
        for key in (
            "file_exit_code",
            "readelf_h_exit_code",
            "readelf_n_exit_code",
            "readelf_d_exit_code",
            "objdump_f_exit_code",
        ):
            value = fields.get(key, "")
            if not value:
                fail(errors, f"{name}: {key} is required when inspection_applicable=yes")
            elif not is_numeric(value):
                fail(errors, f"{name}: {key} must be numeric")
    elif not fields.get("reason"):
        fail(errors, f"{name}: reason is required when inspection_applicable=no and artifact_present=no")


def check_post_build_integrity(fields: dict[str, str], errors: list[str]) -> None:
    name = "POST_BUILD_INTEGRITY.txt"
    for key in ("source_head_before", "source_head_after"):
        value = fields.get(key, "")
        if value and not is_hex_commit(value):
            fail(errors, f"{name}: {key} must be a 40-char lowercase hex commit")
    for key in ("cargo_lock_sha256_before", "cargo_lock_sha256_after"):
        value = fields.get(key, "")
        if value and not is_sha256(value):
            fail(errors, f"{name}: {key} must be a 64-char lowercase hex sha256")
    for key in (
        "source_clean_before",
        "source_clean_after",
        "source_or_lock_changed",
        "artifact_exists",
        "evidence_inventory_complete",
    ):
        value = fields.get(key, "")
        if value and not is_yes_no(value):
            fail(errors, f"{name}: {key} must be yes|no")


def check_witness_statement(fields: dict[str, str], errors: list[str]) -> None:
    name = "WITNESS_STATEMENT.md"
    if not fields.get("witness_identity_or_handle"):
        fail(errors, f"{name}: witness_identity_or_handle is required")
    require_exact(name, fields, "not_package_owner", "yes", errors)
    require_exact(name, fields, "not_owner_side_reproducer", "yes", errors)
    require_exact(name, fields, "witness_controlled_host", "yes", errors)
    ai_used = fields.get("ai_assistance_used", "")
    if ai_used not in ("yes", "no"):
        fail(errors, f"{name}: ai_assistance_used must be yes|no")
    elif ai_used == "yes" and not fields.get("ai_assistance_detail"):
        fail(errors, f"{name}: ai_assistance_detail is required when ai_assistance_used=yes")
    require_exact(name, fields, "human_review_completed", "yes", errors)
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)


def check_witness_verdict(text: str, fields: dict[str, str], errors: list[str]) -> None:
    name = "WITNESS_VERDICT.md"
    _, verdict_errors = parse_verdict_selection(text)
    errors.extend(verdict_errors)
    if not is_safe_token(fields.get("run_id", "")):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
    tag = fields.get("package_tag", "")
    if tag and not re.match(r"^grok-build-witness-v\d+\.\d+\.\d+(-rc\d+)?$", tag):
        fail(errors, f"{name}: package_tag does not match expected tag grammar: {tag!r}")
    weaver_commit = fields.get("weaver_forge_commit", "")
    if weaver_commit and not is_hex_commit(weaver_commit):
        fail(errors, f"{name}: weaver_forge_commit must be a 40-char lowercase hex commit")
    require_exact(name, fields, "grok_build_commit", EXPECTED_GROK_COMMIT, errors)
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)
    require_exact(name, fields, "maintainer_intake_verdict", "pending", errors)


def check_deviations(fields: dict[str, str], text: str, errors: list[str]) -> None:
    name = "DEVIATIONS.txt"
    state = fields.get("deviation_state", "")
    if state not in ("NONE", "PRESENT"):
        fail(errors, f"{name}: deviation_state must be NONE or PRESENT")
        return
    if state == "NONE":
        return
    indices: set[str] = set()
    for match in re.finditer(r"deviation_(\w+)_severity", text):
        indices.add(match.group(1))
    if not indices:
        fail(errors, f"{name}: deviation_state=PRESENT but no enumerated deviation_<n>_* entries were found")
        return
    for idx in sorted(indices):
        severity = fields.get(f"deviation_{idx}_severity", "")
        ceiling = fields.get(f"deviation_{idx}_verdict_ceiling", "")
        impact = fields.get(f"deviation_{idx}_canonical_identity_impact", "")
        description = fields.get(f"deviation_{idx}_description", "")
        if not description:
            fail(errors, f"{name}: deviation_{idx}_description is required")
        if severity not in DEVIATION_SEVERITY_VALUES:
            fail(errors, f"{name}: deviation_{idx}_severity must be one of {sorted(DEVIATION_SEVERITY_VALUES)}")
        if impact not in ("yes", "no"):
            fail(errors, f"{name}: deviation_{idx}_canonical_identity_impact must be yes|no")
        if ceiling not in VERDICT_VALUES:
            fail(errors, f"{name}: deviation_{idx}_verdict_ceiling must be one of {sorted(VERDICT_VALUES)}")
        elif severity in DEVIATION_SEVERITY_FORBIDS_PASS and ceiling == "PASS":
            fail(
                errors,
                f"{name}: deviation_{idx}_severity={severity} forbids a PASS verdict_ceiling",
            )
        elif severity == "PROHIBITED" and ceiling != "FAIL":
            fail(errors, f"{name}: deviation_{idx}_severity=PROHIBITED requires verdict_ceiling=FAIL")


def check_redactions(fields: dict[str, str], text: str, errors: list[str]) -> None:
    name = "REDACTIONS.md"
    state = fields.get("redaction_state", "")
    if state not in ("NONE", "PRESENT"):
        fail(errors, f"{name}: redaction_state must be NONE or PRESENT")
        return
    require_exact(name, fields, "semantic_integrity_declaration", "yes", errors)
    if state == "NONE":
        return
    indices: set[str] = set()
    for match in re.finditer(r"redaction_(\w+)_reason", text):
        indices.add(match.group(1))
    if not indices:
        fail(errors, f"{name}: redaction_state=PRESENT but no enumerated redaction_<n>_* entries were found")
        return
    for idx in sorted(indices):
        file_field = fields.get(f"redaction_{idx}_file", "")
        target_field = fields.get(f"redaction_{idx}_field", "")
        reason = fields.get(f"redaction_{idx}_reason", "")
        marker = fields.get(f"redaction_{idx}_replacement_marker", "")
        if not file_field:
            fail(errors, f"{name}: redaction_{idx}_file is required")
        if not target_field:
            fail(errors, f"{name}: redaction_{idx}_field is required")
        if not reason:
            fail(errors, f"{name}: redaction_{idx}_reason is required")
        if not marker or "[REDACTED" not in marker.upper():
            fail(errors, f"{name}: redaction_{idx}_replacement_marker must be a visible '[REDACTED: ...]' marker")
        haystack = f"{target_field} {reason}".lower()
        for keyword in PROHIBITED_REDACTION_KEYWORDS:
            if keyword in haystack:
                fail(
                    errors,
                    f"{name}: redaction_{idx} appears to redact a prohibited category "
                    f"(matched {keyword!r}); commits, digests, exact commands, exit codes, "
                    "artifact SHA-256/size, and independence statements must never be redacted",
                )
                break


# ---------------------------------------------------------------------------
# Verdict line parsing (exact match; no case-folding)
# ---------------------------------------------------------------------------


def parse_verdict_selection(text: str) -> tuple[list[str], list[str]]:
    """Return (matches, errors) for the 'Witness proposed verdict:' line.

    Matching is exact and case-sensitive: only uppercase PASS/PARTIAL/FAIL/
    INDETERMINATE are accepted. Explanatory uses of those words elsewhere in
    the document are ignored because the regex requires the full line to
    begin with the literal prefix.
    """
    errors: list[str] = []
    matches = VERDICT_LINE_RE.findall(text)
    if not matches:
        errors.append(
            "Missing 'Witness proposed verdict:' line (must be exact uppercase "
            "PASS|PARTIAL|FAIL|INDETERMINATE)"
        )
        return [], errors
    if len(matches) > 1:
        errors.append("Duplicate 'Witness proposed verdict:' lines")
        return matches, errors
    value = matches[0]
    if value not in VERDICT_VALUES:
        errors.append(
            f"Invalid witness proposed verdict value (exact uppercase required, "
            f"lowercase/mixed-case rejected): {value!r}"
        )
    return [value], errors


# ---------------------------------------------------------------------------
# Manifest grammar and validation
# ---------------------------------------------------------------------------


def parse_manifest_line(line: str, line_no: int) -> tuple[str | None, str | None, str | None]:
    """Return (digest, relpath, error). Exactly one of (digest, relpath) or
    error is populated."""
    if "\\" in line:
        return None, None, f"{MANIFEST_NAME}:{line_no}: backslashes not permitted"
    m = MANIFEST_LINE_RE.match(line)
    if not m:
        return (
            None,
            None,
            f"{MANIFEST_NAME}:{line_no}: malformed line "
            "(expected '<64 lowercase hex><two spaces>./<safe-relative-path>')",
        )
    digest, raw_path = m.group(1), m.group(2)
    if digest != digest.lower():
        return None, None, f"{MANIFEST_NAME}:{line_no}: digest must be lowercase hex"
    if not SHA256_RE.match(digest):
        return None, None, f"{MANIFEST_NAME}:{line_no}: hash not 64-char lowercase hex"
    if not raw_path.startswith("./"):
        return None, None, f"{MANIFEST_NAME}:{line_no}: path must be relative and start with './'"
    rel = raw_path[2:]
    if not rel or any(c.isspace() for c in rel):
        return None, None, f"{MANIFEST_NAME}:{line_no}: extra tokens or whitespace in path"
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        return None, None, f"{MANIFEST_NAME}:{line_no}: absolute path not permitted"
    segments = rel.split("/")
    if any(seg in ("", ".", "..") for seg in segments):
        return None, None, f"{MANIFEST_NAME}:{line_no}: parent traversal or empty path segment not permitted"
    if not FILENAME_RE.match(rel):
        return None, None, f"{MANIFEST_NAME}:{line_no}: unsafe filename characters in {rel!r}"
    if rel == MANIFEST_NAME:
        return None, None, f"{MANIFEST_NAME}:{line_no}: manifest must not list itself"
    return digest, rel, None


def check_no_symlinks(evidence_dir: Path, errors: list[str]) -> None:
    """Reject any symlink anywhere under the evidence directory. Symlink
    support is not implemented (reject-by-default policy; see VALIDATOR.md)."""
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_symlink():
            rel = path.relative_to(evidence_dir).as_posix()
            fail(errors, f"Symlinks are not permitted in the evidence directory: {rel}")


def validate_manifest(evidence_dir: Path, errors: list[str]) -> None:
    manifest_path = evidence_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return

    listed: dict[str, str] = {}
    for line_no, raw_line in enumerate(read_text(manifest_path).splitlines(), start=1):
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        digest, rel, error = parse_manifest_line(line, line_no)
        if error is not None:
            fail(errors, error)
            continue
        if rel in listed:
            fail(errors, f"{MANIFEST_NAME}: duplicate entry for {rel}")
            continue
        listed[rel] = digest  # type: ignore[assignment]

    for req in REQUIRED_FILES:
        if req == MANIFEST_NAME:
            continue
        if req not in listed:
            fail(errors, f"{MANIFEST_NAME}: missing mandatory entry for {req}")

    for rel, expected in listed.items():
        target = evidence_dir / rel
        if target.is_symlink() or not target.is_file():
            fail(errors, f"{MANIFEST_NAME}: listed file missing on disk: {rel}")
            continue
        actual = sha256_file(target)
        if actual != expected:
            fail(errors, f"{MANIFEST_NAME}: hash mismatch for {rel}")

    for path in evidence_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        if rel == MANIFEST_NAME or rel in MANIFEST_OPTIONAL_EVIDENCE:
            continue
        if rel not in listed:
            fail(errors, f"Unlisted regular evidence file (policy: structural FAIL): {rel}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def validate_dir(evidence_dir: Path) -> list[str]:
    errors: list[str] = []
    if not evidence_dir.is_dir():
        return [f"Not a directory: {evidence_dir}"]

    for name in REQUIRED_FILES:
        p = evidence_dir / name
        if not p.is_file():
            fail(errors, f"Missing required file: {name}")
        elif p.stat().st_size == 0 and name not in RAW_STREAM_FILES:
            fail(errors, f"Empty required file: {name}")

    check_no_symlinks(evidence_dir, errors)

    for path in evidence_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        text = read_text(path)
        for token in FORBIDDEN_PLACEHOLDERS:
            if token in text:
                fail(errors, f"Placeholder {token!r} in {path.name}")

    file_texts: dict[str, str] = {}
    file_fields: dict[str, dict[str, str]] = {}
    for name in REQUIRED_FILES:
        p = evidence_dir / name
        if p.is_file() and not p.is_symlink():
            text = read_text(p)
            file_texts[name] = text
            if name not in RAW_STREAM_FILES and name != MANIFEST_NAME:
                file_fields[name] = parse_kv(text)

    for name in SCHEMA_VERSIONED_FILES:
        if name in file_fields:
            check_schema_version(name, file_fields[name], errors)
            require_fields(name, file_fields[name], FILE_REQUIRED_FIELDS.get(name, ()), errors)

    if "WEAVER_FORGE_PACKAGE_IDENTITY.txt" in file_fields:
        check_weaver_forge_package_identity(file_fields["WEAVER_FORGE_PACKAGE_IDENTITY.txt"], errors)
    if "SOURCE_ACQUISITION.txt" in file_fields:
        check_source_acquisition(file_fields["SOURCE_ACQUISITION.txt"], errors)
    if "SOURCE_IDENTITY.txt" in file_fields:
        check_source_identity(file_fields["SOURCE_IDENTITY.txt"], errors)
    if "IMAGE_IDENTITY.txt" in file_fields:
        check_image_identity(file_fields["IMAGE_IDENTITY.txt"], errors)
    if "ENVIRONMENT.txt" in file_fields:
        check_environment(file_fields["ENVIRONMENT.txt"], errors)
    if "BOOTSTRAP.txt" in file_fields:
        check_bootstrap(file_fields["BOOTSTRAP.txt"], errors)
    if "CLEAN_TARGET_PROOF.txt" in file_fields:
        check_clean_target_proof(file_fields["CLEAN_TARGET_PROOF.txt"], errors)
    if "BUILD_COMMAND.txt" in file_fields:
        check_build_command(file_fields["BUILD_COMMAND.txt"], errors)
    if "BUILD_ENVIRONMENT.txt" in file_fields:
        check_build_environment(file_fields["BUILD_ENVIRONMENT.txt"], errors)
    if "POST_BUILD_INTEGRITY.txt" in file_fields:
        check_post_build_integrity(file_fields["POST_BUILD_INTEGRITY.txt"], errors)
    if "WITNESS_STATEMENT.md" in file_fields:
        check_witness_statement(file_fields["WITNESS_STATEMENT.md"], errors)
    if "WITNESS_VERDICT.md" in file_fields:
        check_witness_verdict(file_texts["WITNESS_VERDICT.md"], file_fields["WITNESS_VERDICT.md"], errors)
    if "DEVIATIONS.txt" in file_fields:
        check_deviations(file_fields["DEVIATIONS.txt"], file_texts["DEVIATIONS.txt"], errors)
    if "REDACTIONS.md" in file_fields:
        check_redactions(file_fields["REDACTIONS.md"], file_texts["REDACTIONS.md"], errors)

    outcome: str | None = None
    if "BUILD_EXIT_CODE.txt" in file_fields:
        outcome = determine_outcome(evidence_dir, errors)
        check_build_exit_code(file_fields["BUILD_EXIT_CODE.txt"], errors, outcome)

    if "DOCKER_EXIT_CODE.txt" in file_fields:
        check_docker_exit_code(
            file_texts.get("DOCKER_EXIT_CODE.txt", ""), file_fields["DOCKER_EXIT_CODE.txt"], errors, outcome
        )
    if "BUILD_TIMING.txt" in file_fields:
        check_build_timing(file_fields["BUILD_TIMING.txt"], errors, outcome)
    if "ARTIFACT_IDENTITY.txt" in file_fields:
        check_artifact_identity(file_fields["ARTIFACT_IDENTITY.txt"], errors, outcome)
    if "STATIC_ARTIFACT_INSPECTION.txt" in file_fields:
        check_static_artifact_inspection(file_fields["STATIC_ARTIFACT_INSPECTION.txt"], errors, outcome)

    validate_manifest(evidence_dir, errors)

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Witness evidence structure (not truth).")
    parser.add_argument("evidence_dir", type=Path, help="Path to evidence directory")
    args = parser.parse_args(argv)

    errors = validate_dir(args.evidence_dir.resolve())
    if errors:
        print("STRUCTURAL VALIDATION: FAIL")
        for e in errors:
            print(f"  - {e}")
        print(
            "\nStructural FAIL does not prove the run occurred, was independent, or was truthful."
        )
        return 1

    print("STRUCTURAL VALIDATION: PASS")
    print(
        "Structural PASS does not prove execution, independence, or truthfulness."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
