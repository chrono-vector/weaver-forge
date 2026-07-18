# Phase C2B-2 Summary — Isolated container bootstrap

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Status | **COMPLETE** with recorded limitations |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` (unchanged; RO mount) |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Docker run exit | **0** (elapsed ~5m50s primary bootstrap) |

---

## Results

| Area | Result |
|------|--------|
| Native packages | **PASS** — apt install exit 0; ca-certificates/git/perl already present; installed/upgraded build-essential, pkg-config, cmake, curl (+ deps) |
| DotSlash | **PASS** — `cargo install dotslash --version 0.5.7 --locked` exit 0; binary `/work/cargo-home/bin/dotslash`; `DotSlash 0.5.7` |
| DotSlash reproducibility | **Pinned** crates.io **0.5.7**; checksum `981dcd6a72ea3aa94e09589be223e179d65827d9e3722968c81bf5f5e4609ddb` (API at install time). README documents unversioned `cargo install`; verification **chose explicit version**. |
| protoc (first probe) | **FAIL** on direct `/src/bin/protoc` — `env: 'dotslash\r'` (CRLF shebang from Windows checkout) |
| protoc (official DotSlash path, LF-normalized writable copy) | **PASS** — `libprotoc 29.3`; digest `3e866620c5be27664f3d2fa2d656b5f3e09b5152b42f1bedbf427b333e90021a`; fetch under `DOTSLASH_CACHE` |
| Native tool probes | **PASS** — rustc/cargo 1.92.0; gcc/g++ 14.2; make 4.4.1; cmake 3.31.6; pkg-config 1.8.1; git 2.47.3; perl 5.40.1; curl 8.14.1 |
| Source integrity | **PASS** — HEAD pin; clean; key SHA-256 match Phase B |
| Grok Build cargo check/build | **Not executed** |
| Dependency acquisition | **Not executed** |
| Authentication | **None** |

---

## Limitation for C2B-3

Windows checkout of `bin/protoc` may contain **CRLF** shebang lines. Kernel shebang on Linux fails with `dotslash\r`. Mitigation for C2B-3 (without modifying source permanently):

1. Invoke via `dotslash` with an LF-normalized copy under work, or
2. `dotslash -- fetch` then set `PROTOC` to fetched binary, or
3. Ensure `core.autocrlf` / `.gitattributes` yields LF for DotSlash files (policy decision; not applied this phase).

Do **not** treat this as a missing toolchain; treat as mount/checkout encoding hygiene.

---

## Phase C2B-3 readiness

### **`READY_WITH_LIMITATIONS`**

Ready to authorize RO-mounted `cargo check -p xai-grok-pager-bin` after applying the DotSlash/CRLF mitigation and explicit `PATH`/`CARGO_HOME`/`DOTSLASH_CACHE` from C2B-1/C2B-2. Not pure READY because of the CRLF shebang issue on the Windows-hosted tree.

---

## What this phase does not prove

- That Grok Build compiles
- Offline builds
- Security of packages or DotSlash
- Independent witness
