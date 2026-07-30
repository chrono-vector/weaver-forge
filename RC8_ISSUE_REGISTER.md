# RC8 Issue Register

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

Track management issues, classifications, dispositions, ownership, review needs, and traceability without asserting technical closure.

## 2. Scope

- Management issues derived from repository-stated observations and management-baseline needs
- Classification, status, and disposition under controlled vocabularies
- Mapping to Work Packages or Future Candidate backlog items
- Explicit technical closure authority boundaries

## 3. Out of Scope

- Technical remediation of product or package defects
- Validator, manifest, evidence, or identity changes
- Declaring findings or blockers CLEAR, CLOSED, or RESOLVED
- Completing C-014
- Authorizing Independent Witness execution
- Authorizing RC9

## 4. Authority

This register is a management-tracking artifact only.

## 5. Non-Authority

Issue status is management-only. This register does not establish technical closure, formal Source disposition, Independent Witness status, release readiness, production readiness, or finding/blocker CLEAR/CLOSED status. Claim and evidence sources remain authoritative within their own stated scope.

## 6. Issue Rules

- IDs use `ISSUE-RC8-NNN` and are stable once assigned.
- Every issue must have classification and disposition.
- Contract-changing work must not be dispositioned as RC8 Work Package.
- Technical closure authority must be explicit and must not be this register alone.
- No issue may be marked technically closed by this register.
- Duplicate or superseded issues remain visible with disposition `Duplicate` or `Superseded`.

Issue status values are management-tracking values only. They do not establish technical closure, formal Source disposition, Independent Witness status, release readiness, production readiness, or finding/blocker CLEAR/CLOSED status.

Issue disposition values identify management routing only. `Independent Witness Handoff` means the item may require separately authorized witness-bound handling; it does not authorize Independent Witness execution or claim witness completion.

## 7. Identifier Scheme

| Entity | Scheme | Example |
|---|---|---|
| Issues | `ISSUE-RC8-NNN` | `ISSUE-RC8-001` |
| Work Packages | `WP-RC8-NNN` | `WP-RC8-001` |
| Future Candidate items | `FC-NNN` | `FC-001` |
| Governance decisions | `GOV-NNN` | `GOV-001` |
| Gates | `GATE-NN` | `GATE-01` |

## 8. Controlled Vocabularies

### Classification

- `RC8 Management`
- `Future Candidate`
- `Governance`
- `Independent Witness`
- `Rejected / Not Applicable`
- `Duplicate`
- `Superseded`

### Status

- `Identified`
- `Classified`
- `Planned`
- `Authorized`
- `In Progress`
- `Under Review`
- `Implemented`
- `Deferred`
- `Rejected`
- `Superseded`

### Disposition

- `RC8 Work Package`
- `Future Candidate Backlog`
- `Governance Decision`
- `Independent Witness Handoff`
- `Rejected / Not Applicable`
- `Duplicate`
- `Superseded`

## 9. Issue Register

