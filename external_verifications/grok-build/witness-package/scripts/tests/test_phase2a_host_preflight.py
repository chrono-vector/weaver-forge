#!/usr/bin/env python3
"""Phase 2A host preflight behavioral tests (RC4B-004 / RC4B-005 / RC4B-008 / RC4B-009 subset).

Safety contract:
- Temporary workspaces are children of scripts/tests/ (never the OS default temp root)
- Every Bash subprocess uses cwd=SCRIPTS_DIR and repository-local relative paths
- Host script is sourced only as ./run_witness_narrow_build.sh
- Mock Docker executable first on PATH (never delegates to real docker)
- Mock proof is unique marker + invocation log (not cross-runtime absolute-path equality)
- No remote clones / no network
- No Cargo, rustc, rustup, DotSlash, protoc, ldd, or product execution
- No Windows absolute workspace paths passed into Bash
- No OS-temp-to-repository relative traversal
"""

from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

# Resolve paths from this file — never hard-code C:\\dev or user profile paths.
TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
HOST_SCRIPT_NAME = "run_witness_narrow_build.sh"
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
TAG_NAME = "grok-build-witness-v1.0.0-rc4"
MOCK_DOCKER_MARKER = "MOCK_DOCKER_PHASE2A"
DOCKER_LOG_ENV = "PHASE2A_DOCKER_INVOCATION_LOG"
TEMP_PREFIX = "phase2a_test_"

# Explicit subprocess environment: strip inherited Docker/Cargo/gate overrides.
_STRIP_ENV_KEYS = (
    "IDENTITY_GATE_CLOSED",
    "DOCKER_HOST",
    "DOCKER_CONTEXT",
    "CARGO_HOME",
    "RUSTUP_HOME",
    "CARGO_TARGET_DIR",
    DOCKER_LOG_ENV,
)


def _find_bash() -> str:
    """Locate a Bash suitable for sourcing POSIX shell scripts.

    On Windows, prefer Git-for-Windows bash over WSL bash so repository-local
    relative paths behave like the Pi/Git-Bash corroboration environment.
    """
    candidates: list[str] = []
    for key in ("ProgramFiles", "ProgramFiles(x86)"):
        root = os.environ.get(key)
        if root:
            candidates.append(str(Path(root) / "Git" / "bin" / "bash.exe"))
            candidates.append(str(Path(root) / "Git" / "usr" / "bin" / "bash.exe"))
    which = shutil.which("bash")
    if which:
        candidates.append(which)
    for c in candidates:
        if c and Path(c).is_file():
            return c
    raise unittest.SkipTest("bash not available for Phase 2A host preflight tests")


def _bash(args: list[str], *, env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_find_bash(), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
        cwd=str(cwd) if cwd is not None else None,
    )


