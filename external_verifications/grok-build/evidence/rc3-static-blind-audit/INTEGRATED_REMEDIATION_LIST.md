# RC3 static blind audit — integrated remediation list

Maps every material blocker recorded in `INTEGRATED_BLOCKERS.md` to a C2E-5 remediation step (steps 4–33; steps 1–3 are the prior tag-creation, remote-publish, and precheck steps already reflected in `evidence/rc3-integrated-static-blind-audit-remediation/PRECHECK.txt`). Steps 34–35 are the documentation-recording steps for this audit's own verdict and status. This list is a remediation **plan**; no code, script, or documentation remediation has been executed against the 28 blockers as part of producing this audit preservation record — only steps 32–35 (cross-checking, limitations authorship, and recording this audit's own verdict/status) are complete. Remediation execution status: **IN_PROGRESS** under C2E-5 — this phase prepares `rc4`; it does not claim READY.

| Step | Blocker(s) | Remediation action | Status |
|------|------------|---------------------|--------|
| 4 | RC3B-001 | Prepare draft `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4` successor identity constants in a clearly labeled, not-yet-cut staging location; do not create the `rc4` tag itself under this phase | `NOT_STARTED` |
| 5 | RC3B-002 | Sweep normative docs for tag-absence/pending-style wording and replace with phrasing accurate for a published, immutable snapshot | `NOT_STARTED` |
| 6 | RC3B-003 | Make Weaver Forge URL mismatch a hard FAIL in both the host script and the written classification precedence, cross-referenced so the two cannot diverge | `NOT_STARTED` |
| 7 | RC3B-004 | Update `RESULTS.md` / `CLAIM_REGISTER.md` and public status documents to record this audit's intake and its `NOT READY` outcome | `NOT_STARTED` |
| 8 | RC3B-005 | Add an explicit `grok_build_detached_head=yes\|no` evidence field, derived consistently from `git symbolic-ref -q HEAD` exit status, written after every detached checkout | `NOT_STARTED` |
| 9 | RC3B-006 | Add `status=OK\|FAILED\|NOT_REACHED` and `failure_stage` to `IMAGE_IDENTITY.txt`; complete inspect command/exit fields; gate `status=OK` on all identity sub-checks passing | `NOT_STARTED` |
| 10 | RC3B-007 | Finalize all mandatory automated evidence files to `outcome=INFRASTRUCTURE_FAILURE` before any pre-Docker abort path exits | `NOT_STARTED` |
| 11 | RC3B-008 | Make the container-written `BUILD_EXIT_CODE.txt` outcome strictly authoritative on the host once Docker has started; remove host-side outcome re-derivation | `NOT_STARTED` |
| 12 | RC3B-009 | Add an automated cross-file outcome-consistency check across the six named evidence files before a submission is treated as complete | `NOT_STARTED` |
| 13 | RC3B-010 | Add an lstat/readlink-before-delete policy to managed child/scratch cleanup, rejecting symlinked entries | `NOT_STARTED` |
| 14 | RC3B-011 | Add a host safety unit test suite covering constants/overrides, `WORK_ROOT` guards, dirty-clone detection, lock/image failure handling, and outcome preservation | `NOT_STARTED` |
| 15 | RC3B-012 | Require and validate `upstream_product_commands_not_run` in `ENVIRONMENT.txt`, the Witness statement, and `WITNESS_VERDICT.md` | `NOT_STARTED` |
| 16 | RC3B-013 | Reconcile `ENVIRONMENT.txt` required keys across generator/template/validator into one documented source of truth; add all listed missing keys | `NOT_STARTED` |
| 17 | RC3B-014 | Disambiguate `CLEAN_TARGET_PROOF.txt` `observed_entry_count` into distinct host/container-scoped fields, each with its own UTC timestamp | `NOT_STARTED` |
| 18 | RC3B-015 | Reconcile `BUILD_ENVIRONMENT.txt` key casing; add `workdir`, `bootstrap_cargo_target_dir`, `grok_build_commit`, `expected_cargo_lock_sha256`, `canonical_build_command`, `mounts` | `NOT_STARTED` |
| 19 | RC3B-016 | Extend `BUILD_TIMING.txt` with `docker_elapsed_seconds`, `cargo_started`, `cargo_exit_code`, `docker_exit_code`, `failure_stage`, `status` | `NOT_STARTED` |
| 20 | RC3B-017 | Restructure `STATIC_ARTIFACT_INSPECTION.txt` with per-tool `*_command`/`*_output`/`*_exit_code` fields and a defined multiline-output encoding rule | `NOT_STARTED` |
| 21 | RC3B-018 | Specify and enforce the full static-inspection-failure contract (outcome preserved, `inspection_complete=no`, `status=FAILED`, dedicated nonzero exit, `PARTIAL` ceiling, `PASS` prohibited) | `NOT_STARTED` |
| 22 | RC3B-019 | Add the missing `POST_BUILD_INTEGRITY.txt` fields; require all four affirmative integrity fields at the host gate; explicitly normalize blank porcelain output before `yes`/`no` classification | `NOT_STARTED` |
| 23 | RC3B-020 | Require `evidence_inventory_complete=yes` only after automated, manual, and manifest checks are all independently confirmed complete; relocate `BOOTSTRAP_PROTOC_VERSION.txt` out of the required-evidence path | `NOT_STARTED` |
| 24 | RC3B-021 | Define and enforce a closed-inventory auxiliary-file allow-list, checked independently of whether a file happens to be listed in the manifest | `NOT_STARTED` |
| 25 | RC3B-022 | Make `parse_kv` reject files containing duplicate keys instead of resolving them last-value-wins | `NOT_STARTED` |
| 26 | RC3B-023 | Require `WITNESS_VERDICT.md` `outcome=` to cross-check against the fixed automated outcome vocabulary before acceptance | `NOT_STARTED` |
| 27 | RC3B-024 | Implement a single deterministic verdict-ceiling function consumed identically by the script and by `CLASSIFICATION.md`, eliminating independent computation | `NOT_STARTED` |
| 28 | RC3B-025 | Expand the never-redact list to include `outcome`, `build_status`, `failure_stage`, proposed verdict, intake verdict, `canonical_run`, and `verdict_ceiling`; add marker-to-ledger reconciliation for every `[REDACTED:` instance | `NOT_STARTED` |
| 29 | RC3B-026 | Align correction-ledger intake states with `MAINTAINER_INTAKE_POLICY.md`; explicitly resolve `SUPERSEDED` inclusion/exclusion for classification purposes | `NOT_STARTED` |
| 30 | RC3B-027 | Add generator/schema contract tests comparing shell generator key sets to templates/`FILE_REQUIRED_FIELDS`; add golden fixtures for every outcome/failure-mode state | `NOT_STARTED` |
| 31 | RC3B-028 | Add the enumerated manifest/unit test coverage: one-space separator grammar, duplicate-key rejection, auxiliary-file allow-list enforcement, post-lock mismatch detection, verdict-ceiling computation, unlogged-redaction detection, `upstream_product_commands_not_run` validation | `NOT_STARTED` |
| 32 | All (RC3B-001–RC3B-028) | Cross-check Batch 1–4 findings for internal consistency and consolidate into `INTEGRATED_BLOCKERS.md` | `COMPLETE` |
| 33 | All (RC3B-001–RC3B-028) | Author `INTEGRATED_LIMITATIONS.md` documenting the audit method's own limitations | `COMPLETE` |
| 34 (docs) | N/A (verdict recording) | Record `FINAL_AUDIT_VERDICT.md` as **NOT READY**, explicitly distinct from C-014, and record the requirement for a successor `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4` package after remediation and re-audit | `COMPLETE` |
| 35 (docs) | N/A (status/intake recording) | Record `AUDIT_STATUS.md` as `COMPLETE`, package readiness `NOT READY`, and C-014 `NOT_STARTED` | `COMPLETE` |

## Status summary

| Status | Count | Steps |
|--------|------:|-------|
| `COMPLETE` (this audit's own documentation) | 4 | 32–35 |
| `NOT_STARTED` (actual code/script/process remediation) | 28 | 4–31 |

Overall remediation execution status for steps 4–31 is **NOT_STARTED**; the phase-level status recorded for C2E-5 as a whole is **IN_PROGRESS**, reflecting that this audit-and-planning work (steps 4–35 as authored here) is complete while the 28 underlying code/script/documentation remediation actions remain open. No script, code, or configuration remediation has been performed against any of the 28 blockers. Steps 4–31 remain open work for a future phase and require the same execution restrictions (no Docker/Cargo/witness-script execution, no commit/push/tag) to be lifted or separately authorized before they can proceed. Completion of steps 4–31, followed by cutting a distinct `1.0.0-rc4` tag and a fresh audit or Independent Witness reproduction against it, is required before a READY verdict can be considered; see `FINAL_AUDIT_VERDICT.md`.
