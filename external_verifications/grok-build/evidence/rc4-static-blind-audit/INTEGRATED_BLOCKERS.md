# RC4 static blind audit — integrated blockers

Consolidated list of every material blocker identified across Batches 1–4 of the RC4 static blind audit of tag `grok-build-witness-v1.0.0-rc4` (commit `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`, tree `071c4c1f4ed1b3e3a9164709c79ea9f5235ec2e9`). Extracted from `RC4_BATCH_4_FINAL_INTEGRATED.md` Blockers 5.1–5.40. Static owner-side review only; no execution performed. All 40 items below are material blockers to a READY verdict. **None are closed.** Status of every blocker: **OPEN**.

Stable ID mapping: Blocker 5.N → RC4B-00N (zero-padded to three digits).

---

## RC4B-001 — Fixed rc4 still describes itself as pending

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-001` |
| Original Blocker | Blocker 5.1 |
| Originating Batch/finding | Batch 1, Blocker 1 |
| Classification | BLOCKED |
| Exact paths | `README.md`; `external_verifications/grok-build/README.md`; `external_verifications/grok-build/VERDICT.md`; `external_verifications/grok-build/witness-package/README.md`; `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md`; `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`; `external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md` |
| Heading/function/field/test | current status banners and release-status sections |
| Evidence | wording still says rc4 is under preparation, pending commit/tag, or not yet published |
| Readiness-policy consequence | the fixed package is internally inconsistent and cannot truthfully describe its own release state |
| Mandatory correction | replace prospective wording with time-stable text identifying the already-fixed tag and commit while keeping readiness unresolved |
| Status | OPEN (not closed) |

## RC4B-002 — Closure statements contradict current content

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-002` |
| Original Blocker | Blocker 5.2 |
| Originating Batch/finding | Batch 1, Blockers 2 and 12 |
| Classification | BLOCKED |
| Exact paths | `external_verifications/grok-build/RESULTS.md`; `external_verifications/grok-build/CLAIM_REGISTER.md`; `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md`; `external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md` |
| Heading/function/field/test | rc4 remediation/change-log/status summaries |
| Evidence | statements say pending wording or related defects were closed while contradictory text and untested paths remain |
| Readiness-policy consequence | public audit records overstate remediation |
| Mandatory correction | change each claim to the exact narrow remediation actually implemented and leave unresolved controls open |
| Status | OPEN (not closed) |

## RC4B-003 — rc4 is not recorded as the already-published immutable release

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-003` |
| Original Blocker | Blocker 5.3 |
| Originating Batch/finding | Batch 1, Blocker 3 |
| Classification | BLOCKED |
| Exact paths | `external_verifications/grok-build/witness-package/README.md`; `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md`; `external_verifications/grok-build/README.md`; `external_verifications/grok-build/WITNESS_HANDOFF.md` |
| Heading/function/field/test | immutable release history |
| Evidence | rc1–rc3 history is represented, but rc4 remains prospective |
| Readiness-policy consequence | release history and current identity disagree |
| Mandatory correction | append the rc4 tag, commit, and fixed-under-audit status without claiming readiness |
| Status | OPEN (not closed) |

## RC4B-004 — Docker metadata is invoked before identity closure

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-004` |
| Original Blocker | Blocker 5.4 |
| Originating Batch/finding | Batch 1, Blocker 4 |
| Classification | BLOCKED |
| Exact paths | `scripts/run_witness_narrow_build.sh` |
| Heading/function/field/test | `record_host_environment` |
| Evidence | docker version and docker context show precede package/source/lock identity completion |
| Readiness-policy consequence | violates the package’s literal no-Docker-before-identity contract |
| Mandatory correction | move all Docker CLI calls after package, source, and lock checks, or formally narrow the policy; moving them is preferred |
| Status | OPEN (not closed) |

