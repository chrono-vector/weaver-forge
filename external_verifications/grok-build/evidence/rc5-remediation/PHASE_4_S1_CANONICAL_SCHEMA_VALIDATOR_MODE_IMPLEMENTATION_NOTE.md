# Phase 4-S1 — Canonical schema authority and validator mode framework

## Scope of this note

This note records **Phase 4-S1** only (Pi-adjudicated canonical schema register
and explicit validator-mode framework). Phase 4-S2 (runtime writer/template
alignment) and Phase 4-S3 (manifest/completeness/fixtures/full regression/docs)
have **not** begun.

Owner Option A remained in force: `CLAIM_REGISTER.md` and broad public-status /
public-claim documents were not modified. The live remediation ledger was not
updated during S1.

## Repository base

| Item | Value |
|------|-------|
| Branch | `main` |
| HEAD (Phase 3G-B base) | `4545373e48e14e18c4c51fdb34cf445cc1d704d9` |
| origin/main | `4545373e48e14e18c4c51fdb34cf445cc1d704d9` |
| rc5 | absent |
| Historical tags | `grok-build-witness-v1.0.0-rc1` … `rc4` present; unchanged |

## Cursor implementation-side analysis

Cursor identified duplicated schema authority across:

- `validate_witness_evidence.py` (`REQUIRED_FILES`, `FILE_REQUIRED_FIELDS`,
  `HOST_OUTCOME_INGESTION_FIELDS`, placeholder rules, manifest grammar)
- host/container writers and templates
- fixtures / `fixtures_lib.py`
- docs (`VALIDATOR.md`, requirements/runbook)

and the Phase 3F/3G fact that `--host-preliminary` still required final manual
Witness files, conflicting with automated preliminary package truthfulness.

## Pi independent adjudication

Pi independently selected:

- Phase 4 purpose: canonical schema/mode/manifest authority and later
  runtime/validator/template/fixture alignment
- one versioned machine-readable plain-JSON schema register
- validator modes: explicit `--host-preliminary`, explicit `--final-submission`,
  default retained only as compatibility alias to final-submission
- separate automated-preliminary and final-Witness DEVIATIONS schemas
- preliminary/final mode-specific manifests
- separate early-failure schema variants by terminal outcome
- run-id only in ownership/cross-binding records
- three-stage Phase 4 sequence under one fixed Pi plan: S1 → S2 → S3

## Selected architecture

One committed JSON register under `witness-package/schemas/`, loaded by a
standard-library fail-closed loader, with the validator binding mode-required
file sets and exact-schema enforcement boundaries to that register while keeping
a labeled compatibility projection of current field tuples (load-time equality
checked; not a second authority).

## Three-stage Phase 4 sequence

1. **S1** — schema authority + validator mode framework (this note)
2. **S2** — runtime writer/template alignment to register target schemas
3. **S3** — manifest/completeness state machine, fixtures, full regression, docs

## S1 purpose and exact boundary

Establish one versioned canonical machine-readable schema authority and an
explicit validator-mode framework **without** changing host/container writer
behavior, templates, fixtures, or historical Phase 2A–3G tests.

S1 must not activate schema rules that make still-unaligned current runtime
writers invalid before S2.

## Exact files created/modified

### Created

- `external_verifications/grok-build/witness-package/schemas/canonical_schema_register_rc5_phase4_s1.json`
- `external_verifications/grok-build/witness-package/scripts/schema_register_loader.py`
- `external_verifications/grok-build/witness-package/scripts/tests/test_phase4_schema_authority.py`
- `external_verifications/grok-build/evidence/rc5-remediation/PHASE_4_S1_CANONICAL_SCHEMA_VALIDATOR_MODE_IMPLEMENTATION_NOTE.md`

### Modified

- `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py`
- `external_verifications/grok-build/witness-package/scripts/VALIDATOR.md`

## Canonical register location and version

| Item | Value |
|------|-------|
| Path | `external_verifications/grok-build/witness-package/schemas/canonical_schema_register_rc5_phase4_s1.json` |
| `schema_register_version` | `rc5-phase4-s1.1` |
| Family | `rc5_remediation_canonical_schema` |
| `evidence_schema_version` | `1` |

