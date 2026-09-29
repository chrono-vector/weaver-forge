# CODEX_WVMA_V1_FINAL_PLAN_20260929

**PLAN_STATUS**  
FINAL IMPLEMENTATION-AUTHORITATIVE PLAN; coordination review pending; not saved or implemented.

**SCOPE**  
Implement a bounded, local, non-authoritative mutation-assurance system that determines whether selected Weaver security verifiers reject intentional violations. Product baseline: `6140502e915c9668960d00aef7fcd48fd14cc69f`.

**NONCLAIMS**  
WVMA does not prove correctness, complete security, truth, external independence, trusted identity, evidence admissibility, production readiness, hostile-host safety, publication readiness, deployment readiness, or Human Final.

## FROZEN_CRITICAL_PROPERTY_LIST

| ID | Security invariant | Target | Mutation family | Required detection and oracle observation | Consequence |
|---|---|---|---|---|---|
| `WVMA-C01` | Stored decision text cannot override recomputed semantics | `semantic_verification.py`, `orchestrator.verify_run` | False `DECISION` or `FINAL_DECISION`, including rebound hashes | `semantic_ok=false`, `verify_ok=false`; oracle independently confirms stored claim conflicts with target bytes | Any non-detection is MATERIAL |
| `WVMA-C02` | Frozen R4-B cannot downgrade to legacy | `expectation.py`, `r4b_verify.py` | Remove root `r4_b`, report, and reviews; rebind mutable hashes; contradictory markers | R4-B state classification or transaction fails | MATERIAL |
| `WVMA-C03` | Reconstructability is recomputed, not trusted as stored text | `reconstructability.py` | Alter report fields/digest and rebind outer hashes | Exact semantic comparison fails; oracle confirms stored report differs from canonical inputs | MATERIAL |
| `WVMA-C04` | Disagreement records equal the committed complete set and valid chain | `review_disagreement.py` | Delete record, add undeclared record, break successor, duplicate ID | Expected-set or chain verification fails | MATERIAL |
| `WVMA-C05` | R4 artifacts cannot claim authority or fabricate admitted independence | `authority.py`, `provenance.py`, `reconstructability.py` | `authority:true`, positive independent count, admission other than `NOT_CONFIGURED` | Strict parse or semantic recomputation fails | MATERIAL |
| `WVMA-C06` | PRESENT-invalid structured values never receive defaults or coercion | R4 canonical parsers/factories | `None`, Boolean, scalar, string-as-list, mapping-as-list; source mutation introducing coercion | Parser rejects exact malformed value; source mutant causes property tests to fail | MATERIAL |
| `WVMA-C07` | Freeze completion requires a complete transaction | `freeze.py`, `expectation.validate_freeze_transaction` | Missing intent/package/status/manifest/index/sums; temp residue; premature completion fields | State is `FREEZE_INCOMPLETE`, never `FROZEN`; `verify_ok=false` | MATERIAL |
| `WVMA-C08` | Required Human Review cannot be omitted or forged into acceptance | `review_gate.py`, freeze/semantic verification | Remove review, malformed review, mismatched review binding | Freeze or verification rejects; no final package accepted | MATERIAL |
| `WVMA-C09` | Source/target identity remains semantically bound | `pin.py`, `hash_claim.py`, semantic verification | Substitute pinned bytes or expected digest; optionally rebind inventories | Claim recomputation fails; oracle hashes actual target independently | MATERIAL |
| `WVMA-C10` | Campaign state or foreign campaign evidence cannot create PASS | `state_revalidation.py`, campaign evidence bindings | Stored PASS without evidence; wrong campaign/reuse binding | Terminal state rejected/cleared; no PASS retained | MATERIAL |
| `WVMA-C11` | Top-level verification cannot ignore semantic or transaction failure | `orchestrator.verify_run` | Source mutation removes one required conjunction or defaults error to success | Independent canary produces `verify_ok=true` only in mutant; oracle classifies `SURVIVED` | MATERIAL |

