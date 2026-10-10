"""Pure EB-0 decision for a supplied MinGit execution tree.

The inputs are plain data. String normalization does not inspect the
filesystem, reparse points, the Windows loader, ACLs, or a live process.
Those properties stay UNVERIFIED. A tree match does not ratify the
operational pin and cannot return PASS.
"""

from __future__ import annotations

import re

from docs.inr_her_001.supervisor_her_v1 import classify_git_pin

SCHEMA_VERSION = "inr.her.mingit.execution_binding.v0"
RATIFIED_DISTRIBUTION_SHA256 = "da35e72aa21c005a5a0d298cfbae110bc1609a815730ea0dde84b01a1b3cd3be"
EXCLUDED_SNAPSHOT_SHA256 = "ab2543fea7eebdc8476b63af2ff8acec10fce72fc9f72a40c9123df94c6ac1ae"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ROLES = frozenset({"execution_image", "dependency", "other"})
_FORBIDDEN_MEMBER_DIGESTS = frozenset({
    RATIFIED_DISTRIBUTION_SHA256,
    EXCLUDED_SNAPSHOT_SHA256,
})
_PASS_CLAIMS = frozenset({
    "pass",
    "hash_agreement_only",
    "fresh",
    "isolation_pass",
    "full_inr_pass",
})
_REQUIRED = frozenset({
    "distribution_sha256",
    "tree_root",
    "candidate_path",
    "manifest",
    "observed",
    "dependencies",
    "environment",
    "source",
    "reparse_escape",
    "mingit_sha256_authenticated",
})
_OPTIONAL = frozenset({
    "claimed_status",
    "operational_pin_authorized",
    "execution_authorized",
    "full_inr_ready",
    "isolation_pass",
    "freshness_pass",
})
_AUTH_FLAGS = (
    "mingit_sha256_authenticated",
    "operational_pin_authorized",
    "execution_authorized",
    "full_inr_ready",
    "isolation_pass",
    "freshness_pass",
)
_ACCEPTED_SOURCES = frozenset({"BOUND_TREE", "MINGIT_PINNED"})


def evaluate_execution_binding(document: object) -> dict:
    """Return a fail-closed binding decision for one supplied fixture."""
    reason = _validate(document)
    if reason is not None:
        status, binding, accepted = reason
        return _emit(status, binding, "REFUSED", accepted, None)
    assert type(document) is dict
    image_sha = _image_sha(document)
    return _emit(
        "BLOCKED",
        "HER_GIT_PIN_UNRATIFIED",
        "TREE_MATCH_UNPINNED",
        True,
        image_sha,
    )


def _validate(document: object) -> tuple[str, str, bool] | None:
    if type(document) is not dict or any(key not in _REQUIRED | _OPTIONAL for key in document):
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", False)
    if any(key not in document for key in _REQUIRED):
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", False)
    if _contradicts(document):
        return ("FAIL", "HER_CONTRADICTION", False)
    distribution = document.get("distribution_sha256")
    if distribution == EXCLUDED_SNAPSHOT_SHA256:
        return ("BLOCKED", "HER_GIT_DISTRIBUTION_EXCLUDED", False)
    if type(distribution) is not str or _SHA256.fullmatch(distribution) is None:
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", False)
    if distribution != RATIFIED_DISTRIBUTION_SHA256:
        return ("BLOCKED", "HER_GIT_DISTRIBUTION_REJECTED", False)
    manifest = _members(document.get("manifest"), manifest=True)
    if type(manifest) is tuple:
        return manifest
    if manifest == []:
        return ("BLOCKED", "HER_GIT_MANIFEST_ABSENT", True)
    observed = _members(document.get("observed"), manifest=False)
    if type(observed) is tuple:
        return observed
    dependencies = _dependencies(document.get("dependencies"))
    if type(dependencies) is tuple:
        return dependencies
    root = _absolute(document.get("tree_root"))
    candidate = _absolute(document.get("candidate_path"))
    if root is None or candidate is None or type(document.get("source")) is not str:
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
    if document.get("reparse_escape") is True or not _contained(root, candidate):
        return ("BLOCKED", "HER_GIT_SOURCE_NOT_SNAPSHOT", True)
    if document.get("source") not in _ACCEPTED_SOURCES:
        return ("BLOCKED", "HER_GIT_SOURCE_NOT_SNAPSHOT", True)
    if document.get("reparse_escape") is not False:
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
    relative = _relative_of(root, candidate)
    if relative is None:
        return ("BLOCKED", "HER_GIT_SOURCE_NOT_SNAPSHOT", True)
    if not _tree_matches(manifest, observed, relative):
        return ("BLOCKED", "HER_GIT_TREE_INTEGRITY_REFUSED", True)
    if not _dependencies_match(root, manifest, dependencies):
        return ("BLOCKED", "HER_GIT_DEPENDENCY_REFUSED", True)
    if not _environment_matches(document.get("environment"), candidate):
        return ("BLOCKED", "HER_GIT_PATH_CONTROL_REFUSED", True)
    return None


