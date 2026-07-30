# RC8 Work Package Plan

> **Management artifact notice**
>
> This document is a non-authoritative project-management artifact for Weaver Forge RC8 planning and traceability.
>
> It does not modify technical contracts, package identity, validator behavior, manifests, evidence, witness requirements, historical verdicts, protected files, immutable tags, or version-bound records.
>
> It does not declare RC8 READY or NOT READY, does not authorize Independent Witness execution, does not claim C-014 completion, does not mark any finding or blocker CLEAR or CLOSED, and does not authorize RC9 or any future candidate.
>
> Where this document references lifecycle, package, validator, manifest, evidence, identity, witness, or contract material, the referenced repository files remain authoritative within their own stated scope.

## 1. Purpose

Group related management-authorized implementation into auditable Work Packages.

## 2. Scope

- Work Packages for freeze-compatible RC8 management work
- Entry, exit, acceptance, evidence, and gate requirements per package
- Status tracking under Work Package vocabulary

## 3. Out of Scope

- Contract-changing future-candidate implementation
- Protected-file edits
- Independent Witness execution
- Finding or blocker technical closure
- READY/NOT READY decisions
- RC9 authorization

## 4. Authority

This plan defines management Work Packages only.

## 5. Non-Authority

Work Package status values describe repository-management progress only. They do not establish technical correctness, formal Source approval, witness approval, release readiness, production readiness, or finding/blocker closure.

## 6. Work Package Rules

- Work Packages prevent piecemeal implementation.
- Work Package completion is not formal finding closure.
- Contract-changing work must be excluded and deferred to `FUTURE_CANDIDATE_BACKLOG.md`.
- Each Work Package must list included and excluded issue IDs.
- Implementer self-approval is prohibited; reviewer must not be identical to implementer for `GATE-06`.
- IDs use `WP-RC8-NNN` and are stable once assigned.

## 7. Identifier Scheme

| Entity | Scheme | Example |
|---|---|---|
| Work Packages | `WP-RC8-NNN` | `WP-RC8-001` |
| Issues | `ISSUE-RC8-NNN` | `ISSUE-RC8-001` |
| Future Candidate items | `FC-NNN` | `FC-001` |
| Gates | `GATE-NN` | `GATE-04` |

## 8. Status Vocabulary

Use exactly:

- `Draft`
- `Scope Review`
- `Approved`
- `Authorized`
- `In Progress`
- `Internal Review`
- `Evidence Review`
- `Pre-Commit Review`
- `Committed`
- `Post-Commit Review`
- `Pushed`
- `Deferred`
- `Cancelled`

Work Package status values describe repository-management progress only. They do not establish technical correctness, formal Source approval, witness approval, release readiness, production readiness, or finding/blocker closure.

## 9. Work Package Plan

