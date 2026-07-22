# RC3 static blind audit — provenance

| Field | Value |
|-------|-------|
| Phase | C2E-5 (RC3 integrated static blind audit intake and RC4 remediation preparation) |
| Audit type | Integrated static blind audit (4 batches) |
| Method | Static documentation- and script-level review only; **no execution** |
| Repository | https://github.com/chrono-vector/weaver-forge |
| Fixed rc3 tag | `grok-build-witness-v1.0.0-rc3` |
| Fixed rc3 tag commit | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` |
| Transfer mechanism | Offline transfer bundle delivered outside the git remote (see `TRANSFER_IDENTITY.txt`) |
| Transfer bundle path (external, outside this repository) | `C:\dev\weaver-forge-audit-exports\weaver-forge-grok-build-witness-v1.0.0-rc3-transfer-bundle.zip` |
| Transfer bundle SHA-256 | `b7b4c6a20d2e1b8d55c15dbfff784499507f28ccddff7b54e8aa4ab8fc3bde7c` |
| Inner archive | `weaver-forge-grok-build-witness-v1.0.0-rc3.zip` |
| Inner archive SHA-256 | `b3a65151f62dfa975ba7068f68a9ceb00f80c4058a3a6220663e5b9b8fae51d8` |
| Docker executed | **No** |
| Cargo / Rust / rustc / rustup / DotSlash / protoc executed | **No** |
| `ldd` / product executed | **No** |
| Witness host or container script executed | **No** |
| Independent Witness reproduction (C-014) | **No** — remains `NOT_STARTED` |
| Commit / push / tag operation performed during this audit | **No** |
| rc3 immutability | The `grok-build-witness-v1.0.0-rc3` tag and its target commit **must remain immutable**; this audit does not move, delete, or recreate it |
| Verdict | **NOT READY** |

## What this record is

This document preserves the provenance of a completed, static, blind-audit review of the Grok Build Witness package as delivered at the fixed `rc3` tag via an offline transfer bundle. The four batch findings, the integrated blocker/limitation/remediation lists, and the final verdict were produced entirely through static reading of files transferred in the bundle described in `TRANSFER_IDENTITY.txt`. No build, container, Cargo, DotSlash, protoc, `ldd`, or product command was run at any point in this audit.

## Prior audit history

- `grok-build-witness-v1.0.0-rc1` — static/repeat blind audit and defect-closure work: **NOT READY**.
- `grok-build-witness-v1.0.0-rc2` — integrated static blind audit (`external_verifications/grok-build/evidence/rc2-static-blind-audit/`): **NOT READY** (27 material blockers, `RB-001`–`RB-027`).
- `grok-build-witness-v1.0.0-rc3` (this record) — integrated static blind audit: **NOT READY** (28 material blockers, `RC3B-001`–`RC3B-028`).

Each prior candidate's rc tag and target commit remains immutable. This audit does not supersede, retract, or reopen any prior audit's verdict; it is a new, independent static review of the rc3 identity.

## What this record is not

- Not Independent Witness reproduction (C-014 remains `NOT_STARTED`).
- Not a certification of package readiness.
- Not a build, execution, or functional result of any kind.
- Not an authorization to move, delete, or recreate the `rc3` tag.
