#!/usr/bin/env python3
"""Phase 3F-B host validator gating tests (Pi-adjudicated plan).

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (phase3f_test_*)
- Host script is sourced only; run_witness_narrow_build_main is never invoked
- Mock python / fixture validator outputs; no delegation to Docker, Cargo,
  compiler, product, package manager, network, or Independent Witness workflow
- Validator against real product evidence is not used; mocks emit controlled
  stdout/stderr fixtures
- Cleanup of repository-local temps on success and failure
"""

from __future__ import annotations

import hashlib
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
HOST_SCRIPT_NAME = "run_witness_narrow_build.sh"
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
TEMP_PREFIX = "phase3f_test_"

EXACT_VALIDATOR_RESULT_FIELDS = (
    "schema_version",
    "record_owner",
    "run_id",
    "validator_command",
    "validator_script_path",
    "evidence_dir",
    "preliminary_manifest_path",
    "preliminary_manifest_sha256",
    "validator_process_exit_code",
    "structural_status",
    "structural_pass",
    "explicit_outcome_observed",
    "machine_verdict_ceiling",
    "stdout_capture_path",
    "stdout_capture_sha256",
    "stderr_capture_path",
    "stderr_capture_sha256",
    "invocation_started_utc",
    "invocation_finished_utc",
    "failure_stage",
    "error_reason",
)

PASS_LINE = (
    "STRUCTURAL VALIDATION: PASS (host-preliminary structural PASS; "
    "not final Witness validation; not Independent Witness PASS; "
    "not final success eligibility)"
)
FAIL_LINE = "STRUCTURAL VALIDATION: FAIL"

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
    raise unittest.SkipTest("bash not available for Phase 3F-B host validator gate tests")


