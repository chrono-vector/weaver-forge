# RC8 Remaining Work Roadmap

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

Provide the execution roadmap from RC8 freeze through management baseline, issue classification, work packages, reviews, commits, post-commit review, push, and future-candidate deferral.

## 2. Scope

- Sequencing of RC8 management work
- Separation of Future Candidate, Governance, and Independent Witness lanes
- Required gates between states
- Relationship to repository `ROADMAP.md`

## 3. Out of Scope

- Technical product implementation
- Protected-file modification
- Independent Witness execution
- RC9 authorization
- READY/NOT READY decisions
- Finding or blocker closure

## 4. Authority

This document sequences management work only.

## 5. Non-Authority

This roadmap does not supersede `ROADMAP.md`, `STATUS.md`, claim registers, witness-package policies, or formal Source/Witness processes. Lane completion is not technical closure or readiness.

## 6. Relationship to ROADMAP.md

`ROADMAP.md` (`CONTRACT-IDX-031`) is the high-level project roadmap (Phase 0 Launch through Phase 4 Ledger MVP). It does not define RC8 freeze, management gates, or Future Candidate deferral.

This document is the RC8 management remaining-work roadmap. It does not replace `ROADMAP.md` and does not reinterpret Phase 3 Witness Reviews as Independent Witness authorization.

## 7. Execution Flow

```text
Freeze Boundary
→ Contract Index
→ Future Candidate Backlog
→ Issue Register
→ Remaining Work Roadmap
→ Work Package Plan
→ Traceability Matrix
→ Implementation only if separately authorized
→ Review
→ Commit authorization
→ Commit
→ Post-Commit Review
→ Push authorization
→ Push
→ Post-Push confirmation
```

## 8. RC8 Management Lane

Activities limited to freeze-compatible management artifacts and classifications:

- Maintain charter, freeze boundary, contract index, issue register, work packages, and traceability
- Route non-RC8 work out of this lane
- Use gates `GATE-01` through `GATE-10` as applicable for management-file work
- Do not modify protected files

## 9. Future Candidate Lane

Activities for deferred contract-changing or non-RC8 work:

- Maintain `FUTURE_CANDIDATE_BACKLOG.md`
- Keep non-authorization statements visible
- Use `GATE-12` when Source formality must be distinguished
- Do not treat backlog status as RC9 or implementation authorization

## 10. Governance Lane

Activities for governance decisions and role/authority designations:

- Record `GOV-NNN` decisions
- Prevent implementer self-approval
- Keep Pi review as read-only management review unless separately authorized
- Use `GATE-12` for formal Source evaluation boundary

## 11. Independent Witness Lane

Activities related to witness handoff and C-014:

- Remain separate from author implementation
- Require separate authorization before any execution
- Use `GATE-11`
- Do not count author implementation as Independent Witness completion
- Current repository state: Independent Witness not authorized; C-014 NOT_STARTED

## 12. Sequencing Rules

- Freeze boundary before classifying contract-changing work as RC8-compatible.
- Contract index before relying on authority-type classifications.
- Issue classification before Work Package inclusion.
- Future Candidate deferral before any attempt to implement deferred work under RC8.
- Pre-implementation authorization before implementation.
- Internal review and evidence/traceability review before pre-commit review.
- Post-commit review before push authorization.
- Witness handoff stability before any separately authorized witness handoff.
- Formal Source evaluation boundary before treating any Source opinion as formal decision.

## 13. Required Gates

| Gate ID | Gate name | Typical lane | Notes |
|---|---|---|---|
| `GATE-01` | Freeze Boundary | RC8 Management | Required before treating work as RC8-compatible |
| `GATE-02` | Issue Classification | RC8 Management | Required before implementation planning |
| `GATE-03` | Contract Index Integrity | RC8 Management | Index-only integrity |
| `GATE-04` | Work Package Scope | RC8 Management | Before authorization |
| `GATE-05` | Pre-Implementation Authorization | RC8 Management | Before implementation |
| `GATE-06` | Internal Review | RC8 Management | Reviewer ≠ implementer |
| `GATE-07` | Evidence and Traceability Review | RC8 Management | Before pre-commit |
| `GATE-08` | Pre-Commit Review | RC8 Management | Before commit |
| `GATE-09` | Post-Commit Review | RC8 Management | Before push |
| `GATE-10` | Push Authorization | RC8 Management | Before push |
| `GATE-11` | Witness Handoff Stability | Independent Witness | Does not authorize execution by itself |
| `GATE-12` | Formal Source Evaluation Boundary | Governance / Future Candidate | Separates opinion from formal decision |

Gate results are management-control results only. They are not formal technical audit results, Source decisions, witness results, validator results, or readiness decisions.

## 14. Update Triggers

