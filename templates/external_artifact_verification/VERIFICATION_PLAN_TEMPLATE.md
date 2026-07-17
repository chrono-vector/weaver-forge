# Verification Plan — [TARGET NAME]

| Field | Value |
|-------|-------|
| Target slug | `[target-slug]` |
| Plan status | `NOT_STARTED` |
| Package created | `YYYY-MM-DD` |
| Operator / author | |
| Operator role | Owner-side planner (not independent witness) |
| Independent witness status | `NOT_STARTED` |
| Weaver evidence level (target) | E0 / E1 / … (do not claim E4 without uninvolved witness) |

---

## 1. Purpose

State why this external artifact is being evaluated and what decisions the package is intended to support.

```text
[Why verify this target? What decision or claim boundary depends on it?]
```

## 2. Target Summary

| Field | Value |
|-------|-------|
| Artifact type | software / research / repository / archive / notebook / other |
| Canonical name | |
| Canonical publisher | |
| Canonical URL | |
| Intended verification depth | identity only / build / functional / claims / security / full package |

## 3. Scope

### In scope

- [ ] Source identity and version pinning
- [ ] Artifact integrity (hash / immutable reference)
- [ ] Documented build reproduction
- [ ] Documented test or functional checks
- [ ] Claim register evaluation
- [ ] Environment identity recording
- [ ] Owner-side reproduction record
- [ ] Independent witness handoff package
- [ ] Other: ________

### Out of scope

List explicitly. Examples: production deployment, formal security audit, legal compliance, performance benchmarking beyond documented claims.

```text
-
-
```

## 4. Evidence Chain Checklist

Record status per link. Do not mark `PASS` without recorded evidence.

| Chain link | Status | Notes / evidence pointer |
|------------|--------|--------------------------|
| Source | `NOT_STARTED` | |
| Artifact | `NOT_STARTED` | |
| Identity and Version | `NOT_STARTED` | |
| Hash or Immutable Reference | `NOT_STARTED` | |
| Claim | `NOT_STARTED` | |
| Test | `NOT_STARTED` | |
| Reproduction | `NOT_STARTED` | |
| Evidence | `NOT_STARTED` | |
| Receipt | `NOT_STARTED` | |
| Verdict | `NOT_STARTED` | |
| Independent Witness | `NOT_STARTED` | |

## 5. Roles and Independence

| Role | Name / handle | Independent from target authors? | Independent from this package author? |
|------|---------------|----------------------------------|----------------------------------------|
| Package author | | Yes / No / Unknown | N/A |
| Owner-side reproducer | | Yes / No / Unknown | Yes / No |
| Independent witness | *unassigned* | Required: Yes | Required: Yes |

**Rule:** Owner-side reproduction ≠ independent third-party witness verification.

**Rule:** Contributor ≠ Witness. Do not self-witness.

## 6. Package Files

| File | Purpose | Status |
|------|---------|--------|
| `SOURCE_IDENTITY.md` | Publisher, URL, version, hash, license | `NOT_STARTED` |
| `CLAIM_REGISTER.md` | Claims and acceptance criteria | `NOT_STARTED` |
| `ENVIRONMENT.md` | Machine and runtime identity | `NOT_STARTED` |
| `REPRODUCTION.md` | Commands, exits, logs | `NOT_STARTED` |
| `RESULTS.md` | Observed outcomes | `NOT_STARTED` |
| `VERDICT.md` | Multi-axis conservative verdict | `NOT_STARTED` |
| `WITNESS_HANDOFF.md` | Independent witness package | `NOT_STARTED` |

## 7. Planned Procedure (High Level)

Order of work. Exact commands belong in `REPRODUCTION.md` only after they are known and authorized.

1. Freeze source identity (URL, tag/branch, full commit ID, license).
2. Record artifact acquisition method and integrity reference.
3. Register claims with evidence classes and acceptance criteria.
4. Capture environment identity before execution.
5. Execute only documented reproduction steps; preserve logs.
6. Fill results with actual outcomes only.
7. Issue conservative multi-axis verdict.
8. Prepare witness handoff; do not claim E4 until completed by an uninvolved party.

## 8. Blocking Conditions

| Blocker ID | Description | Status | Resolution path |
|------------|-------------|--------|-----------------|
| B-001 | | `NOT_STARTED` / `BLOCKED` / resolved | |

## 9. Authorization Boundaries

| Action | Authorized in this plan? | Notes |
|--------|--------------------------|-------|
| Fetch public metadata / docs only | Yes / No | |
| Clone repository | Yes / No | |
| Build | Yes / No | |
| Install dependencies | Yes / No | |
| Execute tests or binaries | Yes / No | |
| Use credentials / paid APIs | Yes / No | |
| Modify target source | Yes / No | Default: No |
| Network beyond documented needs | Yes / No | |

If this plan is documentation-only, set execution actions to **No** and keep related statuses `NOT_STARTED` or `BLOCKED`.

## 10. Success Criteria for This Plan Document

This plan document is complete when:

- [ ] Target and scope are explicit
- [ ] Out-of-scope items are listed
- [ ] Evidence chain checklist is present (statuses may remain `NOT_STARTED`)
- [ ] Roles and independence rules are stated
- [ ] Authorization boundaries are explicit
- [ ] Non-claims section is filled

Completing this plan does **not** complete verification.

## 11. What This Plan Proves

```text
[Only that a verification package was planned / structured — not that the target works.]
```

## 12. What This Plan Does NOT Prove

- Independent verification of the target
- Source authenticity or artifact integrity
- Build or functional reproducibility
- Truth of publisher claims
- Security review completion
- Operational readiness
- Weaver Forge E4/E5 for this repository or the target
- Any result not yet recorded with evidence

## 13. Change Log

| Date | Change | Author |
|------|--------|--------|
| YYYY-MM-DD | Initial plan | |

---

**No commit. No claim. No receipt. No authority.**
