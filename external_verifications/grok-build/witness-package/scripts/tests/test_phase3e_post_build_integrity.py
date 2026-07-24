#!/usr/bin/env python3
"""Phase 3E host-owned POST_BUILD integrity finalization tests.

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (phase3e_test_*)
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
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import fixtures_lib as fx  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

HOST_SCRIPT_NAME = "run_witness_narrow_build.sh"
HOST_SCRIPT = SCRIPTS_DIR / HOST_SCRIPT_NAME
CONTAINER_SCRIPT = SCRIPTS_DIR / "container_narrow_build.sh"
TEMPLATE = PACKAGE_DIR / "templates" / "POST_BUILD_INTEGRITY.txt"
TEMP_PREFIX = "phase3e_test_"

EXACT_POST_BUILD_FIELDS = (
    "evidence_schema_version",
    "status",
    "outcome",
    "source_head_before",
    "source_head_after",
    "source_head_unchanged",
    "source_clean_before",
    "source_clean_after",
    "cargo_lock_sha256_before",
    "cargo_lock_sha256_after",
    "cargo_lock_unchanged",
    "cargo_lock_post_matches_expected",
    "source_or_lock_changed",
    "artifact_path",
    "artifact_exists",
    "docker_exit_code",
    "failure_stage",
    "evidence_inventory_complete",
    "full_integrity_gate_all_four_yes",
    "full_integrity_gate_note",
    "post_build_integrity_ok",
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

_KEY_RE = re.compile(r'echo\s+"([A-Za-z0-9_]+)=')


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
    raise unittest.SkipTest("bash not available for Phase 3E POST_BUILD tests")


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


def _remaining_phase3e_temps() -> list[Path]:
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


def _post_build_keys(path: Path) -> list[str]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            keys.append(line.split("=", 1)[0])
    return keys


def writer_block_keys(text: str, filename: str) -> set[str]:
    lines = text.splitlines()
    redirect_re = re.compile(r"\}\s*>\s*\"?\$\{EVIDENCE_DIR\}/" + re.escape(filename))
    best: set[str] = set()
    for idx, line in enumerate(lines):
        if not redirect_re.search(line):
            continue
        keys: set[str] = set()
        j = idx - 1
        while j >= 0:
            m = _KEY_RE.search(lines[j])
            if m:
                keys.add(m.group(1))
            if lines[j].strip() == "{":
                break
            j -= 1
        if len(keys) > len(best):
            best = keys
    return best


class Phase3EPostBuildIntegrityTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = _remaining_phase3e_temps()
        assert not leftovers, (
            f"Phase 3E temporary directories remain under {TESTS_DIR}: "
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
                    echo "mock-{name}: prohibited in Phase 3E tests" >&2
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
            RUN_ID=phase3e-test-run
            DOCKER_EXIT=0
            DOCKER_STARTED_UTC=2026-01-01T00:00:00Z
            DOCKER_FINISHED_UTC=2026-01-01T00:01:00Z
            DOCKER_STARTED_EPOCH=1
            DOCKER_FINISHED_EPOCH=61
            OUTCOME=CARGO_SUCCEEDED_ARTIFACT_PRESENT
            FAILURE_STAGE=NONE
            CARGO_STARTED=YES
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
            HOST_POST_BUILD_INTEGRITY_STATUS=NOT_REACHED
            HOST_EVIDENCE_COMPLETENESS_STATUS=INCOMPLETE
            PRELIMINARY_SUCCESS_ELIGIBLE=NO
            POST_BUILD_INTEGRITY_OK=no
            POST_BUILD_STATUS=NOT_REACHED
            SRC_HEAD=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
            SRC_HEAD_AFTER=98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
            CARGO_LOCK_BEFORE=1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421
            CARGO_LOCK_AFTER=1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421
            SOURCE_HEAD_UNCHANGED=yes
            SOURCE_CLEAN_BEFORE=yes
            SOURCE_CLEAN_AFTER=yes
            CARGO_LOCK_UNCHANGED=yes
            CARGO_LOCK_POST_MATCHES_EXPECTED=yes
            SOURCE_OR_LOCK_CHANGED=no
            EVIDENCE_INVENTORY_COMPLETE=no
            FULL_INTEGRITY_GATE_ALL_FOUR_YES=no
            ARTIFACT_PATH=/work/cargo-target/debug/xai-grok-pager
            ARTIFACT_EXISTS=yes
            SPECIFIC_FAILURE_RECORDED=0
            CURRENT_STAGE=phase3e_test
            """
        )

    def _run_sourced(self, body: str) -> subprocess.CompletedProcess[str]:
        script = self._source_prelude() + "\n" + body
        return _bash(["-c", script], env=self._bash_env(), cwd=SCRIPTS_DIR)

    def _assert_no_prohibited(self) -> None:
        text = self.cmd_log.read_text(encoding="utf-8")
        self.assertEqual(text, "", f"prohibited command invoked: {text!r}")

    def _post(self) -> Path:
        return self.evidence / "POST_BUILD_INTEGRITY.txt"

    def _ingestion(self) -> Path:
        return self.evidence / "HOST_OUTCOME_INGESTION.txt"

    def _assert_complete_failed_post_build(self) -> None:
        post = self._post()
        self.assertTrue(post.is_file())
        self.assertEqual(_post_build_keys(post), list(EXACT_POST_BUILD_FIELDS))
        self.assertEqual(_read_kv(post, "status"), "FAILED")
        self.assertEqual(_read_kv(post, "post_build_integrity_ok"), "no")
        self.assertNotEqual(_read_kv(post, "status"), "NOT_APPLICABLE")
        self.assertNotEqual(_read_kv(post, "status"), "OK")

    def _valid_tuple_lines(
        self,
        outcome: str = "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        *,
        cargo_started: str = "YES",
        cargo_exit: str = "0",
        artifact_present: str = "YES",
        identity_complete: str = "YES",
        static_complete: str = "YES",
    ) -> list[str]:
        return [
            "evidence_schema_version=1",
            "status=OK",
            f"outcome={outcome}",
            f"cargo_started={cargo_started}",
            f"build_status={outcome}",
            f"cargo_exit_code={cargo_exit}",
            "failure_stage=NONE",
            f"artifact_present={artifact_present}",
            f"artifact_identity_complete={identity_complete}",
            f"static_inspection_complete={static_complete}",
        ]

    def _write_build_exit(self, lines: list[str]) -> Path:
        path = self.evidence / "BUILD_EXIT_CODE.txt"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return path

    # ------------------------------------------------------------------
    # Ordinary technical gate
    # ------------------------------------------------------------------
    def test_01_ordinary_gate_yes_produces_status_ok(self) -> None:
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=yes
            write_host_post_build_integrity_record
            printf 'STATUS=%s\\n' "$(grep -m1 '^status=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            printf 'OKFLAG=%s\\n' "$(grep -m1 '^post_build_integrity_ok=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            printf 'HOST=%s\\n' "$HOST_POST_BUILD_INTEGRITY_STATUS"
            printf 'PRELIM=%s\\n' "$PRELIMINARY_SUCCESS_ELIGIBLE"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("STATUS=OK", cp.stdout)
        self.assertIn("OKFLAG=yes", cp.stdout)
        self.assertIn("HOST=OK", cp.stdout)
        self.assertIn("PRELIM=NO", cp.stdout)
        self._assert_no_prohibited()

    def test_02_ordinary_gate_no_produces_status_failed(self) -> None:
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=no
            CARGO_LOCK_POST_MATCHES_EXPECTED=no
            write_host_post_build_integrity_record
            printf 'STATUS=%s\\n' "$(grep -m1 '^status=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            printf 'OKFLAG=%s\\n' "$(grep -m1 '^post_build_integrity_ok=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            printf 'HOST=%s\\n' "$HOST_POST_BUILD_INTEGRITY_STATUS"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("STATUS=FAILED", cp.stdout)
        self.assertIn("OKFLAG=no", cp.stdout)
        self.assertIn("HOST=FAILED", cp.stdout)

    def test_03_status_and_ok_cannot_contradict(self) -> None:
        # Policy forces consistency even if caller sets contradictory intent.
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=yes
            apply_host_post_build_status_policy
            test "$POST_BUILD_STATUS" = "OK"
            test "$HOST_POST_BUILD_INTEGRITY_STATUS" = "OK"
            POST_BUILD_INTEGRITY_OK=no
            apply_host_post_build_status_policy
            test "$POST_BUILD_STATUS" = "FAILED"
            test "$HOST_POST_BUILD_INTEGRITY_STATUS" = "FAILED"
            test "$POST_BUILD_INTEGRITY_OK" = "no"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    def test_04_host_post_build_status_matches_final_record(self) -> None:
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=yes
            write_host_post_build_integrity_record
            test "$HOST_POST_BUILD_INTEGRITY_STATUS" = "$(grep -m1 '^status=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            POST_BUILD_INTEGRITY_OK=no
            write_host_post_build_integrity_record
            test "$HOST_POST_BUILD_INTEGRITY_STATUS" = "$(grep -m1 '^status=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    def test_05_ingestion_post_build_status_synchronized(self) -> None:
        self._write_build_exit(self._valid_tuple_lines())
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            POST_BUILD_INTEGRITY_OK=yes
            write_host_post_build_integrity_record
            write_host_outcome_ingestion_record "OK"
            test "$(grep -m1 '^post_build_integrity_status=' "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt" | cut -d= -f2-)" = "OK"
            POST_BUILD_INTEGRITY_OK=no
            SOURCE_HEAD_UNCHANGED=no
            write_host_post_build_integrity_record
            sync_host_outcome_ingestion_post_build_status "OK"
            test "$(grep -m1 '^post_build_integrity_status=' "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt" | cut -d= -f2-)" = "FAILED"
            test "$(grep -m1 '^preliminary_success_eligible=' "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt" | cut -d= -f2-)" = "NO"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    # ------------------------------------------------------------------
    # Ordinary failure conditions
    # ------------------------------------------------------------------
    def test_06_source_head_mismatch_complete_failed(self) -> None:
        body = textwrap.dedent(
            """\
            SOURCE_HEAD_UNCHANGED=no
            SRC_HEAD_AFTER=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
            POST_BUILD_INTEGRITY_OK=no
            write_host_post_build_integrity_record
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_complete_failed_post_build()
        self.assertEqual(_read_kv(self._post(), "source_head_unchanged"), "no")

    def test_07_dirty_source_tree_complete_failed(self) -> None:
        body = textwrap.dedent(
            """\
            SOURCE_CLEAN_AFTER=no
            POST_BUILD_INTEGRITY_OK=no
            write_host_post_build_integrity_record
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_complete_failed_post_build()
        self.assertEqual(_read_kv(self._post(), "source_clean_after"), "no")

    def test_08_cargo_lock_mismatch_complete_failed(self) -> None:
        body = textwrap.dedent(
            """\
            CARGO_LOCK_UNCHANGED=no
            CARGO_LOCK_POST_MATCHES_EXPECTED=no
            CARGO_LOCK_AFTER=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
            POST_BUILD_INTEGRITY_OK=no
            write_host_post_build_integrity_record
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_complete_failed_post_build()
        self.assertEqual(_read_kv(self._post(), "cargo_lock_post_matches_expected"), "no")

    # ------------------------------------------------------------------
    # Pre-/post-Docker failure finalizers
    # ------------------------------------------------------------------
    def test_09_pre_docker_infrastructure_failure_complete_failed(self) -> None:
        (self.evidence / "HOST_RUN_METADATA.txt").write_text("seed=1\n", encoding="utf-8")
        # Seed a NOT_REACHED placeholder that must be replaced.
        (self.evidence / "POST_BUILD_INTEGRITY.txt").write_text(
            "evidence_schema_version=1\nstatus=NOT_REACHED\n",
            encoding="utf-8",
            newline="\n",
        )
        body = textwrap.dedent(
            """\
            # finalize_pre_docker_infrastructure_failure calls abort/exit; trap it.
            set +e
            (
              finalize_pre_docker_infrastructure_failure "image_pull" 7 "pull failed"
            )
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=7", cp.stdout)
        self._assert_complete_failed_post_build()
        self.assertEqual(_read_kv(self._post(), "outcome"), "INFRASTRUCTURE_FAILURE")
        self.assertEqual(_read_kv(self._post(), "docker_exit_code"), "NOT_STARTED")
        self._assert_no_prohibited()

    def test_10_post_docker_unexpected_failure_complete_failed(self) -> None:
        self._write_build_exit(self._valid_tuple_lines())
        before = (self.evidence / "BUILD_EXIT_CODE.txt").read_bytes()
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "unexpected_post_docker" 12 "boom" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            ec=$?
            set -e
            printf 'EC=%s\\n' "$ec"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("EC=12", cp.stdout)
        self._assert_complete_failed_post_build()
        self.assertEqual((self.evidence / "BUILD_EXIT_CODE.txt").read_bytes(), before)
        self.assertEqual(_read_kv(self._ingestion(), "post_build_integrity_status"), "FAILED")

    def test_11_missing_container_result_no_build_exit_created(self) -> None:
        self.assertFalse((self.evidence / "BUILD_EXIT_CODE.txt").exists())
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "missing_container_result" 10 "missing" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertFalse((self.evidence / "BUILD_EXIT_CODE.txt").exists())
        self._assert_complete_failed_post_build()

    def test_12_empty_container_result_byte_preserved(self) -> None:
        path = self.evidence / "BUILD_EXIT_CODE.txt"
        path.write_bytes(b"")
        before = path.read_bytes()
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "empty_container_result" 10 "empty" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self._assert_complete_failed_post_build()

    def test_13_malformed_container_result_byte_preserved(self) -> None:
        path = self.evidence / "BUILD_EXIT_CODE.txt"
        raw = b"not=a\nvalid\x00tuple\n"
        path.write_bytes(raw)
        before = path.read_bytes()
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "malformed_container_result" 10 "malformed" \\
              "FAILED" "OK" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self._assert_complete_failed_post_build()

    def test_14_valid_container_result_byte_preserved(self) -> None:
        path = self._write_build_exit(self._valid_tuple_lines())
        before = path.read_bytes()
        body = textwrap.dedent(
            """\
            set +e
            finalize_post_docker_host_failure \\
              "post_docker_source_integrity" 9 "head drift" \\
              "OK" "FAILED" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(path.read_bytes(), before)
        self._assert_complete_failed_post_build()

    # ------------------------------------------------------------------
    # Ownership / schema / vocabulary
    # ------------------------------------------------------------------
    def test_15_container_script_is_post_build_non_writer(self) -> None:
        text = CONTAINER_SCRIPT.read_text(encoding="utf-8")
        # May mention POST_BUILD in comments as a non-writer obligation, but must
        # never redirect/write the host-owned file.
        self.assertNotRegex(text, r'>\s*"\$\{EVIDENCE_DIR\}/POST_BUILD_INTEGRITY\.txt"')
        self.assertNotRegex(text, r"tee\b.*POST_BUILD_INTEGRITY")
        self.assertIn("Never writes POST_BUILD_INTEGRITY.txt", text)
        self.assertIn("do not create or modify host-owned POST_BUILD_INTEGRITY.txt", text)

    def test_16_exact_field_set_across_writer_template_validator_fixtures(self) -> None:
        host = HOST_SCRIPT.read_text(encoding="utf-8")
        writer_keys = writer_block_keys(host, "POST_BUILD_INTEGRITY.txt")
        required = set(v.FILE_REQUIRED_FIELDS["POST_BUILD_INTEGRITY.txt"])
        self.assertEqual(writer_keys, required)
        self.assertEqual(set(EXACT_POST_BUILD_FIELDS), required)

        template_keys = [
            line.split("=", 1)[0]
            for line in TEMPLATE.read_text(encoding="utf-8").splitlines()
            if "=" in line and not line.startswith("#")
        ]
        self.assertEqual(template_keys, list(EXACT_POST_BUILD_FIELDS))

        for scenario in fx.ALL_SCENARIOS:
            content = fx.build_scenario(scenario)["POST_BUILD_INTEGRITY.txt"]
            keys = [
                line.split("=", 1)[0]
                for line in content.splitlines()
                if "=" in line and not line.startswith("#")
            ]
            self.assertEqual(keys, list(EXACT_POST_BUILD_FIELDS), scenario)

    def test_17_no_not_applicable_final_status_in_writer_policy(self) -> None:
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=no
            write_host_post_build_integrity_record
            status="$(grep -m1 '^status=' "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" | cut -d= -f2-)"
            test "$status" != "NOT_APPLICABLE"
            test "$status" = "FAILED"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        for scenario in fx.ALL_SCENARIOS:
            content = fx.build_scenario(scenario)["POST_BUILD_INTEGRITY.txt"]
            self.assertNotIn("status=NOT_APPLICABLE", content)

    def test_18_not_reached_cannot_qualify_as_finalized_success(self) -> None:
        errors: list[str] = []
        v.check_post_build_integrity(
            {
                "status": "NOT_REACHED",
                "post_build_integrity_ok": "yes",
                "outcome": "INFRASTRUCTURE_FAILURE",
            },
            errors,
        )
        self.assertTrue(any("NOT_REACHED cannot qualify" in e for e in errors), errors)

        body = textwrap.dedent(
            """\
            POST_BUILD_STATUS=NOT_REACHED
            POST_BUILD_INTEGRITY_OK=yes
            apply_host_post_build_status_policy
            # yes forces OK final status — transitional NOT_REACHED cannot remain with ok=yes
            test "$POST_BUILD_STATUS" = "OK"
            POST_BUILD_INTEGRITY_OK=no
            apply_host_post_build_status_policy
            test "$POST_BUILD_STATUS" = "FAILED"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    def test_19_preliminary_success_eligible_remains_no(self) -> None:
        self._write_build_exit(self._valid_tuple_lines())
        body = textwrap.dedent(
            """\
            parse_container_result_tuple
            POST_BUILD_INTEGRITY_OK=yes
            write_host_post_build_integrity_record
            write_host_outcome_ingestion_record "OK"
            test "$PRELIMINARY_SUCCESS_ELIGIBLE" = "NO"
            test "$(grep -m1 '^preliminary_success_eligible=' "$EVIDENCE_DIR/HOST_OUTCOME_INGESTION.txt" | cut -d= -f2-)" = "NO"
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)

    def test_20_validator_not_invoked_by_phase3e_writers(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        for sym in (
            "write_host_post_build_integrity_record",
            "apply_host_post_build_status_policy",
            "sync_host_outcome_ingestion_post_build_status",
            "finalize_post_docker_host_failure",
            "finalize_pre_docker_infrastructure_failure",
        ):
            m = re.search(rf"{sym}\(\)\s*\{{(.*?)\n\}}", text, flags=re.S)
            self.assertIsNotNone(m, sym)
            body = m.group(1)
            self.assertNotIn("validate_witness_evidence", body)
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=yes
            write_host_post_build_integrity_record
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_no_prohibited()

    def test_21_host_exit_validator_gated_after_phase3f_b(self) -> None:
        text = HOST_SCRIPT.read_text(encoding="utf-8")
        # Historical fact: Phase 3E itself did not implement validator-gated exit.
        # Phase 3E writers remain non-invokers (covered by test_20).
        # Current source after Phase 3F-B: host exit 0 is validator-gated.
        self.assertIn("invoke_host_preliminary_validator", text)
        self.assertIn("evaluate_host_automated_structural_gate", text)
        self.assertIn("--host-preliminary", text)
        self.assertIn("VALIDATOR_RESULT", text)
        self.assertIn('mark_stage "step21b_host_preliminary_validator"', text)
        # Ordinary technical integrity failure still maps to nonzero exit class.
        self.assertIn('if [[ "${POST_BUILD_INTEGRITY_OK}" != "yes" ]]; then', text)
        self.assertIn("FINAL_EXIT_CODE=9", text)
        # Host gate OK is required for exit 0.
        self.assertIn('if [[ "${HOST_VALIDATOR_GATE_OK}" == "yes" ]]; then', text)
        self.assertIn("FINAL_EXIT_CODE=0", text)

    def test_22_no_real_workflow_tools_invoked(self) -> None:
        body = textwrap.dedent(
            """\
            POST_BUILD_INTEGRITY_OK=no
            write_host_post_build_integrity_record
            set +e
            finalize_post_docker_host_failure "x" 3 "y" "FAILED" "OK" "FAILED" "FAILED" "NO"
            set -e
            """
        )
        cp = self._run_sourced(body)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self._assert_no_prohibited()
        self.assertFalse((self.workspace / "home").joinpath(".cargo").exists())


if __name__ == "__main__":
    unittest.main()
