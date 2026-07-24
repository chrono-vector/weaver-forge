# Phase 4-S2 — Runtime writer, template, and S2 schema alignment

## Scope of this note

This note records **Phase 4-S2 only** (Pi-corrected runtime writer/template
alignment and versioned S2 schema activation). Phase 4-S3 (manifest/completeness
transitions, full fixture migration, full Phase 2A–3G regression, broader docs)
has **not** begun.

Owner Option A remained in force: `CLAIM_REGISTER.md` and broad public-status /
public-claim documents were not modified. The live remediation ledger was not
updated during S2. The Phase 4-S1 register and S1 implementation note were not
modified.

## Repository base

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (Phase 4-S1 base) | `a7db46dfbbee89cdd48636dbcbde694755d1d51c` |
| origin/main | `a7db46dfbbee89cdd48636dbcbde694755d1d51c` |
| Phase 3G commit | `4545373e48e14e18c4c51fdb34cf445cc1d704d9` |
| Phase 4-S1 commit | `a7db46dfbbee89cdd48636dbcbde694755d1d51c` |
| rc5 | absent |
| Historical tags | `grok-build-witness-v1.0.0-rc1` … `rc4` present; unchanged |

## Original S2 STOP and Pi conflict adjudication

The original S2 authorization conflicted with “don’t rewrite fixtures / don’t
falsely enforce unfinished writer targets.” Cursor STOPPED for Pi re-adjudication.

Pi classified the conflict as a **defect in the original S2 authorization**, not
an S1 design or implementation defect. Pi approved one corrected S2 commit with
fixed rulings summarized as:

1. S1 remains valid, immutable, and historically truthful.
2. The S1 schema register remains frozen.
3. Add a new versioned S2 schema register.
4. Active validator authority becomes the S2 register.
5. Historical S1 schemas/fixture shapes remain supported through an explicit
   compatibility boundary.
6. Existing fixture trees/manifests are not rewritten in S2.
7. Runtime writers/templates emit new S2 target shapes.
8. New S2-shaped controlled evidence is validated under S2 rules.
9. Historical fixtures remain accepted under historical compatibility until S3.
10. `NOT_REACHED` is initialization/pre-terminal only for new S2 runtime output.
11. Finalized S2 terminal packages use outcome-specific `NOT_APPLICABLE` variants.
12. Existing Phase 3C historical tests remain unchanged.
13. New S2 tests prove the new terminal invariant.
14. `HOST_RUN_METADATA` remains an append-log with exact canonical entry grammar.
15. S2 may implement recursive inventory enumeration and fail-closed object checks.
16. S3 retains manifest cryptographic closure, completeness transition, and full
    fixture migration.
17. S2 remains one commit.
18. There is no Phase 4-S4.

## Corrected S2 one-commit plan (executed)

Implement additive S2 register + loader/validator compatibility + writer/template
alignment + focused S2 tests + this note. Do not redesign S1. Do not migrate
fixtures. Do not implement S3 closure/completeness. Do not commit/push/tag.

## Frozen S1 register and note

| Item | Path / version |
|------|----------------|
| S1 register | `witness-package/schemas/canonical_schema_register_rc5_phase4_s1.json` (`rc5-phase4-s1.1`) — **unchanged** |
| S1 note | `evidence/rc5-remediation/PHASE_4_S1_CANONICAL_SCHEMA_VALIDATOR_MODE_IMPLEMENTATION_NOTE.md` — **unchanged** |

## S2 register path/version

| Item | Value |
|------|-------|
| Path | `external_verifications/grok-build/witness-package/schemas/canonical_schema_register_rc5_phase4_s2.json` |
| `schema_register_version` | `rc5-phase4-s2.1` |
| Supersedes | `rc5-phase4-s1.1` |
| Active authority | yes (single active canonical authority) |
| Historical compatibility | explicit S1 path; not a second coequal authority |

## Active-register selection and historical compatibility

- Loader default = S2 (`load_canonical_register()` / `load_active_register()`).
- Explicit historical S1 load via `load_historical_s1_register()` /
  `version=rc5-phase4-s1.1`.
- Unsupported versions fail closed.
- Supersession relationship validated on S2 documents.
- Validator uses active S2; historical fixtures without S2 markers use the
  historical compatibility field projection; S2-shaped evidence is never
  silently downgraded.

## Exact files created/modified

### Created

- `external_verifications/grok-build/witness-package/schemas/canonical_schema_register_rc5_phase4_s2.json`
- `external_verifications/grok-build/witness-package/scripts/evidence_inventory.py`
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase4_s2_runtime_schema_alignment.py`
- `external_verifications/grok-build/evidence/rc5-remediation/PHASE_4_S2_RUNTIME_SCHEMA_ALIGNMENT_IMPLEMENTATION_NOTE.md`

### Modified

- `external_verifications/grok-build/witness-package/scripts/schema_register_loader.py`
- `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py`
- `external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh`
- `external_verifications/grok-build/witness-package/scripts/container_narrow_build.sh`
- `external_verifications/grok-build/witness-package/templates/WEAVER_FORGE_PACKAGE_IDENTITY.txt`
- `external_verifications/grok-build/witness-package/templates/DEVIATIONS.txt`
- `external_verifications/grok-build/witness-package/scripts/VALIDATOR.md`
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase4_schema_authority.py` (narrow historical scoping)
- `external_verifications/grok-build/witness-package/scripts/tests/test_validate_witness_evidence.py` (narrow S2 compatibility assertions)

## Exact writer functions changed

### `run_witness_narrow_build.sh`

