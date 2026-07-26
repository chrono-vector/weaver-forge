#!/usr/bin/env python3
"""RC6-R6 paired redaction index helpers (R6-RD2).

Machine-readable REDACTIONS_INDEX.txt grammar, category enforcement, contiguous
IDs, original-value SHA-256 checks, and exact marker-entry identity
reconciliation. Uses only the Python standard library.
"""

from __future__ import annotations

import re
from typing import Iterable

REDACTION_CATEGORIES = frozenset(
    {
        "FILESYSTEM_PATH",
        "HOME_PATH_IDENTIFIER",
        "COMMAND_TEXT",
        "CAPTURED_COMMAND_OUTPUT",
    }
)

# Categories that are integrity-critical when used to obscure command/authority
# content. COMMAND_TEXT is never a permitted successful redaction of build
# command authority; CAPTURED_COMMAND_OUTPUT may redact only nonmaterial path
# identifiers inside captured output and still fails when targeting prohibited
# integrity keywords.
INTEGRITY_CRITICAL_CATEGORIES = frozenset({"COMMAND_TEXT"})

# Physical marker scanner (any [REDACTED...] token). Active rc6.5 PRESENT entries
# must additionally satisfy CATEGORY_BEARING_MARKER_RE.
REDACTION_MARKER_RE = re.compile(r"\[REDACTED[^\]]*\]")
# Authorized active rc6.5 PRESENT grammar (exact; no aliases / case folding):
# [REDACTED:<CATEGORY>:<marker-id>]
_CATEGORY_ALT = "|".join(
    (
        "FILESYSTEM_PATH",
        "HOME_PATH_IDENTIFIER",
        "COMMAND_TEXT",
        "CAPTURED_COMMAND_OUTPUT",
    )
)
CATEGORY_BEARING_MARKER_RE = re.compile(
    rf"^\[REDACTED:({_CATEGORY_ALT}):([^\]:\s][^\]:]*)]$"
)
INDEXED_KEY_RE = re.compile(
    r"^redaction_(\d+)_(file|field|category|original_value_sha256|replacement_marker)$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
KV_LINE_RE = re.compile(r"^([A-Za-z0-9_.-]+)=(.*)$")


def parse_category_bearing_marker(marker: str) -> tuple[str | None, str | None, str | None]:
    """Parse authorized [REDACTED:<CATEGORY>:<marker-id>] grammar.

    Returns (category, marker_id, error). On success error is None.
    """
    if not marker:
        return None, None, "replacement_marker is empty"
    match = CATEGORY_BEARING_MARKER_RE.fullmatch(marker)
    if not match:
        return (
            None,
            None,
            "replacement_marker must exactly match "
            "[REDACTED:<CATEGORY>:<marker-id>] with CATEGORY one of "
            f"{sorted(REDACTION_CATEGORIES)} (no aliases, no case folding)",
        )
    category, marker_id = match.group(1), match.group(2)
    if category not in REDACTION_CATEGORIES:
        return None, None, f"unknown category token {category!r} in replacement_marker"
    return category, marker_id, None

# Integrity-critical targets/keywords (extend R5 prohibited redaction floor).
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
    "final_machine_ceiling",
    "authoritative_outcome",
    "run_id",
    "package_tag",
    "peeled_commit",
    "tag_object",
    "manifest",
    "deviation_state",
    "redaction_state",
)


def discover_redaction_indices(fields: dict[str, str]) -> list[int]:
    indices: set[int] = set()
    for key in fields:
        match = INDEXED_KEY_RE.fullmatch(key)
        if match:
            indices.add(int(match.group(1)))
    return sorted(indices)


