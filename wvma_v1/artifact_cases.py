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
    build_audit_human_review_prefreeze,
    build_audit_r4b_review_chain,
    build_audit_r4b_zero_review,
    build_campaign_test_only,
    rebind_freeze_package_hashes,
    rebind_root_sha256sums,
    _pin_campaign_state,
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
        # Sealed as one REPLACE producing final DECISION (decision/claim_result/reason).
        operation_enum="REPLACE_EXACT_BYTES",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="decision_mismatch",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("decision_mismatch", "semantic_ok_false"),
        materiality="MATERIAL",
        followup="root_rebind",
    ),
    CaseDef(
        case_id="C01-02",
        property_id="WVMA-C01",
        critical=True,
        baseline_profile=PROFILE_AUDIT_R4B_ZERO_REVIEW,
        mutation_kind="ARTIFACT",
        target_relative_path="{freeze}/FINAL_DECISION.json",
        # Sealed as one REPLACE producing final FINAL_DECISION fields.
        operation_enum="REPLACE_EXACT_BYTES",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="audit.verify_semantics",
        violation_predicate="final_decision_mismatch",
        expected_rejection_predicate="semantic_ok_false",
        oracle_observations=("final_decision_mismatch", "semantic_ok_false"),
        materiality="MATERIAL",
        followup="freeze_rebind",
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
        # Sealed as one REPLACE producing final false-PASS + integrity fields.
        operation_enum="REPLACE_EXACT_BYTES",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="campaign.revalidate",
        violation_predicate="terminal_pass_not_retained",
        expected_rejection_predicate="pass_cleared",
        oracle_observations=("false_pass_cleared",),
        materiality="MATERIAL",
        followup=None,
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
        operation_enum="REPLACE_EXACT_BYTES",
        operation_arguments={},
        mutation_timing="PRE_VERIFY",
        verifier_invocation_id="campaign.revalidate",
        violation_predicate="foreign_entry_no_pass",
        expected_rejection_predicate="no_new_pass",
        oracle_observations=("foreign_evidence",),
        materiality="MATERIAL",
        followup=None,
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


def _final_replace_args(pre_bytes: bytes, final_obj: dict[str, Any]) -> dict[str, Any]:
    """Build REPLACE_EXACT_BYTES args that yield canonical final JSON bytes."""
    final_bytes = canonical_bytes(final_obj)
    return {"find_hex": pre_bytes.hex(), "replace_hex": final_bytes.hex()}


def prepare_operation_arguments(
    case: CaseDef, workspace: Path, target_rel: str
) -> dict[str, Any]:
    """Derive sealed operation arguments from a deterministic baseline.

    Runtime application does not call this — the committed catalog is authority.
    This helper exists only for catalog sealing / tooling.
    """
    args = dict(case.operation_arguments)
    target = workspace / Path(*target_rel.split("/"))

    if case.case_id == "C01-01":
        pre = target.read_bytes()
        data = json.loads(pre.decode("utf-8"))
        data["decision"] = "PASS"
        data["claim_result"] = "PASS"
        data["reason"] = "WVMA_FALSE_PASS"
        return _final_replace_args(pre, data)

    if case.case_id == "C01-02":
        pre = target.read_bytes()
        data = json.loads(pre.decode("utf-8"))
        decision = dict(data.get("decision") or {})
        decision["promoted_to_full"] = True
        decision["broader_classification"] = "CRYPTO_SUPPORTED_E2E_FULL"
        data["decision"] = decision
        return _final_replace_args(pre, data)

    if case.case_id == "C04-02":
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
        return {"content_hex": content.hex()}

    if case.case_id == "C08-02":
        pre = target.read_bytes()
        return {"find_hex": pre.hex(), "replace_hex": b"[1,2,3]".hex()}

    if case.case_id == "C09-01":
        pre = target.read_bytes()
        find = b"third-party-style"
        if pre.count(find) != 1:
            find = pre[:16]
            if pre.count(find) != 1:
                raise ValueError("cannot locate unique replace anchor")
        return {"find_hex": find.hex(), "replace_hex": (find + b"X").hex()}

    if case.case_id == "C10-01":
        from campaign_runner_v0.state_revalidation import compute_state_integrity_digest

        pre = target.read_bytes()
        data = json.loads(pre.decode("utf-8"))
        claims = data.get("claims") or {}
        claim_id = next(
            (cid for cid, row in claims.items() if row.get("state") != "PASS"),
            next(iter(claims), None),
        )
        if claim_id is None:
            raise ValueError("no claims in CAMPAIGN_STATE")
        row = dict(claims[claim_id])
        row["state"] = "PASS"
        row["reason"] = "WVMA_FALSE_PASS"
        claims = dict(claims)
        claims[claim_id] = row
        data["claims"] = claims
        digest = compute_state_integrity_digest(
            claims, data.get("evidence_register") or {}
        )
        data["state_integrity"] = {
            "digest": digest,
            "algorithm": "sha256",
            "covers": ["claims", "evidence_register.entries"],
            "note": "wvma-false-pass",
        }
        return _final_replace_args(pre, data)

    if case.case_id == "C10-02":
        data = json.loads(target.read_text(encoding="utf-8"))
        claims = data.get("claims") or {}
        claim_id = next(
            (
                cid
                for cid, row in claims.items()
                if row.get("state") == "PASS" and row.get("evidence_id")
            ),
            None,
        )
        if claim_id is None:
            raise ValueError("no PASS claim with evidence_id for C10-02")
        return {
            "pointer": f"/claims/{claim_id}/evidence_id",
            "value": "reuse:WRONG_AUDIT_ID_WVMA",
        }

    if case.case_id == "C10-03":
        data = json.loads(target.read_text(encoding="utf-8"))
        foreign = {
            "evidence_id": "foreign:WVMA-UNBOUND",
            "claim_id": "FOREIGN-CLAIM-NO-BINDING",
            "kind": "FROZEN_WEAVER_AUDIT_REUSE",
            "package_digest": "aa" * 32,
        }
        pre = target.read_bytes()
        mutated = json.loads(json.dumps(data))
        mutated.setdefault("entries", []).append(foreign)
        return {
            "find_hex": pre.hex(),
            "replace_hex": canonical_bytes(mutated).hex(),
        }

    return args


def apply_case_followup(
    case: CaseDef,
    workspace: Path,
    audit_root: Path,
    *,
    sealed_target_rel: str | None = None,
) -> None:
    """Code-owned permitted follow-ups (rebind / multi-file isolation).

    Must never rewrite ``sealed_target_rel`` after the sealed final postimage.
    """
    follow = case.followup
    target_path = (
        workspace / Path(*sealed_target_rel.split("/"))
        if sealed_target_rel
        else None
    )
    target_digest_before = (
        _sha256_bytes(target_path.read_bytes())
        if target_path is not None and target_path.is_file()
        else None
    )

    if follow in {None, "c04_02_content", "c08_02_args", "c09_01_args"}:
        if follow == "c09_01_args" or case.case_id == "C09-01":
            rebind_root_sha256sums(audit_root)
    elif follow == "root_rebind" or case.case_id == "C09-02":
        rebind_root_sha256sums(audit_root)
    elif follow in {
        "freeze_rebind",
        "c08_frozen_delete",
        "c08_frozen_status",
        "c08_frozen_um",
    }:
        if case.case_id == "C02-01":
            report = audit_root / "RECONSTRUCTABILITY_REPORT.json"
            if report.is_file():
                report.unlink()
            reviews = audit_root / "reviews"
            if reviews.is_dir():
                for path in reviews.glob("*.json"):
                    path.unlink()
            rebind_root_sha256sums(audit_root)
        else:
            rebind_freeze_package_hashes(audit_root)
    elif follow == "c02_01":
        report = audit_root / "RECONSTRUCTABILITY_REPORT.json"
        if report.is_file():
            report.unlink()
        reviews = audit_root / "reviews"
        if reviews.is_dir():
            for path in reviews.glob("*.json"):
                path.unlink()
        rebind_root_sha256sums(audit_root)
    elif follow == "c07_04_temp_residue":
        # Owned temp residue (path starts with '.' — not expressible as sealed
        # relative target under A2 path grammar; created as code-owned follow-up).
        tmp = audit_root / "freeze" / f".wf_freeze_tmp_{audit_root.name}_deadbeef"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "residue.txt").write_text("temp\n", encoding="utf-8")
    elif follow in {"c07_01_pre_baseline", "c10_02_prepare", "c10_02_args", "c10_03_args"}:
        pass

    if (
        target_path is not None
        and target_digest_before is not None
        and target_path.is_file()
    ):
        after = _sha256_bytes(target_path.read_bytes())
        if after != target_digest_before:
            raise RuntimeError(
                f"follow-up rewrote sealed target for {case.case_id}: "
                f"{sealed_target_rel}"
            )


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


