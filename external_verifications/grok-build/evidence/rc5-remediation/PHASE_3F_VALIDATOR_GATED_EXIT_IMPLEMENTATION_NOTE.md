# Phase 3F — Validator-gated exit implementation note

## Scope of this note

This note records **Phase 3F-A** (Pi-adjudicated validator prerequisites) and
**Phase 3F-B** (Pi-adjudicated host validator gating).

Owner Option A remained in force: `CLAIM_REGISTER.md` and broad public-status
documents were not modified.

## Repository base

### Phase 3F-A

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (pre-change base) | `c576f2d865e8c297f3caf2a9392bdeafc2270f4c` |
| origin/main (pre-change) | `c576f2d865e8c297f3caf2a9392bdeafc2270f4c` |
| Commit | `f62de7b36a567b39a00bcede2a34912c43aa4d4c` |
| rc5 | absent |
| Historical tags | `grok-build-witness-v1.0.0-rc1` … `rc4` present; unchanged |

### Phase 3F-B

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (pre-change base) | `f62de7b36a567b39a00bcede2a34912c43aa4d4c` |
| origin/main (pre-change) | `f62de7b36a567b39a00bcede2a34912c43aa4d4c` |
| Prior phase | Phase 3F-A at same HEAD |
| rc5 | absent |
| Historical tags | `grok-build-witness-v1.0.0-rc1` … `rc4` present; unchanged |

## Cursor options analysis (prior read-only pass)

Cursor independently derived Phase 3F as host orchestrator exit gating on
structural validation of host-finalized automated evidence, with coupled
validator truthfulness work. Key contradictions identified included:

- `determine_outcome` inference vs no-inference contract (RC4B-022)
- Validator `CLOSED_AUX` omitting `HOST_OUTCOME_INGESTION.txt` (hard block for host-time validate)
- RC4B-017 four-yes vs host always recording `evidence_inventory_complete=no`
- `preliminary_success_eligible` remaining `NO` vs success-eligibility pressure

Recommended fixed plan: **O15** staged **3F-A → 3F-B** implementing the
**O2+O7+O10+O13+O17+O18** bundle (explicit outcome; HOST_OUTCOME closed-aux;
O18 automatable RC4B-017 subset without inventory completeness; durable
validator result + host gate deferred to 3F-B).

## Pi independent adjudication

Pi and Cursor agreed on the fixed two-stage plan:

1. **Phase 3F-A (complete at `f62de7b…`):** remove validator outcome inference; require
   explicit authoritative outcome; add and structurally validate
   `HOST_OUTCOME_INGESTION.txt`; align closed auxiliary inventory; implement
   the automatable RC4B-017 structural subset; update directly affected
   validator tests/fixtures/docs/ledger/note.
2. **Phase 3F-B (this task):** host invokes validator after automated evidence and
   preliminary manifest finalization; host captures validator stdout/stderr outside
   `EVIDENCE_DIR`; host writes host-owned `VALIDATOR_RESULT.txt` outside
   `EVIDENCE_DIR`; host exit 0 becomes validator-gated per the adjudicated rule.

---

# Phase 3F-A record (preserved)

## Exact files changed (Phase 3F-A)

### Validator implementation

- `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py`

### Validator documentation

- `external_verifications/grok-build/witness-package/scripts/VALIDATOR.md`

### Validator / phase tests

- `external_verifications/grok-build/witness-package/scripts/tests/test_validate_witness_evidence.py`
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3b_outcome_contract.py` (test_23 supersession only)
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3f_validator_prerequisites.py` (**new**)

### Fixtures

- `external_verifications/grok-build/witness-package/scripts/tests/fixtures_lib.py`
- `external_verifications/grok-build/witness-package/scripts/tests/fixtures/**` (HOST_OUTCOME + manifests)

### Current-status and guidance

- `external_verifications/grok-build/evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`
- `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md`
- `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`

### This note

- `external_verifications/grok-build/evidence/rc5-remediation/PHASE_3F_VALIDATOR_GATED_EXIT_IMPLEMENTATION_NOTE.md`

### Explicitly unchanged in Phase 3F-A (prohibited / deferred)