Excluded from V1: cryptographic identity, witness authenticity, key revocation, generalized mutation generation, probabilistic fuzzing, memory drift, domain-specific promotion policies, network/provider mutation, and hostile-host testing.

## ARTIFACT_MUTATION_BOUNDARY

Allowed targets are newly generated files inside a digest-bound disposable audit or campaign copy: decision documents, R4 reports, disagreement records, manifests, indexes, sums, status/intent files, pinned targets, campaign state, and evidence registers.

Allowed operations are closed enums only: `SET_JSON_POINTER`, `DELETE_JSON_POINTER`, `ADD_DECLARED_FILE`, `DELETE_DECLARED_FILE`, `REPLACE_EXACT_BYTES`, and case-specific `REBIND_DECLARED_HASHES`.

Mutations occur only after a valid baseline artifact is generated. Every case records preimage digest, mutation operation, postimage digest, and affected relative path.

Forbidden targets: active checkout, `.git`, accepted frozen packages, historical evidence, closure/Human Final records, private archives, credentials, external repositories, VECTOR, and EIG.

## SOURCE_CODE_MUTATION_BOUNDARY

Source mutations operate only on a tracked-file export of the pinned source revision under the disposable root. V1 uses exact, catalogued, single-match replacements with fixed preimage and expected postimage digests.

Allowlisted targets are limited to modules named by `WVMA-C06` and `WVMA-C11`. The runner, oracle, catalog, tests, and status writer must remain outside the mutated tree.

No generic arbitrary patch, script, command, AST rewrite, or catalog-supplied executable is allowed. Zero matches, multiple matches, unexpected preimage, or unexpected postimage produces `APPLY_ERROR`.

The disposable source tree is deleted only after immutable attempt results and protection checks are complete.

## MUTANT_VALIDITY_MODEL

A case is a valid mutation only when all four proofs exist:

1. Exact mutation application is confirmed by pre/post digests.
2. An unmutated oracle confirms the intended invariant is actually violated.
3. The catalogued verifier entry point was exercised from the disposable target.
4. The expected security rejection was observed.

`EQUIVALENT_MUTANT`: violation cannot be demonstrated; classify `INVALID_MUTANT`.  
`INVALID_MUTANT`: malformed case or no relevant property change; never a kill.  
`NON_APPLIED_MUTANT`: classify `APPLY_ERROR`.  
`PARTIALLY_APPLIED_MUTANT`: classify `APPLY_ERROR`; never execute as valid.

Arbitrary test failure is not sufficient for `DETECTED`.

## ORACLE_INTERFACE

**Inputs:** catalog/case digest, source revision, clean baseline receipt, pre/post inventories, mutation proof, exact argv/cwd, allowlisted environment metadata, exit code, stdout/stderr digests, verifier result files, and filesystem observations.

**Outputs:** `case_id`, `mutation_valid`, `property_violated`, `verifier_exercised`, `expected_rejection_observed`, result class, observation list, errors, and canonical oracle-result digest.

The oracle independently:

- hashes source and artifacts;
- validates the mutation predicate;
- checks module/entry-point origin;
- checks process exit and result fields;
- recomputes property-specific observations;
- compares expected and actual filesystem state.

It never trusts runner PASS text, stored kill labels, target-verifier classification, or mutated code output alone.

“Independent” means unmutated code separation and independent recomputation inside WVMA. It does not mean an external witness or independent reproduction.

## TRUST_MODEL

Trusted inputs are the pinned Git revision, clean tracked-tree export, sealed catalog, unmutated runner/oracle revisions, explicit test command contract, and operator-selected output root. Stored results, mutated code, local usernames, witness names, and self-asserted receipts are untrusted.

## AUTHORITY_MODEL

