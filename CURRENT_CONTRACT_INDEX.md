# Current Contract Index

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

Index contract-bearing, contract-adjacent, lifecycle, policy, manifest, validator, evidence, and witness-package files without redefining them.

## 2. Scope

- Indexing repository paths relevant to RC8 management planning
- Classifying authority type, lifecycle status, protected/editable status, and change-control requirement
- Providing stable `CONTRACT-IDX-NNN` identifiers for cross-document references

## 3. Out of Scope

- Creating new technical contracts
- Redefining validator, manifest, evidence, identity, or witness rules
- Changing package identity
- Declaring READY or NOT READY
- Authorizing Independent Witness execution
- Closing findings or blockers

## 4. Authority

This document is an index only. Indexed files remain authoritative within their own stated scope.

## 5. Non-Authority

This index does not become a substitute for `STATUS.md`, `README.md`, witness-package policies, manifests, validators, evidence records, claim registers, or identity documents. If this index conflicts with an indexed file, the indexed file controls within its stated scope.

## 6. Index Rules

- Every row is navigational only.
- Authority type classifies the indexed file; it does not create new authority.
- `Protected or editable` describes management-baseline edit expectations, not a license to edit outside separate authorization.
- Historical wording in protected or mixed files must be interpreted using `LIFECYCLE_CLARIFICATION.md` and current lifecycle sources where those sources state current interpretation.
- Missing related surfaces are marked `Not currently identified` rather than invented.
- Index IDs are stable once assigned and must not be renumbered after publication.

## 7. Authority Type Vocabulary

Use exactly:

- `Lifecycle status`
- `Project documentation`
- `External verification record`
- `Claim register`
- `Source identity`
- `Witness package policy`
- `Witness package manifest`
- `Validator documentation`
- `Validator implementation`
- `Outcome contract`
- `Evidence record`
- `Historical receipt`
- `Template`
- `Management artifact`

## 8. Contract and Lifecycle Index

