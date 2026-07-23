#!/usr/bin/env python3
"""Phase 3C container terminal-outcome finalization tests.

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (never the OS default temp root)
- Every Bash subprocess uses cwd=SCRIPTS_DIR and repository-local relative paths
- container_narrow_build.sh is sourced only; container_narrow_build_main is never invoked
- Mock commands (if any) are first on PATH and never delegate to real Docker/Cargo/etc.
- No remote clones / no network
- No Cargo, rustc, rustup, DotSlash, protoc, ldd, Docker, validator, or product execution
- Cleanup of repository-local temps on success and failure
"""

from __future__ import annotations

import json
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

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
GROK_BUILD_DIR = PACKAGE_DIR.parent
CONTAINER_SCRIPT_NAME = "container_narrow_build.sh"
CONTAINER_SCRIPT = SCRIPTS_DIR / CONTAINER_SCRIPT_NAME
CONTRACT_PATH = PACKAGE_DIR / "AUTHORITATIVE_OUTCOME_CONTRACT.json"
TEMP_PREFIX = "phase3c_test_"

EXPECTED_TERMINAL = (
    "BUILD_NOT_STARTED",
    "CARGO_FAILED",
    "CARGO_SUCCEEDED_ARTIFACT_MISSING",
    "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
    "INFRASTRUCTURE_FAILURE",
)

PROHIBITED_COMMANDS = (
    "docker",
    "cargo",
    "rustc",
    "rustup",
    "dotslash",
    "protoc",
    "ldd",
    "validate_witness_evidence",
)

_STRIP_ENV_KEYS = (
    "DOCKER_HOST",
    "DOCKER_CONTEXT",
    "CARGO_HOME",
    "RUSTUP_HOME",
    "CARGO_TARGET_DIR",
)


def _find_bash() -> str:
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
    raise unittest.SkipTest("bash not available for Phase 3C container finalization tests")


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


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _remaining_phase3c_temps() -> list[Path]:
    if not TESTS_DIR.is_dir():
        return []
    return sorted(
        p for p in TESTS_DIR.iterdir() if p.is_dir() and p.name.startswith(TEMP_PREFIX)
    )


