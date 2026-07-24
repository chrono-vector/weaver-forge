# Phase 3D — Host Outcome Ingestion and No-Overwrite Implementation Note

## Base

| Item | Value |
|------|-------|
| Branch | `main` |
| Base commit | `bc4e7879fea3f37bbfabbaf9abd31d9110c3899a` |
| Phase 3B contract | `witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json` |
| Contract version | `1.0.0-phase3b` |
| Phase 3C dependency | `bc4e7879fea3f37bbfabbaf9abd31d9110c3899a` (container terminal finalization on main) |
| RC4 disposition | **NOT READY** (unchanged) |
| RC5 tag | **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **not claimed** |
| C-014 | **NOT_STARTED** |

## Current violations fixed (Phase 3D scope)

1. Host previously read only `outcome=` from `BUILD_EXIT_CODE.txt` rather than a complete tuple — **fixed** via `parse_container_result_tuple`.
2. Host could overwrite `BUILD_EXIT_CODE.txt` after post-Docker source-integrity failure — **fixed**; valid container outcome is preserved byte-for-byte.
3. Invalid/missing outcome path replaced the container result with host `INFRASTRUCTURE_FAILURE` — **fixed**; host records failure in `HOST_OUTCOME_INGESTION.txt` without fabricating/replacing container outcome; absent `BUILD_EXIT_CODE.txt` remains absent.
4. Post-Docker unexpected failure finalization could leave host evidence incomplete / overwrite container outcome — **fixed** via `finalize_post_docker_host_failure`.
5. Validator inference — **unchanged / out of scope** (Phase later).
6. Host success ungated by validator — **unchanged / out of scope** (Phase 3F).

## Complete staged file inventory (Phase 3D)

The original Phase 3D implementation used six files. The Pi-found no-fabrication correction required regression alignment in the Phase 2B and Phase 3B test modules. Those two additional test files are therefore intentionally included in the final Phase 3D staged set. Complete staged inventory (8 paths):

1. `external_verifications/grok-build/evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`
2. `external_verifications/grok-build/evidence/rc5-remediation/PHASE_3D_HOST_OUTCOME_INGESTION_IMPLEMENTATION_NOTE.md` (this file)
3. `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md`
4. `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`
5. `external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh`
6. `external_verifications/grok-build/witness-package/scripts/tests/test_phase2b_mount_isolation.py`
7. `external_verifications/grok-build/witness-package/scripts/tests/test_phase3b_outcome_contract.py`
8. `external_verifications/grok-build/witness-package/scripts/tests/test_phase3d_host_outcome_ingestion.py`

Container script, validator, outcome contract JSON, templates, fixtures, Phase 3B/3C historical notes, and preserved RC4 audit reports were **not** modified.

## Host-owned ingestion record

Filename: `HOST_OUTCOME_INGESTION.txt` (added to host closed auxiliary allow-list only; not added to validator `REQUIRED_FILES` or normative templates in this phase).

Deterministic `key=value` fields:

- `schema_version=`
- `status=` (`OK` only when parse + tuple consistency pass; else `FAILED`)
- `container_result_presence=`
- `container_result_valid=`
- `container_result_error=`
- `container_outcome=` (empty or `INVALID` when source result missing/invalid; never invented)
- `container_exit_code=`
- `cargo_started=`
- `cargo_exit_code=`
- `artifact_present=`
- `artifact_identity_complete=`
- `static_inspection_complete=`
- `host_infrastructure_status=`
- `host_source_integrity_status=`
- `post_build_integrity_status=`
- `evidence_completeness_status=`
- `preliminary_success_eligible=NO` (always in Phase 3D)
- `record_owner=HOST`

## Parser behavior (`parse_container_result_tuple`)

- Reads explicit container-owned evidence; returns structured host representation in globals.
- Terminal outcome must appear exactly once; accepted outcomes are exactly the five contract outcomes.
- Sentinels rejected as terminal outcomes.
- Duplicate keys, missing required keys, malformed lines, and CR/LF injection rejected.
- Contradictory tuple values rejected (not normalized).
- No value inferred from another field; no missing value replaced with `INFRASTRUCTURE_FAILURE`.
- Performs no filesystem writes; invokes no validator; invokes no external tool.
- Paths containing spaces supported via careful quoting.

## Tuple consistency rules

Applied exactly per Phase 3B contract for:

- `BUILD_NOT_STARTED`
- `CARGO_FAILED`
- `CARGO_SUCCEEDED_ARTIFACT_MISSING`
- `CARGO_SUCCEEDED_ARTIFACT_PRESENT` (requires explicit identity/static completion fields)
- `INFRASTRUCTURE_FAILURE` (preserves observed cargo facts; requires explicit failure stage)

