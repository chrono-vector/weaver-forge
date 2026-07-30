# Future Candidate Backlog

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

Track contract-changing, scope-changing, future-candidate, or non-RC8 work without authorizing implementation.

## 2. Scope

- Backlog items deferred from RC8 freeze
- Status tracking under Future Candidate vocabulary
- Promotion criteria and non-authorization rules
- Witness implications stated as implications only

## 3. Out of Scope

- Authorizing RC9
- Authorizing future-candidate creation or implementation
- Changing protected files
- Declaring READY or NOT READY
- Completing C-014
- Closing findings or blockers
- Authorizing Independent Witness execution

## 4. Authority

This document is a management backlog only. It routes deferred work for later formal evaluation.

## 5. Non-Authority

This backlog does not authorize RC9, future-candidate creation, implementation, release, production use, Independent Witness handoff, or formal Source disposition. Existing claim, verdict, lifecycle, and package documents remain authoritative within their own stated scope.

## 6. Backlog Rules

- Contract-changing or otherwise non-RC8 work identified under the freeze must be placed here rather than into RC8 Work Packages.
- Backlog placement is not implementation authorization.
- Each item must retain a non-authorization statement.
- IDs use `FC-NNN` and are stable once assigned.
- Status values are management-only.

Future Candidate status values do not authorize RC9, future-candidate creation, implementation, release, or witness handoff.

## 7. Status Vocabulary

Use exactly:

- `Proposed`
- `Classified`
- `Awaiting Formal Source Evaluation`
- `Eligible for Candidate Planning`
- `Deferred`
- `Rejected`
- `Superseded`

## 8. Backlog Items

| Future Candidate ID | Title | Related issue IDs | Reason deferred from RC8 | Contract area | Candidate impact | Dependencies | Required formal evaluation | Required governance decision | Required technical design | Witness implications | Status | Promotion criteria | Non-authorization statement | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `FC-001` | Post-GOV-004 Future Candidate routing for formal findings | `ISSUE-RC8-004` | GOV-004 records completed RC8 Formal Source Evaluation with final controlling disposition NOT READY; Future Candidate work is required for F-01, F-02, F-03, F-04, B-01, B-02, and B-03 | Source evaluation / lifecycle decision | Would require Future Candidate remediation and subsequent formal reassessment beyond management documentation | `GATE-12`; current lifecycle sources | Formal reassessment of remediated findings and blockers by the authority designated under GOV-002 | Explicit authorization of the Future Candidate scope and subsequent disposition after formal reassessment | Not currently identified beyond existing package and audit surfaces | Does not by itself authorize Independent Witness | `Classified` | Authorized Future Candidate scope, completed remediation evidence, formal reassessment, and explicit disposition record | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | Future Candidate required: F-01, F-02, F-03, F-04, B-01, B-02, B-03. RC8 evidence-only work possible: B-04, B-05. |
| `FC-002` | Independent Witness authorization and C-014 execution | `ISSUE-RC8-003` | Independent Witness not authorized; C-014 NOT_STARTED; execution would be witness-bound, not RC8 management documentation | Independent Witness / C-014 | Would require separate witness authorization and process | `FC-001` may be related but is not assumed sufficient; `GATE-11` | Formal witness-process authorization | Explicit Independent Witness authorization distinct from management baseline | Witness package requirements/runbook already exist; execution design not invented here | Directly concerns Independent Witness; still not authorized by backlog placement | `Classified` | Separate IW authorization, stable handoff package, and witness-process entry criteria stated by authoritative sources | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | `CLAIM_REGISTER.md` C-014 NOT_STARTED; `STATUS.md` IW not authorized/performed |
| `FC-003` | Protected/version-bound package identity and manifest alignment | `ISSUE-RC8-002` | Protected files retain historical RC6/pre-tag RC7 wording; changing them is prohibited under RC8 management freeze | Package identity / manifest / version records | Any future edit would be identity/manifest/version-bound | `LIFECYCLE_CLARIFICATION.md` protected list; `CONTRACT-IDX-014`–`016` | Formal evaluation of whether a future candidate may revise protected surfaces | Governance decision before any protected-file edit | Technical design for identity/manifest migration Not currently identified | Future identity changes could affect witness package interpretation | `Proposed` | Explicit future-candidate authorization plus protected-file change control | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | Current interpretation uses clarification + STATUS/README; protected files remain unchanged |
| `FC-004` | Windows host build-environment readiness (C-015) | `ISSUE-RC8-005` | C-015 is BLOCKED; remediation is runtime/environment contract-adjacent and not management-baseline work | Runtime / environment readiness | Future candidate would address Windows host readiness claim | Claim register C-015; verification plan historical blockers | Formal technical evaluation of Windows readiness scope | Governance decision if claim disposition changes | Environment design Not currently identified beyond existing claim evidence | May affect future witness environment expectations; does not authorize IW | `Classified` | Claim-scope evaluation and separate implementation authorization | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | `CLAIM_REGISTER.md` status BLOCKED |
| `FC-005` | Static startup boundary completion (C-019) | `ISSUE-RC8-006` | C-019 is PARTIAL; further product/runtime boundary work is outside RC8 management freeze | Runtime / startup boundary | Future candidate would address pre-init CLI boundary | Claim register C-019 evidence | Formal technical evaluation | Governance decision if claim disposition changes | Technical design Not currently identified beyond existing claim evidence | May affect future witness expectations; does not authorize IW | `Classified` | Claim-scope evaluation and separate implementation authorization | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | Safe pre-initialization boundary NOT ESTABLISHED per claim register |
| `FC-006` | Historical audit blocker remediation (including RC4 open blockers) | `ISSUE-RC8-007` | Historical audits recorded NOT READY with open blockers; remediation would be contract/package-changing relative to frozen historical releases | Historical audit remediation / package readiness | Future candidate may address open historical blockers without rewriting immutable historical releases | C-027 and related evidence; package readiness policy | Formal Source/technical evaluation of remediation candidate scope | Governance decision distinguishing historical immutability from future candidate work | Remediation design Not currently identified in this backlog | Witness implications depend on future package candidate; not authorized now | `Proposed` | Explicit future-candidate scope that preserves immutable historical releases | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | C-027 records 40 integrated blockers; none marked CLEAR/CLOSED by this backlog |
| `FC-007` | RC9 or later candidate planning | `ISSUE-RC8-008` | RC9 is not authorized; any RC9 planning is future-candidate only | Future release candidate | Would create a new candidate beyond RC8 | Requires prior governance and formal evaluation decisions | Formal Source and governance evaluation | Explicit RC9/future-candidate authorization | Not currently identified | Would redefine witness candidate identity only if separately authorized | `Deferred` | Explicit authorization of a future candidate identity and planning charter | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | `STATUS.md` and `LIFECYCLE_CLARIFICATION.md`: RC9 not authorized / no RC9 exists |
| `FC-008` | Stale project-metrics and mixed-policy footer reconciliation | `ISSUE-RC8-009` | Some editable or mixed surfaces are stale or historically lagging; broad reconciliation may be contract-adjacent and is deferred from RC8 freeze management closure | Documentation alignment / mixed policy | Future candidate or separately authorized docs pass may reconcile stale footers without changing protected files unless explicitly authorized | `PROJECT_METRICS.md`; mixed policy files; clarification | Evaluation of which files are editable vs mixed/protected | Governance decision per file class | Not currently identified | Indirect; must not be mistaken for IW readiness | `Proposed` | File-class-specific authorization and freeze re-check | Backlog placement does not authorize implementation, RC9, future-candidate creation, release, or Independent Witness handoff. | Do not edit protected files under the guise of footer cleanup |

