#!/usr/bin/env python3
"""Phase 3G-A generator/harness framework tests (Pi-adjudicated plan).

Safety contract:
- Python standard library only
- Temporary workspaces are children of scripts/tests/ (phase3g_test_*)
- Host/container scripts are sourced only for function discovery; mains never run
- Command shims are PATH-first and never delegate
- Real local validator may run only in controlled host-preliminary driver smoke
- No Docker daemon, Cargo, rustc, rustup, DotSlash, protoc, ldd, product,
  network, host Witness workflow, or Independent Witness workflow
- Cleanup of repository-local temps on success and failure
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import fixtures_lib as fx  # noqa: E402
import phase3g_harness as harness  # noqa: E402
import phase3g_oracles as oracles  # noqa: E402
import phase3g_scenarios as scenarios  # noqa: E402


class Phase3GFrameworkTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls) -> None:
        leftovers = harness.remaining_phase3g_temps()
        assert not leftovers, (
            f"Phase 3G temporary directories remain under {TESTS_DIR}: "
            f"{[p.name for p in leftovers]}"
        )

    def setUp(self) -> None:
        self._workspaces: list[harness.DisposableWorkspace] = []

    def tearDown(self) -> None:
        for ws in self._workspaces:
            try:
                if ws.workspace.exists():
                    ws.cleanup()
            except Exception:
                # Best-effort; tearDownClass asserts no leftovers.
                if ws.workspace.exists():
                    shutil.rmtree(ws.workspace, ignore_errors=True)
        self._workspaces.clear()

    def _workspace(self) -> harness.DisposableWorkspace:
        ws = harness.DisposableWorkspace.create()
        self._workspaces.append(ws)
        return ws

    # ------------------------------------------------------------------
    # Scenario model
    # ------------------------------------------------------------------
    def test_01_valid_scenario_row_accepted(self) -> None:
        rows = scenarios.framework_smoke_scenarios()
        self.assertGreaterEqual(len(rows), 2)
        for row in rows:
            self.assertIsInstance(row, scenarios.ScenarioRow)
            self.assertIn(row.terminal_outcome, scenarios.TERMINAL_OUTCOMES)
            self.assertIn("scenario_id=", row.diagnostic_prefix())

    def test_02_duplicate_scenario_id_rejected(self) -> None:
        base = dict(scenarios._FRAMEWORK_SMOKE_RAW[0])
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            scenarios.compile_scenario_table([base, dict(base)])
        self.assertIn("duplicate scenario_id", str(ctx.exception))
        self.assertIn(base["scenario_id"], str(ctx.exception))

    def test_03_unknown_terminal_outcome_rejected(self) -> None:
        raw = dict(scenarios._FRAMEWORK_SMOKE_RAW[0])
        raw["terminal_outcome"] = "NOT_A_REAL_OUTCOME"
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            scenarios.make_scenario_row(raw)
        self.assertIn("unknown terminal outcome", str(ctx.exception))
        self.assertIn(raw["scenario_id"], str(ctx.exception))

    def test_04_unknown_scenario_field_rejected(self) -> None:
        raw = dict(scenarios._FRAMEWORK_SMOKE_RAW[0])
        raw["unexpected_field"] = "nope"
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            scenarios.make_scenario_row(raw)
        self.assertIn("unknown top-level scenario field", str(ctx.exception))

    def test_05_malformed_facts_rejected(self) -> None:
        raw = dict(scenarios._FRAMEWORK_SMOKE_RAW[0])
        raw["container_facts"] = "not-a-mapping"
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            scenarios.make_scenario_row(raw)
        self.assertIn("container_facts must be a mapping", str(ctx.exception))

    def test_06_deterministic_ordering_and_fixed_seed_identity(self) -> None:
        rows = scenarios.framework_smoke_scenarios()
        ids = [r.scenario_id for r in rows]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(
            scenarios.PHASE3G_DETERMINISTIC_SEED, "phase3g-fixed-seed-v1"
        )
        self.assertIn("seed=phase3g-fixed-seed-v1", scenarios.PHASE3G_ORDER_IDENTITY)
        self.assertIn(scenarios.PHASE3G_ORDER_IDENTITY, rows[0].diagnostic_prefix())
        # Reversed input still yields ascending order.
        reversed_raw = list(reversed(scenarios._FRAMEWORK_SMOKE_RAW))
        again = scenarios.compile_scenario_table(reversed_raw)
        self.assertEqual([r.scenario_id for r in again], ids)

    # ------------------------------------------------------------------
    # Lifecycle transition model
    # ------------------------------------------------------------------
    def test_07_valid_lifecycle_chain_accepted(self) -> None:
        machine = scenarios.LifecycleMachine()
        machine.apply_chain(scenarios.LIFECYCLE_TRANSITIONS)
        self.assertEqual(tuple(machine.completed), scenarios.LIFECYCLE_TRANSITIONS)
        self.assertTrue(machine.terminal_exit_recorded)
        catalog = scenarios.lifecycle_transition_catalog()
        self.assertEqual(len(catalog), 12)
        self.assertEqual(catalog[0].name, "container_finalization")
        self.assertEqual(catalog[-1].name, "final_host_exit")

    def test_08_transition_before_predecessor_rejected(self) -> None:
        machine = scenarios.LifecycleMachine()
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            machine.apply("host_outcome_ingestion")
        self.assertIn("transition-before-predecessor", str(ctx.exception))

    def test_09_duplicate_final_exit_rejected(self) -> None:
        machine = scenarios.LifecycleMachine()
        machine.apply_chain(scenarios.LIFECYCLE_TRANSITIONS)
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            machine.apply("final_host_exit")
        self.assertIn("duplicate final_host_exit", str(ctx.exception))

    def test_10_pre_docker_failure_excludes_validator(self) -> None:
        machine = scenarios.LifecycleMachine(path_kind="pre_docker_failure")
        # Advance through non-validator prefix that does not require excluded preds.
        for step in (
            "container_finalization",
            "container_evidence_ownership",
            "host_outcome_ingestion",
            "source_integrity_finalization",
            "post_build_finalization",
            "host_outcome_synchronization",
            "closed_auxiliary_finalization",
            "preliminary_manifest_finalization",
        ):
            machine.apply(step)
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            machine.apply("host_preliminary_validator")
        self.assertIn("pre-Docker failure path excludes validator", str(ctx.exception))
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx2:
            machine.apply("validator_result_creation")
        self.assertIn("pre-Docker failure path excludes validator", str(ctx2.exception))

    def test_11_manual_witness_lifecycle_excluded(self) -> None:
        self.assertTrue(scenarios.MANUAL_WITNESS_LIFECYCLE_EXCLUDED)
        machine = scenarios.LifecycleMachine()
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            machine.apply(scenarios.MANUAL_WITNESS_LIFECYCLE_LABEL)
        self.assertIn("manual Witness lifecycle is excluded", str(ctx.exception))

    # ------------------------------------------------------------------
    # Mutation model
    # ------------------------------------------------------------------
    def test_12_known_mutation_accepted_and_ordered(self) -> None:
        ordered = scenarios.validate_mutations(
            ["stale_stderr_capture", "stale_stdout_capture"],
            scenario_id="mut_order",
        )
        self.assertEqual(ordered, ("stale_stderr_capture", "stale_stdout_capture"))
        # Single known mutation from closed vocabulary.
        one = scenarios.validate_mutations(["missing_build_exit"], scenario_id="mut_ok")
        self.assertEqual(one, ("missing_build_exit",))

    def test_13_unknown_mutation_rejected(self) -> None:
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            scenarios.validate_mutations(["not_a_real_mutation"], scenario_id="mut_bad")
        self.assertIn("unknown mutation", str(ctx.exception))
        self.assertIn("mut_bad", str(ctx.exception))

    def test_14_incompatible_and_duplicate_mutations_rejected(self) -> None:
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
            scenarios.validate_mutations(
                ["missing_build_exit", "empty_build_exit"], scenario_id="mut_conflict"
            )
        self.assertIn("incompatible mutation combination", str(ctx.exception))
        with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx2:
            scenarios.validate_mutations(
                ["validator_fail", "validator_fail"], scenario_id="mut_dup"
            )
        self.assertIn("duplicate mutations rejected", str(ctx2.exception))

    # ------------------------------------------------------------------
    # Oracle model
    # ------------------------------------------------------------------
    def test_15_oracle_comparison_kinds_distinct_and_non_deriving(self) -> None:
        kinds = oracles.distinct_comparison_kinds()
        self.assertEqual(len(kinds), 5)
        self.assertIn(oracles.OracleComparisonKind.BYTE_EQUALITY, kinds)
        self.assertIn(oracles.OracleComparisonKind.FILE_SET_EQUALITY, kinds)
        self.assertIn(oracles.OracleComparisonKind.SCHEMA_FIELD_EQUALITY, kinds)
        self.assertIn(oracles.OracleComparisonKind.SEMANTIC_STATUS_EQUALITY, kinds)
        self.assertIn(oracles.OracleComparisonKind.SHA256_EQUALITY, kinds)

        byte_o = oracles.make_oracle_expectation("expected_build_exit_bytes", b"abc")
        self.assertTrue(byte_o.compare(b"abc"))
        self.assertFalse(byte_o.compare(b"abd"))

        files_o = oracles.make_oracle_expectation(
            "expected_evidence_tree_unchanged", ["a.txt", "b.txt"]
        )
        self.assertTrue(files_o.compare(["b.txt", "a.txt"]))

        schema_o = oracles.make_oracle_expectation(
            "expected_host_outcome", {"status": "OK"}
        )
        self.assertTrue(schema_o.compare({"status": "OK"}))

        status_o = oracles.make_oracle_expectation("expected_structural_status", "PASS")
        self.assertTrue(status_o.compare("PASS"))

        hash_o = oracles.make_oracle_expectation("expected_manifest_sha256", "AbC")
        self.assertTrue(hash_o.compare("abc"))

        # Explicit host exit — framework does not recompute from other fields.
        oracles.assert_oracles_do_not_recompute_host_exit(
            0, other_fields={"structural_status": "PASS"}
        )
        with self.assertRaises(scenarios.ScenarioFrameworkError):
            oracles.assert_oracles_do_not_recompute_host_exit(
                None, other_fields={"structural_status": "PASS"}
            )

    # ------------------------------------------------------------------
    # Command shims
    # ------------------------------------------------------------------
    def test_16_prohibited_shims_log_and_fail_without_delegating(self) -> None:
        ws = self._workspace()
        env = ws.bash_env()
        # Invoke docker via PATH-first shim; must fail closed and log (no delegation).
        cp = harness.run_bash(
            ["-c", "set -euo pipefail; docker version; echo REACHABLE=yes"],
            env=env,
            cwd=SCRIPTS_DIR,
        )
        self.assertEqual(cp.returncode, 99)
        self.assertNotIn("REACHABLE=yes", cp.stdout)
        inv = ws.shims.invocations()
        self.assertTrue(any("PROHIBITED docker" in line for line in inv), inv)
        # Cargo similarly.
        cp2 = harness.run_bash(
            ["-c", "set -euo pipefail; cargo --version"],
            env=env,
            cwd=SCRIPTS_DIR,
        )
        self.assertEqual(cp2.returncode, 99)
        self.assertTrue(
            any("PROHIBITED cargo" in line for line in ws.shims.invocations())
        )
        # Product alias shim present.
        self.assertTrue((ws.shims.mock_bin / "xai-grok-pager").is_file())
        self.assertTrue((ws.shims.mock_bin / "xai-grok-pager-bin").is_file())

    def test_17_assert_no_prohibited_when_clean(self) -> None:
        ws = self._workspace()
        ws.shims.assert_no_prohibited_invocations()
        # After an invocation, assert fails.
        harness.run_bash(["-c", "protoc --version"], env=ws.bash_env(), cwd=SCRIPTS_DIR)
        with self.assertRaises(scenarios.ScenarioFrameworkError):
            ws.shims.assert_no_prohibited_invocations()

    # ------------------------------------------------------------------
    # Disposable workspace / residue
    # ------------------------------------------------------------------
    def test_18_workspace_isolated_and_cleanup_succeeds(self) -> None:
        ws = self._workspace()
        self.assertTrue(ws.workspace.name.startswith(harness.TEMP_PREFIX))
        self.assertEqual(ws.workspace.parent, TESTS_DIR)
        self.assertTrue(ws.evidence.is_dir())
        self.assertTrue(ws.home.is_dir())
        self.assertTrue(ws.work_root.is_dir())
        self.assertTrue(ws.source.is_dir())
        self.assertTrue(ws.tmp.is_dir())
        self.assertTrue(ws.captures.is_dir())
        path = ws.workspace
        ws.cleanup()
        self._workspaces.remove(ws)
        self.assertFalse(path.exists())

    def test_19_unexpected_non_test_path_not_silently_deleted(self) -> None:
        foreign = TESTS_DIR / "not_a_phase3g_workspace_marker"
        foreign.mkdir(exist_ok=True)
        try:
            with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx:
                harness.safe_cleanup_workspace(foreign)
            self.assertIn("refusing to delete unexpected non-test path", str(ctx.exception))
            self.assertTrue(foreign.exists())
        finally:
            if foreign.exists():
                foreign.rmdir()

        outside = Path(tempfile.mkdtemp(prefix="phase3g_test_outside_"))
        try:
            with self.assertRaises(scenarios.ScenarioFrameworkError) as ctx2:
                harness.safe_cleanup_workspace(outside)
            self.assertIn("refusing to delete non-test path outside", str(ctx2.exception))
            self.assertTrue(outside.exists())
        finally:
            shutil.rmtree(outside, ignore_errors=True)

    # ------------------------------------------------------------------
    # Sourced-writer adapters
    # ------------------------------------------------------------------
    def test_20_sourced_writer_adapters_locate_functions_without_tools(self) -> None:
        ws = self._workspace()
        adapter = harness.SourcedWriterAdapter(ws)
        cdisc = adapter.discover_container()
        self.assertEqual(cdisc.missing_functions, ())
        self.assertEqual(
            set(cdisc.found_functions), set(harness.CONTAINER_REQUIRED_FUNCTIONS)
        )
        hdisc = adapter.discover_host()
        self.assertEqual(hdisc.missing_functions, ())
        self.assertEqual(set(hdisc.found_functions), set(harness.HOST_REQUIRED_FUNCTIONS))
        self.assertEqual(
            set(hdisc.lifecycle_markers_found), set(harness.HOST_LIFECYCLE_MARKERS)
        )

        cp_c = adapter.smoke_source_container_functions()
        self.assertEqual(cp_c.returncode, 0, cp_c.stderr + cp_c.stdout)
        self.assertIn("CONTAINER_MAIN_TYPE=function", cp_c.stdout)

        cp_h = adapter.smoke_source_host_functions()
        self.assertEqual(cp_h.returncode, 0, cp_h.stderr + cp_h.stdout)
        self.assertIn("HOST_MAIN_TYPE=function", cp_h.stdout)
        ws.shims.assert_no_prohibited_invocations()

    # ------------------------------------------------------------------
    # Real-validator driver
    # ------------------------------------------------------------------
    def test_21_validator_driver_uses_sys_executable_host_preliminary(self) -> None:
        ws = self._workspace()
        driver = harness.RealValidatorDriver(ws)
        self.assertEqual(
            Path(driver.python_executable).resolve(), Path(sys.executable).resolve()
        )
        # Controlled local fixture workspace — framework smoke only, not 3G-B evidence.
        fx.build_and_write(ws.evidence, "success-artifact-present")
        before_files = {p.name: p.read_bytes() for p in ws.evidence.iterdir() if p.is_file()}
        result = driver.run_host_preliminary(ws.evidence)
        self.assertIn("--host-preliminary", result.command)
        self.assertEqual(result.command[0], driver.python_executable)
        self.assertEqual(Path(result.command[1]).name, "validate_witness_evidence.py")
        self.assertTrue(result.stdout_capture_path.is_file())
        self.assertTrue(result.stderr_capture_path.is_file())
        self.assertFalse(harness._is_under(result.stdout_capture_path, ws.evidence))
        self.assertFalse(harness._is_under(result.stderr_capture_path, ws.evidence))
        self.assertEqual(result.stdout_capture_path.parent, ws.captures)
        # Evidence bytes unchanged (driver writes no evidence).
        after_files = {p.name: p.read_bytes() for p in ws.evidence.iterdir() if p.is_file()}
        self.assertEqual(before_files, after_files)
        # Exact command identity available for diagnostics.
        self.assertIsInstance(result.command, tuple)
        self.assertGreaterEqual(len(result.command), 4)

    # ------------------------------------------------------------------
    # Full-main harness preparation (no execution)
    # ------------------------------------------------------------------
    def test_22_full_main_prep_does_not_execute_real_workflow(self) -> None:
        ws = self._workspace()
        prep_harness = harness.FullMainHarness(ws)
        prep = prep_harness.prepare()
        self.assertEqual(prep.main_entry_point, harness.HOST_SCRIPT)
        self.assertEqual(prep.main_function_name, "run_witness_narrow_build_main")
        self.assertFalse(prep.execute_authorized)
        self.assertTrue(prep.shim_path_prefix)
        self.assertTrue(prep.work_root.is_dir())
        self.assertTrue(prep.source_root.is_dir())
        prep_harness.assert_not_executed(prep)
        # Ensure prohibited tools remain shimmed and unused.
        for name in ("docker", "cargo", "rustc", "xai-grok-pager"):
            self.assertTrue((ws.shims.mock_bin / name).is_file())
        ws.shims.assert_no_prohibited_invocations()

    def test_23_no_real_prohibited_workflow_in_framework_suite(self) -> None:
        # Meta-safety: suite itself must leave no prohibited invocation residue
        # from this test's workspace, and interpreter binding must be sys.executable.
        ws = self._workspace()
        self.assertEqual(
            Path(harness.RealValidatorDriver(ws).python_executable).resolve(),
            Path(sys.executable).resolve(),
        )
        # command -v python3 is not used by the harness driver path.
        src = Path(harness.__file__).read_text(encoding="utf-8")
        self.assertNotIn("command -v python3", src)
        self.assertIn("sys.executable", src)
        ws.shims.assert_no_prohibited_invocations()


if __name__ == "__main__":
    unittest.main()
