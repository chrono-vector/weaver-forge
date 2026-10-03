"""Derive a non-authoritative receipt over a completed multi-agent exchange.

The receipt binds proposal, challenge, revision, and optional human selection
by digest. It does not dispatch agents, execute tools, admit evidence, or
create Human Final.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from audit_lifecycle.epistemic.serialize import canonical_digest

SCHEMA_VERSION = "conducting_receipt.v0"
_LEAF_TYPES = (str, bool, int, float)
_SHA256_WIDTH = 64
_HEX = frozenset("0123456789abcdef")
_UNPINNED = frozenset(
    {
        "head",
        "latest",
        "main",
        "master",
        "origin/main",
        "origin/master",
        "current",
        "same as above",
    }
)
_CHALLENGE_KINDS = frozenset({"COUNTEREXAMPLE", "ASSUMPTION_ATTACK", "WEAKENING"})
_CHALLENGE_RESULTS = frozenset(
    {
        "COUNTEREXAMPLE_FOUND",
        "NO_COUNTEREXAMPLE_FOUND",
        "INVALID_CHALLENGE",
    }
)
_EXCHANGE_REQUIRED = frozenset({"session_id", "revisions", "challenges"})
_EXCHANGE_OPTIONAL = frozenset(
    {
        "target_claim_id",
        "target_artifact_digest",
        "human_selection",
    }
)
_REVISION_REQUIRED = frozenset(
    {
        "revision_id",
        "content",
        "created_order",
        "event_order",
        "agent_id",
        "agent_role",
        "assumptions",
    }
)
_REVISION_OPTIONAL = frozenset(
    {
        "content_digest",
        "parent_revision_id",
        "parent_content_digest",
        "responds_to",
        "provider",
        "model",
        "claim_id",
    }
)
_CHALLENGE_REQUIRED = frozenset(
    {
        "challenge_id",
        "target_revision_id",
        "target_content_digest",
        "challenger_id",
        "agent_role",
        "challenge_kind",
        "rationale",
        "counterexample_present",
        "assumptions_attacked",
        "created_order",
        "event_order",
    }
)
_CHALLENGE_OPTIONAL = frozenset(
    {
        "challenge_digest",
        "counterexample",
        "counterexample_digest",
        "provider",
        "model",
    }
)
_ASSUMPTION_REQUIRED = frozenset(
    {"statement", "introduced_in_revision", "status"}
)
_ASSUMPTION_OPTIONAL = frozenset(
    {"assumption_digest", "resolved_by_revision", "resolution_ref"}
)
_RATIONALE_REQUIRED = frozenset({"claim", "assumptions", "attack"})
_SELECTION_REQUIRED = frozenset(
    {"selected_revision_id", "selected_content_digest", "selector_is_human"}
)
_SELECTION_OPTIONAL = frozenset({"selection_note", "authority"})
_COUNTEREXAMPLE_REQUIRED = frozenset({"body"})
_LIMITATIONS = (
    "independent evidence",
    "accepted independent reproduction",
    "Human Final",
    "human verification",
    "agent independence proof",
    "agent identity proof",
    "consensus authority",
    "challenge as proof",
    "revision as acceptance",
    "canonical status",
    "published status",
    "deployed status",
    "truth",
    "hidden chain-of-thought",
    "tool execution",
    "agent dispatch",
)
_COT_ALIASES = frozenset(
    {
        "chainofthought",
        "privatereasoning",
        "hiddenreasoning",
        "scratchpad",
    }
)
_FORBIDDEN_ALIASES = frozenset(
    {
        "independentevidencecount",
        "admissionstatus",
        "structuralcandidate",
        "verificationkind",
        "claimsiwacceptance",
        "claimsindependentwitness",
        "humanfinal",
        "humanfinalstatus",
        "ishumanfinal",
        "createshumanfinal",
        "promotestohumanfinal",
        "independencescore",
        "diversityscore",
        "consensus",
        "majority",
        "verified",
        "recovered",
        "vector",
        "eig",
        "canonical",
        "published",
        "deployed",
        "independent",
        "independence",
        "proventrue",
        "humanreviewaccepted",
        "classification",
        "sequencestatus",
        "counterexamplestatus",
        "selectionstatus",
        "receiptdigest",
        "unresolvedassumptions",
        "assumptionrecords",
        "proposal",
    }
)


class ConductingError(ValueError):
    """Closed failure while deriving a conducting receipt."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise ConductingError(code, message)


def _alias(name: str) -> str:
    return "".join(char for char in name.lower() if char.isalnum())


