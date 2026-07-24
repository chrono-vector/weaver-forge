# Phase 3F — Validator-gated exit implementation note

## Scope of this note

This note records **Phase 3F-A only** (Pi-adjudicated validator prerequisites).
Phase 3F-B (host invokes validator, captures result, writes host-owned
`VALIDATOR_RESULT.txt` outside `EVIDENCE_DIR`, and makes host exit 0
validator-gated) is **not** implemented here and must not begin until
Phase 3F-A receives Pi conformance PASS and is committed and pushed.

Owner Option A remained in force: `CLAIM_REGISTER.md` and broad public-status
documents were not modified.

## Repository base

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (pre-change base) | `c576f2d865e8c297f3caf2a9392bdeafc2270f4c` |
| origin/main (pre-change) | `c576f2d865e8c297f3caf2a9392bdeafc2270f4c` |
| Prior phase | Phase 3E at same HEAD |
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

1. **Phase 3F-A (this task):** remove validator outcome inference; require
   explicit authoritative outcome; add and structurally validate
   `HOST_OUTCOME_INGESTION.txt`; align closed auxiliary inventory; implement
   the automatable RC4B-017 structural subset; update directly affected
   validator tests/fixtures/docs/ledger/note.
2. **Phase 3F-B (later, not authorized now):** host invokes validator; host
   captures validator result; host writes host-owned `VALIDATOR_RESULT.txt`
   outside `EVIDENCE_DIR`; host exit 0 becomes validator-gated.

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

### Explicitly unchanged (prohibited / deferred)

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
- Exposed for isolated tests in Phase 3F-A; host does not invoke it yet

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
directory. No durable `VALIDATOR_RESULT.txt` is created in Phase 3F-A.

## Host invocation / exit gating deferred to 3F-B

`run_witness_narrow_build.sh` is unchanged. No host call to the validator.
No validator-gated `FINAL_EXIT_CODE=0`. No `VALIDATOR_RESULT.txt` writer.

## Phase 3B test_23 supersession

- Historical visibility preserved: Phase 3B contract/note still record the
  inference violation as discovered (`UNRESOLVED`, not ACCEPTABLE)
- Stale current-source expectation that inference must still exist is superseded
- Current validator source must contain no inference fallback
- `AUTHORITATIVE_OUTCOME_CONTRACT.json` and Phase 3B note unchanged
- Unrelated Phase 3B tests preserved

## Exact new test count discovered

`test_phase3f_validator_prerequisites.py`: **25** tests discovered / 25 run / 25 pass / 0 fail / 0 error / 0 skip.

## Exact regression results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_phase3f_validator_prerequisites` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_validate_witness_evidence` | 65 | 65 | 65 | 0 | 0 | 0 |
| `test_phase3b_outcome_contract` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_phase3e_post_build_integrity` | 22 | 22 | 22 | 0 | 0 | 0 |
| `test_phase3d_host_outcome_ingestion` | 50 | 50 | 50 | 0 | 0 | 0 |
| `test_phase2b_mount_isolation` | 22 | 22 | 22 | 0 | 0 | 0 |
| `test_phase2a_host_preflight` | 18 | 18 | 18 | 0 | 0 | 0 |

Phase 3C was **not** run (container script prohibited from modification; ownership guarantee unchanged).
Phase 3F-B host-gating tests were **not** run (not implemented).

Temp residue after all suites: **none** matching `phase2a_test_*` … `phase3f_test_*`.

## Blocker-status treatment

| ID | Status after Phase 3F-A |
|----|-------------------------|
| RC4B-022 | `IMPLEMENTED_ON_MAIN_PENDING_INTEGRATION_AND_REAUDIT` (not CLOSED) |
| RC4B-017 | `OPEN` with automatable host-preliminary subset only (not CLOSED) |
| RC4B-013 | `OPEN` (host invocation / exit gating = Phase 3F-B) |
| RC4B-012 | `OPEN` |
| RC4B-029 | `OPEN` |
| RC4B-019 | `OPEN` |
| Any blocker CLOSED | **No** |

## Remaining gaps (Phase 3F-B and later)

- Host invokes validator after host finalization
- Host captures validator result
- Host writes `VALIDATOR_RESULT.txt` outside `EVIDENCE_DIR`
- Host exit 0 becomes validator-gated
- Full RC4B-017 four-yes / success-eligibility closure
- Final Witness submission lifecycle / inventory completeness
- Independent Witness reproduction / C-014
- rc5 packaging

## Non-claims

- RC4 is NOT READY
- No rc5 tag
- No Independent Witness reproduction or PASS
- C-014 remains `NOT_STARTED`
- Structural PASS ≠ final success eligibility
- Phase 3F-A ≠ Phase 3F-B
- No blocker CLOSED
- Broad public-status documents deferred (Owner Option A)
