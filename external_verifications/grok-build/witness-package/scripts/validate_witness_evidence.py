#!/usr/bin/env python3
"""
Structural validator for Independent Witness evidence directories.

Validates presence, format, and vocabulary — not truthfulness, independence, or execution.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

COMMIT_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERDICT_VALUES = frozenset({"PASS", "PARTIAL", "FAIL", "INDETERMINATE"})
VERDICT_LINE_RE = re.compile(
    r"^Witness proposed verdict:\s*(\S+)\s*$",
    re.MULTILINE,
)
FORBIDDEN_PLACEHOLDERS = ("TODO", "FILL_ME", "<replace-me>")

EXPECTED_GROK_COMMIT = "98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
EXPECTED_IMAGE_DIGEST = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
EXACT_BUILD_CMD = "cargo build -p xai-grok-pager-bin --locked"
MANIFEST_NAME = "EVIDENCE_MANIFEST.sha256"

# Optional host-only files not required in manifest (documented in VALIDATOR.md).
MANIFEST_OPTIONAL_EVIDENCE = frozenset({"HOST_RUN_METADATA.txt"})

REQUIRED_FILES = (
    "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
    "SOURCE_ACQUISITION.txt",
    "SOURCE_IDENTITY.txt",
    "IMAGE_IDENTITY.txt",
    "ENVIRONMENT.txt",
    "BOOTSTRAP.txt",
    "CLEAN_TARGET_PROOF.txt",
    "BUILD_COMMAND.txt",
    "BUILD_ENVIRONMENT.txt",
    "BUILD_STDOUT.txt",
    "BUILD_STDERR.txt",
    "BUILD_EXIT_CODE.txt",
    "BUILD_TIMING.txt",
    "CONTAINER_STDOUT.txt",
    "CONTAINER_STDERR.txt",
    "DOCKER_EXIT_CODE.txt",
    "ARTIFACT_IDENTITY.txt",
    "STATIC_ARTIFACT_INSPECTION.txt",
    "POST_BUILD_INTEGRITY.txt",
    "DEVIATIONS.txt",
    MANIFEST_NAME,
    "REDACTIONS.md",
    "WITNESS_STATEMENT.md",
    "WITNESS_VERDICT.md",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def find_commit(text: str) -> list[str]:
    return COMMIT_RE.findall(text.lower())


def normalize_manifest_path(raw: str) -> str | None:
    """Return safe relative path from sha256sum line, or None if unsafe."""
    path = raw.strip()
    if not path:
        return None
    if path.startswith("./"):
        path = path[2:]
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return None
    if ".." in path.split("/"):
        return None
    if path == MANIFEST_NAME:
        return None
    if not re.match(r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$", path):
        return None
    return path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_verdict_selection(text: str) -> tuple[list[str], list[str]]:
    """Return (matches, errors) for Witness proposed verdict line."""
    errors: list[str] = []
    matches = VERDICT_LINE_RE.findall(text)
    if not matches:
        errors.append("Missing or invalid 'Witness proposed verdict:' selection line")
    elif len(matches) > 1:
        errors.append("Duplicate 'Witness proposed verdict:' selection lines")
    else:
        value = matches[0].upper()
        if value not in VERDICT_VALUES:
            errors.append(f"Invalid witness proposed verdict value: {value}")
        matches = [value if value in VERDICT_VALUES else matches[0]]
    return matches, errors


def validate_manifest(evidence_dir: Path, errors: list[str]) -> None:
    manifest_path = evidence_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        return

    listed: dict[str, str] = {}
    for line_no, line in enumerate(read_text(manifest_path).splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 2:
            fail(errors, f"{MANIFEST_NAME}:{line_no}: malformed line")
            continue
        digest, raw_path = parts[0], parts[-1]
        if not SHA256_RE.match(digest):
            fail(errors, f"{MANIFEST_NAME}:{line_no}: hash not 64-char lowercase hex")
            continue
        rel = normalize_manifest_path(raw_path)
        if rel is None:
            fail(errors, f"{MANIFEST_NAME}:{line_no}: unsafe or forbidden path {raw_path!r}")
            continue
        if rel in listed:
            fail(errors, f"{MANIFEST_NAME}: duplicate entry for {rel}")
            continue
        listed[rel] = digest

    for req in REQUIRED_FILES:
        if req == MANIFEST_NAME:
            continue
        if req not in listed:
            fail(errors, f"{MANIFEST_NAME}: missing mandatory entry for {req}")

    for rel, expected in listed.items():
        target = evidence_dir / rel
        if not target.is_file():
            fail(errors, f"{MANIFEST_NAME}: listed file missing on disk: {rel}")
            continue
        actual = sha256_file(target)
        if actual != expected:
            fail(errors, f"{MANIFEST_NAME}: hash mismatch for {rel}")

    for path in evidence_dir.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(evidence_dir).as_posix()
        if rel == MANIFEST_NAME:
            continue
        if rel in MANIFEST_OPTIONAL_EVIDENCE:
            continue
        if rel not in listed:
            fail(
                errors,
                f"Unlisted regular evidence file (policy: structural FAIL): {rel}",
            )


def validate_dir(evidence_dir: Path) -> list[str]:
    errors: list[str] = []
    if not evidence_dir.is_dir():
        return [f"Not a directory: {evidence_dir}"]

    for name in REQUIRED_FILES:
        p = evidence_dir / name
        if not p.is_file():
            fail(errors, f"Missing required file: {name}")
        elif p.stat().st_size == 0 and name not in (
            "BUILD_STDOUT.txt",
            "BUILD_STDERR.txt",
            "CONTAINER_STDOUT.txt",
            "CONTAINER_STDERR.txt",
        ):
            fail(errors, f"Empty required file: {name}")

    for path in evidence_dir.rglob("*"):
        if path.is_file():
            text = read_text(path)
            for token in FORBIDDEN_PLACEHOLDERS:
                if token in text:
                    fail(errors, f"Placeholder {token!r} in {path.name}")

    combined = ""
    for name in REQUIRED_FILES:
        p = evidence_dir / name
        if p.is_file():
            combined += read_text(p) + "\n"

    if EXACT_BUILD_CMD not in combined:
        fail(errors, f"Exact build command not found: {EXACT_BUILD_CMD}")
    if "CARGO_INCREMENTAL=0" not in combined and "cargo_incremental=0" not in combined.lower():
        fail(errors, "CARGO_INCREMENTAL=0 not documented")

    if EXPECTED_GROK_COMMIT not in combined:
        fail(errors, f"Expected Grok Build commit missing: {EXPECTED_GROK_COMMIT}")
    if EXPECTED_IMAGE_DIGEST not in combined:
        fail(errors, f"Expected Rust image digest missing: {EXPECTED_IMAGE_DIGEST}")

    if "product_executed=NO" not in combined and "product_executed=no" not in combined.lower():
        fail(errors, "product_executed=NO not asserted")
    if "ldd_used=NO" not in combined and "ldd_used=no" not in combined.lower():
        fail(errors, "ldd_used=NO not asserted")

    verdict_path = evidence_dir / "WITNESS_VERDICT.md"
    if verdict_path.is_file():
        vt = read_text(verdict_path)
        _, verdict_errors = parse_verdict_selection(vt)
        for e in verdict_errors:
            fail(errors, e)

    for name in ("SOURCE_IDENTITY.txt", "WEAVER_FORGE_PACKAGE_IDENTITY.txt"):
        p = evidence_dir / name
        if p.is_file():
            commits = find_commit(read_text(p))
            if not commits:
                fail(errors, f"No 40-char commit in {name}")

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
