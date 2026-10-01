"""Process runner and trust-boundary tests for WVMA-V1 Batch A2."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from wvma_v1.canonical import canonical_bytes
from wvma_v1.runner import (
    InvocationContract,
    RunnerError,
    run_baseline,
    run_mutation_case,
    runner_module_origin,
)
from wvma_v1.target_launcher import module_origin as launcher_origin
from wvma_v1.workspace import create_disposable_root


def _make_dir_alias(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (OSError, NotImplementedError):
        pass
    if os.name == "nt":
        cp = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            shell=False,
        )
        if cp.returncode == 0:
            return
    raise unittest.SkipTest("symlink/junction unavailable")


class TestRunner(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="wvma-run-")
        self.active = Path(__file__).resolve().parents[2]
        self.disp = create_disposable_root(
            parent=Path(self._tmpdir.name),
            prefix="ws-",
            active_repository=self.active,
        )
        syn = self.disp / "synthetic"
        syn.mkdir()
        (syn / "artifact.json").write_bytes(
            canonical_bytes({"status": "accepted", "n": 1})
        )

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_baseline_success_and_trusted_origins(self):
        receipt = run_baseline(
            workspace_root=self.disp,
            contract=InvocationContract(invocation_id="synthetic.verify"),
            active_repository=self.active,
        )
        self.assertEqual(receipt.exit_code, 0)
        self.assertFalse(receipt.timed_out)
        self.assertTrue(receipt.verify_ok_claimed)
        self.assertEqual(
            Path(receipt.launcher_module_origin).resolve(),
            Path(launcher_origin()).resolve(),
        )
        self.assertEqual(
            Path(receipt.runner_module_origin).resolve(),
            Path(runner_module_origin()).resolve(),
        )
        # Trusted modules must not live inside disposable workspace.
        for origin in (
            receipt.launcher_module_origin,
            receipt.runner_module_origin,
        ):
            with self.assertRaises(ValueError):
                Path(origin).resolve().relative_to(self.disp.resolve())

    def test_mutation_case_rejects_bad_status(self):
        (self.disp / "synthetic" / "artifact.json").write_bytes(
            canonical_bytes({"status": "BAD", "n": 1})
        )
        receipt = run_mutation_case(
            workspace_root=self.disp,
            contract=InvocationContract(invocation_id="synthetic.verify"),
            require_target_relative_path="synthetic/artifact.json",
        )
        self.assertEqual(receipt.exit_code, 1)
        self.assertIs(receipt.verify_ok_claimed, False)
        # Target may self-claim DETECTED; runner records but does not authorize.
        self.assertEqual(receipt.self_claimed_result, "DETECTED")

    def test_rejects_arbitrary_invocation_id(self):
        with self.assertRaises(RunnerError):
            InvocationContract(invocation_id="rm -rf /")

    def test_shell_false_and_absolute_python(self):
        receipt = run_baseline(
            workspace_root=self.disp,
            contract=InvocationContract(invocation_id="synthetic.canary_pass"),
        )
        self.assertTrue(Path(receipt.python_executable).is_absolute())
        self.assertEqual(receipt.argv[0], receipt.python_executable)
        self.assertIn("-B", receipt.argv)
        payload = json.loads(receipt.stdout_text_preview.strip().splitlines()[0])
        self.assertEqual(payload["invocation_id"], "synthetic.canary_pass")

    def test_output_root_overlap_rejected(self):
        with self.assertRaises(RunnerError):
            run_baseline(
                workspace_root=self.disp,
                contract=InvocationContract(invocation_id="synthetic.verify"),
                output_root=self.active / "wvma_v1",
                protected_paths=[self.active],
                active_repository=self.active,
            )

    def test_workspace_alias_rejected(self):
        alias = Path(self._tmpdir.name) / "ws_alias"
        _make_dir_alias(alias, self.disp)
        with self.assertRaises(RunnerError):
            run_baseline(
                workspace_root=alias,
                contract=InvocationContract(invocation_id="synthetic.verify"),
                active_repository=self.active,
            )


if __name__ == "__main__":
    unittest.main()
