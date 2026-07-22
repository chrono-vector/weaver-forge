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
FORBIDDEN_PLACEHOLDERS = ("TODO", "FILL_ME", "<replace-me>")

EXPECTED_GROK_COMMIT = "98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
EXPECTED_IMAGE_DIGEST = "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
EXACT_BUILD_CMD = "cargo build -p xai-grok-pager-bin --locked"

REQUIRED_FILES = (
    "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
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
    "EVIDENCE_MANIFEST.sha256",
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
        if not any(v in vt for v in VERDICT_VALUES):
            fail(errors, "WITNESS_VERDICT.md lacks PASS/PARTIAL/FAIL/INDETERMINATE")

    for name in ("SOURCE_IDENTITY.txt", "WEAVER_FORGE_PACKAGE_IDENTITY.txt"):
        p = evidence_dir / name
        if p.is_file():
            commits = find_commit(read_text(p))
            if not commits:
                fail(errors, f"No 40-char commit in {name}")

    manifest = evidence_dir / "EVIDENCE_MANIFEST.sha256"
    if manifest.is_file() and manifest.stat().st_size > 0:
        for line in read_text(manifest).splitlines():
            parts = line.split()
            if len(parts) >= 1 and parts[0] and not SHA256_RE.match(parts[0]):
                fail(errors, "EVIDENCE_MANIFEST.sha256 contains non-SHA256 line")
                break

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
