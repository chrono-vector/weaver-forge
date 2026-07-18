# Linux Native Dependency Plan — Phase C2A (static; not installed)

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Base image (selected) | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Packages installed this phase | **None** |

Classification:

- **required** — strongly indicated by documented procedure or hard build-script path
- **likely required** — indicated by Cargo.lock native crates / build scripts; may already be present in full `rust` image
- **optional** — useful fallbacks or alternate paths

---

## Package table

| Package (Debian/Ubuntu apt name) | Class | Why included | Evidence |
|----------------------------------|-------|--------------|----------|
| `ca-certificates` | required | TLS to crates.io, GitHub, DotSlash providers | First dependency acquisition + DotSlash download; network plan |
| `curl` | likely required | Common fetch helper; rustup/dotslash install scripts | README documents curl-based product install; DotSlash prebuilt install options use HTTPS |
| `git` | required | `xai-grok-pager-bin/build.rs` invokes `git rev-parse`; lock has git dep `nucleo` | In-tree build.rs; Cargo.lock `git+https://github.com/helix-editor/nucleo.git?...` |
| `build-essential` | likely required | C/C++ toolchain for `cc`, `ring`, `aws-lc-sys`, `libsqlite3-sys`, `zstd-sys` | Cargo.lock packages `cc`, `ring`, `aws-lc-sys`, `libsqlite3-sys`, `zstd-sys` |
| `pkg-config` | likely required | Discovery for sys crates (`libsqlite3-sys`, `zstd-sys`) | Cargo.lock deps list `pkg-config` |
| `cmake` | likely required | `aws-lc-sys` depends on `cmake` crate | Cargo.lock `aws-lc-sys` → `cmake` |
| `perl` | optional / likely | Some OpenSSL/legacy build scripts; may be pulled transitively | Historical sys-crate builds; not strongly forced by rustls/aws-lc path — keep as optional first pass |
| `clang` or rely on `gcc` from build-essential | optional | Prefer default gcc from build-essential first; add clang only if a crate requires it | No direct clang pin in project docs |
| `libssl-dev` | optional | Workspace `reqwest` uses `rustls-tls` (default-features false); tonic uses `tls-aws-lc` | Cargo.toml features favor rustls/aws-lc over OpenSSL — **do not install unless a compile error demands it** |
| `protobuf-compiler` (system protoc) | optional fallback | Official path prefers DotSlash `bin/protoc` (v29.3); system protoc is documented fallback | README; `find_protoc.rs` order: `$PROTOC` → `bin/protoc` → PATH |
| `protobuf-compiler` as primary | not preferred | Diverges from hermetic DotSlash pin (protoc 29.3 digests in `bin/protoc`) | `bin/protoc` DotSlash JSON |
| `libsqlite3-dev` | optional | `libsqlite3-sys` can build bundled or link system; prefer default crate behavior first | Cargo.lock `libsqlite3-sys` with `cc`/`pkg-config` |

---

## Already expected from official full `rust:1.92.0` image

The full (non-slim) official Rust image typically includes a C compiler and common build tools on its Debian base. C2B-1 must **inventory inside the container** before `apt-get install`:

```text
rustc --version
cargo --version
gcc --version || true
cmake --version || true
pkg-config --version || true
git --version || true
```

Install only packages confirmed missing.

---

## Packages deliberately not listed as required

| Package | Reason |
|---------|--------|
| `nodejs` / `npm` | Not documented source-build prereqs |
| `python3` | Not documented for cargo check of pager-bin (tools may use python elsewhere; out of C2B-3 narrow path) |
| Docker-in-Docker / `docker.io` | Forbidden by isolation policy |
| xAI / product SDKs | Not needed for compile |

---

## Install policy for C2B (do not run in C2A)

1. Prefer packages already in the pinned image.
2. `apt-get update` then install minimal missing set with versions recorded in logs.
3. Do not upgrade the Rust toolchain away from 1.92.0.
4. Record package versions in C2B logs; do not mutate host.

---

## What this plan does not prove

- Exact minimal package set for a green `cargo check`
- That all native crates will link without extra libs
- Security of distro packages
