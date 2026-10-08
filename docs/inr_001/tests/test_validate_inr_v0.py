"""INR-001 v0 regression tests (r2).

The 99418b4 pattern (a synthetic, hand-written event asserted to PASS) is removed.
No test here constructs PASS-capable evidence; every adversarial path must end in
a non-PASS result, and the only evidence objects are minted by real child launches.
Live tests read the local repository through the pinned Git only (read-only Git
commands) and write the ledger and staging files to a temporary directory.
"""
from __future__ import annotations

import base64
import copy
import inspect
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import weakref

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from docs.inr_001 import input_cases, ledger  # noqa: E402
from docs.inr_001 import trusted_capture as tc  # noqa: E402
from docs.inr_001 import validate_inr_v0 as verifier  # noqa: E402
from docs.inr_001.schema_check import check  # noqa: E402

HF = "PSM_NEG_HUMAN_FINAL_PRODUCTION_INFERENCE"
# Never created: read-only lookups of a missing ledger see an empty ledger.
_ABSENT_LEDGER = Path(tempfile.gettempdir()) / "inr001_impl_absent" / "ledger.jsonl"
EXTERNAL = ("non_origin", "shared_state_absence", "all_writer_isolation")


def _rmtree(path):
    def onexc(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=onexc)
    else:  # pragma: no cover
        shutil.rmtree(path, onerror=lambda f, p, e: onexc(f, p, e))


def _tempdir():
    return Path(tempfile.mkdtemp(prefix="inr001_impl_t_"))


def _live_available():
    try:
        tc.probe_git(REPO)
        return True
    except (OSError, ValueError, subprocess.SubprocessError):
        return False


LIVE = _live_available()


def _profile():
    return tc.configuration()[0]


def _spec(case_id):
    return next(c for c in _profile()["required_cases"] if c["case_id"] == case_id)


def _not_pass(test, result):
    test.assertFalse(result["pass_allowed"], result)
    test.assertNotEqual(result["derived_result"], "PASS", result)


def _record(export, case_id):
    return next(r for r in export["capture_records"] if r["case_id"] == case_id)


def _report(record):
    return json.loads(base64.b64decode(record["stdout_base64"]))