def _read_kv(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _count_outcome_lines(path: Path) -> int:
    if not path.is_file():
        return 0
    return sum(
        1
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.startswith("outcome=")
    )


class Phase3CContainerTerminalFinalizationTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_phase3c_temps()
        assert not leftovers, (
            f"Phase 3C temporary directories remain under {TESTS_DIR}: "
            f"{[p.name for p in leftovers]}"
        )

    def setUp(self) -> None:
        self.assertTrue(CONTAINER_SCRIPT.is_file(), f"missing container script: {CONTAINER_SCRIPT}")
        self.assertTrue(CONTRACT_PATH.is_file(), f"missing contract: {CONTRACT_PATH}")
        self._tmpdir = tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(TESTS_DIR))
        self.workspace = Path(self._tmpdir.name).resolve()
        self.assertEqual(self.workspace.parent, TESTS_DIR)
        self.ws_basename = self.workspace.name
        self.ws_rel = f"tests/{self.ws_basename}"
        self.assertFalse(Path(self.ws_rel).is_absolute())
        self.assertTrue(self.ws_rel.startswith("tests/"))

        self.evidence = self.workspace / "evidence"
        self.evidence.mkdir()
        self.evidence_rel = f"{self.ws_rel}/evidence"

        self.mock_bin = self.workspace / "mock-bin"
        self.mock_bin.mkdir()
        self.cmd_log = self.workspace / "prohibited_commands.log"
        self.cmd_log.write_text("", encoding="utf-8")
        self.mock_bin_rel = f"{self.ws_rel}/mock-bin"
        self.cmd_log_rel = f"{self.ws_rel}/prohibited_commands.log"

        # Install non-delegating stubs that fail closed if invoked.
        for name in PROHIBITED_COMMANDS:
            _write_executable(
                self.mock_bin / name,
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    set -euo pipefail
                    printf 'PROHIBITED %s\\n' {shlex.quote(name)} >> {shlex.quote(self.cmd_log_rel)}
                    echo "mock-{name}: prohibited in Phase 3C tests" >&2
                    exit 99
                    """
                ),
            )

        self.env: dict[str, str] = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(self.workspace / "home"),
            "TMPDIR": str(self.workspace / "tmp"),
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
        (self.workspace / "home").mkdir()
        (self.workspace / "tmp").mkdir()
        for k in _STRIP_ENV_KEYS:
            self.env.pop(k, None)
        for k in ("SYSTEMROOT", "WINDIR", "SystemRoot", "COMSPEC"):
            if k in os.environ:
                self.env[k] = os.environ[k]

    def tearDown(self) -> None:
        workspace = getattr(self, "workspace", None)
        self._tmpdir.cleanup()
        if workspace is not None:
            self.assertFalse(
                workspace.exists(),
                f"TemporaryDirectory failed to remove repository-local workspace: {workspace}",
            )

    def _bash_env(self) -> dict[str, str]:
        env = dict(self.env)
        env["HOME"] = self.ws_rel + "/home"
        env["TMPDIR"] = self.ws_rel + "/tmp"
        # Prepend mock-bin so any accidental prohibited command hits the stub.
        env["PATH"] = self.mock_bin_rel + ":" + env.get("PATH", "")
        return env

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = textwrap.dedent(
            f"""\
            set -euo pipefail
            # Source production container helpers; main must not run.
            # shellcheck disable=SC1091
            source ./{CONTAINER_SCRIPT_NAME}
            EVIDENCE={shlex.quote(self.evidence_rel)}
            ARTIFACT={shlex.quote(self.ws_rel + "/no-such-artifact")}
            EVIDENCE_FINALIZED=NO
            FINALIZING_IN_PROGRESS=NO
            CONTAINER_MAIN_ACTIVE=NO
            CARGO_STARTED=NO
            CARGO_EXIT_CODE=
            CARGO_START_UTC=
            CARGO_END_UTC=
            CARGO_ELAPSED_SECONDS=
            CURRENT_STAGE=test
            CT_STATUS=pending
            CT_OUTCOME=NOT_REACHED
            CT_TARGET_PATH_HOST=NOT_REACHED
            CT_PROOF_UTC_HOST=NOT_REACHED
            CT_OBS_HOST=NOT_REACHED
            CT_TARGET_PREBOOT=NOT_REACHED
            CT_UTC_PREBOOT=NOT_REACHED
            CT_OBS_PREBOOT=NOT_REACHED
            CT_TARGET_PRECARGO=NOT_REACHED
            CT_UTC_PRECARGO=NOT_REACHED
            CT_OBS_CONTAINER=NOT_REACHED
            CT_PROOF_FAILED=no
            CT_FAILURE_STAGE=NOT_REACHED
            CT_LISTINGS=
            {body}
            """
        )
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _init_evidence(self) -> None:
        cp = self._run_sourced("init_evidence")
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    def _assert_no_prohibited_invocations(self) -> None:
        text = self.cmd_log.read_text(encoding="utf-8")
        self.assertEqual(text, "", f"prohibited command invoked: {text!r}")

    def _assert_no_host_owned_writes(self) -> None:
        self.assertFalse((self.evidence / "POST_BUILD_INTEGRITY.txt").exists())
        self.assertFalse((self.evidence / "DOCKER_EXIT_CODE.txt").exists())

    def _assert_no_provisional_in_container_owned(self) -> None:
        provisional = (
            "pending",
            "pending_container_toolchain_capture",
            "bootstrap_complete",
        )
        # Files fully owned or partly terminalized by the container finalizer.
        names = (
            "BUILD_EXIT_CODE.txt",
            "BUILD_TIMING.txt",
            "ARTIFACT_IDENTITY.txt",
            "STATIC_ARTIFACT_INSPECTION.txt",
            "CLEAN_TARGET_PROOF.txt",
            "BUILD_COMMAND.txt",
            "BOOTSTRAP.txt",
            "ENVIRONMENT.txt",
        )
        for name in names:
            path = self.evidence / name
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in provisional:
                self.assertNotRegex(
                    text,
                    rf"(?m)^status={re.escape(token)}$",
                    f"{name} retains provisional status={token}",
                )
            # BUILD_EXIT_CODE / BUILD_TIMING must not keep NOT_REACHED outcome/status.
            if name in ("BUILD_EXIT_CODE.txt", "BUILD_TIMING.txt"):
                self.assertNotRegex(text, r"(?m)^status=NOT_REACHED$")
                self.assertNotRegex(text, r"(?m)^outcome=NOT_REACHED$")
                self.assertNotRegex(text, r"(?m)^build_status=NOT_REACHED$")
                self.assertNotRegex(text, r"(?m)^failure_stage=NOT_REACHED$")
                self.assertNotRegex(text, r"(?m)^cargo_exit_code=NOT_REACHED$")

    # ------------------------------------------------------------------
    # 1. sourcing performs no workflow
    # ------------------------------------------------------------------
    def test_01_sourcing_performs_no_workflow(self) -> None:
        marker = self.workspace / "sourced_ok"
        marker_rel = f"{self.ws_rel}/sourced_ok"
        body = textwrap.dedent(
            f"""\
            test "$(type -t finalize_container_terminal_outcome)" = "function"
            test "$(type -t write_evidence_file_atomic)" = "function"
            test "$(type -t container_narrow_build_main)" = "function"
            test "$(type -t fail_build_not_started)" = "function"
            test "$(type -t fail_infrastructure)" = "function"
            # Main must not have run from source alone.
            test "${{EVIDENCE_FINALIZED:-NO}}" = "NO"
            test ! -f {shlex.quote(self.evidence_rel)}/BUILD_EXIT_CODE.txt
            echo sourced_ok > {shlex.quote(marker_rel)}
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertTrue(marker.is_file())
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r'if\s+\[\[\s*"\$\{BASH_SOURCE\[0\]\}"\s*==\s*"\$0"\s*\]\]\s*;\s*then',
        )
        self.assertNotIn("WEAVER_FORGE_WITNESS_CONTAINER_SOURCED", text)
        self._assert_no_prohibited_invocations()

    # ------------------------------------------------------------------
    # 2. exact five terminal outcomes match contract
    # ------------------------------------------------------------------
    def test_02_five_terminal_outcomes_match_contract(self) -> None:
        contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        values = [row["value"] for row in contract["terminal_outcomes"]]
        self.assertEqual(tuple(values), EXPECTED_TERMINAL)
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        for outcome in EXPECTED_TERMINAL:
            self.assertIn(outcome, text)
        # Array declaration must list the exact five outcomes in contract order.
        m = re.search(r"TERMINAL_CONTAINER_OUTCOMES=\((.*?)\)", text, flags=re.S)
        self.assertIsNotNone(m)
        listed = re.findall(r"[A-Z_]+", m.group(1))
        self.assertEqual(tuple(listed), EXPECTED_TERMINAL)

    # ------------------------------------------------------------------
    # 3–5 BUILD_NOT_STARTED
    # ------------------------------------------------------------------
    def test_03_build_not_started_complete_terminal_evidence(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 7 "rustc_version_probe"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "BUILD_NOT_STARTED")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "status"), "FAILED")
        self.assertEqual(_read_kv(self.evidence / "ARTIFACT_IDENTITY.txt", "artifact_present"), "no")
        self.assertEqual(_read_kv(self.evidence / "STATIC_ARTIFACT_INSPECTION.txt", "status"), "NOT_APPLICABLE")
        self.assertTrue((self.evidence / "BUILD_STDOUT.txt").is_file())
        self.assertTrue((self.evidence / "BUILD_STDERR.txt").is_file())
        self._assert_no_provisional_in_container_owned()
        self._assert_no_host_owned_writes()
        self._assert_no_prohibited_invocations()

    def test_04_build_not_started_cargo_started_no(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "pre_bootstrap_empty_target"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_started"), "NO")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_exit_code"), "NOT_APPLICABLE")
        self.assertEqual(_read_kv(self.evidence / "BUILD_TIMING.txt", "cargo_started"), "NO")

    def test_05_build_not_started_no_provisional_values(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "apt_get_update"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self._assert_no_provisional_in_container_owned()
        # CLEAN_TARGET pending must be terminalized.
        self.assertNotEqual(_read_kv(self.evidence / "CLEAN_TARGET_PROOF.txt", "status"), "pending")

    # ------------------------------------------------------------------
    # 6–8 CARGO_FAILED
    # ------------------------------------------------------------------
    def test_06_cargo_failed_preserves_nonzero_exit(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=17
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:01Z
            CARGO_ELAPSED_SECONDS=1
            printf 'cargo out\\n' > "$EVIDENCE/BUILD_STDOUT.txt"
            printf 'cargo err\\n' > "$EVIDENCE/BUILD_STDERR.txt"
            finalize_container_terminal_outcome "CARGO_FAILED" 17 "cargo_build"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "CARGO_FAILED")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_started"), "YES")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_exit_code"), "17")

    def test_07_cargo_failed_preserves_stdout_stderr(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=9
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:01Z
            CARGO_ELAPSED_SECONDS=1
            printf 'UNIQUE_STDOUT_MARKER\\n' > "$EVIDENCE/BUILD_STDOUT.txt"
            printf 'UNIQUE_STDERR_MARKER\\n' > "$EVIDENCE/BUILD_STDERR.txt"
            finalize_container_terminal_outcome "CARGO_FAILED" 9 "cargo_build"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("UNIQUE_STDOUT_MARKER", (self.evidence / "BUILD_STDOUT.txt").read_text(encoding="utf-8"))
        self.assertIn("UNIQUE_STDERR_MARKER", (self.evidence / "BUILD_STDERR.txt").read_text(encoding="utf-8"))

    def test_08_cargo_failed_no_provisional_values(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=3
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:01Z
            CARGO_ELAPSED_SECONDS=1
            finalize_container_terminal_outcome "CARGO_FAILED" 3 "cargo_build"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self._assert_no_provisional_in_container_owned()
        self.assertEqual(_read_kv(self.evidence / "ARTIFACT_IDENTITY.txt", "artifact_present"), "no")

    # ------------------------------------------------------------------
    # 9–11 ARTIFACT_MISSING
    # ------------------------------------------------------------------
    def test_09_artifact_missing_preserves_cargo_exit_zero(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=0
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:02Z
            CARGO_ELAPSED_SECONDS=2
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_MISSING" 42 \
              "artifact_presence_check" "FAILED" "COMPLETE" "missing_applicable"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_exit_code"), "0")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_started"), "YES")

    def test_10_artifact_missing_records_absent(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=0
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:02Z
            CARGO_ELAPSED_SECONDS=2
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_MISSING" 42 \
              "artifact_presence_check"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "ARTIFACT_IDENTITY.txt", "artifact_present"), "no")
        self.assertEqual(_read_kv(self.evidence / "ARTIFACT_IDENTITY.txt", "outcome"), "CARGO_SUCCEEDED_ARTIFACT_MISSING")
        self.assertEqual(_read_kv(self.evidence / "STATIC_ARTIFACT_INSPECTION.txt", "status"), "NOT_APPLICABLE")

    def test_11_artifact_missing_success_impossible(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=0
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:02Z
            CARGO_ELAPSED_SECONDS=2
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_MISSING" 42 \
              "artifact_presence_check"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "status"), "FAILED")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "CARGO_SUCCEEDED_ARTIFACT_MISSING")

    # ------------------------------------------------------------------
    # 12–14 ARTIFACT_PRESENT static success/failure
    # ------------------------------------------------------------------
    def _write_present_artifact_evidence(self, *, static_ok: bool) -> str:
        static_status = "OK" if static_ok else "FAILED"
        inspection_complete = "yes" if static_ok else "no"
        return textwrap.dedent(
            f"""\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=0
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:03Z
            CARGO_ELAPSED_SECONDS=3
            cat > "$EVIDENCE/ARTIFACT_IDENTITY.txt" <<'EOF'
            evidence_schema_version=1
            outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
            applicable=yes
            artifact_present=yes
            artifact_path=/work/cargo-target/debug/xai-grok-pager
            artifact_filename=xai-grok-pager
            artifact_size_bytes=123
            artifact_sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            gnu_build_id=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
            static_inspection_complete={inspection_complete}
            product_executed=NO
            ldd_used=NO
            EOF
            cat > "$EVIDENCE/STATIC_ARTIFACT_INSPECTION.txt" <<'EOF'
            BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION
            evidence_schema_version=1
            status={static_status}
            outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
            applicable=yes
            artifact_present=yes
            artifact_path=/work/cargo-target/debug/xai-grok-pager
            sha256sum_command=sha256sum /work/cargo-target/debug/xai-grok-pager
            sha256sum_output=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            sha256sum_exit_code=0
            stat_command=stat /work/cargo-target/debug/xai-grok-pager
            stat_output=Size: 123
            stat_exit_code=0
            file_command=file /work/cargo-target/debug/xai-grok-pager
            file_output=ELF
            file_exit_code=0
            readelf_h_command=readelf -h
            readelf_h_output=ELF
            readelf_h_exit_code=0
            readelf_n_command=readelf -n
            readelf_n_output=Build ID: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
            readelf_n_exit_code=0
            readelf_d_command=readelf -d
            readelf_d_output=Dynamic
            readelf_d_exit_code=0
            objdump_f_command=objdump -f
            objdump_f_output=file format
            objdump_f_exit_code=0
            inspection_complete={inspection_complete}
            failure_stage={"NOT_APPLICABLE" if static_ok else "static_file"}
            reason=test
            END_SCHEMA_BLOCK
            EOF
            """
        )

    def test_12_artifact_present_static_success_finalization(self) -> None:
        self._init_evidence()
        body = self._write_present_artifact_evidence(static_ok=True)
        body += textwrap.dedent(
            """\
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_PRESENT" 0 \
              "NOT_APPLICABLE" "OK" "COMPLETE" "preserve"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "CARGO_SUCCEEDED_ARTIFACT_PRESENT")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "status"), "OK")
        self.assertEqual(_read_kv(self.evidence / "ARTIFACT_IDENTITY.txt", "artifact_present"), "yes")
        self.assertEqual(_read_kv(self.evidence / "STATIC_ARTIFACT_INSPECTION.txt", "status"), "OK")

    def test_13_artifact_present_static_failure_finalization(self) -> None:
        self._init_evidence()
        body = self._write_present_artifact_evidence(static_ok=False)
        body += textwrap.dedent(
            """\
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_PRESENT" 43 \
              "static_file" "FAILED" "COMPLETE" "preserve"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "CARGO_SUCCEEDED_ARTIFACT_PRESENT")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "status"), "FAILED")
        self.assertEqual(_read_kv(self.evidence / "STATIC_ARTIFACT_INSPECTION.txt", "inspection_complete"), "no")

    def test_14_static_failure_preserves_outcome_and_nonzero_exit(self) -> None:
        self._init_evidence()
        body = self._write_present_artifact_evidence(static_ok=False)
        body += textwrap.dedent(
            """\
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_PRESENT" 43 \
              "static_file" "FAILED" "COMPLETE" "preserve"
            printf 'EXIT_FIELD=%s\\n' "$(read_kv "$EVIDENCE/BUILD_EXIT_CODE.txt" outcome)"
            printf 'STATUS_FIELD=%s\\n' "$(read_kv "$EVIDENCE/BUILD_EXIT_CODE.txt" status)"
            printf 'DOCKER_FIELD=%s\\n' "$(read_kv "$EVIDENCE/BUILD_TIMING.txt" docker_exit_code)"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("EXIT_FIELD=CARGO_SUCCEEDED_ARTIFACT_PRESENT", cp.stdout)
        self.assertIn("STATUS_FIELD=FAILED", cp.stdout)
        self.assertIn("DOCKER_FIELD=43", cp.stdout)
        self.assertEqual(_read_kv(self.evidence / "ARTIFACT_IDENTITY.txt", "artifact_present"), "yes")

    # ------------------------------------------------------------------
    # 15–18 INFRASTRUCTURE_FAILURE
    # ------------------------------------------------------------------
    def test_15_infra_before_cargo_cargo_started_no(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=NO
            CARGO_EXIT_CODE=
            finalize_container_terminal_outcome "INFRASTRUCTURE_FAILURE" 1 "unexpected_err"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_started"), "NO")
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_exit_code"), "NOT_APPLICABLE")

    def test_16_infra_after_cargo_preserves_cargo_started_yes(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=0
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:04Z
            CARGO_ELAPSED_SECONDS=4
            printf 'kept-out\\n' > "$EVIDENCE/BUILD_STDOUT.txt"
            printf 'kept-err\\n' > "$EVIDENCE/BUILD_STDERR.txt"
            finalize_container_terminal_outcome "INFRASTRUCTURE_FAILURE" 1 "post_cargo_infra"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_started"), "YES")

    def test_17_infra_preserves_observed_cargo_exit(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=11
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:04Z
            CARGO_ELAPSED_SECONDS=4
            finalize_container_terminal_outcome "INFRASTRUCTURE_FAILURE" 1 "post_cargo_infra"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "cargo_exit_code"), "11")

    def test_18_infra_preserves_observed_stdout_stderr(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=5
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:04Z
            CARGO_ELAPSED_SECONDS=4
            printf 'INFRA_STDOUT\\n' > "$EVIDENCE/BUILD_STDOUT.txt"
            printf 'INFRA_STDERR\\n' > "$EVIDENCE/BUILD_STDERR.txt"
            finalize_container_terminal_outcome "INFRASTRUCTURE_FAILURE" 1 "post_cargo_infra"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("INFRA_STDOUT", (self.evidence / "BUILD_STDOUT.txt").read_text(encoding="utf-8"))
        self.assertIn("INFRA_STDERR", (self.evidence / "BUILD_STDERR.txt").read_text(encoding="utf-8"))

    # ------------------------------------------------------------------
    # 19–23 finalization semantics
    # ------------------------------------------------------------------
    def test_19_explicit_terminal_outcome_appears_exactly_once(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_x"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(_count_outcome_lines(self.evidence / "BUILD_EXIT_CODE.txt"), 1)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "BUILD_NOT_STARTED")

    def test_20_duplicate_conflicting_finalization_fails_closed(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"
            set +e
            finalize_container_terminal_outcome "CARGO_FAILED" 2 "stage_b"
            ec=$?
            set -e
            printf 'CONFLICT_EC=%s\\n' "$ec"
            printf 'FINAL=%s\\n' "$EVIDENCE_FINALIZED"
            printf 'OUTCOME=%s\\n' "$(read_kv "$EVIDENCE/BUILD_EXIT_CODE.txt" outcome)"
            exit 0
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("CONFLICT_EC=1", cp.stdout)
        self.assertIn("OUTCOME=BUILD_NOT_STARTED", cp.stdout)
        self.assertEqual(_read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"), "BUILD_NOT_STARTED")

    def test_21_same_value_idempotent_finalization_safe(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"
            finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"
            printf 'FINAL=%s\\n' "$EVIDENCE_FINALIZED"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("FINAL=YES", cp.stdout)
        self.assertEqual(_count_outcome_lines(self.evidence / "BUILD_EXIT_CODE.txt"), 1)

    def test_22_evidence_finalized_only_after_success(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            printf 'BEFORE=%s\\n' "$EVIDENCE_FINALIZED"
            finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"
            printf 'AFTER=%s\\n' "$EVIDENCE_FINALIZED"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("BEFORE=NO", cp.stdout)
        self.assertIn("AFTER=YES", cp.stdout)

    def test_23_finalizer_failure_does_not_claim_completion(self) -> None:
        # Point EVIDENCE at a non-writable / missing path after source.
        body = textwrap.dedent(
            """\
            EVIDENCE={path}/missing-evidence-dir
            set +e
            finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            printf 'FINAL=%s\\n' "$EVIDENCE_FINALIZED"
            exit 0
            """.format(path=shlex.quote(self.ws_rel))
        )
        # Bypass _run_sourced's EVIDENCE override by inlining carefully:
        script = textwrap.dedent(
            f"""\
            set -euo pipefail
            source ./{CONTAINER_SCRIPT_NAME}
            EVIDENCE_FINALIZED=NO
            FINALIZING_IN_PROGRESS=NO
            CONTAINER_MAIN_ACTIVE=NO
            CARGO_STARTED=NO
            EVIDENCE={shlex.quote(self.ws_rel)}/missing-evidence-dir
            set +e
            finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            printf 'FINAL=%s\\n' "$EVIDENCE_FINALIZED"
            """
        )
        cp = _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("FINAL=NO", cp.stdout)

    # ------------------------------------------------------------------
    # 24–27 no host/validator/prohibited side effects
    # ------------------------------------------------------------------
    def test_24_no_post_build_integrity_written(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertFalse((self.evidence / "POST_BUILD_INTEGRITY.txt").exists())

    def test_25_no_docker_exit_code_written(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=2
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:01Z
            CARGO_ELAPSED_SECONDS=1
            finalize_container_terminal_outcome "CARGO_FAILED" 2 "cargo_build"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertFalse((self.evidence / "DOCKER_EXIT_CODE.txt").exists())

    def test_26_no_validator_invocation(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("validate_witness_evidence", text)
        self._assert_no_prohibited_invocations()
        # Ensure this test module does not import the validator as a module.
        import_stmt = "import " + "validate_witness_evidence"
        from_stmt = "from " + "validate_witness_evidence"
        self_text = Path(__file__).read_text(encoding="utf-8")
        self.assertNotIn(import_stmt, self_text)
        self.assertNotIn(from_stmt, self_text)

    def test_27_no_prohibited_external_command_invocation(self) -> None:
        self._init_evidence()
        body = textwrap.dedent(
            """\
            CARGO_STARTED=YES
            CARGO_EXIT_CODE=0
            CARGO_START_UTC=2026-01-01T00:00:00Z
            CARGO_END_UTC=2026-01-01T00:00:01Z
            CARGO_ELAPSED_SECONDS=1
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_MISSING" 42 \
              "artifact_presence_check"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self._assert_no_prohibited_invocations()

    # ------------------------------------------------------------------
    # 28 cleanup
    # ------------------------------------------------------------------
    def test_28_repository_local_temporary_cleanup(self) -> None:
        self.assertTrue(str(self.workspace).startswith(str(TESTS_DIR)))
        self.assertTrue(self.workspace.name.startswith(TEMP_PREFIX))
        # tearDown / tearDownClass enforce removal; this test documents the contract.
        self.assertEqual(self.workspace.parent, TESTS_DIR)

    # ------------------------------------------------------------------
    # 29–34 routing through centralized finalizer
    # ------------------------------------------------------------------
    def test_29_fail_build_not_started_routes_through_finalizer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        fn = re.search(
            r"fail_build_not_started\(\)\s*\{(.*?)\n\}",
            text,
            flags=re.S,
        )
        self.assertIsNotNone(fn)
        body = fn.group(1)
        self.assertIn("finalize_container_terminal_outcome", body)
        self.assertIn("BUILD_NOT_STARTED", body)
        # Behavioral: call fail_build_not_started in a subshell after init.
        self._init_evidence()
        script = textwrap.dedent(
            f"""\
            set -euo pipefail
            source ./{CONTAINER_SCRIPT_NAME}
            EVIDENCE={shlex.quote(self.evidence_rel)}
            ARTIFACT={shlex.quote(self.ws_rel + "/no-such-artifact")}
            EVIDENCE_FINALIZED=NO
            FINALIZING_IN_PROGRESS=NO
            CONTAINER_MAIN_ACTIVE=NO
            CARGO_STARTED=NO
            CT_STATUS=pending
            CT_OUTCOME=NOT_REACHED
            CT_TARGET_PATH_HOST=NOT_REACHED
            CT_PROOF_UTC_HOST=NOT_REACHED
            CT_OBS_HOST=NOT_REACHED
            CT_TARGET_PREBOOT=NOT_REACHED
            CT_UTC_PREBOOT=NOT_REACHED
            CT_OBS_PREBOOT=NOT_REACHED
            CT_TARGET_PRECARGO=NOT_REACHED
            CT_UTC_PRECARGO=NOT_REACHED
            CT_OBS_CONTAINER=NOT_REACHED
            CT_PROOF_FAILED=no
            CT_FAILURE_STAGE=NOT_REACHED
            CT_LISTINGS=
            init_evidence
            set +e
            ( fail_build_not_started "routed_stage" 19 )
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            printf 'OUTCOME=%s\\n' "$(read_kv "$EVIDENCE/BUILD_EXIT_CODE.txt" outcome)"
            printf 'FINAL=%s\\n' "$(read_kv "$EVIDENCE/BUILD_EXIT_CODE.txt" status)"
            """
        )
        # Re-init in script; clear prior init files by removing evidence contents first.
        for child in self.evidence.iterdir():
            if child.is_file():
                child.unlink()
        cp = _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=19", cp.stdout)
        self.assertIn("OUTCOME=BUILD_NOT_STARTED", cp.stdout)

    def test_30_fail_infrastructure_routes_through_finalizer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        fn = re.search(r"fail_infrastructure\(\)\s*\{(.*?)\n\}", text, flags=re.S)
        self.assertIsNotNone(fn)
        self.assertIn("finalize_container_terminal_outcome", fn.group(1))
        self.assertIn("INFRASTRUCTURE_FAILURE", fn.group(1))
        for child in self.evidence.iterdir():
            if child.is_file():
                child.unlink()
        script = textwrap.dedent(
            f"""\
            set -euo pipefail
            source ./{CONTAINER_SCRIPT_NAME}
            EVIDENCE={shlex.quote(self.evidence_rel)}
            ARTIFACT={shlex.quote(self.ws_rel + "/no-such-artifact")}
            EVIDENCE_FINALIZED=NO
            FINALIZING_IN_PROGRESS=NO
            CONTAINER_MAIN_ACTIVE=NO
            CARGO_STARTED=NO
            CT_STATUS=pending
            CT_OUTCOME=NOT_REACHED
            CT_TARGET_PATH_HOST=NOT_REACHED
            CT_PROOF_UTC_HOST=NOT_REACHED
            CT_OBS_HOST=NOT_REACHED
            CT_TARGET_PREBOOT=NOT_REACHED
            CT_UTC_PREBOOT=NOT_REACHED
            CT_OBS_PREBOOT=NOT_REACHED
            CT_TARGET_PRECARGO=NOT_REACHED
            CT_UTC_PRECARGO=NOT_REACHED
            CT_OBS_CONTAINER=NOT_REACHED
            CT_PROOF_FAILED=no
            CT_FAILURE_STAGE=NOT_REACHED
            CT_LISTINGS=
            init_evidence
            set +e
            ( fail_infrastructure "infra_stage" 21 )
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            printf 'OUTCOME=%s\\n' "$(read_kv "$EVIDENCE/BUILD_EXIT_CODE.txt" outcome)"
            """
        )
        cp = _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=21", cp.stdout)
        self.assertIn("OUTCOME=INFRASTRUCTURE_FAILURE", cp.stdout)

    def test_31_cargo_nonzero_route_uses_finalizer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r'finalize_container_terminal_outcome\s+"CARGO_FAILED"',
        )

    def test_32_artifact_missing_route_uses_finalizer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r'finalize_container_terminal_outcome\s+"CARGO_SUCCEEDED_ARTIFACT_MISSING"',
        )

    def test_33_artifact_present_success_route_uses_finalizer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r'finalize_container_terminal_outcome\s+"CARGO_SUCCEEDED_ARTIFACT_PRESENT"[\s\S]*"\$\{EXIT_STATUS\}"',
        )
        self.assertIn('EXIT_STATUS="OK"', text)

    def test_34_artifact_present_static_failure_route_uses_finalizer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("STATIC_INSPECTION_INCOMPLETE_EXIT", text)
        self.assertIn('EXIT_STATUS="FAILED"', text)
        self.assertRegex(
            text,
            r'finalize_container_terminal_outcome\s+"CARGO_SUCCEEDED_ARTIFACT_PRESENT"',
        )

    # ------------------------------------------------------------------
    # 35–36 no final provisional / NOT_REACHED where alternatives exist
    # ------------------------------------------------------------------
    def test_35_no_final_pending_values_in_container_owned_mandatory(self) -> None:
        self._init_evidence()
        outcomes = [
            ('"BUILD_NOT_STARTED" 1 "stage_a"', None),
            (
                '"CARGO_FAILED" 4 "cargo_build"',
                "CARGO_STARTED=YES; CARGO_EXIT_CODE=4; CARGO_START_UTC=2026-01-01T00:00:00Z; "
                "CARGO_END_UTC=2026-01-01T00:00:01Z; CARGO_ELAPSED_SECONDS=1",
            ),
            (
                '"CARGO_SUCCEEDED_ARTIFACT_MISSING" 42 "artifact_presence_check"',
                "CARGO_STARTED=YES; CARGO_EXIT_CODE=0; CARGO_START_UTC=2026-01-01T00:00:00Z; "
                "CARGO_END_UTC=2026-01-01T00:00:01Z; CARGO_ELAPSED_SECONDS=1",
            ),
        ]
        for args, preamble in outcomes:
            with self.subTest(args=args):
                for child in list(self.evidence.iterdir()):
                    if child.is_file():
                        child.unlink()
                prep = preamble + "; " if preamble else ""
                body = f"init_evidence; {prep}finalize_container_terminal_outcome {args}"
                cp = self._run_sourced(body)
                self.assertEqual(cp.returncode, 0, cp.stderr)
                self._assert_no_provisional_in_container_owned()

    def test_36_no_final_not_reached_where_terminal_alternatives_exist(self) -> None:
        self._init_evidence()
        cp = self._run_sourced(
            'finalize_container_terminal_outcome "BUILD_NOT_STARTED" 1 "stage_a"'
        )
        self.assertEqual(cp.returncode, 0, cp.stderr)
        for name in ("BUILD_EXIT_CODE.txt", "BUILD_TIMING.txt"):
            text = (self.evidence / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?m)^status=NOT_REACHED$")
            self.assertNotRegex(text, r"(?m)^outcome=NOT_REACHED$")
            self.assertNotRegex(text, r"(?m)^failure_stage=NOT_REACHED$")
            self.assertNotRegex(text, r"(?m)^cargo_exit_code=NOT_REACHED$")
        # BUILD_COMMAND has FAILED alternative and must not keep NOT_REACHED status.
        self.assertNotEqual(_read_kv(self.evidence / "BUILD_COMMAND.txt", "status"), "NOT_REACHED")
        # CLEAN_TARGET pending must be gone.
        self.assertNotEqual(_read_kv(self.evidence / "CLEAN_TARGET_PROOF.txt", "status"), "pending")
        self.assertNotEqual(_read_kv(self.evidence / "CLEAN_TARGET_PROOF.txt", "status"), "NOT_REACHED")
        self._assert_no_host_owned_writes()
        self._assert_no_prohibited_invocations()


if __name__ == "__main__":
    unittest.main()
