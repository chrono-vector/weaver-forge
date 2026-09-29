# CODEX_R4_B_FINAL_ROOT_PLAN_0C34815_20260929

## Provenance

| Field | Value |
|-------|-------|
| PLAN_ID | `CODEX_R4_B_FINAL_ROOT_PLAN_0C34815_20260929` |
| CURRENT_SHA | `0c3481571e6daa808c66e15f9b88c779aaff0354` |
| SOURCE | Codex session log |
| SESSION_LOG | `C:\Users\mine0\.codex\sessions\2026\08\22\rollout-2026-08-22T16-51-21-01a02873-efd8-7251-a7a9-ba57a8f33bf5.jsonl` |
| MODE | DOCUMENTATION ONLY |
| AUTHORITY | Descriptive record only — does not alter authority semantics |

This file preserves the exact Codex R4-B final root plan as emitted in the cited
session log, before implementation. It must not be reinterpreted as a redesign.

---

## Authoritative Codex plan (verbatim)

CODEX_R4_B_FINAL_ROOT_PLAN_ID  
`CODEX_R4_B_FINAL_ROOT_PLAN_0C34815_20260929`

CURRENT_SHA  
`0c3481571e6daa808c66e15f9b88c779aaff0354`

**R4B_MONOTONIC_STATE_INVARIANT**
- Add a distinct contract marker: `weaver_forge_audit_lifecycle_r4b_v1`.
- Place it in both `EXECUTION_MANIFEST.json.r4_b` and the frozen `MANIFEST.json`.
- Frozen manifest stores the canonical digest of the complete `r4_b` expectation.
- `FREEZE_STATUS.json` binds the frozen manifest digest, freeze sums digest, and contract marker.
- For frozen runs, the frozen manifest is the state anchor. Root `r4_b` must exist and match its committed digest.
- Removing root `r4_b`, report, or reviews therefore fails rather than selecting legacy.
- Legacy is allowed only when both root and frozen package match a strict, complete pre-R4-B schema. Missing `r4_b` alone is never sufficient.
- Contradictory root/freeze markers fail closed.
- Coordinated deletion or rewriting of every unauthenticated local anchor remains explicitly unclaimed.

**FREEZE_TRANSACTION_INVARIANT**

```text
PRE_FREEZE
  -> FREEZE_IN_PROGRESS
  -> FROZEN
```

Correct order:

1. Validate report and complete disagreement graph.
2. Finalize `EXECUTION_MANIFEST.json.r4_b`; do not claim freeze completion.
3. Write durable `FREEZE_INTENT.json` with contract marker and finalized manifest digest.
4. Bind root evidence.
5. Build the package in a uniquely owned temporary freeze directory.
6. Write final decision, evidence index, frozen manifest, and freeze SHA sums.
7. Validate every package digest and R4-B expectation binding.
8. Atomically rename the temporary package to its final path.
9. Write `FREEZE_STATUS.json` last with `state="FROZEN"` and all package bindings.
10. Rebind root sums. Do not mutate the execution manifest or package afterward.

`stages_completed_through="FREEZE"` and `freeze_performed=true` may appear only in `FREEZE_STATUS.json`, never before step 9.

On interruption:
- Preserve `FREEZE_INTENT.json` and `FAILURE.json`.
- Remove only an owned temporary directory before publication.
- Final package without status, status without package, or incomplete intent is `FREEZE_INCOMPLETE`.
- `verify_ok=false`; no automatic inference of completion or legacy.
- Recovery must validate the complete package before creating status.

**STRICT_CONSTRUCTION_INVARIANT**
- Introduce one `_ABSENT` sentinel for optional constructor parameters.
- Omitted optional value may default.
- Explicit `None`, scalar, string, mapping, or wrong collection must reject unless that exact type is documented.
- Never call `list()`, `tuple()`, `dict()`, `str()`, or falsey fallback before validation.
- Dataclass `__post_init__`, factories, stored parsers, and persistence paths use the same validators.
- Factories finish by parsing their generated dictionary through the canonical strict parser.
- Persistence accepts only canonical parsed objects.

