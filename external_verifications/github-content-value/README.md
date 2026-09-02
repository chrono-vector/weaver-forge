# GitHub Content & Practical Value Assessment — v0

This directory defines a **read-only advisory specification** for evaluating an arbitrary GitHub repository's published description against its actual contents, and for estimating practical adoption value.

It is a **GitHub-specific evaluation boundary**. It does not modify Weaver Forge receipt verification, VECTOR Package Ingress v0, Grok Build Witness, RC8, FC-04, Independent Witness (IW), Job Agent connectivity, or any existing verification state.

```text
Value Assessment ≠ Evidence
Value Assessment ≠ Certification
Value Assessment ≠ Security Audit
Value Assessment ≠ Independent Witness
Value Assessment ≠ Owner Acceptance
Recommendation ≠ Authorization
Repository description ≠ Verified capability
Test result ≠ General operational readiness
Absence of detected risk ≠ Safety
```

v0 is **specification only**. No evaluator implementation, JSON Schema, or automated tests are defined here.

---

## Purpose

Define a conservative, read-only process to assess any GitHub repository for:

1. Whether published description matches the actual repository contents
2. Which capabilities actually exist in the tree at a pinned commit
3. What has been operationally verified
4. What remains unverified
5. Plausible uses and applications
6. Overlap or duplication with systems already in use
7. Adoption effort, cost, and environment requirements
8. Security, license, and maintenance risks
9. Whether adoption has practical value under the stated purpose

The result is an **advisory value assessment**, not Evidence, not Certification, and not authorization to act.

---

## Scope

### In scope (v0)

- Public or locally cloned **GitHub repositories** only
- Evaluation at a **pinned commit SHA**
- Read-only inspection of repository identity, file inventory, allowlisted file contents, Git metadata, explicitly permitted read-only test outcomes, and existing verification results or receipts
- Advisory recommendation among a fixed enum

### Out of scope (v0)

- Non-GitHub sources (archives, packages, models, papers) — may be noted as future application, not implemented here
- Changing, remediating, or completing the target repository
- Independent Witness, Evidence admission, Owner Acceptance, or VECTOR authority
- Security audit, penetration testing, or formal certification
- Continuous connection to Job Agent, VECTOR, Chronicle, or Weaver receipt pipelines
- Reinterpretation of existing FC-04, RC8, or IW judgments in this repository

---

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| `repository` | Yes | GitHub repository URL **or** path to an already cloned local working tree |
| `commit_sha` | Yes | Exact commit SHA under evaluation (must resolve in the target) |
| `evaluation_purpose` | Yes | Why this assessment is being performed |
| `intended_use_site` | Yes | Where the repository would be used or integrated if adopted |
| `evaluation_criteria` | No | Optional additional criteria supplied by the requester |
| `allowlisted_files` | Yes | Explicit list of file paths that may be read beyond inventory/metadata |
| `network_allowed` | Yes | Boolean: whether network access is permitted for this evaluation run |

If `network_allowed` is false, evaluation must not fetch remote content, clone, pull, or download missing artifacts. Local path and already-present metadata only.

---

## Evaluation Dimensions

Assess each dimension using only confirmed observations. Mark gaps as unverified; do not infer PASS from silence.

| # | Dimension | Question |
|---|-----------|----------|
| 1 | Description fidelity | Do README / marketplace / about text match what exists at `commit_sha`? |
| 2 | Capability inventory | Which features, APIs, scripts, or artifacts are actually present? |
| 3 | Verified range | What has documented, read-only confirmation (tests, receipts, prior results)? |
| 4 | Unverified range | What is claimed or implied but not confirmed in this assessment? |
| 5 | Practical applications | What concrete uses are supported by confirmed facts? |
| 6 | Duplication | Does this overlap systems already available to the intended use site? |
| 7 | Adoption cost | Effort, dependencies, runtime, license obligations, environment needs |
| 8 | Risks and limitations | Security, license, maintenance, supply-chain, and operational hazards |
| 9 | Adoption value | Given purpose and use site, is there practical reason to adopt? |

---

## Result Format

The evaluator returns a single **advisory result** object with exactly these fields:

| Field | Type / constraint | Meaning |
|-------|-------------------|---------|
| `target_repository` | string | URL or local path evaluated |
| `target_commit` | string | Commit SHA pinned for the assessment |
| `evaluation_purpose` | string | Echo of stated purpose |
| `confirmed_facts` | list of strings | Observations supported by allowed operations only |
| `unverified_items` | list of strings | Claims, gaps, or questions not confirmed |
| `available_capabilities` | list of strings | Capabilities evidenced by repository contents at the commit |
| `practical_value` | string | Narrative of adoption value relative to purpose and use site |
| `possible_applications` | list of strings | Plausible applications grounded in confirmed facts |
| `duplication` | string | Overlap analysis vs systems at the intended use site |
| `adoption_cost` | string | Effort, cost, environment, and dependency summary |
| `risks_and_limitations` | list of strings | Security, license, maintenance, and other limits |
| `recommendation` | enum | One of: `ADOPT`, `ADOPT_WITH_CONDITIONS`, `HOLD`, `REJECT` |
| `confidence` | enum | One of: `HIGH`, `MEDIUM`, `LOW` |
| `human_review_required` | boolean | Whether a human must review before any further action |

### Recommendation values (closed set)

| Value | Meaning |
|-------|---------|
| `ADOPT` | Confirmed facts support adoption for the stated purpose; conditions none or trivial |
| `ADOPT_WITH_CONDITIONS` | Adoption may be useful only if listed conditions are met first |
| `HOLD` | Insufficient confirmation, blocking gaps, or unresolved duplication/risk |
| `REJECT` | Confirmed mismatch, unacceptable risk, or no practical value for the stated purpose |

