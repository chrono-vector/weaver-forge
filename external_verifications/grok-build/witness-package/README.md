# Independent Witness Package — Grok Build (narrow clean rebuild)

| Field | Value |
|-------|-------|
| Package status | **WITNESS PACKAGE READY WITH LIMITATIONS** |
| Independent Witness status | **`NOT_STARTED`** (no third-party run yet) |
| Target | Grok Build at pinned commit (not floating tip) |
| Scope | Narrow clean rebuild of `xai-grok-pager-bin` only |
| Product execution | **Forbidden** |

---

## Who this is for

An independent person (not the package owner / owner-side reproducer) who will rebuild Grok Build’s narrow binary from public materials on **their own** host, VM, or cloud environment.

## Canonical entry points (public)

| Role | URL / path |
|------|------------|
| Weaver Forge repository (this package) | `https://github.com/chrono-vector/weaver-forge` |
| Package path in repo | `external_verifications/grok-build/witness-package/` |
| Grok Build source (upstream) | `https://github.com/xai-org/grok-build` |
| Pinned source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |

Start here after cloning Weaver Forge at any commit that includes this directory. Prefer a recent `main` tip that contains the Witness package.

## Fixed identities (must match)

| Item | Value |
|------|--------|
| Source URL | `https://github.com/xai-org/grok-build` |
| Source commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Container image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Rust | **1.92.0** (image + `rust-toolchain.toml` at pin) |
| Package | `xai-grok-pager-bin` |
| Binary name | `xai-grok-pager` |
| Build command | `cargo build -p xai-grok-pager-bin --locked` |
| Incremental | `CARGO_INCREMENTAL=0` |
| Target dir | **new empty** `CARGO_TARGET_DIR` (Witness-chosen path) |

## Read next (in order)

1. [WITNESS_REQUIREMENTS.md](WITNESS_REQUIREMENTS.md)
2. [WITNESS_RUNBOOK.md](WITNESS_RUNBOOK.md)
3. [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)
4. [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md)
5. [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md)
6. [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md)
7. Templates under [templates/](templates/)

## What success means

**INDEPENDENT NARROW REBUILD PASS** does **not** require matching either owner-side artifact SHA-256. You must record **your own** size, SHA-256, Build ID, and static file metadata.

Owner-side artifacts (historical evidence only):

| Build | Size | SHA-256 |
|-------|-----:|---------|
| C2B-4 (incremental) | 600647920 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| C2D-1 (clean) | 600515304 | `eebdbe81a8fc34645a2f3c72aad36825d692fbef594a6c540f77ffaa42c18dad` |

Those hashes are **not** acceptance criteria for Witness PASS.

## Explicit non-claims

- This package readiness status is **not** Independent Witness PASS.
- Offline-from-empty-cache rebuild is **not** established.
- Windows-native build remains **BLOCKED** (Docker Linux route only).
- Product TUI/auth/agent runs are **out of scope**.

## Historical owner evidence

Owner-side logs under `../evidence/` use paths such as `C:\dev\...` and `/work/cargo-target*`. Those are **historical owner records**, not Witness command requirements.
