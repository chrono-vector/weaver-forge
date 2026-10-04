# Presented-Subject Role Descriptor v0 — Human Final

Date:
2026-10-04

Human Final:
HUMAN_REVIEW_ACCEPTED

This document records a Human Final decision explicitly made by the human authority. It does not record an AI acceptance decision.

HUMAN_REVIEW_ACCEPTED accepts the frozen PSRD-v0 contract and its implementation and tested envelope within this scope. It records only the frozen machine question:

Does this descriptor commit the one code-owned role `UNINTERPRETED_PRESENTED_BYTES` to the CLOSED presented-subject digest of these exact supplied bytes?

This acceptance does not establish or introduce a caller-selectable role, an evidence kind, an evidence set, claim support, sufficiency, completeness, truth, authority, independence, freshness, contradiction resolution, admission, verification, or Human Final semantics.

Caller-selection risk remains explicitly unresolved.

Structural consistency is not supplied-input reproduction. Supplied-input reproduction is not independent reproduction. Descriptor existence is not evidence classification. `UNINTERPRETED_PRESENTED_BYTES` is not an evidence role.

Fixed reviewed implementation SHA:
649c5c5c255f91c4422989857ae8b6b5a1077f05

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Presented-Subject Role Descriptor v0 (PSRD-v0) only

Design freeze:
docs/next/PSRD_V0_HUMAN_DESIGN_FREEZE_20261004.md

Design-freeze save commit:
cc75fa4da13a0971df3b300fd49334f205fb4edc

Material blockers:
0

PSRD-v0 status after this record:
CLOSED

## Implementation history

- Human Design Freeze save: cc75fa4da13a0971df3b300fd49334f205fb4edc
- implementation and planned attack tests / fixed reviewed SHA: 649c5c5c255f91c4422989857ae8b6b5a1077f05

The fixed reviewed tree is the implementation commit. No later production or test commit is part of this acceptance.

## Review history

Final independent review:
VERDICT ACCEPT. MATERIAL_FINDINGS NONE. CLOSED_SCOPE_SAFETY PASS. READY_FOR_HUMAN_FINAL YES.

Planned attack tests PSRD-M01 through PSRD-M38: 38/38 PASS. None skipped. None xfailed.

The 38 planned items are attack tests, `test_m01` through `test_m38`. They are not 38 source-code mutation-harness mutants.

Independent source-code mutation exercise:
23 KILLED. 1 EQUIVALENT (SUB1). No material survivor.

## Nonmaterial review notes

These notes do not reopen the scope.

1. The 38 planned items are attack tests, not source mutation-harness mutants.
2. The independent source mutation exercise is 23 KILLED and 1 EQUIVALENT.
3. SUB4 differed only in rejection message and strictness. It left no acceptance hole.
4. Structural checking accepts a structurally well-formed subject digest without the original bytes by design. Exact-byte binding is established only by supplied-input reproduction.

## Accepted evidence

- PSRD focused tests: 39 passed, 37 subtests passed
- DSDS-v0 regression: 36 passed, 19 subtests passed
- CSAR-v0 regression: 45 passed, 15 subtests passed
- ACD-v0 regression: 21 passed, 5 subtests passed
- ACR-v0 regression: 27 passed, 28 subtests passed
- broader relevant regression: 832 passed, 147 subtests passed, 0 failed
- canonical five-field preimage: 917 UTF-8 bytes, no trailing newline
- canonical six-field PSRD record: 1012 UTF-8 bytes, no trailing newline
- CLOSED scope changed: NO
- production and tests unchanged by this documentation-only save
- worktree clean before this documentation-only save
- pushed: NO

Golden values:

- `subject_digest_psrd_v0`: `563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`
- `descriptor_digest_psrd_v0`: `b586f3c45f548220b75b7c00bfed1e0e7b9f713a077d9d53f9534bf02eaeac80`
- ordinary SHA-256 fingerprint of the exact canonical record bytes: `5dc9cf4907c977de3f3672eecb19dbb10adb4ae72069778a71aef2f8d4bb034d`

The ordinary SHA-256 fingerprint is a byte fingerprint of the canonical record. It is not the semantic descriptor digest.

These are the recorded results against the frozen PSRD golden vector. This Human Final does not add a new independent reproduction, a formal proof, or an external anchoring claim.

## Boundary

This Human Final accepts only the defined PSRD-v0 implementation scope at the fixed SHA above.

Accepted boundaries that remain unchanged:

- R3 unchanged / CLOSED
- R4 unchanged / CLOSED
- WVMA-V1 unchanged / CLOSED
- Tested-Envelope Receipt v0 unchanged / CLOSED
- Recovery Preflight v0 unchanged / CLOSED
- Independent Verification Preflight v0 unchanged / CLOSED
- Conducting Receipt v0 unchanged / CLOSED
- Recovery Execution Receipt v0 unchanged / CLOSED
- Evidence Binding DAG v0 unchanged / CLOSED
- Domain-Separated Digest Spec v0 unchanged / CLOSED
- Association Carriage Digest v0 unchanged / CLOSED
- Claim / Subject Association Record v0 unchanged / CLOSED
- Association Carriage Receipt v0 unchanged / CLOSED
- PSRD-v0 Human Design Freeze unchanged
- PSRD-v0 production unchanged by this record
- PSRD-v0 tests unchanged by this record
- no public push
- no private push

## Closure

After this record is saved, PSRD-v0 is CLOSED for this defined scope. Any semantic change requires a new additive scope or version rather than silent modification of this accepted implementation.

## Change rule

Any future change to accepted PSRD-v0 implementation semantics is a new scope or version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record. No push had been performed at the time of this acceptance.
