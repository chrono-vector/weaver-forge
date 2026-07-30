# Project Charter

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

Define the project-management authority, scope, roles, governance rules, and non-authority boundaries for the Weaver Forge RC8 management baseline.

## 2. Scope

- Management process for the RC8 management baseline
- Role definitions for planning, implementation, review, Source evaluation, and Independent Witness boundaries
- Governance rules and review gates used by the management artifacts
- Baseline artifact hierarchy among the eight RC8 management documents
- Freeze-compatible planning that preserves RC8 immutability

## 3. Out of Scope

- Technical implementation of product or package behavior
- Validator behavior changes
- Package identity changes
- Manifest changes
- Evidence changes
- Independent Witness execution
- Formal Source Weaver audit decisions
- Release or production readiness decisions
- RC9 or future-candidate authorization

## 4. Authority

This document governs only the management use of the eight RC8 baseline artifacts listed in Section 9. It may define management roles, gates, and planning rules for those artifacts.

## 5. Non-Authority

This document does not supersede `STATUS.md`, `README.md`, `REPRODUCE.md`, `ROADMAP.md`, `external_verifications/grok-build/README.md`, `external_verifications/grok-build/WITNESS_HANDOFF.md`, `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`, witness-package files, manifests, validator documentation, evidence records, immutable tags, or formal Source/Witness processes.

Lifecycle, package, validator, manifest, evidence, identity, and witness authority remain with the referenced repository files within their own stated scope.

## 6. Current Lifecycle Boundary

Repository-stated and owner-supplied lifecycle facts are authoritative in `STATUS.md`, `README.md`, and related package status surfaces. This charter references them without restating a new verdict.

As stated in those sources for current interpretation:

