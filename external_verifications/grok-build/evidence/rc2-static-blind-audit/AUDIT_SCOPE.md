# RC2 static blind audit — scope

## In scope

- Full static review of `external_verifications/grok-build/witness-package/` (runbook, manifest, submission procedure, templates, validator script) and related host/container orchestrator scripts, as delivered via the offline transfer bundle described in `TRANSFER_IDENTITY.txt`, at fixed tag `grok-build-witness-v1.0.0-rc2` (`255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`)
- **Batch 1 — Release identity & public status:** canonical identity-variable handling, environment-override behavior, public status wording, post-tag finalization process, noncanonical-deviation handling
- **Batch 2 — Host orchestrator safety & acquisition:** `WITNESS_ID` and `WORK_ROOT` input safety, package clone/checkout integrity enforcement, Cargo.lock hashing, Docker pull and image-identity enforcement, evidence-file presence on early failure paths
- **Batch 3 — Container build & evidence outcomes:** toolchain version validation, evidence-file initialization ordering, outcome-sensitive build-result modeling, error trapping, static inspection command rigor, Docker/timing evidence completeness
- **Batch 4 — Validator, classification, policy:** template/generator/validator field-name consistency, per-file schema validation, manifest grammar strictness, validator output policy, verdict parsing strictness, manual Witness form validation, classification precedence, package/maintainer/redaction/correction/PR procedures, unit test rigor

## Out of scope

- Executing Docker, Cargo, DotSlash, protoc, rustc, rustup, `ldd`, or the `xai-grok-pager` product
- Running any Witness host or container script
- Verifying artifact SHA-256 by rebuilding, or verifying build success
- Changing claim C-014 from `NOT_STARTED`
- Moving, deleting, retagging, or recreating tag `grok-build-witness-v1.0.0-rc2` (must remain immutable)
- Committing, pushing, or otherwise mutating the git history of this repository
- Establishing package readiness PASS

## Repository / revision

All findings refer to Weaver Forge repository https://github.com/chrono-vector/weaver-forge, fixed tag `grok-build-witness-v1.0.0-rc2`, commit `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e`, as transferred in the bundle recorded in `TRANSFER_IDENTITY.txt`, unless otherwise noted.
