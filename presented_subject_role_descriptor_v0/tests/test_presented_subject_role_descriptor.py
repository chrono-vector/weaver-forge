"""Focused tests for Presented-Subject Role Descriptor v0."""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path

import unittest

import presented_subject_role_descriptor_v0 as psrd
from association_carriage_digest_v0 import digest_association_carriage_preimage
from domain_separated_digest_v0 import (
    DomainSeparatedDigestError,
    digest_presented_subject_bytes,
    domain_separated_digest,
)
from presented_subject_role_descriptor_v0 import (
    PsrdError,
    parse_psrd,
    produce_psrd,
    psrd_reproduced_from_supplied_inputs,
    psrd_structurally_consistent,
)
from presented_subject_role_descriptor_v0 import record as record_module

_DESIGN = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "PRESENTED_SUBJECT_ROLE_DESCRIPTOR_V0_DESIGN_AND_ATTACK_SPEC_20261004.md"
)
_FREEZE = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "next"
    / "PSRD_V0_HUMAN_DESIGN_FREEZE_20261004.md"
)
_TAG = b"weaver.psrd.digest.v0\x00"
_STRUCTURAL = "PSRD_STRUCTURALLY_CONSISTENT"
_REPRODUCED = "PSRD_REPRODUCED_FROM_SUPPLIED_INPUTS"
_PUBLIC = [
    "PsrdError",
    "produce_psrd",
    "parse_psrd",
    "psrd_structurally_consistent",
    "psrd_reproduced_from_supplied_inputs",
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
    "_ROLE",
    "_LIMITATIONS",
    "_KEYS",
    "_PREIMAGE_KEYS",
    "_DIGEST",
    "PsrdError",
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_subject_digest",
    "_descriptor_digest",
    "_require_limitations",
    "_require_digest_text",
    "_exact_six_fields",
    "psrd_structurally_consistent",
    "produce_psrd",
    "parse_psrd",
    "psrd_reproduced_from_supplied_inputs",
}
_DEFINED = {
    "_fail",
    "_canonical_bytes",
    "_reject_duplicate_keys",
    "_subject_digest",
    "_descriptor_digest",
    "_require_limitations",
    "_require_digest_text",
    "_exact_six_fields",
    "psrd_structurally_consistent",
    "produce_psrd",
    "parse_psrd",
    "psrd_reproduced_from_supplied_inputs",
}
_FORBIDDEN_PARAMS = {
    "domain",
    "prefix",
    "tag",
    "digest",
    "role",
    "limitations",
    "authority",
    "path",
    "filename",
}
_FORBIDDEN_RESULTS = (
    "SUPPORTED",
    "SUFFICIENT",
    "TRUE",
    "VERIFIED",
    "ADMITTED",
    "AUTHORITATIVE",
    "COMPLETE",
    "INDEPENDENT",
    "FRESH",
    "BEST_EVIDENCE",
    "WINNER",
    "HUMAN_ACCEPTED",
    "PASS",
    "VALID",
    "ACCEPTED",
)
_FORBIDDEN_PUBLIC = {
    "TAG",
    "PREFIX",
    "DST",
    "DOMAINS",
    "REGISTRY",
    "NAMESPACE",
    "canonical_digest",
    "digest",
    "domain_separated_digest",
    "hash",
}
_PREIMAGE_KEYS = (
    "schema_version",
    "authority",
    "presented_subject_role",
    "subject_digest_psrd_v0",
    "limitations",
)
_ROLES = ("ARTIFACT", "CONFIG", "EMPIRICAL", "RECEIPT", "SUPPORTS", "COMPATIBLE")
_AUTHORITY = "authority is not exact False"
_ROLE_RULE = "presented_subject_role is not the code-owned role"
_LIMITATION_RULE = "limitations are not the code-owned list"
_SCHEMA_RULE = "schema_version is not the exact schema"
_MALFORMED = "digest text is malformed"
_DIGEST_RULE = "descriptor digest does not reproduce"
_KEYS_RULE = "record keys are not the six-field schema"
_CANONICAL = "serialized bytes are not canonical"
_SUBJECT_TYPE = "subject must be exact bytes"
_DUPLICATE = "duplicate JSON key"
_INEQUAL = "six-field records are not equal"