- RC6 remains an immutable historical NOT READY candidate.
- RC7 remains an immutable historical NOT READY candidate.
- RC8 is an immutable static-audit candidate (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`).
- RC8 artifact generation and verification passed; that result is not a formal Source Weaver audit.
- No formal Source Weaver READY or NOT READY decision exists for RC8.
- Independent Witness was not authorized and was not performed.
- C-014 remains NOT_STARTED.
- No finding or blocker is CLEAR or CLOSED.
- No release-readiness or production-readiness claim is made.
- RC9 is not authorized.

RC8 remains frozen for contract-changing, identity-changing, validator-changing, manifest-changing, evidence-changing, and protected-file work. Management documentation may be created only as non-authoritative planning and traceability artifacts.

## 7. Role Model

| Role | Responsibility | May approve | Must not approve | Independence restriction |
|---|---|---|---|---|
| Repository maintainer | Human or authority responsible for repository changes and final management approvals | Management-file creation, commit authorization, push authorization within explicit scope | Independent Witness completion; formal Source READY/NOT READY unless separately designated | Must not self-certify Independent Witness completion |
| ChatGPT planning coordinator | Planning assistant producing management blueprints and structures | Proposal of structure, vocabulary, gates, and traceability for maintainer consideration | File modification; formal audit authority; readiness decisions | Advisory only |
| Cursor or Grok implementation agent | Implementation agent creating or editing files when authorized | Creation of the eight management files strictly from the approved blueprint | Protected-file edits; invented statuses; READY/NOT READY decisions; witness authorization | Must not act as Independent Witness for the same work |
| Pi read-only reviewer | Read-only reviewer checking management baseline consistency | Management consistency findings and review results under the review vocabulary | Commit, push, protected-file modification, or formal independent audit unless separately authorized | Pi review is not an independent formal audit |
| Source technical evaluator | Technical reviewer or evaluator | Technical opinions; formal Source decision only if explicitly operating in that designated role | Having advisory opinions represented as formal Source decisions unless explicitly designated | Advisory opinion ≠ formal Source decision |
| Independent Witness | Separate uninvolved witness | Formal witness work only if authorized under the witness process | Being the author, implementer, or owner-side reproducer for the same work; accepting author implementation as witness completion | Must remain independent of author/implementer roles |
| Formal decision authority | Distinct authority, if designated | Formal lifecycle, Source, release, or governance decisions within explicit scope | Being implied by management documents if not explicitly designated | Must be explicitly designated; not implied by this charter |

## 8. Governance Rules

- Implementer self-approval is prohibited.
- Author implementation cannot be counted as Independent Witness completion.
- Management status is not technical status.
- Work Package completion is not finding or blocker closure.
- Backlog placement is not implementation authorization.
- Documentation agreement is not READY.
- Source technical opinion is not a formal Source decision unless explicitly designated as such by the applicable formal authority.
- Pi review is a read-only management review unless separately authorized as something else.
- Independent Witness execution requires separate authorization and cannot be created by these management artifacts.
- Commit or push authorization is not release or production readiness.
- Future Candidate backlog placement is not RC9 authorization.
- RC8 remains frozen; contract-changing work is not RC8 work.

## 9. Management Artifact Set

| Artifact | Purpose | Primary category | Depends on | Feeds into |
|---|---|---|---|---|
| `PROJECT_CHARTER.md` | Management authority, roles, and governance baseline | Governance | Existing lifecycle sources (`STATUS.md`, `README.md`, and related references) | All other RC8 management artifacts |
| `RC8_FREEZE_BOUNDARY.md` | RC8 freeze boundary and permitted vs prohibited work | RC8 documentation + governance | `PROJECT_CHARTER.md`, `STATUS.md`, lifecycle references | Issue classification, Work Packages, Future Candidate backlog |
| `CURRENT_CONTRACT_INDEX.md` | Index of contract, lifecycle, validator, manifest, evidence, and witness surfaces | Governance + project management | `PROJECT_CHARTER.md`, `RC8_FREEZE_BOUNDARY.md` | Issue Register, Traceability Matrix |
| `FUTURE_CANDIDATE_BACKLOG.md` | Non-authorizing backlog for contract-changing or non-RC8 work | Future-candidate planning + project management | Freeze Boundary, Contract Index | Issue Register dispositions, Roadmap Future Candidate lane |
| `RC8_ISSUE_REGISTER.md` | Management issue classification and disposition | Project management | Freeze Boundary, Contract Index, Future Candidate Backlog | Work Package Plan, Traceability Matrix, Roadmap |
| `RC8_REMAINING_WORK_ROADMAP.md` | Execution sequencing across management lanes | RC8 documentation + project management | Charter, Freeze Boundary, Issue Register | Work Package Plan, gate sequencing |
| `RC8_WORK_PACKAGE_PLAN.md` | Auditable Work Packages for management-authorized implementation | Project management | Issue Register, Roadmap, Freeze Boundary | Traceability Matrix, reviews, commits |
| `RC8_TRACEABILITY_MATRIX.md` | End-to-end management traceability | Project management | All preceding management artifacts | Reviews, post-commit and push confirmation |

## 10. Protected-File Rule

Management baseline creation and updates must not edit protected, historical, immutable, version-bound, evidence, manifest, validator-implementation, or identity-bearing surfaces identified in `RC8_FREEZE_BOUNDARY.md` and `CURRENT_CONTRACT_INDEX.md`, including at minimum:

- Immutable tag identities and historical release records
- `external_verifications/grok-build/evidence/`
- `external_verifications/grok-build/witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json`
- `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md`
- `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md`
- `external_verifications/grok-build/witness-package/PACKAGE_FILE_MANIFEST.txt`
- `external_verifications/grok-build/witness-package/scripts/VALIDATOR.md`
- `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py`
- Witness package policy, runbook, requirement, classification, and submission files unless separately authorized
- Witness package security and redaction files, including `external_verifications/grok-build/witness-package/WITNESS_SECURITY_AND_REDACTION.md`, unless separately authorized
- Historical receipts

This baseline implementation pass may create only the eight root-level management artifacts listed in Section 9.

## 11. Review and Approval Model

Management work uses the gate model defined across the baseline, including at minimum:

| Gate ID | Gate name |
|---|---|
| `GATE-01` | Freeze Boundary |
| `GATE-02` | Issue Classification |
| `GATE-03` | Contract Index Integrity |
| `GATE-04` | Work Package Scope |
| `GATE-05` | Pre-Implementation Authorization |
| `GATE-06` | Internal Review |
| `GATE-07` | Evidence and Traceability Review |
| `GATE-08` | Pre-Commit Review |
| `GATE-09` | Post-Commit Review |
| `GATE-10` | Push Authorization |
| `GATE-11` | Witness Handoff Stability |
| `GATE-12` | Formal Source Evaluation Boundary |

Gate results are management-control results only. They are not formal technical audit results, Source decisions, witness results, validator results, or readiness decisions.

Review results use: `No Objection`, `Revision Required`, `Blocked`, `Out of Scope`, `Not Evaluated`.

Review results are management-review results only. They do not declare READY or NOT READY, do not authorize Independent Witness execution, do not establish Source disposition, and do not close findings or blockers.

## 12. Update Triggers

- Lifecycle boundary changes stated by authoritative lifecycle sources
- Formal decision authority designation
- New management artifact added to the baseline set
- Role model change
- Governance gate change

## 13. Ownership

Repository maintainer.

## 14. Entry Criteria

- RC8 freeze direction accepted as stated in `STATUS.md` and related lifecycle sources.
- Eight-artifact management baseline set accepted in principle.

## 15. Exit Criteria

- Role model, governance rules, and artifact hierarchy defined in this charter.
- Cross-references to the other seven management artifacts present.

## 16. Acceptance Criteria

- No technical authority claims beyond management scope.
- No protected-file override.
- No READY or NOT READY decision newly declared.
- No C-014 completion claim.
- No finding or blocker marked CLEAR, CLOSED, or RESOLVED.
- No Independent Witness authorization.
- No RC9 or future-candidate authorization.

## 17. References

### Existing repository files

- `README.md`
- `STATUS.md`
- `REPRODUCE.md`
- `ROADMAP.md`
- `external_verifications/grok-build/README.md`
- `external_verifications/grok-build/WITNESS_HANDOFF.md`
- `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`

### RC8 management baseline set

- `RC8_FREEZE_BOUNDARY.md`
- `CURRENT_CONTRACT_INDEX.md`
- `FUTURE_CANDIDATE_BACKLOG.md`
- `RC8_ISSUE_REGISTER.md`
- `RC8_REMAINING_WORK_ROADMAP.md`
- `RC8_WORK_PACKAGE_PLAN.md`
- `RC8_TRACEABILITY_MATRIX.md`
