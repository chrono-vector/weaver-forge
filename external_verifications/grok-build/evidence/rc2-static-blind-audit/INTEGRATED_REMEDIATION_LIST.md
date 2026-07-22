# RC2 static blind audit — integrated remediation list

Maps every material blocker recorded in `INTEGRATED_BLOCKERS.md` to a C2E-4 remediation step (steps 3–33; steps 1–2 are the prior tag-creation and remote-publish steps already reflected in `evidence/rc2-integrated-blind-audit-remediation/PRECHECK.txt`). This list is a remediation **plan**; no code, script, or documentation remediation has been executed as part of producing this audit preservation record — only steps 30–33 (compiling and recording this audit itself) are complete.

| Step | Blocker(s) | Remediation action | Status |
|------|------------|---------------------|--------|
| 3 | RB-001 | Freeze `WEAVER_FORGE_URL`/`TAG`/`COMMIT`, `GROK_BUILD_*`, and `RUST_IMAGE` as canonical constants; require an explicit, disclosed override flag instead of silent environment acceptance | `NOT_STARTED` |
| 4 | RB-002 | Correct public status/readiness files to remove stale rc1/rc2 "current package" wording and point unambiguously at the current fixed tag | `NOT_STARTED` |
| 5 | RB-003 | Author and adopt a post-tag finalization checklist (peel verification, status-doc update, evidence freeze, precheck re-run) required before any readiness claim | `NOT_STARTED` |
| 6 | RB-004 | Define an explicit, self-declaring "noncanonical" execution mode with a mandatory disclosure banner in resulting evidence | `NOT_STARTED` |
| 7 | RB-005 | Add an allow-list validator for `WITNESS_ID` rejecting path separators, `..`, whitespace, and empty values | `NOT_STARTED` |
| 8 | RB-006 | Add `WORK_ROOT` guard rules rejecting `/`, home directory, system prefixes, the package repo path, and symlink-resolved equivalents of any of those, before any destructive operation | `NOT_STARTED` |
| 9 | RB-007 | Enforce a `HEAD`-matches-pin and clean-working-tree check immediately after detached-HEAD checkout; fail closed on mismatch | `NOT_STARTED` |
| 10 | RB-008 | Add direct host-side Cargo.lock SHA-256 computation and comparison immediately before and immediately after the Docker build step | `NOT_STARTED` |
| 11 | RB-009 | Make `docker pull` failure fatal; remove the cached-image fallback path | `NOT_STARTED` |
| 12 | RB-010 | Hard-stop on RepoDigest/platform mismatch immediately before `docker run` | `NOT_STARTED` |
| 13 | RB-011 | Guarantee creation of all stage-required evidence files (as failure placeholders where necessary) on every early-failure exit path | `NOT_STARTED` |
| 14 | RB-012 | Remove `\|\| true` from rustc/cargo/DotSlash version probes; hard-fail on version mismatch against the pin | `NOT_STARTED` |
| 15 | RB-013 | Initialize all validator-required evidence files before the first fallible in-container operation runs | `NOT_STARTED` |
| 16 | RB-014 | Implement an explicit outcome-state model (`BUILD_NOT_STARTED` / `CARGO_FAILED` / `CARGO_SUCCEEDED_ARTIFACT_MISSING` / `CARGO_SUCCEEDED_ARTIFACT_PRESENT` / `INFRASTRUCTURE_FAILURE`) written to a dedicated outcome evidence file | `NOT_STARTED` |
| 17 | RB-015 | Extend host and container ERR/EXIT traps to cover all unexpected-exit paths and guarantee outcome/evidence state is written before exit | `NOT_STARTED` |
| 18 | RB-016 | Add an explicit post-build artifact-presence check independent of cargo's exit code before classifying a run as successful | `NOT_STARTED` |
| 19 | RB-017 | Remove `\|\| true` from required static inspection commands where feasible; keep `ldd`/product execution prohibited and enforced | `NOT_STARTED` |
| 20 | RB-018 | Restructure `DOCKER_EXIT_CODE.txt` as labeled fields; complete `BUILD_TIMING` with start time, end time, and duration together | `NOT_STARTED` |
| 21 | RB-019 | Reconcile field names across templates, generators, and the validator into one documented source of truth | `NOT_STARTED` |
| 22 | RB-020 | Add per-file schema validation to the validator so a generic body cannot satisfy an unrelated required file | `NOT_STARTED` |
| 23 | RB-021 | Tighten manifest grammar to reject extra tokens, enforce consistent case, and reject absolute paths and symlinked entries | `NOT_STARTED` |
| 24 | RB-022 | Document and enforce a validator output policy (exit codes and stdout/stderr contract per outcome class) | `NOT_STARTED` |
| 25 | RB-023 | Make verdict parsing exact-match against an explicit allowed-token list; remove case-insensitive/fuzzy matching | `NOT_STARTED` |
| 26 | RB-024 | Add field-level validation rules (format, non-empty, hex-only where applicable) to the manual Witness submission form | `NOT_STARTED` |
| 27 | RB-025 | Complete the classification precedence table for overlapping-defect cases, including identity mismatch combined with missing artifact | `NOT_STARTED` |
| 28 | RB-026 | Complete the package-readiness sign-off, maintainer intake, redaction, correction ledger, and PR-identity procedures end-to-end | `NOT_STARTED` |
| 29 | RB-027 | Rewrite validator unit tests with per-file fixture bodies; remove shared generic fixtures | `NOT_STARTED` |
| 30 | All (RB-001–RB-027) | Cross-check Batch 1–4 findings for internal consistency and consolidate into `INTEGRATED_BLOCKERS.md` | `COMPLETE` |
| 31 | All (RB-001–RB-027) | Author `INTEGRATED_LIMITATIONS.md` documenting the audit method's own limitations | `COMPLETE` |
| 32 | N/A (verdict recording) | Record `FINAL_AUDIT_VERDICT.md` as **NOT READY**, explicitly distinct from C-014 | `COMPLETE` |
| 33 | N/A (status/intake recording) | Record `AUDIT_STATUS.md` as `COMPLETED` and record intake in `RC2_AUDIT_INTAKE.txt` | `COMPLETE` |

## Status summary

| Status | Count | Steps |
|--------|------:|-------|
| `COMPLETE` (this audit's own documentation) | 4 | 30–33 |
| `NOT_STARTED` (actual code/script/process remediation) | 27 | 3–29 |

No script, code, or configuration remediation has been performed. Steps 3–29 remain open work for a future phase and require the same execution restrictions (no Docker/Cargo/witness-script execution, no commit/push/tag) to be lifted or separately authorized before they can proceed.
