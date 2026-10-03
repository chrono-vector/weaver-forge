"""Derive a non-authoritative evidence/provenance graph.

The DAG cites caller-owned snapshots of closed receipts, claims, and artifacts
by recomputed digest. It does not admit evidence, execute, or create Human Final.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from audit_lifecycle.epistemic.serialize import canonical_digest

SCHEMA_VERSION = "evidence_binding_dag.v0"
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
        "production",
        "same as above",
    }
)

NODE_KINDS = frozenset({"RECEIPT", "CLAIM", "ARTIFACT", "EXTERNAL_REF"})
RECEIPT_SCHEMAS = frozenset(
    {
        "tested_envelope.v0",
        "recovery_preflight.v0",
        "independent_verification_preflight.v0",
        "conducting_receipt.v0",
        "recovery_execution_receipt.v0",
    }
)
RECEIPT_WITH_SELF_DIGEST = frozenset(
    {
        "conducting_receipt.v0",
        "recovery_execution_receipt.v0",
    }
)
CLAIM_SCHEMA = "r4.epistemic.claim.v1"
CLAIM_KINDS = frozenset(
    {
        "DOCUMENT_IDENTITY",
        "FORMAL",
        "IMPLEMENTATION",
        "EMPIRICAL",
        "NORMATIVE",
        "SYMBOLIC",
        "HISTORICAL",
    }
)
EPISTEMIC_STATUSES = frozenset(
    {
        "REPORTED",
        "SPECIFIED",
        "OBSERVED",
        "REPRODUCED",
        "VERIFIED_SCOPE",
        "AMBIGUOUS",
        "UNRESOLVED",
    }
)
RELATIONS = frozenset(
    {"DEPENDS_ON", "BOUNDS", "SUCCESSOR_OF", "CITES", "CONTRADICTS"}
)
DEPENDENCY_RELATIONS = frozenset({"DEPENDS_ON", "BOUNDS", "SUCCESSOR_OF"})
FORBIDDEN_RELATIONS = frozenset(
    {
        "SUPPORTS",
        "OBSERVES",
        "CHALLENGES",
        "RESPONDS_TO",
        "SELECTS",
        "SUPERSEDES",
        "DOES_NOT_ESTABLISH",
        "VERIFIES",
    }
)
FORBIDDEN_NODE_KINDS = frozenset(
    {"CHALLENGE", "REVISION", "HUMAN_SELECTION", "ATTEMPT", "CHECK"}
)

_TE_REQUIRED = frozenset(
    {
        "schema_version",
        "authority",
        "claim_id",
        "artifact_revision",
        "source_result",
        "result",
        "detector_families",
        "scope_binding",
        "exclusions",
        "unresolved_assumptions",
        "missing_observations",
    }
)
_TE_OPTIONAL = frozenset(
    {"broader_classification", "counterexample_count", "annotations"}
)
_RP_REQUIRED = frozenset(
    {
        "schema_version",
        "authority",
        "recovered",
        "classification",
        "cited_decision",
        "limitations",
    }
)
_RP_OPTIONAL = frozenset(
    {
        "revalidation_observation",
        "rejected_terminals",
        "digest_observation",
        "annotations",
    }
)
_IVP_REQUIRED = frozenset(
    {
        "schema_version",
        "authority",
        "admission_status",
        "verification_kind",
        "claim_id",
        "artifact_revision_binding",
        "classification",
        "structural_candidate",
        "source_execution_summary",
        "independent_execution_summary",
        "limitations",
    }
)
_IVP_OPTIONAL = frozenset({"observer", "descriptive", "annotations"})
_CR_REQUIRED = frozenset(
    {
        "schema_version",
        "authority",
        "session_id",
        "proposal",
        "challenges",
        "revisions",
        "human_selection",
        "assumption_records",
        "unresolved_assumptions",
        "sequence_status",
        "counterexample_status",
        "selection_status",
        "limitations",
        "receipt_digest",
    }
)
_CR_OPTIONAL = frozenset({"target_claim_id", "target_artifact_digest"})
_RER_REQUIRED = frozenset(
    {
        "schema_version",
        "authority",
        "recovered",
        "recovery_session_id",
        "target_scope",
        "target_artifact_id",
        "target_environment",
        "pre_state",
        "stop",
        "isolation",
        "restore_target",
        "attempts",
        "independent_verification_refs",
        "unresolved_risks",
        "classification",
        "limitations",
        "receipt_digest",
    }
)
_RER_OPTIONAL = frozenset({"human_review"})
_CLAIM_REQUIRED = frozenset(
    {
        "schema_version",
        "claim_id",
        "statement",
        "claim_kind",
        "epistemic_status",
        "scope",
        "authority",
    }
)
_CLAIM_OPTIONAL = frozenset(
    {
        "evidence_refs",
        "provenance_refs",
        "notes",
        "confidence",
        "workflow_state",
        "extra",
    }
)
_NODE_REQUIRED = frozenset({"node_id", "kind"})
_NODE_OPTIONAL = frozenset(
    {
        "body",
        "digest",
        "label",
        "source_hint",
        "node_digest",
        "artifact_id",
        "immutable_version",
    }
)
_EDGE_REQUIRED = frozenset({"edge_id", "relation", "basis"})
_EDGE_OPTIONAL = frozenset(
    {
        "source_node_id",
        "target_node_id",
        "source_digest",
        "target_digest",
        "rationale_body",
        "rationale_digest",
    }
)
_INPUT_REQUIRED = frozenset({"nodes"})
_INPUT_OPTIONAL = frozenset({"edges"})
_LIMITATIONS = (
    "structural completeness is not verification",
    "citations are not admission",
    "contradiction recording does not resolve contradiction",
    "label-only refs are unresolved for identity purposes",
    "source-local PASS/RECOVERED_BOUNDED/etc remain local only",
    "Human Final citations do not affect technical status",
    "unknown schemas are not recognized as RECEIPT",
    "v0 does not expose internal receipt subrecords as nodes",
    "no execution/orchestration/admission occurs",
)
_FORBIDDEN_ALIASES = frozenset(
    {
        "pass",
        "safe",
        "trusted",
        "verified",
        "recovered",
        "accepted",
        "humanreviewaccepted",
        "humanfinal",
        "humanfinalstatus",
        "ishumanfinal",
        "createshumanfinal",
        "promotestohumanfinal",
        "admissionstatus",
        "independentevidencecount",
        "structuralcandidate",
        "claimsiwacceptance",
        "claimsindependentwitness",
        "structurestatus",
        "contradictionpresent",
        "dagdigest",
        "graphcomplete",
        "graphincomplete",
        "canonical",
        "published",
        "deployed",
        "vector",
        "eig",
        "proventrue",
        "majority",
        "winner",
        "consensus",
    }
)
_EXTERNAL_REF_FORBIDDEN = frozenset(
    {
        "schema_version",
        "classification",
        "result",
        "authority",
        "receipt_digest",
        "body",
        "admission_status",
        "recovered",
    }
)


class EvidenceBindingDagError(ValueError):
    """Closed failure while deriving an evidence binding DAG."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _fail(code: str, message: str) -> None:
    raise EvidenceBindingDagError(code, message)