def _snapshot(value: Any, depth: int = 0) -> Any:
    """Copy caller values once into exact built-in containers and leaves."""
    if depth > 32:
        _fail("CONDUCTING_SOURCE_INVALID", "input is nested too deeply")
    if value is None or type(value) in _LEAF_TYPES:
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("CONDUCTING_SOURCE_INVALID", "mapping key must be a string")
            if key in copied:
                _fail("CONDUCTING_SOURCE_INVALID", "mapping repeats a key")
            copied[key] = _snapshot(item, depth + 1)
        return copied
    if type(value) is list or type(value) is tuple:
        return [_snapshot(item, depth + 1) for item in value]
    _fail("CONDUCTING_SOURCE_INVALID", "input is not plain JSON data")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, bool) or not isinstance(value, Mapping):
        _fail("CONDUCTING_SOURCE_INVALID", f"{label} must be a mapping")
    return value


def _keys(
    record: Mapping[str, Any],
    required: frozenset[str],
    optional: frozenset[str],
    code: str,
) -> None:
    unknown = set(record) - required - optional
    if unknown:
        _fail(code, "record has an unsupported field")
    if not required <= set(record):
        _fail(code, "record is missing a required field")


def _nonempty(value: Any, code: str, label: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(code, f"{label} is missing")
    return value


def _unpinned(value: Any) -> bool:
    return type(value) is str and value.strip().lower() in _UNPINNED


def _identity(value: Any, code: str, label: str) -> str:
    text = _nonempty(value, code, label)
    if _unpinned(text):
        _fail(code, f"{label} is not a bound identity")
    return text


def _sha256(value: Any, code: str) -> str:
    if type(value) is not str or len(value) != _SHA256_WIDTH:
        _fail(code, "digest is not a bound sha256")
    if any(char not in _HEX for char in value):
        _fail(code, "digest is not a bound sha256")
    if _unpinned(value):
        _fail(code, "digest is not a bound sha256")
    return value


def _digest(record: Any, code: str) -> str:
    try:
        return canonical_digest(record)
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ConductingError):
            raise
        _fail(code, "record cannot be canonicalized")
        raise AssertionError("closed") from exc


def _order(value: Any, code: str, label: str) -> int:
    if type(value) is not int:
        _fail(code, f"{label} is not an exact int")
    if value < 0:
        _fail(code, f"{label} is not a bound order")
    return value


def _plain_list(value: Any, code: str, label: str) -> list[Any]:
    if type(value) is not list:
        _fail(code, f"{label} must be a list")
    return value


