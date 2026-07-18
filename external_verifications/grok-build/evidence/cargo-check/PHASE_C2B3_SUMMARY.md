# Phase C2B-3 Summary — Isolated narrow cargo check

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Result | **SUCCESS** |
| Exit code | **0** |
| Classification | Successful compile-check (not a full release build; not functional test) |
| Authorized command | `cargo check -p xai-grok-pager-bin` |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |

## Timing

| Metric | Value |
|--------|-------|
| Cargo internal | **70m 07s** (`Finished ... in 70m 07s`) |
| Host wall clock (docker run) | **01:17:30** |
| Container check window | 2026-07-18T04:19:39Z → 05:36:34Z |

## Toolchain in run

- rustc / cargo 1.92.0
- DotSlash 0.5.7 (from isolated CARGO_HOME)
- protoc 29.3 via PROTOC=DotSlash-fetched binary
- Approved apt packages reinstalled in disposable container

## Integrity

- Source pin clean; Phase B key hashes unchanged; Cargo.lock unchanged
- RO mount write probe failed (expected)
- Caches retained under work root; container removed (`--rm`)

## What this establishes

- Documented narrow validation command **succeeds** at the pin in the isolated Linux container path.

## What this does not establish

- `cargo build --release` or full workspace
- Runtime/functional behavior
- Security or independent witness
- Offline reproducibility from empty caches
- Windows host build