Every WVMA record has `authority:false`. WVMA may report that a technical assurance claim is blocked. It cannot authorize action, admit evidence, establish identity or independence, alter Weaver outcomes, modify Human Final, or change publication/deployment state.

## STATE_MODEL

Canonical states:

```text
NOT_CONFIGURED
  -> CATALOG_SEALED
  -> RUN_IN_PROGRESS
  -> RUN_COMPLETE | RUN_INCOMPLETE | RUN_INVALID
```

`RUN_COMPLETE` requires exactly one verdict:

```text
ALL_CRITICAL_DETECTED
CRITICAL_SURVIVOR
```

Only `WVMA_STATUS.json`, written last after full validation, establishes terminal state. Artifact presence never implies state.

## ATTEMPT_MODEL

Attempt ID: `WVMA-<UTC_BASIC>-<8_HEX_NONCE>`.

Each append-only attempt binds:

- attempt ID;
- catalog ID/digest;
- product source revision/tree digest;
- runner revision/digest;
- oracle revision/digest;
- baseline receipt digest;
- protected-path inventory digest;
- start/completion timestamps;
- immutable case-result references;
- final attempt-root digest.

An attempt directory is exclusive-create and cannot be reused or overwritten.

## RECOVERY_MODEL

Interrupted or failed attempts remain immutable as incomplete evidence. Recovery creates a new attempt with `prior_attempt_id` and prior attempt-root digest. Recovery never edits, promotes, or deletes the previous attempt.

Temporary directories owned by an incomplete attempt may be removed only after verifying ownership token, confinement, and absence of a published completed status.

## REPLAY_MODEL

A previous result may be referenced for comparison only when source, catalog, runner, oracle, and environment contract digests match exactly. It cannot satisfy current execution requirements or be counted as a new detection.

Duplicate attempt IDs, result digests under a different case, foreign-catalog cases, and cross-campaign evidence bindings are rejected.

## FAIL_CLOSED_RESULT_MODEL

Case result classes:

- `DETECTED`
- `SURVIVED`
- `INVALID_MUTANT`
- `APPLY_ERROR`
- `EXECUTION_ERROR`
- `ORACLE_ERROR`
- `MISSING_RESULT`

For every critical V1 case, only `DETECTED` satisfies acceptance. Every other class blocks `ALL_CRITICAL_DETECTED`. `SURVIVED` is a material blocker. Errors and missing results never default to PASS.

Baseline failure produces `RUN_INVALID`; mutation execution must not begin.

## DISPOSABLE_ROOT_MODEL

The runner creates a new exclusive disposable root outside the active repository. Inputs are produced from a pinned tracked-tree export and independently inventoried.

All reads/writes resolve beneath the disposable root. Absolute paths, traversal, symlinks, junctions, reparse points, and aliases escaping that root are rejected for parent and leaf components.

Before and after every attempt, record and compare:

- `ACTIVE_SOURCE_UNCHANGED`
- `FROZEN_HISTORY_UNCHANGED`
- `ACCEPTED_EVIDENCE_UNCHANGED`

Failure to establish any of these prevents a valid completed status.

## CATALOG_SCHEMA

Required fields:

```text
schema_version
authority=false
catalog_id
catalog_version
product_base_sha
runner_contract_version
oracle_contract_version
properties[]
mutations[]
critical_case_ids[]
catalog_digest
```

Each mutation requires:

```text
case_id
property_id
critical=true
mutation_kind
target_relative_path
expected_preimage_sha256
operation_enum
operation_arguments
expected_postimage_sha256
mutation_timing
verifier_invocation_id
violation_predicate
expected_rejection_predicate
oracle_observations[]
materiality
```

Unknown fields and duplicate IDs reject. Catalog digest uses canonical JSON excluding only its own digest field.

## RESULT_SCHEMA

Each immutable case result contains:

