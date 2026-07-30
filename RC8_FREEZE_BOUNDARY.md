# RC8 Freeze Boundary

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

Define the RC8 freeze boundary and separate allowed management work from prohibited RC8 changes and future-candidate work.

## 2. Scope

- RC8 identity references as stated by existing repository sources
- Frozen surfaces and freeze rules for RC8 management planning
- Permitted management-only work under the freeze
- Prohibited RC8 work
- Future-candidate deferral rule
- Independent Witness boundary relative to RC8 freeze
- Freeze-compatibility vocabulary for management routing
- Required gates for freeze-related decisions

## 3. Out of Scope

- Changing package identity, tags, manifests, validators, evidence, or protected files
- Declaring READY or NOT READY
- Authorizing Independent Witness execution
- Authorizing RC9 or any future candidate
- Closing findings or blockers
- Completing C-014

## 4. Authority

This document defines management freeze-boundary rules for planning and routing work related to Weaver Forge RC8. It applies only to management classification and disposition.

## 5. Non-Authority

This document does not supersede `STATUS.md`, `README.md`, `REPRODUCE.md`, `external_verifications/grok-build/README.md`, `external_verifications/grok-build/witness-package/README.md`, `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`, `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md`, `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md`, or any other lifecycle, identity, manifest, validator, evidence, or witness authority surface.

## 6. RC8 Identity References

Identity values below are copied from repository-stated sources for navigation only. Source documents remain authoritative.

| Item | Value | Source |
|---|---|---|
| Package version label | `1.0.0-rc8` | `STATUS.md`, `README.md`, package status surfaces |
| Tag | `grok-build-witness-v1.0.0-rc8` | `STATUS.md` section 1 |
| Annotated tag object | `8113d952d3b127d32e138dbf804141f5d1dfb26f` | `STATUS.md` section 1 |
| Peeled commit | `1de4b4d9523711418390f8331c95988523ef4481` | `STATUS.md` section 1 |
| Tree | `87b40d8a32ca536a4cdba0eee474f6171c62f6bb` | `STATUS.md` section 1 |
| Lifecycle posture | Immutable static-audit candidate | `STATUS.md` section 3; `README.md` RC8 current lifecycle status |
| Formal Source Weaver READY/NOT READY for RC8 | None exists | `STATUS.md` section 3 |
| Independent Witness | Not authorized; not performed | `STATUS.md` section 3 |
| C-014 | `NOT_STARTED` | `STATUS.md` section 3; `CLAIM_REGISTER.md` |
| RC9 | Not authorized | `STATUS.md` section 3; `LIFECYCLE_CLARIFICATION.md` |

Whether current `main` equals the RC8 peeled commit is not re-derived here. `STATUS.md` records `main` / `origin/main` as `35de09a3a8a30d2e321856b721ad92b3cd31edf8` and states that relationship was not re-derived beyond confirmed identities.

## 7. Frozen Surfaces

