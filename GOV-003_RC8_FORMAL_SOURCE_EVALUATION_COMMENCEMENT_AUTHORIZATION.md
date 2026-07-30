# GOV-003 — RC8 Formal Source Evaluation Commencement Authorization

> **Management artifact notice**
>
> This document is a non-authoritative project-management governance Decision Record for Weaver Forge RC8.
>
> It records an evaluation-commencement authorization governance action only. It does not perform Formal Source Evaluation, does not issue READY or NOT READY, does not authorize Independent Witness execution, does not claim C-014 completion, does not mark any finding or blocker CLEAR or CLOSED, and does not authorize RC9 or any future candidate.
>
> It does not modify technical contracts, package identity, validator behavior, manifests, evidence, witness requirements, historical verdicts, protected files, immutable tags, or version-bound records.
>
> Where this document references lifecycle, package, validator, manifest, evidence, identity, witness, or contract material, the referenced repository files remain authoritative within their own stated scope.

## Decision Record

| Field | Value |
|---|---|
| **Decision ID** | `GOV-003` |
| **Decision class** | `Evaluation Authorization` |
| **Subject** | Authorization to commence the RC8 Formal Source Evaluation instance scoped by accepted `GOV-002` |
| **Related references** | `GOV-002`; `ISSUE-RC8-004`; `TRACE-RC8-004`; `FC-001`; `GATE-12`; `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §6 item 8, §9.2 |
| **Role capacity invoked** | `Repository maintainer` (recording commencement authorization under repository-maintainer management scope; evaluation to be conducted under `Formal decision authority` as designated by accepted `GOV-002`) |
| **Designation status** | `Not applicable` — authority designation is recorded in `GOV-002`; this record authorizes commencement only |
| **Scope** | Identical to `GOV-002` Section 1 (Scope and exclusions); no scope expansion permitted |
| **Independence statement** | Commencement authorization is not Independent Witness authorization. This evaluation instance is not Independent Witness execution. Author/implementer self-certification is not claimed. Pi Management Review, Advisory Review, and backlog placement are not Formal Source Evaluation. |
| **Authorization effect** | Upon acceptance, and only after accepted `GOV-002`, permits the designated **Formal decision authority** to **commence** the scoped RC8 Formal Source Evaluation instance. This record does not itself perform evaluation. Designated authority may not expand scope beyond `GOV-002`. Commencement does not authorize protected-file edits, validator or executable activity, technical implementation, Independent Witness, RC9, or C-014 completion unless separately and explicitly authorized by controlling governance. |
| **Recorded outcome** | Not recorded — no Formal Source Evaluation disposition exists in this record |
| **Non-claims** | Not Independent Witness authorization; not RC9 authorization; not protected-file edit authorization; not C-014 completion; not READY or NOT READY; not technical implementation authorization; not validator or executable activity authorization; not alteration of immutable RC6 or RC7 historical NOT READY records; not authorization for designated authority to grant itself powers beyond `GOV-002` scope |
| **Recorder** | `Repository maintainer` (role capacity) |
| **Date** | 2026-07-30 |
| **Status** | `Proposed` |

## 1. Preconditions acknowledged

This commencement authorization is recorded subject to the governance preconditions in `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §6. Upon acceptance of both `GOV-002` and this record:

| Precondition | Acknowledgment |
|---|---|
| Planning Package complete and respected | `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PLANNING_PACKAGE.md` referenced; not contradicted |
| Governance Package accepted as framework | `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` is the applicable framework; its existence is not evaluation performance |
| Authority designated | Satisfied by accepted `GOV-002` |
| `GATE-12` recognized | Formal Source Evaluation Boundary separates advisory opinion from formal Source decision |
| Lifecycle posture readable | `STATUS.md`, `README.md` — no formal Source Weaver READY/NOT READY for RC8; Independent Witness not authorized/performed |
| Freeze and protected-file constraints accepted | `RC8_FREEZE_BOUNDARY.md`; protected surfaces not authorized for edit by this commencement |
| Backlog visibility without false authorization | `FC-001` / `ISSUE-RC8-004` visible; backlog placement is not authorization |
| Separate evaluation authorization | This record (`GOV-003`) |
| Independence statement | Recorded in Decision Record fields above |
| Required inputs available | Inputs in `GOV-002` §1.2 identified by reference; unavailable items listed in `GOV-002` §1.4 |

## 2. Commencement boundary

### 2.1 What acceptance of this record permits

- Entry into the **Evaluation** lifecycle stage (`FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §9.3) for the single RC8 Formal Source Evaluation instance scoped by `GOV-002`
- Formal disposition recording only through later Decision Records under §8.1 structure, if and when actually decided

### 2.2 What acceptance of this record does not permit

- Performing evaluation by the act of accepting this record
- Issuing READY or NOT READY by this record
- Independent Witness authorization or execution
- RC9 authorization
- C-014 completion or status change
- Protected-file, validator, manifest, identity, evidence, or contract modification
- Validator or executable technical verification unless separately and explicitly authorized
- Technical implementation
- Modification of immutable RC6 or RC7 NOT READY historical records
- Presumption of readiness, pass thresholds, or evaluation criteria not defined by controlling governance

### 2.3 Evaluation conduct constraints

Any evaluation conducted under this authorization must:

- Remain within `GOV-002` scope
- Distinguish confirmed facts, unresolved matters, and matters outside scope in findings
- Record unavailable evidence as unavailable, not presumed
- Not treat advisory, Pi, management, or backlog artifacts as formal outcome records

## 3. What this record is not

- Not Formal Source Evaluation performance (evaluation begins only after acceptance and explicit commencement under designated authority)
- Not READY or NOT READY issuance
- Not evaluation closure (closure requires separate `Evaluation Closure` Decision Record per governance framework)

## 4. References

- `GOV-002_RC8_FORMAL_SOURCE_EVALUATION_AUTHORITY_DESIGNATION.md`
- `FORMAL_SOURCE_EVALUATION_GOVERNANCE_PACKAGE.md` §6, §8.1, §9.2–§9.3
