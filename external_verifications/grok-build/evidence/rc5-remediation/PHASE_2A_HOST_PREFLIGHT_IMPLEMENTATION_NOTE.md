# Phase 2A — Host pre-Docker identity and atomic evidence directory

## Base

| Item | Value |
|------|-------|
| Branch | `main` |
| Base commit | `cd8c4872fd714e60fa3d7616199443dac898b31e` |
| RC4 fixed tag | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` |
| RC4 disposition | **NOT READY** (unchanged) |
| RC5 tag | **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| C-014 | **NOT_STARTED** |
| Current corroborated status | **CURSOR_AND_PI_18_18_CROSS_ENV_CORROBORATED** (Pi fourth limited read-only recheck PASS; staged Phase 2A only — **not** Independent Witness) |

## Files changed

1. `external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh`
2. `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md`
3. `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`
4. `external_verifications/grok-build/witness-package/scripts/tests/test_phase2a_host_preflight.py`
5. `external_verifications/grok-build/evidence/rc5-remediation/PHASE_2A_HOST_PREFLIGHT_IMPLEMENTATION_NOTE.md` (this file)
6. `external_verifications/grok-build/evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`

## Test chronology (all results retained; none erased)

### 1) First Cursor run

| Metric | Value |
|--------|-------|
| Environment | Cursor |
| Discovered / run | 14 |
| Passed | 14 |
| Failed | 0 |

### 2) First Pi corroboration — FAIL / STOP

| Item | Result |
|------|--------|
| Pi first corroboration | **FAIL / STOP** |
| No Phase 2A commit | confirmed |
| Re-execution | **14 run, 8 passed, 6 failed** |
| Cause | Windows absolute script path passed into Bash `source` |
| Additional defects identified | (1) public main-suppression env bypass; (2) pre-gate evidence could retain `status=OK`; (3) symlink-collision behavioral coverage gap |

This failed result is **not** erased.

### 3) First correction run (Cursor)

| Metric | Value |
|--------|-------|
| Environment | Cursor |
| Discovered / run | 18 |
| Passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

First-correction production fixes retained on the staged tree:
- Removed the obsolete public main-suppression environment variable completely from the host script.
- Pipeline wrapped in `run_witness_narrow_build_main`; entry is standard:
  `if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then run_witness_narrow_build_main "$@"; fi`
- Production main resets `IDENTITY_GATE_CLOSED="no"` (ignores inherited env).
- Tests resolve the host script from `__file__`, set Bash `cwd` to the scripts directory, and source `./run_witness_narrow_build.sh` (relative POSIX path).
- Pre-gate evidence truthfulness and symlink-collision behavioral coverage added.

### 4) Second Pi recheck — FAIL / STOP

| Item | Result |
|------|--------|
| Pi second recheck | **FAIL / STOP** |
| Re-execution | **18 run, 0 passed, 18 failed** |
| Cause | literal equality between Python/Windows tempfile path and Git-Bash `/tmp` mock-Docker path during test setup |

This failed result is **not** erased.

### 5) Second limited correction (Cursor)

Before the corrected re-run, corroborated status was **FAILED_PENDING_CORRECTION**.

Second-correction test fixes applied:
- Removed cross-runtime absolute-path equality between Python and Bash/Git-Bash paths.
- Proved mock Docker via unique `MOCK_DOCKER_PHASE2A` marker + invocation log (not `command -v` absolute-path identity).
- Removed every remaining obsolete main-suppression env-variable literal from the host script and test module.
- Kept load-bearing proofs on production helpers / controlled production paths.
- Absolute `WORK_ROOT` / local clone URLs obtained from Bash `pwd` (runtime-local), never compared to Python tempfile strings.

### Second limited correction re-run (Cursor; retained)

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python3 -m unittest test_phase2a_host_preflight -v
```

| Metric | Value |
|--------|-------|
| Discovered / run | 18 |
| Passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

No real Docker daemon, Cargo, compiler, bootstrap tools, protoc, DotSlash, ldd, product, remote clone, or network-dependent commands were invoked. Mock docker only.

