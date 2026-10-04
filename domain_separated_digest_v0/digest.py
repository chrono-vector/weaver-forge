"""Domain-Separated Digest Spec v0.

A digest is meaningful only together with its DSDS domain. Equal 64-hex
strings are not semantic equality with legacy untagged digests, including
canonical_digest output and CLOSED receipt or file digests.

Maximum meaning: the same permitted domain and the same spec-defined
preimage bytes produce the same SHA-256. This does not establish creator,
time, order, authenticity, subject correctness, claim truth, evidence
support, freshness, correspondence, independence, admission, authority,
verification, or Human Final.

R4_CLAIM_BODY commits to canonical_dumps(parsed.to_dict()) after the
pre-check below. It does not commit to rejected input. Intentional R4
equivalences that remain are: omitted, null, and "" notes become
notes:""; omitted ref lists become []; ref order and duplicates become
sorted unique; omitted, null, and {} extra omit the key; omitted and null
workflow_state omit the key; workflow_state:"" remains; lists under a
set-like parent key are sorted and deduped at any depth, including inside
extra. Unicode is not normalized.
"""

from __future__ import annotations

import hashlib
from typing import Any

from audit_lifecycle.epistemic.records import EpistemicClaimRecord
from audit_lifecycle.epistemic.serialize import canonical_dumps
from audit_lifecycle.epistemic.validation import (
    EpistemicValidationError,
    validate_claim_dict,
)

PREFIX = "weaver.digest.v0:"
R4_CLAIM_BODY = "R4_CLAIM_BODY"
PRESENTED_SUBJECT_BYTES = "PRESENTED_SUBJECT_BYTES"
CSAR_RECORD = "CSAR_RECORD"
DOMAINS = frozenset({R4_CLAIM_BODY, PRESENTED_SUBJECT_BYTES, CSAR_RECORD})

_ALLOWED_CLAIM_KEYS = frozenset(
    {
        "schema_version",
        "claim_id",
        "statement",
        "claim_kind",
        "epistemic_status",
        "scope",
        "authority",
        "evidence_refs",
        "provenance_refs",
        "notes",
        "workflow_state",
        "extra",
    }
)
_STRIPPED_FIELDS = ("claim_id", "statement", "scope")
_REF_FIELDS = ("evidence_refs", "provenance_refs")


class DomainSeparatedDigestError(ValueError):
    """Closed failure while deriving a domain-separated digest."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise DomainSeparatedDigestError(code, message)


def _walk(value: Any, *, allow_tuple: bool = False) -> None:
    """Reject shapes that R4 or canonical_dumps would coerce or stringify."""
    if value is None or type(value) is bool or type(value) is int or type(value) is str:
        return
    if isinstance(value, float):
        _fail("DSDS_CLAIM_INVALID", "float is not a commitment value")
    if isinstance(value, (bytes, bytearray, memoryview)):
        _fail("DSDS_CLAIM_INVALID", "bytes are not a claim commitment value")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail("DSDS_CLAIM_INVALID", "mapping key is not a string")
            _walk(item)
        return
    if type(value) is list or (allow_tuple and type(value) is tuple):
        for item in value:
            _walk(item)
        return
    _fail("DSDS_CLAIM_INVALID", "claim value is not a plain commitment value")


def _reject_strip(value: Any, label: str) -> None:
    if type(value) is str and value != value.strip():
        _fail("DSDS_CLAIM_INVALID", f"{label} would be stripped")


def r4_claim_body_preimage(claim: Any) -> bytes:
    """Return the UTF-8 canonical preimage of one R4 claim body.

    Caller digest hex is not an input. confidence is rejected.
    """
    if type(claim) is not dict:
        _fail("DSDS_CLAIM_INVALID", "claim must be a dict")
    if "confidence" in claim:
        _fail("DSDS_CLAIM_INVALID", "confidence is not committed")
    unknown = set(claim) - _ALLOWED_CLAIM_KEYS
    if unknown:
        _fail("DSDS_CLAIM_INVALID", "unknown top-level key")
    for field in _STRIPPED_FIELDS:
        if field in claim:
            _reject_strip(claim[field], field)
    for field in _REF_FIELDS:
        if field not in claim:
            continue
        refs = claim[field]
        if type(refs) is list or type(refs) is tuple:
            for item in refs:
                _reject_strip(item, field)
            _walk(refs, allow_tuple=True)
        else:
            _walk(refs)
    for field, value in claim.items():
        if field in _REF_FIELDS:
            continue
        _walk(value)
    try:
        parsed: EpistemicClaimRecord = validate_claim_dict(claim)
        text = canonical_dumps(parsed.to_dict())
    except (EpistemicValidationError, TypeError, ValueError):
        _fail("DSDS_CLAIM_INVALID", "claim is not a valid R4 body")
    if type(text) is not str:
        _fail("DSDS_CLAIM_INVALID", "canonical preimage is not text")
    return text.encode("utf-8")


def domain_separated_digest(domain_id: str, preimage: bytes) -> str:
    """Hash preimage under one code-owned domain.

    The hex return value is the digest. This function does not accept an
    expected or caller-supplied digest.
    """
    if type(domain_id) is not str or domain_id not in DOMAINS:
        _fail("DSDS_DOMAIN_INVALID", "domain is not in the closed registry")
    if type(preimage) is not bytes:
        _fail("DSDS_PREIMAGE_INVALID", "preimage must be exact bytes")
    if domain_id == PRESENTED_SUBJECT_BYTES and len(preimage) < 1:
        _fail("DSDS_PREIMAGE_INVALID", "subject bytes are empty")
    tagged = (PREFIX + domain_id).encode("ascii") + b"\x00" + preimage
    return hashlib.sha256(tagged).hexdigest()


def digest_presented_subject_bytes(subject: bytes) -> str:
    """Digest one presented byte string. No path, text, or archive decoding."""
    return domain_separated_digest(PRESENTED_SUBJECT_BYTES, subject)


def digest_r4_claim_body(claim: Any) -> str:
    """Digest one pre-checked R4 claim body under R4_CLAIM_BODY."""
    return domain_separated_digest(R4_CLAIM_BODY, r4_claim_body_preimage(claim))