def load_committed_catalog() -> Any:
    """Load and strict-parse the committed sealed catalog document."""
    if not CATALOG_PATH.is_file():
        raise FileNotFoundError(f"committed catalog missing: {CATALOG_PATH}")
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return strict_parse_catalog(raw)


def sealed_mutation_spec(case_id: str) -> MutationSpec:
    """Return the committed catalog MutationSpec for ``case_id``."""
    return load_committed_catalog().mutation_by_case_id(case_id)


def _baseline_for_case(case: CaseDef, workspace: Path) -> Path:
    if case.baseline_profile == PROFILE_AUDIT_R4B_ZERO_REVIEW:
        if case.case_id == "C01-01":
            return build_audit_r4b_zero_review(
                workspace,
                audit_id="WFA-WVMA-B1-ZERO",
                force_fail=True,
                freeze=False,
            )
        return build_audit_r4b_zero_review(
            workspace,
            audit_id="WFA-WVMA-B1-ZERO",
            force_fail=False,
            freeze=True,
        )
    if case.baseline_profile == PROFILE_AUDIT_R4B_REVIEW_CHAIN:
        return build_audit_r4b_review_chain(workspace, audit_id="WFA-WVMA-B1-CHAIN")
    if case.baseline_profile == PROFILE_AUDIT_HUMAN_REVIEW_PREFREEZE:
        root, _req = build_audit_human_review_prefreeze(
            workspace, audit_id="WFA-WVMA-B1-HR", with_accepted_review=True
        )
        return root
    if case.baseline_profile == PROFILE_CAMPAIGN_TEST_ONLY:
        return build_campaign_test_only(
            workspace,
            campaign_id=f"wvma_b1_{case.case_id.replace('-', '_').lower()}",
        )
    raise ValueError(case.baseline_profile)


