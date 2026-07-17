# Claim Register — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Register status | `NOT_STARTED` |
| Maintained by | |
| Role | Owner-side (not independent witness) |
| Last updated | `YYYY-MM-DD` |
| Independent witness evaluation of claims | `NOT_STARTED` |

---

## Rules

1. Record the **exact claim** text; do not paraphrase away meaning.
2. Every claim needs an **evidence class**, **verification method**, and **acceptance criteria**.
3. `expected output` may be filled only from documented sources or measured baselines — never invented.
4. `actual result` stays empty or `NOT_STARTED` until a recorded run exists.
5. Status must be one of: `NOT_STARTED`, `BLOCKED`, `PASS`, `PARTIAL`, `FAIL`, `NOT_APPLICABLE`.
6. Always complete **limitations** and **what the result does not establish**.
7. Owner-side results are not `independent_witness_result` unless produced by an uninvolved witness.

### Evidence classes (use exactly)

- `publisher_statement`
- `source_code_observation`
- `build_result`
- `test_result`
- `runtime_observation`
- `analytical_claim`
- `simulation_result`
- `conceptual_mapping`
- `unverified_hypothesis`
- `independent_witness_result`

---

## Claim Index

| Claim ID | Short title | Evidence class | Status |
|----------|-------------|----------------|--------|
| C-001 | | | `NOT_STARTED` |
| C-002 | | | `NOT_STARTED` |

---

## Claim Records

Copy the block below for each claim.

### C-001 — [short title]

| Field | Value |
|-------|-------|
| Claim ID | `C-001` |
| Exact claim | |
| Source of claim | (URL, file path, commit, README section, paper section, release notes) |
| Evidence class | |
| Verification method | |
| Acceptance criteria | |
| Expected output | (documented source or `unknown — not yet documented`) |
| Actual result | `NOT_STARTED` |
| Status | `NOT_STARTED` |
| Operator role for this result | Owner-side / Independent witness / Unassigned |
| Evidence pointers | (log paths, receipt IDs, screenshots — none until collected) |
| Limitations | |
| What the result does not establish | |

### C-002 — [short title]

| Field | Value |
|-------|-------|
| Claim ID | `C-002` |
| Exact claim | |
| Source of claim | |
| Evidence class | |
| Verification method | |
| Acceptance criteria | |
| Expected output | |
| Actual result | `NOT_STARTED` |
| Status | `NOT_STARTED` |
| Operator role for this result | Owner-side / Independent witness / Unassigned |
| Evidence pointers | |
| Limitations | |
| What the result does not establish | |

---

## Aggregate Claim Status

| Status | Count |
|--------|------:|
| `NOT_STARTED` | |
| `BLOCKED` | |
| `PASS` | |
| `PARTIAL` | |
| `FAIL` | |
| `NOT_APPLICABLE` | |
| **Total** | |

Do not compute a single "overall PASS" from partial data.

---

## Claims Explicitly Not Registered

List tempting claims that were considered and excluded, so they are not smuggled into the verdict later.

| Deferred claim | Reason excluded |
|----------------|-----------------|
| | |

---

## What This Register Proves

```text
[That claims were enumerated with methods and boundaries — not that they are true.]
```

## What This Register Does NOT Prove

- That any claim passed verification
- Independent witness confirmation
- Security review
- Completeness of all possible claims about the target
- Operational readiness

## Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial register shell | |

---

**No commit. No claim. No receipt. No authority.**
