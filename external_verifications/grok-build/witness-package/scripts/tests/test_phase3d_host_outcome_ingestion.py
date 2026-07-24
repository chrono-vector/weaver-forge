#!/usr/bin/env python3
"""Phase 3D host outcome ingestion and no-overwrite tests.

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (phase3d_test_*)
- Host script is sourced only; run_witness_narrow_build_main is never invoked
- Mock commands are first on PATH and never delegate
- No remote clones / no network
- No Cargo, rustc, rustup, DotSlash, protoc, ldd, Docker, validator, or product execution
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
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
TEMP_PREFIX = "phase3d_test_"

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
    raise unittest.SkipTest("bash not available for Phase 3D host ingestion tests")


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


def _remaining_phase3d_temps() -> list[Path]:
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


class Phase3DHostOutcomeIngestionTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_phase3d_temps()
        assert not leftovers, (
            f"Phase 3D temporary directories remain under {TESTS_DIR}: "
            f"{[p.name for p in leftovers]}"
        )

    def setUp(self) -> None:
        self.assertTrue(HOST_SCRIPT.is_file(), f"missing host script: {HOST_SCRIPT}")
        self._tmpdir = tempfile.TemporaryDirectory(prefix=TEMP_PREFIX, dir=str(TESTS_DIR))
        self.workspace = Path(self._tmpdir.name).resolve()
        self.assertEqual(self.workspace.parent, TESTS_DIR)
        self.ws_basename = self.workspace.name
        self.ws_rel = f"tests/{self.ws_basename}"

        self.evidence = self.workspace / "evidence"
        self.evidence.mkdir()
        self.evidence_rel = f"{self.ws_rel}/evidence"

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
                    echo "mock-{name}: prohibited in Phase 3D tests" >&2
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
            RUN_ID=phase3d-test-run
            DOCKER_EXIT=0
            DOCKER_STARTED_UTC=2026-01-01T00:00:00Z
            DOCKER_FINISHED_UTC=2026-01-01T00:01:00Z
            DOCKER_STARTED_EPOCH=1
            DOCKER_FINISHED_EPOCH=61
            OUTCOME=BUILD_NOT_STARTED
            FAILURE_STAGE=none
            CARGO_STARTED=NO
            HOST_FINALIZING_IN_PROGRESS=NO
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
            POST_BUILD_INTEGRITY_OK=yes
            SPECIFIC_FAILURE_RECORDED=0
            CURRENT_STAGE=phase3d_test
            """
        )

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._source_prelude() + "\n" + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _write_build_exit(self, lines: list[str]) -> Path:
        path = self.evidence / "BUILD_EXIT_CODE.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return path

    def _write_artifact(
        self,
        *,
        present: str = "NO",
        identity_complete: str | None = None,
        static_complete: str | None = None,
    ) -> None:
        lines = [
            "evidence_schema_version=1",
            f"artifact_present={present}",
            "applicable=yes",
            "product_executed=NO",
            "ldd_used=NO",
        ]
        if identity_complete is not None:
            lines.append(f"artifact_identity_complete={identity_complete}")
        if static_complete is not None:
            lines.append(f"static_inspection_complete={static_complete}")
        (self.evidence / "ARTIFACT_IDENTITY.txt").write_text(
            "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
        )

    def _valid_tuple_lines(
        self,
        outcome: str,
        *,
        cargo_started: str,
        cargo_exit: str,
        artifact_present: str,
        failure_stage: str = "test_stage",
        identity_complete: str | None = None,
        static_complete: str | None = None,
    ) -> list[str]:
        lines = [
            "evidence_schema_version=1",
            "status=FAILED",
            f"outcome={outcome}",
            f"cargo_started={cargo_started}",
            f"build_status={outcome}",
            f"cargo_exit_code={cargo_exit}",
            f"failure_stage={failure_stage}",
            f"artifact_present={artifact_present}",
        ]
        if identity_complete is not None:
            lines.append(f"artifact_identity_complete={identity_complete}")
        if static_complete is not None:
            lines.append(f"static_inspection_complete={static_complete}")
        return lines

    def _assert_no_prohibited(self) -> None:
        text = self.cmd_log.read_text(encoding="utf-8")
        self.assertEqual(text, "", f"prohibited command invoked: {text!r}")

    def _ingestion(self) -> Path:
        return self.evidence / "HOST_OUTCOME_INGESTION.txt"

    # ------------------------------------------------------------------
    # 1. sourcing performs no workflow
    # ------------------------------------------------------------------
    def test_01_sourcing_performs_no_workflow(self) -> None:
        marker = self.workspace / "sourced_ok"
        marker_rel = f"{self.ws_rel}/sourced_ok"
        body = textwrap.dedent(
            f"""\
            test "$(type -t parse_container_result_tuple)" = "function"
            test "$(type -t finalize_post_docker_host_failure)" = "function"
            test "$(type -t write_host_outcome_ingestion_record)" = "function"
            test "$(type -t run_witness_narrow_build_main)" = "function"
            : > {shlex.quote(marker_rel)}
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertTrue(marker.is_file())
        self.assertFalse((self.evidence / "BUILD_EXIT_CODE.txt").exists())
        self._assert_no_prohibited()

    # ------------------------------------------------------------------
    # 2–3. five outcomes + sentinel
    # ------------------------------------------------------------------
    def test_02_exact_five_outcomes_recognized(self) -> None:
        for outcome, started, exit_code, present, ident, static in (
            ("BUILD_NOT_STARTED", "NO", "NOT_APPLICABLE", "NO", None, None),
            ("CARGO_FAILED", "YES", "17", "NO", None, None),
            ("CARGO_SUCCEEDED_ARTIFACT_MISSING", "YES", "0", "NO", None, None),
            ("CARGO_SUCCEEDED_ARTIFACT_PRESENT", "YES", "0", "YES", "YES", "YES"),
            ("INFRASTRUCTURE_FAILURE", "NO", "NOT_APPLICABLE", "NO", None, None),
        ):
            for child in self.evidence.iterdir():
                if child.is_file():
                    child.unlink()
            self._write_build_exit(
                self._valid_tuple_lines(
                    outcome,
                    cargo_started=started,
                    cargo_exit=exit_code,
                    artifact_present=present,
                    identity_complete=ident,
                    static_complete=static,
                    failure_stage="stage_x",
                )
            )
            body = textwrap.dedent(
                """\
                set +e
                parse_container_result_tuple
                ec=$?
                set -e
                printf 'EC=%s VALID=%s OUT=%s\\n' "$ec" "$CONTAINER_RESULT_VALID" "$PARSED_CONTAINER_OUTCOME"
                """
            )
            cp = self._run_sourced(body)
            self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
            self.assertIn(f"EC=0 VALID=YES OUT={outcome}", cp.stdout)

    def test_03_terminal_sentinel_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=NOT_REACHED",
                "cargo_started=NO",
                "cargo_exit_code=NOT_APPLICABLE",
                "artifact_present=NO",
                "failure_stage=none",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s VALID=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_VALID" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 VALID=NO", cp.stdout)
        self.assertIn("terminal_sentinel_rejected", cp.stdout)

    # ------------------------------------------------------------------
    # 4–12. missing/malformed/duplicate/unsupported
    # ------------------------------------------------------------------
    def test_04_missing_build_exit_rejected(self) -> None:
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s PRESENCE=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_PRESENCE" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 PRESENCE=MISSING", cp.stdout)
        self.assertIn("build_exit_code_file_missing", cp.stdout)

    def test_05_empty_build_exit_rejected(self) -> None:
        (self.evidence / "BUILD_EXIT_CODE.txt").write_text("", encoding="utf-8")
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s PRESENCE=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_PRESENCE" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 PRESENCE=EMPTY", cp.stdout)

    def test_06_duplicate_outcome_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=BUILD_NOT_STARTED",
                "outcome=CARGO_FAILED",
                "cargo_started=NO",
                "cargo_exit_code=NOT_APPLICABLE",
                "artifact_present=NO",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertTrue(
            "outcome_field_duplicated" in cp.stdout or "duplicate_tuple_key_outcome" in cp.stdout
        )

    def test_07_unsupported_outcome_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=SUCCESS",
                "cargo_started=YES",
                "cargo_exit_code=0",
                "artifact_present=YES",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("unsupported_outcome", cp.stdout)

    def test_08_malformed_key_line_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "this_is_not_a_kv_line",
                "outcome=BUILD_NOT_STARTED",
                "cargo_started=NO",
                "cargo_exit_code=NOT_APPLICABLE",
                "artifact_present=NO",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 ERR=malformed_key_line", cp.stdout)

    def test_09_duplicate_tuple_key_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=BUILD_NOT_STARTED",
                "cargo_started=NO",
                "cargo_started=YES",
                "cargo_exit_code=NOT_APPLICABLE",
                "artifact_present=NO",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("duplicate_tuple_key", cp.stdout)

    def test_10_missing_cargo_started_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=BUILD_NOT_STARTED",
                "cargo_exit_code=NOT_APPLICABLE",
                "artifact_present=NO",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 ERR=missing_cargo_started", cp.stdout)

    def test_11_missing_cargo_exit_code_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=BUILD_NOT_STARTED",
                "cargo_started=NO",
                "artifact_present=NO",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 ERR=missing_cargo_exit_code", cp.stdout)

    def test_12_missing_artifact_present_rejected(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "outcome=BUILD_NOT_STARTED",
                "cargo_started=NO",
                "cargo_exit_code=NOT_APPLICABLE",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 ERR=missing_artifact_present", cp.stdout)

    # ------------------------------------------------------------------
    # 13–23. valid tuples and contradictions
    # ------------------------------------------------------------------
    def test_13_build_not_started_valid_accepted(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "BUILD_NOT_STARTED",
                cargo_started="NO",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            printf 'VALID=%s OUT=%s\\n' "$CONTAINER_RESULT_VALID" "$PARSED_CONTAINER_OUTCOME"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES OUT=BUILD_NOT_STARTED", cp.stdout)

    def test_14_build_not_started_contradiction_rejected(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "BUILD_NOT_STARTED",
                cargo_started="YES",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("contradiction_BUILD_NOT_STARTED", cp.stdout)

    def test_15_cargo_failed_valid_accepted(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_FAILED",
                cargo_started="YES",
                cargo_exit="7",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            printf 'VALID=%s EXIT=%s\\n' "$CONTAINER_RESULT_VALID" "$PARSED_CARGO_EXIT_CODE"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES EXIT=7", cp.stdout)

    def test_16_cargo_failed_zero_exit_rejected(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_FAILED",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("contradiction_CARGO_FAILED_cargo_exit_code", cp.stdout)

    def test_17_artifact_missing_valid_accepted(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_MISSING",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            printf 'VALID=%s OUT=%s\\n' "$CONTAINER_RESULT_VALID" "$PARSED_CONTAINER_OUTCOME"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES OUT=CARGO_SUCCEEDED_ARTIFACT_MISSING", cp.stdout)

    def test_18_artifact_missing_present_contradiction_rejected(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_MISSING",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("contradiction_ARTIFACT_MISSING_artifact_present", cp.stdout)

    def test_19_artifact_present_valid_accepted(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                identity_complete="YES",
                static_complete="YES",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            printf 'VALID=%s ID=%s ST=%s\\n' "$CONTAINER_RESULT_VALID" "$PARSED_ARTIFACT_IDENTITY_COMPLETE" "$PARSED_STATIC_INSPECTION_COMPLETE"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES ID=YES ST=YES", cp.stdout)

    def test_20_artifact_present_missing_identity_rejected(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                static_complete="YES",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 ERR=missing_artifact_identity_complete", cp.stdout)

    def test_21_artifact_present_missing_static_rejected(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                identity_complete="YES",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 ERR=missing_static_inspection_complete", cp.stdout)

    def test_22_infra_failure_before_cargo_accepted(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "INFRASTRUCTURE_FAILURE",
                cargo_started="NO",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
                failure_stage="bootstrap",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            printf 'VALID=%s CS=%s\\n' "$CONTAINER_RESULT_VALID" "$PARSED_CARGO_STARTED"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES CS=NO", cp.stdout)

    def test_23_infra_failure_after_cargo_accepted(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "INFRASTRUCTURE_FAILURE",
                cargo_started="YES",
                cargo_exit="3",
                artifact_present="NO",
                failure_stage="post_cargo_infra",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            printf 'VALID=%s CS=%s EXIT=%s\\n' "$CONTAINER_RESULT_VALID" "$PARSED_CARGO_STARTED" "$PARSED_CARGO_EXIT_CODE"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES CS=YES EXIT=3", cp.stdout)

    # ------------------------------------------------------------------
    # 24–25. no inference
    # ------------------------------------------------------------------
    def test_24_no_result_inference_from_cargo_facts(self) -> None:
        self._write_build_exit(
            [
                "evidence_schema_version=1",
                "cargo_started=YES",
                "cargo_exit_code=0",
                "artifact_present=YES",
                "failure_stage=x",
            ]
        )
        body = textwrap.dedent(
            """\
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s ERR=%s OUT=%s\\n' "$ec" "$CONTAINER_RESULT_ERROR" "$PARSED_CONTAINER_OUTCOME"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("outcome_field_missing", cp.stdout)
        self.assertNotIn("OUT=CARGO_SUCCEEDED", cp.stdout)

    def test_25_no_result_inference_from_docker_exit(self) -> None:
        body = textwrap.dedent(
            """\
            DOCKER_EXIT=0
            set +e
            parse_container_result_tuple
            ec=$?
            set -e
            printf 'EC=%s OUT=%s\\n' "$ec" "$PARSED_CONTAINER_OUTCOME"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1 OUT=", cp.stdout)

    # ------------------------------------------------------------------
    # 26–29. no-overwrite / no fabrication
    # ------------------------------------------------------------------
    def test_26_valid_outcome_preserved_on_source_head_mismatch(self) -> None:
        original = "\n".join(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                identity_complete="YES",
                static_complete="YES",
            )
        ) + "\n"
        path = self._write_build_exit(original.splitlines())
        before = path.read_bytes()
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("", encoding="utf-8")
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "post_docker_source_integrity" 9 "head mismatch" \\
              "OK" "FAILED" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=9", cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(_read_kv(self._ingestion(), "host_source_integrity_status"), "FAILED")
        self.assertEqual(_read_kv(self._ingestion(), "preliminary_success_eligible"), "NO")
        self.assertEqual(_read_kv(self._ingestion(), "container_outcome"), "CARGO_SUCCEEDED_ARTIFACT_PRESENT")

    def test_27_valid_outcome_preserved_on_dirty_tree(self) -> None:
        original = "\n".join(
            self._valid_tuple_lines(
                "CARGO_FAILED",
                cargo_started="YES",
                cargo_exit="2",
                artifact_present="NO",
            )
        ) + "\n"
        path = self._write_build_exit(original.splitlines())
        before = path.read_bytes()
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("", encoding="utf-8")
        body = textwrap.dedent(
            """\
            enforce_post_docker_source_integrity_boundary "yes" "no"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(_read_kv(self._ingestion(), "host_source_integrity_status"), "FAILED")
        self.assertEqual(_read_kv(path, "outcome"), "CARGO_FAILED")

    def test_28_invalid_container_outcome_not_replaced(self) -> None:
        original = "outcome=SUCCESS\ncargo_started=YES\ncargo_exit_code=0\nartifact_present=YES\n"
        path = self.evidence / "BUILD_EXIT_CODE.txt"
        path.write_text(original, encoding="utf-8", newline="\n")
        before = path.read_bytes()
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "invalid_or_missing_container_outcome" 10 "invalid" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=10", cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(_read_kv(self._ingestion(), "container_result_valid"), "NO")
        self.assertEqual(_read_kv(self._ingestion(), "status"), "FAILED")

    def test_29_missing_container_outcome_not_fabricated(self) -> None:
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "invalid_or_missing_container_outcome" 10 "missing" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            test ! -e "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=10", cp.stdout)
        self.assertFalse((self.evidence / "BUILD_EXIT_CODE.txt").exists())
        self.assertEqual(_read_kv(self._ingestion(), "container_result_presence"), "MISSING")

    # ------------------------------------------------------------------
    # 30–32. atomic writer / writer failure
    # ------------------------------------------------------------------
    def test_30_host_ingestion_record_is_atomic(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("write_evidence_file_atomic", text)
        fn = re.search(r"write_host_outcome_ingestion_record\(\)\s*\{(.*?)\n\}", text, flags=re.S)
        self.assertIsNotNone(fn)
        self.assertIn("write_evidence_file_atomic", fn.group(1))
        self.assertIn(".tmp.", text)
        body = textwrap.dedent(
            """\
            CONTAINER_RESULT_PRESENCE=MISSING
            CONTAINER_RESULT_VALID=NO
            CONTAINER_RESULT_ERROR=build_exit_code_file_missing
            write_host_outcome_ingestion_record "FAILED"
            test -f "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt"
            # no leftover temp files
            ! ls -1 "$EVIDENCE_DIR"/.tmp.* >/dev/null 2>&1
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertTrue(self._ingestion().is_file())

    def test_31_ingestion_writer_failure_returns_nonzero(self) -> None:
        body = textwrap.dedent(
            """\
            EVIDENCE_DIR={ev}/no_such_dir
            set +e
            write_host_outcome_ingestion_record "FAILED"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """.format(ev=shlex.quote(self.evidence_rel))
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)

    def test_32_writer_failure_leaves_container_evidence_unchanged(self) -> None:
        original = "\n".join(
            self._valid_tuple_lines(
                "BUILD_NOT_STARTED",
                cargo_started="NO",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
            )
        ) + "\n"
        path = self._write_build_exit(original.splitlines())
        before = path.read_bytes()
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            EVIDENCE_DIR={ev}/missing_parent/nope
            set +e
            write_host_outcome_ingestion_record "OK"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """.format(ev=shlex.quote(self.evidence_rel))
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertEqual(path.read_bytes(), before)

    # ------------------------------------------------------------------
    # 33–35. finalizer ownership / no validator / no POST_BUILD rewrite
    # ------------------------------------------------------------------
    def test_33_host_finalizer_writes_only_host_owned_files(self) -> None:
        original = "\n".join(
            self._valid_tuple_lines(
                "CARGO_FAILED",
                cargo_started="YES",
                cargo_exit="9",
                artifact_present="NO",
            )
        ) + "\n"
        path = self._write_build_exit(original.splitlines())
        before = path.read_bytes()
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("seed=1\n", encoding="utf-8")
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "unexpected_post_docker" 12 "boom" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            test -f "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt"
            test -f "$EVIDENCE_DIR/DOCKER_EXIT_CODE.txt"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=12", cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self.assertTrue(self._ingestion().is_file())
        self.assertTrue((self.evidence / "DOCKER_EXIT_CODE.txt").is_file())

    def test_34_no_validator_invocation(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        # Phase 3D functions must not invoke validator.
        for sym in (
            "parse_container_result_tuple",
            "finalize_post_docker_host_failure",
            "write_host_outcome_ingestion_record",
        ):
            m = re.search(rf"{sym}\(\)\s*\{{(.*?)\n\}}", text, flags=re.S)
            self.assertIsNotNone(m, sym)
            body = m.group(1)
            self.assertNotIn("validate_witness_evidence", body)
            self.assertNotIn("python", body.lower())
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure "x" 3 "y" "FAILED" "OK" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_no_prohibited()

    def test_35_no_post_build_semantic_rewrite(self) -> None:
        post = self.evidence / "POST_BUILD_INTEGRITY.txt"
        post.write_text(
            "evidence_schema_version=1\nstatus=OK\noutcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\n",
            encoding="utf-8",
            newline="\n",
        )
        before = post.read_bytes()
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                identity_complete="YES",
                static_complete="YES",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "post_docker_source_integrity" 9 "x" \\
              "OK" "FAILED" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(post.read_bytes(), before)

    # ------------------------------------------------------------------
    # 36–39. preliminary eligibility / nonzero
    # ------------------------------------------------------------------
    def test_36_valid_failure_outcome_preliminary_no(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_FAILED",
                cargo_started="YES",
                cargo_exit="1",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            write_host_outcome_ingestion_record "OK"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(_read_kv(self._ingestion(), "status"), "OK")
        self.assertEqual(_read_kv(self._ingestion(), "preliminary_success_eligible"), "NO")

    def test_37_success_capable_still_preliminary_no(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                identity_complete="YES",
                static_complete="YES",
            )
        )
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            write_host_outcome_ingestion_record "OK"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(_read_kv(self._ingestion(), "container_outcome"), "CARGO_SUCCEEDED_ARTIFACT_PRESENT")
        self.assertEqual(_read_kv(self._ingestion(), "preliminary_success_eligible"), "NO")
        self.assertEqual(_read_kv(self._ingestion(), "status"), "OK")

    def test_38_malformed_result_forces_host_nonzero(self) -> None:
        self._write_build_exit(["not a kv", "outcome=BUILD_NOT_STARTED"])
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "invalid_or_missing_container_outcome" 10 "malformed" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=10", cp.stdout)
        self.assertNotEqual(cp.stdout.strip().split("EC=")[-1][:1], "0")

    def test_39_contradictory_tuple_forces_host_nonzero(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_FAILED",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "invalid_or_missing_container_outcome" 10 "contradiction" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s VALID=%s\\n' "$ec" "$CONTAINER_RESULT_VALID"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=10 VALID=NO", cp.stdout)

    # ------------------------------------------------------------------
    # 40–42. infra failure / source field / CRLF
    # ------------------------------------------------------------------
    def test_40_post_docker_infra_failure_preserves_container_result(self) -> None:
        original = "\n".join(
            self._valid_tuple_lines(
                "BUILD_NOT_STARTED",
                cargo_started="NO",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
            )
        ) + "\n"
        path = self._write_build_exit(original.splitlines())
        before = path.read_bytes()
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_unexpected_failure "unexpected_x" 11 "infra"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        # finalize_post_docker_unexpected_failure calls abort by default via finalize → exits.
        # Override by patching: call finalize path with abort NO through unexpected helper?
        # unexpected always abort_after=YES. Capture via subshell.
        body = textwrap.dedent(
            """\
            set +e
            ( finalize_post_docker_unexpected_failure "unexpected_x" 11 "infra" )
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=11", cp.stdout)
        self.assertEqual(path.read_bytes(), before)

    def test_41_post_docker_source_failure_records_separate_host_field(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                cargo_started="YES",
                cargo_exit="0",
                artifact_present="YES",
                identity_complete="YES",
                static_complete="YES",
            )
        )
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("", encoding="utf-8")
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "post_docker_source_integrity" 9 "dirty" \\
              "OK" "FAILED" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(_read_kv(self._ingestion(), "host_source_integrity_status"), "FAILED")
        self.assertEqual(_read_kv(self._ingestion(), "host_infrastructure_status"), "OK")
        self.assertEqual(
            _read_kv(self.evidence / "BUILD_EXIT_CODE.txt", "outcome"),
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        )

    def test_42_no_crlf_injection_in_host_record(self) -> None:
        body = textwrap.dedent(
            """\
            CONTAINER_RESULT_ERROR=$'bad\\rvalue'
            set +e
            write_host_outcome_ingestion_record "FAILED"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertFalse(self._ingestion().exists())

    # ------------------------------------------------------------------
    # 43–48. spaces / idempotent / conflict / residue / trap / routing
    # ------------------------------------------------------------------
    def test_43_paths_containing_spaces_supported(self) -> None:
        spaced = self.workspace / "ev with spaces"
        spaced.mkdir()
        spaced_rel = f"{self.ws_rel}/ev with spaces"
        build = spaced / "BUILD_EXIT_CODE.txt"
        build.write_text(
            "\n".join(
                self._valid_tuple_lines(
                    "BUILD_NOT_STARTED",
                    cargo_started="NO",
                    cargo_exit="NOT_APPLICABLE",
                    artifact_present="NO",
                )
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        body = textwrap.dedent(
            f"""\
            EVIDENCE_DIR={shlex.quote(spaced_rel)}
            parse_container_result_tuple
            write_host_outcome_ingestion_record "OK"
            test -f "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt"
            printf 'VALID=%s\\n' "$CONTAINER_RESULT_VALID"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES", cp.stdout)
        self.assertTrue((spaced / "HOST_OUTCOME_INGESTION.txt").is_file())

    def test_44_same_value_host_finalization_idempotent(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "BUILD_NOT_STARTED",
                cargo_started="NO",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure "stage_a" 9 "msg" "FAILED" "OK" "FAILED" "FAILED" "NO"
            e1=$?
            finalize_post_docker_host_failure "stage_a" 9 "msg" "FAILED" "OK" "FAILED" "FAILED" "NO"
            e2=$?
            set -e
            printf 'E1=%s E2=%s\\n' "$e1" "$e2"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("E1=9 E2=9", cp.stdout)

    def test_45_conflicting_host_finalization_fails_closed(self) -> None:
        self._write_build_exit(
            self._valid_tuple_lines(
                "BUILD_NOT_STARTED",
                cargo_started="NO",
                cargo_exit="NOT_APPLICABLE",
                artifact_present="NO",
            )
        )
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure "stage_a" 9 "msg" "FAILED" "OK" "FAILED" "FAILED" "NO"
            e1=$?
            finalize_post_docker_host_failure "stage_b" 8 "other" "FAILED" "FAILED" "FAILED" "FAILED" "NO"
            e2=$?
            set -e
            printf 'E1=%s E2=%s\\n' "$e1" "$e2"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("E1=9", cp.stdout)
        # Second call fails closed (nonzero writer conflict → returns exit_code from finalize,
        # or 1 from writer). Either way must be nonzero and not succeed silently.
        m = re.search(r"E2=(\d+)", cp.stdout)
        self.assertIsNotNone(m)
        self.assertNotEqual(m.group(1), "0")

    def test_46_no_unlisted_writable_temp_residue(self) -> None:
        body = textwrap.dedent(
            """\
            CONTAINER_RESULT_PRESENCE=MISSING
            CONTAINER_RESULT_VALID=NO
            CONTAINER_RESULT_ERROR=build_exit_code_file_missing
            write_host_outcome_ingestion_record "FAILED"
            shopt -s nullglob
            temps=( "$EVIDENCE_DIR"/.tmp.* )
            printf 'TEMP_COUNT=%s\\n' "${#temps[@]}"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("TEMP_COUNT=0", cp.stdout)

    def test_47_fail_closed_err_trap_does_not_recurse(self) -> None:
        body = textwrap.dedent(
            """\
            HOST_FINALIZING_IN_PROGRESS=YES
            set +e
            finalize_post_docker_host_failure "x" 5 "y" "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=1", cp.stdout)
        self.assertIn("recursion prevented", cp.stderr)

    def test_48_all_post_docker_failure_paths_use_centralized_finalizer(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("finalize_post_docker_host_failure", text)
        # unexpected failure routes through centralized finalizer
        m = re.search(r"finalize_post_docker_unexpected_failure\(\)\s*\{(.*?)\n\}", text, flags=re.S)
        self.assertIsNotNone(m)
        self.assertIn("finalize_post_docker_host_failure", m.group(1))
        # Main invalid-outcome and source-integrity paths reference the finalizer.
        self.assertIn("finalize_post_docker_host_failure", text)
        self.assertGreaterEqual(text.count("finalize_post_docker_host_failure"), 4)
        # No post-Docker overwrite redirect of BUILD_EXIT_CODE in unexpected finalizer.
        unexpected_body = m.group(1)
        self.assertNotRegex(
            unexpected_body,
            r">\s*\"\$\{EVIDENCE_DIR\}/BUILD_EXIT_CODE\.txt\"",
        )
        # Behavioral: invalid path uses finalizer and leaves missing file absent.
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "invalid_or_missing_container_outcome" 10 "missing" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            test ! -f "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
            test -f "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=10", cp.stdout)
        self._assert_no_prohibited()

    # ------------------------------------------------------------------
    # 49–50. source-integrity: absent/empty BUILD_EXIT_CODE must not be fabricated
    # ------------------------------------------------------------------
    def test_49_missing_build_exit_remains_absent_after_source_integrity_failure(self) -> None:
        self.assertFalse((self.evidence / "BUILD_EXIT_CODE.txt").exists())
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("", encoding="utf-8")
        body = textwrap.dedent(
            """\
            set +e
            enforce_post_docker_source_integrity_boundary "no" "yes"
            # Mirror production main: re-invoke centralized finalizer for nonzero exit.
            HOST_OUTCOME_INGESTION_WRITTEN="NO"
            HOST_OUTCOME_INGESTION_FINGERPRINT=""
            finalize_post_docker_host_failure \\
              "post_docker_source_integrity" 9 \\
              "Post-Docker source HEAD or clean-tree integrity failure" \\
              "OK" "FAILED" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            test ! -e "$EVIDENCE_DIR/BUILD_EXIT_CODE.txt"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=9", cp.stdout)
        self.assertFalse((self.evidence / "BUILD_EXIT_CODE.txt").exists())
        ingestion = self._ingestion()
        self.assertEqual(_read_kv(ingestion, "status"), "FAILED")
        self.assertEqual(_read_kv(ingestion, "container_result_valid"), "NO")
        self.assertEqual(_read_kv(ingestion, "container_result_presence"), "MISSING")
        self.assertIn("missing", (_read_kv(ingestion, "container_result_error") or "").lower())
        self.assertEqual(_read_kv(ingestion, "host_source_integrity_status"), "FAILED")
        self.assertEqual(_read_kv(ingestion, "preliminary_success_eligible"), "NO")
        self._assert_no_prohibited()

    def test_50_empty_build_exit_remains_empty_after_source_integrity_failure(self) -> None:
        path = self.evidence / "BUILD_EXIT_CODE.txt"
        path.write_bytes(b"")
        before = path.read_bytes()
        self.assertEqual(before, b"")
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("", encoding="utf-8")
        body = textwrap.dedent(
            """\
            set +e
            enforce_post_docker_source_integrity_boundary "yes" "no"
            HOST_OUTCOME_INGESTION_WRITTEN="NO"
            HOST_OUTCOME_INGESTION_FINGERPRINT=""
            finalize_post_docker_host_failure \\
              "post_docker_source_integrity" 9 \\
              "Post-Docker source HEAD or clean-tree integrity failure" \\
              "OK" "FAILED" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=9", cp.stdout)
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes(), before)
        self.assertNotIn(b"outcome=INFRASTRUCTURE_FAILURE", path.read_bytes())
        self.assertNotIn(b"producer=host_no_container_result", path.read_bytes())
        ingestion = self._ingestion()
        self.assertEqual(_read_kv(ingestion, "status"), "FAILED")
        self.assertEqual(_read_kv(ingestion, "container_result_valid"), "NO")
        self.assertEqual(_read_kv(ingestion, "container_result_presence"), "EMPTY")
        self.assertIn("empty", (_read_kv(ingestion, "container_result_error") or "").lower())
        self.assertEqual(_read_kv(ingestion, "host_source_integrity_status"), "FAILED")
        self.assertEqual(_read_kv(ingestion, "preliminary_success_eligible"), "NO")
        self._assert_no_prohibited()


if __name__ == "__main__":
    unittest.main()