def _alias(name: str) -> str:
    return "".join(char for char in name.lower() if char.isalnum())


def _snapshot(value: Any, depth: int = 0) -> Any:
    """Copy caller values once into exact built-in containers and leaves."""
    if depth > 32:
        _fail("DAG_SOURCE_INVALID", "input is nested too deeply")
    if value is None or type(value) in _LEAF_TYPES:
        return value
    if isinstance(value, Mapping):
        copied: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("DAG_SOURCE_INVALID", "mapping key must be a string")
            if key in copied:
                _fail("DAG_SOURCE_INVALID", "mapping repeats a key")
            copied[key] = _snapshot(item, depth + 1)
        return copied
    if type(value) is list or type(value) is tuple:
        return [_snapshot(item, depth + 1) for item in value]
    _fail("DAG_SOURCE_INVALID", "input is not plain JSON data")


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if isinstance(value, bool) or not isinstance(value, Mapping):
        _fail("DAG_SOURCE_INVALID", f"{label} must be a mapping")
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


def _sha256(value: Any, code: str, label: str = "digest") -> str:
    if type(value) is not str or len(value) != _SHA256_WIDTH:
        _fail(code, f"{label} is not a bound sha256")
    if any(char not in _HEX for char in value):
        _fail(code, f"{label} is not a bound sha256")
    if _unpinned(value):
        _fail(code, f"{label} is not a bound sha256")
    return value


def _digest(value: Any, code: str) -> str:
    try:
        return canonical_digest(value)
    except (TypeError, ValueError):
        _fail(code, "canonical digest could not be computed")
        raise


def _authority_false(record: Mapping[str, Any], code: str) -> None:
    if "authority" not in record or record.get("authority") is not False:
        _fail(code, "authority must be boolean false")
    if type(record.get("authority")) is not bool:
        _fail(code, "authority must be boolean false")


def _reject_forbidden(forbidden: Mapping[str, Any]) -> None:
    if not forbidden:
        return
    for name in forbidden:
        alias = _alias(name)
        if alias in _FORBIDDEN_ALIASES:
            _fail("DAG_FORBIDDEN", "caller cannot assert DAG-level verdicts")
        _fail("DAG_SOURCE_INVALID", "unexpected DAG input")


def _plain_list(raw: Any, code: str, label: str) -> list[Any]:
    if type(raw) is not list:
        _fail(code, f"{label} must be a list")
    return raw


class _Node:
    __slots__ = (
        "node_id",
        "kind",
        "body",
        "node_digest",
        "source_reported_digest",
        "schema_version",
        "digest",
        "label",
        "source_hint",
        "artifact_id",
        "immutable_version",
    )

    def __init__(self) -> None:
        self.node_id = ""
        self.kind = ""
        self.body: dict[str, Any] | None = None
        self.node_digest = ""
        self.source_reported_digest: str | None = None
        self.schema_version: str | None = None
        self.digest: str | None = None
        self.label: str | None = None
        self.source_hint: str | None = None
        self.artifact_id: str | None = None
        self.immutable_version: str | None = None

    @property
    def body_backed(self) -> bool:
        return self.kind in {"RECEIPT", "CLAIM", "ARTIFACT"}


class _Edge:
    __slots__ = (
        "edge_id",
        "relation",
        "source_digest",
        "target_digest",
        "basis",
        "rationale_body",
        "rationale_digest",
        "edge_digest",
    )

    def __init__(self) -> None:
        self.edge_id = ""
        self.relation = ""
        self.source_digest = ""
        self.target_digest = ""
        self.basis = ""
        self.rationale_body: dict[str, Any] | None = None
        self.rationale_digest: str | None = None
        self.edge_digest = ""


class _RequiredRef:
    __slots__ = ("source_node_digest", "source_path", "digest", "relations")

    def __init__(
        self,
        source_node_digest: str,
        source_path: str,
        digest: str,
        relations: tuple[str, ...],
    ) -> None:
        self.source_node_digest = source_node_digest
        self.source_path = source_path
        self.digest = digest
        self.relations = relations


class _LabelRef:
    __slots__ = ("source_node_digest", "source_path", "label", "label_kind")

    def __init__(
        self,
        source_node_digest: str,
        source_path: str,
        label: str,
        label_kind: str,
    ) -> None:
        self.source_node_digest = source_node_digest
        self.source_path = source_path
        self.label = label
        self.label_kind = label_kind


