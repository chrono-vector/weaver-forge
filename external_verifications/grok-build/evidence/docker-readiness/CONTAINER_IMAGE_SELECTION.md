# Container Image Selection — Phase C2A

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Pinned Grok Build commit | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Selection status | **SELECTED** (registry metadata pin; local pull **not** performed) |
| Custom image built this phase | **No** |

---

## 1. Requirements from pinned source

| Requirement | Source |
|-------------|--------|
| Rust channel **1.92.0** | `rust-toolchain.toml` |
| Components rustfmt, clippy | `rust-toolchain.toml` |
| Workspace edition **2024** | root `Cargo.toml` |
| Explicit host targets include `x86_64-unknown-linux-gnu` | `rust-toolchain.toml` |
| DotSlash required before build | README “Building from source” |
| protoc via `bin/protoc` (DotSlash) or PATH / `$PROTOC` | README; `crates/build/xai-proto-build/src/find_protoc.rs` |
| macOS/Linux supported build hosts | README |
| No project Dockerfile / devcontainer | Tree search at pin: **none found** |

---

## 2. Candidates evaluated

### A. Official `rust` image pinned to 1.92.0 — **SELECTED**

| Criterion | Assessment |
|-----------|------------|
| Rust 1.92.0 + edition 2024 | Tag `1.92.0` exists on Docker Hub `library/rust` (active) |
| DotSlash install | Possible in container via `cargo install dotslash` (documented) or prebuilt packages |
| protoc / native tools | Full (non-slim) image includes C toolchain on Debian base; apt packages can add cmake/pkg-config/git as needed |
| Locked Cargo deps | Compatible with Linux x86_64; no Windows MSVC requirement inside Linux container |
| Provenance | Official Docker Official Image `library/rust`; label `org.opencontainers.image.source=https://github.com/rust-lang/docker-rust` |
| Digest pin | Multi-arch index + linux/amd64 platform digests resolved via registry/Hub API |
| Host impact | Minimal: single official base; no custom image build in C2A |

### B. Debian/Ubuntu + rustup 1.92.0 — **DEFERRED fallback**

| Criterion | Assessment |
|-----------|------------|
| Flexibility | Full control over OS package set |
| Reproducibility | Requires pinning both base OS digest **and** rustup toolchain install steps |
| Complexity | Higher than A; more moving parts for C2B bootstrap |
| When to use | Only if official `rust:1.92.0` proves unsuitable after C2B-1 |

### C. Project container / devcontainer — **NOT AVAILABLE**

No `Dockerfile`, `.devcontainer/`, or documented project container at pin.

---

## 3. Tag choice within official rust images

| Tag | Role | Decision |
|-----|------|----------|
| `rust:1.92.0` | Default official pin matching toolchain channel | **Primary selection** |
| `rust:1.92.0-bookworm` | Explicit Debian bookworm base | Acceptable alternate if trixie-related issues arise |
| `rust:1.92.0-slim` / slim-bookworm | Smaller | **Rejected for first attempt** — less likely to include full native build toolchain out of box |
| Alpine tags | musl | **Rejected for first attempt** — project pin lists `*-unknown-linux-gnu` targets |

Hub last_updated for `1.92.0`: 2026-01-22 (tag metadata); linux/amd64 last_pushed: 2026-01-13.

**Tags are not immutable** — Phase C2B must pull/run by **digest**.

---

## 4. Selected image identity (authoritative)

| Field | Value |
|-------|-------|
| Registry | `docker.io` |
| Repository | `library/rust` |
| Tag (human reference) | `1.92.0` |
| Multi-arch **index** digest | `sha256:f58923369ba295ae1f60bc49d03f2c955a5c93a0b7d49acfb2b2a65bebaf350d` |
| **linux/amd64 platform manifest digest (pull/run pin)** | **`sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e`** |
| Config **blob** digest (metadata only; **not** a pull reference) | `sha256:45dfd6a3b0ca04ba914df344b1f01d32092a33c56b067f88d738e4707b8dbec7` |
| Architecture | `amd64` |
| OS | `linux` |
| Created (config) | `2026-01-13T06:12:13.194813512Z` |
| Approximate compressed size (Hub linux/amd64) | 591904291 bytes (~564 MiB) |
| Pull reference (C2B) | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Local image ID | **N/A — not pulled this phase** |

Resolution method: Docker Hub tag API + registry v2 manifest/config fetch (no `docker pull`).

---

## 5. Why not improvise

If the official `1.92.0` image had been missing, this phase would have selected a pinned Debian/Ubuntu base by digest and deferred a Dockerfile that installs rustup channel 1.92.0 to C2B. That path was **not required** — official tag exists and is active.

---

## 6. What this selection does not prove

- That the image will successfully compile Grok Build
- That local daemon can pull (daemon was stopped during C2A)
- Security of the image beyond official provenance notes
- Bit-for-bit local match until pull + digest verify in C2B-1
