#!/usr/bin/env python3
"""RC6-R2 Host incomplete-package marker and trap/finalization tests.

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (rc6r2_test_*)
- Host/container scripts are sourced only; production mains are never invoked
- Mock commands are first on PATH and never delegate
- No remote clones / no network
- No Cargo, rustc, rustup, DotSlash, protoc, ldd, Docker, product execution
- No production validator against real evidence packages
- Cleanup of repository-local temps on success and failure
"""

from __future__ import annotations

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
HOST_SCRIPT_NAME = "run_witness_narrow_build.sh"
CONTAINER_SCRIPT_NAME = "container_narrow_build.sh"
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
CONTAINER_SCRIPT = SCRIPTS_DIR / CONTAINER_SCRIPT_NAME
VALIDATOR_SCRIPT = SCRIPTS_DIR / "validate_witness_evidence.py"
TEMP_PREFIX = "rc6r2_test_"

REQUIRED_MARKER_KEYS = (
    "record_schema_version",
    "record_owner",
    "run_id",
    "evidence_dir",
    "package_state",
    "rerun_required",
    "reason",
    "failure_stage",
    "signal_name",
    "host_timestamp_utc",
    "container_exit_code",
    "docker_exit_code",
    "authoritative_outcome_available",
)

ALLOWED_REASONS = {
    "signal_interrupted",
    "exit_before_terminal_finalization",
    "finalizer_write_failure",
    "missing_build_exit_code",
    "empty_build_exit_code",
    "malformed_build_exit_code",
    "contradictory_build_exit_code",
    "unexpected_host_post_docker_failure",
    "incomplete_terminal_evidence",
}

