#!/usr/bin/env python3
"""Phase 3G harness support: shims, workspace, adapters, validator driver (3G-A).

Phase 3G-A prepares frameworks for Phase 3G-B. Full five-outcome lifecycle and
real host Witness workflow execution are deferred.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from phase3g_scenarios import ScenarioFrameworkError

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
HOST_SCRIPT_NAME = "run_witness_narrow_build.sh"
CONTAINER_SCRIPT_NAME = "container_narrow_build.sh"
VALIDATOR_SCRIPT_NAME = "validate_witness_evidence.py"
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
CONTAINER_SCRIPT = SCRIPTS_DIR / CONTAINER_SCRIPT_NAME
VALIDATOR_SCRIPT = SCRIPTS_DIR / VALIDATOR_SCRIPT_NAME

TEMP_PREFIX = "phase3g_test_"

# Prohibited command identities (PATH-first non-delegating shims).
PROHIBITED_COMMANDS: tuple[str, ...] = (
    "docker",
    "cargo",
    "rustc",
    "rustup",
    "dotslash",
    "protoc",
    "ldd",
    # Product-binary aliases discovered from repository fixtures/scripts.
    "xai-grok-pager",
    "xai-grok-pager-bin",
)

_STRIP_ENV_KEYS = (
    "DOCKER_HOST",
    "DOCKER_CONTEXT",
    "CARGO_HOME",
    "RUSTUP_HOME",
    "CARGO_TARGET_DIR",
)

# Required committed writer / lifecycle markers for adapter discovery.
CONTAINER_REQUIRED_FUNCTIONS: tuple[str, ...] = (
    "finalize_container_terminal_outcome",
    "write_outcome_evidence",
    "write_evidence_file_atomic",
    "container_narrow_build_main",
)

HOST_REQUIRED_FUNCTIONS: tuple[str, ...] = (
    "write_host_outcome_ingestion_record",
    "write_host_post_build_integrity_record",
    "write_host_validator_result_record",
    "invoke_host_preliminary_validator",
    "finalize_post_docker_host_failure",
    "finalize_pre_docker_infrastructure_failure",
    "run_witness_narrow_build_main",
)

HOST_LIFECYCLE_MARKERS: tuple[str, ...] = (
    'mark_stage "step21_manifest_generation"',
    'mark_stage "step21b_host_preliminary_validator"',
    'mark_stage "step22_summary_and_exit"',
)


def find_bash() -> str:
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
    raise ScenarioFrameworkError("bash not available for Phase 3G harness")


def run_bash(
    args: list[str], *, env: Mapping[str, str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [find_bash(), *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=dict(env),
        cwd=str(cwd) if cwd is not None else None,
    )


def write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def host_python_bash_path(python: Path | None = None) -> str:
    p = Path(python or sys.executable).resolve()
    s = str(p)
    if len(s) >= 2 and s[1] == ":":
        return f"/{s[0].lower()}{s[2:].replace(chr(92), '/')}"
    return p.as_posix()


def _is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


@dataclass
class CommandShimFramework:
    """PATH-first non-delegating prohibited-command shims."""

    workspace: Path
    ws_rel: str
    mock_bin: Path = field(init=False)
    cmd_log: Path = field(init=False)
    mock_bin_rel: str = field(init=False)
    cmd_log_rel: str = field(init=False)

    def __post_init__(self) -> None:
        self.mock_bin = self.workspace / "mock-bin"
        self.mock_bin.mkdir(parents=True, exist_ok=True)
        self.cmd_log = self.workspace / "prohibited_commands.log"
        self.cmd_log.write_text("", encoding="utf-8")
        self.mock_bin_rel = f"{self.ws_rel}/mock-bin"
        self.cmd_log_rel = f"{self.ws_rel}/prohibited_commands.log"
        for name in PROHIBITED_COMMANDS:
            write_executable(
                self.mock_bin / name,
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    set -euo pipefail
                    printf 'PROHIBITED %s\\n' {shlex.quote(name)} >> {shlex.quote(self.cmd_log_rel)}
                    echo "mock-{name}: prohibited in Phase 3G tests; never delegates" >&2
                    exit 99
                    """
                ),
            )

    def path_prefix(self) -> str:
        return self.mock_bin_rel

    def assert_no_prohibited_invocations(self) -> None:
        text = self.cmd_log.read_text(encoding="utf-8")
        if text:
            raise ScenarioFrameworkError(f"prohibited command invoked: {text!r}")

    def invocations(self) -> list[str]:
        return [
            line.strip()
            for line in self.cmd_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


@dataclass
class DisposableWorkspace:
    """Repository-local disposable workspace with residue protections."""

    workspace: Path
    _tmpdir: tempfile.TemporaryDirectory[str]
    evidence: Path
    home: Path
    work_root: Path
    source: Path
    tmp: Path
    captures: Path
    shims: CommandShimFramework
    ws_rel: str
    ws_basename: str

    @classmethod
    def create(cls) -> "DisposableWorkspace":
        tmpdir = tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(TESTS_DIR))
        workspace = Path(tmpdir.name).resolve()
        if workspace.parent != TESTS_DIR:
            tmpdir.cleanup()
            raise ScenarioFrameworkError(
                f"workspace parent must be {TESTS_DIR}, got {workspace.parent}"
            )
        if not workspace.name.startswith(TEMP_PREFIX):
            tmpdir.cleanup()
            raise ScenarioFrameworkError(
                f"workspace name must start with {TEMP_PREFIX!r}: {workspace.name}"
            )
        ws_basename = workspace.name
        ws_rel = f"tests/{ws_basename}"
        evidence = workspace / "evidence"
        home = workspace / "home"
        work_root = workspace / "work"
        source = workspace / "source"
        tmp = workspace / "tmp"
        captures = workspace / "captures"
        for p in (evidence, home, work_root, source, tmp, captures):
            p.mkdir(parents=True, exist_ok=True)
        shims = CommandShimFramework(workspace=workspace, ws_rel=ws_rel)
        return cls(
            workspace=workspace,
            _tmpdir=tmpdir,
            evidence=evidence,
            home=home,
            work_root=work_root,
            source=source,
            tmp=tmp,
            captures=captures,
            shims=shims,
            ws_rel=ws_rel,
            ws_basename=ws_basename,
        )

    def base_env(self) -> dict[str, str]:
        env: dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.home),
            "TMPDIR": str(self.tmp),
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
        for k in _STRIP_ENV_KEYS:
            env.pop(k, None)
        for k in ("SYSTEMROOT", "WINDIR", "SystemRoot", "COMSPEC"):
            if k in os.environ:
                env[k] = os.environ[k]
        return env

    def bash_env(self) -> dict[str, str]:
        env = self.base_env()
        env["HOME"] = f"{self.ws_rel}/home"
        env["TMPDIR"] = f"{self.ws_rel}/tmp"
        env["PATH"] = self.shims.path_prefix() + ":" + env.get("PATH", "")
        return env

    def cleanup(self) -> None:
        safe_cleanup_workspace(self.workspace, tmpdir=self._tmpdir)


