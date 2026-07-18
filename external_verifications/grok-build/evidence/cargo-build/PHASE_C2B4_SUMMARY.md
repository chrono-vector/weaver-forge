# Phase C2B-4 Summary — Isolated narrow cargo build

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Result | **SUCCESS** |
| Exit code | **0** |
| Classification | owner-side isolated **incremental** build (not clean-room; not official release) |
| Command | `cargo build -p xai-grok-pager-bin` (dev profile; no `--release`) |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |

## Artifact

| Field | Value |
|-------|-------|
| Name | `xai-grok-pager` |
| Host path | `C:\dev\external-verification-work\grok-build-98c3b24\cargo-target\debug\xai-grok-pager` |
| Size | **600647920** bytes |
| Type | ELF 64-bit LSB pie executable, x86-64, with debug_info, **not stripped** |
| SHA-256 | `1efcd864606d3894b685ed3ec8c6b23e7e0aceeabdc04c4c8fc991c65df4389b` |
| Executed | **No** |

## Timing

| Metric | Value |
|--------|-------|
| Cargo internal | **43m 18s** |
| Host docker wall | **00:48:22** |

## Integrity

Source pin clean; Phase B hashes unchanged; RO mount OK.

## Establishes

- Narrow crate **builds** under recorded isolated env with authorized command.

## Does not establish

- Clean-room/bit-reproducible build; release profile; functional/CLI/auth; security; witness; production readiness.
