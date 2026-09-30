"""Disposable-root confinement and exact Git-blob tracked-tree export for WVMA-V1 A2."""

from __future__ import annotations

import hashlib
import io
import os
import re
import stat
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Iterable, Mapping

from wvma_v1.canonical import canonical_digest, sha256_file
from wvma_v1.models import (
    SAFE_PATH_COMPONENT_MAX_LEN,
    _WINDOWS_RESERVED_DEVICE_NAMES,
)

# Relative path components: same closed ASCII grammar as A1 identifiers.
_REL_COMPONENT_RE = re.compile(
    rf"\A[A-Za-z0-9_][A-Za-z0-9_.-]{{0,{SAFE_PATH_COMPONENT_MAX_LEN - 1}}}\Z"
)
_GIT_REV_RE = re.compile(r"\A[0-9a-f]{40}\Z")
_SHA256_EMPTY = hashlib.sha256(b"").hexdigest()


class WorkspaceError(ValueError):
    """Disposable workspace / export confinement rejection."""


def validate_relative_path(value: object, field: str = "relative_path") -> str:
    """Validate a POSIX-style relative path confined to a disposable root.

    Rejects absolute/drive/UNC/ADS forms, traversal, empty/dot segments,
    backslashes, controls, Windows reserved device names, and overlong
    components. Validation is complete before any filesystem write.
    """
    if value is None:
        raise WorkspaceError(f"{field} is PRESENT-invalid: null")
    if isinstance(value, bool) or not isinstance(value, str):
        raise WorkspaceError(f"{field} must be str; got {type(value).__name__}")
    if value == "":
        raise WorkspaceError(f"{field} must be non-empty str")
    if "\x00" in value:
        raise WorkspaceError(f"{field} must not contain NUL")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise WorkspaceError(f"{field} must not contain control characters")
    if value.startswith("/") or value.startswith("\\"):
        raise WorkspaceError(f"{field} must be relative")
    if "\\" in value:
        raise WorkspaceError(f"{field} must use '/' separators only")
    if ":" in value:
        raise WorkspaceError(f"{field} must not contain colon")
    if value.startswith("./") or "/./" in value or value.endswith("/."):
        raise WorkspaceError(f"{field} must not contain '.' segments")
    parts = value.split("/")
    if any(p == "" for p in parts):
        raise WorkspaceError(f"{field} must not contain empty segments")
    for part in parts:
        if part in {".", ".."}:
            raise WorkspaceError(f"{field} must not contain dot segments")
        if part.endswith(".") or part.endswith(" "):
            raise WorkspaceError(f"{field} component must not trail dot/space")
        if len(part) > SAFE_PATH_COMPONENT_MAX_LEN:
            raise WorkspaceError(
                f"{field} component exceeds max length {SAFE_PATH_COMPONENT_MAX_LEN}"
            )
        if _REL_COMPONENT_RE.match(part) is None:
            raise WorkspaceError(
                f"{field} components must be ASCII "
                f"[A-Za-z0-9_][A-Za-z0-9_.-]* length 1..{SAFE_PATH_COMPONENT_MAX_LEN}"
            )
        stem = part.split(".")[0].upper()
        if stem in _WINDOWS_RESERVED_DEVICE_NAMES:
            raise WorkspaceError(
                f"{field} must not use Windows reserved device name: {part}"
            )
    return value


def _resolve(path: Path) -> Path:
    return Path(path).resolve(strict=False)


def _is_reparse_point(path: Path) -> bool:
    """True for symlinks or Windows junctions/reparse points."""
    if path.is_symlink():
        return True
    try:
        st = os.lstat(path)
    except OSError:
        return False
    # Windows FILE_ATTRIBUTE_REPARSE_POINT == 0x400
    reparse_attr = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    mode_attrs = getattr(st, "st_file_attributes", 0)
    if mode_attrs & reparse_attr:
        return True
    try:
        os.readlink(path)
        return True
    except OSError:
        return False


def assert_no_reparse_chain(path: Path | str, *, field: str = "path") -> Path:
    """Reject if any existing path component is a symlink/junction/reparse point."""
    target = Path(path)
    try:
        parts = target.parts
        if not parts:
            return target
        current = Path(parts[0])
        # Absolute paths: first part is anchor ('C:\\' / '/'); still inspect if present.
        if current.exists(follow_symlinks=False) and _is_reparse_point(current):
            raise WorkspaceError(f"{field} contains reparse point: {current}")
        for part in parts[1:]:
            current = current / part
            if current.exists(follow_symlinks=False) and _is_reparse_point(current):
                raise WorkspaceError(f"{field} contains reparse point: {current}")
    except WorkspaceError:
        raise
    except OSError as exc:
        raise WorkspaceError(f"{field} reparse inspection failed: {exc}") from exc
    return target


