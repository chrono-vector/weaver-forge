# Package readiness policy (RC6 immutable / pre-tag RC7 next-candidate on main)

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

**RC6 FIXED IMMUTABLE — NOT READY — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — NO FINDING CLEAR/CLOSED — NEXT CANDIDATE IDENTITY RC7 (`1.0.0-rc7` / `grok-build-witness-v1.0.0-rc7`) FIXED IN ACTIVE HOST/TEMPLATES AND VALIDATOR MAPPING — RC7 TAG/ARCHIVE/BUNDLE DO NOT YET EXIST — RC7 SOURCE WEAVER AUDIT HAS NOT OCCURRED — NOT READY — NO INDEPENDENT WITNESS REPRODUCTION — NO INDEPENDENT WITNESS PASS**

**NOT READY.** Last immutable tagged package: version `1.0.0-rc6`;
`canonical_package_tag=grok-build-witness-v1.0.0-rc6`; annotated tag object
`c9ce879bb25db54e3d8520f297a8f5d4035ac9a8`; peeled commit
`7b76842bfa1adcedf0c00221cb574d9c3175b7e7`; tree
`77369ab099414167df658b25eac3adcb4f264eb3`; archive SHA-256
`1f411f65735d6e2f8aeb0cb968d0e6b2108af00ef0a0264dc15daed114da0fee`; transfer-bundle SHA-256
`ed23824246563db17d9adb7e5b5c95b633077b79b2681c04c46d8de544de6d26`
(`package_commit_authority=annotated_tag_resolution`). RC6 disposition remains **NOT READY**.
Independent Witness handoff for RC6 is **not authorized**. See
[WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md).

Current `main` hosts next-candidate RC7 identity (`1.0.0-rc7` /
`grok-build-witness-v1.0.0-rc7`) in active Host/templates and validator mapping only. An RC7
tag, archive, and transfer bundle **do not yet exist**. RC7 Source Weaver audit has **not**
occurred. Current `main` is **not** an immutable RC7 fixed candidate, **not** READY, **not**
approved for Independent Witness handoff, and **not** Source Weaver-approved as an RC7 release.
Independent Witness reproduction **NOT PERFORMED**. Independent Witness PASS **NONE**. C-014
remains `NOT_STARTED`. Overall **PARTIAL**. Implementation or documentation alignment does
**not** mark findings CLEAR/CLOSED; final adjudication requires a future immutable fixed
candidate and Source Weaver
audit.

At minimum, the following `NOT READY`-triggering conditions currently apply and must be tracked
before any `READY`/`READY WITH LIMITATIONS` claim is made:

- Immutable RC6 disposition remains **NOT READY**; Independent Witness handoff unauthorized
  (see [WITNESS_PACKAGE_VERSION.md](WITNESS_PACKAGE_VERSION.md)). Historical RC5 Source Weaver
  disposition also remains **NOT READY**.
- Historical rc4 static blind audit disposition remains **NOT READY** (C-027; 40 integrated
  blockers under `evidence/rc4-static-blind-audit/`). Final adjudication of blockers requires a
  future immutable fixed candidate and repeat static audit — not documentation-only alignment.
- Current pre-tag RC7 next-candidate remediation on `main` is not an immutable fixed candidate
  and must not be presented as READY or as Independent Witness-authorized. RC7 tag/archive/bundle
  do not yet exist; RC7 Source Weaver audit has not occurred.
- C-014 (Independent Witness) remains `NOT_STARTED`. No finding CLEAR/CLOSED.

Package readiness for rc1–rc6 is preserved, unaltered, as immutable historical fact:

| Version | Tag | Peeled commit | Release state | Static audit | Readiness recorded |
|---------|-----|---------------|---------------|--------------|--------------------|
| `1.0.0-rc1` | `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc2` | `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc3` | `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc4` | `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc5` | `grok-build-witness-v1.0.0-rc5` | `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07` | FIXED_IMMUTABLE | COMPLETE (Source Weaver) | **NOT READY** |
| `1.0.0-rc6` | `grok-build-witness-v1.0.0-rc6` | `7b76842bfa1adcedf0c00221cb574d9c3175b7e7` | FIXED_IMMUTABLE | COMPLETE (immutable candidate published) | **NOT READY** |

No historical tag is retroactively upgraded by this policy document; all six remain fixed,
immutable, and `NOT READY` as audited/ruled. Independent Witness reproduction remains
**NOT PERFORMED**; C-014 remains **`NOT_STARTED`**. **RC7 tag does not yet exist.**

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
| main (RC6-R7 docs; not an RC6 release) | Record RC5 as FIXED_IMMUTABLE with exact tag-object/peel/tree/archive/bundle identities; Source Weaver RC5 disposition **NOT READY**; Independent Witness handoff unauthorized; describe current `main` as pre-tag RC6-R1–R7 remediation / prospective RC6 fixed candidate only; **does not** mark findings CLEAR/CLOSED; RC6 tag/archive/bundle absent; C-014 NOT_STARTED |