| Index ID | Repository path | Category | Authority type | Lifecycle status | Current or historical | Protected or editable | Change-control requirement | Related validator/manifest/evidence surface | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `CONTRACT-IDX-001` | `README.md` | lifecycle / project-meta | Lifecycle status | States RC8 immutable static-audit candidate; RC6/RC7 historical NOT READY; C-014 NOT_STARTED; overall PARTIAL | Current | Editable current surface; immutable RC8 tag may preserve older README bytes | Do not use management docs to redefine lifecycle | Package table; RC8 lifecycle section | Prefer with `STATUS.md` for current lifecycle |
| `CONTRACT-IDX-002` | `STATUS.md` | lifecycle | Lifecycle status | Owner-supplied RC8 lifecycle authority; RC9 not authorized | Current | Editable lifecycle authority surface | Lifecycle wording changes require explicit maintainer control | References README and external_verifications | Separates Git facts, repo-stated facts, owner authority, stale evidence |
| `CONTRACT-IDX-003` | `REPRODUCE.md` | lifecycle / governance | Lifecycle status | Restates RC8 boundary; IW not authorized/performed; C-014 NOT_STARTED | Current | Editable guide bound to STATUS/README | Must remain consistent with STATUS/README | Local receipt validation docs | Does not authorize SW audit, IW, RC9, or artifact mutation |
| `CONTRACT-IDX-004` | `external_verifications/grok-build/README.md` | lifecycle / identity | Lifecycle status | RC8 current; RC6/RC7 historical NOT READY; C-014 NOT_STARTED; overall PARTIAL | Current | Editable current status surface | Align with STATUS/README | Immutable release table rc1–rc8 | Grok Build verification entry |
| `CONTRACT-IDX-005` | `external_verifications/grok-build/witness-package/README.md` | lifecycle / witness | Lifecycle status | Current candidate RC8; IW handoff not authorized | Current | Editable package entry | Align with STATUS/README | Package constants and releases table | Product execution forbidden by package scope |
| `CONTRACT-IDX-006` | `external_verifications/grok-build/witness-package/LIFECYCLE_CLARIFICATION.md` | lifecycle | Lifecycle status | Companion interpretation; RC8 static-audit candidate; no RC9; protected/mixed lists | Current | Editable clarification companion | Must not supersede protected files | Lists protected and mixed files | Not a verdict or readiness decision |
| `CONTRACT-IDX-007` | `external_verifications/grok-build/WITNESS_HANDOFF.md` | witness / lifecycle | External verification record | Owner handoff; IW unassigned / NOT_STARTED; RC8 lifecycle current | Current | Editable owner handoff | Not IW authorization | Points to package and evidence inventory | Prepared 2026-07-29 per file |
| `CONTRACT-IDX-008` | `external_verifications/grok-build/VERDICT.md` | lifecycle / governance | External verification record | Owner-side multi-axis verdict; overall PARTIAL; IW NOT_STARTED | Current | Editable owner verdict | Do not treat as Independent Witness | Claim rollup C-001–C-027 | Verdict date 2026-07-29 per file |
| `CONTRACT-IDX-009` | `external_verifications/grok-build/RESULTS.md` | evidence / lifecycle | External verification record | Owner-side results; C-014 NOT_STARTED; package-readiness PARTIAL | Current | Editable results register | Align with claim register | Phase and claim tables | Not Independent Witness result |
| `CONTRACT-IDX-010` | `external_verifications/grok-build/CLAIM_REGISTER.md` | governance / identity | Claim register | C-014 NOT_STARTED; C-015 BLOCKED; C-019 PARTIAL; C-022 historical PASS / current readiness superseded | Current | Editable claim register | Claim ID and status changes require explicit control | Links to evidence paths | Authoritative for claim IDs within stated scope |
| `CONTRACT-IDX-011` | `external_verifications/grok-build/witness-package/PACKAGE_READINESS_POLICY.md` | governance / contract | Witness package policy | Normative readiness vocabulary; current status RC8 lifecycle banner; PARTIAL / not ready for IW handoff | Current | Editable policy (current-aligned) | Policy changes are contract-adjacent | Readiness table rc1–rc8 | Does not complete C-014 |
| `CONTRACT-IDX-012` | `external_verifications/grok-build/witness-package/WITNESS_REQUIREMENTS.md` | contract / witness | Witness package policy | RC8 lifecycle banner; outcome model; IW handoff not authorized by this doc | Current | Protected for RC8 management-baseline purposes | Must not be edited without separate authorization | Canonical constants | Execution not authorized by lifecycle |
| `CONTRACT-IDX-013` | `external_verifications/grok-build/witness-package/WITNESS_RUNBOOK.md` | witness / contract | Witness package policy | RC8 status banner; canonical constants include RC8 tag | Current | Protected for RC8 management-baseline purposes | Must not be edited without separate authorization | Validator and build scripts | Lifecycle does not authorize IW execution |

## 9. Validator and Manifest Index

