# SEIC-001 Verification

- Baseline HEAD: `85a948d1cf5df07d2e6dac57da8ca318b2554302`
- Branch: `hardening/seic-001-evaluator-closure`
- Implementation: `audit_lifecycle/epistemic/evaluator_closure.py`
- Focused tests: `audit_lifecycle/tests/test_evaluator_closure.py`
- New subsystem: `NO`
- New authority: `NO`
- New digest domain: `NO`
- CLOSED scope reopened: `NO`

## Focused Results

`python -m unittest audit_lifecycle.tests.test_evaluator_closure -v`

- 36/36 tests passed.
- Unrelated normal source change remained `PASS`.
- Caller semantic input returned `CALLER_SEMANTIC_INPUT`.
- Direct bytes and proposal-local epoch locations were rejected; epoch records
  were loaded only from external trusted test locations.
- Dynamic, unresolved, shadow, generated/unbound read reach returned
  `UNKNOWN_REACH`.
- Checker and ESS declaration proposal edits were non-PASS.
- Cumulative `c_E` comparison blocked commit-split evasion.
- Failure left protected state unchanged.
- Old receipt bytes and digest remained bound to the old epoch.

## Mutation Results

Six focused mutant behaviors were exercised and killed by the corresponding
security oracle:

1. Skip ESS member comparison.
2. Allow a proposal-local checker.
3. Allow a proposal-local ESS declaration.
4. Convert `UNKNOWN_REACH` to `PASS`.
5. Accept caller semantic input.
6. Compare `M(P)` with the proposal parent instead of `c_E`.

Result: `6/6 KILLED`.

## Existing Validation

- `audit_lifecycle.tests.test_epistemic_r4a`,
  `audit_lifecycle.tests.test_epistemic_r4b`, and
  `audit_lifecycle.tests.test_lifecycle`: 231/231 passed on the final full rerun.
- `python scripts/check_ci_supply_chain.py`: passed; 2/2 action refs pinned,
  explicit permissions and GitHub Actions Dependabot configuration present.
- `python scripts/validate_receipts.py`: 15/15 receipt files passed.

The first existing-suite run had one Windows `PermissionError` while the
pre-existing lifecycle code renamed a temporary freeze directory. The affected
T13 test passed immediately in isolation, and the complete 231-test rerun passed.
No implementation change was made for that transient host event.

SEIC validation does not change any existing authority, evidence, Human Final,
runtime authorization, or production status.

## R1 Remediation

Follow-up to the independent review of candidate
`8043629341bc0e6433b78010459208ce667917a6` (2 material, 2 nonmaterial findings).

- Epoch trust anchor: `evaluate_closure` requires `trusted_epoch_sha256`, the
  plain SHA-256 of the exact epoch record bytes from the Human approval record
  outside the proposal tree and epoch file. Missing binding:
  `REQUIRE_HUMAN_REVIEW`; malformed: `INVALID`; mismatch: `EPOCH_MISMATCH`.
  `approval_status` and `human_approval_ref` are descriptive only. Human
  approval is represented by the independently protected binding, not by a
  string inside the epoch file.
- Conservative reach: reachable ESS Python is checked against the closed
  SEIC-v0 evaluator syntax profile. Import bindings are canonicalized through
  aliases; reserved semantic machinery (import machinery, plugin discovery,
  process/environment/filesystem-discovery modules), unsupported builtins,
  star imports, introspection escapes, dynamic attribute access, and
  file/resource access outside literal ESS reads are `UNKNOWN_REACH`. Parent
  packages and `from package import submodule` targets now require ESS.
- Caller semantics: nested, aliased, file-reference, and environment-mapping
  caller inputs are `CALLER_SEMANTIC_INPUT`; caller-derived evaluator reads and
  attribute access are `UNKNOWN_REACH`.
- Cleanup: `_changed_paths_from_parent` was removed from production (the
  parent-comparison mutant is built inside the test). `non_semantic_paths` was
  removed from schema, implementation, docs, and tests.

### R1 Results

`python -m unittest audit_lifecycle.tests.test_evaluator_closure -v`
(with `PYTHONDONTWRITEBYTECODE=1`)

- 58/58 tests passed (36 prior + 22 R1).
- R1 focused coverage: self-declared approval without binding, substituted and
  re-serialized epoch bytes, changed `human_approval_ref` and `approval_status`,
  attacker-selected ESS, `import x as y`, `from x import y as z`, aliased
  `sys.path` mutation, environment/process input, indirect semantic file
  references, nested/indirect caller configuration, generated inputs outside
  ESS, closed-profile rejections, unrelated change control (including
  unsupported syntax outside the evaluator path), and unchanged protected state
  for every new failure case.
- Mutations: 10/10 killed (6 prior plus: bypass external epoch binding, trust
  self-declared approval, alias reach converted to `PASS`, environment semantic
  input converted to `PASS`).
- Existing validation rerun: `test_epistemic_r4a`, `test_epistemic_r4b`,
  `test_lifecycle` 231/231 passed; `scripts/check_ci_supply_chain.py` passed;
  `scripts/validate_receipts.py` 15/15 passed.
- New subsystem: `NO`. New authority: `NO`. New digest domain: `NO`. CLOSED
  scope reopened: `NO`.

## Remaining Limitations

- Python reach analysis is intentionally bounded and conservative; constructs
  outside the closed SEIC-v0 profile fail closed rather than claiming complete
  dependency discovery, so some benign evaluator code may be `UNKNOWN_REACH`.
- The approval binding proves only which exact epoch bytes the caller presents as
  Human-approved; protecting the Human approval record itself is outside v0.
- Local name rebinding and scoping are not modelled; the profile compensates by
  rejecting all unsafe builtins and reserved modules wherever they appear.
- Non-Python evaluator languages are not interpreted by v0.
- External imports must be human-classified as non-semantic in the epoch; SEIC-v0
  does not attest external package integrity.
- Git object availability and local Git correctness are environmental assumptions.
- No production epoch, proposal authorization, or independent reproduction is
  established by these local synthetic tests.

Exact evidence ceiling:
`LOCAL_SEIC_V0_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_AT_PINNED_REPOSITORY_STATE`.