### Confidence values (closed set)

| Value | Meaning |
|-------|---------|
| `HIGH` | Allowlisted coverage and observations strongly support the recommendation |
| `MEDIUM` | Material facts confirmed; notable unverified items remain |
| `LOW` | Sparse allowlist, limited metadata, or large unverified surface |

`recommendation` is advisory only. It is **not** authorization, Evidence admission, Owner Acceptance, Independent Witness, or VECTOR authority.

### Human Review Requirement

`human_review_required` MUST be `true` when any of the following apply:

- `recommendation` is `ADOPT` or `ADOPT_WITH_CONDITIONS`
- `confidence` is `MEDIUM` or `LOW`
- Material claims remain unverified for the stated evaluation purpose
- Security, license, maintenance, supply-chain, or operational risks remain unresolved
- Any next action would involve code execution, dependency acquisition, network access, integration, deployment, Owner Acceptance, Evidence admission, Weaver receipt, VECTOR, Independent Witness, or Job Agent activity

It MAY be `false` only when the result is purely informational and no adoption, integration, execution, authority action, or automated follow-up is proposed or implied.

Regardless of this field, a value assessment never authorizes any external action.

---

## Allowed Operations

- List files and directories in the target tree (read-only inventory)
- Read contents of paths in `allowlisted_files` only
- Read Git metadata (commit, tree, refs as present locally; remote only if `network_allowed`)
- Reference results of **explicitly permitted** read-only tests already authorized for the run
- Reference existing verification results or receipts **without modifying or re-admitting them**

All operations are observational. No write side effects on the target or on Weaver Forge authority surfaces.

---

## Prohibited Operations

- Automatic modification or remediation of the target repository
- Automatic acquisition of missing files, dependencies, or submodules (unless separately and explicitly authorized outside this v0 spec; default is prohibit)
- `commit`, `push`, `tag`, `release`, or pull request creation against the target or this repository
- External transmission of repository contents or assessment payloads
- Owner Acceptance
- Evidence admission
- Certification
- Unauthorized execution of arbitrary code from the target
- Display or exfiltration of secrets, credentials, or private keys
- Automatic promotion into Weaver receipts, VECTOR authority, Job Agent, Chronicle, Independent Witness, or related pipelines
- Persistent or always-on connection to Job Agent or VECTOR as part of this assessment

---

## Authority and Nonclaims

This specification and any result produced under it are **advisory only**.

Mandatory nonclaims:

| Statement | Binding |
|-----------|---------|
| Value Assessment ≠ Evidence | A value result is not a Weaver Evidence object and does not enter the evidence chain |
| Value Assessment ≠ Certification | No certification of quality, safety, or compliance is conferred |
| Value Assessment ≠ Security Audit | Absence of listed risks is not a security audit |
| Value Assessment ≠ Independent Witness | This boundary does not perform or substitute for IW / C-014 |
| Value Assessment ≠ Owner Acceptance | Recommendations do not constitute Owner Acceptance |
| Recommendation ≠ Authorization | `ADOPT` / `ADOPT_WITH_CONDITIONS` do not authorize integration, deploy, or receipt admission |
| Repository description ≠ Verified capability | Marketing or README text is not proof of capability |
| Test result ≠ General operational readiness | A permitted read-only test outcome does not imply general readiness |
| Absence of detected risk ≠ Safety | Undetected risk remains possible |

This boundary **must not**:

- Alter existing receipt verification rules or outcomes
- Alter VECTOR Package Ingress v0
- Alter or reinterpret Grok Build Witness, RC8, FC-04, or IW status
- Claim readiness, PASS, or release authority for this repository or the target

---

## Example Result

Illustrative only. Not a real assessment of any repository.

```text
target_repository: https://github.com/example/demo-tool
target_commit: abcdef0123456789abcdef0123456789abcdef01
evaluation_purpose: Determine whether demo-tool can replace an internal script runner
confirmed_facts:
  - README claims a CLI entry point; allowlisted package manifest lists bin/demo
  - LICENSE file present (Apache-2.0) at commit
  - No CI configuration found in inventory
unverified_items:
  - Runtime behavior of bin/demo (no permitted test executed)
  - Upstream maintenance cadence
  - Compatibility with intended use site OS image
available_capabilities:
  - Documented CLI surface in README
  - Source tree for a single-language tool at pinned commit
practical_value: May reduce custom script maintenance if CLI behavior matches needs; unverified runtime blocks strong adoption
possible_applications:
  - Local developer script runner
  - CI helper if later verified
duplication: Partial overlap with existing internal runner; no confirmed unique capability yet
adoption_cost: Low clone cost; unknown dependency install; needs human runtime check
risks_and_limitations:
  - No security audit performed
  - Secrets must not be read from config examples without redaction policy
  - Single-maintainer risk unassessed
recommendation: HOLD
confidence: LOW
human_review_required: true
```

---

## Future Implementation Boundary

v0 defines **documentation and result shape only**.

| May come later (out of band) | Not implied by this file |
|------------------------------|--------------------------|
| Evaluator script or agent that emits the advisory result | Any running evaluator in this repository today |
| JSON Schema for the result object | Schema validation |
| Allowlist templates or checklists | Automated scoring |
| Application of the same *idea* to non-GitHub artifacts | v0 scope expansion |

Future work may note applicability to other artifact classes. Until a new version explicitly expands scope, **v0 targets GitHub repositories only**.

Implementation of evaluators, schemas, or tests requires a separate, explicit change set. Creating this specification does not authorize those artifacts, does not connect to Job Agent or VECTOR, and does not change FC-04 / RC8 / IW posture.