| Index ID | Repository path | Category | Authority type | Lifecycle status | Current or historical | Protected or editable | Change-control requirement | Related validator/manifest/evidence surface | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `CONTRACT-IDX-014` | `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_VERSION.md` | identity / lifecycle | Witness package manifest | File content retains RC6 / pre-tag RC7-oriented wording; not current RC8 status per clarification | Historical / version-bound | Protected | Must not be edited by RC8 management baseline | Tag/archive identity tables | Interpret via `LIFECYCLE_CLARIFICATION.md` |
| `CONTRACT-IDX-015` | `external_verifications/grok-build/witness-package/WITNESS_PACKAGE_MANIFEST.md` | manifest / contract | Witness package manifest | Historical/version-bound manifest surface; inspected title retains `1.0.0-rc5` wording; current lifecycle interpretation is controlled by current lifecycle sources and `LIFECYCLE_CLARIFICATION.md` | Historical / version-bound | Protected | Must not be edited by RC8 management baseline | Required evidence file set | Inspected title retains `1.0.0-rc5` wording |
| `CONTRACT-IDX-016` | `external_verifications/grok-build/witness-package/PACKAGE_FILE_MANIFEST.txt` | manifest | Witness package manifest | Header retains RC6 FIXED_IMMUTABLE and pre-tag RC7 wording | Historical / version-bound | Protected | Must not be edited by RC8 management baseline | File inventory | Not current RC8 status surface |
| `CONTRACT-IDX-017` | `external_verifications/grok-build/witness-package/AUTHORITATIVE_OUTCOME_CONTRACT.json` | contract | Outcome contract | `contract_status=CONTRACT_DEFINED_ON_MAIN_IMPLEMENTATION_PENDING` per file; machine contract | Version-bound / normative machine surface | Protected | Must not be edited by RC8 management baseline | Outcome vocabulary | Does not claim current runtime compliance |
| `CONTRACT-IDX-018` | `external_verifications/grok-build/witness-package/scripts/VALIDATOR.md` | validator | Validator documentation | Structural validator docs; sampled sections retain pre-RC8 wording | Protected / version-bound | Protected | Must not be edited by RC8 management baseline | `validate_witness_evidence.py` | Structural PASS ≠ IW PASS / READY |
| `CONTRACT-IDX-019` | `external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py` | validator | Validator implementation | Structural validator implementation; package-tag map includes RC8 | Protected / executable normative surface | Protected | Must not be edited by RC8 management baseline | `VALIDATOR.md`; schemas | Do not execute in this management pass |
| `CONTRACT-IDX-020` | `external_verifications/grok-build/witness-package/MAINTAINER_INTAKE_POLICY.md` | governance / contract | Witness package policy | Intake vocabulary; identity footer retains RC6 / pre-tag RC7 | Mixed | Mixed / preserved unchanged by clarification | Separate authorization required to change | C-014 transition notes | Preserved per `LIFECYCLE_CLARIFICATION.md` |
| `CONTRACT-IDX-021` | `external_verifications/grok-build/witness-package/WITNESS_CLASSIFICATION.md` | contract / witness | Witness package policy | Verdict precedence; applies in RC6-oriented identity context in file | Mixed | Mixed / preserved | Separate authorization required to change | Classification rules | Preserved per clarification |
| `CONTRACT-IDX-022` | `external_verifications/grok-build/witness-package/WITNESS_SUBMISSION.md` | witness / governance | Witness package policy | PR submission path; identity footer RC6 / pre-tag RC7 | Mixed | Mixed / preserved | Separate authorization required to change | Validator command references | Preserved per clarification |
| `CONTRACT-IDX-023` | `external_verifications/grok-build/witness-package/WITNESS_SECURITY_AND_REDACTION.md` | governance / contract | Witness package policy | Redaction rules; identity footer lags current RC8 surfaces | Mixed / historically lagging footer | Protected or mixed-preserved for RC8 management-baseline purposes | Must not be edited without separate authorization | Never-redact list | Not a readiness decision |

## 10. Evidence and Witness Index