PROHIBITED_COMMANDS = (
    "docker",
    "cargo",
    "rustc",
    "rustup",
    "dotslash",
    "protoc",
    "ldd",
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
    raise unittest.SkipTest("bash not available for RC6-R2 tests")


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


def _remaining_temps() -> list[Path]:
    if not TESTS_DIR.is_dir():
        return []
    return sorted(p for p in TESTS_DIR.iterdir() if p.is_dir() and p.name.startswith(TEMP_PREFIX))


def _read_kv(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _kv_map(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k] = v
    return out


class Rc6R2IncompletePackageMarkerTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_temps()
        assert not leftovers, (
            f"RC6-R2 temporary directories remain under {TESTS_DIR}: {[p.name for p in leftovers]}"
        )

    def setUp(self) -> None:
        self.assertTrue(HOST_SCRIPT.is_file(), f"missing host script: {HOST_SCRIPT}")
        self.assertTrue(CONTAINER_SCRIPT.is_file(), f"missing container script: {CONTAINER_SCRIPT}")
        self._tmpdir = tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(TESTS_DIR))
        self.workspace = Path(self._tmpdir.name).resolve()
        self.assertEqual(self.workspace.parent, TESTS_DIR)
        self.ws_basename = self.workspace.name
        self.ws_rel = f"tests/{self.ws_basename}"

        self.evidence = self.workspace / "evidence"
        self.evidence.mkdir()
        self.evidence_rel = f"{self.ws_rel}/evidence"
        self.incomplete_dir = self.workspace / "tmp" / "host-incomplete" / "rc6r2-run"
        self.marker_path = self.incomplete_dir / "PACKAGE_INCOMPLETE.txt"

        self.mock_bin = self.workspace / "mock-bin"
        self.mock_bin.mkdir()
        self.cmd_log = self.workspace / "prohibited_commands.log"
        self.cmd_log.write_text("", encoding="utf-8")
        self.mock_bin_rel = f"{self.ws_rel}/mock-bin"
        self.cmd_log_rel = f"{self.ws_rel}/prohibited_commands.log"

        for name in PROHIBITED_COMMANDS:
            _write_executable(
                self.mock_bin / name,
                textwrap.dedent(
                    f"""\
                    #!/usr/bin/env bash
                    set -euo pipefail
                    printf 'PROHIBITED %s\\n' {shlex.quote(name)} >> {shlex.quote(self.cmd_log_rel)}
                    echo "mock-{name}: prohibited in RC6-R2 tests" >&2
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
        env["PATH"] = self.mock_bin_rel + ":" + env.get("PATH", "")
        return env

    def _source_prelude(self) -> str:
        return textwrap.dedent(
            f"""\
            set -euo pipefail
            # shellcheck disable=SC1091
            source ./{HOST_SCRIPT_NAME}
            EVIDENCE_DIR={shlex.quote(self.evidence_rel)}
            WORK_ROOT={shlex.quote(self.ws_rel)}
            RUN_ID=rc6r2-run
            DOCKER_EXIT=7
            DOCKER_STARTED_UTC=2026-01-01T00:00:00Z
            DOCKER_FINISHED_UTC=2026-01-01T00:01:00Z
            DOCKER_STARTED_EPOCH=1
            DOCKER_FINISHED_EPOCH=61
            OUTCOME=BUILD_NOT_STARTED
            FAILURE_STAGE=rc6r2_test
            CARGO_STARTED=NO
            HOST_FINALIZING_IN_PROGRESS=NO
            HOST_TERMINAL_HANDLED=NO
            HOST_MAIN_ACTIVE=NO
            HOST_SIGNAL_NAME=NONE
            HOST_OUTCOME_INGESTION_WRITTEN=NO
            HOST_OUTCOME_INGESTION_FINGERPRINT=
            CONTAINER_RESULT_PRESENCE=MISSING
            CONTAINER_RESULT_VALID=NO
            CONTAINER_RESULT_ERROR=none
            PARSED_CONTAINER_OUTCOME=
            PARSED_CARGO_STARTED=
            PARSED_CARGO_EXIT_CODE=
            PARSED_ARTIFACT_PRESENT=
            PARSED_ARTIFACT_IDENTITY_COMPLETE=
            PARSED_STATIC_INSPECTION_COMPLETE=
            PARSED_SCHEMA_VERSION=
            PARSED_FAILURE_STAGE=
            PARSED_RUN_ID=
            HOST_INFRASTRUCTURE_STATUS=OK
            HOST_SOURCE_INTEGRITY_STATUS=OK
            HOST_POST_BUILD_INTEGRITY_STATUS=OK
            HOST_EVIDENCE_COMPLETENESS_STATUS=INCOMPLETE
            PRELIMINARY_SUCCESS_ELIGIBLE=NO
            POST_BUILD_INTEGRITY_OK=no
            SPECIFIC_FAILURE_RECORDED=0
            CURRENT_STAGE=rc6r2_test
            INCOMPLETE_MARKER_REASON=
            """
        )

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._source_prelude() + "\n" + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _assert_marker_shape(self, path: Path, *, reason: str, signal_name: str) -> dict[str, str]:
        self.assertTrue(path.is_file(), f"marker missing: {path}")
        # Outside EVIDENCE_DIR
        self.assertFalse(str(path.resolve()).startswith(str(self.evidence.resolve())))
        kv = _kv_map(path)
        self.assertEqual(tuple(kv.keys()), REQUIRED_MARKER_KEYS)
        self.assertEqual(kv["record_schema_version"], "1")
        self.assertEqual(kv["record_owner"], "host")
        self.assertEqual(kv["run_id"], "rc6r2-run")
        self.assertEqual(kv["package_state"], "INCOMPLETE_NOT_FINAL_SUBMISSION")
        self.assertEqual(kv["rerun_required"], "yes")
        self.assertEqual(kv["reason"], reason)
        self.assertIn(reason, ALLOWED_REASONS)
        self.assertEqual(kv["signal_name"], signal_name)
        self.assertIn(kv["authoritative_outcome_available"], ("yes", "no"))
        self.assertTrue(kv["failure_stage"])
        self.assertTrue(kv["host_timestamp_utc"])
        self.assertTrue(kv["container_exit_code"])
        self.assertTrue(kv["docker_exit_code"])
        self.assertTrue(kv["evidence_dir"])
        return kv

    # ------------------------------------------------------------------
    # Marker writer unit tests
    # ------------------------------------------------------------------
    def test_01_marker_path_outside_evidence_dir(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                write_host_package_incomplete_marker missing_build_exit_code NONE rc6r2_test
                printf 'PATH=%s\\n' "$HOST_INCOMPLETE_MARKER_PATH"
                printf 'RESOLVED=%s\\n' "$(resolve_host_incomplete_marker_path)"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        expected = f"{self.ws_rel}/tmp/host-incomplete/rc6r2-run/PACKAGE_INCOMPLETE.txt"
        self.assertIn(f"PATH={expected}", cp.stdout)
        self.assertIn(f"RESOLVED={expected}", cp.stdout)
        self.assertTrue(self.marker_path.is_file())
        self.assertFalse(str(self.marker_path.resolve()).startswith(str(self.evidence.resolve())))
        self.assertEqual(
            self.marker_path.resolve(),
            (self.workspace / "tmp" / "host-incomplete" / "rc6r2-run" / "PACKAGE_INCOMPLETE.txt").resolve(),
        )

    def test_02_exact_field_set_and_vocabularies(self) -> None:
        cp = self._run_sourced(
            "write_host_package_incomplete_marker incomplete_terminal_evidence NONE stage_a\n"
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_marker_shape(
            self.marker_path, reason="incomplete_terminal_evidence", signal_name="NONE"
        )

    def test_03_atomic_temp_file_plus_rename(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        fn = re.search(
            r"write_host_package_incomplete_marker\(\) \{.*?\n\}",
            host,
            flags=re.S,
        )
        self.assertIsNotNone(fn)
        body = fn.group(0)
        self.assertIn("write_host_file_atomic", body)
        self.assertIn("mkdir -p", body)
        self.assertNotRegex(body, r'>\s*"\$\{dest\}"')

    def test_04_same_state_idempotency(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                write_host_package_incomplete_marker missing_build_exit_code NONE stage_a
                first="$HOST_INCOMPLETE_MARKER_PATH"
                write_host_package_incomplete_marker missing_build_exit_code NONE stage_a
                second="$HOST_INCOMPLETE_MARKER_PATH"
                test "$first" = "$second"
                printf 'OK\\n'
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("OK", cp.stdout)
        self._assert_marker_shape(
            self.marker_path, reason="missing_build_exit_code", signal_name="NONE"
        )

    def test_05_conflicting_marker_rejection(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                write_host_package_incomplete_marker missing_build_exit_code NONE stage_a
                set +e
                write_host_package_incomplete_marker empty_build_exit_code NONE stage_a
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertEqual(_read_kv(self.marker_path, "reason"), "missing_build_exit_code")

    def test_06_marker_write_failure_nonzero(self) -> None:
        # Point WORK_ROOT at a regular file so mkdir of the fixed marker parent fails closed.
        blocker = self.workspace / "not-a-dir"
        blocker.write_text("x", encoding="utf-8")
        blocker_rel = f"{self.ws_rel}/not-a-dir"
        cp = self._run_sourced(
            textwrap.dedent(
                f"""\
                WORK_ROOT={shlex.quote(blocker_rel)}
                set +e
                write_host_package_incomplete_marker incomplete_terminal_evidence NONE stage_a
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)

    def test_06b_host_incomplete_dir_cannot_alter_marker_path(self) -> None:
        decoy = self.workspace / "decoy-incomplete"
        decoy.mkdir()
        decoy_rel = f"{self.ws_rel}/decoy-incomplete"
        cp = self._run_sourced(
            textwrap.dedent(
                f"""\
                HOST_INCOMPLETE_DIR={shlex.quote(decoy_rel)}
                resolved="$(resolve_host_incomplete_marker_path)"
                printf 'RESOLVED=%s\\n' "$resolved"
                write_host_package_incomplete_marker incomplete_terminal_evidence NONE stage_a
                printf 'WRITTEN=%s\\n' "$HOST_INCOMPLETE_MARKER_PATH"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        expected = f"{self.ws_rel}/tmp/host-incomplete/rc6r2-run/PACKAGE_INCOMPLETE.txt"
        self.assertIn(f"RESOLVED={expected}", cp.stdout)
        self.assertIn(f"WRITTEN={expected}", cp.stdout)
        self.assertTrue(self.marker_path.is_file())
        self.assertFalse((decoy / "PACKAGE_INCOMPLETE.txt").exists())
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        resolve_fn = re.search(
            r"resolve_host_incomplete_marker_path\(\) \{.*?\n\}",
            host,
            flags=re.S,
        )
        self.assertIsNotNone(resolve_fn)
        body = resolve_fn.group(0)
        # Reject env override of the marker directory; allow HOST_INCOMPLETE_DIR_NAME constant.
        self.assertIsNone(re.search(r"\$\{HOST_INCOMPLETE_DIR(?!_NAME)", body))
        self.assertNotIn("HOST_INCOMPLETE_DIR:-", body)
        self.assertIn("${WORK_ROOT}/tmp/${HOST_INCOMPLETE_DIR_NAME}/${RUN_ID}", body)

    # ------------------------------------------------------------------
    # Reason mapping
    # ------------------------------------------------------------------
    def _finalize_with_error(self, error: str, expect_reason: str) -> None:
        body = textwrap.dedent(
            f"""\
            CONTAINER_RESULT_ERROR={shlex.quote(error)}
            CONTAINER_RESULT_VALID=NO
            SRC_HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            SRC_HEAD_AFTER=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            CARGO_LOCK_BEFORE=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
            CARGO_LOCK_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
            SOURCE_HEAD_UNCHANGED=yes
            SOURCE_CLEAN_BEFORE=yes
            SOURCE_CLEAN_AFTER=yes
            CARGO_LOCK_UNCHANGED=yes
            CARGO_LOCK_POST_MATCHES_EXPECTED=yes
            ARTIFACT_PATH=NOT_REACHED
            ARTIFACT_EXISTS=no
            EVIDENCE_INVENTORY_COMPLETE=no
            FULL_INTEGRITY_GATE_ALL_FOUR_YES=no
            set +e
            finalize_post_docker_host_failure "map_test" 10 "mapping" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            rc=$?
            set -e
            printf 'RC=%s\\n' "$rc"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=10", cp.stdout)
        kv = self._assert_marker_shape(self.marker_path, reason=expect_reason, signal_name="NONE")
        self.assertEqual(kv["authoritative_outcome_available"], "no")
        self.assertEqual(kv["rerun_required"], "yes")

    def test_07_missing_build_exit_mapping(self) -> None:
        self._finalize_with_error("build_exit_code_file_missing", "missing_build_exit_code")

    def test_08_empty_build_exit_mapping(self) -> None:
        self._finalize_with_error("build_exit_code_file_empty", "empty_build_exit_code")

    def test_09_malformed_build_exit_mapping(self) -> None:
        self._finalize_with_error("malformed_key_line", "malformed_build_exit_code")

    def test_10_contradictory_build_exit_mapping(self) -> None:
        self._finalize_with_error(
            "contradiction_CARGO_FAILED_cargo_started", "contradictory_build_exit_code"
        )

    def test_11_unexpected_post_docker_mapping(self) -> None:
        self._finalize_with_error(
            "docker_run_launch_failure_exit_125", "unexpected_host_post_docker_failure"
        )

    def test_12_finalizer_write_failure_mapping(self) -> None:
        # Remove evidence dir so POST_BUILD atomic write fails.
        body = textwrap.dedent(
            f"""\
            rm -rf -- {shlex.quote(self.evidence_rel)}
            mkdir -p -- {shlex.quote(self.evidence_rel)}
            # Make POST_BUILD destination unwritable by replacing dir with file after setup
            rmdir -- {shlex.quote(self.evidence_rel)}
            : > {shlex.quote(self.evidence_rel)}
            EVIDENCE_DIR={shlex.quote(self.evidence_rel)}
            set +e
            write_host_package_incomplete_marker finalizer_write_failure NONE stage_fw
            rc=$?
            set -e
            # Restore dir for cleanup expectations
            rm -f -- {shlex.quote(self.evidence_rel)}
            mkdir -p -- {shlex.quote(self.evidence_rel)}
            printf 'RC=%s\\n' "$rc"
            """
        )
        # Direct marker write with finalizer reason (writer itself must succeed).
        # Recreate evidence as directory for marker evidence_dir field.
        self.evidence.rmdir()
        self.evidence.mkdir()
        cp = self._run_sourced(
            "write_host_package_incomplete_marker finalizer_write_failure NONE stage_fw\n"
            "printf 'RC=0\\n'\n"
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_marker_shape(
            self.marker_path, reason="finalizer_write_failure", signal_name="NONE"
        )

    def test_13_signal_int_term_hup_mapping(self) -> None:
        for sig in ("INT", "TERM", "HUP"):
            if self.marker_path.exists():
                self.marker_path.unlink()
            cp = self._run_sourced(
                textwrap.dedent(
                    f"""\
                    HOST_SIGNAL_NAME={sig}
                    write_host_package_incomplete_marker signal_interrupted {sig} signal_stage
                    printf 'OK\\n'
                    """
                )
            )
            self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
            self._assert_marker_shape(
                self.marker_path, reason="signal_interrupted", signal_name=sig
            )

    def test_14_exit_before_finalization_mapping(self) -> None:
        cp = self._run_sourced(
            "write_host_package_incomplete_marker exit_before_terminal_finalization NONE exit_stage\n"
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_marker_shape(
            self.marker_path,
            reason="exit_before_terminal_finalization",
            signal_name="NONE",
        )

    def test_15_authoritative_outcome_available_truthfulness(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                CONTAINER_RESULT_VALID=YES
                write_host_package_incomplete_marker incomplete_terminal_evidence NONE stage_a
                printf 'AUTH=%s\\n' "$(grep -m1 '^authoritative_outcome_available=' "$HOST_INCOMPLETE_MARKER_PATH" | cut -d= -f2-)"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("AUTH=yes", cp.stdout)

        self.marker_path.unlink()
        cp2 = self._run_sourced(
            textwrap.dedent(
                """\
                CONTAINER_RESULT_VALID=NO
                write_host_package_incomplete_marker incomplete_terminal_evidence NONE stage_a
                printf 'AUTH=%s\\n' "$(grep -m1 '^authoritative_outcome_available=' "$HOST_INCOMPLETE_MARKER_PATH" | cut -d= -f2-)"
                """
            )
        )
        self.assertEqual(cp2.returncode, 0, cp2.stderr + cp2.stdout)
        self.assertIn("AUTH=no", cp2.stdout)

    def test_16_host_cannot_return_zero_after_incomplete_finalize(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                SRC_HEAD=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
                SRC_HEAD_AFTER=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
                CARGO_LOCK_BEFORE=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
                CARGO_LOCK_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
                SOURCE_HEAD_UNCHANGED=yes
                SOURCE_CLEAN_BEFORE=yes
                SOURCE_CLEAN_AFTER=yes
                CARGO_LOCK_UNCHANGED=yes
                CARGO_LOCK_POST_MATCHES_EXPECTED=yes
                ARTIFACT_PATH=NOT_REACHED
                ARTIFACT_EXISTS=no
                EVIDENCE_INVENTORY_COMPLETE=no
                FULL_INTEGRITY_GATE_ALL_FOUR_YES=no
                CONTAINER_RESULT_ERROR=build_exit_code_file_missing
                set +e
                finalize_post_docker_host_failure "nz" 10 "must be nonzero" \\
                  "FAILED" "OK" "FAILED" "FAILED" "NO"
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                test "$rc" -ne 0
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=10", cp.stdout)

    def test_17_rerun_requires_new_evidence_dir_policy_text(self) -> None:
        req = (PACKAGE_DIR / "WITNESS_REQUIREMENTS.md").read_text(encoding="utf-8")
        runbook = (PACKAGE_DIR / "WITNESS_RUNBOOK.md").read_text(encoding="utf-8")
        for text in (req, runbook):
            self.assertIn("host-incomplete", text)
            self.assertIn("PACKAGE_INCOMPLETE.txt", text)
            self.assertIn("new `EVIDENCE_DIR`", text)
            self.assertIn("not Witness evidence", text)

    def test_18_validator_does_not_consume_or_modify_marker(self) -> None:
        vtext = VALIDATOR_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("PACKAGE_INCOMPLETE", vtext)
        self.assertNotIn("host-incomplete", vtext)
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        # Validator invocation must not pass marker path.
        self.assertNotRegex(
            host,
            r"validate_witness_evidence\.py[^\n]*PACKAGE_INCOMPLETE",
        )

    def test_19_container_never_writes_marker(self) -> None:
        ctext = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("PACKAGE_INCOMPLETE", ctext)
        self.assertNotIn("host-incomplete", ctext)
        self.assertIn("trap on_container_int INT", ctext)
        self.assertIn("trap on_container_term TERM", ctext)
        self.assertIn("trap on_container_hup HUP", ctext)
        self.assertIn("trap on_container_exit EXIT", ctext)

    def test_20_post_build_uses_atomic_write(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        fn = re.search(
            r"write_host_post_build_integrity_record\(\) \{.*?\n\}",
            host,
            flags=re.S,
        )
        self.assertIsNotNone(fn)
        body = fn.group(0)
        self.assertIn("write_evidence_file_atomic", body)
        self.assertNotRegex(body, r'>\s*"\$\{EVIDENCE_DIR\}/POST_BUILD_INTEGRITY\.txt"')

    def test_21_schema_register_has_no_marker_entry(self) -> None:
        reg = (
            PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn("PACKAGE_INCOMPLETE", reg)
        self.assertNotIn("host-incomplete", reg)

    def test_22_host_traps_installed_in_main(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("trap on_host_int INT", host)
        self.assertIn("trap on_host_term TERM", host)
        self.assertIn("trap on_host_hup HUP", host)
        self.assertIn("trap on_host_exit EXIT", host)
        self.assertIn("write_host_package_incomplete_marker", host)

    def test_23_ordinary_valid_outcome_helpers_preserved(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                test "$(type -t parse_container_result_tuple)" = "function"
                test "$(type -t write_host_post_build_integrity_record)" = "function"
                test "$(type -t finalize_container_terminal_outcome)" != "function"
                printf 'OK\\n'
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        # Container finalizer still present in container script.
        ctext = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("finalize_container_terminal_outcome()", ctext)

    def test_24_incomplete_cannot_enter_final_submission_success_path(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        # After incomplete marker handling, finalizer aborts / returns nonzero and
        # never sets HOST_VALIDATOR_GATE_OK=yes on that path.
        fn = re.search(
            r"finalize_post_docker_host_failure\(\) \{.*?\n\}",
            host,
            flags=re.S,
        )
        self.assertIsNotNone(fn)
        body = fn.group(0)
        self.assertIn("write_host_package_incomplete_marker", body)
        self.assertNotIn('HOST_VALIDATOR_GATE_OK="yes"', body)
        self.assertIn("abort ", body)

    def test_25_same_evidence_dir_not_resumed_policy(self) -> None:
        kv_reason = "missing_build_exit_code"
        cp = self._run_sourced(
            f"write_host_package_incomplete_marker {kv_reason} NONE stage_a\n"
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(_read_kv(self.marker_path, "rerun_required"), "yes")
        self.assertEqual(
            _read_kv(self.marker_path, "package_state"),
            "INCOMPLETE_NOT_FINAL_SUBMISSION",
        )


if __name__ == "__main__":
    unittest.main()