Functions requiring correction:
- `create_disagreement_record`
- `create_successor_record`
- `ReviewDisagreementRecord.__post_init__`
- `strict_parse_record`
- `derive_reconstructability_report`
- `ReconstructabilityReport.__post_init__`
- `ReconstructabilityInputs.__post_init__`
- `strict_parse_report`
- `build_r4b_expectation`
- `R4BExpectation` and `ReconstructabilityExpectation` validation

**ADJACENT_MATERIAL_PATHS_FOUND**
- `is_allowlisted_legacy_manifest` validates only a loose allowed-key subset; a downgraded current manifest qualifies as legacy.
- `verify_run` permits `verify_ok=true` when `freeze_status` and package are both absent, even if the execution manifest claims freeze completion.
- `create_freeze_package` publishes directly into the final directory, exposing partial package state.
- Freeze status/package/manifest contract markers are not cross-validated.
- `list(evidence_refs)` accepts strings and mappings before validation.
- Similar prevalidation conversion exists for reviewer-position and expectation sequences.
- Constructors can return objects containing malformed nested metadata before persistence reparses them.

**FILES_TO_CHANGE**
- `audit_lifecycle/epistemic/expectation.py`
- `audit_lifecycle/epistemic/r4b_verify.py`
- `audit_lifecycle/epistemic/reconstructability.py`
- `audit_lifecycle/epistemic/review_disagreement.py`
- `audit_lifecycle/orchestrator.py`
- `audit_lifecycle/freeze.py`
- `audit_lifecycle/semantic_verification.py`
- `audit_lifecycle/epistemic/__init__.py`
- `audit_lifecycle/tests/test_epistemic_r4b.py`
- `audit_lifecycle/tests/test_lifecycle.py`
- `audit_lifecycle/epistemic/R4_B.md`

**FUNCTIONS_TO_CHANGE**
- Replace loose legacy predicate with `strict_parse_legacy_manifest`.
- Add `classify_frozen_r4b_state(root_manifest, frozen_manifest, freeze_status)`.
- Add `validate_freeze_transaction`.
- Refactor `freeze_run` and `create_freeze_package` to intent, temporary package, validation, atomic publication, then status.
- Make `verify_run` require transaction consistency whenever any freeze marker exists.
- Route every factory through strict field validators and canonical parsers.

**EXACT_CURSOR_IMPLEMENTATION_PLAN**
1. Introduce distinct legacy and R4-B lifecycle contract constants.
2. Require exact legacy manifest fields and types; reject subset-shaped manifests.
3. Add the frozen R4-B marker and expectation digest to frozen manifest and status.
4. Make frozen-state classification depend on mutually consistent root manifest, frozen manifest, and status.
5. Implement the three-state freeze transaction without premature completion fields.
6. Publish the package by atomic directory rename and write status last.
7. Replace constructor conversions with sentinel-based absent/present handling.
8. Harden dataclass initialization and route generated objects through strict parsers.
9. Add downgrade, interruption, partial-package, and constructor Cartesian tests.
10. Rerun all R4-B, R4-A, lifecycle, campaign, and freeze/verify suites.

**ACCEPTANCE_TEST_MATRIX**
- Frozen R4-B minus `r4_b`, report, and reviews plus rebound root hashes: FAIL.
- R4-B marker changed to legacy: FAIL.
- Loose/incomplete legacy manifest: FAIL; genuine historical manifest: PASS.
- Missing intent/package/index/sums/status in every transaction phase: no false `FROZEN`.
- Package without status and status without package: FAIL.
- Manifest claiming freeze without status/package: FAIL.
- No post-index mutation of execution manifest or expected artifacts.
- Every constructor collection/ID field tested with null, Booleans, numbers, string, mapping, mixed list, and wrong collection.
- `evidence_refs="abc"` and `{}`: reject.
- Successor graph, immutable write, expected-set, and non-authority tests remain PASS.
- R4-B 63, R4-A 140, lifecycle 16, campaign 32, and relevant freeze tests all PASS.

VECTOR_CHANGE_REQUIRED:  
NO

EIG_CHANGE_REQUIRED:  
NO

R3_REOPEN_REQUIRED:  
NO

R4_A_REDESIGN_REQUIRED:  
NO

READY_FOR_ONE_FINAL_CURSOR_PASS:  
YES

STOP.
