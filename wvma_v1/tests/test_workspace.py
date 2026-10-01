"""Confinement and Git-blob export tests for WVMA-V1 Batch A2."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from wvma_v1.workspace import (
    WorkspaceError,
    assert_no_reparse_chain,
    assert_protected_unchanged,
    create_disposable_root,
    ensure_output_root_confined,
    export_tracked_tree,
    inventory_protected_paths,
    inventory_tree,
    resolve_under_root,
    validate_relative_path,
)


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", *args],
        cwd=str(repo),
        capture_output=True,
        shell=False,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode())
    return proc.stdout


def _init_fixture_repo(root: Path) -> str:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init")
    _git(root, "config", "user.email", "wvma@example.com")
    _git(root, "config", "user.name", "WVMA")
    _git(root, "config", "core.autocrlf", "true")
    syn = root / "synthetic"
    syn.mkdir()
    artifact = syn / "artifact.json"
    # LF-only blob content even if autocrlf would alter worktree.
    payload = b'{"status":"accepted","n":1}\n'
    # Worktree intentionally CRLF; Git blob pinned to LF via hash-object.
    artifact.write_bytes(payload.replace(b"\n", b"\r\n"))
    proc = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=str(root),
        input=payload,
        capture_output=True,
        shell=False,
        check=True,
    )
    blob = proc.stdout.decode().strip()
    _git(
        root,
        "update-index",
        "--add",
        "--cacheinfo",
        f"100644,{blob},synthetic/artifact.json",
    )
    _git(root, "commit", "-m", "fixture")
    rev = _git(root, "rev-parse", "HEAD").decode().strip()
    return rev


class TestValidateRelativePath(unittest.TestCase):
    def test_accepts_nested_posix(self):
        self.assertEqual(
            validate_relative_path("synthetic/artifact.json"),
            "synthetic/artifact.json",
        )

    def test_rejects_traversal_and_absolute(self):
        for bad in (
            "../x",
            "a/../b",
            "/abs",
            "a\\b",
            "C:/x",
            "a/./b",
            "",
            "CON",
            "synthetic/CON.json",
            "a//b",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(WorkspaceError):
                    validate_relative_path(bad)


class TestDisposableRoot(unittest.TestCase):
    def test_create_outside_active_repo(self):
        active = Path(__file__).resolve().parents[2]
        protected = inventory_protected_paths([active / "wvma_v1" / "__init__.py"])
        root = create_disposable_root(
            prefix="wvma-test-",
            protected_paths=list(protected.keys()),
            active_repository=active,
        )
        try:
            self.assertTrue(root.is_dir())
            self.assertFalse(str(root).startswith(str(active)))
            assert_protected_unchanged(protected, paths=list(protected.keys()))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejects_parent_inside_active_repo(self):
        active = Path(__file__).resolve().parents[2]
        with self.assertRaises(WorkspaceError):
            create_disposable_root(
                parent=active / "wvma_v1",
                active_repository=active,
            )


class TestExportTrackedTree(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="wvma-ws-")
        base = Path(self._tmpdir.name)
        self.repo = base / "repo"
        self.disp_parent = base / "disp_parent"
        self.disp_parent.mkdir()
        self.rev = _init_fixture_repo(self.repo)
        self.active = Path(__file__).resolve().parents[2]

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_export_matches_git_blob_not_worktree(self):
        disp = create_disposable_root(
            parent=self.disp_parent,
            prefix="exp-",
            active_repository=self.repo,
        )
        dest = disp / "tree"
        inv = export_tracked_tree(
            repo_root=self.repo,
            revision=self.rev,
            destination=dest,
            protected_paths=[self.repo],
        )
        rel = "synthetic/artifact.json"
        self.assertIn(rel, inv)
        exported = (dest / rel).read_bytes()
        blob = subprocess.check_output(
            ["git", "cat-file", "blob", f"{self.rev}:{rel}"],
            cwd=str(self.repo),
            shell=False,
        )
        worktree = (self.repo / rel).read_bytes()
        self.assertEqual(exported, blob)
        self.assertNotEqual(exported, worktree)
        self.assertEqual(inv[rel], hashlib.sha256(blob).hexdigest())
        # Active fixture repo content unchanged by export.
        self.assertEqual((self.repo / rel).read_bytes(), worktree)

    def test_rejects_path_escape_specs(self):
        disp = create_disposable_root(
            parent=self.disp_parent,
            prefix="bad-",
            active_repository=self.repo,
        )
        with self.assertRaises(WorkspaceError):
            export_tracked_tree(
                repo_root=self.repo,
                revision=self.rev,
                destination=disp / "t",
                pathspecs=("../secret",),
            )


class TestInventoryAndProtected(unittest.TestCase):
    def test_inventory_and_protected_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="wvma-inv-") as tmp:
            root = Path(tmp)
            f = root / "a.txt"
            f.write_bytes(b"hello")
            inv = inventory_tree(root)
            self.assertEqual(inv["a.txt"], hashlib.sha256(b"hello").hexdigest())
            before = inventory_protected_paths([f])
            assert_protected_unchanged(before, paths=[f])
            f.write_bytes(b"mutated")
            with self.assertRaises(WorkspaceError):
                assert_protected_unchanged(before, paths=[f])

    def test_resolve_under_root_rejects_escape(self):
        with tempfile.TemporaryDirectory(prefix="wvma-res-") as tmp:
            root = Path(tmp)
            with self.assertRaises(WorkspaceError):
                validate_relative_path("../x")
            p = resolve_under_root(root, "ok.txt")
            self.assertTrue(str(p).startswith(str(root.resolve())))

    def test_output_root_must_not_alias_protected(self):
        active = Path(__file__).resolve().parents[2]
        with self.assertRaises(WorkspaceError):
            ensure_output_root_confined(
                active / "wvma_v1",
                protected_paths=[active],
                active_repository=active,
            )


def _make_dir_alias(link: Path, target: Path) -> None:
    """Create a directory symlink or Windows junction; skip-friendly on failure."""
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        cp = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            shell=False,
        )
        if cp.returncode == 0:
            return
    raise unittest.SkipTest("symlink/junction unavailable")


class TestReparseConfinement(unittest.TestCase):
    def test_symlink_component_rejected_when_available(self):
        with tempfile.TemporaryDirectory(prefix="wvma-rp-") as tmp:
            base = Path(tmp)
            real = base / "real"
            real.mkdir()
            link = base / "link"
            _make_dir_alias(link, real)
            with self.assertRaises(WorkspaceError):
                assert_no_reparse_chain(link / "child", field="probe")


class TestUnresolvedPathOrdering(unittest.TestCase):
    """Caller paths must be rejected before resolve follows reparse aliases."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="wvma-alias-")
        self.base = Path(self._tmpdir.name)
        self.external = self.base / "external_ok"
        self.external.mkdir()
        self.repo = self.base / "repo"
        self.rev = _init_fixture_repo(self.repo)
        self.active = Path(__file__).resolve().parents[2]
        self.disp_parent = self.base / "disp_parent"
        self.disp_parent.mkdir()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_junction_parent_rejected_before_create(self):
        alias = self.base / "parent_alias"
        _make_dir_alias(alias, self.external)
        before = set(self.external.iterdir())
        with self.assertRaises(WorkspaceError):
            create_disposable_root(
                parent=alias,
                prefix="rej-",
                active_repository=self.repo,
            )
        self.assertEqual(set(self.external.iterdir()), before)
        self.assertFalse(any(self.external.glob("rej-*")))

    def test_junction_export_destination_rejected_before_write(self):
        alias = self.base / "export_alias"
        _make_dir_alias(alias, self.external)
        dest = alias / "tree"
        with self.assertRaises(WorkspaceError):
            export_tracked_tree(
                repo_root=self.repo,
                revision=self.rev,
                destination=dest,
                protected_paths=[self.repo],
            )
        self.assertFalse(dest.exists())
        self.assertFalse((self.external / "tree").exists())
        self.assertEqual(list(self.external.iterdir()), [])

    def test_external_alias_still_rejected(self):
        """Alias target outside protected paths must still be rejected."""
        alias = self.base / "external_alias"
        _make_dir_alias(alias, self.external)
        with self.assertRaises(WorkspaceError):
            create_disposable_root(
                parent=alias,
                prefix="ext-",
                protected_paths=[self.repo],
                active_repository=self.repo,
            )
        self.assertFalse(any(self.external.glob("ext-*")))

    def test_protected_alias_still_rejected(self):
        """Alias pointing at a protected repository must still be rejected."""
        alias = self.base / "protected_alias"
        _make_dir_alias(alias, self.repo)
        with self.assertRaises(WorkspaceError):
            create_disposable_root(
                parent=alias,
                prefix="prot-",
                active_repository=self.repo,
            )
        # No disposable directory created under the real protected repo.
        self.assertFalse(any(self.repo.glob("prot-*")))

    def test_ordinary_non_reparse_parent_preserved(self):
        root = create_disposable_root(
            parent=self.disp_parent,
            prefix="ok-",
            active_repository=self.repo,
        )
        try:
            self.assertTrue(root.is_dir())
            self.assertEqual(root.parent, self.disp_parent.resolve())
            self.assertTrue(root.name.startswith("ok-"))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_rejected_export_creates_no_destination_state(self):
        alias = self.base / "no_state_alias"
        _make_dir_alias(alias, self.external)
        dest = alias / "never_created"
        marker = self.external / "never_created"
        with self.assertRaises(WorkspaceError):
            export_tracked_tree(
                repo_root=self.repo,
                revision=self.rev,
                destination=dest,
                protected_paths=[self.repo, self.active],
            )
        self.assertFalse(dest.exists(follow_symlinks=False))
        self.assertFalse(marker.exists(follow_symlinks=False))


if __name__ == "__main__":
    unittest.main()