def _validate_te(body: Mapping[str, Any]) -> None:
    _keys(body, _TE_REQUIRED, _TE_OPTIONAL, "DAG_RECEIPT_INVALID")
    _authority_false(body, "DAG_RECEIPT_INVALID")
    if "receipt_digest" in body:
        _fail("DAG_RECEIPT_INVALID", "tested_envelope.v0 cannot carry receipt_digest")
    if type(body.get("claim_id")) is not str or not body["claim_id"].strip():
        _fail("DAG_RECEIPT_INVALID", "claim_id is missing")
    revision = body.get("artifact_revision")
    if type(revision) is not dict:
        _fail("DAG_RECEIPT_INVALID", "artifact_revision is not a record")
    files = revision.get("files")
    if type(files) is not list or not files:
        _fail("DAG_RECEIPT_INVALID", "artifact_revision files are missing")
    for item in files:
        if type(item) is not dict:
            _fail("DAG_RECEIPT_INVALID", "artifact_revision file is not a record")
        _sha256(item.get("sha256"), "DAG_RECEIPT_INVALID", "file sha256")
        if type(item.get("relative_path")) is not str or not item["relative_path"].strip():
            _fail("DAG_RECEIPT_INVALID", "file relative_path is missing")
    if "expected_sha256" in revision and revision.get("expected_sha256") is not None:
        _sha256(revision.get("expected_sha256"), "DAG_RECEIPT_INVALID", "expected_sha256")
    binding = body.get("scope_binding")
    if type(binding) is not dict:
        _fail("DAG_RECEIPT_INVALID", "scope_binding is not a record")
    if type(binding.get("claim_id")) is not str or not binding["claim_id"].strip():
        _fail("DAG_RECEIPT_INVALID", "scope_binding.claim_id is missing")
    _sha256(binding.get("scope_digest"), "DAG_RECEIPT_INVALID", "scope_digest")
    if type(body.get("detector_families")) is not list:
        _fail("DAG_RECEIPT_INVALID", "detector_families must be a list")
    if type(body.get("result")) is not str:
        _fail("DAG_RECEIPT_INVALID", "result is missing")


def _validate_rp(body: Mapping[str, Any]) -> None:
    _keys(body, _RP_REQUIRED, _RP_OPTIONAL, "DAG_RECEIPT_INVALID")
    _authority_false(body, "DAG_RECEIPT_INVALID")
    if "receipt_digest" in body:
        _fail("DAG_RECEIPT_INVALID", "recovery_preflight.v0 cannot carry receipt_digest")
    if body.get("recovered") is not False or type(body.get("recovered")) is not bool:
        _fail("DAG_RECEIPT_INVALID", "recovered must remain false")
    cited = body.get("cited_decision")
    if type(cited) is not dict:
        _fail("DAG_RECEIPT_INVALID", "cited_decision is not a record")
    if type(cited.get("claim_id")) is not str or not cited["claim_id"].strip():
        _fail("DAG_RECEIPT_INVALID", "cited_decision.claim_id is missing")
    observation = body.get("digest_observation")
    if observation is not None:
        if type(observation) is not dict:
            _fail("DAG_RECEIPT_INVALID", "digest_observation is not a record")
        if "prior_integrity_digest" in observation:
            _sha256(
                observation.get("prior_integrity_digest"),
                "DAG_RECEIPT_INVALID",
                "prior_integrity_digest",
            )
        if "digest" in observation:
            _sha256(observation.get("digest"), "DAG_RECEIPT_INVALID", "digest")


def _validate_ivp(body: Mapping[str, Any]) -> None:
    _keys(body, _IVP_REQUIRED, _IVP_OPTIONAL, "DAG_RECEIPT_INVALID")
    _authority_false(body, "DAG_RECEIPT_INVALID")
    if "receipt_digest" in body:
        _fail(
            "DAG_RECEIPT_INVALID",
            "independent_verification_preflight.v0 cannot carry receipt_digest",
        )
    if type(body.get("claim_id")) is not str or not body["claim_id"].strip():
        _fail("DAG_RECEIPT_INVALID", "claim_id is missing")
    revision = body.get("artifact_revision_binding")
    if type(revision) is not dict:
        _fail("DAG_RECEIPT_INVALID", "artifact_revision_binding is not a record")
    files = revision.get("files")
    if type(files) is not list or not files:
        _fail("DAG_RECEIPT_INVALID", "artifact_revision_binding files are missing")
    for item in files:
        if type(item) is not dict:
            _fail("DAG_RECEIPT_INVALID", "revision file is not a record")
        _sha256(item.get("sha256"), "DAG_RECEIPT_INVALID", "file sha256")
    if "expected_sha256" in revision and revision.get("expected_sha256") is not None:
        _sha256(revision.get("expected_sha256"), "DAG_RECEIPT_INVALID", "expected_sha256")
    for key in ("source_execution_summary", "independent_execution_summary"):
        summary = body.get(key)
        if type(summary) is not dict:
            _fail("DAG_RECEIPT_INVALID", f"{key} is not a record")
        if "evidence_digest" in summary:
            _sha256(summary.get("evidence_digest"), "DAG_RECEIPT_INVALID", "evidence_digest")
        if "input_digest" in summary:
            _sha256(summary.get("input_digest"), "DAG_RECEIPT_INVALID", "input_digest")


def _validate_self_digest(body: Mapping[str, Any], schema: str) -> str:
    if "receipt_digest" not in body:
        _fail("DAG_RECEIPT_INVALID", f"{schema} requires receipt_digest")
    reported = _sha256(body.get("receipt_digest"), "DAG_RECEIPT_INVALID", "receipt_digest")
    stripped = {key: value for key, value in body.items() if key != "receipt_digest"}
    recomputed = _digest(stripped, "DAG_RECEIPT_INVALID")
    if reported != recomputed:
        _fail("DAG_RECEIPT_INVALID", "source-reported receipt_digest does not match")
    return reported


def _validate_cr(body: Mapping[str, Any]) -> str:
    _keys(body, _CR_REQUIRED, _CR_OPTIONAL, "DAG_RECEIPT_INVALID")
    _authority_false(body, "DAG_RECEIPT_INVALID")
    if type(body.get("proposal")) is not dict:
        _fail("DAG_RECEIPT_INVALID", "proposal must remain inside the receipt body")
    if type(body.get("challenges")) is not list:
        _fail("DAG_RECEIPT_INVALID", "challenges must remain inside the receipt body")
    if type(body.get("revisions")) is not list:
        _fail("DAG_RECEIPT_INVALID", "revisions must remain inside the receipt body")
    if "target_artifact_digest" in body:
        _sha256(
            body.get("target_artifact_digest"),
            "DAG_RECEIPT_INVALID",
            "target_artifact_digest",
        )
    return _validate_self_digest(body, "conducting_receipt.v0")


