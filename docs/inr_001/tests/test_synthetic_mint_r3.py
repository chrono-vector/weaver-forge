"""INR-001 r3 synthetic trust-mint regression tests (Codex material issue A).

Each test is a real false-PASS attempt of the Codex PoC class, not a constructor
visibility check. A fresh PASS-capable result exists only as the report of a
supervisor process launched by ``capture_inr_v0`` and bound to that process, so
every attempt below must end non-PASS.

A  closure introspection / cell and state mutation
B  synthetic Evidence-like object
C  fake pid / stdout / returncode
D  no-child path
E  empty findings / zero checks
F  historical / disk evidence
G  direct import of internal modules
"""
from __future__ import annotations

import base64
import contextlib
import gc
import inspect
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import types
import unittest
from unittest import mock
import weakref

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inr_r3_support as s  # noqa: E402
from docs.inr_001 import capture_inr_v0 as capture  # noqa: E402
from docs.inr_001 import input_cases, ledger, schema_check  # noqa: E402
from docs.inr_001 import supervisor_inr_v0 as sup  # noqa: E402
from docs.inr_001 import validate_inr_v0 as verifier  # noqa: E402

MODULES = (sup, capture, verifier, ledger, input_cases, schema_check)
MUTABLE = (dict, list, set, bytearray, weakref.WeakKeyDictionary, weakref.WeakValueDictionary, weakref.WeakSet)


def _is_pass(value):
    """True if any (nested) dict claims PASS."""
    if isinstance(value, dict):
        if value.get("pass_allowed") is True or value.get("derived_result") == "PASS" \
                or value.get("local_controls_result") == "PASS":
            return True
        return any(_is_pass(v) for v in value.values() if isinstance(v, (dict, list, tuple)))
    if isinstance(value, (list, tuple)):
        return any(_is_pass(v) for v in value)
    return False


def _module_callables():
    for module in MODULES:
        for name, value in vars(module).items():
            if getattr(value, "__module__", None) != module.__name__ or name.startswith("__"):
                continue
            if inspect.isfunction(value):
                yield module, name, value
            elif inspect.isclass(value):
                yield module, name, value
                for attr, member in vars(value).items():
                    if inspect.isfunction(member):
                        yield module, f"{name}.{attr}", member


def _synthetic_evidence(challenge="c" * 64, event_id="EV-SYN", pid=4242):
    report = {"event_id": event_id, "challenge": challenge, "case_id": "PSM_POSITIVE_ACCEPTED_RECORD",
              "case_nonce": "a" * 32, "errors": [],
              "identity": {"source_sha256": "0" * 64, "isolated": 1, "no_site": 1, "python_version": [3, 11, 9]}}
    fields = {"case_id": "PSM_POSITIVE_ACCEPTED_RECORD", "command_id": "CMD_PSM_POSITIVE_ACCEPTED_RECORD",
              "sequence": 1, "event_id": event_id, "challenge": challenge, "case_nonce": "a" * 32,
              "argv": ("python", "-I", "-S", "-B"), "popen_args": ("python", "-I", "-S", "-B"),
              "child_pid": pid, "pid": pid, "return_code": 0, "returncode": 0,
              "stdout": json.dumps(report).encode(), "stderr": b"", "start_ns": 1, "end_ns": 2,
              "derived_result": "PASS", "pass_allowed": True}
    return types.SimpleNamespace(**fields), fields


@contextlib.contextmanager
def _tmp():
    path = s.tempdir()
    try:
        yield path
    finally:
        s.rmtree(path)


