# Claim Register — xAI Grok Build

| Field | Value |
|-------|-------|
| Target slug | `grok-build` |
| Project | Grok Build |
| Claimed publisher | xAI |
| Claimed canonical repository | https://github.com/xai-org/grok-build |
| Current verification state | `NOT_STARTED` |
| Register status | Skeleton only — results `NOT_STARTED` |
| Maintained by | Weaver Forge documentation package author |
| Role | Owner-side (not independent witness) |
| Last updated | `2026-07-17` |
| Independent witness evaluation of claims | `NOT_STARTED` |

Product claims, expected outputs, and primary-source quote binding remain subject to inspection and pinning. No execution. No independent verification claimed.

---

## Rules

1. Record the **exact claim** text; do not paraphrase away meaning.
2. Every claim needs an **evidence class**, **verification method**, and **acceptance criteria**.
3. `expected output` may be filled only from documented sources or measured baselines — never invented.
4. `actual result` stays empty or `NOT_STARTED` until a recorded run exists.
5. Status must be one of: `NOT_STARTED`, `BLOCKED`, `PASS`, `PARTIAL`, `FAIL`, `NOT_APPLICABLE`.
6. Always complete **limitations** and **what the result does not establish**.
7. Owner-side results are not `independent_witness_result` unless produced by an uninvolved witness.

### Evidence classes (use exactly)

- `publisher_statement`
- `source_code_observation`
- `build_result`
- `test_result`
- `runtime_observation`
- `analytical_claim`
- `simulation_result`
- `conceptual_mapping`
- `unverified_hypothesis`
- `independent_witness_result`

### Register policy for this target

Product-specific performance, feature, or safety claims from Grok Build documentation are **not** registered until official docs are observed under an authorized acquisition. Inventing claim text would violate evidence rules. The claims below are **package-level verification intents** only.

---

## Claim Index

| Claim ID | Short title | Evidence class | Status |
|----------|-------------|----------------|--------|
| C-001 | Designated canonical repository URL | `conceptual_mapping` | `NOT_STARTED` |
| C-002 | Source-control identity freeze (full commit) | `source_code_observation` | `BLOCKED` |
| C-003 | License identification | `source_code_observation` | `BLOCKED` |
| C-004 | Documented build procedure is executable | `build_result` | `BLOCKED` |
| C-005 | Documented tests or checks pass as specified | `test_result` | `BLOCKED` |
| C-006 | Independent witness reproduces frozen package | `independent_witness_result` | `NOT_STARTED` |

---

## Claim Records

### C-001 — Designated canonical repository URL

| Field | Value |
|-------|-------|
| Claim ID | `C-001` |
| Exact claim | The intended canonical public repository for this verification package is `https://github.com/xai-org/grok-build`. |
| Source of claim | Weaver Forge `external_verifications/grok-build/VERIFICATION_PLAN.md` (package designation) |
| Evidence class | `conceptual_mapping` |
| Verification method | When authorized: resolve URL, confirm repository exists and matches designated org/name; record HTTP/git evidence. **Not performed in this pass.** |
| Acceptance criteria | Live check shows repository path `xai-org/grok-build` reachable as public source matching designation; evidence preserved. |
| Expected output | `unknown — not yet documented from live check` |
| Actual result | `NOT_STARTED` |
| Status | `NOT_STARTED` |
| Operator role for this result | Unassigned |
| Evidence pointers | none |
| Limitations | Designation is internal to this package; does not by itself prove xAI official canonicity beyond the URL string. |
| What the result does not establish | Authenticity of contents, security, build success, product claims, independent witness confirmation. |

### C-002 — Source-control identity freeze (full commit)

| Field | Value |
|-------|-------|
| Claim ID | `C-002` |
| Exact claim | A full immutable git commit ID (and optional tag) for the Grok Build tree under review can be recorded and re-checked. |
| Source of claim | Framework requirement: Identity and Version → Hash or Immutable Reference |
| Evidence class | `source_code_observation` |
| Verification method | When authorized: full clone; `git rev-parse HEAD` (or pin to tag); record 40-char commit ID. |
| Acceptance criteria | 40-character commit ID recorded; re-fetch or `git cat-file -t <id>` confirms object; no invented hash. |
| Expected output | `unknown — not yet documented` |
| Actual result | `NOT_STARTED` — blocked pending authorization to clone |
| Status | `BLOCKED` |
| Operator role for this result | Unassigned |
| Evidence pointers | none |
| Limitations | Floating branches are not an identity freeze. |
| What the result does not establish | Correctness of code; reproducibility of build; truth of README claims. |

### C-003 — License identification

| Field | Value |
|-------|-------|
| Claim ID | `C-003` |
| Exact claim | The repository license (name/SPDX and license file path) can be identified from the acquired tree or release metadata. |
| Source of claim | Framework source-identity requirements |
| Evidence class | `source_code_observation` |
| Verification method | When authorized: inspect `LICENSE` / `LICENSE.*` / package metadata; record SPDX if present. |
| Acceptance criteria | License name or explicit “no license file found” recorded with path evidence. |
| Expected output | `unknown — not yet documented` |
| Actual result | `NOT_STARTED` |
| Status | `BLOCKED` |
| Operator role for this result | Unassigned |
| Evidence pointers | none |
| Limitations | Presence of a license file is not legal advice. |
| What the result does not establish | Compliance of a particular use case; patent grants; trademark rights. |

