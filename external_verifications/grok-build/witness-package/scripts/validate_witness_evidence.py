#!/usr/bin/env python3
"""
Structural validator for Independent Witness evidence directories (C2E-5 / 1.0.0-rc5 / evidence_schema_version=1).

Validates presence, format, per-file schema, and vocabulary — not truthfulness,
independence, or execution. A structural PASS never proves that Docker or
Cargo actually ran, that the Witness was independent, or that any recorded
value is true.

This script writes only to its own stdout/stderr. It never writes into the
evidence directory it is validating (see VALIDATOR.md "Output policy").

RC6-R3: active canonical schema authority is the committed rc6 JSON register
(rc6.2 / canonical_schema_register_rc6.json) loaded via schema_register_loader
(ACTIVE_REGISTER_VERSION). Active structured KV files use exact or
exact-with-named-optional key enforcement; unknown keys are rejected. Frozen
rc6.1, rc5 Phase-4 S2, and S1 registers remain explicitly loadable for
historical compatibility only and are not competing active authorities.
Historical fixtures without S2 identity markers remain accepted through the
explicit historical compatibility path for unshaped packages. S2-shaped
evidence is never silently downgraded to historical rules. Evidence content
cannot select schema-register authority. Explicit validator modes remain
--host-preliminary and --final-submission; the default CLI path is a
compatibility alias to final-submission.

Phase 4-S3 completeness/manifest rules remain enforced under the active rc6
register. Structural PASS is never Independent Witness PASS, READY, or package
readiness.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

import evidence_inventory as ei
import deviation_transition as dxt
import statement_binding as sb
import redaction_index as ridx
import submission_sidecars as sidecars
from schema_register_loader import (
    load_historical_rc61_register,
    load_historical_register,

    ACTIVE_REGISTER_VERSION,
    HISTORICAL_REGISTER_VERSIONS,
    HOST_RUN_METADATA_ENTRY_BEGIN,
    HOST_RUN_METADATA_ENTRY_END,
    HOST_RUN_METADATA_ENTRY_KEYS,
    CanonicalSchemaRegister,
    SchemaRegisterError,
    is_s2_host_run_metadata,
    is_s2_not_applicable_terminal,
    is_s2_shaped_final_deviations,
    is_s2_shaped_package_identity,
    is_s2_shaped_preliminary_deviations,
    load_canonical_register,
)

# ---------------------------------------------------------------------------
# Constants (pinned identities — checked structurally, not re-derived)
# ---------------------------------------------------------------------------

EVIDENCE_SCHEMA_VERSION = "1"

# Validator modes (Pi-adjudicated Phase 4-S1).
MODE_HOST_PRELIMINARY = "host-preliminary"
MODE_FINAL_SUBMISSION = "final-submission"
DEFAULT_MODE_COMPATIBILITY_ALIAS = MODE_FINAL_SUBMISSION

# Canonical schema register (single active machine-readable authority for rc6 path).
# RC6-R5: default load is rc6.4. Historical rc6.3/rc6.2/rc6.1/S2/S1 are not coequal authorities.
_SCHEMA_REGISTER: CanonicalSchemaRegister = load_canonical_register()
SCHEMA_REGISTER_VERSION = _SCHEMA_REGISTER.schema_register_version
if SCHEMA_REGISTER_VERSION != ACTIVE_REGISTER_VERSION:
    raise SchemaRegisterError(
        f"active validator authority must be {ACTIVE_REGISTER_VERSION!r}, "
        f"got {SCHEMA_REGISTER_VERSION!r}"
    )
# Frozen historical rc6.1 projection retained for explicit historical loads/tests.
_HISTORICAL_RC61_REGISTER: CanonicalSchemaRegister = load_historical_rc61_register()

EXPECTED_GROK_COMMIT = "98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
EXPECTED_IMAGE_DIGEST = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
EXPECTED_CARGO_LOCK_SHA256 = "1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421"
EXACT_BUILD_CMD = "cargo build -p xai-grok-pager-bin --locked"
# Package-version-aware expected-tag authority (Repository Owner G-3; Future Candidate 1).
# Source of authority: package_version from WEAVER_FORGE_PACKAGE_IDENTITY.txt.
# Tag mismatch never selects historical/active compatibility.
PACKAGE_TAG_ACTIVE_FC01 = "weaver-forge-fc-01"
# Active candidate: Weaver Forge Future Candidate 1; mapping WF-FC-01 -> weaver-forge-fc-01 (Repository Owner G-3).
PACKAGE_TAG_HISTORICAL_RC8 = "grok-build-witness-v1.0.0-rc8"
PACKAGE_TAG_ACTIVE_RC8 = PACKAGE_TAG_HISTORICAL_RC8  # historical alias
PACKAGE_TAG_HISTORICAL_RC7 = "grok-build-witness-v1.0.0-rc7"
PACKAGE_TAG_ACTIVE_RC5 = "grok-build-witness-v1.0.0-rc5"
PACKAGE_TAG_HISTORICAL_RC4 = "grok-build-witness-v1.0.0-rc4"
PACKAGE_TAG_EXPECTED = PACKAGE_TAG_ACTIVE_FC01  # active package default / docs alias
PACKAGE_VERSION_EXPECTED_TAG: dict[str, str] = {
    "1.0.0-rc4": PACKAGE_TAG_HISTORICAL_RC4,
    "WF-FC-01": PACKAGE_TAG_ACTIVE_FC01,
    "1.0.0-rc5": PACKAGE_TAG_ACTIVE_RC5,
    "1.0.0-rc5-phase4-s3-fixture": PACKAGE_TAG_ACTIVE_RC5,
    "1.0.0-rc6": "grok-build-witness-v1.0.0-rc6",
    "1.0.0-rc7": PACKAGE_TAG_HISTORICAL_RC7,
    "1.0.0-rc8": PACKAGE_TAG_HISTORICAL_RC8,
}
EXPECTED_DOTSLASH_VERSION = "0.5.7"


def expected_package_tag_for_version(package_version: str) -> str | None:
    """Resolve the sole expected package tag for a declared package_version.

    Returns None for absent/unknown/unsupported versions (callers must fail closed).
    Does not consult the requested tag — mismatch never selects compatibility.
    """
    if not package_version:
        return None
    return PACKAGE_VERSION_EXPECTED_TAG.get(package_version)

MANIFEST_NAME = "EVIDENCE_MANIFEST.sha256"
FINAL_BINDING_NAME = "WEAVER_FORGE_FINAL_BINDING.txt"
PACKAGE_IDENTITY_NAME = "WEAVER_FORGE_PACKAGE_IDENTITY.txt"

# Closed inventory of optional host-only auxiliary files. This set is
# EXHAUSTIVE: any other file present on disk (or declared in the manifest)
# that is not one of REQUIRED_FILES and not one of these closed-aux files is a
# structural failure, even if its hash matches what's on disk (see
# "Reject undeclared aux even if in manifest" in WITNESS_PACKAGE_MANIFEST.md).
# Phase 3F-A: HOST_OUTCOME_INGESTION.txt is accepted and structurally validated
# when present (not merely allow-listed).
# Phase 4-S1: closed-aux inventory is projected from the canonical register.
HOST_OUTCOME_INGESTION_NAME = "HOST_OUTCOME_INGESTION.txt"
CLOSED_AUX_EVIDENCE_FILES = _SCHEMA_REGISTER.closed_aux_evidence_files()
# Backward-compatible alias (manifest-optional == closed aux set).
MANIFEST_OPTIONAL_EVIDENCE = CLOSED_AUX_EVIDENCE_FILES

# Explicitly forbidden filenames. BOOTSTRAP_PROTOC_VERSION.txt must never be
# written under EVIDENCE_DIR (protoc version output belongs in BOOTSTRAP.txt's
# protoc_version_output/protoc_version_exit_code fields only; see
# container_narrow_build.sh header comment).
EXPLICITLY_FORBIDDEN_FILES = frozenset({"BOOTSTRAP_PROTOC_VERSION.txt"})

# Container-owned files that, on a pre-container / pre-cargo failure path, are
# legitimately left as a truthful `status=NOT_REACHED` placeholder (the host
# orchestrator initializes them before the container runs, and the container
# never overwrites them because it never got that far). For these files a
# NOT_REACHED placeholder is accepted WITHOUT the full field schema, but only
# when the overall outcome is itself a non-started / infrastructure outcome.
PLACEHOLDER_ELIGIBLE_FILES = frozenset(
    {"BOOTSTRAP.txt", "BUILD_COMMAND.txt", "BUILD_ENVIRONMENT.txt"}
)

# Sentinel values that stand in for "this measurement was never taken" on a
# failure path. They are accepted in place of a numeric/hex/sha value for the
# fields that would otherwise require one.
NOT_REACHED_SENTINELS = frozenset({"NOT_REACHED", "NOT_STARTED", "NOT_APPLICABLE"})

RAW_STREAM_FILES = frozenset(
    {
        "BUILD_STDOUT.txt",
        "BUILD_STDERR.txt",
        "CONTAINER_STDOUT.txt",
        "CONTAINER_STDERR.txt",
    }
)

# Compatibility: REQUIRED_FILES remains the final-submission required set
# (historical default-mode inventory). Mode-specific required sets come from
# the canonical register via required_files_for_mode().
REQUIRED_FILES = _SCHEMA_REGISTER.required_files(MODE_FINAL_SUBMISSION)

# Structured (key=value) evidence files that must declare evidence_schema_version.
# Raw stdout/stderr capture files and the manifest itself are exempt.
SCHEMA_VERSIONED_FILES = tuple(
    name for name in REQUIRED_FILES if name not in RAW_STREAM_FILES and name != MANIFEST_NAME
)


def required_files_for_mode(
    mode: str, register: CanonicalSchemaRegister | None = None
) -> tuple[str, ...]:
    """Return the mode-specific required-file set from the selected register."""
    reg = register if register is not None else _SCHEMA_REGISTER
    return reg.required_files(mode)


def accepted_supporting_files_for_mode(
    mode: str, register: CanonicalSchemaRegister | None = None
) -> frozenset[str]:
    """Files accepted but not required for the mode (do not elevate eligibility)."""
    reg = register if register is not None else _SCHEMA_REGISTER
    return reg.accepted_supporting_files(mode)


def resolve_validation_mode(*, host_preliminary: bool = False, mode: str | None = None) -> str:
    """Resolve validation mode.

    ``host_preliminary=True`` remains the Phase 3F compatibility kwarg mapping to
    host-preliminary. Explicit ``mode`` wins when provided.
    """
    if mode is not None:
        if mode not in (MODE_HOST_PRELIMINARY, MODE_FINAL_SUBMISSION):
            raise SchemaRegisterError(f"unknown validation mode: {mode!r}")
        if host_preliminary and mode != MODE_HOST_PRELIMINARY:
            raise SchemaRegisterError(
                "host_preliminary=True conflicts with mode=" + repr(mode)
            )
        return mode
    return MODE_HOST_PRELIMINARY if host_preliminary else DEFAULT_MODE_COMPATIBILITY_ALIAS

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
#   "0"             -> must equal exactly "0"
#   "NOT_APPLICABLE" -> must equal exactly "NOT_APPLICABLE" (container's literal
#                        sentinel; case-sensitive, no "N/A" alias)
#   None            -> must be numeric and non-zero (CARGO_FAILED)
OUTCOME_RULES = {
    "BUILD_NOT_STARTED": {
        "cargo_started": "NO",
        "build_status": "BUILD_NOT_STARTED",
        "cargo_exit_code": "NOT_APPLICABLE",
    },
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
    "INFRASTRUCTURE_FAILURE": {
        "cargo_started": "NO",
        "build_status": "INFRASTRUCTURE_FAILURE",
        "cargo_exit_code": "NOT_APPLICABLE",
    },
}

# Outcomes where cargo actually started (BUILD_TIMING.txt cargo_* fields become mandatory).
OUTCOMES_WITH_CARGO_TIMING = frozenset(
    {"CARGO_FAILED", "CARGO_SUCCEEDED_ARTIFACT_MISSING", "CARGO_SUCCEEDED_ARTIFACT_PRESENT"}
)

# Exact field set for host-owned HOST_OUTCOME_INGESTION.txt (Phase 3D/3E writer).
# Phase 4-S1: projected from the canonical register (compatibility accessor, not
# a second independent authority).
HOST_OUTCOME_INGESTION_FIELDS = _SCHEMA_REGISTER.compatibility_host_outcome_fields()
# Keys that the host writer may emit as empty when the container result is
# missing/invalid (never invent values). All other HOST_OUTCOME keys must be
# non-empty.
HOST_OUTCOME_EMPTY_OK_FIELDS = frozenset(
    {
        "container_outcome",
        "container_exit_code",
        "cargo_started",
        "cargo_exit_code",
        "artifact_present",
        "artifact_identity_complete",
        "static_inspection_complete",
        "container_run_id",
    }
)
HOST_OUTCOME_STATUS_VALUES = frozenset({"OK", "FAILED"})
HOST_OUTCOME_PRESENCE_VALUES = frozenset({"MISSING", "EMPTY", "PRESENT"})
HOST_OUTCOME_YES_NO = frozenset({"YES", "NO"})
HOST_OUTCOME_HOST_STATUS_VALUES = frozenset({"OK", "FAILED"})
HOST_OUTCOME_COMPLETENESS_VALUES = frozenset({"INCOMPLETE", "FAILED", "COMPLETE"})
HOST_OUTCOME_PRELIMINARY_VALUES = frozenset({"YES", "NO"})

# Automatable RC4B-017 host-preliminary structural subset (not full four-yes;
# evidence_inventory_complete=yes is deliberately not required).
HOST_PRELIMINARY_POST_BUILD_REQUIRED = (
    ("status", "OK"),
    ("post_build_integrity_ok", "yes"),
    ("source_head_unchanged", "yes"),
    ("source_clean_before", "yes"),
    ("source_clean_after", "yes"),
    ("cargo_lock_unchanged", "yes"),
    ("cargo_lock_post_matches_expected", "yes"),
    ("source_or_lock_changed", "no"),
)

VERDICT_VALUES = frozenset({"PASS", "PARTIAL", "FAIL", "INDETERMINATE"})
# Goodness rank used to enforce "reject verdict above ceiling": a verdict may
# never have a strictly higher rank than the machine-computed (or recorded)
# ceiling permits.
VERDICT_RANK = {"FAIL": 0, "INDETERMINATE": 1, "PARTIAL": 2, "PASS": 3}
VERDICT_LINE_RE = re.compile(r"^Witness proposed verdict:\s*(\S+)\s*$", re.MULTILINE)

# Enumerated maintainer intake lifecycle values (MAINTAINER_INTAKE_POLICY.md).
# `pending` is required at submission time (see check_witness_verdict), but
# the vocabulary as a whole must include every lifecycle value so that a
# validator re-run against a later-annotated (accepted/rejected/superseded/
# etc.) historical submission does not spuriously fail.
MAINTAINER_INTAKE_VALUES = frozenset(
    {"pending", "accepted", "rejected", "correction_requested", "disputed", "superseded"}
)

DEVIATION_SEVERITY_VALUES = frozenset(
    {"NONE", "NONMATERIAL_DISCLOSED", "MATERIAL_NONCANONICAL", "PROHIBITED"}
)
# Severities that forbid a PASS ceiling.
DEVIATION_SEVERITY_FORBIDS_PASS = frozenset({"MATERIAL_NONCANONICAL", "PROHIBITED"})

# Categories that must never be redacted anywhere in the evidence set. Kept as
# lowercase substrings matched against a redaction's declared field/reason
# text (see check_redactions). Extended for rc4 to explicitly cover the
# outcome/verdict/ceiling machinery that now drives verdict-ceiling enforcement.
PROHIBITED_REDACTION_KEYWORDS = (
    "commit",
    "digest",
    "sha256",
    "exit_code",
    "exit code",
    "independence",
    "artifact_size",
    "artifact_sha256",
    "outcome",
    "build_status",
    "failure_stage",
    "proposed verdict",
    "intake verdict",
    "canonical_run",
    "verdict_ceiling",
)

FORBIDDEN_PLACEHOLDERS = (
    "TODO",
    "FILL_ME",
    "<replace-me>",
    "PLACEHOLDER_UNTIL_RC3_TAGGED",
    "PLACEHOLDER_UNTIL_RC4_TAGGED",
)

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
NUMERIC_RE = re.compile(r"^\d+$")
SAFE_TOKEN_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
REDACTION_MARKER_RE = re.compile(r"\[REDACTED[^\]]*\]")

# Manifest filename grammar: relative path, POSIX separators, safe characters only.
FILENAME_RE = re.compile(r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$")
MANIFEST_LINE_RE = re.compile(r"^([0-9A-Za-z]{64})  (.+)$")
# Package-tag grammar: active Future Candidate tag (exact) or historical grok-build-witness-v* form.
HISTORICAL_PACKAGE_TAG_GRAMMAR_RE = re.compile(
    r"^grok-build-witness-v\d+\.\d+\.\d+(-rc\d+)?$"
)


def package_tag_matches_grammar(tag: str) -> bool:
    """Return True if tag is active FC tag or historical grok-build-witness-v grammar."""
    if not tag:
        return False
    if tag == PACKAGE_TAG_ACTIVE_FC01:
        return True
    return HISTORICAL_PACKAGE_TAG_GRAMMAR_RE.match(tag) is not None


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def parse_kv(text: str, source_name: str = "") -> tuple[dict[str, str], list[str]]:
    """Parse simple ``key=value`` lines. Blank lines, markdown headings ('#'),
    table rows ('|'), and lines without '=' are ignored.

    Duplicate keys are a structural defect, not a last-value-wins situation:
    the first occurrence is retained for downstream schema checks, but every
    repeat of a key — whether the repeated value is identical to or
    conflicts with the first — is reported as an error. A file must declare
    each key at most once.
    """
    result: dict[str, str] = {}
    errors: list[str] = []
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
        value = value.strip()
        if key in result:
            if result[key] == value:
                errors.append(
                    f"{source_name}: duplicate key '{key}' (repeated with the same value) is "
                    "not permitted; each key must be declared exactly once (no last-value-wins)"
                )
            else:
                errors.append(
                    f"{source_name}: duplicate key '{key}' with conflicting values "
                    f"({result[key]!r} vs {value!r}) is not permitted"
                )
            continue
        result[key] = value
    return result, errors


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


def require_exact_field_set(
    name: str, fields: dict[str, str], required: tuple[str, ...], errors: list[str]
) -> None:
    """Require exact key equality: no missing, unknown, or extra fields."""
    required_set = set(required)
    actual = set(fields)
    for key in sorted(required_set - actual):
        fail(errors, f"{name}: missing required field '{key}'")
    for key in sorted(actual - required_set):
        fail(errors, f"{name}: unknown/extra field '{key}'")
    for key in required:
        if key in fields and fields[key] == "":
            fail(errors, f"{name}: missing required field '{key}'")


def require_exact_field_set_with_optional(
    name: str,
    fields: dict[str, str],
    required: tuple[str, ...],
    optional: tuple[str, ...],
    errors: list[str],
) -> None:
    """Exact required presence; unknown keys outside required|optional rejected."""
    allowed = set(required) | set(optional)
    actual = set(fields)
    for key in sorted(set(required) - actual):
        fail(errors, f"{name}: missing required field '{key}'")
    for key in sorted(actual - allowed):
        fail(errors, f"{name}: unknown/extra field '{key}'")
    for key in required:
        if key in fields and fields[key] == "":
            fail(errors, f"{name}: missing required field '{key}'")


def require_exact_field_set_with_indexed(
    name: str,
    fields: dict[str, str],
    required: tuple[str, ...],
    indexed_key_re: re.Pattern[str],
    errors: list[str],
    *,
    allow_indexed: bool,
) -> None:
    """Exact required keys; optionally permit indexed keys; reject all other unknowns."""
    actual = set(fields)
    for key in sorted(set(required) - actual):
        fail(errors, f"{name}: missing required field '{key}'")
    for key in required:
        if key in fields and fields[key] == "":
            fail(errors, f"{name}: missing required field '{key}'")
    for key in sorted(actual - set(required)):
        if allow_indexed and indexed_key_re.match(key):
            continue
        fail(errors, f"{name}: unknown/extra field '{key}'")


def enforce_register_field_set(
    name: str,
    fields: dict[str, str],
    mode: str,
    errors: list[str],
    *,
    register: CanonicalSchemaRegister | None = None,
) -> None:
    """Apply register exact or exact-with-named-optionals policy."""
    reg = register if register is not None else _SCHEMA_REGISTER
    required = reg.required_field_names(name, mode)
    optional = reg.optional_field_names(name, mode)
    if optional:
        require_exact_field_set_with_optional(name, fields, required, optional, errors)
    else:
        require_exact_field_set(name, fields, required, errors)


def check_s2_legal_values(
    name: str,
    fields: dict[str, str],
    legal: dict[str, tuple[str, ...]],
    errors: list[str],
) -> None:
    for key, allowed in legal.items():
        if key in fields and fields[key] not in allowed:
            fail(
                errors,
                f"{name}: field '{key}' must be one of {list(allowed)} (found {fields[key]!r})",
            )


def check_s2_not_applicable_terminal(
    name: str, fields: dict[str, str], errors: list[str]
) -> None:
    """Enforce activated S2 early-failure NOT_APPLICABLE schema."""
    required = (
        "evidence_schema_version",
        "status",
        "applicability",
        "reason",
        "authoritative_outcome",
        "failure_stage",
        "product_executed",
        "ldd_used",
    )
    require_exact_field_set(name, fields, required, errors)
    check_s2_legal_values(
        name,
        fields,
        {
            "status": ("NOT_APPLICABLE",),
            "applicability": ("not_applicable",),
            "product_executed": ("NO",),
            "ldd_used": ("NO",),
            "authoritative_outcome": ("BUILD_NOT_STARTED", "INFRASTRUCTURE_FAILURE"),
        },
        errors,
    )
    if not fields.get("reason"):
        fail(errors, f"{name}: reason must be non-empty for NOT_APPLICABLE terminal")
    if not fields.get("failure_stage"):
        fail(errors, f"{name}: failure_stage must be non-empty for NOT_APPLICABLE terminal")


def check_host_run_metadata_s2(text: str, errors: list[str]) -> None:
    """Validate S2 append-entry grammar for HOST_RUN_METADATA.txt."""
    name = "HOST_RUN_METADATA.txt"
    if not is_s2_host_run_metadata(text):
        return
    begin = HOST_RUN_METADATA_ENTRY_BEGIN
    end = HOST_RUN_METADATA_ENTRY_END
    parts = text.split(begin)
    prefix = parts[0].strip()
    if prefix:
        fail(errors, f"{name}: S2-shaped append log must start with {begin}")
    if len(parts) < 2:
        fail(errors, f"{name}: S2-shaped append log has no entries")
        return
    for idx, chunk in enumerate(parts[1:], start=1):
        if end not in chunk:
            fail(errors, f"{name}: entry {idx} missing {end}")
            continue
        body, remainder = chunk.split(end, 1)
        if remainder.strip():
            for line in remainder.splitlines():
                if line.strip():
                    fail(
                        errors,
                        f"{name}: unexpected content between entries near entry {idx}",
                    )
                    break
        entry_fields: dict[str, str] = {}
        ordered_keys: list[str] = []
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" not in line:
                fail(errors, f"{name}: entry {idx} has non key=value line: {line!r}")
                continue
            key, value = line.split("=", 1)
            if key in entry_fields:
                fail(errors, f"{name}: entry {idx} duplicate key {key!r}")
            entry_fields[key] = value
            ordered_keys.append(key)
        if tuple(ordered_keys) != HOST_RUN_METADATA_ENTRY_KEYS:
            fail(
                errors,
                f"{name}: entry {idx} key order must be exactly "
                f"{list(HOST_RUN_METADATA_ENTRY_KEYS)} (found {ordered_keys})",
            )
        unknown = sorted(set(entry_fields) - set(HOST_RUN_METADATA_ENTRY_KEYS))
        if unknown:
            fail(errors, f"{name}: entry {idx} unknown key(s): {unknown}")
        for key in HOST_RUN_METADATA_ENTRY_KEYS:
            if key not in entry_fields or entry_fields[key] == "":
                fail(errors, f"{name}: entry {idx} missing required key '{key}'")
        if entry_fields.get("evidence_schema_version") != EVIDENCE_SCHEMA_VERSION:
            fail(
                errors,
                f"{name}: entry {idx} evidence_schema_version must be "
                f"{EVIDENCE_SCHEMA_VERSION!r}",
            )
        if not is_safe_token(entry_fields.get("run_id", "")):
            fail(errors, f"{name}: entry {idx} run_id must be a safe non-empty token")


def require_present(name: str, fields: dict[str, str], required: tuple[str, ...], errors: list[str]) -> None:
    """Like require_fields, but only checks that the key line exists (an
    explicit ``key=`` with an empty value is acceptable). Used for fields
    that are legitimately empty in a "not applicable" shape emitted by the
    container script (e.g. per-tool static-inspection fields), where the key
    must always be present but the value is only mandatory conditionally."""
    for key in required:
        if key not in fields:
            fail(errors, f"{name}: missing required key '{key}' (must always be present, even if empty)")


def is_not_reached_placeholder(fields: dict[str, str]) -> bool:
    """True when a container-owned file is still the host's pre-run
    ``status=NOT_REACHED`` placeholder (the container never overwrote it)."""
    return fields.get("status") == "NOT_REACHED"



def package_is_r3_shaped(
    file_fields: dict[str, dict[str, str]],
    evidence_dir: Path | None = None,
) -> bool:
    """Detect RC6-R3 provenance markers for diagnostics/tests only.

    Must never select schema-register authority. Default validation always uses
    active rc6.4; historical registers are reachable only via the explicit
    historical validation API.
    """
    pkg = file_fields.get(PACKAGE_IDENTITY_NAME) or {}
    if "weaver_forge_tag_object_id" in pkg:
        return True
    post = file_fields.get("POST_BUILD_INTEGRITY.txt") or {}
    if "authoritative_outcome" in post:
        return True
    host = file_fields.get(HOST_OUTCOME_INGESTION_NAME) or {}
    if "container_run_id" in host:
        return True
    build = file_fields.get("BUILD_EXIT_CODE.txt") or {}
    if "run_id" in build:
        return True
    if evidence_dir is not None and (evidence_dir / FINAL_BINDING_NAME).is_file():
        return True
    if FINAL_BINDING_NAME in file_fields:
        return True
    return False


def resolve_validation_register(
    schema_register_version: str | None,
) -> tuple[CanonicalSchemaRegister | None, str | None]:
    """Resolve the schema register for validation.

    Default (None) → active rc6.5 only.
    Explicit historical versions → historical loader only.
    Active version requested via historical API → fail closed.
    Unsupported → fail closed.
    """
    if schema_register_version is None:
        return _SCHEMA_REGISTER, None
    if schema_register_version == ACTIVE_REGISTER_VERSION:
        return None, (
            f"schema_register_version={schema_register_version!r} is the active authority; "
            "default validation uses active rc6.5 — do not request it through the "
            "historical validation API"
        )
    if schema_register_version not in HISTORICAL_REGISTER_VERSIONS:
        return None, (
            f"unsupported schema_register_version: {schema_register_version!r} "
            f"(accepted historical: {sorted(HISTORICAL_REGISTER_VERSIONS)})"
        )
    try:
        return load_historical_register(schema_register_version), None
    except SchemaRegisterError as exc:
        return None, str(exc)


def package_is_s2_shaped(
    file_fields: dict[str, dict[str, str]],
    file_texts: dict[str, str] | None = None,
) -> bool:
    """True when evidence carries explicit S2 identity markers.

    Detection is explicit and testable. Historical fixtures without S2 markers
    remain on the S1 compatibility path. Presence of S2 markers must never be
    silently downgraded to historical rules.
    """
    pkg = file_fields.get("WEAVER_FORGE_PACKAGE_IDENTITY.txt") or {}
    if is_s2_shaped_package_identity(pkg):
        return True
    dev = file_fields.get("DEVIATIONS.txt") or {}
    if is_s2_shaped_preliminary_deviations(dev) or is_s2_shaped_final_deviations(dev):
        return True
    texts = file_texts or {}
    host_meta = texts.get("HOST_RUN_METADATA.txt", "")
    if host_meta and is_s2_host_run_metadata(host_meta):
        return True
    for name in PLACEHOLDER_ELIGIBLE_FILES:
        fields = file_fields.get(name) or {}
        if is_s2_not_applicable_terminal(fields):
            return True
    return False


def placeholder_skip(
    name: str,
    fields: dict[str, str],
    outcome: str | None,
    *,
    s2_shaped_package: bool = False,
) -> bool:
    """Whether ``name`` may skip its full field schema / semantic checks
    because it is a legitimate historical NOT_REACHED placeholder on a
    non-started / infrastructure-failure path.

    For S2-shaped packages, NOT_REACHED is initialization-only and must not
    survive as a finalized terminal artifact.
    """
    if s2_shaped_package and is_not_reached_placeholder(fields):
        return False
    return (
        name in PLACEHOLDER_ELIGIBLE_FILES
        and is_not_reached_placeholder(fields)
        and outcome in (None, "BUILD_NOT_STARTED", "INFRASTRUCTURE_FAILURE")
    )


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
# COMPATIBILITY BEHAVIOR (Phase 4-S2): these tuples remain the validator's
# in-process required-field projection for historical / currently compatible
# schemas. They are not a second authority — load-time equality against the
# active register's historical-compatibility projection is required. Full S2
# fields are enforced when S2 identity markers are present on the evidence.

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
        "run_id",
        "grok_build_commit_expected",
        "grok_build_commit_observed",
        "grok_build_detached_head",
        "cargo_lock_sha256_expected",
        "cargo_lock_sha256_before",
    ),
    # Aligned with host orchestrator IMAGE_IDENTITY schema block (rc4 / C2E-5).
    "IMAGE_IDENTITY.txt": (
        "evidence_schema_version",
        "status",
        "failure_stage",
        "requested_image",
        "requested_digest",
        "pull_command",
        "pull_exit_code",
        "inspect_image_id_command",
        "inspect_image_id_exit_code",
        "image_id",
        "inspect_repo_digests_command",
        "inspect_repo_digests_exit_code",
        "repo_digests",
        "inspect_os_command",
        "inspect_os_exit_code",
        "observed_os",
        "inspect_architecture_command",
        "inspect_architecture_exit_code",
        "observed_architecture",
        "observed_platform",
        "image_id_available",
        "digest_match_expected",
        "platform_match_expected",
        "proceeded_to_inspect_or_run",
        "cached_image_fallback_used",
    ),
    "ENVIRONMENT.txt": (
        "evidence_schema_version",
        "status",
        "outcome",
        "witness_id",
        "host_os",
        "host_kernel",
        "host_arch",
        "host_cpu",
        "host_ram_gib",
        "host_free_disk_gb",
        "docker_client_version",
        "docker_server_version",
        "docker_context",
        "canonical_platform",
        "wsl2_indicator",
        "container_os_release",
        "container_uname",
        "rustc_version",
        "cargo_version",
        "ai_assistance_used",
        "ai_assistance_detail",
        "human_review_completed",
        "product_executed",
        "upstream_product_commands_not_run",
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
    # Exact keys from container_narrow_build.sh's `BEGIN_SCHEMA_BLOCK
    # CLEAN_TARGET` writer (flush_clean_target_proof).
    "CLEAN_TARGET_PROOF.txt": (
        "evidence_schema_version",
        "status",
        "outcome",
        "target_path_host",
        "proof_utc_host",
        "observed_entry_count_host",
        "target_path_container_prebootstrap",
        "proof_utc_container_prebootstrap",
        "observed_entry_count_container_prebootstrap",
        "target_path_container_precargo",
        "proof_utc_container_precargo",
        "observed_entry_count_container",
        "proof_failed",
        "failure_stage",
    ),
    "BUILD_COMMAND.txt": (
        "evidence_schema_version",
        "exact_build_command",
        "cargo_incremental",
        "working_directory",
        "product_executed",
    ),
    # Exact keys from container_narrow_build.sh's `BEGIN_SCHEMA_BLOCK
    # BUILD_ENVIRONMENT` writer (record_build_environment / init placeholder).
    "BUILD_ENVIRONMENT.txt": (
        "evidence_schema_version",
        "status",
        "outcome",
        "docker_platform",
        "network_mode",
        "rust_image",
        "workdir",
        "home",
        "cargo_home",
        "cargo_target_dir",
        "bootstrap_cargo_target_dir",
        "cargo_incremental",
        "dotslash_cache",
        "path",
        "grok_build_commit",
        "expected_cargo_lock_sha256",
        "canonical_build_command",
        "mount_src",
        "mount_work",
        "mount_evidence",
        "mount_container_script",
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
    # Exact keys from container_narrow_build.sh's `BEGIN_SCHEMA_BLOCK
    # BUILD_EXIT_CODE` writer (write_outcome_evidence); "status" added
    # alongside "outcome" (both are always emitted by the container).
    "BUILD_EXIT_CODE.txt": (
        "evidence_schema_version",
        "run_id",
        "status",
        "cargo_started",
        "outcome",
        "build_status",
        "cargo_exit_code",
        "failure_stage",
    ),
    # Exact keys from container_narrow_build.sh's `BEGIN_SCHEMA_BLOCK
    # BUILD_TIMING` writer (write_outcome_evidence).
    "BUILD_TIMING.txt": (
        "evidence_schema_version",
        "status",
        "outcome",
        "docker_started_utc",
        "docker_finished_utc",
        "docker_elapsed_seconds",
        "cargo_started_utc",
        "cargo_finished_utc",
        "cargo_elapsed_seconds",
        "cargo_started",
        "cargo_exit_code",
        "docker_exit_code",
        "failure_stage",
    ),
    "ARTIFACT_IDENTITY.txt": (
        "evidence_schema_version",
        "run_id",
        "outcome",
        "applicable",
        "artifact_present",
        "product_executed",
        "ldd_used",
    ),
    # Fields that must ALWAYS be non-empty. The per-tool command/output/
    # exit_code keys and artifact_path are deliberately NOT listed here:
    # container_narrow_build.sh legitimately writes them as truly empty
    # (`key=`) whenever applicable=no (or before inspection ran) — see
    # write_no_artifact_evidence / write_artifact_evidence_best_effort.
    # Their *presence* (even when empty) is enforced separately via
    # require_present(STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS) below,
    # and their conditional non-emptiness (only when applicable=yes) is
    # enforced by check_static_artifact_inspection.
    "STATIC_ARTIFACT_INSPECTION.txt": (
        "evidence_schema_version",
        "status",
        "outcome",
        "applicable",
        "artifact_present",
        "inspection_complete",
        "failure_stage",
        "reason",
    ),
    "POST_BUILD_INTEGRITY.txt": (
        "evidence_schema_version",
        "run_id",
        "status",
        "outcome",
        "authoritative_outcome",
        "source_head_before",
        "source_head_after",
        "source_head_unchanged",
        "source_clean_before",
        "source_clean_after",
        "cargo_lock_sha256_before",
        "cargo_lock_sha256_after",
        "cargo_lock_unchanged",
        "cargo_lock_post_matches_expected",
        "source_or_lock_changed",
        "artifact_path",
        "artifact_exists",
        "docker_exit_code",
        "failure_stage",
        "evidence_inventory_complete",
        "full_integrity_gate_all_four_yes",
        "full_integrity_gate_note",
        "post_build_integrity_ok",
    ),
    "WITNESS_STATEMENT.md": (
        "evidence_schema_version",
        "run_id",
        "package_identity_ref",
        "final_binding_ref",
        "authoritative_outcome",
        "artifact_sha256",
        "evidence_manifest_ref",
        "statement_identity_sha256",
        "deviations_sha256",
        "deviation_state",
        "redactions_index_sha256",
        "redaction_state",
        "final_machine_ceiling",
        "execution_date_utc",
        "execution_started_utc",
        "execution_finished_utc",
        "execution_timing_source_file",
        "execution_timing_source_start_field",
        "execution_timing_source_end_field",
        "witness_identity_or_handle",
        "not_package_owner",
        "not_owner_side_reproducer",
        "witness_controlled_host",
        "ai_assistance_used",
        "human_review_completed",
        "product_executed",
        "ldd_used",
        "upstream_product_commands_not_run",
    ),
    "WITNESS_VERDICT.md": (
        "evidence_schema_version",
        "run_id",
        "package_identity_ref",
        "final_binding_ref",
        "package_tag",
        "weaver_forge_commit",
        "grok_build_commit",
        "outcome",
        "verdict_ceiling",
        "product_executed",
        "ldd_used",
        "maintainer_intake_verdict",
        "witness_statement_sha256",
        "statement_identity_sha256",
        "deviations_sha256",
        "deviation_state",
        "redactions_index_sha256",
        "redaction_state",
        "final_machine_ceiling",
    ),
    "WEAVER_FORGE_FINAL_BINDING.txt": (
        "evidence_schema_version",
        "run_id",
        "package_version",
        "canonical_tag",
        "tag_object_id",
        "peeled_commit",
        "grok_build_source_commit",
        "authoritative_outcome",
        "artifact_sha256",
        "artifact_byte_size",
        "final_manifest_sha256",
        "package_identity_ref",
        "build_exit_code_ref",
        "host_outcome_ingestion_ref",
        "post_build_integrity_ref",
        "source_identity_ref",
        "artifact_identity_ref",
        "evidence_manifest_ref",
    ),
    "DEVIATIONS.txt": (
        "evidence_schema_version",
        "deviation_state",
    ),
    "REDACTIONS.md": (
        "evidence_schema_version",
        "redaction_state",
        "semantic_integrity_declaration",
        "redactions_index_ref",
    ),
    "REDACTIONS_INDEX.txt": (
        "evidence_schema_version",
        "run_id",
        "redaction_state",
        "redaction_count",
    ),
}

_REGISTER_COMPAT_FIELDS = _SCHEMA_REGISTER.compatibility_file_required_fields()
if _REGISTER_COMPAT_FIELDS != FILE_REQUIRED_FIELDS:
    raise SchemaRegisterError(
        "canonical schema register required-field projection disagrees with "
        "FILE_REQUIRED_FIELDS compatibility map; refusing to start with dual authority"
    )
if _SCHEMA_REGISTER.compatibility_host_outcome_fields() != HOST_OUTCOME_INGESTION_FIELDS:
    raise SchemaRegisterError(
        "canonical schema register HOST_OUTCOME field projection disagrees with "
        "HOST_OUTCOME_INGESTION_FIELDS compatibility map"
    )

# The per-tool fields that must always exist as keys in STATIC_ARTIFACT_INSPECTION.txt
# (present in every shape the container script writes), but whose values are only
# mandatory (non-empty, numeric for exit codes) when applicable=yes.
STATIC_TOOL_FIELDS = (
    "sha256sum_command",
    "sha256sum_output",
    "sha256sum_exit_code",
    "stat_command",
    "stat_output",
    "stat_exit_code",
    "file_command",
    "file_output",
    "file_exit_code",
    "readelf_h_command",
    "readelf_h_output",
    "readelf_h_exit_code",
    "readelf_n_command",
    "readelf_n_output",
    "readelf_n_exit_code",
    "readelf_d_command",
    "readelf_d_output",
    "readelf_d_exit_code",
    "objdump_f_command",
    "objdump_f_output",
    "objdump_f_exit_code",
)
STATIC_TOOL_EXIT_CODE_FIELDS = tuple(f for f in STATIC_TOOL_FIELDS if f.endswith("_exit_code"))
STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS = ("artifact_path",) + STATIC_TOOL_FIELDS


# ---------------------------------------------------------------------------
# Per-file semantic checks (beyond simple presence)
# ---------------------------------------------------------------------------


def check_weaver_forge_package_identity(
    fields: dict[str, str],
    errors: list[str],
    *,
    register: CanonicalSchemaRegister | None = None,
) -> None:
    name = "WEAVER_FORGE_PACKAGE_IDENTITY.txt"
    reg = register if register is not None else _SCHEMA_REGISTER
    if is_s2_shaped_package_identity(fields):
        # Exact field set always comes from the selected validation register.
        # Evidence shape cannot select a different schema authority.
        required = reg.required_field_names(name, MODE_HOST_PRELIMINARY)
        optional = reg.optional_field_names(name, MODE_HOST_PRELIMINARY)
        require_exact_field_set_with_optional(name, fields, required, optional, errors)
        check_s2_legal_values(
            name,
            fields,
            {
                "weaver_forge_tag_raw_object_type_required": ("tag",),
                "package_commit_authority": ("annotated_tag_resolution",),
            },
            errors,
        )
        observed = fields.get("weaver_forge_tag_raw_object_type_observed", "")
        if observed != "tag":
            fail(
                errors,
                f"{name}: weaver_forge_tag_raw_object_type_observed must be 'tag' "
                f"for accepted S2 annotated-tag identity (found {observed!r})",
            )
        peeled = fields.get("weaver_forge_tag_peeled_commit", "")
        resolved = fields.get("weaver_forge_commit_resolved", "")
        if peeled and not is_hex_commit(peeled):
            fail(errors, f"{name}: weaver_forge_tag_peeled_commit must be a 40-char lowercase hex commit")
        if peeled and resolved and peeled != resolved:
            fail(
                errors,
                f"{name}: weaver_forge_tag_peeled_commit must equal weaver_forge_commit_resolved",
            )
        tag_ref = fields.get("weaver_forge_tag_ref", "")
        requested = fields.get("weaver_forge_tag_requested", "")
        if tag_ref and requested and tag_ref != f"refs/tags/{requested}":
            fail(
                errors,
                f"{name}: weaver_forge_tag_ref must be refs/tags/<weaver_forge_tag_requested>",
            )
        # RC6-R3: successful R3-shaped identity requires a real annotated-tag
        # object id and rejects UNKNOWN sentinels on the required base tuple.
        # Pre-R3 S2 packages omit weaver_forge_tag_object_id and stay on the
        # rc6.1 projection path.
        status = fields.get("status", "")
        successful_identity = "status" not in fields or status == "OK"
        if successful_identity and "weaver_forge_tag_object_id" in fields:
            object_id = fields.get("weaver_forge_tag_object_id", "")
            if not is_hex_commit(object_id):
                fail(
                    errors,
                    f"{name}: weaver_forge_tag_object_id must be a 40-char lowercase hex "
                    f"tag object id for successful R3 identity (found {object_id!r})",
                )
            for key in (
                "run_id",
                "package_version",
                "weaver_forge_tag_requested",
                "weaver_forge_tag_object_id",
                "weaver_forge_tag_peeled_commit",
                "grok_build_source_commit_expected",
            ):
                value = fields.get(key, "")
                if value in ("", "UNKNOWN", "NOT_REACHED"):
                    fail(
                        errors,
                        f"{name}: {key} must not be empty/UNKNOWN/NOT_REACHED for "
                        "successful R3-shaped package identity",
                    )
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
    package_version = fields.get("package_version", "")
    expected_tag = expected_package_tag_for_version(package_version)
    if package_version and expected_tag is None:
        fail(
            errors,
            f"{name}: unsupported package_version={package_version!r} "
            f"(no expected tag mapping; fail closed)",
        )
    elif expected_tag is not None and tag and tag != expected_tag and fields.get("canonical_run") == "yes":
        fail(
            errors,
            f"{name}: canonical_run=yes requires weaver_forge_tag_requested={expected_tag} "
            f"for package_version={package_version!r}",
        )
    if tag and not package_tag_matches_grammar(tag):
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
    run_id = fields.get("run_id", "")
    if "run_id" in fields and not is_safe_token(run_id):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
    require_exact(name, fields, "grok_build_commit_expected", EXPECTED_GROK_COMMIT, errors)
    require_exact(name, fields, "cargo_lock_sha256_expected", EXPECTED_CARGO_LOCK_SHA256, errors)
    observed_commit = fields.get("grok_build_commit_observed", "")
    if observed_commit and not is_hex_commit(observed_commit):
        fail(errors, f"{name}: grok_build_commit_observed must be a 40-char lowercase hex commit")
    expected_commit = fields.get("grok_build_commit_expected", "")
    # RC6-R3: fail closed when both expected/observed are present and neither is
    # NOT_REACHED — they must match for final active packages.
    if (
        expected_commit
        and observed_commit
        and expected_commit != "NOT_REACHED"
        and observed_commit != "NOT_REACHED"
        and expected_commit != observed_commit
    ):
        fail(
            errors,
            f"{name}: grok_build_commit_expected must equal grok_build_commit_observed "
            f"(found expected={expected_commit!r} observed={observed_commit!r})",
        )
    observed_lock = fields.get("cargo_lock_sha256_before", "")
    if observed_lock and observed_lock not in ("NOT_REACHED",) and not is_sha256(observed_lock):
        fail(errors, f"{name}: cargo_lock_sha256_before must be a 64-char lowercase hex sha256")
    detached = fields.get("grok_build_detached_head", "")
    if detached and detached not in ("yes", "no"):
        fail(errors, f"{name}: grok_build_detached_head must be yes|no")


def check_image_identity(fields: dict[str, str], errors: list[str]) -> None:
    name = "IMAGE_IDENTITY.txt"
    status = fields.get("status", "")
    if status not in ("OK", "FAILED", "NOT_REACHED"):
        fail(errors, f"{name}: status must be OK|FAILED|NOT_REACHED")
    requested_digest = strip_digest_prefix(fields.get("requested_digest", ""))
    if requested_digest and requested_digest not in ("NONE_PARSED", "NOT_REACHED") and requested_digest != EXPECTED_IMAGE_DIGEST:
        fail(errors, f"{name}: requested_digest must resolve to the expected pinned image digest")
    pull_exit = fields.get("pull_exit_code", "")
    if pull_exit and pull_exit not in ("NOT_REACHED",) and not is_numeric(pull_exit):
        fail(errors, f"{name}: pull_exit_code must be numeric")
    cached_fallback = fields.get("cached_image_fallback_used", "")
    if cached_fallback and cached_fallback != "NO":
        fail(
            errors,
            f"{name}: cached_image_fallback_used must be exactly 'NO' — falling back to a "
            "cached/local image instead of the pinned digest is never permitted",
        )
    proceeded = fields.get("proceeded_to_inspect_or_run", "")
    if proceeded and proceeded not in ("YES", "NO"):
        fail(errors, f"{name}: proceeded_to_inspect_or_run must be YES|NO")
    if status == "OK":
        if proceeded != "YES":
            fail(errors, f"{name}: proceeded_to_inspect_or_run must be YES when status=OK")
        for key in ("image_id_available", "digest_match_expected", "platform_match_expected"):
            value = fields.get(key, "")
            if value and not is_yes_no(value):
                fail(errors, f"{name}: {key} must be yes|no")
        for key in (
            "inspect_image_id_exit_code",
            "inspect_repo_digests_exit_code",
            "inspect_os_exit_code",
            "inspect_architecture_exit_code",
        ):
            value = fields.get(key, "")
            if value and value != "NOT_APPLICABLE" and not is_numeric(value):
                fail(errors, f"{name}: {key} must be numeric (or NOT_APPLICABLE)")
        if (
            fields.get("digest_match_expected") != "yes"
            or fields.get("platform_match_expected") != "yes"
            or fields.get("image_id_available") != "yes"
        ):
            fail(
                errors,
                f"{name}: status=OK requires image_id_available=yes, digest_match_expected=yes, "
                "and platform_match_expected=yes (the host refuses to run the container otherwise)",
            )
    elif status == "FAILED":
        if proceeded and proceeded != "NO":
            fail(errors, f"{name}: proceeded_to_inspect_or_run must be NO when status=FAILED")
        failure_stage = fields.get("failure_stage", "")
        if not failure_stage or failure_stage in ("NOT_APPLICABLE", "NONE") and fields.get("pull_exit_code") not in ("0",):
            # failure_stage must be a concrete stage name when FAILED
            if not failure_stage or failure_stage == "NOT_APPLICABLE":
                fail(errors, f"{name}: failure_stage is required when status=FAILED")


def check_environment(fields: dict[str, str], errors: list[str]) -> None:
    name = "ENVIRONMENT.txt"
    if not is_safe_token(fields.get("witness_id", "")):
        fail(errors, f"{name}: witness_id must be a non-empty token with no path separators, whitespace, or '..'")
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)
    upstream = fields.get("upstream_product_commands_not_run", "")
    if upstream and upstream != "yes":
        fail(errors, f"{name}: upstream_product_commands_not_run must be yes")
    outcome = fields.get("outcome", "")
    if outcome and outcome not in OUTCOME_VALUES:
        fail(errors, f"{name}: outcome must be one of {sorted(OUTCOME_VALUES)}")


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
    status = fields.get("status", "")
    if status not in ("OK", "FAILED", "CHECKED", "NOT_REACHED"):
        fail(errors, f"{name}: status must be OK|FAILED|CHECKED|NOT_REACHED")
    proof_failed = fields.get("proof_failed", "")
    if proof_failed not in ("yes", "no"):
        fail(errors, f"{name}: proof_failed must be yes|no")
    for key in (
        "observed_entry_count_host",
        "observed_entry_count_container_prebootstrap",
        "observed_entry_count_container",
    ):
        value = fields.get(key, "")
        if value and value != "NOT_REACHED" and not is_numeric(value):
            fail(errors, f"{name}: {key} must be numeric (or NOT_REACHED)")
        if proof_failed == "no" and value not in ("", "NOT_REACHED") and value != "0":
            fail(errors, f"{name}: {key} must be '0' when proof_failed=no (found {value!r})")


def check_post_build_integrity(fields: dict[str, str], errors: list[str]) -> None:
    name = "POST_BUILD_INTEGRITY.txt"
    run_id = fields.get("run_id", "")
    if "run_id" in fields and not is_safe_token(run_id):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
    status = fields.get("status", "")
    if status == "NOT_APPLICABLE":
        fail(errors, f"{name}: status=NOT_APPLICABLE is prohibited as a final POST_BUILD status")
    elif status and status not in ("OK", "FAILED", "NOT_REACHED"):
        fail(errors, f"{name}: status must be OK|FAILED|NOT_REACHED")
    ok = fields.get("post_build_integrity_ok", "")
    if ok and not is_yes_no(ok):
        fail(errors, f"{name}: post_build_integrity_ok must be yes|no")
    # status=OK iff post_build_integrity_ok=yes. NOT_REACHED must not qualify as success.
    if status == "OK" and ok != "yes":
        fail(errors, f"{name}: status=OK requires post_build_integrity_ok=yes")
    if ok == "yes" and status not in ("OK",):
        fail(errors, f"{name}: post_build_integrity_ok=yes requires status=OK")
    if status == "NOT_REACHED" and ok == "yes":
        fail(errors, f"{name}: status=NOT_REACHED cannot qualify as finalized success")
    if status == "FAILED" and ok == "yes":
        fail(errors, f"{name}: status=FAILED contradicts post_build_integrity_ok=yes")
    for key in ("source_head_before", "source_head_after"):
        value = fields.get(key, "")
        if value and value not in ("NOT_REACHED",) and not is_hex_commit(value):
            fail(errors, f"{name}: {key} must be a 40-char lowercase hex commit")
    for key in ("cargo_lock_sha256_before", "cargo_lock_sha256_after"):
        value = fields.get(key, "")
        if value and value not in ("NOT_REACHED",) and not is_sha256(value):
            fail(errors, f"{name}: {key} must be a 64-char lowercase hex sha256")
    for key in (
        "source_head_unchanged",
        "source_clean_before",
        "source_clean_after",
        "cargo_lock_unchanged",
        "cargo_lock_post_matches_expected",
        "source_or_lock_changed",
        "evidence_inventory_complete",
        "full_integrity_gate_all_four_yes",
        "artifact_exists",
        "post_build_integrity_ok",
    ):
        value = fields.get(key, "")
        if value and not is_yes_no(value):
            fail(errors, f"{name}: {key} must be yes|no")
    # Blank porcelain must never appear in yes/no fields — already enforced by is_yes_no.
    outcome = fields.get("outcome", "")
    if outcome and outcome not in OUTCOME_VALUES:
        fail(errors, f"{name}: outcome must be one of {sorted(OUTCOME_VALUES)}")
    authoritative_outcome = fields.get("authoritative_outcome", "")
    if "authoritative_outcome" in fields:
        if authoritative_outcome not in OUTCOME_VALUES:
            fail(
                errors,
                f"{name}: authoritative_outcome must be one of {sorted(OUTCOME_VALUES)} "
                f"(found {authoritative_outcome!r})",
            )
        elif outcome and authoritative_outcome != outcome:
            fail(
                errors,
                f"{name}: authoritative_outcome={authoritative_outcome!r} must equal "
                f"outcome={outcome!r}",
            )
    note = fields.get("full_integrity_gate_note", "")
    if note is not None and "full_integrity_gate_note" in fields and note == "":
        fail(errors, f"{name}: full_integrity_gate_note must be non-empty when present")
    docker_exit = fields.get("docker_exit_code", "")
    if docker_exit and docker_exit not in ("NOT_REACHED", "NOT_STARTED", "NOT_APPLICABLE") and not is_numeric(
        docker_exit
    ):
        fail(errors, f"{name}: docker_exit_code must be numeric or a NOT_REACHED/NOT_STARTED sentinel")

    # Automatable RC4B-017 consistency (O18): when POST_BUILD claims status=OK,
    # the automatable integrity subset must hold. evidence_inventory_complete=yes
    # is deliberately not required (host-preliminary / Witness lifecycle later).
    if status == "OK":
        for key, expected in HOST_PRELIMINARY_POST_BUILD_REQUIRED:
            if key == "status":
                continue
            actual = fields.get(key, "")
            if actual != expected:
                fail(
                    errors,
                    f"{name}: status=OK requires {key}={expected} "
                    f"(automatable RC4B-017 subset; found {actual!r})",
                )


def check_build_command(fields: dict[str, str], errors: list[str]) -> None:
    name = "BUILD_COMMAND.txt"
    require_exact(name, fields, "exact_build_command", EXACT_BUILD_CMD, errors)
    require_exact(name, fields, "cargo_incremental", "0", errors)
    require_exact(name, fields, "product_executed", "NO", errors)


def check_build_environment(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "BUILD_ENVIRONMENT.txt"
    require_exact(name, fields, "cargo_incremental", "0", errors)
    rust_image = fields.get("rust_image", "")
    if EXPECTED_IMAGE_DIGEST not in rust_image:
        fail(errors, f"{name}: rust_image must reference the expected pinned image digest")
    grok_commit = fields.get("grok_build_commit", "")
    if grok_commit and grok_commit != EXPECTED_GROK_COMMIT:
        fail(errors, f"{name}: grok_build_commit must equal the expected pinned commit")
    lock_sha = fields.get("expected_cargo_lock_sha256", "")
    if lock_sha and lock_sha != EXPECTED_CARGO_LOCK_SHA256:
        fail(errors, f"{name}: expected_cargo_lock_sha256 must equal the expected pinned Cargo.lock SHA-256")
    build_cmd = fields.get("canonical_build_command", "")
    if build_cmd and build_cmd != EXACT_BUILD_CMD:
        fail(errors, f"{name}: canonical_build_command must equal {EXACT_BUILD_CMD!r}")
    status = fields.get("status", "")
    if status not in ("OK", "RECORDED", "NOT_REACHED"):
        fail(errors, f"{name}: status must be one of OK|RECORDED|NOT_REACHED")
    if status == "NOT_REACHED" and outcome not in (None, "BUILD_NOT_STARTED", "INFRASTRUCTURE_FAILURE"):
        fail(
            errors,
            f"{name}: status=NOT_REACHED is only permitted when outcome is BUILD_NOT_STARTED or "
            f"INFRASTRUCTURE_FAILURE (found outcome={outcome})",
        )


def determine_outcome(fields: dict[str, str] | None, errors: list[str]) -> str | None:
    """Require an explicit authoritative ``outcome=`` from BUILD_EXIT_CODE.txt.

    Phase 3F-A / RC4B-022: no inference from cargo_started, build_status, or any
    secondary field pair. Missing, empty, malformed, or unsupported values fail
    closed. The validator never creates or infers an outcome not explicitly
    present in authoritative evidence.
    """
    if fields is None:
        fail(errors, "Cannot determine outcome: BUILD_EXIT_CODE.txt is missing")
        return None
    if "outcome" not in fields:
        fail(
            errors,
            "BUILD_EXIT_CODE.txt: explicit 'outcome' field is required "
            "(outcome inference from cargo_started/build_status is prohibited)",
        )
        return None
    outcome = fields.get("outcome", "")
    if outcome == "":
        fail(
            errors,
            "BUILD_EXIT_CODE.txt: explicit 'outcome' field is empty "
            "(outcome inference is prohibited; fail closed)",
        )
        return None
    if outcome not in OUTCOME_VALUES:
        fail(
            errors,
            f"BUILD_EXIT_CODE.txt: 'outcome' value {outcome!r} is not an allowed "
            f"authoritative outcome {sorted(OUTCOME_VALUES)} "
            "(unsupported/malformed outcome fails closed; no inference)",
        )
        return None
    return outcome


def check_host_outcome_ingestion(
    fields: dict[str, str],
    errors: list[str],
    authoritative_outcome: str | None,
    *,
    register: CanonicalSchemaRegister | None = None,
) -> None:
    """Structurally validate host-owned HOST_OUTCOME_INGESTION.txt.

    Exact field-set equality; legal vocabularies; outcome agreement with
    authoritative BUILD_EXIT_CODE when the host recorded a valid container
    result. Never overwrites or repairs container evidence. Field set comes
    from the selected validation register (active by default).
    """
    name = HOST_OUTCOME_INGESTION_NAME
    reg = register if register is not None else _SCHEMA_REGISTER
    active_validation = reg.is_active_authority
    if active_validation:
        required_fields = HOST_OUTCOME_INGESTION_FIELDS
        empty_ok = HOST_OUTCOME_EMPTY_OK_FIELDS
    else:
        required_fields = reg.compatibility_host_outcome_fields()
        empty_ok = frozenset(
            {
                "container_outcome",
                "container_exit_code",
                "cargo_started",
                "cargo_exit_code",
                "artifact_present",
                "artifact_identity_complete",
                "static_inspection_complete",
                "run_id",
            }
        )
    required_set = set(required_fields)
    actual = set(fields)
    for key in sorted(required_set - actual):
        fail(errors, f"{name}: missing required field '{key}'")
    for key in sorted(actual - required_set):
        fail(errors, f"{name}: unknown/extra field '{key}'")
    for key in required_fields:
        if key not in fields:
            continue
        if fields[key] == "" and key not in empty_ok:
            fail(errors, f"{name}: missing required field '{key}'")

    schema = fields.get("schema_version", "")
    if schema and schema != "1":
        fail(errors, f"{name}: schema_version must be '1' (found {schema!r})")

    status = fields.get("status", "")
    if status and status not in HOST_OUTCOME_STATUS_VALUES:
        fail(errors, f"{name}: status must be one of {sorted(HOST_OUTCOME_STATUS_VALUES)}")

    presence = fields.get("container_result_presence", "")
    if presence and presence not in HOST_OUTCOME_PRESENCE_VALUES:
        fail(
            errors,
            f"{name}: container_result_presence must be one of "
            f"{sorted(HOST_OUTCOME_PRESENCE_VALUES)}",
        )

    valid = fields.get("container_result_valid", "")
    if valid and valid not in HOST_OUTCOME_YES_NO:
        fail(errors, f"{name}: container_result_valid must be YES|NO")

    for key in (
        "host_infrastructure_status",
        "host_source_integrity_status",
        "post_build_integrity_status",
    ):
        value = fields.get(key, "")
        if value and value not in HOST_OUTCOME_HOST_STATUS_VALUES:
            fail(
                errors,
                f"{name}: {key} must be one of {sorted(HOST_OUTCOME_HOST_STATUS_VALUES)}",
            )

    completeness = fields.get("evidence_completeness_status", "")
    if completeness and completeness not in HOST_OUTCOME_COMPLETENESS_VALUES:
        fail(
            errors,
            f"{name}: evidence_completeness_status must be one of "
            f"{sorted(HOST_OUTCOME_COMPLETENESS_VALUES)}",
        )

    preliminary = fields.get("preliminary_success_eligible", "")
    if preliminary and preliminary not in HOST_OUTCOME_PRELIMINARY_VALUES:
        fail(
            errors,
            f"{name}: preliminary_success_eligible must be one of "
            f"{sorted(HOST_OUTCOME_PRELIMINARY_VALUES)}",
        )
    # preliminary_success_eligible remains a recorded field; YES is legal
    # vocabulary but is never treated as final success eligibility by the
    # structural validator.

    owner = fields.get("record_owner", "")
    if owner and owner != "HOST":
        fail(errors, f"{name}: record_owner must be HOST")

    # Active rc6.2: Host run_id is mandatory. Historical registers retain their
    # own empty-ok projection for run_id when selected explicitly.
    run_id = fields.get("run_id", "")
    if active_validation and not is_safe_token(run_id):
        fail(
            errors,
            f"{name}: run_id must be a non-empty safe token when HOST_OUTCOME_INGESTION "
            "is present (empty-ok no longer applies to Host run_id)",
        )
    elif (not active_validation) and run_id and not is_safe_token(run_id):
        fail(
            errors,
            f"{name}: run_id must be a safe token when present",
        )

    container_outcome = fields.get("container_outcome", "")
    if valid == "YES":
        container_run_id = fields.get("container_run_id", "")
        if active_validation and not is_safe_token(container_run_id):
            fail(
                errors,
                f"{name}: container_run_id must be a non-empty safe token when "
                "container_result_valid=YES",
            )
        elif active_validation and container_run_id != run_id:
            fail(
                errors,
                f"{name}: container_run_id={container_run_id!r} must equal "
                f"run_id={run_id!r} when container_result_valid=YES",
            )
        if container_outcome not in OUTCOME_VALUES:
            fail(
                errors,
                f"{name}: container_outcome must be an allowed authoritative outcome "
                f"when container_result_valid=YES (found {container_outcome!r}; "
                "Docker-exit substitution is not permitted)",
            )
        elif (
            authoritative_outcome is not None
            and container_outcome != authoritative_outcome
        ):
            fail(
                errors,
                f"{name}: container_outcome={container_outcome!r} disagrees with "
                f"authoritative BUILD_EXIT_CODE.txt outcome={authoritative_outcome!r} "
                "(HOST_OUTCOME must not overwrite or repair container evidence)",
            )
    elif valid == "NO":
        if (
            container_outcome
            and container_outcome not in OUTCOME_VALUES
            and container_outcome != "INVALID"
        ):
            fail(
                errors,
                f"{name}: container_outcome must be empty, INVALID, or an allowed "
                f"outcome when container_result_valid=NO (found {container_outcome!r})",
            )

    # Contradictory host/container presence vs validity.
    if presence == "MISSING" and valid == "YES":
        fail(
            errors,
            f"{name}: container_result_presence=MISSING contradicts container_result_valid=YES",
        )
    if presence == "EMPTY" and valid == "YES":
        fail(
            errors,
            f"{name}: container_result_presence=EMPTY contradicts container_result_valid=YES",
        )
    if status == "OK" and valid == "NO":
        fail(
            errors,
            f"{name}: status=OK contradicts container_result_valid=NO "
            "(host must not claim OK ingestion over an invalid container result)",
        )


def check_host_preliminary_post_build_subset(
    post_build: dict[str, str],
    host_outcome: dict[str, str] | None,
    errors: list[str],
) -> None:
    """Enforce the automatable RC4B-017 subset for host-preliminary structural PASS.

    Does not require evidence_inventory_complete=yes. Does not grant final
    success eligibility. preliminary_success_eligible remaining NO is expected.
    """
    name = "POST_BUILD_INTEGRITY.txt"
    for key, expected in HOST_PRELIMINARY_POST_BUILD_REQUIRED:
        actual = post_build.get(key, "")
        if actual != expected:
            fail(
                errors,
                f"{name}: host-preliminary structural PASS requires {key}={expected} "
                f"(found {actual!r}); automatable RC4B-017 subset only — "
                "evidence_inventory_complete=yes is not required",
            )

    if host_outcome is None:
        fail(
            errors,
            f"{HOST_OUTCOME_INGESTION_NAME}: required for host-preliminary structural validation",
        )
        return

    for key, expected in (
        ("host_infrastructure_status", "OK"),
        ("host_source_integrity_status", "OK"),
        ("post_build_integrity_status", "OK"),
    ):
        actual = host_outcome.get(key, "")
        if actual != expected:
            fail(
                errors,
                f"{HOST_OUTCOME_INGESTION_NAME}: host-preliminary structural PASS requires "
                f"{key}={expected} (found {actual!r})",
            )

    preliminary = host_outcome.get("preliminary_success_eligible", "")
    if preliminary != "NO":
        fail(
            errors,
            f"{HOST_OUTCOME_INGESTION_NAME}: preliminary_success_eligible must remain NO "
            f"during host-preliminary structural validation (found {preliminary!r}; "
            "YES is never treated as final success eligibility)",
        )


def check_build_exit_code(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "BUILD_EXIT_CODE.txt"
    run_id = fields.get("run_id", "")
    if "run_id" in fields and not is_safe_token(run_id):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
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
    elif expected_exit == "NOT_APPLICABLE":
        if actual_exit != "NOT_APPLICABLE":
            fail(
                errors,
                f"{name}: cargo_exit_code must be exactly 'NOT_APPLICABLE' for outcome {outcome} "
                "(cargo did not start)",
            )
    else:
        if not is_numeric(actual_exit) or actual_exit == "0":
            fail(errors, f"{name}: cargo_exit_code must be a nonzero numeric value for outcome CARGO_FAILED")
    status = fields.get("status", "")
    if status not in ("OK", "FAILED"):
        fail(errors, f"{name}: status must be OK|FAILED")


def check_docker_exit_code(text: str, fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "DOCKER_EXIT_CODE.txt"
    if not fields and re.fullmatch(r"\s*\d+\s*", text):
        fail(errors, f"{name}: bare unlabelled numeric-only file is not permitted; use labeled key=value fields")
        return
    exit_code = fields.get("docker_exit_code", "")
    if exit_code and exit_code not in NOT_REACHED_SENTINELS and not is_numeric(exit_code):
        fail(errors, f"{name}: docker_exit_code must be numeric (or a NOT_STARTED/NOT_REACHED sentinel)")
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
    status = fields.get("status", "")
    if status not in ("OK", "FAILED"):
        fail(errors, f"{name}: status must be OK|FAILED")


def check_artifact_identity(fields: dict[str, str], errors: list[str], outcome: str | None) -> None:
    name = "ARTIFACT_IDENTITY.txt"
    run_id = fields.get("run_id", "")
    if "run_id" in fields and not is_safe_token(run_id):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
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
    # Always-present-key requirement (regardless of applicability): the
    # container script always emits every per-tool key, using an empty value
    # rather than omitting the key when the tool was never run.
    require_present(name, fields, STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS, errors)
    status = fields.get("status", "")
    if status not in ("OK", "FAILED", "NOT_APPLICABLE"):
        fail(errors, f"{name}: status must be one of OK|FAILED|NOT_APPLICABLE")
    if outcome is None:
        return
    expected = "yes" if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" else "no"
    if fields.get("applicable") != expected:
        fail(errors, f"{name}: applicable must be {expected} for outcome {outcome}")
    if fields.get("artifact_present") != expected:
        fail(errors, f"{name}: artifact_present must be {expected} for outcome {outcome}")
    file_outcome = fields.get("outcome")
    expected_file_outcome = "CARGO_SUCCEEDED_ARTIFACT_PRESENT" if expected == "yes" else "NOT_APPLICABLE"
    if file_outcome != expected_file_outcome:
        fail(
            errors,
            f"{name}: outcome must be {expected_file_outcome!r} when overall outcome is {outcome} "
            f"(found {file_outcome!r})",
        )
    complete = fields.get("inspection_complete", "")
    if complete not in ("yes", "no"):
        fail(errors, f"{name}: inspection_complete must be yes|no")
    if expected == "yes":
        for key in STATIC_TOOL_EXIT_CODE_FIELDS:
            value = fields.get(key, "")
            if not value:
                fail(errors, f"{name}: {key} is required (non-empty) when applicable=yes")
            elif not is_numeric(value):
                fail(errors, f"{name}: {key} must be numeric")
        if complete == "yes":
            all_zero = all(fields.get(k, "") == "0" for k in STATIC_TOOL_EXIT_CODE_FIELDS)
            if not all_zero:
                fail(errors, f"{name}: inspection_complete=yes requires every static-inspection exit code to be '0'")
        elif complete == "no" and status != "FAILED":
            fail(errors, f"{name}: status must be FAILED when applicable=yes and inspection_complete=no")
    else:
        if not fields.get("reason"):
            fail(errors, f"{name}: reason is required when applicable=no")
        if complete != "no":
            fail(errors, f"{name}: inspection_complete must be no when applicable=no")
        for key in STATIC_TOOL_EXIT_CODE_FIELDS:
            value = fields.get(key, "")
            if value and value not in NOT_REACHED_SENTINELS and not is_numeric(value):
                fail(errors, f"{name}: {key} must be numeric or a NOT_APPLICABLE/NOT_REACHED sentinel when present")


def check_witness_statement(
    fields: dict[str, str],
    errors: list[str],
    *,
    file_fields: dict[str, dict[str, str]] | None = None,
    evidence_dir: Path | None = None,
    recomputed_ceiling: str | None = None,
) -> None:
    """RC6-R6 R6-M2: central refs + direct critical equality bindings + timing."""
    name = "WITNESS_STATEMENT.md"
    file_fields = file_fields or {}
    run_id = fields.get("run_id", "")
    if "run_id" in fields and not is_safe_token(run_id):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
    package_identity_ref = fields.get("package_identity_ref", "")
    if "package_identity_ref" in fields and package_identity_ref != PACKAGE_IDENTITY_NAME:
        fail(
            errors,
            f"{name}: package_identity_ref must equal {PACKAGE_IDENTITY_NAME!r} "
            f"(found {package_identity_ref!r})",
        )
    final_binding_ref = fields.get("final_binding_ref", "")
    if "final_binding_ref" in fields and final_binding_ref != FINAL_BINDING_NAME:
        fail(
            errors,
            f"{name}: final_binding_ref must equal {FINAL_BINDING_NAME!r} "
            f"(found {final_binding_ref!r})",
        )
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
    upstream = fields.get("upstream_product_commands_not_run", "")
    if upstream != "yes":
        fail(errors, f"{name}: upstream_product_commands_not_run must be yes")

    # Timing grammar + fixed source refs (RC4B-033/034).
    for err in sb.validate_timing_grammar(
        execution_date_utc=fields.get("execution_date_utc", ""),
        execution_started_utc=fields.get("execution_started_utc", ""),
        execution_finished_utc=fields.get("execution_finished_utc", ""),
        source_file=fields.get("execution_timing_source_file", ""),
        source_start_field=fields.get("execution_timing_source_start_field", ""),
        source_end_field=fields.get("execution_timing_source_end_field", ""),
    ):
        fail(errors, f"{name}: {err}")

    build_timing = file_fields.get("BUILD_TIMING.txt") or {}
    if build_timing:
        for err in sb.validate_timing_equality_against_build_timing(
            execution_started_utc=fields.get("execution_started_utc", ""),
            execution_finished_utc=fields.get("execution_finished_utc", ""),
            build_timing_fields=build_timing,
        ):
            fail(errors, f"{name}: {err}")
    else:
        fail(errors, f"{name}: BUILD_TIMING.txt required to equality-bind execution timing")

    # Direct critical equality bindings to authoritative package values.
    final_binding = file_fields.get(FINAL_BINDING_NAME) or {}
    artifact = file_fields.get("ARTIFACT_IDENTITY.txt") or {}
    deviations = file_fields.get("DEVIATIONS.txt") or {}
    red_index = file_fields.get("REDACTIONS_INDEX.txt") or {}
    red_md = file_fields.get("REDACTIONS.md") or {}

    auth_outcome = fields.get("authoritative_outcome", "")
    if final_binding.get("authoritative_outcome") and auth_outcome != final_binding.get(
        "authoritative_outcome"
    ):
        fail(
            errors,
            f"{name}: authoritative_outcome must equal {FINAL_BINDING_NAME} "
            "authoritative_outcome",
        )
    if run_id and final_binding.get("run_id") and run_id != final_binding.get("run_id"):
        fail(errors, f"{name}: run_id must equal {FINAL_BINDING_NAME} run_id")
    pkg = file_fields.get(PACKAGE_IDENTITY_NAME) or {}
    if run_id and pkg.get("run_id") and run_id != pkg.get("run_id"):
        fail(errors, f"{name}: run_id must equal {PACKAGE_IDENTITY_NAME} run_id")

    expected_artifact = final_binding.get("artifact_sha256") or artifact.get("artifact_sha256", "")
    if expected_artifact and fields.get("artifact_sha256") != expected_artifact:
        fail(
            errors,
            f"{name}: artifact_sha256 must equal authoritative artifact identity "
            f"(found {fields.get('artifact_sha256')!r}, expected {expected_artifact!r})",
        )
    if fields.get("evidence_manifest_ref") != MANIFEST_NAME:
        fail(
            errors,
            f"{name}: evidence_manifest_ref must equal {MANIFEST_NAME!r} "
            f"(found {fields.get('evidence_manifest_ref')!r})",
        )
    # Manifest identity is carried by WEAVER_FORGE_FINAL_BINDING.txt (excluded from
    # the sealed manifest). Statement binds via final_binding_ref + evidence_manifest_ref
    # and equality against the final-binding recorded hash when present.
    expected_manifest = final_binding.get("final_manifest_sha256", "")
    if expected_manifest and evidence_dir is not None:
        manifest_path = evidence_dir / MANIFEST_NAME
        if manifest_path.is_file():
            actual_manifest = sha256_file(manifest_path)
            if expected_manifest != actual_manifest:
                fail(
                    errors,
                    f"{name}: {FINAL_BINDING_NAME} final_manifest_sha256 does not match "
                    f"recomputed {MANIFEST_NAME} identity (manifest identity binding)",
                )

    if evidence_dir is not None:
        dev_path = evidence_dir / "DEVIATIONS.txt"
        idx_path = evidence_dir / "REDACTIONS_INDEX.txt"
        if dev_path.is_file():
            actual_dev = sha256_file(dev_path)
            if fields.get("deviations_sha256") != actual_dev:
                fail(
                    errors,
                    f"{name}: deviations_sha256 must equal SHA-256 of DEVIATIONS.txt "
                    "(deviation identity)",
                )
        if idx_path.is_file():
            actual_idx = sha256_file(idx_path)
            if fields.get("redactions_index_sha256") != actual_idx:
                fail(
                    errors,
                    f"{name}: redactions_index_sha256 must equal SHA-256 of "
                    "REDACTIONS_INDEX.txt (redaction identity)",
                )

    if deviations.get("deviation_state") and fields.get("deviation_state") != deviations.get(
        "deviation_state"
    ):
        fail(errors, f"{name}: deviation_state must equal DEVIATIONS.txt deviation_state")
    index_state = red_index.get("redaction_state") or red_md.get("redaction_state")
    if index_state and fields.get("redaction_state") != index_state:
        fail(
            errors,
            f"{name}: redaction_state must equal REDACTIONS_INDEX.txt/REDACTIONS.md "
            "redaction_state",
        )

    expected_ceiling = recomputed_ceiling or deviations.get("final_machine_ceiling")
    if expected_ceiling and fields.get("final_machine_ceiling") != expected_ceiling:
        fail(
            errors,
            f"{name}: final_machine_ceiling must equal validator-authoritative "
            f"recomputed ceiling {expected_ceiling!r} "
            f"(found {fields.get('final_machine_ceiling')!r})",
        )

    expected_identity = sb.compute_statement_identity_sha256(fields)
    if fields.get("statement_identity_sha256") != expected_identity:
        fail(
            errors,
            f"{name}: statement_identity_sha256 mismatch "
            f"(recomputed={expected_identity} recorded={fields.get('statement_identity_sha256')})",
        )


# ---------------------------------------------------------------------------
# Machine-computed verdict ceiling (rc4)
# ---------------------------------------------------------------------------


def detect_prohibited_violation(file_fields: dict[str, dict[str, str]]) -> list[str]:
    """Row-1/2/row-"upstream" FAIL signals: proven product execution, ldd use,
    or upstream product-command invocation. product_executed/ldd_used are
    already independently enforced as required-exact 'NO' per file; this
    aggregates any file where that enforcement would (or did) fail, plus the
    WITNESS_STATEMENT.md upstream-commands disclosure, into a single
    ceiling-relevant signal."""
    reasons: list[str] = []
    for fname, fields in file_fields.items():
        pe = fields.get("product_executed")
        if pe is not None and pe not in ("NO", ""):
            reasons.append(f"{fname}: product_executed={pe!r}")
        lu = fields.get("ldd_used")
        if lu is not None and lu not in ("NO", ""):
            reasons.append(f"{fname}: ldd_used={lu!r}")
    stmt = file_fields.get("WITNESS_STATEMENT.md", {})
    if stmt.get("upstream_product_commands_not_run") == "no":
        reasons.append("WITNESS_STATEMENT.md: upstream_product_commands_not_run=no")
    return reasons


def detect_identity_mismatch(file_fields: dict[str, dict[str, str]]) -> list[str]:
    """Rows 4-9 FAIL signals: canonical tag/commit/image/lock/source mismatch."""
    reasons: list[str] = []
    wfpi = file_fields.get("WEAVER_FORGE_PACKAGE_IDENTITY.txt", {})
    if wfpi.get("tag_head_match") == "no":
        reasons.append("WEAVER_FORGE_PACKAGE_IDENTITY.txt: tag_head_match=no")
    tag = wfpi.get("weaver_forge_tag_requested", "")
    package_version = wfpi.get("package_version", "")
    expected_tag = expected_package_tag_for_version(package_version)
    if package_version and expected_tag is None:
        reasons.append(
            "WEAVER_FORGE_PACKAGE_IDENTITY.txt: unsupported package_version "
            f"(no expected tag for {package_version!r})"
        )
    elif expected_tag is not None and tag and tag != expected_tag:
        reasons.append(
            "WEAVER_FORGE_PACKAGE_IDENTITY.txt: weaver_forge_tag_requested != "
            f"expected tag for package_version={package_version!r} "
            f"(expected {expected_tag})"
        )

    verdict = file_fields.get("WITNESS_VERDICT.md", {})
    package_tag = verdict.get("package_tag", "")
    if expected_tag is not None and package_tag and package_tag != expected_tag:
        reasons.append(
            "WITNESS_VERDICT.md: package_tag != expected tag for "
            f"package_version={package_version!r} (expected {expected_tag})"
        )

    binding = file_fields.get(FINAL_BINDING_NAME, {})
    canonical_tag = binding.get("canonical_tag", "")
    if expected_tag is not None and canonical_tag and canonical_tag != expected_tag:
        reasons.append(
            f"{FINAL_BINDING_NAME}: canonical_tag != expected tag for "
            f"package_version={package_version!r} (expected {expected_tag})"
        )

    observed_tags = [t for t in (tag, package_tag, canonical_tag) if t]
    if len(set(observed_tags)) > 1:
        reasons.append(
            "cross-file package identity tag mismatch among "
            "weaver_forge_tag_requested / package_tag / canonical_tag"
        )

    si = file_fields.get("SOURCE_IDENTITY.txt", {})
    observed_commit = si.get("grok_build_commit_observed", "")
    if observed_commit and observed_commit != EXPECTED_GROK_COMMIT:
        reasons.append("SOURCE_IDENTITY.txt: grok_build_commit_observed mismatch")
    observed_lock = si.get("cargo_lock_sha256_before", "")
    if observed_lock and observed_lock != EXPECTED_CARGO_LOCK_SHA256:
        reasons.append("SOURCE_IDENTITY.txt: cargo_lock_sha256_before mismatch")

    ii = file_fields.get("IMAGE_IDENTITY.txt", {})
    if ii.get("digest_match_expected") == "no" or ii.get("platform_match_expected") == "no":
        reasons.append("IMAGE_IDENTITY.txt: digest_match_expected/platform_match_expected=no")

    pbi = file_fields.get("POST_BUILD_INTEGRITY.txt", {})
    if pbi.get("source_clean_before") == "no" or pbi.get("source_clean_after") == "no":
        reasons.append("POST_BUILD_INTEGRITY.txt: source not clean before/after build")
    if pbi.get("source_or_lock_changed") == "yes":
        reasons.append("POST_BUILD_INTEGRITY.txt: source_or_lock_changed=yes")
    head_before, head_after = pbi.get("source_head_before", ""), pbi.get("source_head_after", "")
    if head_before and head_after and head_before != head_after:
        reasons.append("POST_BUILD_INTEGRITY.txt: source_head_before != source_head_after")
    lock_before, lock_after = pbi.get("cargo_lock_sha256_before", ""), pbi.get("cargo_lock_sha256_after", "")
    if lock_before and lock_after and lock_before != lock_after:
        reasons.append("POST_BUILD_INTEGRITY.txt: cargo_lock_sha256_before != cargo_lock_sha256_after")
    return reasons


def compute_verdict_ceiling(
    outcome: str | None,
    prohibited: bool,
    identity_mismatch: bool,
    static_inspection_incomplete: bool,
    deviation_final_ceiling: str | None = None,
    redaction_integrity_critical: bool = False,
) -> str:
    """Machine-enforced verdict ceiling (R5-C3 validator-authoritative).

    Precedence (strictest wins):
      - proven product execution / ldd use / upstream command use -> FAIL
      - integrity-critical improper redaction (R6-RD2)            -> FAIL
      - canonical identity mismatch (tag/commit/image/lock/source)  -> FAIL
      - outcome is CARGO_FAILED or CARGO_SUCCEEDED_ARTIFACT_MISSING -> FAIL
      - outcome is BUILD_NOT_STARTED or INFRASTRUCTURE_FAILURE (or
        undetermined)                                               -> INDETERMINATE
      - outcome is CARGO_SUCCEEDED_ARTIFACT_PRESENT with incomplete
        static inspection                                           -> PARTIAL (max)
      - outcome is CARGO_SUCCEEDED_ARTIFACT_PRESENT, fully complete  -> PASS (eligible)
      - deviation final_machine_ceiling / severity caps (incl.
        NONMATERIAL_DISCLOSED→PARTIAL, PROHIBITED→FAIL, and FAIL for
        EXPECTED_RUSTC_VERSION / EXPECTED_DOTSLASH_VERSION / RUST_IMAGE
        identity overrides) fold in via strictest-wins recomputation
    """
    return dxt.recompute_machine_ceiling(
        outcome=outcome,
        prohibited=prohibited or redaction_integrity_critical,
        identity_mismatch=identity_mismatch,
        static_inspection_incomplete=static_inspection_incomplete,
        deviation_final_ceiling=deviation_final_ceiling,
    )


def check_witness_verdict(
    text: str,
    fields: dict[str, str],
    errors: list[str],
    outcome: str | None,
    computed_ceiling: str,
    *,
    mode: str = MODE_FINAL_SUBMISSION,
    file_fields: dict[str, dict[str, str]] | None = None,
    evidence_dir: Path | None = None,
    statement_text: str | None = None,
    enforce_r6_bindings: bool = True,
) -> None:
    name = "WITNESS_VERDICT.md"
    file_fields = file_fields or {}
    matches, verdict_errors = parse_verdict_selection(text)
    errors.extend(verdict_errors)
    if not is_safe_token(fields.get("run_id", "")):
        fail(errors, f"{name}: run_id must be a non-empty token with no path separators, whitespace, or '..'")
    package_identity_ref = fields.get("package_identity_ref", "")
    if "package_identity_ref" in fields and package_identity_ref != PACKAGE_IDENTITY_NAME:
        fail(
            errors,
            f"{name}: package_identity_ref must equal {PACKAGE_IDENTITY_NAME!r} "
            f"(found {package_identity_ref!r})",
        )
    final_binding_ref = fields.get("final_binding_ref", "")
    if "final_binding_ref" in fields and final_binding_ref != FINAL_BINDING_NAME:
        fail(
            errors,
            f"{name}: final_binding_ref must equal {FINAL_BINDING_NAME!r} "
            f"(found {final_binding_ref!r})",
        )
    tag = fields.get("package_tag", "")
    if tag and not package_tag_matches_grammar(tag):
        fail(errors, f"{name}: package_tag does not match expected tag grammar: {tag!r}")
    # Package-version/tag tuple equality (RC4B-022/026/028/035): package_tag must
    # equal the version-aware expected tag and the observed identity/final-binding tags.
    wfpi = file_fields.get(PACKAGE_IDENTITY_NAME) or {}
    final_binding = file_fields.get(FINAL_BINDING_NAME) or {}
    package_version = wfpi.get("package_version", "")
    expected_tag = expected_package_tag_for_version(package_version)
    requested_tag = wfpi.get("weaver_forge_tag_requested", "")
    canonical_tag = final_binding.get("canonical_tag", "")
    if tag and expected_tag is not None and tag != expected_tag:
        fail(
            errors,
            f"{name}: package_tag must equal expected tag for "
            f"package_version={package_version!r} "
            f"(expected {expected_tag}, found {tag!r})",
        )
    if tag and requested_tag and tag != requested_tag:
        fail(
            errors,
            f"{name}: package_tag must equal {PACKAGE_IDENTITY_NAME} "
            "weaver_forge_tag_requested",
        )
    if tag and canonical_tag and tag != canonical_tag:
        fail(
            errors,
            f"{name}: package_tag must equal {FINAL_BINDING_NAME} canonical_tag",
        )
    weaver_commit = fields.get("weaver_forge_commit", "")
    if weaver_commit and not is_hex_commit(weaver_commit):
        fail(errors, f"{name}: weaver_forge_commit must be a 40-char lowercase hex commit")
    require_exact(name, fields, "grok_build_commit", EXPECTED_GROK_COMMIT, errors)
    require_exact(name, fields, "product_executed", "NO", errors)
    require_exact(name, fields, "ldd_used", "NO", errors)

    maintainer_intake = fields.get("maintainer_intake_verdict", "")
    # RC6-R6 / R6-I2: final submission freezes intake at pending; later intake is
    # append-only outside the hashed package and must not mutate this field.
    if enforce_r6_bindings and mode == MODE_FINAL_SUBMISSION:
        if maintainer_intake != "pending":
            fail(
                errors,
                f"{name}: maintainer_intake_verdict must be pending for active final "
                f"submission (found {maintainer_intake!r}); later dispositions append to "
                "the external MAINTAINER_INTAKE_LEDGER.txt sidecar",
            )
    elif maintainer_intake not in MAINTAINER_INTAKE_VALUES:
        fail(
            errors,
            f"{name}: maintainer_intake_verdict must be one of {sorted(MAINTAINER_INTAKE_VALUES)} "
            f"(found {maintainer_intake!r})",
        )

    file_outcome = fields.get("outcome")
    if file_outcome not in OUTCOME_VALUES:
        fail(errors, f"{name}: outcome must be one of {sorted(OUTCOME_VALUES)}")
    elif outcome is not None and file_outcome != outcome:
        fail(errors, f"{name}: outcome ({file_outcome}) does not match BUILD_EXIT_CODE.txt outcome ({outcome})")

    recorded_ceiling = fields.get("verdict_ceiling", "")
    if recorded_ceiling not in VERDICT_VALUES:
        fail(errors, f"{name}: verdict_ceiling must be one of {sorted(VERDICT_VALUES)} (found {recorded_ceiling!r})")

    effective_ceiling_rank = VERDICT_RANK[computed_ceiling]
    if recorded_ceiling in VERDICT_RANK:
        if VERDICT_RANK[recorded_ceiling] < effective_ceiling_rank:
            effective_ceiling_rank = VERDICT_RANK[recorded_ceiling]

    if matches:
        verdict_value = matches[0]
        if verdict_value in VERDICT_RANK and VERDICT_RANK[verdict_value] > VERDICT_RANK[computed_ceiling]:
            fail(
                errors,
                f"{name}: proposed verdict {verdict_value} exceeds the machine-computed verdict "
                f"ceiling {computed_ceiling} for this run's evidence — a verdict may never be "
                "recorded above its ceiling",
            )
        elif verdict_value in VERDICT_RANK and VERDICT_RANK[verdict_value] > effective_ceiling_rank:
            fail(
                errors,
                f"{name}: proposed verdict {verdict_value} exceeds the recorded verdict_ceiling "
                f"{recorded_ceiling!r} (machine-computed ceiling is {computed_ceiling!r})",
            )

    # R6 equality bindings to statement / deviation / redaction / ceiling identities.
    if not enforce_r6_bindings:
        return
    stmt = file_fields.get("WITNESS_STATEMENT.md") or {}
    deviations = file_fields.get("DEVIATIONS.txt") or {}
    red_index = file_fields.get("REDACTIONS_INDEX.txt") or {}
    if stmt:
        if fields.get("statement_identity_sha256") != stmt.get("statement_identity_sha256"):
            fail(
                errors,
                f"{name}: statement_identity_sha256 must equal WITNESS_STATEMENT.md "
                "statement_identity_sha256",
            )
        if fields.get("deviations_sha256") != stmt.get("deviations_sha256"):
            fail(errors, f"{name}: deviations_sha256 must equal WITNESS_STATEMENT.md deviations_sha256")
        if fields.get("redactions_index_sha256") != stmt.get("redactions_index_sha256"):
            fail(
                errors,
                f"{name}: redactions_index_sha256 must equal WITNESS_STATEMENT.md "
                "redactions_index_sha256",
            )
        if fields.get("deviation_state") != stmt.get("deviation_state"):
            fail(errors, f"{name}: deviation_state must equal WITNESS_STATEMENT.md deviation_state")
        if fields.get("redaction_state") != stmt.get("redaction_state"):
            fail(errors, f"{name}: redaction_state must equal WITNESS_STATEMENT.md redaction_state")
        if fields.get("final_machine_ceiling") != stmt.get("final_machine_ceiling"):
            fail(
                errors,
                f"{name}: final_machine_ceiling must equal WITNESS_STATEMENT.md "
                "final_machine_ceiling",
            )
        if fields.get("run_id") and stmt.get("run_id") and fields.get("run_id") != stmt.get("run_id"):
            fail(errors, f"{name}: run_id must equal WITNESS_STATEMENT.md run_id")
    if deviations.get("deviation_state") and fields.get("deviation_state") != deviations.get(
        "deviation_state"
    ):
        fail(errors, f"{name}: deviation_state must equal DEVIATIONS.txt deviation_state")
    if red_index.get("redaction_state") and fields.get("redaction_state") != red_index.get(
        "redaction_state"
    ):
        fail(errors, f"{name}: redaction_state must equal REDACTIONS_INDEX.txt redaction_state")
    if fields.get("final_machine_ceiling") != computed_ceiling:
        fail(
            errors,
            f"{name}: final_machine_ceiling must equal validator-authoritative "
            f"recomputed ceiling {computed_ceiling!r} "
            f"(found {fields.get('final_machine_ceiling')!r})",
        )
    if evidence_dir is not None and statement_text is not None:
        actual_stmt = hashlib.sha256(statement_text.encode("utf-8")).hexdigest()
        if fields.get("witness_statement_sha256") != actual_stmt:
            fail(
                errors,
                f"{name}: witness_statement_sha256 must equal SHA-256 of "
                "WITNESS_STATEMENT.md bytes (statement identity)",
            )
        if evidence_dir.joinpath("DEVIATIONS.txt").is_file():
            actual_dev = sha256_file(evidence_dir / "DEVIATIONS.txt")
            if fields.get("deviations_sha256") != actual_dev:
                fail(errors, f"{name}: deviations_sha256 must equal SHA-256 of DEVIATIONS.txt")
        if evidence_dir.joinpath("REDACTIONS_INDEX.txt").is_file():
            actual_idx = sha256_file(evidence_dir / "REDACTIONS_INDEX.txt")
            if fields.get("redactions_index_sha256") != actual_idx:
                fail(
                    errors,
                    f"{name}: redactions_index_sha256 must equal SHA-256 of REDACTIONS_INDEX.txt",
                )


def check_deviations(
    fields: dict[str, str],
    text: str,
    errors: list[str],
    *,
    mode: str = MODE_FINAL_SUBMISSION,
    register: CanonicalSchemaRegister | None = None,
    expected_run_id: str | None = None,
) -> str | None:
    """Validate DEVIATIONS.txt. Returns recomputed final_machine_ceiling for R5 finals."""
    name = "DEVIATIONS.txt"
    reg = register or _SCHEMA_REGISTER
    state = fields.get("deviation_state", "")
    if state not in ("NONE", "PRESENT"):
        fail(errors, f"{name}: deviation_state must be NONE or PRESENT")
        return None

    s2_prelim = mode == MODE_HOST_PRELIMINARY and is_s2_shaped_preliminary_deviations(fields)
    s2_final = mode == MODE_FINAL_SUBMISSION and is_s2_shaped_final_deviations(fields)
    r5_final = (
        s2_final
        and "preliminary_deviations_sha256" in reg.required_field_names(name, MODE_FINAL_SUBMISSION)
    )

    # Reject mode crossover: preliminary S2 schema must not carry final indexed
    # Witness deviation fabrication; final S2 must not carry automated_summary.
    if mode == MODE_HOST_PRELIMINARY and any(
        k.startswith("deviation_") and k.endswith("_severity") for k in fields
    ):
        fail(
            errors,
            f"{name}: host-preliminary DEVIATIONS must not contain final indexed "
            "deviation_<n>_severity records (mode crossover)",
        )
    if mode == MODE_FINAL_SUBMISSION and "automated_summary" in fields:
        fail(
            errors,
            f"{name}: final-submission DEVIATIONS must not contain automated_summary "
            "(preliminary host field; mode crossover)",
        )

    if s2_prelim:
        required = reg.required_field_names(name, MODE_HOST_PRELIMINARY)
        require_exact_field_set(name, fields, required, errors)
        count_raw = fields.get("deviation_count", "")
        if not count_raw.isdigit():
            fail(errors, f"{name}: deviation_count must be a non-negative integer")
        else:
            count = int(count_raw)
            if state == "NONE" and count != 0:
                fail(errors, f"{name}: deviation_state=NONE requires deviation_count=0")
            if state == "PRESENT" and count < 1:
                fail(errors, f"{name}: deviation_state=PRESENT requires deviation_count>=1")
        if not fields.get("automated_summary"):
            fail(errors, f"{name}: automated_summary must be non-empty")
        return None

    if r5_final:
        core = reg.required_field_names(name, MODE_FINAL_SUBMISSION)
        indexed_re = re.compile(
            r"^deviation_\d+_(description|severity|canonical_identity_impact|verdict_ceiling)$"
        )
        require_exact_field_set_with_indexed(
            name,
            fields,
            core,
            indexed_re,
            errors,
            allow_indexed=(state == "PRESENT"),
        )
        for msg in dxt.verify_final_package_consistency(
            fields, expected_run_id=expected_run_id
        ):
            fail(errors, msg)
        return fields.get("final_machine_ceiling")

    if s2_final:
        # Historical / pre-R5 final shape: core count fields; indexed keys when PRESENT.
        core = ("evidence_schema_version", "deviation_state", "deviation_count")
        indexed_re = re.compile(
            r"^deviation_\w+_(description|severity|canonical_identity_impact|verdict_ceiling)$"
        )
        require_exact_field_set_with_indexed(
            name,
            fields,
            core,
            indexed_re,
            errors,
            allow_indexed=(state == "PRESENT"),
        )
        count_raw = fields.get("deviation_count", "")
        if not count_raw.isdigit():
            fail(errors, f"{name}: deviation_count must be a non-negative integer")
        else:
            count = int(count_raw)
            if state == "NONE" and count != 0:
                fail(errors, f"{name}: deviation_state=NONE requires deviation_count=0")
            if state == "PRESENT" and count < 1:
                fail(errors, f"{name}: deviation_state=PRESENT requires deviation_count>=1")
        if state == "NONE":
            return None
        # Fall through to indexed checks for PRESENT.
    elif state == "NONE":
        return None

    indices: set[str] = set()
    for match in re.finditer(r"deviation_(\w+)_severity", text):
        indices.add(match.group(1))
    if not indices:
        fail(errors, f"{name}: deviation_state=PRESENT but no enumerated deviation_<n>_* entries were found")
        return None
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
    if s2_final and count_raw.isdigit() and int(count_raw) != len(indices):
        fail(
            errors,
            f"{name}: deviation_count={count_raw} does not match enumerated deviation count {len(indices)}",
        )
    return None


def check_redactions(fields: dict[str, str], text: str, errors: list[str]) -> None:
    """RC6-R6: human-readable REDACTIONS.md paired with REDACTIONS_INDEX.txt."""
    name = "REDACTIONS.md"
    state = fields.get("redaction_state", "")
    if state not in ("NONE", "PRESENT"):
        fail(errors, f"{name}: redaction_state must be NONE or PRESENT")
        return
    core = (
        "evidence_schema_version",
        "redaction_state",
        "semantic_integrity_declaration",
        "redactions_index_ref",
    )
    # Human file has no machine indexed entries under R6-RD2; index owns those.
    require_exact_field_set(name, fields, core, errors)
    require_exact(name, fields, "semantic_integrity_declaration", "yes", errors)
    require_exact(name, fields, "redactions_index_ref", "REDACTIONS_INDEX.txt", errors)


def check_redactions_index(
    fields: dict[str, str],
    text: str,
    errors: list[str],
    *,
    expected_run_id: str | None = None,
    redactions_md_fields: dict[str, str] | None = None,
) -> bool:
    """Validate REDACTIONS_INDEX.txt. Returns integrity_critical flag for ceiling."""
    name = "REDACTIONS_INDEX.txt"
    if expected_run_id and fields.get("run_id") and fields.get("run_id") != expected_run_id:
        fail(errors, f"{name}: run_id must equal package run_id {expected_run_id!r}")
    if redactions_md_fields:
        if fields.get("redaction_state") != redactions_md_fields.get("redaction_state"):
            fail(
                errors,
                f"{name}: redaction_state must equal REDACTIONS.md redaction_state",
            )
    state = fields.get("redaction_state", "")
    core = ("evidence_schema_version", "run_id", "redaction_state", "redaction_count")
    indexed_re = re.compile(
        r"^redaction_\d+_(file|field|category|original_value_sha256|replacement_marker)$"
    )
    require_exact_field_set_with_indexed(
        name,
        fields,
        core,
        indexed_re,
        errors,
        allow_indexed=(state == "PRESENT"),
    )
    index_errors, integrity_critical = ridx.validate_redaction_index_fields(fields, name=name)
    for msg in index_errors:
        fail(errors, msg)
    return integrity_critical


def check_weaver_forge_final_binding(
    fields: dict[str, str],
    errors: list[str],
    evidence_dir: Path,
    file_fields: dict[str, dict[str, str]],
    outcome: str | None,
    *,
    mode: str = MODE_FINAL_SUBMISSION,
) -> None:
    """RC6-R3: validate Host-owned WEAVER_FORGE_FINAL_BINDING.txt cross-bindings.

    Mechanical ownership/tuple checks only — does not implement R4–R7 semantics.
    """
    name = FINAL_BINDING_NAME
    enforce_register_field_set(name, fields, mode, errors)
    check_s2_legal_values(
        name,
        fields,
        _SCHEMA_REGISTER.legal_values(name, mode),
        errors,
    )

    if not is_safe_token(fields.get("run_id", "")):
        fail(errors, f"{name}: run_id must be a non-empty safe token")

    authoritative_outcome = fields.get("authoritative_outcome", "")
    if authoritative_outcome and authoritative_outcome not in OUTCOME_VALUES:
        fail(
            errors,
            f"{name}: authoritative_outcome must be one of {sorted(OUTCOME_VALUES)} "
            f"(found {authoritative_outcome!r})",
        )

    manifest_path = evidence_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        fail(errors, f"{name}: cannot verify final_manifest_sha256; {MANIFEST_NAME} missing")
    else:
        # Reject if final binding is listed inside the sealed manifest.
        for line_no, raw_line in enumerate(read_text(manifest_path).splitlines(), start=1):
            line = raw_line.rstrip("\r\n")
            if not line.strip():
                continue
            _digest, rel, error = parse_manifest_line(line, line_no)
            if error is not None:
                continue
            if rel == FINAL_BINDING_NAME:
                fail(
                    errors,
                    f"{name}: must not be listed inside {MANIFEST_NAME} "
                    "(final binding seals the manifest and is excluded from it)",
                )
                break
        actual_manifest_sha = sha256_file(manifest_path)
        recorded = fields.get("final_manifest_sha256", "")
        if not is_sha256(recorded):
            fail(errors, f"{name}: final_manifest_sha256 must be a 64-char lowercase hex sha256")
        elif actual_manifest_sha != recorded:
            fail(
                errors,
                f"{name}: final_manifest_sha256 mismatch "
                f"(recomputed={actual_manifest_sha} recorded={recorded})",
            )

    wfpi = file_fields.get(PACKAGE_IDENTITY_NAME, {})
    build_exit = file_fields.get("BUILD_EXIT_CODE.txt", {})
    host_outcome = file_fields.get(HOST_OUTCOME_INGESTION_NAME, {})
    post_build = file_fields.get("POST_BUILD_INTEGRITY.txt", {})
    source_identity = file_fields.get("SOURCE_IDENTITY.txt", {})
    artifact_identity = file_fields.get("ARTIFACT_IDENTITY.txt", {})

    binding_run_id = fields.get("run_id", "")
    for label, peer in (
        (PACKAGE_IDENTITY_NAME, wfpi),
        ("BUILD_EXIT_CODE.txt", build_exit),
        (HOST_OUTCOME_INGESTION_NAME, host_outcome),
    ):
        peer_run_id = peer.get("run_id", "")
        if peer and peer_run_id and binding_run_id and peer_run_id != binding_run_id:
            fail(
                errors,
                f"{name}: run_id={binding_run_id!r} must equal {label} run_id={peer_run_id!r}",
            )

    if wfpi:
        if fields.get("package_version") != wfpi.get("package_version"):
            fail(
                errors,
                f"{name}: package_version must equal {PACKAGE_IDENTITY_NAME} package_version",
            )
        if fields.get("canonical_tag") != wfpi.get("weaver_forge_tag_requested"):
            fail(
                errors,
                f"{name}: canonical_tag must equal {PACKAGE_IDENTITY_NAME} "
                "weaver_forge_tag_requested",
            )
        expected_tag = expected_package_tag_for_version(wfpi.get("package_version", ""))
        canonical = fields.get("canonical_tag", "")
        if expected_tag is not None and canonical and canonical != expected_tag:
            fail(
                errors,
                f"{name}: canonical_tag must equal expected tag for "
                f"package_version={wfpi.get('package_version', '')!r} "
                f"(expected {expected_tag}, found {canonical!r})",
            )
        if fields.get("tag_object_id") != wfpi.get("weaver_forge_tag_object_id"):
            fail(
                errors,
                f"{name}: tag_object_id must equal {PACKAGE_IDENTITY_NAME} "
                "weaver_forge_tag_object_id",
            )
        if fields.get("peeled_commit") != wfpi.get("weaver_forge_tag_peeled_commit"):
            fail(
                errors,
                f"{name}: peeled_commit must equal {PACKAGE_IDENTITY_NAME} "
                "weaver_forge_tag_peeled_commit",
            )
        expected_source = wfpi.get("grok_build_source_commit_expected", "")
        if fields.get("grok_build_source_commit") != expected_source:
            fail(
                errors,
                f"{name}: grok_build_source_commit must equal {PACKAGE_IDENTITY_NAME} "
                "grok_build_source_commit_expected",
            )
        observed = source_identity.get("grok_build_commit_observed", "")
        if (
            observed
            and observed != "NOT_REACHED"
            and fields.get("grok_build_source_commit") != observed
        ):
            fail(
                errors,
                f"{name}: grok_build_source_commit must equal SOURCE_IDENTITY.txt "
                "grok_build_commit_observed when observed is present and not NOT_REACHED",
            )

    if authoritative_outcome:
        if build_exit.get("outcome") and build_exit.get("outcome") != authoritative_outcome:
            fail(
                errors,
                f"{name}: authoritative_outcome must equal BUILD_EXIT_CODE.txt outcome",
            )
        post_auth = post_build.get("authoritative_outcome", "")
        if post_auth and post_auth != authoritative_outcome:
            fail(
                errors,
                f"{name}: authoritative_outcome must equal POST_BUILD_INTEGRITY.txt "
                "authoritative_outcome when present",
            )
        if (
            host_outcome.get("container_result_valid") == "YES"
            and host_outcome.get("container_outcome")
            and host_outcome.get("container_outcome") != authoritative_outcome
        ):
            fail(
                errors,
                f"{name}: authoritative_outcome must equal HOST_OUTCOME_INGESTION "
                "container_outcome when container_result_valid=YES",
            )
        if outcome is not None and authoritative_outcome != outcome:
            fail(
                errors,
                f"{name}: authoritative_outcome must equal determined BUILD_EXIT outcome",
            )

    applicable = artifact_identity.get("applicable", "")
    if applicable == "yes":
        if fields.get("artifact_sha256") != artifact_identity.get("artifact_sha256"):
            fail(
                errors,
                f"{name}: artifact_sha256 must equal ARTIFACT_IDENTITY.txt artifact_sha256 "
                "when applicable=yes",
            )
        if fields.get("artifact_byte_size") != artifact_identity.get("artifact_size_bytes"):
            fail(
                errors,
                f"{name}: artifact_byte_size must equal ARTIFACT_IDENTITY.txt "
                "artifact_size_bytes when applicable=yes",
            )
    elif applicable == "no":
        if fields.get("artifact_sha256") != "NOT_APPLICABLE":
            fail(
                errors,
                f"{name}: artifact_sha256 must be NOT_APPLICABLE when "
                "ARTIFACT_IDENTITY applicable=no",
            )
        if fields.get("artifact_byte_size") != "NOT_APPLICABLE":
            fail(
                errors,
                f"{name}: artifact_byte_size must be NOT_APPLICABLE when "
                "ARTIFACT_IDENTITY applicable=no",
            )


def check_redaction_marker_consistency(
    all_texts: dict[str, str], redaction_index_fields: dict[str, str], errors: list[str]
) -> None:
    """Cross-check markers against REDACTIONS_INDEX.txt indexed entries (R6-RD2)."""
    for msg in ridx.reconcile_markers(
        index_fields=redaction_index_fields,
        all_texts=all_texts,
    ):
        fail(errors, msg)


# Files where the container script's escape_oneline() convention applies
# (multiline command output flattened into a single `key=value` line using
# an embedded literal '\n' with the CR stripped). Human-authored markdown
# files (WITNESS_STATEMENT.md, WITNESS_VERDICT.md, DEVIATIONS.txt,
# REDACTIONS.md, REDACTIONS_INDEX.txt) and dual-owned free-text files
# (ENVIRONMENT.txt) are intentionally excluded — they may legitimately contain
# real multi-line text (or CRLF from a Windows editor) that has nothing to do
# with this escaping convention.
ESCAPE_ONELINE_FILES = frozenset({"BOOTSTRAP.txt", "STATIC_ARTIFACT_INSPECTION.txt"})


def check_no_raw_carriage_returns(evidence_dir: Path, errors: list[str]) -> None:
    """Multiline command output (e.g. STATIC_ARTIFACT_INSPECTION.txt's
    *_output fields, BOOTSTRAP.txt's protoc_version_output) must be escaped
    to a single line with a literal '\\n' sequence before being written (see
    container_narrow_build.sh's escape_oneline()). A raw carriage-return
    byte in one of these files indicates output was captured without that
    escaping."""
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        if Path(rel).name not in ESCAPE_ONELINE_FILES:
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if b"\r" in raw:
            fail(
                errors,
                f"{rel}: contains a raw carriage-return byte; multiline command output must be "
                "escaped to a single line (embedded literal '\\n', CR stripped) before being "
                "written, not left as raw CR/CRLF",
            )


def collect_all_texts(evidence_dir: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        if rel == MANIFEST_NAME:
            continue
        texts[rel] = read_text(path)
    return texts


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


def check_no_empty_directories(
    evidence_dir: Path,
    errors: list[str],
    *,
    register: CanonicalSchemaRegister | None = None,
) -> None:
    """RC6-R4-E1: reject every empty directory under active rc6 evidence."""
    reg = register if register is not None else _SCHEMA_REGISTER
    if not reg.enforces_empty_directory_rejection():
        return
    try:
        empty = ei.find_empty_directories(evidence_dir)
    except ei.EvidenceInventoryError as exc:
        fail(errors, f"Empty-directory inspection fail-closed: {exc}")
        return
    for rel in empty:
        fail(errors, f"Empty directory rejected: {rel}")


def check_typed_nested_evidence_files(
    evidence_dir: Path,
    errors: list[str],
    *,
    register: CanonicalSchemaRegister | None = None,
    package_run_id: str | None = None,
    mode: str = MODE_FINAL_SUBMISSION,
) -> None:
    """RC6-R4-N2: every nested regular file must match exactly one registered class.

    Enforces owner/purpose/lifecycle/exact grammar from the active register.
    Historical registers skip this check (frozen semantics).
    """
    reg = register if register is not None else _SCHEMA_REGISTER
    if not reg.enforces_typed_nested_classes():
        return
    try:
        on_disk = ei.enumerate_evidence_files(evidence_dir)
    except ei.EvidenceInventoryError as exc:
        fail(errors, f"Evidence inventory fail-closed: {exc}")
        return
    for rel in on_disk:
        if "/" not in rel:
            continue
        try:
            rec = reg.resolve_nested_class_for_path(rel)
        except SchemaRegisterError as exc:
            fail(errors, str(exc))
            continue
        if rec is None:
            fail(
                errors,
                f"Unauthorized nested evidence file (no registered typed class): {rel}",
            )
            continue
        class_id = str(rec.get("class_id") or "")
        basename = rel.rsplit("/", 1)[-1]
        grammar = str(rec.get("filename_grammar") or "")
        if not grammar or re.fullmatch(grammar, basename) is None:
            fail(
                errors,
                f"{rel}: basename does not match registered filename_grammar "
                f"for class_id={class_id!r}",
            )
            continue
        modes = rec.get("lifecycle_modes") or []
        if mode not in modes:
            fail(
                errors,
                f"{rel}: class_id={class_id!r} is not authorized for lifecycle mode {mode!r}",
            )
            continue
        path = evidence_dir / rel
        text = read_text(path)
        fields, dup_errors = parse_kv(text, rel)
        errors.extend(dup_errors)
        required = tuple(
            f["name"]
            for f in (rec.get("fields") or [])
            if isinstance(f, dict) and f.get("requirement", "required") == "required"
        )
        if rec.get("exact_field_set_policy") == "exact":
            require_exact_field_set(rel, fields, required, errors)
        else:
            require_fields(rel, fields, required, errors)
        legal = rec.get("legal_values") or {}
        if isinstance(legal, dict):
            check_s2_legal_values(rel, fields, {k: tuple(v) for k, v in legal.items() if isinstance(v, list)}, errors)
        # Enforce path/class/purpose/owner consistency from register authority.
        if fields.get("class_id") and fields.get("class_id") != class_id:
            fail(
                errors,
                f"{rel}: class_id={fields.get('class_id')!r} does not match "
                f"registered class for path prefix ({class_id!r})",
            )
        if fields.get("purpose") and fields.get("purpose") != rec.get("purpose"):
            fail(
                errors,
                f"{rel}: purpose={fields.get('purpose')!r} does not match "
                f"registered purpose {rec.get('purpose')!r}",
            )
        if fields.get("owner") and fields.get("owner") != rec.get("owner"):
            fail(
                errors,
                f"{rel}: owner={fields.get('owner')!r} does not match "
                f"registered owner {rec.get('owner')!r}",
            )
        nested_run_id = fields.get("run_id", "")
        if nested_run_id and package_run_id and nested_run_id != package_run_id:
            fail(
                errors,
                f"{rel}: run_id={nested_run_id!r} must equal package run_id "
                f"{package_run_id!r} (class-level R3 provenance binding)",
            )


def check_forbidden_files(evidence_dir: Path, errors: list[str]) -> None:
    for path in sorted(evidence_dir.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.name in EXPLICITLY_FORBIDDEN_FILES:
            rel = path.relative_to(evidence_dir).as_posix()
            fail(
                errors,
                f"{rel}: {path.name} must never appear under the evidence directory "
                "(protoc version output belongs in BOOTSTRAP.txt's protoc_version_output/"
                "protoc_version_exit_code fields only)",
            )


FINAL_STRUCTURAL_REQUIRED_INPUTS = (
    "WITNESS_STATEMENT.md",
    "WITNESS_VERDICT.md",
    "DEVIATIONS.txt",
    "REDACTIONS.md",
    "REDACTIONS_INDEX.txt",
)
FINAL_STRUCTURAL_REQUIRED_INPUTS_PRE_R6 = (
    "WITNESS_STATEMENT.md",
    "WITNESS_VERDICT.md",
    "DEVIATIONS.txt",
    "REDACTIONS.md",
)


def check_completeness_state_machine(
    *,
    mode: str,
    s2_shaped: bool,
    evidence_dir: Path,
    post_build: dict[str, str] | None,
    host_outcome: dict[str, str] | None,
    errors: list[str],
    register: CanonicalSchemaRegister | None = None,
) -> None:
    """Enforce Phase 4-S3 completeness transitions without mutating evidence.

    Authority:
    - evidence_inventory_complete → POST_BUILD_INTEGRITY.txt
    - evidence_completeness_status / preliminary_success_eligible → HOST_OUTCOME_INGESTION.txt

    Does not create Independent Witness PASS or READY. Historical S1-shaped
    packages retain inventory_complete=no compatibility under final-submission.
    """
    reg = register if register is not None else _SCHEMA_REGISTER
    if not reg.is_s3_manifest_completeness_enforced():
        return

    inventory = (post_build or {}).get("evidence_inventory_complete", "")
    completeness = (host_outcome or {}).get("evidence_completeness_status", "")
    preliminary = (host_outcome or {}).get("preliminary_success_eligible", "")

    if preliminary and preliminary != "NO":
        # Phase 4 invariant: eligibility remains NO in both modes.
        fail(
            errors,
            f"{HOST_OUTCOME_INGESTION_NAME}: preliminary_success_eligible must remain NO "
            f"in Phase 4 (found {preliminary!r}; machine must not elevate eligibility)",
        )

    if mode == MODE_HOST_PRELIMINARY:
        if inventory == "yes":
            fail(
                errors,
                "POST_BUILD_INTEGRITY.txt: evidence_inventory_complete=yes is rejected in "
                "host-preliminary mode (inventory_complete remains no until final-submission "
                "structural boundary)",
            )
        if completeness == "COMPLETE" and inventory != "yes":
            # COMPLETE without yes is inconsistent for S2-shaped packages.
            if s2_shaped:
                fail(
                    errors,
                    f"{HOST_OUTCOME_INGESTION_NAME}: evidence_completeness_status=COMPLETE "
                    "is inconsistent with evidence_inventory_complete!=yes",
                )
        return

    # final-submission
    if not s2_shaped:
        # Historical S1 compatibility: inventory_complete=no remains accepted.
        return

    required_inputs = (
        FINAL_STRUCTURAL_REQUIRED_INPUTS
        if reg.is_active_authority
        else FINAL_STRUCTURAL_REQUIRED_INPUTS_PRE_R6
    )
    required_present = all((evidence_dir / name).is_file() for name in required_inputs)
    if inventory == "yes":
        if not required_present:
            missing = [
                name
                for name in required_inputs
                if not (evidence_dir / name).is_file()
            ]
            fail(
                errors,
                "POST_BUILD_INTEGRITY.txt: evidence_inventory_complete=yes rejected because "
                f"required final structural inputs are absent: {missing}",
            )
        if host_outcome is not None and completeness and completeness != "COMPLETE":
            fail(
                errors,
                f"{HOST_OUTCOME_INGESTION_NAME}: evidence_completeness_status must be COMPLETE "
                f"when evidence_inventory_complete=yes (found {completeness!r})",
            )
    else:
        fail(
            errors,
            "POST_BUILD_INTEGRITY.txt: S2-shaped final-submission requires "
            "evidence_inventory_complete=yes after completeness finalization and before "
            f"immutable final-manifest validation (found {inventory!r})",
        )


def validate_manifest(
    evidence_dir: Path,
    errors: list[str],
    *,
    mode: str = MODE_FINAL_SUBMISSION,
    s2_shaped: bool = False,
    register: CanonicalSchemaRegister | None = None,
) -> None:
    manifest_path = evidence_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return

    reg = register if register is not None else _SCHEMA_REGISTER
    mode_required = required_files_for_mode(mode, reg)
    accepted_supporting = accepted_supporting_files_for_mode(mode, reg)
    allowed = set(mode_required) | set(CLOSED_AUX_EVIDENCE_FILES) | set(accepted_supporting)

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

    if MANIFEST_NAME in listed:
        fail(errors, f"{MANIFEST_NAME}: must not list itself")
    if FINAL_BINDING_NAME in listed:
        fail(
            errors,
            f"{MANIFEST_NAME}: must not list {FINAL_BINDING_NAME} "
            "(final binding seals the manifest and is excluded from checksum lines)",
        )

    for req in mode_required:
        if req in (MANIFEST_NAME, FINAL_BINDING_NAME):
            continue
        if req not in listed:
            fail(errors, f"{MANIFEST_NAME}: missing mandatory entry for {req}")

    # Closed inventory allow-list for top-level declared paths.
    # Nested relative paths (containing '/') require registered typed-class
    # authority under active rc6.4 (RC6-R4 nested classes retained). Historical
    # registers retain recursive total-closure acceptance without typed-class
    # authority when they do not declare nested_evidence_classes.
    for rel in listed:
        if "/" in rel:
            if reg.enforces_typed_nested_classes():
                try:
                    rec = reg.resolve_nested_class_for_path(rel)
                except SchemaRegisterError as exc:
                    fail(errors, f"{MANIFEST_NAME}: {exc}")
                    continue
                if rec is None:
                    fail(
                        errors,
                        f"{MANIFEST_NAME}: declares nested path {rel} without registered "
                        "typed-class authority (listed+hashed is not sufficient)",
                    )
            continue
        if rel not in allowed:
            fail(
                errors,
                f"{MANIFEST_NAME}: declares {rel}, which is outside the closed required/optional "
                "evidence inventory (WITNESS_PACKAGE_MANIFEST.md); undeclared aux files are "
                "rejected even when correctly listed and hashed",
            )

    for rel, expected in listed.items():
        target = evidence_dir / rel
        if target.is_symlink() or not target.is_file():
            fail(errors, f"{MANIFEST_NAME}: listed file missing on disk: {rel}")
            continue
        actual = sha256_file(target)
        if actual != expected:
            fail(errors, f"{MANIFEST_NAME}: hash mismatch for {rel}")

    # Recursive inventory substrate (fail-closed). Nested regular files are
    # included under total manifest closure; unsafe objects are rejected by the
    # inventory helper (symlink/special/escape/duplicate).
    try:
        on_disk = ei.enumerate_evidence_files(evidence_dir)
    except ei.EvidenceInventoryError as exc:
        fail(errors, f"Evidence inventory fail-closed: {exc}")
        return

    on_disk_set = set(on_disk)
    if MANIFEST_NAME in on_disk_set:
        on_disk_set.remove(MANIFEST_NAME)
    if FINAL_BINDING_NAME in on_disk_set:
        on_disk_set.remove(FINAL_BINDING_NAME)

    if s2_shaped:
        # Phase 4-S3: no auxiliary / supporting exemption for S2-shaped packages.
        # Nested regular files must be listed and hashed like any other regular file.
        for rel in sorted(on_disk_set):
            if rel not in listed:
                fail(
                    errors,
                    f"Unlisted regular evidence file (S2/S3 total manifest closure; "
                    f"no auxiliary exemption): {rel}",
                )
        for rel in sorted(listed):
            if rel not in on_disk_set:
                fail(errors, f"{MANIFEST_NAME}: listed file missing on disk: {rel}")
        # Deterministic ordering: listed relative paths must match sorted inventory order.
        expected_order = sorted(on_disk_set)
        actual_order = list(listed.keys())
        if actual_order != expected_order:
            fail(
                errors,
                f"{MANIFEST_NAME}: entries must be in deterministic sorted relative-path order "
                "(byte-order / inventory order)",
            )
    else:
        # Historical S1 compatibility: closed-aux and accepted_supporting may exist
        # unlisted at top level; nested and other regular files must be listed.
        for rel in sorted(on_disk_set):
            if "/" not in rel and (
                rel in CLOSED_AUX_EVIDENCE_FILES or rel in accepted_supporting
            ):
                continue
            if rel not in listed:
                fail(errors, f"Unlisted regular evidence file (policy: structural FAIL): {rel}")


def validate_dir(
    evidence_dir: Path,
    *,
    host_preliminary: bool = False,
    mode: str | None = None,
    schema_register_version: str | None = None,
) -> list[str]:
    """Validate an evidence directory structurally.

    Modes (Phase 4-S1/S3):
    - ``host-preliminary`` / ``host_preliminary=True``: automated host evidence
      structural validation. Manual Witness files are not required.
    - ``final-submission``: final-shaped structural validation with S3 manifest
      totality and completeness-state enforcement for S2-shaped packages.
    - default (no explicit mode): compatibility alias to final-submission.

    Schema authority (RC6-R6 / SH-A retained):
    - default (``schema_register_version=None``): always active rc6.5
    - explicit historical version: historical loader only
    - evidence shape/fields cannot select schema authority

    This is not Independent Witness PASS, not final eligibility, not READY, and
    not rc5 readiness. The validator still writes nothing into evidence.
    """
    errors: list[str] = []
    if not evidence_dir.is_dir():
        return [f"Not a directory: {evidence_dir}"]

    field_register, reg_error = resolve_validation_register(schema_register_version)
    if reg_error is not None or field_register is None:
        return [reg_error or "schema register resolution failed"]

    selected_mode = resolve_validation_mode(host_preliminary=host_preliminary, mode=mode)
    mode_required = list(required_files_for_mode(selected_mode, field_register))
    accepted_supporting = accepted_supporting_files_for_mode(selected_mode, field_register)
    host_preliminary_mode = selected_mode == MODE_HOST_PRELIMINARY

    for name in mode_required:
        p = evidence_dir / name
        if not p.is_file():
            fail(errors, f"Missing required file: {name}")
        elif p.stat().st_size == 0 and name not in RAW_STREAM_FILES:
            fail(errors, f"Empty required file: {name}")

    check_no_symlinks(evidence_dir, errors)
    check_no_empty_directories(evidence_dir, errors, register=field_register)
    check_forbidden_files(evidence_dir, errors)
    check_no_raw_carriage_returns(evidence_dir, errors)

    for path in evidence_dir.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        text = read_text(path)
        for token in FORBIDDEN_PLACEHOLDERS:
            if token in text:
                fail(errors, f"Placeholder {token!r} in {path.name}")

    # Parse mode-required structured files plus any present accepted_supporting
    # files (backward regression visibility; not required for PASS).
    parse_names = list(mode_required)
    for name in sorted(accepted_supporting):
        if name not in parse_names and (evidence_dir / name).is_file():
            parse_names.append(name)

    file_texts: dict[str, str] = {}
    file_fields: dict[str, dict[str, str]] = {}
    for name in parse_names:
        p = evidence_dir / name
        if p.is_file() and not p.is_symlink():
            text = read_text(p)
            file_texts[name] = text
            if name not in RAW_STREAM_FILES and name != MANIFEST_NAME:
                fields, dup_errors = parse_kv(text, name)
                file_fields[name] = fields
                errors.extend(dup_errors)

    # Determine the overall outcome up front: it gates both the placeholder
    # allowance (NOT_REACHED container-owned files on a non-started /
    # infrastructure path) and every outcome-sensitive per-file check.
    # Explicit authoritative outcome only — no inference (Phase 3F-A).
    outcome: str | None = None
    if "BUILD_EXIT_CODE.txt" in file_fields:
        outcome = determine_outcome(file_fields["BUILD_EXIT_CODE.txt"], errors)
    elif (evidence_dir / "BUILD_EXIT_CODE.txt").is_file():
        # File present but not parsed into file_fields (should not happen for
        # required files); still fail closed on missing explicit outcome path.
        fail(errors, "Cannot determine outcome: BUILD_EXIT_CODE.txt could not be parsed")

    # Closed-aux HOST_RUN_METADATA may be present; load for S2 grammar / shape detection.
    host_meta_path = evidence_dir / "HOST_RUN_METADATA.txt"
    if host_meta_path.is_file() and not host_meta_path.is_symlink():
        file_texts["HOST_RUN_METADATA.txt"] = read_text(host_meta_path)

    s2_shaped = package_is_s2_shaped(file_fields, file_texts)

    # HOST_OUTCOME_INGESTION.txt uses schema_version= (not evidence_schema_version=)
    # and an exact host-owned field set. Parse/validate here; never route it through
    # the evidence_schema_version / FILE_REQUIRED_FIELDS path.
    host_outcome_fields: dict[str, str] | None = None
    if HOST_OUTCOME_INGESTION_NAME in file_fields:
        host_outcome_fields = file_fields[HOST_OUTCOME_INGESTION_NAME]
        check_host_outcome_ingestion(
            host_outcome_fields, errors, outcome, register=field_register
        )
    else:
        host_outcome_path = evidence_dir / HOST_OUTCOME_INGESTION_NAME
        if host_outcome_path.is_file() and not host_outcome_path.is_symlink():
            host_text = read_text(host_outcome_path)
            host_outcome_fields, host_dup_errors = parse_kv(host_text, HOST_OUTCOME_INGESTION_NAME)
            errors.extend(host_dup_errors)
            check_host_outcome_ingestion(
                host_outcome_fields, errors, outcome, register=field_register
            )
        elif host_preliminary_mode:
            # Compatibility message retained for Phase 3F coupled tests when the
            # file is absent and was not already reported via mode_required.
            if HOST_OUTCOME_INGESTION_NAME not in mode_required:
                fail(
                    errors,
                    f"Missing required file for host-preliminary mode: {HOST_OUTCOME_INGESTION_NAME}",
                )

    schema_versioned = [
        name
        for name in parse_names
        if name not in RAW_STREAM_FILES
        and name != MANIFEST_NAME
        and name != HOST_OUTCOME_INGESTION_NAME
        and name in file_fields
    ]
    for name in schema_versioned:
        fields = file_fields[name]
        # S2 NOT_APPLICABLE terminals use their own schema (no evidence_schema_version
        # skip); still require schema version via the NA checker.
        if name in PLACEHOLDER_ELIGIBLE_FILES and is_s2_not_applicable_terminal(fields):
            check_s2_not_applicable_terminal(name, fields, errors)
            continue
        check_schema_version(name, fields, errors)
        if placeholder_skip(name, fields, outcome, s2_shaped_package=s2_shaped):
            continue
        if s2_shaped and name in PLACEHOLDER_ELIGIBLE_FILES and is_not_reached_placeholder(fields):
            fail(
                errors,
                f"{name}: NOT_REACHED is initialization-only for S2-shaped packages; "
                "finalized terminal evidence must use NOT_APPLICABLE or the applicable "
                "full schema",
            )
            continue
        if name == "WEAVER_FORGE_PACKAGE_IDENTITY.txt" and is_s2_shaped_package_identity(fields):
            # Exact S2/rc6 field enforcement happens in check_weaver_forge_package_identity.
            continue
        if name == "DEVIATIONS.txt" and (
            (selected_mode == MODE_HOST_PRELIMINARY and is_s2_shaped_preliminary_deviations(fields))
            or (selected_mode == MODE_FINAL_SUBMISSION and is_s2_shaped_final_deviations(fields))
        ):
            # Exact S2/rc6 field enforcement happens in check_deviations.
            continue
        if name == "REDACTIONS.md":
            # Exact base keys enforced in check_redactions (R6-RD2 paired human file).
            continue
        if name == "REDACTIONS_INDEX.txt":
            # Exact base + indexed keys enforced in check_redactions_index.
            continue
        # Active WITNESS_STATEMENT.md / WITNESS_VERDICT.md must use register exact
        # field-set enforcement here (R1 authority). Semantic R6 bindings remain in
        # check_witness_statement / check_witness_verdict and do not replace this.
        policy = field_register.exact_field_set_policy(name, selected_mode)
        # Active validation uses the active FILE_REQUIRED_FIELDS projection.
        # Explicit historical validation must use the selected historical
        # register's own subset/required fields — never active R3 requirements
        # and never evidence-shape authority selection.
        if field_register.is_active_authority:
            required = FILE_REQUIRED_FIELDS.get(name, ())
        else:
            hist_compat = field_register.historical_compatibility_required_field_names(
                name, selected_mode
            )
            if hist_compat is not None:
                required = hist_compat
            else:
                required = field_register.required_field_names(name, selected_mode)
        if policy == "exact":
            # Exact or exact-with-named-optionals from the selected register.
            enforce_register_field_set(name, fields, selected_mode, errors, register=field_register)
        elif policy == "exact_when_s2_shaped_else_historical_subset":
            # Historical unshaped fixtures: required-subset projection only.
            require_fields(name, fields, required, errors)
        elif name == "POST_BUILD_INTEGRITY.txt":
            require_exact_field_set(name, fields, required, errors)
        else:
            require_fields(name, fields, required, errors)

    if "WEAVER_FORGE_PACKAGE_IDENTITY.txt" in file_fields:
        check_weaver_forge_package_identity(
            file_fields["WEAVER_FORGE_PACKAGE_IDENTITY.txt"],
            errors,
            register=field_register,
        )
    package_run_id = (file_fields.get(PACKAGE_IDENTITY_NAME) or {}).get("run_id")
    check_typed_nested_evidence_files(
        evidence_dir,
        errors,
        register=field_register,
        package_run_id=package_run_id,
        mode=selected_mode,
    )
    if "SOURCE_ACQUISITION.txt" in file_fields:
        check_source_acquisition(file_fields["SOURCE_ACQUISITION.txt"], errors)
    if "SOURCE_IDENTITY.txt" in file_fields:
        check_source_identity(file_fields["SOURCE_IDENTITY.txt"], errors)
    if "IMAGE_IDENTITY.txt" in file_fields:
        check_image_identity(file_fields["IMAGE_IDENTITY.txt"], errors)
    if "ENVIRONMENT.txt" in file_fields:
        check_environment(file_fields["ENVIRONMENT.txt"], errors)
    if "BOOTSTRAP.txt" in file_fields and not placeholder_skip(
        "BOOTSTRAP.txt", file_fields["BOOTSTRAP.txt"], outcome, s2_shaped_package=s2_shaped
    ):
        if not is_s2_not_applicable_terminal(file_fields["BOOTSTRAP.txt"]):
            check_bootstrap(file_fields["BOOTSTRAP.txt"], errors)
    if "CLEAN_TARGET_PROOF.txt" in file_fields:
        check_clean_target_proof(file_fields["CLEAN_TARGET_PROOF.txt"], errors)
    if "BUILD_COMMAND.txt" in file_fields and not placeholder_skip(
        "BUILD_COMMAND.txt", file_fields["BUILD_COMMAND.txt"], outcome, s2_shaped_package=s2_shaped
    ):
        if not is_s2_not_applicable_terminal(file_fields["BUILD_COMMAND.txt"]):
            check_build_command(file_fields["BUILD_COMMAND.txt"], errors)
    if "POST_BUILD_INTEGRITY.txt" in file_fields:
        check_post_build_integrity(file_fields["POST_BUILD_INTEGRITY.txt"], errors)
    deviation_ceiling: str | None = None
    package_run_id = None
    pkg_fields = file_fields.get(PACKAGE_IDENTITY_NAME) or {}
    if pkg_fields.get("run_id"):
        package_run_id = pkg_fields.get("run_id")
    if "DEVIATIONS.txt" in file_fields:
        deviation_ceiling = check_deviations(
            file_fields["DEVIATIONS.txt"],
            file_texts["DEVIATIONS.txt"],
            errors,
            mode=selected_mode,
            register=field_register,
            expected_run_id=package_run_id,
        )
    if "REDACTIONS.md" in file_fields:
        if field_register.is_active_authority:
            check_redactions(file_fields["REDACTIONS.md"], file_texts["REDACTIONS.md"], errors)
        else:
            # Historical pre-R6 REDACTIONS.md: base keys + optional indexed entries.
            hname = "REDACTIONS.md"
            hfields = file_fields["REDACTIONS.md"]
            htext = file_texts["REDACTIONS.md"]
            hstate = hfields.get("redaction_state", "")
            if hstate not in ("NONE", "PRESENT"):
                fail(errors, f"{hname}: redaction_state must be NONE or PRESENT")
            else:
                core = (
                    "evidence_schema_version",
                    "redaction_state",
                    "semantic_integrity_declaration",
                )
                indexed_re = re.compile(
                    r"^redaction_\w+_(file|field|reason|replacement_marker)$"
                )
                require_exact_field_set_with_indexed(
                    hname,
                    hfields,
                    core,
                    indexed_re,
                    errors,
                    allow_indexed=(hstate == "PRESENT"),
                )
                require_exact(hname, hfields, "semantic_integrity_declaration", "yes", errors)
                if hstate == "PRESENT":
                    indices: set[str] = set()
                    for match in re.finditer(r"redaction_(\w+)_reason", htext):
                        indices.add(match.group(1))
                    if not indices:
                        fail(
                            errors,
                            f"{hname}: redaction_state=PRESENT but no enumerated "
                            "redaction_<n>_* entries were found",
                        )
                    for idx in sorted(indices):
                        if not hfields.get(f"redaction_{idx}_file"):
                            fail(errors, f"{hname}: redaction_{idx}_file is required")
                        if not hfields.get(f"redaction_{idx}_field"):
                            fail(errors, f"{hname}: redaction_{idx}_field is required")
                        if not hfields.get(f"redaction_{idx}_reason"):
                            fail(errors, f"{hname}: redaction_{idx}_reason is required")
                        marker = hfields.get(f"redaction_{idx}_replacement_marker", "")
                        if not marker or "[REDACTED" not in marker.upper():
                            fail(
                                errors,
                                f"{hname}: redaction_{idx}_replacement_marker must be a "
                                "visible '[REDACTED: ...]' marker",
                            )
                        haystack = (
                            f"{hfields.get(f'redaction_{idx}_field', '')} "
                            f"{hfields.get(f'redaction_{idx}_reason', '')}"
                        ).lower()
                        for keyword in PROHIBITED_REDACTION_KEYWORDS:
                            if keyword in haystack:
                                fail(
                                    errors,
                                    f"{hname}: redaction_{idx} appears to redact a prohibited "
                                    f"category (matched {keyword!r}); commits, digests, exact "
                                    "commands, exit codes, outcome/build_status/failure_stage, "
                                    "proposed/intake verdicts, canonical_run, verdict_ceiling, "
                                    "artifact SHA-256/size, and independence statements must "
                                    "never be redacted",
                                )
                                break
    redaction_integrity_critical = False
    if "REDACTIONS_INDEX.txt" in file_fields and field_register.is_active_authority:
        redaction_integrity_critical = check_redactions_index(
            file_fields["REDACTIONS_INDEX.txt"],
            file_texts["REDACTIONS_INDEX.txt"],
            errors,
            expected_run_id=package_run_id,
            redactions_md_fields=file_fields.get("REDACTIONS.md"),
        )

    if "BUILD_EXIT_CODE.txt" in file_fields:
        check_build_exit_code(file_fields["BUILD_EXIT_CODE.txt"], errors, outcome)

    if "BUILD_ENVIRONMENT.txt" in file_fields and not placeholder_skip(
        "BUILD_ENVIRONMENT.txt",
        file_fields["BUILD_ENVIRONMENT.txt"],
        outcome,
        s2_shaped_package=s2_shaped,
    ):
        if not is_s2_not_applicable_terminal(file_fields["BUILD_ENVIRONMENT.txt"]):
            check_build_environment(file_fields["BUILD_ENVIRONMENT.txt"], errors, outcome)
    if "HOST_RUN_METADATA.txt" in file_texts:
        check_host_run_metadata_s2(file_texts["HOST_RUN_METADATA.txt"], errors)
    if "DOCKER_EXIT_CODE.txt" in file_fields:
        check_docker_exit_code(
            file_texts.get("DOCKER_EXIT_CODE.txt", ""), file_fields["DOCKER_EXIT_CODE.txt"], errors, outcome
        )
    if "BUILD_TIMING.txt" in file_fields:
        check_build_timing(file_fields["BUILD_TIMING.txt"], errors, outcome)
    if "ARTIFACT_IDENTITY.txt" in file_fields:
        check_artifact_identity(file_fields["ARTIFACT_IDENTITY.txt"], errors, outcome)

    static_inspection_incomplete = False
    if "STATIC_ARTIFACT_INSPECTION.txt" in file_fields:
        check_static_artifact_inspection(file_fields["STATIC_ARTIFACT_INSPECTION.txt"], errors, outcome)
        if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
            static_inspection_incomplete = file_fields["STATIC_ARTIFACT_INSPECTION.txt"].get(
                "inspection_complete"
            ) != "yes"

    # BUILD_EXIT_CODE.txt's own `status` must mirror static-inspection
    # completeness once an artifact is present (container contract: status
    # is FAILED — never OK — whenever inspection_complete=no).
    if outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT" and "BUILD_EXIT_CODE.txt" in file_fields:
        build_exit_status = file_fields["BUILD_EXIT_CODE.txt"].get("status")
        if static_inspection_incomplete and build_exit_status != "FAILED":
            fail(
                errors,
                "BUILD_EXIT_CODE.txt: status must be FAILED when static inspection is incomplete "
                "(verdict ceiling PARTIAL; PASS prohibited)",
            )
        if not static_inspection_incomplete and build_exit_status not in (None, "OK"):
            fail(errors, "BUILD_EXIT_CODE.txt: status must be OK when static inspection is complete")

    prohibited_reasons = detect_prohibited_violation(file_fields)
    identity_reasons = detect_identity_mismatch(file_fields)
    ceiling = compute_verdict_ceiling(
        outcome,
        bool(prohibited_reasons),
        bool(identity_reasons),
        static_inspection_incomplete,
        deviation_final_ceiling=deviation_ceiling,
        redaction_integrity_critical=redaction_integrity_critical,
    )

    # R6-M2 statement bindings require timing/deviation/redaction/ceiling peers.
    if "WITNESS_STATEMENT.md" in file_fields and field_register.is_active_authority:
        check_witness_statement(
            file_fields["WITNESS_STATEMENT.md"],
            errors,
            file_fields=file_fields,
            evidence_dir=evidence_dir,
            recomputed_ceiling=ceiling,
        )
    elif "WITNESS_STATEMENT.md" in file_fields:
        # Historical schemas: independence/product checks only (pre-R6 fields).
        hist_fields = file_fields["WITNESS_STATEMENT.md"]
        name = "WITNESS_STATEMENT.md"
        if not hist_fields.get("witness_identity_or_handle"):
            fail(errors, f"{name}: witness_identity_or_handle is required")
        require_exact(name, hist_fields, "not_package_owner", "yes", errors)
        require_exact(name, hist_fields, "not_owner_side_reproducer", "yes", errors)
        require_exact(name, hist_fields, "witness_controlled_host", "yes", errors)
        ai_used = hist_fields.get("ai_assistance_used", "")
        if ai_used not in ("yes", "no"):
            fail(errors, f"{name}: ai_assistance_used must be yes|no")
        elif ai_used == "yes" and not hist_fields.get("ai_assistance_detail"):
            fail(errors, f"{name}: ai_assistance_detail is required when ai_assistance_used=yes")
        require_exact(name, hist_fields, "human_review_completed", "yes", errors)
        require_exact(name, hist_fields, "product_executed", "NO", errors)
        require_exact(name, hist_fields, "ldd_used", "NO", errors)
        upstream = hist_fields.get("upstream_product_commands_not_run", "")
        if upstream and upstream != "yes":
            fail(errors, f"{name}: upstream_product_commands_not_run must be yes")

    if "WITNESS_VERDICT.md" in file_fields:
        check_witness_verdict(
            file_texts["WITNESS_VERDICT.md"],
            file_fields["WITNESS_VERDICT.md"],
            errors,
            outcome,
            ceiling,
            mode=selected_mode,
            file_fields=file_fields,
            evidence_dir=evidence_dir,
            statement_text=file_texts.get("WITNESS_STATEMENT.md"),
            enforce_r6_bindings=field_register.is_active_authority,
        )

    all_texts = collect_all_texts(evidence_dir)
    if "REDACTIONS_INDEX.txt" in file_fields:
        check_redaction_marker_consistency(
            all_texts, file_fields.get("REDACTIONS_INDEX.txt", {}), errors
        )
    elif "REDACTIONS.md" in file_fields and not field_register.is_active_authority:
        # Historical pre-R6 marker reconciliation against REDACTIONS.md declarations.
        hist_red = file_fields.get("REDACTIONS.md", {})
        state = hist_red.get("redaction_state", "")
        files_with_markers: dict[str, int] = {}
        for fname, text in all_texts.items():
            if fname in ("REDACTIONS.md", MANIFEST_NAME):
                continue
            count = len(REDACTION_MARKER_RE.findall(text))
            if count:
                files_with_markers[fname] = count
        if state == "NONE":
            for fname, count in sorted(files_with_markers.items()):
                fail(
                    errors,
                    f"REDACTIONS.md: redaction_state=NONE but {fname} contains {count} "
                    "'[REDACTED...]' marker(s)",
                )
        elif state == "PRESENT":
            declared_files: set[str] = set()
            for key, value in hist_red.items():
                if re.match(r"^redaction_\w+_file$", key) and value:
                    declared_files.add(value)
            for fname in sorted(files_with_markers):
                if fname not in declared_files:
                    fail(
                        errors,
                        f"REDACTIONS.md: {fname} contains a '[REDACTED...]' marker but no "
                        f"redaction_<n>_file entry declares {fname}",
                    )
            for fname in sorted(declared_files):
                if fname not in files_with_markers and fname in all_texts:
                    fail(
                        errors,
                        f"REDACTIONS.md: a redaction_<n>_file entry declares {fname} but no "
                        "'[REDACTED...]' marker was found in that file",
                    )

    check_completeness_state_machine(
        mode=selected_mode,
        s2_shaped=s2_shaped,
        evidence_dir=evidence_dir,
        post_build=file_fields.get("POST_BUILD_INTEGRITY.txt"),
        host_outcome=host_outcome_fields,
        errors=errors,
        register=field_register,
    )

    validate_manifest(
        evidence_dir,
        errors,
        mode=selected_mode,
        s2_shaped=s2_shaped,
        register=field_register,
    )

    if host_preliminary_mode and "POST_BUILD_INTEGRITY.txt" in file_fields:
        check_host_preliminary_post_build_subset(
            file_fields["POST_BUILD_INTEGRITY.txt"], host_outcome_fields, errors
        )

    if FINAL_BINDING_NAME in file_fields:
        check_weaver_forge_final_binding(
            file_fields[FINAL_BINDING_NAME],
            errors,
            evidence_dir,
            file_fields,
            outcome,
            mode=selected_mode,
        )

    # RC6-R3 cross-binding: run_id agreement across package/build/source/artifact/post-build.
    # Applies under the selected validation register whenever those fields are present.
    wfpi_fields = file_fields.get(PACKAGE_IDENTITY_NAME, {})
    build_exit_fields = file_fields.get("BUILD_EXIT_CODE.txt", {})
    wfpi_run_id = wfpi_fields.get("run_id", "")
    build_run_id = build_exit_fields.get("run_id", "")
    if wfpi_run_id and build_run_id and wfpi_run_id != build_run_id:
        fail(
            errors,
            f"{PACKAGE_IDENTITY_NAME} run_id={wfpi_run_id!r} must equal "
            f"BUILD_EXIT_CODE.txt run_id={build_run_id!r}",
        )
    anchor_run_id = wfpi_run_id or build_run_id
    for peer_name in (
        "SOURCE_IDENTITY.txt",
        "ARTIFACT_IDENTITY.txt",
        "POST_BUILD_INTEGRITY.txt",
    ):
        peer = file_fields.get(peer_name, {})
        peer_run_id = peer.get("run_id", "")
        if anchor_run_id and peer_run_id and peer_run_id != anchor_run_id:
            fail(
                errors,
                f"{peer_name} run_id={peer_run_id!r} must equal "
                f"package/build run_id={anchor_run_id!r}",
            )

    # Optional light check: evidence must not select a historical register authority.
    for fname, fields in file_fields.items():
        selected = fields.get("schema_register_version")
        if selected is None:
            continue
        if selected in HISTORICAL_REGISTER_VERSIONS or selected != ACTIVE_REGISTER_VERSION:
            fail(
                errors,
                f"{fname}: schema_register_version={selected!r} cannot select schema "
                f"authority (active authority is {ACTIVE_REGISTER_VERSION!r})",
            )

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Witness evidence structure (not truth). "
            "Modes: --host-preliminary (automated host structural checks) and "
            "--final-submission (final-shaped structural validation with Phase 4-S3 "
            "manifest totality and completeness rules for S2-shaped packages). "
            "Default with neither flag is a compatibility alias to final-submission. "
            "Structural PASS never claims Independent Witness PASS, final eligibility, "
            "READY, or rc5 readiness."
        )
    )
    parser.add_argument("evidence_dir", type=Path, help="Path to evidence directory")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--host-preliminary",
        action="store_true",
        help=(
            "Host-preliminary structural validation mode: enforce the automatable "
            "RC4B-017 POST_BUILD subset and require HOST_OUTCOME_INGESTION.txt; "
            "do not require WITNESS_STATEMENT.md, WITNESS_VERDICT.md, or final "
            "REDACTIONS.md; do not require evidence_inventory_complete=yes; reject "
            "evidence_inventory_complete=yes. Not final Witness validation and not "
            "Independent Witness PASS. preliminary_success_eligible remains NO."
        ),
    )
    mode_group.add_argument(
        "--final-submission",
        action="store_true",
        help=(
            "Final-submission structural validation mode: require final-shaped "
            "manual Witness inputs structurally; enforce S2-shaped total manifest "
            "closure and completeness finalization sequencing. Does not claim "
            "Independent Witness PASS, final eligibility, READY, or rc5 readiness."
        ),
    )
    parser.add_argument(
        "--schema-register-version",
        default=None,
        help=(
            "Explicit historical schema-register version for compatibility validation "
            f"(accepted: {sorted(HISTORICAL_REGISTER_VERSIONS)}). Default is active "
            f"{ACTIVE_REGISTER_VERSION}. Active version cannot be requested here."
        ),
    )
    args = parser.parse_args(argv)

    if args.host_preliminary:
        selected_mode = MODE_HOST_PRELIMINARY
    elif args.final_submission:
        selected_mode = MODE_FINAL_SUBMISSION
    else:
        selected_mode = DEFAULT_MODE_COMPATIBILITY_ALIAS

    errors = validate_dir(
        args.evidence_dir.resolve(),
        mode=selected_mode,
        schema_register_version=args.schema_register_version,
    )
    if errors:
        print("STRUCTURAL VALIDATION: FAIL")
        for e in errors:
            print(f"  - {e}")
        print(
            "\nStructural FAIL does not prove the run occurred, was independent, or was truthful."
        )
        return 1

    if selected_mode == MODE_HOST_PRELIMINARY:
        # Keep exact Phase 3F-B PASS suffix so host gate / coupled tests remain stable.
        mode_note = (
            " (host-preliminary structural PASS; not final Witness validation; "
            "not Independent Witness PASS; not final success eligibility)"
        )
    else:
        mode_note = (
            " (final-submission structural PASS; not Independent Witness PASS; "
            "not final eligibility; not READY; not rc5 readiness)"
        )
    print(f"STRUCTURAL VALIDATION: PASS{mode_note}")
    print(
        "Structural PASS does not prove execution, independence, or truthfulness."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
