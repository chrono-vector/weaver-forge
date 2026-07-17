# Source Identity — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Identity status | `NOT_STARTED` |
| Recorded by | |
| Role | Owner-side / Independent witness |
| Record date | `YYYY-MM-DD` |
| Independent verification of identity | `NOT_STARTED` |

Do not invent hashes, commit IDs, sizes, or signatures. Unknown fields stay empty or `unknown` with status `NOT_STARTED` / `BLOCKED`.

---

## 1. Canonical Publisher

| Field | Value |
|-------|-------|
| Canonical publisher name | |
| Publisher type | company / foundation / academic group / individual / other |
| Official website | |
| Publisher confidence | high / medium / low / unknown |
| Confidence basis | |

## 2. Canonical Repository or Release URL

| Field | Value |
|-------|-------|
| Canonical repository URL | |
| Canonical release / download URL | |
| Mirror URLs (if any) | |
| Docs / project page URL | |
| How canonicity was established | publisher site / org profile / signed release notes / other |

## 3. Source-Control Owner

| Field | Value |
|-------|-------|
| Hosting platform | GitHub / GitLab / other |
| Organization or user | |
| Repository name | |
| Visibility | public / private / unknown |
| Default branch (as advertised) | |
| Owner verification notes | |

## 4. Artifact Acquisition Method

| Field | Value |
|-------|-------|
| Planned acquisition method | git clone / release tarball / pip / container / other |
| Exact acquisition command (if known) | |
| Acquisition performed? | No / Yes |
| Acquisition date | |
| Acquisition location (path) | |
| Network conditions | online / offline / restricted |
| Status | `NOT_STARTED` / `PASS` / `FAIL` / `BLOCKED` |

## 5. License

| Field | Value |
|-------|-------|
| License name / SPDX ID | |
| License file path in artifact | |
| License URL | |
| License status | `NOT_STARTED` / confirmed / missing / unclear |
| Restrictions relevant to verification | |

## 6. Version Identity

| Field | Value |
|-------|-------|
| Advertised version | |
| Tag | |
| Branch | |
| Full commit ID (40-char where git) | |
| Short commit ID | |
| Commit ID verification method | `git rev-parse` / release page / not yet verified |
| Release date (if any) | |
| Version status | `NOT_STARTED` |

**Rule:** Prefer full immutable references. Do not treat floating tags or `latest` as frozen identity.

## 7. Artifact File Identity (when applicable)

Complete one row per acquired file or archive. Leave blank if identity is git-only and no separate archive was acquired.

| Field | Artifact 1 | Artifact 2 |
|-------|------------|------------|
| Filename | | |
| Size (bytes) | | |
| Size source | measured / publisher-stated / unknown | |
| Cryptographic hash algorithm | SHA-256 / SHA-512 / other | |
| Cryptographic hash value | | |
| Hash source | self-computed / publisher-published / unknown | |
| Hash match status | `NOT_STARTED` / `PASS` / `FAIL` / `NOT_APPLICABLE` | |

## 8. Signature and Signing Keys (when available)

| Field | Value |
|-------|-------|
| Signature present? | Yes / No / Unknown |
| Signature type | GPG / Sigstore / cosign / other / none |
| Signature file or URL | |
| Signing key ID / fingerprint | |
| Key provenance | |
| Verification command | |
| Verification status | `NOT_STARTED` / `PASS` / `FAIL` / `NOT_APPLICABLE` / `BLOCKED` |

## 9. Hash or Immutable Reference Summary

| Reference type | Value | Status |
|----------------|-------|--------|
| Full commit ID | | `NOT_STARTED` |
| Content hash of archive | | `NOT_STARTED` / `NOT_APPLICABLE` |
| Container digest | | `NOT_STARTED` / `NOT_APPLICABLE` |
| Other immutable ref | | `NOT_STARTED` / `NOT_APPLICABLE` |

## 10. Source Confidence

| Dimension | Rating | Notes |
|-----------|--------|-------|
| Publisher legitimacy | high / medium / low / unknown | |
| URL canonicity | high / medium / low / unknown | |
| Version immutability | high / medium / low / unknown | |
| Integrity reference strength | high / medium / low / unknown | |
| Overall source confidence | high / medium / low / unknown | |

## 11. Unresolved Identity Risks

| Risk ID | Description | Severity | Status |
|---------|-------------|----------|--------|
| IR-001 | | low / medium / high | open / mitigated / accepted |

Examples of risks to consider (delete if not applicable):

- Tag moved after recording
- Shallow clone used (history incomplete)
- Hash published only on unauthenticated page
- Fork mistaken for canonical repository
- License missing or ambiguous
- Signed release not available

## 12. What This Identity Record Proves

```text
[Only what was directly recorded with evidence — e.g. "URL listed as canonical in plan."]
```

## 13. What This Identity Record Does NOT Prove

- That the artifact is free of malware or supply-chain compromise
- That the publisher's claims are true
- That the build is reproducible
- That an independent witness confirmed identity
- That any later checkout matches this record if version fields are still empty
- Security or operational readiness

## 14. Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial identity shell | |

---

**Evidence before authority.**
