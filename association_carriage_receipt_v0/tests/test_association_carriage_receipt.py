"""Focused tests for Association Carriage Receipt v0."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import unittest

import association_carriage_receipt_v0 as acr
from association_carriage_digest_v0 import digest_association_carriage_preimage
from association_carriage_receipt_v0 import (
    AcrError,
    acr_reproduced_from_supplied_inputs,
    acr_structurally_consistent,
    parse_acr,
    produce_acr,
)
from association_carriage_receipt_v0 import receipt as receipt_module
from csar_v0 import (
    CsarError,
    csar_reproduced_from_supplied_inputs,
    csar_structurally_consistent,
    produce_csar,
)
from domain_separated_digest_v0 import domain_separated_digest

_FREEZE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "ACR_V0_HUMAN_DESIGN_FREEZE_20261004.md"
)
_ACD_FREEZE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "ACD_V0_HUMAN_DESIGN_FREEZE_20261004.md"
)
_RECEIPT = "bdd4a8cfb4e319547a322e505c8e525de8d09cf58ec9880b8b719b0fedbe00e2"
_FINGERPRINT = "1c00d03fb1e4430bde21fc7cc79ae93dd42fd2c3d26d4d56cd9467b9159ae1fe"
_UNTAGGED = "251e9a7ca83bd9d0f44116a3f1782c491f9697e15c46190e29cee9aa84e239b7"
_CSAR_RECORD_DIGEST = "66946272d5bb6214dff312dbac3879562dec7a31bc77d605fefc6250cf79ae5e"
_ASSOCIATION = "3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204"
_STRUCTURAL = "ACR_STRUCTURALLY_CONSISTENT"
_REPRODUCED = "ACR_REPRODUCED_FROM_SUPPLIED_INPUTS"
_PUBLIC = [
    "AcrError",
    "produce_acr",
    "parse_acr",
    "acr_structurally_consistent",
    "acr_reproduced_from_supplied_inputs",
]
_RECEIPT_NAMESPACE = {
    "annotations",
    "json",
    "re",
    "AssociationCarriageDigestError",
    "digest_association_carriage_preimage",
    "CsarError",
    "csar_reproduced_from_supplied_inputs",
    "csar_structurally_consistent",
    "produce_csar",
    "_SCHEMA_VERSION",
    "_LIMITATIONS",
    "_KEYS",
    "_DIGEST",
    "_CSAR_STRUCTURAL",
    "_CSAR_REPRODUCED",
    "AcrError",
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_consume_csar",
    "_receipt_digest",
    "_require_limitations",
    "_require_digest_text",
    "_require_csar_tag",
    "acr_structurally_consistent",
    "produce_acr",
    "parse_acr",
    "acr_reproduced_from_supplied_inputs",
}
_DEFINED = {
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_consume_csar",
    "_receipt_digest",
    "_require_limitations",
    "_require_digest_text",
    "_require_csar_tag",
    "acr_structurally_consistent",
    "produce_acr",
    "parse_acr",
    "acr_reproduced_from_supplied_inputs",
}
_FORBIDDEN_PARAMS = {
    "digest",
    "claim_digest",
    "subject_digest",
    "association_digest",
    "receipt_digest",
    "limitations",
    "authority",
    "domain",
    "domain_id",
    "prefix",
    "path",
    "filename",
    "expected",
    "tag",
}
_CSAR_KEYS = (
    "schema_version",
    "authority",
    "claim_digest_csar_v0",
    "subject_digest_csar_v0",
    "limitations",
    "association_digest_csar_v0",
)


def _claim(**over: object) -> dict:
    claim = {
        "schema_version": "r4.epistemic.claim.v1",
        "claim_id": "c1",
        "statement": "s",
        "claim_kind": "EMPIRICAL",
        "epistemic_status": "REPORTED",
        "scope": "scope-text",
        "authority": False,
    }
    claim.update(over)
    return claim


def _frozen_line(path: Path, marker: str) -> bytes:
    text = path.read_text(encoding="utf-8")
    window = text[text.index(marker) :]
    line = next(item for item in window.splitlines() if item.startswith("`{") and item.endswith("`"))
    return line[1:-1].encode("utf-8")


def _canonical(record: dict) -> bytes:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _preimage(record: dict) -> dict:
    return {
        "schema_version": record["schema_version"],
        "authority": record["authority"],
        "csar_record": record["csar_record"],
        "limitations": record["limitations"],
    }


class _Bytes(bytes):
    pass


class _Dict(dict):
    pass


class _List(list):
    pass


class _Str(str):
    pass


class _AuthorityGranted(str):
    """Limitation text whose equality does not reveal its contents."""

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


class AcrTests(unittest.TestCase):
    def _reject(self, fn) -> None:
        with self.assertRaises(AcrError) as caught:
            fn()
        self.assertEqual(caught.exception.code, "ACR_REJECTED")

    def _reject_message(self, fn, message: str) -> None:
        with self.assertRaises(AcrError) as caught:
            fn()
        text = str(caught.exception)
        self.assertEqual(caught.exception.code, "ACR_REJECTED")
        self.assertIn(message, text)
        self.assertNotIn("receipt digest does not reproduce", text)

    def _with_consistent_receipt(self, record: dict) -> dict:
        mutated = dict(record)
        expected = digest_association_carriage_preimage(_canonical(_preimage(mutated)))
        mutated["receipt_digest"] = expected
        self.assertEqual(
            digest_association_carriage_preimage(_canonical(_preimage(mutated))),
            mutated["receipt_digest"],
        )
        return mutated

    def _produced(self) -> dict:
        claim = _claim()
        return produce_acr(claim, b"a", produce_csar(claim, b"a"))

    def test_01_golden_matches_frozen_bytes_and_closed_acd(self) -> None:
        claim = _claim()
        supplied = produce_csar(claim, b"a")
        record = produce_acr(claim, b"a", supplied)
        raw = _canonical(record)
        preimage = _canonical(_preimage(record))
        frozen_record = _frozen_line(_FREEZE, "Exact record text:")
        frozen_preimage = _frozen_line(_FREEZE, "Exact preimage text:")
        acd_fixture = _frozen_line(_ACD_FREEZE, "Exact fixture text:")
        self.assertEqual(raw, frozen_record)
        self.assertEqual(preimage, frozen_preimage)
        self.assertEqual(preimage, acd_fixture)
        self.assertEqual(len(preimage), 1346)
        self.assertEqual(len(raw), 1430)
        self.assertFalse(raw.endswith(b"\n"))
        self.assertFalse(preimage.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        self.assertNotIn(b"\r", preimage)
        self.assertNotIn(b"receipt_digest", preimage)
        self.assertEqual(record["receipt_digest"], _RECEIPT)
        self.assertEqual(digest_association_carriage_preimage(preimage), _RECEIPT)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _FINGERPRINT)
        self.assertNotEqual(_FINGERPRINT, _RECEIPT)
        self.assertEqual(hashlib.sha256(preimage).hexdigest(), _UNTAGGED)
        self.assertEqual(domain_separated_digest("CSAR_RECORD", preimage), _CSAR_RECORD_DIGEST)
        self.assertNotEqual(_RECEIPT, _UNTAGGED)
        self.assertNotEqual(_RECEIPT, _CSAR_RECORD_DIGEST)
        self.assertEqual(record["csar_record"]["association_digest_csar_v0"], _ASSOCIATION)
        self.assertIsNot(record["csar_record"], supplied)
        supplied["authority"] = True
        self.assertIs(record["csar_record"]["authority"], False)

    def test_02_parse_and_results_round_trip_the_golden(self) -> None:
        claim = _claim()
        record = self._produced()
        raw = _canonical(record)
        parsed = parse_acr(raw)
        self.assertEqual(parsed, record)
        self.assertEqual(acr_structurally_consistent(parsed), _STRUCTURAL)
        self.assertEqual(acr_reproduced_from_supplied_inputs(parsed, claim, b"a"), _REPRODUCED)
        self.assertEqual(
            csar_structurally_consistent(parsed["csar_record"]),
            "CSAR_STRUCTURALLY_CONSISTENT",
        )
        self.assertEqual(
            csar_reproduced_from_supplied_inputs(parsed["csar_record"], claim, b"a"),
            "CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS",
        )
        self.assertEqual(produce_acr(claim, b"a", parsed["csar_record"]), record)

    def test_03_exact_five_keys_types_and_limitation_order(self) -> None:
        record = self._produced()
        frozen = json.loads(_frozen_line(_FREEZE, "Exact record text:"))
        self.assertEqual(set(record), set(receipt_module._KEYS))
        self.assertIs(type(record), dict)
        self.assertIs(type(record["schema_version"]), str)
        self.assertEqual(record["schema_version"], "association_carriage_receipt.v0")
        self.assertIs(type(record["authority"]), bool)
        self.assertIs(record["authority"], False)
        self.assertIs(type(record["limitations"]), list)
        self.assertEqual(record["limitations"], frozen["limitations"])
        self.assertEqual(len(record["limitations"]), 22)
        for item in record["limitations"]:
            self.assertIs(type(item), str)
        self.assertIs(type(record["csar_record"]), dict)
        self.assertEqual(set(record["csar_record"]), set(_CSAR_KEYS))
        self.assertIs(type(record["receipt_digest"]), str)
        self.assertEqual(len(record["receipt_digest"]), 64)
        self.assertEqual(record["receipt_digest"], record["receipt_digest"].lower())

    def test_04_originals_are_not_retained(self) -> None:
        raw = _canonical(self._produced())
        for needle in (b"claim_id", b"scope-text", b"EMPIRICAL", b"REPORTED", b"r4.epistemic"):
            self.assertNotIn(needle, raw)

    def test_05_altered_originals_fail_reproduction_and_keep_structure(self) -> None:
        claim = _claim()
        record = self._produced()
        self.assertEqual(acr_structurally_consistent(record), _STRUCTURAL)
        self._reject(lambda: acr_reproduced_from_supplied_inputs(record, _claim(statement="other"), b"a"))
        self._reject(lambda: acr_reproduced_from_supplied_inputs(record, claim, b"b"))
        self._reject(lambda: produce_acr(_claim(statement="other"), b"a", record["csar_record"]))
        self._reject(lambda: produce_acr(claim, b"b", record["csar_record"]))

    def test_06_forged_consistent_receipt_is_not_reproduced_from_other_inputs(self) -> None:
        other_claim = _claim(claim_id="c2")
        forged = produce_acr(other_claim, b"a", produce_csar(other_claim, b"a"))
        self.assertEqual(acr_structurally_consistent(forged), _STRUCTURAL)
        self.assertNotEqual(acr_structurally_consistent(forged), _REPRODUCED)
        self._reject(lambda: acr_reproduced_from_supplied_inputs(forged, _claim(), b"a"))
        self.assertEqual(
            acr_reproduced_from_supplied_inputs(forged, other_claim, b"a"),
            _REPRODUCED,
        )

    def test_07_stale_receipt_digest_is_rejected_for_the_digest_rule(self) -> None:
        record = self._produced()
        stale = dict(record)
        last = "0" if record["receipt_digest"][-1] != "0" else "1"
        stale["receipt_digest"] = record["receipt_digest"][:-1] + last
        with self.assertRaises(AcrError) as caught:
            acr_structurally_consistent(stale)
        self.assertEqual(caught.exception.code, "ACR_REJECTED")
        self.assertIn("receipt digest does not reproduce", str(caught.exception))
        self._reject(lambda: acr_reproduced_from_supplied_inputs(stale, _claim(), b"a"))

    def test_08_reordered_limitations_with_consistent_digest_are_rejected(self) -> None:
        record = dict(self._produced())
        record["limitations"] = list(reversed(record["limitations"]))
        record = self._with_consistent_receipt(record)
        self._reject_message(
            lambda: acr_structurally_consistent(record),
            "limitations are not the code-owned list",
        )

    def test_09_authority_zero_with_consistent_digest_is_rejected(self) -> None:
        record = self._with_consistent_receipt(dict(self._produced(), authority=0))
        self.assertEqual(record["authority"], False)
        self.assertIs(type(record["authority"]), int)
        self._reject_message(lambda: acr_structurally_consistent(record), "authority is not exact False")

    def test_10_authority_true_and_schema_mismatch_fail(self) -> None:
        true_authority = self._with_consistent_receipt(dict(self._produced(), authority=True))
        self._reject_message(
            lambda: acr_structurally_consistent(true_authority),
            "authority is not exact False",
        )
        renamed = self._with_consistent_receipt(
            dict(self._produced(), schema_version="association_carriage_receipt.v9")
        )
        self._reject_message(lambda: acr_structurally_consistent(renamed), "schema_version mismatch")

    def test_11_extra_and_missing_keys_fail_before_the_digest_rule(self) -> None:
        extra = self._with_consistent_receipt(dict(self._produced(), note=""))
        self.assertEqual(extra["receipt_digest"], self._produced()["receipt_digest"])
        self._reject_message(
            lambda: acr_structurally_consistent(extra),
            "record keys are not the five-field schema",
        )
        missing = dict(self._produced())
        del missing["limitations"]
        self._reject_message(
            lambda: acr_structurally_consistent(missing),
            "record keys are not the five-field schema",
        )

    def test_12_schema_and_digest_subclasses_with_consistent_digest_are_rejected(self) -> None:
        named = dict(self._produced())
        named["schema_version"] = _Str("association_carriage_receipt.v0")
        named = self._with_consistent_receipt(named)
        self.assertEqual(named["receipt_digest"], _RECEIPT)
        self.assertIsNot(type(named["schema_version"]), str)
        self._reject_message(lambda: acr_structurally_consistent(named), "schema_version mismatch")
        digested = dict(self._produced())
        digested["receipt_digest"] = _Str(digested["receipt_digest"])
        self.assertEqual(digested["receipt_digest"], _RECEIPT)
        self.assertIsNot(type(digested["receipt_digest"]), str)
        self._reject_message(lambda: acr_structurally_consistent(digested), "digest text is malformed")

    def test_13_limitation_str_subclass_is_rejected_when_digest_matches(self) -> None:
        claim = _claim()
        record = dict(self._produced())
        same_text = list(record["limitations"])
        same_text[0] = _Str(same_text[0])
        same = self._with_consistent_receipt(dict(record, limitations=same_text))
        self.assertEqual(same["receipt_digest"], _RECEIPT)
        self.assertEqual(same["limitations"][0], receipt_module._LIMITATIONS[0])
        self.assertIsNot(type(same["limitations"][0]), str)
        self._reject_message(
            lambda: acr_structurally_consistent(same),
            "limitations are not the code-owned list",
        )
        self._reject_message(
            lambda: acr_reproduced_from_supplied_inputs(same, claim, b"a"),
            "limitations are not the code-owned list",
        )
        lying = list(record["limitations"])
        lying[0] = _AuthorityGranted("authority_granted")
        lied = self._with_consistent_receipt(dict(record, limitations=lying))
        self.assertEqual(lied["limitations"][0], receipt_module._LIMITATIONS[0])
        self.assertNotEqual(digest_association_carriage_preimage(_canonical(_preimage(lied))), _RECEIPT)
        self._reject_message(
            lambda: acr_structurally_consistent(lied),
            "limitations are not the code-owned list",
        )
        # Canonical JSON keeps the characters and json.loads returns a builtin str.
        raw = _canonical(lied)
        self.assertIn(b"authority_granted", raw)
        self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
        self._reject_message(lambda: parse_acr(raw), "limitations are not the code-owned list")

    def test_14_nested_csar_failures_survive_a_recomputed_outer_digest(self) -> None:
        record = dict(self._produced())
        nested = dict(record["csar_record"])
        nested["association_digest_csar_v0"] = "0" * 64
        embedded = self._with_consistent_receipt(dict(record, csar_record=nested))
        with self.assertRaises(AcrError) as caught:
            acr_structurally_consistent(embedded)
        self.assertIsInstance(caught.exception.__cause__, CsarError)
        self.assertIn("association digest does not reproduce", str(caught.exception))
        self.assertNotIn("receipt digest does not reproduce", str(caught.exception))
        zero_authority = dict(record["csar_record"])
        zero_authority["authority"] = 0
        csar_preimage = {key: zero_authority[key] for key in _CSAR_KEYS if key != "association_digest_csar_v0"}
        zero_authority["association_digest_csar_v0"] = domain_separated_digest(
            "CSAR_RECORD",
            _canonical(csar_preimage),
        )
        outer = self._with_consistent_receipt(dict(record, csar_record=zero_authority))
        self._reject_message(lambda: acr_structurally_consistent(outer), "authority is not exact False")
        self.assertIsInstance(
            self._raised(lambda: acr_structurally_consistent(outer)).__cause__,
            CsarError,
        )

    def test_15_nested_subject_flip_stays_structural_and_fails_reproduction(self) -> None:
        claim = _claim()
        record = dict(self._produced())
        nested = dict(record["csar_record"])
        nested["subject_digest_csar_v0"] = "0" * 64
        csar_preimage = {key: nested[key] for key in _CSAR_KEYS if key != "association_digest_csar_v0"}
        nested["association_digest_csar_v0"] = domain_separated_digest(
            "CSAR_RECORD",
            _canonical(csar_preimage),
        )
        self.assertEqual(csar_structurally_consistent(nested), "CSAR_STRUCTURALLY_CONSISTENT")
        outer = self._with_consistent_receipt(dict(record, csar_record=nested))
        self.assertEqual(acr_structurally_consistent(outer), _STRUCTURAL)
        self._reject_message(
            lambda: acr_reproduced_from_supplied_inputs(outer, claim, b"a"),
            "six-field records are not equal",
        )

    def test_16_one_nested_csar_is_required(self) -> None:
        record = self._produced()
        digest_only = dict(record, csar_record=record["csar_record"]["association_digest_csar_v0"])
        path_only = dict(record, csar_record="C:/missing/nested-csar.json")
        several = dict(record, csar_record=[record["csar_record"], record["csar_record"]])
        missing = dict(record)
        del missing["csar_record"]
        outside = dict(record, outside_csar=record["csar_record"])
        for mutated in (digest_only, path_only, several):
            with self.subTest(kind=type(mutated["csar_record"]).__name__):
                with self.assertRaises(AcrError) as caught:
                    acr_structurally_consistent(mutated)
                self.assertIn("csar_record must be one exact dict", str(caught.exception))
                self.assertNotIsInstance(caught.exception.__cause__, OSError)
        self._reject_message(
            lambda: acr_structurally_consistent(missing),
            "record keys are not the five-field schema",
        )
        self._reject_message(
            lambda: acr_structurally_consistent(outside),
            "record keys are not the five-field schema",
        )
        self._reject(lambda: produce_acr(_claim(), b"a", record["receipt_digest"]))
        self._reject(lambda: produce_acr(_claim(), "C:/missing/subject.bin", record["csar_record"]))

    def test_17_duplicate_json_keys_fail(self) -> None:
        raw = _canonical(self._produced())
        outer = raw.replace(
            b'"schema_version":"association_carriage_receipt.v0"',
            b'"schema_version":"association_carriage_receipt.v0","schema_version":"association_carriage_receipt.v0"',
            1,
        )
        nested = raw.replace(
            b'"schema_version":"csar.v0"',
            b'"schema_version":"csar.v0","schema_version":"csar.v0"',
            1,
        )
        for duplicated in (outer, nested):
            with self.subTest(duplicated=duplicated[:40]):
                self._reject_message(lambda duplicated=duplicated: parse_acr(duplicated), "duplicate JSON key")

    def test_18_noncanonical_bytes_fail_after_values_remain_structural(self) -> None:
        raw = _canonical(self._produced())
        spaced = raw.replace(b",", b", ", 1)
        escaped = raw.replace(b"carries_exactly", b"\\u0063arries_exactly", 1)
        self.assertEqual(json.loads(escaped.decode("utf-8"))["limitations"][0], "carries_exactly_one_nested_csar_v0")
        for variant in (spaced, escaped, raw + b"\n", b" " + raw, raw + b"\r\n"):
            with self.subTest(variant=variant[:12]):
                self.assertNotEqual(variant, raw)
                self.assertEqual(acr_structurally_consistent(json.loads(variant.decode("utf-8"))), _STRUCTURAL)
                self._reject_message(lambda variant=variant: parse_acr(variant), "serialized bytes are not canonical")
        self._reject_message(lambda: parse_acr(b"\xef\xbb\xbf" + raw), "serialized ACR is not JSON")
        self._reject_message(lambda: parse_acr(raw.decode("utf-8").encode("utf-16")), "serialized ACR is not UTF-8")
        self._reject_message(lambda: parse_acr(b"\xff"), "serialized ACR is not UTF-8")
        self._reject_message(lambda: parse_acr(b"[]"), "record must be an exact dict")
        self._reject_message(lambda: parse_acr(b"null"), "record must be an exact dict")

    def test_19_rejected_insertion_order_has_the_same_length(self) -> None:
        record = json.loads(_frozen_line(_FREEZE, "Exact record text:"))
        nested = record["csar_record"]
        ordered_nested = {
            "authority": nested["authority"],
            "claim_digest_csar_v0": nested["claim_digest_csar_v0"],
            "limitations": nested["limitations"],
            "schema_version": nested["schema_version"],
            "subject_digest_csar_v0": nested["subject_digest_csar_v0"],
            "association_digest_csar_v0": nested["association_digest_csar_v0"],
        }
        ordered = {
            "schema_version": record["schema_version"],
            "authority": record["authority"],
            "csar_record": ordered_nested,
            "limitations": record["limitations"],
            "receipt_digest": record["receipt_digest"],
        }
        alternative = json.dumps(
            ordered,
            sort_keys=False,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        canonical = _canonical(record)
        self.assertEqual(len(alternative), 1430)
        self.assertNotEqual(alternative, canonical)
        self.assertTrue(hashlib.sha256(alternative).hexdigest().startswith("0291f454"))
        self.assertEqual(acr_structurally_consistent(json.loads(alternative)), _STRUCTURAL)
        self._reject_message(lambda: parse_acr(alternative), "serialized bytes are not canonical")

    def test_20_malformed_and_uppercase_receipt_digests_fail(self) -> None:
        record = self._produced()
        upper = dict(record)
        upper["receipt_digest"] = record["receipt_digest"].upper()
        self._reject_message(lambda: acr_structurally_consistent(upper), "digest text is malformed")
        for bad in ("ab", "a" * 63, "a" * 65, "g" * 64, "A" * 64, ""):
            with self.subTest(bad=bad):
                stale = dict(record, receipt_digest=bad)
                self._reject_message(lambda stale=stale: acr_structurally_consistent(stale), "digest text is malformed")

    def test_21_exact_builtin_types_are_required(self) -> None:
        claim = _claim()
        record = self._produced()
        self._reject(lambda: produce_acr(_Dict(claim), b"a", record["csar_record"]))
        self._reject(lambda: produce_acr(claim, _Bytes(b"a"), record["csar_record"]))
        self._reject(lambda: produce_acr(claim, bytearray(b"a"), record["csar_record"]))
        self._reject(lambda: produce_acr(claim, memoryview(b"a"), record["csar_record"]))
        self._reject(lambda: produce_acr(claim, b"", record["csar_record"]))
        self._reject_message(lambda: acr_structurally_consistent(_Dict(record)), "record must be an exact dict")
        listed = self._with_consistent_receipt(dict(record, limitations=_List(record["limitations"])))
        self.assertEqual(listed["receipt_digest"], _RECEIPT)
        self._reject_message(
            lambda: acr_structurally_consistent(listed),
            "limitations are not the code-owned list",
        )
        keyed = dict(record)
        del keyed["schema_version"]
        keyed[_Str("schema_version")] = "association_carriage_receipt.v0"
        self._reject_message(lambda: acr_structurally_consistent(keyed), "key must be exact str")
        nested = _Dict(record["csar_record"])
        wrapped = self._with_consistent_receipt(dict(record, csar_record=nested))
        self._reject_message(
            lambda: acr_structurally_consistent(wrapped),
            "csar_record must be one exact dict",
        )
        raw = _canonical(record)
        self._reject_message(lambda: parse_acr(_Bytes(raw)), "serialized ACR must be exact bytes")
        self._reject_message(lambda: parse_acr(bytearray(raw)), "serialized ACR must be exact bytes")
        self._reject_message(lambda: parse_acr(memoryview(raw)), "serialized ACR must be exact bytes")
        self._reject_message(lambda: parse_acr(raw.decode("utf-8")), "serialized ACR must be exact bytes")

    def test_22_parse_rejects_canonical_structurally_invalid_records(self) -> None:
        produced = self._produced()
        cases = (
            self._with_consistent_receipt(dict(produced, authority=0)),
            self._with_consistent_receipt(
                dict(produced, limitations=list(reversed(produced["limitations"])))
            ),
            self._with_consistent_receipt(
                dict(produced, schema_version="association_carriage_receipt.v9")
            ),
        )
        messages = (
            "authority is not exact False",
            "limitations are not the code-owned list",
            "schema_version mismatch",
        )
        for mutated, message in zip(cases, messages, strict=True):
            raw = _canonical(mutated)
            self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
            with self.subTest(message=message):
                self._reject_message(lambda raw=raw: parse_acr(raw), message)

    def test_23_reproduction_rejects_outer_records_that_match_only_some_fields(self) -> None:
        claim = _claim()
        produced = self._produced()
        authority_zero = dict(produced, authority=0)
        self.assertEqual(authority_zero["authority"], produced["authority"])
        self.assertIs(type(authority_zero["authority"]), int)
        zero_receipt = dict(produced, receipt_digest="0" * 64)
        reversed_limitations = dict(produced, limitations=list(reversed(produced["limitations"])))
        self._reject_message(
            lambda: acr_reproduced_from_supplied_inputs(authority_zero, claim, b"a"),
            "authority is not exact False",
        )
        with self.assertRaises(AcrError) as caught:
            acr_reproduced_from_supplied_inputs(zero_receipt, claim, b"a")
        self.assertIn("receipt digest does not reproduce", str(caught.exception))
        self._reject_message(
            lambda: acr_reproduced_from_supplied_inputs(reversed_limitations, claim, b"a"),
            "limitations are not the code-owned list",
        )

    def test_24_no_caller_controlled_digest_domain_or_limitations(self) -> None:
        for fn in (
            produce_acr,
            parse_acr,
            acr_structurally_consistent,
            acr_reproduced_from_supplied_inputs,
        ):
            with self.subTest(fn=fn.__name__):
                signature = inspect.signature(fn)
                self.assertFalse(set(signature.parameters) & _FORBIDDEN_PARAMS)
                self.assertFalse(
                    any(
                        parameter.kind in (parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL)
                        for parameter in signature.parameters.values()
                    )
                )
        self.assertEqual(
            list(inspect.signature(produce_acr).parameters),
            ["claim", "subject", "csar_record"],
        )
        self.assertEqual(list(inspect.signature(acr_structurally_consistent).parameters), ["record"])
        self.assertEqual(list(inspect.signature(parse_acr).parameters), ["raw"])
        self.assertEqual(
            list(inspect.signature(acr_reproduced_from_supplied_inputs).parameters),
            ["record", "claim", "subject"],
        )
        claim = _claim()
        nested = produce_csar(claim, b"a")
        with self.assertRaises(TypeError):
            produce_acr(claim, b"a", nested, receipt_digest=_RECEIPT)
        with self.assertRaises(TypeError):
            produce_acr(claim, b"a", nested, limitations=["not_truth"])
        with self.assertRaises(TypeError):
            produce_acr(claim, b"a", nested, domain="CSAR_RECORD")
        with self.assertRaises(TypeError):
            produce_acr(claim, b"a", nested, prefix="weaver.acr.digest.v0")
        with self.assertRaises(TypeError):
            produce_acr(claim, b"a", nested, path="C:/missing/acr.json")

    def test_25_results_are_not_bool_and_avoid_forbidden_words(self) -> None:
        claim = _claim()
        record = self._produced()
        results = (
            acr_structurally_consistent(record),
            acr_reproduced_from_supplied_inputs(record, claim, b"a"),
        )
        self.assertEqual(results, (_STRUCTURAL, _REPRODUCED))
        source = Path(receipt_module.__file__).read_text(encoding="utf-8")
        for result in results:
            self.assertIs(type(result), str)
            self.assertNotIsInstance(result, bool)
            for word in ("PASS", "VALID", "VERIFIED", "ACCEPTED"):
                self.assertNotIn(word, result)
                self.assertNotIn(word, source)

    def test_26_public_surface_consumes_closed_apis_without_a_selector(self) -> None:
        self.assertEqual(acr.__all__, _PUBLIC)
        package_public = {name for name in vars(acr) if not name.startswith("_")}
        self.assertEqual(package_public, set(_PUBLIC) | {"receipt"})
        module_names = {name for name in vars(receipt_module) if not name.startswith("__")}
        self.assertEqual(module_names, _RECEIPT_NAMESPACE)
        defined = {
            name
            for name, value in vars(receipt_module).items()
            if inspect.isfunction(value) and value.__module__ == receipt_module.__name__
        }
        self.assertEqual(defined, _DEFINED)
        self.assertEqual({name for name in vars(AcrError) if not name.startswith("__")}, set())
        source = Path(receipt_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("hashlib", source)
        self.assertNotIn("domain_separated_digest", source)
        self.assertNotIn("canonical_digest", source)
        self.assertNotIn("parse_csar", source)
        structural = inspect.getsource(acr_structurally_consistent)
        self.assertIn("csar_structurally_consistent", structural)
        self.assertNotIn("produce_csar", structural)
        self.assertNotIn("csar_reproduced_from_supplied_inputs", structural)
        reproduction = inspect.getsource(acr_reproduced_from_supplied_inputs)
        self.assertIn("acr_structurally_consistent(record)", reproduction)
        self.assertIn("csar_reproduced_from_supplied_inputs", reproduction)
        creation = inspect.getsource(produce_acr)
        self.assertIn("csar_reproduced_from_supplied_inputs", creation)
        self.assertIn("_receipt_digest", creation)
        self.assertIn(
            "digest_association_carriage_preimage",
            inspect.getsource(receipt_module._receipt_digest),
        )
        self.assertNotIn("acr_structurally_consistent", creation)

    def _raised(self, fn) -> AcrError:
        with self.assertRaises(AcrError) as caught:
            fn()
        return caught.exception