def _prepare_case_baseline(
    case: CaseDef, workspace: Path, audit_or_campaign: Path
) -> Path:
    """Freeze C08 frozen mutants before sealed path resolution when needed."""
    if case.case_id in {"C08-04", "C08-05", "C08-UM-01"}:
        from audit_lifecycle.request import read_json
        from wvma_v1.baselines import attempt_freeze

        if not (audit_or_campaign / "FREEZE_STATUS.json").is_file():
            policy = read_json(audit_or_campaign / "AUDIT_REQUEST.json").get("policy") or {}
            outcome = attempt_freeze(audit_or_campaign, policy)
            if not outcome["ok"]:
                raise RuntimeError(
                    f"baseline freeze failed for {case.case_id}: {outcome['error']}"
                )
    return audit_or_campaign


def apply_case_mutation(
    workspace: Path,
    case: CaseDef,
    audit_or_campaign: Path,
) -> tuple[MutationApplication, MutationSpec, str]:
    """Apply the committed sealed catalog mutation; fail closed on any mismatch."""
    sealed = sealed_mutation_spec(case.case_id)
    audit_or_campaign = _prepare_case_baseline(case, workspace, audit_or_campaign)
    if case.baseline_profile == PROFILE_CAMPAIGN_TEST_ONLY:
        # Baseline campaign.revalidate rewrites invocation, clock, and workspace.
        # Re-pin before the sealed preimage is read.
        _pin_campaign_state(audit_or_campaign)
    tokens = resolve_case_paths(workspace, audit_or_campaign, case)
    target_rel = materialize_target_path(case.target_relative_path, tokens)

    if target_rel != sealed.target_relative_path:
        raise RuntimeError(
            f"{case.case_id} path mismatch: exercised={target_rel!r} "
            f"sealed={sealed.target_relative_path!r}"
        )
    if sealed.operation_enum != case.operation_enum:
        raise RuntimeError(
            f"{case.case_id} operation mismatch: case={case.operation_enum} "
            f"sealed={sealed.operation_enum}"
        )

    actual_pre, _preview_post = compute_digests_for_target(
        workspace,
        target_rel,
        sealed.operation_enum,
        dict(sealed.operation_arguments),
    )
    if actual_pre != sealed.expected_preimage_sha256:
        raise RuntimeError(
            f"{case.case_id} preimage mismatch: actual={actual_pre} "
            f"sealed={sealed.expected_preimage_sha256}"
        )

    app = apply_mutation(workspace, sealed)
    if app.postimage_sha256 != sealed.expected_postimage_sha256:
        raise RuntimeError(
            f"{case.case_id} applied postimage mismatch: "
            f"actual={app.postimage_sha256} sealed={sealed.expected_postimage_sha256}"
        )

    apply_case_followup(
        case,
        workspace,
        audit_or_campaign,
        sealed_target_rel=sealed.target_relative_path,
    )

    # Final target digest must still equal sealed postimage after follow-ups.
    target = workspace / Path(*sealed.target_relative_path.split("/"))
    if sealed.operation_enum == "DELETE_DECLARED_FILE":
        final = EMPTY_SHA256
        if target.exists():
            raise RuntimeError(f"{case.case_id} deleted target still present")
    else:
        if not target.is_file():
            raise RuntimeError(f"{case.case_id} sealed target missing after apply")
        final = _sha256_bytes(target.read_bytes())
    if final != sealed.expected_postimage_sha256:
        raise RuntimeError(
            f"{case.case_id} final target digest mismatch: "
            f"actual={final} sealed={sealed.expected_postimage_sha256}"
        )
    return app, sealed, sealed.target_relative_path