- `run_witness_narrow_build.sh`, `container_narrow_build.sh`
- `AUTHORITATIVE_OUTCOME_CONTRACT.json`
- Historical Phase 3B/3C/3D/3E notes
- `CLAIM_REGISTER.md` / broad public-status documents
- Host validator invocation, host exit gating, `VALIDATOR_RESULT.txt`
- rc tags / packaging / Independent Witness / C-014

## Exact explicit-outcome rule

- An explicit `outcome=` field must exist in `BUILD_EXIT_CODE.txt`
- It must contain exactly one allowed authoritative outcome value from the
  existing repository vocabulary:
  `BUILD_NOT_STARTED`, `CARGO_FAILED`, `CARGO_SUCCEEDED_ARTIFACT_MISSING`,
  `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, `INFRASTRUCTURE_FAILURE`
- Missing / empty / malformed / unsupported outcome → fail closed
- Contradictory secondary fields fail validation; they do not replace or
  repair outcome
- Validator never creates or infers an outcome not explicitly present

## Every removed inference path

Removed from `determine_outcome`:

1. `cargo_started=NO` ∧ `build_status=BUILD_NOT_STARTED` → `BUILD_NOT_STARTED`
2. `cargo_started=NO` ∧ `build_status=INFRASTRUCTURE_FAILURE` → `INFRASTRUCTURE_FAILURE`
3. `cargo_started=YES` ∧ `build_status=FAILED` → `CARGO_FAILED`
4. The fallback error path that only failed when inference was also ambiguous
   (`conservatively inferred from cargo_started/build_status`)

## Exact HOST_OUTCOME field set and structural rules

Exact keys (Phase 3D/3E host writer `_host_outcome_ingestion_body`):

1. `schema_version`
2. `status`
3. `container_result_presence`
4. `container_result_valid`
5. `container_result_error`
6. `container_outcome`
7. `container_exit_code`
8. `cargo_started`
9. `cargo_exit_code`
10. `artifact_present`
11. `artifact_identity_complete`
12. `static_inspection_complete`
13. `host_infrastructure_status`
14. `host_source_integrity_status`
15. `post_build_integrity_status`
16. `evidence_completeness_status`
17. `preliminary_success_eligible`
18. `record_owner`
19. `run_id`
20. `failure_stage`

Structural rules:

- Exact field-set equality (no missing / unknown / extra / duplicate keys)
- Legal vocabularies for status, presence, validity, host statuses,
  completeness, preliminary eligibility
- `record_owner=HOST`
- When `container_result_valid=YES`, `container_outcome` must be an allowed
  outcome and must match authoritative `BUILD_EXIT_CODE.txt` outcome
- Presence/validity contradictions fail closed
- `status=OK` ∧ `container_result_valid=NO` fails closed
- HOST_OUTCOME does not overwrite or repair container evidence
- `preliminary_success_eligible` vocabulary allows YES|NO but YES is never
  treated as final success eligibility; host-preliminary mode requires NO

## CLOSED_AUX treatment

`HOST_OUTCOME_INGESTION.txt` added to `CLOSED_AUX_EVIDENCE_FILES`. Presence
may be declared in the evidence manifest without undeclared-aux rejection.
Presence triggers structural validation (allow-listing alone is insufficient).
Unrelated extra auxiliary files remain rejected. Manifest hashing / closed
inventory protections remain intact.

## Host-preliminary mode semantics

`validate_dir(..., host_preliminary=True)` / CLI `--host-preliminary`:

- Structurally validates finalized automated host evidence + preliminary manifest
- Not final Witness validation
- Not Independent Witness PASS
- Not final success eligibility
- `evidence_inventory_complete=yes` is not required
- `preliminary_success_eligible` must remain `NO`
- Requires `HOST_OUTCOME_INGESTION.txt` and the automatable RC4B-017 subset

## Automatable RC4B-017 subset

For host-preliminary structural PASS (and, for consistency, whenever
`POST_BUILD` claims `status=OK`):

- `status=OK`
- `post_build_integrity_ok=yes`
- `source_head_unchanged=yes`
- `source_clean_before=yes`
- `source_clean_after=yes`
- `cargo_lock_unchanged=yes`
- `cargo_lock_post_matches_expected=yes`
- `source_or_lock_changed=no`
- Matching HOST_OUTCOME: `host_infrastructure_status=OK`,
  `host_source_integrity_status=OK`, `post_build_integrity_status=OK`

Not required (and not claimed as full RC4B-017 remediation):

- `evidence_inventory_complete=yes`
- `preliminary_success_eligible=YES`
- Final Witness manifest completion
- Independent Witness PASS
- Final success eligibility

## Validator no-write boundary

Validator writes only to stdout/stderr. It never writes into the evidence
directory. No durable `VALIDATOR_RESULT.txt` is created by the validator.

## Phase 3B test_23 supersession

- Historical visibility preserved: Phase 3B contract/note still record the
  inference violation as discovered (`UNRESOLVED`, not ACCEPTABLE)
- Stale current-source expectation that inference must still exist is superseded
- Current validator source must contain no inference fallback
- `AUTHORITATIVE_OUTCOME_CONTRACT.json` and Phase 3B note unchanged
- Unrelated Phase 3B tests preserved

## Exact Phase 3F-A test count

`test_phase3f_validator_prerequisites.py`: **25** tests discovered / 25 run / 25 pass / 0 fail / 0 error / 0 skip.

## Exact Phase 3F-A regression results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_phase3f_validator_prerequisites` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_validate_witness_evidence` | 65 | 65 | 65 | 0 | 0 | 0 |
| `test_phase3b_outcome_contract` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_phase3e_post_build_integrity` | 22 | 22 | 22 | 0 | 0 | 0 |
| `test_phase3d_host_outcome_ingestion` | 50 | 50 | 50 | 0 | 0 | 0 |
| `test_phase2b_mount_isolation` | 22 | 22 | 22 | 0 | 0 | 0 |
| `test_phase2a_host_preflight` | 18 | 18 | 18 | 0 | 0 | 0 |