def _is_under_or_equal(path: Path, root: Path) -> bool:
    if path == root:
        return True
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _paths_overlap(a: Path, b: Path) -> bool:
    """True when either path equals or contains the other."""
    ra = _resolve(a)
    rb = _resolve(b)
    return _is_under_or_equal(ra, rb) or _is_under_or_equal(rb, ra)


def _assert_outside_protected(
    candidate: Path,
    protected: Iterable[Path | str],
    *,
    field: str,
    allow_parent_of_protected: bool = False,
) -> None:
    """Reject candidate when it aliases a protected location.

    When ``allow_parent_of_protected`` is True (disposable parent dirs), the
    candidate may be an ancestor of a protected path so siblings can be created
    beside a fixture repo. The created disposable root itself must still use
    full overlap rejection.
    """
    cand = _resolve(candidate)
    for item in protected:
        prot = _resolve(Path(item))
        if allow_parent_of_protected:
            if _is_under_or_equal(cand, prot):
                raise WorkspaceError(
                    f"{field} is inside protected path: {cand} vs {prot}"
                )
            continue
        if _paths_overlap(cand, prot):
            raise WorkspaceError(
                f"{field} overlaps protected path: {cand} vs {prot}"
            )


def create_disposable_root(
    *,
    parent: Path | str | None = None,
    prefix: str = "wvma-disp-",
    protected_paths: Iterable[Path | str] = (),
    active_repository: Path | str | None = None,
) -> Path:
    """Create an exclusive disposable directory outside the active repository.

    The directory is created with exist_ok=False semantics (via mkdtemp) under
    ``parent`` (default: system temp). Parent and result must not overlap
    protected paths or the active repository checkout.
    """
    if not isinstance(prefix, str) or not prefix or "/" in prefix or "\\" in prefix:
        raise WorkspaceError("prefix must be a non-empty single path component")
    if prefix.startswith("."):
        raise WorkspaceError("prefix must not be a dot segment")

    parent_path = Path(parent) if parent is not None else Path(tempfile.gettempdir())
    parent_path = _resolve(parent_path)
    if not parent_path.is_dir():
        raise WorkspaceError(f"disposable parent is not a directory: {parent_path}")

    protected_list = [Path(p) for p in protected_paths]
    if active_repository is not None:
        protected_list.append(Path(active_repository))

    _assert_outside_protected(
        parent_path,
        protected_list,
        field="disposable parent",
        allow_parent_of_protected=True,
    )
    assert_no_reparse_chain(parent_path, field="disposable parent")

    # mkdtemp is exclusive-create under parent.
    try:
        created = Path(tempfile.mkdtemp(prefix=prefix, dir=str(parent_path)))
    except OSError as exc:
        raise WorkspaceError(f"exclusive disposable create failed: {exc}") from exc

    created = _resolve(created)
    try:
        if created.parent != parent_path:
            raise WorkspaceError("disposable root escaped requested parent")
        if not created.name.startswith(prefix):
            raise WorkspaceError("disposable root name prefix mismatch")
        _assert_outside_protected(created, protected_list, field="disposable root")
        assert_no_reparse_chain(created, field="disposable root")
    except WorkspaceError:
        # Best-effort cleanup of the exclusive directory we just created.
        try:
            created.rmdir()
        except OSError:
            pass
        raise
    return created


def _validate_git_revision(revision: object) -> str:
    if revision is None:
        raise WorkspaceError("revision is PRESENT-invalid: null")
    if isinstance(revision, bool) or not isinstance(revision, str):
        raise WorkspaceError(f"revision must be str; got {type(revision).__name__}")
    if revision == "":
        raise WorkspaceError("revision must be non-empty str")
    if revision.startswith("-"):
        raise WorkspaceError("revision must not look like a CLI flag")
    if any(c in revision for c in " \t\n\r\"'\\"):
        raise WorkspaceError("revision contains unsafe characters")
    # Prefer full commit SHA; also allow HEAD for local test fixtures only when exact.
    if revision != "HEAD" and _GIT_REV_RE.match(revision) is None:
        raise WorkspaceError("revision must be HEAD or a full 40-char lowercase SHA")
    return revision


def _validate_repo_root(repo_root: Path) -> Path:
    root = _resolve(repo_root)
    if not (root / ".git").exists():
        raise WorkspaceError(f"repo_root is not a git repository: {root}")
    assert_no_reparse_chain(root, field="repo_root")
    return root


def _run_git(repo_root: Path, args: list[str]) -> bytes:
    """Fixed-argument Git invocation; never uses shell=True."""
    argv = [
        "git",
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.eol=lf",
        *args,
    ]
    try:
        proc = subprocess.run(
            argv,
            cwd=str(repo_root),
            capture_output=True,
            shell=False,
            check=False,
        )
    except OSError as exc:
        raise WorkspaceError(f"git invocation failed: {exc}") from exc
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")
        raise WorkspaceError(f"git failed ({proc.returncode}): {err}")
    return proc.stdout


