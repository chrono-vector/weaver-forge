# Witness Handoff — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Handoff status | `NOT_STARTED` |
| Prepared by | |
| Preparer role | Owner-side package author (not the witness) |
| Prepared date | `YYYY-MM-DD` |
| Verification-plan version / date | (path + date or git blob of `VERIFICATION_PLAN.md`) |
| Independent witness | *unassigned* |
| Witness completion status | `NOT_STARTED` |

This document packages everything an **uninvolved third party** needs to attempt independent verification. Preparing this handoff does **not** complete independent verification.

---

## 1. Independence Requirements

The witness must:

- Have **no authorship** on the external target's commits or releases under review (unless reviewing only public claims as an external party with disclosed relationship)
- Have **no authorship** on this verification package's substantive claims being attested
- Not be the same person/operator as the owner-side reproducer for the run they are witnessing
- Record an explicit independence declaration (section 9)
- Claim only what they directly observed

**Contributor ≠ Witness.**
**Owner-side reproduction ≠ Independent witness.**
**This handoff ≠ E4 completion.**

---

## 2. Package Inventory

| Item | Path / URL | Present? |
|------|------------|----------|
| Verification plan | `VERIFICATION_PLAN.md` | Yes / No |
| Source identity | `SOURCE_IDENTITY.md` | Yes / No |
| Claim register | `CLAIM_REGISTER.md` | Yes / No |
| Environment record | `ENVIRONMENT.md` | Yes / No |
| Reproduction procedure | `REPRODUCTION.md` | Yes / No |
| Results (owner-side, if any) | `RESULTS.md` | Yes / No |
| Current verdict (owner-side) | `VERDICT.md` | Yes / No |
| Official target documentation | (URL) | Yes / No |

---

## 3. Pinned Source Reference

**Required before witness execution.** Empty pins → handoff is `BLOCKED`.

| Field | Value |
|-------|-------|
| Canonical repository or release URL | |
| Source-control owner | |
| Branch (if any) | |
| Tag (if any) | |
| **Full commit ID** (40-char if git) | |
| Docs revision used for procedure | path + commit or URL + date |
| Pin freeze date | |
| Pin status | `NOT_STARTED` / frozen / `BLOCKED` |

Do not invent commit IDs. If unknown, leave blank and set pin status to `NOT_STARTED` or `BLOCKED`.

---

## 4. Artifact Hash

| Field | Value |
|-------|-------|
| Artifact type | git tree / release tarball / wheel / container / other |
| Artifact filename (if file) | |
| Size (bytes) | |
| Hash algorithm | SHA-256 / SHA-512 / git tree SHA / other |
| **Artifact hash value** | |
| Hash source | self-computed after acquire / publisher-published / unknown |
| Signature (if any) | |
| Hash status | `NOT_STARTED` / recorded / verified / `NOT_APPLICABLE` / `BLOCKED` |

For pure git reviews, record full commit ID in section 3 and optionally `git rev-parse HEAD^{tree}` or archive hash of `git archive` output. Prefer publisher-published hashes when available; still recompute after acquire when feasible.

---

## 5. Environment Prerequisites

Minimum environment the witness must prepare **before** commands. Align with `ENVIRONMENT.md` when filled.

| Prerequisite | Required value / constraint | Status |
|--------------|----------------------------|--------|
| OS | | `NOT_STARTED` |
| Shell | | `NOT_STARTED` |
| CPU / GPU | | `NOT_STARTED` / `NOT_APPLICABLE` |
| Language / runtime | | `NOT_STARTED` |
| Package managers | | `NOT_STARTED` |
| Dependency lock identity | | `NOT_STARTED` / `NOT_APPLICABLE` |
| Network | | `NOT_STARTED` |
| Credentials / auth boundary | public-only preferred / … | `NOT_STARTED` |
| Sandbox / isolation | | `NOT_STARTED` |
| Precision mode / seeds | | `NOT_STARTED` / `NOT_APPLICABLE` |

```text
# Prerequisite check commands (exact), if known:
```

---

## 6. Exact Verification Commands

Ordered, copy-pasteable commands. Do not leave implicit steps.

| Step | Working directory | Exact command | Purpose | Linked claim IDs |
|------|-------------------|---------------|---------|------------------|
| 1 | | | | |
| 2 | | | | |

```text
# Full script form (preferred when multi-step):
# Leave empty or marked NOT_STARTED until procedure is frozen from primary sources.
```

Command set status: `NOT_STARTED` / frozen / `BLOCKED`

---

## 7. Expected Machine-Readable Outputs

Document only outputs grounded in official docs or prior measured baselines. **Never invent.**

| Step / claim | Output channel | Expected pattern or value | Machine-readable form | Source of expectation |
|--------------|----------------|---------------------------|----------------------|------------------------|
| | stdout / stderr / file / exit code | | regex / JSON field / exact string / exit `0` | docs path or `unknown` |

If unknown:

```text
Expected outputs: unknown — not yet documented from primary sources. Status: NOT_STARTED
```

---

## 8. Tolerances

