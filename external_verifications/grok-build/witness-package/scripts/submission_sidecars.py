#!/usr/bin/env python3
"""RC6-R6 external append-only maintainer intake and correction sidecars (R6-I2).

Sidecars live outside the hashed evidence package at:
  external_verifications/grok-build/witness-submissions/<run_id>/MAINTAINER_INTAKE_LEDGER.txt
  external_verifications/grok-build/witness-submissions/<run_id>/CORRECTION_LEDGER_ENTRIES.txt

They must not mutate, repair, or reinterpret the original submitted package.
Integrity-critical correction proposals require a superseding package.
"""

from __future__ import annotations

import re
from pathlib import Path

MAINTAINER_INTAKE_LEDGER_NAME = "MAINTAINER_INTAKE_LEDGER.txt"
CORRECTION_LEDGER_ENTRIES_NAME = "CORRECTION_LEDGER_ENTRIES.txt"

INTAKE_DISPOSITIONS = frozenset(
    {
        "pending",
        "accepted",
        "rejected",
        "correction_requested",
        "disputed",
        "superseded",
    }
)

SUPERSESSION_RELATIONSHIPS = frozenset(
    {
        "ADDENDUM",
        "CLARIFICATION",
        "PARTIAL_SUPERSESSION",
        "FULL_SUPERSESSION",
        "REQUIRES_SUPERSEDING_PACKAGE",
    }
)

# Properties that cannot be silently corrected via sidecar alone.
INTEGRITY_CRITICAL_CORRECTION_TARGETS = frozenset(
    {
        "evidence",
        "verdict",
        "artifact",
        "manifest",
        "authoritative_tuple",
        "package_identity",
        "final_binding",
        "statement_identity",
        "deviation_package",
        "redaction_package",
        "machine_ceiling",
        "WITNESS_VERDICT.md",
        "WITNESS_STATEMENT.md",
        "DEVIATIONS.txt",
        "REDACTIONS.md",
        "REDACTIONS_INDEX.txt",
        "EVIDENCE_MANIFEST.sha256",
        "WEAVER_FORGE_FINAL_BINDING.txt",
        "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
        "ARTIFACT_IDENTITY.txt",
        "BUILD_EXIT_CODE.txt",
    }
)

