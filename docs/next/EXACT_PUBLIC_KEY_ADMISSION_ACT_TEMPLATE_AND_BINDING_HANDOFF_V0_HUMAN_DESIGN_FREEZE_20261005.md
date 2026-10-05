# Exact Public-Key Admission Act Template and Binding Handoff v0 - Human Design Freeze

Date:
2026-10-05

`HUMAN_DESIGN_FREEZE_STATUS: ACCEPTED`

This record saves the Human Design Freeze of Exact Public-Key Admission Act Template and Binding Handoff v0. It does not amend the frozen design, select or admit a real key, create or request private material, perform an admission act, authorize implementation, or create identity, role, authorization, trust, provenance, evidence, truth, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Frozen design commit:
`68625cee90cb322cef19b4d3927744c2177ad9dc`

Frozen design document:
`docs/next/EXACT_PUBLIC_KEY_ADMISSION_ACT_TEMPLATE_AND_BINDING_HANDOFF_V0_20261005.md`

## Accepted admission-act model

The frozen model uses two separate phases:

1. `PREPARE` accepts exactly one built-in `bytes` value of exactly 32 bytes representing an Ed25519 public key, validates it, derives its canonical display, and has `NO_ADMISSION_EFFECT`.
2. `CONFIRM` is a separate active Human act after inspection of the prepared display. It explicitly invokes `EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0` for `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` and confirms `VERSION_RELATIVE_EXACT_KEY_MEMBERSHIP` for the exact displayed bytes.

Ordinary Human Final acceptance, Human Design Freeze, repository commits, candidate-key signatures, AI recommendations, caller labels, and mere file presence do not perform confirmation and do not admit a key.

The canonical Human-readable public-key display is exactly 64 lowercase ASCII hexadecimal characters with no prefix, whitespace, separator, case folding, normalization, or alternate encoding. The display must strictly round-trip to the exact original 32-byte value and back to identical text before confirmation.

## Accepted handoff boundary

The handoff remains the origin-neutral immutable typed pair of:

- fixed snapshot `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`
- exact admitted built-in 32-byte public-key value

The handoff states version-relative exact-key membership only. It does not identify a human, AI execution or service, verifier service, model, provider, organization, device, or other signer reference.

Future signer-reference binding requires a separate scope. Admission v0 gains no identity, role, authorization, trust, provenance, truth, freshness, revocation, evidence, or Human Final semantics.

The following distinctions remain frozen:

`valid signature != admitted key != identity != role != authorization != truth`

## Private-key boundary

The admission mechanism does not require, accept, create, or request a private key, seed, recovery phrase, expanded secret key, or secret backup. Proof of possession is not required for admission and remains a separate possible future scope.

`PRIVATE_KEY_REQUIRED_BY_ADMISSION: NO`

`PROOF_OF_POSSESSION_REQUIRED_NOW: NO`

`REAL_KEY_SELECTED: NO`

`PRIVATE_KEY_CREATED_OR_REQUESTED: NO`

`ADMISSION_ACT_PERFORMED: NO`

`IMPLEMENTATION_AUTHORIZED: NO`

## Historical snapshot and supersession

`EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` is immutable and historical. The frozen model creates no current, active, latest, fresh, unrevoked, preferred, or superseded status.

Replacing, adding, or removing a key requires a new additive scope, snapshot identifier, and explicit admission act. The v0 snapshot and handoff cannot be edited in place or relabeled as current.

## Planned assurance surface

The frozen design plans:

- 28 focused attack and boundary tests
- 14 separately defined source mutation operators

These plans do not authorize implementation, test changes, mutation tooling, or dependency changes.

## Closed-scope protection

This freeze record does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, Exact-Bytes Witness v0, Exact Public-Key Admission Decision Semantics v0, the accepted Admission Act Template and Binding Handoff v0, or any other CLOSED scope.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependencies, registry, key material, admission decision, or receipt.

## Push status

NO. No public or remote push is authorized by this Human Design Freeze save.