def _validate_rer(body: Mapping[str, Any]) -> str:
    _keys(body, _RER_REQUIRED, _RER_OPTIONAL, "DAG_RECEIPT_INVALID")
    _authority_false(body, "DAG_RECEIPT_INVALID")
    if body.get("recovered") is not False or type(body.get("recovered")) is not bool:
        _fail("DAG_RECEIPT_INVALID", "recovered must remain false")
    restore = body.get("restore_target")
    if type(restore) is not dict:
        _fail("DAG_RECEIPT_INVALID", "restore_target is not a record")
    if "expected_digest" in restore:
        _sha256(restore.get("expected_digest"), "DAG_RECEIPT_INVALID", "expected_digest")
    env = body.get("target_environment")
    if type(env) is not dict:
        _fail("DAG_RECEIPT_INVALID", "target_environment is not a record")
    if "environment_digest" in env:
        _sha256(env.get("environment_digest"), "DAG_RECEIPT_INVALID", "environment_digest")
    refs = body.get("independent_verification_refs")
    if type(refs) is not list:
        _fail("DAG_RECEIPT_INVALID", "independent_verification_refs must be a list")
    for item in refs:
        if type(item) is not dict:
            _fail("DAG_RECEIPT_INVALID", "independent verification ref is not a record")
        if "receipt_digest" in item:
            _sha256(item.get("receipt_digest"), "DAG_RECEIPT_INVALID", "receipt_digest")
        if "evidence_digest" in item:
            _sha256(item.get("evidence_digest"), "DAG_RECEIPT_INVALID", "evidence_digest")
    return _validate_self_digest(body, "recovery_execution_receipt.v0")


def _validate_claim(body: Mapping[str, Any]) -> None:
    _keys(body, _CLAIM_REQUIRED, _CLAIM_OPTIONAL, "DAG_CLAIM_INVALID")
    _authority_false(body, "DAG_CLAIM_INVALID")
    if body.get("schema_version") != CLAIM_SCHEMA:
        _fail("DAG_CLAIM_INVALID", "claim schema_version is not recognized")
    if body.get("claim_kind") not in CLAIM_KINDS:
        _fail("DAG_CLAIM_INVALID", "claim_kind is not recognized")
    if body.get("epistemic_status") not in EPISTEMIC_STATUSES:
        _fail("DAG_CLAIM_INVALID", "epistemic_status is not recognized")
    for field in ("claim_id", "statement", "scope"):
        if type(body.get(field)) is not str or not body[field].strip():
            _fail("DAG_CLAIM_INVALID", f"{field} is missing")


def _validate_receipt(body: Mapping[str, Any]) -> str | None:
    schema = body.get("schema_version")
    if schema not in RECEIPT_SCHEMAS:
        _fail("DAG_RECEIPT_INVALID", "schema_version is not a closed receipt")
    if schema == "tested_envelope.v0":
        _validate_te(body)
        return None
    if schema == "recovery_preflight.v0":
        _validate_rp(body)
        return None
    if schema == "independent_verification_preflight.v0":
        _validate_ivp(body)
        return None
    if schema == "conducting_receipt.v0":
        return _validate_cr(body)
    return _validate_rer(body)


def _add_digest_ref(
    refs: list[_RequiredRef],
    seen: set[tuple[str, str, str]],
    source_digest: str,
    path: str,
    digest: Any,
    relations: tuple[str, ...],
) -> None:
    bound = _sha256(digest, "DAG_RECEIPT_INVALID", path)
    key = (source_digest, path, bound)
    if key in seen:
        return
    seen.add(key)
    refs.append(_RequiredRef(source_digest, path, bound, relations))


def _add_label(
    labels: list[_LabelRef],
    source_digest: str,
    path: str,
    label: Any,
    kind: str,
) -> None:
    if type(label) is not str or not label.strip():
        return
    labels.append(_LabelRef(source_digest, path, label, kind))


def _file_digests(revision: Mapping[str, Any], prefix: str) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    files = revision.get("files")
    if type(files) is not list:
        return found
    for index, item in enumerate(files):
        if type(item) is not dict:
            continue
        found.append((f"{prefix}.files[{index}].sha256", item.get("sha256")))
    if "expected_sha256" in revision and revision.get("expected_sha256") is not None:
        found.append((f"{prefix}.expected_sha256", revision.get("expected_sha256")))
    return found


def _extract_te(
    node: _Node,
    refs: list[_RequiredRef],
    labels: list[_LabelRef],
    seen: set[tuple[str, str, str]],
) -> None:
    body = node.body or {}
    _add_label(labels, node.node_digest, "claim_id", body.get("claim_id"), "claim_id")
    binding = body.get("scope_binding") or {}
    _add_label(
        labels,
        node.node_digest,
        "scope_binding.claim_id",
        binding.get("claim_id"),
        "claim_id",
    )
    _add_digest_ref(
        refs,
        seen,
        node.node_digest,
        "scope_binding.scope_digest",
        binding.get("scope_digest"),
        ("DEPENDS_ON", "BOUNDS"),
    )
    revision = body.get("artifact_revision") or {}
    for path, digest in _file_digests(revision, "artifact_revision"):
        _add_digest_ref(refs, seen, node.node_digest, path, digest, ("DEPENDS_ON",))


def _extract_rp(
    node: _Node,
    refs: list[_RequiredRef],
    labels: list[_LabelRef],
    seen: set[tuple[str, str, str]],
) -> None:
    body = node.body or {}
    cited = body.get("cited_decision") or {}
    _add_label(
        labels,
        node.node_digest,
        "cited_decision.claim_id",
        cited.get("claim_id"),
        "claim_id",
    )
    if type(cited.get("decision")) is str:
        _add_label(
            labels,
            node.node_digest,
            "cited_decision.decision",
            cited.get("decision"),
            "decision",
        )
    observation = body.get("digest_observation")
    if type(observation) is dict:
        if "prior_integrity_digest" in observation:
            _add_digest_ref(
                refs,
                seen,
                node.node_digest,
                "digest_observation.prior_integrity_digest",
                observation.get("prior_integrity_digest"),
                ("DEPENDS_ON",),
            )
        if "digest" in observation:
            _add_digest_ref(
                refs,
                seen,
                node.node_digest,
                "digest_observation.digest",
                observation.get("digest"),
                ("DEPENDS_ON",),
            )