def validate_redaction_index_fields(
    fields: dict[str, str],
    *,
    name: str = "REDACTIONS_INDEX.txt",
) -> tuple[list[str], bool]:
    """Validate machine index structure. Returns (errors, integrity_critical_fail)."""
    errors: list[str] = []
    integrity_critical = False
    state = fields.get("redaction_state", "")
    if state not in ("NONE", "PRESENT"):
        errors.append(f"{name}: redaction_state must be NONE or PRESENT")
        return errors, False

    count_raw = fields.get("redaction_count", "")
    if not re.fullmatch(r"\d+", count_raw or ""):
        errors.append(f"{name}: redaction_count must be a non-negative integer")
        return errors, False
    count = int(count_raw)

    indices = discover_redaction_indices(fields)
    if state == "NONE":
        if count != 0:
            errors.append(f"{name}: redaction_state=NONE requires redaction_count=0")
        if indices:
            errors.append(
                f"{name}: redaction_state=NONE forbids indexed redaction_<n>_* entries"
            )
        return errors, False

    # PRESENT
    if count < 1:
        errors.append(f"{name}: redaction_state=PRESENT requires redaction_count>=1")
    expected = list(range(1, count + 1)) if count >= 1 else []
    if indices != expected:
        errors.append(
            f"{name}: indexed redaction IDs must be contiguous 1..redaction_count "
            f"(expected {expected}, found {indices})"
        )

    for idx in indices:
        prefix = f"redaction_{idx}_"
        file_v = fields.get(prefix + "file", "")
        field_v = fields.get(prefix + "field", "")
        category = fields.get(prefix + "category", "")
        orig = fields.get(prefix + "original_value_sha256", "")
        marker = fields.get(prefix + "replacement_marker", "")
        if not file_v:
            errors.append(f"{name}: {prefix}file is required")
        if not field_v:
            errors.append(f"{name}: {prefix}field is required")
        if not category:
            errors.append(f"{name}: {prefix}category is required")
        elif category not in REDACTION_CATEGORIES:
            errors.append(
                f"{name}: {prefix}category unknown {category!r}; "
                f"allowed={sorted(REDACTION_CATEGORIES)}"
            )
        if not orig:
            errors.append(f"{name}: {prefix}original_value_sha256 is required")
        elif not SHA256_RE.fullmatch(orig):
            errors.append(
                f"{name}: {prefix}original_value_sha256 must be 64-char lowercase hex"
            )
        parsed_cat, _marker_id, marker_err = parse_category_bearing_marker(marker)
        if marker_err:
            errors.append(f"{name}: {prefix}replacement_marker {marker_err}")
        elif parsed_cat != category and category in REDACTION_CATEGORIES:
            errors.append(
                f"{name}: {prefix}replacement_marker category token {parsed_cat!r} "
                f"must exactly equal {prefix}category={category!r}"
            )

        haystack = f"{field_v} {category}".lower()
        for keyword in PROHIBITED_REDACTION_KEYWORDS:
            if keyword in haystack:
                errors.append(
                    f"{name}: redaction_{idx} improperly redacts integrity-critical "
                    f"content (matched {keyword!r})"
                )
                integrity_critical = True
                break
        if category in INTEGRITY_CRITICAL_CATEGORIES:
            errors.append(
                f"{name}: redaction_{idx} category={category} is integrity-critical "
                "and is rejected for structural submission"
            )
            integrity_critical = True

    return errors, integrity_critical


def count_markers(text: str) -> int:
    return len(REDACTION_MARKER_RE.findall(text or ""))


def _parse_kv_map(text: str) -> dict[str, str]:
    """Parse key=value lines; first occurrence wins (duplicates reported elsewhere)."""
    result: dict[str, str] = {}
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("|"):
            continue
        match = KV_LINE_RE.fullmatch(line)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        if key not in result:
            result[key] = value
    return result


def _field_value(text: str, field: str) -> str | None:
    """Return the exact field/section value when present as a KV key."""
    if not field:
        return None
    values = _parse_kv_map(text)
    if field in values:
        return values[field]
    return None


