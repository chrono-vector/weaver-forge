"""Claim / Subject Association Record v0.

The record binds one DSDS claim digest to one DSDS presented-subject
digest under code-owned limitations. Matching association digests are
commitments under the CSAR_RECORD domain and assumed SHA-256 collision
resistance. This does not establish creator, time, order, truth, support,
admission, authority, verification, or Human Final.
"""

from __future__ import annotations

import json
import re

from domain_separated_digest_v0 import (
    DomainSeparatedDigestError,
    digest_presented_subject_bytes,
    digest_r4_claim_body,
    domain_separated_digest,
)

_ASSOCIATION_DOMAIN = "CSAR_RECORD"
_SCHEMA_VERSION = "csar.v0"
_LIMITATIONS = (
    "presented_bytes_only",
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
    "not_creator_time_or_order",
    "not_legacy_digest_equivalence",
    "not_historical_closed_receipt_binding",
    "omission_not_detected_here",
    "not_freshness",
    "not_replacement_or_post_hoc_detection",
)
_KEYS = (
    "schema_version",
    "authority",
    "claim_digest_csar_v0",
    "subject_digest_csar_v0",
    "limitations",
    "association_digest_csar_v0",
)
_PREIMAGE_KEYS = (
    "schema_version",
    "authority",
    "claim_digest_csar_v0",
    "subject_digest_csar_v0",
    "limitations",
)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class CsarError(ValueError):
    """Closed failure while producing or checking a CSAR-v0 record."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(message: str) -> None:
    raise CsarError("CSAR_REJECTED", message)


def _canonical_bytes(record: dict) -> bytes:
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in parsed:
            _fail("duplicate JSON key")
        parsed[key] = value
    return parsed


def _closed_digest(fn, value, message: str):
    try:
        return fn(value)
    except DomainSeparatedDigestError as exc:
        raise CsarError("CSAR_REJECTED", message) from exc


def _require_limitations(value: object) -> None:
    if type(value) is not list or len(value) != len(_LIMITATIONS):
        _fail("limitations are not the code-owned list")
    for got, expected in zip(value, _LIMITATIONS, strict=True):
        if type(got) is not str or got != expected:
            _fail("limitations are not the code-owned list")


def _require_digest_text(value: object) -> None:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        _fail("digest text is malformed")


def csar_structurally_consistent(record: dict) -> str:
    """Return the structural tag for one internally consistent record.

    Original claim bytes and subject bytes are not inputs. The returned
    tag does not establish reproduction from originals.
    """
    if type(record) is not dict:
        _fail("record must be an exact dict")
    for key in record:
        if type(key) is not str:
            _fail("key must be exact str")
    if set(record) != set(_KEYS):
        _fail("record keys are not the six-field schema")
    if type(record["schema_version"]) is not str or record["schema_version"] != _SCHEMA_VERSION:
        _fail("schema_version mismatch")
    authority = record["authority"]
    if type(authority) is not bool or authority:
        _fail("authority is not exact False")
    _require_limitations(record["limitations"])
    for name in ("claim_digest_csar_v0", "subject_digest_csar_v0", "association_digest_csar_v0"):
        _require_digest_text(record[name])
    preimage = {key: record[key] for key in _PREIMAGE_KEYS}
    association = _closed_digest(
        lambda raw: domain_separated_digest(_ASSOCIATION_DOMAIN, raw),
        _canonical_bytes(preimage),
        "association preimage was rejected",
    )
    if record["association_digest_csar_v0"] != association:
        _fail("association digest does not reproduce")
    return "CSAR_STRUCTURALLY_CONSISTENT"


def produce_csar(claim: dict, subject: bytes) -> dict:
    """Build one six-field record from an R4 claim dict and subject bytes.

    The only inputs are the claim and the subject. Digests, limitations,
    authority, domain, and paths are not inputs.
    """
    if type(claim) is not dict:
        _fail("claim must be an exact dict")
    for key in claim:
        if type(key) is not str:
            _fail("claim key must be exact str")
    if type(subject) is not bytes:
        _fail("subject must be exact bytes")
    claim_digest = _closed_digest(
        digest_r4_claim_body,
        claim,
        "claim was rejected",
    )
    subject_digest = _closed_digest(
        digest_presented_subject_bytes,
        subject,
        "subject was rejected",
    )
    preimage = {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "claim_digest_csar_v0": claim_digest,
        "subject_digest_csar_v0": subject_digest,
        "limitations": list(_LIMITATIONS),
    }
    association = _closed_digest(
        lambda raw: domain_separated_digest(_ASSOCIATION_DOMAIN, raw),
        _canonical_bytes(preimage),
        "association preimage was rejected",
    )
    return {
        "association_digest_csar_v0": association,
        "authority": False,
        "claim_digest_csar_v0": claim_digest,
        "limitations": list(_LIMITATIONS),
        "schema_version": _SCHEMA_VERSION,
        "subject_digest_csar_v0": subject_digest,
    }


def parse_csar(raw: bytes) -> dict:
    """Parse one canonical six-field serialization.

    Duplicate keys are rejected. The raw bytes must equal the canonical
    UTF-8 re-encoding, with no trailing newline.
    """
    if type(raw) is not bytes:
        _fail("serialized CSAR must be exact bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CsarError("CSAR_REJECTED", "serialized CSAR is not UTF-8") from exc
    try:
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise CsarError("CSAR_REJECTED", "serialized CSAR is not JSON") from exc
    csar_structurally_consistent(parsed)
    if raw != _canonical_bytes(parsed):
        _fail("serialized bytes are not canonical")
    return parsed


def csar_reproduced_from_supplied_inputs(record: dict, claim: dict, subject: bytes) -> str:
    """Return the reproduction tag when the supplied originals rebuild the record.

    This is supplied-input reproduction only. It recomputes the record
    and requires exact six-field equality.
    """
    csar_structurally_consistent(record)
    produced = produce_csar(claim, subject)
    if produced != record:
        _fail("six-field records are not equal")
    return "CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS"