def compute_sealed_entries() -> dict[str, tuple[str, str, str, dict[str, Any], str]]:
    """Compute sealed (path, pre, post, args, operation) for every CaseDef."""
    import tempfile

    sealed: dict[str, tuple[str, str, str, dict[str, Any], str]] = {}
    for case in CASE_DEFS:
        with tempfile.TemporaryDirectory(prefix=f"wvma-seal-{case.case_id}-") as td:
            workspace = Path(td) / "ws"
            workspace.mkdir()
            root = _baseline_for_case(case, workspace)
            root = _prepare_case_baseline(case, workspace, root)
            tokens = resolve_case_paths(workspace, root, case)
            target_rel = materialize_target_path(case.target_relative_path, tokens)
            op = (
                "REPLACE_EXACT_BYTES"
                if case.case_id == "C10-03"
                else case.operation_enum
            )
            args = prepare_operation_arguments(case, workspace, target_rel)
            pre, post = compute_digests_for_target(workspace, target_rel, op, args)
            # Apply once and confirm final digest equals computed postimage
            # (no same-file follow-up may alter the sealed target).
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
            apply_mutation(workspace, spec)
            apply_case_followup(
                case, workspace, root, sealed_target_rel=target_rel
            )
            target = workspace / Path(*target_rel.split("/"))
            if op == "DELETE_DECLARED_FILE":
                final = EMPTY_SHA256
            else:
                final = _sha256_bytes(target.read_bytes())
            if final != post:
                raise RuntimeError(
                    f"seal {case.case_id}: final {final} != post {post}"
                )
            sealed[case.case_id] = (target_rel, pre, post, args, op)
    return sealed


