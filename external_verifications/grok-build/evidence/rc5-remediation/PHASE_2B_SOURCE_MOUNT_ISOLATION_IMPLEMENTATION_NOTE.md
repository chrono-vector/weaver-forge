# Phase 2B — Source-mount isolation (RC4B-010)

## Base

| Item | Value |
|------|-------|
| Branch | `main` |
| Base commit | `4d220f5e2f8594535fcd5e736b7d330902e3af0f` |
| RC4 fixed tag | `grok-build-witness-v1.0.0-rc4` → `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` |
| RC4 disposition | **NOT READY** (unchanged) |
| RC5 tag | **absent** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness PASS | **not claimed** |
| C-014 | **NOT_STARTED** |

## Original vulnerable mount topology

| Host source | Container target | Mode | Notes |
|-------------|------------------|------|-------|
| `${SRC_DIR}` (`${WORK_ROOT}/grok-build-src`) | `/src` | ro | intended source |
| `${WORK_ROOT}` | `/work` | rw | **broad parent mount** |
| `${EVIDENCE_DIR}` | `/evidence` | rw | |
| `${HOST_CONTAINER_SCRIPT}` (under `${WF_DIR}`) | `/witness/container_narrow_build.sh` | ro | file |

**Alias proof:** `GROK_BUILD_DIR` (`SRC_DIR`) is under `WORK_ROOT`, so the same checkout was reachable as `/work/grok-build-src` with write access (audit text names `/work/grok-build`; code path is `grok-build-src`). `WF_DIR` was similarly writable via `/work/weaver-forge`.

## Corrected mount topology

| Host source | Container target | Mode |
|-------------|------------------|------|
| `${SRC_DIR}` | `/src` | ro (exactly once) |
| `${HOST_CONTAINER_SCRIPT}` | `/witness/container_narrow_build.sh` | ro (file) |
| `${CARGO_TARGET_DIR}` | `/work/cargo-target` | rw |
| `${BOOTSTRAP_CARGO_TARGET_DIR}` | `/work/bootstrap-cargo-target` | rw |
| `${CARGO_HOME_DIR}` | `/work/cargo-home` | rw |
| `${HOME_DIR}` | `/work/home` | rw |
| `${DOTSLASH_CACHE_DIR}` | `/work/dotslash-cache` | rw |
| `${BOOTSTRAP_DIR}` | `/work/bootstrap` | rw |
| `${TMP_DIR}` | `/work/tmp` | rw |
| `${EVIDENCE_DIR}` | `/evidence` | rw |

**Prohibited:** broad `WORK_ROOT` → `/work` writable mount; any writable mount of either checkout or its ancestor/descendant; writable targets overlapping `/src`.

## Mount validator invariants

`validate_mount_plan` runs after directories exist and **before** `docker run` (no Docker invoked by the validator). Fail-closed order:

1. mount record structurally present
2. source/destination/mode field syntax (comma, CR, LF rejected; ordinary spaces allowed)
3. required source exists (distinct from canonicalization failure; sources are not created here)
4. source canonicalization succeeds (no unresolved textual fallback)
5. checkout overlap relationships validated
6. destination overlap validated
7. duplicate destination and ro/rw conflicts validated
8. structured Docker argv constructed (only after validation)
9. Docker invoked

Additional fail-closed cases:

- writable host source equals / inside / ancestor of `GROK_BUILD_DIR` or `WF_DIR`
- writable host source equals `WORK_ROOT`
- writable container target equals / inside / ancestor of `/src`
- duplicate container targets
- same host source mounted both ro and rw

Path comparison is canonicalized (symlink/junction aware where supported) and component-safe (avoids `/source` vs `/source-other` prefix false positives). Docker `--mount` field values containing comma/CR/LF are rejected before argv construction (no escaping).

## Pre/post source-integrity checks

- Pre-Docker: existing detached HEAD + clean-tree + Cargo.lock checks preserved; snapshot recorded via `record_pre_docker_source_integrity_snapshot`.
- Post-Docker: existing HEAD/clean/Cargo.lock rechecks preserved; `enforce_post_docker_source_integrity_boundary` forces `outcome=INFRASTRUCTURE_FAILURE` when HEAD changed or tree became dirty (not PASS-capable).
- These checks do **not** claim protection against every possible filesystem mutation beyond HEAD and clean-tree porcelain.

## Container path model

- Canonical source remains `/src`; build cwd `/src`.
- No `/work/grok-build` reference in executable code.
- `CARGO_TARGET_DIR`, bootstrap target, `HOME`/`CARGO_HOME`, `TMPDIR`, evidence use dedicated writable mounts.
- `BUILD_ENVIRONMENT.txt` records `mount_work=broad_WORK_ROOT_mount_prohibited` (required key retained; templates/fixtures/validator untouched).

## Files changed (authorized Phase 2B set)

1. `external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh`
2. `external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh`
3. `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md`
4. `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`
5. `external_verifications/grok-build/witness-package/scripts/tests/test_phase2b_mount_isolation.py`
6. `external_verifications/grok-build/evidence/rc5-remediation/PHASE_2B_SOURCE_MOUNT_ISOLATION_IMPLEMENTATION_NOTE.md` (this file)
7. `external_verifications/grok-build/evidence/rc4-static-blind-audit/INTEGRATED_REMEDIATION_LIST.md`

