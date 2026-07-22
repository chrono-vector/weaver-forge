# RC2 static blind audit — integrated blockers

Consolidated list of every material blocker identified across Batches 1–4 of the RC2 static blind audit of tag `grok-build-witness-v1.0.0-rc2` (`255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`). Static review only; no execution performed. All 27 items below are material blockers to a READY verdict.

## Batch 1 — Release identity & public status

| ID | Blocker |
|----|---------|
| RB-001 | Silent environment overrides of `WEAVER_FORGE_URL`/`TAG`/`COMMIT`, `GROK_BUILD_*`, `RUST_IMAGE` accepted as canonical |
| RB-002 | Stale rc1/rc2 "current package" wording in public status files |
| RB-003 | Missing post-tag finalization checklist |
| RB-004 | No explicit noncanonical deviation mode |

## Batch 2 — Host orchestrator safety & acquisition

| ID | Blocker |
|----|---------|
| RB-005 | `WITNESS_ID` unrestricted (path injection via slash, `..`, whitespace) |
| RB-006 | `WORK_ROOT` deletion/reset insufficiently guarded (`/`, home, system prefixes, package repo, symlinks) |
| RB-007 | Package clone HEAD/clean status not enforced after detached checkout |
| RB-008 | No direct Cargo.lock SHA-256 enforcement before/after Docker |
| RB-009 | `docker pull` non-fatal; continues with cached image |
| RB-010 | Image identity: RepoDigest/platform not hard-stop enforced before `docker run` |
| RB-011 | Evidence files missing on early failure paths |

## Batch 3 — Container build & evidence outcomes

| ID | Blocker |
|----|---------|
| RB-012 | Rustc/Cargo/DotSlash version not hard-validated (`DotSlash --version \|\| true`) |
| RB-013 | Required evidence files not initialized before fallible ops |
| RB-014 | No outcome-sensitive model (`BUILD_NOT_STARTED` / `CARGO_FAILED` / `CARGO_SUCCEEDED_ARTIFACT_MISSING` / `CARGO_SUCCEEDED_ARTIFACT_PRESENT` / `INFRASTRUCTURE_FAILURE`) |
| RB-015 | Unexpected ERR traps incomplete |
| RB-016 | Cargo exit 0 + missing artifact can still look like success |
| RB-017 | Required static inspection commands use `\|\| true`; `ldd`/product still prohibited |
| RB-018 | `DOCKER_EXIT_CODE.txt` bare numeric line; `BUILD_TIMING` incomplete |

## Batch 4 — Validator, classification, policy

| ID | Blocker |
|----|---------|
| RB-019 | Templates vs generators vs validator field-name drift |
| RB-020 | No file-specific schema validation (generic body can satisfy unrelated files) |
| RB-021 | Manifest grammar too loose (extra tokens, uppercase, abs paths, symlinks) |
| RB-022 | Validator output policy ambiguous |
| RB-023 | Verdict parsing case-insensitive / ambiguous |
| RB-024 | Manual Witness form fields under-validated |
| RB-025 | Classification precedence incomplete for identity mismatches / missing artifact |
| RB-026 | Package readiness / maintainer intake / redaction / correction ledger / PR identity incomplete |
| RB-027 | Unit tests too weak; shared generic fixture bodies |

## Summary

| Field | Value |
|-------|-------|
| Total material blockers | 27 (RB-001–RB-027) |
| Batch 1 count | 4 |
| Batch 2 count | 7 |
| Batch 3 count | 7 |
| Batch 4 count | 9 |
| Remediation mapping | See `INTEGRATED_REMEDIATION_LIST.md` (C2E-4 steps 3–33) |
| C-014 status | `NOT_STARTED` (unaffected by this audit) |
| Verdict | **NOT READY** |