@unittest.skipUnless(LIVE, "pinned Git / target repository unavailable")
class LiveCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = _tempdir()
        cls.ledger = cls.tmp / "ledger.jsonl"
        fake_claims = {"INR_IS_NON_ORIGIN": "true", "IS_NON_ORIGIN": "PASS",
                       "INR_ALL_WRITER_ISOLATION": "ESTABLISHED", "INR_SHARED_STATE": "NONE"}
        with mock.patch.dict(os.environ, fake_claims):
            cls.result, cls.export = tc._run_and_verify(REPO, "EV-LIVE-1", ledger_path=cls.ledger,
                                                        work_dir=cls.tmp)

    @classmethod
    def tearDownClass(cls):
        _rmtree(cls.tmp)

    def run_event(self, event_id):
        return tc._run_and_verify(REPO, event_id, ledger_path=self.ledger, work_dir=self.tmp)

    def test_real_child_execution_binds_evidence(self):
        components = self.result["components"]
        for name in ("trusted_configuration", "challenge_ledger", "git_runtime",
                     "child_execution_binding", "argv_binding", "module_identity",
                     "refusal_semantics"):
            self.assertEqual(components[name], "PASS", (name, self.result))
        self.assertEqual(len(self.export["capture_records"]), 10)
        for record in self.export["capture_records"]:
            self.assertGreater(record["child_pid"], 0)
            self.assertEqual(record["argv"], record["popen_args"])
            self.assertEqual(record["argv"][1:4], ["-I", "-S", "-B"])
            self.assertEqual(record["env_git"], [["GIT_NO_REPLACE_OBJECTS", "1"]])
        _not_pass(self, self.result)  # v0: external assurance is always UNCONFIRMED

    def test_fake_is_non_origin_is_ignored(self):
        # setUpClass ran with INR_IS_NON_ORIGIN/IS_NON_ORIGIN asserted in the environment
        self.assertEqual(self.result["components"]["non_origin"], "UNCONFIRMED")
        self.assertEqual(inspect.signature(verifier._assess_non_origin).parameters, {})
        forged = copy.deepcopy(self.export)
        forged["is_non_origin"] = True
        forged["non_origin_evidence"] = {"runner_class": "FRESH_HOSTED_RUNNER"}
        _not_pass(self, verifier.recheck_export(forged, ledger_path=self.ledger))

    def test_fake_all_writer_isolation_is_ignored(self):
        self.assertEqual(self.result["components"]["all_writer_isolation"], "UNCONFIRMED")
        self.assertEqual(self.result["components"]["shared_state_absence"], "UNCONFIRMED")
        self.assertEqual(inspect.signature(verifier._assess_all_writer_isolation).parameters, {})
        forged = copy.deepcopy(self.export)
        forged["verification"]["components"]["all_writer_isolation"] = "PASS"
        forged["verification"]["components"]["non_origin"] = "PASS"
        forged["verification"]["derived_result"] = "PASS"
        forged["verification"]["pass_allowed"] = True
        result = verifier.recheck_export(forged, ledger_path=self.ledger)
        _not_pass(self, result)
        self.assertEqual(result["derived_result"], "FAIL")

    def test_human_final_case_hits_intended_refusal(self):
        record = _record(self.export, HF)
        self.assertEqual(record["return_code"], 2)
        self.assertEqual(_report(record)["errors"], [
            "source_records[1] does not resolve to an accepted Human Final record",
            "required nonclaims are missing: does_not_create_human_final, "
            "does_not_grant_production_permission"])
        self.assertEqual(_report(record)["errors"], _spec(HF)["expected_errors"])

    def test_every_negative_control_hits_its_exact_refusal(self):
        for spec in _profile()["required_cases"]:
            self.assertEqual(_report(_record(self.export, spec["case_id"]))["errors"],
                             spec["expected_errors"], spec["case_id"])

    def test_valid_new_schema_event_passes_schema(self):
        self.assertEqual(check(self.export, verifier.load_schema()), [])
        result = verifier.recheck_export(self.export, ledger_path=self.ledger)
        self.assertFalse(any(m.startswith(("schema:", "ledger: export")) for m in result["fail"]), result)
        _not_pass(self, result)  # disk exports are never PASS-capable

    def test_challenge_reuse_event_id_rejected(self):
        result, export = self.run_event("EV-LIVE-1")
        self.assertIsNone(export)
        self.assertEqual(result["components"]["challenge_ledger"], "FAIL")
        _not_pass(self, result)
        kinds = [e["kind"] for e in ledger.read_entries(self.ledger) if e["event_id"] == "EV-LIVE-1"]
        self.assertIn("REJECTED", kinds)

    def test_challenge_reuse_same_challenge_rejected(self):
        with mock.patch.object(tc.secrets, "token_hex", return_value=self.export["challenge"]):
            result, export = self.run_event("EV-CHALLENGE-REUSE")
        self.assertIsNone(export)
        self.assertEqual(result["components"]["challenge_ledger"], "FAIL")
        _not_pass(self, result)

    def test_historical_output_replay_rejected(self):
        historical = {r["case_id"]: base64.b64decode(r["stdout_base64"])
                      for r in self.export["capture_records"]}
        real = subprocess.Popen.communicate
        probe = str(tc.PROBE.resolve())

        def replaying(popen, *args, **kwargs):
            out, err = real(popen, *args, **kwargs)
            argv = list(popen.args) if isinstance(popen.args, (list, tuple)) else []
            if probe in argv:
                return historical[Path(argv[-2]).stem], err
            return out, err

        with mock.patch.object(subprocess.Popen, "communicate", replaying):
            result, export = self.run_event("EV-REPLAY")
        self.assertEqual(result["components"]["child_execution_binding"], "FAIL", result)
        self.assertTrue(any("replay" in m for m in result["fail"]), result)
        _not_pass(self, result)

    def test_argv_mismatch_rejected(self):
        original = tc._capture_argv

        def drop_site_flag(command, values):
            return [part for part in original(command, values) if part != "-S"]

        with mock.patch.object(tc, "_capture_argv", drop_site_flag):
            result, export = self.run_event("EV-ARGV")
        self.assertEqual(result["components"]["argv_binding"], "FAIL", result)
        _not_pass(self, result)

    def test_no_child_process_rejected(self):
        real_popen = subprocess.Popen
        probe = str(tc.PROBE.resolve())
        canned = _record(self.export, "PSM_POSITIVE_ACCEPTED_RECORD")

        class NoChildPopen(real_popen):
            def __init__(self, args, **kwargs):
                if probe in list(args):
                    self._child_created = False
                    self.args, self.pid, self.returncode = args, 4242, 0
                    self.stdout = self.stderr = self.stdin = None
                    return
                super().__init__(args, **kwargs)

            def communicate(self, *a, **k):
                if self.pid == 4242:
                    return base64.b64decode(canned["stdout_base64"]), b""
                return super().communicate(*a, **k)

        with mock.patch.object(subprocess, "Popen", NoChildPopen):
            result, export = self.run_event("EV-NO-CHILD")
        self.assertEqual(export["capture_records"], [])
        self.assertNotEqual(result["components"]["child_execution_binding"], "PASS")
        self.assertTrue(any("not a real subprocess.Popen" in m for m in result["blocked"]), result)
        _not_pass(self, result)

    def test_synthetic_snapshot_injection_rejected(self):
        self.assertFalse(hasattr(tc, "_SESSIONS"))
        self.assertFalse(hasattr(tc, "consume"))
        # A synthetic session built from the real export (plain records, real values).
        session = {"event_id": "EV-LIVE-1", "challenge": self.export["challenge"],
                   "ledger_path": str(self.ledger),
                   "ledger_reservation_entry_sha256": self.export["ledger_reservation_entry_sha256"],
                   "lifecycle": dict(self.export["lifecycle"]), "git": dict(self.export["git_probe"]),
                   "measurements": dict(self.export["measurements"]),
                   "evidence": copy.deepcopy(self.export["capture_records"]),
                   "blocked_reasons": [], "failure_reasons": [], "stage": self.tmp}
        result = verifier._verify_live(session)
        self.assertNotEqual(result["components"]["child_execution_binding"], "PASS")
        self.assertEqual(result["components"]["challenge_ledger"], "FAIL")  # already completed
        _not_pass(self, result)
        # A schema-valid export relabelled as a new event is not in the ledger.
        relabelled = copy.deepcopy(self.export)
        relabelled["inr_event_id"] = "EV-SYNTHETIC"
        result = verifier.recheck_export(relabelled, ledger_path=self.ledger)
        self.assertEqual(result["derived_result"], "FAIL")
        _not_pass(self, result)

    def test_forged_capture_record_rejected(self):
        real = self.export["capture_records"][0]
        fields = dict(real, argv=tuple(real["argv"]), popen_args=tuple(real["popen_args"]),
                      env_git=(("GIT_NO_REPLACE_OBJECTS", "1"),),
                      env_python=(("PYTHONDONTWRITEBYTECODE", "1"),),
                      stdout=base64.b64decode(real["stdout_base64"]), stderr=b"")
        forged = object.__new__(tc._Evidence)
        object.__setattr__(forged, "_fields", types.MappingProxyType(fields))
        self.assertFalse(tc._take_evidence(forged))
        session = {"event_id": "EV-FORGED", "challenge": real["challenge"], "ledger_path": str(self.ledger),
                   "ledger_reservation_entry_sha256": "0" * 64, "lifecycle": dict(self.export["lifecycle"]),
                   "git": dict(self.export["git_probe"]), "measurements": dict(self.export["measurements"]),
                   "evidence": [forged], "blocked_reasons": [], "failure_reasons": [], "stage": self.tmp}
        result = verifier._verify_live(session)
        self.assertNotEqual(result["components"]["child_execution_binding"], "PASS")
        _not_pass(self, result)