def _design_vectors() -> tuple[str, str, list[str]]:
    text = _DESIGN.read_text(encoding="utf-8")
    quoted = [
        line[1:-1]
        for line in text.splitlines()
        if line.startswith("`{") and line.endswith("`")
    ]
    hexes = re.findall(r"`([0-9a-f]{64})`", text)
    if len(quoted) != 2 or len(hexes) != 8:
        raise RuntimeError("frozen PSRD vectors were not found")
    return quoted[0], quoted[1], hexes


_PREIMAGE_TEXT, _RECORD_TEXT, _HEXES = _design_vectors()
_SUBJECT_DIGEST = _HEXES[0]
_DESCRIPTOR = _HEXES[1]
_FINGERPRINT = _HEXES[2]
_UNTAGGED = _HEXES[3]
_CSAR_RECORD = _HEXES[4]
_PRESENTED_SUBJECT = _HEXES[5]
_R4_CLAIM_BODY = _HEXES[6]
_ACD = _HEXES[7]
_GOLDEN = json.loads(_RECORD_TEXT)
_SCHEMA = _GOLDEN["schema_version"]
_ROLE = _GOLDEN["presented_subject_role"]
_LIMITATIONS = list(_GOLDEN["limitations"])


class _Text(str):
    """Exact text with a distinct type."""


class _AlwaysEqual(str):
    """Equality that hides a different limitation string."""

    def __eq__(self, other: object) -> bool:
        return True

    def __ne__(self, other: object) -> bool:
        return False


class _Bytes(bytes):
    """Bytes subclass that must not alias the subject."""


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
        "presented_subject_role": _ROLE,
        "subject_digest_psrd_v0": _SUBJECT_DIGEST,
        "limitations": list(_LIMITATIONS),
    }
    if overrides:
        fields.update(overrides)
    preimage = {key: fields[key] for key in _PREIMAGE_KEYS}
    record = dict(preimage)
    record["descriptor_digest_psrd_v0"] = _tag_digest(_canonical(preimage))
    return record


def _preimage_of(record: dict) -> dict:
    return {key: record[key] for key in _PREIMAGE_KEYS}