### C-004 — Documented build procedure is executable

| Field | Value |
|-------|-------|
| Claim ID | `C-004` |
| Exact claim | Following the official Grok Build build/install documentation at a frozen identity produces a successful build (or a documented, reproducible failure) with preserved logs. |
| Source of claim | *To be bound to exact README/docs quote after authorized docs review* — currently a verification intent, not a publisher quote |
| Evidence class | `build_result` |
| Verification method | When authorized: capture environment; run exact documented commands; record exit codes and logs. |
| Acceptance criteria | Documented build commands executed in order; exit codes and logs preserved; status `PASS` only if official success criteria met. |
| Expected output | `unknown — not yet documented from official procedure` |
| Actual result | `NOT_STARTED` |
| Status | `BLOCKED` |
| Operator role for this result | Unassigned |
| Evidence pointers | none |
| Limitations | Until official procedure text is quoted, this claim is not publisher-bound. Owner-side success ≠ independent witness. |
| What the result does not establish | Functional correctness beyond build; security; production readiness; independent witness E4. |

### C-005 — Documented tests or checks pass as specified

| Field | Value |
|-------|-------|
| Claim ID | `C-005` |
| Exact claim | Documented test or verification commands for Grok Build, at a frozen identity, complete with outcomes matching documented acceptance criteria. |
| Source of claim | *To be bound to exact docs quote after authorized review* — verification intent only |
| Evidence class | `test_result` |
| Verification method | When authorized: run documented test/check commands only; preserve output. |
| Acceptance criteria | Commands, exit codes, and pass/fail criteria from docs are recorded; match required for `PASS`. |
| Expected output | `unknown — not yet documented` |
| Actual result | `NOT_STARTED` |
| Status | `BLOCKED` |
| Operator role for this result | Unassigned |
| Evidence pointers | none |
| Limitations | No test suite is assumed to exist; `NOT_APPLICABLE` if docs provide none. |
| What the result does not establish | Coverage completeness; absence of bugs; security properties; unrun scenarios. |

### C-006 — Independent witness reproduces frozen package

| Field | Value |
|-------|-------|
| Claim ID | `C-006` |
| Exact claim | An uninvolved third party can reproduce the frozen, documented verification steps and record a witness conclusion with an independence statement. |
| Source of claim | Weaver Forge E4 independence standard; `WITNESS_HANDOFF.md` |
| Evidence class | `independent_witness_result` |
| Verification method | Uninvolved witness follows `WITNESS_HANDOFF.md` after identity freeze and executable procedure exist. |
| Acceptance criteria | Witness record with independence statement, pinned commit/hash, commands, outcomes, and conclusion `Reproduced` or clearly bounded `PARTIAL`/`FAIL`/`BLOCKED`. |
| Expected output | Completed witness sections 7–9 in `WITNESS_HANDOFF.md` |
| Actual result | `NOT_STARTED` — no witness assigned; handoff not executable yet |
| Status | `NOT_STARTED` |
| Operator role for this result | Unassigned (must be independent witness) |
| Evidence pointers | none |
| Limitations | Package author cannot satisfy this claim. |
| What the result does not establish | E5 external audit; production readiness; claims outside witness scope. |

---

## Aggregate Claim Status

| Status | Count |
|--------|------:|
| `NOT_STARTED` | 2 |
| `BLOCKED` | 4 |
| `PASS` | 0 |
| `PARTIAL` | 0 |
| `FAIL` | 0 |
| `NOT_APPLICABLE` | 0 |
| **Total** | 6 |

Do not compute a single "overall PASS" from partial data.

---

## Claims Explicitly Not Registered

| Deferred claim | Reason excluded |
|----------------|-----------------|
| Any specific Grok Build feature, benchmark, or safety claim | Official documentation not observed in this documentation-only pass; quoting without source would invent claims |
| “Grok Build is production-ready” | Out of scope; would require operational criteria not authorized |
| “Repository is secure” | Security review not in scope for this revision |
| “Weaver Forge E4 is complete” | E4 is about independent witness of cited work; creating this package does not complete Weaver Forge E4 or Grok Build E4 |

---

## What This Register Proves

- That six verification intents are enumerated with methods, blockers, and non-establishments.
- That no claim has been marked `PASS`.
- That product-specific publisher claims are deferred until docs can be quoted honestly.

## What This Register Does NOT Prove

- That any claim passed verification
- Independent witness confirmation
- Security review
- Completeness of all possible claims about Grok Build
- Operational readiness
- Any hash, commit, or test result

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-07-17 | Initial skeleton register; execution blocked; no invented publisher claims | Weaver Forge documentation package author |

---

**No commit. No claim. No receipt. No authority.**