def safe_cleanup_workspace(
    path: Path, *, tmpdir: tempfile.TemporaryDirectory[str] | None = None
) -> None:
    """Cleanup only test-owned phase3g_test_* under TESTS_DIR. Never silent elsewhere."""
    resolved = path.resolve()
    if resolved.parent != TESTS_DIR:
        raise ScenarioFrameworkError(
            f"refusing to delete non-test path outside tests dir: {resolved}"
        )
    if not resolved.name.startswith(TEMP_PREFIX):
        raise ScenarioFrameworkError(
            f"refusing to delete unexpected non-test path: {resolved}"
        )
    if tmpdir is not None:
        tmpdir.cleanup()
    elif resolved.exists():
        shutil.rmtree(resolved)
    if resolved.exists():
        raise ScenarioFrameworkError(
            f"failed to remove repository-local workspace: {resolved}"
        )


def remaining_phase3g_temps() -> list[Path]:
    if not TESTS_DIR.is_dir():
        return []
    return sorted(
        p for p in TESTS_DIR.iterdir() if p.is_dir() and p.name.startswith(TEMP_PREFIX)
    )


@dataclass(frozen=True)
class SourcedWriterDiscovery:
    script_path: Path
    required_functions: tuple[str, ...]
    found_functions: tuple[str, ...]
    missing_functions: tuple[str, ...]
    lifecycle_markers_found: tuple[str, ...]
    lifecycle_markers_missing: tuple[str, ...]