def _scan_cot(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _alias(key) in _COT_ALIASES:
                _fail(
                    "CONDUCTING_COT_FORBIDDEN",
                    "hidden chain-of-thought is not stored",
                )
            _scan_cot(item)
        return
    if type(value) is list:
        for item in value:
            _scan_cot(item)


def _reject_forbidden_names(names: set[str], code: str) -> None:
    for name in names:
        alias = _alias(name)
        if alias in _COT_ALIASES:
            _fail("CONDUCTING_COT_FORBIDDEN", "hidden chain-of-thought is not stored")
        if alias in _FORBIDDEN_ALIASES:
            _fail(code, "caller cannot set admission, authority, or derived status")


def _reject_record_forbidden(record: Mapping[str, Any], code: str) -> None:
    _reject_forbidden_names(set(record), code)


def _descriptive(record: Mapping[str, Any], code: str) -> dict[str, Any] | None:
    descriptive: dict[str, Any] = {}
    for key in ("provider", "model"):
        if key in record:
            descriptive[key] = _nonempty(record.get(key), code, key)
    if not descriptive:
        return None
    descriptive["authority"] = False
    return descriptive


def _unique_ids(values: list[str], code: str, label: str) -> list[str]:
    seen: set[str] = set()
    copied: list[str] = []
    for item in values:
        ident = _identity(item, code, label)
        if ident in seen:
            _fail(code, f"{label} repeats an id")
        seen.add(ident)
        copied.append(ident)
    return copied


def _contiguous(orders: list[int], code: str, label: str) -> None:
    if sorted(orders) != list(range(len(orders))):
        _fail(code, f"{label} is not contiguous from 0")
    if len(set(orders)) != len(orders):
        _fail(code, f"{label} repeats an order")


def _rationale(value: Any) -> dict[str, Any]:
    mapping = _require_mapping(value, "rationale")
    _reject_record_forbidden(mapping, "CONDUCTING_SCOPE_VIOLATION")
    _keys(mapping, _RATIONALE_REQUIRED, frozenset(), "CONDUCTING_SOURCE_INVALID")
    claim = _nonempty(mapping.get("claim"), "CONDUCTING_SOURCE_INVALID", "rationale claim")
    attack = _nonempty(
        mapping.get("attack"),
        "CONDUCTING_SOURCE_INVALID",
        "rationale attack",
    )
    raw = _plain_list(
        mapping.get("assumptions"),
        "CONDUCTING_SOURCE_INVALID",
        "rationale assumptions",
    )
    assumptions: list[str] = []
    for item in raw:
        assumptions.append(
            _nonempty(item, "CONDUCTING_SOURCE_INVALID", "rationale assumption")
        )
    return {"claim": claim, "assumptions": assumptions, "attack": attack}


def _assumption_digest(statement: str) -> str:
    return _digest(statement, "CONDUCTING_SOURCE_INVALID")


def _bind_assumption(
    raw: Mapping[str, Any],
    *,
    current_id: str,
    current_order: int,
    parent_open: Mapping[str, Mapping[str, Any]],
    parent_resolved: Mapping[str, Mapping[str, Any]],
    known_revisions: Mapping[str, Mapping[str, Any]],
    known_digests: set[str],
) -> dict[str, Any]:
    _reject_record_forbidden(raw, "CONDUCTING_SCOPE_VIOLATION")
    _keys(raw, _ASSUMPTION_REQUIRED, _ASSUMPTION_OPTIONAL, "CONDUCTING_SOURCE_INVALID")
    statement = _nonempty(raw.get("statement"), "CONDUCTING_SOURCE_INVALID", "statement")
    digest = _assumption_digest(statement)
    if "assumption_digest" in raw:
        stated = _sha256(raw.get("assumption_digest"), "CONDUCTING_SOURCE_INVALID")
        if stated != digest:
            _fail("CONDUCTING_SOURCE_INVALID", "assumption digest does not match")
    introduced = _identity(
        raw.get("introduced_in_revision"),
        "CONDUCTING_REVISION_UNBOUND",
        "introduced_in_revision",
    )
    if introduced not in known_revisions and introduced != current_id:
        _fail("CONDUCTING_REVISION_UNBOUND", "introduced_in_revision is unknown")
    status = raw.get("status")
    if status not in {"OPEN", "RESOLVED"}:
        _fail("CONDUCTING_SOURCE_INVALID", "assumption status is not closed")
    record: dict[str, Any] = {
        "statement": statement,
        "assumption_digest": digest,
        "introduced_in_revision": introduced,
        "status": status,
    }
    if status == "OPEN":
        if "resolved_by_revision" in raw:
            _fail("CONDUCTING_SOURCE_INVALID", "OPEN assumption cannot name a resolver")
        if digest in parent_resolved:
            _fail("CONDUCTING_LINEAGE_INVALID", "resolved assumption cannot reopen")
        if introduced == current_id:
            if digest in parent_open or digest in parent_resolved:
                _fail("CONDUCTING_REPLAY", "assumption digest repeats an introduction")
        else:
            if digest not in parent_open:
                _fail(
                    "CONDUCTING_ASSUMPTION_DROPPED",
                    "carried assumption was not open on the parent",
                )
            parent = parent_open[digest]
            if parent["introduced_in_revision"] != introduced:
                _fail(
                    "CONDUCTING_LINEAGE_INVALID",
                    "introduced_in_revision does not match the parent",
                )
            if parent["statement"] != statement:
                _fail("CONDUCTING_LINEAGE_INVALID", "assumption statement changed")
    else:
        resolver = _identity(
            raw.get("resolved_by_revision"),
            "CONDUCTING_REVISION_UNBOUND",
            "resolved_by_revision",
        )
        if resolver != current_id and digest not in parent_resolved:
            _fail(
                "CONDUCTING_REVISION_UNBOUND",
                "assumption is not resolved by this revision",
            )
        if digest in parent_resolved:
            prior = parent_resolved[digest]
            if prior["resolved_by_revision"] != resolver:
                _fail("CONDUCTING_LINEAGE_INVALID", "resolution lineage mismatch")
            if introduced != prior["introduced_in_revision"]:
                _fail("CONDUCTING_LINEAGE_INVALID", "introduced_in_revision mismatch")
        else:
            if digest not in parent_open:
                _fail(
                    "CONDUCTING_REVISION_UNBOUND",
                    "resolved assumption was not open on the parent",
                )
            if resolver != current_id:
                _fail(
                    "CONDUCTING_REVISION_UNBOUND",
                    "assumption is not resolved by this revision",
                )
            parent = parent_open[digest]
            if parent["introduced_in_revision"] != introduced:
                _fail("CONDUCTING_LINEAGE_INVALID", "introduced_in_revision mismatch")
            introduced_order = known_revisions[introduced]["created_order"]
            if current_order <= introduced_order:
                _fail(
                    "CONDUCTING_REVISION_UNBOUND",
                    "RESOLVED requires a later revision",
                )
        record["resolved_by_revision"] = resolver
    if "resolution_ref" in raw:
        ref = _sha256(raw.get("resolution_ref"), "CONDUCTING_SOURCE_INVALID")
        if ref not in known_digests:
            _fail("CONDUCTING_SOURCE_INVALID", "resolution_ref is not a known digest")
        record["resolution_ref"] = ref
    return record


def _bind_assumptions(
    raw: Any,
    *,
    current_id: str,
    current_order: int,
    parent_state: Mapping[str, Any] | None,
    known_revisions: Mapping[str, Mapping[str, Any]],
    known_digests: set[str],
) -> dict[str, dict[str, Any]]:
    rows = _plain_list(raw, "CONDUCTING_SOURCE_INVALID", "assumptions")
    parent_open: dict[str, Mapping[str, Any]] = {}
    parent_resolved: dict[str, Mapping[str, Any]] = {}
    if parent_state is not None:
        for digest, item in parent_state["assumptions"].items():
            if item["status"] == "OPEN":
                parent_open[digest] = item
            else:
                parent_resolved[digest] = item
    bound: dict[str, dict[str, Any]] = {}
    for item in rows:
        mapping = _require_mapping(item, "assumption")
        record = _bind_assumption(
            mapping,
            current_id=current_id,
            current_order=current_order,
            parent_open=parent_open,
            parent_resolved=parent_resolved,
            known_revisions=known_revisions,
            known_digests=known_digests,
        )
        digest = record["assumption_digest"]
        if digest in bound:
            _fail("CONDUCTING_REPLAY", "assumption digest repeats in a revision")
        bound[digest] = record
    missing = set(parent_open) - set(bound)
    if missing:
        _fail("CONDUCTING_ASSUMPTION_DROPPED", "open assumption was silently dropped")
    return bound


def _challenge_material(record: Mapping[str, Any]) -> dict[str, Any]:
    material = {
        "target_revision_id": record["target_revision_id"],
        "target_content_digest": record["target_content_digest"],
        "challenge_kind": record["challenge_kind"],
        "rationale": record["rationale"],
        "assumptions_attacked": record["assumptions_attacked"],
        "counterexample_present": record["counterexample_present"],
    }
    if record["counterexample_present"]:
        material["counterexample_body"] = record["counterexample_body"]
    return material


def _bind_counterexample(record: Mapping[str, Any]) -> tuple[bool, dict[str, Any] | None, str | None]:
    present = record.get("counterexample_present")
    if type(present) is not bool:
        _fail("CONDUCTING_SOURCE_INVALID", "counterexample_present is not a boolean")
    has_object = "counterexample" in record
    if present and not has_object:
        _fail("CONDUCTING_SOURCE_INVALID", "counterexample object is required")
    if has_object and not present:
        _fail("CONDUCTING_SOURCE_INVALID", "counterexample object is not allowed")
    if not present:
        if "counterexample_digest" in record:
            _fail("CONDUCTING_SOURCE_INVALID", "counterexample digest is not allowed")
        return False, None, None
    counter = _require_mapping(record.get("counterexample"), "counterexample")
    _keys(
        counter,
        _COUNTEREXAMPLE_REQUIRED,
        frozenset(),
        "CONDUCTING_SOURCE_INVALID",
    )
    body = counter.get("body")
    if body is None:
        _fail("CONDUCTING_SOURCE_INVALID", "counterexample body is required")
    digest = _digest(body, "CONDUCTING_CHALLENGE_UNBOUND")
    if "counterexample_digest" in record:
        stated = _sha256(record.get("counterexample_digest"), "CONDUCTING_CHALLENGE_UNBOUND")
        if stated != digest:
            _fail("CONDUCTING_CHALLENGE_UNBOUND", "counterexample digest does not match")
    return True, body, digest


def _bind_revision(
    raw: Mapping[str, Any],
    *,
    claim_id: str | None,
    known: dict[str, dict[str, Any]],
    challenges: Mapping[str, Mapping[str, Any]],
    known_digests: set[str],
    content_digests: dict[str, str],
) -> dict[str, Any]:
    _reject_record_forbidden(raw, "CONDUCTING_SCOPE_VIOLATION")
    _keys(raw, _REVISION_REQUIRED, _REVISION_OPTIONAL, "CONDUCTING_SOURCE_INVALID")
    revision_id = _identity(raw.get("revision_id"), "CONDUCTING_REVISION_UNBOUND", "revision_id")
    if revision_id in known:
        _fail("CONDUCTING_REPLAY", "revision_id repeats")
    created_order = _order(raw.get("created_order"), "CONDUCTING_LINEAGE_INVALID", "created_order")
    event_order = _order(raw.get("event_order"), "CONDUCTING_LINEAGE_INVALID", "event_order")
    agent_id = _nonempty(raw.get("agent_id"), "CONDUCTING_SOURCE_INVALID", "agent_id")
    role = raw.get("agent_role")
    content = raw.get("content")
    digest = _digest(content, "CONDUCTING_REVISION_UNBOUND")
    if "content_digest" in raw:
        stated = _sha256(raw.get("content_digest"), "CONDUCTING_REVISION_UNBOUND")
        if stated != digest:
            _fail("CONDUCTING_REVISION_UNBOUND", "content_digest does not match")
    if digest in content_digests:
        _fail("CONDUCTING_REPLAY", "revision content repeats under a new identity")
    parent_id = None
    parent_digest = None
    parent_state = None
    responds: list[str] = []
    if created_order == 0:
        if role != "PROPOSER":
            _fail("CONDUCTING_SOURCE_INVALID", "r0 agent_role must be PROPOSER")
        if event_order != 0:
            _fail("CONDUCTING_LINEAGE_INVALID", "proposal must be event_order 0")
        if "parent_revision_id" in raw or "parent_content_digest" in raw:
            _fail("CONDUCTING_LINEAGE_INVALID", "r0 cannot name a parent")
        if "responds_to" in raw:
            extra = raw.get("responds_to")
            if extra not in (None, [], ()):
                _fail("CONDUCTING_LINEAGE_INVALID", "r0 cannot respond to a challenge")
    else:
        if role != "REVISER":
            _fail("CONDUCTING_SOURCE_INVALID", "later agent_role must be REVISER")
        parent_id = _identity(
            raw.get("parent_revision_id"),
            "CONDUCTING_REVISION_UNBOUND",
            "parent_revision_id",
        )
        if parent_id == revision_id:
            _fail("CONDUCTING_LINEAGE_INVALID", "revision cannot parent itself")
        if parent_id not in known:
            _fail("CONDUCTING_REVISION_UNBOUND", "parent revision is unknown")
        parent_state = known[parent_id]
        if parent_state["event_order"] >= event_order:
            _fail("CONDUCTING_LINEAGE_INVALID", "parent is not earlier than the revision")
        parent_digest = _sha256(
            raw.get("parent_content_digest"),
            "CONDUCTING_REVISION_UNBOUND",
        )
        if parent_digest != parent_state["content_digest"]:
            _fail("CONDUCTING_REVISION_UNBOUND", "parent_content_digest does not match")
        raw_responds = raw.get("responds_to")
        if type(raw_responds) is not list or not raw_responds:
            _fail("CONDUCTING_SOURCE_INVALID", "responds_to must be a nonempty list")
        responds = _unique_ids(raw_responds, "CONDUCTING_CHALLENGE_UNBOUND", "responds_to")
        for challenge_id in responds:
            if challenge_id not in challenges:
                _fail("CONDUCTING_CHALLENGE_UNBOUND", "responds_to names an unknown challenge")
            challenge = challenges[challenge_id]
            if challenge["event_order"] >= event_order:
                _fail(
                    "CONDUCTING_LINEAGE_INVALID",
                    "revision cannot answer a later challenge",
                )
            if challenge["target_revision_id"] != parent_id:
                _fail(
                    "CONDUCTING_CHALLENGE_UNBOUND",
                    "challenge does not target the parent revision",
                )
            if challenge["target_content_digest"] != parent_digest:
                _fail(
                    "CONDUCTING_CHALLENGE_UNBOUND",
                    "challenge is not bound to the parent bytes",
                )
    local_claim = None
    if "claim_id" in raw:
        local_claim = _nonempty(raw.get("claim_id"), "CONDUCTING_SOURCE_INVALID", "claim_id")
        if claim_id is not None and local_claim != claim_id:
            _fail("CONDUCTING_SOURCE_INVALID", "claim_id does not match the exchange")
    known[revision_id] = {
        "created_order": created_order,
        "event_order": event_order,
        "content_digest": digest,
        "assumptions": {},
    }
    assumptions = _bind_assumptions(
        raw.get("assumptions"),
        current_id=revision_id,
        current_order=created_order,
        parent_state=parent_state,
        known_revisions=known,
        known_digests=known_digests,
    )
    known[revision_id]["assumptions"] = assumptions
    bound: dict[str, Any] = {
        "revision_id": revision_id,
        "content": content,
        "content_digest": digest,
        "created_order": created_order,
        "event_order": event_order,
        "agent_id": agent_id,
        "agent_role": role,
        "assumptions": [dict(item) for item in assumptions.values()],
    }
    if parent_id is not None:
        bound["parent_revision_id"] = parent_id
        bound["parent_content_digest"] = parent_digest
        bound["responds_to"] = list(responds)
    if local_claim is not None:
        bound["claim_id"] = local_claim
    descriptive = _descriptive(raw, "CONDUCTING_SOURCE_INVALID")
    if descriptive is not None:
        bound["descriptive"] = descriptive
    content_digests[digest] = revision_id
    known_digests.add(digest)
    return bound


def _bind_challenge(
    raw: Mapping[str, Any],
    *,
    revisions: Mapping[str, Mapping[str, Any]],
    challenge_digests: dict[str, str],
    counterexample_digests: dict[str, str],
    known_digests: set[str],
) -> dict[str, Any]:
    _reject_record_forbidden(raw, "CONDUCTING_SCOPE_VIOLATION")
    _keys(raw, _CHALLENGE_REQUIRED, _CHALLENGE_OPTIONAL, "CONDUCTING_SOURCE_INVALID")
    challenge_id = _identity(
        raw.get("challenge_id"),
        "CONDUCTING_CHALLENGE_UNBOUND",
        "challenge_id",
    )
    created_order = _order(raw.get("created_order"), "CONDUCTING_LINEAGE_INVALID", "created_order")
    event_order = _order(raw.get("event_order"), "CONDUCTING_LINEAGE_INVALID", "event_order")
    target_id = _identity(
        raw.get("target_revision_id"),
        "CONDUCTING_CHALLENGE_UNBOUND",
        "target_revision_id",
    )
    if target_id not in revisions:
        _fail("CONDUCTING_CHALLENGE_UNBOUND", "target revision is unknown")
    target = revisions[target_id]
    if target["event_order"] >= event_order:
        _fail("CONDUCTING_LINEAGE_INVALID", "challenge is not later than its target")
    target_digest = _sha256(
        raw.get("target_content_digest"),
        "CONDUCTING_CHALLENGE_UNBOUND",
    )
    if target_digest != target["content_digest"]:
        _fail("CONDUCTING_CHALLENGE_UNBOUND", "target_content_digest does not match")
    if raw.get("agent_role") != "CHALLENGER":
        _fail("CONDUCTING_SOURCE_INVALID", "challenge agent_role must be CHALLENGER")
    kind = raw.get("challenge_kind")
    if kind not in _CHALLENGE_KINDS:
        _fail("CONDUCTING_SOURCE_INVALID", "challenge_kind is not closed")
    rationale = _rationale(raw.get("rationale"))
    present, body, counter_digest = _bind_counterexample(raw)
    attacked_raw = _plain_list(
        raw.get("assumptions_attacked"),
        "CONDUCTING_SOURCE_INVALID",
        "assumptions_attacked",
    )
    attacked = _unique_ids(
        attacked_raw,
        "CONDUCTING_CHALLENGE_UNBOUND",
        "assumptions_attacked",
    )
    known_assumptions = {
        digest
        for digest, item in target["assumptions"].items()
        if item["status"] == "OPEN"
    }
    for digest in attacked:
        _sha256(digest, "CONDUCTING_CHALLENGE_UNBOUND")
        if digest not in known_assumptions:
            _fail(
                "CONDUCTING_CHALLENGE_UNBOUND",
                "assumptions_attacked is not open on the target",
            )
    if kind == "ASSUMPTION_ATTACK" and not attacked:
        _fail("CONDUCTING_SOURCE_INVALID", "ASSUMPTION_ATTACK requires assumptions_attacked")
    bound = {
        "challenge_id": challenge_id,
        "target_revision_id": target_id,
        "target_content_digest": target_digest,
        "challenger_id": _nonempty(
            raw.get("challenger_id"),
            "CONDUCTING_SOURCE_INVALID",
            "challenger_id",
        ),
        "agent_role": "CHALLENGER",
        "challenge_kind": kind,
        "rationale": rationale,
        "assumptions_attacked": attacked,
        "counterexample_present": present,
        "created_order": created_order,
        "event_order": event_order,
    }
    if present:
        bound["counterexample_body"] = body
        bound["counterexample"] = {"body": body}
        bound["counterexample_digest"] = counter_digest
        if counter_digest in counterexample_digests:
            _fail("CONDUCTING_REPLAY", "counterexample digest repeats")
        counterexample_digests[counter_digest] = challenge_id
        known_digests.add(counter_digest)
    material = _challenge_material(bound)
    digest = _digest(material, "CONDUCTING_CHALLENGE_UNBOUND")
    if "challenge_digest" in raw:
        stated = _sha256(raw.get("challenge_digest"), "CONDUCTING_CHALLENGE_UNBOUND")
        if stated != digest:
            _fail("CONDUCTING_CHALLENGE_UNBOUND", "challenge_digest does not match")
    if digest in challenge_digests:
        _fail("CONDUCTING_REPLAY", "challenge content repeats under a new identity")
    bound["challenge_digest"] = digest
    if _digest(rationale, "CONDUCTING_CHALLENGE_UNBOUND") == target_digest:
        result = "INVALID_CHALLENGE"
    elif present:
        result = "COUNTEREXAMPLE_FOUND"
    else:
        result = "NO_COUNTEREXAMPLE_FOUND"
    if result not in _CHALLENGE_RESULTS:
        _fail("CONDUCTING_SOURCE_INVALID", "challenge result is not closed")
    bound["result"] = result
    descriptive = _descriptive(raw, "CONDUCTING_SOURCE_INVALID")
    if descriptive is not None:
        bound["descriptive"] = descriptive
    challenge_digests[digest] = challenge_id
    known_digests.add(digest)
    return bound


def _bind_selection(
    raw: Any,
    revisions: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], str]:
    if raw is None:
        return {"selection_present": False}, "NO_HUMAN_SELECTION"
    mapping = _require_mapping(raw, "human_selection")
    _reject_record_forbidden(mapping, "CONDUCTING_SCOPE_VIOLATION")
    _keys(mapping, _SELECTION_REQUIRED, _SELECTION_OPTIONAL, "CONDUCTING_SOURCE_INVALID")
    if mapping.get("authority", False) is not False:
        _fail("CONDUCTING_SCOPE_VIOLATION", "human selection cannot carry authority")
    if mapping.get("selector_is_human") is not True or type(
        mapping.get("selector_is_human")
    ) is not bool:
        _fail("CONDUCTING_SELECTION_UNBOUND", "selector_is_human must be true")
    selected_id = _identity(
        mapping.get("selected_revision_id"),
        "CONDUCTING_SELECTION_UNBOUND",
        "selected_revision_id",
    )
    if selected_id not in revisions:
        _fail("CONDUCTING_SELECTION_UNBOUND", "selected revision is unknown")
    selected_digest = _sha256(
        mapping.get("selected_content_digest"),
        "CONDUCTING_SELECTION_UNBOUND",
    )
    if selected_digest != revisions[selected_id]["content_digest"]:
        _fail("CONDUCTING_SELECTION_UNBOUND", "selected_content_digest does not match")
    bound: dict[str, Any] = {
        "selection_present": True,
        "selected_revision_id": selected_id,
        "selected_content_digest": selected_digest,
        "selector_is_human": True,
        "authority": False,
    }
    if "selection_note" in mapping:
        note = mapping.get("selection_note")
        if type(note) is not str:
            _fail("CONDUCTING_SOURCE_INVALID", "selection_note must be a string")
        bound["selection_note"] = note
    return bound, "REVISION_SELECTED"