def _extract_ivp(
    node: _Node,
    refs: list[_RequiredRef],
    labels: list[_LabelRef],
    seen: set[tuple[str, str, str]],
) -> None:
    body = node.body or {}
    _add_label(labels, node.node_digest, "claim_id", body.get("claim_id"), "claim_id")
    revision = body.get("artifact_revision_binding") or {}
    for path, digest in _file_digests(revision, "artifact_revision_binding"):
        _add_digest_ref(refs, seen, node.node_digest, path, digest, ("DEPENDS_ON",))
    for key in ("source_execution_summary", "independent_execution_summary"):
        summary = body.get(key) or {}
        if type(summary) is not dict:
            continue
        if "evidence_digest" in summary:
            _add_digest_ref(
                refs,
                seen,
                node.node_digest,
                f"{key}.evidence_digest",
                summary.get("evidence_digest"),
                ("DEPENDS_ON",),
            )
        if "input_digest" in summary:
            _add_digest_ref(
                refs,
                seen,
                node.node_digest,
                f"{key}.input_digest",
                summary.get("input_digest"),
                ("DEPENDS_ON",),
            )


def _extract_cr(
    node: _Node,
    refs: list[_RequiredRef],
    labels: list[_LabelRef],
    seen: set[tuple[str, str, str]],
) -> None:
    body = node.body or {}
    _add_label(
        labels,
        node.node_digest,
        "target_claim_id",
        body.get("target_claim_id"),
        "claim_id",
    )
    if "target_artifact_digest" in body:
        _add_digest_ref(
            refs,
            seen,
            node.node_digest,
            "target_artifact_digest",
            body.get("target_artifact_digest"),
            ("DEPENDS_ON", "CITES"),
        )


def _maybe_sha(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == _SHA256_WIDTH
        and all(char in _HEX for char in value)
        and not _unpinned(value)
    )


def _extract_rer(
    node: _Node,
    refs: list[_RequiredRef],
    labels: list[_LabelRef],
    seen: set[tuple[str, str, str]],
) -> None:
    body = node.body or {}
    restore = body.get("restore_target") or {}
    if type(restore) is dict and "expected_digest" in restore:
        _add_digest_ref(
            refs,
            seen,
            node.node_digest,
            "restore_target.expected_digest",
            restore.get("expected_digest"),
            ("DEPENDS_ON",),
        )
    if type(restore) is dict and _maybe_sha(restore.get("approval_ref")):
        _add_digest_ref(
            refs,
            seen,
            node.node_digest,
            "restore_target.approval_ref",
            restore.get("approval_ref"),
            ("DEPENDS_ON",),
        )
    env = body.get("target_environment") or {}
    if type(env) is dict and "environment_digest" in env:
        _add_digest_ref(
            refs,
            seen,
            node.node_digest,
            "target_environment.environment_digest",
            env.get("environment_digest"),
            ("DEPENDS_ON",),
        )
    refs_raw = body.get("independent_verification_refs") or []
    if type(refs_raw) is list:
        for index, item in enumerate(refs_raw):
            if type(item) is not dict:
                continue
            if "receipt_digest" in item:
                _add_digest_ref(
                    refs,
                    seen,
                    node.node_digest,
                    f"independent_verification_refs[{index}].receipt_digest",
                    item.get("receipt_digest"),
                    ("DEPENDS_ON", "CITES"),
                )
            if "evidence_digest" in item:
                _add_digest_ref(
                    refs,
                    seen,
                    node.node_digest,
                    f"independent_verification_refs[{index}].evidence_digest",
                    item.get("evidence_digest"),
                    ("DEPENDS_ON", "CITES"),
                )
            if type(item.get("claim")) is str:
                _add_label(
                    labels,
                    node.node_digest,
                    f"independent_verification_refs[{index}].claim",
                    item.get("claim"),
                    "claim",
                )


def _extract_refs(
    node: _Node,
    refs: list[_RequiredRef],
    labels: list[_LabelRef],
    seen: set[tuple[str, str, str]],
) -> None:
    schema = node.schema_version
    if schema == "tested_envelope.v0":
        _extract_te(node, refs, labels, seen)
    elif schema == "recovery_preflight.v0":
        _extract_rp(node, refs, labels, seen)
    elif schema == "independent_verification_preflight.v0":
        _extract_ivp(node, refs, labels, seen)
    elif schema == "conducting_receipt.v0":
        _extract_cr(node, refs, labels, seen)
    elif schema == "recovery_execution_receipt.v0":
        _extract_rer(node, refs, labels, seen)


