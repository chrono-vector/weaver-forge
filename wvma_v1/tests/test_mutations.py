"""Closed mutation primitive tests for WVMA-V1 Batch A2."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from wvma_v1.canonical import canonical_bytes
from wvma_v1.models import MutationSpec
from wvma_v1.mutations import EMPTY_SHA256, MutationError, apply_mutation


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _spec(
    *,
    op: str,
    path: str,
    pre: str,
    post: str,
    args: dict,
    case_id: str = "WVMA-S01-M01",
) -> MutationSpec:
    return MutationSpec(
        case_id=case_id,
        property_id="WVMA-S01",
        critical=True,
        mutation_kind="SYNTHETIC_ARTIFACT",
        target_relative_path=path,
        expected_preimage_sha256=pre,
        operation_enum=op,
        operation_arguments=args,
        expected_postimage_sha256=post,
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="synthetic.verify",
        violation_predicate="status_not_accepted",
        expected_rejection_predicate="verify_rejects",
        oracle_observations=("status_field",),
        materiality="MATERIAL",
    )


class TestMutations(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix="wvma-mut-")
        self.root = Path(self._tmpdir.name)
        self.artifact = self.root / "synthetic" / "artifact.json"
        self.artifact.parent.mkdir(parents=True)
        self.original_obj = {"status": "accepted", "n": 1}
        self.original = canonical_bytes(self.original_obj)
        self.artifact.write_bytes(self.original)
        self.pre = _sha(self.original)

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_set_json_pointer(self):
        new_obj = {"n": 1, "status": "BAD"}
        post_bytes = canonical_bytes(new_obj)
        post = _sha(post_bytes)
        app = apply_mutation(
            self.root,
            _spec(
                op="SET_JSON_POINTER",
                path="synthetic/artifact.json",
                pre=self.pre,
                post=post,
                args={"pointer": "/status", "value": "BAD"},
            ),
        )
        self.assertTrue(app.applied)
        self.assertEqual(self.artifact.read_bytes(), post_bytes)

    def test_delete_json_pointer(self):
        new_obj = {"n": 1}
        post_bytes = canonical_bytes(new_obj)
        post = _sha(post_bytes)
        app = apply_mutation(
            self.root,
            _spec(
                op="DELETE_JSON_POINTER",
                path="synthetic/artifact.json",
                pre=self.pre,
                post=post,
                args={"pointer": "/status"},
            ),
        )
        self.assertTrue(app.applied)
        self.assertEqual(json.loads(self.artifact.read_bytes()), new_obj)

    def test_replace_exact_bytes(self):
        find = b"accepted"
        repl = b"REJECTED"
        new = self.original.replace(find, repl, 1)
        app = apply_mutation(
            self.root,
            _spec(
                op="REPLACE_EXACT_BYTES",
                path="synthetic/artifact.json",
                pre=self.pre,
                post=_sha(new),
                args={"find_hex": find.hex(), "replace_hex": repl.hex()},
            ),
        )
        self.assertTrue(app.applied)
        self.assertEqual(self.artifact.read_bytes(), new)

    def test_add_and_delete_declared_file(self):
        content = b"extra-bytes"
        add_path = "synthetic/extra.txt"
        app = apply_mutation(
            self.root,
            _spec(
                op="ADD_DECLARED_FILE",
                path=add_path,
                pre=EMPTY_SHA256,
                post=_sha(content),
                args={"content_hex": content.hex()},
                case_id="WVMA-S01-M02",
            ),
        )
        self.assertTrue(app.applied)
        target = self.root / "synthetic" / "extra.txt"
        self.assertEqual(target.read_bytes(), content)
        app2 = apply_mutation(
            self.root,
            _spec(
                op="DELETE_DECLARED_FILE",
                path=add_path,
                pre=_sha(content),
                post=EMPTY_SHA256,
                args={},
                case_id="WVMA-S01-M02",
            ),
        )
        self.assertTrue(app2.applied)
        self.assertFalse(target.exists())

    def test_rebind_declared_hashes(self):
        obj = {"digest": "1" * 64, "nested": {"h": "2" * 64}}
        raw = canonical_bytes(obj)
        self.artifact.write_bytes(raw)
        pre = _sha(raw)
        new_obj = {"digest": "a" * 64, "nested": {"h": "b" * 64}}
        post_bytes = canonical_bytes(new_obj)
        app = apply_mutation(
            self.root,
            _spec(
                op="REBIND_DECLARED_HASHES",
                path="synthetic/artifact.json",
                pre=pre,
                post=_sha(post_bytes),
                args={
                    "bindings": [
                        {"pointer": "/digest", "sha256": "a" * 64},
                        {"pointer": "/nested/h", "sha256": "b" * 64},
                    ]
                },
            ),
        )
        self.assertTrue(app.applied)
        self.assertEqual(self.artifact.read_bytes(), post_bytes)

    def test_preimage_mismatch_does_not_write(self):
        before = self.artifact.read_bytes()
        with self.assertRaises(MutationError):
            apply_mutation(
                self.root,
                _spec(
                    op="SET_JSON_POINTER",
                    path="synthetic/artifact.json",
                    pre="0" * 64,
                    post="1" * 64,
                    args={"pointer": "/status", "value": "BAD"},
                ),
            )
        self.assertEqual(self.artifact.read_bytes(), before)

    def test_postimage_mismatch_does_not_write(self):
        before = self.artifact.read_bytes()
        with self.assertRaises(MutationError):
            apply_mutation(
                self.root,
                _spec(
                    op="SET_JSON_POINTER",
                    path="synthetic/artifact.json",
                    pre=self.pre,
                    post="f" * 64,
                    args={"pointer": "/status", "value": "BAD"},
                ),
            )
        self.assertEqual(self.artifact.read_bytes(), before)

    def test_path_escape_rejected_before_write(self):
        with self.assertRaises(MutationError):
            apply_mutation(
                self.root,
                _spec(
                    op="SET_JSON_POINTER",
                    path="../escape.json",
                    pre=self.pre,
                    post="1" * 64,
                    args={"pointer": "/status", "value": "BAD"},
                ),
            )

    def test_unknown_argument_rejected(self):
        with self.assertRaises(MutationError):
            apply_mutation(
                self.root,
                _spec(
                    op="SET_JSON_POINTER",
                    path="synthetic/artifact.json",
                    pre=self.pre,
                    post="1" * 64,
                    args={"pointer": "/status", "value": "BAD", "shell": "rm -rf"},
                ),
            )


if __name__ == "__main__":
    unittest.main()