## No-inference behavior

Missing `outcome=` is not filled from `cargo_started`, artifact presence, or Docker exit. Unsupported/missing results fail closed with the original missing/invalid state visible in `HOST_OUTCOME_INGESTION.txt`.

## No-overwrite behavior

- Valid container `BUILD_EXIT_CODE.txt` remains unchanged after host source-integrity / infrastructure failures.
- Host records `host_source_integrity_status=FAILED` / `host_infrastructure_status=FAILED` separately.
- Host never rewrites a container outcome to `INFRASTRUCTURE_FAILURE`.
- Pre-Docker failures may still use host-generated infrastructure evidence where no container outcome exists.

## Invalid/missing result behavior

- Host exit nonzero
- `HOST_OUTCOME_INGESTION` `status=FAILED`, `container_result_valid=NO`, exact error class recorded
- No fabricated terminal container outcome
- No host overwrite of `BUILD_EXIT_CODE.txt`
- If absent, leave absent
- Validator not invoked

## Valid failure / success-capable behavior

- Valid failure outcomes: parse complete tuple; preserve container outcome; ingestion `status=OK` when internally valid; `preliminary_success_eligible=NO`; host exit nonzero on failure paths; no conversion; no validator.
- `CARGO_SUCCEEDED_ARTIFACT_PRESENT`: preserved; ingestion `status=OK` when valid; `preliminary_success_eligible=NO` always in Phase 3D; host does not claim success merely from this outcome. Validator-gated exit remains Phase 3F.

## Source-integrity failure behavior

Starting from a valid container outcome: HEAD mismatch or dirty-tree failure preserves `BUILD_EXIT_CODE.txt`, records `host_source_integrity_status=FAILED`, host exit nonzero, `preliminary_success_eligible=NO`. Phase 2B mount/source protections are not weakened.

## Atomic writer / writer-failure limitation

- `write_host_outcome_ingestion_record` uses same-directory temp write + rename (`write_evidence_file_atomic`).
- Rejects CR/LF in dynamic single-line fields; no `eval`.
- If the host-owned record cannot be written: nonzero return, no success claim, container evidence untouched, stderr identifies failure, no recursive trap loop.
- Total filesystem failure cannot truthfully yield a complete host record; that boundary is unavoidable and explicit.

## Centralized finalizer

`finalize_post_docker_host_failure`:

- Preserves valid container-owned files
- Writes/replaces only host-owned evidence
- Always writes `HOST_OUTCOME_INGESTION.txt`
- Finalizes `DOCKER_EXIT_CODE.txt` and host timing facts
- Keeps `preliminary_success_eligible=NO`
- Returns nonzero / abort path
- Prevents recursive ERR trap via `HOST_FINALIZING_IN_PROGRESS`
- Fail-closed if host-owned record cannot be written
- Never claims evidence completeness or validator success; never invokes validator
- No Phase 3E `POST_BUILD` semantic rewrite

## Exact test command / results (preserve initial and current)

