"""Focused tests for Claim / Subject Association Record v0."""

from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import unittest

import csar_v0 as csar
from csar_v0 import (
    CsarError,
    csar_reproduced_from_supplied_inputs,
    csar_structurally_consistent,
    parse_csar,
    produce_csar,
)
from csar_v0 import record as record_module
from domain_separated_digest_v0 import (
    digest_presented_subject_bytes,
    digest_r4_claim_body,
    domain_separated_digest,
)

_FREEZE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "CSAR_V0_HUMAN_DESIGN_FREEZE_20261004.md"
)
_CLAIM_DIGEST = "d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf"
_SUBJECT_DIGEST = "563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"
_ASSOCIATION_DIGEST = "3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204"
_STRUCTURAL = "CSAR_STRUCTURALLY_CONSISTENT"
_REPRODUCED = "CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS"
_PUBLIC = [
    "CsarError",
    "produce_csar",
    "parse_csar",
    "csar_structurally_consistent",
    "csar_reproduced_from_supplied_inputs",
]
_RECORD_NAMESPACE = {
    "annotations",
    "json",
    "re",
    "DomainSeparatedDigestError",
    "digest_presented_subject_bytes",
    "digest_r4_claim_body",
    "domain_separated_digest",
    "_ASSOCIATION_DOMAIN",
    "_SCHEMA_VERSION",
    "_LIMITATIONS",
    "_KEYS",
    "_PREIMAGE_KEYS",
    "_DIGEST",
    "CsarError",
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_closed_digest",
    "_require_limitations",
    "_require_digest_text",
    "csar_structurally_consistent",
    "produce_csar",
    "parse_csar",
    "csar_reproduced_from_supplied_inputs",
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


def _frozen_line(marker: str) -> bytes:
    text = _FREEZE.read_text(encoding="utf-8")
    window = text[text.index(marker) :]
    line = next(item for item in window.splitlines() if item.startswith('`{"') and item.endswith("`"))
    return line[1:-1].encode("utf-8")


def _canonical(record: dict) -> bytes:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


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


class CsarTests(unittest.TestCase):
    def _reject(self, fn) -> None:
        with self.assertRaises(CsarError) as caught:
            fn()
        self.assertEqual(caught.exception.code, "CSAR_REJECTED")

    def _reject_message(self, fn, message: str) -> None:
        with self.assertRaises(CsarError) as caught:
            fn()
        text = str(caught.exception)
        self.assertEqual(caught.exception.code, "CSAR_REJECTED")
        self.assertIn(message, text)
        self.assertNotIn("association digest does not reproduce", text)

    def _with_consistent_association(self, record: dict) -> dict:
        mutated = dict(record)
        preimage = {key: mutated[key] for key in record_module._PREIMAGE_KEYS}
        expected = domain_separated_digest("CSAR_RECORD", _canonical(preimage))
        mutated["association_digest_csar_v0"] = expected
        checked = {key: mutated[key] for key in record_module._PREIMAGE_KEYS}
        self.assertEqual(
            domain_separated_digest("CSAR_RECORD", _canonical(checked)),
            mutated["association_digest_csar_v0"],
        )
        return mutated

    def test_01_golden_producer_matches_closed_dsds(self) -> None:
        claim = _claim()
        record = produce_csar(claim, b"a")
        claim_digest = digest_r4_claim_body(claim)
        subject_digest = digest_presented_subject_bytes(b"a")
        preimage = _canonical(
            {
                "schema_version": "csar.v0",
                "authority": False,
                "claim_digest_csar_v0": claim_digest,
                "subject_digest_csar_v0": subject_digest,
                "limitations": record["limitations"],
            }
        )
        association = domain_separated_digest("CSAR_RECORD", preimage)
        self.assertEqual(record["claim_digest_csar_v0"], claim_digest)
        self.assertEqual(record["subject_digest_csar_v0"], subject_digest)
        self.assertEqual(record["association_digest_csar_v0"], association)
        self.assertEqual(claim_digest, _CLAIM_DIGEST)
        self.assertEqual(subject_digest, _SUBJECT_DIGEST)
        self.assertEqual(association, _ASSOCIATION_DIGEST)
        self.assertEqual(produce_csar(claim, b"a"), record)

    def test_02_golden_canonical_six_field_length_is_720(self) -> None:
        record = produce_csar(_claim(), b"a")
        raw = _canonical(record)
        frozen = _frozen_line("Canonical six-field record text")
        preimage = _frozen_line("Canonical preimage text")
        self.assertEqual(len(raw), 720)
        self.assertEqual(raw, frozen)
        self.assertFalse(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        self.assertEqual(len(preimage), 624)
        self.assertNotIn(b"association_digest_csar_v0", preimage)

    def test_03_structural_consistency_golden(self) -> None:
        record = produce_csar(_claim(), b"a")
        result = csar_structurally_consistent(record)
        self.assertEqual(result, _STRUCTURAL)
        self.assertIs(type(result), str)

    def test_04_reproduction_golden(self) -> None:
        claim = _claim()
        record = produce_csar(claim, b"a")
        result = csar_reproduced_from_supplied_inputs(record, claim, b"a")
        self.assertEqual(result, _REPRODUCED)
        parsed = parse_csar(_canonical(record))
        self.assertEqual(csar_reproduced_from_supplied_inputs(parsed, claim, b"a"), _REPRODUCED)

    def test_05_altered_original_claim_reproduction_fails(self) -> None:
        record = produce_csar(_claim(), b"a")
        self._reject(lambda: csar_reproduced_from_supplied_inputs(record, _claim(statement="other"), b"a"))

    def test_06_altered_subject_reproduction_fails(self) -> None:
        record = produce_csar(_claim(), b"a")
        self._reject(lambda: csar_reproduced_from_supplied_inputs(record, _claim(), b"b"))

    def test_07_altered_claim_digest_fails(self) -> None:
        record = produce_csar(_claim(), b"a")
        stale = dict(record)
        stale["claim_digest_csar_v0"] = "0" + record["claim_digest_csar_v0"][1:]
        self._reject(lambda: csar_structurally_consistent(stale))
        self._reject(lambda: csar_reproduced_from_supplied_inputs(stale, _claim(), b"a"))
        rebuilt = dict(stale)
        preimage = _canonical({key: rebuilt[key] for key in record_module._PREIMAGE_KEYS})
        rebuilt["association_digest_csar_v0"] = domain_separated_digest("CSAR_RECORD", preimage)
        self.assertEqual(csar_structurally_consistent(rebuilt), _STRUCTURAL)
        self._reject(lambda: csar_reproduced_from_supplied_inputs(rebuilt, _claim(), b"a"))

    def test_08_altered_subject_digest_fails(self) -> None:
        record = produce_csar(_claim(), b"a")
        stale = dict(record)
        stale["subject_digest_csar_v0"] = "0" + record["subject_digest_csar_v0"][1:]
        self._reject(lambda: csar_structurally_consistent(stale))
        self._reject(lambda: csar_reproduced_from_supplied_inputs(stale, _claim(), b"a"))

    def test_09_altered_association_digest_structural_fails(self) -> None:
        record = produce_csar(_claim(), b"a")
        stale = dict(record)
        last = "0" if record["association_digest_csar_v0"][-1] != "0" else "1"
        stale["association_digest_csar_v0"] = record["association_digest_csar_v0"][:-1] + last
        self._reject(lambda: csar_structurally_consistent(stale))

    def test_10_altered_limitations_fail(self) -> None:
        record = produce_csar(_claim(), b"a")
        stale = dict(record)
        stale["limitations"] = list(record["limitations"])
        stale["limitations"][0] = "presented_text_only"
        self._reject(lambda: csar_structurally_consistent(stale))

    def test_11_reordered_limitations_fail(self) -> None:
        record = produce_csar(_claim(), b"a")
        stale = dict(record)
        stale["limitations"] = list(reversed(record["limitations"]))
        self._reject(lambda: csar_structurally_consistent(stale))

    def test_12_authority_true_fails(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["authority"] = True
        self._reject(lambda: csar_structurally_consistent(record))

    def test_13_authority_zero_fails(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["authority"] = 0
        self._reject(lambda: csar_structurally_consistent(record))

    def test_14_schema_mismatch_fails(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["schema_version"] = "csar.v1"
        self._reject(lambda: csar_structurally_consistent(record))

    def test_15_extra_key_fails(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["note"] = ""
        self._reject(lambda: csar_structurally_consistent(record))

    def test_16_missing_key_fails(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        del record["limitations"]
        self._reject(lambda: csar_structurally_consistent(record))

    def test_17_duplicate_json_key_strict_parse_fails(self) -> None:
        raw = _canonical(produce_csar(_claim(), b"a"))
        duplicated = raw.replace(
            b'"schema_version":"csar.v0"',
            b'"schema_version":"csar.v0","schema_version":"csar.v0"',
            1,
        )
        with self.assertRaises(CsarError) as caught:
            parse_csar(duplicated)
        self.assertEqual(caught.exception.code, "CSAR_REJECTED")
        self.assertIn("duplicate JSON key", str(caught.exception))

    def test_18_noncanonical_json_bytes_fail(self) -> None:
        raw = _canonical(produce_csar(_claim(), b"a"))
        self._reject(lambda: parse_csar(raw.replace(b"{", b"{ ", 1)))

    def test_19_trailing_newline_fails(self) -> None:
        raw = _canonical(produce_csar(_claim(), b"a"))
        self._reject(lambda: parse_csar(raw + b"\n"))

    def test_20_uppercase_digest_fails(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["claim_digest_csar_v0"] = record["claim_digest_csar_v0"].upper()
        preimage = _canonical({key: record[key] for key in record_module._PREIMAGE_KEYS})
        record["association_digest_csar_v0"] = domain_separated_digest("CSAR_RECORD", preimage)
        self._reject(lambda: csar_structurally_consistent(record))

    def test_21_short_long_and_nonhex_digest_fail(self) -> None:
        record = produce_csar(_claim(), b"a")
        for bad in ("ab", "a" * 63, "a" * 65, "g" * 64, "A" * 64):
            with self.subTest(bad=bad):
                stale = dict(record)
                stale["subject_digest_csar_v0"] = bad
                self._reject(lambda: csar_structurally_consistent(stale))

    def test_22_subject_bytearray_fails(self) -> None:
        self._reject(lambda: produce_csar(_claim(), bytearray(b"a")))
        record = produce_csar(_claim(), b"a")
        self._reject(lambda: csar_reproduced_from_supplied_inputs(record, _claim(), bytearray(b"a")))

    def test_23_subject_memoryview_fails(self) -> None:
        self._reject(lambda: produce_csar(_claim(), memoryview(b"a")))

    def test_24_bytes_subclass_fails(self) -> None:
        self._reject(lambda: produce_csar(_claim(), _Bytes(b"a")))

    def test_25_exact_builtin_subclasses_fail(self) -> None:
        self._reject(lambda: produce_csar(_Dict(_claim()), b"a"))
        self._reject(lambda: produce_csar(_claim(statement=_Str("s")), b"a"))
        record = dict(produce_csar(_claim(), b"a"))
        listed = dict(record)
        listed["limitations"] = _List(record["limitations"])
        self._reject(lambda: csar_structurally_consistent(listed))
        named = dict(record)
        named["schema_version"] = _Str("csar.v0")
        self._reject(lambda: csar_structurally_consistent(named))
        keyed = dict(record)
        del keyed["schema_version"]
        keyed[_Str("schema_version")] = "csar.v0"
        self._reject(lambda: csar_structurally_consistent(keyed))

    def test_26_caller_provided_digest_path_does_not_exist(self) -> None:
        for fn in (
            produce_csar,
            parse_csar,
            csar_structurally_consistent,
            csar_reproduced_from_supplied_inputs,
        ):
            with self.subTest(fn=fn.__name__):
                signature = inspect.signature(fn)
                names = set(signature.parameters)
                self.assertFalse(names & _FORBIDDEN_PARAMS)
                self.assertFalse(
                    any(
                        parameter.kind in (parameter.VAR_KEYWORD, parameter.VAR_POSITIONAL)
                        for parameter in signature.parameters.values()
                    )
                )
        self.assertEqual(list(inspect.signature(produce_csar).parameters), ["claim", "subject"])
        with self.assertRaises(TypeError):
            produce_csar(_claim(), b"a", claim_digest=_CLAIM_DIGEST)

    def test_27_caller_limitations_and_authority_override_do_not_exist(self) -> None:
        with self.assertRaises(TypeError):
            produce_csar(_claim(), b"a", limitations=["presented_bytes_only"])
        with self.assertRaises(TypeError):
            produce_csar(_claim(), b"a", authority=True)
        with self.assertRaises(TypeError):
            csar_reproduced_from_supplied_inputs(
                produce_csar(_claim(), b"a"),
                _claim(),
                b"a",
                authority=False,
            )

    def test_28_structural_result_omits_reproduced_tag(self) -> None:
        record = produce_csar(_claim(), b"a")
        result = csar_structurally_consistent(record)
        self.assertEqual(result, _STRUCTURAL)
        self.assertNotEqual(result, _REPRODUCED)
        self.assertEqual(list(inspect.signature(csar_structurally_consistent).parameters), ["record"])

    def test_29_fabricated_consistent_record_does_not_reproduce(self) -> None:
        fabricated = produce_csar(_claim(claim_id="c2"), b"a")
        self.assertEqual(csar_structurally_consistent(fabricated), _STRUCTURAL)
        self._reject(lambda: csar_reproduced_from_supplied_inputs(fabricated, _claim(), b"a"))

    def test_30_association_digest_uses_csar_record_domain(self) -> None:
        record = produce_csar(_claim(), b"a")
        preimage = _canonical({key: record[key] for key in record_module._PREIMAGE_KEYS})
        association = record["association_digest_csar_v0"]
        self.assertEqual(association, domain_separated_digest("CSAR_RECORD", preimage))
        self.assertNotEqual(association, hashlib.sha256(preimage).hexdigest())
        self.assertNotEqual(association, domain_separated_digest("R4_CLAIM_BODY", preimage))
        self.assertNotEqual(association, domain_separated_digest("PRESENTED_SUBJECT_BYTES", preimage))
        self.assertEqual(record_module._ASSOCIATION_DOMAIN, "CSAR_RECORD")

    def test_31_claim_digest_uses_r4_claim_body(self) -> None:
        claim = _claim()
        record = produce_csar(claim, b"a")
        self.assertEqual(record["claim_digest_csar_v0"], digest_r4_claim_body(claim))
        self.assertNotEqual(record["claim_digest_csar_v0"], digest_presented_subject_bytes(b"a"))

    def test_32_subject_digest_uses_presented_subject_bytes(self) -> None:
        record = produce_csar(_claim(), b"a")
        self.assertEqual(record["subject_digest_csar_v0"], digest_presented_subject_bytes(b"a"))
        self.assertNotEqual(record["subject_digest_csar_v0"], domain_separated_digest("CSAR_RECORD", b"a"))

    def test_33_same_bytes_stay_separated_across_dsds_domains(self) -> None:
        preimage = _frozen_line("Canonical preimage text")
        csar_domain = domain_separated_digest("CSAR_RECORD", preimage)
        claim_domain = domain_separated_digest("R4_CLAIM_BODY", preimage)
        subject_domain = domain_separated_digest("PRESENTED_SUBJECT_BYTES", preimage)
        self.assertEqual(csar_domain, _ASSOCIATION_DIGEST)
        self.assertNotEqual(csar_domain, claim_domain)
        self.assertNotEqual(csar_domain, subject_domain)
        self.assertNotEqual(claim_domain, subject_domain)

    def test_34_no_legacy_digest_equivalence(self) -> None:
        source = Path(record_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("canonical_digest", source)
        self.assertNotIn("hashlib", source)
        preimage = _frozen_line("Canonical preimage text")
        self.assertNotEqual(_ASSOCIATION_DIGEST, hashlib.sha256(preimage).hexdigest())

    def test_35_path_text_is_not_a_subject(self) -> None:
        missing = "C:/missing/not-a-subject.bin"
        with self.assertRaises(CsarError) as caught:
            produce_csar(_claim(), missing)
        self.assertEqual(caught.exception.code, "CSAR_REJECTED")
        self.assertNotIsInstance(caught.exception.__cause__, OSError)

    def test_36_result_tags_are_not_bool_and_avoid_forbidden_words(self) -> None:
        claim = _claim()
        record = produce_csar(claim, b"a")
        results = (
            csar_structurally_consistent(record),
            csar_reproduced_from_supplied_inputs(record, claim, b"a"),
        )
        self.assertEqual(results, (_STRUCTURAL, _REPRODUCED))
        for result in results:
            self.assertIs(type(result), str)
            self.assertNotIsInstance(result, bool)
            for word in ("PASS", "VALID", "VERIFIED", "ACCEPTED"):
                self.assertNotIn(word, result)

    def test_37_public_surface_has_no_domain_selector(self) -> None:
        self.assertEqual(csar.__all__, _PUBLIC)
        package_public = {name for name in vars(csar) if not name.startswith("_")}
        self.assertEqual(package_public, set(_PUBLIC) | {"record"})
        module_names = {name for name in vars(record_module) if not name.startswith("__")}
        self.assertEqual(module_names, _RECORD_NAMESPACE)
        defined = {
            name
            for name, value in vars(record_module).items()
            if inspect.isfunction(value) and value.__module__ == record_module.__name__
        }
        self.assertEqual(
            defined,
            {
                "_fail",
                "_canonical_bytes",
                "_reject_duplicate_keys",
                "_closed_digest",
                "_require_limitations",
                "_require_digest_text",
                "csar_structurally_consistent",
                "produce_csar",
                "parse_csar",
                "csar_reproduced_from_supplied_inputs",
            },
        )

    def test_38_authority_zero_with_consistent_digest_is_rejected(self) -> None:
        record = self._with_consistent_association(dict(produce_csar(_claim(), b"a"), authority=0))
        self.assertEqual(record["authority"], 0)
        self._reject_message(lambda: csar_structurally_consistent(record), "authority is not exact False")
        raw = _canonical(record)
        self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
        self._reject_message(lambda: parse_csar(raw), "authority is not exact False")

    def test_39_reordered_limitations_with_consistent_digest_are_rejected(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["limitations"] = list(reversed(record["limitations"]))
        record = self._with_consistent_association(record)
        self.assertEqual(set(record["limitations"]), set(record_module._LIMITATIONS))
        self.assertNotEqual(record["limitations"], list(record_module._LIMITATIONS))
        self._reject_message(
            lambda: csar_structurally_consistent(record),
            "limitations are not the code-owned list",
        )
        raw = _canonical(record)
        self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
        self._reject_message(lambda: parse_csar(raw), "limitations are not the code-owned list")

    def test_40_schema_str_subclass_with_consistent_digest_is_rejected(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["schema_version"] = _Str("csar.v0")
        record = self._with_consistent_association(record)
        self.assertEqual(record["schema_version"], "csar.v0")
        self.assertIsNot(type(record["schema_version"]), str)
        self._reject_message(lambda: csar_structurally_consistent(record), "schema_version mismatch")

    def test_41_digest_str_subclass_with_consistent_digest_is_rejected(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        record["claim_digest_csar_v0"] = _Str(record["claim_digest_csar_v0"])
        record["subject_digest_csar_v0"] = _Str(record["subject_digest_csar_v0"])
        record = self._with_consistent_association(record)
        record["association_digest_csar_v0"] = _Str(record["association_digest_csar_v0"])
        checked = {key: record[key] for key in record_module._PREIMAGE_KEYS}
        self.assertEqual(
            domain_separated_digest("CSAR_RECORD", _canonical(checked)),
            record["association_digest_csar_v0"],
        )
        for name in ("claim_digest_csar_v0", "subject_digest_csar_v0", "association_digest_csar_v0"):
            self.assertIsNot(type(record[name]), str)
        self._reject_message(lambda: csar_structurally_consistent(record), "digest text is malformed")

    def test_42_parse_rejects_canonical_structurally_invalid_records(self) -> None:
        base = produce_csar(_claim(), b"a")
        cases = []
        authority = self._with_consistent_association(dict(base, authority=0))
        cases.append((authority, "authority is not exact False"))
        reordered = dict(base)
        reordered["limitations"] = list(reversed(base["limitations"]))
        cases.append(
            (self._with_consistent_association(reordered), "limitations are not the code-owned list")
        )
        renamed = dict(base)
        renamed["schema_version"] = "csar.v9"
        cases.append((self._with_consistent_association(renamed), "schema_version mismatch"))
        for record, message in cases:
            raw = _canonical(record)
            with self.subTest(message=message):
                self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
                self._reject_message(lambda: parse_csar(raw), message)

    def test_43_reproduction_requires_exact_six_field_equality(self) -> None:
        claim = _claim()
        produced = produce_csar(claim, b"a")
        supplied = dict(produced)
        flipped = "0" if supplied["subject_digest_csar_v0"][-1] != "0" else "1"
        supplied["subject_digest_csar_v0"] = supplied["subject_digest_csar_v0"][:-1] + flipped
        supplied = self._with_consistent_association(supplied)
        self.assertEqual(csar_structurally_consistent(supplied), _STRUCTURAL)
        self.assertEqual(supplied["schema_version"], produced["schema_version"])
        self.assertIs(supplied["authority"], False)
        self.assertEqual(supplied["limitations"], produced["limitations"])
        self.assertEqual(supplied["claim_digest_csar_v0"], produced["claim_digest_csar_v0"])
        self.assertNotEqual(supplied["subject_digest_csar_v0"], produced["subject_digest_csar_v0"])
        self.assertNotEqual(supplied["association_digest_csar_v0"], produced["association_digest_csar_v0"])
        self._reject_message(
            lambda: csar_reproduced_from_supplied_inputs(supplied, claim, b"a"),
            "six-field records are not equal",
        )

    def test_44_reproduction_rejects_records_that_match_only_some_fields(self) -> None:
        claim = _claim()
        produced = produce_csar(claim, b"a")
        authority_zero = dict(produced, authority=0)
        self.assertIs(type(authority_zero["authority"]), int)
        self.assertEqual(authority_zero["authority"], produced["authority"])
        zero_association = dict(produced, association_digest_csar_v0="0" * 64)
        reversed_limitations = dict(
            produced,
            limitations=list(reversed(produced["limitations"])),
        )
        cases = (
            authority_zero,
            zero_association,
            reversed_limitations,
        )
        for mutated in cases:
            with self.subTest(authority=mutated["authority"], association=mutated["association_digest_csar_v0"][:8]):
                self.assertEqual(mutated["claim_digest_csar_v0"], produced["claim_digest_csar_v0"])
                self.assertEqual(mutated["subject_digest_csar_v0"], produced["subject_digest_csar_v0"])
                self.assertIsNot(mutated, produced)
                self._reject(
                    lambda mutated=mutated: csar_reproduced_from_supplied_inputs(mutated, claim, b"a")
                )

    def test_45_limitation_str_subclass_is_rejected_when_digest_matches(self) -> None:
        record = dict(produce_csar(_claim(), b"a"))
        limitations = list(record["limitations"])
        limitations[0] = _AuthorityGranted("authority_granted")
        record["limitations"] = limitations
        record = self._with_consistent_association(record)
        self.assertIsNot(type(record["limitations"][0]), str)
        self.assertEqual(record["limitations"][0], record_module._LIMITATIONS[0])
        self._reject_message(
            lambda: csar_structurally_consistent(record),
            "limitations are not the code-owned list",
        )
        # Canonical JSON keeps the characters authority_granted and json.loads
        # returns a builtin str, so parse_csar cannot observe the subclass.
        raw = _canonical(record)
        self.assertIn(b"authority_granted", raw)
        self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
        self._reject(lambda: parse_csar(raw))
