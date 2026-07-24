# Phase 3G — Generator/harness integration implementation note

## Scope of this note

This note records **Phase 3G-A** (Pi-adjudicated generator/harness framework)
and **Phase 3G-B** (integrated lifecycle scenarios, mutations, real-validator
primary cases, limited full-main smoke). Phase 3G is complete pending Pi
conformance; Phase 3G-C is not authorized.

Owner Option A remained in force: `CLAIM_REGISTER.md` and broad public-status
documents were not modified.

## Repository base

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (pre-change base) | `bbf087c74485789fee4e496bd9657e2a6d27085b` |
| origin/main (pre-change) | `bbf087c74485789fee4e496bd9657e2a6d27085b` |
| Prior phase | Phase 3F-B at same HEAD |
| rc5 | absent |
| Historical tags | `grok-build-witness-v1.0.0-rc1` … `rc4` present; unchanged |

## Cursor implementation-side options analysis

Cursor independently derived Phase 3G as generator-backed behavioral coverage
over the Phase 3C–3F automated preliminary lifecycle, with options spanning:

- Integration boundary (fixture-only vs sourced writers vs full-main)
- Validator treatment (mock-primary vs real-local primary)
- Generator architecture (ad-hoc cases vs declarative scenario table +
  lifecycle/mutations)
- Host-main treatment (sourced-only vs limited full-main smoke)
- Runtime immutability vs runtime edits for testability
- Single-commit vs two-stage 3G-A/3G-B sequencing

## Pi independent adjudication

Pi independently selected:

| Dimension | Selection |
|-----------|-----------|
| Integration boundary | **E** — layered sourced-writer integration plus limited full-main smoke with the real local validator |
| Validator treatment | **C** — real local validator is primary; mocks remain only for parser/fault-unit tests |
| Generator architecture | **F** — declarative scenario table + lifecycle/state transitions + mutation/fault injection |
| Host-main treatment | **C** — sourced functions are primary; limited full-main smoke is mandatory in Phase 3G-B |
| Runtime immutability | **B** — runtime may change only if a real defect is exposed and a new Pi adjudication authorizes it |
| Commit sequencing | **B** — Phase 3G-A framework, then Phase 3G-B integrated scenarios |

## Selected architecture (summary)

- Boundary **E**, validator **C**, generator **F**, host-main **C**, runtime
  immutability **B**, two-stage **3G-A / 3G-B** sequencing.

## Phase 3G-A purpose

Create the deterministic generator/harness framework and test the framework
itself. Do **not** populate the Phase 3G-B integrated scenario matrix. Do **not**
execute a successful real host Witness workflow. Do **not** advance RC4B-018 or
RC4B-040 to implemented status.

## Exact files added (Phase 3G-A)

### Framework / support modules

- `external_verifications/grok-build/witness-package/scripts/tests/phase3g_scenarios.py`
- `external_verifications/grok-build/witness-package/scripts/tests/phase3g_oracles.py`
- `external_verifications/grok-build/witness-package/scripts/tests/phase3g_harness.py`

### Focused framework tests

- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3g_framework.py`

### This note

- `external_verifications/grok-build/evidence/rc5-remediation/PHASE_3G_GENERATOR_INTEGRATION_IMPLEMENTATION_NOTE.md`

### Explicitly unchanged (prohibited / deferred)

- `run_witness_narrow_build.sh`, `container_narrow_build.sh`
- `validate_witness_evidence.py`, validator templates
- `fixtures_lib.py`, existing fixture trees/manifests
- Existing Phase 2A/2B/3B/3C/3D/3E/3F tests
- `AUTHORITATIVE_OUTCOME_CONTRACT.json`
- `INTEGRATED_REMEDIATION_LIST.md`, `WITNESS_REQUIREMENTS.md`, `WITNESS_RUNBOOK.md`
- Historical Phase 3B/3C/3D/3E/3F implementation notes
- `CLAIM_REGISTER.md` / broad public-status documents
- rc tags / archives / packaging / Independent Witness / C-014

## Exact scenario-row schema

Required top-level fields (unknown fields rejected):

| Field | Role |
|-------|------|
| `scenario_id` | Unique stable identity; diagnostics include it |
| `terminal_outcome` | Legal vocabulary from `AUTHORITATIVE_OUTCOME_CONTRACT.json` |
| `container_facts` | Mapping of container-side declared facts |
| `host_facts` | Mapping of host-side declared facts |
| `post_build_facts` | Mapping of post-build declared facts |
| `expected_validator_result` | Explicit expected validator structural result |
| `expected_host_gate` | Explicit expected host gate / exit expectations |
| `mutations` | Closed mutation vocabulary (ordered deterministically) |
| `expected_residue_policy` | Residue expectations for disposable workspaces |
| `oracle_bindings` | Explicit oracle expectations (not derived exit logic) |

Additional framework rules:

- Unique `scenario_id` enforcement
- Deterministic ordering: `scenario_id` ascending
- Frozen / immutable `ScenarioRow`
- Rejection of unknown terminal outcomes, unknown fields, duplicates, malformed structures
- Stable diagnostic output containing `scenario_id` and seed/order identity

Phase 3G-A includes only minimum framework smoke rows
(`framework_smoke_build_not_started`, `framework_smoke_success_capable`).

## Deterministic seed / order policy

| Item | Value |
|------|-------|
| Fixed seed constant | `phase3g-fixed-seed-v1` |
| Order identity | `seed=phase3g-fixed-seed-v1;order=scenario_id_asc` |
| Prohibited | current-time seed, environment-derived seed, nondeterministic filesystem ordering, random expansion |

## Lifecycle-transition schema

Ordered automated preliminary lifecycle (12 steps):

1. `container_finalization`
2. `container_evidence_ownership`
3. `host_outcome_ingestion`
4. `source_integrity_finalization`
5. `post_build_finalization`
6. `host_outcome_synchronization`
7. `closed_auxiliary_finalization`
8. `preliminary_manifest_finalization`
9. `host_preliminary_validator`
10. `validator_result_creation`
11. `final_summary`
12. `final_host_exit`

Framework rules:

- Explicit legal predecessor relationships
- Deterministic transition order
- Rejection of transition-before-predecessor
- Rejection of duplicate `final_host_exit`
- Fail-closed transition representation
- Pre-Docker failure path excludes validator transitions
- Manual Witness lifecycle is outside this model

Phase 3G-A validates the model only; it does not execute the full production lifecycle.

## Mutation vocabulary

Closed intent-only vocabulary:

- `missing_build_exit`
- `empty_build_exit`
- `malformed_build_exit`
- `outcome_disagreement`
- `host_status_failure`
- `post_build_failure`
- `validator_nonzero`
- `validator_fail`
- `validator_malformed_output`
- `stale_run_id`
- `stale_manifest_hash`
- `stale_validator_identity`
- `stale_evidence_path`
- `stale_stdout_capture`
- `stale_stderr_capture`
- `mixed_run_evidence`
- `preliminary_success_yes_injection`

Rules:

- Unknown mutations rejected
- Deterministic mutation ordering (sorted)
- Duplicate mutations rejected (no silent dedup)
- Incompatible combinations rejected by explicit group rule (build-exit trio;
  validator-result trio). Duplicate mutations rejected separately. Stale_* and
  `mixed_run_evidence` may combine in Phase 3G-B and are not mutual-exclusion
  grouped in 3G-A.

Mutations describe intent only and do not duplicate production decision logic.
Full evidence-package mutation application is deferred to Phase 3G-B.

## Oracle comparison model

Oracle binding names include:

- `expected_host_exit`
- `expected_explicit_outcome`
- `expected_host_outcome`
- `expected_post_build`
- `expected_validator_exit`
- `expected_structural_status`
- `expected_preliminary_success_eligible`
- `expected_build_exit_bytes`
- `expected_manifest_sha256`
- `expected_validator_result_bindings`
- `expected_evidence_tree_unchanged`
- `expected_residue_absent`

Distinct comparison kinds:

| Kind | Meaning |
|------|---------|
| `exact_byte_equality` | Exact byte equality |
| `exact_file_set_equality` | Exact file-set equality |
| `exact_schema_field_equality` | Exact schema-field equality |
| `semantic_status_equality` | Semantic status equality |
| `sha256_equality` | SHA-256 equality |

Scenario rows state expected results explicitly. The oracle framework does **not**
recompute production host-exit boolean logic.

## Command-shim policy

PATH-first non-delegating shims for:

- `docker`, `cargo`, `rustc`, `rustup`, `dotslash`, `protoc`, `ldd`
- product aliases: `xai-grok-pager`, `xai-grok-pager-bin`

Behavior: log to disposable test-owned log, exit nonzero (99), never delegate.
Tests assert no prohibited invocation occurred when none is expected.

## Workspace / residue policy

- Prefix: `phase3g_test_*`
- Unique workspace per test under `scripts/tests/`
- Isolated `HOME`, `WORK_ROOT`, `EVIDENCE_DIR`, source, temp, and capture locations
- Cleanup in `finally` / `tearDown`
- Explicit residue assertion
- Unexpected non-test paths are **not** silently deleted
- No writes outside the test-owned workspace except ordinary Python cache behavior
- No `py`-launcher installation-manager residue; interpreter binding uses `sys.executable`

## Sourced-writer adapter boundary (3G-A)

Adapters locate and safely source committed container/host writer functions:

- Verify function discovery and safe sourcing mechanics
- Verify required function names / lifecycle markers
- Use disposable workspace variables
- Keep prohibited tools shimmed
- Do **not** run the complete five-outcome lifecycle
- Do **not** run real Docker/Cargo/product
- Do **not** change runtime scripts

## Real-validator driver boundary (3G-A)

Driver for committed local validator
`validate_witness_evidence.py`:

- Explicit `sys.executable` (or adjudicated explicit interpreter path)
- `--host-preliminary` mode
- Explicit evidence input path
- stdout/stderr capture paths outside `EVIDENCE_DIR`
- No evidence writes by the driver
- Process exit captured
- Exact command identity available to scenario diagnostics

Phase 3G-A may invoke the real validator only against a controlled disposable
fixture workspace to prove the driver. Fixture-only validator PASS is **not**
Phase 3G integration evidence. RC4B-018 / RC4B-040 are **not** claimed implemented.

## Full-main harness preparation boundary (3G-A)

May:

- Build controlled environment dictionaries
- Construct PATH shim directories
- Construct disposable source/work roots
- Identify the main entry point (`run_witness_narrow_build_main`)
- Verify the harness can prevent real prohibited tools

Must **not**:

- Execute a successful real host Witness workflow
- Invoke Docker daemon / Cargo / compiler / product
- Claim Witness reproduction
- Populate full-main scenario coverage

## Exact Phase 3G-A test count and result

| Suite | Module | Result |
|-------|--------|--------|
| Phase 3G-A framework | `test_phase3g_framework` | **23/23 PASS** (0 failed, 0 errors, 0 skipped) |

Discovered test methods: `test_01` … `test_23` (framework behavior coverage; not an arbitrary target count).

## Regressions run

Mandatory separate suites (required committed baselines) — all PASS:

| Suite | Result |
|-------|--------|
| `test_phase3f_host_validator_gate` | **32/32 PASS** |
| `test_phase3f_validator_prerequisites` | **25/25 PASS** |
| `test_validate_witness_evidence` | **65/65 PASS** |
| `test_phase3e_post_build_integrity` | **22/22 PASS** |
| `test_phase3d_host_outcome_ingestion` | **50/50 PASS** |
| `test_phase3c_container_terminal_finalization` | **36/36 PASS** |
| `test_phase3b_outcome_contract` | **25/25 PASS** |
| `test_phase2b_mount_isolation` | **22/22 PASS** |
| `test_phase2a_host_preflight` | **18/18 PASS** |

## Phase 3G-B integrated scenarios (this stage)

Phase 3G-B is the integrated behavioral scenario stage and the final stage of
Phase 3G. It extends the committed Phase 3G-A framework without redesign and
without creating Phase 3G-C.

### Phase 3G-B base

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (pre-change base) | `e12df255e5b1c772e07f333d133617597d0e8b40` |
| origin/main (pre-change) | `e12df255e5b1c772e07f333d133617597d0e8b40` |
| Prior phase | Phase 3G-A at same HEAD |
| rc5 | absent |
| Historical tags | `grok-build-witness-v1.0.0-rc1` … `rc4` present; unchanged |

### Exact files changed / created (Phase 3G-B)

- `external_verifications/grok-build/witness-package/scripts/tests/phase3g_scenarios.py` (integrated scenario matrix)
- `external_verifications/grok-build/witness-package/scripts/tests/phase3g_oracles.py` (oracle evaluation helpers)
- `external_verifications/grok-build/witness-package/scripts/tests/phase3g_harness.py` (sourced-writer runner, mutations, full-main fail-closed smoke)
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3g_integration.py` (**new**)
- This note (additive Phase 3G-B section)
- Narrow updates: `INTEGRATED_REMEDIATION_LIST.md`, `WITNESS_REQUIREMENTS.md`, `WITNESS_RUNBOOK.md`