- Issue disposition changes that alter lane routing
- New Work Package creation
- Gate model changes
- Independent Witness authorization status change stated by authoritative sources
- Formal Source evaluation boundary change

## 15. Ownership

Repository maintainer.

## 16. Entry Criteria

- RC8 freeze direction accepted.
- Management baseline artifacts defined in charter.

## 17. Exit Criteria

- Execution flow and lanes defined.
- Sequencing rules and gates cross-referenced.

## 18. Acceptance Criteria

- Distinct from `ROADMAP.md`.
- Future Candidate lane does not authorize RC9.
- Independent Witness lane remains unauthorized unless separately authorized by authoritative sources.
- No READY/NOT READY decision newly declared.
- No finding or blocker closure claimed.

## 19. References

### Existing repository files

- `ROADMAP.md`
- `STATUS.md`
- `README.md`
- `external_verifications/grok-build/CLAIM_REGISTER.md`
- `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`

### RC8 management baseline set

- `PROJECT_CHARTER.md`
- `RC8_FREEZE_BOUNDARY.md`
- `CURRENT_CONTRACT_INDEX.md`
- `FUTURE_CANDIDATE_BACKLOG.md`
- `RC8_ISSUE_REGISTER.md`
- `RC8_WORK_PACKAGE_PLAN.md`
- `RC8_TRACEABILITY_MATRIX.md`

### Execution Roadmap

| Sequence | Lane | Activity | Input artifacts | Output artifacts | Required gate | Allowed next step | Prohibited next step | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | RC8 Management | Confirm freeze boundary | `STATUS.md`, lifecycle sources | `RC8_FREEZE_BOUNDARY.md` | `GATE-01` | Contract indexing | Protected-file edits | RC8 frozen |
| 2 | RC8 Management | Index contracts | Freeze boundary, existing files | `CURRENT_CONTRACT_INDEX.md` | `GATE-03` | Backlog and issue classification | Redefining contracts | Index-only |
| 3 | Future Candidate | Capture deferred work | Freeze boundary, contract index | `FUTURE_CANDIDATE_BACKLOG.md` | `GATE-01` | Issue mapping to FC IDs | Implementation of deferred work | Non-authorization required |
| 4 | RC8 Management | Classify issues | Sources, backlog, index | `RC8_ISSUE_REGISTER.md` | `GATE-02` | Roadmap/WP planning | Implementation without classification | Management status only |
| 5 | RC8 Management | Sequence remaining work | Issue register, charter | `RC8_REMAINING_WORK_ROADMAP.md` | `GATE-01` | Work Package planning | Treating roadmap as readiness | Distinct from `ROADMAP.md` |
| 6 | RC8 Management | Define Work Packages | Issue register, freeze boundary | `RC8_WORK_PACKAGE_PLAN.md` | `GATE-04` | Pre-implementation authorization | Including deferred FC work in RC8 WP | WP completion ≠ finding closure |
| 7 | RC8 Management | Build traceability | Issues, WPs, FCs, index | `RC8_TRACEABILITY_MATRIX.md` | `GATE-07` | Review / authorization | Claiming technical closure via matrix | Empty commit fields allowed |
| 8 | RC8 Management | Authorize implementation if applicable | WP plan, freeze result | Authorization note | `GATE-05` | Implementation of approved WP scope | Commit/push without authorization | Baseline creation may be in progress under maintainer direction |
| 9 | RC8 Management | Internal review | Diff/changed files, WP | Review result | `GATE-06` | Evidence/traceability review | Commit | Reviewer ≠ implementer |
| 10 | RC8 Management | Evidence and traceability review | Matrix, issue register, WP | Review note | `GATE-07` | Pre-commit review | Commit with broken ID mapping | Management review only |
| 11 | RC8 Management | Pre-commit review | Changed-file list, protected-file check | Pre-commit note | `GATE-08` | Commit authorization | Commit without authorization | Protected files must be unchanged |
| 12 | RC8 Management | Commit | Authorized scope | Commit ID | `GATE-08` pass + maintainer authorization | Post-commit review | Push | Commit ≠ readiness |
| 13 | RC8 Management | Post-commit review | Commit ID, changed files | Post-commit note | `GATE-09` | Push authorization | Push | |
| 14 | RC8 Management | Push authorization / push | Post-commit review | Remote update | `GATE-10` | Post-push confirmation | Push without authorization | Push ≠ release readiness |
| 15 | Independent Witness | Witness handoff stability check if applicable | Handoff docs, WP outputs | Handoff stability note | `GATE-11` | Separately authorized witness process only | Author-as-witness completion | Currently not authorized |
| 16 | Governance / Future Candidate | Formal Source evaluation boundary | Source refs, decision records | Source boundary note / FC updates | `GATE-12` | Candidate planning or deferral | READY/NOT READY claim by management docs | Opinion ≠ formal decision |