### 6) Third Pi recheck — FAIL / STOP

| Item | Result |
|------|--------|
| Pi third recheck | **FAIL / STOP** |
| Observed | **18 discovered, 18 run, 5 passed, 13 failed, 0 errors, 0 skipped** |
| Cause | tests created a Windows OS temporary workspace and attempted to reach the repository host script through an MSYS/Git-Bash relative traversal such as `../../../../../../dev/weaver-forge/.../run_witness_narrow_build.sh`; Git Bash could not resolve that path |

This failed result is **not** erased.

### 7) Before this (third) limited correction

| Item | Value |
|------|-------|
| Status | **FAILED_PENDING_CROSS_ENV_CORRECTION** |
| Blockers | RC4B-004 / RC4B-008 set to **OPEN_PENDING_CROSS_ENV_CORROBORATION**; RC4B-005 / RC4B-009 remain **OPEN**; none CLOSED |

### 8) Third limited correction (this pass — Cursor)

Third-correction test architecture fixes applied:
- Replace OS-default temporary workspace with a repository-local `TemporaryDirectory(dir=TESTS_DIR, prefix=phase2a_test_)`.
- Every Bash subprocess uses `cwd=SCRIPTS_DIR`.
- Host script is sourced only as `./run_witness_narrow_build.sh`.
- Bash-visible workspace is only `tests/<temporary-basename>` (no Windows absolute workspace path; no OS-temp-to-repository traversal; no cygpath/wslpath/WSL/drive-mapping).
- Cross-runtime setup probe (not counted among the 18 behavioral tests) proves host script readability, workspace existence, mock-docker executability, and shared probe-file visibility.
- Mock Docker proof retained via `MOCK_DOCKER_PHASE2A` marker + relative invocation log.
- Full-host identity-failure cases invoke production `run_witness_narrow_build_main` after sourcing; the test harness rebinds only `validate_work_root` so repository-local `scripts/tests/phase2a_test_*` WORK_ROOT values are accepted (production still refuses arbitrary in-repo WORK_ROOT for real Witness runs).
- All 18 behavioral tests retained; TemporaryDirectory cleanup verified; no `phase2a_test_*` leftovers under `scripts/tests`.