### Integrated scenario architecture

- Declarative `ScenarioRow` table via `integrated_scenarios()` (33 rows)
- Fixed seed/order identity unchanged: `seed=phase3g-fixed-seed-v1;order=scenario_id_asc`
- Explicit terminal outcomes, facts, mutations, residue policy, oracle bindings
- No Cartesian product; no nondeterministic / wall-clock generation
- Primary proof: sourced committed writers from `container_narrow_build.sh` and
  `run_witness_narrow_build.sh` inside disposable `phase3g_test_*` workspaces
- Supporting identity / Witness-manual files may be seeded from `fixtures_lib`
  only for files the Phase 3C–3F writers under test do not produce
- Preserve-mode artifact seed includes `artifact_identity_complete` required by
  host tuple parse (Phase 3D); container finalize still writes BUILD_EXIT /
  BUILD_TIMING via the real writer

### Exact scenario categories (33 IDs)

Five terminal outcomes; success-capable writer→validator→gate; missing/empty/
malformed BUILD_EXIT; four outcome-disagreement categories; host infrastructure /
source-integrity / POST_BUILD / sync-mismatch failures; real-validator structural
FAIL; mock fault units (nonzero / missing PASS / contradictory / multiple PASS);
eight stale/spoof/mixed-run / preliminary_success_yes mutations; pre-Docker
no-validator; limited full-main fail-closed smoke; full-main success-capable row
(documented as sourced-primary — see boundary note).

