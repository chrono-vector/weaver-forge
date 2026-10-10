"""Schema contract tests for INR-HER-001 Phase 1."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docs.inr_001.schema_check import check as schema_check
from docs.inr_her_001.supervisor_her_v1 import (
    SURFACE_ROLES,
    synthetic_event,
)
from docs.inr_her_001.validate_her_v1 import (
    ALLOWED_SCHEMA_KEYS,
    HerSchemaContractError,
    assert_schema_contract,
    load_schemas,
    schema_errors,
)

SOURCE_HEAD = "38131191710aad087c274fc3ffc95e80f1c140cf"
ACCEPTED_PATHS = (
    "docs/inr_001/INR_001_CLOSURE_MATRIX.md",
    "docs/inr_001/INR_001_EXTERNAL_RUN_PROCEDURE.md",
    "docs/inr_001/INR_001_FINAL_CLOSURE_ADDENDUM.md",
    "docs/inr_001/INR_001_IMPLEMENTATION_MATRIX_R3.md",
    "docs/inr_001/INR_001_PROFILE_REFREEZE_R3.md",
    "docs/inr_001/INR_AWI_001_HUMAN_FINAL.md",
    "docs/inr_001/capture_inr_v0.py",
    "docs/inr_001/input_cases.py",
    "docs/inr_001/ledger.py",
    "docs/inr_001/origin/psm_001_origin_reference_set_v0.json",
    "docs/inr_001/profiles/psm_001_inr_target_profile_v0.json",
    "docs/inr_001/runtime_probe.py",
    "docs/inr_001/schema/inr_event_v0.schema.json",
    "docs/inr_001/schema/inr_origin_reference_v0.schema.json",
    "docs/inr_001/schema/inr_target_profile_v0.schema.json",
    "docs/inr_001/schema_check.py",
    "docs/inr_001/supervisor_inr_v0.py",
    "docs/inr_001/tests/inr_r3_support.py",
    "docs/inr_001/tests/test_property_boundary_r3.py",
    "docs/inr_001/tests/test_staged_lock_awi.py",
    "docs/inr_001/tests/test_synthetic_mint_r3.py",
    "docs/inr_001/tests/test_validate_inr_v0.py",
    "docs/inr_001/validate_inr_v0.py",
    "docs/inr_001/xr/EXTERNAL_RUN_BUNDLE_PROCEDURE.md",
    "docs/inr_001/xr/INR_XR_001_IMPLEMENTATION_MATRIX.md",
    "docs/inr_001/xr/collect_bundle_v0.py",
    "docs/inr_001/xr/provider_github_v0.py",
    "docs/inr_001/xr/schema/external_run_manifest_v0.schema.json",
    "docs/inr_001/xr/tests/test_validate_external_run_v0.py",
    "docs/inr_001/xr/validate_external_run_v0.py",
    "docs/inr_001/xr/xr_verifier_v0.py",
    "docs/portfolio_state/validate_psm_v0.py",
    "docs/wacp_001/SCOPE_MANIFEST_EXAMPLE.json",
    "docs/wacp_001/WACP_001.md",
    "tools/wacp/cli.py",
    "tools/wacp/generator.py",
)


def _walk(schema: object, found: list[tuple[str, object]]) -> None:
    if type(schema) is not dict:
        return
    if "const" in schema or "enum" in schema:
        found.append(("typed", schema))
    for value in schema.values():
        if type(value) is dict:
            _walk(value, found)
        elif type(value) is list:
            for item in value:
                if type(item) is dict:
                    _walk(item, found)


class SchemaHerTests(unittest.TestCase):
    def test_four_schemas_load_with_typed_constants(self) -> None:
        loaded = load_schemas()
        self.assertEqual(
            set(loaded),
            {
                "inr.event.v0.r4",
                "inr.supervisor.result.v0.r4",
                "inr.her.surface_record.v0",
                "inr.her.predicate_result.v0",
            },
        )
        for schema in loaded.values():
            self.assertNotIn("$schema", schema)
            self.assertNotIn("title", schema)
            self.assertTrue(set(schema) <= ALLOWED_SCHEMA_KEYS)
            found: list[tuple[str, object]] = []
            _walk(schema, found)
            for _kind, node in found:
                self.assertIn("type", node)

    def test_surface_roles_match_the_schema_enum(self) -> None:
        schema = load_schemas()["inr.her.surface_record.v0"]
        self.assertEqual(tuple(schema["properties"]["surface_role"]["enum"]), SURFACE_ROLES)

    def test_integer_does_not_satisfy_typed_boolean_const(self) -> None:
        self.assertEqual(schema_check(1, {"type": "boolean", "const": True}), ["$: wrong type"])
        self.assertEqual(schema_check(0, {"type": "boolean", "const": False}), ["$: wrong type"])
        self.assertEqual(schema_check(True, {"type": "boolean", "const": True}), [])
        self.assertEqual(schema_check(False, {"type": "boolean", "const": False}), [])

    def test_untyped_const_is_outside_the_her_contract(self) -> None:
        with self.assertRaises(HerSchemaContractError):
            assert_schema_contract({"const": True})
        with self.assertRaises(HerSchemaContractError):
            assert_schema_contract({"type": "object", "properties": {}})
        with self.assertRaises(HerSchemaContractError):
            assert_schema_contract({"title": "x", "type": "string"})
        self.assertEqual(schema_check(1, {"const": True}), [])
        self.assertEqual(schema_check(0, {"const": False}), [])

    def test_synthetic_event_matches_r4_schemas(self) -> None:
        event = synthetic_event()
        self.assertEqual(schema_errors(event), [])
        self.assertEqual(schema_check(1, load_schemas()["inr.her.surface_record.v0"]["properties"]["u_write_denied"]), ["$: wrong type"])

    def test_r3_event_schema_constant_remains(self) -> None:
        text = (ROOT / "docs/inr_001/schema/inr_event_v0.schema.json").read_text(encoding="utf-8")
        self.assertIn('"const": "inr.event.v0.r3"', text)

    def test_accepted_r3_paths_match_the_freeze_commit(self) -> None:
        self.assertEqual(len(ACCEPTED_PATHS), 36)
        completed = subprocess.run(
            ["git", "diff", "--name-only", SOURCE_HEAD, "--", *ACCEPTED_PATHS],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "")

    def test_phase1_does_not_create_the_external_workflow(self) -> None:
        workflow = ROOT / ".github" / "workflows" / "inr-her-001-external-run.yml"
        self.assertFalse(workflow.exists())

    def test_verifier_modules_do_not_launch_processes(self) -> None:
        package = ROOT / "docs" / "inr_her_001"
        for name in ("supervisor_her_v1.py", "collect_bundle_her_v1.py"):
            text = (package / name).read_text(encoding="utf-8")
            self.assertNotIn("subprocess", text)
            self.assertNotIn("ctypes", text)
            self.assertNotIn("urllib", text)
            self.assertNotIn("socket", text)
            self.assertNotIn("CreateProcess", text)
            self.assertNotIn("open(", text)
            self.assertNotIn("import supervisor_inr_v0", text)
            self.assertNotIn("from docs.inr_001.supervisor_inr_v0", text)
        validator = (package / "validate_her_v1.py").read_text(encoding="utf-8")
        self.assertNotIn("import supervisor_inr_v0", validator)
        self.assertIn("from docs.inr_001.schema_check import check as schema_check", validator)


if __name__ == "__main__":
    unittest.main()
