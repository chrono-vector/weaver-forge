# Verdict — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Verdict status | `NOT_STARTED` |
| Issued by | |
| Role | Owner-side evaluator (not independent witness unless stated) |
| Verdict date | `YYYY-MM-DD` |
| Source identity pin | commit / tag / hash or `NOT_STARTED` |
| Linked results | `RESULTS.md` |
| Linked witness handoff | `WITNESS_HANDOFF.md` |

---

## Allowed Verdict Values

Use only:

- `PASS`
- `PARTIAL`
- `FAIL`
- `BLOCKED`
- `NOT_APPLICABLE`
- `NOT_STARTED`

No other labels. No implied pass from documentation completeness.

---

## 1. Multi-Axis Verdict Table

Each axis is judged **separately**. Do not collapse into a single marketing status.

| Axis | Verdict | Summary of evidence | What this axis does not establish |
|------|---------|---------------------|-----------------------------------|
| Source authenticity | `NOT_STARTED` | | |
| Artifact integrity | `NOT_STARTED` | | |
| Build reproducibility | `NOT_STARTED` | | |
| Functional reproducibility | `NOT_STARTED` | | |
| Claim verification | `NOT_STARTED` | | |
| Security review | `NOT_STARTED` | | |
| Independent-witness status | `NOT_STARTED` | | |
| Operational readiness | `NOT_STARTED` | | |

### Axis definitions (normative)

| Axis | Means | Does not mean |
|------|-------|---------------|
| Source authenticity | Canonical publisher/URL/owner identity is established as recorded | Supplier is trustworthy forever; code is safe |
| Artifact integrity | Hash / signature / immutable ref matches recorded expectation | Artifact is free of vulnerabilities |
| Build reproducibility | Documented build was repeated with recorded outcome | Bit-identical reproducible builds across all platforms |
| Functional reproducibility | Documented functional checks behaved as acceptance criteria require | Production SLOs; all features work |
| Claim verification | Registered claims evaluated against acceptance criteria | Unregistered claims; marketing pages not in register |
| Security review | Explicit security verification steps in scope were performed | Full audit; certification; exploit absence |
| Independent-witness status | Uninvolved third party completed witness procedure | Owner-side success; self-audit |
| Operational readiness | Explicit ops criteria in scope were met | Blanket production approval |

---

## 2. Overall Package Verdict

| Field | Value |
|-------|-------|
| Overall verdict | `NOT_STARTED` |
| Overall verdict rule used | See below |

### Overall verdict rules (conservative)

1. If any in-scope axis required for the package goal is `FAIL`, overall is `FAIL` or `PARTIAL` (justify).
2. If required axes are `BLOCKED`, overall is `BLOCKED` until unblocked.
3. If no execution has occurred, overall remains `NOT_STARTED` even if templates are complete.
4. Overall may be `PARTIAL` when some axes pass and others remain open, with limitations listed.
5. Overall `PASS` requires every **in-scope** axis to be `PASS` or justified `NOT_APPLICABLE`, **and** must not claim independent-witness `PASS` without an uninvolved witness record.
6. Documentation-only packages must not issue overall `PASS` for build, functional, claim, security, witness, or operational axes.

### Overall justification

```text
[Required when overall ≠ NOT_STARTED]
```

---

## 3. Claim Verification Rollup

| Claim ID | Status | Notes |
|----------|--------|-------|
| C-001 | `NOT_STARTED` | |
| C-002 | `NOT_STARTED` | |

---

## 4. Independence and E4 Alignment

| Question | Answer |
|----------|--------|
| Was owner-side reproduction performed? | No / Yes / `NOT_STARTED` |
| Was independent third-party witness performed? | No / Yes / `NOT_STARTED` |
| Does this verdict claim E4 for the target? | **No** (default) / Yes only with witness record |
| Does this verdict claim E5 external audit? | **No** (default) |

**Reminder:** Completing templates is not E4. Owner-side success is not E4. E4 requires an uninvolved third party and a witness record.

---

## 5. Residual Risks and Limitations

| ID | Risk / limitation | Severity | Accepted? |
|----|-------------------|----------|-----------|
| L-001 | | low / medium / high | Yes / No / Pending |

---

## 6. Promotion / Use Recommendations

Recommendations only — not authority.

| Use case | Recommended? | Condition |
|----------|--------------|-----------|
| Cite as independently verified | No / Conditional / Yes | |
| Use as internal research reference | No / Conditional / Yes | |
| Depend on in production | No / Conditional / Yes | |
| Request independent witness | Yes / No | |

---

## 7. Mandatory Evidence Boundaries

Every verdict file must complete all five subsections.

### 7.1 What was observed

```text
[Direct observations supporting any non-NOT_STARTED axis. If none: state none.]
```

### 7.2 What was not observed

```text
[Identity pins, hashes, build/test/runtime evidence not seen, witness record, etc.]
```

### 7.3 What was not tested

```text
[Axes and claims left unexecuted.]
```

### 7.4 What is not claimed

```text
[Independent verification, E4/E5, security certification, production readiness, etc.]
```

### 7.5 Reproduction class

| Class | Selected |
|-------|----------|
| Owner-side reproduction | ☐ |
| Independent reproduction (uninvolved third-party witness) | ☐ |
| Neither — documentation / planning only; no reproduction run | ☐ |

## 8. What This Verdict Proves

```text
```

## 9. What This Verdict Does NOT Prove

- Anything marked `NOT_STARTED`, `BLOCKED`, or `NOT_APPLICABLE`
- Security beyond axes explicitly reviewed
- Independent verification without witness axis `PASS`
- Operational readiness without that axis `PASS`
- Authority beyond recorded evidence
- That Weaver Forge E4/E5 is complete for this repository

## 10. Sign-Off

| Role | Name / handle | Verdict acknowledged | Date |
|------|---------------|----------------------|------|
| Owner-side evaluator | | Yes / No | |
| Independent witness | *unassigned* | | |

---

**Witness is attestation, not authority.**