Phase 3C was **not** run (container script prohibited from modification).

---

# Phase 3F-B record

## Exact files changed (Phase 3F-B)

### Host runtime

- `external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh`

### New Phase 3F-B focused tests

- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3f_host_validator_gate.py` (**new**, 32 tests)

### Direct supersession of stale current-source expectations

- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3e_post_build_integrity.py`
  (`test_21_host_exit_not_validator_gated` → `test_21_host_exit_validator_gated_after_phase3f_b`)
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase3f_validator_prerequisites.py`
  (`test_22_no_host_invocation_or_exit_gating_in_3f_a` → `test_22_host_gating_deferred_from_3f_a_implemented_in_3f_b`)

### Current-status and guidance

- `external_verifications/grok-build/evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`
- `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md`
- `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`

### This note

- `external_verifications/grok-build/evidence/rc5-remediation/PHASE_3F_VALIDATOR_GATED_EXIT_IMPLEMENTATION_NOTE.md`

### Explicitly unchanged (prohibited)

- `validate_witness_evidence.py` / Phase 3F-A validator behavior / `determine_outcome`
- Validator fixtures / manifests / `test_validate_witness_evidence.py`
- `test_phase3b_outcome_contract.py`
- `container_narrow_build.sh` / `BUILD_EXIT_CODE.txt` ownership
- `AUTHORITATIVE_OUTCOME_CONTRACT.json`
- Historical Phase 3B/3C/3D/3E notes
- `CLAIM_REGISTER.md` / broad public-status documents
- Phase 3G / rc5 packaging / Independent Witness / C-014

### Schema template decision

**No separate `VALIDATOR_RESULT` template/schema document was created.**
Rationale: host-owned records in this package (`HOST_OUTCOME_INGESTION`,
`POST_BUILD_INTEGRITY`) define ordered field sets inline in the host script;
`HOST_RUN_METADATA.txt` remains schema-less auxiliary evidence. Adding a new
template would be inconsistent with that convention and unnecessary for Phase 3F-B.
Exact ordered field set is recorded below and enforced by focused tests.

## Exact validator invocation lifecycle

Required order (success path reaching automated completion):

1. container execution finalized
2. `BUILD_EXIT_CODE.txt` parsed and validated
3. `HOST_OUTCOME_INGESTION.txt` finalized
4. host source-integrity checks finalized
5. `POST_BUILD_INTEGRITY.txt` finalized
6. `HOST_OUTCOME` post-build status synchronized
7. permitted closed auxiliary evidence finalized
8. preliminary `EVIDENCE_MANIFEST.sha256` finalized
9. **host-preliminary validator invocation** (`step21b_host_preliminary_validator`)
10. **fresh host-owned `VALIDATOR_RESULT` record**
11. final summary
12. final host exit

Pre-Docker and post-Docker failure finalizers do **not** invoke the validator.

Exact command identity:

```text
${HOST_PYTHON_OR_python3} ${SCRIPT_DIR}/validate_witness_evidence.py --host-preliminary ${EVIDENCE_DIR}
```

Stdout → `${WORK_ROOT}/tmp/host-validator/VALIDATOR_STDOUT.txt` (or `HOST_VALIDATOR_DIR`)
Stderr → `${WORK_ROOT}/tmp/host-validator/VALIDATOR_STDERR.txt`
Result → `${WORK_ROOT}/tmp/host-validator/VALIDATOR_RESULT.txt`

Evidence is not modified after validator invocation. Errexit cannot bypass
result recording (`set +e` around the process; result write always attempted).

## Exact PASS parse rule

Accepted definitive final structural result line:

- Line text begins with exactly `STRUCTURAL VALIDATION: PASS`
  (covers plain PASS and the committed host-preliminary PASS note suffix)
- Require **exactly one** such PASS line in current-run stdout
- Require **zero** lines beginning with `STRUCTURAL VALIDATION: FAIL`
- Reject contradictory PASS+FAIL, multiple PASS lines, absent PASS, or
  arbitrary text containing the word `PASS`

## Exact VALIDATOR_RESULT path

`${WORK_ROOT}/tmp/host-validator/VALIDATOR_RESULT.txt`

(or `${HOST_VALIDATOR_DIR}/VALIDATOR_RESULT.txt` for isolated sourced tests)

Outside `EVIDENCE_DIR`; never listed in `EVIDENCE_MANIFEST.sha256`; host-owned;
never written by the validator.

## Exact ordered VALIDATOR_RESULT field set

1. `schema_version`
2. `record_owner` (= `host`)
3. `run_id`
4. `validator_command`
5. `validator_script_path`
6. `evidence_dir`
7. `preliminary_manifest_path`
8. `preliminary_manifest_sha256`
9. `validator_process_exit_code`
10. `structural_status`
11. `structural_pass`
12. `explicit_outcome_observed`
13. `machine_verdict_ceiling`
14. `stdout_capture_path`
15. `stdout_capture_sha256`
16. `stderr_capture_path`
17. `stderr_capture_sha256`
18. `invocation_started_utc`
19. `invocation_finished_utc`
20. `failure_stage`
21. `error_reason`

No final-success-eligibility fields. No Independent Witness verdict fields.

## Stale/spoof resistance

Before invocation:

- delete prior `VALIDATOR_RESULT.txt` / stdout / stderr in the disposable host-validator dir
- bind new record to current `run_id`, preliminary manifest SHA-256, validator
  script path, validator command, and evidence directory

After invocation:

- hash captures from current files
- reject missing/altered captures
- reject result whose run_id / manifest hash / command / script / evidence dir
  do not match the current run
- do not trust a pre-existing `VALIDATOR_RESULT` record

No cryptographic signing / Phase 4 work.

## Exact host exit 0 rule

Host exit 0 requires **all** of:

1. Docker exit code = 0
2. explicit container outcome = `CARGO_SUCCEEDED_ARTIFACT_PRESENT`
3. `container_result_valid=YES`
4. `HOST_OUTCOME_INGESTION` `status=OK`
5. `host_infrastructure_status=OK`
6. `host_source_integrity_status=OK`
7. `post_build_integrity_status=OK`
8. `POST_BUILD_INTEGRITY.txt` `status=OK`
9. `post_build_integrity_ok=yes`
10. validator process exit code = 0
11. explicit host-preliminary structural PASS
12. no validator inference (guaranteed by committed Phase 3F-A)
13. fresh `VALIDATOR_RESULT` matches current run, manifest, validator identity,
    evidence directory, and captures

Otherwise host exit is nonzero. Failure is recorded truthfully in host-owned
validator-result metadata. Container evidence is not rewritten. Missing evidence
is not fabricated. Automated structural success is not claimed.

Host exit 0 meaning only:
`AUTOMATED HOST PACKAGE STRUCTURAL VALIDATION SUCCEEDED`

## preliminary_success_eligible treatment

`preliminary_success_eligible=NO` before invocation, after structural PASS, and
when host exit is 0. HOST_OUTCOME is not modified to YES. No validator-owned
fields are added to HOST_OUTCOME.

## Phase 3E supersession

- Suite count unchanged: **22** tests
- Changed method: `test_21_host_exit_not_validator_gated` →
  `test_21_host_exit_validator_gated_after_phase3f_b`
- Preserves: Phase 3E writers still do not invoke validator (`test_20`);
  POST_BUILD ownership / field-set / sync / fail-closed / no-overwrite coverage
- Requires current host source to contain Phase 3F-B invocation and gate

## Phase 3F-A test_22 supersession

- Suite count unchanged: **25** tests
- Changed method: `test_22_no_host_invocation_or_exit_gating_in_3f_a` →
  `test_22_host_gating_deferred_from_3f_a_implemented_in_3f_b`
- Preserves Phase 3F-A fact that validator writes no `VALIDATOR_RESULT`
- Requires current host source to contain Phase 3F-B gating

## Exact new Phase 3F-B test count

`test_phase3f_host_validator_gate.py`: **32** tests discovered / 32 run / 32 pass /
0 fail / 0 error / 0 skip.

## Exact Phase 3F-B regression results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_phase3f_host_validator_gate` | 32 | 32 | 32 | 0 | 0 | 0 |
| `test_phase3f_validator_prerequisites` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_validate_witness_evidence` | 65 | 65 | 65 | 0 | 0 | 0 |
| `test_phase3b_outcome_contract` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_phase3e_post_build_integrity` | 22 | 22 | 22 | 0 | 0 | 0 |
| `test_phase3d_host_outcome_ingestion` | 50 | 50 | 50 | 0 | 0 | 0 |
| `test_phase2b_mount_isolation` | 22 | 22 | 22 | 0 | 0 | 0 |
| `test_phase2a_host_preflight` | 18 | 18 | 18 | 0 | 0 | 0 |