## RC4B-005 — Raw annotated-tag type is not enforced

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-005` |
| Original Blocker | Blocker 5.5 |
| Originating Batch/finding | Batch 1, Blocker 5 |
| Classification | BLOCKED |
| Exact paths | host tag-resolution block |
| Heading/function/field/test | tag resolution (`refs/tags/<tag>^{commit}`) |
| Evidence | `refs/tags/<tag>^{commit}` proves commit resolution but accepts a lightweight tag |
| Readiness-policy consequence | annotated-tag authority is asserted but not enforced |
| Mandatory correction | require `git cat-file -t refs/tags/<tag>` to equal `tag`, record it, and test lightweight-tag rejection |
| Status | OPEN (not closed) |

## RC4B-006 — DEVIATIONS.txt generator is incompatible with template and validator

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-006` |
| Original Blocker | Blocker 5.6 |
| Originating Batch/finding | Batch 1, Blocker 6; Batch 3 deviation blockers 38 and 45 |
| Classification | BLOCKED |
| Exact paths | host deviation writer; `templates/DEVIATIONS.txt`; validator deviation parser; tests |
| Heading/function/field/test | deviation writer / template / validator / tests |
| Evidence | host emits a summary/changed-field structure; the normative model expects indexed records |
| Readiness-policy consequence | noncanonical evidence requires manual reconstruction and cannot be relied on for verdict enforcement |
| Mandatory correction | make the real generator emit the exact indexed schema directly |
| Status | OPEN (not closed) |

## RC4B-007 — Rust/DotSlash deviations receive insufficient severity

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-007` |
| Original Blocker | Blocker 5.7 |
| Originating Batch/finding | Batch 1, Blocker 7 |
| Classification | BLOCKED |
| Exact paths | host ceiling logic, requirements, classification policy, validator |
| Heading/function/field/test | Rust/DotSlash version-deviation severity / ceiling |
| Evidence | accepted version deviations require noncanonical mode but are not uniformly FAIL-level |
| Readiness-policy consequence | materially altered toolchain identity can retain an unsupported ceiling |
| Mandatory correction | prohibit those overrides or cap them at FAIL in both host and validator |
| Status | OPEN (not closed) |

## RC4B-008 — Evidence directory is not atomically fresh

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-008` |
| Original Blocker | Blocker 5.8 |
| Originating Batch/finding | Batch 1, Blockers 8 and 9 |
| Classification | BLOCKED |
| Exact paths | host evidence initialization |
| Heading/function/field/test | evidence-directory creation |
| Evidence | `mkdir -p` permits reuse and merging |
| Readiness-policy consequence | prior and current evidence can mix |
| Mandatory correction | atomically create an absent directory; reject any collision before writing |
| Status | OPEN (not closed) |

## RC4B-009 — Behavioral host-safety and actual noncanonical-output tests are absent

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-009` |
| Original Blocker | Blocker 5.9 |
| Originating Batch/finding | Batch 1, Blockers 10 and 11 |
| Classification | BLOCKED |
| Exact paths | host tests and validator tests |
| Heading/function/field/test | host-safety and noncanonical-output behavioral tests |
| Evidence | source-text assertions and synthetic fixtures do not prove destructive-operation safety or actual writer output |
| Readiness-policy consequence | material host controls are not regression-proven |
| Mandatory correction | use temporary repositories and mocked external tools to behaviorally test every host safety and noncanonical branch |
| Status | OPEN (not closed) |

## RC4B-010 — Source read-only protection is bypassed through /work

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-010` |
| Original Blocker | Blocker 5.10 |
| Originating Batch/finding | Batch 2, Blocker 1 |
| Classification | BLOCKED |
| Exact paths | host Docker invocation |
| Heading/function/field/test | Docker mounts `${SRC_DIR}:/src:ro` and `${WORK_ROOT}:/work:rw` while `${SRC_DIR}` is beneath `${WORK_ROOT}` |
| Evidence | `${SRC_DIR}:/src:ro` and `${WORK_ROOT}:/work:rw` while `${SRC_DIR}` is beneath `${WORK_ROOT}` |
| Readiness-policy consequence | `/work/grok-build` exposes the same source read-write, so source immutability is not preventive |
| Mandatory correction | keep source outside all writable mounts or mount only narrow writable subdirectories |
| Status | OPEN (not closed) |

