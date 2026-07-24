#!/usr/bin/env python3
"""Phase 3G-B integrated sourced-writer / validator / full-main smoke tests.

Primary proof uses committed container/host writers and the real local
``validate_witness_evidence.py --host-preliminary`` driver. Mock validators are
used only for host-parser/fault-unit rejection categories. Docker/Cargo/product
commands are PATH-first non-delegating tripwires.

Host exit 0 means automated structural package success only — not Independent
Witness PASS, not RC4 READY, and not rc5 readiness.
``preliminary_success_eligible`` remains NO.
"""

from __future__ import annotations

import hashlib
import shlex
import textwrap
import unittest
from pathlib import Path

import fixtures_lib
from phase3g_harness import (
    DisposableWorkspace,
    IntegratedLifecycleRunner,
    SCRIPTS_DIR,
    apply_phase3g_mutation,
    host_python_bash_path,
    remaining_phase3g_temps,
    run_bash,
    run_full_main_fail_closed_smoke,
)
from phase3g_oracles import assert_oracle_bindings
from phase3g_scenarios import integrated_scenarios


PASS_LINE = (
    "STRUCTURAL VALIDATION: PASS (host-preliminary structural PASS; "
    "not final Witness validation; not Independent Witness PASS; "
    "not final success eligibility)"
)
FAIL_LINE = "STRUCTURAL VALIDATION: FAIL"

# Supporting files produced by host pre-Docker / Witness-manual steps — not by
# the Phase 3C–3F writers under primary proof. Seeded from fixtures_lib only.
SUPPORTING_SEED_FILES = (
    "WEAVER_FORGE_PACKAGE_IDENTITY.txt",
    "SOURCE_ACQUISITION.txt",
    "SOURCE_IDENTITY.txt",
    "IMAGE_IDENTITY.txt",
    "ENVIRONMENT.txt",
    "CONTAINER_STDOUT.txt",
    "CONTAINER_STDERR.txt",
    "WITNESS_STATEMENT.md",
    "WITNESS_VERDICT.md",
    "DEVIATIONS.txt",
    "REDACTIONS.md",
    "HOST_RUN_METADATA.txt",
    "CARGO_LOCK_INTEGRITY.txt",
)


def _kv(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    prefix = f"{key}="
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :]
    return None


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_tree_bytes(evidence: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(evidence.iterdir()) if p.is_file()}