Phase 3C was **not** run (container script prohibited / unchanged).

Expected `phase*_test_*` residue after all suites: **none**.

**Staging stop:** unexpected non-test residue was created under
`witness-package/scripts/` by the Windows `py` launcher during the first failed
mock-interpreter attempt (before `HOST_PYTHON=sys.executable` was fixed). Per
Task 17 these paths were **not** silently deleted and staging was **not**
performed while they remain. See final report.

## Blocker-status treatment (after Phase 3F-B)

| ID | Status after Phase 3F-B |
|----|-------------------------|
| RC4B-013 | `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT` (not CLOSED) |
| RC4B-022 | `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT` (not CLOSED) |
| RC4B-017 | `OPEN` with automatable host-preliminary subset only (not CLOSED) |
| RC4B-012 | `OPEN` |
| RC4B-029 | `OPEN` |
| RC4B-019 | `OPEN` |
| Any blocker CLOSED | **No** |

## Remaining gaps

- Full RC4B-017 four-yes / success-eligibility closure
- Final Witness submission lifecycle / inventory completeness
- Independent Witness reproduction / C-014
- rc5 packaging
- Phase 3G work

## Non-claims

- RC4 is NOT READY
- No rc5 tag
- No Independent Witness reproduction or PASS
- C-014 remains `NOT_STARTED`
- Structural PASS ≠ final success eligibility
- Host exit 0 ≠ Independent Witness PASS
- No blocker CLOSED
- Broad public-status documents deferred (Owner Option A)
- No real Docker, Cargo, compiler, bootstrap, ldd, network, product, or host
  Witness execution occurred during Phase 3F-B tests