Additive supersession only. Does not rewrite
`AUTHORITATIVE_OUTCOME_CONTRACT.json`, rc1–rc4 evidence, historical fixtures,
historical notes, or original blocker wording. Unsupported register versions
fail closed.

## Canonical register structure

Top-level keys (unknown keys rejected):

- `schema_register_version`, `family`, `evidence_schema_version`,
  `supported_register_versions`, `supersession`
- `lifecycle_modes`, `default_mode_compatibility_alias`
- `mode_required_file_sets`, `mode_accepted_supporting_files`,
  `closed_aux_evidence_files`
- `run_id_policy`, `evidence_completeness_inventory`
- `artifacts[]` with artifact identity, owner, lifecycle modes, required-file
  classification, activation, ordered fields, required/optional/conditional
  variants, exact-field-set policy, legal values, run-id binding flags

## Artifact/mode scope

Canonical automated/runtime artifacts represented include:
`BUILD_EXIT_CODE.txt`, `HOST_OUTCOME_INGESTION.txt`, `POST_BUILD_INTEGRITY.txt`,
`BOOTSTRAP.txt`, `BUILD_COMMAND.txt`, `BUILD_ENVIRONMENT.txt`,
`ARTIFACT_IDENTITY.txt`, `STATIC_ARTIFACT_INSPECTION.txt`,
`HOST_RUN_METADATA.txt`, mode-aware `DEVIATIONS.txt`,
`EVIDENCE_MANIFEST.sha256` grammar/policy, and host-owned outside-EVIDENCE_DIR
validator-result record schema.

Mode-aware final-input schemas: `WITNESS_STATEMENT.md`, `WITNESS_VERDICT.md`,
`REDACTIONS.md`, final-mode `DEVIATIONS.txt`.

Completeness/inventory state definitions included for later S3 activation.
RC4B-005 annotated-tag identity target fields included as future S2 alignment.
`CONTAINER_RESULT.txt` excluded (no authoritative artifact found).

## Schema activation versus future-alignment distinction

| Activation | Meaning in S1 |
|------------|---------------|
| `enforced_current_compatible` | Bound where current writers/fixtures already match |
| `defined_future_s2_writer_alignment` | Defined only; not enforced until S2 |
| `defined_future_s3_manifest_completeness` | Defined only; not activated until S3 |
| `defined_structural_only_s1` | Mode/policy structural representation in S1 |

Exact enforcement retained at minimum for `POST_BUILD_INTEGRITY.txt` and
`HOST_OUTCOME_INGESTION.txt`. Preliminary DEVIATIONS target extensions,
annotated-tag identity additions, early-failure `NOT_APPLICABLE` variants, and
final-manifest cryptographic closure are represented but not falsely enforced.

## Schema-loader behavior

`scripts/schema_register_loader.py`:

- deterministic load from committed path
- explicit supported version set
- structural validation; unknown-key rejection; duplicate detection
- legal-mode validation; artifact lookup by filename+mode
- ordered / required / optional / exact-policy / legal-value accessors
- fail-closed diagnostics via `SchemaRegisterError`

## Validator mode behavior

- `--host-preliminary` and `--final-submission` are mutually exclusive
- default (neither flag) is a documented compatibility alias to final-submission
- `validate_dir(..., host_preliminary=True)` remains the Phase 3F compatibility
  API and maps to host-preliminary
- validator remains read-only and performs no outcome inference
- structural PASS wording identifies the selected mode
- final-submission PASS explicitly denies Independent Witness PASS, final
  eligibility, READY, and rc5 readiness
- host-preliminary PASS retains the Phase 3F-B exact suffix text required by
  the host gate

## Host-preliminary required-file result

Host-preliminary required set excludes `WITNESS_STATEMENT.md`,
`WITNESS_VERDICT.md`, and `REDACTIONS.md`. Those files are
`accepted_supporting` (optional; may remain for fixture regression visibility;
do not elevate eligibility). `preliminary_success_eligible` remains `NO`.
`evidence_inventory_complete` is not interpreted as final Witness completion.
Existing successful automated preliminary behavior remains reachable.