## Exact tests executed and results

### Cursor initial Phase 2B implementation (preserved)

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python3 -m unittest test_phase2b_mount_isolation -v
```

| Metric | Value |
|--------|-------|
| Discovered / run | 18 |
| Passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

### Cursor initial Phase 2A regression (preserved)

```text
python3 -m unittest test_phase2a_host_preflight -v
```

| Metric | Value |
|--------|-------|
| Discovered / run | 18 |
| Passed | 18 |
| Failed | 0 |
| Errors | 0 |
| Skipped | 0 |

### Pi first Phase 2B staged-tree corroboration (appended; do not erase)

| Item | Value |
|------|-------|
| Result | **PASS WITH CORRECTIONS REQUIRED BEFORE COMMIT** |
| Phase 2B runtime | 18 discovered / 18 run / 18 passed / 0 failed / 0 errors / 0 skipped |
| Phase 2A regression | 18 discovered / 18 run / 18 passed / 0 failed / 0 errors / 0 skipped |
| Corrections identified | (1) comma-bearing `--mount` fields not rejected; (2) writable source inside `WF_DIR` lacked explicit behavioral test; (3) missing required source lacked explicit behavioral test; (4) canonicalization failure lacked explicit behavioral test |
| corroboration_status (before corrected Cursor execution) | **CORRECTIONS_PENDING** |

### Cursor limited correction pass (appended after corrected suite)

```text
cd external_verifications/grok-build/witness-package/scripts/tests
python3 -m unittest test_phase2b_mount_isolation -v
python3 -m unittest test_phase2a_host_preflight -v
```

| Suite | Discovered | Run | Passed | Failed | Errors | Skipped |
|-------|------------|-----|--------|--------|--------|---------|
| Phase 2B (corrected) | 22 | 22 | 22 | 0 | 0 | 0 |
| Phase 2A regression | 18 | 18 | 18 | 0 | 0 | 0 |

New Phase 2B methods: `test_reject_comma_in_mount_fields`, `test_reject_writable_source_inside_wf_dir`, `test_reject_missing_required_mount_source`, `test_reject_mount_source_canonicalization_failure`.

Cross-environment corroboration is **not** complete. Independent Witness execution / reproduction / PASS is **not** claimed.

### Pi corrected-suite read-only recheck (appended; do not erase)

| Item | Value |
|------|-------|
| Result | **PASS** |
| Phase 2B | 22 run / 22 passed / 0 failed / 0 errors / 0 skipped |
| Phase 2A regression | 18 run / 18 passed / 0 failed / 0 errors / 0 skipped |
| Static corrections corroborated | comma/CR/LF mount-field rejection; writable source inside `WF_DIR` rejection; missing required source rejection; canonicalization failure rejection; Docker invocation zero on mount validation failure; read-only unique `/src` mount; no broad `WORK_ROOT` writable mount; no writable source alias; pre/post source integrity boundary |
| Post-test cleanup | **PASS** |
| Cross-environment corrected-suite corroboration | **COMPLETE** |

This was **Pi read-only corroboration** of the staged owner-side remediation. It was **not** Independent Witness execution, **not** Independent Witness reproduction, and **not** Independent Witness PASS. C-014 was **not** advanced. **rc4 remains NOT READY**. **No rc5 tag exists**. Final closure of RC4B-010 requires a future fixed candidate and repeat static audit. Prior Cursor and Pi results (including PASS WITH CORRECTIONS REQUIRED BEFORE COMMIT) remain preserved above and are not relabeled.

## Prohibited tooling

No real Docker daemon, Cargo, rustc, rustup, DotSlash, protoc, ldd, full Witness workflow, Grok Build product, remote clone, or other network-dependent commands were executed for this phase. Tests used Python standard library, Bash, repository-local temporary workspaces, local temporary Git repositories, and mock Docker only.

## Blocker statuses

| Blocker | Status |
|---------|--------|
| RC4B-010 | **REMEDIATED_ON_MAIN_PENDING_REAUDIT** (advanced after Pi corrected-suite PASS; **not CLOSED**; **REMEDIATED_ON_MAIN_PENDING_REAUDIT is not final closure**; final closure requires a future fixed candidate + repeat static audit) |
| RC4B-009 | **OPEN** (Phase 2B adds mount-plan behavioral subset only) |
| RC4B-005 | **OPEN** (unchanged) |
| RC4B-004 / RC4B-008 | unchanged from Phase 2A disposition (REMEDIATED_ON_MAIN_PENDING_REAUDIT) |
| All others | unchanged |
| Any CLOSED | **none** |

## Remaining limitations

- RC4B-009 broader host-safety / generator-backed coverage still incomplete.
- RC4B-005 normative annotated-tag evidence schema integration still deferred.
- Post-Docker integrity covers HEAD + clean-tree (and existing Cargo.lock fields); not every filesystem mutation class.
- No Independent Witness reproduction; no PASS claimed; C-014 NOT_STARTED.
- Final closure of RC4B-010 requires future fixed candidate + repeat static audit.

## Disposition

- **rc4 remains NOT READY**
- **rc5 tag does not exist**
- Implementation is on `main` toward a possible future rc5 candidate
- Phase 2C / Phase 3 not started
