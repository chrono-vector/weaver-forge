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
from .expectation import (
    EXPECTATION_SCHEMA_VERSION,
    FREEZE_STATE_FROZEN,
    FREEZE_STATE_IN_PROGRESS,
    FREEZE_STATE_INCOMPLETE,
    FREEZE_STATE_PRE,
    LEGACY_LIFECYCLE,
    R4B_CONTRACT_MARKER,
    R4BExpectation,
    R4BExpectationError,
    STATE_LEGACY_PRE_R4B,
    STATE_R4_B_ENABLED,
    build_r4b_expectation,
    classify_audit_root,
    classify_frozen_r4b_state,
    classify_package_r4b_state,
    expectation_digest,
    strict_parse_legacy_manifest,
    strict_parse_r4b_expectation,
    validate_freeze_transaction,
)
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
from .r4b_verify import verify_r4b_at_root
from .reconstructability import (
    ReconstructabilityError,
    ReconstructabilityInputs,
    ReconstructabilityReport,
    derive_expected_report,
    derive_reconstructability_report,
    emit_reconstructability_report,
    strict_parse_report,
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
    collect_disagreement_expectation,
    create_disagreement_record,
    create_successor_record,
    strict_parse_record,
    validate_disagreement_record,
    verify_chain_graph,
    verify_disagreement_expected_set,
    verify_disagreement_records_at_root,
    write_disagreement_record,
)
from .serialize import (
    ABSENT,
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
    "ABSENT",
    "CLAIM_KINDS",
    "DISAGREEMENT_CATEGORIES",
    "DISAGREEMENT_STATUSES",
    "EPISTEMIC_STATUSES",
    "EXPECTATION_SCHEMA_VERSION",
    "FREEZE_STATE_FROZEN",
    "FREEZE_STATE_IN_PROGRESS",
    "FREEZE_STATE_INCOMPLETE",
    "FREEZE_STATE_PRE",
    "INDEPENDENT_EVIDENCE_ADMISSION_STATUS",
    "LEGACY_LIFECYCLE",
    "ORDERED_SEQUENCE_FIELDS",
    "R4B_CONTRACT_MARKER",
    "RELATION_TYPES",
    "SET_LIKE_SEQUENCE_FIELDS",
    "STATE_LEGACY_PRE_R4B",
    "STATE_R4_B_ENABLED",
    "AuthorityViolation",
    "EpistemicClaimRecord",
    "EpistemicStatusError",
    "EpistemicValidationError",
    "IndependenceBasis",
    "IndependentOriginAccounting",
    "ProvenanceGraphError",
    "ProvenanceGraphIndex",
    "ProvenanceRecord",
    "R4BExpectation",
    "R4BExpectationError",
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
    "build_r4b_expectation",
    "canonical_digest",
    "canonical_dumps",
    "canonical_loads",
    "classify_audit_root",
    "classify_frozen_r4b_state",
    "classify_package_r4b_state",
    "collect_disagreement_expectation",
    "create_disagreement_record",
    "create_successor_record",
    "derive_expected_report",
    "derive_reconstructability_report",
    "emit_reconstructability_report",
    "expectation_digest",
    "legacy_claim_view",
    "normalize_sequences",
    "parse_optional_epistemic_container",
    "read_claim_record",
    "strict_parse_legacy_manifest",
    "strict_parse_r4b_expectation",
    "strict_parse_record",
    "strict_parse_report",
    "validate_disagreement_record",
    "validate_epistemic_record",
    "validate_freeze_transaction",
    "validate_provenance_graph",
    "verify_chain_graph",
    "verify_disagreement_expected_set",
    "verify_disagreement_records_at_root",
    "verify_r4b_at_root",
    "verify_reconstructability_at_root",
    "verify_reconstructability_report",
    "write_disagreement_record",
]

SCHEMA_VERSION_CLAIM = "r4.epistemic.claim.v1"
SCHEMA_VERSION_RELATION = "r4.epistemic.relation.v1"
SCHEMA_VERSION_PROVENANCE = "r4.epistemic.provenance.v1"
SCHEMA_VERSION_RECONSTRUCTABILITY = "r4.epistemic.reconstructability.v1"
SCHEMA_VERSION_REVIEW_DISAGREEMENT = "r4.epistemic.review-disagreement.v1"
SCHEMA_VERSION_EXPECTATION = "r4.epistemic.expectation.v1"