```text
schema_version
authority=false
attempt_id
catalog_digest
case_id
property_id
result_class
mutation_proof
violation_proof
verifier_exercise_proof
process_observation
filesystem_observations
digest_observations
oracle_result
started_at
completed_at
result_digest
```

Present malformed fields reject; no falsey coercion or synthesized stored digest is allowed.

## STATUS_SCHEMA

`WVMA_STATUS.json` requires:

```text
schema_version
authority=false
attempt_id
catalog_digest
source_revision
runner_digest
oracle_digest
state
verdict              # RUN_COMPLETE only
baseline_receipt_digest
case_result_digests[]
result_counts
blocking_case_ids[]
attempt_root_digest
completed_at
status_digest
```

`verdict` is forbidden outside `RUN_COMPLETE`. Missing or contradictory fields reject.

## WVMA_A_DESIGN

WVMA-A delivers strict schemas/parsers, canonical serialization, sealed catalog loading, append-only state/attempt handling, disposable-root confinement, mutation application, runner execution, oracle recomputation, result publication, and status-last transaction semantics.

WVMA-A contains no critical product mutation catalog beyond minimal synthetic fixtures needed to prove its own machinery.

## WVMA_B_DESIGN

WVMA-B implements only `WVMA-C01` through `WVMA-C11`, with fixed artifact and source mutations. Every case has a direct property-specific oracle and at least one negative test proving that self-reported success cannot create `DETECTED`.

No runtime mutation discovery or unbounded enumeration is permitted.

## CAMPAIGN_ISOLATION_DECISION

DEFER.

Current campaign tests write transient outputs, but this does not materially prevent deterministic WVMA execution because baseline and mutation tests run inside disposable tracked-tree exports. Campaign cleanup remains a separate nonmaterial engineering task.

## FILES_AND_MODULES

All implementation files are additive:

| File | Ownership | Purpose |
|---|---|---|
| `wvma_v1/__init__.py` | New | Package identity and nonclaims |
| `wvma_v1/__main__.py` | New | `python -m wvma_v1` entry |
| `wvma_v1/cli.py` | New | Minimal `seal`, `run`, `verify` commands |
| `wvma_v1/canonical.py` | New | Canonical JSON and digest rules |
| `wvma_v1/models.py` | New | Strict catalog/result/status parsers |
| `wvma_v1/state.py` | New | State machine, intent, status-last publication |
| `wvma_v1/workspace.py` | New | Disposable-root and protected-path enforcement |
| `wvma_v1/mutations.py` | New | Closed mutation operations |
| `wvma_v1/runner.py` | New | Baseline and mutation process orchestration |
| `wvma_v1/oracle.py` | New | Unmutated property-specific observations |
| `wvma_v1/catalogs/WVMA_V1_CATALOG.json` | New | Sealed C01-C11 catalog |
| `wvma_v1/tests/` | New | Focused unit/adversarial/integration tests |

No accepted R4 module is modified. No root packaging change is required; invocation remains module-based.

## IMPLEMENTATION_BATCHES

**Batch 0 — Fixed baseline preflight**  
Start from the mechanically saved plan commit whose parent is `6140502…` and whose only baseline delta is this plan. Require clean worktree. Stop on any other delta.

**Batch A1 — Contracts and state**  
Add canonicalization, strict models, catalog parser, state machine, append-only attempts, and transaction tests. Stop unless malformed, downgrade, partial, and replay cases fail closed.

**Batch A2 — Confinement, runner, oracle**  
Add disposable export, protected inventories, process receipts, oracle interface, and synthetic fixtures. Stop on any write escape, oracle coupling, or inability to prove unchanged protected state.

**Batch B1 — Artifact mutation catalog**  
Implement artifact cases for C01-C10 with exact pre/post digests and direct oracle tests. Stop if any critical case is invalid, equivalent, or non-deterministic.

**Batch B2 — Source mutation and integrated acceptance**  
Implement C06/C11 source mutants, run all WVMA tests and existing relevant regressions, perform direct adversarial reproductions, and publish an implementation review candidate. No Human Final automation.

