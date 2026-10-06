"""Focused SEIC-001 closure, regression-control, and mutation tests."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from audit_lifecycle.epistemic import evaluator_closure as closure
from audit_lifecycle.epistemic.serialize import canonical_dumps


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# Sentinel: the test plays the Human approver and binds the exact epoch bytes.
_BOUND = object()


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
            },
        }

    def _epoch_bytes(self, **overrides) -> bytes:
        return canonical_dumps(self._epoch_record(**overrides)).encode("utf-8")

    def _trusted_epoch_path(self, epoch_bytes: bytes) -> Path:
        epoch_path = self.trusted / f"{_sha(epoch_bytes)}.json"
        if not epoch_path.exists():
            epoch_path.write_bytes(epoch_bytes)
        return epoch_path

    def _evaluate(
        self,
        proposal: str | None = None,
        epoch: bytes | None = None,
        *,
        caller_semantic_input=None,
        binding=_BOUND,
    ) -> dict:
        """Evaluate with the independently protected Human approval binding.

        By default the binding is the SHA-256 of the exact epoch bytes used;
        ``binding=None`` omits it and any other value is passed unchanged.
        """
        epoch_bytes = self.epoch if epoch is None else epoch
        epoch_path = self._trusted_epoch_path(epoch_bytes)
        trusted = _sha(epoch_bytes) if binding is _BOUND else binding
        return closure.evaluate_closure(
            self.root,
            epoch_path,
            self.base if proposal is None else proposal,
            trusted_epoch_sha256=trusted,
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
        def mutant(root, _base, target):
            parent = str(closure._git(root, "rev-parse", f"{target}^")).strip()
            return closure._changed_paths_between(root, parent, target)

        with mock.patch.object(closure, "_changed_paths", side_effect=mutant):
            actual = self._evaluate(proposal)["disposition"]
        self._assert_mutant_killed("CLOSURE_HIT", actual)
        self.assertEqual("PASS", actual)

    # ------------------------------------------------------------------
    # R1 helpers
    # ------------------------------------------------------------------

    def _set_evaluator(
        self,
        source: bytes,
        *,
        allowed_external: list[str] | None = None,
        extra: dict[str, bytes] | None = None,
    ) -> None:
        files = {"semantic/evaluator.py": source, **(extra or {})}
        self._write_files(files)
        self._git("add", "-A")
        self._git("commit", "--amend", "-q", "--no-edit")
        self.base = self._git("rev-parse", "HEAD")
        self.base_files.update(files)
        self.epoch = self._epoch_bytes(
            evaluator_source=source,
            extra_ess=extra,
            allowed_external=allowed_external,
        )

    def _protected_state(self) -> tuple:
        trusted = tuple(
            sorted((path.name, path.read_bytes()) for path in self.trusted.iterdir())
        )
        return (
            self._git("rev-parse", "HEAD"),
            self._git("status", "--porcelain=v1", "--untracked-files=all"),
            self._git("for-each-ref"),
            (self.root / closure.CHECKER_RELATIVE_PATH).read_bytes(),
            Path(closure.__file__).read_bytes(),
            trusted,
        )

    def _assert_protected_non_pass(self, expected: str, proposal=None, **kwargs) -> dict:
        """Evaluate one failure case and require unchanged protected state."""
        epoch = kwargs.get("epoch")
        self._trusted_epoch_path(self.epoch if epoch is None else epoch)
        before = self._protected_state()
        receipt = self._evaluate(proposal, **kwargs)
        self.assertEqual(before, self._protected_state())
        self._assert_disposition(expected, receipt)
        self.assertNotEqual("PASS", receipt["disposition"])
        return receipt

    def _attacker_epoch(self) -> bytes:
        """Canonical epoch that self-declares approval and selects its own ESS."""
        record = self._epoch_record()
        keep = {
            closure.CHECKER_RELATIVE_PATH,
            "config/evaluator_epoch.json",
            "semantic/helper.py",
        }
        record["approval_status"] = "HUMAN_APPROVED"
        record["human_approval_ref"] = "HUMAN-FORGED-BY-ATTACKER"
        record["evaluator_entrypoints"] = ["semantic/helper.py"]
        record["ess"] = [entry for entry in record["ess"] if entry["relative_path"] in keep]
        return canonical_dumps(record).encode("utf-8")

    # ------------------------------------------------------------------
    # R1-1 trusted epoch approval binding
    # ------------------------------------------------------------------

    def test_r1_self_declared_approval_without_binding_is_non_pass(self) -> None:
        record = self._epoch_record()
        self.assertEqual("HUMAN_APPROVED", record["approval_status"])
        proposal = self._commit("ordinary change", {"ordinary/source.py": b"VALUE = 3\n"})
        receipt = self._assert_protected_non_pass(
            "REQUIRE_HUMAN_REVIEW", proposal, binding=None
        )
        self.assertEqual("UNRESOLVED", receipt["epoch_id"])
        self._assert_disposition("PASS", self._evaluate(proposal))

    def test_r1_substituted_epoch_bytes_are_rejected(self) -> None:
        approved = _sha(self.epoch)
        substituted = self._epoch_bytes(epoch_id="SEIC-EPOCH-SUBSTITUTED")
        self._assert_protected_non_pass(
            "EPOCH_MISMATCH", epoch=substituted, binding=approved
        )
        reformatted = json.dumps(self._epoch_record(), indent=2).encode("utf-8")
        self._assert_protected_non_pass(
            "EPOCH_MISMATCH", epoch=reformatted, binding=approved
        )
        self._assert_protected_non_pass("INVALID", binding=approved.upper())
        self._assert_protected_non_pass("INVALID", binding=approved.encode("ascii"))

    def test_r1_changed_approval_fields_cannot_establish_trust(self) -> None:
        approved = _sha(self.epoch)
        record = self._epoch_record()
        record["human_approval_ref"] = "HUMAN-FORGED-999"
        forged_ref = canonical_dumps(record).encode("utf-8")
        self._assert_protected_non_pass("EPOCH_MISMATCH", epoch=forged_ref, binding=approved)
        self._assert_protected_non_pass("REQUIRE_HUMAN_REVIEW", epoch=forged_ref, binding=None)

        unapproved = self._epoch_bytes(approval_status="UNAPPROVED")
        self._assert_protected_non_pass("REQUIRE_HUMAN_REVIEW", epoch=unapproved)
        flipped = unapproved.replace(b'"UNAPPROVED"', b'"HUMAN_APPROVED"', 1)
        self.assertNotEqual(unapproved, flipped)
        self._assert_protected_non_pass(
            "EPOCH_MISMATCH", epoch=flipped, binding=_sha(unapproved)
        )
        self._assert_protected_non_pass("REQUIRE_HUMAN_REVIEW", epoch=flipped, binding=None)

    def test_r1_attacker_selected_ess_in_self_declared_epoch_cannot_pass(self) -> None:
        proposal = self._commit(
            "semantic threshold change", {"semantic/config.json": b'{"threshold":0}\n'}
        )
        attacker = self._attacker_epoch()
        self._assert_protected_non_pass(
            "REQUIRE_HUMAN_REVIEW", proposal, epoch=attacker, binding=None
        )
        self._assert_protected_non_pass(
            "EPOCH_MISMATCH", proposal, epoch=attacker, binding=_sha(self.epoch)
        )
        self._assert_protected_non_pass("CLOSURE_HIT", proposal)

    # ------------------------------------------------------------------
    # R1-2 closed evaluator syntax / reach profile
    # ------------------------------------------------------------------

    def test_r1_import_as_reach_is_handled(self) -> None:
        self._set_evaluator(b"import semantic.helper as h\nVALUE = h.VALUE\n")
        self._assert_disposition("PASS", self._evaluate())
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/helper.py", b"VALUE = 5\n")
        )

    def test_r1_import_as_outside_ess_or_machinery_is_unknown_reach(self) -> None:
        self._set_evaluator(b"import ordinary.source as s\nVALUE = s.VALUE\n")
        receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
        self.assertIn("repo-local import outside ESS: ordinary/source.py", receipt["unknown_reach"])
        self._set_evaluator(
            b"import importlib as il\nPLUGIN = il.import_module('plug')\n",
            allowed_external=["importlib"],
        )
        receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
        self.assertIn("dynamic semantic loading: semantic/evaluator.py", receipt["unknown_reach"])

    def test_r1_from_import_as_reach_is_handled(self) -> None:
        self._set_evaluator(b"from semantic import helper as h\nVALUE = h.VALUE\n")
        self._assert_disposition("PASS", self._evaluate())
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/helper.py", b"VALUE = 6\n")
        )

    def test_r1_from_import_as_unknown_constructs_are_unknown_reach(self) -> None:
        cases = {
            "import_module_alias": (
                b"from importlib import import_module as im\nPLUGIN = im('plug')\n",
                ["importlib"],
            ),
            "member_outside_ess": (
                b"from ordinary import source as s\nVALUE = s.VALUE\n",
                [],
            ),
            "pathlib_alias_outside_ess": (
                b"from pathlib import Path as P\n"
                b"DATA = P('semantic/generated.json').read_bytes()\n",
                ["pathlib"],
            ),
        }
        for name, (source, allowed) in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=allowed)
                self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r1_aliased_pathlib_read_inside_ess_is_understood(self) -> None:
        self._set_evaluator(
            b"from pathlib import Path as P\n"
            b"DATA = P('semantic/schema.json').read_bytes()\n",
            allowed_external=["pathlib"],
        )
        self._assert_disposition("PASS", self._evaluate())
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/schema.json", b'{"type":"null"}\n')
        )

    def test_r1_aliased_sys_path_manipulation_is_unknown_reach(self) -> None:
        cases = {
            "import_sys_as": b"import sys as s\ns.path.insert(0, 'plugins')\n",
            "from_sys_import_path_as": b"from sys import path as p\np.append('plugins')\n",
            "slice_assignment": b"from sys import path as p\np[:0] = ['plugins']\n",
            "unaliased": b"import sys\nsys.path.insert(0, 'plugins')\n",
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=["sys"])
                receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
                self.assertTrue(
                    any("reserved semantic machinery import: sys" in item for item in receipt["unknown_reach"])
                )

    def test_r1_closed_profile_rejects_unsupported_semantic_constructs(self) -> None:
        allowed = ["importlib", "json", "pkg_resources", "plugins_lib", "runpy"]
        cases = {
            "star_import": b"from semantic.helper import *\n",
            "eval": b"VALUE = eval('1')\n",
            "exec": b"exec('VALUE = 1')\n",
            "compile": b"CODE = compile('1', 'x', 'eval')\n",
            "globals": b"SCOPE = globals()\n",
            "dunder_import": b"MODULE = __import__('json')\n",
            "builtin_alias": b"loader = __import__\nMODULE = loader('json')\n",
            "introspection": b"CLASSES = object.__subclasses__()\n",
            "dynamic_getattr": b"import json\nNAME = 'loads'\nF = getattr(json, NAME)\n",
            "entry_points_alias": (
                b"from importlib import metadata as md\nPLUGINS = md.entry_points()\n"
            ),
            "pkg_resources": (
                b"import pkg_resources as pr\nPLUGINS = pr.iter_entry_points('seic')\n"
            ),
            "plugin_discovery_method": (
                b"import plugins_lib\nPLUGINS = plugins_lib.entry_points(group='seic')\n"
            ),
            "runpy": b"import runpy\nSCOPE = runpy.run_path('plugin.py')\n",
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=allowed)
                self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r1_generated_input_outside_ess_is_unknown_reach(self) -> None:
        self._set_evaluator(b"DATA = open('build/generated_policy.json', 'rb').read()\n")
        receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
        self.assertIn(
            "semantic data read outside ESS: build/generated_policy.json",
            receipt["unknown_reach"],
        )

    # ------------------------------------------------------------------
    # R1-3 environment / process and indirect caller semantics
    # ------------------------------------------------------------------

    def test_r1_environment_derived_semantic_input_is_non_pass(self) -> None:
        self._assert_protected_non_pass(
            "CALLER_SEMANTIC_INPUT", caller_semantic_input=os.environ
        )
        cases = {
            "os_alias_environ": (
                b"import os as o\nTHRESHOLD = o.environ.get('SEIC_THRESHOLD')\n"
            ),
            "getenv_alias": b"from os import getenv as g\nTHRESHOLD = g('SEIC_THRESHOLD')\n",
            "from_os_environ": b"from os import environ\nTHRESHOLD = environ['SEIC_THRESHOLD']\n",
            "argv_alias": b"import sys as s\nMODE = s.argv[1]\n",
            "stdin_input": b"MODE = input()\n",
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=["os", "sys"])
                self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r1_indirect_semantic_file_reference_is_non_pass(self) -> None:
        allowed = ["io", "pathlib"]
        cases = {
            "variable_path": (
                b"CONFIG_PATH = 'semantic/config.json'\n"
                b"CONFIG = open(CONFIG_PATH, 'rb').read()\n"
            ),
            "stored_path_object": (
                b"from pathlib import Path\n"
                b"CONFIG_FILE = Path('semantic/config.json')\n"
                b"CONFIG = CONFIG_FILE.read_text()\n"
            ),
            "pointer_file": (
                b"POINTER = open('semantic/config.json', 'rb').read().decode().strip()\n"
                b"CONFIG = open(POINTER, 'rb').read()\n"
            ),
            "open_alias": (
                b"reader = open\nCONFIG = reader('semantic/config.json', 'rb').read()\n"
            ),
            "io_alias_dynamic": (
                b"import io as stream\nNAME = 'semantic/config.json'\n"
                b"CONFIG = stream.open(NAME, 'rb').read()\n"
            ),
            "getattr_reader": (
                b"from pathlib import Path\n"
                b"CONFIG = getattr(Path('semantic/config.json'), 'read_text')()\n"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=allowed)
                self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r1_nested_indirect_caller_semantic_configuration_is_non_pass(self) -> None:
        caller_inputs = {
            "nested": {"subject": {"evaluator": {"policy": {"threshold": 99}}}},
            "aliased_field": {"thr3shold_alias": 99},
            "file_reference": {"config_ref": "semantic/config.json"},
            "mapping_proxy": types.MappingProxyType({}),
            "list_wrapper": [{"threshold": 99}],
        }
        for name, value in caller_inputs.items():
            with self.subTest(caller_input=name):
                self._assert_protected_non_pass(
                    "CALLER_SEMANTIC_INPUT", caller_semantic_input=value
                )
        sources = {
            "scope_reread": (
                b"import json\n\n"
                b"def evaluate(subject):\n"
                b"    scope = json.loads(open(subject['scope_path'], 'rb').read())\n"
                b"    return scope['policy']['required_vectors']\n"
            ),
            "aliased_policy_field": (
                b"def evaluate(subject):\n"
                b"    return getattr(subject, subject['policy_field'])\n"
            ),
        }
        for name, source in sources.items():
            with self.subTest(source=name):
                self._set_evaluator(source, allowed_external=["json"])
                self._assert_protected_non_pass("UNKNOWN_REACH")

    # ------------------------------------------------------------------
    # R1 controls and cleanup
    # ------------------------------------------------------------------

    def test_r1_unrelated_change_outside_evaluator_path_still_passes(self) -> None:
        self._assert_disposition("PASS", self._evaluate())
        receipt = self._change(
            "ordinary/source.py",
            b"import os as o\nimport importlib as il\n"
            b"VALUE = o.environ.get('X')\nPLUGIN = il.import_module('plug')\n",
        )
        self._assert_disposition("PASS", receipt)
        self.assertEqual(["ordinary/source.py"], receipt["changed_paths"])

    def test_r1_protected_state_unchanged_for_every_new_failure_case(self) -> None:
        approved = _sha(self.epoch)
        self._assert_protected_non_pass("REQUIRE_HUMAN_REVIEW", binding=None)
        self._assert_protected_non_pass(
            "EPOCH_MISMATCH", epoch=self._attacker_epoch(), binding=approved
        )
        self._assert_protected_non_pass("INVALID", binding="0" * 63)
        self._assert_protected_non_pass(
            "CALLER_SEMANTIC_INPUT", caller_semantic_input={"a": {"b": 1}}
        )
        self._set_evaluator(
            b"import sys as s\ns.path.insert(0, 'x')\n", allowed_external=["sys"]
        )
        self._assert_protected_non_pass("UNKNOWN_REACH")
        self._set_evaluator(
            b"from os import getenv as g\nT = g('X')\n", allowed_external=["os"]
        )
        self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r1_non_semantic_paths_removed_and_helper_not_in_production(self) -> None:
        record = self._epoch_record()
        self.assertNotIn("non_semantic_paths", record["closure_policy"])
        record["closure_policy"]["non_semantic_paths"] = ["ordinary"]
        stale = canonical_dumps(record).encode("utf-8")
        self._assert_protected_non_pass("INVALID", epoch=stale)
        self.assertFalse(hasattr(closure, "_changed_paths_from_parent"))
        source = Path(closure.__file__).read_text(encoding="utf-8")
        self.assertNotIn("non_semantic_paths", source)

    # ------------------------------------------------------------------
    # R1 mutation coverage
    # ------------------------------------------------------------------

    def test_mutant_bypass_external_epoch_binding_is_killed(self) -> None:
        proposal = self._commit(
            "semantic threshold change", {"semantic/config.json": b'{"threshold":0}\n'}
        )
        with mock.patch.object(closure, "_verify_epoch_binding", return_value=None):
            actual = self._evaluate(
                proposal, epoch=self._attacker_epoch(), binding=_sha(self.epoch)
            )["disposition"]
        self._assert_mutant_killed("EPOCH_MISMATCH", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_trust_self_declared_approval_is_killed(self) -> None:
        proposal = self._commit(
            "semantic threshold change", {"semantic/config.json": b'{"threshold":0}\n'}
        )
        original = closure._verify_epoch_binding

        def mutant(raw, binding):
            try:
                declared = json.loads(raw)
            except ValueError:
                declared = {}
            if (
                type(declared) is dict
                and declared.get("approval_status") == "HUMAN_APPROVED"
                and declared.get("human_approval_ref")
            ):
                return None
            return original(raw, binding)

        with mock.patch.object(closure, "_verify_epoch_binding", side_effect=mutant):
            actual = self._evaluate(
                proposal, epoch=self._attacker_epoch(), binding=None
            )["disposition"]
        self._assert_mutant_killed("REQUIRE_HUMAN_REVIEW", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_alias_reach_to_pass_is_killed(self) -> None:
        self._set_evaluator(
            b"import sys as s\ns.path.insert(0, 'plugins')\n", allowed_external=["sys"]
        )
        original = closure._import_bindings

        def mutant(syntax, package_parts):
            return tuple(
                binding for binding in original(syntax, package_parts) if not binding[2]
            )

        with mock.patch.object(closure, "_import_bindings", side_effect=mutant):
            actual = self._evaluate()["disposition"]
        self._assert_mutant_killed("UNKNOWN_REACH", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_environment_semantic_input_to_pass_is_killed(self) -> None:
        self._set_evaluator(
            b"import os as o\nTHRESHOLD = o.environ.get('SEIC_THRESHOLD')\n",
            allowed_external=["os"],
        )
        relaxed = closure._RESERVED_SEMANTIC_MODULES - {"os"}
        with mock.patch.object(closure, "_RESERVED_SEMANTIC_MODULES", relaxed):
            actual = self._evaluate()["disposition"]
        self._assert_mutant_killed("UNKNOWN_REACH", actual)
        self.assertEqual("PASS", actual)

    # ------------------------------------------------------------------
    # R2 getattr-family fails closed in evaluator reach
    # ------------------------------------------------------------------

    _R2_GETATTR_FINDING = "getattr-family attribute access: builtins.getattr: semantic/evaluator.py"

    def test_r2_getattr_io_open_with_caller_path_is_unknown_reach(self) -> None:
        cases = {
            "caller_path": (
                b"import io\n\n"
                b"def evaluate(subject):\n"
                b"    return getattr(io, 'open')(subject['path'], 'rb').read()\n"
            ),
            "non_literal_path": (
                b"import io\nNAME = 'semantic/config.json'\n"
                b"CONFIG = getattr(io, 'open')(NAME, 'rb').read()\n"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=["io"])
                receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
                self.assertIn(self._R2_GETATTR_FINDING, receipt["unknown_reach"])

    def test_r2_aliased_module_getattr_is_unknown_reach(self) -> None:
        self._set_evaluator(
            b"import io as x\n\n"
            b"def evaluate(subject):\n"
            b"    return getattr(x, 'open')(subject['path'], 'rb').read()\n",
            allowed_external=["io"],
        )
        receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
        self.assertIn(self._R2_GETATTR_FINDING, receipt["unknown_reach"])

    def test_r2_getattr_on_evaluator_owned_object_is_unknown_reach(self) -> None:
        cases = {
            "getattr_literal": (
                b"class Policy:\n    threshold = 3\n\n"
                b"POLICY = Policy()\nTHRESHOLD = getattr(POLICY, 'threshold')\n"
            ),
            "getattr_default": (
                b"class Policy:\n    threshold = 3\n\n"
                b"THRESHOLD = getattr(Policy, 'threshold', 0)\n"
            ),
            "hasattr_literal": (
                b"class Policy:\n    threshold = 3\n\n"
                b"HAS = hasattr(Policy, 'threshold')\n"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source)
                self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r2_nested_or_aliased_getattr_result_is_unknown_reach(self) -> None:
        cases = {
            "aliased_builtin": (
                b"import io\ng = getattr\nNAME = 'semantic/config.json'\n"
                b"opener = g(io, 'open')\nCONFIG = opener(NAME, 'rb').read()\n"
            ),
            "nested_getattr": (
                b"import io\nNAME = 'semantic/config.json'\n"
                b"CONFIG = getattr(getattr(io, 'open'), '__call__')(NAME, 'rb').read()\n"
            ),
            "stored_result": (
                b"import io\nREADER = getattr(io, 'open')\n\n"
                b"def evaluate(subject):\n    return READER(subject['path']).read()\n"
            ),
            "attrgetter_alias": (
                b"import io\nfrom operator import attrgetter as ag\n"
                b"NAME = 'semantic/config.json'\nCONFIG = ag('open')(io)(NAME, 'rb').read()\n"
            ),
            "methodcaller": (
                b"import operator\nNAME = 'semantic/config.json'\n"
                b"CONFIG = operator.methodcaller('read_text')(NAME)\n"
            ),
            "module_dict": (
                b"import io\nNAME = 'semantic/config.json'\n"
                b"CONFIG = io.__dict__['open'](NAME, 'rb').read()\n"
            ),
        }
        for name, source in cases.items():
            with self.subTest(case=name):
                self._set_evaluator(source, allowed_external=["io", "operator"])
                self._assert_protected_non_pass("UNKNOWN_REACH")

    def test_r2_setattr_is_unknown_reach(self) -> None:
        self._set_evaluator(
            b"from . import helper\nsetattr(helper, 'VALUE', 9)\nVALUE = helper.VALUE\n"
        )
        receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
        self.assertIn(
            "getattr-family attribute access: builtins.setattr: semantic/evaluator.py",
            receipt["unknown_reach"],
        )

    def test_r2_delattr_is_unknown_reach(self) -> None:
        self._set_evaluator(b"from . import helper\ndelattr(helper, 'VALUE')\n")
        receipt = self._assert_protected_non_pass("UNKNOWN_REACH")
        self.assertIn(
            "getattr-family attribute access: builtins.delattr: semantic/evaluator.py",
            receipt["unknown_reach"],
        )

    def test_r2_direct_safe_code_without_getattr_keeps_behavior(self) -> None:
        self._assert_disposition("PASS", self._evaluate())
        self._set_evaluator(
            b"from . import helper\n"
            b"VALUE = helper.VALUE\n"
            b"SCHEMA = open('semantic/schema.json', 'rb').read()\n"
            b"TOTAL = sum([VALUE, len(SCHEMA)])\n"
        )
        self._assert_disposition("PASS", self._evaluate())
        self._assert_disposition(
            "CLOSURE_HIT", self._change("semantic/helper.py", b"VALUE = 7\n")
        )

    def test_r2_unrelated_change_with_getattr_outside_reach_passes(self) -> None:
        receipt = self._change(
            "ordinary/source.py",
            b"import io\nOPENER = getattr(io, 'open')\nsetattr(io, 'X', 1)\n",
        )
        self._assert_disposition("PASS", receipt)
        self.assertEqual(["ordinary/source.py"], receipt["changed_paths"])

    def test_r2_protected_state_unchanged_after_getattr_unknown_reach(self) -> None:
        self._set_evaluator(
            b"import io\nNAME = 'semantic/config.json'\n"
            b"CONFIG = getattr(io, 'open')(NAME, 'rb').read()\n",
            allowed_external=["io"],
        )
        self._trusted_epoch_path(self.epoch)
        before = self._protected_state()
        receipt = self._evaluate()
        self.assertEqual(before, self._protected_state())
        self._assert_disposition("UNKNOWN_REACH", receipt)
        proposal = self._commit("ordinary change", {"ordinary/source.py": b"VALUE = 4\n"})
        self._assert_protected_non_pass("UNKNOWN_REACH", proposal)

    def test_mutant_getattr_family_to_pass_is_killed(self) -> None:
        self._set_evaluator(
            b"import io\n\n"
            b"def evaluate(subject):\n"
            b"    return getattr(io, 'open')(subject['path'], 'rb').read()\n",
            allowed_external=["io"],
        )
        with mock.patch.object(closure, "_getattr_family_findings", return_value=[]):
            actual = self._evaluate()["disposition"]
        self._assert_mutant_killed("UNKNOWN_REACH", actual)
        self.assertEqual("PASS", actual)

    def test_mutant_reinstate_literal_getattr_exemption_is_killed(self) -> None:
        self._set_evaluator(
            b"import io as x\nNAME = 'semantic/config.json'\n"
            b"CONFIG = getattr(x, 'open')(NAME, 'rb').read()\n",
            allowed_external=["io"],
        )

        def mutant(path, syntax, aliases):
            findings = []
            for node in ast.walk(syntax):
                if not isinstance(node, ast.Call):
                    continue
                if closure._canonical_name(node.func, aliases) not in closure._GETATTR_FAMILY:
                    continue
                name = node.args[1] if len(node.args) >= 2 else None
                if not (isinstance(name, ast.Constant) and type(name.value) is str):
                    findings.append(f"dynamic attribute access: {path}")
            return findings

        with mock.patch.object(closure, "_getattr_family_findings", side_effect=mutant):
            actual = self._evaluate()["disposition"]
        self._assert_mutant_killed("UNKNOWN_REACH", actual)
        self.assertEqual("PASS", actual)


if __name__ == "__main__":
    unittest.main()
