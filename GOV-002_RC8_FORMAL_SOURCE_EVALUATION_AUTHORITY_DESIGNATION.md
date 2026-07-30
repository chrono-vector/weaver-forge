# GOV-002 — RC8 Formal Source Evaluation Authority Designation

> **Management artifact notice**
>
> This document is a non-authoritative project-management governance Decision Record for Weaver Forge RC8.
>
> It records an authority-designation governance action only. It does not perform Formal Source Evaluation, does not issue READY or NOT READY, does not authorize Independent Witness execution, does not claim C-014 completion, does not mark any finding or blocker CLEAR or CLOSED, and does not authorize RC9 or any future candidate.
>
> It does not modify technical contracts, package identity, validator behavior, manifests, evidence, witness requirements, historical verdicts, protected files, immutable tags, or version-bound records.
>
> Where this document references lifecycle, package, validator, manifest, evidence, identity, witness, or contract material, the referenced repository files remain authoritative within their own stated scope.

## Decision Record

| Field | Value |
|---|---|
| **Decision ID** | `GOV-002` |
| **Decision class** | `Authority Designation` |
| **Subject** | Designation of Formal decision authority role capacity to conduct the RC8 Formal Source Evaluation instance routed by `FC-001` / `ISSUE-RC8-004` / `TRACE-RC8-004` under `GATE-12` |
| **Related references** | `ISSUE-RC8-004`; `TRACE-RC8-004`; `FC-001`; `GATE-12`; `PROJECT_CHARTER.md` §7; `RC8_FREEZE_BOUNDARY.md`; `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PLANNING_PACKAGE.md`; `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §5; `GOV-001` (management-baseline acceptance only; not prior Formal Source Evaluation designation) |
| **Role capacity invoked** | `Repository maintainer` (recording designation under `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §5.2 D-4 repository-maintainer management scope) |
| **Designation status** | `Designated` upon acceptance of this record — scoped **Formal decision authority** role capacity for the RC8 Formal Source Evaluation instance identified in the Scope field below |
| **Designated role capacity** | `Formal decision authority` — existing charter role capacity (`PROJECT_CHARTER.md` §7); no personal name, organization, or external reviewer is designated |
| **Scope** | See Section 1 below |
| **Independence statement** | This designation does not confer Independent Witness authority. Author/implementer self-certification is not claimed as a substitute for designated formal Source process or for Independent Witness. Advisory Review, Pi Management Review, management baseline acceptance (`GOV-001`), and backlog placement (`FC-001`) are not Formal Source Evaluation. |
| **Authorization effect** | Upon acceptance, creates scoped **Formal decision authority** capacity to conduct the single RC8 Formal Source Evaluation instance described in Scope. This record does not itself commence evaluation; commencement requires accepted `GOV-003`. Designated authority may not expand its own scope beyond this record and `GOV-003`. Designated authority may not authorize protected-file edits, validator or executable activity, technical implementation, Independent Witness, RC9, or C-014 completion unless separately and explicitly authorized by controlling governance. |
| **Recorded outcome** | Not recorded — no Formal Source Evaluation disposition exists in this record |
| **Non-claims** | Not Independent Witness authorization; not RC9 authorization; not protected-file edit authorization; not C-014 completion; not READY or NOT READY; not technical implementation authorization; not validator or executable activity authorization; not alteration of immutable RC6 or RC7 historical NOT READY records |
| **Recorder** | `Repository maintainer` (role capacity) |
| **Date** | 2026-07-30 |
| **Status** | `Proposed` |

## 1. Scope and exclusions

### 1.1 Evaluation subject