def _validate_tar_member(name: str, member: tarfile.TarInfo) -> str:
    """Validate one archive member before any extraction write."""
    # git archive may emit pax global headers; skip non-file/dir payload names later.
    if member.issym() or member.islnk():
        raise WorkspaceError(f"archive rejects link member: {name}")
    if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
        raise WorkspaceError(f"archive rejects special member: {name}")
    if not (member.isfile() or member.isdir()):
        raise WorkspaceError(f"archive rejects unsupported member type: {name}")
    # Normalize git archive names (no leading ./).
    rel = name.replace("\\", "/")
    if rel in {"", "."}:
        raise WorkspaceError("archive member path is empty")
    if rel.endswith("/"):
        rel = rel[:-1]
    validated = validate_relative_path(rel, field="archive.member")
    return validated


def export_tracked_tree(
    *,
    repo_root: Path | str,
    revision: str,
    destination: Path | str,
    protected_paths: Iterable[Path | str] = (),
    pathspecs: tuple[str, ...] | None = None,
) -> dict[str, str]:
    """Export tracked tree bytes from Git objects into ``destination``.

    Uses ``git -c core.autocrlf=false archive`` so content matches blob bytes
    even when the active worktree has ``core.autocrlf=true``. Archive members
    are fully validated before any write. Returns relative-path → sha256 map.
    """
    root = _validate_repo_root(Path(repo_root))
    rev = _validate_git_revision(revision)
    dest = _resolve(Path(destination))
    if dest.exists() and any(dest.iterdir()):
        raise WorkspaceError(f"destination is not empty: {dest}")
    # Destination confinement checks before any content write. Directory may be
    # created only after the archive has been fetched and fully validated.
    if dest.exists():
        assert_no_reparse_chain(dest, field="export destination")
    else:
        assert_no_reparse_chain(dest.parent, field="export destination parent")
    _assert_outside_protected(
        dest,
        [Path(p) for p in protected_paths] + [root],
        field="export destination",
    )

    args = ["archive", "--format=tar", rev]
    if pathspecs:
        for spec in pathspecs:
            validate_relative_path(spec, field="pathspec")
        args.append("--")
        args.extend(list(pathspecs))
    archive_bytes = _run_git(root, args)

    try:
        tar = tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:")
    except tarfile.TarError as exc:
        raise WorkspaceError(f"invalid git archive: {exc}") from exc

    # Pass 1: validate all members and detect collisions before any write.
    planned: list[tuple[str, tarfile.TarInfo]] = []
    seen_fold: dict[str, str] = {}
    for member in tar.getmembers():
        name = member.name
        if name in {"pax_global_header", "pax_global_header/"}:
            continue
        if name.startswith("pax_global_header"):
            continue
        rel = _validate_tar_member(name, member)
        fold = rel.casefold()
        prior = seen_fold.get(fold)
        if prior is not None and prior != rel:
            raise WorkspaceError(
                f"archive path collision under case-insensitive FS: {prior} vs {rel}"
            )
        if fold in seen_fold and member.isfile():
            # Exact duplicate file path in archive.
            raise WorkspaceError(f"archive duplicate path: {rel}")
        seen_fold[fold] = rel
        planned.append((rel, member))

    dest.mkdir(parents=True, exist_ok=True)
    assert_no_reparse_chain(dest, field="export destination")

    # Pass 2: materialize validated members only.
    inventory: dict[str, str] = {}
    for rel, member in planned:
        target = dest / Path(*rel.split("/"))
        # Reject escape even after join (defense in depth).
        resolved_target = _resolve(target)
        try:
            resolved_target.relative_to(dest)
        except ValueError as exc:
            raise WorkspaceError(f"archive member escapes destination: {rel}") from exc
        assert_no_reparse_chain(target.parent, field="export parent")
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
            assert_no_reparse_chain(target, field="export dir")
            continue
        # file
        target.parent.mkdir(parents=True, exist_ok=True)
        extracted = tar.extractfile(member)
        if extracted is None:
            raise WorkspaceError(f"archive member not readable: {rel}")
        data = extracted.read()
        if member.size >= 0 and len(data) != member.size:
            raise WorkspaceError(f"archive member size mismatch: {rel}")
        # Exclusive create: refuse overwrite.
        if target.exists():
            raise WorkspaceError(f"export target already exists: {rel}")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
        fd = os.open(str(target), flags, 0o644)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        inventory[rel] = hashlib.sha256(data).hexdigest()

    tar.close()
    return dict(sorted(inventory.items()))