class EvidenceObjectTests(unittest.TestCase):
    def test_no_module_global_writable_registry(self):
        for module in (tc, verifier, ledger):
            for name, value in vars(module).items():
                if name.startswith("__"):
                    continue
                self.assertNotIsInstance(value, (dict, set, list, weakref.WeakKeyDictionary),
                                         f"{module.__name__}.{name}")

    def test_evidence_cannot_be_constructed_directly(self):
        with self.assertRaises(TypeError):
            tc._Evidence()

    def test_evidence_is_single_use_frozen_and_tamper_evident(self):
        tmp = _tempdir()
        try:
            env = dict(os.environ)
            make = lambda: tc._launch([sys.executable, "-c", "print('x')"], env=env, cwd=tmp,
                                      case_id="X", command_id="CMD_X", sequence=1,
                                      event_id="EV-X", challenge="0" * 64)
            evidence = make()
            self.assertGreater(evidence.child_pid, 0)
            with self.assertRaises(AttributeError):
                evidence.return_code = 0
            self.assertTrue(tc._take_evidence(evidence))
            self.assertFalse(tc._take_evidence(evidence))  # single use
            tampered = make()
            fields = dict(object.__getattribute__(tampered, "_fields"), stdout=b"forged")
            object.__setattr__(tampered, "_fields", types.MappingProxyType(fields))
            self.assertFalse(tc._take_evidence(tampered))
        finally:
            _rmtree(tmp)

    def test_no_child_evidence_is_not_pass(self):
        result = verifier._verify_live({"event_id": "EV-EMPTY", "challenge": "0" * 64,
                                        "ledger_path": str(_ABSENT_LEDGER), "evidence": [],
                                        "lifecycle": {}})
        self.assertNotEqual(result["components"]["child_execution_binding"], "PASS")
        _not_pass(self, result)