### Initial Phase 3D result (historical evidence only)

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python3 -m unittest test_phase3d_host_outcome_ingestion -v
```

Initial result before Pi staged-tree review: **48 discovered / 48 run / 48 passed / 0 failed / 0 errors / 0 skipped**.

```text
Ran 48 tests in 89.637s
OK
```

`48/48` is historical initial evidence only. It is not erased and is not relabeled as the current gate.

### Pi staged-tree review

**FAIL / STOP** because one post-Docker fabrication path remained (`enforce_post_docker_source_integrity_boundary` could still create/replace missing or empty `BUILD_EXIT_CODE.txt`).

### Corrected current Phase 3D requirement and result

Current required and observed Phase 3D gate: **50 discovered / 50 run / 50 passed / 0 failed / 0 errors / 0 skipped** (`50/50`).

```text
python3 -m unittest test_phase3d_host_outcome_ingestion -v
# Ran 50 tests — OK
```

### Regression results (preserved; Phase 3C not required for documentation-only correction)

```text
python3 -m unittest test_phase3b_outcome_contract -v   # Ran 25 tests — OK (25/25 PASS)
python3 -m unittest test_phase2b_mount_isolation -v    # Ran 22 tests — OK (22/22 PASS)
python3 -m unittest test_phase2a_host_preflight -v     # Ran 18 tests — OK (18/18 PASS)
```

Phase 3C suite is not rerun for a documentation-only correction; container runtime is unchanged. No `phase2a_test_*`, `phase2b_test_*`, or `phase3d_test_*` residue remained.

## Remaining gaps (explicit)

- Validator outcome inference remains unresolved (`RC4B-022`)
- `POST_BUILD` semantic alignment remains Phase 3E
- Validator-gated host success remains Phase 3F
- No end-to-end compliance claim
- RC4 remains **NOT READY**
- `rc5` tag absent
- No Independent Witness reproduction/PASS
- C-014 remains **NOT_STARTED**
- No blocker CLOSED

## Historical baseline and current implementation status

1. `AUTHORITATIVE_OUTCOME_CONTRACT.json` and `PHASE_3B_OUTCOME_OWNERSHIP_CONTRACT.md` preserve the Phase 3B historical baseline.
2. Their `HOST_OVERWRITES_CONTAINER_BUILD_EXIT_CODE=UNRESOLVED` entry records the condition that existed when Phase 3B was defined.
3. The entry is retained so the historical defect is not erased.
4. The current staged Phase 3D host implementation removes the post-Docker overwrite/fabrication path.
5. `INTEGRATED_REMEDIATION_LIST.md` is the live current-status authority for remediation progress.
6. Current implementation status is `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT`, not CLOSED and not reaudited.
7. `PHASE_3C_CONTAINER_TERMINAL_FINALIZATION_IMPLEMENTATION_NOTE.md` remains a historical Phase 3C snapshot written before Phase 3D began.
8. `VALIDATOR_DETERMINE_OUTCOME_INFERENCE` remains genuinely unresolved.
9. No statement in this Phase 3D note changes or rewrites the historical Phase 3B or Phase 3C record.
10. RC4 remains **NOT READY**; `rc5` does not exist; no Independent Witness reproduction/PASS occurred; C-014 remains **NOT_STARTED**.

## Blocker status wording (Phase 3D staged set)

The limited Pi no-fabrication correction did not newly change blocker statuses relative to the initial Phase 3D staged implementation. The complete Phase 3D staged set does advance:

- `RC4B-014` = `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT`
- `RC4B-023` = `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT`

And leaves the remainder as follows:

- `RC4B-012` and `RC4B-029` remain **OPEN** with host-side implementation recorded
- `RC4B-022` remains `CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING`
- `RC4B-011`, `RC4B-024`, `RC4B-019`, `RC4B-005`, and `RC4B-009` remain **OPEN**
- No blocker is **CLOSED**

## Pi correction history (no-fabrication)

| Item | Value |
|------|-------|
| Initial Cursor Phase 3D | **48/48 PASS** (historical initial evidence only) |
| Pi staged-tree review | **FAIL / STOP** |
| Remaining fabrication path | `enforce_post_docker_source_integrity_boundary`: when `BUILD_EXIT_CODE.txt` was missing or empty (`! -s`), host created/replaced it with `outcome=INFRASTRUCTURE_FAILURE` and `producer=host_no_container_result` |
| Pi test timeout | Separate from the code defect (not treated as a test failure of the parser/finalizer suite) |
| Limited correction | Removed all post-Docker host creation/replacement of container-owned `BUILD_EXIT_CODE.txt` from the source-integrity boundary; missing/empty/malformed/valid handling delegated to `finalize_post_docker_host_failure` only |
| New behavioral tests | Exactly two added: (49) missing `BUILD_EXIT_CODE` remains absent after source-integrity failure; (50) empty `BUILD_EXIT_CODE` remains byte-for-byte empty after source-integrity failure |
| Corrected current Phase 3D gate | **50/50 PASS** (current required and observed result; initial 48/48 not erased or relabeled) |
| Phase 3B test | `test_phase3b_outcome_contract.py` test_24 updated so the fixed overwrite is required to be absent (fixing is not treated as failure); validator-inference remains unresolved; contract JSON / Phase 3B note unchanged |
| Phase 2B tests | `test_phase2b_mount_isolation.py` post-HEAD/dirty tests updated: they previously required the host-fabricated `BUILD_EXIT_CODE.txt` path; they now assert absent container result + host-owned `HOST_OUTCOME_INGESTION.txt` failure fields (success still prevented) |
| Prior results | No prior PASS/FAIL result erased or relabeled |
| RC4 disposition | Remains **NOT READY** |
| RC5 tag | Remains **absent** |
| Independent Witness reproduction / PASS | **NOT PERFORMED** / **not claimed** |
| C-014 | Remains **NOT_STARTED** |
| Blocker statuses | Limited Pi no-fabrication correction did not newly change blocker statuses relative to the initial Phase 3D staged implementation; complete Phase 3D staged set advances RC4B-014 and RC4B-023 to `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT`; no blocker CLOSED |
