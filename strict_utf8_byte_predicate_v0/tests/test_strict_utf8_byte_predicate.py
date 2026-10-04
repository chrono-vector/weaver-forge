"""Focused attack tests for Strict UTF-8 Byte Predicate v0.

SUBP-A01 through SUBP-A27 are attack tests. They are not source-code
mutation operators. SUBP-S01 through SUBP-S15 are specified separately
and are not executed by this module.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import unicodedata
from pathlib import Path
from unittest.mock import patch

import unittest

import strict_utf8_byte_predicate_v0 as subp
from association_carriage_digest_v0 import digest_association_carriage_preimage
from domain_separated_digest_v0 import (
    DomainSeparatedDigestError,
    digest_presented_subject_bytes,
    domain_separated_digest,
)
from strict_utf8_byte_predicate_v0 import (
    SubpError,
    parse_subp,
    produce_subp,
    subp_reproduced_from_supplied_inputs,
    subp_structurally_consistent,
)
from strict_utf8_byte_predicate_v0 import record as record_module

_DESIGN = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "STRICT_UTF8_BYTE_PREDICATE_V0_DESIGN_AND_ATTACK_SPEC_20261004.md"
)
_FREEZE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "SUBP_V0_HUMAN_DESIGN_FREEZE_20261004.md"
)
_TAG = b"weaver.subp.digest.v0\x00"
_PSRD_TAG = b"weaver.psrd.digest.v0\x00"
_STRUCTURAL = "SUBP_STRUCTURALLY_CONSISTENT"
_REPRODUCED = "SUBP_REPRODUCED_FROM_SUPPLIED_INPUTS"
_PUBLIC = [
    "SubpError",
    "produce_subp",
    "parse_subp",
    "subp_structurally_consistent",
    "subp_reproduced_from_supplied_inputs",
]
_NAMESPACE = {
    "annotations",
    "json",
    "re",
    "hashlib",
    "_DomainSeparatedDigestError",
    "_digest_presented_subject_bytes",
    "_TAG",
    "_SCHEMA_VERSION",
    "_TOKEN",
    "_BOM",
    "_LIMITATIONS",
    "_KEYS",
    "_PREIMAGE_KEYS",
    "_DIGEST",
    "SubpError",
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_presented_digest",
    "_predicate_digest",
    "_require_limitations",
    "_require_digest_text",
    "_exact_six_fields",
    "subp_structurally_consistent",
    "produce_subp",
    "parse_subp",
    "subp_reproduced_from_supplied_inputs",
}
_DEFINED = {
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_presented_digest",
    "_predicate_digest",
    "_require_limitations",
    "_require_digest_text",
    "_exact_six_fields",
    "subp_structurally_consistent",
    "produce_subp",
    "parse_subp",
    "subp_reproduced_from_supplied_inputs",
}
_FORBIDDEN_PARAMS = {
    "domain",
    "prefix",
    "tag",
    "digest",
    "role",
    "kind",
    "format",
    "mime",
    "filename",
    "authority",
    "limitations",
}
_FORBIDDEN_PUBLIC = {
    "TAG",
    "PREFIX",
    "DST",
    "DOMAINS",
    "REGISTRY",
    "NAMESPACE",
    "CODEC",
    "UTF8",
    "canonical_digest",
    "digest",
    "domain_separated_digest",
    "hash",
}
_PREIMAGE_KEYS = (
    "schema_version",
    "authority",
    "utf8_predicate",
    "presented_subject_digest",
    "limitations",
)
_AUTHORITY = "authority is not exact False"
_TOKEN_RULE = "utf8_predicate is not the code-owned token"
_LIMITATION_RULE = "limitations are not the code-owned list"
_SCHEMA_RULE = "schema_version is not the exact schema"
_MALFORMED = "digest text is malformed"
_DIGEST_RULE = "predicate digest does not reproduce"
_KEYS_RULE = "record keys are not the six-field schema"
_CANONICAL = "serialized bytes are not canonical"
_SUBJECT_TYPE = "subject must be exact bytes"
_EMPTY = "subject is empty"
_BOM_RULE = "subject has a leading UTF-8 BOM"
_UTF8_RULE = "subject is not strict UTF-8"
_DUPLICATE = "duplicate JSON key"
_NOT_JSON = "serialized SUBP is not JSON"
_NOT_UTF8 = "serialized SUBP is not UTF-8"
_RAW_TYPE = "serialized SUBP must be exact bytes"
_INEQUAL = "six-field records are not equal"
_DICT_RULE = "record must be an exact dict"
_EVIDENCE_WORDS = (
    "EVIDENCE",
    "TEXT",
    "VERIFIED",
    "SUPPORTED",
    "ADMITTED",
    "AUTHORITATIVE",
)
_CONCLUSION_WORDS = ("TRUE", "SUPPORTED", "AUTHORITATIVE")


def _design_vectors() -> tuple[str, str, list[str]]:
    text = _DESIGN.read_text(encoding="utf-8")
    golden, _, _attacks = text.partition("## Attack and mutation spec")
    quoted = [
        line[1:-1]
        for line in golden.splitlines()
        if line.startswith("`{") and line.endswith("`")
    ]
    hexes = re.findall(r"`([0-9a-f]{64})`", golden)
    if len(quoted) != 2 or len(hexes) != 19:
        raise RuntimeError("frozen SUBP vectors were not found")
    return quoted[0], quoted[1], hexes


_PREIMAGE_TEXT, _RECORD_TEXT, _HEXES = _design_vectors()
(
    _SUBJECT_DIGEST,
    _PREDICATE,
    _FINGERPRINT,
    _UNTAGGED,
    _CSAR_RECORD,
    _PRESENTED_SUBJECT_DOMAIN,
    _R4_CLAIM_BODY,
    _ACD,
    _PSRD_OVER_PREIMAGE,
    _NUL_SUBJECT,
    _NUL_PREDICATE,
    _JSON_SUBJECT,
    _JSON_PREDICATE,
    _SPACE_SUBJECT,
    _SPACE_PREDICATE,
    _NAN_SUBJECT,
    _NAN_PREDICATE,
    _DUP_SUBJECT,
    _DUP_PREDICATE,
) = _HEXES
_GOLDEN = json.loads(_RECORD_TEXT)
_SCHEMA = _GOLDEN["schema_version"]
_TOKEN = _GOLDEN["utf8_predicate"]
_LIMITATIONS = list(_GOLDEN["limitations"])


class _Text(str):
    """Exact text with a distinct type."""


class _AlwaysEqual(str):
    """Equality that hides a different string."""

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


class _Bytes(bytes):
    """Bytes subclass that must not alias the subject."""


class _List(list):
    """List subclass that must not alias limitations."""


class _Dict(dict):
    """Dict subclass that must not alias a record."""


def _canonical(value: dict) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _tag_digest(preimage: bytes) -> str:
    return hashlib.sha256(_TAG + preimage).hexdigest()


def _consistent(overrides: dict | None = None) -> dict:
    fields = {
        "schema_version": _SCHEMA,
        "authority": False,
        "utf8_predicate": _TOKEN,
        "presented_subject_digest": _SUBJECT_DIGEST,
        "limitations": list(_LIMITATIONS),
    }
    if overrides:
        fields.update(overrides)
    preimage = {key: fields[key] for key in _PREIMAGE_KEYS}
    record = dict(preimage)
    record["predicate_digest"] = _tag_digest(_canonical(preimage))
    return record


def _preimage_of(record: dict) -> dict:
    return {key: record[key] for key in _PREIMAGE_KEYS}


class StrictUtf8BytePredicateTests(unittest.TestCase):
    def test_golden_vector_matches_the_frozen_design(self) -> None:
        design = _DESIGN.read_text(encoding="utf-8")
        freeze = _FREEZE.read_text(encoding="utf-8")
        self.assertIn("HUMAN_DESIGN_FREEZE:\nACCEPTED", freeze)
        self.assertIn("bd0b893e11b3594a769935f68dcf878d9d17314e", freeze)
        self.assertIn("Planned attack tests:\n27", freeze)
        self.assertIn("Planned actual source-code mutations:\n15", freeze)
        attack_ids = re.findall(r"^### SUBP-A(\d+)$", design, re.MULTILINE)
        mutation_ids = re.findall(r"^### SUBP-S(\d+)$", design, re.MULTILINE)
        self.assertEqual(attack_ids, [f"{index:02d}" for index in range(1, 28)])
        self.assertEqual(mutation_ids, [f"{index:02d}" for index in range(1, 16)])
        names = {name[:8] for name in dir(type(self)) if name.startswith("test_a")}
        self.assertEqual(names, {f"test_a{index:02d}" for index in range(1, 28)})
        preimage = _PREIMAGE_TEXT.encode("utf-8")
        record_bytes = _RECORD_TEXT.encode("utf-8")
        self.assertNotIn(b"\r", preimage)
        self.assertNotIn(b"\r", record_bytes)
        self.assertFalse(preimage.endswith(b"\n"))
        self.assertFalse(record_bytes.endswith(b"\n"))
        self.assertEqual(len(preimage), 891)
        self.assertEqual(len(record_bytes), 977)
        self.assertNotIn("predicate_digest", _PREIMAGE_TEXT)
        self.assertEqual(digest_presented_subject_bytes(b"a"), _SUBJECT_DIGEST)
        self.assertEqual(_tag_digest(preimage), _PREDICATE)
        self.assertEqual(hashlib.sha256(record_bytes).hexdigest(), _FINGERPRINT)
        self.assertNotEqual(_FINGERPRINT, _PREDICATE)
        substitutes = {
            "untagged": hashlib.sha256(preimage).hexdigest(),
            "CSAR_RECORD": domain_separated_digest("CSAR_RECORD", preimage),
            "PRESENTED_SUBJECT_BYTES": domain_separated_digest(
                "PRESENTED_SUBJECT_BYTES", preimage
            ),
            "R4_CLAIM_BODY": domain_separated_digest("R4_CLAIM_BODY", preimage),
            "ACD": digest_association_carriage_preimage(preimage),
            "PSRD": hashlib.sha256(_PSRD_TAG + preimage).hexdigest(),
        }
        self.assertEqual(
            substitutes,
            {
                "untagged": _UNTAGGED,
                "CSAR_RECORD": _CSAR_RECORD,
                "PRESENTED_SUBJECT_BYTES": _PRESENTED_SUBJECT_DOMAIN,
                "R4_CLAIM_BODY": _R4_CLAIM_BODY,
                "ACD": _ACD,
                "PSRD": _PSRD_OVER_PREIMAGE,
            },
        )
        self.assertNotIn(_PREDICATE, substitutes.values())
        self.assertEqual(record_module._TAG, _TAG)
        self.assertEqual(len(_LIMITATIONS), 29)
        produced = produce_subp(b"a")
        self.assertEqual(_canonical(produced), record_bytes)
        self.assertEqual(produced["presented_subject_digest"], _SUBJECT_DIGEST)
        self.assertEqual(produced["predicate_digest"], _PREDICATE)
        self.assertIs(produced["authority"], False)
        self.assertEqual(produced["utf8_predicate"], _TOKEN)
        self.assertEqual(produced["limitations"], _LIMITATIONS)
        self.assertEqual(parse_subp(record_bytes), produced)
        self.assertEqual(subp_structurally_consistent(produced), _STRUCTURAL)
        self.assertEqual(
            subp_reproduced_from_supplied_inputs(produced, b"a"),
            _REPRODUCED,
        )
        produced["limitations"].append("caller-added")
        again = produce_subp(b"a")
        self.assertEqual(again["limitations"], _LIMITATIONS)
        source = Path(record_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("produce_psrd", source)
        self.assertNotIn("canonical_dumps", source)
        self.assertNotIn("canonical_digest", source)
        self.assertNotIn("weaver.psrd.digest", source)

    def test_a01_caller_kind_or_format_is_not_a_parameter(self) -> None:
        calls: list[bytes] = []
        real = record_module.hashlib.sha256

        def spy(data: bytes = b"", *args, **kwargs):
            calls.append(data)
            return real(data, *args, **kwargs)

        with patch.object(record_module.hashlib, "sha256", spy):
            for keyword, value in (("kind", "LOG"), ("format", "UTF8_TEXT")):
                with self.subTest(keyword=keyword):
                    with self.assertRaises(TypeError) as caught:
                        produce_subp(b"a", **{keyword: value})
                    self.assertNotIn("LOG verified", str(caught.exception))
        self.assertEqual(calls, [])
        self.assertFalse(any(b"LOG" in item for item in calls))

    def test_a02_filename_and_path_are_not_a_format(self) -> None:
        with self.assertRaises(TypeError) as caught:
            produce_subp(b"a", filename="notes.log")
        self.assertNotIn("LOG verified", str(caught.exception))

        def opened(*args, **kwargs):
            raise OSError("path was opened")

        with patch("builtins.open", opened):
            with self.assertRaises(SubpError) as rejected:
                produce_subp("C:/missing/subject.bin")
        self.assertEqual(rejected.exception.code, "SUBP_REJECTED")
        self.assertIn(_SUBJECT_TYPE, str(rejected.exception))
        self.assertNotIsInstance(rejected.exception, OSError)
        self.assertNotIsInstance(rejected.exception.__cause__, OSError)

    def test_a03_mime_is_not_hashed(self) -> None:
        calls: list[bytes] = []
        real = record_module.hashlib.sha256

        def spy(data: bytes = b"", *args, **kwargs):
            calls.append(data)
            return real(data, *args, **kwargs)

        with patch.object(record_module.hashlib, "sha256", spy):
            with self.assertRaises(TypeError) as caught:
                produce_subp(b"a", mime="application/json")
        self.assertNotIn("JSON verified", str(caught.exception))
        self.assertEqual(calls, [])
        self.assertFalse(any(b"application/json" in item for item in calls))

    def test_a04_nul_holds_without_retaining_decoded_text(self) -> None:
        record = produce_subp(b"\x00")
        self.assertEqual(record["utf8_predicate"], _TOKEN)
        self.assertEqual(record["presented_subject_digest"], _NUL_SUBJECT)
        self.assertEqual(record["predicate_digest"], _NUL_PREDICATE)
        self.assertEqual(set(record), set(_PREIMAGE_KEYS) | {"predicate_digest"})
        self.assertNotIn("\x00", json.dumps(record))
        structural = subp_structurally_consistent(record)
        reproduced = subp_reproduced_from_supplied_inputs(record, b"\x00")
        self.assertEqual(structural, _STRUCTURAL)
        self.assertEqual(reproduced, _REPRODUCED)
        self.assertIsInstance(structural, str)
        self.assertIsInstance(reproduced, str)
        self.assertNotIsInstance(structural, bool)
        self.assertNotIsInstance(reproduced, bool)

    def test_a05_invalid_json_text_holds_the_utf8_predicate(self) -> None:
        def loads(*args, **kwargs):
            raise AssertionError("subject was parsed as JSON")

        with patch.object(record_module.json, "loads", loads):
            brace = produce_subp(b"{")
            nan = produce_subp(b"NaN")
        self.assertEqual(brace["utf8_predicate"], _TOKEN)
        self.assertEqual(nan["utf8_predicate"], _TOKEN)
        self.assertEqual(nan["presented_subject_digest"], _NAN_SUBJECT)
        self.assertEqual(nan["predicate_digest"], _NAN_PREDICATE)
        self.assertEqual(
            brace["presented_subject_digest"],
            digest_presented_subject_bytes(b"{"),
        )
        for record in (brace, nan):
            self.assertNotIn("JSON", json.dumps(record))
            self.assertNotIn("JSON", record["utf8_predicate"])

    def test_a06_scalar_and_object_share_one_token(self) -> None:
        def loads(*args, **kwargs):
            raise AssertionError("subject was parsed as JSON")

        with patch.object(record_module.json, "loads", loads):
            scalar = produce_subp(b"1")
            obj = produce_subp(b'{"a":1}')
        self.assertEqual(scalar["utf8_predicate"], _TOKEN)
        self.assertEqual(obj["utf8_predicate"], _TOKEN)
        self.assertEqual(obj["presented_subject_digest"], _JSON_SUBJECT)
        self.assertEqual(obj["predicate_digest"], _JSON_PREDICATE)
        self.assertNotEqual(
            scalar["presented_subject_digest"],
            obj["presented_subject_digest"],
        )
        self.assertNotEqual(scalar["predicate_digest"], obj["predicate_digest"])
        self.assertEqual(scalar["presented_subject_digest"], digest_presented_subject_bytes(b"1"))
        for record in (scalar, obj):
            encoded = json.dumps(record)
            self.assertNotIn("scalar", encoded)
            self.assertNotIn("object", encoded)

    def test_a07_duplicate_json_keys_are_not_a_subject_policy(self) -> None:
        raw = b'{"a":1,"a":2}'

        def loads(*args, **kwargs):
            raise AssertionError("subject was parsed as JSON")

        with patch.object(record_module.json, "loads", loads):
            record = produce_subp(raw)
        self.assertEqual(record["utf8_predicate"], _TOKEN)
        self.assertEqual(record["presented_subject_digest"], _DUP_SUBJECT)
        self.assertEqual(record["predicate_digest"], _DUP_PREDICATE)

    def test_a08_nan_and_infinity_text_are_not_json_numbers(self) -> None:
        seen: list[object] = []
        real = record_module.json.dumps

        def spy(obj, *args, **kwargs):
            seen.append(obj)
            self.assertIs(kwargs.get("allow_nan"), False)
            return real(obj, *args, **kwargs)

        with patch.object(record_module.json, "dumps", spy):
            nan = produce_subp(b"NaN")
            infinity = produce_subp(b"Infinity")
        self.assertEqual(nan["utf8_predicate"], _TOKEN)
        self.assertEqual(infinity["utf8_predicate"], _TOKEN)
        self.assertEqual(nan["presented_subject_digest"], _NAN_SUBJECT)
        self.assertEqual(nan["predicate_digest"], _NAN_PREDICATE)
        self.assertEqual(
            infinity["presented_subject_digest"],
            digest_presented_subject_bytes(b"Infinity"),
        )
        self.assertTrue(seen)
        self.assertTrue(all(type(obj) is dict for obj in seen))
        for record in (nan, infinity):
            self.assertFalse(any(type(value) is float for value in record.values()))
            self.assertNotIn("JSON", record["utf8_predicate"])

    def test_a09_leading_bom_is_rejected(self) -> None:
        caught = self._reject_message(lambda: produce_subp(b"\xef\xbb\xbfa"), _BOM_RULE)
        self.assertIsNone(caught.__cause__)

    def test_a10_utf16_is_not_transcoded(self) -> None:
        utf16 = "a".encode("utf-16")
        self.assertTrue(utf16.startswith((b"\xff\xfe", b"\xfe\xff")))
        caught = self._reject_message(lambda: produce_subp(utf16), _UTF8_RULE)
        self.assertIsInstance(caught.__cause__, UnicodeDecodeError)

    def test_a11_invalid_utf8_is_not_repaired(self) -> None:
        for subject in (b"\xff", bytes.fromhex("c080")):
            with self.subTest(subject=subject.hex()):
                caught = self._reject_message(lambda subject=subject: produce_subp(subject), _UTF8_RULE)
                self.assertIsInstance(caught.__cause__, UnicodeDecodeError)

    def test_a12_nul_is_not_a_terminator(self) -> None:
        record = produce_subp(b"\x00")
        self.assertIn("nul_not_terminator", record["limitations"])
        self.assertEqual(record["presented_subject_digest"], _NUL_SUBJECT)
        self.assertEqual(record["predicate_digest"], _NUL_PREDICATE)
        self.assertNotEqual(record["presented_subject_digest"], _SUBJECT_DIGEST)

    def test_a13_trailing_bytes_stay_in_the_subject(self) -> None:
        short = produce_subp(b"a")
        long = produce_subp(b"a\x00b")
        self.assertEqual(short["utf8_predicate"], _TOKEN)
        self.assertEqual(long["utf8_predicate"], _TOKEN)
        self.assertEqual(short["presented_subject_digest"], _SUBJECT_DIGEST)
        self.assertEqual(long["presented_subject_digest"], digest_presented_subject_bytes(b"a\x00b"))
        self.assertNotEqual(short["presented_subject_digest"], long["presented_subject_digest"])
        self.assertNotEqual(long["predicate_digest"], short["predicate_digest"])

    def test_a14_whitespace_and_nfc_are_not_canonicalized(self) -> None:
        spaced = produce_subp(b" a")
        plain = produce_subp(b"a")
        self.assertEqual(spaced["utf8_predicate"], _TOKEN)
        self.assertEqual(spaced["presented_subject_digest"], _SPACE_SUBJECT)
        self.assertEqual(spaced["predicate_digest"], _SPACE_PREDICATE)
        self.assertNotEqual(spaced["presented_subject_digest"], plain["presented_subject_digest"])
        self.assertNotEqual(spaced["predicate_digest"], plain["predicate_digest"])
        nfd = unicodedata.normalize("NFD", "é").encode("utf-8")
        nfc = unicodedata.normalize("NFC", "é").encode("utf-8")
        self.assertNotEqual(nfd, nfc)
        held = produce_subp(nfd)
        self.assertEqual(held["utf8_predicate"], _TOKEN)
        self.assertEqual(held["presented_subject_digest"], digest_presented_subject_bytes(nfd))
        self.assertNotEqual(held["presented_subject_digest"], digest_presented_subject_bytes(nfc))

    def test_a15_polyglot_json_keeps_one_token(self) -> None:
        record = produce_subp(b'{"a":1}')
        self.assertEqual(record["utf8_predicate"], _TOKEN)
        self.assertEqual(record["presented_subject_digest"], _JSON_SUBJECT)
        self.assertEqual(record["predicate_digest"], _JSON_PREDICATE)
        self.assertIn("not_exclusive_grammar", record["limitations"])
        self.assertEqual(set(record), set(_PREIMAGE_KEYS) | {"predicate_digest"})

    def test_a16_empty_bytes_are_rejected(self) -> None:
        calls: list[bytes] = []
        real = record_module._presented_digest

        def spy(subject: bytes) -> str:
            calls.append(subject)
            return real(subject)

        with patch.object(record_module, "_presented_digest", spy):
            caught = self._reject_message(lambda: produce_subp(b""), _EMPTY)
        self.assertEqual(calls, [])
        self.assertNotIsInstance(caught.__cause__, DomainSeparatedDigestError)

    def test_a17_byte_aliases_are_rejected(self) -> None:
        subjects = (bytearray(b"a"), memoryview(b"a"), _Bytes(b"a"))
        for subject in subjects:
            with self.subTest(subject=type(subject).__name__):
                with self.assertRaises(SubpError) as caught:
                    produce_subp(subject)
                self.assertEqual(caught.exception.code, "SUBP_REJECTED")
                self.assertIn(_SUBJECT_TYPE, str(caught.exception))
                self.assertNotIsInstance(caught.exception, OSError)
                self.assertNotIsInstance(caught.exception.__cause__, OSError)

    def test_a18_str_subclass_token_rejects_before_digest(self) -> None:
        exact = dict(produce_subp(b"a"))
        exact["utf8_predicate"] = _Text(_TOKEN)
        self.assertEqual(exact["utf8_predicate"], _TOKEN)
        self.assertEqual(exact["predicate_digest"], _PREDICATE)
        self._reject_rule(lambda: subp_structurally_consistent(exact), _TOKEN_RULE)
        evidence = _consistent({"utf8_predicate": _AlwaysEqual("EVIDENCE")})
        self._assert_consistent_digest(evidence)
        self._reject_rule(lambda: subp_structurally_consistent(evidence), _TOKEN_RULE)

    def test_a19_authority_zero_is_not_exact_false(self) -> None:
        recomputed = _consistent({"authority": 0})
        self.assertEqual(recomputed["authority"], False)
        self.assertIsNot(recomputed["authority"], False)
        self._assert_consistent_digest(recomputed)
        self._reject_rule(lambda: subp_structurally_consistent(recomputed), _AUTHORITY)
        self._reject_rule(
            lambda: subp_reproduced_from_supplied_inputs(recomputed, b"a"),
            _AUTHORITY,
        )
        stale = dict(produce_subp(b"a"))
        stale["authority"] = 0
        self.assertEqual(stale["predicate_digest"], _PREDICATE)
        self.assertEqual(stale["authority"], False)
        self._reject_rule(lambda: subp_structurally_consistent(stale), _AUTHORITY)
        self._reject_rule(lambda: subp_reproduced_from_supplied_inputs(stale, b"a"), _AUTHORITY)

    def test_a20_extra_or_missing_keys_keep_the_five_field_digest(self) -> None:
        for key, value in (("mime", "application/json"), ("evidence_id", "ext-1")):
            with self.subTest(key=key):
                record = dict(produce_subp(b"a"))
                record[key] = value
                self.assertEqual(record["predicate_digest"], _PREDICATE)
                self.assertEqual(_tag_digest(_canonical(_preimage_of(record))), _PREDICATE)
                self._reject_rule(lambda record=record: subp_structurally_consistent(record), _KEYS_RULE)
        missing = dict(produce_subp(b"a"))
        del missing["limitations"]
        self.assertEqual(missing["predicate_digest"], _PREDICATE)
        self._reject_rule(lambda: subp_structurally_consistent(missing), _KEYS_RULE)

    def test_a21_foreign_digests_are_not_the_predicate_digest(self) -> None:
        preimage = _PREIMAGE_TEXT.encode("utf-8")
        substitutes = (
            hashlib.sha256(preimage).hexdigest(),
            domain_separated_digest("CSAR_RECORD", preimage),
            domain_separated_digest("PRESENTED_SUBJECT_BYTES", preimage),
            domain_separated_digest("R4_CLAIM_BODY", preimage),
            digest_association_carriage_preimage(preimage),
            hashlib.sha256(_PSRD_TAG + preimage).hexdigest(),
            _SUBJECT_DIGEST,
        )
        self.assertEqual(
            substitutes,
            (
                _UNTAGGED,
                _CSAR_RECORD,
                _PRESENTED_SUBJECT_DOMAIN,
                _R4_CLAIM_BODY,
                _ACD,
                _PSRD_OVER_PREIMAGE,
                _SUBJECT_DIGEST,
            ),
        )
        for digest in substitutes:
            with self.subTest(digest=digest[:8]):
                self.assertEqual(len(digest), 64)
                self.assertNotEqual(digest, _PREDICATE)
                record = dict(produce_subp(b"a"))
                record["predicate_digest"] = digest
                self._reject_message(lambda record=record: subp_structurally_consistent(record), _DIGEST_RULE)

    def test_a22_stale_evidence_token_fails_the_token_rule(self) -> None:
        record = dict(produce_subp(b"a"))
        record["utf8_predicate"] = "EVIDENCE"
        self.assertEqual(record["predicate_digest"], _PREDICATE)
        caught = self._reject_rule(lambda: subp_structurally_consistent(record), _TOKEN_RULE)
        self.assertNotIn(_DIGEST_RULE, str(caught))

    def test_a23_structural_consistency_is_not_reproduction(self) -> None:
        golden = produce_subp(b"a")
        nul = produce_subp(b"\x00")
        self.assertNotEqual(nul["presented_subject_digest"], golden["presented_subject_digest"])
        self.assertNotEqual(nul["predicate_digest"], golden["predicate_digest"])

        def consulted(subject: bytes) -> str:
            raise AssertionError("structural check consulted a presented-subject digest")

        with patch.object(record_module, "_presented_digest", consulted):
            structural = subp_structurally_consistent(golden)
        self.assertEqual(structural, _STRUCTURAL)
        self.assertNotEqual(structural, _REPRODUCED)
        self.assertIsInstance(structural, str)
        self.assertNotIsInstance(structural, bool)
        self._reject_message(lambda: subp_reproduced_from_supplied_inputs(nul, b"a"), _INEQUAL)

    def test_a24_reproduction_compares_all_six_fields(self) -> None:
        zeros = dict(produce_subp(b"a"))
        zeros["predicate_digest"] = "0" * 64
        self.assertEqual(zeros["presented_subject_digest"], _SUBJECT_DIGEST)
        self._reject_message(lambda: subp_reproduced_from_supplied_inputs(zeros, b"a"), _DIGEST_RULE)
        changed = _consistent({"utf8_predicate": "EVIDENCE"})
        self.assertEqual(changed["presented_subject_digest"], _SUBJECT_DIGEST)
        self.assertNotEqual(changed["predicate_digest"], _PREDICATE)
        self.assertEqual(
            changed["presented_subject_digest"],
            produce_subp(b"a")["presented_subject_digest"],
        )
        self._reject_rule(lambda: subp_reproduced_from_supplied_inputs(changed, b"a"), _TOKEN_RULE)

    def test_a25_success_tags_are_not_an_evidence_kind(self) -> None:
        record = produce_subp(b"a")
        structural = subp_structurally_consistent(record)
        reproduced = subp_reproduced_from_supplied_inputs(record, b"a")
        self.assertEqual((structural, reproduced), (_STRUCTURAL, _REPRODUCED))
        self.assertIsInstance(structural, str)
        self.assertIsInstance(reproduced, str)
        self.assertNotIsInstance(structural, bool)
        self.assertNotIsInstance(reproduced, bool)
        self.assertEqual(record["utf8_predicate"], _TOKEN)
        self.assertIn("not_evidence_kind", record["limitations"])
        self.assertNotEqual("not_evidence_kind", "EVIDENCE")
        encoded = json.dumps(record)
        for word in _EVIDENCE_WORDS:
            self.assertNotIn(word, encoded)
            self.assertNotIn(word, structural)
            self.assertNotIn(word, reproduced)

    def test_a26_grammar_hold_is_not_truth_support_or_authority(self) -> None:
        record = produce_subp(b"a")
        structural = subp_structurally_consistent(record)
        reproduced = subp_reproduced_from_supplied_inputs(record, b"a")
        self.assertEqual(record["predicate_digest"], _PREDICATE)
        for word in _CONCLUSION_WORDS:
            self.assertNotIn(word, structural)
            self.assertNotIn(word, reproduced)
            self.assertNotIn(word, record["utf8_predicate"])
            self.assertNotEqual(record["predicate_digest"], word)

    def test_a27_public_surface_has_no_selector(self) -> None:
        functions = (
            produce_subp,
            parse_subp,
            subp_structurally_consistent,
            subp_reproduced_from_supplied_inputs,
        )
        for fn in functions:
            with self.subTest(fn=fn.__name__):
                signature = inspect.signature(fn)
                self.assertFalse(set(signature.parameters) & _FORBIDDEN_PARAMS)
                self.assertFalse(
                    any(
                        parameter.kind in (parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL)
                        for parameter in signature.parameters.values()
                    )
                )
        self.assertEqual(list(inspect.signature(produce_subp).parameters), ["subject"])
        self.assertEqual(list(inspect.signature(subp_structurally_consistent).parameters), ["record"])
        self.assertEqual(
            list(inspect.signature(subp_reproduced_from_supplied_inputs).parameters),
            ["record", "subject"],
        )
        self.assertEqual(list(inspect.signature(parse_subp).parameters), ["raw"])
        produced = produce_subp(b"a")
        for keyword in _FORBIDDEN_PARAMS:
            with self.subTest(keyword=keyword):
                with self.assertRaises(TypeError):
                    produce_subp(b"a", **{keyword: "selector"})
                with self.assertRaises(TypeError):
                    parse_subp(b"{}", **{keyword: "selector"})
                with self.assertRaises(TypeError):
                    subp_structurally_consistent(produced, **{keyword: "selector"})
                with self.assertRaises(TypeError):
                    subp_reproduced_from_supplied_inputs(produced, b"a", **{keyword: "selector"})
        self.assertEqual(subp.__all__, _PUBLIC)
        package_public = {name for name in vars(subp) if not name.startswith("_")}
        self.assertEqual(package_public, set(_PUBLIC) | {"record"})
        self.assertFalse(set(subp.__all__) & _FORBIDDEN_PUBLIC)
        module_names = {name for name in vars(record_module) if not name.startswith("__")}
        self.assertEqual(module_names, _NAMESPACE)
        defined = {
            name
            for name, value in vars(record_module).items()
            if inspect.isfunction(value) and value.__module__ == record_module.__name__
        }
        self.assertEqual(defined, _DEFINED)
        public_callables = {
            name
            for name, value in vars(record_module).items()
            if not name.startswith("_") and callable(value)
        }
        self.assertEqual(public_callables, set(_PUBLIC))
        self.assertFalse(set(vars(record_module)) & _FORBIDDEN_PUBLIC)
        self.assertNotIn("hash", SubpError.__dict__)
        self.assertEqual({name for name in vars(SubpError) if not name.startswith("__")}, set())
        self.assertEqual(list(inspect.signature(record_module._predicate_digest).parameters), ["preimage"])

    def test_record_bytes_reject_noncanonical_and_field_rules(self) -> None:
        raw = _RECORD_TEXT.encode("utf-8")
        needle = '"schema_version":"strict_utf8_byte_predicate.v0"'
        self.assertEqual(_RECORD_TEXT.count(needle), 1)
        duplicate = (_RECORD_TEXT.replace(needle, needle + "," + needle, 1)).encode("utf-8")
        self._reject_message(lambda: parse_subp(duplicate), _DUPLICATE)
        spaced = raw.replace(b"{", b"{ ", 1)
        escaped = raw.replace(
            b"strict_utf8_byte_predicate",
            b"\\u0073trict_utf8_byte_predicate",
            1,
        )
        newline = raw + b"\n"
        for attacked in (spaced, escaped, newline):
            with self.subTest(attacked=attacked[:12]):
                parsed = json.loads(attacked.decode("utf-8"))
                self.assertEqual(subp_structurally_consistent(parsed), _STRUCTURAL)
                self._reject_message(lambda attacked=attacked: parse_subp(attacked), _CANONICAL)
        self._reject_message(lambda: parse_subp(b"\xef\xbb\xbf" + raw), _NOT_JSON)
        self._reject_message(lambda: parse_subp(raw.decode("utf-8").encode("utf-16")), _NOT_UTF8)
        order = [
            "utf8_predicate",
            "schema_version",
            "presented_subject_digest",
            "limitations",
            "authority",
            "predicate_digest",
        ]
        body = ",".join(
            json.dumps(key, ensure_ascii=True)
            + ":"
            + json.dumps(_GOLDEN[key], separators=(",", ":"), ensure_ascii=True)
            for key in order
        )
        inserted = ("{" + body + "}").encode("utf-8")
        self.assertEqual(len(inserted), 977)
        self.assertNotEqual(inserted, raw)
        self.assertEqual(subp_structurally_consistent(json.loads(inserted.decode("utf-8"))), _STRUCTURAL)
        self._reject_message(lambda: parse_subp(inserted), _CANONICAL)
        reversed_limitations = _consistent({"limitations": list(reversed(_LIMITATIONS))})
        self._assert_consistent_digest(reversed_limitations)
        self._reject_rule(
            lambda: subp_structurally_consistent(reversed_limitations),
            _LIMITATION_RULE,
        )
        produced = produce_subp(b"a")
        for digest in (produced["predicate_digest"].upper(), "ab", "0" * 63, "0" * 65, "g" * 64):
            with self.subTest(digest=digest):
                record = dict(produced)
                record["predicate_digest"] = digest
                self._reject_rule(lambda record=record: subp_structurally_consistent(record), _MALFORMED)
        lying = list(_LIMITATIONS)
        lying[0] = _AlwaysEqual(_LIMITATIONS[0])
        lying_record = _consistent({"limitations": lying})
        self.assertEqual(lying_record["predicate_digest"], _PREDICATE)
        self._reject_rule(lambda: subp_structurally_consistent(lying_record), _LIMITATION_RULE)
        schema = _consistent({"schema_version": _Text(_SCHEMA)})
        self.assertEqual(schema["predicate_digest"], _PREDICATE)
        self._reject_rule(lambda: subp_structurally_consistent(schema), _SCHEMA_RULE)
        listed = _consistent({"limitations": _List(_LIMITATIONS)})
        self._reject_rule(lambda: subp_structurally_consistent(listed), _LIMITATION_RULE)
        digest_text = dict(produced)
        digest_text["predicate_digest"] = _Text(_PREDICATE)
        self._reject_rule(lambda: subp_structurally_consistent(digest_text), _MALFORMED)
        self._reject_rule(
            lambda: subp_structurally_consistent(_Dict(produced)),
            _DICT_RULE,
        )
        self._reject_message(lambda: parse_subp(_Bytes(raw)), _RAW_TYPE)
        self._reject_message(lambda: parse_subp("not-bytes"), _RAW_TYPE)
        self._reject_rule(lambda: parse_subp(b"[]"), _DICT_RULE)
        self._reject_message(lambda: parse_subp(raw + raw), _NOT_JSON)
        self._reject_rule(lambda: subp_structurally_consistent(_consistent({"authority": True})), _AUTHORITY)

    def _assert_consistent_digest(self, record: dict) -> None:
        self.assertEqual(
            record["predicate_digest"],
            _tag_digest(_canonical(_preimage_of(record))),
        )

    def _reject_code(self, fn) -> SubpError:
        with self.assertRaises(SubpError) as caught:
            fn()
        self.assertEqual(caught.exception.code, "SUBP_REJECTED")
        return caught.exception

    def _reject_message(self, fn, message: str) -> SubpError:
        caught = self._reject_code(fn)
        self.assertIn(message, str(caught))
        return caught

    def _reject_rule(self, fn, message: str) -> SubpError:
        caught = self._reject_message(fn, message)
        self.assertNotIn(_DIGEST_RULE, str(caught))
        return caught