def _sequence_status(
    revisions: list[Mapping[str, Any]],
    challenges: list[Mapping[str, Any]],
) -> str:
    valid = [item for item in challenges if item["result"] != "INVALID_CHALLENGE"]
    if not valid:
        return "INCOMPLETE_SEQUENCE"
    valid_ids = {item["challenge_id"] for item in valid}
    for item in revisions:
        responds = item.get("responds_to") or []
        if any(challenge_id in valid_ids for challenge_id in responds):
            return "COMPLETE_SEQUENCE"
    return "INCOMPLETE_SEQUENCE"


def _counterexample_status(
    revisions: list[Mapping[str, Any]],
    challenges: list[Mapping[str, Any]],
) -> str:
    found = [
        item for item in challenges if item["result"] == "COUNTEREXAMPLE_FOUND"
    ]
    if not found:
        return "NO_COUNTEREXAMPLE"
    addressed: set[str] = set()
    for item in revisions:
        for challenge_id in item.get("responds_to") or []:
            addressed.add(challenge_id)
    if all(item["challenge_id"] in addressed for item in found):
        return "COUNTEREXAMPLE_ADDRESSED"
    return "COUNTEREXAMPLE_OPEN"


def _assumption_history(
    revisions: list[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    latest: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for revision in revisions:
        for item in revision["assumptions"]:
            digest = item["assumption_digest"]
            if digest not in latest:
                order.append(digest)
            latest[digest] = dict(item)
    records = [latest[digest] for digest in order]
    unresolved = [
        item["assumption_digest"] for item in records if item["status"] == "OPEN"
    ]
    return records, unresolved


def _emit_challenge(record: Mapping[str, Any]) -> dict[str, Any]:
    emitted = {
        "challenge_id": record["challenge_id"],
        "target_revision_id": record["target_revision_id"],
        "target_content_digest": record["target_content_digest"],
        "challenger_id": record["challenger_id"],
        "agent_role": record["agent_role"],
        "challenge_kind": record["challenge_kind"],
        "rationale": record["rationale"],
        "challenge_digest": record["challenge_digest"],
        "counterexample_present": record["counterexample_present"],
        "assumptions_attacked": list(record["assumptions_attacked"]),
        "result": record["result"],
        "created_order": record["created_order"],
        "event_order": record["event_order"],
    }
    if record["counterexample_present"]:
        emitted["counterexample"] = {"body": record["counterexample_body"]}
        emitted["counterexample_digest"] = record["counterexample_digest"]
    if "descriptive" in record:
        emitted["descriptive"] = record["descriptive"]
    return emitted


def build_conducting_receipt(exchange: Mapping[str, Any], **forbidden: Any) -> dict[str, Any]:
    """Return a non-authoritative conducting receipt.

    Human selection, challenge results, and sequence status are local. They
    do not admit independent evidence or create Human Final.
    """
    if forbidden:
        _reject_forbidden_names(set(forbidden), "CONDUCTING_SCOPE_VIOLATION")
        _fail("CONDUCTING_SOURCE_INVALID", "unexpected conducting input")
    mapping = _snapshot(_require_mapping(exchange, "exchange"))
    _scan_cot(mapping)
    _reject_forbidden_names(set(mapping), "CONDUCTING_SCOPE_VIOLATION")
    _keys(mapping, _EXCHANGE_REQUIRED, _EXCHANGE_OPTIONAL, "CONDUCTING_SOURCE_INVALID")
    session_id = _nonempty(mapping.get("session_id"), "CONDUCTING_SOURCE_INVALID", "session_id")
    claim_id = None
    if "target_claim_id" in mapping:
        claim_id = _nonempty(
            mapping.get("target_claim_id"),
            "CONDUCTING_SOURCE_INVALID",
            "target_claim_id",
        )
    target_artifact = None
    if "target_artifact_digest" in mapping:
        target_artifact = _sha256(
            mapping.get("target_artifact_digest"),
            "CONDUCTING_REVISION_UNBOUND",
        )
    raw_revisions = mapping.get("revisions")
    if type(raw_revisions) is not list or not raw_revisions:
        _fail("CONDUCTING_SOURCE_INVALID", "revisions must be a nonempty list")
    raw_challenges = mapping.get("challenges")
    if type(raw_challenges) is not list:
        _fail("CONDUCTING_SOURCE_INVALID", "challenges must be a list")
    revision_rows = [_require_mapping(item, "revision") for item in raw_revisions]
    challenge_rows = [_require_mapping(item, "challenge") for item in raw_challenges]
    events: list[tuple[str, Mapping[str, Any]]] = []
    for item in revision_rows:
        events.append(
            (
                "revision",
                item,
            )
        )
    for item in challenge_rows:
        events.append(("challenge", item))
    event_orders = [
        _order(item[1].get("event_order"), "CONDUCTING_LINEAGE_INVALID", "event_order")
        for item in events
    ]
    _contiguous(event_orders, "CONDUCTING_LINEAGE_INVALID", "event_order")
    events.sort(key=lambda item: item[1]["event_order"])
    known_revisions: dict[str, dict[str, Any]] = {}
    bound_revisions: dict[str, dict[str, Any]] = {}
    bound_challenges: dict[str, dict[str, Any]] = {}
    content_digests: dict[str, str] = {}
    challenge_digests: dict[str, str] = {}
    counterexample_digests: dict[str, str] = {}
    known_digests: set[str] = set()
    for kind, item in events:
        if kind == "revision":
            bound = _bind_revision(
                item,
                claim_id=claim_id,
                known=known_revisions,
                challenges=bound_challenges,
                known_digests=known_digests,
                content_digests=content_digests,
            )
            bound_revisions[bound["revision_id"]] = bound
        else:
            bound_c = _bind_challenge(
                item,
                revisions=known_revisions,
                challenge_digests=challenge_digests,
                counterexample_digests=counterexample_digests,
                known_digests=known_digests,
            )
            if bound_c["challenge_id"] in bound_challenges:
                _fail("CONDUCTING_REPLAY", "challenge_id repeats")
            bound_challenges[bound_c["challenge_id"]] = bound_c
    revision_list = sorted(bound_revisions.values(), key=lambda item: item["created_order"])
    challenge_list = sorted(
        bound_challenges.values(),
        key=lambda item: item["created_order"],
    )
    _contiguous(
        [item["created_order"] for item in revision_list],
        "CONDUCTING_LINEAGE_INVALID",
        "revision created_order",
    )
    if challenge_list:
        _contiguous(
            [item["created_order"] for item in challenge_list],
            "CONDUCTING_LINEAGE_INVALID",
            "challenge created_order",
        )
    if revision_list[0]["created_order"] != 0 or revision_list[0]["agent_role"] != "PROPOSER":
        _fail("CONDUCTING_LINEAGE_INVALID", "proposal r0 is missing")
    selection, selection_status = _bind_selection(
        mapping.get("human_selection"),
        bound_revisions,
    )
    assumption_records, unresolved = _assumption_history(revision_list)
    emitted_challenges = [_emit_challenge(item) for item in challenge_list]
    receipt: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "authority": False,
        "session_id": session_id,
        "proposal": dict(revision_list[0]),
        "challenges": emitted_challenges,
        "revisions": [dict(item) for item in revision_list],
        "human_selection": selection,
        "assumption_records": assumption_records,
        "unresolved_assumptions": unresolved,
        "sequence_status": _sequence_status(revision_list, challenge_list),
        "counterexample_status": _counterexample_status(revision_list, emitted_challenges),
        "selection_status": selection_status,
        "limitations": list(_LIMITATIONS),
    }
    if claim_id is not None:
        receipt["target_claim_id"] = claim_id
    if target_artifact is not None:
        receipt["target_artifact_digest"] = target_artifact
    receipt["receipt_digest"] = _digest(
        {key: value for key, value in receipt.items()},
        "CONDUCTING_SOURCE_INVALID",
    )
    return receipt