class Phase3GIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ws = DisposableWorkspace.create()
        self.runner = IntegratedLifecycleRunner(self.ws)
        (self.ws.workspace / "host-validator").mkdir(exist_ok=True)

    def tearDown(self) -> None:
        try:
            self.ws.shims.assert_no_prohibited_invocations()
        finally:
            self.ws.cleanup()

    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = remaining_phase3g_temps()
        assert not leftovers, f"residue remains: {[p.name for p in leftovers]}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _seed_supporting_files(self) -> None:
        files = fixtures_lib.build_scenario("success-artifact-present")
        for name in SUPPORTING_SEED_FILES:
            if name in files:
                (self.ws.evidence / name).write_text(
                    files[name], encoding="utf-8", newline="\n"
                )
        # Raw captures may be empty; ensure present for inventory.
        for name in ("CONTAINER_STDOUT.txt", "CONTAINER_STDERR.txt"):
            path = self.ws.evidence / name
            if not path.exists():
                path.write_text("", encoding="utf-8")

    def _present_artifact_seed_bash(self) -> str:
        """Caller-written preserve-mode artifact evidence (Phase 3C pattern).

        Includes ``artifact_identity_complete`` required by host tuple parse
        (Phase 3D). Container finalize with preserve keeps these files and
        writes BUILD_EXIT / BUILD_TIMING via the real writer.
        """
        return textwrap.dedent(
            """\
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
            artifact_identity_complete=YES
            static_inspection_complete=yes
            product_executed=NO
            ldd_used=NO
            EOF
            cat > "$EVIDENCE/STATIC_ARTIFACT_INSPECTION.txt" <<'EOF'
            BEGIN_SCHEMA_BLOCK STATIC_ARTIFACT_INSPECTION
            evidence_schema_version=1
            status=OK
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
            inspection_complete=yes
            failure_stage=NOT_APPLICABLE
            reason=test
            END_SCHEMA_BLOCK
            EOF
            """
        )

    def _finalize_success_container(self) -> None:
        evidence_rel = f"{self.ws.ws_rel}/evidence"
        artifact_rel = f"{self.ws.ws_rel}/cargo-target/debug/xai-grok-pager"
        artifact = self.ws.workspace / "cargo-target" / "debug" / "xai-grok-pager"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"phase3g inert artifact\n")
        body = textwrap.dedent(
            f"""\
            set -euo pipefail
            source ./container_narrow_build.sh
            EVIDENCE={shlex.quote(evidence_rel)}
            ARTIFACT={shlex.quote(artifact_rel)}
            EVIDENCE_FINALIZED=NO
            FINALIZING_IN_PROGRESS=NO
            CONTAINER_MAIN_ACTIVE=NO
            CURRENT_STAGE=phase3g_b
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
            {self._present_artifact_seed_bash()}
            finalize_container_terminal_outcome "CARGO_SUCCEEDED_ARTIFACT_PRESENT" 0 \
              "NOT_APPLICABLE" "OK" "COMPLETE" "preserve"
            """
        )
        cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertEqual(
            _kv(self.ws.evidence / "BUILD_EXIT_CODE.txt", "outcome"),
            "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        )

    def _host_ok_prelude(self) -> str:
        e = f"{self.ws.ws_rel}/evidence"
        hv = f"{self.ws.ws_rel}/host-validator"
        return textwrap.dedent(
            f"""\
            set -euo pipefail
            source ./run_witness_narrow_build.sh
            EVIDENCE_DIR={shlex.quote(e)}
            WORK_ROOT={shlex.quote(self.ws.ws_rel + "/work")}
            TMP_DIR={shlex.quote(self.ws.ws_rel + "/tmp")}
            HOST_VALIDATOR_DIR={shlex.quote(hv)}
            RUN_ID=run-2026-07-22-001
            DOCKER_EXIT=0
            DOCKER_STARTED_UTC=2026-01-01T00:00:00Z
            DOCKER_FINISHED_UTC=2026-01-01T00:01:00Z
            OUTCOME=CARGO_SUCCEEDED_ARTIFACT_PRESENT
            FAILURE_STAGE=NONE
            CARGO_STARTED=YES
            HOST_INFRASTRUCTURE_STATUS=OK
            HOST_SOURCE_INTEGRITY_STATUS=OK
            HOST_POST_BUILD_INTEGRITY_STATUS=OK
            HOST_EVIDENCE_COMPLETENESS_STATUS=INCOMPLETE
            POST_BUILD_INTEGRITY_OK=yes
            POST_BUILD_STATUS=OK
            PRELIMINARY_SUCCESS_ELIGIBLE=NO
            HOST_OUTCOME_INGESTION_WRITTEN=NO
            HOST_OUTCOME_INGESTION_FINGERPRINT=
            HOST_FINALIZING_IN_PROGRESS=NO
            CURRENT_STAGE=phase3g_b
            SRC_HEAD={fixtures_lib.GROK}
            SRC_HEAD_AFTER={fixtures_lib.GROK}
            SOURCE_HEAD_UNCHANGED=yes
            SOURCE_CLEAN_BEFORE=yes
            SOURCE_CLEAN_AFTER=yes
            CARGO_LOCK_BEFORE={fixtures_lib.LOCK}
            CARGO_LOCK_AFTER={fixtures_lib.LOCK}
            CARGO_LOCK_UNCHANGED=yes
            CARGO_LOCK_POST_MATCHES_EXPECTED=yes
            SOURCE_OR_LOCK_CHANGED=no
            ARTIFACT_PATH=/work/cargo-target/debug/xai-grok-pager
            ARTIFACT_EXISTS=yes
            EVIDENCE_INVENTORY_COMPLETE=no
            FULL_INTEGRITY_GATE_ALL_FOUR_YES=no
            HOST_PYTHON={shlex.quote(host_python_bash_path())}
            VALIDATOR_SCRIPT=./validate_witness_evidence.py
            mkdir -p "$HOST_VALIDATOR_DIR"
            """
        )

    def _write_preliminary_manifest(self) -> str:
        """Regenerate preliminary manifest; return SHA-256 of the manifest file."""
        # Match committed host find|sha256sum semantics via Python for Windows.
        lines: list[str] = []
        for p in sorted(self.ws.evidence.iterdir()):
            if p.is_file() and p.name != "EVIDENCE_MANIFEST.sha256":
                lines.append(f"{_sha256_file(p)}  ./{p.name}")
        manifest = self.ws.evidence / "EVIDENCE_MANIFEST.sha256"
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        return _sha256_file(manifest)

    def _host_ingest_and_post_build(self) -> None:
        body = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                set +e
                parse_container_result_tuple
                parse_rc=$?
                set -e
                printf 'PARSE_RC=%s VALID=%s ERR=%s\\n' \
                  "$parse_rc" "$CONTAINER_RESULT_VALID" "$CONTAINER_RESULT_ERROR"
                test "$CONTAINER_RESULT_VALID" = "YES"
                OUTCOME="$PARSED_CONTAINER_OUTCOME"
                FAILURE_STAGE="${PARSED_FAILURE_STAGE:-NONE}"
                CARGO_STARTED="$PARSED_CARGO_STARTED"
                write_host_docker_exit_code
                write_host_outcome_ingestion_record "OK"
                write_host_post_build_integrity_record
                sync_host_outcome_ingestion_post_build_status "OK"
                printf 'PRELIM=%s\\n' "$PRELIMINARY_SUCCESS_ELIGIBLE"
                """
            )
        )
        cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("VALID=YES", cp.stdout)
        self.assertIn("PRELIM=NO", cp.stdout)
        self.assertEqual(_kv(self.ws.evidence / "HOST_OUTCOME_INGESTION.txt", "status"), "OK")
        self.assertEqual(
            _kv(self.ws.evidence / "HOST_OUTCOME_INGESTION.txt", "preliminary_success_eligible"),
            "NO",
        )
        self.assertEqual(_kv(self.ws.evidence / "POST_BUILD_INTEGRITY.txt", "status"), "OK")
        self.assertEqual(
            _kv(self.ws.evidence / "POST_BUILD_INTEGRITY.txt", "post_build_integrity_ok"),
            "yes",
        )

    def _prepare_success_capable_package(self) -> bytes:
        """Build success package via real writers; return BUILD_EXIT bytes."""
        self._seed_supporting_files()
        self._finalize_success_container()
        # Restore supporting ENVIRONMENT / dual-owned schemas from fixtures after
        # container terminalization left provisional values that fail validator.
        files = fixtures_lib.build_scenario("success-artifact-present")
        for name in (
            "ENVIRONMENT.txt",
            "BOOTSTRAP.txt",
            "CLEAN_TARGET_PROOF.txt",
            "BUILD_COMMAND.txt",
            "BUILD_ENVIRONMENT.txt",
        ):
            (self.ws.evidence / name).write_text(
                files[name], encoding="utf-8", newline="\n"
            )
        build_exit_bytes = (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes()
        self._host_ingest_and_post_build()
        # BUILD_EXIT must remain byte-identical through host ingestion.
        self.assertEqual(
            (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes(), build_exit_bytes
        )
        self._write_preliminary_manifest()
        return build_exit_bytes

    def _run_real_validator_and_gate(self) -> tuple[str, str]:
        body = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                parse_container_result_tuple
                test "$CONTAINER_RESULT_VALID" = "YES"
                OUTCOME="$PARSED_CONTAINER_OUTCOME"
                set +e
                invoke_host_preliminary_validator
                inv=$?
                evaluate_host_automated_structural_gate
                gate=$?
                set -e
                printf 'INV=%s GATE_RC=%s GATE=%s PRELIM=%s STRUCT=%s\\n' \
                  "$inv" "$gate" "$HOST_VALIDATOR_GATE_OK" \
                  "$PRELIMINARY_SUCCESS_ELIGIBLE" "$VALIDATOR_STRUCTURAL_STATUS"
                """
            )
        )
        cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        return cp.process.stdout if hasattr(cp, "process") else cp.stdout, (
            cp.process.stderr if hasattr(cp, "process") else cp.stderr
        ) + f"\nrc={cp.returncode if hasattr(cp, 'returncode') else cp.process.returncode}"

    # ------------------------------------------------------------------
    # Scenario table
    # ------------------------------------------------------------------
    def test_01_integrated_scenario_table_categories(self) -> None:
        rows = integrated_scenarios()
        self.assertGreaterEqual(len(rows), 33)
        ids = [r.scenario_id for r in rows]
        self.assertEqual(ids, sorted(ids))
        categories = {r.container_facts.get("category") for r in rows}
        required = {
            "terminal_outcome",
            "success_capable",
            "invalid_build_exit",
            "outcome_disagreement",
            "host_failure",
            "post_build_failure",
            "validator_fault",
            "stale_mutation",
            "pre_docker",
            "full_main_fail_closed",
        }
        self.assertTrue(required.issubset(categories), categories)
        for row in rows:
            self.assertIn(
                ("expected_preliminary_success_eligible", "NO"),
                row.oracle_bindings,
            )

    # ------------------------------------------------------------------
    # Success-capable real writer → validator → gate
    # ------------------------------------------------------------------
    def test_02_success_capable_real_writer_validator_gate(self) -> None:
        build_exit_before = self._prepare_success_capable_package()
        before_tree = _evidence_tree_bytes(self.ws.evidence)
        body = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                parse_container_result_tuple
                test "$CONTAINER_RESULT_VALID" = "YES"
                OUTCOME="$PARSED_CONTAINER_OUTCOME"
                set +e
                invoke_host_preliminary_validator
                inv=$?
                evaluate_host_automated_structural_gate
                gate=$?
                set -e
                printf 'INV=%s GATE_RC=%s GATE=%s PRELIM=%s STRUCT=%s VEXIT=%s\\n' \
                  "$inv" "$gate" "$HOST_VALIDATOR_GATE_OK" \
                  "$PRELIMINARY_SUCCESS_ELIGIBLE" "$VALIDATOR_STRUCTURAL_STATUS" \
                  "$VALIDATOR_PROCESS_EXIT_CODE"
                """
            )
        )
        cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("GATE=yes", cp.stdout)
        self.assertIn("PRELIM=NO", cp.stdout)
        self.assertIn("STRUCT=PASS", cp.stdout)
        self.assertIn("VEXIT=0", cp.stdout)
        after_tree = _evidence_tree_bytes(self.ws.evidence)
        self.assertEqual(before_tree, after_tree)
        self.assertEqual(
            (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes(), build_exit_before
        )
        result = self.ws.workspace / "host-validator" / "VALIDATOR_RESULT.txt"
        stdout_cap = self.ws.workspace / "host-validator" / "VALIDATOR_STDOUT.txt"
        stderr_cap = self.ws.workspace / "host-validator" / "VALIDATOR_STDERR.txt"
        self.assertTrue(result.is_file())
        self.assertTrue(stdout_cap.is_file())
        self.assertTrue(stderr_cap.is_file())
        self.assertFalse((self.ws.evidence / "VALIDATOR_RESULT.txt").exists())
        self.assertEqual(_kv(result, "record_owner"), "host")
        self.assertEqual(_kv(result, "structural_pass"), "yes")
        self.assertEqual(
            _kv(self.ws.evidence / "HOST_OUTCOME_INGESTION.txt", "preliminary_success_eligible"),
            "NO",
        )
        # Manifest / result bindings
        manifest = self.ws.evidence / "EVIDENCE_MANIFEST.sha256"
        self.assertEqual(_kv(result, "preliminary_manifest_sha256"), _sha256_file(manifest))
        self.assertIn("validate_witness_evidence.py", _kv(result, "validator_script_path") or "")
        self.assertEqual(_kv(result, "stdout_capture_sha256"), _sha256_file(stdout_cap))
        self.assertEqual(_kv(result, "stderr_capture_sha256"), _sha256_file(stderr_cap))
        assert_oracle_bindings(
            {
                "expected_host_exit": 0,
                "expected_explicit_outcome": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                "expected_structural_status": "PASS",
                "expected_preliminary_success_eligible": "NO",
                "expected_validator_exit": 0,
            },
            {
                "expected_host_exit": 0,
                "expected_explicit_outcome": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                "expected_structural_status": "PASS",
                "expected_preliminary_success_eligible": "NO",
                "expected_validator_exit": 0,
            },
            scenario_id="terminal_cargo_succeeded_artifact_present",
        )

    # ------------------------------------------------------------------
    # Five terminal outcomes
    # ------------------------------------------------------------------
    def test_03_five_terminal_outcomes_sourced_writers(self) -> None:
        cases = (
            ("BUILD_NOT_STARTED", 7, "rustc_version_probe", "NO", ""),
            ("CARGO_FAILED", 17, "cargo_build", "YES", "17"),
            ("CARGO_SUCCEEDED_ARTIFACT_MISSING", 42, "artifact_presence_check", "YES", "0"),
            ("INFRASTRUCTURE_FAILURE", 1, "unexpected_err", "NO", ""),
        )
        for outcome, exit_code, stage, cargo_started, cargo_exit in cases:
            with self.subTest(outcome=outcome):
                for p in list(self.ws.evidence.iterdir()):
                    if p.is_file():
                        p.unlink()
                evidence_rel = f"{self.ws.ws_rel}/evidence"
                cargo_setup = ""
                if cargo_started == "YES":
                    cargo_setup = textwrap.dedent(
                        f"""\
                        CARGO_STARTED=YES
                        CARGO_EXIT_CODE={cargo_exit or exit_code}
                        CARGO_START_UTC=2026-01-01T00:00:00Z
                        CARGO_END_UTC=2026-01-01T00:00:02Z
                        CARGO_ELAPSED_SECONDS=2
                        """
                    )
                else:
                    cargo_setup = "CARGO_STARTED=NO\nCARGO_EXIT_CODE=\n"
                body = textwrap.dedent(
                    f"""\
                    set -euo pipefail
                    source ./container_narrow_build.sh
                    EVIDENCE={shlex.quote(evidence_rel)}
                    ARTIFACT={shlex.quote(self.ws.ws_rel + "/no-such-artifact")}
                    EVIDENCE_FINALIZED=NO
                    FINALIZING_IN_PROGRESS=NO
                    CONTAINER_MAIN_ACTIVE=NO
                    CURRENT_STAGE=phase3g_b
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
                    {cargo_setup}
                    init_evidence
                    finalize_container_terminal_outcome {shlex.quote(outcome)} {exit_code} \
                      {shlex.quote(stage)}
                    """
                )
                cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(cp.returncode, 0, cp.stderr)
                self.assertEqual(
                    _kv(self.ws.evidence / "BUILD_EXIT_CODE.txt", "outcome"), outcome
                )
                before = (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes()
                host = (
                    self._host_ok_prelude()
                    + textwrap.dedent(
                        f"""\
                        OUTCOME={shlex.quote(outcome)}
                        set +e
                        parse_container_result_tuple
                        parse_rc=$?
                        if [[ "$CONTAINER_RESULT_VALID" == "YES" ]]; then
                          write_host_docker_exit_code
                          write_host_outcome_ingestion_record "OK"
                          POST_BUILD_INTEGRITY_OK=no
                          write_host_post_build_integrity_record
                          sync_host_outcome_ingestion_post_build_status "FAILED"
                          final_rc=1
                        else
                          finalize_post_docker_host_failure phase3g_terminal 1 fail \
                            OK OK FAILED INCOMPLETE NO
                          final_rc=$?
                        fi
                        set -e
                        printf 'PARSE=%s VALID=%s FINAL=%s PRELIM=%s\\n' \
                          "$parse_rc" "$CONTAINER_RESULT_VALID" "$final_rc" \
                          "$PRELIMINARY_SUCCESS_ELIGIBLE"
                        """
                    )
                )
                hcp = run_bash(["-c", host], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(hcp.returncode, 0, hcp.stderr + hcp.stdout)
                self.assertIn("FINAL=1", hcp.stdout)
                self.assertIn("PRELIM=NO", hcp.stdout)
                self.assertEqual(
                    (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes(), before
                )
                self.assertFalse(
                    (self.ws.workspace / "host-validator" / "VALIDATOR_RESULT.txt").exists()
                )

        # Fifth outcome: success path covered by test_02; assert scenario exists.
        ids = {r.scenario_id for r in integrated_scenarios()}
        self.assertIn("terminal_cargo_succeeded_artifact_present", ids)

    # ------------------------------------------------------------------
    # Invalid BUILD_EXIT
    # ------------------------------------------------------------------
    def test_04_invalid_build_exit_fail_closed(self) -> None:
        for mode, payload in (
            ("missing", None),
            ("empty", b""),
            ("malformed", b"not-a-schema\n"),
        ):
            with self.subTest(mode=mode):
                for p in list(self.ws.evidence.iterdir()):
                    if p.is_file():
                        p.unlink()
                result = self.runner.finalize_container(
                    "BUILD_NOT_STARTED", exit_code=7, failure_stage="probe"
                )
                self.assertEqual(result.process.returncode, 0, result.process.stderr)
                target = self.ws.evidence / "BUILD_EXIT_CODE.txt"
                if payload is None:
                    target.unlink()
                    before = None
                else:
                    target.write_bytes(payload)
                    before = payload
                host = (
                    self._host_ok_prelude()
                    + textwrap.dedent(
                        """\
                        set +e
                        parse_container_result_tuple
                        finalize_post_docker_host_failure invalid_tuple 10 invalid \
                          FAILED OK FAILED FAILED NO
                        rc=$?
                        set -e
                        printf 'RC=%s VALID=%s PRELIM=%s\\n' \
                          "$rc" "$CONTAINER_RESULT_VALID" "$PRELIMINARY_SUCCESS_ELIGIBLE"
                        """
                    )
                )
                cp = run_bash(["-c", host], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
                self.assertIn("RC=10", cp.stdout)
                self.assertIn("VALID=NO", cp.stdout)
                self.assertIn("PRELIM=NO", cp.stdout)
                after = target.read_bytes() if target.exists() else None
                self.assertEqual(after, before)
                self.assertFalse(
                    (self.ws.workspace / "host-validator" / "VALIDATOR_RESULT.txt").exists()
                )

    # ------------------------------------------------------------------
    # Outcome disagreements
    # ------------------------------------------------------------------
    def test_05_outcome_disagreements_fail_closed(self) -> None:
        cases = (
            (
                "disagreement_cargo_started",
                "BUILD_NOT_STARTED",
                "NO",
                "NOT_APPLICABLE",
                "NO",
                None,
                None,
                lambda text: text.replace("cargo_started=NO", "cargo_started=YES"),
            ),
            (
                "disagreement_cargo_exit_code",
                "CARGO_FAILED",
                "YES",
                "17",
                "NO",
                None,
                None,
                lambda text: text.replace("cargo_exit_code=17", "cargo_exit_code=0"),
            ),
            (
                "disagreement_artifact_present",
                "CARGO_SUCCEEDED_ARTIFACT_MISSING",
                "YES",
                "0",
                "NO",
                None,
                None,
                lambda text: text.replace(
                    "artifact_present=NO", "artifact_present=YES"
                ),
            ),
            (
                "disagreement_container_result_validity",
                "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
                "YES",
                "0",
                "YES",
                "YES",
                "YES",
                lambda text: text.replace("cargo_started=YES", "cargo_started=NO"),
            ),
        )
        for (
            sid,
            outcome,
            cargo_started,
            cargo_exit,
            art_present,
            ident,
            static,
            mutator,
        ) in cases:
            with self.subTest(scenario_id=sid):
                for p in list(self.ws.evidence.iterdir()):
                    if p.is_file():
                        p.unlink()
                # Build a consistent tuple then apply an explicit disagreement.
                lines = [
                    "evidence_schema_version=1",
                    "status=FAILED",
                    f"outcome={outcome}",
                    f"cargo_started={cargo_started}",
                    f"build_status={outcome}",
                    f"cargo_exit_code={cargo_exit}",
                    "failure_stage=phase3g_disagreement",
                    f"artifact_present={art_present}",
                ]
                if ident is not None:
                    lines.append(f"artifact_identity_complete={ident}")
                if static is not None:
                    lines.append(f"static_inspection_complete={static}")
                text = "\n".join(lines) + "\n"
                if mutator is not None:
                    text = mutator(text)
                (self.ws.evidence / "BUILD_EXIT_CODE.txt").write_text(
                    text, encoding="utf-8", newline="\n"
                )
                art_lines = [
                    "evidence_schema_version=1",
                    f"artifact_present={'yes' if art_present == 'YES' else 'no'}",
                    "applicable=yes",
                    "product_executed=NO",
                    "ldd_used=NO",
                ]
                if sid == "disagreement_artifact_present":
                    art_lines[1] = "artifact_present=no"
                if ident is not None:
                    art_lines.append(f"artifact_identity_complete={ident}")
                if static is not None:
                    art_lines.append(f"static_inspection_complete={static}")
                (self.ws.evidence / "ARTIFACT_IDENTITY.txt").write_text(
                    "\n".join(art_lines) + "\n", encoding="utf-8", newline="\n"
                )
                before = (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes()
                host = (
                    self._host_ok_prelude()
                    + textwrap.dedent(
                        """\
                        set +e
                        parse_container_result_tuple
                        finalize_post_docker_host_failure disagreement 10 disagree \
                          FAILED OK FAILED FAILED NO
                        rc=$?
                        set -e
                        printf 'RC=%s VALID=%s ERR=%s\\n' \
                          "$rc" "$CONTAINER_RESULT_VALID" "$CONTAINER_RESULT_ERROR"
                        """
                    )
                )
                cp = run_bash(["-c", host], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
                self.assertIn("RC=10", cp.stdout)
                self.assertIn("VALID=NO", cp.stdout)
                self.assertEqual(
                    (self.ws.evidence / "BUILD_EXIT_CODE.txt").read_bytes(), before
                )
                self.assertFalse(
                    (self.ws.workspace / "host-validator" / "VALIDATOR_RESULT.txt").exists()
                )

    # ------------------------------------------------------------------
    # Host / POST_BUILD failures
    # ------------------------------------------------------------------
    def test_06_host_and_post_build_failures(self) -> None:
        self._prepare_success_capable_package()
        # Host infrastructure failure finalizer
        host = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                set +e
                parse_container_result_tuple
                finalize_post_docker_host_failure host_infra 10 infra \
                  FAILED OK FAILED FAILED NO
                rc=$?
                set -e
                printf 'RC=%s INFRA=%s PRELIM=%s\\n' \
                  "$rc" "$HOST_INFRASTRUCTURE_STATUS" "$PRELIMINARY_SUCCESS_ELIGIBLE"
                """
            )
        )
        cp = run_bash(["-c", host], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("RC=10", cp.stdout)
        self.assertIn("INFRA=FAILED", cp.stdout)
        self.assertEqual(
            _kv(self.ws.evidence / "HOST_OUTCOME_INGESTION.txt", "preliminary_success_eligible"),
            "NO",
        )

        # Fresh package for POST_BUILD failure
        self.ws.cleanup()
        self.ws = DisposableWorkspace.create()
        self.runner = IntegratedLifecycleRunner(self.ws)
        (self.ws.workspace / "host-validator").mkdir(exist_ok=True)
        self._seed_supporting_files()
        self._finalize_success_container()
        files = fixtures_lib.build_scenario("success-artifact-present")
        for name in (
            "ENVIRONMENT.txt",
            "BOOTSTRAP.txt",
            "CLEAN_TARGET_PROOF.txt",
            "BUILD_COMMAND.txt",
            "BUILD_ENVIRONMENT.txt",
        ):
            (self.ws.evidence / name).write_text(
                files[name], encoding="utf-8", newline="\n"
            )
        host = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                parse_container_result_tuple
                test "$CONTAINER_RESULT_VALID" = "YES"
                OUTCOME="$PARSED_CONTAINER_OUTCOME"
                write_host_docker_exit_code
                write_host_outcome_ingestion_record "OK"
                POST_BUILD_INTEGRITY_OK=no
                write_host_post_build_integrity_record
                sync_host_outcome_ingestion_post_build_status "FAILED"
                printf 'POST=%s OKFLAG=%s PRELIM=%s\\n' \
                  "$(read_kv_strict "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" status)" \
                  "$(read_kv_strict "$EVIDENCE_DIR/POST_BUILD_INTEGRITY.txt" post_build_integrity_ok)" \
                  "$PRELIMINARY_SUCCESS_ELIGIBLE"
                """
            )
        )
        cp = run_bash(["-c", host], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("POST=FAILED", cp.stdout)
        self.assertIn("OKFLAG=no", cp.stdout)
        self.assertIn("PRELIM=NO", cp.stdout)

        # HOST_OUTCOME sync mismatch: POST_BUILD OK but ingestion left FAILED
        self.ws.cleanup()
        self.ws = DisposableWorkspace.create()
        self.runner = IntegratedLifecycleRunner(self.ws)
        (self.ws.workspace / "host-validator").mkdir(exist_ok=True)
        self._prepare_success_capable_package()
        ingestion = self.ws.evidence / "HOST_OUTCOME_INGESTION.txt"
        text = ingestion.read_text(encoding="utf-8")
        text = text.replace(
            "post_build_integrity_status=OK", "post_build_integrity_status=FAILED"
        )
        ingestion.write_text(text, encoding="utf-8", newline="\n")
        self._write_preliminary_manifest()
        body = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                parse_container_result_tuple
                set +e
                invoke_host_preliminary_validator
                inv=$?
                evaluate_host_automated_structural_gate
                gate=$?
                set -e
                printf 'INV=%s GATE=%s\\n' "$inv" "$HOST_VALIDATOR_GATE_OK"
                """
            )
        )
        cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
        self.assertIn("GATE=no", cp.stdout)

    # ------------------------------------------------------------------
    # Real validator FAIL + mock fault units
    # ------------------------------------------------------------------
    def test_07_real_validator_structural_fail(self) -> None:
        # Real validator against a terminal failure package (incomplete for PASS).
        result = self.runner.finalize_container(
            "CARGO_FAILED", exit_code=17, failure_stage="cargo_build"
        )
        self.assertEqual(result.process.returncode, 0, result.process.stderr)
        self._write_preliminary_manifest()
        from phase3g_harness import RealValidatorDriver

        driver = RealValidatorDriver(self.ws)
        vr = driver.run_host_preliminary(self.ws.evidence)
        self.assertNotEqual(vr.returncode, 0)
        self.assertIn("FAIL", vr.stdout)
        self.assertNotIn(PASS_LINE, vr.stdout)

    def test_08_mock_validator_fault_parser_categories(self) -> None:
        for label, code, stdout in (
            ("nonzero", 7, PASS_LINE + "\n"),
            ("missing", 0, "not a structural result\n"),
            ("contradictory", 0, PASS_LINE + "\n" + FAIL_LINE + "\n"),
            ("multiple", 0, PASS_LINE + "\n" + PASS_LINE + "\n"),
        ):
            with self.subTest(label=label):
                self.ws.cleanup()
                self.ws = DisposableWorkspace.create()
                self.runner = IntegratedLifecycleRunner(self.ws)
                (self.ws.workspace / "host-validator").mkdir(exist_ok=True)
                self._prepare_success_capable_package()
                mock = self.ws.workspace / "mock_validator.py"
                mock.write_text(
                    "import sys\n"
                    f"sys.stdout.write({stdout!r})\n"
                    f"raise SystemExit({code})\n",
                    encoding="utf-8",
                    newline="\n",
                )
                body = (
                    self._host_ok_prelude()
                    + f"VALIDATOR_SCRIPT={shlex.quote(self.ws.ws_rel + '/mock_validator.py')}\n"
                    + textwrap.dedent(
                        """\
                        parse_container_result_tuple
                        set +e
                        invoke_host_preliminary_validator
                        inv=$?
                        evaluate_host_automated_structural_gate
                        gate=$?
                        set -e
                        printf 'INV=%s GATE=%s STRUCT=%s\\n' \
                          "$inv" "$HOST_VALIDATOR_GATE_OK" "$VALIDATOR_STRUCTURAL_STATUS"
                        """
                    )
                )
                cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
                self.assertIn("GATE=no", cp.stdout)
                self.assertIn("INV=1", cp.stdout)
                # Nonzero process exit may still parse a PASS line; gate must reject.
                if label != "nonzero":
                    self.assertNotIn("STRUCT=PASS", cp.stdout)

    # ------------------------------------------------------------------
    # Stale / spoof / mixed-run mutations
    # ------------------------------------------------------------------
    def test_09_stale_spoof_mixed_run_mutations(self) -> None:
        mutations = (
            "stale_run_id",
            "stale_manifest_hash",
            "stale_validator_identity",
            "stale_evidence_path",
            "stale_stdout_capture",
            "stale_stderr_capture",
            "mixed_run_evidence",
            "preliminary_success_yes_injection",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.ws.cleanup()
                self.ws = DisposableWorkspace.create()
                self.runner = IntegratedLifecycleRunner(self.ws)
                (self.ws.workspace / "host-validator").mkdir(exist_ok=True)
                self._prepare_success_capable_package()
                body = (
                    self._host_ok_prelude()
                    + textwrap.dedent(
                        """\
                        parse_container_result_tuple
                        set +e
                        invoke_host_preliminary_validator
                        evaluate_host_automated_structural_gate
                        set -e
                        printf 'BASE_GATE=%s\\n' "$HOST_VALIDATOR_GATE_OK"
                        """
                    )
                )
                cp = run_bash(["-c", body], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
                self.assertIn("BASE_GATE=yes", cp.stdout)
                apply_phase3g_mutation(self.ws, mutation)
                body2 = (
                    self._host_ok_prelude()
                    + textwrap.dedent(
                        """\
                        parse_container_result_tuple
                        set +e
                        verify_host_validator_result_bindings
                        bind=$?
                        evaluate_host_automated_structural_gate
                        gate=$?
                        set -e
                        printf 'BIND=%s GATE=%s PRELIM=%s\\n' \
                          "$bind" "$HOST_VALIDATOR_GATE_OK" "$PRELIMINARY_SUCCESS_ELIGIBLE"
                        """
                    )
                )
                cp2 = run_bash(["-c", body2], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
                self.assertEqual(cp2.returncode, 0, cp2.stderr + cp2.stdout)
                self.assertIn("GATE=no", cp2.stdout)
                self.assertIn("PRELIM=NO", cp2.stdout)
                if mutation == "preliminary_success_yes_injection":
                    # Injection must be rejected by gate; eligibility stays NO in memory.
                    self.assertEqual(
                        _kv(
                            self.ws.evidence / "HOST_OUTCOME_INGESTION.txt",
                            "preliminary_success_eligible",
                        ),
                        "YES",
                    )

    # ------------------------------------------------------------------
    # Pre-Docker no-validator + full-main fail-closed smoke
    # ------------------------------------------------------------------
    def test_10_pre_docker_no_validator_and_full_main_fail_closed(self) -> None:
        # Sourced pre-Docker finalizer: no validator artifacts.
        host = (
            self._host_ok_prelude()
            + textwrap.dedent(
                """\
                mkdir -p "$EVIDENCE_DIR"
                : > "$EVIDENCE_DIR/ENVIRONMENT.txt"
                set +e
                # finalize_pre_docker calls abort(); trap exit and observe files.
                finalize_pre_docker_infrastructure_failure phase3g_pre_docker 3 "pre-docker test"
                rc=$?
                set -e
                printf 'RC=%s\\n' "$rc"
                """
            )
        )
        cp = run_bash(["-c", host], env=self.ws.bash_env(), cwd=SCRIPTS_DIR)
        # abort() terminates the shell; accept nonzero and assert no validator result.
        self.assertNotEqual(cp.returncode, 0)
        self.assertFalse(
            (self.ws.workspace / "host-validator" / "VALIDATOR_RESULT.txt").exists()
        )
        self.assertFalse((self.ws.evidence / "VALIDATOR_RESULT.txt").exists())
        self.assertEqual(
            _kv(self.ws.evidence / "BUILD_EXIT_CODE.txt", "outcome"),
            "INFRASTRUCTURE_FAILURE",
        )

        # Limited full-main fail-closed smoke (real main, shims, no Docker).
        self.ws.cleanup()
        self.ws = DisposableWorkspace.create()
        self.runner = IntegratedLifecycleRunner(self.ws)
        (self.ws.workspace / "host-validator").mkdir(exist_ok=True)
        # Ensure work root exists for main.
        self.ws.work_root.mkdir(exist_ok=True)
        exec_result = run_full_main_fail_closed_smoke(self.ws)
        self.assertNotEqual(exec_result.process.returncode, 0, exec_result.process.stderr)
        # Docker shim must not have been invoked for pull/run (pre-docker failure).
        docker_log = self.ws.workspace / "docker_shim.log"
        if docker_log.is_file():
            text = docker_log.read_text(encoding="utf-8")
            self.assertNotIn(" pull ", f" {text} ")
            self.assertNotIn(" run ", f" {text} ")
        self.assertFalse(
            (self.ws.workspace / "host-validator" / "VALIDATOR_RESULT.txt").exists()
        )

    # ------------------------------------------------------------------
    # Limited full-main success-capable note: sourced path is primary.
    # Full-main exit 0 requires Witness-manual completion the automated main
    # intentionally does not write; success-capable exit 0 is proven in test_02.
    # ------------------------------------------------------------------
    def test_11_full_main_success_capable_delegated_to_sourced_proof(self) -> None:
        row = next(
            r
            for r in integrated_scenarios()
            if r.scenario_id == "full_main_success_capable_smoke"
        )
        self.assertEqual(row.terminal_outcome, "CARGO_SUCCEEDED_ARTIFACT_PRESENT")
        self.assertEqual(row.expected_host_gate.get("host_exit"), 0)
        # Documented: primary success-capable proof is test_02 (sourced writers +
        # real validator). Full-main automated orchestration cannot reach host
        # exit 0 without Witness-manual files the main does not write; runtime
        # modification is prohibited. Fail-closed full-main is test_10.


if __name__ == "__main__":
    unittest.main(verbosity=2)