class PresentedSubjectRoleDescriptorTests(unittest.TestCase):
    def test_golden_vector_matches_the_frozen_design(self) -> None:
        freeze = _FREEZE.read_text(encoding="utf-8")
        self.assertIn("HUMAN_DESIGN_FREEZE:\nACCEPTED", freeze)
        self.assertIn("d11a2ec703ed700e7f7704c7c2a1d8e3d0c578aa", freeze)
        self.assertIn("Planned mutant count:\n38", freeze)
        names = {name[:8] for name in dir(type(self)) if name.startswith("test_m")}
        self.assertEqual(names, {f"test_m{index:02d}" for index in range(1, 39)})
        preimage = _PREIMAGE_TEXT.encode("utf-8")
        record_bytes = _RECORD_TEXT.encode("utf-8")
        self.assertNotIn(b"\r", preimage)
        self.assertNotIn(b"\r", record_bytes)
        self.assertFalse(preimage.endswith(b"\n"))
        self.assertFalse(record_bytes.endswith(b"\n"))
        self.assertEqual(len(preimage), 917)
        self.assertEqual(len(record_bytes), 1012)
        self.assertNotIn("descriptor_digest_psrd_v0", _PREIMAGE_TEXT)
        self.assertEqual(digest_presented_subject_bytes(b"a"), _SUBJECT_DIGEST)
        self.assertEqual(_tag_digest(preimage), _DESCRIPTOR)
        self.assertEqual(hashlib.sha256(record_bytes).hexdigest(), _FINGERPRINT)
        self.assertNotEqual(_FINGERPRINT, _DESCRIPTOR)
        substitutes = {
            "untagged": hashlib.sha256(preimage).hexdigest(),
            "CSAR_RECORD": domain_separated_digest("CSAR_RECORD", preimage),
            "PRESENTED_SUBJECT_BYTES": domain_separated_digest("PRESENTED_SUBJECT_BYTES", preimage),
            "R4_CLAIM_BODY": domain_separated_digest("R4_CLAIM_BODY", preimage),
            "ACD": digest_association_carriage_preimage(preimage),
        }
        self.assertEqual(
            substitutes,
            {
                "untagged": _UNTAGGED,
                "CSAR_RECORD": _CSAR_RECORD,
                "PRESENTED_SUBJECT_BYTES": _PRESENTED_SUBJECT,
                "R4_CLAIM_BODY": _R4_CLAIM_BODY,
                "ACD": _ACD,
            },
        )
        self.assertNotIn(_DESCRIPTOR, substitutes.values())
        self.assertEqual(record_module._TAG, _TAG)
        produced = produce_psrd(b"a")
        self.assertEqual(_canonical(produced), record_bytes)
        self.assertEqual(produced["subject_digest_psrd_v0"], _SUBJECT_DIGEST)
        self.assertEqual(produced["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self.assertIs(produced["authority"], False)
        self.assertEqual(produced["presented_subject_role"], _ROLE)
        self.assertEqual(len(produced["limitations"]), 30)
        self.assertEqual(parse_psrd(record_bytes), produced)
        self.assertEqual(psrd_structurally_consistent(produced), _STRUCTURAL)
        self.assertEqual(psrd_reproduced_from_supplied_inputs(produced, b"a"), _REPRODUCED)

    def test_m01_authority_zero_recomputed_digest_rejects_exact_false(self) -> None:
        record = _consistent({"authority": 0})
        self.assertIs(type(record["authority"]), int)
        self.assertEqual(record["authority"], False)
        self.assertNotEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _AUTHORITY)
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _AUTHORITY)

    def test_m02_authority_true_recomputed_digest_rejects(self) -> None:
        record = _consistent({"authority": True})
        self.assertNotEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _AUTHORITY)

    def test_m03_role_subclass_keeps_golden_digest_and_rejects_type(self) -> None:
        role = _Text(_ROLE)
        record = _consistent({"presented_subject_role": role})
        self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self.assertIsNot(type(record["presented_subject_role"]), str)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _ROLE_RULE)

    def test_m04_lying_limitation_subclass_rejects_and_parse_rejects_builtin(self) -> None:
        limitations = list(_LIMITATIONS)
        limitations[0] = _AlwaysEqual("authority_granted")
        record = _consistent({"limitations": limitations})
        self.assertEqual(record["limitations"][0], _LIMITATIONS[0])
        self.assertIsNot(type(record["limitations"][0]), str)
        self.assertNotEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _LIMITATION_RULE)
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _LIMITATION_RULE)
        raw = _canonical(record)
        loaded = json.loads(raw.decode("utf-8"))
        self.assertIs(type(loaded["limitations"][0]), str)
        self.assertEqual(loaded["limitations"][0], "authority_granted")
        self._reject_rule(lambda: parse_psrd(raw), _LIMITATION_RULE)

    def test_m05_schema_subclass_keeps_golden_digest_and_rejects_type(self) -> None:
        record = _consistent({"schema_version": _Text(_SCHEMA)})
        self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self.assertIsNot(type(record["schema_version"]), str)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _SCHEMA_RULE)

    def test_m06_descriptor_subclass_rejects_without_lowercase_acceptance(self) -> None:
        produced = produce_psrd(b"a")
        subclass = _Text(produced["descriptor_digest_psrd_v0"])
        record = dict(produced)
        record["descriptor_digest_psrd_v0"] = subclass
        self.assertEqual(subclass, produced["descriptor_digest_psrd_v0"])
        self.assertEqual(subclass.lower(), produced["descriptor_digest_psrd_v0"])
        self.assertIs(type(subclass.lower()), str)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _MALFORMED)

    def test_m07_extra_note_or_evidence_id_keeps_five_field_digest(self) -> None:
        produced = produce_psrd(b"a")
        for key, value in (("note", "aside"), ("evidence_id", "second")):
            record = dict(produced)
            record[key] = value
            self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
            self.assertEqual(_tag_digest(_canonical(_preimage_of(record))), _DESCRIPTOR)
            self._reject_rule(lambda record=record: psrd_structurally_consistent(record), _KEYS_RULE)

    def test_m08_missing_limitations_rejects_key_set(self) -> None:
        record = dict(produce_psrd(b"a"))
        del record["limitations"]
        self._reject_rule(lambda: psrd_structurally_consistent(record), _KEYS_RULE)

    def test_m09_reversed_limitations_recomputed_digest_rejects_order(self) -> None:
        record = _consistent({"limitations": list(reversed(_LIMITATIONS))})
        self.assertNotEqual(record["limitations"], _LIMITATIONS)
        self.assertNotEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _LIMITATION_RULE)
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _LIMITATION_RULE)

    def test_m10_duplicate_schema_key_rejects_parse(self) -> None:
        raw = _RECORD_TEXT.replace(
            "{",
            '{"schema_version":"presented_subject_role_descriptor.v0",',
            1,
        ).encode("utf-8")
        self._reject_rule(lambda: parse_psrd(raw), _DUPLICATE)

    def test_m11_noncanonical_bytes_reject_even_when_values_match(self) -> None:
        raw = _RECORD_TEXT.encode("utf-8")
        attacks = {
            "whitespace": raw.replace(b"{", b"{ ", 1),
            "newline": raw + b"\n",
            "escape": raw.replace(b'"uninterpreted', b'"\\u0075ninterpreted', 1),
        }
        for name, attack in attacks.items():
            with self.subTest(attack=name):
                parsed = json.loads(attack.decode("utf-8"))
                self.assertEqual(psrd_structurally_consistent(parsed), _STRUCTURAL)
                self._reject_rule(lambda attack=attack: parse_psrd(attack), _CANONICAL)
        for name, attack in {
            "bom": b"\xef\xbb\xbf" + raw,
            "utf16": _RECORD_TEXT.encode("utf-16"),
        }.items():
            with self.subTest(attack=name):
                self._reject_code(lambda attack=attack: parse_psrd(attack))

    def test_m12_insertion_order_same_length_rejects_parse(self) -> None:
        values = json.loads(_RECORD_TEXT)
        ordered = {key: values[key] for key in reversed(tuple(values))}
        raw = json.dumps(
            ordered,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        self.assertEqual(len(raw), 1012)
        self.assertNotEqual(raw, _RECORD_TEXT.encode("utf-8"))
        self.assertEqual(psrd_structurally_consistent(json.loads(raw.decode("utf-8"))), _STRUCTURAL)
        self._reject_rule(lambda: parse_psrd(raw), _CANONICAL)

    def test_m13_untagged_sha256_is_not_the_descriptor_digest(self) -> None:
        self._reject_substitute(_UNTAGGED)

    def test_m14_csar_record_domain_is_not_the_descriptor_digest(self) -> None:
        self._reject_substitute(_CSAR_RECORD)

    def test_m15_presented_subject_domain_is_not_the_descriptor_digest(self) -> None:
        self._reject_substitute(_PRESENTED_SUBJECT)

    def test_m16_claim_body_domain_is_not_the_descriptor_digest(self) -> None:
        self._reject_substitute(_R4_CLAIM_BODY)

    def test_m17_acd_digest_is_not_the_descriptor_digest(self) -> None:
        self._reject_substitute(_ACD)

    def test_m18_subject_digest_is_not_the_descriptor_digest(self) -> None:
        self._reject_substitute(_SUBJECT_DIGEST)

    def test_m19_record_fingerprint_is_not_legacy_canonical_digest(self) -> None:
        raw = _RECORD_TEXT.encode("utf-8")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), _FINGERPRINT)
        self.assertNotEqual(_FINGERPRINT, _DESCRIPTOR)
        source = Path(record_module.__file__).read_text(encoding="utf-8")
        self.assertNotIn("canonical_digest", source)
        self.assertNotIn("hashlib", inspect.getsource(produce_psrd))
        helper = inspect.getsource(record_module._descriptor_digest)
        self.assertIn("hashlib.sha256", helper)
        self.assertNotIn("canonical_digest", helper)

    def test_m20_evidence_set_refs_or_omission_argument_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            produce_psrd(b"a", [b"a"])
        with self.assertRaises(TypeError):
            produce_psrd(b"a", evidence_refs=["ref-1"])
        with self.assertRaises(TypeError):
            produce_psrd(b"a", omission=True)

    def test_m21_lists_and_tuples_of_subject_bytes_reject(self) -> None:
        for subject in ([b"a"], [b"a", b"b"], (b"a",), (b"a", b"b")):
            with self.subTest(subject=type(subject).__name__, count=len(subject)):
                self._reject_rule(lambda subject=subject: produce_psrd(subject), _SUBJECT_TYPE)

    def test_m22_evidence_id_does_not_add_a_second_identifier(self) -> None:
        record = dict(produce_psrd(b"a"))
        record["evidence_id"] = "same-bytes-other-id"
        self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self.assertEqual(_tag_digest(_canonical(_preimage_of(record))), _DESCRIPTOR)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _KEYS_RULE)

    def test_m23_claim_dict_keyword_and_extra_claim_kind_reject(self) -> None:
        claim = {"claim_kind": "EMPIRICAL", "statement": "s"}
        self._reject_rule(lambda: produce_psrd(claim), _SUBJECT_TYPE)
        with self.assertRaises(TypeError):
            produce_psrd(b"a", claim_kind="EMPIRICAL")
        record = dict(produce_psrd(b"a"))
        record["claim_kind"] = "EMPIRICAL"
        self.assertEqual(_tag_digest(_canonical(_preimage_of(record))), _DESCRIPTOR)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _KEYS_RULE)

    def test_m24_closed_vocabulary_roles_reject_with_recomputed_digests(self) -> None:
        for role in _ROLES:
            with self.subTest(role=role):
                record = _consistent({"presented_subject_role": role})
                self.assertNotEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
                self._assert_consistent_digest(record)
                self._reject_rule(lambda record=record: psrd_structurally_consistent(record), _ROLE_RULE)

    def test_m25_success_tags_are_exact_strings_and_not_conclusion_words(self) -> None:
        record = produce_psrd(b"a")
        results = (
            psrd_structurally_consistent(record),
            psrd_reproduced_from_supplied_inputs(record, b"a"),
        )
        self.assertEqual(results, (_STRUCTURAL, _REPRODUCED))
        for result in results:
            self.assertIs(type(result), str)
            self.assertNotIsInstance(result, bool)
            self.assertNotIn(result, _FORBIDDEN_RESULTS)
            for word in _FORBIDDEN_RESULTS:
                self.assertNotIn(word, result)

    def test_m26_contradiction_present_keeps_five_field_digest_and_rejects(self) -> None:
        record = dict(produce_psrd(b"a"))
        record["contradiction_present"] = True
        self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self.assertEqual(_tag_digest(_canonical(_preimage_of(record))), _DESCRIPTOR)
        self._reject_rule(lambda: psrd_structurally_consistent(record), _KEYS_RULE)

    def test_m27_empty_subject_rejects_without_a_record(self) -> None:
        with self.assertRaises(PsrdError) as caught:
            produce_psrd(b"")
        self.assertEqual(caught.exception.code, "PSRD_REJECTED")
        self.assertIsInstance(caught.exception.__cause__, DomainSeparatedDigestError)

    def test_m28_stale_authority_zero_is_not_python_equality(self) -> None:
        record = dict(produce_psrd(b"a"))
        record["authority"] = 0
        self.assertEqual(record["authority"], False)
        self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _AUTHORITY)

    def test_m29_zero_descriptor_digest_is_not_subject_digest_comparison(self) -> None:
        record = dict(produce_psrd(b"a"))
        record["descriptor_digest_psrd_v0"] = "0" * 64
        self.assertEqual(record["subject_digest_psrd_v0"], _SUBJECT_DIGEST)
        self._reject_message(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _DIGEST_RULE)

    def test_m30_stale_reversed_limitations_reject_for_the_limitation_rule(self) -> None:
        record = dict(produce_psrd(b"a"))
        record["limitations"] = list(reversed(record["limitations"]))
        self.assertEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _LIMITATION_RULE)

    def test_m31_recomputed_artifact_role_is_not_subject_digest_reproduction(self) -> None:
        record = _consistent({"presented_subject_role": "ARTIFACT"})
        self.assertEqual(record["subject_digest_psrd_v0"], _SUBJECT_DIGEST)
        self.assertNotEqual(record["descriptor_digest_psrd_v0"], _DESCRIPTOR)
        self._assert_consistent_digest(record)
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(record, b"a"), _ROLE_RULE)

    def test_m32_canonical_bytes_of_field_attacks_still_fail_parse(self) -> None:
        attacks = [
            (_consistent({"authority": 0}), _AUTHORITY),
            (_consistent({"limitations": list(reversed(_LIMITATIONS))}), _LIMITATION_RULE),
        ]
        attacks.extend(
            (_consistent({"presented_subject_role": role}), _ROLE_RULE) for role in _ROLES
        )
        for record, message in attacks:
            raw = _canonical(record)
            self.assertEqual(raw, _canonical(json.loads(raw.decode("utf-8"))))
            self._reject_rule(lambda raw=raw: parse_psrd(raw), message)

    def test_m33_public_signatures_reject_selector_keywords(self) -> None:
        functions = (
            produce_psrd,
            parse_psrd,
            psrd_structurally_consistent,
            psrd_reproduced_from_supplied_inputs,
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
        self.assertEqual(list(inspect.signature(produce_psrd).parameters), ["subject"])
        self.assertEqual(list(inspect.signature(psrd_structurally_consistent).parameters), ["record"])
        self.assertEqual(
            list(inspect.signature(psrd_reproduced_from_supplied_inputs).parameters),
            ["record", "subject"],
        )
        self.assertEqual(list(inspect.signature(parse_psrd).parameters), ["raw"])
        produced = produce_psrd(b"a")
        for keyword in _FORBIDDEN_PARAMS:
            with self.subTest(keyword=keyword):
                with self.assertRaises(TypeError):
                    produce_psrd(b"a", **{keyword: "selector"})
                with self.assertRaises(TypeError):
                    psrd_structurally_consistent(produced, **{keyword: "selector"})
                with self.assertRaises(TypeError):
                    psrd_reproduced_from_supplied_inputs(produced, b"a", **{keyword: "selector"})

    def test_m34_exports_have_no_public_selector_or_error_hash(self) -> None:
        self.assertEqual(psrd.__all__, _PUBLIC)
        package_public = {name for name in vars(psrd) if not name.startswith("_")}
        self.assertEqual(package_public, set(_PUBLIC) | {"record"})
        self.assertFalse(set(psrd.__all__) & _FORBIDDEN_PUBLIC)
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
        self.assertNotIn("hash", PsrdError.__dict__)
        self.assertEqual({name for name in vars(PsrdError) if not name.startswith("__")}, set())
        self.assertEqual(list(inspect.signature(record_module._descriptor_digest).parameters), ["preimage"])

    def test_m35_uppercase_short_long_and_nonhex_digests_are_malformed(self) -> None:
        produced = produce_psrd(b"a")
        attacks = (
            produced["descriptor_digest_psrd_v0"].upper(),
            "ab",
            "0" * 63,
            "0" * 65,
            "g" * 64,
        )
        for digest in attacks:
            with self.subTest(digest=digest):
                record = dict(produced)
                record["descriptor_digest_psrd_v0"] = digest
                self._reject_rule(lambda record=record: psrd_structurally_consistent(record), _MALFORMED)

    def test_m36_byte_like_aliases_and_paths_reject_without_oserror(self) -> None:
        subjects = (
            bytearray(b"a"),
            memoryview(b"a"),
            _Bytes(b"a"),
            "C:/missing/subject.bin",
        )
        for subject in subjects:
            with self.subTest(subject=type(subject).__name__):
                with self.assertRaises(PsrdError) as caught:
                    produce_psrd(subject)
                self.assertEqual(caught.exception.code, "PSRD_REJECTED")
                self.assertIn(_SUBJECT_TYPE, str(caught.exception))
                self.assertNotIsInstance(caught.exception, OSError)
                self.assertNotIsInstance(caught.exception.__cause__, OSError)

    def test_m37_structural_consistency_is_not_reproduction(self) -> None:
        golden = produce_psrd(b"a")
        other = produce_psrd(b"b")
        self.assertEqual(psrd_structurally_consistent(golden), _STRUCTURAL)
        self.assertEqual(psrd_structurally_consistent(other), _STRUCTURAL)
        self.assertNotEqual(other["subject_digest_psrd_v0"], golden["subject_digest_psrd_v0"])
        self.assertNotEqual(other["descriptor_digest_psrd_v0"], golden["descriptor_digest_psrd_v0"])
        self._reject_rule(lambda: psrd_reproduced_from_supplied_inputs(other, b"a"), _INEQUAL)

    def test_m38_consistent_digests_report_the_field_rule(self) -> None:
        attacks = [
            (_consistent({"authority": 0}), _AUTHORITY, True),
            (
                _consistent({"limitations": [_AlwaysEqual("authority_granted"), *_LIMITATIONS[1:]]}),
                _LIMITATION_RULE,
                True,
            ),
            (_consistent({"limitations": list(reversed(_LIMITATIONS))}), _LIMITATION_RULE, True),
        ]
        attacks.extend((_consistent({"presented_subject_role": role}), _ROLE_RULE, False) for role in _ROLES)
        for record, message, reproduce in attacks:
            self._assert_consistent_digest(record)
            self._reject_rule(lambda record=record: psrd_structurally_consistent(record), message)
            if reproduce:
                self._reject_rule(
                    lambda record=record: psrd_reproduced_from_supplied_inputs(record, b"a"),
                    message,
                )

    def _assert_consistent_digest(self, record: dict) -> None:
        self.assertEqual(
            record["descriptor_digest_psrd_v0"],
            _tag_digest(_canonical(_preimage_of(record))),
        )

    def _reject_code(self, fn) -> PsrdError:
        with self.assertRaises(PsrdError) as caught:
            fn()
        self.assertEqual(caught.exception.code, "PSRD_REJECTED")
        return caught.exception

    def _reject_message(self, fn, message: str) -> PsrdError:
        caught = self._reject_code(fn)
        self.assertIn(message, str(caught))
        return caught

    def _reject_rule(self, fn, message: str) -> PsrdError:
        caught = self._reject_message(fn, message)
        self.assertNotIn(_DIGEST_RULE, str(caught))
        return caught

    def _reject_substitute(self, digest: str) -> None:
        self.assertEqual(len(digest), 64)
        self.assertNotEqual(digest, _DESCRIPTOR)
        record = dict(produce_psrd(b"a"))
        record["descriptor_digest_psrd_v0"] = digest
        self._reject_message(lambda: psrd_structurally_consistent(record), _DIGEST_RULE)
