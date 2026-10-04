"""Focused tests for Association Carriage Digest v0."""

from __future__ import annotations

import hashlib
import inspect
from pathlib import Path
import unittest
from unittest.mock import patch

import association_carriage_digest_v0 as acd
from association_carriage_digest_v0 import digest as digest_module
from association_carriage_digest_v0.digest import (
    AssociationCarriageDigestError,
    digest_association_carriage_preimage,
)
from domain_separated_digest_v0 import domain_separated_digest

GOLDEN_1 = "686a6035076c8087092763cc4f069045f16ff767277fdcb4f7d7d2ee1a05f5fe"
GOLDEN_2 = "bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2"
_DST = bytes.fromhex("7765617665722e6163722e6469676573742e763000")
_PUBLIC = [
    "AssociationCarriageDigestError",
    "digest_association_carriage_preimage",
]


def _frozen_fixture() -> bytes:
    path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "next"
        / "ACD_V0_HUMAN_DESIGN_FREEZE_20261004.md"
    )
    text = path.read_text(encoding="utf-8")
    line = ""
    at = text.index("Exact fixture text:")
    for candidate in text[at:].splitlines():
        if candidate.startswith("`{") and candidate.endswith("`"):
            line = candidate[1:-1]
            break
    if not line:
        raise AssertionError("frozen fixture text is missing")
    raw = line.encode("utf-8")
    if len(raw) != 1346 or b"\r" in raw or raw.endswith(b"\n"):
        raise AssertionError("frozen fixture is not the 1346-byte record")
    return raw


def _boom(data: bytes) -> str:
    raise AssertionError(data)


_FORBIDDEN_PUBLIC = frozenset(
    {
        "TAG",
        "ACD_TAG",
        "PREFIX",
        "DST",
        "DOMAINS",
        "REGISTRY",
        "NAMESPACE",
        "DOMAIN",
        "TAGS",
    }
)


def _is_tag_surface(value: object, tag: bytes) -> bool:
    ascii_tag = tag[:-1] if tag.endswith(b"\x00") else tag
    text = ascii_tag.decode("ascii")
    if value == tag or value == ascii_tag or value == text:
        return True
    if isinstance(value, (list, tuple, set, frozenset)):
        return any(_is_tag_surface(item, tag) for item in value)
    if isinstance(value, dict):
        return any(_is_tag_surface(item, tag) for item in (*value.keys(), *value.values()))
    return False


def _defined_functions(module: object) -> dict[str, object]:
    found: dict[str, object] = {}
    for name, value in vars(module).items():
        if inspect.isfunction(value) and value.__module__ == module.__name__:
            found[name] = value
    return found