ENTRY_BEGIN = "BEGIN_ENTRY"
ENTRY_END = "END_ENTRY"
SAFE_RUN_ID_RE = re.compile(r"^[a-zA-Z0-9._-]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def submissions_root_default(package_dir: Path) -> Path:
    """witness-package -> grok-build/witness-submissions."""
    return package_dir.parent / "witness-submissions"


def sidecar_dir_for_run(submissions_root: Path, run_id: str) -> Path:
    return submissions_root / run_id


def parse_append_entries(text: str) -> tuple[list[dict[str, str]], list[str]]:
    """Parse append-only BEGIN_ENTRY/END_ENTRY blocks of key=value lines."""
    errors: list[str] = []
    entries: list[dict[str, str]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue
        if line != ENTRY_BEGIN:
            errors.append(f"expected {ENTRY_BEGIN}, found {line!r}")
            i += 1
            continue
        i += 1
        fields: dict[str, str] = {}
        while i < len(lines) and lines[i].strip() != ENTRY_END:
            raw = lines[i].strip()
            i += 1
            if not raw or raw.startswith("#"):
                continue
            if "=" not in raw:
                errors.append(f"sidecar entry line missing '=': {raw!r}")
                continue
            key, _, value = raw.partition("=")
            key = key.strip()
            if key in fields:
                errors.append(f"duplicate sidecar key within entry: {key}")
            fields[key] = value
        if i >= len(lines) or lines[i].strip() != ENTRY_END:
            errors.append(f"sidecar entry missing {ENTRY_END}")
            break
        i += 1
        entries.append(fields)
    return entries, errors


def validate_maintainer_intake_ledger(
    text: str,
    *,
    expected_run_id: str,
    original_manifest_sha256: str | None = None,
) -> list[str]:
    """Validate external MAINTAINER_INTAKE_LEDGER.txt append-only grammar."""
    errors: list[str] = []
    name = MAINTAINER_INTAKE_LEDGER_NAME
    entries, parse_errors = parse_append_entries(text)
    errors.extend(f"{name}: {e}" for e in parse_errors)
    for idx, fields in enumerate(entries, start=1):
        run_id = fields.get("run_id", "")
        if run_id != expected_run_id:
            errors.append(
                f"{name}: entry {idx} run_id={run_id!r} must equal package run_id "
                f"{expected_run_id!r}"
            )
        disposition = fields.get("maintainer_intake_verdict", "")
        if disposition not in INTAKE_DISPOSITIONS:
            errors.append(
                f"{name}: entry {idx} maintainer_intake_verdict must be one of "
                f"{sorted(INTAKE_DISPOSITIONS)} (found {disposition!r})"
            )
        recorded = fields.get("recorded_utc", "")
        if not UTC_RE.fullmatch(recorded or ""):
            errors.append(f"{name}: entry {idx} recorded_utc must be YYYY-MM-DDTHH:MM:SSZ")
        if not fields.get("maintainer_identity"):
            errors.append(f"{name}: entry {idx} maintainer_identity is required")
        manifest = fields.get("original_evidence_manifest_sha256", "")
        if manifest and not SHA256_RE.fullmatch(manifest):
            errors.append(
                f"{name}: entry {idx} original_evidence_manifest_sha256 must be sha256 hex"
            )
        if (
            original_manifest_sha256
            and manifest
            and manifest != original_manifest_sha256
        ):
            errors.append(
                f"{name}: entry {idx} original_evidence_manifest_sha256 must equal the "
                "immutable submitted package manifest identity"
            )
        # Sidecar must not claim to rewrite package bytes.
        if fields.get("mutates_original_package", "no") != "no":
            errors.append(
                f"{name}: entry {idx} mutates_original_package must be no "
                "(submitted package remains immutable)"
            )
    return errors


def validate_correction_ledger_entries(
    text: str,
    *,
    expected_run_id: str,
) -> list[str]:
    """Validate CORRECTION_LEDGER_ENTRIES.txt; require superseding package when needed."""
    errors: list[str] = []
    name = CORRECTION_LEDGER_ENTRIES_NAME
    entries, parse_errors = parse_append_entries(text)
    errors.extend(f"{name}: {e}" for e in parse_errors)
    seen_ids: set[str] = set()
    for idx, fields in enumerate(entries, start=1):
        entry_id = fields.get("entry_id", "")
        if not entry_id:
            errors.append(f"{name}: entry {idx} entry_id is required")
        elif entry_id in seen_ids:
            errors.append(f"{name}: duplicate entry_id {entry_id!r}")
        else:
            seen_ids.add(entry_id)
        run_id = fields.get("original_run_id", "")
        if run_id != expected_run_id:
            errors.append(
                f"{name}: entry {idx} original_run_id={run_id!r} must equal "
                f"{expected_run_id!r}"
            )
        rel = fields.get("supersession_relationship", "")
        if rel not in SUPERSESSION_RELATIONSHIPS:
            errors.append(
                f"{name}: entry {idx} supersession_relationship must be one of "
                f"{sorted(SUPERSESSION_RELATIONSHIPS)} (found {rel!r})"
            )
        if fields.get("original_negative_evidence_preserved", "") != "yes":
            errors.append(
                f"{name}: entry {idx} original_negative_evidence_preserved must be yes"
            )
        if fields.get("mutates_original_package", "no") != "no":
            errors.append(
                f"{name}: entry {idx} mutates_original_package must be no"
            )
        affected = fields.get("affected_integrity_critical_properties", "")
        targets = {t.strip() for t in affected.split(",") if t.strip()}
        critical_hit = sorted(targets & INTEGRITY_CRITICAL_CORRECTION_TARGETS)
        if critical_hit and rel != "REQUIRES_SUPERSEDING_PACKAGE" and rel != "FULL_SUPERSESSION":
            errors.append(
                f"{name}: entry {idx} affects integrity-critical properties "
                f"{critical_hit}; sidecar alone is insufficient — require "
                "supersession_relationship=REQUIRES_SUPERSEDING_PACKAGE or FULL_SUPERSESSION "
                "with a new superseding package"
            )
        if rel == "REQUIRES_SUPERSEDING_PACKAGE" and not fields.get("superseding_run_id"):
            errors.append(
                f"{name}: entry {idx} REQUIRES_SUPERSEDING_PACKAGE needs superseding_run_id"
            )
        manifest = fields.get("original_evidence_manifest_sha256", "")
        if not SHA256_RE.fullmatch(manifest or ""):
            errors.append(
                f"{name}: entry {idx} original_evidence_manifest_sha256 must be sha256 hex"
            )
    return errors


def emit_empty_intake_ledger_header(run_id: str) -> str:
    return (
        f"# {MAINTAINER_INTAKE_LEDGER_NAME} — append-only maintainer intake sidecar\n"
        f"# Outside hashed evidence. run_id={run_id}\n"
        f"# Submitted WITNESS_VERDICT.md keeps maintainer_intake_verdict=pending forever.\n"
        f"# Later dispositions append here; they must not mutate the original package.\n"
    )


def emit_empty_correction_ledger_header(run_id: str) -> str:
    return (
        f"# {CORRECTION_LEDGER_ENTRIES_NAME} — append-only correction sidecar\n"
        f"# Outside hashed evidence. original_run_id={run_id}\n"
        f"# Corrections never rewrite the original immutable package.\n"
        f"# Integrity-critical property changes require a superseding package.\n"
    )