def _parse_node(raw: Mapping[str, Any]) -> _Node:
    _keys(raw, _NODE_REQUIRED, _NODE_OPTIONAL, "DAG_NODE_INVALID")
    node = _Node()
    node.node_id = _nonempty(raw.get("node_id"), "DAG_NODE_INVALID", "node_id")
    kind = raw.get("kind")
    if kind in FORBIDDEN_NODE_KINDS:
        _fail("DAG_NODE_INVALID", "internal receipt subrecords are not nodes")
    if kind not in NODE_KINDS:
        _fail("DAG_NODE_INVALID", "node kind is not closed")
    node.kind = kind
    if "artifact_id" in raw:
        node.artifact_id = _nonempty(raw.get("artifact_id"), "DAG_NODE_INVALID", "artifact_id")
    if "immutable_version" in raw:
        node.immutable_version = _nonempty(
            raw.get("immutable_version"),
            "DAG_NODE_INVALID",
            "immutable_version",
        )
    if kind == "EXTERNAL_REF":
        for field in _EXTERNAL_REF_FORBIDDEN:
            if field in raw:
                _fail("DAG_NODE_INVALID", "EXTERNAL_REF cannot carry receipt semantics")
        node.digest = _sha256(raw.get("digest"), "DAG_NODE_INVALID", "digest")
        node.node_digest = node.digest
        if "label" in raw:
            node.label = _nonempty(raw.get("label"), "DAG_NODE_INVALID", "label")
        if "source_hint" in raw:
            node.source_hint = _nonempty(
                raw.get("source_hint"),
                "DAG_NODE_INVALID",
                "source_hint",
            )
        if "node_digest" in raw:
            stated = _sha256(raw.get("node_digest"), "DAG_NODE_INVALID", "node_digest")
            if stated != node.node_digest:
                _fail("DAG_NODE_INVALID", "caller node_digest does not match")
        return node
    if "body" not in raw:
        _fail("DAG_NODE_INVALID", "body-backed node requires a body")
    body = raw.get("body")
    if type(body) is not dict:
        _fail("DAG_NODE_INVALID", "body must be a mapping")
    node.body = body
    if kind == "RECEIPT":
        node.source_reported_digest = _validate_receipt(body)
        node.schema_version = body.get("schema_version")
        node.node_digest = _digest(body, "DAG_NODE_INVALID")
    elif kind == "CLAIM":
        _validate_claim(body)
        node.schema_version = CLAIM_SCHEMA
        node.node_digest = _digest(body, "DAG_NODE_INVALID")
    else:
        node.node_digest = _digest(body, "DAG_NODE_INVALID")
        if type(body.get("schema_version")) is str:
            node.schema_version = body.get("schema_version")
    if "digest" in raw:
        _fail("DAG_NODE_INVALID", "body-backed node cannot be digest-only")
    if "node_digest" in raw:
        stated = _sha256(raw.get("node_digest"), "DAG_NODE_INVALID", "node_digest")
        if stated != node.node_digest:
            _fail("DAG_NODE_INVALID", "caller node_digest does not match recomputation")
    return node


def _edge_payload(edge: _Edge) -> dict[str, str]:
    payload = {
        "relation": edge.relation,
        "source_digest": edge.source_digest,
        "target_digest": edge.target_digest,
        "basis": edge.basis,
    }
    if edge.rationale_digest is not None:
        payload["rationale_digest"] = edge.rationale_digest
    return payload


def _finish_edge(edge: _Edge) -> None:
    if edge.source_digest == edge.target_digest:
        _fail("DAG_EDGE_INVALID", "self-loop is not allowed")
    edge.edge_digest = _digest(_edge_payload(edge), "DAG_EDGE_INVALID")


def _lookup_node(
    token: str,
    by_id: Mapping[str, _Node],
    by_digest: Mapping[str, _Node],
    by_reported: Mapping[str, _Node],
) -> _Node | None:
    if token in by_id:
        return by_id[token]
    if token in by_digest:
        return by_digest[token]
    if token in by_reported:
        return by_reported[token]
    return None


def _parse_caller_edge(
    raw: Mapping[str, Any],
    by_id: Mapping[str, _Node],
    by_digest: Mapping[str, _Node],
    by_reported: Mapping[str, _Node],
) -> _Edge:
    _keys(raw, _EDGE_REQUIRED, _EDGE_OPTIONAL, "DAG_EDGE_INVALID")
    edge = _Edge()
    edge.edge_id = _nonempty(raw.get("edge_id"), "DAG_EDGE_INVALID", "edge_id")
    relation = raw.get("relation")
    if relation in FORBIDDEN_RELATIONS:
        _fail("DAG_EDGE_INVALID", "relation is not allowed in v0")
    if relation not in RELATIONS:
        _fail("DAG_EDGE_INVALID", "relation is not closed")
    edge.relation = relation
    basis = raw.get("basis")
    if basis not in {"SOURCE_DERIVED", "CALLER_DECLARED"}:
        _fail("DAG_EDGE_INVALID", "basis is not closed")
    if basis == "SOURCE_DERIVED":
        _fail("DAG_EDGE_INVALID", "caller cannot declare SOURCE_DERIVED")
    if relation in {"DEPENDS_ON", "BOUNDS"}:
        _fail("DAG_EDGE_INVALID", f"{relation} is SOURCE_DERIVED only")
    if relation == "CONTRADICTS" and basis != "CALLER_DECLARED":
        _fail("DAG_EDGE_INVALID", "CONTRADICTS is CALLER_DECLARED only")
    edge.basis = basis
    source_node = None
    target_node = None
    if "source_node_id" in raw:
        source_id = _nonempty(raw.get("source_node_id"), "DAG_EDGE_INVALID", "source_node_id")
        source_node = by_id.get(source_id)
        if source_node is None:
            _fail("DAG_EDGE_INVALID", "source_node_id does not resolve")
    if "target_node_id" in raw:
        target_id = _nonempty(raw.get("target_node_id"), "DAG_EDGE_INVALID", "target_node_id")
        target_node = by_id.get(target_id)
        if target_node is None:
            _fail("DAG_EDGE_INVALID", "target_node_id does not resolve")
    if "source_digest" in raw:
        source_digest = _sha256(raw.get("source_digest"), "DAG_EDGE_INVALID", "source_digest")
        found = _lookup_node(source_digest, by_id, by_digest, by_reported)
        if found is None:
            _fail("DAG_EDGE_INVALID", "source_digest does not resolve")
        if source_node is not None and found.node_digest != source_node.node_digest:
            _fail("DAG_EDGE_INVALID", "source identity conflicts")
        source_node = found
    if "target_digest" in raw:
        target_digest = _sha256(raw.get("target_digest"), "DAG_EDGE_INVALID", "target_digest")
        found = _lookup_node(target_digest, by_id, by_digest, by_reported)
        if found is None:
            _fail("DAG_EDGE_INVALID", "target_digest does not resolve")
        if target_node is not None and found.node_digest != target_node.node_digest:
            _fail("DAG_EDGE_INVALID", "target identity conflicts")
        target_node = found
    if source_node is None or target_node is None:
        _fail("DAG_EDGE_INVALID", "edge endpoints must resolve")
    edge.source_digest = source_node.node_digest
    edge.target_digest = target_node.node_digest
    if relation == "CONTRADICTS":
        if not source_node.body_backed or not target_node.body_backed:
            _fail("DAG_EDGE_INVALID", "CONTRADICTS requires body-backed endpoints")
        if "rationale_body" not in raw:
            _fail("DAG_EDGE_INVALID", "CONTRADICTS requires rationale_body")
        rationale = raw.get("rationale_body")
        if type(rationale) is not dict:
            _fail("DAG_EDGE_INVALID", "rationale_body must be a mapping")
        edge.rationale_body = rationale
        recomputed = _digest(rationale, "DAG_EDGE_INVALID")
        if "rationale_digest" in raw:
            stated = _sha256(
                raw.get("rationale_digest"),
                "DAG_EDGE_INVALID",
                "rationale_digest",
            )
            if stated != recomputed:
                _fail("DAG_EDGE_INVALID", "rationale_digest does not match")
        edge.rationale_digest = recomputed
    elif "rationale_body" in raw:
        rationale = raw.get("rationale_body")
        if type(rationale) is not dict:
            _fail("DAG_EDGE_INVALID", "rationale_body must be a mapping")
        edge.rationale_body = rationale
        edge.rationale_digest = _digest(rationale, "DAG_EDGE_INVALID")
        if "rationale_digest" in raw:
            stated = _sha256(
                raw.get("rationale_digest"),
                "DAG_EDGE_INVALID",
                "rationale_digest",
            )
            if stated != edge.rationale_digest:
                _fail("DAG_EDGE_INVALID", "rationale_digest does not match")
    elif "rationale_digest" in raw:
        _fail("DAG_EDGE_INVALID", "rationale_digest requires rationale_body")
    if relation == "SUCCESSOR_OF":
        if not source_node.body_backed or not target_node.body_backed:
            _fail("DAG_EDGE_INVALID", "SUCCESSOR_OF requires body-backed endpoints")
    _finish_edge(edge)
    return edge


