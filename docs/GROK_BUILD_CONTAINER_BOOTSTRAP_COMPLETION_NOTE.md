# Completion Note — Grok Build Phase C2B-2: Isolated Container Bootstrap

| Field | Value |
|-------|-------|
| Phase | **C2B-2** — packages, DotSlash, protoc resolution |
| Date | 2026-07-18 |
| Source pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Image | `docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| Work root | `C:\dev\external-verification-work\grok-build-98c3b24\` |
| Source integrity | **PASS** (pin clean; Phase B hashes match) |
| DotSlash | **0.5.7** pinned; install exit 0 |
| protoc | **libprotoc 29.3** via DotSlash (LF-normalized wrapper) |
| cargo against Grok Build | **No** |
| Phase C2B-3 readiness | **`READY_WITH_LIMITATIONS`** |
| Evidence | `external_verifications/grok-build/evidence/container-bootstrap/` |

---

## 1. Work-path layout

```text
logs\  cargo-home\  cargo-target\  dotslash-cache\  container-state\
```

Source RO-mounted only; not copied.

## 2. Packages installed (container)

Already present: `ca-certificates`, `git`, `perl`.
Installed/upgraded: `build-essential` 12.12, `pkg-config` 1.8.1-4, `cmake` 3.31.6-2, `curl` 8.14.1-2+deb13u4 (+ deps).
apt exit codes: update 0, install 0.

## 3. DotSlash

- Command: `cargo install dotslash --version 0.5.7 --locked` (into `CARGO_HOME=/work/cargo-home`)
- crates.io checksum: `981dcd6a72ea3aa94e09589be223e179d65827d9e3722968c81bf5f5e4609ddb`
- Version output: `DotSlash 0.5.7`
- Path: `/work/cargo-home/bin/dotslash`
- Reproducibility: **version-pinned** (README shows unversioned install; verification pinned 0.5.7)

## 4. protoc

- Official path: in-tree DotSlash `bin/protoc` → protobuf **v29.3** linux-x86_64 digest `3e866620c5be27664f3d2fa2d656b5f3e09b5152b42f1bedbf427b333e90021a`
- First probe on RO mount failed: CRLF shebang (`dotslash\r`)
- Retry: LF-normalized **writable copy** under work + `dotslash -- fetch` → **libprotoc 29.3** exit 0
- No silent system-protoc substitution as primary path

## 5. What was not executed

- `cargo check` / `build` / `test` / `run` / `metadata` against Grok Build
- Project dependency acquisition
- xAI authentication
- Source modification; git fetch/pull
- Host software install

## 6. Multi-axis verdict (conservative)

| Axis | Status |
|------|--------|
| Source authenticity | PASS |
| Artifact integrity | PARTIAL |
| Windows readiness | BLOCKED |
| Docker image/toolchain | PASS |
| Container bootstrap | **PASS** (with CRLF limitation for shebang) |
| Build reproducibility | **NOT_STARTED** |
| Functional reproducibility | **NOT_STARTED** |
| Claim verification | PARTIAL |
| Security / witness / ops | NOT_STARTED |
| **Overall** | **PARTIAL** |

## 7. Recommended next action

Authorize **C2B-3**: `cargo check -p xai-grok-pager-bin` in disposable container with:

- same image pin and RO source mount
- `PATH` including `/work/cargo-home/bin` and `/usr/local/cargo/bin` (avoid bare `bash -lc`)
- `CARGO_HOME`, `CARGO_TARGET_DIR`, `DOTSLASH_CACHE` on work volumes
- DotSlash/protoc via LF-safe wrapper or `PROTOC` from `dotslash -- fetch`
- still **no** product authentication

---

**Evidence before authority. Bootstrap PASS is not compile PASS.**