def inventory_tree(root: Path | str) -> dict[str, str]:
    """SHA-256 inventory of regular files under root (relative POSIX paths)."""
    base = _resolve(Path(root))
    if not base.is_dir():
        raise WorkspaceError(f"inventory root is not a directory: {base}")
    assert_no_reparse_chain(base, field="inventory root")
    out: dict[str, str] = {}
    seen_fold: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(base, followlinks=False):
        current = Path(dirpath)
        # Refuse to descend into reparse points.
        if _is_reparse_point(current) and current != base:
            raise WorkspaceError(f"inventory hit reparse point: {current}")
        # Filter dirnames in place to skip reparse children.
        keep_dirs: list[str] = []
        for name in list(dirnames):
            child = current / name
            if _is_reparse_point(child):
                raise WorkspaceError(f"inventory hit reparse point: {child}")
            keep_dirs.append(name)
        dirnames[:] = keep_dirs
        for name in filenames:
            path = current / name
            if _is_reparse_point(path):
                raise WorkspaceError(f"inventory hit reparse file: {path}")
            if not path.is_file():
                raise WorkspaceError(f"inventory refuses non-regular file: {path}")
            rel = path.relative_to(base).as_posix()
            validated = validate_relative_path(rel, field="inventory.path")
            fold = validated.casefold()
            if fold in seen_fold and seen_fold[fold] != validated:
                raise WorkspaceError(
                    f"inventory path collision: {seen_fold[fold]} vs {validated}"
                )
            seen_fold[fold] = validated
            out[validated] = sha256_file(path)
    return dict(sorted(out.items()))


def inventory_protected_paths(
    paths: Iterable[Path | str],
) -> dict[str, str]:
    """Byte inventory of protected files/directories (resolved absolute keys)."""
    out: dict[str, str] = {}
    for raw in paths:
        path = _resolve(Path(raw))
        assert_no_reparse_chain(path, field="protected path")
        key = str(path)
        if path.is_file():
            out[key] = sha256_file(path)
        elif path.is_dir():
            # Directory inventory digest over sorted relative file digests.
            tree = inventory_tree(path)
            out[key] = canonical_digest(tree)
        else:
            raise WorkspaceError(f"protected path missing: {path}")
    return dict(sorted(out.items()))


def protected_inventory_digest(inventory: Mapping[str, str]) -> str:
    """Canonical digest of a protected-path inventory mapping."""
    return canonical_digest(dict(sorted(inventory.items())))


def assert_protected_unchanged(
    before: Mapping[str, str],
    after: Mapping[str, str] | None = None,
    *,
    paths: Iterable[Path | str] | None = None,
) -> None:
    """Require protected-path inventory to remain byte-identical."""
    if after is None:
        if paths is None:
            raise WorkspaceError("assert_protected_unchanged requires after or paths")
        after = inventory_protected_paths(paths)
    if dict(before) != dict(after):
        raise WorkspaceError("protected paths changed")


def resolve_under_root(root: Path | str, relative_path: str) -> Path:
    """Resolve ``relative_path`` under ``root`` with full confinement checks."""
    rel = validate_relative_path(relative_path)
    base = _resolve(Path(root))
    if not base.is_dir():
        raise WorkspaceError(f"workspace root is not a directory: {base}")
    assert_no_reparse_chain(base, field="workspace root")
    candidate = base.joinpath(*rel.split("/"))
    # Validate parents that exist for reparse before create/read.
    assert_no_reparse_chain(candidate.parent, field="target parent")
    resolved = _resolve(candidate)
    try:
        resolved.relative_to(base)
    except ValueError as exc:
        raise WorkspaceError(f"path escapes workspace root: {rel}") from exc
    if resolved.exists(follow_symlinks=False) and _is_reparse_point(resolved):
        raise WorkspaceError(f"target is a reparse point: {resolved}")
    return resolved


def ensure_output_root_confined(
    output_root: Path | str,
    *,
    protected_paths: Iterable[Path | str],
    active_repository: Path | str | None = None,
) -> Path:
    """Validate an operator output root does not alias protected locations."""
    out = _resolve(Path(output_root))
    protected = [Path(p) for p in protected_paths]
    if active_repository is not None:
        protected.append(Path(active_repository))
    _assert_outside_protected(out, protected, field="output_root")
    assert_no_reparse_chain(out if out.exists() else out.parent, field="output_root")
    return out


__all__ = [
    "WorkspaceError",
    "validate_relative_path",
    "assert_no_reparse_chain",
    "create_disposable_root",
    "export_tracked_tree",
    "inventory_tree",
    "inventory_protected_paths",
    "protected_inventory_digest",
    "assert_protected_unchanged",
    "resolve_under_root",
    "ensure_output_root_confined",
    "_SHA256_EMPTY",
]
