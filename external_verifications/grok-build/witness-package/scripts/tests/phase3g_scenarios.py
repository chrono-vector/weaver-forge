#!/usr/bin/env python3
"""Phase 3G declarative scenario / lifecycle / mutation framework.

Deterministic, immutable scenario-row model. Phase 3G-A ships the framework
plus minimum smoke rows; Phase 3G-B adds the integrated scenario matrix.
Does not execute Docker, Cargo, product, network, or Witness workflows by
itself — execution lives in phase3g_harness / integration tests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

TESTS_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = TESTS_DIR.parent
PACKAGE_DIR = SCRIPTS_DIR.parent
CONTRACT_PATH = PACKAGE_DIR / "AUTHORITATIVE_OUTCOME_CONTRACT.json"

# Fixed deterministic seed / order identity (Pi-adjudicated). No wall-clock,
# no environment-derived seed, no nondeterministic filesystem ordering.
PHASE3G_DETERMINISTIC_SEED = "phase3g-fixed-seed-v1"
PHASE3G_ORDER_IDENTITY = f"seed={PHASE3G_DETERMINISTIC_SEED};order=scenario_id_asc"

SCENARIO_ROW_FIELDS = frozenset(
    {
        "scenario_id",
        "terminal_outcome",
        "container_facts",
        "host_facts",
        "post_build_facts",
        "expected_validator_result",
        "expected_host_gate",
        "mutations",
        "expected_residue_policy",
        "oracle_bindings",
    }
)

FACT_MAPPING_FIELDS = ("container_facts", "host_facts", "post_build_facts")

# Closed mutation vocabulary for later Phase 3G-B categories (intent only).
MUTATION_VOCABULARY = frozenset(
    {
        "missing_build_exit",
        "empty_build_exit",
        "malformed_build_exit",
        "outcome_disagreement",
        "host_status_failure",
        "post_build_failure",
        "validator_nonzero",
        "validator_fail",
        "validator_malformed_output",
        "stale_run_id",
        "stale_manifest_hash",
        "stale_validator_identity",
        "stale_evidence_path",
        "stale_stdout_capture",
        "stale_stderr_capture",
        "mixed_run_evidence",
        "preliminary_success_yes_injection",
    }
)

# Explicit incompatible-mutation rule: at most one member of each group.
# Documented rule — no silent normalization.
# Stale_* / mixed_run_evidence may combine in Phase 3G-B; they are not grouped here.
INCOMPATIBLE_MUTATION_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"missing_build_exit", "empty_build_exit", "malformed_build_exit"}),
    frozenset({"validator_nonzero", "validator_fail", "validator_malformed_output"}),
)

# Automated preliminary lifecycle (committed host/container flow). Ordered.
LIFECYCLE_TRANSITIONS: tuple[str, ...] = (
    "container_finalization",
    "container_evidence_ownership",
    "host_outcome_ingestion",
    "source_integrity_finalization",
    "post_build_finalization",
    "host_outcome_synchronization",
    "closed_auxiliary_finalization",
    "preliminary_manifest_finalization",
    "host_preliminary_validator",
    "validator_result_creation",
    "final_summary",
    "final_host_exit",
)

LIFECYCLE_PREDECESSORS: dict[str, tuple[str, ...]] = {
    "container_finalization": (),
    "container_evidence_ownership": ("container_finalization",),
    "host_outcome_ingestion": ("container_evidence_ownership",),
    "source_integrity_finalization": ("host_outcome_ingestion",),
    "post_build_finalization": ("source_integrity_finalization",),
    "host_outcome_synchronization": ("post_build_finalization",),
    "closed_auxiliary_finalization": ("host_outcome_synchronization",),
    "preliminary_manifest_finalization": ("closed_auxiliary_finalization",),
    "host_preliminary_validator": ("preliminary_manifest_finalization",),
    "validator_result_creation": ("host_preliminary_validator",),
    "final_summary": ("validator_result_creation",),
    "final_host_exit": ("final_summary",),
}

# Pre-Docker failure path: validator transitions are excluded.
PRE_DOCKER_EXCLUDED_TRANSITIONS = frozenset(
    {
        "host_preliminary_validator",
        "validator_result_creation",
    }
)

# Manual Witness lifecycle is outside this automated model.
MANUAL_WITNESS_LIFECYCLE_EXCLUDED = True
MANUAL_WITNESS_LIFECYCLE_LABEL = "manual_witness_lifecycle"


class ScenarioFrameworkError(ValueError):
    """Framework validation failure with stable scenario_id diagnostics."""

    def __init__(self, message: str, *, scenario_id: str | None = None) -> None:
        sid = scenario_id if scenario_id is not None else "<unknown>"
        super().__init__(
            f"[phase3g scenario_id={sid} {PHASE3G_ORDER_IDENTITY}] {message}"
        )
        self.scenario_id = scenario_id


def load_terminal_outcomes(contract_path: Path | None = None) -> frozenset[str]:
    path = contract_path or CONTRACT_PATH
    data = json.loads(path.read_text(encoding="utf-8"))
    values = {row["value"] for row in data["terminal_outcomes"]}
    return frozenset(values)


TERMINAL_OUTCOMES = load_terminal_outcomes()


def _require_mapping(name: str, value: Any, *, scenario_id: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ScenarioFrameworkError(
            f"{name} must be a mapping, got {type(value).__name__}",
            scenario_id=scenario_id,
        )
    for k in value:
        if not isinstance(k, str):
            raise ScenarioFrameworkError(
                f"{name} keys must be str, got {type(k).__name__}",
                scenario_id=scenario_id,
            )
    return value


def _normalize_mutations(
    raw: Any, *, scenario_id: str
) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        items = (raw,)
    elif isinstance(raw, Sequence) and not isinstance(raw, (bytes, bytearray)):
        items = tuple(raw)
    else:
        raise ScenarioFrameworkError(
            f"mutations must be a sequence of strings, got {type(raw).__name__}",
            scenario_id=scenario_id,
        )
    for m in items:
        if not isinstance(m, str):
            raise ScenarioFrameworkError(
                f"mutation entries must be str, got {type(m).__name__}",
                scenario_id=scenario_id,
            )
        if m not in MUTATION_VOCABULARY:
            raise ScenarioFrameworkError(
                f"unknown mutation {m!r}; closed vocabulary only",
                scenario_id=scenario_id,
            )
    if len(items) != len(set(items)):
        raise ScenarioFrameworkError(
            "duplicate mutations rejected (explicit rule: no silent dedup)",
            scenario_id=scenario_id,
        )
    present = set(items)
    for group in INCOMPATIBLE_MUTATION_GROUPS:
        hit = present & group
        if len(hit) > 1:
            raise ScenarioFrameworkError(
                "incompatible mutation combination rejected by explicit group rule: "
                + ", ".join(sorted(hit)),
                scenario_id=scenario_id,
            )
    # Deterministic mutation ordering: vocabulary sort order among selected.
    return tuple(sorted(items))


def _normalize_oracle_bindings(
    raw: Any, *, scenario_id: str
) -> tuple[tuple[str, Any], ...]:
    if raw is None:
        return ()
    mapping = _require_mapping("oracle_bindings", raw, scenario_id=scenario_id)
    # Deterministic key order for stable representation.
    return tuple((k, mapping[k]) for k in sorted(mapping))


@dataclass(frozen=True)
class ScenarioRow:
    """Immutable scenario row for Phase 3G generator harness."""

    scenario_id: str
    terminal_outcome: str
    container_facts: Mapping[str, Any]
    host_facts: Mapping[str, Any]
    post_build_facts: Mapping[str, Any]
    expected_validator_result: Mapping[str, Any]
    expected_host_gate: Mapping[str, Any]
    mutations: tuple[str, ...]
    expected_residue_policy: Mapping[str, Any]
    oracle_bindings: tuple[tuple[str, Any], ...]

    def diagnostic_prefix(self) -> str:
        return f"[phase3g scenario_id={self.scenario_id} {PHASE3G_ORDER_IDENTITY}]"


def make_scenario_row(raw: Mapping[str, Any]) -> ScenarioRow:
    if not isinstance(raw, Mapping):
        raise ScenarioFrameworkError(
            f"scenario row must be a mapping, got {type(raw).__name__}"
        )
    unknown = set(raw) - SCENARIO_ROW_FIELDS
    if unknown:
        sid = raw.get("scenario_id") if isinstance(raw.get("scenario_id"), str) else None
        raise ScenarioFrameworkError(
            f"unknown top-level scenario field(s): {', '.join(sorted(unknown))}",
            scenario_id=sid,
        )
    missing = SCENARIO_ROW_FIELDS - set(raw)
    if missing:
        sid = raw.get("scenario_id") if isinstance(raw.get("scenario_id"), str) else None
        raise ScenarioFrameworkError(
            f"missing required scenario field(s): {', '.join(sorted(missing))}",
            scenario_id=sid,
        )

    scenario_id = raw["scenario_id"]
    if not isinstance(scenario_id, str) or not scenario_id.strip():
        raise ScenarioFrameworkError(
            "scenario_id must be a nonempty string",
            scenario_id=str(scenario_id) if scenario_id is not None else None,
        )

    terminal_outcome = raw["terminal_outcome"]
    if terminal_outcome not in TERMINAL_OUTCOMES:
        raise ScenarioFrameworkError(
            f"unknown terminal outcome {terminal_outcome!r}; "
            f"legal vocabulary={sorted(TERMINAL_OUTCOMES)}",
            scenario_id=scenario_id,
        )

    facts: dict[str, Mapping[str, Any]] = {}
    for name in FACT_MAPPING_FIELDS:
        facts[name] = dict(_require_mapping(name, raw[name], scenario_id=scenario_id))

    expected_validator_result = dict(
        _require_mapping(
            "expected_validator_result",
            raw["expected_validator_result"],
            scenario_id=scenario_id,
        )
    )
    expected_host_gate = dict(
        _require_mapping(
            "expected_host_gate", raw["expected_host_gate"], scenario_id=scenario_id
        )
    )
    expected_residue_policy = dict(
        _require_mapping(
            "expected_residue_policy",
            raw["expected_residue_policy"],
            scenario_id=scenario_id,
        )
    )
    mutations = _normalize_mutations(raw["mutations"], scenario_id=scenario_id)
    oracle_bindings = _normalize_oracle_bindings(
        raw["oracle_bindings"], scenario_id=scenario_id
    )

    return ScenarioRow(
        scenario_id=scenario_id,
        terminal_outcome=terminal_outcome,
        container_facts=facts["container_facts"],
        host_facts=facts["host_facts"],
        post_build_facts=facts["post_build_facts"],
        expected_validator_result=expected_validator_result,
        expected_host_gate=expected_host_gate,
        mutations=mutations,
        expected_residue_policy=expected_residue_policy,
        oracle_bindings=oracle_bindings,
    )


def compile_scenario_table(rows: Iterable[Mapping[str, Any]]) -> tuple[ScenarioRow, ...]:
    """Validate and return scenarios in deterministic scenario_id ascending order."""
    compiled: list[ScenarioRow] = []
    seen: set[str] = set()
    for raw in rows:
        row = make_scenario_row(raw)
        if row.scenario_id in seen:
            raise ScenarioFrameworkError(
                f"duplicate scenario_id {row.scenario_id!r}",
                scenario_id=row.scenario_id,
            )
        seen.add(row.scenario_id)
        compiled.append(row)
    # Deterministic ordering: scenario_id ascending (seed identity recorded).
    compiled.sort(key=lambda r: r.scenario_id)
    return tuple(compiled)


# Minimum framework smoke rows (not the Phase 3G-B matrix).
_FRAMEWORK_SMOKE_RAW: tuple[dict[str, Any], ...] = (
    {
        "scenario_id": "framework_smoke_build_not_started",
        "terminal_outcome": "BUILD_NOT_STARTED",
        "container_facts": {"cargo_started": "NO"},
        "host_facts": {"host_infrastructure_status": "OK"},
        "post_build_facts": {"status": "FAILED"},
        "expected_validator_result": {"structural_status": "FAIL"},
        "expected_host_gate": {"host_exit": 1},
        "mutations": (),
        "expected_residue_policy": {"prefix": "phase3g_test_", "must_be_absent": True},
        "oracle_bindings": {
            "expected_host_exit": 1,
            "expected_explicit_outcome": "BUILD_NOT_STARTED",
        },
    },
    {
        "scenario_id": "framework_smoke_success_capable",
        "terminal_outcome": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        "container_facts": {"cargo_started": "YES", "artifact_present": "YES"},
        "host_facts": {"host_infrastructure_status": "OK"},
        "post_build_facts": {"status": "OK", "post_build_integrity_ok": "yes"},
        "expected_validator_result": {"structural_status": "PASS"},
        "expected_host_gate": {"host_exit": 0},
        "mutations": ("stale_stdout_capture",),
        "expected_residue_policy": {"prefix": "phase3g_test_", "must_be_absent": True},
        "oracle_bindings": {
            "expected_host_exit": 0,
            "expected_explicit_outcome": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            "expected_preliminary_success_eligible": "NO",
        },
    },
)


def framework_smoke_scenarios() -> tuple[ScenarioRow, ...]:
    return compile_scenario_table(_FRAMEWORK_SMOKE_RAW)


def _row(
    scenario_id: str,
    terminal_outcome: str,
    *,
    container_facts: dict[str, Any] | None = None,
    host_facts: dict[str, Any] | None = None,
    post_build_facts: dict[str, Any] | None = None,
    expected_validator_result: dict[str, Any] | None = None,
    expected_host_gate: dict[str, Any] | None = None,
    mutations: Sequence[str] = (),
    oracle_bindings: dict[str, Any] | None = None,
    path_kind: str = "automated_preliminary",
) -> dict[str, Any]:
    """Build an explicit integrated scenario row (no silent inference)."""
    return {
        "scenario_id": scenario_id,
        "terminal_outcome": terminal_outcome,
        "container_facts": {
            **(container_facts or {}),
            "path_kind": path_kind,
        },
        "host_facts": host_facts or {},
        "post_build_facts": post_build_facts or {},
        "expected_validator_result": expected_validator_result
        or {"structural_status": "FAIL", "invoked": False},
        "expected_host_gate": expected_host_gate or {"host_exit": 1},
        "mutations": tuple(mutations),
        "expected_residue_policy": {
            "prefix": "phase3g_test_",
            "must_be_absent": True,
        },
        "oracle_bindings": {
            "expected_preliminary_success_eligible": "NO",
            **(oracle_bindings or {}),
        },
    }


# Phase 3G-B integrated scenario matrix (Pi-adjudicated categories; not Cartesian).
_INTEGRATED_SCENARIO_RAW: tuple[dict[str, Any], ...] = (
    # --- Five terminal outcomes (sourced-writer chain) ---
    _row(
        "terminal_build_not_started",
        "BUILD_NOT_STARTED",
        container_facts={"cargo_started": "NO", "category": "terminal_outcome"},
        host_facts={"host_infrastructure_status": "OK"},
        post_build_facts={"status": "FAILED"},
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_explicit_outcome": "BUILD_NOT_STARTED",
            "expected_structural_status": "FAIL",
        },
    ),
    _row(
        "terminal_cargo_failed",
        "CARGO_FAILED",
        container_facts={
            "cargo_started": "YES",
            "cargo_exit_code": "17",
            "category": "terminal_outcome",
        },
        host_facts={"host_infrastructure_status": "OK"},
        post_build_facts={"status": "FAILED"},
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_explicit_outcome": "CARGO_FAILED",
            "expected_structural_status": "FAIL",
        },
    ),
    _row(
        "terminal_cargo_succeeded_artifact_missing",
        "CARGO_SUCCEEDED_ARTIFACT_MISSING",
        container_facts={
            "cargo_started": "YES",
            "cargo_exit_code": "0",
            "artifact_present": "NO",
            "category": "terminal_outcome",
        },
        host_facts={"host_infrastructure_status": "OK"},
        post_build_facts={"status": "FAILED"},
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_explicit_outcome": "CARGO_SUCCEEDED_ARTIFACT_MISSING",
            "expected_structural_status": "FAIL",
        },
    ),
    _row(
        "terminal_cargo_succeeded_artifact_present",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={
            "cargo_started": "YES",
            "cargo_exit_code": "0",
            "artifact_present": "YES",
            "category": "success_capable",
        },
        host_facts={
            "host_infrastructure_status": "OK",
            "host_source_integrity_status": "OK",
        },
        post_build_facts={"status": "OK", "post_build_integrity_ok": "yes"},
        expected_validator_result={
            "structural_status": "PASS",
            "invoked": True,
            "process_exit": 0,
        },
        expected_host_gate={"host_exit": 0, "gate_ok": "yes"},
        oracle_bindings={
            "expected_host_exit": 0,
            "expected_explicit_outcome": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            "expected_structural_status": "PASS",
            "expected_validator_exit": 0,
            "expected_evidence_tree_unchanged": True,
        },
    ),
    _row(
        "terminal_infrastructure_failure",
        "INFRASTRUCTURE_FAILURE",
        container_facts={
            "cargo_started": "NO",
            "category": "terminal_outcome",
        },
        host_facts={"host_infrastructure_status": "OK"},
        post_build_facts={"status": "FAILED"},
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_explicit_outcome": "INFRASTRUCTURE_FAILURE",
            "expected_structural_status": "FAIL",
        },
    ),
    # --- Invalid BUILD_EXIT ---
    _row(
        "invalid_build_exit_missing",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "invalid_build_exit", "build_exit_mode": "missing"},
        mutations=("missing_build_exit",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 10,
            "expected_build_exit_bytes": None,
        },
    ),
    _row(
        "invalid_build_exit_empty",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "invalid_build_exit", "build_exit_mode": "empty"},
        mutations=("empty_build_exit",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10, "expected_build_exit_bytes": b""},
    ),
    _row(
        "invalid_build_exit_malformed",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={
            "category": "invalid_build_exit",
            "build_exit_mode": "malformed",
            "malformed_bytes": "not-a-schema\n",
        },
        mutations=("malformed_build_exit",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 10,
            "expected_build_exit_bytes": b"not-a-schema\n",
        },
    ),
    # --- Outcome disagreements ---
    _row(
        "disagreement_cargo_started",
        "BUILD_NOT_STARTED",
        container_facts={
            "category": "outcome_disagreement",
            "disagreement": "cargo_started",
            "force_cargo_started": "YES",
        },
        mutations=("outcome_disagreement",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10},
    ),
    _row(
        "disagreement_cargo_exit_code",
        "CARGO_FAILED",
        container_facts={
            "category": "outcome_disagreement",
            "disagreement": "cargo_exit_code",
            "force_cargo_exit_code": "0",
        },
        mutations=("outcome_disagreement",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10},
    ),
    _row(
        "disagreement_artifact_present",
        "CARGO_SUCCEEDED_ARTIFACT_MISSING",
        container_facts={
            "category": "outcome_disagreement",
            "disagreement": "artifact_present",
            "force_artifact_present": "YES",
        },
        mutations=("outcome_disagreement",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10},
    ),
    _row(
        "disagreement_container_result_validity",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={
            "category": "outcome_disagreement",
            "disagreement": "container_result_validity",
            "force_cargo_started": "NO",
        },
        mutations=("outcome_disagreement",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10},
    ),
    # --- Host / POST_BUILD failures ---
    _row(
        "host_infrastructure_failure",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "host_failure"},
        host_facts={
            "host_infrastructure_status": "FAILED",
            "category": "host_infrastructure_failure",
        },
        mutations=("host_status_failure",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10},
    ),
    _row(
        "source_integrity_failure",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "host_failure"},
        host_facts={
            "host_source_integrity_status": "FAILED",
            "category": "source_integrity_failure",
        },
        mutations=("host_status_failure",),
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 10, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 10},
    ),
    _row(
        "post_build_failure",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "post_build_failure"},
        post_build_facts={"status": "FAILED", "post_build_integrity_ok": "no"},
        mutations=("post_build_failure",),
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_post_build": {"status": "FAILED", "post_build_integrity_ok": "no"},
        },
    ),
    _row(
        "post_build_integrity_flag_mismatch",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "post_build_failure"},
        post_build_facts={
            "status": "OK",
            "post_build_integrity_ok": "no",
            "category": "integrity_flag_mismatch",
        },
        mutations=("post_build_failure",),
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "host_outcome_sync_mismatch",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "host_outcome_sync_mismatch"},
        host_facts={"category": "host_outcome_sync_mismatch"},
        post_build_facts={"status": "OK", "post_build_integrity_ok": "yes"},
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    # --- Real-validator primary / fault categories ---
    _row(
        "validator_structural_fail",
        "CARGO_FAILED",
        container_facts={"category": "validator_real_fail"},
        mutations=("validator_fail",),
        expected_validator_result={"structural_status": "FAIL", "invoked": True},
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_structural_status": "FAIL",
        },
    ),
    _row(
        "validator_nonzero_exit",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "validator_fault"},
        mutations=("validator_nonzero",),
        expected_validator_result={
            "structural_status": "FAIL",
            "invoked": True,
            "process_exit": 7,
        },
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1, "expected_validator_exit": 7},
    ),
    _row(
        "validator_missing_definitive_pass",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "validator_fault"},
        mutations=("validator_malformed_output",),
        expected_validator_result={
            "structural_status": "ABSENT",
            "invoked": True,
            "fault": "missing_pass",
        },
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "validator_contradictory_pass_fail",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "validator_fault", "fault": "contradictory"},
        mutations=("validator_malformed_output",),
        expected_validator_result={
            "structural_status": "CONTRADICTORY",
            "invoked": True,
        },
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "validator_multiple_pass_lines",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "validator_fault", "fault": "multiple_pass"},
        mutations=("validator_malformed_output",),
        expected_validator_result={
            "structural_status": "CONTRADICTORY",
            "invoked": True,
        },
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    # --- Stale / spoof / mixed-run mutations ---
    _row(
        "mutation_stale_run_id",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("stale_run_id",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_stale_manifest_hash",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("stale_manifest_hash",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_stale_validator_identity",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("stale_validator_identity",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_stale_evidence_path",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("stale_evidence_path",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_stale_stdout_capture",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("stale_stdout_capture",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_stale_stderr_capture",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("stale_stderr_capture",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_mixed_run_evidence",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("mixed_run_evidence",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 1},
    ),
    _row(
        "mutation_preliminary_success_yes_injection",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "stale_mutation"},
        mutations=("preliminary_success_yes_injection",),
        expected_host_gate={"host_exit": 1, "gate_ok": "no"},
        oracle_bindings={
            "expected_host_exit": 1,
            "expected_preliminary_success_eligible": "NO",
        },
    ),
    # --- Pre-Docker no-validator invariant ---
    _row(
        "pre_docker_no_validator",
        "INFRASTRUCTURE_FAILURE",
        container_facts={"category": "pre_docker"},
        path_kind="pre_docker_failure",
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 3, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 3},
    ),
    # --- Limited full-main smoke markers (executed by harness adapters) ---
    _row(
        "full_main_fail_closed_smoke",
        "INFRASTRUCTURE_FAILURE",
        container_facts={"category": "full_main_fail_closed"},
        path_kind="pre_docker_failure",
        expected_validator_result={"structural_status": "ABSENT", "invoked": False},
        expected_host_gate={"host_exit": 3, "gate_ok": "no"},
        oracle_bindings={"expected_host_exit": 3},
    ),
    _row(
        "full_main_success_capable_smoke",
        "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
        container_facts={"category": "full_main_success_capable"},
        host_facts={"host_infrastructure_status": "OK"},
        post_build_facts={"status": "OK", "post_build_integrity_ok": "yes"},
        expected_validator_result={"structural_status": "PASS", "invoked": True},
        expected_host_gate={"host_exit": 0, "gate_ok": "yes"},
        oracle_bindings={
            "expected_host_exit": 0,
            "expected_explicit_outcome": "CARGO_SUCCEEDED_ARTIFACT_PRESENT",
            "expected_structural_status": "PASS",
        },
    ),
)


def integrated_scenarios() -> tuple[ScenarioRow, ...]:
    """Phase 3G-B integrated scenario table (deterministic scenario_id ascending)."""
    return compile_scenario_table(_INTEGRATED_SCENARIO_RAW)


def all_phase3g_scenarios() -> tuple[ScenarioRow, ...]:
    """Framework smoke rows plus integrated Phase 3G-B rows."""
    return compile_scenario_table(
        list(_FRAMEWORK_SMOKE_RAW) + list(_INTEGRATED_SCENARIO_RAW)
    )


@dataclass(frozen=True)
class LifecycleTransition:
    name: str
    predecessors: tuple[str, ...]
    fail_closed: bool = True


def lifecycle_transition_catalog() -> tuple[LifecycleTransition, ...]:
    return tuple(
        LifecycleTransition(
            name=name,
            predecessors=LIFECYCLE_PREDECESSORS[name],
            fail_closed=True,
        )
        for name in LIFECYCLE_TRANSITIONS
    )


@dataclass
class LifecycleMachine:
    """Declarative transition validator (does not execute production lifecycle)."""

    completed: list[str]
    path_kind: str  # "automated_preliminary" | "pre_docker_failure"
    terminal_exit_recorded: bool

    def __init__(self, *, path_kind: str = "automated_preliminary") -> None:
        if path_kind not in {"automated_preliminary", "pre_docker_failure"}:
            raise ScenarioFrameworkError(f"unknown lifecycle path_kind {path_kind!r}")
        self.completed = []
        self.path_kind = path_kind
        self.terminal_exit_recorded = False

    def apply(self, transition: str) -> None:
        if transition == MANUAL_WITNESS_LIFECYCLE_LABEL:
            raise ScenarioFrameworkError(
                "manual Witness lifecycle is excluded from the automated model"
            )
        if transition not in LIFECYCLE_PREDECESSORS:
            raise ScenarioFrameworkError(f"unknown lifecycle transition {transition!r}")
        if (
            self.path_kind == "pre_docker_failure"
            and transition in PRE_DOCKER_EXCLUDED_TRANSITIONS
        ):
            raise ScenarioFrameworkError(
                f"pre-Docker failure path excludes validator transition {transition!r}"
            )
        if transition == "final_host_exit" and self.terminal_exit_recorded:
            raise ScenarioFrameworkError(
                "duplicate final_host_exit transition rejected"
            )
        preds = LIFECYCLE_PREDECESSORS[transition]
        # For pre_docker_failure, skip predecessor checks that involve excluded steps
        # by requiring only non-excluded predecessors that appear in the legal prefix.
        for pred in preds:
            if (
                self.path_kind == "pre_docker_failure"
                and pred in PRE_DOCKER_EXCLUDED_TRANSITIONS
            ):
                continue
            if pred not in self.completed:
                raise ScenarioFrameworkError(
                    f"transition-before-predecessor rejected: {transition!r} "
                    f"requires {pred!r}"
                )
        self.completed.append(transition)
        if transition == "final_host_exit":
            self.terminal_exit_recorded = True

    def apply_chain(self, transitions: Sequence[str]) -> None:
        for t in transitions:
            self.apply(t)


def validate_mutations(mutations: Sequence[str], *, scenario_id: str = "n/a") -> tuple[str, ...]:
    return _normalize_mutations(list(mutations), scenario_id=scenario_id)
