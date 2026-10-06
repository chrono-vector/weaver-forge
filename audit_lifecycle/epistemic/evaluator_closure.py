"""Non-authoritative semantic evaluator isolation closure v0.

The checker reads committed Git objects only.  A human-approved, canonical
epoch record pins the accepted base, this checker, evaluator entrypoints, and
their evaluator semantic surface (ESS).  A closure receipt may block or defer;
it never authorizes a proposal or changes Weaver evidence semantics.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from audit_lifecycle.epistemic.serialize import canonical_digest, canonical_dumps


EPOCH_SCHEMA_VERSION = "evaluator_epoch.v0"
RECEIPT_SCHEMA_VERSION = "evaluator_closure.v0"
CHECKER_RELATIVE_PATH = "audit_lifecycle/epistemic/evaluator_closure.py"
DISPOSITIONS = frozenset(
    {
        "PASS",
        "CLOSURE_HIT",
        "UNKNOWN_REACH",
        "CALLER_SEMANTIC_INPUT",
        "EPOCH_MISMATCH",
        "REQUIRE_HUMAN_REVIEW",
        "INVALID",
    }
)
_SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_COMMIT_RE = re.compile(r"\A[0-9a-f]{40}\Z")
_EPOCH_FIELDS = frozenset(
    {
        "schema_version",
        "authority",
        "epoch_id",
        "accepted_base_commit",
        "approval_status",
        "human_approval_ref",
        "checker",
        "evaluator_entrypoints",
        "ess",
        "semantic_config",
        "closure_policy",
    }
)
_CHECKER_FIELDS = frozenset({"source", "relative_path", "sha256"})
_ESS_FIELDS = frozenset({"relative_path", "sha256"})
_SEMANTIC_CONFIG_FIELDS = frozenset(
    {"caller_semantic_input", "non_semantic_external_imports"}
)
_POLICY_FIELDS = frozenset(
    {"epoch_declaration_paths", "non_semantic_paths"}
)
_RECEIPT_FIELDS = frozenset(
    {
        "schema_version",
        "authority",
        "epoch_id",
        "epoch_record_digest",
        "accepted_base_commit",
        "proposal_commit",
        "checker_sha256",
        "ess_digest",
        "disposition",
        "changed_paths",
        "closure_hits",
        "unknown_reach",
        "limitations",
        "receipt_digest",
    }
)
_LIMITATIONS = (
    "not_authorization",
    "not_correctness",
    "not_merge_approval",
    "not_policy_approval",
    "not_human_final",
    "not_independent_reproduction",
    "static_reach_is_bounded_not_complete",
    "external_import_allowlist_is_epoch_scoped",
    "pass_means_no_v0_closure_violation_detected_only",
)
_DYNAMIC_CALLS = frozenset(
    {
        "__import__",
        "importlib.import_module",
        "importlib.util.spec_from_file_location",
        "pkgutil.iter_modules",
        "pkgutil.walk_packages",
    }
)
_PATH_MUTATORS = frozenset(
    {
        "sys.path.append",
        "sys.path.clear",
        "sys.path.extend",
        "sys.path.insert",
        "sys.path.pop",
        "sys.path.remove",
        "sys.path.reverse",
        "sys.path.sort",
    }
)


class EvaluatorClosureError(ValueError):
    """Internal closed failure carrying the required receipt disposition."""

    def __init__(self, disposition: str, message: str) -> None:
        if disposition not in DISPOSITIONS or disposition == "PASS":
            raise ValueError("invalid closure failure disposition")
        self.disposition = disposition
        self.message = message
        super().__init__(f"{disposition}: {message}")


def _fail(disposition: str, message: str) -> None:
    raise EvaluatorClosureError(disposition, message)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return canonical_dumps(value).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            _fail("INVALID", "epoch record contains a duplicate or non-string key")
        result[key] = value
    return result


def _exact_dict(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail("INVALID", f"{label} must be an exact mapping")
    return value


def _exact_list(value: Any, label: str) -> list[Any]:
    if type(value) is not list:
        _fail("INVALID", f"{label} must be an exact list")
    return value


def _exact_string(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        _fail("INVALID", f"{label} must be a non-empty string")
    return value


def _require_keys(record: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if set(record) != set(expected):
        _fail("INVALID", f"{label} fields are not the closed schema")


def _require_sha256(value: Any, label: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _fail("INVALID", f"{label} must be lowercase SHA-256")
    return value


def _require_commit(value: Any, label: str) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        _fail("INVALID", f"{label} must be a full lowercase Git commit id")
    return value


def _safe_path(value: Any, label: str) -> str:
    text = _exact_string(value, label)
    if "\\" in text or text.startswith("/"):
        _fail("INVALID", f"{label} must be repository-relative with '/' separators")
    try:
        text.encode("utf-8", "strict")
    except UnicodeError:
        _fail("INVALID", f"{label} is not strict UTF-8")
    path = PurePosixPath(text)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        _fail("INVALID", f"{label} is not a normalized repository-relative path")
    if path.as_posix() != text:
        _fail("INVALID", f"{label} is not normalized")
    return text


def _canonical_strings(value: Any, label: str, *, paths: bool = False) -> tuple[str, ...]:
    raw = _exact_list(value, label)
    result: list[str] = []
    for index, item in enumerate(raw):
        text = _safe_path(item, f"{label}[{index}]") if paths else _exact_string(item, f"{label}[{index}]")
        result.append(text)
    expected = sorted(set(result), key=lambda item: item.encode("utf-8"))
    if result != expected:
        _fail("INVALID", f"{label} must be unique and bytewise UTF-8 sorted")
    return tuple(result)


def parse_epoch_record(raw: bytes) -> dict[str, Any]:
    """Parse one exact canonical evaluator_epoch.v0 record."""
    if type(raw) is not bytes:
        _fail("INVALID", "epoch record must be exact bytes")
    try:
        text = raw.decode("utf-8", "strict")
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except EvaluatorClosureError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        _fail("INVALID", "epoch record must be strict UTF-8 JSON")
    record = _exact_dict(parsed, "epoch record")
    if raw != _canonical_bytes(record):
        _fail("INVALID", "epoch record bytes are not canonical JSON")
    _require_keys(record, _EPOCH_FIELDS, "epoch record")
    if record["schema_version"] != EPOCH_SCHEMA_VERSION:
        _fail("INVALID", "epoch schema_version mismatch")
    if type(record["authority"]) is not bool or record["authority"]:
        _fail("INVALID", "epoch authority must be exact false")
    _exact_string(record["epoch_id"], "epoch_id")
    _require_commit(record["accepted_base_commit"], "accepted_base_commit")
    if record["approval_status"] not in {"HUMAN_APPROVED", "UNAPPROVED"}:
        _fail("INVALID", "approval_status is not closed")
    _exact_string(record["human_approval_ref"], "human_approval_ref")

    checker = _exact_dict(record["checker"], "checker")
    _require_keys(checker, _CHECKER_FIELDS, "checker")
    if checker["source"] != "ACCEPTED_BASE":
        _fail("INVALID", "checker source must be ACCEPTED_BASE")
    checker_path = _safe_path(checker["relative_path"], "checker.relative_path")
    _require_sha256(checker["sha256"], "checker.sha256")

    entrypoints = _canonical_strings(
        record["evaluator_entrypoints"], "evaluator_entrypoints", paths=True
    )
    if not entrypoints:
        _fail("INVALID", "evaluator_entrypoints must not be empty")

    ess_raw = _exact_list(record["ess"], "ess")
    if not ess_raw:
        _fail("INVALID", "ess must not be empty")
    ess_paths: list[str] = []
    for index, item in enumerate(ess_raw):
        entry = _exact_dict(item, f"ess[{index}]")
        _require_keys(entry, _ESS_FIELDS, f"ess[{index}]")
        ess_paths.append(_safe_path(entry["relative_path"], f"ess[{index}].relative_path"))
        _require_sha256(entry["sha256"], f"ess[{index}].sha256")
    expected_paths = sorted(set(ess_paths), key=lambda item: item.encode("utf-8"))
    if ess_paths != expected_paths:
        _fail("INVALID", "ESS paths must be unique and bytewise UTF-8 sorted")

    semantic_config = _exact_dict(record["semantic_config"], "semantic_config")
    _require_keys(semantic_config, _SEMANTIC_CONFIG_FIELDS, "semantic_config")
    if semantic_config["caller_semantic_input"] != "REJECT":
        _fail("INVALID", "caller_semantic_input must be REJECT")
    _canonical_strings(
        semantic_config["non_semantic_external_imports"],
        "non_semantic_external_imports",
    )

    policy = _exact_dict(record["closure_policy"], "closure_policy")
    _require_keys(policy, _POLICY_FIELDS, "closure_policy")
    declaration_paths = _canonical_strings(
        policy["epoch_declaration_paths"], "epoch_declaration_paths", paths=True
    )
    if not declaration_paths:
        _fail("INVALID", "epoch_declaration_paths must not be empty")
    _canonical_strings(policy["non_semantic_paths"], "non_semantic_paths", paths=True)

    ess_set = set(ess_paths)
    required_members = {checker_path, *entrypoints, *declaration_paths}
    if not required_members <= ess_set:
        _fail("INVALID", "checker, entrypoints, and epoch declarations must be ESS members")
    return record


def _git(root: Path, *arguments: str, binary: bool = False) -> bytes | str:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=not binary,
        check=False,
        env=environment,
    )
    if result.returncode != 0:
        detail = result.stderr if not binary else result.stderr.decode("utf-8", "replace")
        raise RuntimeError(detail.strip() or "git object read failed")
    return result.stdout


def _commit_exists(root: Path, commit: str) -> bool:
    try:
        _git(root, "cat-file", "-e", f"{commit}^{{commit}}")
        return True
    except RuntimeError:
        return False


def _is_ancestor(root: Path, base: str, proposal: str) -> bool:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, proposal],
        cwd=root,
        capture_output=True,
        check=False,
        env=environment,
    )
    return result.returncode == 0


def _tree_paths(root: Path, commit: str) -> set[str]:
    raw = _git(root, "ls-tree", "-r", "--name-only", "-z", commit, binary=True)
    assert isinstance(raw, bytes)
    return {
        item.decode("utf-8", "strict")
        for item in raw.split(b"\0")
        if item
    }


def _blob(root: Path, commit: str, path: str) -> bytes:
    listing = _git(root, "ls-tree", "-z", commit, "--", path, binary=True)
    assert isinstance(listing, bytes)
    records = [item for item in listing.split(b"\0") if item]
    if len(records) != 1:
        _fail("INVALID", f"ESS file is missing: {path}")
    metadata, listed_path = records[0].split(b"\t", 1)
    mode, object_type, _object_id = metadata.split(b" ", 2)
    if listed_path.decode("utf-8", "strict") != path:
        _fail("INVALID", f"ESS path did not resolve exactly: {path}")
    if mode == b"120000" or object_type != b"blob":
        _fail("INVALID", f"ESS path is not a regular tracked blob: {path}")
    try:
        content = _git(root, "show", f"{commit}:{path}", binary=True)
    except RuntimeError:
        _fail("INVALID", f"ESS file is unreadable: {path}")
    assert isinstance(content, bytes)
    return content


def _verify_ess_inventory(root: Path, record: Mapping[str, Any]) -> None:
    base = record["accepted_base_commit"]
    for entry in record["ess"]:
        content = _blob(root, base, entry["relative_path"])
        if _sha256(content) != entry["sha256"]:
            _fail("INVALID", f"ESS hash mismatch: {entry['relative_path']}")


def _verify_checker(root: Path, record: Mapping[str, Any]) -> None:
    checker = record["checker"]
    if checker["relative_path"] != CHECKER_RELATIVE_PATH:
        _fail("EPOCH_MISMATCH", "epoch checker path does not name this checker")
    trusted_bytes = _blob(root, record["accepted_base_commit"], checker["relative_path"])
    runtime_bytes = Path(__file__).read_bytes()
    if _sha256(trusted_bytes) != checker["sha256"]:
        _fail("EPOCH_MISMATCH", "accepted-base checker does not match epoch pin")
    if _sha256(runtime_bytes) != checker["sha256"]:
        _fail("EPOCH_MISMATCH", "executing checker does not match trusted epoch pin")


def _changed_paths_between(root: Path, base: str, proposal: str) -> tuple[str, ...]:
    raw = _git(
        root,
        "diff",
        "--name-only",
        "--no-renames",
        "-z",
        base,
        proposal,
        "--",
        binary=True,
    )
    assert isinstance(raw, bytes)
    paths = [item.decode("utf-8", "strict") for item in raw.split(b"\0") if item]
    return tuple(sorted(set(paths), key=lambda item: item.encode("utf-8")))


def _changed_paths(root: Path, base: str, proposal: str) -> tuple[str, ...]:
    return _changed_paths_between(root, base, proposal)


def _changed_paths_from_parent(root: Path, _base: str, proposal: str) -> tuple[str, ...]:
    """Mutation-test primitive: the forbidden proposal-parent comparison."""
    parent = str(_git(root, "rev-parse", f"{proposal}^")).strip()
    return _changed_paths_between(root, parent, proposal)


def _dotted_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def _module_candidates(module: str) -> tuple[str, str]:
    stem = module.replace(".", "/")
    return f"{stem}.py", f"{stem}/__init__.py"


def _resolve_module(
    module: str,
    tree: set[str],
    ess: set[str],
    allowed_external: set[str],
    findings: list[str],
    queue: list[str],
) -> None:
    file_path, package_path = _module_candidates(module)
    present = [path for path in (file_path, package_path) if path in tree]
    if len(present) > 1:
        findings.append(f"shadow module ambiguity: {module}")
        return
    if len(present) == 1:
        path = present[0]
        if path not in ess:
            findings.append(f"repo-local import outside ESS: {path}")
            return
        queue.append(path)
        return
    top_level = module.split(".", 1)[0]
    repo_local = any(
        path == f"{top_level}.py" or path.startswith(f"{top_level}/") for path in tree
    )
    if repo_local or top_level not in allowed_external:
        findings.append(f"unresolved import: {module}")


def _literal_read_path(call: ast.Call) -> str | None:
    if not call.args or not isinstance(call.args[0], ast.Constant):
        return None
    value = call.args[0].value
    return value if type(value) is str else None


def _pathlib_read_path(call: ast.Call) -> tuple[bool, str | None]:
    if not isinstance(call.func, ast.Attribute):
        return False, None
    if call.func.attr not in {"open", "read_bytes", "read_text"}:
        return False, None
    constructor = call.func.value
    if not isinstance(constructor, ast.Call):
        return False, None
    if _dotted_name(constructor.func) not in {"Path", "pathlib.Path"}:
        return False, None
    return True, _literal_read_path(constructor)


def _proposal_shadow_findings(
    root: Path, record: Mapping[str, Any], proposal: str
) -> tuple[str, ...]:
    base_tree = _tree_paths(root, record["accepted_base_commit"])
    proposal_tree = _tree_paths(root, proposal)
    findings: list[str] = []
    for entry in record["ess"]:
        path = entry["relative_path"]
        if path.endswith("/__init__.py"):
            alternative = f"{path[:-len('/__init__.py')]}.py"
        elif path.endswith(".py"):
            alternative = f"{path[:-3]}/__init__.py"
        else:
            continue
        if alternative in proposal_tree and alternative not in base_tree:
            findings.append(f"proposal-local shadow module: {alternative}")
    return tuple(sorted(set(findings), key=lambda item: item.encode("utf-8")))


def _analyze_reach(root: Path, record: Mapping[str, Any]) -> tuple[str, ...]:
    base = record["accepted_base_commit"]
    tree = _tree_paths(root, base)
    ess = {entry["relative_path"] for entry in record["ess"]}
    allowed_external = set(
        record["semantic_config"]["non_semantic_external_imports"]
    )
    queue = list(record["evaluator_entrypoints"])
    visited: set[str] = set()
    findings: list[str] = []

    while queue:
        path = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)
        if path not in ess:
            findings.append(f"semantic entrypoint outside ESS: {path}")
            continue
        if not path.endswith(".py"):
            continue
        try:
            source = _blob(root, base, path).decode("utf-8", "strict")
            syntax = ast.parse(source, filename=path)
        except (UnicodeDecodeError, SyntaxError):
            findings.append(f"unparseable semantic Python: {path}")
            continue

        package_parts = list(PurePosixPath(path).parent.parts)
        for node in ast.walk(syntax):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets: list[ast.AST] = []
                if isinstance(node, ast.Assign):
                    targets.extend(node.targets)
                else:
                    targets.append(node.target)
                if any((_dotted_name(target) or "").startswith("sys.path") for target in targets):
                    findings.append(f"sys.path manipulation: {path}")
            if isinstance(node, ast.Call):
                called = _dotted_name(node.func)
                if called in _DYNAMIC_CALLS:
                    findings.append(f"dynamic semantic loading: {path}")
                if called in _PATH_MUTATORS:
                    findings.append(f"sys.path manipulation: {path}")
                if called in {"open", "io.open"}:
                    literal = _literal_read_path(node)
                    if literal is None:
                        findings.append(f"dynamic semantic data read: {path}")
                    else:
                        try:
                            read_path = _safe_path(literal, "semantic read path")
                        except EvaluatorClosureError:
                            findings.append(f"unresolved semantic data read: {path}")
                        else:
                            if read_path not in ess:
                                findings.append(f"semantic data read outside ESS: {read_path}")
                is_pathlib_read, pathlib_literal = _pathlib_read_path(node)
                if is_pathlib_read:
                    if pathlib_literal is None:
                        findings.append(f"dynamic pathlib semantic data read: {path}")
                    else:
                        try:
                            read_path = _safe_path(pathlib_literal, "semantic read path")
                        except EvaluatorClosureError:
                            findings.append(f"unresolved pathlib semantic data read: {path}")
                        else:
                            if read_path not in ess:
                                findings.append(
                                    f"pathlib semantic data read outside ESS: {read_path}"
                                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    _resolve_module(
                        alias.name, tree, ess, allowed_external, findings, queue
                    )
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    remove = node.level - 1
                    if remove > len(package_parts):
                        findings.append(f"unresolved relative import: {path}")
                        continue
                    base_parts = package_parts[: len(package_parts) - remove]
                    if node.module:
                        modules = [".".join([*base_parts, *node.module.split(".")])]
                    else:
                        modules = [".".join([*base_parts, alias.name]) for alias in node.names]
                    for module in modules:
                        if not module:
                            findings.append(f"unresolved relative import: {path}")
                        else:
                            _resolve_module(
                                module, tree, ess, allowed_external, findings, queue
                            )
                elif node.module:
                    _resolve_module(
                        node.module, tree, ess, allowed_external, findings, queue
                    )

    return tuple(sorted(set(findings), key=lambda item: item.encode("utf-8")))


def _caller_semantic_input_present(value: Any) -> bool:
    if value is None:
        return False
    if type(value) is not dict:
        return True
    return bool(value)


def _load_trusted_epoch(root: Path, trusted_epoch_path: str | Path) -> bytes:
    if type(trusted_epoch_path) is not str and not isinstance(trusted_epoch_path, Path):
        _fail("INVALID", "trusted epoch location must be a path")
    supplied = Path(trusted_epoch_path)
    if supplied.is_symlink():
        _fail("INVALID", "trusted epoch location must not be a symlink")
    try:
        resolved = supplied.resolve(strict=True)
    except OSError:
        _fail("INVALID", "trusted epoch location is missing or unreadable")
    if not resolved.is_file():
        _fail("INVALID", "trusted epoch location is not a regular file")
    try:
        resolved.relative_to(root)
    except ValueError:
        pass
    else:
        _fail("INVALID", "trusted epoch location must be outside the proposal repository")
    try:
        return resolved.read_bytes()
    except OSError:
        _fail("INVALID", "trusted epoch location is unreadable")
    raise AssertionError("unreachable")


def _receipt(
    *,
    record: Mapping[str, Any] | None,
    raw_epoch: bytes,
    proposal_commit: str,
    disposition: str,
    changed_paths: tuple[str, ...] = (),
    closure_hits: tuple[str, ...] = (),
    unknown_reach: tuple[str, ...] = (),
) -> dict[str, Any]:
    if disposition not in DISPOSITIONS:
        raise ValueError("receipt disposition is not closed")
    checker = record.get("checker", {}) if type(record) is dict else {}
    ess = record.get("ess", []) if type(record) is dict else []
    body: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "authority": False,
        "epoch_id": record.get("epoch_id", "UNRESOLVED") if type(record) is dict else "UNRESOLVED",
        "epoch_record_digest": _sha256(raw_epoch),
        "accepted_base_commit": record.get("accepted_base_commit", "UNRESOLVED") if type(record) is dict else "UNRESOLVED",
        "proposal_commit": proposal_commit,
        "checker_sha256": checker.get("sha256", "UNRESOLVED") if type(checker) is dict else "UNRESOLVED",
        "ess_digest": canonical_digest(ess),
        "disposition": disposition,
        "changed_paths": list(changed_paths),
        "closure_hits": list(closure_hits),
        "unknown_reach": list(unknown_reach),
        "limitations": list(_LIMITATIONS),
    }
    body["receipt_digest"] = canonical_digest(body)
    validate_closure_receipt(body)
    return body


def validate_closure_receipt(receipt: Any) -> None:
    """Validate one non-authoritative evaluator_closure.v0 receipt."""
    if type(receipt) is not dict or set(receipt) != set(_RECEIPT_FIELDS):
        raise ValueError("receipt fields are not the closed schema")
    if receipt["schema_version"] != RECEIPT_SCHEMA_VERSION:
        raise ValueError("receipt schema_version mismatch")
    if type(receipt["authority"]) is not bool or receipt["authority"]:
        raise ValueError("receipt authority must be exact false")
    if receipt["disposition"] not in DISPOSITIONS:
        raise ValueError("receipt disposition is not closed")
    for field in ("epoch_id", "accepted_base_commit", "proposal_commit", "checker_sha256"):
        if type(receipt[field]) is not str or not receipt[field]:
            raise ValueError(f"receipt {field} must be a non-empty string")
    for field in ("changed_paths", "closure_hits", "unknown_reach"):
        values = receipt[field]
        if type(values) is not list or any(type(item) is not str for item in values):
            raise ValueError(f"receipt {field} must be a string list")
        if values != sorted(set(values), key=lambda item: item.encode("utf-8")):
            raise ValueError(f"receipt {field} is not canonical")
    if receipt["limitations"] != list(_LIMITATIONS):
        raise ValueError("receipt limitations are not code-owned")
    if _SHA256_RE.fullmatch(receipt["epoch_record_digest"]) is None:
        raise ValueError("epoch_record_digest malformed")
    if _SHA256_RE.fullmatch(receipt["ess_digest"]) is None:
        raise ValueError("ess_digest malformed")
    stored = receipt["receipt_digest"]
    if type(stored) is not str or _SHA256_RE.fullmatch(stored) is None:
        raise ValueError("receipt_digest malformed")
    preimage = dict(receipt)
    del preimage["receipt_digest"]
    if stored != canonical_digest(preimage):
        raise ValueError("receipt_digest mismatch")


def evaluate_closure(
    repository: str | Path,
    trusted_epoch_path: str | Path,
    proposal_commit: str,
    *,
    caller_semantic_input: Any = None,
) -> dict[str, Any]:
    """Evaluate SEIC-v0 closure without writing repository or protected state."""
    root = Path(repository).resolve()
    record: dict[str, Any] | None = None
    safe_proposal = (
        proposal_commit
        if type(proposal_commit) is str and _COMMIT_RE.fullmatch(proposal_commit)
        else "UNRESOLVED"
    )
    raw = b""
    try:
        raw = _load_trusted_epoch(root, trusted_epoch_path)
        record = parse_epoch_record(raw)
        proposal = _require_commit(proposal_commit, "proposal_commit")
        base = record["accepted_base_commit"]
        if not _commit_exists(root, base) or not _commit_exists(root, proposal):
            _fail("EPOCH_MISMATCH", "accepted base or proposal commit does not exist")
        if not _is_ancestor(root, base, proposal):
            _fail("EPOCH_MISMATCH", "proposal is not a descendant of accepted base")
        if record["approval_status"] != "HUMAN_APPROVED":
            return _receipt(
                record=record,
                raw_epoch=raw,
                proposal_commit=proposal,
                disposition="REQUIRE_HUMAN_REVIEW",
            )
        _verify_checker(root, record)
        _verify_ess_inventory(root, record)
        if _caller_semantic_input_present(caller_semantic_input):
            return _receipt(
                record=record,
                raw_epoch=raw,
                proposal_commit=proposal,
                disposition="CALLER_SEMANTIC_INPUT",
            )
        changed = _changed_paths(root, base, proposal)
        protected = {
            record["checker"]["relative_path"],
            *(entry["relative_path"] for entry in record["ess"]),
            *record["closure_policy"]["epoch_declaration_paths"],
        }
        hits = tuple(path for path in changed if path in protected)
        if hits:
            return _receipt(
                record=record,
                raw_epoch=raw,
                proposal_commit=proposal,
                disposition="CLOSURE_HIT",
                changed_paths=changed,
                closure_hits=hits,
            )
        unknown = tuple(
            sorted(
                set(_analyze_reach(root, record))
                | set(_proposal_shadow_findings(root, record, proposal)),
                key=lambda item: item.encode("utf-8"),
            )
        )
        if unknown:
            return _receipt(
                record=record,
                raw_epoch=raw,
                proposal_commit=proposal,
                disposition="UNKNOWN_REACH",
                changed_paths=changed,
                unknown_reach=unknown,
            )
        return _receipt(
            record=record,
            raw_epoch=raw,
            proposal_commit=proposal,
            disposition="PASS",
            changed_paths=changed,
        )
    except EvaluatorClosureError as exc:
        return _receipt(
            record=record,
            raw_epoch=raw,
            proposal_commit=safe_proposal,
            disposition=exc.disposition,
            unknown_reach=(exc.message,) if exc.disposition == "UNKNOWN_REACH" else (),
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        return _receipt(
            record=record,
            raw_epoch=raw,
            proposal_commit=safe_proposal,
            disposition="INVALID",
            unknown_reach=(f"closed internal failure: {type(exc).__name__}",),
        )


__all__ = [
    "CHECKER_RELATIVE_PATH",
    "DISPOSITIONS",
    "EPOCH_SCHEMA_VERSION",
    "EvaluatorClosureError",
    "RECEIPT_SCHEMA_VERSION",
    "evaluate_closure",
    "parse_epoch_record",
    "validate_closure_receipt",
]