## RC4B-011 — Unexpected container failures do not finalize all mandatory evidence

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-011` |
| Original Blocker | Blocker 5.11 |
| Originating Batch/finding | Batch 2, Blocker 2 |
| Classification | BLOCKED |
| Exact paths | `container_narrow_build.sh` |
| Heading/function/field/test | `fail_build_not_started`, `fail_infrastructure` |
| Evidence | mandatory files can remain preliminary or `NOT_REACHED` |
| Readiness-policy consequence | some failure submissions require reconstruction and are not complete |
| Mandatory correction | one schema-aware finalizer must finish every mandatory automated file on every exit |
| Status | OPEN (not closed) |

## RC4B-012 — Invalid/missing container outcome finalization is incomplete

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-012` |
| Original Blocker | Blocker 5.12 |
| Originating Batch/finding | Batch 2, Blocker 3 |
| Classification | BLOCKED |
| Exact paths | host invalid-outcome branch |
| Heading/function/field/test | invalid/missing container outcome finalization |
| Evidence | only principal outcome files are rewritten before abort; full post-Docker integrity and evidence closure are skipped |
| Readiness-policy consequence | invalid outcome paths produce partial packages |
| Mandatory correction | route through a comprehensive post-Docker infrastructure finalizer |
| Status | OPEN (not closed) |

## RC4B-013 — Host success is not conditioned on validator or full structural validity

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-013` |
| Original Blocker | Blocker 5.13 |
| Originating Batch/finding | Batch 2, Blocker 4 |
| Classification | BLOCKED |
| Exact paths | host final exit selection |
| Heading/function/field/test | host final exit selection |
| Evidence | host can return Docker zero after limited checks without full schema/manifest validation |
| Readiness-policy consequence | malformed but superficially successful evidence can accompany zero host exit |
| Mandatory correction | gate zero on a complete structural checker over finalized evidence |
| Status | OPEN (not closed) |

## RC4B-014 — Host validates only outcome=, not the full tuple

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-014` |
| Original Blocker | Blocker 5.14 |
| Originating Batch/finding | Batch 2, Blocker 5 |
| Classification | BLOCKED |
| Exact paths | host outcome parser |
| Heading/function/field/test | host outcome parser |
| Evidence | `cargo_started`, build status, Cargo exit, failure stage, timing, and status are not fully cross-validated |
| Readiness-policy consequence | a contradictory outcome package can be accepted by the orchestrator |
| Mandatory correction | parse and enforce the complete authoritative tuple |
| Status | OPEN (not closed) |

## RC4B-015 — POST_BUILD_INTEGRITY.txt can say status=OK when its gate fails

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-015` |
| Original Blocker | Blocker 5.15 |
| Originating Batch/finding | Batch 2, Blocker 6 |
| Classification | BLOCKED |
| Exact paths | host post-build writer |
| Heading/function/field/test | `POST_BUILD_INTEGRITY.txt` / `status` vs `post_build_integrity_ok` |
| Evidence | top-level `status=OK` is unconditional while `post_build_integrity_ok` may be `no` |
| Readiness-policy consequence | internally contradictory evidence |
| Mandatory correction | write `status=FAILED` whenever the full gate is false |
| Status | OPEN (not closed) |

## RC4B-016 — Post-build generator, template, and validator are not aligned

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-016` |
| Original Blocker | Blocker 5.16 |
| Originating Batch/finding | Batch 2, Blocker 7; Batch 3 schema blockers |
| Classification | BLOCKED |
| Exact paths | post-build writer, template, validator, tests |
| Heading/function/field/test | post-build generator / template / validator alignment |
| Evidence | load-bearing generated fields are absent from the exact normative schema |
| Readiness-policy consequence | successful-looking evidence may contain unvalidated integrity assertions |
| Mandatory correction | define one exact field set and reject all drift |
| Status | OPEN (not closed) |

