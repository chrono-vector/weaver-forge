"""Association Carriage Receipt v0.

The receipt carries one nested CSAR-v0 record. The outer digest is the
CLOSED association-carriage digest of the four-field preimage. Matching
receipt digests are commitments under assumed SHA-256 collision
resistance. Supplied-input reproduction is not independent reproduction.
This does not establish creator, time, order, truth, support, admission,
authority, or Human Final.
"""

from __future__ import annotations

import json
import re

from association_carriage_digest_v0 import (
    AssociationCarriageDigestError,
    digest_association_carriage_preimage,
)
from csar_v0 import (
    CsarError,
    csar_reproduced_from_supplied_inputs,
    csar_structurally_consistent,
    produce_csar,
)

_SCHEMA_VERSION = "association_carriage_receipt.v0"
_LIMITATIONS = (
    "carries_exactly_one_nested_csar_v0",
    "structural_consistency_is_not_reproduction",
    "originals_not_retained",
    "not_creator_time_or_order",
    "not_pre_execution_occurrence",
    "not_subject_correctness",
    "not_truth",
    "not_support",
    "not_sufficiency",
    "not_completeness",
    "not_correspondence",
    "not_independence",
    "not_admission",
    "not_authority",
    "not_verification",
    "not_human_final",
    "not_freshness",
    "replay_not_distinguished",
    "not_external_anchor",
    "not_historical_closed_receipt_binding",
    "not_execution_success",
    "not_legacy_digest_equivalence",
)
_KEYS = (
    "schema_version",
    "authority",
    "csar_record",
    "limitations",
    "receipt_digest",
)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_CSAR_STRUCTURAL = "CSAR_STRUCTURALLY_CONSISTENT"
_CSAR_REPRODUCED = "CSAR_REPRODUCED_FROM_SUPPLIED_INPUTS"


class AcrError(ValueError):
    """Closed failure while producing or checking an ACR-v0 record."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(message: str) -> None:
    raise AcrError("ACR_REJECTED", message)


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
        raise AcrError("ACR_REJECTED", "record is not canonical JSON") from exc
    return text.encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[object, object]]) -> dict:
    parsed: dict[str, object] = {}
    for key, value in pairs:
        if type(key) is not str or key in parsed:
            _fail("duplicate JSON key")
        parsed[key] = value
    return parsed


def _consume_csar(fn, *args):
    try:
        return fn(*args)
    except CsarError as exc:
        detail = str(exc)
        prefix = "CSAR_REJECTED: "
        if detail.startswith(prefix):
            detail = detail[len(prefix) :]
        raise AcrError("ACR_REJECTED", detail) from exc


def _receipt_digest(preimage: bytes) -> str:
    try:
        return digest_association_carriage_preimage(preimage)
    except AssociationCarriageDigestError as exc:
        raise AcrError("ACR_REJECTED", "receipt preimage was rejected") from exc


def _require_limitations(value: object) -> None:
    if type(value) is not list or len(value) != len(_LIMITATIONS):
        _fail("limitations are not the code-owned list")
    for got, expected in zip(value, _LIMITATIONS, strict=True):
        if type(got) is not str or got != expected:
            _fail("limitations are not the code-owned list")


def _require_digest_text(value: object) -> None:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        _fail("digest text is malformed")


def _require_csar_tag(result: object, expected: str, message: str) -> None:
    if result != expected:
        _fail(message)


def acr_structurally_consistent(record: dict) -> str:
    """Return the structural tag for one internally consistent receipt.

    Original claim and subject bytes are not inputs. The returned tag
    does not establish reproduction from originals.
    """
    if type(record) is not dict:
        _fail("record must be an exact dict")
    for key in record:
        if type(key) is not str:
            _fail("key must be exact str")
    if set(record) != set(_KEYS):
        _fail("record keys are not the five-field schema")
    if type(record["schema_version"]) is not str or record["schema_version"] != _SCHEMA_VERSION:
        _fail("schema_version mismatch")
    authority = record["authority"]
    if type(authority) is not bool or authority:
        _fail("authority is not exact False")
    _require_limitations(record["limitations"])
    nested = record["csar_record"]
    if type(nested) is not dict:
        _fail("csar_record must be one exact dict")
    _require_csar_tag(
        _consume_csar(csar_structurally_consistent, nested),
        _CSAR_STRUCTURAL,
        "nested CSAR is not structurally consistent",
    )
    _require_digest_text(record["receipt_digest"])
    preimage = {
        "schema_version": record["schema_version"],
        "authority": record["authority"],
        "csar_record": nested,
        "limitations": record["limitations"],
    }
    if record["receipt_digest"] != _receipt_digest(_canonical_bytes(preimage)):
        _fail("receipt digest does not reproduce")
    return "ACR_STRUCTURALLY_CONSISTENT"


def produce_acr(claim: dict, subject: bytes, csar_record: dict) -> dict:
    """Build one five-field receipt from originals and one embedded CSAR.

    Structural consistency of the embedded record does not authorize
    creation. The embedded record must be reproduced from the supplied
    claim and subject. Digests, limitations, and paths are not inputs.
    """
    if type(csar_record) is not dict:
        _fail("csar_record must be one exact dict")
    _require_csar_tag(
        _consume_csar(csar_reproduced_from_supplied_inputs, csar_record, claim, subject),
        _CSAR_REPRODUCED,
        "nested CSAR was not reproduced from the supplied inputs",
    )
    nested = _consume_csar(produce_csar, claim, subject)
    preimage = {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "csar_record": nested,
        "limitations": list(_LIMITATIONS),
    }
    return {
        "schema_version": _SCHEMA_VERSION,
        "authority": False,
        "csar_record": nested,
        "limitations": list(_LIMITATIONS),
        "receipt_digest": _receipt_digest(_canonical_bytes(preimage)),
    }


def parse_acr(raw: bytes) -> dict:
    """Parse one canonical five-field serialization.

    Duplicate keys are rejected. The raw bytes must equal the canonical
    UTF-8 re-encoding, with no trailing newline.
    """
    if type(raw) is not bytes:
        _fail("serialized ACR must be exact bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AcrError("ACR_REJECTED", "serialized ACR is not UTF-8") from exc
    try:
        parsed = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise AcrError("ACR_REJECTED", "serialized ACR is not JSON") from exc
    acr_structurally_consistent(parsed)
    if raw != _canonical_bytes(parsed):
        _fail("serialized bytes are not canonical")
    return parsed


def acr_reproduced_from_supplied_inputs(record: dict, claim: dict, subject: bytes) -> str:
    """Return the reproduction tag when the supplied originals rebuild the receipt.

    This is supplied-input reproduction only. It is not independent
    reproduction.
    """
    acr_structurally_consistent(record)
    _require_csar_tag(
        _consume_csar(
            csar_reproduced_from_supplied_inputs,
            record["csar_record"],
            claim,
            subject,
        ),
        _CSAR_REPRODUCED,
        "nested CSAR was not reproduced from the supplied inputs",
    )
    return "ACR_REPRODUCED_FROM_SUPPLIED_INPUTS"
