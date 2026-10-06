"""Focused SEIC-001 closure, regression-control, and mutation tests."""

from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from audit_lifecycle.epistemic import evaluator_closure as closure
from audit_lifecycle.epistemic.serialize import canonical_dumps


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class EvaluatorClosureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="seic-001-")
        self.sandbox = Path(self._temporary.name)
        self.root = self.sandbox / "repository"
        self.trusted = self.sandbox / "trusted-epochs"
        self.root.mkdir()
        self.trusted.mkdir()
        self._git("init", "-q")
        self._git("config", "user.email", "seic@example.invalid")
        self._git("config", "user.name", "SEIC Test")
        self.checker_bytes = Path(closure.__file__).read_bytes()
        self.base_files: dict[str, bytes] = {
            closure.CHECKER_RELATIVE_PATH: self.checker_bytes,
            "config/evaluator_epoch.json": b"trusted epoch declaration marker\n",
            "semantic/__init__.py": b"",
            "semantic/evaluator.py": (
                b"from . import helper\n"
                b"VALUE = helper.VALUE\n"
                b"SCHEMA = open('semantic/schema.json', 'rb').read()\n"
                b"CONFIG = open('semantic/config.json', 'rb').read()\n"
                b"TOKENS = open('semantic/tokenizer.txt', 'rb').read()\n"
                b"UNITS = open('semantic/units.json', 'rb').read()\n"
                b"GENERATOR = open('semantic/generator.txt', 'rb').read()\n"
            ),
            "semantic/helper.py": b"VALUE = 1\n",
            "semantic/schema.json": b'{"type":"number"}\n',
            "semantic/config.json": b'{"threshold":3}\n',
            "semantic/tokenizer.txt": b"alpha\n",
            "semantic/units.json": b'{"distance":"m"}\n',
            "semantic/generator.txt": b"template-v1\n",
            "ordinary/source.py": b"VALUE = 'ordinary'\n",
        }
        self._write_files(self.base_files)
        self.base = self._commit("accepted evaluator base")
        self.epoch = self._epoch_bytes()

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def _git(self, *arguments: str) -> str:
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            self.fail(result.stderr or result.stdout)
        return result.stdout.strip()

    def _write_files(self, files: dict[str, bytes | None]) -> None:
        for relative_path, content in files.items():
            path = self.root / relative_path
            if content is None:
                path.unlink()
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def _commit(self, message: str, files: dict[str, bytes | None] | None = None) -> str:
        if files:
            self._write_files(files)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)
        return self._git("rev-parse", "HEAD")

    def _epoch_record(
        self,
        *,
        epoch_id: str = "SEIC-EPOCH-TEST-001",
        approval_status: str = "HUMAN_APPROVED",
        evaluator_source: bytes | None = None,
        extra_ess: dict[str, bytes] | None = None,
        allowed_external: list[str] | None = None,
    ) -> dict:
        content = dict(self.base_files)
        if evaluator_source is not None:
            content["semantic/evaluator.py"] = evaluator_source
        if extra_ess:
            content.update(extra_ess)
        ess_paths = sorted(
            [
                closure.CHECKER_RELATIVE_PATH,
                "config/evaluator_epoch.json",
                "semantic/__init__.py",
                "semantic/evaluator.py",
                "semantic/helper.py",
                "semantic/schema.json",
                "semantic/config.json",
                "semantic/tokenizer.txt",
                "semantic/units.json",
                "semantic/generator.txt",
                *(extra_ess or {}).keys(),
            ],
            key=lambda item: item.encode("utf-8"),
        )
        return {
            "schema_version": "evaluator_epoch.v0",
            "authority": False,
            "epoch_id": epoch_id,
            "accepted_base_commit": self.base,
            "approval_status": approval_status,
            "human_approval_ref": "HUMAN-SEIC-TEST-001",
            "checker": {
                "source": "ACCEPTED_BASE",
                "relative_path": closure.CHECKER_RELATIVE_PATH,
                "sha256": _sha(self.checker_bytes),
            },
            "evaluator_entrypoints": ["semantic/evaluator.py"],
            "ess": [
                {"relative_path": path, "sha256": _sha(content[path])}
                for path in ess_paths
            ],
            "semantic_config": {
                "caller_semantic_input": "REJECT",
                "non_semantic_external_imports": sorted(allowed_external or []),
            },
            "closure_policy": {
                "epoch_declaration_paths": ["config/evaluator_epoch.json"],
                "non_semantic_paths": ["ordinary"],
            },
        }

    def _epoch_bytes(self, **overrides) -> bytes:
        return canonical_dumps(self._epoch_record(**overrides)).encode("utf-8")

    def _evaluate(
        self,
        proposal: str | None = None,
        epoch: bytes | None = None,
        *,
        caller_semantic_input=None,
    ) -> dict:
        epoch_bytes = self.epoch if epoch is None else epoch
        epoch_path = self.trusted / f"{_sha(epoch_bytes)}.json"
        if not epoch_path.exists():
            epoch_path.write_bytes(epoch_bytes)
        return closure.evaluate_closure(
            self.root,
            epoch_path,
            self.base if proposal is None else proposal,
            caller_semantic_input=caller_semantic_input,
        )

    def _change(self, path: str, content: bytes) -> dict:
        proposal = self._commit(f"change {path}", {path: content})
        return self._evaluate(proposal)

    def _replace_base(self, files: dict[str, bytes], *, allowed_external=None) -> None:
        self._write_files(files)
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files.update(files)
        self.epoch = self._epoch_bytes(
            evaluator_source=files.get("semantic/evaluator.py"),
            extra_ess={
                path: content
                for path, content in files.items()
                if path not in self.base_files or path.startswith("semantic/helper/")
            }
            or None,
            allowed_external=allowed_external,
        )

    def _assert_disposition(self, expected: str, receipt: dict) -> None:
        closure.validate_closure_receipt(receipt)
        self.assertEqual(expected, receipt["disposition"])
        self.assertIs(receipt["authority"], False)

    def _assert_mutant_killed(self, expected: str, actual: str) -> None:
        with self.assertRaises(AssertionError):
            self.assertEqual(expected, actual)

    def test_schema_change_is_closure_hit(self) -> None:
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/schema.json", b'{"type":"string"}\n')
        )

    def test_threshold_config_change_is_closure_hit(self) -> None:
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/config.json", b'{"threshold":4}\n')
        )

    def test_tokenizer_change_is_closure_hit(self) -> None:
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/tokenizer.txt", b"beta\n")
        )

    def test_unit_table_change_is_closure_hit(self) -> None:
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/units.json", b'{"distance":"ft"}\n')
        )

    def test_generator_input_change_is_closure_hit(self) -> None:
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/generator.txt", b"template-v2\n")
        )

    def test_imported_helper_change_is_closure_hit(self) -> None:
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/helper.py", b"VALUE = 2\n")
        )

    def test_shadow_module_is_unknown_reach(self) -> None:
        extra = {"semantic/helper/__init__.py": b"VALUE = 1\n"}
        self._write_files(extra)
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files.update(extra)
        self.epoch = self._epoch_bytes(extra_ess=extra)
        self._assert_disposition("UNKNOWN_REACH", self._evaluate())

    def test_proposal_added_shadow_module_is_unknown_reach(self) -> None:
        proposal = self._commit(
            "add proposal shadow", {"semantic/helper/__init__.py": b"VALUE = 99\n"}
        )
        receipt = self._evaluate(proposal)
        self._assert_disposition("UNKNOWN_REACH", receipt)
        self.assertTrue(
            any("proposal-local shadow module" in item for item in receipt["unknown_reach"])
        )

    def test_dynamic_plugin_is_unknown_reach(self) -> None:
        source = b"import importlib\nPLUGIN = importlib.import_module('plug')\n"
        self._write_files({"semantic/evaluator.py": source})
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files["semantic/evaluator.py"] = source
        self.epoch = self._epoch_bytes(
            evaluator_source=source, allowed_external=["importlib"]
        )
        self._assert_disposition("UNKNOWN_REACH", self._evaluate())

    def test_caller_semantic_input_is_rejected(self) -> None:
        receipt = self._evaluate(caller_semantic_input={"threshold": 99})
        self._assert_disposition("CALLER_SEMANTIC_INPUT", receipt)

    def test_ess_declaration_tampering_is_non_pass(self) -> None:
        receipt = self._change(
            "config/evaluator_epoch.json", b"proposal-local epoch declaration\n"
        )
        self._assert_disposition("CLOSURE_HIT", receipt)

    def test_checker_tampering_is_non_pass(self) -> None:
        receipt = self._change(
            closure.CHECKER_RELATIVE_PATH, self.checker_bytes + b"\n# proposal edit\n"
        )
        self._assert_disposition("CLOSURE_HIT", receipt)

    def test_commit_splitting_remains_relative_to_epoch(self) -> None:
        self._commit("semantic first commit", {"semantic/config.json": b'{"threshold":7}\n'})
        proposal = self._commit("unrelated second commit", {"ordinary/source.py": b"VALUE = 2\n"})
        receipt = self._evaluate(proposal)
        self._assert_disposition("CLOSURE_HIT", receipt)
        self.assertIn("semantic/config.json", receipt["closure_hits"])

    def test_unrelated_source_change_passes(self) -> None:
        receipt = self._change("ordinary/source.py", b"VALUE = 'changed'\n")
        self._assert_disposition("PASS", receipt)

    def test_malformed_epoch_is_invalid(self) -> None:
        self._assert_disposition("INVALID", self._evaluate(epoch=b"{}"))

    def test_direct_epoch_bytes_are_invalid(self) -> None:
        receipt = closure.evaluate_closure(self.root, self.epoch, self.base)
        self._assert_disposition("INVALID", receipt)

    def test_proposal_local_epoch_location_is_invalid(self) -> None:
        proposal_epoch = self.root / "proposal-epoch.json"
        proposal_epoch.write_bytes(self.epoch)
        receipt = closure.evaluate_closure(self.root, proposal_epoch, self.base)
        self._assert_disposition("INVALID", receipt)

    def test_missing_ess_file_is_invalid(self) -> None:
        record = self._epoch_record()
        record["ess"].append(
            {"relative_path": "semantic/zz_missing.json", "sha256": "0" * 64}
        )
        record["ess"].sort(key=lambda item: item["relative_path"].encode("utf-8"))
        epoch = canonical_dumps(record).encode("utf-8")
        self._assert_disposition("INVALID", self._evaluate(epoch=epoch))

    def test_ess_hash_mismatch_is_invalid(self) -> None:
        record = self._epoch_record()
        for entry in record["ess"]:
            if entry["relative_path"] == "semantic/schema.json":
                entry["sha256"] = "0" * 64
        epoch = canonical_dumps(record).encode("utf-8")
        self._assert_disposition("INVALID", self._evaluate(epoch=epoch))

    def test_wrong_checker_is_epoch_mismatch(self) -> None:
        record = self._epoch_record()
        record["checker"] = {
            "source": "ACCEPTED_BASE",
            "relative_path": "semantic/evaluator.py",
            "sha256": _sha(self.base_files["semantic/evaluator.py"]),
        }
        epoch = canonical_dumps(record).encode("utf-8")
        self._assert_disposition("EPOCH_MISMATCH", self._evaluate(epoch=epoch))

    def test_missing_epoch_base_is_epoch_mismatch(self) -> None:
        record = self._epoch_record()
        record["accepted_base_commit"] = "f" * 40
        epoch = canonical_dumps(record).encode("utf-8")
        self._assert_disposition("EPOCH_MISMATCH", self._evaluate(epoch=epoch))

    def test_unapproved_successor_requires_human_review(self) -> None:
        epoch = self._epoch_bytes(approval_status="UNAPPROVED")
        self._assert_disposition("REQUIRE_HUMAN_REVIEW", self._evaluate(epoch=epoch))

    def test_old_receipt_remains_bound_to_old_epoch(self) -> None:
        first = self._evaluate()
        first_copy = canonical_dumps(first)
        second_epoch = self._epoch_bytes(epoch_id="SEIC-EPOCH-TEST-002")
        second = self._evaluate(epoch=second_epoch)
        self.assertNotEqual(first["epoch_id"], second["epoch_id"])
        self.assertNotEqual(first["receipt_digest"], second["receipt_digest"])
        self.assertEqual(first_copy, canonical_dumps(first))
        closure.validate_closure_receipt(first)

    def test_unresolved_import_is_unknown_reach(self) -> None:
        source = b"from . import missing\nVALUE = missing.VALUE\n"
        self._write_files({"semantic/evaluator.py": source})
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files["semantic/evaluator.py"] = source
        self.epoch = self._epoch_bytes(evaluator_source=source)
        self._assert_disposition("UNKNOWN_REACH", self._evaluate())

    def test_proposal_cannot_hide_dependency_by_editing_ess(self) -> None:
        receipt = self._change(
            "config/evaluator_epoch.json", b'{"ess":[]}\n'
        )
        self._assert_disposition("CLOSURE_HIT", receipt)

    def test_proposal_cannot_edit_checker_to_bless_itself(self) -> None:
        receipt = self._change(
            closure.CHECKER_RELATIVE_PATH,
            self.checker_bytes.replace(b'"CLOSURE_HIT"', b'"PASS_______"', 1),
        )
        self._assert_disposition("CLOSURE_HIT", receipt)

    def test_protected_state_unchanged_on_failure(self) -> None:
        before_status = self._git("status", "--porcelain=v1", "--untracked-files=all")
        before_checker = (self.root / closure.CHECKER_RELATIVE_PATH).read_bytes()
        record = self._epoch_record()
        record["ess"][0]["sha256"] = "0" * 64
        epoch = canonical_dumps(record).encode("utf-8")
        self._assert_disposition("INVALID", self._evaluate(epoch=epoch))
        self.assertEqual(before_status, self._git("status", "--porcelain=v1", "--untracked-files=all"))
        self.assertEqual(before_checker, (self.root / closure.CHECKER_RELATIVE_PATH).read_bytes())

    def test_dynamic_semantic_read_is_unknown_reach(self) -> None:
        source = b"path = 'semantic/schema.json'\nDATA = open(path, 'rb').read()\n"
        self._write_files({"semantic/evaluator.py": source})
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files["semantic/evaluator.py"] = source
        self.epoch = self._epoch_bytes(evaluator_source=source)
        self._assert_disposition("UNKNOWN_REACH", self._evaluate())

    def test_pathlib_semantic_read_outside_ess_is_unknown_reach(self) -> None:
        source = (
            b"from pathlib import Path\n"
            b"DATA = Path('semantic/generated.json').read_bytes()\n"
        )
        self._write_files({"semantic/evaluator.py": source})
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files["semantic/evaluator.py"] = source
        self.epoch = self._epoch_bytes(
            evaluator_source=source, allowed_external=["pathlib"]
        )
        self._assert_disposition("UNKNOWN_REACH", self._evaluate())

    def test_receipt_has_no_authorizing_disposition(self) -> None:
        self.assertEqual(
            {
                "PASS",
                "CLOSURE_HIT",
                "UNKNOWN_REACH",
                "CALLER_SEMANTIC_INPUT",
                "EPOCH_MISMATCH",
                "REQUIRE_HUMAN_REVIEW",
                "INVALID",
            },
            set(closure.DISPOSITIONS),
        )
        receipt = self._evaluate()
        self.assertFalse(receipt["authority"])
        self.assertNotIn("authorization", receipt)
        self.assertNotIn("merge_approval", receipt)

    def test_mutant_skip_ess_member_comparison_is_killed(self) -> None:
        record = self._epoch_record()
        record["ess"][0]["sha256"] = "0" * 64
        epoch = canonical_dumps(record).encode("utf-8")
        with mock.patch.object(closure, "_verify_ess_inventory", return_value=None):
            actual = self._evaluate(epoch=epoch)["disposition"]
        self._assert_mutant_killed("INVALID", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_allow_proposal_local_checker_is_killed(self) -> None:
        proposal = self._commit(
            "edit checker", {closure.CHECKER_RELATIVE_PATH: self.checker_bytes + b"\n# edit\n"}
        )
        original = closure._changed_paths

        def mutant(root, base, target):
            return tuple(
                path for path in original(root, base, target)
                if path != closure.CHECKER_RELATIVE_PATH
            )

        with mock.patch.object(closure, "_changed_paths", side_effect=mutant):
            actual = self._evaluate(proposal)["disposition"]
        self._assert_mutant_killed("CLOSURE_HIT", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_allow_proposal_local_ess_declaration_is_killed(self) -> None:
        path = "config/evaluator_epoch.json"
        proposal = self._commit("edit epoch declaration", {path: b"proposal epoch\n"})
        original = closure._changed_paths

        def mutant(root, base, target):
            return tuple(item for item in original(root, base, target) if item != path)

        with mock.patch.object(closure, "_changed_paths", side_effect=mutant):
            actual = self._evaluate(proposal)["disposition"]
        self._assert_mutant_killed("CLOSURE_HIT", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_convert_unknown_reach_to_pass_is_killed(self) -> None:
        source = b"import importlib\nPLUGIN = importlib.import_module('plug')\n"
        self._write_files({"semantic/evaluator.py": source})
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files["semantic/evaluator.py"] = source
        self.epoch = self._epoch_bytes(
            evaluator_source=source, allowed_external=["importlib"]
        )
        with mock.patch.object(closure, "_analyze_reach", return_value=()):
            actual = self._evaluate()["disposition"]
        self._assert_mutant_killed("UNKNOWN_REACH", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_accept_caller_semantic_input_is_killed(self) -> None:
        with mock.patch.object(
            closure, "_caller_semantic_input_present", return_value=False
        ):
            actual = self._evaluate(
                caller_semantic_input={"threshold": 99}
            )["disposition"]
        self._assert_mutant_killed("CALLER_SEMANTIC_INPUT", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_compare_against_proposal_parent_is_killed(self) -> None:
        self._commit("semantic first commit", {"semantic/config.json": b'{"threshold":7}\n'})
        proposal = self._commit("unrelated second commit", {"ordinary/source.py": b"VALUE = 2\n"})
        with mock.patch.object(
            closure, "_changed_paths", side_effect=closure._changed_paths_from_parent
        ):
            actual = self._evaluate(proposal)["disposition"]
        self._assert_mutant_killed("CLOSURE_HIT", actual)
        self.assertEqual("PASS", actual)


if __name__ == "__main__":
    unittest.main()