def _contradicts(document: dict) -> bool:
    for name in _AUTH_FLAGS:
        if document.get(name) is True:
            return True
    claimed = document.get("claimed_status")
    return type(claimed) is str and claimed.strip().casefold().replace("-", "_") in _PASS_CLAIMS


def _members(value: object, *, manifest: bool) -> list[tuple[str, str, str]] | tuple[str, str, bool]:
    if type(value) is not list:
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
    parsed: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict:
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", False)
        allowed = {"relative_path", "sha256", "role"} if manifest else {"relative_path", "sha256"}
        if any(key not in allowed for key in item) or any(key not in item for key in allowed):
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", False)
        relative = _relative(item.get("relative_path"))
        if relative == "TRAVERSAL":
            return ("BLOCKED", "HER_GIT_SOURCE_NOT_SNAPSHOT", True)
        digest = item.get("sha256")
        if relative is None or type(digest) is not str or _SHA256.fullmatch(digest) is None:
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
        role = item.get("role") if manifest else "observed"
        if manifest and (type(role) is not str or role not in _ROLES):
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
        if manifest and not _role_fits(relative, role):
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
        if manifest and digest in _FORBIDDEN_MEMBER_DIGESTS:
            return ("BLOCKED", "HER_GIT_DIGEST_ROLE_MISMATCH", True)
        folded = relative.casefold()
        if folded in seen:
            return ("BLOCKED", "HER_GIT_PATH_COLLISION", True)
        seen.add(folded)
        parsed.append((relative, digest, role if type(role) is str else "observed"))
    return parsed


def _dependencies(value: object) -> list[tuple[tuple[str, tuple[str, ...]], str]] | tuple[str, str, bool]:
    if type(value) is not list:
        return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
    parsed = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for item in value:
        if type(item) is not dict or set(item) != {"path", "sha256"}:
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
        path = _absolute(item.get("path"))
        digest = item.get("sha256")
        if path is None or type(digest) is not str or _SHA256.fullmatch(digest) is None:
            return ("BLOCKED", "HER_BINDING_INPUT_REJECTED", True)
        if _abs_key(path) in seen:
            return ("BLOCKED", "HER_GIT_PATH_COLLISION", True)
        seen.add(_abs_key(path))
        parsed.append((path, digest))
    return parsed


def _tree_matches(
    manifest: list[tuple[str, str, str]],
    observed: list[tuple[str, str, str]],
    candidate: str,
) -> bool:
    expected = {_fold(path): (path, digest, role) for path, digest, role in manifest}
    actual = {_fold(path): digest for path, digest, _role in observed}
    if set(expected) != set(actual):
        return False
    if any(actual[key] != expected[key][1] for key in expected):
        return False
    images = [item for item in manifest if item[2] == "execution_image"]
    if not images or all(_is_shim(path) for path, _digest, _role in images):
        return False
    selected = expected.get(_fold(candidate))
    return selected is not None and selected[2] == "execution_image" and not _is_shim(selected[0])


def _dependencies_match(
    root: tuple[str, tuple[str, ...]],
    manifest: list[tuple[str, str, str]],
    dependencies: list[tuple[tuple[str, tuple[str, ...]], str]],
) -> bool:
    expected = {
        _fold(path): digest
        for path, digest, role in manifest
        if role == "dependency"
    }
    actual: dict[str, str] = {}
    for path, digest in dependencies:
        if not _contained(root, path):
            return False
        relative = _relative_of(root, path)
        if relative is None:
            return False
        key = _fold(relative)
        if key in actual:
            return False
        actual[key] = digest
    return actual == expected


def _environment_matches(value: object, candidate: tuple[str, tuple[str, ...]]) -> bool:
    if type(value) is not dict or any(type(key) is not str or type(item) is not str for key, item in value.items()):
        return False
    git_items = [(key.upper(), item) for key, item in value.items() if key.upper().startswith("GIT_")]
    if git_items != [("GIT_NO_REPLACE_OBJECTS", "1")]:
        return False
    path_items = [item for key, item in value.items() if key.upper() == "PATH"]
    if len(path_items) != 1:
        return False
    parent = (candidate[0], candidate[1][:-1])
    return _one_path(path_items[0], parent)