Formal remediation routing under GOV-004: Future Candidate required — F-01, F-02, F-03, F-04, B-01, B-02, B-03. RC8 evidence-only work possible — B-04, B-05. Independent Witness required for formal findings — none. This backlog does not authorize future-candidate creation, RC9, Independent Witness, C-014, protected-file edits, or remediation.

## 9. Promotion Criteria

An item may become eligible for candidate planning only when all of the following are true:

- Status reaches `Eligible for Candidate Planning` under the vocabulary above.
- Required formal evaluation has occurred or is explicitly waived by designated formal authority.
- Required governance decision is recorded under a `GOV-NNN` identifier.
- RC8 freeze re-check confirms the work remains outside RC8 frozen surfaces or is explicitly authorized as a new candidate scope.
- Non-authorization statement remains visible until true authorization exists.

Promotion criteria satisfaction does not itself authorize implementation, RC9, release, or Independent Witness handoff.

## 10. Non-Authorization Rule

Backlog placement does not authorize implementation, RC9, future-candidate creation, release, production use, or Independent Witness handoff.

No row in Section 8 authorizes work merely by existing.

## 11. Witness Implications

Witness implications listed per item are planning notes only.

- They do not authorize Independent Witness execution.
- They do not start or complete C-014.
- They do not convert owner-side evidence into Independent Witness PASS.
- `GATE-11` remains required before any separately authorized witness handoff.

## 12. Update Triggers

- New contract-changing issue classified under the Issue Register
- Formal Source evaluation outcome recorded
- Governance decision affecting future-candidate eligibility
- Independent Witness authorization status change stated by authoritative sources
- New protected-file or mixed-file classification change

## 13. Ownership

Repository maintainer.

## 14. Entry Criteria

- `RC8_FREEZE_BOUNDARY.md` deferral rule available.
- `CURRENT_CONTRACT_INDEX.md` available for contract-area references.

## 15. Exit Criteria

- Deferred contract-changing items represented as `FC-NNN` rows.
- Each row includes the required non-authorization statement.
- Status vocabulary used exactly.

## 16. Acceptance Criteria

- No RC9 authorization.
- No implementation authorization.
- No Independent Witness authorization.
- No finding or blocker marked CLEAR, CLOSED, or RESOLVED.
- No READY/NOT READY decision newly declared.

## 17. References

### Existing repository files

- `STATUS.md`
- `README.md`
- `external_verifications/grok-build/CLAIM_REGISTER.md`
- `external_verifications/grok-build/VERDICT.md`
- `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`
- `external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md`
- `PROJECT_METRICS.md`

### RC8 management baseline set

- `PROJECT_CHARTER.md`
- `RC8_FREEZE_BOUNDARY.md`
- `CURRENT_CONTRACT_INDEX.md`
- `RC8_ISSUE_REGISTER.md`
- `RC8_REMAINING_WORK_ROADMAP.md`
- `RC8_WORK_PACKAGE_PLAN.md`
- `RC8_TRACEABILITY_MATRIX.md`
