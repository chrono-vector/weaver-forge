"""Presented-Subject Role Descriptor v0.

The record commits one code-owned role to the CLOSED presented-subject
digest of one exact byte string. The descriptor digest is a private-tag
SHA-256 of the five-field preimage. Matching descriptor digests mean the
same tag and the same preimage bytes under assumed SHA-256 collision
resistance. This does not establish compatibility, support, sufficiency,
completeness, truth, correspondence, independence, admission, authority,
verification, or Human Final.
"""

from __future__ import annotations

import hashlib
import json
import re

from domain_separated_digest_v0 import (
    DomainSeparatedDigestError as _DomainSeparatedDigestError,
    digest_presented_subject_bytes as _digest_presented_subject_bytes,
)

_TAG = b"weaver.psrd.digest.v0\x00"
_SCHEMA_VERSION = "presented_subject_role_descriptor.v0"
_ROLE = "UNINTERPRETED_PRESENTED_BYTES"
_LIMITATIONS = (
    "uninterpreted_presented_bytes_only",
    "role_not_inferred_from_bytes",
    "not_evidence_selection",
    "not_compatibility",
    "not_support",
    "not_sufficiency",
    "not_completeness",
    "not_truth",
    "not_correspondence",
    "not_independence",
    "not_admission",
    "not_authority",
    "not_verification",
    "not_human_final",
    "not_claim_binding",
    "not_omission_detection",
    "not_contradiction_detection",
    "not_duplicate_detection",
    "not_order",
    "not_replay_distinction",
    "not_freshness",
    "not_external_anchor",
    "not_self_production_detection",
    "not_relevance",
    "not_creator_time_or_order",
    "not_legacy_digest_equivalence",
    "not_historical_closed_receipt_binding",
    "not_rer_evidence_kind",
    "not_ebd_relation",
    "originals_not_retained",
)
_KEYS = (
    "schema_version",
    "authority",
    "presented_subject_role",
    "subject_digest_psrd_v0",
    "limitations",
    "descriptor_digest_psrd_v0",
)
_PREIMAGE_KEYS = (
    "schema_version",
    "authority",
    "presented_subject_role",
    "subject_digest_psrd_v0",
    "limitations",
)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class PsrdError(ValueError):
    """Closed failure while producing or checking a PSRD-v0 record."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(message: str) -> None:
    raise PsrdError("PSRD_REJECTED", message)


def _canonical_bytes(record: dict) -> bytes:
    try:
        text = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PsrdError("PSRD_REJECTED", "record is not canonical JSON") from exc
    return text.encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in parsed:
            _fail("duplicate JSON key")
        parsed[key] = value
    return parsed


def _subject_digest(subject: bytes) -> str:
    try:
        return _digest_presented_subject_bytes(subject)
    except _DomainSeparatedDigestError as exc:
        raise PsrdError("PSRD_REJECTED", "subject was rejected") from exc


def _descriptor_digest(preimage: bytes) -> str:
    if type(preimage) is not bytes or len(preimage) < 1:
        _fail("descriptor preimage was rejected")
    return hashlib.sha256(_TAG + preimage).hexdigest()


def _require_limitations(value: object) -> None:
    if type(value) is not list or len(value) != len(_LIMITATIONS):
        _fail("limitations are not the code-owned list")
    for got, expected in zip(value, _LIMITATIONS, strict=True):
        if type(got) is not str or got != expected:
            _fail("limitations are not the code-owned list")


def _require_digest_text(value: object) -> None:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        _fail("digest text is malformed")


def _exact_six_fields(produced: dict, record: dict) -> bool:
    if type(produced) is not dict or type(record) is not dict:
        return False
    if set(produced) != set(_KEYS) or set(record) != set(_KEYS):
        return False
    for key in _KEYS:
        left = produced[key]
        right = record[key]
        if type(left) is not type(right):
            return False
        if key == "limitations":
            if type(left) is not list or len(left) != len(right):
                return False
            for item, expected in zip(left, right, strict=True):
                if type(item) is not str or type(expected) is not str or item != expected:
                    return False
        elif left != right:
            return False
    return True


def psrd_structurally_consistent(record: dict) -> str:
    """Return the structural tag for one internally consistent descriptor.

    Subject bytes are not an input. The returned tag does not establish
    reproduction from those bytes.
    """
    if type(record) is not dict:
        _fail("record must be an exact dict")
    for key in record:
        if type(key) is not str:
            _fail("key must be exact str")
    if set(record) != set(_KEYS):
        _fail("record keys are not the six-field schema")
    if type(record["schema_version"]) is not str or record["schema_version"] != _SCHEMA_VERSION:
        _fail("schema_version is not the exact schema")
    authority = record["authority"]
    if type(authority) is not bool or authority:
        _fail("authority is not exact False")
    role = record["presented_subject_role"]
    if type(role) is not str or role != _ROLE:
        _fail("presented_subject_role is not the code-owned role")
    _require_limitations(record["limitations"])
    _require_digest_text(record["subject_digest_psrd_v0"])
    _require_digest_text(record["descriptor_digest_psrd_v0"])
    preimage = {key: record[key] for key in _PREIMAGE_KEYS}
    if record["descriptor_digest_psrd_v0"] != _descriptor_digest(_canonical_bytes(preimage)):
        _fail("descriptor digest does not reproduce")
    return "PSRD_STRUCTURALLY_CONSISTENT"


def produce_psrd(subject: bytes) -> dict:
    """Build one six-field descriptor from exact presented-subject bytes.

    The only input is the subject. Role, limitations, authority, digests,
    domains, prefixes, paths, and evidence sets are not inputs.
    """
    if type(subject) is not bytes:
        _fail("subject must be exact bytes")
    subject_digest = _subject_digest(subject)
    limitations = list(_LIMITATIONS)
    preimage = {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "presented_subject_role": _ROLE,
        "subject_digest_psrd_v0": subject_digest,
        "limitations": limitations,
    }
    return {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "presented_subject_role": _ROLE,
        "subject_digest_psrd_v0": subject_digest,
        "limitations": limitations,
        "descriptor_digest_psrd_v0": _descriptor_digest(_canonical_bytes(preimage)),
    }


def parse_psrd(raw: bytes) -> dict:
    """Parse one canonical six-field serialization.

    Duplicate keys are rejected. The raw bytes must equal the canonical
    UTF-8 re-encoding, with no trailing newline.
    """
    if type(raw) is not bytes:
        _fail("serialized PSRD must be exact bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PsrdError("PSRD_REJECTED", "serialized PSRD is not UTF-8") from exc
    try:
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise PsrdError("PSRD_REJECTED", "serialized PSRD is not JSON") from exc
    psrd_structurally_consistent(parsed)
    if raw != _canonical_bytes(parsed):
        _fail("serialized bytes are not canonical")
    return parsed


def psrd_reproduced_from_supplied_inputs(record: dict, subject: bytes) -> str:
    """Return the reproduction tag when the supplied subject rebuilds the record.

    This is supplied-input reproduction only. Comparing the subject digest
    alone is not reproduction.
    """
    psrd_structurally_consistent(record)
    produced = produce_psrd(subject)
    if not _exact_six_fields(produced, record):
        _fail("six-field records are not equal")
    return "PSRD_REPRODUCED_FROM_SUPPLIED_INPUTS"
