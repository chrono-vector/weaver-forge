"""Canonical JSON and digest determinism tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from wvma_v1.canonical import (
    canonical_bytes,
    canonical_digest,
    digest_excluding_field,
    sha256_file,
)


class CanonicalTests(unittest.TestCase):
    def test_canonical_determinism(self):
        a = {"b": 1, "a": [2, 3], "nested": {"y": False, "x": True}}
        b = {"nested": {"x": True, "y": False}, "a": [2, 3], "b": 1}
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))
        self.assertEqual(
            canonical_bytes(a),
            b'{"a":[2,3],"b":1,"nested":{"x":true,"y":false}}',
        )

    def test_canonical_digest_determinism(self):
        obj = {"z": "q", "a": 1}
        self.assertEqual(canonical_digest(obj), canonical_digest({"a": 1, "z": "q"}))
        self.assertEqual(len(canonical_digest(obj)), 64)

    def test_rejects_tuple_normalization(self):
        with self.assertRaises(TypeError):
            canonical_bytes({"a": (1, 2)})

    def test_rejects_set_normalization(self):
        with self.assertRaises(TypeError):
            canonical_bytes({"a": {1, 2}})

    def test_rejects_nan(self):
        with self.assertRaises(ValueError):
            canonical_bytes({"a": float("nan")})

    def test_digest_excluding_field(self):
        obj = {"a": 1, "digest": "x", "b": 2}
        d1 = digest_excluding_field(obj, "digest")
        d2 = canonical_digest({"a": 1, "b": 2})
        self.assertEqual(d1, d2)
        self.assertNotEqual(d1, canonical_digest(obj))

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.bin"
            path.write_bytes(b"abc")
            self.assertEqual(
                sha256_file(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )


if __name__ == "__main__":
    unittest.main()