def _bash(
    args: list[str], *, env: dict[str, str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
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


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _read_kv(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _result_keys(path: Path) -> list[str]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            keys.append(line.split("=", 1)[0])
    return keys


def _remaining_phase3f_temps() -> list[Path]:
    if not TESTS_DIR.is_dir():
        return []
    return sorted(
        p for p in TESTS_DIR.iterdir() if p.is_dir() and p.name.startswith(TEMP_PREFIX)
    )


class Phase3FHostValidatorGateTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_phase3f_temps()
        assert not leftovers, (
            f"Phase 3F temporary directories remain under {TESTS_DIR}: "
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

        self.validator_dir = self.workspace / "host-validator"
        self.validator_dir.mkdir()
        self.validator_dir_rel = f"{self.ws_rel}/host-validator"

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
                    echo "mock-{name}: prohibited in Phase 3F-B tests" >&2
                    exit 99
                    """
                ),
            )

        self.mock_validator = self.workspace / "mock_validate_witness_evidence.py"
        # Use the same interpreter running these tests (avoid broken Windows py launcher).
        self.host_python = Path(sys.executable).resolve()
        self._install_mock_validator(exit_code=0, stdout=PASS_LINE + "\n", stderr="")

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

        self._seed_gate_evidence()

    def tearDown(self) -> None:
        workspace = getattr(self, "workspace", None)
        self._tmpdir.cleanup()
        if workspace is not None:
            self.assertFalse(
                workspace.exists(),
                f"TemporaryDirectory failed to remove repository-local workspace: {workspace}",
            )

    def _install_mock_validator(
        self, *, exit_code: int, stdout: str, stderr: str = ""
    ) -> None:
        # Fixture validator: controlled output only; never touches evidence.
        self.mock_validator.write_text(
            textwrap.dedent(
                f"""\
                #!/usr/bin/env python3
                import sys
                sys.stdout.write({stdout!r})
                sys.stderr.write({stderr!r})
                raise SystemExit({exit_code})
                """
            ),
            encoding="utf-8",
            newline="\n",
        )

    def _host_python_bash_path(self) -> str:
        # Prefer a path Git bash can exec; fall back to as_posix.
        p = self.host_python
        s = str(p)
        if len(s) >= 2 and s[1] == ":":
            return f"/{s[0].lower()}{s[2:].replace(chr(92), '/')}"
        return p.as_posix()

    def _seed_gate_evidence(self) -> None:
        (self.evidence / "HOST_OUTCOME_INGESTION.txt").write_text(
            textwrap.dedent(
                """\
                schema_version=1
                status=OK
                container_result_presence=PRESENT
                container_result_valid=YES
                container_result_error=none
                container_outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
                container_exit_code=0
                cargo_started=YES
                cargo_exit_code=0
                artifact_present=YES
                artifact_identity_complete=YES
                static_inspection_complete=YES
                host_infrastructure_status=OK
                host_source_integrity_status=OK
                post_build_integrity_status=OK
                evidence_completeness_status=INCOMPLETE
                preliminary_success_eligible=NO
                record_owner=HOST
                run_id=phase3f-b-test-run
                failure_stage=NONE
                """
            ),
            encoding="utf-8",
            newline="\n",
        )
        (self.evidence / "POST_BUILD_INTEGRITY.txt").write_text(
            textwrap.dedent(
                """\
                evidence_schema_version=1
                status=OK
                outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT
                source_head_before=abc
                source_head_after=abc
                source_head_unchanged=yes
                source_clean_before=yes
                source_clean_after=yes
                cargo_lock_sha256_before=dead
                cargo_lock_sha256_after=dead
                cargo_lock_unchanged=yes
                cargo_lock_post_matches_expected=yes
                source_or_lock_changed=no
                artifact_path=/x
                artifact_exists=yes
                docker_exit_code=0
                failure_stage=NONE
                evidence_inventory_complete=no
                full_integrity_gate_all_four_yes=no
                full_integrity_gate_note=note
                post_build_integrity_ok=yes
                """
            ),
            encoding="utf-8",
            newline="\n",
        )
        (self.evidence / "BUILD_EXIT_CODE.txt").write_text(
            "evidence_schema_version=1\nstatus=OK\noutcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT\n",
            encoding="utf-8",
            newline="\n",
        )
        (self.evidence / "EVIDENCE_MANIFEST.sha256").write_text(
            "0" * 64 + "  ./BUILD_EXIT_CODE.txt\n",
            encoding="utf-8",
            newline="\n",
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
            TMP_DIR={shlex.quote(self.ws_rel + "/tmp")}
            HOST_VALIDATOR_DIR={shlex.quote(self.validator_dir_rel)}
            VALIDATOR_SCRIPT={shlex.quote(self.ws_rel + "/mock_validate_witness_evidence.py")}
            HOST_PYTHON={shlex.quote(self._host_python_bash_path())}
            RUN_ID=phase3f-b-test-run
            DOCKER_EXIT=0
            OUTCOME=CARGO_SUCCEEDED_ARTIFACT_PRESENT
            FAILURE_STAGE=NONE
            CARGO_STARTED=YES
            VERDICT_CEILING=PASS
            CONTAINER_RESULT_VALID=YES
            CONTAINER_RESULT_PRESENCE=PRESENT
            CONTAINER_RESULT_ERROR=none
            HOST_INFRASTRUCTURE_STATUS=OK
            HOST_SOURCE_INTEGRITY_STATUS=OK
            HOST_POST_BUILD_INTEGRITY_STATUS=OK
            HOST_EVIDENCE_COMPLETENESS_STATUS=INCOMPLETE
            PRELIMINARY_SUCCESS_ELIGIBLE=NO
            POST_BUILD_INTEGRITY_OK=yes
            POST_BUILD_STATUS=OK
            HOST_OUTCOME_INGESTION_WRITTEN=NO
            HOST_OUTCOME_INGESTION_FINGERPRINT=
            HOST_FINALIZING_IN_PROGRESS=NO
            CURRENT_STAGE=phase3f_b_test
            """
        )

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._source_prelude() + "\n" + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _assert_no_prohibited(self) -> None:
        text = self.cmd_log.read_text(encoding="utf-8")
        self.assertEqual(text, "", f"prohibited command invoked: {text!r}")

    def _result_path(self) -> Path:
        return self.validator_dir / "VALIDATOR_RESULT.txt"

    def _stdout_path(self) -> Path:
        return self.validator_dir / "VALIDATOR_STDOUT.txt"

    def _stderr_path(self) -> Path:
        return self.validator_dir / "VALIDATOR_STDERR.txt"

    # ------------------------------------------------------------------
    # Lifecycle / invocation shape
    # ------------------------------------------------------------------
    def test_01_lifecycle_order_validator_after_manifest_before_summary(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        i_manifest = text.find('mark_stage "step21_manifest_generation"')
        i_validator = text.find('mark_stage "step21b_host_preliminary_validator"')
        i_summary = text.find('mark_stage "step22_summary_and_exit"')
        self.assertGreater(i_manifest, 0)
        self.assertGreater(i_validator, i_manifest)
        self.assertGreater(i_summary, i_validator)
        self.assertIn("invoke_host_preliminary_validator", text)
        self.assertIn("evaluate_host_automated_structural_gate", text)
        # Failure finalizers must not invoke validator.
        for sym in (
            "finalize_post_docker_host_failure",
            "finalize_pre_docker_infrastructure_failure",
        ):
            m = re.search(rf"{sym}\(\)\s*\{{(.*?)\n\}}", text, flags=re.S)
            self.assertIsNotNone(m, sym)
            self.assertNotIn("invoke_host_preliminary_validator", m.group(1))

    def test_02_invokes_host_preliminary_mode(self) -> None:
        body = textwrap.dedent(
            """\
            invoke_host_preliminary_validator
            printf 'CMD=%s\\n' "$VALIDATOR_COMMAND"
            printf 'PASS=%s\\n' "$VALIDATOR_STRUCTURAL_PASS"
            printf 'RC=%s\\n' "$VALIDATOR_PROCESS_EXIT_CODE"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("--host-preliminary", cp.stdout)
        self.assertIn("PASS=yes", cp.stdout)
        self.assertIn("RC=0", cp.stdout)
        self._assert_no_prohibited()

    def test_03_stdout_stderr_and_result_outside_evidence_dir(self) -> None:
        cp = self._run_sourced("invoke_host_preliminary_validator\n")
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertTrue(self._stdout_path().is_file())
        self.assertTrue(self._stderr_path().is_file())
        self.assertTrue(self._result_path().is_file())
        for p in (self._stdout_path(), self._stderr_path(), self._result_path()):
            self.assertFalse(str(p.resolve()).startswith(str(self.evidence.resolve())))
            self.assertNotIn(p.name, [x.name for x in self.evidence.iterdir()])

    def test_04_result_not_in_manifest_and_exact_field_set(self) -> None:
        cp = self._run_sourced("invoke_host_preliminary_validator\n")
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        manifest = (self.evidence / "EVIDENCE_MANIFEST.sha256").read_text(encoding="utf-8")
        self.assertNotIn("VALIDATOR_RESULT", manifest)
        self.assertNotIn("VALIDATOR_STDOUT", manifest)
        self.assertNotIn("VALIDATOR_STDERR", manifest)
        keys = _result_keys(self._result_path())
        self.assertEqual(keys, list(EXACT_VALIDATOR_RESULT_FIELDS))
        self.assertEqual(_read_kv(self._result_path(), "record_owner"), "host")
        self.assertEqual(_read_kv(self._result_path(), "schema_version"), "1")

    def test_05_stale_result_removed_before_invocation(self) -> None:
        stale = self._result_path()
        stale.write_text("schema_version=1\nrun_id=STALE\n", encoding="utf-8", newline="\n")
        (self.validator_dir / "VALIDATOR_STDOUT.txt").write_text("STALE\n", encoding="utf-8")
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                printf 'RUN=%s\\n' "$(grep -m1 '^run_id=' "$VALIDATOR_RESULT_PATH" | cut -d= -f2-)"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RUN=phase3f-b-test-run", cp.stdout)
        self.assertNotIn("STALE", self._stdout_path().read_text(encoding="utf-8"))
        self.assertNotEqual(_read_kv(self._result_path(), "run_id"), "STALE")

    # ------------------------------------------------------------------
    # Structural PASS / FAIL parse + process exit coupling
    # ------------------------------------------------------------------
    def test_06_exit0_plus_exact_structural_pass_accepted(self) -> None:
        self._install_mock_validator(exit_code=0, stdout=PASS_LINE + "\n")
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                evaluate_host_automated_structural_gate
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                printf 'PRELIM=%s\\n' "$PRELIMINARY_SUCCESS_ELIGIBLE"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("GATE=yes", cp.stdout)
        self.assertIn("PRELIM=NO", cp.stdout)

    def test_07_exit0_without_pass_rejected(self) -> None:
        self._install_mock_validator(exit_code=0, stdout="ok done\n")
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                set +e
                invoke_host_preliminary_validator
                inv=$?
                set -e
                printf 'INV=%s\\n' "$inv"
                printf 'PASS=%s\\n' "$VALIDATOR_STRUCTURAL_PASS"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("PASS=no", cp.stdout)
        self.assertIn("REASON=structural_pass_missing", cp.stdout)

    def test_08_pass_text_with_nonzero_exit_rejected(self) -> None:
        self._install_mock_validator(exit_code=1, stdout=PASS_LINE + "\n")
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                set +e
                invoke_host_preliminary_validator
                inv=$?
                set -e
                evaluate_host_automated_structural_gate || true
                printf 'INV=%s\\n' "$inv"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)
        self.assertIn("REASON=validator_process_nonzero", cp.stdout)

    def test_09_structural_fail_rejected(self) -> None:
        self._install_mock_validator(exit_code=1, stdout=FAIL_LINE + "\n")
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                set +e
                invoke_host_preliminary_validator
                inv=$?
                set -e
                printf 'INV=%s\\n' "$inv"
                printf 'STATUS=%s\\n' "$VALIDATOR_STRUCTURAL_STATUS"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("STATUS=FAIL", cp.stdout)

    def test_10_contradictory_pass_fail_rejected(self) -> None:
        self._install_mock_validator(
            exit_code=0, stdout=PASS_LINE + "\n" + FAIL_LINE + "\n"
        )
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                set +e
                invoke_host_preliminary_validator
                inv=$?
                set -e
                printf 'INV=%s\\n' "$inv"
                printf 'STATUS=%s\\n' "$VALIDATOR_STRUCTURAL_STATUS"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("STATUS=CONTRADICTORY", cp.stdout)
        self.assertIn("REASON=contradictory_pass_fail", cp.stdout)

    def test_11_arbitrary_pass_word_not_accepted(self) -> None:
        self._install_mock_validator(
            exit_code=0, stdout="all checks PASS successfully\n"
        )
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                set +e
                invoke_host_preliminary_validator
                inv=$?
                set -e
                printf 'INV=%s\\n' "$inv"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("REASON=structural_pass_missing", cp.stdout)

    def test_12_missing_validator_script_rejected(self) -> None:
        body = textwrap.dedent(
            """\
            VALIDATOR_SCRIPT="$HOST_VALIDATOR_DIR/does_not_exist.py"
            set +e
            invoke_host_preliminary_validator
            inv=$?
            set -e
            printf 'INV=%s\\n' "$inv"
            printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
            test -f "$VALIDATOR_RESULT_PATH"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("REASON=validator_script_missing", cp.stdout)
        self.assertTrue(self._result_path().is_file())

    def test_13_invocation_failure_rejected(self) -> None:
        # Non-delegating failing interpreter stub (does not call real python/docker/etc.).
        bad_py = self.workspace / "bad_python"
        _write_executable(
            bad_py,
            textwrap.dedent(
                """\
                #!/usr/bin/env bash
                echo "mock python cannot start" >&2
                exit 127
                """
            ),
        )
        body = textwrap.dedent(
            f"""\
            HOST_PYTHON={shlex.quote(self.ws_rel + "/bad_python")}
            set +e
            invoke_host_preliminary_validator
            inv=$?
            set -e
            printf 'INV=%s\\n' "$inv"
            printf 'RC=%s\\n' "$VALIDATOR_PROCESS_EXIT_CODE"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("INV=1", cp.stdout)
        self.assertIn("RC=127", cp.stdout)

    def test_14_missing_capture_rejected(self) -> None:
        # Simulate capture missing by pointing stdout path to a non-writable situation
        # after invalidate: replace invoke internals via parse on missing file.
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invalidate_host_validator_artifacts
                set +e
                parse_validator_structural_stdout "$HOST_VALIDATOR_DIR/missing_stdout.txt"
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("REASON=stdout_capture_missing", cp.stdout)

    # ------------------------------------------------------------------
    # Binding / spoof resistance
    # ------------------------------------------------------------------
    def test_15_manifest_hash_binding_enforced(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                VALIDATOR_MANIFEST_SHA256=deadbeef
                set +e
                verify_host_validator_result_bindings
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("REASON=manifest_hash_mismatch", cp.stdout)

    def test_16_run_id_binding_enforced(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                RUN_ID=other-run
                set +e
                verify_host_validator_result_bindings
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("REASON=run_id_mismatch", cp.stdout)

    def test_17_evidence_dir_binding_enforced(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                EVIDENCE_DIR=/tmp/not-this-evidence
                set +e
                verify_host_validator_result_bindings
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("REASON=evidence_dir_mismatch", cp.stdout)

    def test_18_validator_identity_binding_enforced(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                VALIDATOR_SCRIPT=/tmp/forged_validator.py
                set +e
                verify_host_validator_result_bindings
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'REASON=%s\\n' "$VALIDATOR_ERROR_REASON"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("REASON=validator_identity_mismatch", cp.stdout)

    # ------------------------------------------------------------------
    # Host exit gate conditions
    # ------------------------------------------------------------------
    def test_19_docker_nonzero_prevents_gate(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                DOCKER_EXIT=1
                set +e
                evaluate_host_automated_structural_gate
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    def test_20_wrong_outcome_prevents_gate(self) -> None:
        text = (self.evidence / "HOST_OUTCOME_INGESTION.txt").read_text(encoding="utf-8")
        (self.evidence / "HOST_OUTCOME_INGESTION.txt").write_text(
            text.replace(
                "container_outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                "container_outcome=CARGO_FAILED",
            ),
            encoding="utf-8",
            newline="\n",
        )
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                OUTCOME=CARGO_FAILED
                set +e
                evaluate_host_automated_structural_gate
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    def test_21_invalid_container_result_prevents_gate(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                CONTAINER_RESULT_VALID=NO
                set +e
                evaluate_host_automated_structural_gate
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    def test_22_host_outcome_status_not_ok_prevents_gate(self) -> None:
        text = (self.evidence / "HOST_OUTCOME_INGESTION.txt").read_text(encoding="utf-8")
        (self.evidence / "HOST_OUTCOME_INGESTION.txt").write_text(
            text.replace("status=OK", "status=FAILED", 1),
            encoding="utf-8",
            newline="\n",
        )
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                set +e
                evaluate_host_automated_structural_gate
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    def test_23_host_status_fields_not_ok_prevent_gate(self) -> None:
        for var in (
            "HOST_INFRASTRUCTURE_STATUS",
            "HOST_SOURCE_INTEGRITY_STATUS",
            "HOST_POST_BUILD_INTEGRITY_STATUS",
        ):
            cp = self._run_sourced(
                textwrap.dedent(
                    f"""\
                    invoke_host_preliminary_validator
                    {var}=FAILED
                    set +e
                    evaluate_host_automated_structural_gate
                    rc=$?
                    set -e
                    printf 'VAR={var}\\n'
                    printf 'RC=%s\\n' "$rc"
                    printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                    """
                )
            )
            self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
            self.assertIn("RC=1", cp.stdout)
            self.assertIn("GATE=no", cp.stdout)

    def test_24_post_build_status_not_ok_prevents_gate(self) -> None:
        text = (self.evidence / "POST_BUILD_INTEGRITY.txt").read_text(encoding="utf-8")
        (self.evidence / "POST_BUILD_INTEGRITY.txt").write_text(
            text.replace("status=OK", "status=FAILED", 1),
            encoding="utf-8",
            newline="\n",
        )
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                set +e
                evaluate_host_automated_structural_gate
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    def test_25_post_build_integrity_ok_not_yes_prevents_gate(self) -> None:
        text = (self.evidence / "POST_BUILD_INTEGRITY.txt").read_text(encoding="utf-8")
        (self.evidence / "POST_BUILD_INTEGRITY.txt").write_text(
            text.replace("post_build_integrity_ok=yes", "post_build_integrity_ok=no"),
            encoding="utf-8",
            newline="\n",
        )
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                POST_BUILD_INTEGRITY_OK=no
                set +e
                evaluate_host_automated_structural_gate
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=1", cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    def test_26_success_keeps_preliminary_success_eligible_no(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                evaluate_host_automated_structural_gate
                printf 'GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                printf 'PRELIM=%s\\n' "$PRELIMINARY_SUCCESS_ELIGIBLE"
                printf 'FILE=%s\\n' "$(grep -m1 '^preliminary_success_eligible=' "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt")"
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("GATE=yes", cp.stdout)
        self.assertIn("PRELIM=NO", cp.stdout)
        self.assertIn("FILE=preliminary_success_eligible=NO", cp.stdout)

    # ------------------------------------------------------------------
    # BUILD_EXIT_CODE immutability + no evidence write
    # ------------------------------------------------------------------
    def test_27_build_exit_missing_remains_missing(self) -> None:
        bec = self.evidence / "BUILD_EXIT_CODE.txt"
        bec.unlink()
        self.assertFalse(bec.exists())
        cp = self._run_sourced("invoke_host_preliminary_validator || true\n")
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertFalse(bec.exists())

    def test_28_empty_build_exit_remains_empty(self) -> None:
        bec = self.evidence / "BUILD_EXIT_CODE.txt"
        bec.write_bytes(b"")
        before = bec.read_bytes()
        cp = self._run_sourced("invoke_host_preliminary_validator || true\n")
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(bec.read_bytes(), before)

    def test_29_malformed_build_exit_unchanged(self) -> None:
        bec = self.evidence / "BUILD_EXIT_CODE.txt"
        payload = b"not=a\nvalid tuple\n\xff"
        bec.write_bytes(payload)
        cp = self._run_sourced("invoke_host_preliminary_validator || true\n")
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(bec.read_bytes(), payload)

    def test_30_valid_build_exit_byte_for_byte_unchanged(self) -> None:
        bec = self.evidence / "BUILD_EXIT_CODE.txt"
        before = bec.read_bytes()
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                evaluate_host_automated_structural_gate
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(bec.read_bytes(), before)

    def test_31_validator_path_writes_no_evidence(self) -> None:
        before = {
            p.name: (p.stat().st_mtime_ns, p.read_bytes())
            for p in self.evidence.iterdir()
            if p.is_file()
        }
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                evaluate_host_automated_structural_gate
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        after_names = {p.name for p in self.evidence.iterdir() if p.is_file()}
        self.assertEqual(after_names, set(before))
        for name, (mtime, data) in before.items():
            p = self.evidence / name
            self.assertEqual(p.read_bytes(), data)
            self.assertEqual(p.stat().st_mtime_ns, mtime)
        self.assertNotIn("VALIDATOR_RESULT.txt", after_names)

    def test_32_no_real_workflow_tools_invoked(self) -> None:
        cp = self._run_sourced(
            textwrap.dedent(
                """\
                invoke_host_preliminary_validator
                evaluate_host_automated_structural_gate
                """
            )
        )
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_no_prohibited()
        self.assertFalse((self.workspace / "home").joinpath(".cargo").exists())
        # Capture hashes bound in result
        result = self._result_path()
        self.assertEqual(
            _read_kv(result, "stdout_capture_sha256"),
            _sha256_file(self._stdout_path()),
        )
        self.assertEqual(
            _read_kv(result, "stderr_capture_sha256"),
            _sha256_file(self._stderr_path()),
        )


if __name__ == "__main__":
    unittest.main()
