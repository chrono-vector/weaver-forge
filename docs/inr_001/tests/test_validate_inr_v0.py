"""INR-001 v0 regression tests (r3): supervisor process boundary.

Fresh PASS-capable results exist only as the report of a trusted supervisor process
(``supervisor_inr_v0``) launched by ``capture_inr_v0`` and bound to that process.
No test constructs PASS-capable evidence; every adversarial path must end non-PASS.
Live tests read the local repository through the pinned Git only (read-only Git
commands) and write ledgers/staging/exports to ``inr001_r3_t_*`` temporary dirs.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inr_r3_support as s  # noqa: E402
from docs.inr_001 import capture_inr_v0 as capture  # noqa: E402
from docs.inr_001 import input_cases, ledger  # noqa: E402
from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001 import validate_inr_v0 as verifier  # noqa: E402
from docs.inr_001.schema_check import check  # noqa: E402

# Predicates a real supervisor process run on this machine must establish. Python
# runtime (3.14 != frozen 3.11) and target HEAD are environment facts and stay BLOCKED.
LOCAL_BOUND = ("supervisor_process", "profile_pinned", "event_challenge", "git_runtime",
               "child_launched", "child_provenance", "argv_exact", "capture_complete",
               "mandatory_cases_executed", "module_identity", "refusal_semantics")
FAKE_CLAIMS = {"INR_IS_NON_ORIGIN": "true", "IS_NON_ORIGIN": "PASS", "INR_ALL_WRITER_ISOLATION": "ESTABLISHED",
               "INR_SHARED_STATE": "NONE", "INR_TRUSTED_EVIDENCE": "PASS"}


@unittest.skipUnless(s.LIVE, "pinned Git / target repository unavailable")
class LiveSupervisorProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = s.tempdir()
        cls.ledger = cls.tmp / "ledger.jsonl"
        cls.report, cls.rc, cls.export = s.run_supervisor_process("EV-R3-LIVE-1", cls.tmp, ledger=cls.ledger,
                                                                  env=FAKE_CLAIMS)

    @classmethod
    def tearDownClass(cls):
        s.rmtree(cls.tmp)

    def test_supervisor_process_boundary_established(self):
        self.assertEqual(self.report["result_kind"], "FRESH_SUPERVISOR_RUN", self.report)
        self.assertEqual(self.report["predicates"]["supervisor_process"], "PASS", self.report)
        self.assertNotEqual(self.report["supervisor_pid"], os.getpid())
        self.assertTrue(self.export["supervisor"]["is_supervisor_process"])
        self.assertEqual((self.export["supervisor"]["isolated"], self.export["supervisor"]["no_site"]), (1, 1))

    def test_real_children_are_launched_and_bound(self):
        for name in LOCAL_BOUND:
            self.assertEqual(self.report["predicates"][name], "PASS", (name, self.report))
        self.assertEqual(len(self.export["capture_records"]), len(s.profile()["required_cases"]))
        for rec in self.export["capture_records"]:
            self.assertGreater(rec["child_pid"], 0)
            self.assertNotIn(rec["child_pid"], (os.getpid(), self.report["supervisor_pid"]))
            self.assertEqual(rec["argv"], rec["popen_args"])
            self.assertEqual(rec["argv"][1:4], ["-I", "-S", "-B"])
            self.assertEqual(rec["env_git"], [["GIT_NO_REPLACE_OBJECTS", "1"]])
            self.assertEqual(s.child_report(rec)["challenge"], self.export["challenge"])

    def test_overall_never_pass_and_external_unconfirmed(self):
        s.not_pass(self, self.report)
        self.assertEqual(self.rc, 1)
        for name in s.EXTERNAL:  # fake environment claims are ignored
            self.assertEqual(self.report["predicates"][name], "UNCONFIRMED")

    def test_every_negative_control_hits_its_exact_refusal(self):
        for spec in s.profile()["required_cases"]:
            rec = s.record(self.export, spec["case_id"])
            self.assertEqual(s.child_report(rec)["errors"], spec["expected_errors"], spec["case_id"])
            self.assertIn(rec["return_code"], spec["accepted_return_codes"], spec["case_id"])

    def test_split_human_final_and_production_nonclaim_cases(self):
        self.assertEqual(s.child_report(s.record(self.export, s.HF))["errors"],
                         ["source_records[1] does not resolve to an accepted Human Final record"])
        self.assertEqual(s.child_report(s.record(self.export, s.PN))["errors"],
                         ["required nonclaims are missing: does_not_grant_production_permission"])

    def test_export_schema_valid_and_recheck_is_informational(self):
        self.assertEqual(check(self.export, verifier.load_schema()), [])
        result = verifier.recheck_export(self.export, ledger_path=self.ledger)
        self.assertFalse(any(m.startswith(("schema:", "ledger: export")) for m in result["fail"]), result)
        self.assertEqual(result["result_kind"], "INFORMATIONAL_RECHECK")
        self.assertFalse(result["fresh_pass_capable"])
        s.not_pass(self, result)

    def test_forged_export_pass_claims_rejected_by_recheck(self):
        forged = copy.deepcopy(self.export)
        forged["verification"].update(derived_result="PASS", pass_allowed=True, local_controls_result="PASS")
        forged["verification"]["predicates"] = {k: "PASS" for k in forged["verification"]["predicates"]}
        result = verifier.recheck_export(forged, ledger_path=self.ledger)
        self.assertEqual(result["derived_result"], "FAIL")
        s.not_pass(self, result)
        forged["is_non_origin"] = True
        s.not_pass(self, verifier.recheck_export(forged, ledger_path=self.ledger))

    def test_event_id_replay_rejected_by_supervisor_process(self):
        tmp = self.tmp / "replay"
        tmp.mkdir()
        report, _, export = s.run_supervisor_process("EV-R3-LIVE-1", tmp, ledger=self.ledger)
        self.assertIsNone(export)
        self.assertEqual(report["predicates"]["event_challenge"], "FAIL", report)
        s.not_pass(self, report)
        kinds = [e["kind"] for e in ledger.read_entries(self.ledger) if e["event_id"] == "EV-R3-LIVE-1"]
        self.assertIn("REJECTED", kinds)

    def test_challenge_reuse_rejected(self):
        with mock.patch.object(sup.secrets, "token_hex", return_value=self.export["challenge"]):
            result, export = sup.supervise("EV-R3-CHALLENGE-REUSE", s.REPO, ledger_path=self.ledger,
                                           work_dir=self.tmp)
        self.assertIsNone(export)
        self.assertEqual(result["predicates"]["event_challenge"], "FAIL")
        s.not_pass(self, result)

    def test_argv_mismatch_rejected(self):
        original = sup._command_argv

        def drop_site_flag(command, values):
            return [part for part in original(command, values) if part != "-S"]

        with mock.patch.object(sup, "_command_argv", drop_site_flag):
            result, _ = sup.supervise("EV-R3-ARGV", s.REPO, ledger_path=self.ledger, work_dir=self.tmp)
        self.assertEqual(result["predicates"]["argv_exact"], "FAIL", result)
        s.not_pass(self, result)
        self.assertNotEqual(result["local_controls_result"], "PASS")


class LauncherTests(unittest.TestCase):
    def test_supervisor_command_has_only_non_trust_parameters(self):
        command = capture.supervisor_command("EV", s.REPO, s.REPO / "x.json", ledger=s.REPO / "l", work_dir=s.REPO)
        self.assertEqual(command[1:5], ["-I", "-S", "-B", str(sup.SUPERVISOR)])
        self.assertTrue(Path(command[0]).is_absolute() and Path(command[4]).is_absolute())
        options = [part for part in command if part.startswith("--")]
        self.assertEqual(options, ["--event-id", "--repository", "--out", "--ledger", "--work-dir"])

    def test_launcher_rejects_report_not_bound_to_its_child(self):
        def forged_supervisor(report, pid, returncode):
            class ForgedSupervisor:
                def __init__(self, *args, **kwargs):
                    self.pid, self.returncode = pid, returncode

                def communicate(self, timeout=None):
                    return json.dumps(report).encode(), b""
            return ForgedSupervisor

        forged = {"derived_result": "PASS", "pass_allowed": True, "local_controls_result": "PASS",
                  "event_id": "EV-FORGED", "supervisor_pid": os.getpid()}  # e.g. an in-process report
        tmp = s.tempdir()
        try:
            for fake, why in ((forged_supervisor(forged, 999999, 0), "pid not bound to the launched child"),
                              (forged_supervisor(dict(forged, supervisor_pid=999999), 999999, 1),
                               "exit status contradicts PASS"),
                              (forged_supervisor(dict(forged, supervisor_pid=999999, event_id="OTHER"), 999999, 0),
                               "event not bound")):
                with mock.patch.object(capture.subprocess, "Popen", fake):
                    report, _ = capture.launch_supervisor("EV-FORGED", s.REPO, tmp / "o.json")
                s.not_pass(self, report)
                self.assertEqual(report["result_kind"], "LAUNCHER_BINDING_FAILURE", why)
        finally:
            s.rmtree(tmp)

    def test_cli_has_no_evidence_option(self):
        tmp = s.tempdir()
        try:
            for option in ("--evidence", "--snapshot", "--capture", "--report", "--provenance"):
                with self.assertRaises(SystemExit) as caught, mock.patch("sys.stderr"):
                    capture.main(["--event-id", "E", "--repository", str(s.REPO), "--out", str(tmp / "o"),
                                  option, "x"])
                self.assertEqual(caught.exception.code, 2)
                with self.assertRaises(SystemExit) as caught, mock.patch("sys.stderr"):
                    sup.main(["--event-id", "E", "--repository", str(s.REPO), "--out", str(tmp / "o"),
                              option, "x"])
                self.assertEqual(caught.exception.code, 2)
            self.assertEqual(list(tmp.iterdir()), [])
        finally:
            s.rmtree(tmp)


class RefusalSemanticsTests(unittest.TestCase):
    def test_profile_binds_exact_refusals(self):
        for spec in s.profile()["required_cases"]:
            if spec["expected_classification"] == "PASS":
                self.assertEqual(spec["expected_errors"], [])
            else:
                self.assertTrue(spec["expected_errors"], spec["case_id"])
                self.assertTrue(spec["intended_refusal"])
                self.assertEqual(spec["accepted_return_codes"], [2])

    def test_wrong_reason_rejection_is_not_an_expected_refusal(self):
        for spec in s.profile()["required_cases"]:
            if spec["expected_classification"] == "FAIL":
                self.assertTrue(sup.refusal_problems(spec, ["some unrelated error"]))
                self.assertTrue(sup.refusal_problems(spec, []))
                self.assertTrue(sup.refusal_problems(spec, spec["expected_errors"] + ["extra"]))
            else:
                self.assertTrue(sup.refusal_problems(spec, ["any error"]))
            self.assertEqual(sup.refusal_problems(spec, list(spec["expected_errors"])), [])

    @unittest.skipUnless(s.LIVE, "pinned Git / target repository unavailable")
    def test_old_top_level_human_final_input_is_wrong_reason(self):
        """The pre-r2 top-level mutation is refused only by the generic schema rule."""
        value = json.loads(s.pinned_bytes("docs/portfolio_state/portfolio_state_v0.example.json"))
        value["human_final"], value["production_permission"] = "INFERRED", "GRANTED"
        rc, errors = s.run_pinned_probe(json.dumps(value).encode())
        self.assertEqual(rc, 2)  # rc=2 alone must not count
        self.assertEqual(errors, ["top-level fields do not match the closed PSM-v0 schema"])
        self.assertTrue(sup.refusal_problems(s.spec(s.HF), errors))
        self.assertTrue(sup.refusal_problems(s.spec(s.PN), errors))

    @unittest.skipUnless(s.LIVE, "pinned Git / target repository unavailable")
    def test_closed_inputs_keep_top_level_key_set(self):
        raw = s.pinned_bytes("docs/portfolio_state/portfolio_state_v0.example.json")
        for spec in s.profile()["required_cases"]:
            if spec["case_id"] == "PSM_NEG_MUTATED_ARCHIVE_OR_INPUT":
                continue
            self.assertEqual(set(input_cases.case_value(spec["case_id"], raw)), set(json.loads(raw)))
            self.assertEqual(sup.digest(input_cases.case_bytes(spec["case_id"], raw)), spec["input_digest"])


class SchemaTests(unittest.TestCase):
    def test_stale_99418b4_event_fails(self):
        stale = {"schema_version": "inr.event.v0", "inr_event_id": "EV1", "target_sha": sup.TARGET_SHA,
                 "trusted_challenge_record": {"generated_by": "capture_inr_v0", "single_use": True},
                 "byte_identity_evidence": {"measured_by": "capture_inr_v0"},
                 "non_origin_evidence": {"runner_class": "FRESH_HOSTED_RUNNER"},
                 "capture_records": [], "case_result_bindings": [], "final_result": "PASS"}
        result = verifier.recheck_export(stale, ledger_path=s.ABSENT_LEDGER)
        self.assertEqual(result["derived_result"], "FAIL")
        self.assertTrue(any(m.startswith("schema:") for m in result["fail"]))
        s.not_pass(self, result)

    def test_stale_r2_event_fails(self):
        stale = s.synthetic_export("EV-R2", "a" * 64, "b" * 64)
        stale["schema_version"] = "inr.event.v0.r2"
        stale["blocked_reasons"], stale["failure_reasons"] = [], []
        result = verifier.recheck_export(stale, ledger_path=s.ABSENT_LEDGER)
        self.assertEqual(result["derived_result"], "FAIL")
        s.not_pass(self, result)

    def test_synthetic_export_is_schema_valid_but_not_recorded(self):
        forged = s.synthetic_export("EV-SYN", "a" * 64, "b" * 64)
        self.assertEqual(check(forged, verifier.load_schema()), [])
        result = verifier.recheck_export(forged, ledger_path=s.ABSENT_LEDGER)
        self.assertEqual(result["derived_result"], "FAIL")
        s.not_pass(self, result)

    def test_profile_origin_conform_and_digest_is_pinned(self):
        profile, _ = sup.configuration()
        raw = json.loads((sup.ROOT / "profiles/psm_001_inr_target_profile_v0.json").read_bytes())
        body = {k: v for k, v in raw.items() if k != "target_profile_digest"}
        self.assertEqual(sup.digest(sup.canonical(body)), sup.PROFILE_DIGEST)
        self.assertEqual(raw["target_profile_digest"], sup.PROFILE_DIGEST)
        self.assertNotEqual(sup.PROFILE_DIGEST, "bae309aa9a8f04f64990359d75f1e262945b8bf68149229f1a3023de207dc4ca")
        self.assertEqual({tuple(c["argv"]) for c in profile["command_inventory"]}, {sup.ARGV_TEMPLATE})


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = s.tempdir()
        self.path = self.tmp / "ledger.jsonl"

    def tearDown(self):
        s.rmtree(self.tmp)

    def test_reserve_complete_and_replay(self):
        first = ledger.reserve(self.path, "E1", "c1")
        ledger.complete(self.path, "E1", "c1", {"derived_result": "UNCONFIRMED"})
        with self.assertRaises(ledger.LedgerError):
            ledger.reserve(self.path, "E1", "c2")
        with self.assertRaises(ledger.LedgerError):
            ledger.reserve(self.path, "E2", "c1")
        with self.assertRaises(ledger.LedgerError):
            ledger.complete(self.path, "E1", "c1", {})
        entries = ledger.read_entries(self.path)
        self.assertEqual([e["kind"] for e in entries], ["RESERVED", "COMPLETED", "REJECTED", "REJECTED"])
        self.assertEqual(entries[1]["prev_entry_sha256"], first["entry_sha256"])

    def test_tampered_ledger_fails_closed(self):
        ledger.reserve(self.path, "E1", "c1")
        ledger.reserve(self.path, "E2", "c2")
        lines = self.path.read_bytes().split(b"\n")
        lines[0] = lines[0].replace(b"E1", b"E9")
        self.path.write_bytes(b"\n".join(lines))
        with self.assertRaises(ledger.LedgerError):
            ledger.read_entries(self.path)
        with self.assertRaises(ledger.LedgerError):
            ledger.reserve(self.path, "E3", "c3")

    def test_truncated_ledger_fails_closed_via_head_record(self):
        ledger.reserve(self.path, "E1", "c1")
        ledger.complete(self.path, "E1", "c1", {"derived_result": "UNCONFIRMED"})
        lines = [line for line in self.path.read_bytes().split(b"\n") if line]
        self.path.write_bytes(lines[0] + b"\n")  # drop the newest entry (valid chain prefix)
        with self.assertRaises(ledger.LedgerError):
            ledger.read_entries(self.path)
        with self.assertRaises(ledger.LedgerError):
            ledger.reserve(self.path, "E1", "c9")  # event ID reuse after truncation is refused

    def test_deleted_ledger_with_head_fails_closed(self):
        ledger.reserve(self.path, "E1", "c1")
        self.path.unlink()
        with self.assertRaises(ledger.LedgerError):
            ledger.reserve(self.path, "E1", "c2")

    def test_ledger_without_head_record_fails_closed(self):
        ledger.reserve(self.path, "E1", "c1")
        ledger.head_path(self.path).unlink()
        with self.assertRaises(ledger.LedgerError):
            ledger.read_entries(self.path)

    def test_documented_limitation_both_deleted_is_a_fresh_ledger(self):
        """Not tamper evidence: deleting ledger AND head is indistinguishable from fresh."""
        ledger.reserve(self.path, "E1", "c1")
        self.path.unlink()
        ledger.head_path(self.path).unlink()
        self.assertEqual(ledger.read_entries(self.path), [])
        self.assertEqual(ledger.reserve(self.path, "E1", "c2")["seq"], 1)

    def test_ledger_location_is_outside_worktree(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.resolve_path(sup.ROOT / "ledger.jsonl")
        default = ledger.resolve_path(None)
        self.assertNotIn(s.REPO.resolve(), default.parents)


if __name__ == "__main__":
    unittest.main()