## RC4B-017 — Validator does not explicitly require all four post-build conditions

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-017` |
| Original Blocker | Blocker 5.17 |
| Originating Batch/finding | Batch 2, Blocker 8 |
| Classification | BLOCKED |
| Exact paths | `check_post_build_integrity` |
| Heading/function/field/test | `check_post_build_integrity` |
| Evidence | all four required `yes` values are not independently and completely enforced |
| Readiness-policy consequence | PASS may survive a failed technical gate |
| Mandatory correction | require all four `yes` fields plus `post_build_integrity_ok=yes` and `status=OK` |
| Status | OPEN (not closed) |

## RC4B-018 — Behavioral tests do not prove end-to-end host/container outcome preservation

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-018` |
| Original Blocker | Blocker 5.18 |
| Originating Batch/finding | Batch 2, Blocker 9 |
| Classification | BLOCKED |
| Exact paths | tests and fixture builder |
| Heading/function/field/test | end-to-end host/container outcome preservation tests |
| Evidence | tests inspect source text or synthetic evidence instead of actual writers and host rewrites |
| Readiness-policy consequence | outcome authority and finalization can drift undetected |
| Mandatory correction | generator-backed behavioral outcome tests for all paths |
| Status | OPEN (not closed) |

## RC4B-019 — Global false-success impossibility is unsupported

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-019` |
| Original Blocker | Blocker 5.19 |
| Originating Batch/finding | Batch 2, Blocker 10 |
| Classification | BLOCKED |
| Exact paths | (umbrella; relationship stated without merging underlying blockers) |
| Heading/function/field/test | global false-success impossibility |
| Relationship | umbrella consequence of Blockers 5.10–5.18; preserved separately |
| Evidence | writable source alias, incomplete finalization, limited tuple validation, no validator-gated zero |
| Readiness-policy consequence | readiness policy expressly requires NOT READY |
| Mandatory correction | resolve all underlying false-success paths and test them behaviorally |
| Status | OPEN (not closed) |

## RC4B-020 — Auxiliary files may remain outside the manifest

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-020` |
| Original Blocker | Blocker 5.20 |
| Originating Batch/finding | Batch 3 Part 1, Blockers 1 and 2 |
| Classification | BLOCKED |
| Exact paths | manifest validator auxiliary exemption |
| Heading/function/field/test | manifest auxiliary exemption |
| Evidence | allowed auxiliary files can exist without entries |
| Readiness-policy consequence | submission is not cryptographically closed |
| Mandatory correction | require exactly one manifest entry for every regular file except the manifest itself |
| Status | OPEN (not closed) |

## RC4B-021 — Exact allowed-key schemas are not enforced

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-021` |
| Original Blocker | Blocker 5.21 |
| Originating Batch/finding | Batch 3 Part 1, Blockers 3 and 4 |
| Classification | BLOCKED |
| Exact paths | validator `FILE_REQUIRED_FIELDS` and `parse_kv` |
| Heading/function/field/test | `FILE_REQUIRED_FIELDS` / `parse_kv` |
| Evidence | minimum fields are enforced, but unknown and extra keys are accepted |
| Readiness-policy consequence | unvalidated assertions can coexist with a structural PASS |
| Mandatory correction | define exact per-file required/optional/conditional key sets and reject unknown keys |
| Status | OPEN (not closed) |

## RC4B-022 — Validator outcome inference violates fail-closed authority

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-022` |
| Original Blocker | Blocker 5.22 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 5 |
| Classification | BLOCKED |
| Exact paths | `determine_outcome` |
| Heading/function/field/test | `determine_outcome` |
| Evidence | missing or invalid outcome can be inferred from secondary fields |
| Readiness-policy consequence | exactly one explicit authoritative outcome is not fail-closed |
| Mandatory correction | remove all inference and require one explicit valid outcome |
| Status | OPEN (not closed) |