def _git(repo: Path, *git_args: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        ["git", "-C", str(repo), *git_args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env=env,
    )
    if check and cp.returncode != 0:
        raise AssertionError(
            f"git {' '.join(git_args)} failed ({cp.returncode}): {cp.stderr}"
        )
    return cp


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_dir_link(path: Path) -> bool:
    """True for symlinks or Windows directory junctions (reparse points)."""
    if path.is_symlink():
        return True
    try:
        os.readlink(path)
        return True
    except OSError:
        return False


def _create_dir_link(link: Path, target: Path) -> None:
    """Create a directory symlink, or a Windows junction if symlinks are unavailable."""
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        cp = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if cp.returncode == 0 and _is_dir_link(link):
            return
        raise AssertionError(
            f"mklink /J failed ({cp.returncode}): {cp.stdout} {cp.stderr}"
        )
    raise AssertionError("directory link creation unavailable on this platform")


def _status_of(path: Path) -> str | None:
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status="):
            return line.split("=", 1)[1]
    return None


def _remaining_phase2a_temps() -> list[Path]:
    if not TESTS_DIR.is_dir():
        return []
    return sorted(
        p for p in TESTS_DIR.iterdir() if p.is_dir() and p.name.startswith(TEMP_PREFIX)
    )


class Phase2AHostPreflightTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_phase2a_temps()
        assert not leftovers, (
            f"Phase 2A temporary directories remain under {TESTS_DIR}: "
            f"{[p.name for p in leftovers]}"
        )

    def setUp(self) -> None:
        self.assertTrue(HOST_SCRIPT.is_file(), f"missing host script: {HOST_SCRIPT}")
        # Repository-local temp workspace under scripts/tests/ — never OS default temp.
        self._tmpdir = tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(TESTS_DIR))
        self.workspace = Path(self._tmpdir.name).resolve()
        self.assertEqual(self.workspace.parent, TESTS_DIR)
        self.ws_basename = self.workspace.name
        # Bash-visible path from cwd=SCRIPTS_DIR (repository-local relative only).
        self.ws_rel = f"tests/{self.ws_basename}"
        self.assertFalse(Path(self.ws_rel).is_absolute())
        self.assertTrue(self.ws_rel.startswith("tests/"))

        self.mock_bin = self.workspace / "mock-bin"
        self.mock_bin.mkdir()
        self.docker_log = self.workspace / "docker_invocations.log"
        self.docker_log.write_text("", encoding="utf-8")
        self.mock_bin_rel = f"{self.ws_rel}/mock-bin"
        self.mock_docker_rel = f"{self.mock_bin_rel}/docker"
        self.docker_log_rel = f"{self.ws_rel}/docker_invocations.log"

        # Mock docker: relative PATH + relative log; never delegates to real docker.
        _write_executable(
            self.mock_bin / "docker",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                if [[ -z "${{{DOCKER_LOG_ENV}:-}}" ]]; then
                  echo "mock-docker: {DOCKER_LOG_ENV} is unset" >&2
                  exit 96
                fi
                printf '%s %s\\n' "{MOCK_DOCKER_MARKER}" "$*" >> "${{{DOCKER_LOG_ENV}}}"
                case "${{1:-}}" in
                  version)
                    if [[ "${{2:-}}" == "--format" ]]; then
                      echo "0.0.0-mock"
                    else
                      echo "Client: Docker Engine - Community"
                      echo " Version: 0.0.0-mock"
                      echo "Server: Docker Engine - Community"
                      echo " Version: 0.0.0-mock"
                    fi
                    ;;
                  context)
                    echo "mock-context"
                    ;;
                  *)
                    echo "mock-docker: unexpected command: $*" >&2
                    exit 97
                    ;;
                esac
                """
            ),
        )
        mock_body = (self.mock_bin / "docker").read_text(encoding="utf-8")
        self.assertNotRegex(mock_body, r"(?m)^\s*exec\s+")
        self.assertNotIn("command -v docker", mock_body)
        self.assertNotIn("/usr/bin/docker", mock_body)
        self.assertNotIn("docker.io", mock_body)

        self.env: dict[str, str] = {
            # Keep a host PATH for git/python tooling; Bash prepends mock-bin itself.
            # HOME/TMPDIR stay Python-native for Python-side git only; Bash preamble
            # overrides them to repository-local relative paths (never OS-temp traversal).
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.workspace / "home"),
            "TMPDIR": str(self.workspace / "tmp"),
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "protocol.file.allow",
            "GIT_CONFIG_VALUE_0": "always",
            "LANG": "C",
            "LC_ALL": "C",
            DOCKER_LOG_ENV: self.docker_log_rel,
        }
        (self.workspace / "home").mkdir()
        (self.workspace / "tmp").mkdir()
        for k in _STRIP_ENV_KEYS:
            if k == DOCKER_LOG_ENV:
                continue
            self.env.pop(k, None)
        for k in ("SYSTEMROOT", "WINDIR", "SystemRoot", "COMSPEC"):
            if k in os.environ:
                self.env[k] = os.environ[k]

        # Cross-runtime setup probe (not counted among the 18 behavioral tests).
        self._run_setup_probe()

        # Discover real git through Bash *before* any git mock is installed.
        git_probe = self._bash_in_scripts("command -v git")
        self.assertEqual(git_probe.returncode, 0, git_probe.stderr)
        self.bash_real_git = git_probe.stdout.strip()
        self.assertTrue(self.bash_real_git)

        # Load-bearing mock proof: unique marker + invocation log (not absolute-path equality).
        self.docker_log.write_text("", encoding="utf-8")
        probe = self._bash_in_scripts("docker version --format '{{.Client.Version}}'")
        self.assertEqual(probe.returncode, 0, probe.stderr + probe.stdout)
        self.assertEqual(probe.stdout.strip(), "0.0.0-mock")
        log_text = self.docker_log.read_text(encoding="utf-8")
        self.assertIn(MOCK_DOCKER_MARKER, log_text)
        self.assertIn("version --format", log_text)
        self.assertEqual(self._docker_invocation_count(), 1)
        self.docker_log.write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        workspace = getattr(self, "workspace", None)
        self._tmpdir.cleanup()
        if workspace is not None:
            self.assertFalse(
                workspace.exists(),
                f"TemporaryDirectory failed to remove repository-local workspace: {workspace}",
            )

    def _bash_env(self) -> dict[str, str]:
        """Environment for Bash: repository-local relative HOME/TMPDIR/log only."""
        env = dict(self.env)
        env["HOME"] = self.ws_rel + "/home"
        env["TMPDIR"] = self.ws_rel + "/tmp"
        env[DOCKER_LOG_ENV] = self.docker_log_rel
        return env

    def _run_setup_probe(self) -> None:
        """Prove Bash can see host script + repo-local workspace before behavioral tests."""
        probe_rel = f"{self.ws_rel}/setup_probe.txt"
        probe_py = self.workspace / "setup_probe.txt"
        if probe_py.exists():
            probe_py.unlink()
        script = textwrap.dedent(
            f"""\
            set -Eeuo pipefail
            if [[ ! -r ./run_witness_narrow_build.sh ]]; then
              echo "setup-probe: host script not readable" >&2
              exit 91
            fi
            if [[ ! -d {shlex.quote(self.ws_rel)} ]]; then
              echo "setup-probe: workspace missing: {self.ws_rel}" >&2
              exit 92
            fi
            if [[ ! -x {shlex.quote(self.mock_docker_rel)} ]]; then
              echo "setup-probe: mock docker not executable: {self.mock_docker_rel}" >&2
              exit 93
            fi
            printf 'setup-probe-ok\\n' > {shlex.quote(probe_rel)}
            if [[ ! -f {shlex.quote(probe_rel)} ]]; then
              echo "setup-probe: failed to write probe file" >&2
              exit 94
            fi
            """
        )
        cp = _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)
        if cp.returncode != 0:
            self.fail(
                "Phase 2A cross-runtime setup probe failed.\n"
                f"Bash cwd={SCRIPTS_DIR}\n"
                f"relative workspace={self.ws_rel}\n"
                f"stderr:\n{cp.stderr}\n"
                f"stdout:\n{cp.stdout}"
            )
        self.assertTrue(probe_py.is_file(), f"Python cannot see probe file: {probe_py}")
        self.assertEqual(probe_py.read_text(encoding="utf-8").strip(), "setup-probe-ok")

    def _bash_preamble(self) -> str:
        return textwrap.dedent(
            f"""\
            set -Eeuo pipefail
            export PATH={shlex.quote(self.mock_bin_rel)}:"$PATH"
            export {DOCKER_LOG_ENV}={shlex.quote(self.docker_log_rel)}
            export HOME={shlex.quote(self.ws_rel + "/home")}
            export TMPDIR={shlex.quote(self.ws_rel + "/tmp")}
            """
        )

    def _bash_in_scripts(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._bash_preamble() + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _source_helpers_snippet(self) -> str:
        return (
            self._bash_preamble()
            + textwrap.dedent(
                """\
                # shellcheck disable=SC1091
                . ./run_witness_narrow_build.sh
                """
            )
        )

    def _docker_invocation_count(self) -> int:
        text = self.docker_log.read_text(encoding="utf-8")
        return len([ln for ln in text.splitlines() if MOCK_DOCKER_MARKER in ln])

    def _docker_log_text(self) -> str:
        return self.docker_log.read_text(encoding="utf-8")

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._source_helpers_snippet() + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _ws(self, *parts: str) -> str:
        """Bash-visible repository-local relative path under the temporary workspace."""
        rel = self.ws_rel
        if parts:
            rel = "/".join((self.ws_rel, *(p.replace("\\", "/") for p in parts)))
        self.assertFalse(Path(rel).is_absolute(), f"Bash path must be relative: {rel}")
        self.assertTrue(rel.startswith("tests/"), f"Bash path must be under tests/: {rel}")
        return rel

    def _init_user_repo(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        _git(path, "init", env=self.env)
        _git(path, "config", "user.email", "phase2a@example.test", env=self.env)
        _git(path, "config", "user.name", "Phase2A Test", env=self.env)
        _git(path, "config", "commit.gpgsign", "false", env=self.env)
        _git(path, "config", "tag.gpgsign", "false", env=self.env)

    def _commit_tree(self, repo: Path, relative_files: dict[str, str], message: str) -> str:
        for rel, content in relative_files.items():
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
            _git(repo, "add", "--", rel, env=self.env)
        _git(repo, "commit", "-m", message, env=self.env)
        return _git(repo, "rev-parse", "HEAD", env=self.env).stdout.strip()

    def _make_weaver_package_repo(self, *, tag_mode: str) -> Path:
        src = self.workspace / "repos" / f"weaver-src-{tag_mode}"
        if src.exists():
            shutil.rmtree(src)
        self._init_user_repo(src)
        container_rel = (
            "external_verifications/grok-build/witness-package/scripts/"
            "container_narrow_build.sh"
        )
        self._commit_tree(
            src,
            {
                container_rel: "#!/usr/bin/env bash\necho stub-container\n",
                "README.md": "phase2a weaver fixture\n",
            },
            "phase2a weaver fixture",
        )
        if tag_mode == "annotated":
            _git(src, "tag", "-a", TAG_NAME, "-m", "phase2a annotated", env=self.env)
        elif tag_mode == "lightweight":
            _git(src, "tag", TAG_NAME, env=self.env)
        elif tag_mode == "missing":
            pass
        else:
            raise AssertionError(f"unknown tag_mode={tag_mode}")

        bare = self.workspace / "repos" / f"weaver-{tag_mode}.git"
        if bare.exists():
            shutil.rmtree(bare)
        subprocess.run(
            ["git", "clone", "--bare", str(src), str(bare)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self.env,
        )
        return bare

    def _enable_git_head_lie(self) -> None:
        lie_flag = self.workspace / "lie_about_head"
        lie_flag_rel = self._ws("lie_about_head")
        if (self.mock_bin / "git").exists():
            lie_flag.write_text("1", encoding="utf-8")
            return
        lie_hash = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
        # REAL_GIT is the path Bash itself resolved — never a Python/Windows string compare.
        _write_executable(
            self.mock_bin / "git",
            textwrap.dedent(
                f"""\
                #!/usr/bin/env bash
                set -euo pipefail
                REAL_GIT={shlex.quote(self.bash_real_git)}
                if [[ "${{1:-}}" == "-C" && "${{3:-}}" == "rev-parse" && "${{4:-}}" == "HEAD" ]]; then
                  if [[ -f {shlex.quote(lie_flag_rel)} ]]; then
                    echo "{lie_hash}"
                    exit 0
                  fi
                fi
                exec "$REAL_GIT" "$@"
                """
            ),
        )
        lie_flag.write_text("1", encoding="utf-8")

    def _make_grok_repo(self) -> tuple[Path, str, str]:
        src = self.workspace / "repos" / "grok-src"
        if src.exists():
            shutil.rmtree(src)
        self._init_user_repo(src)
        lock_payload = b"# phase2a Cargo.lock fixture\n[[package]]\nname = \"x\"\nversion = \"0.0.0\"\n"
        lock_hash = _sha256_bytes(lock_payload)
        (src / "Cargo.lock").write_bytes(lock_payload)
        _git(src, "add", "--", "Cargo.lock", env=self.env)
        _git(src, "commit", "-m", "phase2a grok fixture", env=self.env)
        real_commit = _git(src, "rev-parse", "HEAD", env=self.env).stdout.strip()
        bare = self.workspace / "repos" / "grok.git"
        if bare.exists():
            shutil.rmtree(bare)
        subprocess.run(
            ["git", "clone", "--bare", str(src), str(bare)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self.env,
        )
        return bare, real_commit, lock_hash

    def _py_to_bash_rel(self, path: Path) -> str:
        """Map a Python Path under the workspace to tests/<basename>/... for Bash."""
        resolved = path.resolve()
        try:
            rel_under_ws = resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise AssertionError(
                f"path {resolved} is not under repository-local workspace {self.workspace}"
            ) from exc
        return self._ws(*rel_under_ws.parts)

    def _bash_pwd(self, bash_rel: str = ".") -> str:
        """Absolute path as Bash itself renders it (no Python/Windows string compare)."""
        cp = self._bash_in_scripts(f"cd {shlex.quote(bash_rel)} && pwd")
        self.assertEqual(cp.returncode, 0, cp.stderr or "")
        out = (cp.stdout or "").strip()
        self.assertTrue(out, "bash pwd returned empty")
        return out

    def _run_host(
        self,
        *,
        work_root: Path,
        weaver_url: str,
        grok_url: str,
        grok_commit: str,
        expected_lock: str,
    ) -> subprocess.CompletedProcess[str]:
        env = dict(self._bash_env())
        # Inherited gate must be ignored/reset by production main.
        env["IDENTITY_GATE_CLOSED"] = "yes"
        env.update(
            {
                "WEAVER_FORGE_URL": weaver_url,
                "WEAVER_FORGE_TAG": TAG_NAME,
                "GROK_BUILD_URL": grok_url,
                "GROK_BUILD_COMMIT": grok_commit,
                "EXPECTED_CARGO_LOCK_SHA256": expected_lock,
                "RUST_IMAGE": (
                    "docker.io/library/rust@sha256:"
                    "6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
                ),
            }
        )
        # Host requires an absolute WORK_ROOT; obtain it from Bash pwd (runtime-local).
        work_rel = self._py_to_bash_rel(work_root)
        work_abs = self._bash_pwd(work_rel)
        # Production validate_work_root refuses any WORK_ROOT inside the package
        # repository. Repository-local Phase 2A workspaces live under
        # scripts/tests/phase2a_test_* (required for Git-Bash relative paths), so
        # the harness rebinds validate_work_root to allow only that prefix while
        # still invoking production run_witness_narrow_build_main.
        script = self._source_helpers_snippet() + textwrap.dedent(
            f"""\
            validate_work_root() {{
              local wr="$1"
              if [[ -z "${{wr}}" ]]; then
                die_arg "WORK_ROOT must not be empty (set WORK_ROOT or pass --work-root)"
              fi
              if [[ "${{wr}}" != /* ]]; then
                die_arg "WORK_ROOT must be an absolute path: ${{wr}}"
              fi
              local resolved
              resolved="$(resolve_path_m "${{wr}}")"
              if [[ "${{resolved}}" == "/" ]]; then
                die_arg "WORK_ROOT must not resolve to / (resolved: ${{resolved}})"
              fi
              if is_system_prefix "${{resolved}}"; then
                die_arg "WORK_ROOT must not resolve within a system prefix (resolved: ${{resolved}})"
              fi
              local phase2a_tests_resolved
              phase2a_tests_resolved="$(resolve_path_m "${{SCRIPT_DIR}}/tests")"
              if [[ "${{resolved}}" != "${{phase2a_tests_resolved}}/phase2a_test_"* ]]; then
                die_arg "Phase 2A harness WORK_ROOT must stay under scripts/tests/phase2a_test_* (resolved: ${{resolved}})"
              fi
              WORK_ROOT_RESOLVED="${{resolved}}"
            }}
            run_witness_narrow_build_main \\
              --work-root {shlex.quote(work_abs)} \\
              --allow-nonempty-work-root \\
              --force-work-root-reset \\
              --noncanonical-deviation \\
              phase2a-wit
            """
        )
        return _bash(["-c", script], env=env, cwd=SCRIPTS_DIR)

    def _evidence_dirs(self, work: Path) -> list[Path]:
        parent = work / "evidence"
        if not parent.is_dir():
            return []
        return [p for p in parent.iterdir() if p.is_dir()]

    def _assert_no_success_implying_identity(self, work: Path) -> Path:
        dirs = self._evidence_dirs(work)
        self.assertTrue(dirs, "expected an evidence directory after failure")
        ev = dirs[0]
        for name in (
            "ENVIRONMENT.txt",
            "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
            "SOURCE_IDENTITY.txt",
        ):
            status = _status_of(ev / name)
            self.assertIsNotNone(status, f"missing {name}")
            self.assertNotEqual(
                status,
                "OK",
                f"{name} must not imply success on pre-gate failure (status={status})",
            )
        return ev

    # ------------------------------------------------------------------
    # Sourced mode / gate inheritance
    # ------------------------------------------------------------------
    def test_sourcing_has_no_side_effects(self) -> None:
        marker = self.workspace / "side-effect-marker"
        marker_rel = self._ws("side-effect-marker")
        body = textwrap.dedent(
            f"""
            # After source, main must not have run.
            test "$(type -t allocate_atomic_evidence_dir)" = "function"
            test "$(type -t record_docker_environment_metadata)" = "function"
            test "$(type -t run_witness_narrow_build_main)" = "function"
            # No evidence allocation from sourcing alone.
            test -z "${{EVIDENCE_DIR:-}}"
            # Inherited gate must not matter: main was never invoked by source.
            export IDENTITY_GATE_CLOSED=yes
            echo sourced_ok > {shlex.quote(marker_rel)}
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertTrue(marker.is_file())
        self.assertEqual(self._docker_invocation_count(), 0)
        self.assertFalse(any(self.workspace.rglob("HOST_RUN_METADATA.txt")))

    def test_host_script_uses_standard_bash_source_entry(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIn('BASH_SOURCE[0]', text)
        self.assertIn("run_witness_narrow_build_main", text)
        self.assertRegex(
            text,
            r'if\s+\[\[\s*"\$\{BASH_SOURCE\[0\]\}"\s*==\s*"\$0"\s*\]\]\s*;\s*then',
        )
        self.assertNotIn("WEAVER_FORGE_WITNESS_HOST_SOURCED", text)

    def test_identity_gate_reset_ignores_environment(self) -> None:
        # Unit-level: production reset leaves gate closed=no; helper refuses.
        body = textwrap.dedent(
            """
            IDENTITY_GATE_CLOSED="yes"
            # Simulate production reset performed at main entry.
            IDENTITY_GATE_CLOSED="no"
            EVIDENCE_DIR=""
            CURRENT_STAGE="test"
            set +e
            record_docker_environment_metadata
            ec=$?
            set -e
            exit "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(self._docker_invocation_count(), 0)

    # ------------------------------------------------------------------
    # RC4B-008 atomic EVIDENCE_DIR
    # ------------------------------------------------------------------
    def test_atomic_evidence_dir_new_succeeds(self) -> None:
        work_rel = self._ws("work-a")
        body = textwrap.dedent(
            f"""
            WORK_ROOT={shlex.quote(work_rel)}
            WITNESS_ID="phase2a-wit"
            CURRENT_STAGE="test"
            mkdir -p "$WORK_ROOT"
            allocate_atomic_evidence_dir
            printf 'RUN_ID=%s\\n' "$RUN_ID"
            printf 'EVIDENCE_DIR=%s\\n' "$EVIDENCE_DIR"
            test -d "$EVIDENCE_DIR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertRegex(cp.stdout, r"RUN_ID=phase2a-wit-\d{8}-[0-9a-f]+")

    def test_atomic_evidence_dir_collision_preserves_sentinel(self) -> None:
        work = self.workspace / "work-collide"
        parent = work / "evidence"
        parent.mkdir(parents=True)
        work_rel = self._py_to_bash_rel(work)
        parent_rel = self._py_to_bash_rel(parent)
        counter_rel = self._ws("suffix_counter")
        body = textwrap.dedent(
            f"""
            WORK_ROOT={shlex.quote(work_rel)}
            WITNESS_ID="phase2a-wit"
            CURRENT_STAGE="test"
            UTC_DATE="$(date -u +%Y%m%d)"
            collide={shlex.quote(parent_rel)}"/phase2a-wit-${{UTC_DATE}}-fixedsuffix"
            mkdir -p "$collide"
            echo sentinel-keep > "$collide/SENTINEL.txt"
            counter_file={shlex.quote(counter_rel)}
            echo 0 > "$counter_file"
            random_run_suffix() {{
              local n
              n="$(cat "$counter_file")"
              n=$((n + 1))
              printf '%s' "$n" > "$counter_file"
              if [[ "$n" -eq 1 ]]; then
                echo fixedsuffix
              else
                echo "newsuffix${{n}}"
              fi
            }}
            allocate_atomic_evidence_dir
            grep -qx sentinel-keep "$collide/SENTINEL.txt"
            [[ "$EVIDENCE_DIR" != "$collide" ]]
            [[ -d "$EVIDENCE_DIR" ]]
            [[ -z "$(ls -A "$EVIDENCE_DIR")" ]]
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    def test_atomic_evidence_dir_two_rapid_allocations_differ(self) -> None:
        work_rel = self._ws("work-rapid")
        body = textwrap.dedent(
            f"""
            WORK_ROOT={shlex.quote(work_rel)}
            WITNESS_ID="phase2a-wit"
            CURRENT_STAGE="test"
            mkdir -p "$WORK_ROOT"
            allocate_atomic_evidence_dir
            a="$EVIDENCE_DIR"
            allocate_atomic_evidence_dir
            b="$EVIDENCE_DIR"
            [[ "$a" != "$b" ]]
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)

    def test_atomic_evidence_dir_symlink_collision_preserves_target(self) -> None:
        work = self.workspace / "work-symlink"
        parent = work / "evidence"
        parent.mkdir(parents=True)
        external = self.workspace / "external-target"
        external.mkdir()
        sentinel = external / "SENTINEL.txt"
        sentinel_payload = b"symlink-sentinel-bytes-v1\n"
        sentinel.write_bytes(sentinel_payload)
        utc = self._bash_in_scripts("date -u +%Y%m%d").stdout.strip()
        collide = parent / f"phase2a-wit-{utc}-fixedsuffix"
        _create_dir_link(collide, external)

        before_target = os.readlink(collide)
        work_rel = self._py_to_bash_rel(work)
        collide_rel = self._py_to_bash_rel(collide)
        counter_rel = self._ws("symlink_suffix_counter")
        body = textwrap.dedent(
            f"""
            WORK_ROOT={shlex.quote(work_rel)}
            WITNESS_ID="phase2a-wit"
            CURRENT_STAGE="test"
            counter_file={shlex.quote(counter_rel)}
            echo 0 > "$counter_file"
            random_run_suffix() {{
              local n
              n="$(cat "$counter_file")"
              n=$((n + 1))
              printf '%s' "$n" > "$counter_file"
              if [[ "$n" -eq 1 ]]; then
                echo fixedsuffix
              else
                echo "symnewsuffix${{n}}"
              fi
            }}
            allocate_atomic_evidence_dir
            printf 'EVIDENCE_DIR=%s\\n' "$EVIDENCE_DIR"
            if [[ "$EVIDENCE_DIR" == {shlex.quote(collide_rel)} ]]; then
              echo "FATAL: allocated onto symlink candidate" >&2
              exit 1
            fi
            if [[ ! -d "$EVIDENCE_DIR" ]]; then
              echo "FATAL: fresh evidence dir missing" >&2
              exit 1
            fi
            if [[ -L "$EVIDENCE_DIR" ]]; then
              echo "FATAL: fresh evidence dir is a symlink" >&2
              exit 1
            fi
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, (cp.stderr or "") + (cp.stdout or ""))
        # Candidate link/junction not followed/removed/replaced; target sentinel intact.
        self.assertTrue(_is_dir_link(collide), "candidate must remain a directory link")
        self.assertEqual(os.readlink(collide), before_target)
        self.assertEqual(sentinel.read_bytes(), sentinel_payload)
        m = re.search(r"EVIDENCE_DIR=(.+)", cp.stdout or "")
        self.assertIsNotNone(m)
        # Bash may print a runtime-local absolute path; compare via name + workspace walk.
        fresh_name = Path(m.group(1).strip()).name
        matches = [p for p in (work / "evidence").iterdir() if p.name == fresh_name]
        self.assertEqual(len(matches), 1)
        fresh = matches[0]
        self.assertTrue(fresh.is_dir())
        self.assertFalse(_is_dir_link(fresh))
        self.assertNotEqual(fresh.resolve(), collide)

    def test_final_evidence_dir_never_uses_mkdir_p(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        m = re.search(r"allocate_atomic_evidence_dir\(\) \{\n(.*?\n)\}", text, flags=re.S)
        self.assertIsNotNone(m)
        body = m.group(1)
        self.assertIn('mkdir -p "${evidence_parent}"', body)
        self.assertNotRegex(body, r'mkdir\s+-p\s+"\$\{candidate_dir\}"')
        self.assertRegex(body, r'mkdir\s+"\$\{candidate_dir\}"')

    # ------------------------------------------------------------------
    # RC4B-005 annotated tag enforcement
    # ------------------------------------------------------------------
    def test_annotated_tag_accepted_lightweight_rejected_missing_rejected(self) -> None:
        cases = [
            ("annotated", True),
            ("lightweight", False),
            ("missing", False),
        ]
        for mode, expect_ok in cases:
            with self.subTest(mode=mode):
                src = self.workspace / "repos" / f"tagcheck-{mode}"
                if src.exists():
                    shutil.rmtree(src)
                self._init_user_repo(src)
                self._commit_tree(src, {"f.txt": "x\n"}, "c")
                if mode == "annotated":
                    _git(src, "tag", "-a", TAG_NAME, "-m", "ann", env=self.env)
                elif mode == "lightweight":
                    _git(src, "tag", TAG_NAME, env=self.env)
                evidence = self.workspace / "evidence" / f"ev-{mode}"
                evidence.mkdir(parents=True, exist_ok=True)
                (evidence / "HOST_RUN_METADATA.txt").write_text(
                    "evidence_schema_version=1\n", encoding="utf-8"
                )
                body = textwrap.dedent(
                    f"""
                    WF_DIR={shlex.quote(self._py_to_bash_rel(src))}
                    EVIDENCE_DIR={shlex.quote(self._py_to_bash_rel(evidence))}
                    EFFECTIVE_WEAVER_FORGE_TAG="{TAG_NAME}"
                    EFFECTIVE_WEAVER_FORGE_URL={shlex.quote("file://" + self._py_to_bash_rel(src))}
                    CURRENT_STAGE="test"
                    finalize_pre_docker_infrastructure_failure() {{
                      echo "FINALIZE:$1" >&2
                      exit 3
                    }}
                    set +e
                    assert_raw_annotated_package_tag_type
                    ec=$?
                    set -e
                    exit "$ec"
                    """
                )
                cp = self._run_sourced(body)
                if expect_ok:
                    self.assertEqual(cp.returncode, 0, cp.stderr)
                    meta = (evidence / "HOST_RUN_METADATA.txt").read_text(encoding="utf-8")
                    self.assertIn("weaver_forge_tag_raw_object_type=tag", meta)
                else:
                    self.assertNotEqual(cp.returncode, 0)
                    self.assertEqual(self._docker_invocation_count(), 0)

    def test_tag_pointing_to_commit_still_requires_raw_type_tag(self) -> None:
        src = self.workspace / "repos" / "lw-ultimate-commit"
        self._init_user_repo(src)
        self._commit_tree(src, {"f.txt": "x\n"}, "c")
        _git(src, "tag", TAG_NAME, env=self.env)
        peeled = _git(
            src, "rev-parse", f"refs/tags/{TAG_NAME}^{{commit}}", env=self.env
        ).stdout.strip()
        self.assertRegex(peeled, r"^[0-9a-f]{40}$")
        raw = _git(src, "cat-file", "-t", f"refs/tags/{TAG_NAME}", env=self.env).stdout.strip()
        self.assertEqual(raw, "commit")

    # ------------------------------------------------------------------
    # RC4B-004 Docker ordering + evidence truthfulness
    # ------------------------------------------------------------------
    def test_docker_metadata_refuses_before_identity_gate(self) -> None:
        evidence = self.workspace / "evidence" / "ev-gate"
        evidence.mkdir(parents=True)
        (evidence / "HOST_RUN_METADATA.txt").write_text("x=1\n", encoding="utf-8")
        body = textwrap.dedent(
            f"""
            EVIDENCE_DIR={shlex.quote(self._py_to_bash_rel(evidence))}
            IDENTITY_GATE_CLOSED="no"
            CURRENT_STAGE="test"
            set +e
            record_docker_environment_metadata
            ec=$?
            set -e
            exit "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(self._docker_invocation_count(), 0)
        self.assertIn("refused", cp.stderr)

    def test_docker_metadata_runs_only_after_gate_closed(self) -> None:
        evidence = self.workspace / "evidence" / "ev-gate-ok"
        evidence.mkdir(parents=True)
        (evidence / "HOST_RUN_METADATA.txt").write_text("x=1\n", encoding="utf-8")
        (evidence / "ENVIRONMENT.txt").write_text(
            "evidence_schema_version=1\nstatus=NOT_REACHED\n",
            encoding="utf-8",
        )
        body = textwrap.dedent(
            f"""
            EVIDENCE_DIR={shlex.quote(self._py_to_bash_rel(evidence))}
            WITNESS_ID="phase2a-wit"
            IDENTITY_GATE_CLOSED="yes"
            CURRENT_STAGE="test"
            HOST_ENV_UTC="2026-01-01T00:00:00Z"
            HOST_ENV_OS="Linux"
            HOST_ENV_KERNEL="test"
            HOST_ENV_ARCH="x86_64"
            HOST_ENV_CPU_MODEL="test-cpu"
            HOST_ENV_RAM_GIB="1"
            HOST_ENV_DISK_FREE_GB="1"
            HOST_ENV_PLATFORM="linux/amd64"
            HOST_ENV_WSL="UNKNOWN"
            HOST_ENV_CPU_SUMMARY="cpu"
            HOST_ENV_RAM="ram"
            HOST_ENV_DISK="disk"
            record_docker_environment_metadata
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertGreaterEqual(self._docker_invocation_count(), 1)
        log = self._docker_log_text()
        self.assertIn(MOCK_DOCKER_MARKER, log)
        env_txt = (evidence / "ENVIRONMENT.txt").read_text(encoding="utf-8")
        self.assertIn("status=OK", env_txt)
        self.assertIn("docker_client_version=0.0.0-mock", env_txt)
        self.assertNotIn("PENDING_IDENTITY_CLOSURE", env_txt)

    def _assert_docker_count_zero_on_identity_failure(self, *, mode: str) -> Path:
        work = self.workspace / "evidence" / f"work-{mode}"
        work.mkdir(parents=True)
        if mode == "package_tag_type":
            weaver = self._make_weaver_package_repo(tag_mode="lightweight")
            grok, grok_commit, lock_hash = self._make_grok_repo()
        elif mode == "package_tag_missing":
            weaver = self._make_weaver_package_repo(tag_mode="missing")
            grok, grok_commit, lock_hash = self._make_grok_repo()
        elif mode == "package_head":
            weaver = self._make_weaver_package_repo(tag_mode="annotated")
            grok, grok_commit, lock_hash = self._make_grok_repo()
            self._enable_git_head_lie()
        elif mode == "source_identity":
            weaver = self._make_weaver_package_repo(tag_mode="annotated")
            grok, grok_commit, lock_hash = self._make_grok_repo()
            grok_commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        elif mode == "cargo_lock":
            weaver = self._make_weaver_package_repo(tag_mode="annotated")
            grok, grok_commit, lock_hash = self._make_grok_repo()
            lock_hash = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        else:
            raise AssertionError(mode)

        self.docker_log.write_text("", encoding="utf-8")
        # Clone URLs use Bash-rendered absolute paths (not Python/Windows literals).
        weaver_url = f"file://{self._bash_pwd(self._py_to_bash_rel(weaver))}"
        grok_url = f"file://{self._bash_pwd(self._py_to_bash_rel(grok))}"
        cp = self._run_host(
            work_root=work,
            weaver_url=weaver_url,
            grok_url=grok_url,
            grok_commit=grok_commit,
            expected_lock=lock_hash,
        )
        out = cp.stdout or ""
        err = cp.stderr or ""
        self.assertNotEqual(cp.returncode, 0, out + "\n" + err)
        self.assertEqual(
            self._docker_invocation_count(),
            0,
            f"mode={mode} docker log:\n{self._docker_log_text()}\n"
            f"stdout:\n{out}\nstderr:\n{err}",
        )
        return self._assert_no_success_implying_identity(work)

    def test_docker_count_zero_and_truthful_evidence_on_package_tag_type_failure(self) -> None:
        ev = self._assert_docker_count_zero_on_identity_failure(mode="package_tag_type")
        self.assertNotEqual(_status_of(ev / "WEAVER_FORGE_PACKAGE_IDENTITY.txt"), "OK")
        self.assertNotEqual(_status_of(ev / "ENVIRONMENT.txt"), "OK")

    def test_docker_count_zero_when_package_tag_missing(self) -> None:
        self._assert_docker_count_zero_on_identity_failure(mode="package_tag_missing")

    def test_docker_count_zero_and_truthful_evidence_on_package_head_failure(self) -> None:
        ev = self._assert_docker_count_zero_on_identity_failure(mode="package_head")
        self.assertNotEqual(_status_of(ev / "WEAVER_FORGE_PACKAGE_IDENTITY.txt"), "OK")

    def test_docker_count_zero_and_truthful_evidence_on_source_identity_failure(self) -> None:
        ev = self._assert_docker_count_zero_on_identity_failure(mode="source_identity")
        self.assertNotEqual(_status_of(ev / "SOURCE_IDENTITY.txt"), "OK")
        self.assertNotEqual(_status_of(ev / "ENVIRONMENT.txt"), "OK")

    def test_docker_count_zero_and_truthful_evidence_on_cargo_lock_failure(self) -> None:
        ev = self._assert_docker_count_zero_on_identity_failure(mode="cargo_lock")
        self.assertNotEqual(_status_of(ev / "SOURCE_IDENTITY.txt"), "OK")
        self.assertNotEqual(_status_of(ev / "ENVIRONMENT.txt"), "OK")

    def test_source_order_docker_metadata_after_identity_gate_close(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        call_region = text.split("step13b_identity_gate_close_and_docker_metadata", 1)[1]
        self.assertLess(
            call_region.index("close_identity_gate"),
            call_region.index("record_docker_environment_metadata"),
        )
        collect = text.split("collect_host_environment_facts() {", 1)[1].split("\n}", 1)[0]
        self.assertNotRegex(collect, r"(?m)^\s*docker\s")
        self.assertNotIn("status=OK", collect)


if __name__ == "__main__":
    unittest.main(verbosity=2)