def _one_path(value: object, parent: tuple[str, tuple[str, ...]]) -> bool:
    if type(value) is not str or value == "" or ";" in value:
        return False
    parsed = _absolute(value)
    return parsed is not None and _abs_key(parsed) == _abs_key(parent)


def _role_fits(relative: str, role: str) -> bool:
    is_git = relative.casefold().endswith("/git.exe") or relative.casefold() == "git.exe"
    if is_git:
        return role == "execution_image"
    return role != "execution_image"


def _is_shim(relative: str) -> bool:
    parts = relative.casefold().split("/")
    return len(parts) >= 2 and parts[-2] == "cmd" and parts[-1] == "git.exe"


def _image_sha(document: dict) -> str | None:
    root = _absolute(document.get("tree_root"))
    candidate = _absolute(document.get("candidate_path"))
    if root is None or candidate is None:
        return None
    relative = _relative_of(root, candidate)
    if relative is None or type(document.get("manifest")) is not list:
        return None
    for item in document.get("manifest"):
        if type(item) is dict and type(item.get("relative_path")) is str:
            parsed = _relative(item.get("relative_path"))
            if type(parsed) is str and _fold(parsed) == _fold(relative) and type(item.get("sha256")) is str:
                return item.get("sha256")
    return None


def _relative(value: object) -> str | None:
    if type(value) is not str or value == "" or value != value.strip():
        return None
    text = value.replace("\\", "/")
    if text.startswith("/") or (len(text) >= 2 and text[1] == ":"):
        return None
    parts: list[str] = []
    for part in text.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            return "TRAVERSAL"
        parts.append(part)
    if not parts:
        return None
    return "/".join(parts)


def _absolute(value: object) -> tuple[str, tuple[str, ...]] | None:
    if type(value) is not str or value == "" or value != value.strip():
        return None
    text = value.replace("\\", "/")
    if text.startswith("//") or len(text) < 3 or text[1] != ":" or text[2] != "/":
        return None
    drive = text[0]
    if not drive.isalpha():
        return None
    parts: list[str] = []
    for part in text[3:].split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(part)
    return (drive.upper(), tuple(parts))


def _contained(root: tuple[str, tuple[str, ...]], path: tuple[str, tuple[str, ...]]) -> bool:
    if root[0] != path[0] or len(path[1]) <= len(root[1]):
        return False
    return tuple(part.casefold() for part in path[1][: len(root[1])]) == tuple(
        part.casefold() for part in root[1]
    )


def _relative_of(
    root: tuple[str, tuple[str, ...]],
    path: tuple[str, tuple[str, ...]],
) -> str | None:
    if not _contained(root, path):
        return None
    return "/".join(path[1][len(root[1]) :])


def _fold(relative: str) -> str:
    return relative.casefold()


def _abs_key(path: tuple[str, tuple[str, ...]]) -> tuple[str, tuple[str, ...]]:
    return (path[0], tuple(part.casefold() for part in path[1]))


def _emit(
    status: str,
    reason: str,
    binding: str,
    distribution_accepted: bool,
    image_sha: str | None,
) -> dict:
    if status == "PASS" or reason in _PASS_CLAIMS:
        status, reason = "BLOCKED", "HER_PHASE1_PASS_FORBIDDEN"
    pin_status, pin_reason = classify_git_pin(image_sha)
    if pin_status == "PASS" or pin_reason in _PASS_CLAIMS:
        pin_status, pin_reason = "BLOCKED", "HER_PHASE1_PASS_FORBIDDEN"
    return {
        "schema_version": SCHEMA_VERSION,
        "overall_status": status,
        "overall_reason": reason,
        "binding_result": binding,
        "operational_pin_status": pin_status,
        "operational_pin_reason": pin_reason,
        "distribution_accepted": distribution_accepted,
        "filesystem_verification": "UNVERIFIED",
        "reparse_verification": "UNVERIFIED",
        "loader_verification": "UNVERIFIED",
        "acl_verification": "UNVERIFIED",
        "process_isolation": "UNVERIFIED",
        "execution_binding_real": "UNEXECUTED",
        "operational_mingit_pin": "UNRATIFIED",
        "full_inr_ready": False,
        "isolation_pass": False,
        "freshness_pass": False,
    }
