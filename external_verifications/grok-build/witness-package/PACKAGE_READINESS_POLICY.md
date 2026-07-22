# Package readiness policy (1.0.0-rc4)

This document defines the **normative readiness classification** for the Witness package as a
whole — distinct from any single Witness run's proposed verdict (`WITNESS_VERDICT.md`, governed
by [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)) and distinct from maintainer intake of
a single submission ([MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md)). Package
readiness answers: *"Can an uninvolved person, following only this package's public
documentation, safely and correctly attempt a Witness run today?"*

## Readiness values

| Value | Meaning |
|-------|---------|
| `NOT READY` | The package must not be presented as safe or complete to attempt a blind Witness run. |
| `READY WITH LIMITATIONS` | The package can be safely and correctly attempted end-to-end; any remaining gaps are disclosed, non-fatal, and do not create a risk of false success. |
| `READY` | The package can be safely and correctly attempted end-to-end with complete, conservative internal consistency and no known remaining material gap. |

## `NOT READY` is mandatory when any of the following hold

| Condition | Explanation |
|-----------|-------------|
| False success is possible | Any path exists by which a run that did **not** faithfully reproduce the canonical procedure (wrong tag/commit/image/lock, product execution, `ldd` use, silent identity override) could still be classified `PASS` or accepted as `PASS` without a visible, mandatory disclosure. |
| Truthful negative submission is impossible | The package does not fully support (structurally, procedurally, or in its templates/validator) a Witness truthfully recording and submitting `FAIL`, `INDETERMINATE`, or an infrastructure/build failure outcome. A package that only "works" when the build succeeds is not ready. |
| Mandatory evidence cannot be generated | Any documented mandatory evidence file cannot actually be produced by following the runbook as written (e.g. a referenced script, flag, or file does not exist; a required field has no corresponding generator). |
| Validator can pass materially inadequate evidence | The structural validator accepts a submission that is missing a materially relevant fact (wrong outcome inference, generic body satisfying an unrelated file's schema, unenforced verdict-ceiling rule, unenforced prohibited-redaction rule). |
| Material execution/evidence/classification policy must be reconstructed | A Witness (or auditor) would have to infer, guess, or reconstruct a load-bearing rule (an outcome mapping, a deviation ceiling, a redaction boundary, a maintainer-intake value) because it is not written down anywhere in the package, even if the underlying script or validator behavior happens to be correct. |

Any **one** of the conditions above is independently sufficient to require `NOT READY` for the
whole package, regardless of how many other areas are complete.

## `READY WITH LIMITATIONS` requires all of the following

- Every material path above is **complete**: no false-success path, truthful negative
  submissions are fully supported, every mandatory evidence file is actually generatable, the
  validator cannot be satisfied by materially inadequate evidence, and no load-bearing policy is
  left unwritten.
- Every remaining limitation is:
  - **Disclosed** in the relevant document (e.g. unpinned apt package versions, network
    dependency, no fully-offline reproduction, macOS unvalidated).
  - **Nonfatal** — it does not create a false-success risk and does not block a truthful
    submission of any outcome.
- The disclosed limitations are enumerated in a single place per affected document (not buried or
  contradicted elsewhere).

`READY WITH LIMITATIONS` is a genuine, usable readiness state — it is not a euphemism for `NOT
READY`, but it also never overrides a `NOT READY`-triggering condition above.

## `READY` requires

- Everything required for `READY WITH LIMITATIONS`, **and**
- **Complete conservative internal consistency**: every document, template, script, and the
  validator agree on field names, outcome values, canonical constants, tag/version strings, and
  classification ceilings, with zero known contradictions.
- No remaining disclosed limitation that a reasonable Witness would consider material to the
  correctness of their own run.
- A repeat blind audit (or equivalent independent review) against the **exact published tag**
  has confirmed the above, in writing, after the tag was cut.

## Current package status

**RC3 INTEGRATED STATIC BLIND-AUDIT RECORDED — RC4 PACKAGE CONTENT UNDER PREPARATION — NOT READY PENDING RC4 COMMIT, TAG AND RE-AUDIT**

**NOT READY** — package version `1.0.0-rc4`; `canonical_package_tag=grok-build-witness-v1.0.0-rc4`;
`package_commit_authority=annotated_tag_resolution` (no embedded future rc4 commit). Tag
availability is verified by annotated-tag resolution; canonical execution requires successful
resolution; if resolution fails, canonical execution stops. After publication, the tag is
immutable. Package remains **NOT READY** until rc4 is committed, tagged, and repeat-audited.
C-014 remains `NOT_STARTED`. Overall **PARTIAL**. At minimum, the following
`NOT READY`-triggering conditions currently apply and must be tracked to closure before any
`READY`/`READY WITH LIMITATIONS` claim is made:

- Fixed-tag repeat blind audit against `grok-build-witness-v1.0.0-rc4` has not yet recorded a
  readiness-passing result (see [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)).
- `run_witness_narrow_build.sh` and `container_narrow_build.sh` field-for-field reconciliation
  against the `evidence_schema_version=1` templates and validator remains a tracked gap for the
  orchestrator's own `verdict_ceiling` computation (see the `Known gaps` section of
  [scripts/VALIDATOR.md](scripts/VALIDATOR.md) and
  [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md)).
- C-014 (Independent Witness) remains `NOT_STARTED`.

Package readiness for rc1, rc2, and rc3 is preserved, unaltered, as immutable historical fact:

| Tag | Commit | Audit performed | Readiness recorded |
|-----|--------|------------------|----------------------|
| `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | Repeat public-entry-point blind audit | **NOT READY** |
| `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | Integrated four-batch static blind audit | **NOT READY** |
| `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | Integrated four-batch static blind audit (preserved under `evidence/rc3-static-blind-audit/`) | **NOT READY** |

Neither historical tag is retroactively upgraded by this policy document; all three remain fixed,
immutable, and `NOT READY` as audited.

## Relationship to other verdict/intake values

| Concept | Scope | Governing document |
|---------|-------|----------------------|
| Witness proposed verdict | A single run | [WITNESS_CLASSIFICATION.md](WITNESS_CLASSIFICATION.md) |
| Maintainer intake verdict | A single submission | [MAINTAINER_INTAKE_POLICY.md](MAINTAINER_INTAKE_POLICY.md) |
| Package readiness | The package as a whole, across all runs | This document |

A package can be `READY` while an individual submission is `FAIL` (a truthful failure report
about a correctly-functioning package). A package must be `NOT READY` even if every past
submission happened to record `PASS`, if any structural false-success path exists. These are
independent axes and must never be collapsed into one status field.

## Change log

| Version | Change |
|---------|--------|
| 1.0.0-rc3 | Created. Normative `NOT READY` / `READY WITH LIMITATIONS` / `READY` table with mandatory-`NOT READY` trigger conditions; current package status recorded as `NOT READY`; rc1/rc2 historical readiness preserved unaltered. |
| 1.0.0-rc4 | Status/identity advanced to `1.0.0-rc4` / `grok-build-witness-v1.0.0-rc4`; rc3 immutable NOT READY history added; time-stable annotated-tag resolution wording; C-014 NOT_STARTED; overall PARTIAL |
