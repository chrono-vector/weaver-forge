#!/usr/bin/env python3
"""RC6-R6 statement binding helpers (R6-M2 + RC4B-033/034 timing equality).

Computes statement_identity_sha256 over the fixed critical binding field set
(excluding statement_identity_sha256 itself) and validates timing-source
equality against BUILD_TIMING.txt. Uses only the Python standard library.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

# Canonical ordered critical binding fields that form statement identity.
# statement_identity_sha256 is excluded from the hashed payload (non-circular).
STATEMENT_IDENTITY_PAYLOAD_FIELDS: tuple[str, ...] = (
    "run_id",
    "package_identity_ref",
    "final_binding_ref",
    "authoritative_outcome",
    "artifact_sha256",
    "evidence_manifest_ref",
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
)

EXECUTION_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
EXECUTION_INSTANT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

FIXED_TIMING_SOURCE_FILE = "BUILD_TIMING.txt"
FIXED_TIMING_START_FIELD = "docker_started_utc"
FIXED_TIMING_END_FIELD = "docker_finished_utc"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_hex(text.encode("utf-8"))


def compute_statement_identity_sha256(fields: dict[str, str]) -> str:
    """Hash the fixed critical binding payload (excludes statement_identity_sha256)."""
    lines: list[str] = []
    for key in STATEMENT_IDENTITY_PAYLOAD_FIELDS:
        lines.append(f"{key}={fields.get(key, '')}")
    payload = "\n".join(lines) + "\n"
    return sha256_text(payload)


def parse_utc_instant(value: str) -> datetime | None:
    if not EXECUTION_INSTANT_RE.fullmatch(value or ""):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def validate_timing_grammar(
    *,
    execution_date_utc: str,
    execution_started_utc: str,
    execution_finished_utc: str,
    source_file: str,
    source_start_field: str,
    source_end_field: str,
) -> list[str]:
    """Fail-closed grammar/source/relation checks for statement timing fields."""
    errors: list[str] = []
    if source_file != FIXED_TIMING_SOURCE_FILE:
        errors.append(
            "execution_timing_source_file must equal BUILD_TIMING.txt "
            f"(found {source_file!r})"
        )
    if source_start_field != FIXED_TIMING_START_FIELD:
        errors.append(
            "execution_timing_source_start_field must equal docker_started_utc "
            f"(found {source_start_field!r})"
        )
    if source_end_field != FIXED_TIMING_END_FIELD:
        errors.append(
            "execution_timing_source_end_field must equal docker_finished_utc "
            f"(found {source_end_field!r})"
        )
    if not EXECUTION_DATE_RE.fullmatch(execution_date_utc or ""):
        errors.append(
            "execution_date_utc must be YYYY-MM-DD "
            f"(found {execution_date_utc!r})"
        )
    started = parse_utc_instant(execution_started_utc)
    finished = parse_utc_instant(execution_finished_utc)
    if started is None:
        errors.append(
            "execution_started_utc must be YYYY-MM-DDTHH:MM:SSZ "
            f"(found {execution_started_utc!r})"
        )
    if finished is None:
        errors.append(
            "execution_finished_utc must be YYYY-MM-DDTHH:MM:SSZ "
            f"(found {execution_finished_utc!r})"
        )
    if started is not None and finished is not None:
        if started > finished:
            errors.append(
                "execution_started_utc must be less than or equal to execution_finished_utc"
            )
        if EXECUTION_DATE_RE.fullmatch(execution_date_utc or ""):
            if execution_date_utc != execution_started_utc[:10]:
                errors.append(
                    "execution_date_utc must equal the date portion of execution_started_utc"
                )
    return errors


def validate_timing_equality_against_build_timing(
    *,
    execution_started_utc: str,
    execution_finished_utc: str,
    build_timing_fields: dict[str, str],
) -> list[str]:
    """Equality-bind statement timing to BUILD_TIMING.txt authoritative fields."""
    errors: list[str] = []
    docker_started = build_timing_fields.get(FIXED_TIMING_START_FIELD, "")
    docker_finished = build_timing_fields.get(FIXED_TIMING_END_FIELD, "")
    if not docker_started:
        errors.append("BUILD_TIMING.txt docker_started_utc is missing")
    if not docker_finished:
        errors.append("BUILD_TIMING.txt docker_finished_utc is missing")
    if docker_started and execution_started_utc != docker_started:
        errors.append(
            "execution_started_utc must equal BUILD_TIMING.txt docker_started_utc "
            f"(statement={execution_started_utc!r} timing={docker_started!r})"
        )
    if docker_finished and execution_finished_utc != docker_finished:
        errors.append(
            "execution_finished_utc must equal BUILD_TIMING.txt docker_finished_utc "
            f"(statement={execution_finished_utc!r} timing={docker_finished!r})"
        )
    return errors