class SyntheticMintTests(unittest.TestCase):
    # -- A ------------------------------------------------------------------------
    def test_A_closure_introspection_and_state_mutation_cannot_mint_pass(self):
        gc.collect()
        functions = [fn for _, _, fn in _module_callables() if inspect.isfunction(fn)]
        functions += [o for o in gc.get_objects() if inspect.isfunction(o)
                      and (getattr(o, "__module__", None) or "").startswith("docs.inr_001")]
        cells = [(fn, cell) for fn in functions for cell in (fn.__closure__ or ())]
        # Structural: no provenance/session registry lives in closure or module state.
        for fn, cell in cells:
            try:
                content = cell.cell_contents
            except ValueError:
                continue
            self.assertNotIsInstance(content, MUTABLE, fn.__qualname__)
        for module in MODULES:
            for name, value in vars(module).items():
                if not name.startswith("__"):
                    self.assertNotIsInstance(value, MUTABLE, f"{module.__name__}.{name}")
        # Codex PoC: inject synthetic evidence into every reachable closure cell and every
        # live INR state object, then try to obtain PASS.
        evidence, fields = _synthetic_evidence()
        injected = 0
        for fn, cell in cells:
            try:
                content = cell.cell_contents
            except ValueError:
                continue
            if isinstance(content, sup.Findings):
                content.established = {k: True for k in content.established}
                injected += 1
        for obj in gc.get_objects():
            if isinstance(obj, sup.Findings):
                obj.established = {k: True for k in obj.established}
                injected += 1
        self.assertFalse(sup.Findings().result()["pass_allowed"])  # a fresh run starts empty
        self.assertEqual(sup.Findings().result()["derived_result"], "UNCONFIRMED")
        # In-process monkeypatching of the classifier and pinned constants in the CALLER
        # process cannot reach the supervisor process launched afterwards.
        with _tmp() as tmp, \
                mock.patch.object(sup.Findings, "_classify", lambda self, names: "PASS"), \
                mock.patch.object(sup, "_REAL_POPEN", type(evidence)):
            report, rc, export = s.run_supervisor_process(
                "EV-R3-A", tmp, repository=s.REPO if s.LIVE else tmp)
        s.not_pass(self, report)
        self.assertEqual(rc, 1)
        self.assertEqual(report["result_kind"], "FRESH_SUPERVISOR_RUN")
        self.assertEqual(report["predicates"]["supervisor_process"], "PASS")
        if s.LIVE:
            pids = {r["child_pid"] for r in export["capture_records"]}
            self.assertNotIn(fields["child_pid"], pids)
            self.assertEqual(report["predicates"]["child_launched"], "PASS")
        else:
            self.assertEqual(report["predicates"]["child_launched"], "NOT_ESTABLISHED")

    def _attempt_all_payloads(self, module, name, fn, evidence, fields):
        if inspect.isclass(fn) and issubclass(fn, BaseException):
            return 0
        try:
            signature = inspect.signature(fn)
        except (TypeError, ValueError):
            return 0
        required = [p for p in signature.parameters.values()
                    if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        attempts = 0
        for payload in (evidence, fields, [evidence], [fields]):
            args = [payload] * max(1, len(required))
            if name.startswith("Findings."):
                args[0] = sup.Findings()
            attempts += 1
            try:
                value = fn(*args)
            except BaseException:  # noqa: BLE001 - any refusal is fine
                continue
            self.assertFalse(_is_pass(value), f"{module.__name__}.{name} -> {value!r}")
        return attempts

    # -- B ------------------------------------------------------------------------
    def test_B_synthetic_evidence_like_object_cannot_create_pass(self):
        evidence, fields = _synthetic_evidence()
        attempts = 0
        cwd = os.getcwd()
        with _tmp() as tmp, mock.patch.dict(os.environ, {"LOCALAPPDATA": str(tmp), "XDG_STATE_HOME": str(tmp)}), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            os.chdir(tmp)  # any relative path a callable might derive from the payload lands here
            try:
                for module, name, fn in _module_callables():
                    attempts += self._attempt_all_payloads(module, name, fn, evidence, fields)
            finally:
                os.chdir(cwd)
        self.assertGreater(attempts, 20)
        # The supervisor process accepts no evidence via argv, stdin or environment.
        with _tmp() as tmp:
            synthetic_file = tmp / "evidence.json"
            synthetic_file.write_text(json.dumps({k: (base64.b64encode(v).decode() if isinstance(v, bytes) else v)
                                                  for k, v in fields.items()}), encoding="utf-8")
            base = [sys.executable, "-I", "-S", "-B", str(sup.SUPERVISOR), "--event-id", "EV-R3-B",
                    "--repository", str(s.REPO if s.LIVE else tmp), "--out", str(tmp / "o.json"),
                    "--ledger", str(tmp / "ledger.jsonl"), "--work-dir", str(tmp)]
            for extra in (["--evidence", str(synthetic_file)], ["--snapshot", str(synthetic_file)],
                          ["--capture-record", str(synthetic_file)], ["--provenance", str(synthetic_file)]):
                cp = subprocess.run(base + extra, capture_output=True, timeout=120, check=False)
                self.assertEqual(cp.returncode, 2, extra)
                self.assertEqual(cp.stdout, b"")
            env = dict(os.environ, INR_EVIDENCE=str(synthetic_file), INR_CAPTURE_RECORD="PASS",
                       INR_TRUSTED_SNAPSHOT=synthetic_file.read_text(encoding="utf-8"))
            cp = subprocess.run(base, input=synthetic_file.read_bytes(), capture_output=True, env=env,
                                timeout=1800, check=False)
            report = json.loads(cp.stdout.decode().strip().splitlines()[-1])
            s.not_pass(self, report)
            self.assertEqual(cp.returncode, 1)
            if s.LIVE:
                export = json.loads((tmp / "o.json").read_bytes())
                self.assertNotEqual(export["challenge"], fields["challenge"])
                self.assertNotIn(fields["child_pid"], {r["child_pid"] for r in export["capture_records"]})
                self.assertEqual(report["predicates"]["child_provenance"], "PASS")

    # -- C ------------------------------------------------------------------------
    @unittest.skipUnless(s.LIVE, "pinned Git / target repository unavailable")
    def test_C_fake_pid_stdout_returncode_cannot_create_pass(self):
        profile = s.profile()
        expected = {c["case_id"]: c for c in profile["required_cases"]}
        probe, real_popen = str(sup.PROBE.resolve()), subprocess.Popen

        class FakeChild(subprocess.Popen):
            """Spawns nothing for target cases; fabricates a perfect child report from the launch env."""
            def __init__(self, args, **kwargs):
                if probe not in list(args):
                    super().__init__(args, **kwargs)  # Git probes stay real
                    return
                env = kwargs["env"]
                cid = env["INR_CASE_ID"]
                self.args, self.pid, self.returncode = list(args), 4242, 0 if not expected[cid]["expected_errors"] else 2
                self.stdin = self.stdout = self.stderr = None
                self._child_created = False
                identity = {"source_sha256": profile["target_file_digests"]["validate_psm_v0.py"],
                            "post_source_sha256": profile["target_file_digests"]["validate_psm_v0.py"],
                            "input_sha256": expected[cid]["input_digest"], "target_preloaded": False,
                            "source_path": args[5], "site_loaded": False, "sitecustomize_loaded": False,
                            "usercustomize_loaded": False, "isolated": 1, "no_site": 1,
                            "dont_write_bytecode": True, "python_executable": args[0],
                            "python_version": [3, 11, 9], "git_which": str(sup.DEFAULT_GIT.resolve()),
                            "git_shadowing": [], "git_environment": [["GIT_NO_REPLACE_OBJECTS", "1"]]}
                self._out = json.dumps({"event_id": env["INR_EVENT_ID"], "challenge": env["INR_RUN_CHALLENGE"],
                                        "case_id": cid, "case_nonce": env["INR_CASE_NONCE"],
                                        "identity": identity, "errors": expected[cid]["expected_errors"]}).encode()

            def communicate(self, *a, **k):
                if not hasattr(self, "_out"):
                    return super().communicate(*a, **k)
                return self._out, b""

        class DuckChild:
            def __new__(cls, args, **kwargs):
                if probe not in list(args):
                    return real_popen(args, **kwargs)
                return super().__new__(cls)

            def __init__(self, args, **kwargs):
                self.args, self.pid, self.returncode = list(args), 4242, 0

            def communicate(self, *a, **k):
                return b"{}", b""

        with _tmp() as tmp:
            for fake in (FakeChild, DuckChild):
                with mock.patch.object(subprocess, "Popen", fake):
                    result, export = sup.supervise("EV-R3-C-" + fake.__name__, s.REPO,
                                                   ledger_path=tmp / "ledger.jsonl", work_dir=tmp)
                s.not_pass(self, result)
                self.assertEqual(result["predicates"]["child_launched"], "BLOCKED", result)
                self.assertTrue(any("not a real subprocess.Popen" in m for m in result["blocked"]), result)
                self.assertEqual(export["capture_records"], [])
                self.assertNotEqual(result["local_controls_result"], "PASS")
            # Even an in-process attacker who also swaps the supervisor's Popen reference
            # only forges child facts in its OWN process: never a fresh supervisor PASS.
            with mock.patch.object(subprocess, "Popen", FakeChild), mock.patch.object(sup, "_REAL_POPEN", FakeChild):
                result, export = sup.supervise("EV-R3-C-SWAP", s.REPO, ledger_path=tmp / "ledger.jsonl",
                                               work_dir=tmp)
            s.not_pass(self, result)
            self.assertNotEqual(result["local_controls_result"], "PASS")
            self.assertEqual(result["result_kind"], "IN_PROCESS_NOT_TRUSTED")
            self.assertEqual(result["predicates"]["supervisor_process"], "UNCONFIRMED")
            self.assertEqual(result["supervisor_pid"], os.getpid())

    # -- D ------------------------------------------------------------------------
    def test_D_no_child_path_is_never_pass(self):
        with _tmp() as tmp:
            # (1) the real supervisor process, but nothing launchable: not a Git repository
            empty = tmp / "not_a_repo"
            empty.mkdir()
            report, rc, export = s.run_supervisor_process("EV-R3-D-PROC", tmp, repository=empty)
            s.not_pass(self, report)
            self.assertEqual(rc, 1)
            self.assertEqual(report["predicates"]["child_launched"], "NOT_ESTABLISHED", report)
            self.assertEqual(report["predicates"]["mandatory_cases_executed"], "UNCONFIRMED", report)
            self.assertIn("mandatory_cases_executed: executed 0 of 11 mandatory cases", report["unconfirmed"])
            self.assertEqual(export["capture_records"], [])
            self.assertNotEqual(report["local_controls_result"], "PASS")
            # (2) profile cannot be pinned: zero children, nothing established
            with mock.patch.object(sup, "PROFILE_DIGEST", "0" * 64):
                result, export = sup.supervise("EV-R3-D-PROFILE", s.REPO, ledger_path=tmp / "ledger.jsonl",
                                               work_dir=tmp)
            s.not_pass(self, result)
            self.assertEqual(result["predicates"]["profile_pinned"], "BLOCKED")
            self.assertEqual(export["capture_records"], [])
            for name in ("child_launched", "child_provenance", "argv_exact", "refusal_semantics",
                         "mandatory_cases_executed", "capture_complete"):
                self.assertEqual(result["predicates"][name], "NOT_ESTABLISHED", name)
            # (3) launch itself fails
            if s.LIVE:
                probe, real_popen = str(sup.PROBE.resolve()), subprocess.Popen

                def failing(args, **kwargs):
                    if probe in list(args):
                        raise OSError("no child")
                    return real_popen(args, **kwargs)

                with mock.patch.object(subprocess, "Popen", failing):
                    result, export = sup.supervise("EV-R3-D-OSERROR", s.REPO, ledger_path=tmp / "ledger.jsonl",
                                                   work_dir=tmp)
                s.not_pass(self, result)
                self.assertEqual(result["predicates"]["child_launched"], "BLOCKED")
                self.assertEqual(export["capture_records"], [])

    # -- E ------------------------------------------------------------------------
    def test_E_empty_findings_default_is_unconfirmed(self):
        result = sup.Findings().result()
        self.assertEqual(result["derived_result"], "UNCONFIRMED")
        self.assertEqual(result["local_controls_result"], "UNCONFIRMED")
        self.assertFalse(result["pass_allowed"])
        self.assertEqual(set(result["predicates"].values()), {"NOT_ESTABLISHED"})
        self.assertEqual(result["not_established"], list(sup.REQUIRED_PREDICATES))
        zero = sup.Findings(required=(), local=()).result()  # zero checks
        self.assertEqual(zero["derived_result"], "UNCONFIRMED")
        self.assertFalse(zero["pass_allowed"])
        partial = sup.Findings()
        for name in sup.REQUIRED_PREDICATES[:-1]:
            partial.establish(name)
        self.assertEqual(partial.result()["derived_result"], "UNCONFIRMED")  # one missing predicate
        contradiction = sup.Findings()
        contradiction.add("argv_exact", "fail", "x")
        contradiction.establish("argv_exact")
        self.assertEqual(contradiction.status("argv_exact"), "FAIL")
        self.assertEqual(contradiction.result()["derived_result"], "FAIL")
        self.assertTrue(contradiction.result()["contradictions"])
        with _tmp() as tmp:  # a supervised event with an invalid event ID establishes nothing
            result, export = sup.supervise("", s.REPO, ledger_path=tmp / "ledger.jsonl", work_dir=tmp)
            self.assertIsNone(export)
            s.not_pass(self, result)
            self.assertNotIn("PASS", result["predicates"].values())

    # -- F ------------------------------------------------------------------------
    def test_F_historical_or_disk_evidence_never_becomes_fresh_pass(self):
        with _tmp() as tmp:
            path = tmp / "ledger.jsonl"
            # attacker-authored ledger history (valid chain + head) recording PASS, and a
            # schema-valid self-authored export claiming PASS everywhere
            reservation = ledger.reserve(path, "EV-R3-F", "d" * 64)
            forged = s.synthetic_export("EV-R3-F", "d" * 64, reservation["entry_sha256"])
            ledger.complete(path, "EV-R3-F", "d" * 64, {"derived_result": "PASS", "local_controls_result": "PASS",
                                                         "export_sha256": sup.digest(sup.canonical(forged))})
            result = verifier.recheck_export(forged, ledger_path=path)
            self.assertEqual(result["result_kind"], "INFORMATIONAL_RECHECK")
            self.assertFalse(result["fresh_pass_capable"])
            self.assertEqual(result["fail"], [], result)  # ledger-consistent, still not PASS
            self.assertEqual(result["derived_result"], "UNCONFIRMED")
            s.not_pass(self, result)
            # the supervisor offers no way to load a historical export/report
            cp = subprocess.run([sys.executable, "-I", "-S", "-B", str(sup.SUPERVISOR), "--event-id", "EV-R3-F2",
                                 "--repository", str(tmp), "--out", str(tmp / "o.json"),
                                 "--replay", str(tmp / "forged.json")], capture_output=True, timeout=120, check=False)
            self.assertEqual(cp.returncode, 2)
            self.assertEqual(cp.stdout, b"")
            if not s.LIVE:
                return
            # a real historical run, then replay of its child output into a new event
            report, _, export = s.run_supervisor_process("EV-R3-F-HIST", tmp, ledger=path)
            s.not_pass(self, verifier.recheck_export(export, ledger_path=path))
            historical = {r["case_id"]: base64.b64decode(r["stdout_base64"]) for r in export["capture_records"]}
            real = subprocess.Popen.communicate
            probe = str(sup.PROBE.resolve())

            def replaying(popen, *args, **kwargs):
                out, err = real(popen, *args, **kwargs)
                argv = list(popen.args) if isinstance(popen.args, (list, tuple)) else []
                if probe in argv:
                    return historical[Path(argv[-2]).stem], err
                return out, err

            with mock.patch.object(subprocess.Popen, "communicate", replaying):
                result, _ = sup.supervise("EV-R3-F-REPLAY", s.REPO, ledger_path=path, work_dir=tmp)
            self.assertEqual(result["predicates"]["child_provenance"], "FAIL", result)
            self.assertTrue(any("replay" in m for m in result["fail"]), result)
            s.not_pass(self, result)

    # -- G ------------------------------------------------------------------------
    def test_G_direct_import_cannot_mint_fresh_trusted_provenance(self):
        with _tmp() as tmp:
            repository = s.REPO if s.LIVE else tmp
            # (1) calling the supervisor entry in-process (real children when LIVE)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                rc = sup.main(["--event-id", "EV-R3-G-IMPORT", "--repository", str(repository),
                               "--out", str(tmp / "g1.json"), "--ledger", str(tmp / "ledger.jsonl"),
                               "--work-dir", str(tmp)])
            report = json.loads(buffer.getvalue().strip().splitlines()[-1])
            self.assertEqual(rc, 1)
            s.not_pass(self, report)
            self.assertEqual(report["result_kind"], "IN_PROCESS_NOT_TRUSTED")
            self.assertEqual(report["predicates"]["supervisor_process"], "UNCONFIRMED")
            self.assertNotEqual(report["local_controls_result"], "PASS")
            self.assertEqual(report["supervisor_pid"], os.getpid())
            if s.LIVE:
                self.assertEqual(report["predicates"]["child_launched"], "PASS")  # real children, still not trusted
            # (2) executing the supervisor file as __main__ inside this process
            argv = [str(sup.SUPERVISOR), "--event-id", "EV-R3-G-RUNPY", "--repository", str(tmp),
                    "--out", str(tmp / "g2.json"), "--ledger", str(tmp / "ledger.jsonl"), "--work-dir", str(tmp)]
            buffer = io.StringIO()
            saved_path, saved_prefix = list(sys.path), sys.pycache_prefix
            try:
                with mock.patch.object(sys, "argv", argv), contextlib.redirect_stdout(buffer), \
                        self.assertRaises(SystemExit) as caught:
                    runpy.run_path(str(sup.SUPERVISOR), run_name="__main__")
            finally:
                sys.path[:] = saved_path
                sys.pycache_prefix = saved_prefix
            self.assertEqual(caught.exception.code, 1)
            report = json.loads(buffer.getvalue().strip().splitlines()[-1])
            s.not_pass(self, report)
            self.assertEqual(report["result_kind"], "IN_PROCESS_NOT_TRUSTED")
            # (3) an in-process report cannot be submitted anywhere as fresh evidence
            for fn in (capture.launch_supervisor, capture.supervisor_command, sup.supervise):
                params = set(inspect.signature(fn).parameters)
                self.assertFalse(params & {"evidence", "report", "snapshot", "capture", "provenance", "result"}, fn)
            self.assertEqual(set(inspect.signature(sup.supervise).parameters),
                             {"event_id", "repository", "ledger_path", "work_dir"})
            forged = dict(report, derived_result="PASS", pass_allowed=True, local_controls_result="PASS",
                          result_kind="FRESH_SUPERVISOR_RUN")

            class Relay:
                def __init__(self, *args, **kwargs):
                    self.pid, self.returncode = 999999, 0

                def communicate(self, timeout=None):
                    return json.dumps(forged).encode(), b""

            with mock.patch.object(capture.subprocess, "Popen", Relay):
                relayed, _ = capture.launch_supervisor(forged["event_id"], tmp, tmp / "g3.json")
            s.not_pass(self, relayed)  # supervisor_pid is this process, not the launched child
            self.assertEqual(relayed["result_kind"], "LAUNCHER_BINDING_FAILURE")
            self.assertFalse(hasattr(sup, "_take_evidence") or hasattr(sup, "validate_trusted_evidence")
                             or hasattr(sup, "register_snapshot") or hasattr(verifier, "_verify_live"))


if __name__ == "__main__":
    unittest.main()
