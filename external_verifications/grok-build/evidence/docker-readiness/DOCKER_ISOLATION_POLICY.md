# Docker Isolation Policy — Phase C2B (defined; not executed)

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| Pin | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| Preferred work root | `C:\dev\external-verification-work\grok-build-98c3b24\` |

---

## 1. Mounts and paths

| Path | Mount / role | Mode |
|------|--------------|------|
| `C:\dev\external-verification-targets\grok-build` | Source tree | **Read-only** bind mount → `/src` |
| `C:\dev\external-verification-work\grok-build-98c3b24\target` | `CARGO_TARGET_DIR` | Writable → `/work/target` |
| `C:\dev\external-verification-work\grok-build-98c3b24\cargo-home` | `CARGO_HOME` (registry/git/bin caches) | Writable → `/work/cargo-home` |
| `C:\dev\external-verification-work\grok-build-98c3b24\dotslash-cache` | DotSlash cache (if env supported) | Writable → `/work/dotslash-cache` |
| `C:\dev\external-verification-work\grok-build-98c3b24\logs` | Logs / exit codes | Writable host path (or mount `/work/logs`) |

Do **not** mount:

- User home directories
- SSH keys, `.git-credentials`, browser profiles
- Docker socket (`//var/run/docker.sock` or Windows pipe)
- Weaver Forge repo (unless separately justified; default **no**)
- Any path containing xAI API keys or product credentials

---

## 2. Network policy

| Phase | Network | Rationale |
|-------|---------|-----------|
| C2B-1 bootstrap (apt if needed, DotSlash install) | **On** | Package + crate fetch for DotSlash |
| C2B-2 dependency acquisition (`cargo fetch` / first check download) | **On** | crates.io + git nucleo + possible DotSlash protoc zip |
| After caches populated | Prefer **off** for repeat verification | Demonstrates cache sufficiency; optional second pass |
| C2B-3 first `cargo check` | **On** if caches incomplete; attempt **off** only after successful fetch | Record which mode was used |

Allowlisted destinations (conceptual; Docker Desktop may not fine-filter easily):

- `crates.io`, `static.crates.io`, `index.crates.io` (as used by cargo)
- `github.com` (nucleo git; protobuf release zip; rust-lang as needed)
- Debian/Ubuntu apt mirrors (only if apt install required)
- DotSlash provider URLs referenced by `bin/protoc`

**No xAI product API credentials** inside the container. Compile does not require product auth per prior C1 review.

---

## 3. Security / runtime flags

| Flag / posture | Policy |
|----------------|--------|
| Privileged mode | **Forbidden** |
| Host networking | **Forbidden** |
| Unnecessary published ports | **None** |
| Docker socket mount | **Forbidden** |
| User | Prefer non-root after bootstrap if practical; root acceptable only for initial apt then drop if feasible; record actual user |
| Capabilities | Default; do not add `SYS_ADMIN` etc. |
| Resource limits | Set explicit `--cpus` and `--memory` once daemon reports host capacity (e.g. leave headroom on host) |
| Read-only rootfs | Optional hardening after bootstrap; not required for first C2B-1 |

---

## 4. Integrity checks

| Check | When |
|-------|------|
| `git rev-parse HEAD` == pin | Before container start; after container exit |
| `git status --short` empty | Before and after |
| `git diff --exit-code` | Before and after |
| Container/image identity in logs | Every run (`image digest`, `docker version` server) |
| Source tree not written | Confirm no new files under clone |

---

## 5. Log and exit-code capture

Under work root `logs\`:

| File | Content |
|------|---------|
| `precheck-before.txt` | Host pin precheck |
| `precheck-after.txt` | Host pin postcheck |
| `container-identity.txt` | Image digest, `docker version`, `rustc -vV` |
| `c2b1-bootstrap.stdout.txt` / `.stderr.txt` / `exitcode.txt` | Bootstrap |
| `c2b2-fetch.stdout.txt` / `.stderr.txt` / `exitcode.txt` | Dep acquisition |
| `c2b3-cargo-check.stdout.txt` / `.stderr.txt` / `exitcode.txt` | cargo check |
| `elapsed-*.txt` | Wall-clock times |

---

## 6. Cleanup and cache retention

| Item | Policy |
|------|--------|
| Source clone | Retain; never write build outputs into it |
| `target/` cache | Retain between C2B attempts for speed; may wipe for clean-room re-run |
| `cargo-home` | Retain after first successful fetch |
| Containers | `--rm` default; no long-lived containers |
| Images | Retain pinned rust image; do not delete mid-phase without note |
| Secrets | None expected; if any appear in logs, redact before commit to Weaver package |

---

## 7. What this policy is not

- Not a security audit (Security review axis remains `NOT_STARTED`)
- Not a guarantee of hermetic offline builds on first try
- Not authorization to run product authentication or the TUI