Formal Source Weaver evaluation disposition boundary for Weaver Forge RC8 (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`), as routed by `FC-001` and classified by `ISSUE-RC8-004`, under `GATE-12` Formal Source Evaluation Boundary.

### 1.2 Included surfaces (by reference only)

Evaluation authority under this designation is limited to review and disposition recording against the committed repository state and evidence expressly identified by the controlling documents below. No surface is redefined by this record.

| Input / surface | Purpose |
|---|---|
| `PROJECT_CHARTER.md` | Role model; `GATE-12` |
| `RC8_FREEZE_BOUNDARY.md` | Freeze and `GATE-12` management boundary |
| `CURRENT_CONTRACT_INDEX.md` | Navigation to contract, lifecycle, validator, manifest, evidence, and witness surfaces |
| `RC8_TRACEABILITY_MATRIX.md` | Management traceability including `TRACE-RC8-004` |
| `RC8_ISSUE_REGISTER.md` | Issue classification including `ISSUE-RC8-004` |
| `FUTURE_CANDIDATE_BACKLOG.md` | Backlog routing including `FC-001` |
| `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PLANNING_PACKAGE.md` | Planning-boundary reference |
| `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` | Governance framework reference |
| Authoritative lifecycle sources | `STATUS.md`, `README.md`, and related lifecycle surfaces cited by the above (by reference only) |
| RC8 identity references | As stated in `RC8_FREEZE_BOUNDARY.md` §6 and `STATUS.md` §1 (tag `grok-build-witness-v1.0.0-rc8`; peeled commit `1de4b4d9523711418390f8331c95988523ef4481`; tree `87b40d8a32ca536a4cdba0eee474f6171c62f6bb`) |
| Repository commit at initiation | `aecac167625d7951bdce727158596f9f8607c4d4` (includes Governance Package; evaluation instances must cite the commit they inspect) |

### 1.3 Explicit exclusions

- Immutable historical RC6 and RC7 NOT READY records — remain unchanged; not reopened or revised by this designation
- Independent Witness authorization, handoff, reproduction, or PASS — separate later decision (`FC-002`; `GATE-11`)
- RC9 or any future-candidate creation or implementation — not authorized
- C-014 completion or disposition change — remains unchanged unless separately and explicitly evaluated
- Protected, version-bound, validator, manifest, identity, evidence, or contract surface modification — not authorized
- Validator execution, product binary execution, Docker, Cargo, Rust, DotSlash, protoc, ldd, builds, or other executable technical verification — prohibited unless separately and explicitly authorized by controlling governance
- Technical implementation or protected-file modification — not authorized
- Evaluation criteria, scoring, pass percentages, automatic thresholds, or presumptions of readiness — not defined by this record

### 1.4 Unavailable evidence

The following remain **unavailable** or **not currently identified** in repository management surfaces and must not be presumed:

| Item | Status |
|---|---|
| Formal Source Weaver decision authority holder by personal name | Not currently identified — designation is by role capacity only |
| Pi Management Review of this designation (`REVIEW-PI-NNN`) | Not currently identified |
| Formal scoped evaluation plan document beyond governance framework | Not currently identified beyond existing package and audit surfaces (`FC-001` notes) |
| Whether current `main` equals RC8 peeled commit beyond identities stated in `STATUS.md` | Not re-derived; relationship recorded as not re-derived in `STATUS.md` |

Unavailable items do not block this designation record; they must be recorded as unavailable during any later evaluation, not presumed.

### 1.5 Evaluation finding categories (for later evaluation only)

When evaluation later occurs under accepted authorization, findings must distinguish:

1. **Confirmed facts** — directly supported by cited authoritative or committed repository surfaces
2. **Unresolved matters** — gaps, conflicts, or items marked not verified / not currently identified
3. **Matters outside scope** — items explicitly excluded above or outside `GATE-12` formal Source decision boundary

## 2. What this record is not

- Not Formal Source Evaluation performance
- Not READY or NOT READY issuance
- Not evaluation commencement (see `GOV-003`)
- Not collapse of Formal Source Evaluation with Independent Witness, RC9 authorization, or management baseline acceptance

## 3. References

- `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §5, §6 item 3, §8.1
- `GOV-003_RC8_FORMAL_SOURCE_EVALUATION_COMMENCEMENT_AUTHORIZATION.md` (companion commencement authorization; required before evaluation start)