| Index ID | Repository path | Category | Authority type | Lifecycle status | Current or historical | Protected or editable | Change-control requirement | Related validator/manifest/evidence surface | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `CONTRACT-IDX-024` | `external_verifications/grok-build/SOURCE_IDENTITY.md` | identity | Source identity | Pin and identity layers recorded; IW of identity NOT_STARTED | Historical pin record | Treat as identity freeze / historical | Do not redefine pin via management docs | Pin `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` | Record date 2026-07-17 per file |
| `CONTRACT-IDX-025` | `external_verifications/grok-build/VERIFICATION_PLAN.md` | roadmap / governance | External verification record | Owner plan; Windows BLOCKED; IW NOT_STARTED; partially superseded by later RESULTS | Historical / planning | Editable but partially historical | Do not treat stale phase wording as current RC8 authority | Blockers B-001–B-013 | Prefer RESULTS/CLAIM_REGISTER for later state |
| `CONTRACT-IDX-026` | `external_verifications/grok-build/REPRODUCTION.md` | evidence | Evidence record | Owner-side reproduction PARTIAL; Witness note restates RC8 lifecycle | Historical owner evidence | Historical evidence surface | Do not mutate historical run records via management baseline | Command log / run IDs | Not Independent Witness |
| `CONTRACT-IDX-027` | `SELF_REPRODUCTION_AUDIT.md` | evidence | Evidence record | Blind self-reproduction audit 2026-07-12; not E4 | Historical | Historical | Preserve as historical | Receipts / Actions claims in file | Author self-reproduction only |
| `CONTRACT-IDX-028` | `WITNESS_REVIEW.md` | witness / evidence | Evidence record | Owner-workspace review 2026-06-30; not independent | Historical | Historical | Preserve as historical | Owner-authored review | Not Independent Witness |
| `CONTRACT-IDX-029` | `WITNESS_REVIEW_TEMPLATE.md` | witness | Template | Blank witness template | Template | Editable template | Template-only | Reproduced / Partially / Not reproduced | Does not authorize IW |
| `CONTRACT-IDX-030` | `E4_REPRODUCTION_PLAN.md` | governance / witness | Project documentation | Defines Independent Reproduction (E4) plan; does not claim E4 done | Plan / current template-like | Editable plan | Plan existence ≠ E4 completion | Independent third-party criteria | No RC8 package status claim verified in file |

## 11. Project Governance and Roadmap Index

| Index ID | Repository path | Category | Authority type | Lifecycle status | Current or historical | Protected or editable | Change-control requirement | Related validator/manifest/evidence surface | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `CONTRACT-IDX-031` | `ROADMAP.md` | roadmap | Project documentation | Phase 0 Launch (Current) through Phase 4; Phase 3 Witness Reviews | Current high-level roadmap | Editable | Distinct from RC8 remaining-work roadmap | Not currently identified | No RC8/C-014 language in file |
| `CONTRACT-IDX-032` | `PROJECT_METRICS.md` | project-meta | Project documentation | Snapshot as of 2026-07-05; stale relative to later audits | Historical / stale | Editable but stale | Do not treat as current lifecycle | Receipts/metrics claims | STATUS marks metrics not current |
| `CONTRACT-IDX-033` | `PROJECT_PODS.md` | project-meta | Project documentation | Starter pods; no lifecycle/RC claims | Current meta | Editable | Low change-control | Not currently identified | No RC claims |
| `CONTRACT-IDX-034` | `CONTRIBUTING.md` | governance | Project documentation | Evidence first; Contributor ≠ Witness | Current | Editable | Preserve Contributor ≠ Witness | Not currently identified | Governance culture |
| `CONTRACT-IDX-035` | `RECEIPT_TEMPLATE.md` | other | Template | Build-receipt sections including blockers | Template | Editable template | Template-only | `receipts/` | Not a verdict |
| `CONTRACT-IDX-036` | `PROJECT_CHARTER.md` | governance | Management artifact | RC8 management baseline charter | Current management | Management artifact created by baseline | Management update triggers in charter | Points to seven sibling artifacts | Non-authoritative |
| `CONTRACT-IDX-037` | `RC8_FREEZE_BOUNDARY.md` | governance | Management artifact | RC8 freeze boundary | Current management | Management artifact | Management update triggers in freeze boundary | Protected-surface list | Non-authoritative |
| `CONTRACT-IDX-038` | `FUTURE_CANDIDATE_BACKLOG.md` | future-candidate planning | Management artifact | Future Candidate backlog | Current management | Management artifact | Backlog placement ≠ authorization | Related issue IDs | Non-authoritative |
| `CONTRACT-IDX-039` | `RC8_ISSUE_REGISTER.md` | project management | Management artifact | Issue register | Current management | Management artifact | Status values are management-only | Traceability Matrix | Non-authoritative |
| `CONTRACT-IDX-040` | `RC8_REMAINING_WORK_ROADMAP.md` | project management | Management artifact | RC8 remaining-work roadmap | Current management | Management artifact | Distinct from `ROADMAP.md` | Gate sequence | Non-authoritative |
| `CONTRACT-IDX-041` | `RC8_WORK_PACKAGE_PLAN.md` | project management | Management artifact | Work Package plan | Current management | Management artifact | WP completion ≠ finding closure | Issue Register | Non-authoritative |
| `CONTRACT-IDX-042` | `RC8_TRACEABILITY_MATRIX.md` | project management | Management artifact | Traceability matrix | Current management | Management artifact | Trace rows ≠ technical closure | Issue / WP / FC IDs | Non-authoritative |
| `CONTRACT-IDX-043` | `CURRENT_CONTRACT_INDEX.md` | governance | Management artifact | This index | Current management | Management artifact | Index-only; no new authority | All indexed paths | Self-reference for completeness |