| Surface | Repository path or identity | Freeze rule | Protected status | Notes |
|---|---|---|---|---|
| RC8 tag identity | `grok-build-witness-v1.0.0-rc8` | Must not be moved, deleted, force-updated, or redefined by management docs | Protected / immutable | Exact identities in `STATUS.md` |
| RC8 annotated tag object | `8113d952d3b127d32e138dbf804141f5d1dfb26f` | Immutable reference | Protected / immutable | Git fact in `STATUS.md` |
| RC8 peeled commit | `1de4b4d9523711418390f8331c95988523ef4481` | Immutable reference | Protected / immutable | Git fact in `STATUS.md` |
| RC8 tree | `87b40d8a32ca536a4cdba0eee474f6171c62f6bb` | Immutable reference | Protected / immutable | Git fact in `STATUS.md` |
| RC6 / RC7 historical records | Tags and historical NOT READY records | Remain immutable historical NOT READY | Protected / historical | `STATUS.md`, `README.md` |
| Existing immutable RC8 artifact bytes | Artifact / archive / bundle surfaces referenced by package docs | Must not be changed | Protected / immutable | `STATUS.md` section 3 |
| Evidence directory | `external_verifications/grok-build/evidence/` | No management-baseline edits | Protected / evidence | Blueprint protected-file rule |
| Outcome contract | `external_verifications/grok-build/witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json` | No management-baseline edits | Protected / contract | Blueprint protected-file rule |
| Package version record | `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md` | Preserved unchanged; may retain historical wording | Protected / version-bound | `LIFECYCLE_CLARIFICATION.md` |
| Package manifest | `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md` | Preserved unchanged | Protected / version-bound | `LIFECYCLE_CLARIFICATION.md` |
| Package file manifest | `external_verifications/grok-build/witness-package/PACKAGE_FILE_MANIFEST.txt` | Preserved unchanged | Protected / version-bound | Inventory surface |
| Validator documentation | `external_verifications/grok-build/witness-package/scripts/VALIDATOR.md` | Preserved unchanged | Protected / version-bound | `LIFECYCLE_CLARIFICATION.md` |
| Validator implementation | `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py` | No management-baseline edits | Protected / validator | Blueprint protected-file rule |
| Witness requirements | `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md` | Frozen/protected for RC8 management-baseline purposes; must not be edited unless separately authorized | Protected | Not modified by this baseline |
| Witness runbook | `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md` | Frozen/protected for RC8 management-baseline purposes; must not be edited unless separately authorized | Protected | Not modified by this baseline |
| Package readiness policy | `external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md` | Frozen/protected for RC8 management-baseline purposes; must not be edited unless separately authorized | Protected | Not modified by this baseline |
| Witness classification | `external_verifications/grok-build/witness-package/WITNESS_CLASSIFICATION.md` | Frozen/protected or mixed-preserved for RC8 management-baseline purposes; must not be edited unless separately authorized | Mixed / preserved | `LIFECYCLE_CLARIFICATION.md`; not modified by this baseline |
| Witness submission | `external_verifications/grok-build/witness-package/WITNESS_SUBMISSION.md` | Frozen/protected or mixed-preserved for RC8 management-baseline purposes; must not be edited unless separately authorized | Mixed / preserved | `LIFECYCLE_CLARIFICATION.md`; not modified by this baseline |
| Maintainer intake policy | `external_verifications/grok-build/witness-package/MAINTAINER_INTAKE_POLICY.md` | Frozen/protected or mixed-preserved for RC8 management-baseline purposes; must not be edited unless separately authorized | Mixed / preserved | `LIFECYCLE_CLARIFICATION.md`; not modified by this baseline |
| Witness security and redaction | `external_verifications/grok-build/witness-package/WITNESS_SECURITY_AND_REDACTION.md` | Frozen/protected or mixed-preserved for RC8 management-baseline purposes; must not be edited unless separately authorized | Protected or mixed-preserved | Not modified by this baseline |
| Historical receipts | `receipts/` | Historical evidence; not rewritten by this baseline | Historical receipt | Project evidence layer |
| Claim register and owner verification records | `external_verifications/grok-build/CLAIM_REGISTER.md` and related owner records | Not redefined by management docs | Editable owner surfaces remain authoritative within scope; not superseded here | Index only via `CURRENT_CONTRACT_INDEX.md` |

## 8. Permitted Management Work

The following work is RC8-compatible when non-authoritative and freeze-preserving:

- Creating or updating the eight root-level RC8 management baseline documents
- Indexing existing contract, lifecycle, validator, manifest, evidence, and witness surfaces without redefining them
- Classifying issues and routing contract-changing work to `FUTURE_CANDIDATE_BACKLOG.md`
- Defining Work Packages that exclude protected-file and contract-changing work
- Performing management reviews and gate evaluations under management vocabularies
- Referencing existing lifecycle and identity facts without changing them

Management documentation may be created only if non-authoritative.

## 9. Prohibited RC8 Work

The following are not RC8 freeze-compatible management work:

- Changing package identity, tags, peeled commits, trees, archives, bundles, checksums, or release identities
- Changing validator behavior or validator implementation
- Changing manifests or outcome contracts
- Changing evidence records or historical receipts
- Changing protected or version-bound witness-package files listed in Section 7
- Declaring RC8 READY or NOT READY as a new decision
- Claiming C-014 completion
- Marking findings or blockers CLEAR, CLOSED, or RESOLVED
- Authorizing Independent Witness execution
- Authorizing RC9 or creating a future candidate
- Treating Work Package completion as technical finding closure
- Treating Source advisory opinion as formal Source decision without designation

## 10. Future-Candidate Deferral Rule

Contract-changing, scope-changing, identity-changing, validator-changing, manifest-changing, evidence-changing, or otherwise non-RC8 work must be deferred to `FUTURE_CANDIDATE_BACKLOG.md`.

Future Candidate backlog placement is not future candidate authorization, not RC9 authorization, not implementation authorization, not release authorization, and not Independent Witness handoff authorization.

## 11. Independent Witness Boundary

Independent Witness activity remains separate from author implementation and from this management baseline.

- Independent Witness was not authorized and was not performed, per `STATUS.md`.
- C-014 remains NOT_STARTED.
- Author implementation cannot be counted as Independent Witness completion.
- `GATE-11` Witness Handoff Stability applies before any separately authorized witness handoff.
- These management artifacts do not authorize Independent Witness execution.

## 12. Freeze Compatibility Vocabulary

Use the following values when stating RC8 freeze compatibility in management tables:

| Value | Meaning |
|---|---|
| `Compatible` | Management-only or otherwise freeze-preserving work allowed under RC8 freeze |
| `Conditional` | Potentially compatible only with explicit conditions and required gates; no implementation by default |
| `Deferred` | Not RC8 work; route to Future Candidate Backlog |
| `Prohibited` | Not allowed under RC8 freeze |
| `Not Applicable` | Freeze compatibility does not apply to the item |

