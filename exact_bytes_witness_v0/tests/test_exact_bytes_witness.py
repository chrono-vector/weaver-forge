"""Focused attack tests for Exact-Bytes Witness v0.

APKD2-A01 through APKD2-A36 are attack tests. They are not source
mutations. APKD2-S01 through APKD2-S14 are applied to temporary copies
of the production source and are not executed by this module.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import sys
import unittest
from importlib.metadata import version
from pathlib import Path

import exact_bytes_witness_v0 as witness
from exact_bytes_witness_v0 import ExactBytesWitnessError, verify_exact_bytes_witness
from exact_bytes_witness_v0 import verify as verify_module

_SUCCESS = "EXACT_BYTES_WITNESS_VALID"
_FAILURE = "EXACT_BYTES_WITNESS_REJECTED"
_REPO = Path(__file__).resolve().parents[2]
_FREEZE = (
    _REPO / "docs" / "next" / "EXACT_BYTES_WITNESS_V0_HUMAN_DESIGN_FREEZE_20261005.md"
)
_TEST1_PK = bytes.fromhex(
    "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
)
_TEST1_SIG = bytes.fromhex(
    "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e06522490155"
    "5fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
)
_TEST1_MSG = b""
_TEST2_PK = bytes.fromhex(
    "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c"
)
_TEST2_SIG = bytes.fromhex(
    "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
    "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
)
_TEST2_MSG = bytes.fromhex("72")
_PUBLIC = [
    "ExactBytesWitnessError",
    "verify_exact_bytes_witness",
]
_FORBIDDEN = frozenset(
    {
        "sign",
        "generate",
        "generate_key",
        "from_private_bytes",
        "Ed25519PrivateKey",
    }
)
_PROMOTED = frozenset(
    {
        "WITNESS_VERIFIED",
        "SIGNATURE_VALID",
        "TRUSTED_SIGNER",
        "AUTHENTIC",
        "PROVENANCE",
        "EVIDENCE",
        "LOG",
        "VERIFIED",
        "FRESH",
        "INDEPENDENT",
        "COMPATIBLE",
    }
)


class _ExactBytes(bytes):
    """Subclass used to prove the exact-type rule."""


def _flip_first(value: bytes) -> bytes:
    return bytes([value[0] ^ 0x01]) + value[1:]


class ExactBytesWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if len(_TEST1_PK) != 32 or len(_TEST2_PK) != 32:
            raise AssertionError("public-key vector is not 32 bytes")
        if len(_TEST1_SIG) != 64 or len(_TEST2_SIG) != 64:
            raise AssertionError("signature vector is not 64 bytes")
        if _TEST2_MSG != b"\x72":
            raise AssertionError("TEST 2 message is not octet 0x72")

    def _ok(self, public_key: bytes, signature: bytes, message: bytes) -> str:
        result = verify_exact_bytes_witness(public_key, signature, message)
        self.assertIs(type(result), str)
        self.assertEqual(result, _SUCCESS)
        self.assertNotIn(result, _PROMOTED)
        return result

    def _no(self, public_key: object, signature: object, message: object) -> None:
        with self.assertRaises(ExactBytesWitnessError) as caught:
            verify_exact_bytes_witness(public_key, signature, message)  # type: ignore[arg-type]
        self.assertIs(type(caught.exception), ExactBytesWitnessError)
        self.assertIs(type(caught.exception.code), str)
        self.assertEqual(caught.exception.code, _FAILURE)

    def test_freeze_record_names_the_accepted_contract(self) -> None:
        text = _FREEZE.read_text(encoding="utf-8")
        self.assertIn("HUMAN_DESIGN_FREEZE:\nACCEPTED", text)
        self.assertIn("0bb0303f4d026f2b83c4d19fe198fe4280c14aaf", text)
        self.assertIn("Planned attack tests:\n36", text)
        self.assertIn("Planned actual source-code mutations:\n14", text)
        self.assertIn("cryptography==50.0.2", text)
        self.assertIn("cffi==2.1.1", text)
        self.assertIn("pycparser==3.0", text)
        signature = (
            "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da"
            "085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
        )
        design = (
            _REPO
            / "docs"
            / "next"
            / "AUDITED_PUBLIC_KEY_VERIFICATION_DEPENDENCY_D2_20261005.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(len(signature), 128)
        self.assertIn(signature, text)
        self.assertIn(signature, design)
        self.assertEqual(_TEST2_SIG.hex(), signature)
        names = sorted(name for name in dir(type(self)) if name.startswith("test_a"))
        self.assertEqual(names, [f"test_a{index:02d}" for index in range(1, 37)])

    def test_installed_profile_matches_the_freeze(self) -> None:
        self.assertEqual(version("cryptography"), "50.0.2")
        self.assertEqual(version("cffi"), "2.1.1")
        self.assertEqual(version("pycparser"), "3.0")

    def test_a01(self) -> None:
        self._ok(_TEST1_PK, _TEST1_SIG, _TEST1_MSG)

    def test_a02(self) -> None:
        self._ok(_TEST2_PK, _TEST2_SIG, _TEST2_MSG)

    def test_a03(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, b"\x73")

    def test_a04(self) -> None:
        self._no(_TEST1_PK, _TEST2_SIG, _TEST2_MSG)

    def test_a05(self) -> None:
        flipped = _flip_first(_TEST2_PK)
        self.assertEqual(len(flipped), 32)
        self.assertNotEqual(flipped, _TEST2_PK)
        self._no(flipped, _TEST2_SIG, _TEST2_MSG)

    def test_a06(self) -> None:
        changed = b"\x93" + _TEST2_SIG[1:]
        self.assertEqual(_TEST2_SIG[0], 0x92)
        self.assertEqual(changed[0], 0x93)
        self.assertEqual(len(changed), 64)
        self._no(_TEST2_PK, changed, _TEST2_MSG)

    def test_a07(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, b"")

    def test_a08(self) -> None:
        self._no(_TEST2_PK[:31], _TEST2_SIG, _TEST2_MSG)

    def test_a09(self) -> None:
        self._no(_TEST2_PK + b"\x00", _TEST2_SIG, _TEST2_MSG)

    def test_a10(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG[:63], _TEST2_MSG)

    def test_a11(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG + b"\x00", _TEST2_MSG)

    def test_a12(self) -> None:
        self._no(_ExactBytes(_TEST2_PK), _TEST2_SIG, _TEST2_MSG)

    def test_a13(self) -> None:
        self._no(_TEST2_PK, _ExactBytes(_TEST2_SIG), _TEST2_MSG)

    def test_a14(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, _ExactBytes(_TEST2_MSG))

    def test_a15(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, bytearray(_TEST2_MSG))

    def test_a16(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, memoryview(_TEST2_MSG))

    def test_a17(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, "r")

    def test_a18(self) -> None:
        self._no("d75a980182b10ab7d54bfed3c964073a", _TEST2_SIG, _TEST2_MSG)

    def test_a19(self) -> None:
        self._no(_TEST2_PK, "92a009a9f0d4cab8720e820b5f642540", _TEST2_MSG)

    def test_a20(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, _TEST2_MSG + b"\x0a")

    def test_a21(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, b"\x0a" + _TEST2_MSG)

    def test_a22(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, b"\x0d" + _TEST2_MSG)

    def test_a23(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, b"\n")
        self._no(_TEST2_PK, _TEST2_SIG, b"\r\n")

    def test_a24(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, bytes.fromhex("c3a9"))
        self._no(_TEST2_PK, _TEST2_SIG, bytes.fromhex("65cc81"))

    def test_a25(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, _TEST2_MSG + b"\x00")

    def test_a26(self) -> None:
        self._no(_TEST2_PK, _TEST2_SIG, b"\x00" + _TEST2_MSG)

    def test_a27(self) -> None:
        first = self._ok(_TEST1_PK, _TEST1_SIG, _TEST1_MSG)
        second = self._ok(_TEST1_PK, _TEST1_SIG, _TEST1_MSG)
        self.assertEqual(first, second)

    def test_a28(self) -> None:
        with self.assertRaises(TypeError):
            verify_exact_bytes_witness(  # type: ignore[call-arg]
                _TEST2_PK,
                _TEST2_SIG,
                _TEST2_MSG,
                algorithm="ed25519",
            )

    def test_a29(self) -> None:
        with self.assertRaises(TypeError):
            verify_exact_bytes_witness(  # type: ignore[call-arg]
                _TEST2_PK,
                _TEST2_SIG,
                _TEST2_MSG,
                signer="alice",
            )

    def test_a30(self) -> None:
        with self.assertRaises(TypeError):
            verify_exact_bytes_witness(  # type: ignore[call-arg]
                _TEST2_PK,
                _TEST2_SIG,
                _TEST2_MSG,
                kind="evidence",
            )

    def test_a31(self) -> None:
        self._no(b"\x00" * 32, b"\x00" * 64, _TEST2_MSG)

    def test_a32(self) -> None:
        self._no(b"\xff" * 32, _TEST2_SIG, _TEST2_MSG)

    def test_a33(self) -> None:
        from cryptography.exceptions import InvalidSignature

        changed = b"\x93" + _TEST2_SIG[1:]
        with self.assertRaises(ExactBytesWitnessError) as caught:
            verify_exact_bytes_witness(_TEST2_PK, changed, _TEST2_MSG)
        self.assertIs(type(caught.exception), ExactBytesWitnessError)
        self.assertNotIsInstance(caught.exception, InvalidSignature)
        self.assertEqual(caught.exception.code, _FAILURE)
        self.assertIsNone(caught.exception.__cause__)

    def test_a34(self) -> None:
        real_import = builtins.__import__
        saved = {
            name: sys.modules.pop(name)
            for name in list(sys.modules)
            if name == "cryptography" or name.startswith("cryptography.")
        }

        def guarded(
            name: str,
            globals: dict | None = None,
            locals: dict | None = None,
            fromlist: tuple = (),
            level: int = 0,
        ):
            if name == "cryptography" or name.startswith("cryptography."):
                raise ImportError(name)
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded
        try:
            self._no(_TEST2_PK, _TEST2_SIG, _TEST2_MSG)
        finally:
            builtins.__import__ = real_import
            sys.modules.update(saved)
        self._ok(_TEST2_PK, _TEST2_SIG, _TEST2_MSG)

    def test_a35(self) -> None:
        self.assertEqual(witness.__all__, _PUBLIC)
        self.assertEqual(verify_module.__all__, _PUBLIC)
        self.assertTrue(_FORBIDDEN.isdisjoint(witness.__all__))
        self.assertTrue(_FORBIDDEN.isdisjoint(dir(witness)))
        self.assertTrue(_FORBIDDEN.isdisjoint(dir(verify_module)))
        signature = inspect.signature(verify_exact_bytes_witness)
        self.assertEqual(
            list(signature.parameters),
            ["public_key", "signature", "message"],
        )
        for parameter in signature.parameters.values():
            self.assertIs(parameter.default, inspect.Parameter.empty)
        defined = {
            node.name
            for node in ast.parse(
                Path(verify_module.__file__).read_text(encoding="utf-8")
            ).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        }
        self.assertTrue(_FORBIDDEN.isdisjoint(defined))
        self.assertEqual(
            defined,
            {"ExactBytesWitnessError", "_reject", "verify_exact_bytes_witness"},
        )
        for path in (Path(verify_module.__file__), Path(witness.__file__)):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn("cryptography", node.module)
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn("cryptography", alias.name)
        with self.assertRaises(TypeError):
            verify_exact_bytes_witness(  # type: ignore[call-arg]
                _TEST2_PK, _TEST2_SIG, _TEST2_MSG, b""
            )
        with self.assertRaises(TypeError):
            verify_exact_bytes_witness(  # type: ignore[call-arg]
                _TEST2_PK, _TEST2_SIG, _TEST2_MSG, domain="pure"
            )
        with self.assertRaises(TypeError):
            verify_exact_bytes_witness(  # type: ignore[call-arg]
                _TEST2_PK, _TEST2_SIG, _TEST2_MSG, hash="sha512"
            )

    def test_a36(self) -> None:
        valid = (_TEST2_PK, _TEST2_SIG, _TEST2_MSG)
        for bad in (1, True, None):
            for index in range(3):
                arguments = list(valid)
                arguments[index] = bad
                self._no(arguments[0], arguments[1], arguments[2])
