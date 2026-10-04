# Claim / Subject Association Record v0 — Human Final

Date:
2026-10-04

Human Final:
HUMAN_REVIEW_ACCEPTED

This document records a Human Final decision explicitly made by the human authority. It does not record an AI acceptance decision.

HUMAN_REVIEW_ACCEPTED accepts the frozen CSAR-v0 contract and its implementation and tested envelope within this scope. It does not establish truth, support, sufficiency, completeness, correspondence, independence, admission, authority, creator identity, creation time or order, freshness, technical verification of external reality, historical CLOSED-receipt binding, legacy digest equivalence, or replacement or post-hoc detection.

PASS is not authority. Evidence is not authority. This Human Final does not convert a CSAR record into authority or truth.

Supplied-input reproduction remains supplied-input reproduction. It is not independent reproduction.

Fixed implementation SHA:
0c25a729503a8670368daeb7b2cfd5316c2420e9

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Claim / Subject Association Record v0 (CSAR-v0) only

Design freeze:
docs/next/CSAR_V0_HUMAN_DESIGN_FREEZE_20261004.md

Design-freeze save commit:
ba165499660d264e892576d8d677eea830763922

Material blockers:
0

## Implementation history

- initial implementation: 4562fe839cfebdf9ae8a1078640cfd88dd2ea602
- R1 test-only remediation: a85c7c08bd6113b74274319cea37d9c82c82904f
- R2 final test-only remediation / fixed implementation and test SHA: 0c25a729503a8670368daeb7b2cfd5316c2420e9

Production implementation originated at 4562fe839cfebdf9ae8a1078640cfd88dd2ea602. R1 and R2 were test-only. Production remained byte-identical to that implementation through the fixed SHA. The remediation strengthened tests. It did not change production semantics.

## Review history

Independent review after the initial implementation:
REMEDIATION_REQUIRED, test adequacy only. Production behavior was correct.

Targeted confirmation after R1:
REMEDIATION_REQUIRED, remaining H2, S11, and S4 test gaps only. Production remained correct and byte-identical.

Final targeted confirmation:
ACCEPT. H2 KILLED. S11 KILLED. S4 KILLED. Prior L, M, M2, S8, S10, and S12 remained covered.

Final review:
VERDICT ACCEPT. MATERIAL_FINDINGS NONE. NONMATERIAL_FINDINGS NONE. CLOSED_SCOPE_SAFETY PASS. READY_FOR_HUMAN_FINAL YES.

## Accepted evidence

- CSAR focused tests: 45 passed, 15 subtests passed
- DSDS-v0 regression: 36 passed, 19 subtests passed
- ACD-v0 regression: 21 passed, 5 subtests passed
- broader relevant regression: 766 passed, 82 subtests passed, 0 failed
- canonical complete CSAR record: 720 UTF-8 bytes, no trailing newline
- production code changed during R1 or R2: NO
- CLOSED scope changed: NO
- worktree clean before this documentation-only save
- pushed: NO

Golden digests:

- `claim_digest_csar_v0`: `d7af1740ffeed7854b6da2568c2ffe3790ea76d9d3b84f094d97e2328fbbb2bf`
- `subject_digest_csar_v0`: `563fb5a4d734474c7b6e0c612ff117f379129a1eeccdaca8afecf8ade60919f1`
- `association_digest_csar_v0`: `3f2c6ecc95ae64bfa7f89f414d88aa5c03cd884541257660cd3417bf747b8204`

These are the recorded results against the frozen CSAR golden vector. This Human Final does not add a new independent reproduction, a formal proof, or an external anchoring claim.

## Boundary

This Human Final accepts only the defined CSAR-v0 implementation scope at the fixed SHA above.

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
- ACR-v0 Human Design Freeze unchanged
- no public push
- no private push

## Next target

The next authorized planning target is ACR-v0 implementation. The ACR-v0 design is already Human Design Frozen. That implementation must consume this reviewed Human-Final CSAR-v0 implementation as its dependency. It must not fork, duplicate, or independently reimplement CSAR semantics. This Human Final does not itself implement ACR-v0.

## Closure

After this record is saved, CSAR-v0 is CLOSED for this defined scope. Any semantic change requires a new additive scope or version rather than silent modification of this accepted implementation.

## Change rule

Any future change to accepted CSAR-v0 implementation semantics is a new scope or version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record. No push had been performed at the time of this acceptance.