def _derived_edge(
    relation: str,
    source_digest: str,
    target_digest: str,
    basis: str = "SOURCE_DERIVED",
) -> _Edge:
    edge = _Edge()
    edge.edge_id = f"derived:{relation}:{source_digest}:{target_digest}"
    edge.relation = relation
    edge.source_digest = source_digest
    edge.target_digest = target_digest
    edge.basis = basis
    _finish_edge(edge)
    return edge


def _contradiction_key(edge: _Edge) -> tuple[str, str, str]:
    left, right = sorted((edge.source_digest, edge.target_digest))
    rationale = edge.rationale_digest or ""
    return (left, right, rationale)


def _register_edge(
    edge: _Edge,
    by_id: dict[str, _Edge],
    by_digest: dict[str, _Edge],
    contradictions: dict[tuple[str, str, str], _Edge],
) -> None:
    if edge.edge_id in by_id:
        prior = by_id[edge.edge_id]
        if prior.edge_digest != edge.edge_digest:
            _fail("DAG_DUPLICATE", "edge_id repeats with a different body")
        return
    if edge.edge_digest in by_digest:
        _fail("DAG_DUPLICATE", "edge_digest repeats under a new edge_id")
    if edge.relation == "CONTRADICTS":
        key = _contradiction_key(edge)
        if key in contradictions:
            _fail("DAG_DUPLICATE", "contradiction pair+rationale repeats")
        contradictions[key] = edge
    by_id[edge.edge_id] = edge
    by_digest[edge.edge_digest] = edge


def _resolve_required(
    required: list[_RequiredRef],
    by_digest: Mapping[str, _Node],
    by_reported: Mapping[str, _Node],
) -> tuple[list[dict[str, str]], list[_Edge]]:
    unresolved: list[dict[str, str]] = []
    derived: list[_Edge] = []
    emitted: set[str] = set()
    for item in required:
        body_match = by_digest.get(item.digest)
        if body_match is not None and not body_match.body_backed:
            body_match = None
        if body_match is None:
            reported = by_reported.get(item.digest)
            if reported is not None and reported.body_backed:
                body_match = reported
        if body_match is not None and body_match.body_backed:
            target = body_match
            for relation in item.relations:
                if relation == "BOUNDS" and not target.body_backed:
                    continue
                try:
                    edge = _derived_edge(relation, item.source_node_digest, target.node_digest)
                except EvidenceBindingDagError as exc:
                    if "self-loop" in str(exc):
                        _fail("DAG_EDGE_INVALID", "required reference forms a self-loop")
                    raise
                if edge.edge_digest not in emitted:
                    derived.append(edge)
                    emitted.add(edge.edge_digest)
            continue
        external = by_digest.get(item.digest)
        if external is not None and external.kind == "EXTERNAL_REF":
            unresolved.append(
                {
                    "source_node_digest": item.source_node_digest,
                    "source_path": item.source_path,
                    "digest": item.digest,
                    "reason": "DIGEST_ONLY_EXTERNAL",
                }
            )
            if "DEPENDS_ON" in item.relations:
                try:
                    edge = _derived_edge(
                        "DEPENDS_ON",
                        item.source_node_digest,
                        external.node_digest,
                    )
                except EvidenceBindingDagError as exc:
                    if "self-loop" in str(exc):
                        _fail("DAG_EDGE_INVALID", "required reference forms a self-loop")
                    raise
                if edge.edge_digest not in emitted:
                    derived.append(edge)
                    emitted.add(edge.edge_digest)
            continue
        unresolved.append(
            {
                "source_node_digest": item.source_node_digest,
                "source_path": item.source_path,
                "digest": item.digest,
                "reason": "MISSING",
            }
        )
    return unresolved, derived


def _dependency_cycle(edges: list[_Edge], nodes: list[_Node]) -> bool:
    adj: dict[str, list[str]] = {node.node_digest: [] for node in nodes}
    for edge in edges:
        if edge.relation not in DEPENDENCY_RELATIONS:
            continue
        adj.setdefault(edge.source_digest, [])
        adj.setdefault(edge.target_digest, [])
        adj[edge.source_digest].append(edge.target_digest)
    color = {node: 0 for node in adj}

    def dfs(current: str) -> bool:
        color[current] = 1
        for nxt in adj[current]:
            if color.get(nxt, 0) == 1:
                return True
            if color.get(nxt, 0) == 0 and dfs(nxt):
                return True
        color[current] = 2
        return False

    return any(color[node] == 0 and dfs(node) for node in adj)


