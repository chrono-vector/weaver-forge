"""R4-A epistemic foundation — non-authoritative claim / relation / provenance contracts.

All records in this package are advisory metadata only.
They never authorize execution, change VECTOR/EIG semantics, create Human Final,
alter Weaver PASS/FAIL, or silently promote epistemic status.
"""

from __future__ import annotations

from .authority import (
    AuthorityViolation,
    assert_authority_false,
    assert_confidence_cannot_authorize,
    assert_epistemic_cannot_create_human_final,
    assert_epistemic_cannot_change_execution_authorization,
)
from .compat import legacy_claim_view, read_claim_record
from .provenance import (
    INDEPENDENT_EVIDENCE_ADMISSION_STATUS,
    IndependenceBasis,
    IndependentOriginAccounting,
    ProvenanceGraphError,
    ProvenanceGraphIndex,
    ProvenanceRecord,
    ValidatedBasisRef,
    account_independent_origins,
    validate_provenance_graph,
)
from .records import (
    CLAIM_KINDS,
    EPISTEMIC_STATUSES,
    EpistemicClaimRecord,
    EpistemicStatusError,
    assert_no_silent_status_promotion,
)
from .relations import (
    RELATION_TYPES,
    RelationAsClaim,
    RelationSatisfactionError,
    analogous_to_cannot_satisfy_causes,
)
from .serialize import (
    ORDERED_SEQUENCE_FIELDS,
    SET_LIKE_SEQUENCE_FIELDS,
    canonical_digest,
    canonical_dumps,
    canonical_loads,
    normalize_sequences,
)
from .validation import (
    EpistemicValidationError,
    parse_optional_epistemic_container,
    validate_epistemic_record,
)

__all__ = [
    "CLAIM_KINDS",
    "EPISTEMIC_STATUSES",
    "INDEPENDENT_EVIDENCE_ADMISSION_STATUS",
    "ORDERED_SEQUENCE_FIELDS",
    "RELATION_TYPES",
    "SET_LIKE_SEQUENCE_FIELDS",
    "AuthorityViolation",
    "EpistemicClaimRecord",
    "EpistemicStatusError",
    "EpistemicValidationError",
    "IndependenceBasis",
    "IndependentOriginAccounting",
    "ProvenanceGraphError",
    "ProvenanceGraphIndex",
    "ProvenanceRecord",
    "RelationAsClaim",
    "RelationSatisfactionError",
    "ValidatedBasisRef",
    "account_independent_origins",
    "analogous_to_cannot_satisfy_causes",
    "assert_authority_false",
    "assert_confidence_cannot_authorize",
    "assert_epistemic_cannot_change_execution_authorization",
    "assert_epistemic_cannot_create_human_final",
    "assert_no_silent_status_promotion",
    "canonical_digest",
    "canonical_dumps",
    "canonical_loads",
    "legacy_claim_view",
    "normalize_sequences",
    "parse_optional_epistemic_container",
    "read_claim_record",
    "validate_epistemic_record",
    "validate_provenance_graph",
]

SCHEMA_VERSION_CLAIM = "r4.epistemic.claim.v1"
SCHEMA_VERSION_RELATION = "r4.epistemic.relation.v1"
SCHEMA_VERSION_PROVENANCE = "r4.epistemic.provenance.v1"
