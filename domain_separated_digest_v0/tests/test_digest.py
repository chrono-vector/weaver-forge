"""Focused tests for Domain-Separated Digest Spec v0."""

from __future__ import annotations

import hashlib
import inspect
import unittest
from unittest.mock import patch

import domain_separated_digest_v0 as dsds
from domain_separated_digest_v0 import digest as digest_module
from domain_separated_digest_v0.digest import (
    DomainSeparatedDigestError,
    digest_presented_subject_bytes,
    digest_r4_claim_body,
    domain_separated_digest,
)

MINIMAL_R4 = "d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf"
MINIMAL_AS_SUBJECT = "277b3d8e2710a7964b482c9dfae69346b8fc0fe334d0fd065958bf0d550dddaf"
SUBJECT_A = "563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1"
SUBJECT_A_AS_CLAIM = "6daf4090ec51ea72d4862ac5284254461cd06e4b153b84c134aaa52841c8ccd8"
SUBJECT_NUL = "2b9add605cbfd93e870fa44423fef7329a40cf4a5424328e838d7e00128fa65d"
SUBJECT_CRLF = "5831eaf9de3b7897d240ceeab8f657dd24e73719c33332876964f90500bae827"
SUBJECT_LF = "02ead9b94b50800a044f50c44d460dedccf70d7eb31ea6ee4813f42bc588e19e"
SUBJECT_BOM = "3a124a309d9702586266f5c90f28b36ef1b37c8adddbfc831c1237ccf6cad0d0"
SUBJECT_NFC = "ed21ceeb3421c3926bd3d8a0417b8915dec1ec8609e44081a9cdada98499efd1"
SUBJECT_NFD = "502d21869c638cdab0db8f2a640707b4c4061882b809adfa5233ef50adac7034"
SUBJECT_DST_PREFIX = "c8102784931c7ea68e23b2174694dab20640726113a35104ef6c6e16c808280e"


def _minimal(**over: object) -> dict:
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


def _expect(test: unittest.TestCase, fn) -> None:
    with test.assertRaises(DomainSeparatedDigestError) as caught:
        fn()
    test.assertEqual(caught.exception.code, "DSDS_CLAIM_INVALID")