### Actual sourced-writer boundary

Exercises, as applicable: container finalization; container-owned evidence;
host outcome ingestion; source-integrity / POST_BUILD finalization; HOST_OUTCOME
sync; closed-auxiliary inventory posture; preliminary manifest; real
`--host-preliminary` validator; host-owned `VALIDATOR_RESULT`; binding
verification; final host-gate decision. Does **not** execute either script’s
real production workflow, Docker daemon, Cargo, compiler, product, or network.

### Real-validator primary boundary

Success integration uses `sys.executable` + committed
`validate_witness_evidence.py --host-preliminary` with captures outside
`EVIDENCE_DIR`. Mock validators are retained only for parser/fault-unit
rejection categories and are not the sole success-integration proof.

### Limited full-main smoke boundary

- Fail-closed smoke invokes `run_witness_narrow_build_main` with Phase 3G
  work-root rebind and controlled Docker shim; fails pre-Docker; no pull/run.
- Success-capable **host exit 0** via unmodified full main is not safely
  reachable under shims alone: the automated main intentionally does not
  complete Witness-manual files required for host-preliminary PASS. Primary
  success-capable exit 0 is proven by the sourced-writer chain (test_02).
  Runtime modification to force full-main exit 0 was not performed.

### Exact Phase 3G-B test count and result

| Suite | Module | Result |
|-------|--------|--------|
| Phase 3G-B integration | `test_phase3g_integration` | **11/11 PASS** (0 failed, 0 errors, 0 skipped) |

Discovered test methods: `test_01` … `test_11` (category-derived; not an arbitrary target count).

### Exact regression results (Phase 3G-B run)

| Suite | Result |
|-------|--------|
| `test_phase3g_framework` | **23/23 PASS** |
| `test_phase3f_host_validator_gate` | **32/32 PASS** |
| `test_phase3f_validator_prerequisites` | **25/25 PASS** |
| `test_validate_witness_evidence` | **65/65 PASS** |
| `test_phase3e_post_build_integrity` | **22/22 PASS** |
| `test_phase3d_host_outcome_ingestion` | **50/50 PASS** |
| `test_phase3c_container_terminal_finalization` | **36/36 PASS** |
| `test_phase3b_outcome_contract` | **25/25 PASS** |
| `test_phase2b_mount_isolation` | **22/22 PASS** |
| `test_phase2a_host_preflight` | **18/18 PASS** |

### Residue / runtime / non-claims

- Residue: no remaining `phase3g_test_*` (or earlier phase) temps after suites
- Runtime files unchanged: `run_witness_narrow_build.sh`,
  `container_narrow_build.sh`, `validate_witness_evidence.py`
- No real Docker, Cargo, compiler, product, or network
- No Independent Witness reproduction / PASS
- RC4 remains **NOT READY**; rc5 absent; C-014 **NOT_STARTED**
- No blocker CLOSED

## Phase 3G-B work previously deferred — now addressed

The following Phase 3G-A deferrals are addressed by Phase 3G-B:

- Integrated lifecycle scenario matrix (33 declarative rows)
- Mutation application against generated packages
- Real-validator primary integrated success + FAIL cases
- Limited full-main fail-closed smoke execution
- RC4B-018 / RC4B-040 automated-preliminary status advancement (pending reaudit; not CLOSED)

Runtime script edits remain prohibited and were not performed.

## Non-claims / blocker status

- Runtime files unchanged
- No blocker CLOSED
- RC4 remains **NOT READY**
- rc5 tag absent
- No Independent Witness reproduction / PASS
- C-014 remains **NOT_STARTED**
- RC4B-018 → **IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT** (Phase 3G-B)
- RC4B-040 automated preliminary package subset → implemented/integration-evidenced
  pending reaudit; final manual-submission scope remains later; **not CLOSED**
- RC4B-013 and RC4B-022 remain **IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT**
  with Phase 3G integration evidence added
- RC4B-009, RC4B-012, RC4B-017, RC4B-019, and RC4B-029 remain **OPEN**