## 12. Protected and Version-Bound Surfaces

The following indexed entries are protected, version-bound, mixed-preserved, or historical for RC8 management-baseline purposes and must not be edited by this baseline:

- `CONTRACT-IDX-012` `WITNESS_REQUIREMENTS.md` (protected for RC8 management-baseline purposes)
- `CONTRACT-IDX-013` `WITNESS_RUNBOOK.md` (protected for RC8 management-baseline purposes)
- `CONTRACT-IDX-014` `WITNESS_PACKAGE_VERSION.md`
- `CONTRACT-IDX-015` `WITNESS_PACKAGE_MANIFEST.md`
- `CONTRACT-IDX-016` `PACKAGE_FILE_MANIFEST.txt`
- `CONTRACT-IDX-017` `AUTHORITATIVE_OUTCOME_CONTRACT.json`
- `CONTRACT-IDX-018` `scripts/VALIDATOR.md`
- `CONTRACT-IDX-019` `scripts/validate_witness_evidence.py`
- `CONTRACT-IDX-020` `MAINTAINER_INTAKE_POLICY.md` (mixed / preserved)
- `CONTRACT-IDX-021` `WITNESS_CLASSIFICATION.md` (mixed / preserved)
- `CONTRACT-IDX-022` `WITNESS_SUBMISSION.md` (mixed / preserved)
- `CONTRACT-IDX-023` `WITNESS_SECURITY_AND_REDACTION.md` (protected or mixed-preserved)
- `CONTRACT-IDX-024` `SOURCE_IDENTITY.md` (identity freeze / historical pin record)
- Evidence under `external_verifications/grok-build/evidence/` (directory; not exhaustively row-indexed here)
- Historical receipts under `receipts/`

`LIFECYCLE_CLARIFICATION.md` (`CONTRACT-IDX-006`) states that RC7-oriented wording remaining in protected or mixed files must not be interpreted as current RC8 lifecycle status.

## 13. Update Triggers

- New contract, policy, manifest, validator, evidence, or witness authority file introduced
- Protected/mixed classification change stated by lifecycle clarification or maintainer authority
- Lifecycle authority surface change in STATUS/README/package readiness policy
- New management artifact added to the baseline set

## 14. Ownership

Repository maintainer.

## 15. Entry Criteria

- `PROJECT_CHARTER.md` and `RC8_FREEZE_BOUNDARY.md` available.
- Required indexed files exist in the repository or are explicitly marked absent.

## 16. Exit Criteria

- Required files indexed with `CONTRACT-IDX-NNN` IDs.
- Authority types drawn from the controlled vocabulary.
- Index-only rule stated.

## 17. Acceptance Criteria

- Document remains index-only.
- No redefinition of validator, manifest, evidence, identity, or witness rules.
- Protected surfaces identified.
- No READY/NOT READY decision newly declared.
- References use actual repository paths.

## 18. References

### Existing repository files

All paths listed in Sections 8–11.

### RC8 management baseline set

- `PROJECT_CHARTER.md`
- `RC8_FREEZE_BOUNDARY.md`
- `FUTURE_CANDIDATE_BACKLOG.md`
- `RC8_ISSUE_REGISTER.md`
- `RC8_REMAINING_WORK_ROADMAP.md`
- `RC8_WORK_PACKAGE_PLAN.md`
- `RC8_TRACEABILITY_MATRIX.md`
