# Exact-Bytes Witness v0 - Human Final

Date:
2026-10-05

Human Final:
HUMAN_REVIEW_ACCEPTED

This document records a Human Final decision explicitly made by the sole Human Final authority. It does not record an AI acceptance decision. The independent reviewer is not the Human Final authority.

HUMAN_REVIEW_ACCEPTED accepts the frozen Exact-Bytes Witness v0 contract and its implementation and tested envelope within this scope.

Fixed reviewed implementation SHA:
9d516deb654f09f6129cadf4f036a08fd30575aa

This Human Final documentation commit is a later save. It does not replace the fixed reviewed implementation SHA above. No later production, test, or requirements commit is part of this acceptance.

Repository:
C:\dev\Weaver\weaver-forge-r4

Scope:
Exact-Bytes Witness v0 only

Human Final status:
HUMAN_REVIEW_ACCEPTED

Material blockers:
0

Exact-Bytes Witness v0 status after this record:
CLOSED

Push:
FORBIDDEN

## Design freeze

Human Design Freeze:
ACCEPTED

Freeze document:
`docs/next/EXACT_BYTES_WITNESS_V0_HUMAN_DESIGN_FREEZE_20261005.md`

Design-freeze save commit:
`81d0336daa2964a0b51863d151c5c49d850c42be`

Freeze vector correction commit:
`25ca2c8097d8a96b90ba9ca8a60b7ca0383e93a9`

The correction is NONMATERIAL. The RFC 8032 section 7.1 TEST 2 signature was corrected from malformed or incomplete 120 hex characters to the authoritative 128 hex characters. The frozen semantics did not change.

## Frozen contract

Profile:

- Ed25519, RFC 8032 pure
- `RAW_EXACT_BYTES`
- exact 32-byte public key
- exact 64-byte signature
- fixed algorithm and no caller selector

Frozen runtime dependencies:

- `cryptography==50.0.2`
- `cffi==2.1.1`
- `pycparser==3.0`

The dependencies are hash-locked in:
`requirements/exact-bytes-witness-v0.txt`

Public API:

`verify_exact_bytes_witness(public_key: bytes, signature: bytes, message: bytes) -> str`

Success:
`EXACT_BYTES_WITNESS_VALID`

Failure:
`EXACT_BYTES_WITNESS_REJECTED`

## Review history

The initial independent review was BLOCKED solely because the review machine had `cryptography` 50.0.1 and `cffi` 2.0.0 instead of the frozen versions.

At that stage:

- code material findings: 0
- freeze conformance: PASS
- RFC vectors: PASS
- public API: PASS
- exact-byte behavior: PASS
- semantic-promotion resistance: PASS
- fail-closed behavior: PASS
- CLOSED-scope safety: PASS
- read-only deviation: NONE

The independent review is not this Human Final and is not an independent reproduction claim.

## Source-mutation results

Independent source mutations:

- executed: 14
- KILLED: 12
- EQUIVALENT: 2
- SURVIVED: 0

Equivalent mutations:

- S08: removal of the explicit public-key-length check was observationally equivalent under the frozen observable contract because the underlying Ed25519 parser rejects the tested wrong lengths with the frozen rejection semantics.
- S09: removal of the explicit signature-length check was observationally equivalent under the frozen observable contract because the underlying verification rejects the tested wrong lengths with the frozen rejection semantics.

S08 and S09 remain classified as EQUIVALENT. They must not be rewritten as KILLED.

## Blocker clearance

The environment blocker was CLEARED using a clean temporary virtual environment outside the repository and without `--system-site-packages`.

Frozen requirements were installed with:

- `--require-hashes`
- `--only-binary :all:`

Actual versions:

- Python 3.14.3
- cryptography 50.0.2
- cffi 2.1.1
- pycparser 3.0

Version mocking:
NO

Accepted test results:

- Exact-Bytes Witness focused tests: 38/38 PASS
- planned attacks: 36/36 PASS
- PSRD-v0 regression: 39 passed
- DSDS-v0 regression: 36 passed
- CSAR-v0 regression: 45 passed
- ACD-v0 regression: 21 passed
- ACR-v0 regression: 27 passed
- SUBP-v0 regression: 29 passed
- relevant regressions total: 197 passed and 143 subtests
- new material findings: 0

The system environment was not changed. The repository was not changed by the review. The temporary environment was cleaned. HEAD remained unchanged and the worktree was clean.

## Reproduction transparency

An initial temporary environment created with `--system-site-packages` was rejected as decisive evidence because system `pycparser` could be treated as already satisfied without hash verification.

The decisive reproduction used a fresh clean virtual environment.

`pytest` was not added to the frozen production dependencies. Existing system `pytest` was exposed only as test tooling through `sys.path` ordering, while assertions verified that the frozen runtime packages loaded from the clean virtual environment.

There was no system or repository mutation.

## Semantic boundary

`EXACT_BYTES_WITNESS_VALID` establishes only that the pinned verifier accepted the supplied exact 64-byte signature as a pure Ed25519 signature over the supplied exact message bytes under the supplied exact 32-byte public key and frozen profile.

It does not establish:

- a trusted key or trusted signer
- signer identity
- signer authorization
- signer independence
- creator identity
- strong provenance
- timestamp
- freshness
- anti-replay
- evidence or an evidence kind
- truth
- support
- relevance
- sufficiency
- completeness
- admission
- authority
- real-world correspondence
- Human Final

The identical public-key, signature, and message tuple may verify again. Such replay is not anti-replay.

This Human Final does not create an independent reproduction claim. AI agreement is not evidence.

## Next unresolved prerequisite

Public-key trust, signer identity, and authorization remain unresolved.

Claim-Evidence Compatibility remains deferred.

## Closed-scope boundary

This Human Final accepts only the defined Exact-Bytes Witness v0 implementation at the fixed reviewed implementation SHA.

It does not modify or reinterpret:

- R3
- R4
- WVMA-V1
- Tested-Envelope Receipt v0
- Recovery Preflight v0
- Independent Verification Preflight v0
- Conducting Receipt v0
- Recovery Execution Receipt v0
- Evidence Binding DAG v0
- Domain-Separated Digest Spec v0
- Association Carriage Digest v0
- Claim / Subject Association Record v0
- Association Carriage Receipt v0
- Presented-Subject Role Descriptor v0
- Strict UTF-8 Byte Predicate v0

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state.

This documentation-only save changes no production code, tests, requirements, dependencies, or accepted CLOSED-scope semantics.

## Closure

EXACT_BYTES_WITNESS_V0_CLOSED:
YES

MATERIAL_BLOCKERS:
0

After this record is saved, Exact-Bytes Witness v0 is CLOSED for this defined scope. Any future semantic change requires a new additive scope or version and must not silently rewrite this Human Final.

## Push status

NO. No public or remote push is authorized by this record. No push was performed as part of this Human Final save.
