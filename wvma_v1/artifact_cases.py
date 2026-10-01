"""Fixed B1 artifact case definitions and sealed-catalog helpers.

Catalog text carries no commands. Case identity, operations, and digests are
code-owned and sealed through A1 catalog parsing.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from wvma_v1.baselines import (
    PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
    PROFILE_AUDIT_R4B_REVIEW_CHAIN,
    PROFILE_AUDIT_R4B_ZERO_REVIEW,
    PROFILE_CAMPAIGN_TEST_ONLY,
    rebind_freeze_package_hashes,
    rebind_root_sha256sums,
)
from wvma_v1.canonical import canonical_bytes, digest_excluding_field
from wvma_v1.models import MutationSpec, strict_parse_catalog
from wvma_v1.mutations import (
    EMPTY_SHA256,
    MutationApplication,
    apply_mutation,
    _compute_delete_json,
    _compute_rebind_hashes,
    _compute_replace_bytes,
    _compute_set_json,
    _content_from_add_args,
    _sha256_bytes,
)

# Git revision of R4 Human Final (40-hex). Catalog field requires sha256 (64-hex),
# so bind the revision via SHA-256 of the exact revision string.
PRODUCT_REVISION = "6140502e915c9668960d00aef7fcd48fd14cc69f"
PRODUCT_BASE_SHA = hashlib.sha256(PRODUCT_REVISION.encode("ascii")).hexdigest()
CATALOG_ID = "WVMA-V1-ARTIFACT-B1"
CATALOG_VERSION = "1"
RUNNER_CONTRACT = "wvma_v1.runner.a2"
ORACLE_CONTRACT = "wvma_v1.oracle.a2"

# Required critical B1 case IDs (C01-C10). C08-UM-01 is non-critical INVALID_MUTANT.
CRITICAL_CASE_IDS: tuple[str, ...] = (
    "C01-01",
    "C01-02",
    "C02-01",
    "C02-02",
    "C03-01",
    "C04-01",
    "C04-02",
    "C04-03",
    "C04-04",
    "C05-01",
    "C05-02",
    "C05-03",
    "C06-01",
    "C06-02",
    "C06-03",
    "C07-01",
    "C07-02",
    "C07-03",
    "C07-04",
    "C08-01",
    "C08-02",
    "C08-03",
    "C08-04",
    "C08-05",
    "C09-01",
    "C09-02",
    "C10-01",
    "C10-02",
    "C10-03",
)


@dataclass(frozen=True)
class CaseDef:
    case_id: str
    property_id: str
    critical: bool
    baseline_profile: str
    mutation_kind: str
    target_relative_path: str  # may include "{audit}" / "{freeze}" tokens
    operation_enum: str
    operation_arguments: dict[str, Any]
    mutation_timing: str
    verifier_invocation_id: str
    violation_predicate: str
    expected_rejection_predicate: str
    oracle_observations: tuple[str, ...]
    materiality: str
    # Code-owned follow-ups after the sealed mutation (permitted rebinds / multi-file).
    followup: str | None = None
    # When True, unbound-metadata style: expect INVALID_MUTANT (no property violation).
    expect_invalid_mutant: bool = False


def _props() -> list[dict[str, Any]]:
    rows = [
        (
            "WVMA-C01",
            "Stored decision text cannot override recomputed semantics",
            ["audit_lifecycle/semantic_verification.py"],
            ["audit.verify_semantics"],
        ),
        (
            "WVMA-C02",
            "Frozen R4-B cannot downgrade to accepted legacy semantics",
            ["audit_lifecycle/epistemic/r4b_verify.py"],
            ["audit.verify_r4b"],
        ),
        (
            "WVMA-C03",
            "Reconstructability is recomputed, not trusted as stored text",
            ["audit_lifecycle/epistemic/reconstructability.py"],
            ["audit.verify_reconstructability"],
        ),
        (
            "WVMA-C04",
            "Disagreement records equal the committed complete set and valid chain",
            ["audit_lifecycle/epistemic/review_disagreement.py"],
            ["audit.verify_r4b"],
        ),
        (
            "WVMA-C05",
            "R4 artifacts cannot claim authority or fabricate admitted independence",
            ["audit_lifecycle/epistemic/authority.py"],
            ["audit.verify_reconstructability"],
        ),
        (
            "WVMA-C06",
            "PRESENT-invalid structured values never receive defaults or coercion",
            ["audit_lifecycle/epistemic/expectation.py"],
            ["audit.verify_r4b"],
        ),
        (
            "WVMA-C07",
            "Freeze completion requires a complete transaction",
            ["audit_lifecycle/epistemic/expectation.py"],
            ["audit.validate_freeze_transaction"],
        ),
        (
            "WVMA-C08",
            "When policy requires Human Review, freeze/verify require ACCEPTED status gate",
            ["audit_lifecycle/review_gate.py"],
            ["audit.freeze_run", "audit.verify_semantics"],
        ),
        (
            "WVMA-C09",
            "Source/target identity remains semantically bound",
            ["audit_lifecycle/pin.py", "audit_lifecycle/adapters/hash_claim.py"],
            ["audit.verify_semantics"],
        ),
        (
            "WVMA-C10",
            "Campaign state or foreign evidence cannot create PASS",
            ["campaign_runner_v0/state_revalidation.py"],
            ["campaign.revalidate"],
        ),
    ]
    return [
        {
            "property_id": pid,
            "invariant": inv,
            "target_paths": paths,
            "target_entry_points": eps,
            "materiality": "MATERIAL",
        }
        for pid, inv, paths, eps in rows
    ]


CASE_DEFS: tuple[CaseDef, ...] = (
    CaseDef(
        case_id="C01-01",
        property_id="WVMA-C01",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/DECISION.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/decision", "value": "PASS"},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="decision_mismatch",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("decision_mismatch", "semantic_ok_false"),
        materiality="MATERIAL",
        followup="c01_01",
    ),
    CaseDef(
        case_id="C01-02",
        property_id="WVMA-C01",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{freeze}/FINAL_DECISION.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/decision/promoted_to_full", "value": True},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="final_decision_mismatch",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("final_decision_mismatch", "semantic_ok_false"),
        materiality="MATERIAL",
        followup="c01_02",
    ),
    CaseDef(
        case_id="C02-01",
        property_id="WVMA-C02",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/EXECUTION_MANIFEST.json",
        operation_enum="DELETE_JSON_POINTER",
        operation_arguments={"pointer": "/r4_b"},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="r4b_downgrade_rejected",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("r4b_ok_false", "not_legacy_accept"),
        materiality="MATERIAL",
        followup="c02_01",
    ),
    CaseDef(
        case_id="C02-02",
        property_id="WVMA-C02",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{freeze}/MANIFEST.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={
            "pointer": "/contract_marker",
            "value": "weaver_forge_audit_lifecycle_v0",
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="r4b_classification_fail",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("marker_legacy", "r4b_ok_false"),
        materiality="MATERIAL",
        followup="freeze_rebind",
    ),
    CaseDef(
        case_id="C03-01",
        property_id="WVMA-C03",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/RECONSTRUCTABILITY_REPORT.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/reconstructable", "value": False},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_reconstructability",
        violation_predicate="recon_recompute_mismatch",
        expected_rejection_predicate="recon_ok_false",
        oracle_observations=("recon_mismatch",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C04-01",
        property_id="WVMA-C04",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{review_first}",
        operation_enum="DELETE_DECLARED_FILE",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="expected_set_mismatch",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("expected_set_mismatch",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C04-02",
        property_id="WVMA-C04",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/reviews/undeclared_extra.json",
        operation_enum="ADD_DECLARED_FILE",
        operation_arguments={},  # filled at materialize with content_hex
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="extra_record_rejected",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("extra_record",),
        materiality="MATERIAL",
        followup="c04_02_content",
    ),
    CaseDef(
        case_id="C04-03",
        property_id="WVMA-C04",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{review_second}",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={
            "pointer": "/prior_record_digest",
            "value": "ab" * 32,
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="chain_verification_fail",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("chain_fail",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C04-04",
        property_id="WVMA-C04",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{review_second}",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/disagreement_id", "value": "D-1"},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="duplicate_id_rejected",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("duplicate_id",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C05-01",
        property_id="WVMA-C05",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/RECONSTRUCTABILITY_REPORT.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/authority", "value": True},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_reconstructability",
        violation_predicate="authority_true_rejected",
        expected_rejection_predicate="recon_ok_false",
        oracle_observations=("authority_rejected",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C05-02",
        property_id="WVMA-C05",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/RECONSTRUCTABILITY_REPORT.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/independent_evidence_count", "value": 1},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_reconstructability",
        violation_predicate="positive_independent_count_rejected",
        expected_rejection_predicate="recon_ok_false",
        oracle_observations=("independent_count_rejected",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C05-03",
        property_id="WVMA-C05",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/RECONSTRUCTABILITY_REPORT.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={
            "pointer": "/independent_evidence_admission_status",
            "value": "ADMITTED",
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_reconstructability",
        violation_predicate="admission_not_configured_required",
        expected_rejection_predicate="recon_ok_false",
        oracle_observations=("admission_rejected",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C06-01",
        property_id="WVMA-C06",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/EXECUTION_MANIFEST.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={
            "pointer": "/r4_b/expected_disagreement_record_digests",
            "value": "not-a-list",
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="strict_parser_rejects_string_as_list",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("parser_reject",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C06-02",
        property_id="WVMA-C06",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/RECONSTRUCTABILITY_REPORT.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/missing_inputs", "value": True},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_reconstructability",
        violation_predicate="strict_parser_rejects_bool_collection",
        expected_rejection_predicate="recon_ok_false",
        oracle_observations=("parser_reject",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C06-03",
        property_id="WVMA-C06",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{review_first}",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={
            "pointer": "/reviewer_positions",
            "value": {"rev-A": "PASS"},
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_r4b",
        violation_predicate="strict_parser_rejects_mapping_as_list",
        expected_rejection_predicate="r4b_ok_false",
        oracle_observations=("parser_reject",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C07-01",
        property_id="WVMA-C07",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_REVIEW_CHAIN,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/FREEZE_INTENT.json",
        operation_enum="ADD_DECLARED_FILE",
        operation_arguments={
            # Intent without completed package/status => FREEZE_INCOMPLETE.
            "content_hex": (
                b'{"audit_id":"WFA-WVMA-B1-CHAIN","contract_marker":'
                b'"weaver_forge_audit_lifecycle_r4b_v1",'
                b'"execution_manifest_digest":"' + b"ab" * 32 + b'",'
                b'"r4_b_expectation_digest":"' + b"cd" * 32 + b'",'
                b'"state":"FREEZE_IN_PROGRESS"}'
            ).hex(),
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.validate_freeze_transaction",
        violation_predicate="freeze_incomplete",
        expected_rejection_predicate="txn_verify_ok_false",
        oracle_observations=("freeze_incomplete",),
        materiality="MATERIAL",
        followup="c07_01_pre_baseline",
    ),
    CaseDef(
        case_id="C07-02",
        property_id="WVMA-C07",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{freeze}/FINAL_DECISION.json",
        operation_enum="DELETE_DECLARED_FILE",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.validate_freeze_transaction",
        violation_predicate="transaction_incomplete",
        expected_rejection_predicate="txn_verify_ok_false",
        oracle_observations=("missing_package_file",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C07-03",
        property_id="WVMA-C07",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/FREEZE_STATUS.json",
        operation_enum="DELETE_DECLARED_FILE",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.validate_freeze_transaction",
        violation_predicate="transaction_incomplete",
        expected_rejection_predicate="txn_verify_ok_false",
        oracle_observations=("status_absent",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C07-04",
        property_id="WVMA-C07",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/FREEZE_STATUS.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/state", "value": "FREEZE_IN_PROGRESS"},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.validate_freeze_transaction",
        violation_predicate="never_classify_frozen",
        expected_rejection_predicate="txn_verify_ok_false",
        oracle_observations=("premature_completion",),
        materiality="MATERIAL",
        followup="c07_04_temp_residue",
    ),
    CaseDef(
        case_id="C08-01",
        property_id="WVMA-C08",
        critical=True,
        baseline_profile=PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/HUMAN_REVIEW.json",
        operation_enum="DELETE_DECLARED_FILE",
        operation_arguments={},
        mutation_timing="PRE_FREEZE",
        verifier_invocation_id="audit.freeze_run",
        violation_predicate="freeze_rejected_missing_review",
        expected_rejection_predicate="freeze_not_ok",
        oracle_observations=("freeze_rejected",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C08-02",
        property_id="WVMA-C08",
        critical=True,
        baseline_profile=PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/HUMAN_REVIEW.json",
        operation_enum="REPLACE_EXACT_BYTES",
        operation_arguments={},  # filled at materialize
        mutation_timing="PRE_FREEZE",
        verifier_invocation_id="audit.freeze_run",
        violation_predicate="conservative_failure_invalid_json",
        expected_rejection_predicate="freeze_not_ok",
        oracle_observations=("invalid_json",),
        materiality="MATERIAL",
        followup="c08_02_args",
    ),
    CaseDef(
        case_id="C08-03",
        property_id="WVMA-C08",
        critical=True,
        baseline_profile=PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/HUMAN_REVIEW.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/status", "value": "REJECTED"},
        mutation_timing="PRE_FREEZE",
        verifier_invocation_id="audit.freeze_run",
        violation_predicate="freeze_rejected_non_accepted",
        expected_rejection_predicate="freeze_not_ok",
        oracle_observations=("status_rejected",),
        materiality="MATERIAL",
    ),
    CaseDef(
        case_id="C08-04",
        property_id="WVMA-C08",
        critical=True,
        baseline_profile=PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/HUMAN_REVIEW.json",
        operation_enum="DELETE_DECLARED_FILE",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="semantic_verification_false",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("review_missing_frozen",),
        materiality="MATERIAL",
        followup="c08_frozen_delete",
    ),
    CaseDef(
        case_id="C08-05",
        property_id="WVMA-C08",
        critical=True,
        baseline_profile=PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/HUMAN_REVIEW.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/status", "value": "REJECTED"},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="semantic_verification_false",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("status_non_accepted_frozen",),
        materiality="MATERIAL",
        followup="c08_frozen_status",
    ),
    CaseDef(
        case_id="C08-UM-01",
        property_id="WVMA-C08",
        critical=False,
        baseline_profile=PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/HUMAN_REVIEW.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={"pointer": "/notes", "value": "UNBOUND_METADATA_ONLY"},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="unbound_metadata_no_violation",
        expected_rejection_predicate="none",
        oracle_observations=("unbound_metadata",),
        materiality="NON_MATERIAL",
        expect_invalid_mutant=True,
        followup="c08_frozen_um",
    ),
    CaseDef(
        case_id="C09-01",
        property_id="WVMA-C09",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/pinned_target/README.txt",
        operation_enum="REPLACE_EXACT_BYTES",
        operation_arguments={},  # filled at materialize
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="actual_expected_hash_mismatch",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("hash_mismatch",),
        materiality="MATERIAL",
        followup="c09_01_args",
    ),
    CaseDef(
        case_id="C09-02",
        property_id="WVMA-C09",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{audit}/CLAIM.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={
            "pointer": "/adapter_params/expected_sha256",
            "value": "ff" * 32,
        },
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="actual_expected_mismatch",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("expected_digest_mismatch",),
        materiality="MATERIAL",
        followup="root_rebind",
    ),
    CaseDef(
        case_id="C10-01",
        property_id="WVMA-C10",
        critical=True,
        baseline_profile=PROFILE_CAMPAIGN_TEST_ONLY,
        mutation_kind="ARTIFACT",
        target_relative_path="{campaign}/CAMPAIGN_STATE.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={},  # filled: false PASS + digest
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="campaign.revalidate",
        violation_predicate="terminal_pass_not_retained",
        expected_rejection_predicate="pass_cleared",
        oracle_observations=("false_pass_cleared",),
        materiality="MATERIAL",
        followup="c10_01_args",
    ),
    CaseDef(
        case_id="C10-02",
        property_id="WVMA-C10",
        critical=True,
        baseline_profile=PROFILE_CAMPAIGN_TEST_ONLY,
        mutation_kind="ARTIFACT",
        target_relative_path="{campaign}/CAMPAIGN_STATE.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={},  # filled at materialize
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="campaign.revalidate",
        violation_predicate="reuse_validation_fails",
        expected_rejection_predicate="pass_cleared",
        oracle_observations=("wrong_evidence_binding",),
        materiality="MATERIAL",
        followup="c10_02_prepare",
    ),
    CaseDef(
        case_id="C10-03",
        property_id="WVMA-C10",
        critical=True,
        baseline_profile=PROFILE_CAMPAIGN_TEST_ONLY,
        mutation_kind="ARTIFACT",
        target_relative_path="{campaign}/EVIDENCE_REGISTER.json",
        operation_enum="SET_JSON_POINTER",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="campaign.revalidate",
        violation_predicate="foreign_entry_no_pass",
        expected_rejection_predicate="no_new_pass",
        oracle_observations=("foreign_evidence",),
        materiality="MATERIAL",
        followup="c10_03_args",
    ),
)


def case_by_id(case_id: str) -> CaseDef:
    for case in CASE_DEFS:
        if case.case_id == case_id:
            return case
    raise KeyError(case_id)


def _rel_under(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def resolve_case_paths(
    workspace: Path, audit_or_campaign: Path, case: CaseDef
) -> dict[str, str]:
    """Resolve path tokens to workspace-relative POSIX paths."""
    ws = workspace.resolve()
    root = audit_or_campaign.resolve()
    tokens: dict[str, str] = {"audit": _rel_under(ws, root), "campaign": _rel_under(ws, root)}
    freeze_dirs = sorted((root / "freeze").glob("*_FROZEN")) if (root / "freeze").is_dir() else []
    if freeze_dirs:
        tokens["freeze"] = _rel_under(ws, freeze_dirs[0])
    reviews = sorted((root / "reviews").glob("*.json")) if (root / "reviews").is_dir() else []
    if reviews:
        tokens["review_first"] = _rel_under(ws, reviews[0])
        tokens["review_second"] = _rel_under(ws, reviews[-1] if len(reviews) > 1 else reviews[0])
    return tokens


def materialize_target_path(template: str, tokens: dict[str, str]) -> str:
    out = template
    for key, value in tokens.items():
        out = out.replace("{" + key + "}", value)
    if "{" in out or "}" in out:
        raise ValueError(f"unresolved path tokens in {template!r} -> {out!r}")
    return out


def _preview_post_bytes(pre: bytes, op: str, args: dict[str, Any]) -> bytes:
    if op == "SET_JSON_POINTER":
        return _compute_set_json(pre, args)
    if op == "DELETE_JSON_POINTER":
        return _compute_delete_json(pre, args)
    if op == "REPLACE_EXACT_BYTES":
        return _compute_replace_bytes(pre, args)
    if op == "REBIND_DECLARED_HASHES":
        return _compute_rebind_hashes(pre, args)
    if op == "ADD_DECLARED_FILE":
        return _content_from_add_args(args)
    if op == "DELETE_DECLARED_FILE":
        return b""
    raise ValueError(f"unsupported op: {op}")


def build_mutation_spec(
    case: CaseDef,
    *,
    target_relative_path: str,
    preimage: str,
    postimage: str,
    operation_arguments: dict[str, Any] | None = None,
) -> MutationSpec:
    args = dict(operation_arguments if operation_arguments is not None else case.operation_arguments)
    return MutationSpec(
        case_id=case.case_id,
        property_id=case.property_id,
        critical=case.critical,
        mutation_kind=case.mutation_kind,
        target_relative_path=target_relative_path,
        expected_preimage_sha256=preimage,
        operation_enum=case.operation_enum,
        operation_arguments=args,
        expected_postimage_sha256=postimage,
        mutation_timing=case.mutation_timing,
        verifier_invocation_id=case.verifier_invocation_id,
        violation_predicate=case.violation_predicate,
        expected_rejection_predicate=case.expected_rejection_predicate,
        oracle_observations=case.oracle_observations,
        materiality=case.materiality,
    )


def prepare_operation_arguments(
    case: CaseDef, workspace: Path, target_rel: str
) -> dict[str, Any]:
    """Fill case-specific operation arguments that depend on baseline bytes."""
    args = dict(case.operation_arguments)
    target = workspace / Path(*target_rel.split("/"))
    follow = case.followup

    if case.case_id == "C04-02" or follow == "c04_02_content":
        from audit_lifecycle.epistemic.review_disagreement import create_disagreement_record
        from audit_lifecycle.epistemic.serialize import canonical_dumps

        rec = create_disagreement_record(
            disagreement_id="D-EXTRA",
            subject_id="WFA-WVMA-B1-CHAIN",
            reviewer_positions=[
                {"reviewer_id": "rev-A", "position": "PASS", "label": "A"},
                {"reviewer_id": "rev-B", "position": "FAIL", "label": "B"},
            ],
            scope="unit",
            category="SPEC_AMBIGUITY",
        )
        content = canonical_dumps(rec.to_dict()).encode("utf-8")
        args = {"content_hex": content.hex()}
        return args

    if case.case_id == "C08-02" or follow == "c08_02_args":
        pre = target.read_bytes()
        # Replace entire file with invalid JSON / non-object.
        find = pre
        repl = b"[1,2,3]"
        args = {"find_hex": find.hex(), "replace_hex": repl.hex()}
        return args

    if case.case_id == "C09-01" or follow == "c09_01_args":
        pre = target.read_bytes()
        # Append unique marker once.
        marker = b"\nWVMA_TAMPER\n"
        if marker in pre:
            raise ValueError("tamper marker already present")
        # REPLACE requires exact one match of find; use a unique substring.
        find = b"third-party-style"
        if pre.count(find) != 1:
            find = pre[:16]
            if pre.count(find) != 1:
                raise ValueError("cannot locate unique replace anchor")
        repl = find + b"X"
        args = {"find_hex": find.hex(), "replace_hex": repl.hex()}
        return args

    if case.case_id == "C10-01" or follow == "c10_01_args":
        from campaign_runner_v0.state_revalidation import compute_state_integrity_digest

        data = json.loads(target.read_text(encoding="utf-8"))
        claims = data.get("claims") or {}
        claim_id = None
        for cid, row in claims.items():
            if row.get("state") != "PASS":
                claim_id = cid
                break
        if claim_id is None and claims:
            claim_id = next(iter(claims))
        if claim_id is None:
            raise ValueError("no claims in CAMPAIGN_STATE")
        side = workspace / ".wvma_c10_01_claim.txt"
        side.write_text(claim_id, encoding="utf-8")
        args = {"pointer": f"/claims/{claim_id}/state", "value": "PASS"}
        return args

    if case.case_id == "C10-02" or follow == "c10_02_prepare":
        data = json.loads(target.read_text(encoding="utf-8"))
        claims = data.get("claims") or {}
        claim_id = next(
            (c for c, r in claims.items() if r.get("state") == "PASS" and r.get("evidence_id")),
            None,
        )
        if claim_id is None:
            raise ValueError("no PASS claim with evidence_id for C10-02")
        # Wrong evidence ID triggers stored_evidence_id_mismatch on revalidation.
        args = {
            "pointer": f"/claims/{claim_id}/evidence_id",
            "value": "reuse:WRONG_AUDIT_ID_WVMA",
        }
        return args

    if case.case_id == "C10-03" or follow == "c10_03_args":
        data = json.loads(target.read_text(encoding="utf-8"))
        entries = data.get("entries") or []
        foreign = {
            "evidence_id": "foreign:WVMA-UNBOUND",
            "claim_id": "FOREIGN-CLAIM-NO-BINDING",
            "kind": "FROZEN_WEAVER_AUDIT_REUSE",
            "package_digest": "aa" * 32,
        }
        args = {"pointer": f"/entries/{len(entries)}", "value": foreign}
        # JSON pointer set into list index == len may fail; use append via replace.
        # Prefer SET on a new last index only if list allows; else replace whole.
        pre = target.read_bytes()
        mutated = json.loads(json.dumps(data))
        mutated.setdefault("entries", []).append(foreign)
        side = workspace / ".wvma_c10_03_post.json"
        side.write_bytes(canonical_bytes(mutated))
        # Switch to REPLACE_EXACT_BYTES for whole-file foreign insert.
        args = {
            "find_hex": pre.hex(),
            "replace_hex": canonical_bytes(mutated).hex(),
        }
        return args

    return args


def apply_case_followup(case: CaseDef, workspace: Path, audit_root: Path) -> None:
    """Code-owned permitted follow-ups (rebind / multi-file isolation)."""
    follow = case.followup
    if follow in {None, "c04_02_content", "c08_02_args", "c09_01_args"}:
        if follow == "c09_01_args" or case.case_id == "C09-01":
            rebind_root_sha256sums(audit_root)
        return
    if follow in {"c01_01", "root_rebind"} or case.case_id in {"C01-01", "C09-02"}:
        # Also flip claim_result for C01-01.
        if case.case_id == "C01-01":
            from audit_lifecycle.request import read_json, write_json

            decision = read_json(audit_root / "DECISION.json")
            decision["claim_result"] = "PASS"
            decision["reason"] = "WVMA_FALSE_PASS"
            write_json(audit_root / "DECISION.json", decision)
        rebind_root_sha256sums(audit_root)
        return
    if follow in {"c01_02", "freeze_rebind", "c08_frozen_delete", "c08_frozen_status", "c08_frozen_um"}:
        if case.case_id == "C01-02":
            from audit_lifecycle.request import read_json, write_json

            freeze = next((audit_root / "freeze").glob("*_FROZEN"))
            fd = read_json(freeze / "FINAL_DECISION.json")
            fd["decision"]["broader_classification"] = "CRYPTO_SUPPORTED_E2E_FULL"
            write_json(freeze / "FINAL_DECISION.json", fd)
        if case.case_id == "C02-01":
            report = audit_root / "RECONSTRUCTABILITY_REPORT.json"
            if report.is_file():
                report.unlink()
            reviews = audit_root / "reviews"
            if reviews.is_dir():
                for p in reviews.glob("*.json"):
                    p.unlink()
            rebind_root_sha256sums(audit_root)
            return
        rebind_freeze_package_hashes(audit_root)
        return
    if follow == "c02_01":
        report = audit_root / "RECONSTRUCTABILITY_REPORT.json"
        if report.is_file():
            report.unlink()
        reviews = audit_root / "reviews"
        if reviews.is_dir():
            for p in reviews.glob("*.json"):
                p.unlink()
        rebind_root_sha256sums(audit_root)
        return
    if follow == "c07_04_temp_residue":
        # Owned temp residue (path starts with '.' — not expressible as sealed
        # relative target under A2 path grammar; created as code-owned follow-up).
        tmp = audit_root / "freeze" / f".wf_freeze_tmp_{audit_root.name}_deadbeef"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "residue.txt").write_text("temp\n", encoding="utf-8")
        return
    if follow == "c07_01_pre_baseline":
        return
    if follow == "c10_02_args" or follow == "c10_02_prepare":
        return
    if follow == "c10_01_args":
        from campaign_runner_v0.state_revalidation import compute_state_integrity_digest
        from audit_lifecycle.request import read_json, write_json

        target = audit_root / "CAMPAIGN_STATE.json"
        st = read_json(target)
        side = workspace / ".wvma_c10_01_claim.txt"
        claim_id = side.read_text(encoding="utf-8").strip() if side.is_file() else None
        if claim_id and claim_id in st.get("claims", {}):
            st["claims"][claim_id] = dict(st["claims"][claim_id])
            st["claims"][claim_id]["reason"] = "WVMA_FALSE_PASS"
        digest = compute_state_integrity_digest(
            st["claims"], st.get("evidence_register") or {}
        )
        st["state_integrity"] = {
            "digest": digest,
            "algorithm": "sha256",
            "covers": ["claims", "evidence_register.entries"],
            "note": "wvma-false-pass",
        }
        write_json(target, st)
        return


def compute_digests_for_target(
    workspace: Path,
    target_rel: str,
    op: str,
    args: dict[str, Any],
) -> tuple[str, str]:
    target = workspace / Path(*target_rel.split("/"))
    if op == "ADD_DECLARED_FILE":
        pre = EMPTY_SHA256
        post = _sha256_bytes(_content_from_add_args(args))
        return pre, post
    if op == "DELETE_DECLARED_FILE":
        pre = _sha256_bytes(target.read_bytes())
        return pre, EMPTY_SHA256
    pre_bytes = target.read_bytes()
    pre = _sha256_bytes(pre_bytes)
    post = _sha256_bytes(_preview_post_bytes(pre_bytes, op, args))
    return pre, post


def apply_case_mutation(
    workspace: Path,
    case: CaseDef,
    audit_or_campaign: Path,
) -> tuple[MutationApplication, MutationSpec, str]:
    """Resolve paths, apply sealed mutation, run follow-ups. Returns app, spec, target_rel."""
    # C08 frozen cases need freeze first.
    if case.case_id in {"C08-04", "C08-05", "C08-UM-01"}:
        from wvma_v1.baselines import attempt_freeze
        from audit_lifecycle.request import read_json

        if not (audit_or_campaign / "FREEZE_STATUS.json").is_file():
            policy = read_json(audit_or_campaign / "AUDIT_REQUEST.json").get("policy") or {}
            outcome = attempt_freeze(audit_or_campaign, policy)
            if not outcome["ok"]:
                raise RuntimeError(f"baseline freeze failed for {case.case_id}: {outcome['error']}")
            rebind_freeze_package_hashes(audit_or_campaign)

    # C08-02 / C09 / C10 need dynamic args from baseline bytes; also C04-02.
    tokens = resolve_case_paths(workspace, audit_or_campaign, case)
    target_rel = materialize_target_path(case.target_relative_path, tokens)

    # C10-03 switches to REPLACE_EXACT_BYTES via prepare args.
    op = case.operation_enum
    args = prepare_operation_arguments(case, workspace, target_rel)
    if case.case_id == "C10-03":
        op = "REPLACE_EXACT_BYTES"
        # Mutate a temporary CaseDef-like apply via direct MutationSpec.
        pre, post = compute_digests_for_target(workspace, target_rel, op, args)
        spec = MutationSpec(
            case_id=case.case_id,
            property_id=case.property_id,
            critical=case.critical,
            mutation_kind=case.mutation_kind,
            target_relative_path=target_rel,
            expected_preimage_sha256=pre,
            operation_enum=op,
            operation_arguments=args,
            expected_postimage_sha256=post,
            mutation_timing=case.mutation_timing,
            verifier_invocation_id=case.verifier_invocation_id,
            violation_predicate=case.violation_predicate,
            expected_rejection_predicate=case.expected_rejection_predicate,
            oracle_observations=case.oracle_observations,
            materiality=case.materiality,
        )
        app = apply_mutation(workspace, spec)
        apply_case_followup(case, workspace, audit_or_campaign)
        return app, spec, target_rel

    pre, post = compute_digests_for_target(workspace, target_rel, op, args)
    if op != case.operation_enum:
        spec = MutationSpec(
            case_id=case.case_id,
            property_id=case.property_id,
            critical=case.critical,
            mutation_kind=case.mutation_kind,
            target_relative_path=target_rel,
            expected_preimage_sha256=pre,
            operation_enum=op,
            operation_arguments=args,
            expected_postimage_sha256=post,
            mutation_timing=case.mutation_timing,
            verifier_invocation_id=case.verifier_invocation_id,
            violation_predicate=case.violation_predicate,
            expected_rejection_predicate=case.expected_rejection_predicate,
            oracle_observations=case.oracle_observations,
            materiality=case.materiality,
        )
    else:
        spec = build_mutation_spec(
            case,
            target_relative_path=target_rel,
            preimage=pre,
            postimage=post,
            operation_arguments=args,
        )
    app = apply_mutation(workspace, spec)
    apply_case_followup(case, workspace, audit_or_campaign)
    return app, spec, target_rel


def build_catalog_document(
    *,
    sealed_digests: dict[str, tuple[str, str, str, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Build catalog mapping. sealed_digests: case_id -> (path, pre, post, args)."""
    mutations: list[dict[str, Any]] = []
    for case in CASE_DEFS:
        if sealed_digests and case.case_id in sealed_digests:
            path, pre, post, args = sealed_digests[case.case_id]
        else:
            # Placeholder digests for structure; seal step replaces with exact.
            path = case.target_relative_path.replace("{", "x").replace("}", "x")
            # Ensure path is schema-valid relative path characters.
            path = "placeholder/" + case.case_id + ".json"
            pre = "11" * 32
            post = "22" * 32
            args = dict(case.operation_arguments) or {"pointer": "/x", "value": None}
            if case.operation_enum == "DELETE_JSON_POINTER":
                args = {"pointer": "/x"}
            elif case.operation_enum == "DELETE_DECLARED_FILE":
                args = {}
            elif case.operation_enum == "ADD_DECLARED_FILE":
                args = dict(case.operation_arguments) or {"content_hex": "00"}
            elif case.operation_enum == "REPLACE_EXACT_BYTES":
                args = {"find_hex": "00", "replace_hex": "01"}
            elif case.operation_enum == "SET_JSON_POINTER" and not args:
                args = {"pointer": "/x", "value": "y"}
        mutations.append(
            {
                "case_id": case.case_id,
                "property_id": case.property_id,
                "critical": case.critical,
                "mutation_kind": case.mutation_kind,
                "target_relative_path": path,
                "expected_preimage_sha256": pre,
                "operation_enum": case.operation_enum
                if case.case_id != "C10-03"
                else "REPLACE_EXACT_BYTES",
                "operation_arguments": args,
                "expected_postimage_sha256": post,
                "mutation_timing": case.mutation_timing,
                "verifier_invocation_id": case.verifier_invocation_id,
                "violation_predicate": case.violation_predicate,
                "expected_rejection_predicate": case.expected_rejection_predicate,
                "oracle_observations": list(case.oracle_observations),
                "materiality": case.materiality,
            }
        )
    critical = [c for c in CRITICAL_CASE_IDS]
    doc: dict[str, Any] = {
        "schema_version": "wvma_v1.catalog.v1",
        "authority": False,
        "catalog_id": CATALOG_ID,
        "catalog_version": CATALOG_VERSION,
        "product_base_sha": PRODUCT_BASE_SHA,
        "runner_contract_version": RUNNER_CONTRACT,
        "oracle_contract_version": ORACLE_CONTRACT,
        "properties": _props(),
        "mutations": mutations,
        "critical_case_ids": critical,
        "catalog_digest": "00" * 32,
    }
    doc["catalog_digest"] = digest_excluding_field(doc, "catalog_digest")
    return doc


def write_catalog(path: Path, doc: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = doc if doc is not None else build_catalog_document()
    # Validate before write.
    strict_parse_catalog(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return payload


CATALOG_PATH = Path(__file__).resolve().parent / "catalogs" / "WVMA_V1_CATALOG.json"

__all__ = [
    "CASE_DEFS",
    "CATALOG_PATH",
    "CRITICAL_CASE_IDS",
    "CaseDef",
    "apply_case_mutation",
    "build_catalog_document",
    "case_by_id",
    "write_catalog",
]
