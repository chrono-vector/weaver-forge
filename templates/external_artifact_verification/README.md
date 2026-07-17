# External Artifact Verification Framework

Reusable, documentation-only templates for independently evaluating **external** software, research artifacts, repositories, archives, notebooks, and claims.

This framework extends Weaver Forge evidence discipline outward. It does **not** replace Weaver Forge's own receipt workflow, validator scripts, or E4 independent-reproduction path for this repository.

**Build. Test. Commit. Receipt. Repeat.**

**No commit. No claim. No receipt. No authority.**

---

## Purpose

Use these templates when Weaver Forge (or a Weaver pod) evaluates something **outside** this repository:

- Third-party source code and release artifacts
- Research papers with code, data, or notebooks
- Archives, model weights, datasets, or binaries
- Publisher or author claims about behavior, performance, or safety
- Conceptual mappings that must not be confused with measured results

The goal is a **conservative, receipt-ready evidence trail** that any later independent witness can re-run or re-check.

---

## Evidence Chain

Every verification package should preserve this chain, in order:

```text
Source
  → Artifact
    → Identity and Version
      → Hash or Immutable Reference
        → Claim
          → Test
            → Reproduction
              → Evidence
                → Receipt
                  → Verdict
                    → Independent Witness
```

Missing links are **gaps**, not implied successes. Record them as `NOT_STARTED`, `BLOCKED`, or `NOT_APPLICABLE` — never as silent assumptions.

---

## Evidence Levels (Weaver Forge Alignment)

This framework is compatible with Weaver Forge evidence levels. Do not skip levels by narrative:

| Level | Meaning (for an external target) |
|-------|----------------------------------|
| E0 | Concept / target selected |
| E1 | Verification plan and templates filled (specification) |
| E2 | Local owner-side execution of documented steps |
| E3 | Receipt-backed candidate (claims bound to evidence) |
| E4 | **Independent** third-party witness reproduction |
| E5 | External audit (beyond a single witness package) |

**Owner-side reproduction is not E4.** Author self-audit, same-workspace review, or project-operator execution may reach E2/E3 for the external target. E4 requires an uninvolved third party, an independence statement, and a completed witness record. See Weaver Forge `E4_REPRODUCTION_PLAN.md` and `WITNESS_REVIEW_TEMPLATE.md` for the repository's own E4 rules; apply the same independence standard here.

---

## Allowed Status Values

Use only these explicit statuses unless a template field is free-text notes:

| Status | Meaning |
|--------|---------|
| `NOT_STARTED` | Step or claim not yet attempted |
| `BLOCKED` | Cannot proceed; record the blocker |
| `PASS` | Acceptance criteria fully met with recorded evidence |
| `PARTIAL` | Some criteria met; limitations required |
| `FAIL` | Attempted; acceptance criteria not met |
| `NOT_APPLICABLE` | Outside scope for this target (justify why) |

Do not invent intermediate statuses. Do not upgrade status without new evidence.

---

## Evidence Classes

Every claim in the claim register must use one primary evidence class:

| Class | Description |
|-------|-------------|
| `publisher_statement` | Claim made by the publisher/author without independent check |
| `source_code_observation` | Direct inspection of source or docs as published |
| `build_result` | Outcome of a documented build |
| `test_result` | Outcome of a documented test suite or check |
| `runtime_observation` | Observed behavior of a running system |
| `analytical_claim` | Derived analysis; not a measured reproduction |
| `simulation_result` | Result of a simulation or model run |
| `conceptual_mapping` | Terminology or design mapping; not functional proof |
| `unverified_hypothesis` | Proposed claim with no confirming evidence yet |
| `independent_witness_result` | Result recorded by an uninvolved third-party witness |

Classes are labels for **how** a claim is supported, not grades of truth. A `publisher_statement` is never upgraded to `independent_witness_result` without an actual independent witness.

---

## Package Layout

### Reusable templates (this directory)

| File | Role |
|------|------|
| `VERIFICATION_PLAN_TEMPLATE.md` | Scope, roles, chain checklist, non-claims |
| `SOURCE_IDENTITY_TEMPLATE.md` | Canonical publisher, URLs, version, hash, license |
| `CLAIM_REGISTER_TEMPLATE.md` | Claims, evidence classes, acceptance criteria |
| `ENVIRONMENT_TEMPLATE.md` | Machine, runtime, locks, network, isolation |
| `REPRODUCTION_TEMPLATE.md` | Exact commands, order, exits, logs, deviations |
| `RESULTS_TEMPLATE.md` | Per-claim and aggregate results |
| `VERDICT_TEMPLATE.md` | Conservative multi-axis verdict |
| `WITNESS_HANDOFF_TEMPLATE.md` | Package for independent third-party witness |

