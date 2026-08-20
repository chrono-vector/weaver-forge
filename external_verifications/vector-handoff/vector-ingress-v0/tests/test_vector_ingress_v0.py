"""Synthetic and read-only integration tests for VECTOR Package Ingress v0."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
MOD = HERE.parent
if str(MOD) not in sys.path:
    sys.path.insert(0, str(MOD))

import fixtures_lib as fx  # noqa: E402
import ingress_v0  # noqa: E402
from ingress_v0 import evaluate_vector_package_ingress_v0  # noqa: E402
from package_reader_v0 import (  # noqa: E402
    MAX_UNCOMPRESSED_PER_ENTRY,
    MAX_ZIP_ENTRY_COUNT,
    MAX_ZIP_FILE_BYTES,
)
from result_v0 import validate_vector_ingress_result_v0  # noqa: E402

REAL_ZIP = Path(
    r"C:\dev\AI_Lab-local-staging\weaver_handoff_packages"
    r"\VECTOR_WEAVER_HANDOFF_vwh-v0-383a940e88a49dbbb9fd4250420b038e.zip"
)


def _eval_bytes(data: bytes, name: str = "vwh-v0-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip") -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_bytes(data)
        before = {p.name for p in Path(tmp).iterdir()}
        result = evaluate_vector_package_ingress_v0(path)
        after = {p.name for p in Path(tmp).iterdir()}
        if after != before:
            raise AssertionError(f"evaluator wrote files: {after - before}")
        return result


class NormalPathTests(unittest.TestCase):
    def test_valid_synthetic_package_ready_with_limitations(self) -> None:
        result = _eval_bytes(fx.valid_zip_bytes())
        self.assertEqual(result["final_disposition"], "INGRESS_READY")
        self.assertEqual(result["schema_id"], "weaver-vector-ingress-result-v0")
        self.assertEqual(result["source_package_id"], fx.PACKAGE_ID)
        for key, value in result["authority"].items():
            self.assertIs(value, False, key)
        for status in result["checks"].values():
            self.assertEqual(status, "ok")
        self.assertIn("L1_approved_request_bytes_absent", result["limitation_codes"])
        self.assertIn("L2_payload_digest_not_recomputed", result["limitation_codes"])
        self.assertIn("L3_pinned_bytes_not_checked", result["limitation_codes"])
        self.assertEqual(validate_vector_ingress_result_v0(result), [])
        self.assertTrue(result["ingress_result_id"].startswith("wvir-v0-"))
        self.assertEqual(len(result["ingress_result_id"]), len("wvir-v0-") + 32)

    def test_shared_artifact_id_across_classes_allowed(self) -> None:
        result = _eval_bytes(fx.valid_zip_bytes())
        self.assertEqual(result["final_disposition"], "INGRESS_READY")
        self.assertNotIn("same_class_id_different_bytes", result["reason_codes"])

    def test_no_writer_api(self) -> None:
        self.assertFalse(hasattr(ingress_v0, "write_vector_ingress_result_v0"))

    def test_directory_input_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = evaluate_vector_package_ingress_v0(tmp)
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertEqual(result["checks"]["container"], "failed")


class IntegrityTests(unittest.TestCase):
    def test_changed_artifact_bytes_reject(self) -> None:
        files = fx.build_file_map()
        files["decision_trace.json"] += b" "
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_mismatch", result["reason_codes"])

    def test_manifest_package_id_mismatch(self) -> None:
        def mutate(objects: dict) -> None:
            objects["package_id"] = "vwh-v0-dddddddddddddddddddddddddddddddd"

            def patch(manifest: dict) -> None:
                manifest["approved_core04_request_id"] = fx.PACKAGE_ID

            objects["manifest_patch"] = patch

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("identity_mismatch", result["reason_codes"])

    def test_same_class_id_different_bytes_reject(self) -> None:
        def mutate(objects: dict) -> None:
            def patch(manifest: dict) -> None:
                for entry in manifest["payload"]:
                    if entry["filename"] == "replay_eligibility_result.json":
                        entry["artifact_class"] = "vector_replay_contract"

            objects["manifest_patch"] = patch

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("same_class_id_different_bytes", result["reason_codes"])

    def test_malformed_digest_line(self) -> None:
        files = fx.build_file_map()
        files["DIGESTS.sha256"] = b"not-a-digest-line\n"
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_grammar", result["reason_codes"])

    def test_uppercase_digest_rejected(self) -> None:
        files = fx.build_file_map()
        line = files["DIGESTS.sha256"].decode("utf-8").splitlines()[0]
        digest, name = line.split("  ", 1)
        files["DIGESTS.sha256"] = (digest.upper() + "  " + name + "\n").encode("utf-8")
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_grammar", result["reason_codes"])

    def test_duplicate_digest_line(self) -> None:
        files = fx.build_file_map()
        text = files["DIGESTS.sha256"].decode("utf-8")
        first = text.splitlines()[0]
        files["DIGESTS.sha256"] = (text + first + "\n").encode("utf-8")
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_inventory", result["reason_codes"])

    def test_extra_digest_line(self) -> None:
        files = fx.build_file_map()
        extra = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa  extra.txt\n"
        files["DIGESTS.sha256"] += extra.encode("utf-8")
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_inventory", result["reason_codes"])

    def test_missing_digest_line(self) -> None:
        files = fx.build_file_map()
        lines = [ln for ln in files["DIGESTS.sha256"].decode("utf-8").splitlines() if ln]
        files["DIGESTS.sha256"] = ("\n".join(lines[1:]) + "\n").encode("utf-8")
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_inventory", result["reason_codes"])

    def test_zip_basename_without_package_id(self) -> None:
        result = _eval_bytes(fx.valid_zip_bytes(), name="unrelated.zip")
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("identity_mismatch", result["reason_codes"])

    def test_exact_handoff_basename_ready(self) -> None:
        name = f"VECTOR_WEAVER_HANDOFF_{fx.PACKAGE_ID}.zip"
        result = _eval_bytes(fx.valid_zip_bytes(), name=name)
        self.assertEqual(result["final_disposition"], "INGRESS_READY")

    def test_substring_basename_rejected(self) -> None:
        result = _eval_bytes(
            fx.valid_zip_bytes(),
            name=f"copy-{fx.PACKAGE_ID}-extra.zip",
        )
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("identity_mismatch", result["reason_codes"])

    def _payload_sha_mismatch_zip(self, filename: str) -> bytes:
        files = fx.build_file_map()
        manifest = json.loads(files["HANDOFF_MANIFEST.json"].decode("utf-8"))
        fake = "ab" * 32
        found = False
        for entry in manifest["payload"]:
            if entry["filename"] == filename:
                entry["content_sha256"] = fake
                entry["observed_sha256"] = fake
                found = True
        self.assertTrue(found, filename)
        files["HANDOFF_MANIFEST.json"] = json.dumps(
            manifest, ensure_ascii=True, separators=(",", ":")
        ).encode("utf-8")
        listed = [n for n in files if n != "DIGESTS.sha256"]
        lines = [f"{fx.sha256_bytes(files[n])}  {n}" for n in sorted(listed)]
        files["DIGESTS.sha256"] = ("\n".join(lines) + "\n").encode("utf-8")
        return fx.zip_bytes(files)

    def test_payload_sha_mismatch_envelope(self) -> None:
        result = _eval_bytes(self._payload_sha_mismatch_zip("verification_pre_handoff_envelope.json"))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_mismatch", result["reason_codes"])

    def test_payload_sha_mismatch_replay_contract(self) -> None:
        result = _eval_bytes(self._payload_sha_mismatch_zip("replay_contract.json"))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_mismatch", result["reason_codes"])

    def test_payload_sha_mismatch_replay_eligibility(self) -> None:
        result = _eval_bytes(self._payload_sha_mismatch_zip("replay_eligibility_result.json"))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("digest_mismatch", result["reason_codes"])


class VersionJsonTests(unittest.TestCase):
    def test_unknown_future_version(self) -> None:
        def mutate(objects: dict) -> None:
            objects["schema_version"] = "1"

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("schema_unsupported", result["reason_codes"])

    def test_unsupported_schema_id(self) -> None:
        def mutate(objects: dict) -> None:
            objects["schema_id"] = "vector-weaver-materialized-handoff-package-v1"

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("schema_unsupported", result["reason_codes"])

    def test_wrong_target_system(self) -> None:
        def mutate(objects: dict) -> None:
            objects["target_system"] = "SOMEWHERE_ELSE"

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("identity_mismatch", result["reason_codes"])

    def test_wrong_requested_operation(self) -> None:
        def mutate(objects: dict) -> None:
            objects["requested_operation"] = "REPLAY"

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("identity_mismatch", result["reason_codes"])

    def test_malformed_json(self) -> None:
        files = fx.build_file_map()
        files["HANDOFF_MANIFEST.json"] = b"{not json"
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("json_malformed", result["reason_codes"])

    def test_duplicate_json_keys(self) -> None:
        files = fx.build_file_map()
        raw = files["HANDOFF_MANIFEST.json"].decode("utf-8")
        # Insert a duplicate top-level key after the first key.
        files["HANDOFF_MANIFEST.json"] = raw.replace(
            '"schema_id":', '"schema_id":"x","schema_id":', 1
        ).encode("utf-8")
        result = _eval_bytes(fx.zip_bytes(files))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertTrue(
            "json_duplicate_key" in result["reason_codes"]
            or "json_malformed" in result["reason_codes"]
            or "schema_unsupported" in result["reason_codes"]
        )

    def test_wrong_required_field_type(self) -> None:
        def mutate(objects: dict) -> None:
            def patch(manifest: dict) -> None:
                manifest["payload"] = "not-a-list"

            objects["manifest_patch"] = patch

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("json_type_mismatch", result["reason_codes"])


class ZipSecurityTests(unittest.TestCase):
    def test_path_traversal(self) -> None:
        files = fx.build_file_map()
        info = zipfile.ZipInfo("../decision_trace.json")
        info.compress_type = zipfile.ZIP_STORED
        data = fx.zip_bytes(files, extra_infos=[info], extra_payloads={info.filename: b"{}"})
        result = _eval_bytes(data)
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertEqual(result["checks"]["container"], "failed")

    def test_absolute_path(self) -> None:
        files = fx.build_file_map()
        info = zipfile.ZipInfo("/tmp/evil.json")
        info.compress_type = zipfile.ZIP_STORED
        result = _eval_bytes(fx.zip_bytes(files, extra_infos=[info], extra_payloads={info.filename: b"x"}))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_path_unsafe", result["reason_codes"])

    def test_windows_drive_prefix(self) -> None:
        files = fx.build_file_map()
        info = zipfile.ZipInfo("C:/evil.json")
        info.compress_type = zipfile.ZIP_STORED
        result = _eval_bytes(fx.zip_bytes(files, extra_infos=[info], extra_payloads={info.filename: b"x"}))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_path_unsafe", result["reason_codes"])

    def test_backslash_alias(self) -> None:
        files = fx.build_file_map()
        result = _eval_bytes(
            fx.zip_bytes(files, name_overrides={"decision_trace.json": "subdir\\decision_trace.json"})
        )
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertTrue(
            "container_path_unsafe" in result["reason_codes"]
            or "container_undeclared_or_missing_member" in result["reason_codes"]
        )

    def test_symlink_attribute(self) -> None:
        files = fx.build_file_map()
        info = zipfile.ZipInfo("link.json")
        info.create_system = 3
        info.external_attr = (0o120777 << 16)
        info.compress_type = zipfile.ZIP_STORED
        result = _eval_bytes(fx.zip_bytes(files, extra_infos=[info], extra_payloads={info.filename: b"x"}))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_path_unsafe", result["reason_codes"])

    def test_encrypted_entry_flag(self) -> None:
        data = bytearray(fx.zip_bytes(fx.build_file_map(), compress=zipfile.ZIP_STORED))
        i = 0
        while True:
            j = data.find(b"PK\x03\x04", i)
            if j < 0:
                break
            flags = int.from_bytes(data[j + 6 : j + 8], "little")
            data[j + 6 : j + 8] = (flags | 0x1).to_bytes(2, "little")
            i = j + 4
        i = 0
        while True:
            j = data.find(b"PK\x01\x02", i)
            if j < 0:
                break
            flags = int.from_bytes(data[j + 8 : j + 10], "little")
            data[j + 8 : j + 10] = (flags | 0x1).to_bytes(2, "little")
            i = j + 4
        result = _eval_bytes(bytes(data))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_encrypted_or_unsupported_compression", result["reason_codes"])

    def test_unsupported_compression(self) -> None:
        data = bytearray(fx.zip_bytes(fx.build_file_map(), compress=zipfile.ZIP_STORED))
        i = 0
        while True:
            j = data.find(b"PK\x03\x04", i)
            if j < 0:
                break
            data[j + 8 : j + 10] = (9).to_bytes(2, "little")
            i = j + 4
        i = 0
        while True:
            j = data.find(b"PK\x01\x02", i)
            if j < 0:
                break
            data[j + 10 : j + 12] = (9).to_bytes(2, "little")
            i = j + 4
        result = _eval_bytes(bytes(data))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_encrypted_or_unsupported_compression", result["reason_codes"])

    def test_unexpected_extra_file(self) -> None:
        files = fx.build_file_map()
        info = zipfile.ZipInfo("extra.json")
        info.compress_type = zipfile.ZIP_STORED
        result = _eval_bytes(fx.zip_bytes(files, extra_infos=[info], extra_payloads={"extra.json": b"{}"}))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_undeclared_or_missing_member", result["reason_codes"])

    def test_entry_count_limit(self) -> None:
        files = fx.build_file_map()
        extras = []
        payloads = {}
        for i in range(MAX_ZIP_ENTRY_COUNT):
            name = f"extra{i:02d}.txt"
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_STORED
            extras.append(info)
            payloads[name] = b"x"
        result = _eval_bytes(fx.zip_bytes(files, extra_infos=extras, extra_payloads=payloads))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_limit_exceeded", result["reason_codes"])

    def test_per_file_size_limit(self) -> None:
        files = fx.build_file_map()
        files["WEAVER_REVIEW_INSTRUCTION.md"] = b"A" * (MAX_UNCOMPRESSED_PER_ENTRY + 1)
        result = _eval_bytes(fx.zip_bytes(files, compress=zipfile.ZIP_STORED))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_limit_exceeded", result["reason_codes"])

    def test_zip_file_size_limit(self) -> None:
        files = fx.build_file_map()
        files["WEAVER_REVIEW_INSTRUCTION.md"] = os.urandom(MAX_ZIP_FILE_BYTES)
        result = _eval_bytes(fx.zip_bytes(files, compress=zipfile.ZIP_STORED))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_limit_exceeded", result["reason_codes"])

    def test_oversized_zip_rejected_before_full_read(self) -> None:
        original = Path.read_bytes
        calls = {"n": 0}

        def wrapped(self: Path) -> bytes:
            calls["n"] += 1
            return original(self)

        Path.read_bytes = wrapped  # type: ignore[method-assign]
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"{fx.PACKAGE_ID}.zip"
                path.write_bytes(b"\x00" * (MAX_ZIP_FILE_BYTES + 1))
                result = evaluate_vector_package_ingress_v0(path)
            self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
            self.assertIn("container_limit_exceeded", result["reason_codes"])
            self.assertEqual(calls["n"], 0)
        finally:
            Path.read_bytes = original  # type: ignore[method-assign]

    def test_compression_ratio_limit(self) -> None:
        files = fx.build_file_map()
        files["WEAVER_REVIEW_INSTRUCTION.md"] = b"A" * 40000
        result = _eval_bytes(fx.zip_bytes(files, compress=zipfile.ZIP_DEFLATED))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("container_limit_exceeded", result["reason_codes"])

    def test_casefold_duplicate_name(self) -> None:
        files = fx.build_file_map()
        info = zipfile.ZipInfo("Decision_Trace.json")
        info.compress_type = zipfile.ZIP_STORED
        result = _eval_bytes(
            fx.zip_bytes(files, extra_infos=[info], extra_payloads={info.filename: files["decision_trace.json"]})
        )
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertTrue(
            "container_duplicate_name" in result["reason_codes"]
            or "container_undeclared_or_missing_member" in result["reason_codes"]
        )


class AuthorityTests(unittest.TestCase):
    def _inflate(self, mutator: Callable) -> dict:
        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutator)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("authority_inflation", result["reason_codes"])
        for value in result["authority"].values():
            self.assertIs(value, False)
        return result

    def test_vr_truth_verified(self) -> None:
        def mutate(objects: dict) -> None:
            objects["verification_result_record"]["truth_verified"] = True

        self._inflate(mutate)

    def test_vr_evidence_admitted(self) -> None:
        def mutate(objects: dict) -> None:
            objects["verification_result_record"]["evidence_admitted"] = True

        self._inflate(mutate)

    def test_vr_replay_authorized(self) -> None:
        def mutate(objects: dict) -> None:
            objects["verification_result_record"]["replay_authorized"] = True

        self._inflate(mutate)

    def test_vr_execution_authorized(self) -> None:
        def mutate(objects: dict) -> None:
            objects["verification_result_record"]["execution_authorized"] = True

        self._inflate(mutate)

    def test_vr_stage6_entered(self) -> None:
        def mutate(objects: dict) -> None:
            objects["verification_result_record"]["stage6_entered"] = True

        self._inflate(mutate)

    def test_rc_truth_verified(self) -> None:
        def mutate(objects: dict) -> None:
            objects["replay_contract"]["authority"]["truth_verified"] = True

        self._inflate(mutate)

    def test_eligibility_not_promoted(self) -> None:
        result = _eval_bytes(fx.valid_zip_bytes())
        blob = json.dumps(result)
        self.assertNotIn("WITNESS", blob)
        self.assertNotIn("C-014", blob)
        self.assertNotIn("ACCEPTED", blob)
        self.assertEqual(result["authority"]["replay_authorized"], False)
        self.assertEqual(result["final_disposition"], "INGRESS_READY")

    def test_pinned_bytes_upgrade_rejected(self) -> None:
        def mutate(objects: dict) -> None:
            objects["verification_result_record"]["verification_result"]["checks"]["pinned_bytes"][
                "status"
            ] = "passed"

        result = _eval_bytes(fx.zip_bytes(fx.build_file_map(mutate)))
        self.assertEqual(result["final_disposition"], "INGRESS_REJECT")
        self.assertIn("boundary_upgrade_forbidden", result["reason_codes"])

    def test_hold_not_emitted(self) -> None:
        result = _eval_bytes(fx.valid_zip_bytes())
        self.assertNotEqual(result["final_disposition"], "INGRESS_HOLD")


class DeterminismTests(unittest.TestCase):
    def test_stable_id_across_paths(self) -> None:
        data = fx.valid_zip_bytes()
        a = _eval_bytes(data, name="vwh-v0-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip")
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "nested"
            other.mkdir()
            path = other / "vwh-v0-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.zip"
            path.write_bytes(data)
            b = evaluate_vector_package_ingress_v0(path)
        self.assertEqual(a["ingress_result_id"], b["ingress_result_id"])
        self.assertEqual(a["final_disposition"], "INGRESS_READY")

    def test_reason_message_does_not_change_id(self) -> None:
        result = _eval_bytes(fx.valid_zip_bytes())
        from result_v0 import compute_ingress_result_id

        clone = dict(result)
        clone["reasons"] = [{"code": "x", "message": "different"}]
        clone["operational"] = {"zip_path": "/elsewhere", "hostname": "host"}
        self.assertEqual(compute_ingress_result_id(result), compute_ingress_result_id(clone))


class RealPackageIntegrationTests(unittest.TestCase):
    def test_current_vector_package_readonly(self) -> None:
        if not REAL_ZIP.is_file():
            self.fail(f"authorized real package ZIP missing: {REAL_ZIP}")
        before = REAL_ZIP.stat()
        parent_listing = set(REAL_ZIP.parent.iterdir())
        result = evaluate_vector_package_ingress_v0(REAL_ZIP)
        after = REAL_ZIP.stat()
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(set(REAL_ZIP.parent.iterdir()), parent_listing)
        self.assertEqual(result["final_disposition"], "INGRESS_READY")
        self.assertEqual(result["source_package_id"], "vwh-v0-383a940e88a49dbbb9fd4250420b038e")
        self.assertIn("L1_approved_request_bytes_absent", result["limitation_codes"])
        self.assertIn("L2_payload_digest_not_recomputed", result["limitation_codes"])
        self.assertIn("L3_pinned_bytes_not_checked", result["limitation_codes"])
        for value in result["authority"].values():
            self.assertIs(value, False)
        self.assertEqual(validate_vector_ingress_result_v0(result), [])
        self.assertNotEqual(result["final_disposition"], "INGRESS_HOLD")


if __name__ == "__main__":
    unittest.main()
