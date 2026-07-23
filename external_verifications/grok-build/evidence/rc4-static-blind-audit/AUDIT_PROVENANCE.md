# RC4 static blind audit — provenance

| Field | Value |
|-------|-------|
| Audit phase | RC5 Phase 0 — RC4 static blind audit intake only |
| Source type | Source Weaver static blind audit |
| Audit modality | Owner-side / static audit only |
| Method | Static documentation- and script-level review only; **no execution** |
| Repository | https://github.com/chrono-vector/weaver-forge |
| Package version | `1.0.0-rc4` |
| Fixed package tag | `grok-build-witness-v1.0.0-rc4` |
| Tagged Weaver Forge commit | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` |
| Commit tree | `071c4c1f4ed1b3e3a9164709c79ea9f5235ec2e9` |
| Pinned Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Transfer / archive identities | See `TRANSFER_IDENTITY.txt` (`bundle_sha256`, `inner_archive_sha256`) — identities already recorded in the source audit reports |
| External verbatim intake source directory | `C:\dev\weaver-forge-rc4-audit-source\rc4_audit_intake_source` |
| Expected source zip SHA-256 (intake authorization) | `fa8da4f986c7f8104dc5b6e7323d265a31e217345fa938a4d70d6e88af6a1974` |
| Source-file manifest | `RC4_AUDIT_SOURCE_MANIFEST.sha256` (verbatim preserved; hashes verified for all listed batch files) |
| Docker executed | **No** |
| Cargo / Rust / rustc / rustup / DotSlash / protoc executed | **No** |
| `ldd` / product executed | **No** |
| Witness host or container script executed | **No** |
| Validator / validator tests executed | **No** |
| Independent Witness reproduction | **NOT PERFORMED** |
| Independent Witness (C-014) | **`NOT_STARTED`** |
| Commit / push / tag operation performed during this intake | **No** |
| rc1–rc4 immutability | Tags `grok-build-witness-v1.0.0-rc1` through `grok-build-witness-v1.0.0-rc4` and their peeled targets **must remain immutable**; this intake does not move, delete, or recreate any of them |
| Final static disposition | **NOT READY** |

## What this record is

This document preserves the provenance of a completed Source Weaver static blind audit of the Grok Build Witness package at the fixed `rc4` tag. The twelve verbatim source reports under this directory, the derived integrated blocker/limitation/remediation records, and the final verdict are owner-side / static audit evidence only. No build, container, Cargo, DotSlash, protoc, `ldd`, Witness script, validator, or product command was run at any point in this audit or in this Phase 0 intake.

## Source-file manifest reference

Verbatim preserved sources (byte-for-byte copies of the external intake directory):

- `README_INTAKE.md`
- `RC4_AUDIT_SOURCE_MANIFEST.sha256`
- `RC4_BATCH_1_PART_1.md`
- `RC4_BATCH_1_PART_2.md`
- `RC4_BATCH_1_PART_3.md`
- `RC4_BATCH_1_PART_4_FINAL.md`
- `RC4_BATCH_2_PART_1.md`
- `RC4_BATCH_2_PART_2_CONTINUATION_FINAL.md`
- `RC4_BATCH_3_PART_1.md`
- `RC4_BATCH_3_PART_2.md`
- `RC4_BATCH_3_PART_3_FINAL.md`
- `RC4_BATCH_4_FINAL_INTEGRATED.md`

Batch-file SHA-256 values are authoritative in `RC4_AUDIT_SOURCE_MANIFEST.sha256`. Extra intake files not listed in that manifest were still preserved byte-for-byte:

- `README_INTAKE.md` SHA-256 = `e709e71e49e61e052955ba614f74af517fa99f45bdcf9f30d3529e0fcdfe5a65`
- `RC4_AUDIT_SOURCE_MANIFEST.sha256` SHA-256 = `06a8ec9abe9bc553f6ed6357bfd597863e79d436037df2d17a8a65a279a8f688`

## Prior audit history

- `grok-build-witness-v1.0.0-rc1` — static/repeat blind audit: **NOT READY**.
- `grok-build-witness-v1.0.0-rc2` — integrated static blind audit: **NOT READY**.
- `grok-build-witness-v1.0.0-rc3` — integrated static blind audit: **NOT READY**.
- `grok-build-witness-v1.0.0-rc4` (this record) — integrated static blind audit: **NOT READY** (40 material blockers, `RC4B-001`–`RC4B-040`).

## What this record is not

- Not Independent Witness reproduction (C-014 remains `NOT_STARTED`).
- Not a certification of package readiness.
- Not a build, execution, or functional result of any kind.
- Not an authorization to move, delete, or recreate the `rc4` (or prior) tags.
- Not Phase 1 remediation; no blocker is closed by this intake.
