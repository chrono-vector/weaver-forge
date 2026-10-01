"""Controlled process execution for WVMA-V1 Batch A2.

Runner code is trusted and must remain outside the mutated disposable tree.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from wvma_v1.canonical import canonical_digest
from wvma_v1.target_launcher import ALLOWED_INVOCATION_IDS, module_origin as launcher_module_origin
from wvma_v1.workspace import (
    WorkspaceError,
    assert_no_reparse_chain,
    ensure_output_root_confined,
    resolve_under_root,
)

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_OUTPUT_BYTES = 64 * 1024
RUNNER_CONTRACT_VERSION = "wvma_v1.runner.a2"


class RunnerError(ValueError):
    """Process execution contract rejection."""


@dataclass(frozen=True)
class InvocationContract:
    """Code-owned invocation binding; never carries arbitrary shell strings."""

    invocation_id: str
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.invocation_id, str) or not self.invocation_id:
            raise RunnerError("invocation_id must be non-empty str")
        if self.invocation_id not in ALLOWED_INVOCATION_IDS:
            raise RunnerError(f"unsupported invocation_id: {self.invocation_id}")
        if not isinstance(self.timeout_seconds, (int, float)) or isinstance(
            self.timeout_seconds, bool
        ):
            raise RunnerError("timeout_seconds must be a number")
        if float(self.timeout_seconds) <= 0:
            raise RunnerError("timeout_seconds must be > 0")
        if not isinstance(self.max_output_bytes, int) or isinstance(
            self.max_output_bytes, bool
        ):
            raise RunnerError("max_output_bytes must be int")
        if self.max_output_bytes <= 0:
            raise RunnerError("max_output_bytes must be > 0")


@dataclass(frozen=True)
class ProcessReceipt:
    """Structured execution evidence for independent oracle evaluation."""

    invocation_id: str
    argv: tuple[str, ...]
    cwd: str
    exit_code: int | None
    timed_out: bool
    stdout_sha256: str
    stderr_sha256: str
    stdout_truncated: bool
    stderr_truncated: bool
    stdout_byte_length: int
    stderr_byte_length: int
    python_executable: str
    launcher_module_origin: str
    runner_module_origin: str
    env_digest: str
    started_at: str
    completed_at: str
    workspace_root: str
    verify_ok_claimed: bool | None
    self_claimed_result: str | None
    stdout_text_preview: str

    def to_observation_dict(self) -> dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "invocation_id": self.invocation_id,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "launcher_module_origin": self.launcher_module_origin,
            "runner_module_origin": self.runner_module_origin,
            "verify_ok_claimed": self.verify_ok_claimed,
            "self_claimed_result": self.self_claimed_result,
        }


def runner_module_origin() -> str:
    return str(Path(__file__).resolve())


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _absolute_python() -> str:
    exe = Path(sys.executable)
    if not exe.is_file():
        raise RunnerError(f"python executable missing: {exe}")
    resolved = str(exe.resolve())
    if not os.path.isabs(resolved):
        raise RunnerError("python executable must be absolute")
    return resolved


def _bounded_capture(raw: bytes, limit: int) -> tuple[bytes, bool]:
    if len(raw) > limit:
        return raw[:limit], True
    return raw, False


def _build_env(*, home: Path, tmp: Path) -> dict[str, str]:
    """Deterministic, network-avoiding environment for child processes."""
    env: dict[str, str] = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONHASHSEED": "0",
        "HOME": str(home),
        "USERPROFILE": str(home),
        "TMP": str(tmp),
        "TEMP": str(tmp),
        "TMPDIR": str(tmp),
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_TERMINAL_PROMPT": "0",
    }
    # Windows needs SystemRoot for CRT; keep minimal host essentials only.
    for key in ("SYSTEMROOT", "WINDIR", "SystemRoot", "COMSPEC", "PATH"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def _parse_launcher_stdout(text: str) -> tuple[bool | None, str | None]:
    """Extract claimed fields without trusting them for DETECTED."""
    import json

    line = text.strip().splitlines()[0] if text.strip() else ""
    if not line:
        return None, None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(payload, dict):
        return None, None
    verify = payload.get("verify_ok")
    claimed = payload.get("self_claimed_result")
    verify_ok = verify if isinstance(verify, bool) else None
    self_claimed = claimed if isinstance(claimed, str) else None
    return verify_ok, self_claimed


def _launch(
    *,
    contract: InvocationContract,
    workspace_root: Path,
    isolated_home: Path,
    isolated_tmp: Path,
) -> ProcessReceipt:
    python = _absolute_python()
    launcher = Path(launcher_module_origin())
    if not launcher.is_file():
        raise RunnerError(f"trusted launcher missing: {launcher}")
    # Ensure launcher is NOT loaded from the disposable workspace.
    try:
        launcher.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        pass
    else:
        raise RunnerError("launcher origin is inside disposable workspace")

    argv = [
        python,
        "-B",
        str(launcher),
        "--invocation-id",
        contract.invocation_id,
        "--workspace",
        str(workspace_root),
    ]
    env = _build_env(home=isolated_home, tmp=isolated_tmp)
    env_digest = canonical_digest(dict(sorted(env.items())))
    started = _utc_now()
    try:
        proc = subprocess.run(
            argv,
            cwd=str(workspace_root),
            env=env,
            capture_output=True,
            shell=False,
            timeout=float(contract.timeout_seconds),
            check=False,
        )
        timed_out = False
        exit_code: int | None = int(proc.returncode)
        stdout_raw = proc.stdout or b""
        stderr_raw = proc.stderr or b""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout_raw = exc.stdout or b""
        stderr_raw = exc.stderr or b""
    except OSError as exc:
        raise RunnerError(f"process launch failed: {exc}") from exc
    completed = _utc_now()

    stdout, stdout_trunc = _bounded_capture(stdout_raw, contract.max_output_bytes)
    stderr, stderr_trunc = _bounded_capture(stderr_raw, contract.max_output_bytes)
    stdout_text = stdout.decode("utf-8", errors="replace")
    verify_ok, self_claimed = _parse_launcher_stdout(stdout_text)

    return ProcessReceipt(
        invocation_id=contract.invocation_id,
        argv=tuple(argv),
        cwd=str(workspace_root),
        exit_code=exit_code,
        timed_out=timed_out,
        stdout_sha256=_sha256_bytes(stdout),
        stderr_sha256=_sha256_bytes(stderr),
        stdout_truncated=stdout_trunc,
        stderr_truncated=stderr_trunc,
        stdout_byte_length=len(stdout_raw),
        stderr_byte_length=len(stderr_raw),
        python_executable=python,
        launcher_module_origin=str(launcher.resolve()),
        runner_module_origin=runner_module_origin(),
        env_digest=env_digest,
        started_at=started,
        completed_at=completed,
        workspace_root=str(workspace_root),
        verify_ok_claimed=verify_ok,
        self_claimed_result=self_claimed,
        stdout_text_preview=stdout_text[:512],
    )


def _prepare_workspace(workspace_root: Path | str) -> Path:
    raw = Path(workspace_root)
    try:
        # Reject junction/symlink aliases before resolve erases them.
        assert_no_reparse_chain(raw, field="workspace_root")
        root = raw.resolve()
        if not root.is_dir():
            raise RunnerError(f"workspace_root is not a directory: {root}")
        assert_no_reparse_chain(root, field="workspace_root")
    except WorkspaceError as exc:
        raise RunnerError(str(exc)) from exc
    return root


def run_baseline(
    *,
    workspace_root: Path | str,
    contract: InvocationContract,
    protected_paths: tuple[Path | str, ...] = (),
    active_repository: Path | str | None = None,
    output_root: Path | str | None = None,
) -> ProcessReceipt:
    """Execute the baseline invocation inside the disposable workspace."""
    if not isinstance(contract, InvocationContract):
        raise RunnerError("contract must be InvocationContract")
    root = _prepare_workspace(workspace_root)
    if output_root is not None:
        try:
            ensure_output_root_confined(
                output_root,
                protected_paths=protected_paths,
                active_repository=active_repository,
            )
        except WorkspaceError as exc:
            raise RunnerError(str(exc)) from exc

    with tempfile.TemporaryDirectory(prefix="wvma-run-home-") as home:
        with tempfile.TemporaryDirectory(prefix="wvma-run-tmp-") as tmp:
            return _launch(
                contract=contract,
                workspace_root=root,
                isolated_home=Path(home),
                isolated_tmp=Path(tmp),
            )


def run_mutation_case(
    *,
    workspace_root: Path | str,
    contract: InvocationContract,
    protected_paths: tuple[Path | str, ...] = (),
    active_repository: Path | str | None = None,
    output_root: Path | str | None = None,
    require_target_relative_path: str | None = None,
) -> ProcessReceipt:
    """Execute a mutation-case invocation; same trust boundary as baseline."""
    root = _prepare_workspace(workspace_root)
    if require_target_relative_path is not None:
        try:
            resolve_under_root(root, require_target_relative_path)
        except WorkspaceError as exc:
            raise RunnerError(str(exc)) from exc
    return run_baseline(
        workspace_root=root,
        contract=contract,
        protected_paths=protected_paths,
        active_repository=active_repository,
        output_root=output_root,
    )


def receipt_digest(receipt: ProcessReceipt) -> str:
    """Canonical digest of receipt observation fields."""
    return canonical_digest(receipt.to_observation_dict())


__all__ = [
    "RunnerError",
    "InvocationContract",
    "ProcessReceipt",
    "run_baseline",
    "run_mutation_case",
    "runner_module_origin",
    "receipt_digest",
    "RUNNER_CONTRACT_VERSION",
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_MAX_OUTPUT_BYTES",
]
