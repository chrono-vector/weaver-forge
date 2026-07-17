# Phase C2 — Isolated build procedure (defined, not executed)

Date planned: 2026-07-17
Status: **PLAN ONLY** — do not execute until readiness is no longer `BLOCKED` and a plan revision authorizes C2.

Pinned source (immutable):

```text
C:\dev\external-verification-targets\grok-build
commit 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
```

Preferred work root (create only when C2 starts):

```text
C:\dev\external-verification-work\grok-build-98c3b24\
  logs\
  target\          # via CARGO_TARGET_DIR
```

---

## 1. Preconditions (must be true before C2)

| # | Precondition |
|---|--------------|
| 1 | Pin precheck still PASS (HEAD exact, clean, no dirty) |
| 2 | rustup + channel **1.92.0** available (or rustc/cargo matching toolchain file) |
| 3 | DotSlash on PATH (per README) |
| 4 | MSVC Build Tools + Windows SDK **or** documented alternative linker, if building on Windows |
| 5 | Network allowed for crates.io + git + DotSlash providers **or** fully populated offline cache (not present today) |
| 6 | Explicit authorization in `VERIFICATION_PLAN.md` for C2 |
| 7 | Prefer Linux/macOS host per upstream “supported build hosts” if available |

**Current host fails 2–4 → Phase C2 readiness = BLOCKED.**

---

## 2. Isolation and outputs

| Item | Policy |
|------|--------|
| Source tree | Read-only intent: **do not edit** files under the clone |
| `CARGO_TARGET_DIR` | `C:\dev\external-verification-work\grok-build-98c3b24\target` (outside source) |
| `CARGO_HOME` | Optional dedicated dir under work root (outside source) |
| Logs | `...\logs\cargo-check.stdout.txt`, `.stderr.txt`, `env-summary.txt`, `precheck.txt` |
| Network | Allowlist crates.io, static.crates.io, github.com (nucleo git, DotSlash providers) only as needed |
| Authentication | **No** product/xAI API credentials; compile-only |
| Secrets | Do not log tokens; do not dump full env |

---

## 3. Command order (proposed; not run)

### 3.1 Precheck (always)

```text
cd C:\dev\external-verification-targets\grok-build
git rev-parse HEAD
# expect 98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce
git status --short
git diff --exit-code
```

Capture outputs under work `logs\precheck-*.txt`.

### 3.2 Tool versions

```text
rustc --version --verbose
cargo --version --verbose
rustup show
dotslash --help
where cl   # Windows
```

### 3.3 Documented validation command (primary C2 goal)

From README at pin:

```text
set CARGO_TARGET_DIR=C:\dev\external-verification-work\grok-build-98c3b24\target
cd C:\dev\external-verification-targets\grok-build
cargo check -p xai-grok-pager-bin
```

Optional later (separate authorization):

```text
cargo build -p xai-grok-pager-bin --release
```

**Do not** in C2 (default):

```text
cargo run -p xai-grok-pager-bin   # launches TUI / may trigger auth
```

### 3.4 Capture

- Exit code of each command
- Full stdout/stderr to log files
- Start/end timestamps
- Whether `CARGO_TARGET_DIR` received artifacts

---

## 4. Proving source tree unchanged

After C2 attempt:

```text
cd C:\dev\external-verification-targets\grok-build
git status --short
git diff --exit-code
git rev-parse HEAD
```

Expect: still clean, still pin.
Any modification → record `FAIL` for isolation hygiene and list paths (do not auto-revert without operator decision).

Note: cargo may write to source tree if `target/` not redirected — **require** `CARGO_TARGET_DIR` outside tree. Also watch for accidental `Cargo.lock` changes (should not change if lock used as-is).

---

## 5. Cleanup procedure

| Action | When |
|--------|------|
| Keep logs | Always (evidence) |
| Delete `CARGO_TARGET_DIR` | Optional after evidence harvested |
| Never delete pin clone | Unless operator explicitly retires verification target |
| Unset temporary env vars | End of session |

---

## 6. Distinguishing success classes

| Outcome | Means | Does not mean |
|---------|-------|---------------|
| `cargo check` exit 0 | Compilation/typecheck of package graph for that package succeeded | Product works; AI service OK; tests passed |
| `cargo build --release` exit 0 | Binary artifact produced | Auth, tools, or agent quality verified |
| Binary runs + auth UI | Functional/product concern | Separate phase; out of C2 default |
| Exit non-zero | Build failure evidence | Not a security audit |

---

## 7. Witness notes

Independent witnesses must use the same pin, record their own host inventory, and not claim owner-side C1/C2 results. Owner-side package author is not a witness.

---

## 8. Explicit non-execution record

This file does **not** authorize or record any C2 run.
As of 2026-07-17 readiness inspection: **do not start C2 on the current Windows host**.