class SourcedWriterAdapter:
    """Locate and safely source committed container/host writer functions."""

    def __init__(self, workspace: DisposableWorkspace) -> None:
        self.workspace = workspace

    def discover_container(self) -> SourcedWriterDiscovery:
        return self._discover(
            CONTAINER_SCRIPT, CONTAINER_REQUIRED_FUNCTIONS, lifecycle_markers=()
        )

    def discover_host(self) -> SourcedWriterDiscovery:
        return self._discover(
            HOST_SCRIPT, HOST_REQUIRED_FUNCTIONS, lifecycle_markers=HOST_LIFECYCLE_MARKERS
        )

    def _discover(
        self,
        script: Path,
        required: Sequence[str],
        *,
        lifecycle_markers: Sequence[str],
    ) -> SourcedWriterDiscovery:
        if not script.is_file():
            raise ScenarioFrameworkError(f"missing script: {script}")
        text = script.read_text(encoding="utf-8")
        found: list[str] = []
        missing: list[str] = []
        for name in required:
            if re.search(rf"(?m)^{re.escape(name)}\(\)\s*\{{", text):
                found.append(name)
            else:
                missing.append(name)
        markers_found = [m for m in lifecycle_markers if m in text]
        markers_missing = [m for m in lifecycle_markers if m not in text]
        return SourcedWriterDiscovery(
            script_path=script,
            required_functions=tuple(required),
            found_functions=tuple(found),
            missing_functions=tuple(missing),
            lifecycle_markers_found=tuple(markers_found),
            lifecycle_markers_missing=tuple(markers_missing),
        )

    def smoke_source_container_functions(self) -> subprocess.CompletedProcess[str]:
        """Source container script and assert required functions exist; do not run main."""
        names = " ".join(CONTAINER_REQUIRED_FUNCTIONS)
        body = textwrap.dedent(
            f"""\
            set -euo pipefail
            # shellcheck disable=SC1091
            source ./{CONTAINER_SCRIPT_NAME}
            for fn in {names}; do
              test "$(type -t "$fn")" = "function"
            done
            printf 'CONTAINER_MAIN_TYPE=%s\\n' "$(type -t container_narrow_build_main)"
            """
        )
        return run_bash(["-c", body], env=self.workspace.bash_env(), cwd=SCRIPTS_DIR)

    def smoke_source_host_functions(self) -> subprocess.CompletedProcess[str]:
        """Source host script and assert required functions exist; do not run main."""
        names = " ".join(HOST_REQUIRED_FUNCTIONS)
        body = textwrap.dedent(
            f"""\
            set -euo pipefail
            # shellcheck disable=SC1091
            source ./{HOST_SCRIPT_NAME}
            EVIDENCE_DIR={shlex.quote(self.workspace.ws_rel + "/evidence")}
            WORK_ROOT={shlex.quote(self.workspace.ws_rel + "/work")}
            TMP_DIR={shlex.quote(self.workspace.ws_rel + "/tmp")}
            for fn in {names}; do
              test "$(type -t "$fn")" = "function"
            done
            printf 'HOST_MAIN_TYPE=%s\\n' "$(type -t run_witness_narrow_build_main)"
            """
        )
        return run_bash(["-c", body], env=self.workspace.bash_env(), cwd=SCRIPTS_DIR)


@dataclass(frozen=True)
class ValidatorDriverResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    stdout_capture_path: Path
    stderr_capture_path: Path
    evidence_dir: Path