class DomainSeparatedDigestTests(unittest.TestCase):
    def test_01_same_preimage_and_domain_match(self) -> None:
        first = digest_presented_subject_bytes(b"a")
        second = domain_separated_digest("PRESENTED_SUBJECT_BYTES", b"a")
        self.assertEqual(first, second)
        self.assertEqual(first, SUBJECT_A)

    def test_02_same_preimage_different_domain(self) -> None:
        subject = digest_presented_subject_bytes(b"a")
        claim_domain = domain_separated_digest("R4_CLAIM_BODY", b"a")
        self.assertNotEqual(subject, claim_domain)
        self.assertEqual(subject, SUBJECT_A)
        self.assertEqual(claim_domain, SUBJECT_A_AS_CLAIM)

    def test_03_empty_subject_rejected_before_hash(self) -> None:
        def boom(data: bytes) -> str:
            raise AssertionError(data)

        with patch("domain_separated_digest_v0.digest.hashlib.sha256", boom):
            with self.assertRaises(DomainSeparatedDigestError) as caught:
                digest_presented_subject_bytes(b"")
        self.assertEqual(caught.exception.code, "DSDS_PREIMAGE_INVALID")

    def test_04_nul_subject_accepted(self) -> None:
        self.assertEqual(digest_presented_subject_bytes(b"a\x00b"), SUBJECT_NUL)

    def test_05_dst_prefix_does_not_change_domain(self) -> None:
        prefix = b"weaver.digest.v0:PRESENTED_SUBJECT_BYTES\x00"
        prefixed = domain_separated_digest("PRESENTED_SUBJECT_BYTES", prefix + b"a")
        self.assertEqual(prefixed, SUBJECT_DST_PREFIX)
        self.assertNotEqual(prefixed, digest_presented_subject_bytes(b"a"))
        self.assertNotEqual(
            prefixed,
            domain_separated_digest("R4_CLAIM_BODY", prefix + b"a"),
        )

    def test_06_crlf_differs_from_lf(self) -> None:
        crlf = digest_presented_subject_bytes(b"a\r\nb")
        lf = digest_presented_subject_bytes(b"a\nb")
        self.assertEqual(crlf, SUBJECT_CRLF)
        self.assertEqual(lf, SUBJECT_LF)
        self.assertNotEqual(crlf, lf)

    def test_07_bom_differs_from_no_bom(self) -> None:
        bom = digest_presented_subject_bytes(b"\xef\xbb\xbfa")
        plain = digest_presented_subject_bytes(b"a")
        self.assertEqual(bom, SUBJECT_BOM)
        self.assertEqual(plain, SUBJECT_A)
        self.assertNotEqual(bom, plain)

    def test_08_nfc_and_nfd_bytes_differ(self) -> None:
        nfc = digest_presented_subject_bytes("é".encode("utf-8"))
        nfd = digest_presented_subject_bytes("e\u0301".encode("utf-8"))
        self.assertEqual(nfc, SUBJECT_NFC)
        self.assertEqual(nfd, SUBJECT_NFD)
        self.assertNotEqual(nfc, nfd)

    def test_09_unknown_domain_rejected(self) -> None:
        with self.assertRaises(DomainSeparatedDigestError) as caught:
            domain_separated_digest("OTHER_DOMAIN", b"a")
        self.assertEqual(caught.exception.code, "DSDS_DOMAIN_INVALID")

    def test_10_case_mutated_domain_rejected(self) -> None:
        with self.assertRaises(DomainSeparatedDigestError) as caught:
            domain_separated_digest("r4_claim_body", b"a")
        self.assertEqual(caught.exception.code, "DSDS_DOMAIN_INVALID")

    def test_11_unknown_top_level_key_rejected(self) -> None:
        _expect(self, lambda: digest_r4_claim_body(_minimal(comment="x")))

    def test_12_non_string_mapping_key_rejected(self) -> None:
        _expect(self, lambda: digest_r4_claim_body(_minimal(extra={1: "x"})))

    def test_13_all_floats_rejected(self) -> None:
        for value in (1.0, float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                _expect(self, lambda value=value: digest_r4_claim_body(_minimal(extra={"n": value})))

    def test_14_confidence_key_rejected(self) -> None:
        for value in (True, 1, None):
            with self.subTest(value=value):
                with self.assertRaises(DomainSeparatedDigestError) as caught:
                    digest_r4_claim_body(_minimal(confidence=value))
                self.assertEqual(caught.exception.code, "DSDS_CLAIM_INVALID")
                self.assertIn("confidence", str(caught.exception))

    def test_15_strip_changing_claim_id_rejected(self) -> None:
        _expect(self, lambda: digest_r4_claim_body(_minimal(claim_id=" c1")))

    def test_16_strip_changing_statement_rejected(self) -> None:
        _expect(self, lambda: digest_r4_claim_body(_minimal(statement=" s")))

    def test_17_strip_changing_scope_rejected(self) -> None:
        _expect(self, lambda: digest_r4_claim_body(_minimal(scope=" scope-text")))

    def test_18_strip_changing_refs_rejected(self) -> None:
        _expect(self, lambda: digest_r4_claim_body(_minimal(evidence_refs=[" p"])))
        _expect(self, lambda: digest_r4_claim_body(_minimal(provenance_refs=[" p"])))

    def test_19_statement_change_changes_digest(self) -> None:
        same_id = digest_r4_claim_body(_minimal())
        changed = digest_r4_claim_body(_minimal(statement="other"))
        self.assertEqual(same_id, MINIMAL_R4)
        self.assertNotEqual(same_id, changed)

    def test_20_status_change_is_not_evidence_strength(self) -> None:
        reported = digest_r4_claim_body(_minimal(provenance_refs=["p1"]))
        verified = digest_r4_claim_body(
            _minimal(epistemic_status="VERIFIED_SCOPE", provenance_refs=["p1"])
        )
        self.assertNotEqual(reported, verified)
        self.assertEqual(len(verified), 64)
        self.assertNotIn("evidence_strength", dsds.__all__)
        self.assertNotIn("support", dsds.__all__)

    def test_21_intentional_r4_equivalences(self) -> None:
        base = digest_r4_claim_body(_minimal())
        self.assertEqual(base, digest_r4_claim_body(_minimal(notes="")))
        self.assertEqual(base, digest_r4_claim_body(_minimal(notes=None)))
        self.assertEqual(base, digest_r4_claim_body(_minimal(evidence_refs=[])))
        self.assertEqual(base, digest_r4_claim_body(_minimal(provenance_refs=[])))
        ordered = digest_r4_claim_body(_minimal(evidence_refs=["b", "a", "a"]))
        sorted_unique = digest_r4_claim_body(_minimal(evidence_refs=["a", "b"]))
        self.assertEqual(ordered, sorted_unique)
        self.assertEqual(base, digest_r4_claim_body(_minimal(extra=None)))
        self.assertEqual(base, digest_r4_claim_body(_minimal(extra={})))
        self.assertEqual(base, digest_r4_claim_body(_minimal(workflow_state=None)))
        blank_state = digest_r4_claim_body(_minimal(workflow_state=""))
        self.assertNotEqual(base, blank_state)
        nested = digest_r4_claim_body(_minimal(extra={"evidence_refs": ["b", "a"]}))
        nested_sorted = digest_r4_claim_body(_minimal(extra={"evidence_refs": ["a", "b"]}))
        self.assertEqual(nested, nested_sorted)
        preserved = digest_r4_claim_body(_minimal(notes=" s "))
        self.assertNotEqual(base, preserved)

    def test_22_unicode_is_not_normalized(self) -> None:
        nfc = digest_r4_claim_body(_minimal(statement="é"))
        nfd = digest_r4_claim_body(_minimal(statement="e\u0301"))
        self.assertNotEqual(nfc, nfd)

    def test_23_producer_rejects_caller_digest(self) -> None:
        for fn in (
            domain_separated_digest,
            digest_presented_subject_bytes,
            digest_r4_claim_body,
        ):
            params = inspect.signature(fn).parameters
            self.assertNotIn("expected_digest", params)
            self.assertFalse(any("digest" in name for name in params))
        with self.assertRaises(TypeError):
            domain_separated_digest(  # type: ignore[call-arg]
                "PRESENTED_SUBJECT_BYTES",
                b"a",
                expected_digest=SUBJECT_A,
            )

    def test_24_no_legacy_comparison_helper(self) -> None:
        names = [
            name
            for name in dsds.__all__
            if "compar" in name.lower() or "legacy" in name.lower()
        ]
        self.assertEqual(names, [])
        self.assertIn("not semantic equality", digest_module.__doc__)

    def test_25_digest_computation_does_not_open_files(self) -> None:
        def guard(*args: object, **kwargs: object) -> None:
            raise AssertionError((args, kwargs))

        with patch("builtins.open", guard):
            self.assertEqual(digest_presented_subject_bytes(b"a"), SUBJECT_A)
            self.assertEqual(digest_r4_claim_body(_minimal()), MINIMAL_R4)

    def test_minimal_claim_bytes_under_subject_domain(self) -> None:
        preimage = digest_module.r4_claim_body_preimage(_minimal())
        self.assertEqual(
            domain_separated_digest("PRESENTED_SUBJECT_BYTES", preimage),
            MINIMAL_AS_SUBJECT,
        )

    def test_csar_domain_has_no_schema_helper(self) -> None:
        self.assertIn("CSAR_RECORD", digest_module.DOMAINS)
        self.assertNotIn("digest_csar", dsds.__all__)
        tagged = domain_separated_digest("CSAR_RECORD", b"{}")
        self.assertEqual(len(tagged), 64)
        self.assertNotEqual(tagged, hashlib.sha256(b"{}").hexdigest())


if __name__ == "__main__":
    unittest.main()
