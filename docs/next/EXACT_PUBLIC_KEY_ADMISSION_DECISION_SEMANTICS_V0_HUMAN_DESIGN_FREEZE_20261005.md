# Exact Public-Key Admission Decision Semantics v0 - Human Design Freeze

Date:
2026-10-05

`HUMAN_DESIGN_FREEZE_STATUS: ACCEPTED`

This record saves the Human Design Freeze of Exact Public-Key Admission Decision Semantics v0 D1. It does not amend the frozen D1, select or admit a key, perform an admission act, authorize implementation, or create identity, role, authorization, trust, provenance, evidence, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Frozen D1 design commit:
`7e8d499e6313d9d7aeb9e2805a3b28360f23e789`

Frozen D1 design document:
`docs/next/EXACT_PUBLIC_KEY_ADMISSION_DECISION_SEMANTICS_V0_D1_20261005.md`

## Accepted semantics

The frozen machine question remains:

> Are the candidate's exact 32 bytes equal to the sole Ed25519 public-key bytes explicitly admitted by the non-caller admission authority in the code-owned immutable snapshot `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`?

The positive result means version-relative exact-key membership for that immutable historical snapshot only.

The freeze accepts all of the following boundaries:

- No real public key is selected.
- No private key, seed, or other secret material is created or requested.
- No admission act is performed.
- No implementation is authorized.
- Human Final technical acceptance is not key admission.
- A later admission act must explicitly invoke the frozen admission capacity and bind exactly one future 32-byte Ed25519 public key to the exact frozen snapshot.
- A valid signature is not an admitted key.
- An admitted key is not signer identity.
- Signer identity is not role.
- Role is not authorization.
- Authorization is not truth.
- No trusted-signer, provenance, freshness, currentness, revocation, anti-replay, evidence, claim-support, or Human Final claim is created.
- The snapshot is immutable and historical. Replacement, addition, removal, or changed limitations require a new additive scope, snapshot, and admission act.
- The runtime caller cannot select or replace the registry, version, manifest, path, root, algorithm, digest, fingerprint, issuer, role, identity, authority, epoch, environment, signature, or admission record.
- The planned implementation review surface contains 24 attack tests and 10 source mutation operators.

## Origin-neutral conformance

`GENERALIZATION_RESULT: COMPATIBLE_AS_FROZEN`

`ORIGIN_NEUTRAL_KEY_ADMISSION: YES`

The frozen D1 admits exact key bytes, not a person, AI system, model, provider, service, organization, device, role, or signer identity. It contains no `actor_type`, model name, provider, signer-reference, identity, role, authorization, provenance, or trust field.

The human admission authority and the origin or later holder of the admitted key are distinct concepts. Human governance of the bounded admission act does not semantically classify the admitted key as a human key.

Consequently, a later separately frozen scope may bind the admitted exact key to a human signer reference, an AI execution or service signer reference, a verifier-service signer reference, or another narrowly defined signer reference. Such a binding is not part of Admission v0 and must not be inferred from key membership or signature validity.

`AI_EXECUTION_FUTURE_BINDING_COMPATIBLE: YES`

`HUMAN_FUTURE_BINDING_COMPATIBLE: YES`

`VERIFIER_SERVICE_FUTURE_BINDING_COMPATIBLE: YES`

`ADMISSION_V0_IDENTITY_SEMANTICS_ADDED: NO`

`ADMISSION_V0_ROLE_SEMANTICS_ADDED: NO`

`ADMISSION_V0_AUTHORIZATION_SEMANTICS_ADDED: NO`

Future signer-reference applicability is permitted only because the admitted key is origin-neutral. Admission v0 itself does not identify, authenticate, authorize, trust, or describe any human, AI execution, service, verifier, model, provider, or other actor.

## Frozen nonclaims

`REAL_KEY_SELECTED: NO`

`PRIVATE_KEY_CREATED_OR_REQUESTED: NO`

`ADMISSION_ACT_PERFORMED: NO`

`IMPLEMENTATION_AUTHORIZED: NO`

`TRUSTED_SIGNER_CLAIMED: NO`

`SIGNER_IDENTITY_CLAIMED: NO`

`SIGNER_ROLE_CLAIMED: NO`

`AUTHORIZATION_CLAIMED: NO`

`PROVENANCE_CLAIMED: NO`

`FRESHNESS_CLAIMED: NO`

`REVOCATION_CLAIMED: NO`

`EVIDENCE_KIND_CREATED: NO`

`HUMAN_FINAL_AUTOMATED: NO`

## Closed-scope protection

This freeze record does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, Exact-Bytes Witness v0, or any other CLOSED scope.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependencies, key registry, real key material, or admission receipt.

## Change rule

The frozen D1 may not be silently generalized by adding actor type, model, provider, identity, signer reference, role, authorization, provenance, trust, evidence, lifecycle, or currentness semantics. Each such concern requires a later additive and separately authorized scope.

## Push status

NO. No public or remote push is authorized by this Human Design Freeze save.
