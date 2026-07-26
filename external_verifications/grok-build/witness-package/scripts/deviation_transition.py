#!/usr/bin/env python3
"""RC6-R5 deviation transition and validator-authoritative ceiling helpers.

Implements the fixed R5-D1 preliminary→final transition and R5-C3 machine-ceiling
recomputation. Uses only the Python standard library.

Host preliminary DEVIATIONS bytes are emitted by emit_host_preliminary_deviations_bytes,
which mirrors the active Host STEP-8 writer in run_witness_narrow_build.sh.
"""

from __future__ import annotations

import hashlib
import re
from typing import Iterable

DEVIATION_SEVERITY_VALUES = frozenset(
    {"NONE", "NONMATERIAL_DISCLOSED", "MATERIAL_NONCANONICAL", "PROHIBITED"}
)
VERDICT_VALUES = frozenset({"PASS", "PARTIAL", "FAIL", "INDETERMINATE"})

# Strictness: lower rank wins (stricter).
SEVERITY_RANK = {
    "NONE": 0,
    "NONMATERIAL_DISCLOSED": 1,
    "MATERIAL_NONCANONICAL": 2,
    "PROHIBITED": 3,
}
CEILING_RANK = {
    "PASS": 3,
    "PARTIAL": 2,
    "INDETERMINATE": 1,
    "FAIL": 0,
}

# Identity overrides that force FAIL ceiling (RC4B-007 / R5-C3).
FAIL_CEILING_IDENTITY_FIELDS = frozenset(
    {
        "WEAVER_FORGE_URL",
        "WEAVER_FORGE_TAG",
        "GROK_BUILD_URL",
        "GROK_BUILD_COMMIT",
        "RUST_IMAGE",
        "EXPECTED_CARGO_LOCK_SHA256",
        "BUILD_CMD",
        "EXPECTED_RUSTC_VERSION",
        "EXPECTED_DOTSLASH_VERSION",
    }
)

TOOLCHAIN_FAIL_FIELDS = frozenset(
    {"EXPECTED_RUSTC_VERSION", "EXPECTED_DOTSLASH_VERSION", "RUST_IMAGE"}
)

_CHANGED_FIELD_RE = re.compile(
    r"([A-Z][A-Z0-9_]*)\s*:\s*canonical='([^']*)'\s*effective='([^']*)'"
)