## RC4B-023 — Complete cross-file outcome tuple is absent

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-023` |
| Original Blocker | Blocker 5.23 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 6 |
| Classification | BLOCKED |
| Exact paths | build exit, timing, Docker exit, verdict, artifact/static, post-build files |
| Heading/function/field/test | cross-file outcome tuple |
| Relationship | overlaps Batch 2 host-parser weakness but applies package-wide |
| Evidence | only selected fields are cross-checked |
| Readiness-policy consequence | mutually inconsistent evidence may remain structurally accepted |
| Mandatory correction | define and enforce one complete outcome tuple across all outcome-bearing files |
| Status | OPEN (not closed) |

## RC4B-024 — NOT_REACHED placeholders can survive final submission

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-024` |
| Original Blocker | Blocker 5.24 |
| Originating Batch/finding | Batch 3 Part 1, Blockers 7 and 12 |
| Classification | BLOCKED |
| Exact paths | bootstrap, build command, build environment schemas |
| Heading/function/field/test | `NOT_REACHED` placeholder handling |
| Evidence | validator skips normal schema for permitted placeholders on negative outcomes |
| Readiness-policy consequence | a preliminary initializer state can be accepted as final evidence |
| Mandatory correction | replace with explicit final `NOT_APPLICABLE` schemas |
| Status | OPEN (not closed) |

## RC4B-025 — No machine-wide current-run provenance

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-025` |
| Original Blocker | Blocker 5.25 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 8 |
| Classification | BLOCKED |
| Exact paths | all templates, manual forms, validator |
| Heading/function/field/test | machine-wide current-run provenance / run ID |
| Evidence | one run ID is not required across every file |
| Readiness-policy consequence | mixed-run packages and copied forms can pass selected checks |
| Mandatory correction | require one immutable run ID across all structured and manual evidence, with raw files bound through manifest metadata |
| Status | OPEN (not closed) |

## RC4B-026 — Host inventory checks only top-level regular files

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-026` |
| Original Blocker | Blocker 5.26 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 9 |
| Classification | BLOCKED |
| Exact paths | host inventory function |
| Heading/function/field/test | host inventory function |
| Evidence | nested objects, directories, symlinks, and special objects are not comprehensively checked by the host |
| Readiness-policy consequence | host zero can precede discovery of an invalid filesystem inventory |
| Mandatory correction | recursively reject all unauthorized object types and paths |
| Status | OPEN (not closed) |

## RC4B-027 — Validator output can contaminate an allowed auxiliary filename

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-027` |
| Original Blocker | Blocker 5.27 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 10 |
| Classification | BLOCKED |
| Exact paths | (validator output redirection / auxiliary exemption path) |
| Heading/function/field/test | validator output vs allowed auxiliary filenames |
| Evidence | caller-controlled redirection into an exempt allowed filename may remain unhashed |
| Readiness-policy consequence | final evidence can be contaminated without complete manifest closure |
| Mandatory correction | eliminate manifest exemption and exact-schema validate auxiliary files |
| Status | OPEN (not closed) |

## RC4B-028 — evidence_inventory_complete lifecycle is circular

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-028` |
| Original Blocker | Blocker 5.28 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 11 |
| Classification | BLOCKED |
| Exact paths | manifest policy, runbook, post-build template |
| Heading/function/field/test | `evidence_inventory_complete` lifecycle |
| Evidence | field is said to become `yes` only after manifest validation, but changing it after validation invalidates the manifest |
| Readiness-policy consequence | no coherent canonical finalization sequence exists |
| Mandatory correction | set the field before final manifest generation, then validate once, with no post-validation edit |
| Status | OPEN (not closed) |

