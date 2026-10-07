from __future__ import annotations

import json
import socket
import unittest
import urllib.request
from unittest import mock

from tools.ecp import checkpoint as ecp


def digest(value: str) -> dict[str, str]:
    return {"algorithm": "sha256", "value": value}


HEAD = "a" * 64
OTHER = "b" * 64


def checkpoint(**updates):
    value = {
        "schema_version": "ecp.checkpoint.v0",
        "subject_log_id": "audit-main",
        "checkpoint_sequence": 120,
        "committed_head_digest": digest(HEAD),
        "holder_id": "holder-A",
        "holder_basis": "operator-supplied descriptive label",
        "verification_method": "retained_checkpoint_bytes.v0",
        "provider_receipt_digest": None,
        "limitations": [],
        "nonclaims": [],
    }
    value.update(updates)
    return value


def verify(value=None, retained=None, **updates):
    record = value or checkpoint()
    if retained is None:
        retained = ecp.canonical_checkpoint_bytes(record)
    arguments = {
        "subject_log_id": "audit-main",
        "current_sequence": 120,
        "current_head_digest": digest(HEAD),
    }
    arguments.update(updates)
    return ecp.verify_checkpoint(record, retained, **arguments)


class ECPCheckpointTests(unittest.TestCase):
    def test_current_matching_checkpoint(self):
        self.assertEqual(ecp.CHECKPOINT_MATCH_CURRENT, verify())

    def test_local_ahead_with_preserved_lineage_is_stale_match(self):
        self.assertEqual(
            ecp.CHECKPOINT_MATCH_STALE,
            verify(current_sequence=150, current_head_digest=digest(OTHER), head_digest_at_sequence=lambda sequence: digest(HEAD)),
        )

    def test_truncation_before_checkpoint_is_detected(self):
        self.assertEqual(
            ecp.LOCAL_HISTORY_BEHIND_CHECKPOINT,
            verify(current_sequence=119, current_head_digest=digest(OTHER)),
        )

    def test_same_sequence_rewrite_is_detected(self):
        self.assertEqual(ecp.LINEAGE_MISMATCH, verify(current_head_digest=digest(OTHER)))

    def test_fully_rehashed_history_is_detected(self):
        self.assertEqual(
            ecp.LINEAGE_MISMATCH,
            verify(current_sequence=150, current_head_digest=digest(OTHER), head_digest_at_sequence=lambda sequence: digest(OTHER)),
        )

    def test_missing_external_material(self):
        self.assertEqual(
            ecp.EXTERNAL_MATERIAL_MISSING,
            ecp.verify_checkpoint(checkpoint(), None, subject_log_id="audit-main", current_sequence=120, current_head_digest=digest(HEAD)),
        )

    def test_malformed_checkpoint(self):
        value = checkpoint()
        del value["holder_basis"]
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(value, retained=b"{}\n"))

    def test_malformed_digest(self):
        value = checkpoint(committed_head_digest=digest("A" * 64))
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(value, retained=b"{}\n"))

    def test_wrong_subject(self):
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(subject_log_id="other-log"))

    def test_unsupported_schema(self):
        value = checkpoint(schema_version="ecp.checkpoint.v1")
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(value, retained=b"{}\n"))

    def test_unsupported_verification_method(self):
        value = checkpoint(verification_method="provider-specific.v0")
        retained = ecp.canonical_checkpoint_bytes(value)
        self.assertEqual(ecp.UNSUPPORTED_VERIFICATION_METHOD, verify(value, retained=retained))

    def test_ambiguous_verification_method(self):
        value = checkpoint(verification_method=["retained_checkpoint_bytes.v0"])
        self.assertEqual(ecp.UNSUPPORTED_VERIFICATION_METHOD, verify(value, retained=b"{}\n"))

    def test_ahead_without_checkpoint_state_is_unverifiable(self):
        self.assertEqual(ecp.UNVERIFIABLE_LOCAL_STATE, verify(current_sequence=121))
        self.assertEqual(
            ecp.UNVERIFIABLE_LOCAL_STATE,
            verify(current_sequence=121, head_digest_at_sequence=lambda sequence: None),
        )

    def test_stale_match_does_not_claim_freshness(self):
        result = verify(current_sequence=121, current_head_digest=digest(OTHER), head_digest_at_sequence=lambda sequence: digest(HEAD))
        self.assertEqual(ecp.CHECKPOINT_MATCH_STALE, result)
        self.assertNotIn("FRESH", result)
        value = checkpoint(provider_timestamp="2026-10-07T00:00:00Z")
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(value, retained=b"{}\n"))

    def test_provider_receipt_absence_remains_null(self):
        value = checkpoint()
        retained = ecp.canonical_checkpoint_bytes(value)
        parsed = ecp.parse_checkpoint_bytes(retained)
        self.assertIsNone(parsed["provider_receipt_digest"])
        self.assertEqual(ecp.CHECKPOINT_MATCH_CURRENT, verify(value, retained=retained))

    def test_provider_receipt_digest_is_descriptive_only(self):
        value = checkpoint(provider_receipt_digest=digest("c" * 64))
        retained = ecp.canonical_checkpoint_bytes(value)
        self.assertEqual(ecp.CHECKPOINT_MATCH_CURRENT, verify(value, retained=retained))

    def test_multiple_holders_do_not_create_quorum(self):
        first = checkpoint(holder_id="holder-A")
        second = checkpoint(holder_id="holder-B")
        retained = [ecp.canonical_checkpoint_bytes(first), ecp.canonical_checkpoint_bytes(second)]
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(first, retained=retained))
        self.assertEqual(ecp.CHECKPOINT_MATCH_CURRENT, verify(first))
        self.assertEqual(ecp.CHECKPOINT_MATCH_CURRENT, verify(second))

    def test_verification_uses_no_network(self):
        with mock.patch.object(socket, "create_connection", side_effect=AssertionError("network")), mock.patch.object(urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.assertEqual(ecp.CHECKPOINT_MATCH_CURRENT, verify())

    def test_local_checkpoint_alone_never_matches(self):
        self.assertEqual(
            ecp.EXTERNAL_MATERIAL_MISSING,
            ecp.verify_checkpoint(checkpoint(), None, subject_log_id="audit-main", current_sequence=120, current_head_digest=digest(HEAD)),
        )

    def test_altered_retained_bytes_never_match(self):
        value = checkpoint()
        retained = bytearray(ecp.canonical_checkpoint_bytes(value))
        retained[-2] = ord("x")
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(value, retained=bytes(retained)))

    def test_canonical_bytes_are_sorted_utf8_with_one_lf(self):
        retained = ecp.canonical_checkpoint_bytes(checkpoint(holder_id="保持者"))
        self.assertTrue(retained.endswith(b"\n"))
        self.assertFalse(retained.endswith(b"\n\n"))
        self.assertIn("保持者".encode("utf-8"), retained)
        decoded = json.loads(retained)
        self.assertEqual(sorted(decoded.keys()), list(decoded.keys()))

    def test_duplicate_json_key_is_invalid(self):
        retained = ecp.canonical_checkpoint_bytes(checkpoint())
        altered = retained.replace(b'{"algorithm":"sha256"', b'{"algorithm":"sha256","algorithm":"sha256"', 1)
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(retained=altered))

    def test_noncanonical_retained_bytes_are_invalid(self):
        retained = json.dumps(checkpoint(), indent=2).encode("utf-8") + b"\n"
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(retained=retained))

    def test_malformed_local_state_is_unverifiable(self):
        self.assertEqual(ecp.UNVERIFIABLE_LOCAL_STATE, verify(current_sequence=True))
        self.assertEqual(ecp.UNVERIFIABLE_LOCAL_STATE, verify(current_head_digest=digest("x" * 64)))

    def test_unknown_checkpoint_field_is_invalid(self):
        value = checkpoint(untrusted_metadata={"timestamp": "opaque"})
        self.assertEqual(ecp.INVALID_CHECKPOINT, verify(value, retained=b"{}\n"))

    def test_closed_result_set(self):
        self.assertEqual(8, len(ecp.RESULTS))
        self.assertIn(verify(), ecp.RESULTS)


if __name__ == "__main__":
    unittest.main()
