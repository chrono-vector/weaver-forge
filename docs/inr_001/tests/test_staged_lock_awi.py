"""INR-AWI-001: the supervisor PROCESS write-excludes its staged execution objects.

A real supervisor process run (launcher -> isolated supervisor -> real children) must
record its own observation of the staged-object lock: on Windows every staged object
(staging directory = child cwd, staged validator, staged case inputs) and every ancestor
of the staging directory held, every write/delete/re-ACL open-only probe denied at
freeze and after execution, trusted digests, unchanged identity and listing, released
after the post measurement and cleaned up. The record is checked with the XR adapter
rule. The lock changes no INR predicate: ``all_writer_isolation`` stays UNCONFIRMED.
Temporary directories use the ``inr001_r3_t_`` prefix (``inr_r3_support``).
"""
from __future__ import annotations

from pathlib import Path
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inr_r3_support as s  # noqa: E402
from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001.xr import validate_external_run_v0 as xr  # noqa: E402


def expected_staged(export):
    """Runtime-derived staged objects of a supervisor export (cwd and executed argv)."""
    t = xr.trusted_configuration()
    records = export["capture_records"]
    cwd = xr._norm(records[0]["cwd"])
    expected = {"execution_cwd": {xr._key(cwd): (cwd, "dir", "")}, "staged_validator": {}, "case_inputs": {}}
    for case, record in zip(t["cases"], records):
        validator, case_input = xr._norm(record["argv"][5]), xr._norm(record["argv"][6])
        expected["staged_validator"][xr._key(validator)] = (validator, "file",
                                                            t["target_file_digests"][xr.VALIDATOR_FILE])
        expected["case_inputs"][xr._key(case_input)] = (case_input, "file", case["input_digest"])
    return expected


@unittest.skipUnless(s.LIVE, "pinned Git / target repository unavailable")
class SupervisorStagedLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = s.tempdir()
        cls.report, cls.rc, cls.export = s.run_supervisor_process("EV-AWI-LOCK-1", cls.tmp,
                                                                  ledger=cls.tmp / "ledger.jsonl")
        cls.lock = cls.export["measurements"]["staged_lock"]

    @classmethod
    def tearDownClass(cls):
        s.rmtree(cls.tmp)

    @unittest.skipUnless(os.name == "nt", "the staged-object lock is a Windows mechanism")
    def test_supervisor_process_records_its_own_held_lock(self):
        lock = self.lock
        self.assertEqual(self.report["result_kind"], "FRESH_SUPERVISOR_RUN", self.report)
        self.assertEqual((lock["platform"], lock["mechanism"], lock["problems"]),
                         ("nt", sup.STAGED_LOCK_MECHANISM, []))
        self.assertEqual(len(lock["objects"]), 2 + len(s.profile()["required_cases"]))
        for item in lock["objects"]:
            self.assertTrue(item["held"] and item["dacl_applied"], item)
        for item in lock["objects"] + lock["ancestors"]:
            self.assertTrue(item["held"], item)
            for phase in ("freeze", "post"):
                self.assertTrue(item[phase]["probes"] and all(v in ("DENIED:5", "DENIED:32")
                                                              for v in item[phase]["probes"].values()), item)
        self.assertEqual(xr.staged_lock_problems(lock, expected_staged(self.export), self.export["lifecycle"]), [])
        # released and cleaned up: no staging directory survives the run
        self.assertEqual(list(self.tmp.glob("inr-local-*")), [])

    def test_lock_changes_no_inr_predicate(self):
        self.assertEqual(self.report["predicates"]["all_writer_isolation"], "UNCONFIRMED")
        self.assertIn("all_writer_isolation: read-only staging does not establish all-writer immutability",
                      self.report["unconfirmed"])
        s.not_pass(self, self.report)

    def test_platform_without_lock_records_absence_and_stays_unconfirmed(self):
        stage = self.tmp / "nolock-stage"
        stage.mkdir()
        with mock.patch.object(sup.os, "name", "posix"):
            record = sup._StagedLock(stage, []).freeze()
        self.assertEqual((record["mechanism"], record["objects"], record["ancestors"]), ("none", [], []))
        problems = xr.staged_lock_problems(record, expected_staged(self.export), self.export["lifecycle"])
        self.assertEqual([level for level, _ in problems], ["unconfirmed"])
        self.assertIn("no supervisor write-exclusion lock on this platform", problems[0][1])


if __name__ == "__main__":
    unittest.main()