## Final-submission skeleton result

Final-submission mode defines the final required-file set and structural manual
input expectations. Compatible final-shaped validation is retained. Final
manifest cryptographic closure and evidence-completeness transition machinery
are **not** implemented in S1. Mode is explicitly not fully hardened until S3.

## DEVIATIONS schema definitions

- `DEVIATIONS.txt@host-preliminary` — host-owned automated preliminary schema
- `DEVIATIONS.txt@final-submission` — Witness-input final schema with indexed
  deviation role when `deviation_state=PRESENT`

No-deviation state `NONE` retained. Severity/redaction/ceiling policy beyond
current compatible checks remains deferred (RC4B-007 / RC4B-034–036 not
implemented).

## Annotated-tag schema definitions (RC4B-005 target)

Future-alignment fields on package identity (not enforced in S1):

- `weaver_forge_tag_requested`
- `weaver_forge_tag_ref`
- `weaver_forge_tag_raw_object_type_required` (`tag`)
- `weaver_forge_tag_raw_object_type_observed`
- `weaver_forge_tag_peeled_commit`
- `weaver_forge_commit_resolved`
- `package_clone_detached`
- `package_commit_authority`

No runtime writer change. No real rc5 tag created.

## Early-failure variant definitions

For `BOOTSTRAP.txt`, `BUILD_COMMAND.txt`, `BUILD_ENVIRONMENT.txt`:

- current-compatible `NOT_REACHED` placeholder variant (enforced as today)
- future S2 `NOT_APPLICABLE` outcome-specific variant (defined, not activated)

`container_narrow_build.sh` unchanged.

## Run-ID policy

Ownership/cross-binding only for package identity, `HOST_RUN_METADATA`,
`HOST_OUTCOME_INGESTION`, post-build binding context, host validator-result
record, final manual forms where already structurally required in final mode,
and manifest/inventory lifecycle metadata when represented. Not forced into
every raw capture. RC4B-025 remains unresolved.

## Phase 4-S1 focused test count/results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_phase4_schema_authority` | 15 | 15 | 15 | 0 | 0 | 0 |

## Directly coupled regression results

| Suite | Discovered | Run | Pass | Fail | Error | Skip |
|-------|------------|-----|------|------|-------|------|
| `test_validate_witness_evidence` | 65 | 65 | 65 | 0 | 0 | 0 |
| `test_phase3f_validator_prerequisites` | 25 | 25 | 25 | 0 | 0 | 0 |
| `test_phase3f_host_validator_gate` | 32 | 32 | 32 | 0 | 0 | 0 |
| `test_phase3g_framework` | 23 | 23 | 23 | 0 | 0 | 0 |
| `test_phase3g_integration` | 11 | 11 | 11 | 0 | 0 | 0 |

## Runtime writers / templates / fixtures

Unchanged in S1:

- `run_witness_narrow_build.sh`
- `container_narrow_build.sh`
- all template files
- `fixtures_lib.py`, fixture generators, existing fixture trees
- existing Phase 2A–3G test modules
- `AUTHORITATIVE_OUTCOME_CONTRACT.json`
- `INTEGRATED_BLOCKERS.md`, `INTEGRATED_REMEDIATION_LIST.md`
- `WITNESS_REQUIREMENTS.md`, `WITNESS_RUNBOOK.md`
- historical Phase 0–3G notes
- `CLAIM_REGISTER.md` / broad public-status files

## Deferred work

### S2

Runtime writer/template alignment to register target schemas (annotated-tag
identity fields, preliminary DEVIATIONS extensions, early-failure
`NOT_APPLICABLE` variants, related container-stage truths).

### S3

Final manifest cryptographic closure, evidence-completeness transition
machinery, new fixture families, full Phase 2A–3G regression set, broader docs.

## Non-claims / blocker status

- No blocker is CLOSED
- RC4 remains NOT READY
- rc5 tag does not exist
- No Independent Witness reproduction or PASS
- C-014 remains NOT_STARTED
- No real Docker, Cargo, compiler, product, network, production Witness, manual
  Witness, or Independent Witness execution occurred during S1 tests
