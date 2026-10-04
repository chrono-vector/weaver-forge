"""Strict UTF-8 Byte Predicate v0.

The record certifies one code-owned fact about one exact byte string:
the bytes are nonempty, they decode as strict UTF-8, and they do not
start with a UTF-8 BOM. The predicate digest is a private-tag SHA-256
of the five-field preimage. Matching predicate digests mean the same
tag and the same preimage bytes under assumed SHA-256 collision
resistance. This does not establish meaning, evidence kind,
compatibility, support, relevance, sufficiency, completeness, truth,
authority, independence, admission, verification, or Human Final.
"""

from __future__ import annotations

import hashlib
import json
import re

from domain_separated_digest_v0 import (
    DomainSeparatedDigestError as _DomainSeparatedDigestError,
    digest_presented_subject_bytes as _digest_presented_subject_bytes,
)

_TAG = b"weaver.subp.digest.v0\x00"
_SCHEMA_VERSION = "strict_utf8_byte_predicate.v0"
_TOKEN = "NON_EMPTY_STRICT_UTF8_NO_BOM"
_BOM = b"\xef\xbb\xbf"
_LIMITATIONS = (
    "nonempty_strict_utf8_no_bom_only",
    "decoded_text_not_retained",
    "originals_not_retained",
    "no_unicode_normalization",
    "nul_not_terminator",
    "not_exclusive_grammar",
    "not_json",
    "not_mime_or_filename",
    "not_meaning_or_language",
    "not_evidence_kind",
    "not_evidence_selection",
    "not_compatibility",
    "not_support",
    "not_relevance",
    "not_sufficiency",
    "not_completeness",
    "not_truth",
    "not_authority",
    "not_admission",
    "not_verification",
    "not_human_final",
    "not_claim_binding",
    "not_psrd_role_reinterpretation",
    "not_omission_or_contradiction_detection",
    "not_duplicate_or_order",
    "not_replay_or_freshness",
    "not_external_anchor",
    "not_self_production_detection",
    "not_legacy_digest_equivalence",
)
_KEYS = (
    "schema_version",
    "authority",
    "utf8_predicate",
    "presented_subject_digest",
    "limitations",
    "predicate_digest",
)
_PREIMAGE_KEYS = (
    "schema_version",
    "authority",
    "utf8_predicate",
    "presented_subject_digest",
    "limitations",
)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class SubpError(ValueError):
    """Closed failure while producing or checking a SUBP-v0 record."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(message: str) -> None:
    raise SubpError("SUBP_REJECTED", message)


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
        raise SubpError("SUBP_REJECTED", "record is not canonical JSON") from exc
    return text.encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in parsed:
            _fail("duplicate JSON key")
        parsed[key] = value
    return parsed


def _presented_digest(subject: bytes) -> str:
    try:
        return _digest_presented_subject_bytes(subject)
    except _DomainSeparatedDigestError as exc:
        raise SubpError("SUBP_REJECTED", "subject was rejected") from exc


def _predicate_digest(preimage: bytes) -> str:
    if type(preimage) is not bytes or len(preimage) < 1:
        _fail("predicate preimage was rejected")
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


def subp_structurally_consistent(record: dict) -> str:
    """Return the structural tag for one internally consistent predicate.

    Subject bytes are not an input. The returned tag does not establish
    reproduction from those bytes and does not decode UTF-8.
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
    if type(authority) is not bool or authority is not False:
        _fail("authority is not exact False")
    token = record["utf8_predicate"]
    if type(token) is not str or token != _TOKEN:
        _fail("utf8_predicate is not the code-owned token")
    _require_limitations(record["limitations"])
    _require_digest_text(record["presented_subject_digest"])
    _require_digest_text(record["predicate_digest"])
    preimage = {key: record[key] for key in _PREIMAGE_KEYS}
    if record["predicate_digest"] != _predicate_digest(_canonical_bytes(preimage)):
        _fail("predicate digest does not reproduce")
    return "SUBP_STRUCTURALLY_CONSISTENT"


def produce_subp(subject: bytes) -> dict:
    """Build one six-field predicate from exact presented-subject bytes.

    The only input is the subject. Format, kind, MIME, filename, role,
    limitations, authority, digests, domains, prefixes, and paths are
    not inputs.
    """
    if type(subject) is not bytes:
        _fail("subject must be exact bytes")
    if len(subject) == 0:
        _fail("subject is empty")
    if subject.startswith(_BOM):
        _fail("subject has a leading UTF-8 BOM")
    try:
        subject.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise SubpError("SUBP_REJECTED", "subject is not strict UTF-8") from exc
    presented = _presented_digest(subject)
    limitations = list(_LIMITATIONS)
    preimage = {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "utf8_predicate": _TOKEN,
        "presented_subject_digest": presented,
        "limitations": limitations,
    }
    return {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "utf8_predicate": _TOKEN,
        "presented_subject_digest": presented,
        "limitations": limitations,
        "predicate_digest": _predicate_digest(_canonical_bytes(preimage)),
    }


def parse_subp(raw: bytes) -> dict:
    """Parse one canonical six-field serialization.

    Duplicate keys are rejected. The raw bytes must equal the canonical
    UTF-8 re-encoding, with no trailing newline. This is a parse of the
    descriptor record, not of the presented subject.
    """
    if type(raw) is not bytes:
        _fail("serialized SUBP must be exact bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SubpError("SUBP_REJECTED", "serialized SUBP is not UTF-8") from exc
    try:
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise SubpError("SUBP_REJECTED", "serialized SUBP is not JSON") from exc
    subp_structurally_consistent(parsed)
    if raw != _canonical_bytes(parsed):
        _fail("serialized bytes are not canonical")
    return parsed


def subp_reproduced_from_supplied_inputs(record: dict, subject: bytes) -> str:
    """Return the reproduction tag when the supplied subject rebuilds the record.

    This is supplied-input reproduction only. Comparing the presented-subject
    digest alone is not reproduction.
    """
    subp_structurally_consistent(record)
    produced = produce_subp(subject)
    if not _exact_six_fields(produced, record):
        _fail("six-field records are not equal")
    return "SUBP_REPRODUCED_FROM_SUPPLIED_INPUTS"
