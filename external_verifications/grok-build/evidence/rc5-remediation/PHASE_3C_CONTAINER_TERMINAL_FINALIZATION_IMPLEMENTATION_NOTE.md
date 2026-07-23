# Phase 3C — Container Terminal-Outcome Finalization Implementation Note

## Base

| Item | Value |
|------|-------|
| Branch | `main` |
| Base commit | `4b087cd5219c6f8083ecb4bab911627d31566026` |
| Contract | `witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json` |
| Contract version | `1.0.0-phase3b` |
| RC4 disposition | **NOT READY** (unchanged) |
| RC5 tag | **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **not claimed** |
| C-014 | **NOT_STARTED** |

## Exact five terminal outcomes

1. `BUILD_NOT_STARTED`
2. `CARGO_FAILED`
3. `CARGO_SUCCEEDED_ARTIFACT_MISSING`
4. `CARGO_SUCCEEDED_ARTIFACT_PRESENT`
5. `INFRASTRUCTURE_FAILURE`

## Files changed (Phase 3C)

1. `witness-package/scripts/container_narrow_build.sh`
2. `witness-package/scripts/tests/test_phase3c_container_terminal_finalization.py`
3. `evidence/rc5-remediation/PHASE_3C_CONTAINER_TERMINAL_FINALIZATION_IMPLEMENTATION_NOTE.md` (this file)
4. `evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`
5. `witness-package/WITNESS_REQUIREMENTS.md`
6. `witness-package/WITNESS_RUNBOOK.md`

Host script, validator, contract JSON, templates, and fixtures were **not** modified.

## Centralized finalization design

Authoritative function: `finalize_container_terminal_outcome`.

Properties implemented:

- Every supported terminal container path routes through this boundary.
- Writes an explicit terminal `outcome=` exactly once into container-owned outcome evidence.
- Never infers a different outcome from secondary facts; the caller-supplied outcome is authoritative.
- Never writes host-owned `POST_BUILD_INTEGRITY.txt` or `DOCKER_EXIT_CODE.txt`.
- Never invokes the validator.
- Idempotent on same-value repeat; fail-closed on conflicting repeat.
- Sets `EVIDENCE_FINALIZED=YES` only after mandatory final writes succeed.
- Finalizer failure returns nonzero and does not claim evidence completeness.
- Trap recursion prevented via `FINALIZING_IN_PROGRESS` and temporary `trap - ERR`.
- A valid recorded container outcome is never silently replaced.

## Source guard

Entry refactored to `container_narrow_build_main` with:

```bash
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  container_narrow_build_main "$@"
fi
```

Direct execution preserves workflow behavior. Sourcing defines functions only and performs no build, bootstrap, package-manager, network, or product action. No environment-variable bypass alters production behavior.

## Atomic write behavior

Shared writer: `write_evidence_file_atomic`.

- Writes a temporary file in the same evidence directory.
- Renames into the final path.
- Removes the temporary file on failure where possible.
- No `eval`.
- Paths with spaces preserved via careful quoting.
- Dynamically generated single-line field values reject embedded CR/LF via `reject_field_newlines`.

## Outcome-specific behavior

| Outcome | cargo_started | cargo_exit_code | artifact | success |
|---------|---------------|-----------------|----------|---------|
| `BUILD_NOT_STARTED` | NO | `NOT_APPLICABLE` | absent / static N/A | impossible |
| `CARGO_FAILED` | YES | preserved nonzero | absent / static N/A | impossible |
| `CARGO_SUCCEEDED_ARTIFACT_MISSING` | YES | 0 | explicit absent | impossible (exit 42) |
| `CARGO_SUCCEEDED_ARTIFACT_PRESENT` | YES | 0 | preserved identity + static | success-capable; static failure exits 43 with same outcome |
| `INFRASTRUCTURE_FAILURE` | YES or NO (preserved) | preserved when cargo ran | context / best-effort | impossible |

## Routed paths

- `fail_build_not_started`
- `fail_infrastructure`
- unexpected ERR trap after evidence initialization (`on_err`)
- Cargo nonzero
- Cargo zero + artifact missing
- Cargo zero + artifact present + static success
- Cargo zero + artifact present + static failure
- Bootstrap / clean-target / tool identity / source-lock / evidence-generation failures that already called `fail_build_not_started` or `fail_infrastructure`

## Writer-failure limitation