def build_catalog_document(
    *,
    sealed_digests: dict[str, tuple[str, str, str, dict[str, Any], str]]
    | dict[str, tuple[str, str, str, dict[str, Any]]]
    | None = None,
) -> dict[str, Any]:
    """Build catalog mapping from sealed digests (no placeholders).

    When ``sealed_digests`` is omitted, re-emit the committed catalog document
    if present and free of placeholders; otherwise compute sealed entries.
    """
    entries: dict[str, tuple[str, str, str, dict[str, Any], str]]
    if sealed_digests is None:
        if CATALOG_PATH.is_file():
            committed = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            raw_mutations = committed.get("mutations") or []
            has_placeholder = any(
                str(row.get("target_relative_path", "")).startswith("placeholder/")
                or row.get("expected_preimage_sha256") == "11" * 32
                or row.get("expected_postimage_sha256") == "22" * 32
                for row in raw_mutations
            )
            if not has_placeholder and raw_mutations:
                # Recompute digest fields for a deterministic re-emit.
                entries = {}
                for row in raw_mutations:
                    entries[row["case_id"]] = (
                        row["target_relative_path"],
                        row["expected_preimage_sha256"],
                        row["expected_postimage_sha256"],
                        dict(row["operation_arguments"]),
                        row["operation_enum"],
                    )
            else:
                entries = compute_sealed_entries()
        else:
            entries = compute_sealed_entries()
    else:
        entries = {}
        for case_id, payload in sealed_digests.items():
            if len(payload) == 5:
                entries[case_id] = payload  # type: ignore[assignment]
            else:
                path, pre, post, args = payload  # type: ignore[misc]
                case = case_by_id(case_id)
                op = (
                    "REPLACE_EXACT_BYTES"
                    if case_id == "C10-03"
                    else case.operation_enum
                )
                entries[case_id] = (path, pre, post, args, op)

    mutations: list[dict[str, Any]] = []
    for case in CASE_DEFS:
        if case.case_id not in entries:
            raise ValueError(f"missing sealed entry for {case.case_id}")
        path, pre, post, args, op = entries[case.case_id]
        if path.startswith("placeholder/"):
            raise ValueError(f"placeholder path not allowed: {path}")
        if pre == "11" * 32 or post == "22" * 32:
            raise ValueError(f"dummy digest not allowed for {case.case_id}")
        mutations.append(
            {
                "case_id": case.case_id,
                "property_id": case.property_id,
                "critical": case.critical,
                "mutation_kind": case.mutation_kind,
                "target_relative_path": path,
                "expected_preimage_sha256": pre,
                "operation_enum": op,
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
        "critical_case_ids": list(CRITICAL_CASE_IDS),
        "catalog_digest": "00" * 32,
    }
    doc["catalog_digest"] = digest_excluding_field(doc, "catalog_digest")
    return doc


def write_catalog(path: Path, doc: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = doc if doc is not None else build_catalog_document()
    # Validate before write.
    strict_parse_catalog(payload)
    for row in payload.get("mutations") or []:
        if str(row.get("target_relative_path", "")).startswith("placeholder/"):
            raise ValueError("refusing to write catalog with placeholder paths")
        if row.get("expected_preimage_sha256") == "11" * 32:
            raise ValueError("refusing to write catalog with dummy preimage")
        if row.get("expected_postimage_sha256") == "22" * 32:
            raise ValueError("refusing to write catalog with dummy postimage")
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
    "compute_sealed_entries",
    "load_committed_catalog",
    "sealed_mutation_spec",
    "write_catalog",
]