- `write_not_reached` retained (initialization only)
- added `write_s2_not_applicable_terminal`
- added `append_host_run_metadata_entry` (exact append-entry grammar)
- `assert_raw_annotated_package_tag_type` / `close_identity_gate` metadata appends
- `finalize_pre_docker_infrastructure_failure` PLACEHOLDER_ELIGIBLE → S2
  `NOT_APPLICABLE`; package identity failure rewrite emits S2 tag fields
- step 8 preliminary `DEVIATIONS` writer → S2 host schema
- step 8 / all `HOST_RUN_METADATA` append sites → entry grammar
- success package identity writer → S2 annotated-tag fields

### `container_narrow_build.sh`

- `_terminalize_bootstrap_file`
- `_terminalize_build_command_file`
- `_terminalize_build_environment_file`

## Exact templates changed

- `templates/WEAVER_FORGE_PACKAGE_IDENTITY.txt` — S2 annotated-tag fields
- `templates/DEVIATIONS.txt` — final Witness-input schema with `deviation_count`

## Annotated-tag result

New S2 runtime package identity emits ordered fields including
`weaver_forge_tag_ref`, `weaver_forge_tag_raw_object_type_required=tag`,
`weaver_forge_tag_raw_object_type_observed`, `weaver_forge_tag_peeled_commit`,
plus existing resolved/detached/authority fields. Lightweight/non-tag input
remains fail-closed via the pre-Docker raw tag-object check. No real rc5 or
production tag was created.

## DEVIATIONS result

- Preliminary host writer: `evidence_schema_version`, `deviation_state`,
  `deviation_count`, `automated_summary` (no Witness persona / no indexed
  fabrication).
- Final template: Witness-input ownership with required `deviation_count` and
  indexed records when `PRESENT`.
- Mode crossover rejected by validator.

## NOT_REACHED initialization policy

`write_not_reached` / container `init_evidence` retain safe initialization.
Finalized S2 packages must not retain raw initializer placeholders for
`BOOTSTRAP.txt` / `BUILD_COMMAND.txt` / `BUILD_ENVIRONMENT.txt`.

## Terminal NOT_APPLICABLE result

Host pre-Docker finalizer and container early-failure terminalizers rewrite
affected files to outcome-specific `NOT_APPLICABLE` records with
`applicability`, `reason`, `authoritative_outcome`, `failure_stage`,
`product_executed=NO`, `ldd_used=NO`. Successful/applicable paths retain normal
canonical schemas. No host rewrite of container-owned evidence after container
ownership; no false product/ldd execution claims.

## HOST_RUN_METADATA grammar

Append-log preserved. Each S2 entry:

```
BEGIN_HOST_RUN_METADATA_ENTRY
evidence_schema_version=1
run_id=...
witness_id=...
entry_kind=...
entry_utc=...
payload=...
END_HOST_RUN_METADATA_ENTRY
```

Exact key order normative; unknown keys rejected; `run_id` required per entry.
Historical free-form logs without BEGIN markers remain accepted via compatibility.

## Run-ID scope

Applied only to adjudicated ownership/cross-binding records (package identity,
`HOST_RUN_METADATA` entries, `HOST_OUTCOME_INGESTION`, validator-result binding
where already applicable). Not forced into every raw capture. RC4B-025 remains
unresolved.

## Recursive inventory helper scope

`evidence_inventory.py` provides read-only recursive enumeration with
deterministic normalized relative paths and fail-closed symlink/special-object/
path-escape/duplicate rejection. No final manifest cryptographic closure and no
`evidence_inventory_complete` transition. RC4B-020/026/027/028 remain open.

## Exact S2 focused test count/results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_phase4_s2_runtime_schema_alignment` | 11 | 11 | 11 | 0 | 0 | 0 |

## Coupled regression results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_phase4_schema_authority` | 15 | 15 | 15 | 0 | 0 | 0 |
| `test_validate_witness_evidence` | 68 | 68 | 68 | 0 | 0 | 0 |
| `test_phase3c_container_terminal_finalization` | 36 | 36 | 36 | 0 | 0 | 0 |
| `test_phase3f_validator_prerequisites` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_phase3f_host_validator_gate` | 32 | 32 | 32 | 0 | 0 | 0 |
| `test_phase3g_framework` | 23 | 23 | 23 | 0 | 0 | 0 |
| `test_phase3g_integration` | 11 | 11 | 11 | 0 | 0 | 0 |

`test_phase3d_host_outcome_ingestion`, `test_phase3e_post_build_integrity`,
`test_phase3b_outcome_contract`, and `test_phase2a_host_preflight` were not
required: those writer field bindings were not changed beyond HOST_RUN_METADATA
append grammar / package-identity/DEVIATIONS/terminal paths already covered by
S2 and Phase 3C suites.

## Historical fixtures unchanged

Existing fixture trees, fixture manifests, and fixture generators were not
modified. Historical `NOT_REACHED` fixtures remain accepted through the S1
compatibility path.

## S3 deferred work

- Final manifest cryptographic closure
- `evidence_inventory_complete` transition machinery
- Complete preliminary/final manifest inclusion policy
- Full fixture-family migration
- Full Phase 2A–3G regression set and broader docs

## Non-claims / blocker status

- No blocker is CLOSED
- RC4 remains NOT READY
- rc5 tag does not exist
- No Independent Witness reproduction or PASS
- C-014 remains NOT_STARTED
- No real Docker, Cargo, compiler, product, network, production Witness, manual
  Witness, or Independent Witness execution occurred during S2 tests
- No prohibited tool execution; PATH tripwires used where sourced bash tests
  could reach prohibited commands