class AssociationCarriageDigestTests(unittest.TestCase):
    def test_01_golden_vector_1(self) -> None:
        self.assertEqual(digest_association_carriage_preimage(b"a"), GOLDEN_1)

    def test_02_golden_vector_2_from_frozen_document(self) -> None:
        raw = _frozen_fixture()
        self.assertEqual(len(raw), 1346)
        self.assertEqual(digest_association_carriage_preimage(raw), GOLDEN_2)

    def test_03_exact_bytes_accepted(self) -> None:
        self.assertEqual(digest_association_carriage_preimage(b"\x00"), digest_module.digest_association_carriage_preimage(b"\x00"))
        self.assertEqual(len(digest_association_carriage_preimage(b"\x00")), 64)

    def test_04_empty_bytes_rejected_before_hash(self) -> None:
        with patch("association_carriage_digest_v0.digest.hashlib.sha256", _boom):
            with self.assertRaises(AssociationCarriageDigestError) as caught:
                digest_association_carriage_preimage(b"")
        self.assertEqual(caught.exception.code, "ACD_PREIMAGE_REJECTED")
        self.assertEqual(str(caught.exception), "ACD_PREIMAGE_REJECTED: preimage is empty")

    def test_05_bytes_subclass_rejected_before_hash(self) -> None:
        class LyingLen(bytes):
            def __len__(self) -> int:
                return 1

        with patch("association_carriage_digest_v0.digest.hashlib.sha256", _boom):
            with self.assertRaises(AssociationCarriageDigestError) as caught:
                digest_association_carriage_preimage(LyingLen(b"a"))  # type: ignore[arg-type]
        self.assertEqual(str(caught.exception), "ACD_PREIMAGE_REJECTED: preimage must be exact bytes")

    def test_06_bytearray_rejected_before_hash(self) -> None:
        with patch("association_carriage_digest_v0.digest.hashlib.sha256", _boom):
            with self.assertRaises(AssociationCarriageDigestError) as caught:
                digest_association_carriage_preimage(bytearray(b"a"))  # type: ignore[arg-type]
        self.assertEqual(str(caught.exception), "ACD_PREIMAGE_REJECTED: preimage must be exact bytes")

    def test_07_memoryview_rejected_before_hash(self) -> None:
        with patch("association_carriage_digest_v0.digest.hashlib.sha256", _boom):
            with self.assertRaises(AssociationCarriageDigestError) as caught:
                digest_association_carriage_preimage(memoryview(b"a"))  # type: ignore[arg-type]
        self.assertEqual(str(caught.exception), "ACD_PREIMAGE_REJECTED: preimage must be exact bytes")

    def test_08_str_rejected_before_hash(self) -> None:
        with patch("association_carriage_digest_v0.digest.hashlib.sha256", _boom):
            with self.assertRaises(AssociationCarriageDigestError) as caught:
                digest_association_carriage_preimage("a")  # type: ignore[arg-type]
        self.assertEqual(str(caught.exception), "ACD_PREIMAGE_REJECTED: preimage must be exact bytes")

    def test_09_other_types_rejected_before_hash(self) -> None:
        samples = (None, 1, 1.0, ["a"], {"a": 1})
        with patch("association_carriage_digest_v0.digest.hashlib.sha256", _boom):
            for sample in samples:
                with self.subTest(sample=type(sample).__name__):
                    with self.assertRaises(AssociationCarriageDigestError) as caught:
                        digest_association_carriage_preimage(sample)  # type: ignore[arg-type]
                    self.assertEqual(
                        str(caught.exception),
                        "ACD_PREIMAGE_REJECTED: preimage must be exact bytes",
                    )

    def test_10_output_is_lowercase_64_hex(self) -> None:
        digest = digest_association_carriage_preimage(b"a")
        self.assertEqual(len(digest), 64)
        self.assertEqual(digest, digest.lower())
        self.assertTrue(all(char in "0123456789abcdef" for char in digest))
        self.assertNotEqual(digest, digest.upper())

    def test_11_no_caller_domain_or_prefix_argument(self) -> None:
        signature = inspect.signature(digest_association_carriage_preimage)
        self.assertEqual(list(signature.parameters), ["preimage"])
        with self.assertRaises(TypeError):
            digest_association_carriage_preimage(b"a", "CSAR_RECORD")  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            digest_association_carriage_preimage(b"a", domain="CSAR_RECORD")  # type: ignore[call-arg]
        with self.assertRaises(TypeError):
            digest_association_carriage_preimage(b"a", prefix="weaver.digest.v1")  # type: ignore[call-arg]

    def test_12_no_expected_digest_argument(self) -> None:
        with self.assertRaises(TypeError):
            digest_association_carriage_preimage(b"a", expected_digest=GOLDEN_1)  # type: ignore[call-arg]

    def test_13_same_bytes_are_deterministic(self) -> None:
        self.assertEqual(
            digest_association_carriage_preimage(b"a"),
            digest_association_carriage_preimage(b"a"),
        )

    def test_14_prefix_omission_differs_from_golden(self) -> None:
        omitted = hashlib.sha256(b"\x00" + b"a").hexdigest()
        self.assertNotEqual(digest_association_carriage_preimage(b"a"), omitted)
        self.assertEqual(digest_association_carriage_preimage(b"a"), GOLDEN_1)

    def test_15_nul_omission_differs_from_golden(self) -> None:
        omitted = hashlib.sha256(b"weaver.acr.digest.v0" + b"a").hexdigest()
        self.assertNotEqual(digest_association_carriage_preimage(b"a"), omitted)

    def test_16_untagged_sha256_differs(self) -> None:
        self.assertNotEqual(
            digest_association_carriage_preimage(b"a"),
            hashlib.sha256(b"a").hexdigest(),
        )

    def test_17_dsds_csar_record_differs(self) -> None:
        self.assertNotEqual(
            digest_association_carriage_preimage(b"a"),
            domain_separated_digest("CSAR_RECORD", b"a"),
        )

    def test_18_no_generic_registry_or_domain_helper(self) -> None:
        self.assertFalse(hasattr(acd, "DOMAINS"))
        self.assertFalse(hasattr(acd, "PREFIX"))
        self.assertFalse(hasattr(acd, "domain_separated_digest"))
        self.assertFalse(hasattr(digest_module, "DOMAINS"))
        self.assertFalse(hasattr(digest_module, "PREFIX"))
        self.assertFalse(hasattr(digest_module, "domain_separated_digest"))
        for name, value in vars(digest_module).items():
            if not callable(value) or name.startswith("__"):
                continue
            for parameter in inspect.signature(value).parameters:
                self.assertNotIn(
                    parameter,
                    {"domain", "domain_id", "prefix", "expected_digest"},
                )
        defined = _defined_functions(digest_module)
        self.assertEqual(
            set(defined),
            {"_fail", "digest_association_carriage_preimage"},
        )
        self.assertEqual(list(inspect.signature(defined["_fail"]).parameters), ["message"])
        self.assertEqual(
            list(inspect.signature(defined["digest_association_carriage_preimage"]).parameters),
            ["preimage"],
        )
        for name, value in vars(digest_module).items():
            if name.startswith("_") or name == "annotations":
                continue
            if inspect.ismodule(value) or inspect.isfunction(value) or inspect.isclass(value):
                continue
            self.assertNotIn(name, _FORBIDDEN_PUBLIC)
            self.assertFalse(_is_tag_surface(value, digest_module._TAG))

    def test_19_public_exports_are_exact(self) -> None:
        self.assertEqual(acd.__all__, _PUBLIC)
        self.assertEqual(digest_module.__all__, _PUBLIC)
        self.assertFalse(set(acd.__all__) & _FORBIDDEN_PUBLIC)
        self.assertFalse(set(digest_module.__all__) & _FORBIDDEN_PUBLIC)
        self.assertEqual(digest_module._TAG, _DST)
        self.assertEqual(len(digest_module._TAG), 21)
        package_public = {name for name in vars(acd) if not name.startswith("_")}
        self.assertEqual(package_public, set(_PUBLIC) | {"digest"})
        for name, value in vars(acd).items():
            if name.startswith("_") or inspect.ismodule(value):
                continue
            self.assertIn(name, _PUBLIC)
            self.assertNotIn(name, _FORBIDDEN_PUBLIC)
            self.assertFalse(_is_tag_surface(value, digest_module._TAG))

    def test_20_successful_hash_uses_sha256_after_checks(self) -> None:
        seen: list[bytes] = []
        original = hashlib.sha256

        def spy(data: bytes):
            seen.append(data)
            return original(data)

        with patch("association_carriage_digest_v0.digest.hashlib.sha256", spy):
            digest = digest_association_carriage_preimage(b"a")
        self.assertEqual(digest, GOLDEN_1)
        self.assertEqual(seen, [_DST + b"a"])
