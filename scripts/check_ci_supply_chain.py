#!/usr/bin/env python3
"""Check the repository's GitHub Actions supply-chain policy."""

from __future__ import annotations

import re
import sys
from pathlib import Path


FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
USES_LINE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def workflow_files(root: Path) -> list[Path]:
    workflow_dir = root / ".github" / "workflows"
    return sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))


def external_action_refs(text: str) -> list[str]:
    refs: list[str] = []
    for line in text.splitlines():
        match = USES_LINE.match(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            continue
        refs.append(ref)
    return refs


def has_explicit_permissions(text: str) -> bool:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line == "permissions:":
            for child in lines[index + 1 :]:
                if child and not child[0].isspace():
                    break
                if re.match(r"^  [a-z-]+:\s*(?:read|write|none)\s*(?:#.*)?$", child):
                    return True
    return False


def validate_workflow(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if not has_explicit_permissions(text):
        errors.append(f"{path}: explicit top-level permissions are required")
    for ref in external_action_refs(text):
        if "@" not in ref:
            errors.append(f"{path}: external action has no ref: {ref}")
            continue
        action, revision = ref.rsplit("@", 1)
        if not action or not FULL_SHA.fullmatch(revision):
            errors.append(f"{path}: external action is not pinned to a full SHA: {ref}")
    return errors


def validate_dependabot(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path}: missing Dependabot configuration"]
    text = path.read_text(encoding="utf-8")
    required = (
        r"(?m)^version:\s*2\s*$",
        r"(?m)^\s*-\s+package-ecosystem:\s*[\"']?github-actions[\"']?\s*$",
        r"(?m)^\s+directory:\s*[\"']?/[\"']?\s*$",
        r"(?m)^\s+interval:\s*[\"']?weekly[\"']?\s*$",
    )
    if all(re.search(pattern, text) for pattern in required):
        return []
    return [f"{path}: expected weekly github-actions update configuration"]


def validate_repository(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    workflows = workflow_files(root)
    if not workflows:
        errors.append(f"{root}: no workflow YAML files found")
    action_count = 0
    for path in workflows:
        text = path.read_text(encoding="utf-8")
        action_count += len(external_action_refs(text))
        errors.extend(validate_workflow(path))
    errors.extend(validate_dependabot(root / ".github" / "dependabot.yml"))
    return errors, action_count


def main() -> int:
    errors, action_count = validate_repository(repo_root())
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"PASS: {action_count} external action reference(s) use full SHA pins")
    print("PASS: workflow permissions are explicit")
    print("PASS: weekly github-actions Dependabot configuration is present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
