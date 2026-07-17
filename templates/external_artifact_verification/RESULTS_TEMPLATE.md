# Results — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Results status | `NOT_STARTED` |
| Compiled by | |
| Role | Owner-side / Independent witness |
| Compilation date | `YYYY-MM-DD` |
| Linked reproduction run ID | |
| Linked claim register | `CLAIM_REGISTER.md` |

Results must cite evidence. Do not mark `PASS` without logs, receipts, or other preserved artifacts.

---

## 1. Run Metadata

| Field | Value |
|-------|-------|
| Source identity reference | commit / tag / hash — or `NOT_STARTED` |
| Environment reference | `ENVIRONMENT.md` |
| Reproduction reference | `REPRODUCTION.md` |
| Execution authorized? | Yes / No |
| Execution performed? | No / Yes |

## 2. Per-Claim Results

| Claim ID | Exact claim (short) | Evidence class | Expected (documented) | Actual | Status | Evidence pointer |
|----------|---------------------|----------------|-----------------------|--------|--------|------------------|
| C-001 | | | | `NOT_STARTED` | `NOT_STARTED` | |
| C-002 | | | | `NOT_STARTED` | `NOT_STARTED` | |

## 3. Build Results

| Check | Status | Evidence |
|-------|--------|----------|
| Dependencies installed as documented | `NOT_STARTED` | |
| Build command completed | `NOT_STARTED` | |
| Build artifacts produced | `NOT_STARTED` | |
| Build reproducibility (repeat run) | `NOT_STARTED` / `NOT_APPLICABLE` | |

## 4. Test Results

| Suite / check | Documented command | Exit code | Status | Log path |
|---------------|--------------------|-----------|--------|----------|
| | | | `NOT_STARTED` | |

## 5. Runtime / Functional Observations

| Observation ID | What was observed | Method | Status | Evidence |
|----------------|-------------------|--------|--------|----------|
| O-001 | | | `NOT_STARTED` | |

## 6. Integrity and Identity Results

| Check | Status | Evidence |
|-------|--------|----------|
| Canonical URL resolved | `NOT_STARTED` | |
| Full commit / version recorded | `NOT_STARTED` | |
| Hash verified | `NOT_STARTED` / `NOT_APPLICABLE` | |
| Signature verified | `NOT_STARTED` / `NOT_APPLICABLE` | |

## 7. Failures, Warnings, and Anomalies

| ID | Severity | Description | Linked step / claim | Status |
|----|----------|-------------|---------------------|--------|
| A-001 | low / medium / high | | | open |

## 8. Blockers

| Block ID | Description | Blocks which claims / axes | Status |
|----------|-------------|----------------------------|--------|
| BK-001 | | | `BLOCKED` |

## 9. Aggregate Counts

| Status | Claims | Build checks | Test checks |
|--------|-------:|-------------:|------------:|
| `NOT_STARTED` | | | |
| `BLOCKED` | | | |
| `PASS` | | | |
| `PARTIAL` | | | |
| `FAIL` | | | |
| `NOT_APPLICABLE` | | | |

## 10. Owner-Side vs Independent Witness

| Result class | Status | Notes |
|--------------|--------|-------|
| Owner-side reproduction results | `NOT_STARTED` | |
| Independent witness results | `NOT_STARTED` | Required for E4-class attestation |

Do not merge these rows. A green owner-side row does not fill the witness row.

| Field | Value |
|-------|-------|
| Reproduction class for **this** results file | Owner-side reproduction / Independent reproduction / Neither (no run) |
| Operator is uninvolved third party? | Yes / No / N/A |

## 11. Mandatory Evidence Boundaries

Every results file must complete all five subsections. Empty implied success is forbidden.

### 11.1 What was observed

```text
[Direct observations only. If none: "Nothing observed — no execution performed."]
```

### 11.2 What was not observed

```text
[Explicit list: e.g. live repo tree, build logs, test output, runtime behavior, witness attestation.]
```

### 11.3 What was not tested

```text
[Explicit list of unrun checks, suites, scenarios, platforms.]
```

### 11.4 What is not claimed

```text
[Non-claims: authenticity beyond recorded evidence, security, production readiness, E4/E5, etc.]
```

### 11.5 Reproduction class

| Class | Selected |
|-------|----------|
| Owner-side reproduction | ☐ |
| Independent reproduction (uninvolved third-party witness) | ☐ |
| Neither — documentation / planning only; no reproduction run | ☐ |

## 12. What These Results Prove

```text
[Strictly limited to evidenced outcomes.]
```

## 13. What These Results Do NOT Prove

- Unrun checks
- Security review completion
- Production or operational readiness
- Independent witness confirmation (unless witness section is complete)
- Claims outside the register
- That the package templates alone verified the target

## Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial results shell | |

---

**No hype without evidence.**