| Issue ID | Title | Description | Source | Source reference | Classification | Status | Disposition | RC8 freeze compatibility | Contract-changing | Work Package ID | Future Candidate ID | Required gate | Owner | Reviewer | Dependencies | Management resolution | Technical closure authority | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ISSUE-RC8-001` | Establish RC8 management baseline artifacts | Eight accepted root-level management artifacts were created as non-authoritative management docs, reviewed, committed in `f1110c6`, pushed, and post-push confirmed | Repository observation / management baseline acceptance | Blueprint accepted artifact set; prior absence check | `RC8 Management` | `Implemented` | `RC8 Work Package` | `Compatible` | No | `WP-RC8-001` | N/A | `GATE-01`, `GATE-04`, `GATE-05` | Repository maintainer | Pi read-only reviewer | Charter, freeze boundary, contract index | Eight root-level management files created, Pi-reviewed, committed in `f1110c65035e13efad8e2956ab62300d1ad1706a`, pushed, and post-push confirmed as management work only | Not applicable — documentation creation, not technical finding closure | Does not alter protected files |
| `ISSUE-RC8-002` | Protected/version-bound surfaces retain pre-RC8 wording | `LIFECYCLE_CLARIFICATION.md` states protected/mixed files may retain RC7-oriented wording that must not be read as current RC8 status | `LIFECYCLE_CLARIFICATION.md`; package version/manifest surfaces | `CONTRACT-IDX-006`, `CONTRACT-IDX-014`–`016` | `Future Candidate` | `Classified` | `Future Candidate Backlog` | `Deferred` | Yes, if files were changed | N/A | `FC-003` | `GATE-01`, `GATE-12` | Repository maintainer | Pi read-only reviewer | Protected-file list | Route to backlog; do not edit protected files in RC8 management pass | Formal future-candidate change control / designated technical authority — Not currently identified by name | Interpretation uses clarification + STATUS/README |
| `ISSUE-RC8-003` | Independent Witness / C-014 remains NOT_STARTED | Repository states Independent Witness not authorized/performed and C-014 NOT_STARTED | `STATUS.md`; `CLAIM_REGISTER.md` | `STATUS.md` §3; C-014 | `Independent Witness` | `Classified` | `Independent Witness Handoff` | `Prohibited` under current authorization | Not by management docs; witness-bound if later authorized | N/A | `FC-002` | `GATE-11` | Repository maintainer | Formal decision authority if designated; Pi for management review only | Witness package + handoff docs | Track as handoff-routed backlog item only | Independent Witness process / C-014 evidence authority — not this register | Disposition is routing only; not IW authorization |
| `ISSUE-RC8-004` | No formal Source Weaver READY/NOT READY for RC8 | Repository states no formal Source Weaver READY or NOT READY decision exists for RC8 | `STATUS.md`; `README.md` | `STATUS.md` §3; README RC8 lifecycle | `Governance` | `Classified` | `Future Candidate Backlog` | `Deferred` | Decision would be lifecycle-authoritative | N/A | `FC-001` | `GATE-12` | Repository maintainer | Formal Source authority if designated | Current lifecycle sources | Defer formal evaluation; do not invent READY/NOT READY | Formal Source Weaver decision authority — Not currently identified by personal name | Management docs must not declare READY/NOT READY |
| `ISSUE-RC8-005` | C-015 Windows host readiness BLOCKED | Claim register records C-015 BLOCKED for Windows host build-environment readiness | `CLAIM_REGISTER.md` | C-015 | `Future Candidate` | `Classified` | `Future Candidate Backlog` | `Deferred` | Yes | N/A | `FC-004` | `GATE-01`, `GATE-02` | Repository maintainer | Pi read-only reviewer for management classification | Historical verification plan blockers | Backlog only; no technical remediation in this pass | Technical environment authority / claim evidence — not this register | Do not mark BLOCKED cleared |
| `ISSUE-RC8-006` | C-019 static startup boundary PARTIAL | Claim register records C-019 PARTIAL; pre-initialization CLI boundary not established | `CLAIM_REGISTER.md` | C-019 | `Future Candidate` | `Classified` | `Future Candidate Backlog` | `Deferred` | Yes | N/A | `FC-005` | `GATE-01`, `GATE-02` | Repository maintainer | Pi read-only reviewer for management classification | Related runtime evidence | Backlog only | Technical claim/evidence authority — not this register | Do not mark PARTIAL as PASS/CLOSED |
| `ISSUE-RC8-007` | Historical audit blockers remain open | Historical audits recorded NOT READY; C-027 notes 40 integrated blockers; documentation alignment does not CLEAR/CLOSE them | `CLAIM_REGISTER.md`; package readiness policy | C-023–C-027; C-027 integrated_blockers=40 | `Future Candidate` | `Classified` | `Future Candidate Backlog` | `Deferred` | Yes for remediation | N/A | `FC-006` | `GATE-01`, `GATE-02` | Repository maintainer | Pi read-only reviewer for management classification | Immutable historical releases | Preserve historical immutability; backlog remediation separately | Formal remediation / Source-technical authority — Not currently identified | No blocker marked CLEAR/CLOSED here |
| `ISSUE-RC8-008` | RC9 not authorized | STATUS and lifecycle clarification state RC9 is not authorized / no RC9 exists | `STATUS.md`; `LIFECYCLE_CLARIFICATION.md` | `STATUS.md` §3; clarification current interpretation | `Governance` | `Classified` | `Future Candidate Backlog` | `Prohibited` for RC8 authorization of RC9 | N/A for unauthorized RC9 | N/A | `FC-007` | `GATE-01` | Repository maintainer | Pi read-only reviewer | Freeze boundary | Record non-authorization; defer any later candidate planning | Formal candidate-authorization authority — Not currently identified | Backlog row does not create RC9 |
| `ISSUE-RC8-009` | Stale metrics and lagging mixed-policy footers | `PROJECT_METRICS.md` is a 2026-07-05 snapshot; some mixed policy footers lag current RC8 surfaces | `STATUS.md` stale/partial section; inspected mixed policy files | `CONTRACT-IDX-032`; mixed policy index rows | `Future Candidate` | `Identified` | `Future Candidate Backlog` | `Deferred` | Possibly, depending on file class | N/A | `FC-008` | `GATE-01`, `GATE-03` | Repository maintainer | Pi read-only reviewer | Contract index classifications | Classify per file; no protected-file edits in RC8 management pass | Per-file technical/docs authority — Not currently identified | Avoid treating metrics as current lifecycle |
| `ISSUE-RC8-010` | Management gate and traceability model required | Explicit gates and traceability model were embedded in the RC8 management baseline docs, then reviewed, committed in `f1110c6`, pushed, and post-push confirmed | Management baseline acceptance / `PROJECT_CHARTER.md` | Charter §11; freeze boundary §13 | `RC8 Management` | `Implemented` | `RC8 Work Package` | `Compatible` | No | `WP-RC8-001` | N/A | `GATE-07` | Repository maintainer | Pi read-only reviewer | Issue register + matrix | Gate and traceability model embedded in baseline docs; management creation/review/commit/push cycle completed in `f1110c65035e13efad8e2956ab62300d1ad1706a` as management work only | Not applicable — management process only | Does not equal formal audit |
| `ISSUE-RC8-011` | Owner package readiness remains PARTIAL / not ready for IW handoff | Claim register and package readiness policy state PARTIAL and not ready for Independent Witness handoff | `CLAIM_REGISTER.md`; `PACKAGE_READINESS_POLICY.md` | Package-readiness status rows | `Governance` | `Classified` | `Governance Decision` | `Compatible` as observation-only | No for observation; yes if attempting readiness change | N/A | Related: `FC-001`, `FC-002` | `GATE-12` | Repository maintainer | Pi read-only reviewer | Lifecycle sources | Record observation; do not convert to READY/NOT READY decision | Formal readiness/Source authority — not this register | Observation only; no new readiness decision. Related governance decision ID for baseline acceptance in principle: `GOV-001` (tracked in Traceability Matrix; not an issue row). |

## 10. Disposition Rules

- `RC8 Work Package`: freeze-compatible management work only.
- `Future Candidate Backlog`: contract-changing, deferred, or non-RC8 work.
- `Governance Decision`: requires explicit governance tracking (`GOV-NNN`) and does not imply READY.
- `Independent Witness Handoff`: routing only; requires separate authorization before any witness execution.
- `Rejected / Not Applicable`, `Duplicate`, and `Superseded` remain visible.

## 11. Technical Closure Boundary

- Technical closure authority must be named explicitly in the register column.
- This register cannot be the technical closure authority.
- Management resolution is not technical closure.
- Work Package completion is not finding or blocker closure.
- No issue in this register is marked CLEAR, CLOSED, or RESOLVED as a technical finding/blocker state.

## 12. Update Triggers

- New repository-stated observation requiring management classification
- Work Package or Future Candidate mapping change
- Gate result change
- Governance decision recorded
- Source or witness authorization status change stated by authoritative sources

## 13. Ownership

Repository maintainer.

## 14. Entry Criteria

- Freeze boundary and contract index available.
- Controlled vocabularies defined.

## 15. Exit Criteria

- Initial repository-derived management issues classified and dispositioned.
- Technical closure boundary stated.

## 16. Acceptance Criteria

- Issue status is management-only.
- Technical closure authority is explicit.
- No issue marked technically closed by this register.
- No C-014 completion claim.
- No READY/NOT READY decision newly declared.

## 17. References

### Existing repository files

- `STATUS.md`
- `README.md`
- `external_verifications/grok-build/CLAIM_REGISTER.md`
- `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`
- `external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md`
- `PROJECT_METRICS.md`

### RC8 management baseline set

- `PROJECT_CHARTER.md`
- `RC8_FREEZE_BOUNDARY.md`
- `CURRENT_CONTRACT_INDEX.md`
- `FUTURE_CANDIDATE_BACKLOG.md`
- `RC8_REMAINING_WORK_ROADMAP.md`
- `RC8_WORK_PACKAGE_PLAN.md`
- `RC8_TRACEABILITY_MATRIX.md`
