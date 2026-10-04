# Association Carriage Digest v0 — Human Final

Date:
2026-10-04

Human Final:
HUMAN_REVIEW_ACCEPTED

This document records a Human Final decision explicitly made by the human authority. It does not record an AI acceptance decision.

HUMAN_REVIEW_ACCEPTED is a human governance decision for this defined Association Carriage Digest v0 implementation scope. It does not turn digest equality into truth, support, authority, admission, verification of external reality, freshness, non-replay, external anchoring, creator/time/order evidence, or Human Final for any later ACR-v0 or CSAR-v0 scope.

Fixed implementation SHA:
21d5ff4dfa6b43b712108f12206373bc7e44c5cb

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Association Carriage Digest v0 (ACD-v0) only

Design freeze:
docs/next/ACD_V0_HUMAN_DESIGN_FREEZE_20261004.md

Design-freeze save commit:
6429d74b02fbacdaaa2fb62d33f830ba3a92d91f

## Implementation history

- initial implementation: 53d4c078ff0d521ce03bdd78046709b0ea99cddb
- R1 test-only remediation: 58faa0463ab79ba3287ddcb6f65bfa8caccd97b6
- R2 test-only final surface closure / fixed implementation and test SHA: 21d5ff4dfa6b43b712108f12206373bc7e44c5cb

Production implementation did not change during the R1 or R2 test remediations. Those commits changed only association_carriage_digest_v0/tests/test_association_carriage_digest.py.

## Accepted evidence

- golden vector 1: PASS
- golden vector 2: PASS
- final ACD focused tests: 21 passed, 5 subtests passed
- DSDS-v0 regression: 36 passed, 19 subtests passed
- production code changed during final R2 remediation: NO
- CLOSED scope changed: NO
- worktree clean before this documentation-only save
- pushed: NO

Golden vector results are the recorded implementation-test results against the vectors frozen in the design-freeze document. This Human Final does not add a new independent reproduction, a formal proof, or an external anchoring claim. The design-freeze record already states that Python hashlib and .NET SHA-256 agreed on those design vectors before the freeze.

## M1

Independent adversarial review found one material assurance gap.

M1:
tests did not initially close all prohibited caller-controlled digest, tag, helper, and export surfaces.

M1 was remediated test-only.

Final closure demonstrated KILLED:

- module tag helper
- neutral alias helper
- public TAG
- package re-export
- class staticmethod
- error-class method
- callable instance

M1 final status:
CLOSED

Material blockers:
0

## Safe semantics

ACD-v0 retains the safe semantics of its frozen design. The same code-owned tag and the same exact preimage bytes produce the same lowercase SHA-256. Within this tag, matching digests are treated as matching preimage commitments under the assumed collision resistance of SHA-256. ACD-v0 does not claim mathematical injectivity.

## Explicit nonclaims

ACD-v0 retains all nonclaims from its frozen design. ACD-v0 does not establish:

- ACR schema correctness
- CSAR correctness
- CSAR reproduction
- creator identity
- creation time
- order
- pre-execution occurrence
- claim truth
- support
- sufficiency
- completeness
- correspondence
- independence
- admission
- authority
- technical verification
- Human Final
- freshness
- non-replay
- external anchoring
- historical CLOSED-receipt binding
- equivalence with any other digest family
- proof that a receipt was created

The function sees bytes only. Equal 64-hex strings are not semantic equality with DSDS-v0 digests, untagged canonical digests, file SHA-256, or other legacy receipt digests.

## Boundary

This Human Final accepts only the defined ACD-v0 implementation scope at the fixed SHA above.

It does not:

- reopen or reinterpret DSDS-v0
- reopen or reinterpret any other CLOSED scope
- authorize CSAR-v0 implementation
- freeze ACR-v0
- implement ACR-v0

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
- CSAR-v0 Human Design Freeze unchanged; CSAR-v0 implementation remains not authorized
- ACR-v0 remains unfrozen and unimplemented
- no public push
- no private push

## Closure

After this record is saved, ACD-v0 is CLOSED for this defined scope. Any semantic change requires a new additive scope or version rather than silent modification of this accepted implementation.

## Change rule

Any future change to accepted ACD-v0 implementation semantics is a new scope/version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record. No push had been performed at the time of this acceptance.
