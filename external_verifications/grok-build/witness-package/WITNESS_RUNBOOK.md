# Witness runbook — Grok Build narrow clean rebuild (1.0.0-rc1)

**Package status:** NOT READY until annotated tag `grok-build-witness-v1.0.0-rc1` exists and re-audit passes. This runbook is the canonical procedure once the tag is published.

**Upstream warning:** Normal Grok Build product commands (`xai-grok-pager`, `grok`, `--version`, `--help`, TUI, login, agents, OAuth, models, update) are **outside Witness scope** and **must not** be run.

---

## Canonical platform

| Route | Status |
|-------|--------|
| Linux x86_64 host + Docker | **Canonical** |
| WSL2 Linux shell + Docker Desktop (Linux containers) | **Canonical** |
| PowerShell-only host orchestration | **Noncanonical** for 1.0.0-rc1 |
| Windows-native `cargo` | **BLOCKED** |
| macOS Docker | **Unvalidated / noncanonical** |

All builds run **inside** `linux/amd64` Docker (`--platform linux/amd64`).

---

## One copyable host block (Linux / WSL2 bash)

Assign variables and invoke the host orchestrator. Replace `YOUR_WITNESS_ID` and choose an **empty** work root **outside** any Weaver Forge clone.

```bash
export WEAVER_FORGE_URL="https://github.com/chrono-vector/weaver-forge.git"
export WEAVER_FORGE_TAG="grok-build-witness-v1.0.0-rc1"
export GROK_BUILD_URL="https://github.com/xai-org/grok-build.git"
export GROK_BUILD_COMMIT="98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce"
export RUST_IMAGE="docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e"
export WORK_ROOT="/var/tmp/grok-witness-work"

# After tag exists: clone Weaver Forge only to obtain scripts, or run from an existing checkout of the tagged commit.
WF_CHECKOUT="/var/tmp/weaver-forge-tag-checkout"
git clone "${WEAVER_FORGE_URL}" "${WF_CHECKOUT}"
git -C "${WF_CHECKOUT}" fetch --tags origin
git -C "${WF_CHECKOUT}" checkout "refs/tags/${WEAVER_FORGE_TAG}"

bash "${WF_CHECKOUT}/external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh" \
  --work-root "${WORK_ROOT}" \
  YOUR_WITNESS_ID
```

**Exact invocation (once variables are set):**

```bash
bash external_verifications/grok-build/witness-package/scripts/run_witness_narrow_build.sh \
  --work-root "${WORK_ROOT}" \
  YOUR_WITNESS_ID
```

### Run ID and evidence directory

Format: `<witness-id>-<UTC-YYYYMMDD>-<short-run-id>`

Evidence directory (host helper default):

```text
${WORK_ROOT}/evidence/<run-id>/
```

Copy completed templates + logs into submission path per [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md).

---

## Directory layout (host helper)

| Variable | Typical path under `WORK_ROOT` |
|----------|--------------------------------|
| `WF_DIR` | `weaver-forge/` (fresh clone; resolves tag) |
| `SRC_DIR` | `grok-build-src/` (fresh clone at pin) |
| `CARGO_HOME_DIR` | `cargo-home/` |
| `CARGO_TARGET_DIR` | `cargo-target/` (must start empty) |
| `DOTSLASH_CACHE_DIR` | `dotslash-cache/` |
| `HOME_DIR` | `home/` |
| `BOOTSTRAP_DIR` | `bootstrap/` (LF protoc descriptor copy) |
| `EVIDENCE_DIR` | `evidence/<run-id>/` |

---

## Docker contract (single container run)

The host script runs **one** disposable container:

| Flag / mount | Value |
|--------------|--------|
| `--rm` | yes |
| `--platform` | `linux/amd64` |
| `--network` | `bridge` |
| Source | `-v ${SRC_DIR}:/src:ro` |
| Work | `-v ${WORK_ROOT}:/work` |
| Evidence | `-v ${EVIDENCE_DIR}:/evidence` |
| Script | `-v .../container_narrow_build.sh:/witness/container_narrow_build.sh:ro` |
| `-w` | `/src` |
| `HOME` | `/work/home` |
| `CARGO_HOME` | `/work/cargo-home` |
| `CARGO_TARGET_DIR` | `/work/cargo-target` |
| `CARGO_INCREMENTAL` | `0` |
| `DOTSLASH_CACHE` | `/work/dotslash-cache` |
| `PATH` | `/work/cargo-home/bin:` + image cargo paths |
| `RUSTUP_HOME` | **Do not** set to empty work dir — preserve image toolchain; record effective value |

---

## Evidence filenames (required)

| File | Role |
|------|------|
| `CONTAINER_STDOUT.txt` / `CONTAINER_STDERR.txt` | Full Docker capture |
| `DOCKER_EXIT_CODE.txt` | Docker exit code |
| `BUILD_STDOUT.txt` / `BUILD_STDERR.txt` | Cargo-only logs |
| `BUILD_EXIT_CODE.txt` | Cargo exit + `cargo_started` |
| `BUILD_TIMING.txt` | UTC start/end, elapsed, command |
| `CLEAN_TARGET_PROOF.txt` | Host + container empty-target proof |
| `WEAVER_FORGE_PACKAGE_IDENTITY.txt` | Tag + resolved Weaver commit |
| `SOURCE_IDENTITY.txt` | Grok pin + Cargo.lock hash |
| `EVIDENCE_MANIFEST.sha256` | Checksum manifest |
| `REDACTIONS.md` | Redaction log |

See [WITNESS_PACKAGE_MANIFEST.md](WITNESS_PACKAGE_MANIFEST.md) for the full list.

---

## Bootstrap (container)

Noninteractive `apt-get install` (versions **not** pinned — record observed):

`ca-certificates`, `git`, `build-essential`, `pkg-config`, `cmake`, `curl`, `perl`, `file`, `binutils`

| Component | Pin |
|-----------|-----|
| DotSlash | `cargo install dotslash --version 0.5.7 --locked` into isolated `CARGO_HOME` |
| protoc | Copy `/src/bin/protoc` → writable LF file under `/work/bootstrap/`; `chmod +x`; `export PROTOC=<that path>`; version probe via descriptor only |

**Do not** modify `/src`. **Do not** run the product binary.

---

## Build command (exact)

```bash
cargo build -p xai-grok-pager-bin --locked
```

With `CARGO_INCREMENTAL=0`. No `-j 2` in the canonical command (optional parallelism is a **noncanonical** deviation if used).

Separate `cargo fetch --locked` is **omitted**; fresh `CARGO_HOME` still requires network during the locked build. Completely offline reproduction is **NOT ESTABLISHED**.

---

## Failure behavior

| Condition | Behavior |
|-----------|----------|
| Missing `WEAVER_FORGE_TAG` on origin | Host script **exit 3** with clear message |
| Non-empty `WORK_ROOT` | Refused unless `--allow-nonempty-work-root` |
| Unsafe `WORK_ROOT` (`/`, `$HOME`, Weaver repo) | **exit 2** |
| Non-empty target before build | Stop; record failure; no Cargo |
| Bootstrap failure | `cargo_started=NO`, `BUILD_NOT_STARTED`, container exit ≠ 0 |
| Source / lock change | FAIL classification per [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) |

---

## Optional / noncanonical alternatives

Manual step-by-step Docker without the host script is **unvalidated**. Owner historical paths under `../evidence/` are **not** Witness commands.

---

## Static inspection (after successful build only)

Record path, size, SHA-256, `file`, `readelf -h`, `readelf -n`, `readelf -d`, `objdump -f`. **Never execute** the artifact. **`ldd` forbidden.**