def reconcile_markers(
    *,
    index_fields: dict[str, str],
    all_texts: dict[str, str],
    exclude_names: Iterable[str] = (),
) -> list[str]:
    """Exact per-entry identity reconciliation (file/field/category/marker).

    Each indexed entry must bind to exactly one physical marker occurrence at the
    declared file and field/section. Rejects relocation, category/file/field/
    marker substitution, duplicate-marker ambiguity, one-to-many matches, orphans,
    and within-file entry swapping.
    """
    errors: list[str] = []
    name = "REDACTIONS_INDEX.txt"
    state = index_fields.get("redaction_state", "")
    exclude = set(exclude_names) | {name, "REDACTIONS.md", "EVIDENCE_MANIFEST.sha256"}

    # Physical marker occurrences: (fname, start, end, marker_text)
    physical: list[tuple[str, int, int, str]] = []
    for fname, text in sorted(all_texts.items()):
        if fname in exclude:
            continue
        for match in REDACTION_MARKER_RE.finditer(text or ""):
            physical.append((fname, match.start(), match.end(), match.group(0)))

    if state == "NONE":
        for fname, start, _end, marker in physical:
            errors.append(
                f"{name}: redaction_state=NONE but {fname} contains "
                f"unindexed marker {marker!r}"
            )
        return errors

    if state != "PRESENT":
        return errors

    indices = discover_redaction_indices(index_fields)
    entries: list[dict[str, str | int]] = []
    identity_seen: dict[tuple[str, str, str, str], int] = {}
    location_seen: dict[tuple[str, str, str], list[int]] = {}

    for idx in indices:
        fname = index_fields.get(f"redaction_{idx}_file", "")
        field = index_fields.get(f"redaction_{idx}_field", "")
        category = index_fields.get(f"redaction_{idx}_category", "")
        marker = index_fields.get(f"redaction_{idx}_replacement_marker", "")
        if not fname or not field or not category or not marker:
            # Structural gaps already reported by validate_redaction_index_fields.
            continue
        identity = (fname, field, category, marker)
        if identity in identity_seen:
            errors.append(
                f"{name}: duplicate indexed entry identity for redaction_{idx} "
                f"conflicts with redaction_{identity_seen[identity]} "
                f"(file/field/category/marker)"
            )
        else:
            identity_seen[identity] = idx
        loc = (fname, field, marker)
        location_seen.setdefault(loc, []).append(idx)
        entries.append(
            {
                "idx": idx,
                "file": fname,
                "field": field,
                "category": category,
                "marker": marker,
            }
        )

    for loc, idxs in sorted(location_seen.items()):
        if len(idxs) > 1:
            errors.append(
                f"{name}: file/field/marker location {loc!r} claimed by multiple "
                f"index entries {idxs}; category substitution or duplicate binding "
                "is rejected"
            )

    # Assign each entry to exactly one physical occurrence at the declared field.
    claimed_physical: dict[tuple[str, int, int], int] = {}
    for entry in entries:
        idx = int(entry["idx"])
        fname = str(entry["file"])
        field = str(entry["field"])
        category = str(entry["category"])
        marker = str(entry["marker"])
        text = all_texts.get(fname)
        if text is None:
            errors.append(
                f"{name}: indexed redaction_{idx} declares file={fname!r} but that "
                "file is absent from the evidence set"
            )
            continue

        field_val = _field_value(text, field)
        if field_val is None:
            errors.append(
                f"{name}: indexed redaction_{idx} field/section {field!r} not found "
                f"in {fname} (field relocation or missing section)"
            )
            continue
        marker_cat, _marker_id, marker_err = parse_category_bearing_marker(marker)
        if marker_err:
            errors.append(
                f"{name}: indexed redaction_{idx} replacement_marker {marker_err}"
            )
            continue
        if marker_cat != category:
            errors.append(
                f"{name}: indexed redaction_{idx} category substitution rejected: "
                f"declared category={category!r} but replacement_marker carries "
                f"{marker_cat!r}"
            )
            continue

        if marker not in field_val:
            errors.append(
                f"{name}: indexed redaction_{idx} replacement_marker {marker!r} not "
                f"present in {fname} field/section {field!r} "
                f"(category={category}); rejects field/category/marker relocation "
                "or substitution"
            )
            continue

        # Locate physical occurrences of this marker inside the declared field's
        # KV value span(s) for unambiguous one-to-one binding.
        candidates: list[tuple[str, int, int, str]] = []
        offset = 0
        for raw_line in text.splitlines(keepends=True):
            line_start = offset
            offset += len(raw_line)
            stripped = raw_line.strip()
            match = KV_LINE_RE.fullmatch(stripped) if stripped else None
            if not match or match.group(1) != field:
                continue
            value = match.group(2)
            # Map value span back into the raw line (preserve original offsets).
            value_offset_in_line = raw_line.find(value)
            if value_offset_in_line < 0:
                continue
            value_abs = line_start + value_offset_in_line
            for m in REDACTION_MARKER_RE.finditer(value):
                if m.group(0) != marker:
                    continue
                abs_start = value_abs + m.start()
                abs_end = value_abs + m.end()
                candidates.append((fname, abs_start, abs_end, marker))

        if not candidates:
            # Field value contained marker substring but not as a discrete physical
            # marker token in the KV value span.
            errors.append(
                f"{name}: indexed redaction_{idx} could not bind marker {marker!r} "
                f"to a unique physical occurrence in {fname} field {field!r}"
            )
            continue
        if len(candidates) > 1:
            errors.append(
                f"{name}: indexed redaction_{idx} marker {marker!r} occurs "
                f"{len(candidates)} times in {fname} field {field!r}; one index "
                "entry must not be satisfied by multiple markers"
            )
            continue
        phys = candidates[0]
        phys_marker = phys[3]
        if phys_marker != marker:
            errors.append(
                f"{name}: indexed redaction_{idx} replacement_marker {marker!r} "
                f"must exactly equal physical marker {phys_marker!r} at "
                f"{fname} field/section {field!r}"
            )
            continue
        phys_cat, _phys_id, phys_err = parse_category_bearing_marker(phys_marker)
        if phys_err:
            errors.append(
                f"{name}: physical marker {phys_marker!r} in {fname} field "
                f"{field!r} {phys_err}"
            )
            continue
        if phys_cat != category:
            errors.append(
                f"{name}: indexed redaction_{idx} category substitution rejected: "
                f"declared category={category!r} but physical marker carries "
                f"{phys_cat!r}"
            )
            continue
        phys_key = (phys[0], phys[1], phys[2])
        if phys_key in claimed_physical:
            errors.append(
                f"{name}: physical marker at {fname}:{phys[1]} satisfies both "
                f"redaction_{claimed_physical[phys_key]} and redaction_{idx}; "
                "one physical marker must not satisfy multiple index entries"
            )
            continue
        claimed_physical[phys_key] = idx

    # Orphan physical markers (including duplicate-marker leftovers).
    for fname, start, end, marker in physical:
        key = (fname, start, end)
        if key not in claimed_physical:
            errors.append(
                f"{name}: orphan marker {marker!r} in {fname} has no matching "
                "indexed redaction entry at the exact file/field/category identity"
            )

    # Orphan index entries already reported when they failed to claim a physical.
    return errors
