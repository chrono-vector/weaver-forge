"""WVMA-V1 package identity.

Nonclaims: WVMA does not authorize Weaver outcomes, admit evidence, establish
identity/independence, modify Human Final, or change VECTOR/EIG/R3/R4.
"""

from wvma_v1.canonical import (
    canonical_bytes,
    canonical_digest,
    digest_excluding_field,
    sha256_file,
)
from wvma_v1.models import (
    AttemptState,
    AttemptVerdict,
    CaseResult,
    Catalog,
    CatalogError,
    MutationSpec,
    OracleResult,
    PropertySpec,
    ResultClass,
    SchemaError,
    WVMAStatus,
    strict_parse_case_result,
    strict_parse_catalog,
    strict_parse_status,
)
from wvma_v1.state import (
    ReplayError,
    StateError,
    create_attempt,
    create_recovery_attempt,
    derive_attempt_state,
    finalize_attempt,
    publish_case_result,
    seal_catalog,
    verify_attempt,
    write_finalize_intent,
)

# Batch A2 surfaces (confinement / runner / oracle). Imported lazily-safe as
# modules; symbols re-exported for package discoverability only.
from wvma_v1.workspace import WorkspaceError  # noqa: E402
from wvma_v1.mutations import MutationError, apply_mutation  # noqa: E402
from wvma_v1.runner import (  # noqa: E402
    InvocationContract,
    ProcessReceipt,
    RunnerError,
    run_baseline,
    run_mutation_case,
)
from wvma_v1.oracle import (  # noqa: E402
    OracleError,
    derive_result_class,
    evaluate_case,
)

__all__ = [
    "canonical_bytes",
    "canonical_digest",
    "sha256_file",
    "digest_excluding_field",
    "SchemaError",
    "CatalogError",
    "StateError",
    "ReplayError",
    "ResultClass",
    "AttemptState",
    "AttemptVerdict",
    "PropertySpec",
    "MutationSpec",
    "Catalog",
    "CaseResult",
    "OracleResult",
    "WVMAStatus",
    "strict_parse_catalog",
    "strict_parse_case_result",
    "strict_parse_status",
    "seal_catalog",
    "create_attempt",
    "publish_case_result",
    "write_finalize_intent",
    "finalize_attempt",
    "verify_attempt",
    "derive_attempt_state",
    "create_recovery_attempt",
    "WorkspaceError",
    "MutationError",
    "apply_mutation",
    "RunnerError",
    "InvocationContract",
    "ProcessReceipt",
    "run_baseline",
    "run_mutation_case",
    "OracleError",
    "evaluate_case",
    "derive_result_class",
]
