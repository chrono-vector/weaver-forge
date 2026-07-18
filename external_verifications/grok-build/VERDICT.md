# Verdict — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Verdict status | **Windows BLOCKED; Docker/Linux image+toolchain PASS; overall PARTIAL** |
| Issued by | Weaver Forge documentation package author |
| Role | Owner-side evaluator (not independent witness) |
| Verdict date | `2026-07-18` |
| Source identity pin | **`98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce`** |
| Linked results | `RESULTS.md` |
| Linked witness handoff | `WITNESS_HANDOFF.md` |

---

## Allowed Verdict Values

`PASS` | `PARTIAL` | `FAIL` | `BLOCKED` | `NOT_APPLICABLE` | `NOT_STARTED`

---

## 1. Multi-Axis Verdict Table

| Axis | Verdict | Summary of evidence | What this axis does not establish |
|------|---------|---------------------|-----------------------------------|
| Source authenticity | `PASS` | Official x.ai pages + public `xai-org/grok-build` clone | Ongoing trust; code safety |
| Artifact integrity | `PARTIAL` | Full commit + tree OID + local key-file SHA-256; no publisher checksums/signed tags | Supply-chain audit; binary integrity |
| Build reproducibility | `NOT_STARTED` | No cargo against Grok Build | Compile success |
| Functional reproducibility | `NOT_STARTED` | No product execution | Runtime behavior |
| Claim verification | `PARTIAL` | Docs PASS; C-015 BLOCKED; C-016 PASS (image/toolchain only); build claims unstarted | Runtime truth |
| Security review | `NOT_STARTED` | Out of scope | Security assurance |
| Independent-witness status | `NOT_STARTED` | No witness | E4 |
| Operational readiness | `NOT_STARTED` | Product ops not evaluated | Production approval |
| **Windows environment readiness** | **`BLOCKED`** | Missing Rust, DotSlash, MSVC/SDK on Windows host | Future host readiness after installs |
| **Docker/Linux build readiness** | **`PASS`** (image + toolchain only) | Daemon 29.4.3; pin pulled; RepoDigest match; rustc/cargo 1.92.0 direct | Packages, DotSlash, cargo check, compile |

---

## 2. Overall Package Verdict

| Field | Value |
|-------|-------|
| Overall verdict | **`PARTIAL`** |
| Overall verdict rule used | Rule 4: some axes PASS with limitations; build/functional/security/witness/ops open; **not** overall PASS |

### Overall justification

```text
Source authenticity PASS; artifact integrity PARTIAL. Windows readiness BLOCKED.
Docker/Linux image+toolchain readiness PASS after C2B-1 pull and rustc/cargo
1.92.0 verification (login-shell PATH anomaly only). Build/functional/security/
witness/ops remain NOT_STARTED. Claim verification PARTIAL. Overall PARTIAL.
```

---

## 3. Claim Verification Rollup

| Claim ID | Status |
|----------|--------|
| C-001–C-011 | `PASS` (identity/docs) |
| C-012–C-014 | `NOT_STARTED` |
| C-015 | `BLOCKED` (Windows host) |
| C-016 | `PASS` (Docker/Linux image+toolchain readiness only) |

---

## 4. Independence and E4 Alignment

| Question | Answer |
|----------|--------|
| Was owner-side reproduction performed? | **Yes** (clone/inspect + C1 + C2A + C2B-1) |
| Was independent third-party witness performed? | **No** |
| Does this verdict claim E4 for the target? | **No** |
| Does this verdict claim E5 external audit? | **No** |

---

## 5. Residual Risks and Limitations

| ID | Risk / limitation | Severity | Accepted? |
|----|-------------------|----------|-----------|
| L-001 | No signed tags / publisher tree checksums | medium | Yes |
| L-002 | Build untested | high for build claims | Yes — NOT_STARTED |
| L-003 | Windows source-build best-effort | medium | Yes |
| L-006 | Windows host missing rust/DotSlash/MSVC | high | C-015 BLOCKED |
| L-009 | Login-shell PATH omits rustc unless PATH set | low | Documented; use direct or PATH export |
| L-010 | DotSlash/packages/deps not installed in container | medium | C2B-2+ |
| L-004 | Package author ≠ independent witness | high for E4 | Yes |

---

## 6. Promotion / Use Recommendations

| Use case | Recommended? | Condition |
|----------|--------------|-----------|
| Cite as independently verified | **No** | |
| Cite pinned source + container image digest | Conditional | Quote digests; not “fully verified product” |
| Depend on in production | **No** | |
| Next technical step | Yes | C2B-2 isolation: RO mount, packages/DotSlash, deps; then C2B-3 cargo check if authorized |

---

## 7. Mandatory Evidence Boundaries

### 7.1 What was observed

```text
Pin intact; Docker server 29.4.3 linux/amd64 WSL2; image pull + RepoDigest match;
rustc/cargo 1.92.0 direct in image; bash -lc rustc not found (PATH only);
no Grok Build cargo, no DotSlash, no packages, no auth.
```

### 7.2 What was not observed

```text
Build logs for Grok Build; functional runtime; witness; signed release artifacts;
successful login-shell rustc without PATH fix.
```

### 7.3 What was not tested

```text
cargo check/build/test/run on Grok Build; DotSlash/protoc; full native deps;
product authentication; security.
```

### 7.4 What is not claimed

```text
Build or functional reproducibility; overall PASS; Windows host ready;
that cargo check will succeed after C2B-2.
```

### 7.5 Reproduction class

| Class | Selected |
|-------|----------|
| Owner-side reproduction | ☑ |
| Independent reproduction | ☐ |
| Neither | ☐ |

---

## 8. What This Verdict Proves

- C2B-1: pinned image present locally with matching RepoDigest; Rust 1.92.0 available via direct rustc/cargo in that image.
- Windows path still BLOCKED; overall package still PARTIAL.

## 9. What This Verdict Does NOT Prove

- Grok Build builds or runs correctly
- Independent verification (E4)
- Security or operational readiness

## 10. Sign-Off

| Role | Name / handle | Verdict acknowledged | Date |
|------|---------------|----------------------|------|
| Owner-side evaluator | Weaver Forge documentation package author | Yes — overall `PARTIAL` | 2026-07-18 |
| Independent witness | *unassigned* | | |

---

**Witness is attestation, not authority.**
