# Witness runbook — Grok Build narrow clean rebuild

**Supersedes** informal build snippets in owner-side `REPRODUCTION.md` / historical evidence for **Witness** use. Owner evidence remains historical.

Variables (Witness-chosen):

```text
WF_DIR          # clone of https://github.com/chrono-vector/weaver-forge
SRC_DIR         # clone of https://github.com/xai-org/grok-build (fresh)
WORK_DIR        # empty work root you create
CARGO_HOME_W    # $WORK_DIR/cargo-home
CARGO_TARGET_W  # $WORK_DIR/cargo-target   (must start empty)
DOTSLASH_CACHE_W # $WORK_DIR/dotslash-cache
RUSTUP_HOME_W   # $WORK_DIR/rustup-home (optional but recommended)
EVIDENCE_DIR    # your submission evidence directory
IMAGE           # docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e
PIN             # 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
```

Do **not** use owner paths such as `C:\dev\external-verification-*`.

---

## A. Host precheck

Record OS, arch, Docker client/server versions, free disk, RAM if known. Confirm Docker can run Linux containers.

## B. Source acquisition

```text
git clone https://github.com/xai-org/grok-build.git "$SRC_DIR"
cd "$SRC_DIR"
git checkout 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
```

## C. Source identity

```text
git rev-parse HEAD
# must print: 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
git status --short
# must be empty (clean)
# record SHA-256 of Cargo.lock (and optionally README.md, LICENSE, Cargo.toml)
```

Expected Cargo.lock SHA-256 (Phase B):
`1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421`

## D. Image acquisition and digest verification

```text
docker pull docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e
docker image inspect docker.io/library/rust@sha256:6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e --format "{{json .RepoDigests}}"
```

Confirm the digest matches the pin. Prefer **linux/amd64**.

## E. Clean directory creation

```text
mkdir -p "$CARGO_HOME_W" "$CARGO_TARGET_W" "$DOTSLASH_CACHE_W" "$RUSTUP_HOME_W" "$WORK_DIR/state" "$WORK_DIR/logs" "$EVIDENCE_DIR"
# Prove CARGO_TARGET_W is empty (no prior compiled artifacts)
```

## F. Dependency / bootstrap acquisition

In a disposable container (network **on** for bootstrap and dependency fetch), with:

- Source: `"$SRC_DIR":/src:ro` (read-only recommended)
- Writable: `CARGO_HOME_W`, `CARGO_TARGET_W`, `DOTSLASH_CACHE_W`, `RUSTUP_HOME_W`, state/logs
- Env: `CARGO_HOME`, `CARGO_TARGET_DIR`, `CARGO_INCREMENTAL=0`, `DOTSLASH_CACHE`, `RUSTUP_HOME`, `HOME` under work (not host home)
- No host home, no Docker socket, no SSH keys, no product credentials

Bootstrap (record all commands and outputs):

1. `apt-get update` and install (recommended set):
   `ca-certificates git build-essential pkg-config cmake curl perl`
   (package **versions** not pinned in this package — disclose observed versions)
2. Ensure DotSlash:
   `cargo install dotslash --version 0.5.7 --locked`
   (if not already present in your `CARGO_HOME`/bin)
3. Protoc via DotSlash:
   - Prefer LF-normalized copy of `/src/bin/protoc` into writable state (strip CR) if needed
   - `dotslash -- fetch <wrapper>` then set `PROTOC` to the fetched binary
   - Expect protoc **29.3** class resolution
4. Optionally `cargo fetch --locked` (network); disclose downloads

**Do not** mount or copy owner caches/targets.

## G. Narrow build

Authorized command only:

```text
export CARGO_INCREMENTAL=0
export CARGO_TARGET_DIR=...   # your empty target
export CARGO_HOME=...
# plus PROTOC, PATH including cargo-home/bin
cd /src
cargo build -p xai-grok-pager-bin --locked
```

Capture full stdout/stderr, exit code, wall time.
Jobs flag (`-j N`) is optional; if used, record it as a deviation from the bare command.

Network during compile: disclose whether bridge/host network was available. Offline-from-empty-cache is **not** required or proven.

## H. Artifact static inspection (no execution)

After success, expected path pattern:

```text
$CARGO_TARGET_DIR/debug/xai-grok-pager
```

Record (static only):

- filename, size, SHA-256
- `file` output
- `readelf -h` (or equivalent)
- `readelf -n` Build ID if available
- `readelf -d` NEEDED list (**do not use `ldd`**)

**Do not run** the binary. **Do not** pass `--version`, `--help`, `-h`, or any product argument.

## I. Post-build integrity

```text
git -C "$SRC_DIR" rev-parse HEAD   # still pin
git -C "$SRC_DIR" status --short   # still clean
# Cargo.lock SHA-256 unchanged
```

## J. Evidence packaging

Fill templates under `templates/` and capture:

- `BUILD_STDOUT.txt`, `BUILD_STDERR.txt` (raw logs)

Follow [WITNESS_SUBMISSION.md](WITNESS_SUBMISSION.md) and [WITNESS_SECURITY_AND_REDACTION.md](WITNESS_SECURITY_AND_REDACTION.md).

---

## Authorized commands (summary)

- git clone/checkout/status/rev-parse/hash
- docker pull/inspect/run (Linux container)
- apt install of bootstrap packages (disclosed)
- cargo install of DotSlash 0.5.7; cargo fetch/build as above
- static tools: sha256sum/file/readelf/objdump static parsing

## Prohibited commands (summary)

- Any execution of `xai-grok-pager` / `grok` product entry
- `--version`, `--help`, `-h`, bare TUI, login, agent, prompts, OAuth, models, update
- Full workspace build; `--release` (unless separately authorized later)
- Source or Cargo.lock modification
- `ldd` (not required; use `readelf -d`)
- Using owner artifacts or caches as inputs
