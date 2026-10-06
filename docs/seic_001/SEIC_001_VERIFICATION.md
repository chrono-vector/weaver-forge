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

- 69/69 tests passed (36 original + 22 R1 + 11 R2).
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

Twelve focused mutant behaviors were exercised and killed by the corresponding
security oracle:

1. Skip ESS member comparison.
2. Allow a proposal-local checker.
3. Allow a proposal-local ESS declaration.
4. Convert `UNKNOWN_REACH` to `PASS`.
5. Accept caller semantic input.
6. Compare `M(P)` with the proposal parent instead of `c_E`.
7. Bypass the external exact-byte epoch binding.
8. Trust self-declared epoch approval.
9. Convert aliased semantic reach to `PASS`.
10. Convert environment-derived semantic input to `PASS`.
11. Remove the unconditional getattr-family rejection.
12. Reinstate the literal-name getattr exemption.

Result: `12/12 KILLED`.

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

These `58/58` and `10/10` values are the historical R1 checkpoint. The final
R2 totals are recorded below.

## R2 Final Closure

R2 candidate: `28c09d005c3002f518523856f01515fd957f33d7`.

- Final focused tests: `69/69 PASS`.
- Final focused mutations: `12/12 KILLED`.
- `getattr`, `setattr`, and `delattr` calls or references inside reachable
  evaluator code produce `UNKNOWN_REACH`; no literal-name or safe-receiver
  exemption exists in v0.
- `hasattr`, `operator.attrgetter`, `operator.methodcaller`, and applicable
  dunder attribute access such as `__dict__` are treated conservatively as
  `UNKNOWN_REACH`.
- The concrete indirect `getattr(io, "open")` semantic-read path, including a
  caller-derived or non-literal path, is closed.
- The external exact-byte `trusted_epoch_sha256` trust binding remains intact.
  Epoch contents cannot authenticate themselves, and self-declared approval is
  not trusted.
- Both material findings from the R1 review are closed. The final focused Codex
  review found `0` new material findings and recommended
  `ACCEPT_WITH_NONMATERIAL_LIMITATIONS`.
- Conservative overblocking is intentional and remains non-authoritative. It
  does not create approval, correctness, Human Final, or production permission.

## Remaining Limitations

- Conservative overblocking is intentional in v0; benign evaluator code outside
  the closed profile may produce `UNKNOWN_REACH`.
- No safe-receiver getattr model exists; the getattr family fails closed.
- Local name rebinding and scope analysis remain limited.
- Third-party non-semantic import classification remains Human-controlled;
  SEIC-v0 does not attest external package integrity.
- Protection of the Human approval record supplying `trusted_epoch_sha256` is
  outside v0.
- Non-Python evaluators are not interpreted.
- No production authorization is established. These local synthetic tests also
  do not establish independent reproduction.

Exact evidence ceiling:
`LOCAL_SEIC_V0_IMPLEMENTATION_AND_SYNTHETIC_VALIDATION_AT_PINNED_REPOSITORY_STATE`.