| Check | Metric | Tolerance / acceptance band | Notes |
|-------|--------|-----------------------------|-------|
| Exit codes | per step | exact match unless docs allow otherwise | |
| Timing | wall clock | | `NOT_APPLICABLE` if not claimed |
| Numeric outputs | | absolute / relative / `NOT_APPLICABLE` | |
| Log noise | warnings | allowed / disallowed | list known benign warnings |
| Nondeterminism | seeds | fixed seed required? | |

Default: **zero invented tolerance**. If docs do not define a band, require exact documented match or mark `NOT_STARTED`.

---

## 9. Known Limitations

| ID | Limitation | Impact on witness | Status |
|----|------------|-------------------|--------|
| KL-001 | | | open |

Examples: credential-gated steps, flaky network, platform-only docs, shallow-clone failure modes, non-reproducible timestamps.

---

## 10. Independence Declaration

### 10.1 Requirements (pre-run)

Witness confirms before executing:

| Check | Yes / No |
|-------|----------|
| No authorship on reviewed target commits/releases under review | |
| No authorship on owner-side package claims being attested | |
| Not the owner-side reproducer for this run | |
| Will claim only direct observations | |

### 10.2 Declaration text (post-run)

```text
I am uninvolved in the authorship of the reviewed artifact and of the owner-side
verification package claims I am attesting. I claim only what I directly observed.
I used the pinned source reference and artifact hash recorded in this handoff
(or I recorded BLOCKED if pins were missing).
```

| Field | Value |
|-------|-------|
| Witness name / handle | |
| Date | |
| Declaration accepted as true? | Yes / No |
| If No, stop and do not claim independent reproduction | |

---

## 11. Result-Submission Procedure

| Field | Value |
|-------|-------|
| Submission channel | pull request / sealed archive / agreed path |
| Target path or PR convention | e.g. `external_verifications/<slug>/` update or `witness-reviews/` |
| Required artifacts to attach | completed handoff, environment record, command transcripts, exit codes |
| Naming convention | |
| Reviewer / receiver | |
| Confidentiality / redaction rules | redact secrets; preserve exit codes and non-secret logs |

### Submission checklist

- [ ] Pinned source reference recorded (section 3)
- [ ] Artifact hash recorded or `NOT_APPLICABLE` justified (section 4)
- [ ] Environment prerequisites captured (section 5 + `ENVIRONMENT.md`)
- [ ] Exact commands and actual outputs preserved
- [ ] Expected vs actual compared within tolerances (sections 7–8)
- [ ] Known limitations acknowledged (section 9)
- [ ] Independence declaration completed (section 10)
- [ ] Per-claim statuses filled (section 12)
- [ ] Evidence boundaries completed (section 13)
- [ ] Conclusion selected (section 14)

### After submission

Owner-side maintainers may file a Weaver Forge receipt referencing this witness package (see framework README **Receipt Compatibility**). Submitting a witness form is attestation, not project authority.

---

## 12. Witness Results

| Claim ID or step | Observed result | Status | Evidence pointer |
|------------------|-----------------|--------|------------------|
| | | `NOT_STARTED` | |

| Axis | Witness verdict |
|------|-----------------|
| Source authenticity | `NOT_STARTED` |
| Artifact integrity | `NOT_STARTED` |
| Build reproducibility | `NOT_STARTED` |
| Functional reproducibility | `NOT_STARTED` |
| Claim verification | `NOT_STARTED` |
| Security review | `NOT_STARTED` / `NOT_APPLICABLE` |
| Independent-witness status | `NOT_STARTED` |
| Operational readiness | `NOT_STARTED` / `NOT_APPLICABLE` |

---

## 13. Mandatory Evidence Boundaries (Witness)

### 13.1 What was observed

```text
```

### 13.2 What was not observed

```text
```

### 13.3 What was not tested

```text
```

### 13.4 What is not claimed

```text
- Production readiness
- External audit (E5)
- Correctness beyond executed checks
- Owner-side results not re-run by the witness
```

### 13.5 Reproduction class

| Class | Selected |
|-------|----------|
| Independent reproduction (uninvolved third-party witness) | ☐ (required for E4-class claim) |
| Owner-side reproduction | ☐ (invalid for this handoff’s witness conclusion) |
| Neither / blocked | ☐ |

---

## 14. Witness Conclusion

Choose **one**:

| Conclusion | Selected |
|------------|----------|
| `NOT_STARTED` | ☐ |
| `BLOCKED` | ☐ |
| Reproduced (`PASS`) | ☐ |
| Partially reproduced (`PARTIAL`) | ☐ |
| Not reproduced (`FAIL`) | ☐ |
| `NOT_APPLICABLE` | ☐ |

### What the witness confirms

```text
[Only direct observations.]
```

### What the witness does NOT confirm

```text
- Production readiness
- External audit (E5)
- Correctness beyond executed checks
- Owner-side results not re-run by the witness
- Any claim outside witness scope
```

---

## 15. What This Handoff Proves

- That a package was prepared for independent review (when fields are complete enough to attempt)
- Nothing about target correctness until a witness completes independence, commands, and conclusion with evidence

## 16. What This Handoff Does NOT Prove

- That independent verification occurred
- That E4 is complete for the target
- That owner-side results are correct
- Security or operational readiness
- Authority beyond attestation

## Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial handoff shell | |

---

**E4 is not complete because this handoff exists. E4 requires execution by an uninvolved third party.**