class RefusalSemanticsTests(unittest.TestCase):
    def test_profile_binds_exact_refusals(self):
        for spec in _profile()["required_cases"]:
            if spec["expected_classification"] == "PASS":
                self.assertEqual(spec["expected_errors"], [])
            else:
                self.assertTrue(spec["expected_errors"], spec["case_id"])
                self.assertTrue(spec["intended_refusal"])

    def test_wrong_reason_rejection_is_not_an_expected_refusal(self):
        for spec in _profile()["required_cases"]:
            if spec["expected_classification"] == "FAIL":
                self.assertTrue(verifier._refusal_findings(spec, ["some unrelated error"]))
                self.assertTrue(verifier._refusal_findings(spec, []))
            else:
                self.assertTrue(verifier._refusal_findings(spec, ["any error"]))
            self.assertEqual(verifier._refusal_findings(spec, list(spec["expected_errors"])), [])

    @unittest.skipUnless(LIVE, "pinned Git / target repository unavailable")
    def test_old_top_level_human_final_input_is_wrong_reason(self):
        """Real pinned validator on the pre-r2 HUMAN_FINAL input refuses for the wrong reason."""
        executable = tc.DEFAULT_GIT.resolve()
        source = tc._git(executable, REPO, "show", tc.TARGET_SHA + ":docs/portfolio_state/validate_psm_v0.py")
        accepted = tc._git(executable, REPO, "show",
                           tc.TARGET_SHA + ":docs/portfolio_state/portfolio_state_v0.example.json")
        value = json.loads(accepted)
        value["human_final"], value["production_permission"] = "INFERRED", "GRANTED"
        tmp = _tempdir()
        try:
            (tmp / "validate_psm_v0.py").write_bytes(source)
            (tmp / "old.json").write_bytes(json.dumps(value).encode())
            env = tc._child_environment(executable)
            cp = subprocess.run([sys.executable, "-I", "-S", "-B", str(tc.PROBE), str(tmp / "validate_psm_v0.py"),
                                 str(tmp / "old.json"), str(REPO)], cwd=tmp, env=env,
                                capture_output=True, check=False, timeout=300)
            errors = json.loads(cp.stdout)["errors"]
        finally:
            _rmtree(tmp)
        self.assertEqual(cp.returncode, 2)  # rc=2 alone must not count
        self.assertEqual(errors, ["top-level fields do not match the closed PSM-v0 schema"])
        self.assertTrue(verifier._refusal_findings(_spec(HF), errors))

    @unittest.skipUnless(LIVE, "pinned Git / target repository unavailable")
    def test_closed_inputs_keep_top_level_key_set(self):
        raw = tc._git(tc.DEFAULT_GIT.resolve(), REPO, "show",
                      tc.TARGET_SHA + ":docs/portfolio_state/portfolio_state_v0.example.json")
        for spec in _profile()["required_cases"]:
            if spec["case_id"] == "PSM_NEG_MUTATED_ARCHIVE_OR_INPUT":
                continue
            self.assertEqual(set(input_cases.case_value(spec["case_id"], raw)), set(json.loads(raw)))
            self.assertEqual(tc.digest(input_cases.case_bytes(spec["case_id"], raw)), spec["input_digest"])