Each batch starts from the exact accepted prior-batch commit recorded by the Owner and a clean worktree.

## TEST_MATRIX

- Unit: canonical digests, strict schemas, duplicate/unknown rejection.
- State machine: every valid and invalid transition.
- Parser: ABSENT versus PRESENT-invalid Cartesian cases.
- Runner: exact command, exit, timeout, module origin, environment allowlist.
- Oracle: false runner labels and false verifier self-reports rejected.
- Mutant validity: equivalent, invalid, unapplied, and partial mutants.
- Adversarial: every C01-C11 mutation and expected rejection.
- Transaction: interruption before/after intent, result publication, and status.
- Replay: duplicate attempt, foreign catalog, stale source, mismatched oracle.
- Regression: R4-A, R4-B, lifecycle, and full campaign tests in disposable export.
- Manual: C01, C02, C07, C10, and C11 independently reproduced.

Test quantity alone is not an acceptance signal.

## ADVERSARIAL_MATRIX

Required direct attacks:

- False stored PASS plus rebound digests.
- R4-B expectation/report/reviews removed plus rebound root hashes.
- Positive independent-evidence fabrication.
- Partial freeze package/status/intent combinations.
- Human-review-required freeze without accepted review.
- Pinned target substitution.
- Foreign campaign evidence reused for PASS.
- Mutated `verify_ok` conjunction.
- Runner emits fake `DETECTED` while oracle observations disagree.
- Result/status deletion or downgrade.
- Attempt replay under changed catalog/source/oracle.
- Path traversal or reparse escape from disposable root.

## ACCEPTANCE_MATRIX

WVMA-V1 implementation is acceptable only when:

- fixed baseline and clean worktree confirmed;
- catalog digest exact;
- baseline regressions pass before mutation;
- canonical transitions and strict parsers pass;
- ABSENT/PRESENT-invalid behavior is correct;
- disposable confinement holds;
- every critical mutation is exactly applied;
- every intended violation is independently confirmed;
- every relevant verifier is exercised;
- every C01-C11 result is `DETECTED`;
- survivor/error/missing/invalid cases block acceptance;
- replay, downgrade, and partial states reject;
- attempts are append-only;
- active source and historical artifacts remain unchanged;
- all WVMA artifacts retain `authority:false`;
- Human Final, VECTOR, EIG, R3, and R4 remain unchanged.

## STOP_CONDITIONS

STOP implementation if any of these becomes necessary:

- VECTOR or EIG modification;
- reopening R3 or R4;
- changing Human Final semantics;
- trusted identity or evidence admission;
- Operational Hardening;
- mutation of accepted evidence;
- unbounded mutation enumeration;
- oracle execution from mutated code;
- unsound equivalent-mutant handling;
- unexpected baseline SHA/delta;
- inability to enforce disposable confinement;
- unresolved architecture ambiguity.

## DEFERRED_ITEMS

Trusted reviewer identity, signatures, evidence admission, independent reproduction, witness authenticity, knowledge/memory, source-drift lifecycle, cross-campaign provenance registry, campaign-output cleanup, key custody, ACL hardening, production signing, deployment, hostile-host assurance, and generalized mutation generation.

**PLAN_FILE_PATH**  
`docs/next/CODEX_WEAVER_VERIFIER_MUTATION_ASSURANCE_V1_PLAN_20260929.md`  
Not created.

VECTOR_CHANGE_REQUIRED: NO  
EIG_CHANGE_REQUIRED: NO  
R3_REOPEN_REQUIRED: NO  
R4_REOPEN_REQUIRED: NO  
HUMAN_FINAL_BOUNDARY_CHANGED: NO

MATERIAL_OPEN_QUESTIONS: NONE

READY_FOR_MECHANICAL_PLAN_SAVE: YES

STOP.