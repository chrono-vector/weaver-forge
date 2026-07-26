#!/usr/bin/env python3
"""RC6-R5 tests: deviation transition (D1) and machine-ceiling recomputation (C3).

Uses only the Python standard library and local controlled temporary directories.
Does not invoke Docker, Cargo, compilers, product binaries, network, or Witness
workflows. Synthetic only — not Independent Witness evidence.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

import deviation_transition as dxt  # noqa: E402
import schema_register_loader as srl  # noqa: E402
import validate_witness_evidence as v  # noqa: E402

RC6_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.json"
RC63_REGISTER = PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.3.json"
FIXTURES = TESTS_DIR / "fixtures"
HOST_SCRIPT = SCRIPTS_DIR / "run_witness_narrow_build.sh"

_TEMPS: list[Path] = []


def _mktmp(prefix: str = "rc6r5_test_") -> Path:
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=str(TESTS_DIR)))
    _TEMPS.append(path)
    return path


def _cleanup() -> None:
    for path in _TEMPS:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    _TEMPS.clear()
    for path in TESTS_DIR.glob("rc6r5_test_*"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)


def _bash_available() -> bool:
    for candidate in ("bash", "bash.exe"):
        if shutil.which(candidate):
            return True
    return False


class Rc6R5SchemaAuthorityTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_01_active_default_is_rc6_5(self) -> None:
        active = srl.load_active_register()
        default = srl.load_canonical_register()
        self.assertEqual(default.schema_register_version, "rc6.5")
        self.assertEqual(active.schema_register_version, "rc6.5")
        self.assertEqual(v.SCHEMA_REGISTER_VERSION, "rc6.5")
        self.assertEqual(active.supersession().get("supersedes"), "rc6.4")

    def test_02_historical_rc64_and_rc63_explicit_only(self) -> None:
        rc64 = srl.load_historical_register("rc6.4")
        self.assertTrue(rc64.is_historical_rc64)
        self.assertTrue((PACKAGE_DIR / "schemas" / "canonical_schema_register_rc6.4.json").is_file())
        rc63 = srl.load_historical_register("rc6.3")
        self.assertTrue(rc63.is_historical_rc63)
        self.assertTrue(RC63_REGISTER.is_file())
        with self.assertRaises(srl.SchemaRegisterError):
            srl.load_historical_register("rc6.5")

    def test_03_final_deviations_require_r5_binding_fields(self) -> None:
        active = srl.load_active_register()
        required = active.required_field_names("DEVIATIONS.txt", "final-submission")
        for key in (
            "run_id",
            "preliminary_deviations_sha256",
            "aggregate_severity",
            "aggregate_canonical_identity_impact",
            "final_machine_ceiling",
        ):
            self.assertIn(key, required)
        prelim = active.required_field_names("DEVIATIONS.txt", "host-preliminary")
        self.assertEqual(
            prelim,
            (
                "evidence_schema_version",
                "deviation_state",
                "deviation_count",
                "automated_summary",
            ),
        )


class Rc6R5DeviationTransitionTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_04_none_transition_preserves_binding(self) -> None:
        run_id = "run-rc6-r5-none-001"
        prelim = dxt.emit_host_preliminary_deviations_bytes()
        final = dxt.transition_preliminary_to_final(preliminary_bytes=prelim, run_id=run_id)
        self.assertEqual(dxt.verify_deviation_transition(
            preliminary_bytes=prelim, final_text=final, run_id=run_id
        ), [])
        fields = dxt.parse_kv_bytes(final.encode("utf-8"))
        self.assertEqual(fields["preliminary_deviations_sha256"], dxt.sha256_hex(prelim))
        self.assertEqual(fields["aggregate_severity"], "NONE")
        self.assertEqual(fields["final_machine_ceiling"], "PASS")

    def test_05_host_writer_bytes_transition_noncanonical(self) -> None:
        """RC4B-011 supplemental: actual Host-writer-shaped noncanonical bytes → final."""
        run_id = "run-rc6-r5-noncanon-001"
        changed = [
            "RUST_IMAGE: canonical='docker.io/library/rust@sha256:aaa' effective='docker.io/library/rust@sha256:bbb'",
            "EXPECTED_RUSTC_VERSION: canonical='1.92.0' effective='1.91.0'",
            "EXPECTED_DOTSLASH_VERSION: canonical='0.5.7' effective='0.5.6'",
        ]
        prelim = dxt.emit_host_preliminary_deviations_bytes(changed_identity_fields=changed)
        self.assertIn(b"deviation_state=PRESENT", prelim)
        self.assertIn(b"deviation_count=3", prelim)
        final = dxt.transition_preliminary_to_final(preliminary_bytes=prelim, run_id=run_id)
        self.assertEqual(
            dxt.verify_deviation_transition(
                preliminary_bytes=prelim, final_text=final, run_id=run_id
            ),
            [],
        )
        fields = dxt.parse_kv_bytes(final.encode("utf-8"))
        self.assertEqual(fields["deviation_count"], "3")
        self.assertEqual(fields["deviation_1_severity"], "PROHIBITED")
        self.assertEqual(fields["deviation_2_severity"], "PROHIBITED")
        self.assertEqual(fields["deviation_3_severity"], "PROHIBITED")
        self.assertEqual(fields["aggregate_severity"], "PROHIBITED")
        self.assertEqual(fields["aggregate_canonical_identity_impact"], "yes")
        self.assertEqual(fields["final_machine_ceiling"], "FAIL")
        self.assertEqual(fields["preliminary_deviations_sha256"], dxt.sha256_hex(prelim))

    def test_06_transition_rejects_drop_change_invent(self) -> None:
        run_id = "run-rc6-r5-neg-001"
        changed = [
            "EXPECTED_RUSTC_VERSION: canonical='1.92.0' effective='1.90.0'",
        ]
        prelim = dxt.emit_host_preliminary_deviations_bytes(changed_identity_fields=changed)
        final = dxt.transition_preliminary_to_final(preliminary_bytes=prelim, run_id=run_id)
        # Drop
        dropped = "\n".join(
            line
            for line in final.splitlines()
            if not line.startswith("deviation_1_description=")
        ) + "\n"
        self.assertTrue(dxt.verify_deviation_transition(
            preliminary_bytes=prelim, final_text=dropped, run_id=run_id
        ))
        # Change
        changed_txt = final.replace("final_machine_ceiling=FAIL", "final_machine_ceiling=PASS")
        self.assertTrue(dxt.verify_deviation_transition(
            preliminary_bytes=prelim, final_text=changed_txt, run_id=run_id
        ))
        # Invent
        invented = final.rstrip("\n") + "\norphan_key=yes\n"
        self.assertTrue(dxt.verify_deviation_transition(
            preliminary_bytes=prelim, final_text=invented, run_id=run_id
        ))

    @unittest.skipUnless(_bash_available(), "bash not available for Host writer shell proof")
    def test_07_sourced_host_writer_bytes_match_helper(self) -> None:
        """Isolated local shell around write_preliminary_deviations_file from Host script."""
        out_dir = _mktmp()
        out_path = out_dir / "DEVIATIONS.txt"
        host_text = HOST_SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")
        start = host_text.find("write_preliminary_deviations_file() {")
        self.assertGreaterEqual(start, 0)
        end = host_text.find("\n}\n", start)
        self.assertGreater(end, start)
        fn_body = host_text[start : end + 3]
        script_path = out_dir / "writer.sh"
        script_path.write_text(
            "\n".join(
                [
                    "set -euo pipefail",
                    "NONCANONICAL_RUN=1",
                    "CHANGED_IDENTITY_FIELDS=(",
                    "  \"EXPECTED_RUSTC_VERSION: canonical='1.92.0' effective='1.91.0'\"",
                    "  \"RUST_IMAGE: canonical='imgA' effective='imgB'\"",
                    ")",
                    "NONCANONICAL_DISCLOSURE_TEXT=\"$(printf '%s; ' \"${CHANGED_IDENTITY_FIELDS[@]}\")\"",
                    fn_body,
                    'write_preliminary_deviations_file "./DEVIATIONS.txt"',
                    "",
                ]
            ),
            encoding="utf-8",
            newline="\n",
        )
        proc = subprocess.run(
            ["bash", "./writer.sh"],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(out_dir),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        shell_bytes = out_path.read_bytes()
        helper_bytes = dxt.emit_host_preliminary_deviations_bytes(
            changed_identity_fields=[
                "EXPECTED_RUSTC_VERSION: canonical='1.92.0' effective='1.91.0'",
                "RUST_IMAGE: canonical='imgA' effective='imgB'",
            ]
        )
        self.assertEqual(shell_bytes, helper_bytes)
        run_id = "run-rc6-r5-shell-001"
        final = dxt.transition_preliminary_to_final(
            preliminary_bytes=shell_bytes, run_id=run_id
        )
        self.assertEqual(
            dxt.verify_deviation_transition(
                preliminary_bytes=shell_bytes, final_text=final, run_id=run_id
            ),
            [],
        )
        fields = dxt.parse_kv_bytes(final.encode("utf-8"))
        self.assertEqual(fields["final_machine_ceiling"], "FAIL")


class Rc6R5CeilingRecomputationTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_08_nonmaterial_caps_at_partial(self) -> None:
        entries = [
            {
                "severity": "NONMATERIAL_DISCLOSED",
                "canonical_identity_impact": "no",
                "verdict_ceiling": "PARTIAL",
            }
        ]
        sev, impact, ceiling = dxt.recompute_aggregates_from_entries(entries)
        self.assertEqual(sev, "NONMATERIAL_DISCLOSED")
        self.assertEqual(impact, "no")
        self.assertEqual(ceiling, "PARTIAL")
        machine = dxt.recompute_machine_ceiling(
            outcome="CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            prohibited=False,
            identity_mismatch=False,
            static_inspection_incomplete=False,
            deviation_final_ceiling=ceiling,
        )
        self.assertEqual(machine, "PARTIAL")

    def test_09_prohibited_and_toolchain_fail(self) -> None:
        for field in (
            "EXPECTED_RUSTC_VERSION",
            "EXPECTED_DOTSLASH_VERSION",
            "RUST_IMAGE",
        ):
            sev, impact, ceil = dxt.severity_ceiling_for_identity_field(field)
            self.assertEqual(sev, "PROHIBITED")
            self.assertEqual(impact, "yes")
            self.assertEqual(ceil, "FAIL")
        machine = dxt.recompute_machine_ceiling(
            outcome="CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            prohibited=False,
            identity_mismatch=False,
            static_inspection_incomplete=False,
            deviation_final_ceiling="FAIL",
        )
        self.assertEqual(machine, "FAIL")

    def test_10_rejects_ceiling_disagreement(self) -> None:
        run_id = "run-rc6-r5-disagree-001"
        changed = [
            "EXPECTED_DOTSLASH_VERSION: canonical='0.5.7' effective='0.1.0'",
        ]
        prelim = dxt.emit_host_preliminary_deviations_bytes(changed_identity_fields=changed)
        final = dxt.transition_preliminary_to_final(preliminary_bytes=prelim, run_id=run_id)
        bad = final.replace("final_machine_ceiling=FAIL", "final_machine_ceiling=PASS")
        fields = dxt.parse_kv_bytes(bad.encode("utf-8"))
        errors = dxt.verify_final_package_consistency(fields, expected_run_id=run_id)
        self.assertTrue(any("final_machine_ceiling" in e for e in errors), errors)

    def test_11_contiguous_ids_and_orphan_rejection(self) -> None:
        fields = {
            "evidence_schema_version": "1",
            "run_id": "run-x",
            "deviation_state": "PRESENT",
            "deviation_count": "2",
            "preliminary_deviations_sha256": "a" * 64,
            "aggregate_severity": "PROHIBITED",
            "aggregate_canonical_identity_impact": "yes",
            "final_machine_ceiling": "FAIL",
            "deviation_1_description": "a",
            "deviation_1_severity": "PROHIBITED",
            "deviation_1_canonical_identity_impact": "yes",
            "deviation_1_verdict_ceiling": "FAIL",
            "deviation_3_description": "b",
            "deviation_3_severity": "PROHIBITED",
            "deviation_3_canonical_identity_impact": "yes",
            "deviation_3_verdict_ceiling": "FAIL",
        }
        errors = dxt.verify_final_package_consistency(fields, expected_run_id="run-x")
        self.assertTrue(any("contiguous" in e for e in errors), errors)

        fields2 = dict(fields)
        del fields2["deviation_3_description"]
        del fields2["deviation_3_severity"]
        del fields2["deviation_3_canonical_identity_impact"]
        del fields2["deviation_3_verdict_ceiling"]
        fields2["deviation_2_description"] = "b"
        fields2["deviation_2_severity"] = "PROHIBITED"
        fields2["deviation_2_canonical_identity_impact"] = "yes"
        fields2["deviation_2_verdict_ceiling"] = "FAIL"
        fields2["orphan_key"] = "no"
        errors2 = dxt.verify_final_package_consistency(fields2, expected_run_id="run-x")
        self.assertTrue(any("unknown key" in e for e in errors2), errors2)


class Rc6R5FixtureValidatorTests(unittest.TestCase):
    def tearDown(self) -> None:
        _cleanup()

    def test_12_active_r5_fixtures_conform(self) -> None:
        prelim = FIXTURES / "rc6-r6-synthetic-preliminary"
        final = FIXTURES / "rc6-r6-synthetic-final"
        self.assertTrue(prelim.is_dir())
        self.assertTrue(final.is_dir())
        self.assertEqual(v.validate_dir(prelim, host_preliminary=True), [])
        self.assertEqual(v.validate_dir(final), [])

    def test_13_historical_r4_fixtures_via_rc63(self) -> None:
        r4p = FIXTURES / "rc6-r4-synthetic-preliminary"
        r4f = FIXTURES / "rc6-r4-synthetic-final"
        self.assertEqual(
            v.validate_dir(r4p, host_preliminary=True, schema_register_version="rc6.3"),
            [],
        )
        self.assertEqual(v.validate_dir(r4f, schema_register_version="rc6.3"), [])


if __name__ == "__main__":
    unittest.main()