`Compatible` and `Conditional` do not authorize protected-file edits, READY/NOT READY decisions, Independent Witness execution, C-014 completion, finding/blocker closure, or RC9.

### Freeze Compatibility

| Work type | RC8-compatible? | Required disposition | Required gate | Notes |
|---|---|---|---|---|
| Create non-authoritative RC8 management baseline docs | `Compatible` | RC8 Work Package | `GATE-01`, `GATE-04`, `GATE-05` | Eight root-level management files only |
| Index existing contracts without redefining them | `Compatible` | RC8 Work Package | `GATE-03` | `CURRENT_CONTRACT_INDEX.md` |
| Classify issues and route work | `Compatible` | RC8 Work Package | `GATE-02` | Management classification only |
| Edit protected/version-bound package files | `Prohibited` | Rejected / Not Applicable or Future Candidate if separately scoped later | `GATE-01` | Includes version, manifest, validator surfaces listed above |
| Contract-changing package remediation | `Deferred` | Future Candidate Backlog | `GATE-01`, `GATE-12` as applicable | Not RC8 freeze work |
| Independent Witness execution | `Prohibited` under current authorization state | Independent Witness Handoff routing only | `GATE-11` | Not authorized per `STATUS.md` |
| Declare RC8 READY/NOT READY | `Prohibited` | Governance Decision / Rejected | `GATE-12` | No formal Source decision exists; management docs must not invent one |
| Authorize RC9 | `Prohibited` | Rejected / Not Applicable | `GATE-01` | RC9 not authorized |

## 13. Required Gates

| Gate ID | Gate name | Purpose | Required inputs | Responsible role | Pass conditions | Conditional Pass conditions | Fail conditions | Required evidence | Permitted next state | Prohibited next state |
|---|---|---|---|---|---|---|---|---|---|---|
| `GATE-01` | Freeze Boundary | Confirm RC8 freeze and identify prohibited work | This document, `STATUS.md`, lifecycle references | Repository maintainer + Pi read-only reviewer | Work is management-only or explicitly RC8-compatible | Minor wording issue with no boundary change | Contract-changing or protected-file change proposed for RC8 | Freeze-boundary review note | Issue classification | Implementation of prohibited work |
| `GATE-11` | Witness Handoff Stability | Confirm witness handoff is stable if applicable | Witness handoff docs, WP outputs | Formal decision authority + witness boundary reviewer | Handoff material is stable and separate authorization exists | Not applicable or deferred | Author claims witness completion or handoff without authorization | Handoff stability note | Witness handoff only if authorized | Independent Witness execution without authorization |
| `GATE-12` | Formal Source Evaluation Boundary | Separate Source opinion from formal Source decision | Source review refs, decision records | Formal Source authority if designated | Formality level is explicit | Advisory opinion labeled correctly | Advisory review presented as formal decision | Source boundary note | Candidate planning or deferral | READY/NOT READY claim |

Gate results are management-control results only. They are not formal technical audit results, Source decisions, witness results, validator results, or readiness decisions.

## 14. Update Triggers

- New RC tag, peel, or tree identity recorded by authoritative sources
- Change in protected-file inventory stated by lifecycle clarification or maintainer authority
- New class of prohibited or permitted management work
- Independent Witness authorization status change stated by authoritative sources
- Formal Source evaluation boundary change

## 15. Ownership

Repository maintainer.

## 16. Entry Criteria

- RC8 identity and lifecycle posture available in `STATUS.md` / `README.md`.
- `PROJECT_CHARTER.md` role and governance model available.

## 17. Exit Criteria

- Frozen surfaces listed.
- Permitted and prohibited work distinguished.
- Future-candidate deferral rule stated.
- Independent Witness boundary stated.

## 18. Acceptance Criteria

- RC8 is treated as frozen.
- Contract-changing work is not classified as RC8 work.
- Management documentation is non-authoritative.
- Future Candidate backlog placement is not future-candidate authorization.
- No READY/NOT READY decision newly declared.
- No protected file modified by this document.

## 19. References

### Existing repository files

- `STATUS.md`
- `README.md`
- `REPRODUCE.md`
- `external_verifications/grok-build/README.md`
- `external_verifications/grok-build/CLAIM_REGISTER.md`
- `external_verifications/grok-build/witness-package/README.md`
- `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md`
- `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md`
- `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md`

### RC8 management baseline set

- `PROJECT_CHARTER.md`
- `CURRENT_CONTRACT_INDEX.md`
- `FUTURE_CANDIDATE_BACKLOG.md`
- `RC8_ISSUE_REGISTER.md`
- `RC8_WORK_PACKAGE_PLAN.md`
- `RC8_TRACEABILITY_MATRIX.md`