If the evidence directory is missing or not writable, the finalizer cannot produce a complete evidence package. It emits a clear stderr message, returns nonzero, and leaves `EVIDENCE_FINALIZED=NO`. Total filesystem failure cannot truthfully yield a complete package; that boundary is unavoidable and explicit.

## Failure-only final NOT_REACHED limitations

Allowed failure-only final `NOT_REACHED` limitations for early evidence fields:

1. `BOOTSTRAP.txt` may retain a final `NOT_REACHED` only when failure occurs before bootstrap begins or before a truthful bootstrap terminal fact can be recorded.
2. `BUILD_ENVIRONMENT.txt` may retain a final `NOT_REACHED` only when failure occurs before build-environment capture begins or before a truthful environment terminal fact can be recorded.
3. These cases are limited to failure-only outcomes such as `BUILD_NOT_STARTED` or early `INFRASTRUCTURE_FAILURE`.
4. They are not permitted in a success-capable `CARGO_SUCCEEDED_ARTIFACT_PRESENT` submission.
5. They do not satisfy success eligibility, evidence completeness, validator PASS, or machine PASS ceiling.
6. They are schema limitations, not completed evidence.
7. RC4B-024 remains **OPEN** because future schema/template/validator alignment must replace or formally govern these remaining sentinels.
8. No claim is made that Phase 3C eliminates every final `NOT_REACHED` value.
9. Host ingestion, validator alignment, full integration tests, fixed candidate creation, and repeat static audit remain required.
10. RC4 remains **NOT READY**; `rc5` does not exist; no Independent Witness reproduction/PASS occurred; C-014 remains **NOT_STARTED**.

These limitations occur only where: execution fails before the relevant facts can truthfully be recorded; the existing schema has no truthful terminal `FAILED` or `NOT_APPLICABLE` alternative for that field; the authoritative terminal outcome is failure-only; and success eligibility is impossible.

## Test safety

- Python standard library only
- Repository-local temporary workspaces under `scripts/tests/` (`phase3c_test_*`)
- Never calls `container_narrow_build_main`
- Mock prohibited commands first on PATH; mocks never delegate
- No real Docker, Cargo, compiler, package manager, network, validator, or product execution
- Temporary directories cleaned on success and failure

## Exact test command / results

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python3 -m unittest test_phase3c_container_terminal_finalization -v
```

Required: **36 discovered / 36 run / 36 passed / 0 failed / 0 errors / 0 skipped**

Observed (this staging session):

```text
Ran 36 tests in 220.805s
OK
```

## Regression results

```text
python3 -m unittest test_phase3b_outcome_contract -v   # Ran 25 tests — OK
python3 -m unittest test_phase2b_mount_isolation -v    # Ran 22 tests — OK
python3 -m unittest test_phase2a_host_preflight -v     # Ran 18 tests — OK
```

Temporary directories: no `phase2a_test_*`, `phase2b_test_*`, or `phase3c_test_*` remained after the suite.
## Unresolved (out of Phase 3C scope)

- Host overwrite of container `BUILD_EXIT_CODE.txt` after source-integrity failure remains an **UNRESOLVED** Phase 3D violation (`HOST_OVERWRITES_CONTAINER_BUILD_EXIT_CODE`).
- Validator outcome inference remains an **UNRESOLVED** later-slice violation (`VALIDATOR_DETERMINE_OUTCOME_INFERENCE`).
- Phase 3C does **not** claim complete end-to-end outcome preservation.

## Blocker tracking (Phase 3C)

| ID | Status |
|----|--------|
| RC4B-011 | **OPEN** — container-side terminal finalization implemented on main; host ingestion, validator/schema alignment, full integration tests, fixed candidate, and repeat static audit remain required |
| RC4B-024 | **OPEN** — same Phase 3C note as RC4B-011 |
| RC4B-029 | **OPEN** — same Phase 3C note as RC4B-011 |
| RC4B-014 / 022 / 023 | `CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING` (unchanged) |
| RC4B-019 / 005 / 009 | **OPEN** (unchanged) |

**No blocker is CLOSED.** Do not use `REMEDIATED_ON_MAIN_PENDING_REAUDIT` for this container-only slice.

## Explicit non-claims

- RC4 remains **NOT READY**.
- RC5 tag absent.
- No Independent Witness reproduction / PASS.
- C-014 remains **NOT_STARTED**.
- No end-to-end compliance claim.
- Phase 3D / 3E / 3F / 3G not begun.