## RC4B-029 — Some failure packages require manual reconstruction

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-029` |
| Original Blocker | Blocker 5.29 |
| Originating Batch/finding | Batch 3 Part 1, Blocker 13 |
| Classification | BLOCKED |
| Exact paths | (failure finalizers / placeholder schemas) |
| Heading/function/field/test | failure-package generator completeness |
| Relationship | direct consequence of incomplete finalizers and placeholder schemas; preserved separately |
| Evidence | Witness may need to reinterpret or rewrite load-bearing automated files |
| Readiness-policy consequence | package fails the stated direct-use threshold |
| Mandatory correction | all supported outcomes must be generator-complete |
| Status | OPEN (not closed) |

## RC4B-030 — WITNESS_STATEMENT.md is not bound to the run or outcome

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-030` |
| Original Blocker | Blocker 5.30 |
| Originating Batch/finding | Batch 3 Part 2, Blocker 1 |
| Classification | BLOCKED |
| Exact paths | statement template and validator |
| Heading/function/field/test | `WITNESS_STATEMENT.md` run/outcome binding |
| Evidence | no run ID, package tag, commits, or outcome |
| Readiness-policy consequence | statement can be copied from another run |
| Mandatory correction | add and cross-check all run and outcome identities |
| Status | OPEN (not closed) |

## RC4B-031 — Manual statement schema is internally incomplete

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-031` |
| Original Blocker | Blocker 5.31 |
| Originating Batch/finding | Batch 3 Part 2, Blocker 2 |
| Classification | BLOCKED |
| Exact paths | statement template / validator required fields |
| Heading/function/field/test | fields: `ai_assistance_detail`, `upstream_product_commands_not_run` |
| Evidence | template and semantic checks are not fully reflected in required fields |
| Readiness-policy consequence | exact manual-form schema closure is absent |
| Mandatory correction | include every normative field in exact allowed/required schema rules |
| Status | OPEN (not closed) |

## RC4B-032 — Verdict run ID, tag, and Weaver Forge commit are not fully cross-checked

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-032` |
| Original Blocker | Blocker 5.32 |
| Originating Batch/finding | Batch 3 Part 2, Blockers 3–5 and 27 |
| Classification | BLOCKED |
| Exact paths | verdict template and validator |
| Heading/function/field/test | verdict run ID / tag / Weaver Forge commit cross-checks |
| Evidence | run ID is format-only; tag is grammar-only; commit is hex-only |
| Readiness-policy consequence | verdict can refer to another run or package |
| Mandatory correction | exact equality against package/source identity files |
| Status | OPEN (not closed) |

## RC4B-033 — New submissions are not forced to start with intake pending

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-033` |
| Original Blocker | Blocker 5.33 |
| Originating Batch/finding | Batch 3 Part 2, Blockers 6 and 26 |
| Classification | BLOCKED |
| Exact paths | validator intake values |
| Heading/function/field/test | validator intake values / initial-submission mode |
| Evidence | accepted/rejected/superseded values are structurally accepted in an initial submission |
| Readiness-policy consequence | Witness can predeclare maintainer disposition |
| Mandatory correction | separate initial-submission mode from later intake metadata |
| Status | OPEN (not closed) |

## RC4B-034 — Machine ceiling ignores deviations and canonical state

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-034` |
| Original Blocker | Blocker 5.34 |
| Originating Batch/finding | Batch 3 Part 2, Blockers 7–12 |
| Classification | BLOCKED |
| Exact paths | `compute_verdict_ceiling` |
| Heading/function/field/test | `compute_verdict_ceiling` |
| Evidence | deviation state and `canonical_run` are not complete ceiling inputs |
| Readiness-policy consequence | unsupported PASS eligibility |
| Mandatory correction | machine-recompute the full normative PASS checklist |
| Status | OPEN (not closed) |

## RC4B-035 — NONMATERIAL_DISCLOSED can retain PASS

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-035` |
| Original Blocker | Blocker 5.35 |
| Originating Batch/finding | Batch 3 Part 2, Blocker 10 |
| Classification | BLOCKED |
| Exact paths | deviation severity validation |
| Heading/function/field/test | deviation severity validation / `NONMATERIAL_DISCLOSED` |
| Evidence | policy says maximum PARTIAL; validator forbids PASS only for stronger categories |
| Readiness-policy consequence | policy/validator disagreement |
| Mandatory correction | enforce PARTIAL maximum |
| Status | OPEN (not closed) |

## RC4B-036 — Deviation records are not exact, numeric, contiguous, or complete

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-036` |
| Original Blocker | Blocker 5.36 |
| Originating Batch/finding | Batch 3 Part 2, Blockers 13–17 |
| Classification | BLOCKED |
| Exact paths | deviation records / validator aggregation |
| Heading/function/field/test | deviation record indices / orphans / ceiling aggregation |
| Evidence | nonnumeric and sparse indices are accepted; orphan fields may be ignored; impacts are self-declared; ceilings are not aggregated |
| Readiness-policy consequence | deviation-bearing evidence can be incomplete or misclassified |
| Mandatory correction | require count-backed numeric indices 1..n, full records, no orphans, and automatic strictest-ceiling aggregation |
| Status | OPEN (not closed) |