class DeviationTransitionError(ValueError):
    """Fail-closed deviation transition or ceiling disagreement."""


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def emit_host_preliminary_deviations_bytes(
    *,
    changed_identity_fields: Iterable[str] | None = None,
) -> bytes:
    """Emit Host preliminary DEVIATIONS.txt bytes matching the active Host writer.

    ``changed_identity_fields`` entries must already be formatted as:
    ``FIELD: canonical='...' effective='...'``
    (the same strings the Host script appends to CHANGED_IDENTITY_FIELDS).
    """
    changed = list(changed_identity_fields or [])
    lines = ["evidence_schema_version=1"]
    if changed:
        disclosure = "".join(f"{item}; " for item in changed)
        lines.extend(
            [
                "deviation_state=PRESENT",
                f"deviation_count={len(changed)}",
                f"automated_summary=noncanonical_identity_fields_changed:{disclosure}",
            ]
        )
    else:
        lines.extend(
            [
                "deviation_state=NONE",
                "deviation_count=0",
                "automated_summary=no_automated_identity_deviations",
            ]
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_kv_bytes(data: bytes) -> dict[str, str]:
    text = data.decode("utf-8")
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        fields[key] = value
    return fields


def parse_changed_identity_entries(automated_summary: str) -> list[tuple[str, str, str]]:
    """Parse Host automated_summary into (field, canonical, effective) triples."""
    if automated_summary == "no_automated_identity_deviations":
        return []
    prefix = "noncanonical_identity_fields_changed:"
    if not automated_summary.startswith(prefix):
        raise DeviationTransitionError(
            f"unsupported preliminary automated_summary: {automated_summary!r}"
        )
    body = automated_summary[len(prefix) :]
    entries = _CHANGED_FIELD_RE.findall(body)
    if not entries:
        raise DeviationTransitionError(
            "preliminary automated_summary declares noncanonical changes but "
            "no parseable FIELD: canonical='...' effective='...' entries were found"
        )
    return [(name, canonical, effective) for name, canonical, effective in entries]


def severity_ceiling_for_identity_field(field_name: str) -> tuple[str, str, str]:
    """Return (severity, canonical_identity_impact, per_entry_ceiling)."""
    if field_name in FAIL_CEILING_IDENTITY_FIELDS:
        # Toolchain / image / other identity overrides: FAIL-cap (RC4B-007 / R5-C3).
        severity = "PROHIBITED" if field_name in TOOLCHAIN_FAIL_FIELDS else "MATERIAL_NONCANONICAL"
        return severity, "yes", "FAIL"
    # Unknown disclosed field: material noncanonical, no silent PASS.
    return "MATERIAL_NONCANONICAL", "yes", "FAIL"


def ceiling_required_by_severity(severity: str) -> str:
    if severity == "PROHIBITED":
        return "FAIL"
    if severity == "MATERIAL_NONCANONICAL":
        return "FAIL"
    if severity == "NONMATERIAL_DISCLOSED":
        return "PARTIAL"
    if severity == "NONE":
        return "PASS"
    raise DeviationTransitionError(f"unknown severity: {severity!r}")


def strictest_ceiling(*ceilings: str) -> str:
    chosen = "PASS"
    for ceiling in ceilings:
        if ceiling not in CEILING_RANK:
            raise DeviationTransitionError(f"unknown ceiling: {ceiling!r}")
        if CEILING_RANK[ceiling] < CEILING_RANK[chosen]:
            chosen = ceiling
    return chosen


def strictest_severity(*severities: str) -> str:
    chosen = "NONE"
    for severity in severities:
        if severity not in SEVERITY_RANK:
            raise DeviationTransitionError(f"unknown severity: {severity!r}")
        if SEVERITY_RANK[severity] > SEVERITY_RANK[chosen]:
            chosen = severity
    return chosen


def recompute_aggregates_from_entries(
    entries: list[dict[str, str]],
) -> tuple[str, str, str]:
    """Return (aggregate_severity, aggregate_canonical_identity_impact, final_machine_ceiling)."""
    if not entries:
        return "NONE", "no", "PASS"
    aggregate_severity = strictest_severity(*(e["severity"] for e in entries))
    aggregate_impact = (
        "yes" if any(e.get("canonical_identity_impact") == "yes" for e in entries) else "no"
    )
    entry_ceilings = [e["verdict_ceiling"] for e in entries]
    severity_caps = [ceiling_required_by_severity(e["severity"]) for e in entries]
    final_ceiling = strictest_ceiling(*entry_ceilings, *severity_caps)
    # NONMATERIAL_DISCLOSED may never leave aggregate above PARTIAL.
    if aggregate_severity == "NONMATERIAL_DISCLOSED":
        final_ceiling = strictest_ceiling(final_ceiling, "PARTIAL")
    return aggregate_severity, aggregate_impact, final_ceiling


def transition_preliminary_to_final(
    *,
    preliminary_bytes: bytes,
    run_id: str,
) -> str:
    """Convert Host preliminary DEVIATIONS bytes into a truthful final indexed package."""
    if not run_id or any(ch in run_id for ch in ("/", "\\", " ", "..")):
        raise DeviationTransitionError(f"invalid run_id for deviation transition: {run_id!r}")
    prelim = parse_kv_bytes(preliminary_bytes)
    required_prelim = (
        "evidence_schema_version",
        "deviation_state",
        "deviation_count",
        "automated_summary",
    )
    missing = [k for k in required_prelim if k not in prelim]
    if missing:
        raise DeviationTransitionError(f"preliminary DEVIATIONS missing keys: {missing}")
    unknown = sorted(set(prelim) - set(required_prelim))
    if unknown:
        raise DeviationTransitionError(f"preliminary DEVIATIONS unknown keys: {unknown}")
    if prelim.get("evidence_schema_version") != "1":
        raise DeviationTransitionError("preliminary evidence_schema_version must be 1")

    state = prelim["deviation_state"]
    count_raw = prelim["deviation_count"]
    if not count_raw.isdigit():
        raise DeviationTransitionError("preliminary deviation_count must be a non-negative integer")
    count = int(count_raw)
    summary = prelim["automated_summary"]
    transition_ref = sha256_hex(preliminary_bytes)

    if state == "NONE":
        if count != 0:
            raise DeviationTransitionError("preliminary NONE requires deviation_count=0")
        if summary != "no_automated_identity_deviations":
            raise DeviationTransitionError(
                "preliminary NONE requires automated_summary=no_automated_identity_deviations"
            )
        lines = [
            "evidence_schema_version=1",
            f"run_id={run_id}",
            "deviation_state=NONE",
            "deviation_count=0",
            f"preliminary_deviations_sha256={transition_ref}",
            "aggregate_severity=NONE",
            "aggregate_canonical_identity_impact=no",
            "final_machine_ceiling=PASS",
        ]
        return "\n".join(lines) + "\n"

    if state != "PRESENT":
        raise DeviationTransitionError(f"invalid preliminary deviation_state: {state!r}")
    if count < 1:
        raise DeviationTransitionError("preliminary PRESENT requires deviation_count>=1")

    parsed = parse_changed_identity_entries(summary)
    if len(parsed) != count:
        raise DeviationTransitionError(
            f"preliminary deviation_count={count} does not match parsed changed-field "
            f"entries {len(parsed)}"
        )

    entries: list[dict[str, str]] = []
    for idx, (field_name, canonical, effective) in enumerate(parsed, start=1):
        severity, impact, ceiling = severity_ceiling_for_identity_field(field_name)
        description = (
            f"host_identity_override:{field_name}:canonical={canonical}:effective={effective}"
        )
        entries.append(
            {
                "index": str(idx),
                "description": description,
                "severity": severity,
                "canonical_identity_impact": impact,
                "verdict_ceiling": ceiling,
                "field_name": field_name,
            }
        )

    aggregate_severity, aggregate_impact, final_ceiling = recompute_aggregates_from_entries(
        entries
    )
    lines = [
        "evidence_schema_version=1",
        f"run_id={run_id}",
        "deviation_state=PRESENT",
        f"deviation_count={len(entries)}",
        f"preliminary_deviations_sha256={transition_ref}",
        f"aggregate_severity={aggregate_severity}",
        f"aggregate_canonical_identity_impact={aggregate_impact}",
        f"final_machine_ceiling={final_ceiling}",
    ]
    for entry in entries:
        n = entry["index"]
        lines.extend(
            [
                f"deviation_{n}_description={entry['description']}",
                f"deviation_{n}_severity={entry['severity']}",
                f"deviation_{n}_canonical_identity_impact={entry['canonical_identity_impact']}",
                f"deviation_{n}_verdict_ceiling={entry['verdict_ceiling']}",
            ]
        )
    return "\n".join(lines) + "\n"


def extract_indexed_entries(fields: dict[str, str]) -> list[dict[str, str]]:
    """Extract contiguous numeric indexed deviation entries from final fields."""
    indices: set[int] = set()
    orphan_keys: list[str] = []
    indexed_re = re.compile(
        r"^deviation_(\d+)_(description|severity|canonical_identity_impact|verdict_ceiling)$"
    )
    non_numeric_indexed = re.compile(
        r"^deviation_(\w+)_(description|severity|canonical_identity_impact|verdict_ceiling)$"
    )
    for key in fields:
        m = indexed_re.match(key)
        if m:
            indices.add(int(m.group(1)))
            continue
        m2 = non_numeric_indexed.match(key)
        if m2 and not m2.group(1).isdigit():
            orphan_keys.append(key)
    if orphan_keys:
        raise DeviationTransitionError(
            f"non-numeric or malformed indexed deviation keys: {sorted(orphan_keys)}"
        )
    if not indices:
        return []
    expected = set(range(1, max(indices) + 1))
    if indices != expected:
        raise DeviationTransitionError(
            f"deviation IDs must be contiguous 1..n; found {sorted(indices)}"
        )
    entries: list[dict[str, str]] = []
    for idx in range(1, max(indices) + 1):
        prefix = f"deviation_{idx}_"
        needed = (
            "description",
            "severity",
            "canonical_identity_impact",
            "verdict_ceiling",
        )
        missing = [k for k in needed if f"{prefix}{k}" not in fields]
        if missing:
            raise DeviationTransitionError(f"deviation_{idx} missing keys: {missing}")
        entries.append(
            {
                "index": str(idx),
                "description": fields[f"{prefix}description"],
                "severity": fields[f"{prefix}severity"],
                "canonical_identity_impact": fields[f"{prefix}canonical_identity_impact"],
                "verdict_ceiling": fields[f"{prefix}verdict_ceiling"],
            }
        )
    return entries


def verify_final_package_consistency(
    fields: dict[str, str],
    *,
    expected_run_id: str | None = None,
) -> list[str]:
    """Validator-side consistency checks for an R5 final DEVIATIONS package."""
    errors: list[str] = []
    core = {
        "evidence_schema_version",
        "run_id",
        "deviation_state",
        "deviation_count",
        "preliminary_deviations_sha256",
        "aggregate_severity",
        "aggregate_canonical_identity_impact",
        "final_machine_ceiling",
    }
    indexed_re = re.compile(
        r"^deviation_\d+_(description|severity|canonical_identity_impact|verdict_ceiling)$"
    )
    unknown = sorted(k for k in fields if k not in core and not indexed_re.match(k))
    if unknown:
        errors.append(f"DEVIATIONS.txt: unknown key(s): {unknown}")

    state = fields.get("deviation_state", "")
    if state not in ("NONE", "PRESENT"):
        errors.append("DEVIATIONS.txt: deviation_state must be NONE or PRESENT")
        return errors

    if expected_run_id is not None and fields.get("run_id") != expected_run_id:
        errors.append(
            f"DEVIATIONS.txt: run_id {fields.get('run_id')!r} does not match package "
            f"run_id {expected_run_id!r}"
        )

    ref = fields.get("preliminary_deviations_sha256", "")
    if not re.fullmatch(r"[0-9a-f]{64}", ref or ""):
        errors.append(
            "DEVIATIONS.txt: preliminary_deviations_sha256 must be a 64-char lowercase hex digest"
        )

    count_raw = fields.get("deviation_count", "")
    if not (count_raw or "").isdigit():
        errors.append("DEVIATIONS.txt: deviation_count must be a non-negative integer")
        return errors
    count = int(count_raw)

    try:
        entries = extract_indexed_entries(fields) if state == "PRESENT" else []
    except DeviationTransitionError as exc:
        errors.append(f"DEVIATIONS.txt: {exc}")
        return errors

    if state == "NONE":
        if count != 0:
            errors.append("DEVIATIONS.txt: deviation_state=NONE requires deviation_count=0")
        if entries:
            errors.append("DEVIATIONS.txt: deviation_state=NONE forbids indexed deviation keys")
    else:
        if count < 1:
            errors.append("DEVIATIONS.txt: deviation_state=PRESENT requires deviation_count>=1")
        if count != len(entries):
            errors.append(
                f"DEVIATIONS.txt: deviation_count={count} does not match enumerated "
                f"contiguous entries {len(entries)}"
            )

    for entry in entries:
        idx = entry["index"]
        if entry["severity"] not in DEVIATION_SEVERITY_VALUES:
            errors.append(
                f"DEVIATIONS.txt: deviation_{idx}_severity must be one of "
                f"{sorted(DEVIATION_SEVERITY_VALUES)}"
            )
        if entry["canonical_identity_impact"] not in ("yes", "no"):
            errors.append(
                f"DEVIATIONS.txt: deviation_{idx}_canonical_identity_impact must be yes|no"
            )
        if entry["verdict_ceiling"] not in VERDICT_VALUES:
            errors.append(
                f"DEVIATIONS.txt: deviation_{idx}_verdict_ceiling must be one of "
                f"{sorted(VERDICT_VALUES)}"
            )
            continue
        required = ceiling_required_by_severity(entry["severity"])
        if CEILING_RANK[entry["verdict_ceiling"]] > CEILING_RANK[required]:
            errors.append(
                f"DEVIATIONS.txt: deviation_{idx}_verdict_ceiling {entry['verdict_ceiling']} "
                f"exceeds severity cap {required} for {entry['severity']}"
            )
        if entry["severity"] == "PROHIBITED" and entry["verdict_ceiling"] != "FAIL":
            errors.append(
                f"DEVIATIONS.txt: deviation_{idx}_severity=PROHIBITED requires "
                "verdict_ceiling=FAIL"
            )

    try:
        agg_sev, agg_impact, final_ceiling = recompute_aggregates_from_entries(entries)
    except DeviationTransitionError as exc:
        errors.append(f"DEVIATIONS.txt: {exc}")
        return errors

    if fields.get("aggregate_severity") != agg_sev:
        errors.append(
            f"DEVIATIONS.txt: aggregate_severity {fields.get('aggregate_severity')!r} "
            f"disagrees with recomputed {agg_sev!r}"
        )
    if fields.get("aggregate_canonical_identity_impact") != agg_impact:
        errors.append(
            "DEVIATIONS.txt: aggregate_canonical_identity_impact "
            f"{fields.get('aggregate_canonical_identity_impact')!r} disagrees with "
            f"recomputed {agg_impact!r}"
        )
    if fields.get("final_machine_ceiling") != final_ceiling:
        errors.append(
            f"DEVIATIONS.txt: final_machine_ceiling {fields.get('final_machine_ceiling')!r} "
            f"disagrees with recomputed {final_ceiling!r}"
        )
    return errors


def verify_deviation_transition(
    *,
    preliminary_bytes: bytes,
    final_text: str,
    run_id: str,
) -> list[str]:
    """Verify final package is exactly the truthful transition of preliminary bytes."""
    errors: list[str] = []
    try:
        expected = transition_preliminary_to_final(
            preliminary_bytes=preliminary_bytes, run_id=run_id
        )
    except DeviationTransitionError as exc:
        return [f"DEVIATIONS.txt transition: {exc}"]

    # Normalize newlines for comparison.
    got = final_text.replace("\r\n", "\n")
    exp = expected.replace("\r\n", "\n")
    if got != exp:
        # Detailed disagreement categories for fail-closed diagnostics.
        got_fields = parse_kv_bytes(got.encode("utf-8"))
        exp_fields = parse_kv_bytes(exp.encode("utf-8"))
        for key in sorted(set(exp_fields) | set(got_fields)):
            if key not in got_fields:
                errors.append(f"DEVIATIONS.txt transition: dropped key {key}")
            elif key not in exp_fields:
                errors.append(f"DEVIATIONS.txt transition: invented key {key}")
            elif got_fields[key] != exp_fields[key]:
                errors.append(
                    f"DEVIATIONS.txt transition: changed key {key}: "
                    f"expected {exp_fields[key]!r} found {got_fields[key]!r}"
                )
        if not errors:
            errors.append(
                "DEVIATIONS.txt transition: final package bytes disagree with "
                "authoritative transition output"
            )
    return errors


def recompute_machine_ceiling(
    *,
    outcome: str | None,
    prohibited: bool,
    identity_mismatch: bool,
    static_inspection_incomplete: bool,
    deviation_final_ceiling: str | None = None,
) -> str:
    """Validator-authoritative machine ceiling (R5-C3). Strictest input wins."""
    if prohibited:
        base = "FAIL"
    elif identity_mismatch:
        base = "FAIL"
    elif outcome in ("CARGO_FAILED", "CARGO_SUCCEEDED_ARTIFACT_MISSING"):
        base = "FAIL"
    elif outcome in ("BUILD_NOT_STARTED", "INFRASTRUCTURE_FAILURE") or outcome is None:
        base = "INDETERMINATE"
    elif outcome == "CARGO_SUCCEEDED_ARTIFACT_PRESENT":
        base = "PARTIAL" if static_inspection_incomplete else "PASS"
    else:
        base = "INDETERMINATE"

    if deviation_final_ceiling:
        return strictest_ceiling(base, deviation_final_ceiling)
    return base
