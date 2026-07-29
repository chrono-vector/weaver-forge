# Package readiness policy (RC8 lifecycle boundary)

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

**RC6 IMMUTABLE HISTORICAL — NOT READY — RC7 IMMUTABLE HISTORICAL — NOT READY AFTER COMPLETED SOURCE WEAVER AUDIT — RC7 NOT ELIGIBLE FOR INDEPENDENT WITNESS HANDOFF — INDEPENDENT WITNESS HANDOFF NOT AUTHORIZED — C-014 NOT_STARTED — NO FINDING CLEAR/CLOSED — RC8 IMMUTABLE STATIC-AUDIT CANDIDATE (`1.0.0-rc8` / `grok-build-witness-v1.0.0-rc8`) — RC8 ARTIFACT GENERATION AND VERIFICATION PASSED — ACCEPTED NON-AUTHORITATIVE ADVISORY TECHNICAL EVALUATION — FORMAL SOURCE WEAVER AUDIT NOT PERFORMED FOR RC8 — NO FORMAL SOURCE WEAVER READY/NOT READY DECISION FOR RC8 — NOT READY FOR INDEPENDENT WITNESS HANDOFF — NO INDEPENDENT WITNESS REPRODUCTION — NO INDEPENDENT WITNESS PASS — NO RELEASE READINESS OR PRODUCTION READINESS CLAIMED**

**PARTIAL / not ready for Independent Witness handoff.** RC8 is an immutable static-audit
candidate: version `1.0.0-rc8`; `canonical_package_tag=grok-build-witness-v1.0.0-rc8`;
annotated tag object `8113d952d3b127d32e138dbf804141f5d1dfb26f`; peeled commit
`1de4b4d9523711418390f8331c95988523ef4481`; tree
`87b40d8a32ca536a4cdba0eee474f6171c62f6bb` (`package_commit_authority=annotated_tag_resolution`).
RC8 artifact generation and verification passed, but that result is not a formal Source Weaver
audit, not a formal Source Weaver READY decision, not a formal Source Weaver NOT READY decision,
not Independent Witness PASS, and not release or production readiness.

RC6 remains immutable historical **NOT READY**. RC7 remains immutable historical **NOT READY**
after completed Source Weaver audit and is not eligible for Independent Witness handoff. Current
`main` is a post-RC8 documentation/status surface only: not RC9, not READY, not release-approved,
and not authorized for Independent Witness handoff. Independent Witness reproduction **NOT
PERFORMED**. Independent Witness PASS **NONE**. C-014 remains `NOT_STARTED`. Overall **PARTIAL**.
Implementation or documentation alignment does **not** mark findings or blockers CLEAR/CLOSED.

At minimum, the following `NOT READY`-triggering conditions currently apply and must be tracked
before any `READY`/`READY WITH LIMITATIONS` claim is made:

- RC6 and RC7 remain immutable historical **NOT READY** candidates. RC7 completed Source Weaver
  static audit and is not eligible for Independent Witness handoff.
- RC8 is an immutable static-audit candidate only. RC8 artifact generation and verification passed,
  but no formal Source Weaver audit was performed for RC8 and no formal Source Weaver READY/NOT
  READY decision exists for RC8.
- Historical rc4 static blind audit disposition remains **NOT READY** (C-027; 40 integrated
  blockers under `evidence/rc4-static-blind-audit/`). Final adjudication of blockers requires a
  future immutable fixed candidate and repeat static audit — not documentation-only alignment.
- C-014 (Independent Witness) remains `NOT_STARTED`. Independent Witness handoff is not authorized
  and reproduction was not performed. No finding or blocker is CLEAR/CLOSED.

Package readiness for rc1–rc7 and lifecycle status for rc8 are preserved, unaltered, as immutable historical or candidate fact:

| Version | Tag | Peeled commit | Release state | Static audit | Readiness recorded |
|---------|-----|---------------|---------------|--------------|--------------------|
| `1.0.0-rc1` | `grok-build-witness-v1.0.0-rc1` | `89127c78c3a11492892de7e3b5f0dee18d71775a` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc2` | `grok-build-witness-v1.0.0-rc2` | `255b357c9ee33c4a9e34b5d9b6e396c53cfe494e` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc3` | `grok-build-witness-v1.0.0-rc3` | `77221a224bbd6194cfafb81f6ecb58c800e5bc13` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc4` | `grok-build-witness-v1.0.0-rc4` | `039b46737c5968a81fb756d7a6d1d0dd57b6ad96` | FIXED_IMMUTABLE | COMPLETE | **NOT READY** |
| `1.0.0-rc5` | `grok-build-witness-v1.0.0-rc5` | `5ae08cb8be9c1c97f25b9093bb5490a0ef195a07` | FIXED_IMMUTABLE | COMPLETE (Source Weaver) | **NOT READY** |
| `1.0.0-rc6` | `grok-build-witness-v1.0.0-rc6` | `7b76842bfa1adcedf0c00221cb574d9c3175b7e7` | FIXED_IMMUTABLE | COMPLETE (immutable candidate published) | **NOT READY** |
| `1.0.0-rc7` | `grok-build-witness-v1.0.0-rc7` | `4316b976b086cb7116cabe0c8deaa47159001c09` | FIXED_IMMUTABLE | COMPLETE (Source Weaver static audit of tagged RC7) | **NOT READY** |
| `1.0.0-rc8` | `grok-build-witness-v1.0.0-rc8` | `1de4b4d9523711418390f8331c95988523ef4481` | FIXED_IMMUTABLE static-audit candidate | Artifact generation/verification passed; accepted non-authoritative advisory technical evaluation; formal Source Weaver audit not performed | **No formal Source Weaver READY/NOT READY decision for RC8** |

No historical tag is retroactively upgraded by this policy document. RC6 and RC7 remain fixed,
immutable, and `NOT READY` as audited/ruled. RC8 remains an immutable static-audit candidate with
no formal Source Weaver READY/NOT READY decision. Independent Witness reproduction remains
**NOT PERFORMED**; C-014 remains **`NOT_STARTED`**; Independent Witness handoff is not authorized.

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
| main (RC6-R7 docs; not an RC6 release) | Historical alignment of RC5/RC6 identity/status wording; **does not** mark findings CLEAR/CLOSED; C-014 NOT_STARTED. Later lifecycle documents supersede prospective RC6/RC7/RC8 wording. |
| main (RC8 lifecycle-boundary docs; not RC9) | RC6/RC7 immutable historical **NOT READY**; RC8 immutable static-audit candidate; RC8 artifact generation and verification passed within lifecycle boundary only; no formal Source Weaver READY/NOT READY decision for RC8; Independent Witness not authorized/performed; C-014 NOT_STARTED; no finding/blocker CLEAR/CLOSED; no release or production readiness claim |