### Third limited correction re-run (Cursor; appended after success)

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python3 -m unittest test_phase2a_host_preflight -v
```

| Metric | Value |
|--------|-------|
| Discovered / run | 18 |
| Passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

Cursor staged-test result only. **Not** described as cross-environment corroborated at that time. Only a subsequent independent Pi run can supply that corroboration. No Independent Witness claim is made.

No real Docker daemon, Cargo, compiler, bootstrap tools, protoc, DotSlash, ldd, product, remote clone, or network-dependent commands were invoked. Mock docker only.

### 9) Pi fourth limited read-only recheck — PASS

| Item | Result |
|------|--------|
| Pi fourth limited read-only recheck | **PASS** |
| Discovered | 18 |
| Run | 18 |
| Passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |
| Repository-local workspace | **PASS** |
| Mock Docker isolation | **PASS** |
| Pre-gate evidence truthfulness | **PASS** |
| Atomic EVIDENCE_DIR and link/junction collision behavior | **PASS** |
| Temporary cleanup | **PASS** (no `phase2a_test_*` temporary directory remained; no untracked file remained; staged set unchanged; unstaged set empty) |
| Cross-environment staged-tree corroboration | **COMPLETE** |

This was **Pi read-only corroboration of the staged Phase 2A implementation** only.

Explicit non-claims for this entry:
- It was **not** Independent Witness execution.
- It was **not** an Independent Witness reproduction.
- It was **not** an Independent Witness PASS.
- It did **not** advance C-014 (`C-014` remains **NOT_STARTED**).
- `rc4` remains **NOT READY**.
- Final blocker closure still requires a future fixed candidate and repeat static audit.
- **REMEDIATED_ON_MAIN_PENDING_REAUDIT** for RC4B-004 / RC4B-008 is **not** final closure.

All prior failed Cursor/Pi results above remain preserved and are not erased, rewritten, or compressed.

## Exact implementation (cumulative Phase 2A)

### RC4B-004 — Docker ordering

- Non-Docker fact collection early; Docker CLI only after `IDENTITY_GATE_CLOSED=yes`.
- Gate closes only after full identity list including raw annotated tag type and Cargo.lock match.
- Pre-gate failure evidence cannot imply success.

### RC4B-005 — Raw annotated-tag type

- `git cat-file -t` must equal `tag` before checkout and before any Docker CLI.
- Diagnostic recording in `HOST_RUN_METADATA.txt`; normative schema field integration remains deferred (**OPEN**).

### RC4B-008 — Atomic `EVIDENCE_DIR`

- Parent may `mkdir -p`; final dir uses plain `mkdir` + bounded random-suffix retry.
- Collision and symlink/junction tests included.

### Pre-gate evidence truthfulness

- ENVIRONMENT facts collected without publishing `status=OK`; ENVIRONMENT schema published only after identity gate + Docker metadata.
- Package / source identity `status=OK` published only after all respective pre-Docker checks (including Cargo.lock for source).
- `finalize_pre_docker_infrastructure_failure` unconditionally rewrites pre-gate-sensitive mandatory files even if an earlier writer set `status=OK`.

### Cross-runtime test workspace model (third limited correction)

- Python-visible workspace: `TESTS_DIR / temporary_basename` (`phase2a_test_*`).
- Bash-visible workspace from `cwd=SCRIPTS_DIR`: `tests/temporary_basename`.
- Shared identifier is the temporary basename / `tests/<basename>` only.

## Historical test metrics (retained duplicates of chronology above)

### Failed Pi re-execution (historical; retained)

| Metric | Value |
|--------|-------|
| Run | 14 |
| Passed | 8 |
| Failed | 6 |
| Cause | Windows absolute path passed to Bash sourcing |

### First correction Cursor re-run (historical; retained)

| Metric | Value |
|--------|-------|
| Discovered / run | 18 |
| Passed | 18 |
| Failed | 0 |

### Second Pi recheck (historical; retained)

| Metric | Value |
|--------|-------|
| Run | 18 |
| Passed | 0 |
| Failed | 18 |
| Cause | Python/Windows tempfile path vs Git-Bash `/tmp` mock-Docker path literal equality |

### Third Pi recheck (historical; retained)

| Metric | Value |
|--------|-------|
| Run | 18 |
| Passed | 5 |
| Failed | 13 |
| Cause | relative traversal from Windows OS temp workspace to repository host script was not resolvable by Git Bash |

## Blocker status (after Pi fourth limited read-only recheck PASS)

| ID | Status | Notes |
|----|--------|-------|
| RC4B-004 | REMEDIATED_ON_MAIN_PENDING_REAUDIT | Cursor and Pi both 18/18 on staged Phase 2A; Docker CLI after identity closure; truthful pre-gate evidence; **not CLOSED**; final closure requires future fixed candidate + repeat static audit |
| RC4B-005 | OPEN | Enforcement present; normative schema integration deferred |
| RC4B-008 | REMEDIATED_ON_MAIN_PENDING_REAUDIT | Cursor and Pi both 18/18; atomic plain `mkdir` EVIDENCE_DIR; collisions do not merge/overwrite; **not CLOSED**; final closure requires future fixed candidate + repeat static audit |
| RC4B-009 | OPEN | Subset only |
| RC4B-010 | OPEN | Phase 2B reserved |
| All others | unchanged | **None CLOSED** |

## Explicit non-claims

- RC4 was **not** corrected or re-tagged; `rc4` remains **NOT READY**.
- No Independent Witness execution, reproduction, or PASS is claimed.
- Pi fourth PASS was read-only corroboration of the staged Phase 2A tree only; it did **not** advance C-014 (`NOT_STARTED`).
- No Phase 2B source-mount work was begun.
- No validator/template/fixture golden changes.
- All failed Pi/Cursor results above are retained; history is not rewritten as continuously passing.
- **REMEDIATED_ON_MAIN_PENDING_REAUDIT** is **not** final closure; final blocker closure still requires a future fixed candidate and repeat static audit.