| Work Package ID | Title | Objective | Included issue IDs | Excluded issue IDs | Classification | RC8 freeze compatibility | Contract impact | Entry criteria | Exit criteria | Acceptance criteria | Required evidence | Implementer | Reviewer | Required gates | Status | Commit | Post-commit review | Push state | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `WP-RC8-001` | Establish RC8 Management Baseline | Create the eight root-level non-authoritative management baseline documents with required sections, tables, vocabularies, gates, and cross-references | `ISSUE-RC8-001`, `ISSUE-RC8-010` | `ISSUE-RC8-002`, `ISSUE-RC8-003`, `ISSUE-RC8-004`, `ISSUE-RC8-005`, `ISSUE-RC8-006`, `ISSUE-RC8-007`, `ISSUE-RC8-008`, `ISSUE-RC8-009`, `ISSUE-RC8-011` | `RC8 Management` | `Compatible` | None intended; index and reference only | Freeze direction accepted; eight-artifact set accepted in principle (`GOV-001`); no protected-file edits planned | Eight files exist at repository root; shared notices present; required tables/columns present; no existing file modified | Matches Blueprint document specs; no READY/NOT READY claim; no C-014 completion; no finding/blocker CLEAR/CLOSED; no IW/RC9 authorization | Committed eight-file management baseline at `f1110c6`; protected-file unchanged check; cross-document ID consistency; Pi management post-commit `No Objection` (no objection to narrow push); Pi post-push confirmed (HEAD matched `origin/main`) | Cursor or Grok implementation agent | Pi read-only reviewer; repository maintainer for authorization | `GATE-01`, `GATE-03`, `GATE-04`, `GATE-05`, `GATE-06`, `GATE-07`, `GATE-08` | `Pushed` | `f1110c65035e13efad8e2956ab62300d1ad1706a` | `No Objection` | Pushed; HEAD matched `origin/main` after post-push confirmation | Eight management baseline files committed in `f1110c6`, Pi post-commit management review recorded `No Objection` (no objection to narrow push), narrow push performed, and post-push confirmed; management-record reconciliation only — not technical closure, READY/NOT READY, IW, C-014, RC9, or Future Candidate authorization |
| `WP-RC8-002` | Post-creation management review package | Perform Pi/maintainer management reviews of the baseline docs through pre-commit readiness without modifying protected files | Depends on closure routing of `ISSUE-RC8-001` / `ISSUE-RC8-010` after `WP-RC8-001` file creation | All Future Candidate issues | `RC8 Management` | `Compatible` | None | `WP-RC8-001` files created; working tree inspectable | Review sequence items for non-authority, freeze, references, terminology, IDs, and traceability completed or explicitly deferred | Review results recorded under review vocabulary; no formal audit claim | Review notes; `REVIEW-PI-NNN` references when assigned | Not currently identified | Pi read-only reviewer | `GATE-06`, `GATE-07`, `GATE-08` | `Draft` | Not currently identified | `Not Evaluated` | Not pushed | Does not authorize commit by itself |
| `WP-RC8-003` | Commit and push authorization package | If separately authorized, commit and push only the eight management files after reviews | None until `WP-RC8-001`/`WP-RC8-002` satisfy entry criteria | All Future Candidate and Independent Witness issues | `RC8 Management` | `Compatible` | None | `GATE-08` pass or conditional pass with maintainer authorization | Commit exists for authorized scope; post-commit review complete before push | Only approved files changed; protected files unchanged; no prohibited claims introduced | Commit ID; post-commit review; push authorization note | Not currently identified | Repository maintainer; Pi post-commit review | `GATE-08`, `GATE-09`, `GATE-10` | `Draft` | Not currently identified | `Not Evaluated` | Not pushed | Commit/push ≠ release or production readiness |

## 10. Entry Criteria Rules

A Work Package may enter implementation only when:

- Included issues are classified and dispositioned to `RC8 Work Package`.
- Excluded issues that are contract-changing are deferred to Future Candidate Backlog.
- Freeze compatibility is `Compatible` or explicitly `Conditional` with recorded conditions.
- Required gates up to `GATE-05` are `Pass` or `Conditional Pass` with documented conditions.
- Protected files are outside scope.

## 11. Exit Criteria Rules

A Work Package may exit implementation only when:

- Acceptance criteria are satisfied.
- Required evidence references exist or are explicitly marked Not currently identified with justification.
- Traceability rows exist for included issues.
- Reviewer distinct from implementer has recorded a management review result, or status remains below Internal Review with that gap explicit.

Exit does not mean technical finding closure.

## 12. Review and Evidence Rules

- Evidence references use `EVID-NNN`, `REVIEW-PI-NNN`, or `REVIEW-SOURCE-NNN` when assigned.
- Empty commit fields are allowed before implementation/commit.
- Review results use: `No Objection`, `Revision Required`, `Blocked`, `Out of Scope`, `Not Evaluated`.
- Review results are management-review results only. They do not declare READY or NOT READY, do not authorize Independent Witness execution, do not establish Source disposition, and do not close findings or blockers.

## 13. Update Triggers

- Issue inclusion/exclusion changes
- Gate results
- Commit or push state changes
- Reviewer/implementer assignment changes
- Scope changes requiring `GATE-04` re-check

## 14. Ownership

Repository maintainer.

## 15. Entry Criteria

- Issue Register and Freeze Boundary available.
- Future Candidate Backlog available for exclusion routing.

## 16. Exit Criteria

- Initial Work Packages defined for baseline creation and follow-on review/commit packaging.
- Contract-changing work excluded.

## 17. Acceptance Criteria

- Work Packages prevent piecemeal implementation for the baseline set.
- Work Package completion is not treated as formal finding closure.
- Contract-changing work is excluded and deferred.
- No READY/NOT READY decision newly declared.
- No Independent Witness authorization.

## 18. References

### Existing repository files

- `STATUS.md`
- `README.md`
- `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`

### RC8 management baseline set

- `PROJECT_CHARTER.md`
- `RC8_FREEZE_BOUNDARY.md`
- `CURRENT_CONTRACT_INDEX.md`
- `FUTURE_CANDIDATE_BACKLOG.md`
- `RC8_ISSUE_REGISTER.md`
- `RC8_REMAINING_WORK_ROADMAP.md`
- `RC8_TRACEABILITY_MATRIX.md`
