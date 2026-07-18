# DotSlash and protoc Plan — Phase C2A (not installed / not executed)

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| DotSlash installed this phase | **No** |
| protoc executed this phase | **No** |

---

## 1. Documented DotSlash installation (primary sources at pin)

From README “Building from source”:

```sh
cargo install dotslash
# or: prebuilt packages — https://dotslash-cli.com/docs/installation/
/usr/bin/env dotslash --help   # sanity check
```

Requirements stated:

- DotSlash required so hermetic tools under `bin/` (notably `bin/protoc`) can download and run
- `dotslash` must be on `PATH` **before** building

Closest to official documented procedure for a Rust-based Linux container:

1. Use pinned official Rust image (already has `cargo`)
2. `cargo install dotslash` **or** install a prebuilt DotSlash package from the documented installation page
3. Sanity-check with `dotslash --help` (not `protoc` execution beyond what cargo build scripts need later)

---

## 2. Should DotSlash itself be pinned?

| Approach | Pros | Cons | C2B recommendation |
|----------|------|------|--------------------|
| `cargo install dotslash` (latest crates.io) | Matches README first example | Version floats; less reproducible | Acceptable only if version recorded in logs |
| `cargo install dotslash --version <X.Y.Z>` | Better pin | Need to choose X.Y.Z from crates.io at C2B time | **Preferred if crates.io install used** |
| Prebuilt package with published version/hash | Strong pin if hashes published | Extra install path | Prefer if official install docs publish immutable artifacts |

**C2A decision:** Do not pin a specific DotSlash crates.io version without live crates.io inspection at install time. C2B-1 must:

- Record the exact DotSlash version (`dotslash --version` if available)
- Prefer version-pinned `cargo install` once a current stable version is noted
- Optionally record crate checksum from crates.io metadata in logs
- Treat DotSlash as a **toolchain bootstrap component**, not as Grok Build source

This phase does **not** invent a DotSlash commit hash without evidence.

---

## 3. How in-tree `bin/protoc` is resolved

`bin/protoc` is a **DotSlash wrapper** (shebang `#!/usr/bin/env dotslash`), not a native binary.

Pinned provider artifact (linux-x86_64) from `bin/protoc` at pin:

| Field | Value |
|-------|-------|
| Platform key | `linux-x86_64` |
| Upstream URL | `https://github.com/protocolbuffers/protobuf/releases/download/v29.3/protoc-29.3-linux-x86_64.zip` |
| Format | zip |
| Path inside archive | `bin/protoc` |
| Size | 3288836 |
| Hash alg | sha256 |
| Digest | `3e866620c5be27664f3d2fa2d656b5f3e09b5152b42f1bedbf427b333e90021a` |

Also defined: `macos-aarch64`, `linux-aarch64` (no Windows platform entry in the DotSlash JSON at this pin).

### Resolution order (`find_protoc.rs`)

1. `$PROTOC` if set and executable (`protoc --version` succeeds)
2. Walk parents for `bin/protoc` (DotSlash wrapper); on execute failure, fall through
3. `protoc` on `$PATH`
4. If not found: error in GitHub Actions; otherwise warn (`likely it is missing in docker image`) and return `Ok(None)` outside GHA

Error text when DotSlash missing and wrapper fails:

```text
protoc --version failed, likely dotslash is missing; try `cargo install dotslash`
```

---

## 4. System protoc vs DotSlash path

| Path | Closeness to docs | Reproducibility | C2B preference |
|------|-------------------|-----------------|----------------|
| DotSlash + `bin/protoc` (v29.3 pinned digests) | **Closest to README** | Strong (artifact digests in tree) | **Primary** |
| System `protobuf-compiler` on PATH | Documented fallback | Distro version drift | Fallback if DotSlash path blocked |
| `$PROTOC` to fixed binary | Supported by find_protoc | Good if binary pinned | Acceptable CI-style override |

---

## 5. Network implications

- First successful use of `bin/protoc` via DotSlash may download the zip from GitHub releases (unless already cached in DotSlash cache volume).
- Cache location should be on the **writable work volume**, not inside the read-only source mount (see isolation policy).

---

## 6. C2B execution boundaries (future)

| Action | C2A | C2B-1 | C2B-3 |
|--------|-----|-------|-------|
| Install DotSlash | No | Yes (if missing) | — |
| Run `dotslash --help` | No | Yes (sanity) | — |
| Intentionally invoke `protoc` standalone | No | Optional version probe only | Only via cargo build scripts |
| Compile Grok Build | No | No | `cargo check -p xai-grok-pager-bin` only after bootstrap+deps |

---

## 7. What this plan does not prove

- That DotSlash install will succeed offline
- That protoc 29.3 will satisfy all prost/tonic codegen needs (expected, not proven)
- Security properties of DotSlash or protobuf release artifacts
