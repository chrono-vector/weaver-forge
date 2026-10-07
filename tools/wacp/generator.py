"""Deterministic, bounded Weaver AI Context Pack v0 generator."""

from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "wacp.scope_manifest.v0"
PACK_SCHEMA_VERSION = "wacp.pack_manifest.v0"
GENERATOR_NAME = "weaver-wacp"
GENERATOR_VERSION = "0.1.0"
PACK_STATUSES = frozenset({"PACK_READY", "PACK_INCOMPLETE", "PACK_TOO_LARGE", "INVALID"})
REVIEW_MODES = frozenset({"implementation", "independent_review", "remediation"})
ARTIFACT_NAMES = (
    "PACK_MANIFEST.json", "CONTEXT_SUMMARY.md", "DIFF.patch",
    "OPEN_FINDINGS.md", "CLAIM_BOUNDARY.md", "TEST_STATUS.md",
)
HASHED_ARTIFACT_NAMES = ARTIFACT_NAMES[1:]
_REQUIRED_FIELDS = frozenset({"scope_id", "base", "head", "review_mode", "include", "max_bytes"})
_OPTIONAL_FIELDS = frozenset({
    "schema_version", "exclude", "required_status_files", "finding_sources",
    "test_status", "clean_worktree_required",
})
_NONCLAIMS = (
    "not_authorization", "not_correctness", "not_safety", "not_completeness_proof",
    "not_independent_verification", "not_human_final", "not_evidence_promotion",
    "not_production_permission", "not_excluded_file_irrelevance",
    "not_selected_file_sufficiency", "not_test_verification",
    "not_repository_inspection_replacement", "not_reviewer_judgment_replacement",
)
_DRIVE_RE = re.compile(r"\A[A-Za-z]:")


class WACPError(ValueError):
    pass


@dataclass(frozen=True)
class GenerationResult:
    status: str
    pack_id: str | None
    output_dir: Path | None
    errors: tuple[str, ...] = ()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _markdown_bytes(lines: Sequence[str]) -> bytes:
    return ("\n".join(lines).rstrip("\n") + "\n").encode("utf-8")


def _git(root: Path, *arguments: str, binary: bool = False, check: bool = True) -> bytes | str:
    environment = os.environ.copy()
    environment.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"})
    result = subprocess.run(
        ["git", *arguments], cwd=root, env=environment, capture_output=True,
        text=not binary, check=False,
    )
    if check and result.returncode != 0:
        error = result.stderr if isinstance(result.stderr, str) else result.stderr.decode("utf-8", "replace")
        raise WACPError(error.strip() or "git command failed")
    return result.stdout


def _repo_root(repository: str | Path) -> Path:
    candidate = Path(repository).resolve()
    root = Path(str(_git(candidate, "rev-parse", "--show-toplevel")).strip()).resolve()
    if candidate != root:
        raise WACPError("repository must name the Git top-level directory")
    return root


def _resolve_commit(root: Path, value: Any, label: str) -> str:
    if type(value) is not str or not value or value.startswith("-"):
        raise WACPError(f"{label} must be a non-empty Git revision")
    try:
        resolved = str(_git(root, "rev-parse", "--verify", f"{value}^{{commit}}")).strip()
    except WACPError as exc:
        raise WACPError(f"{label} is missing, ambiguous, or unresolvable") from exc
    if re.fullmatch(r"[0-9a-f]{40}", resolved) is None:
        raise WACPError(f"{label} did not resolve to a full commit SHA")
    return resolved


def _is_ancestor(root: Path, first: str, second: str) -> bool:
    return subprocess.run(
        ["git", "merge-base", "--is-ancestor", first, second], cwd=root,
        capture_output=True, check=False,
    ).returncode == 0


def _relationship(root: Path, base: str, head: str) -> str:
    if base == head:
        return "EQUAL"
    if _is_ancestor(root, base, head):
        return "BASE_IS_ANCESTOR"
    if _is_ancestor(root, head, base):
        return "HEAD_IS_ANCESTOR"
    return "DIVERGED"


def _validate_pattern(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise WACPError(f"{label} must be a non-empty POSIX path pattern")
    if "\\" in value or value.startswith("/") or _DRIVE_RE.match(value):
        raise WACPError(f"{label} must be repository-relative POSIX syntax")
    path = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in path.parts) or path.as_posix() != value:
        raise WACPError(f"{label} contains traversal or is not normalized")
    return value


