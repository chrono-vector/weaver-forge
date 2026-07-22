# Clean Rebuild Summary — Phase C2D-1

| Field | Value |
|-------|-------|
| Date | 2026-07-22 |
| Classification | **CLEAN REBUILD PASS** |
| Bit-identical status | **BIT_IDENTICAL_NOT_OBSERVED** |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Product executed | **No** |

## Clean environment

| Control | Value |
|---------|-------|
| New empty `CARGO_TARGET_DIR` | `...\c2d1-clean-rebuild\cargo-target` (0 entries before build) |
| C2B-4 target mounted | **No** |
| `CARGO_INCREMENTAL` | **0** |
| Command | `cargo build -p xai-grok-pager-bin --locked -j 2` |
| Jobs note | `-j 2` disclosed (stability after Docker crashes) |
| Dependency cache | Reused `cargo-home` + `dotslash-cache` (no compiled C2B-4 target) |
| Network | bridge (disclosed; not offline build) |
| Bootstrap | Prior verified apt + DotSlash 0.5.7 + LF protoc wrapper |

## Results

| Metric | Value |
|--------|-------|
| Exit code | **0** |
| Cargo elapsed | **85m 21s** |
| Host wall | ~**01:27:12** |
| Warnings | **0** `warning:` lines |
| Compiling lines | **1000** |
| New artifact | `xai-grok-pager` |
| New size | **600515304** |
| New SHA-256 | `eebdbe81a8fc34645a2f3c72aad36825d692fbef594a6c540f77ffaa42c18dad` |
| Old size | 600647920 |
| Old SHA-256 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| SHA match | **no** |
| Size match | **no** |
| Format/arch match | **yes** (ELF x86-64 pie, debug_info) |

## Classification

**CLEAN REBUILD PASS** — pinned source/image matched; empty target; incremental disabled; `--locked` build exit 0; expected artifact produced; source and Cargo.lock unchanged.

Bit-identical: **BIT_IDENTICAL_NOT_OBSERVED** → record as *owner-side build reproduced; bit-identical result not established*.

## Deviations / limitations disclosed

1. Earlier Docker crashes during fetch/bootstrap (exit 125) before successful run.
2. Successful run used `-j 2` and persistent `RUSTUP_HOME`.
3. Network remained available (bridge); not a network-none offline rebuild.
4. Dependency registry cache reused from prior C2B work (not a from-empty-registry clean room).
5. Product binary never executed this phase.

## Multi-axis note

- Owner-side narrow rebuild: may be recorded **PASS**
- Build reproducibility overall: remains **PARTIAL** (no independent witness; not bit-identical)
- Overall verification: remains **PARTIAL**

## What this does not verify

Functionality, startup, auth, API, security, production readiness, Windows native readiness, independent witness, universal bit-for-bit reproducibility.
