# RC4 static blind audit — scope

## In scope

Static review only of the Witness package at fixed tag `grok-build-witness-v1.0.0-rc4` (commit `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`, tree `071c4c1f4ed1b3e3a9164709c79ea9f5235ec2e9`), as preserved in the verbatim Source Weaver audit reports under this directory.

Four-batch scope (from `RC4_BATCH_4_FINAL_INTEGRATED.md` and the Batch 1–3 source reports):

- **Batch 1 — Release identity, wording, public status:** fixed rc4 identity consistency; pending/prospective wording; closure overclaims; immutable release-history recording; Docker-before-identity ordering; annotated-tag type enforcement; deviation generator/schema alignment; Rust/DotSlash deviation severity; evidence-directory atomicity; behavioral host-safety and noncanonical-output tests
- **Batch 2 — Host orchestrator / container path safety and outcomes:** `/work` writable source alias; unexpected/invalid outcome finalization; host zero vs validator/structural validity; full outcome tuple validation; `POST_BUILD_INTEGRITY.txt` status truthfulness; post-build generator/template/validator alignment; post-build four-condition enforcement; behavioral end-to-end outcome tests; global false-success impossibility
- **Batch 3 — Evidence schemas, validator, manual forms, deviations, redactions, intake:** manifest auxiliary exemptions; exact allowed-key schemas; outcome inference; cross-file outcome tuple; `NOT_REACHED` placeholders; machine-wide run provenance; host inventory depth; validator-output contamination; `evidence_inventory_complete` lifecycle; failure-package reconstruction; `WITNESS_STATEMENT` / verdict binding; intake pending enforcement; verdict ceilings; deviation indices; redaction binding; correction ledger; maintainer-intake mutation; generator-backed full-submission tests
- **Batch 4 — Integration:** integrated material blockers 5.1–5.40; integrated non-fatal limitations; readiness-policy application; public-status and claim-register assessment; C-014 assessment; Independent Witness handoff assessment; false-success / unsupported-PASS assessment; minimal mandatory remediation sequence; final static disposition **NOT READY**

## Prohibited execution boundary

This audit and this Phase 0 intake did **not** and must **not**:

- Execute Docker, Cargo, rustc, rustup, DotSlash, protoc, `ldd`, or the Grok Build product
- Execute either Witness script, the validator, or validator tests
- Transfer, extract, build, or run any archive contents as executable work
- Perform Independent Witness reproduction
- Advance C-014 from `NOT_STARTED`
- Commit, push, create/delete/move tags, or rewrite history
- Begin Phase 1 or any implementation remediation
- Close, merge, omit, downgrade, rename, or renumber any of the 40 integrated blockers

## Repository / revision

All findings refer to Weaver Forge fixed tag `grok-build-witness-v1.0.0-rc4`, commit `039b46737c5968a81fb756d7a6d1d0dd57b6ad96`, tree `071c4c1f4ed1b3e3a9164709c79ea9f5235ec2e9`, with archive/bundle identities recorded in `TRANSFER_IDENTITY.txt` and the verbatim Batch reports, unless otherwise noted.
