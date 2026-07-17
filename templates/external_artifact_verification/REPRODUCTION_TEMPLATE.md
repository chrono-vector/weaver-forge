# Reproduction Record — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Reproduction status | `NOT_STARTED` |
| Run ID | `run-YYYYMMDD-001` |
| Operator | |
| Role | **Owner-side reproduction** / **Independent witness** |
| Independence statement | Operator is / is not uninvolved with target authorship and package authorship |
| Start time (UTC or local + offset) | |
| End time | |
| Linked environment record | `ENVIRONMENT.md` |
| Linked source identity | `SOURCE_IDENTITY.md` |

**Critical distinction**

- **Owner-side reproduction:** Operator may be package author or project member. Can support E2/E3 for the external target. **Does not complete E4.**
- **Independent third-party witness:** Uninvolved party following `WITNESS_HANDOFF.md`. Required for E4-class claims.

---

## 1. Official Procedure Reference

| Field | Value |
|-------|-------|
| Official docs URL or path | |
| Official procedure title / section | |
| Procedure revision (commit / date) | |
| Procedure status at run time | followed / partially followed / unavailable |

## 2. Working Directory

| Field | Value |
|-------|-------|
| Repository / artifact root | |
| Shell working directory per phase | |
| Path normalization notes (Windows vs POSIX) | |

## 3. Command Sequence

Record **exact** commands in order. Do not omit failing steps. Do not invent exit codes.

| Step | Working directory | Command | Exit code | Started | Ended | Status | Notes |
|------|-------------------|---------|-----------|---------|-------|--------|-------|
| 1 | | | | | | `NOT_STARTED` | |
| 2 | | | | | | `NOT_STARTED` | |

### Raw command log

```text
# Paste or point to transcript. Leave empty while NOT_STARTED.
```

## 4. Stdout / Stderr Preservation

| Step | stdout path | stderr path | Combined transcript path | Status |
|------|-------------|-------------|--------------------------|--------|
| 1 | | | | `NOT_STARTED` |

**Rule:** Prefer preserving full logs over summarizing. If logs are too large, preserve hash + retention location and a representative excerpt with explicit truncation note.

## 5. Exit Codes Summary

| Step | Expected exit (if documented) | Actual exit | Match? |
|------|-------------------------------|-------------|--------|
| 1 | unknown / 0 / other | | `NOT_STARTED` |

## 6. Deviations from Official Procedure

| Deviation ID | Step | Official expectation | Actual action | Reason | Impact |
|--------------|------|----------------------|---------------|--------|--------|
| D-001 | | | | | |

If none: write `None recorded` only after a completed run. While unrun, status remains `NOT_STARTED`.

## 7. Blocked Steps

| Block ID | Step | Blocker | Status | Unblock plan |
|----------|------|---------|--------|--------------|
| BK-001 | | | `BLOCKED` / resolved | |

## 8. Cleanup Procedure

| Field | Value |
|-------|-------|
| Cleanup required? | Yes / No / Unknown |
| Cleanup commands | |
| Cleanup performed? | No / Yes |
| Residual artifacts left behind | |
| Cleanup status | `NOT_STARTED` / `PASS` / `PARTIAL` / `NOT_APPLICABLE` |

```text
# Cleanup commands (exact)
```

## 9. Evidence Produced by This Run

| Evidence item | Location | Linked claim IDs | Status |
|---------------|----------|------------------|--------|
| | | | `NOT_STARTED` |

## 10. Reproduction Outcome (This Run Only)

Choose one for **this run**, not for the whole product:

| Outcome | Selected |
|---------|----------|
| `NOT_STARTED` | ☐ |
| `BLOCKED` | ☐ |
| `PASS` | ☐ |
| `PARTIAL` | ☐ |
| `FAIL` | ☐ |
| `NOT_APPLICABLE` | ☐ |

Justification (required if not `NOT_STARTED`):

```text
```

## 11. What This Reproduction Proves

```text
[Only steps actually executed with preserved evidence.]
```

## 12. What This Reproduction Does NOT Prove

- Independent witness verification (unless this run **is** the independent witness run and independence is attested)
- Claims not exercised by the command sequence
- Security properties
- Long-term stability or operational readiness
- Correctness beyond observed outputs
- That future checkouts at floating refs will match

## 13. Operator Attestation

| Field | Value |
|-------|-------|
| I executed the commands listed | Yes / No |
| I preserved logs as listed | Yes / No |
| I am an independent witness for this target | Yes / No |
| Signature / handle | |
| Date | |

---

**Contributor ≠ Witness. Owner-side ≠ E4.**