def _pattern_list(value: Any, label: str, *, required: bool = False) -> list[str]:
    if type(value) is not list:
        raise WACPError(f"{label} must be an exact list")
    result = [_validate_pattern(item, f"{label}[{index}]") for index, item in enumerate(value)]
    if required and not result:
        raise WACPError(f"{label} must not be empty")
    if len(result) != len(set(result)):
        raise WACPError(f"{label} contains a duplicate normalized path or pattern")
    return result


def _parse_manifest(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", "strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WACPError("scope manifest must be strict UTF-8 JSON") from exc
    if type(value) is not dict:
        raise WACPError("scope manifest must be an exact object")
    fields = set(value)
    if not _REQUIRED_FIELDS <= fields or not fields <= (_REQUIRED_FIELDS | _OPTIONAL_FIELDS):
        raise WACPError("scope manifest fields do not match the closed v0 schema")
    if value.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        raise WACPError("scope manifest schema_version mismatch")
    if type(value["scope_id"]) is not str or not value["scope_id"]:
        raise WACPError("scope_id must be a non-empty string")
    if value["review_mode"] not in REVIEW_MODES:
        raise WACPError("review_mode is not in the closed v0 set")
    if type(value["max_bytes"]) is not int or type(value["max_bytes"]) is bool or value["max_bytes"] <= 0:
        raise WACPError("max_bytes must be a positive integer")
    value["include"] = _pattern_list(value["include"], "include", required=True)
    value["exclude"] = _pattern_list(value.get("exclude", []), "exclude")
    value["required_status_files"] = _pattern_list(value.get("required_status_files", []), "required_status_files")
    value["finding_sources"] = _pattern_list(value.get("finding_sources", []), "finding_sources")
    clean = value.get("clean_worktree_required", True)
    if type(clean) is not bool:
        raise WACPError("clean_worktree_required must be boolean")
    value["clean_worktree_required"] = clean
    if value.get("test_status") is not None and type(value["test_status"]) is not dict:
        raise WACPError("test_status must be an exact object when supplied")
    return value


def _tree(root: Path, commit: str) -> dict[str, tuple[str, str]]:
    raw = _git(root, "ls-tree", "-r", "-z", "--full-tree", commit, binary=True)
    assert isinstance(raw, bytes)
    result: dict[str, tuple[str, str]] = {}
    for record in (item for item in raw.split(b"\0") if item):
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, _object_id = metadata.decode("ascii").split(" ", 2)
        result[raw_path.decode("utf-8", "strict")] = (mode, object_type)
    return result


def _segment_glob(pattern: str, path: str) -> bool:
    pattern_parts, path_parts = pattern.split("/"), path.split("/")

    def match(pi: int, xi: int) -> bool:
        while pi < len(pattern_parts):
            part = pattern_parts[pi]
            if part == "**":
                if pi + 1 == len(pattern_parts):
                    return True
                return any(match(pi + 1, candidate) for candidate in range(xi, len(path_parts) + 1))
            if xi >= len(path_parts) or not fnmatch.fnmatchcase(path_parts[xi], part):
                return False
            pi, xi = pi + 1, xi + 1
        return xi == len(path_parts)

    return match(0, 0)


def _expand(
    patterns: Sequence[str], paths: set[str], label: str, *, unmatched_invalid: bool = True
) -> set[str]:
    selected: set[str] = set()
    for pattern in patterns:
        matches = {path for path in paths if _segment_glob(pattern, path)}
        if not matches and unmatched_invalid:
            raise WACPError(f"unmatched {label} pattern: {pattern}")
        selected.update(matches)
    return selected


def _changed_paths(root: Path, base: str, head: str) -> tuple[str, ...]:
    raw = _git(root, "diff", "--name-only", "--no-renames", "-z", base, head, "--", binary=True)
    assert isinstance(raw, bytes)
    return tuple(sorted(part.decode("utf-8", "strict") for part in raw.split(b"\0") if part))


def _blob(root: Path, commit: str, path: str, tree: Mapping[str, tuple[str, str]]) -> bytes | None:
    if path not in tree:
        return None
    mode, object_type = tree[path]
    if mode == "120000":
        raise WACPError(f"selected path is a symlink: {path}")
    if object_type != "blob":
        raise WACPError(f"selected path is not a regular tracked file: {path}")
    raw = _git(root, "show", f"{commit}:{path}", binary=True)
    assert isinstance(raw, bytes)
    return raw


def _inventory(
    root: Path, base: str, head: str, selected: Sequence[str],
    base_tree: Mapping[str, tuple[str, str]], head_tree: Mapping[str, tuple[str, str]],
) -> list[dict[str, Any]]:
    result = []
    for path in selected:
        before = _blob(root, base, path, base_tree)
        after = _blob(root, head, path, head_tree)
        result.append({
            "path": path,
            "base_sha256": _sha256(before) if before is not None else None,
            "head_sha256": _sha256(after) if after is not None else None,
        })
    return result


def _selected_diff(root: Path, base: str, head: str, selected: Sequence[str]) -> bytes:
    if not selected:
        return b""
    raw = _git(
        root, "-c", "core.quotepath=true", "diff", "--binary", "--full-index",
        "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames",
        base, head, "--", *selected, binary=True,
    )
    assert isinstance(raw, bytes)
    return raw.replace(b"\r\n", b"\n")


def _sources(
    root: Path, head: str, paths: Sequence[str], selected: set[str],
    head_tree: Mapping[str, tuple[str, str]], missing: list[str],
) -> list[tuple[str, bytes]]:
    result = []
    for path in sorted(paths):
        if path not in selected:
            missing.append(f"required source is not selected: {path}")
            continue
        content = _blob(root, head, path, head_tree)
        if content is None:
            missing.append(f"required source is missing at head: {path}")
        else:
            result.append((path, content))
    return result


def _claim_boundary() -> bytes:
    return _markdown_bytes([
        "# Claim Boundary", "",
        "This WACP pack is a deterministic, bounded extraction of declared repository context for the stated scope manifest, base/head pair, review mode, repository identity, and generator version.",
        "", "WACP does NOT:", "",
        "- authorize changes", "- prove correctness", "- prove safety",
        "- prove completeness", "- establish independent verification",
        "- establish Human Final", "- promote evidence", "- grant production permission",
        "- prove excluded files are irrelevant", "- prove selected files are sufficient",
        "- prove tests passed unless WACP actually executed and recorded them",
        "- replace repository inspection", "- replace reviewer judgment",
    ])


def _summary(manifest: Mapping[str, Any], base: str, head: str, status: str) -> bytes:
    focus = {
        "implementation": "Implement only the declared scope and inspect its bounded base-to-head change.",
        "independent_review": "Independently inspect the declared change; do not trust supplied conclusions.",
        "remediation": "Determine whether declared findings are closed without broadening the remediation scope.",
    }[manifest["review_mode"]]
    return _markdown_bytes([
        "# Context Summary", "", f"- Scope: `{manifest['scope_id']}`",
        "- Purpose: deterministic bounded repository context extraction",
        f"- Base: `{base}`", f"- Head: `{head}`",
        f"- Review mode: `{manifest['review_mode']}`",
        f"- Completeness status: `{status}`", f"- Reviewer focus: {focus}",
        "- Expected external review context: `PACK_ONLY` or `PACK_PLUS_TARGETED_REPO`",
        "", "## Limitations", "",
        "Context selection is not verification completeness. This pack does not replace repository inspection or reviewer judgment.",
    ])


def _open_findings(
    sources: Sequence[tuple[str, bytes]], *, source_declared: bool
) -> bytes:
    if not sources:
        marker = (
            "DECLARED_FINDING_SOURCE_UNAVAILABLE"
            if source_declared
            else "NO_FINDING_SOURCE_SUPPLIED"
        )
        return _markdown_bytes(["# Open Findings", "", marker])
    lines = ["# Open Findings", ""]
    for path, content in sources:
        lines.extend([f"## Source: `{path}`", "", content.decode("utf-8", "replace").rstrip(), ""])
    return _markdown_bytes(lines)


def _test_status(manifest: Mapping[str, Any], sources: Sequence[tuple[str, bytes]]) -> bytes:
    lines = ["# Test Status", "", "WACP-v0 did not execute tests while generating this pack.", ""]
    supplied = manifest.get("test_status")
    if supplied is None:
        lines.extend(["NO_TEST_STATUS_SUPPLIED", ""])
    else:
        lines.extend(["## Supplied Test Information", "", "```json", json.dumps(supplied, sort_keys=True, indent=2, ensure_ascii=True), "```", ""])
    for path, content in sources:
        lines.extend([f"## Required Status Source: `{path}`", "", content.decode("utf-8", "replace").rstrip(), ""])
    lines.extend(["## Limitation", "", "WACP did not independently verify supplied test, mutation, or regression results."])
    return _markdown_bytes(lines)


def _repo_identity(root: Path) -> dict[str, str]:
    remote = str(_git(root, "config", "--get", "remote.origin.url", check=False)).strip()
    return {"remote_origin": remote or "NO_REMOTE"}


def _git_context(root: Path) -> dict[str, str]:
    return {
        "version": str(_git(root, "--version")).strip(),
        "diff_renames_config": str(_git(root, "config", "--get", "diff.renames", check=False)).strip() or "UNSET",
        "wacp_rename_policy": "NO_RENAMES", "external_diff": "DISABLED", "textconv": "DISABLED",
    }


def _artifact_inventory(artifacts: Mapping[str, bytes]) -> list[dict[str, Any]]:
    return [{"name": name, "sha256": _sha256(artifacts[name]), "bytes": len(artifacts[name])} for name in HASHED_ARTIFACT_NAMES]


def _manifest_with_size(body: dict[str, Any], artifacts: Mapping[str, bytes]) -> bytes:
    size = 0
    while True:
        body["generated_byte_size"] = size
        encoded = _json_bytes(body)
        calculated = len(encoded) + sum(len(value) for value in artifacts.values())
        if calculated == size:
            return encoded
        size = calculated


def _build_pack(
    *, root: Path, manifest: Mapping[str, Any], source_digest: str, base: str,
    head: str, relationship: str, selected: tuple[str, ...], changed: tuple[str, ...],
    excluded_changed: tuple[str, ...], out_of_scope: tuple[str, ...],
    selected_inventory: list[dict[str, Any]], missing_sources: tuple[str, ...],
    finding_sources: Sequence[tuple[str, bytes]], status_sources: Sequence[tuple[str, bytes]],
) -> tuple[dict[str, Any], dict[str, bytes]]:
    status = "PACK_INCOMPLETE" if out_of_scope or excluded_changed or missing_sources else "PACK_READY"
    repo_identity, git_context = _repo_identity(root), _git_context(root)
    identity_seed = {
        "schema_version": PACK_SCHEMA_VERSION, "repo_identity": repo_identity,
        "base": base, "head": head, "base_head_relationship": relationship,
        "scope_id": manifest["scope_id"], "review_mode": manifest["review_mode"],
        "source_scope_manifest_sha256": source_digest,
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "git": git_context, "max_bytes": manifest["max_bytes"],
    }
    pack_id = _sha256(_json_bytes(identity_seed))

    def make_artifacts(current_status: str) -> dict[str, bytes]:
        return {
            "CONTEXT_SUMMARY.md": _summary(manifest, base, head, current_status),
            "DIFF.patch": _selected_diff(root, base, head, selected),
            "OPEN_FINDINGS.md": _open_findings(
                finding_sources, source_declared=bool(manifest["finding_sources"])
            ),
            "CLAIM_BOUNDARY.md": _claim_boundary(),
            "TEST_STATUS.md": _test_status(manifest, status_sources),
        }

    artifacts = make_artifacts(status)
    body: dict[str, Any] = {
        "schema_version": PACK_SCHEMA_VERSION, "version": 0, "pack_id": pack_id,
        "repo_identity": repo_identity, "base_sha": base, "head_sha": head,
        "base_head_relationship": relationship, "scope_id": manifest["scope_id"],
        "review_mode": manifest["review_mode"], "include_patterns": list(manifest["include"]),
        "exclude_patterns": list(manifest["exclude"]), "selected_files": list(selected),
        "changed_files": list(changed), "excluded_changed_files": list(excluded_changed),
        "out_of_scope_changed_files": list(out_of_scope),
        "missing_required_sources": list(missing_sources),
        "source_scope_manifest_sha256": source_digest,
        "selected_file_inventory": selected_inventory,
        "generated_artifact_inventory": _artifact_inventory(artifacts),
        "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
        "git": git_context,
        "context_budget": {"max_bytes": manifest["max_bytes"], "policy": "NO_TRUNCATION"},
        "generated_byte_size": 0, "completeness_status": status,
        "nonclaims": list(_NONCLAIMS),
    }
    manifest_bytes = _manifest_with_size(body, artifacts)
    if body["generated_byte_size"] > manifest["max_bytes"]:
        status = "PACK_TOO_LARGE"
        artifacts = make_artifacts(status)
        body["completeness_status"] = status
        body["generated_artifact_inventory"] = _artifact_inventory(artifacts)
        manifest_bytes = _manifest_with_size(body, artifacts)
    return body, {"PACK_MANIFEST.json": manifest_bytes, **artifacts}


def _ensure_empty_output(output_dir: Path) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise WACPError("output directory must not contain existing files")
    output_dir.mkdir(parents=True, exist_ok=True)


def verify_pack(output_dir: str | Path) -> tuple[str, ...]:
    root, errors = Path(output_dir), []
    manifest_path, claim_path = root / "PACK_MANIFEST.json", root / "CLAIM_BOUNDARY.md"
    if not manifest_path.is_file():
        return ("missing PACK_MANIFEST.json",)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return ("malformed PACK_MANIFEST.json",)
    if not claim_path.is_file() or claim_path.read_bytes() != _claim_boundary():
        errors.append("missing or malformed claim boundary")
    inventory = manifest.get("generated_artifact_inventory")
    if type(inventory) is not list:
        return tuple([*errors, "generated artifact inventory is malformed"])
    for entry in inventory:
        if type(entry) is not dict or set(entry) != {"name", "sha256", "bytes"}:
            errors.append("generated artifact inventory entry is malformed")
            continue
        path = root / entry["name"]
        if not path.is_file():
            errors.append(f"missing generated artifact: {entry['name']}")
            continue
        content = path.read_bytes()
        if len(content) != entry["bytes"] or _sha256(content) != entry["sha256"]:
            errors.append(f"generated artifact hash mismatch: {entry['name']}")
    return tuple(errors)


def generate_pack(repository: str | Path, manifest_path: str | Path, output_dir: str | Path) -> GenerationResult:
    """Generate one WACP-v0 pack without executing tests or using a network."""
    destination: Path | None = None
    try:
        root = _repo_root(repository)
        raw = Path(manifest_path).read_bytes()
        manifest = _parse_manifest(raw)
        base = _resolve_commit(root, manifest["base"], "base")
        head = _resolve_commit(root, manifest["head"], "head")
        if manifest["clean_worktree_required"] and str(_git(root, "status", "--porcelain=v1", "--untracked-files=all")):
            raise WACPError("worktree is dirty while clean_worktree_required is true")
        base_tree, head_tree = _tree(root, base), _tree(root, head)
        all_paths = set(base_tree) | set(head_tree)
        included = _expand(manifest["include"], all_paths, "include")
        excluded = (
            _expand(
                manifest["exclude"], all_paths, "exclude", unmatched_invalid=False
            )
            if manifest["exclude"]
            else set()
        )
        selected_set = included - excluded
        selected = tuple(sorted(selected_set))
        changed = _changed_paths(root, base, head)
        excluded_changed = tuple(sorted(set(changed) & included & excluded))
        out_of_scope = tuple(sorted(set(changed) - selected_set))
        inventory = _inventory(root, base, head, selected, base_tree, head_tree)
        missing: list[str] = []
        finding_sources = _sources(root, head, manifest["finding_sources"], selected_set, head_tree, missing)
        status_sources = _sources(root, head, manifest["required_status_files"], selected_set, head_tree, missing)
        body, artifacts = _build_pack(
            root=root, manifest=manifest, source_digest=_sha256(raw), base=base, head=head,
            relationship=_relationship(root, base, head), selected=selected, changed=changed,
            excluded_changed=excluded_changed, out_of_scope=out_of_scope,
            selected_inventory=inventory, missing_sources=tuple(sorted(missing)),
            finding_sources=finding_sources, status_sources=status_sources,
        )
        destination = Path(output_dir)
        _ensure_empty_output(destination)
        for name in ARTIFACT_NAMES:
            (destination / name).write_bytes(artifacts[name])
        errors = verify_pack(destination)
        if errors:
            return GenerationResult("INVALID", body["pack_id"], destination, errors)
        return GenerationResult(body["completeness_status"], body["pack_id"], destination)
    except (OSError, UnicodeError, WACPError, ValueError, TypeError) as exc:
        return GenerationResult("INVALID", None, destination, (str(exc),))
