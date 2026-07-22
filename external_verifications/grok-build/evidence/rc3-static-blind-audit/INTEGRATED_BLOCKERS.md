# RC3 static blind audit — integrated blockers

Consolidated list of every material blocker identified across Batches 1–4 of the RC3 static blind audit of tag `grok-build-witness-v1.0.0-rc3` (`77221a224bbd6194cfafb81f6ecb58c800e5bc13`). Static review only; no execution performed. All 28 items below are material blockers to a READY verdict.

## Batch 1 — Release identity, wording, public status

| ID | Blocker |
|----|---------|
| RC3B-001 | Package identity still `1.0.0-rc3` / tag `grok-build-witness-v1.0.0-rc3`; successor `rc4` identity not prepared |
| RC3B-002 | Normative docs may retain time-unstable tag-absence / pending wording patterns inappropriate for post-publication snapshots |
| RC3B-003 | Weaver Forge URL mismatch not treated as material FAIL consistently across script and classification |
| RC3B-004 | Public status / `CLAIM_REGISTER` still describe rc3 as current candidate without recording this audit intake |
| RC3B-005 | Grok Build detached HEAD uses only symbolic-ref check inconsistently; missing explicit `grok_build_detached_head=yes\|no` evidence field after detached checkout |

## Batch 2 — Host orchestrator: image, pre-Docker failure, outcomes

| ID | Blocker |
|----|---------|
| RC3B-006 | `IMAGE_IDENTITY.txt` lacks `status=OK\|FAILED\|NOT_REACHED` and `failure_stage`; incomplete inspect command/exit fields; `status=OK` not gated on all identity checks |
| RC3B-007 | Pre-Docker infrastructure failures (pull/inspect/digest/OS/arch/platform) do not finalize all mandatory automated evidence with `INFRASTRUCTURE_FAILURE` before abort; may leave `NOT_REACHED` as final |
| RC3B-008 | Host may reconstruct ordinary outcomes from `cargo_started`/artifact/docker exit alone; `BUILD_EXIT_CODE.txt` container outcome not strictly authoritative after Docker begins |
| RC3B-009 | Outcome consistency not machine-enforced across `BUILD_EXIT_CODE` / `BUILD_TIMING` / `DOCKER_EXIT_CODE` / `ARTIFACT_IDENTITY` / `STATIC_ARTIFACT_INSPECTION` / `WITNESS_VERDICT` |
| RC3B-010 | Managed child `rm -rf` may follow symlinks; no lstat/readlink-before-delete policy |
| RC3B-011 | Host safety unit tests incomplete for constants, overrides, `WORK_ROOT`, dirty clones, lock/image failures, outcome preservation |
| RC3B-012 | `upstream_product_commands_not_run` not required/validated in `ENVIRONMENT` / `WITNESS_STATEMENT` / `WITNESS_VERDICT` |

## Batch 3 — Container evidence schemas

| ID | Blocker |
|----|---------|
| RC3B-013 | `ENVIRONMENT.txt` generator/template/validator key drift; missing required keys (`status`, `outcome`, `host_kernel`, `host_cpu`, `docker_context`, `wsl2_indicator`, `ai_assistance_*`, `human_review_completed`, `upstream_product_commands_not_run`, etc.) |
| RC3B-014 | `CLEAN_TARGET_PROOF.txt` uses ambiguous/duplicate `observed_entry_count`; missing distinct host/container path and UTC fields |
| RC3B-015 | `BUILD_ENVIRONMENT.txt` key names drift (`HOME` vs `home`, etc.); missing `workdir`, `bootstrap_cargo_target_dir`, `grok_build_commit`, `expected_cargo_lock_sha256`, `canonical_build_command`, `mounts` |
| RC3B-016 | `BUILD_TIMING.txt` uses generic `utc_start`/`utc_end`; missing `docker_elapsed_seconds`, `cargo_started`, `cargo_exit_code`, `docker_exit_code`, `failure_stage`, `status` |
| RC3B-017 | `STATIC_ARTIFACT_INSPECTION.txt` uses repeated generic `command=`/`exit_code=`; missing per-tool `*_command`/`*_output`/`*_exit_code`; multiline encoding undefined |
| RC3B-018 | Static inspection command failure does not keep `outcome=CARGO_SUCCEEDED_ARTIFACT_PRESENT` with `inspection_complete=no`, `status=FAILED`, dedicated nonzero exit, `PARTIAL` ceiling, `PASS` prohibited |
| RC3B-019 | `POST_BUILD_INTEGRITY.txt` missing `status`, `outcome`, `source_head_unchanged`, `cargo_lock_unchanged`, `cargo_lock_post_matches_expected`, `failure_stage`; host gate does not require all four `yes` fields; blank porcelain may pollute `yes`/`no` |
| RC3B-020 | `evidence_inventory_complete` may be marked `yes` before automated+manual+manifest complete; `BOOTSTRAP_PROTOC_VERSION.txt` still written under `EVIDENCE_DIR` |

## Batch 4 — Validator, redaction, tests, policy

| ID | Blocker |
|----|---------|
| RC3B-021 | Auxiliary-file policy open/ambiguous; undeclared auxiliaries (`IMAGE_PULL_*`, `CARGO_LOCK_INTEGRITY`, etc.) not closed-inventory enumerated; undeclared files may pass if listed in manifest |
| RC3B-022 | `parse_kv` last-value-wins on duplicate keys; no rejection of same-key duplicates |
| RC3B-023 | `WITNESS_VERDICT.md` does not require/cross-check `outcome=` against automated outcome vocabulary |
| RC3B-024 | Verdict ceiling not machine-computed from outcome+identity+deviation+inspection+product/ldd/independence; script ceiling may diverge from validator/`CLASSIFICATION` |
| RC3B-025 | Redaction never-redact list incomplete (`outcome`, `build_status`, `failure_stage`, proposed verdict, intake verdict, `canonical_run`, `verdict_ceiling`); marker reconciliation for `[REDACTED:` missing |
| RC3B-026 | Correction-ledger intake states not aligned with `MAINTAINER_INTAKE_POLICY` (incl. `SUPERSEDED` include/exclude) |
| RC3B-027 | No generator/schema contract tests comparing shell generator key sets to templates/`FILE_REQUIRED_FIELDS`; golden fixtures missing for all outcomes/failure modes |
| RC3B-028 | Manifest/unit tests incomplete (one-space separator, duplicate keys, aux policy, post-lock mismatch, verdict ceilings, unlogged redaction, `upstream_product_commands_not_run`) |

## Summary

| Field | Value |
|-------|-------|
| Total material blockers | 28 (RC3B-001–RC3B-028) |
| Batch 1 count | 5 |
| Batch 2 count | 7 |
| Batch 3 count | 8 |
| Batch 4 count | 8 |
| Remediation mapping | See `INTEGRATED_REMEDIATION_LIST.md` (C2E-5 steps 4–33, docs steps 34–35) |
| C-014 status | `NOT_STARTED` (unaffected by this audit) |
| Verdict | **NOT READY** |
