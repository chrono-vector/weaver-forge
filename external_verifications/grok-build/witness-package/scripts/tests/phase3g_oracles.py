#!/usr/bin/env python3
"""Phase 3G oracle comparison model (3G-A framework).

Scenario rows state expected results explicitly. This module does not
recompute production host-exit boolean logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

from phase3g_scenarios import ScenarioFrameworkError

# Closed oracle binding names for later Phase 3G-B checks.
ORACLE_BINDING_NAMES = frozenset(
    {
        "expected_host_exit",
        "expected_explicit_outcome",
        "expected_host_outcome",
        "expected_post_build",
        "expected_validator_exit",
        "expected_structural_status",
        "expected_preliminary_success_eligible",
        "expected_build_exit_bytes",
        "expected_manifest_sha256",
        "expected_validator_result_bindings",
        "expected_evidence_tree_unchanged",
        "expected_residue_absent",
    }
)


class OracleComparisonKind(Enum):
    """Distinct comparison kinds — not interchangeable."""

    BYTE_EQUALITY = "exact_byte_equality"
    FILE_SET_EQUALITY = "exact_file_set_equality"
    SCHEMA_FIELD_EQUALITY = "exact_schema_field_equality"
    SEMANTIC_STATUS_EQUALITY = "semantic_status_equality"
    SHA256_EQUALITY = "sha256_equality"


# Default comparison kind per oracle binding name.
ORACLE_COMPARISON_BY_BINDING: Mapping[str, OracleComparisonKind] = {
    "expected_host_exit": OracleComparisonKind.SEMANTIC_STATUS_EQUALITY,
    "expected_explicit_outcome": OracleComparisonKind.SEMANTIC_STATUS_EQUALITY,
    "expected_host_outcome": OracleComparisonKind.SCHEMA_FIELD_EQUALITY,
    "expected_post_build": OracleComparisonKind.SCHEMA_FIELD_EQUALITY,
    "expected_validator_exit": OracleComparisonKind.SEMANTIC_STATUS_EQUALITY,
    "expected_structural_status": OracleComparisonKind.SEMANTIC_STATUS_EQUALITY,
    "expected_preliminary_success_eligible": OracleComparisonKind.SEMANTIC_STATUS_EQUALITY,
    "expected_build_exit_bytes": OracleComparisonKind.BYTE_EQUALITY,
    "expected_manifest_sha256": OracleComparisonKind.SHA256_EQUALITY,
    "expected_validator_result_bindings": OracleComparisonKind.SCHEMA_FIELD_EQUALITY,
    "expected_evidence_tree_unchanged": OracleComparisonKind.FILE_SET_EQUALITY,
    "expected_residue_absent": OracleComparisonKind.FILE_SET_EQUALITY,
}


@dataclass(frozen=True)
class OracleExpectation:
    binding_name: str
    comparison_kind: OracleComparisonKind
    expected: Any

    def compare(self, actual: Any) -> bool:
        kind = self.comparison_kind
        if kind is OracleComparisonKind.BYTE_EQUALITY:
            if isinstance(self.expected, str):
                exp = self.expected.encode("utf-8")
            else:
                exp = self.expected
            if isinstance(actual, str):
                act = actual.encode("utf-8")
            else:
                act = actual
            return exp == act
        if kind is OracleComparisonKind.FILE_SET_EQUALITY:
            return set(self.expected) == set(actual)
        if kind is OracleComparisonKind.SCHEMA_FIELD_EQUALITY:
            if not isinstance(self.expected, Mapping) or not isinstance(actual, Mapping):
                return False
            return dict(self.expected) == dict(actual)
        if kind is OracleComparisonKind.SEMANTIC_STATUS_EQUALITY:
            return self.expected == actual
        if kind is OracleComparisonKind.SHA256_EQUALITY:
            return str(self.expected).lower() == str(actual).lower()
        raise ScenarioFrameworkError(f"unhandled comparison kind {kind!r}")


def make_oracle_expectation(
    binding_name: str, expected: Any, *, scenario_id: str = "n/a"
) -> OracleExpectation:
    if binding_name not in ORACLE_BINDING_NAMES:
        raise ScenarioFrameworkError(
            f"unknown oracle binding {binding_name!r}",
            scenario_id=scenario_id,
        )
    return OracleExpectation(
        binding_name=binding_name,
        comparison_kind=ORACLE_COMPARISON_BY_BINDING[binding_name],
        expected=expected,
    )


def oracle_expectations_from_bindings(
    bindings: Mapping[str, Any] | tuple[tuple[str, Any], ...],
    *,
    scenario_id: str = "n/a",
) -> tuple[OracleExpectation, ...]:
    if isinstance(bindings, tuple):
        items = bindings
    else:
        items = tuple((k, bindings[k]) for k in sorted(bindings))
    out: list[OracleExpectation] = []
    for name, value in items:
        out.append(make_oracle_expectation(name, value, scenario_id=scenario_id))
    return tuple(out)


def distinct_comparison_kinds() -> frozenset[OracleComparisonKind]:
    return frozenset(OracleComparisonKind)


def assert_oracles_do_not_recompute_host_exit(
    expected_host_exit: Any,
    *,
    other_fields: Mapping[str, Any],
) -> None:
    """Framework invariant: expected_host_exit is explicit, not derived here.

    Production exit logic must not be reimplemented. This helper only verifies
    that a caller-supplied expected_host_exit is present as a declared value and
    that this module does not synthesize it from other_fields.
    """
    if expected_host_exit is None:
        raise ScenarioFrameworkError(
            "expected_host_exit must be stated explicitly on the scenario row"
        )
    # Deliberately ignore other_fields for derivation — presence is diagnostic only.
    _ = other_fields


@dataclass(frozen=True)
class OracleObservation:
    """One declared binding compared with an observation from a real run."""

    binding_name: str
    expected: Any
    actual: Any
    matched: bool


def evaluate_oracle_bindings(
    bindings: Mapping[str, Any] | tuple[tuple[str, Any], ...],
    actual_values: Mapping[str, Any],
    *,
    scenario_id: str = "n/a",
) -> tuple[OracleObservation, ...]:
    """Compare declared scenario bindings to observations only.

    In particular, ``expected_host_exit`` is compared as supplied by the test;
    this helper never derives an exit/gate value from other observations.
    """
    observations: list[OracleObservation] = []
    for expectation in oracle_expectations_from_bindings(
        bindings, scenario_id=scenario_id
    ):
        if expectation.binding_name not in actual_values:
            raise ScenarioFrameworkError(
                f"missing actual observation for {expectation.binding_name!r}",
                scenario_id=scenario_id,
            )
        actual = actual_values[expectation.binding_name]
        observations.append(
            OracleObservation(
                binding_name=expectation.binding_name,
                expected=expectation.expected,
                actual=actual,
                matched=expectation.compare(actual),
            )
        )
    return tuple(observations)


def assert_oracle_bindings(
    bindings: Mapping[str, Any] | tuple[tuple[str, Any], ...],
    actual_values: Mapping[str, Any],
    *,
    scenario_id: str = "n/a",
) -> tuple[OracleObservation, ...]:
    """Evaluate bindings and raise a stable diagnostic for the first mismatch."""
    observations = evaluate_oracle_bindings(
        bindings, actual_values, scenario_id=scenario_id
    )
    for observed in observations:
        if not observed.matched:
            raise ScenarioFrameworkError(
                f"oracle mismatch {observed.binding_name}: "
                f"expected={observed.expected!r} actual={observed.actual!r}",
                scenario_id=scenario_id,
            )
    return observations