def _emit_node(node: _Node) -> dict[str, Any]:
    record: dict[str, Any] = {
        "node_id": node.node_id,
        "kind": node.kind,
        "node_digest": node.node_digest,
    }
    if node.body is not None:
        record["body"] = node.body
    if node.schema_version is not None:
        record["schema_version"] = node.schema_version
    if node.source_reported_digest is not None:
        record["source_reported_digest"] = node.source_reported_digest
    if node.digest is not None:
        record["digest"] = node.digest
    if node.label is not None:
        record["label"] = node.label
    if node.source_hint is not None:
        record["source_hint"] = node.source_hint
    if node.artifact_id is not None:
        record["artifact_id"] = node.artifact_id
    if node.immutable_version is not None:
        record["immutable_version"] = node.immutable_version
    return record


def _emit_edge(edge: _Edge) -> dict[str, Any]:
    record: dict[str, Any] = {
        "edge_id": edge.edge_id,
        "relation": edge.relation,
        "source_digest": edge.source_digest,
        "target_digest": edge.target_digest,
        "basis": edge.basis,
        "edge_digest": edge.edge_digest,
    }
    if edge.rationale_body is not None:
        record["rationale_body"] = edge.rationale_body
    if edge.rationale_digest is not None:
        record["rationale_digest"] = edge.rationale_digest
    return record


def _sort_unresolved(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda item: (
            item["source_node_digest"],
            item["source_path"],
            item["digest"],
            item["reason"],
        ),
    )


def _sort_labels(rows: list[_LabelRef]) -> list[dict[str, str]]:
    ordered = sorted(
        rows,
        key=lambda item: (
            item.source_node_digest,
            item.source_path,
            item.label,
            item.label_kind,
        ),
    )
    return [
        {
            "source_node_digest": item.source_node_digest,
            "source_path": item.source_path,
            "label": item.label,
            "label_kind": item.label_kind,
        }
        for item in ordered
    ]


def build_evidence_binding_dag(
    record: Mapping[str, Any],
    **forbidden: Any,
) -> dict[str, Any]:
    """Return a non-authoritative evidence binding DAG over snapshot nodes."""
    _reject_forbidden(forbidden)
    mapping = _snapshot(_require_mapping(record, "record"))
    _keys(mapping, _INPUT_REQUIRED, _INPUT_OPTIONAL, "DAG_SOURCE_INVALID")
    raw_nodes = _plain_list(mapping.get("nodes"), "DAG_SOURCE_INVALID", "nodes")
    raw_edges = mapping.get("edges", [])
    if "edges" in mapping:
        raw_edges = _plain_list(raw_edges, "DAG_SOURCE_INVALID", "edges")
    parsed_nodes: list[_Node] = []
    by_id: dict[str, _Node] = {}
    by_digest: dict[str, _Node] = {}
    by_reported: dict[str, _Node] = {}
    for item in raw_nodes:
        node_map = _require_mapping(item, "node")
        if type(item) is not dict and not isinstance(item, Mapping):
            _fail("DAG_NODE_INVALID", "node must be a mapping")
        node = _parse_node(node_map)
        if node.node_id in by_id:
            prior = by_id[node.node_id]
            if prior.node_digest != node.node_digest:
                _fail("DAG_DUPLICATE", "node_id repeats with a different body")
            _fail("DAG_DUPLICATE", "node_id repeats")
        if node.node_digest in by_digest:
            _fail("DAG_DUPLICATE", "node_digest repeats under a new node_id")
        if (
            node.source_reported_digest is not None
            and node.source_reported_digest in by_digest
            and by_digest[node.source_reported_digest].node_digest != node.node_digest
        ):
            _fail("DAG_DUPLICATE", "source-reported digest collides")
        by_id[node.node_id] = node
        by_digest[node.node_digest] = node
        if node.source_reported_digest is not None:
            by_reported[node.source_reported_digest] = node
        parsed_nodes.append(node)
    required: list[_RequiredRef] = []
    labels: list[_LabelRef] = []
    seen_refs: set[tuple[str, str, str]] = set()
    for node in parsed_nodes:
        if node.kind == "RECEIPT":
            _extract_refs(node, required, labels, seen_refs)
    unresolved, derived = _resolve_required(required, by_digest, by_reported)
    edge_by_id: dict[str, _Edge] = {}
    edge_by_digest: dict[str, _Edge] = {}
    contradictions: dict[tuple[str, str, str], _Edge] = {}
    for edge in derived:
        _register_edge(edge, edge_by_id, edge_by_digest, contradictions)
    if type(raw_edges) is not list:
        _fail("DAG_SOURCE_INVALID", "edges must be a list")
    for item in raw_edges:
        edge_map = _require_mapping(item, "edge")
        edge = _parse_caller_edge(edge_map, by_id, by_digest, by_reported)
        _register_edge(edge, edge_by_id, edge_by_digest, contradictions)
    all_edges = list(edge_by_id.values())
    if _dependency_cycle(all_edges, parsed_nodes):
        _fail("DAG_CYCLE", "dependency_dag contains a cycle")
    structure_status = "GRAPH_COMPLETE" if not unresolved else "GRAPH_INCOMPLETE"
    contradiction_edges = [
        edge for edge in all_edges if edge.relation == "CONTRADICTS"
    ]
    output = {
        "schema_version": SCHEMA_VERSION,
        "authority": False,
        "structure_status": structure_status,
        "unresolved_references": _sort_unresolved(unresolved),
        "label_only_refs": _sort_labels(labels),
        "contradiction_present": bool(contradiction_edges),
        "contradictions": sorted(edge.edge_digest for edge in contradiction_edges),
        "nodes": [
            _emit_node(node)
            for node in sorted(parsed_nodes, key=lambda item: item.node_digest)
        ],
        "edges": [
            _emit_edge(edge)
            for edge in sorted(all_edges, key=lambda item: item.edge_digest)
        ],
        "limitations": list(_LIMITATIONS),
    }
    output["dag_digest"] = _digest(output, "DAG_SOURCE_INVALID")
    return output
