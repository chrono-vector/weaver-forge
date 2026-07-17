# Source Identity — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Project | **Grok Build** |
| Claimed publisher | **xAI** |
| Claimed canonical repository | **https://github.com/xai-org/grok-build** |
| Current verification state | **`NOT_STARTED`** |
| Identity status | `NOT_STARTED` (intake designation only; no live verification) |
| Recorded by | Weaver Forge documentation package author |
| Role | Owner-side planner (not independent witness) |
| Record date | `2026-07-17` |
| Independent verification of identity | `NOT_STARTED` |

**Intake rule:** License, commit, build requirements, claims, and expected outputs remain **subject to primary-source inspection and pinning**. Do not invent hashes, commit IDs, sizes, or signatures. Unknown fields stay empty or `unknown` with status `NOT_STARTED` / `BLOCKED`. No execution has occurred. No independent verification is claimed.

---

## 1. Canonical Publisher

| Field | Value |
|-------|-------|
| Canonical publisher name | xAI (designated from org path `xai-org`; not re-verified live in this pass) |
| Publisher type | company |
| Official website | *not recorded in this pass* |
| Publisher confidence | **low–medium (provisional)** |
| Confidence basis | Package designates GitHub org path `xai-org` and URL provided for this verification target; no separate publisher-site confirmation performed here |

## 2. Canonical Repository or Release URL

| Field | Value |
|-------|-------|
| Canonical repository URL | https://github.com/xai-org/grok-build |
| Canonical release / download URL | *unknown — `NOT_STARTED`* |
| Mirror URLs (if any) | *none recorded* |
| Docs / project page URL | *unknown — `NOT_STARTED`* |
| How canonicity was established | Designated by Weaver Forge verification plan for this package; **not** established by live org audit in this pass |

## 3. Source-Control Owner

| Field | Value |
|-------|-------|
| Hosting platform | GitHub |
| Organization or user | `xai-org` (path segment of designated URL) |
| Repository name | `grok-build` |
| Visibility | *unknown until fetch — expected public; `NOT_STARTED`* |
| Default branch (as advertised) | *unknown — `NOT_STARTED`* |
| Owner verification notes | No clone, API, or browser verification recorded in this documentation-only package |

## 4. Artifact Acquisition Method

| Field | Value |
|-------|-------|
| Planned acquisition method | full `git clone` (future; when authorized) |
| Exact acquisition command (if known) | `git clone https://github.com/xai-org/grok-build.git` (planned only — **not executed**) |
| Acquisition performed? | **No** |
| Acquisition date | |
| Acquisition location (path) | |
| Network conditions | not applicable (no acquisition) |
| Status | `NOT_STARTED` / blocked by plan authorization |

## 5. License

| Field | Value |
|-------|-------|
| License name / SPDX ID | *unknown — `NOT_STARTED`* |
| License file path in artifact | *unknown* |
| License URL | *unknown* |
| License status | `NOT_STARTED` |
| Restrictions relevant to verification | *unknown until license observed* |

## 6. Version Identity

| Field | Value |
|-------|-------|
| Advertised version | *unknown — not invented* |
| Tag | *unknown — not invented* |
| Branch | *unknown — not invented* |
| Full commit ID (40-char where git) | *unknown — not invented* |
| Short commit ID | *unknown — not invented* |
| Commit ID verification method | not yet verified |
| Release date (if any) | *unknown* |
| Version status | `NOT_STARTED` |

**Rule:** Prefer full immutable references. Do not treat floating tags or `latest` as frozen identity.

## 7. Artifact File Identity (when applicable)

No separate archive acquired. Git identity not frozen.

| Field | Artifact 1 |
|-------|------------|
| Filename | *none acquired* |
| Size (bytes) | |
| Size source | unknown |
| Cryptographic hash algorithm | |
| Cryptographic hash value | |
| Hash source | unknown |
| Hash match status | `NOT_APPLICABLE` (no archive) / version pin `NOT_STARTED` |

## 8. Signature and Signing Keys (when available)

| Field | Value |
|-------|-------|
| Signature present? | Unknown |
| Signature type | none recorded |
| Signature file or URL | |
| Signing key ID / fingerprint | |
| Key provenance | |
| Verification command | |
| Verification status | `NOT_STARTED` |

## 9. Hash or Immutable Reference Summary

| Reference type | Value | Status |
|----------------|-------|--------|
| Full commit ID | *unknown — not invented* | `NOT_STARTED` |
| Content hash of archive | | `NOT_APPLICABLE` |
| Container digest | | `NOT_APPLICABLE` / `NOT_STARTED` if later relevant |
| Other immutable ref | | `NOT_STARTED` |

## 10. Source Confidence

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Publisher legitimacy | unknown | Not audited in this pass |
| URL canonicity | provisional | Designated URL only |
| Version immutability | unknown | No pin recorded |
| Integrity reference strength | none yet | No hash/signature |
| Overall source confidence | **low (documentation designation only)** | Must not be treated as verified authenticity |

## 11. Unresolved Identity Risks

| Risk ID | Description | Severity | Status |
|---------|-------------|----------|--------|
| IR-001 | No full commit ID or tag freeze; floating `main` or default branch could move | high | open |
| IR-002 | Canonicity not confirmed against xAI official site or signed release notes in this pass | high | open |
| IR-003 | License unknown; redistribution/verification constraints unknown | medium | open |
| IR-004 | No signature or published hash recorded | medium | open |
| IR-005 | Fork or naming confusion possible until org/repo identity is observed live | medium | open |
| IR-006 | Acquisition and inspection blocked by current authorization | high | open (`BLOCKED`) |

## 12. What This Identity Record Proves

- That this package **designates** https://github.com/xai-org/grok-build as the intended canonical repository URL for future verification work.
- That version, hash, license, and signature fields are intentionally unfilled rather than fabricated.

## 13. What This Identity Record Does NOT Prove

- That the repository was fetched, browsed, or confirmed live in this pass
- That `xai-org` ownership was independently audited
- That any commit, tag, release, or binary is authentic
- That the artifact is free of malware or supply-chain compromise
- That publisher claims are true
- That the build is reproducible
- That an independent witness confirmed identity
- Security or operational readiness

## 14. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Initial identity shell; designated URL only; no invented pins | Weaver Forge documentation package author |

---

**Evidence before authority.**