## RC4B-037 — Critical redactions are incompletely prohibited or bound

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-037` |
| Original Blocker | Blocker 5.37 |
| Originating Batch/finding | Batch 3 Part 2, Blockers 19–22 |
| Classification | BLOCKED |
| Exact paths | redaction template and validator |
| Heading/function/field/test | redaction prohibition / binding |
| Evidence | command, tag, URL, platform, architecture, and broad identity categories are incomplete; declarations are free-text and not bound to exact key/marker |
| Readiness-policy consequence | structural validity may coexist with concealed critical evidence |
| Mandatory correction | bind redactions to exact file/key/original-value hash/replacement marker and prohibit all reproducibility-critical categories |
| Status | OPEN (not closed) |

## RC4B-038 — Correction ledger is not machine-enforced

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-038` |
| Original Blocker | Blocker 5.38 |
| Originating Batch/finding | Batch 3 Part 2, Blocker 23 |
| Classification | BLOCKED |
| Exact paths | `CORRECTION_LEDGER.md` |
| Heading/function/field/test | `CORRECTION_LEDGER.md` machine enforcement |
| Evidence | append-only, original hash, correction hash, and supersession semantics are documentation-only |
| Readiness-policy consequence | immutable correction history is not structurally guaranteed |
| Mandatory correction | define separately validated correction packages or machine-readable ledger records |
| Status | OPEN (not closed) |

## RC4B-039 — Maintainer intake mutates validated Witness evidence

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-039` |
| Original Blocker | Blocker 5.39 |
| Originating Batch/finding | Batch 3 Part 2, Blockers 24–25 |
| Classification | BLOCKED |
| Exact paths | intake policy, verdict form, correction ledger |
| Heading/function/field/test | maintainer intake / `maintainer_intake_verdict` mutation |
| Evidence | policy says update `maintainer_intake_verdict` in the hashed verdict file after validation |
| Readiness-policy consequence | original evidence and manifest become inconsistent |
| Mandatory correction | move maintainer intake to separate append-only metadata outside the immutable Witness package |
| Status | OPEN (not closed) |

## RC4B-040 — Generator-backed full-submission tests are absent

| Field | Value |
|-------|-------|
| Stable ID | `RC4B-040` |
| Original Blocker | Blocker 5.40 |
| Originating Batch/finding | Batch 3 Part 2, Blocker 28; Batch 3 consolidation test blockers |
| Classification | BLOCKED |
| Exact paths | fixture builder and validator tests |
| Heading/function/field/test | generator-backed full-submission tests |
| Evidence | no actual manifest-complete package generated through real writers for all six supported result states |
| Readiness-policy consequence | central package contract is unproved |
| Mandatory correction | generator-backed submission tests for every supported outcome, including mixed-run rejection |
| Status | OPEN (not closed) |

---

## Summary

| Field | Value |
|-------|-------|
| Total material blockers | 40 (`RC4B-001`–`RC4B-040`) |
| Contiguous unique IDs | Yes |
| Every Blocker 5.1–5.40 appears exactly once | Yes |
| Closed blockers | 0 |
| Final static disposition | **NOT READY** |
| C-014 status | `NOT_STARTED` (unaffected by this audit) |
| Remediation mapping | See `INTEGRATED_REMEDIATION_LIST.md` |
| Source | `RC4_BATCH_4_FINAL_INTEGRATED.md` section 5 |