### Concrete verification package (example)

```text
external_verifications/<target-slug>/
  VERIFICATION_PLAN.md
  SOURCE_IDENTITY.md
  CLAIM_REGISTER.md
  ENVIRONMENT.md
  REPRODUCTION.md
  RESULTS.md
  VERDICT.md
  WITNESS_HANDOFF.md
```

Copy every template into a new target directory. Rename only if repository conventions require it. Keep filenames stable so packages are comparable.

---

## Roles (Do Not Collapse)

| Role | May do | Must not claim |
|------|--------|----------------|
| **Operator / owner-side verifier** | Plan, acquire identity facts, reproduce documented steps, record receipts | Independent witness / E4 for own work |
| **Independent witness** | Repeat package from clean environment; attest only to observed results | Project authority; success of unrun steps |
| **External auditor** | Formal audit under separate charter | Implied by a single witness package |

**Contributor ≠ Witness.** You cannot witness your own work. This rule applies to external targets the same way it applies inside Weaver Forge.

---

## Hard Rules

1. **Documentation is not verification.** Creating a package does not mean claims were tested.
2. **Do not invent facts.** No fabricated hashes, commit IDs, sizes, test counts, or expected outputs.
3. **Record expected outputs only from documented sources** (official README, release notes, pinned docs). If unknown, write `NOT_STARTED` or `unknown — not yet documented`.
4. **Preserve claim boundaries.** Every positive claim needs a matching "what this does not establish" limit.
5. **Do not modify the external target** as part of verification unless the plan explicitly allows and records patch deviation.
6. **Do not change Weaver Forge validators, receipts, runtime code, or governance rules** solely to accommodate an external package.
7. **Independent witness status starts as `NOT_STARTED`** until an uninvolved party completes a witness record.
8. **Blocked is honest.** Prefer `BLOCKED` with a reason over silent omission.

---

## Verdict Axes

Overall package verdicts must separate at least these axes (see `VERDICT_TEMPLATE.md`):

- Source authenticity
- Artifact integrity
- Build reproducibility
- Functional reproducibility
- Claim verification
- Security review
- Independent-witness status
- Operational readiness

A single green label is forbidden when axes disagree. Prefer a table of axis statuses plus a short conservative summary.

---

## Evidence Boundaries (Mandatory in Results and Verdict)

Every `RESULTS.md` and `VERDICT.md` must explicitly state:

1. **What was observed**
2. **What was not observed**
3. **What was not tested**
4. **What is not claimed**
5. **Reproduction class:** owner-side reproduction **or** independent reproduction **or** neither (documentation only)

Silent omission is a process failure. Prefer verbose non-claims over implied success.

---

## Witness Handoff Minimum Fields

`WITNESS_HANDOFF_TEMPLATE.md` must include, before a handoff is considered executable:

| Required block | Purpose |
|----------------|---------|
| Pinned source reference | Full commit / tag / immutable ref |
| Artifact hash | Content hash or justified git-tree identity |
| Environment prerequisites | Minimum OS/runtime/network/auth/isolation |
| Exact verification commands | Ordered, copy-pasteable |
| Expected machine-readable outputs | From primary docs only; never invented |
| Tolerances | Acceptance bands or exact-match default |
| Known limitations | What witness work cannot overcome |
| Independence declaration | Uninvolved third-party attestation |
| Result-submission procedure | How and where to return evidence |

---

## Receipt Compatibility

**Do not modify** `scripts/validate_receipts.py` or the required sections of `RECEIPT_TEMPLATE.md` for this framework. External verification receipts remain ordinary Weaver Forge build receipts that already require: built/shipped, Evidence (with `Commit:`), proves, does NOT prove, next step.

### How future receipts should reference an external verification package

When filing a receipt under `receipts/` for work on an external target, include the following in **Evidence** (and optionally Metrics), using plain Markdown so the existing validator still only requires a `Commit:` line for the **Weaver Forge** commit that records the work:

| Receipt field guidance | What to write |
|------------------------|---------------|
| **Target project** | Name + slug, e.g. `Grok Build` (`external_verifications/grok-build/`) |
| **Pinned commit or artifact hash** | Full external commit ID and/or artifact hash from `SOURCE_IDENTITY.md`; if not yet pinned, write `NOT_STARTED` — do not invent |
| **Verification-plan version** | Path + date or Weaver commit that last materially changed `VERIFICATION_PLAN.md` |
| **Executed claim IDs** | e.g. `C-001`, `C-004` from that package’s `CLAIM_REGISTER.md` |
| **Evidence locations** | Paths to logs, `RESULTS.md`, transcripts under the package or agreed evidence store |
| **Verdict** | Overall + axis statuses from `VERDICT.md` (e.g. overall `NOT_STARTED`) |
| **Reproduction class** | Owner-side **or** independent witness (never conflate) |

### Example Evidence block (illustrative shape only)

```markdown
## Evidence
- Commit: <full hash of the Weaver Forge commit that added/updated the package work>
- Target project: Grok Build (external_verifications/grok-build/)
- External pin: NOT_STARTED  # or full commit / artifact hash when known
- Verification plan: external_verifications/grok-build/VERIFICATION_PLAN.md (as of YYYY-MM-DD)
- Executed claim IDs: none  # or C-001, C-002, …
- Evidence locations: external_verifications/grok-build/RESULTS.md
- Verdict: overall NOT_STARTED (see VERDICT.md)
- Reproduction class: neither (documentation only)  # or owner-side / independent
```

### What such a receipt may prove

- That Weaver Forge documentation or owner-side/witness work on the package was committed
- That listed claim IDs and paths existed at the receipt’s Weaver Forge `Commit:`

### What such a receipt must not prove by implication

- That the external target passed verification if `VERDICT.md` is still `NOT_STARTED`
- Independent verification without a completed witness handoff
- Anything the existing receipt validator does not check (it checks form and commit object presence, not external claim truth)

---

## Relationship to Weaver Forge Internals

| Weaver Forge artifact | Role relative to this framework |
|-----------------------|----------------------------------|
| `RECEIPT_TEMPLATE.md` | Daily build receipts for Weaver Forge work (including docs that add packages) |
| `REPRODUCE.md` | How to reproduce **Weaver Forge** validation — not external targets |
| `E4_REPRODUCTION_PLAN.md` | E4 for **this** repository |
| `WITNESS_REVIEW_TEMPLATE.md` | Witness form for Weaver Forge itself |
| This template set | Witness-ready packaging for **external** artifacts |
| `WITNESS_HANDOFF_TEMPLATE.md` | External-target witness package (not a substitute for Weaver Forge E4) |

When a package is ready for independent review, complete `WITNESS_HANDOFF.md` for the target. That handoff is the external analogue of a Weaver Forge witness review package — it does not itself complete E4 for Weaver Forge or for the external target.

---

## How to Start a New Target

1. Create `external_verifications/<target-slug>/`.
2. Copy all templates from this directory; drop the `_TEMPLATE` suffix.
3. Fill `VERIFICATION_PLAN.md` with scope and non-claims first.
4. Record only known identity facts in `SOURCE_IDENTITY.md`; leave unknowns blank or `NOT_STARTED`.
5. Register claims without pre-filling results as `PASS`.
6. Keep `ENVIRONMENT.md`, `REPRODUCTION.md`, and `RESULTS.md` at `NOT_STARTED` until execution is authorized and performed.
7. Keep `VERDICT.md` and independent-witness fields at `NOT_STARTED` until evidence exists.
8. Complete mandatory evidence-boundary sections in results and verdict even when empty.
9. File a Weaver Forge receipt for the **documentation work** if this package is itself a Weaver Forge deliverable — that receipt proves the package exists, not that the external target was verified. Follow **Receipt Compatibility** above.

### Reuse for future targets (e.g. Weaver Nexus, C*Hive)

Copy the same template directory into a new slug:

- `external_verifications/weaver-nexus/`
- `external_verifications/c-star-hive/` (or the project’s chosen slug)

Do not share a single `RESULTS.md` across targets. Each target keeps its own evidence chain, claim IDs, pins, and verdict. Cross-links between packages are `conceptual_mapping` until independently evidenced.

---

## What This Framework Proves

- Weaver Forge has a reusable structure for external artifact evaluation.
- Packages can enforce an explicit evidence chain and claim boundaries.

## What This Framework Does NOT Prove

- That any listed external target has been verified
- That E4 or E5 has been reached for any external target
- Security, safety, or production readiness of any external software
- Correctness of publisher claims
- That templates alone substitute for execution, receipts, or independent witnesses

---

**Evidence before authority.**