class RealValidatorDriver:
    """Invoke committed local validator with --host-preliminary (framework only)."""

    def __init__(
        self,
        workspace: DisposableWorkspace,
        *,
        python_executable: str | None = None,
    ) -> None:
        self.workspace = workspace
        # Explicit interpreter binding — never Windows py-manager via command -v.
        self.python_executable = str(
            Path(python_executable or sys.executable).resolve()
        )
        self.validator_script = VALIDATOR_SCRIPT

    def build_command(self, evidence_dir: Path) -> tuple[str, ...]:
        return (
            self.python_executable,
            str(self.validator_script.resolve()),
            "--host-preliminary",
            str(evidence_dir.resolve()),
        )

    def run_host_preliminary(
        self, evidence_dir: Path, *, capture_dir: Path | None = None
    ) -> ValidatorDriverResult:
        if not evidence_dir.is_dir():
            raise ScenarioFrameworkError(f"evidence_dir is not a directory: {evidence_dir}")
        cap = capture_dir or self.workspace.captures
        cap.mkdir(parents=True, exist_ok=True)
        stdout_path = cap / "VALIDATOR_STDOUT.txt"
        stderr_path = cap / "VALIDATOR_STDERR.txt"
        if _is_under(stdout_path, evidence_dir):
            raise ScenarioFrameworkError("stdout capture must be outside EVIDENCE_DIR")
        if _is_under(stderr_path, evidence_dir):
            raise ScenarioFrameworkError("stderr capture must be outside EVIDENCE_DIR")

        before_names = {p.name for p in evidence_dir.iterdir() if p.is_file()}
        before_mtime = {
            p.name: p.stat().st_mtime_ns
            for p in evidence_dir.iterdir()
            if p.is_file()
        }
        cmd = self.build_command(evidence_dir)
        cp = subprocess.run(
            list(cmd),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            cwd=str(SCRIPTS_DIR),
            env=self.workspace.base_env(),
        )
        stdout_path.write_text(cp.stdout, encoding="utf-8", newline="\n")
        stderr_path.write_text(cp.stderr, encoding="utf-8", newline="\n")
        after_names = {p.name for p in evidence_dir.iterdir() if p.is_file()}
        after_mtime = {
            p.name: p.stat().st_mtime_ns
            for p in evidence_dir.iterdir()
            if p.is_file()
        }
        if before_names != after_names:
            raise ScenarioFrameworkError(
                "validator driver must not write evidence; file set changed"
            )
        if before_mtime != after_mtime:
            raise ScenarioFrameworkError(
                "validator driver must not write evidence; mtime set changed"
            )
        return ValidatorDriverResult(
            command=cmd,
            returncode=cp.returncode,
            stdout=cp.stdout,
            stderr=cp.stderr,
            stdout_capture_path=stdout_path,
            stderr_capture_path=stderr_path,
            evidence_dir=evidence_dir,
        )


@dataclass(frozen=True)
class FullMainHarnessPrep:
    """Framework preparation for Phase 3G-B limited full-main smoke (not executed)."""

    main_entry_point: Path
    main_function_name: str
    env: Mapping[str, str]
    shim_path_prefix: str
    work_root: Path
    source_root: Path
    evidence_dir: Path
    execute_authorized: bool = False


class FullMainHarness:
    """Build controlled env / shims / roots; do not execute real workflow in 3G-A."""

    def __init__(self, workspace: DisposableWorkspace) -> None:
        self.workspace = workspace

    def prepare(self) -> FullMainHarnessPrep:
        if not HOST_SCRIPT.is_file():
            raise ScenarioFrameworkError(f"missing host main entry: {HOST_SCRIPT}")
        env = self.workspace.bash_env()
        env["WORK_ROOT"] = f"{self.workspace.ws_rel}/work"
        env["EVIDENCE_DIR"] = f"{self.workspace.ws_rel}/evidence"
        env["HOME"] = f"{self.workspace.ws_rel}/home"
        return FullMainHarnessPrep(
            main_entry_point=HOST_SCRIPT,
            main_function_name="run_witness_narrow_build_main",
            env=env,
            shim_path_prefix=self.workspace.shims.path_prefix(),
            work_root=self.workspace.work_root,
            source_root=self.workspace.source,
            evidence_dir=self.workspace.evidence,
            execute_authorized=False,
        )

    def assert_not_executed(self, prep: FullMainHarnessPrep) -> None:
        if prep.execute_authorized:
            raise ScenarioFrameworkError(
                "Phase 3G-A must not authorize full-main execution"
            )
        self.workspace.shims.assert_no_prohibited_invocations()
