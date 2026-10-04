# Domain-Separated Digest Spec v0 — Human Final

Date:
2026-10-04

Human Final:
HUMAN_REVIEW_ACCEPTED_WITH_NONMATERIAL_LIMITATIONS

This document records a Human Final decision explicitly made by the human authority. It does not record an AI acceptance decision.

Fixed implementation SHA:
a7d5d63ebd7aeefc6b6fd83d7cfe30191eee51b0

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Domain-Separated Digest Spec v0 (DSDS-v0) only

## Implementation history

- initial implementation: 11598c62803a47b5a61ab70c2f6184cced777811
- material remediation R1: b534c227b81f1108cf7b799d22e51fcac4468d64
- test-only remediation R2 / fixed implementation SHA: a7d5d63ebd7aeefc6b6fd83d7cfe30191eee51b0

## Accepted evidence

- DSDS tests: 36 passed
- DSDS subtests: 19 passed
- focused R4 regression: 2 passed, 138 deselected
- golden vectors: PASS
- F1: CLOSED
- F2 mutation gaps: CLOSED
- F3: CLOSED
- M15: CLOSED
- N2: CLOSED
- CLOSED scope changed: NO
- worktree clean before this documentation-only save
- pushed: NO

## Safe semantics

Given the same permitted domain ID and the same spec-defined preimage bytes, conforming implementations compute the same domain-separated SHA-256.

## Explicit nonclaims

DSDS-v0 does not establish:

- creator identity
- creation time
- ordering
- authenticity
- subject correctness
- claim truth
- evidence support
- sufficiency
- completeness
- freshness
- formal/runtime correspondence
- independence
- admission
- authority
- technical verification
- Human Final for any other scope
- legacy digest equivalence
- historical CLOSED-receipt binding

## Legacy separation

DSDS typed/domain-separated digests must not be treated as semantically equivalent to legacy untagged CLOSED digests merely because displayed 64-hex values match.

## Residual accepted nonmaterial limitations

- generic domain_separated_digest can hash arbitrary bytes under R4_CLAIM_BODY / CSAR_RECORD
- large-int acceptance/rejection may depend on runtime integer-string limits
- lone surrogate handling remains
- tuple/list ref equivalence remains where already identified
- r4_claim_body_preimage visibility remains
- exact-str set-like lists remain sorted/unique

## Boundary

This Human Final does not accept:

- CSAR-v0
- D0/D1
- Independent Evidence Admission
- signatures/key custody
- authority/grants
- freshness
- correspondence
- expected-evidence manifests
- receiver receipt design
- EBD integration

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
- no public push
- no private push

## Change rule

Any future change to accepted DSDS-v0 implementation semantics is a new scope/version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record.