class SchemaTests(unittest.TestCase):
    def test_stale_99418b4_event_fails(self):
        stale = {"schema_version": "inr.event.v0", "inr_event_id": "EV1", "target_sha": tc.TARGET_SHA,
                 "trusted_challenge_record": {"generated_by": "capture_inr_v0", "single_use": True},
                 "byte_identity_evidence": {"measured_by": "capture_inr_v0"},
                 "module_execution_evidence": {}, "git_runtime_evidence": {"path_resolution_verified": True},
                 "protected_set_isolation_evidence": {"all_writer_isolation_evidence": "ESTABLISHED"},
                 "non_origin_evidence": {"runner_class": "FRESH_HOSTED_RUNNER"},
                 "capture_records": [], "case_result_bindings": [], "final_result": "PASS"}
        result = verifier.recheck_export(stale, ledger_path=_ABSENT_LEDGER)
        self.assertEqual(result["derived_result"], "FAIL")
        self.assertTrue(any(m.startswith("schema:") for m in result["fail"]))
        _not_pass(self, result)

    def test_stale_codex_intermediate_event_fails(self):
        stale = {"schema_version": "inr.event.v0", "inr_event_id": "EV2", "target_sha": tc.TARGET_SHA,
                 "challenge": "a" * 64, "trusted_evidence_ref": "b" * 64, "lifecycle": {},
                 "capture_records": [], "measurements": {}, "git_probe": {}, "assurance_gaps": [],
                 "blocked_reasons": [], "failure_reasons": [], "final_result": "PASS"}
        result = verifier.recheck_export(stale, ledger_path=_ABSENT_LEDGER)
        self.assertEqual(result["derived_result"], "FAIL")
        _not_pass(self, result)

    def test_profile_origin_conform_and_digest_is_pinned(self):
        profile, origin = tc.configuration()
        raw = json.loads((tc.ROOT / "profiles/psm_001_inr_target_profile_v0.json").read_bytes())
        body = {k: v for k, v in raw.items() if k != "target_profile_digest"}
        self.assertEqual(tc.digest(tc.canonical(body)), tc.PROFILE_DIGEST)
        self.assertEqual(raw["target_profile_digest"], tc.PROFILE_DIGEST)
        self.assertEqual({tuple(c["argv"]) for c in profile["command_inventory"]}, {verifier.ARGV_TEMPLATE})


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = _tempdir()
        self.path = self.tmp / "ledger.jsonl"

    def tearDown(self):
        _rmtree(self.tmp)

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

    def test_ledger_location_is_outside_worktree(self):
        with self.assertRaises(ledger.LedgerError):
            ledger.resolve_path(tc.ROOT / "ledger.jsonl")
        default = ledger.resolve_path(None)
        self.assertNotIn(REPO.resolve(), default.parents)


if __name__ == "__main__":
    unittest.main()
