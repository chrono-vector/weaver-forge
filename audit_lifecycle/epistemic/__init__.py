"""R4 epistemic foundation — non-authoritative claim / relation / provenance /
reconstructability / review-disagreement contracts.

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
from .reconstructability import (
    ReconstructabilityError,
    ReconstructabilityInputs,
    ReconstructabilityReport,
    derive_reconstructability_report,
    emit_reconstructability_report,
    verify_reconstructability_at_root,
    verify_reconstructability_report,
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
from .review_disagreement import (
    DISAGREEMENT_CATEGORIES,
    DISAGREEMENT_STATUSES,
    ReviewDisagreementError,
    ReviewDisagreementRecord,
    create_disagreement_record,
    create_successor_record,
    validate_disagreement_record,
    verify_disagreement_records_at_root,
    write_disagreement_record,
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
    "DISAGREEMENT_CATEGORIES",
    "DISAGREEMENT_STATUSES",
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
    "ReconstructabilityError",
    "ReconstructabilityInputs",
    "ReconstructabilityReport",
    "RelationAsClaim",
    "RelationSatisfactionError",
    "ReviewDisagreementError",
    "ReviewDisagreementRecord",
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
    "create_disagreement_record",
    "create_successor_record",
    "derive_reconstructability_report",
    "emit_reconstructability_report",
    "legacy_claim_view",
    "normalize_sequences",
    "parse_optional_epistemic_container",
    "read_claim_record",
    "validate_disagreement_record",
    "validate_epistemic_record",
    "validate_provenance_graph",
    "verify_disagreement_records_at_root",
    "verify_reconstructability_at_root",
    "verify_reconstructability_report",
    "write_disagreement_record",
]

SCHEMA_VERSION_CLAIM = "r4.epistemic.claim.v1"
SCHEMA_VERSION_RELATION = "r4.epistemic.relation.v1"
SCHEMA_VERSION_PROVENANCE = "r4.epistemic.provenance.v1"
SCHEMA_VERSION_RECONSTRUCTABILITY = "r4.epistemic.reconstructability.v1"
SCHEMA_VERSION_REVIEW_DISAGREEMENT = "r4.epistemic.review-disagreement.v1"
