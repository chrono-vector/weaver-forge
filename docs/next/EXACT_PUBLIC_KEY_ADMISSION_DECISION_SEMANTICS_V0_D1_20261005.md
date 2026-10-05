# Exact Public-Key Admission Decision Semantics v0 - D1

Date:
2026-10-05

Design status:
READY_FOR_HUMAN_DESIGN_FREEZE

This document is a D1 design only. It is not a Human Design Freeze, does not select or admit a real key, does not authorize implementation, and does not create identity, role, authorization, trust, provenance, freshness, revocation, evidence, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Base HEAD:
`5a6aac0a5d7714b8e309463328f7d9c6e7095261`

Predecessor D0:
`docs/next/EXACT_BYTES_WITNESS_PUBLIC_KEY_ADMISSION_PREREQUISITE_D0_20261005.md`

Exact-Bytes Witness v0 is CLOSED. This D1 does not modify or reinterpret it.

## Recommended scope

`Exact Public-Key Admission Decision Semantics v0`

The scope defines one immutable, singleton, non-caller admission decision and one version-relative exact-byte membership predicate. It does not define a registry service, mutable manifest, trust-root lifecycle, signer identity, role, authorization, revocation, or evidence admission.

## Machine question

For one exact candidate value of type `bytes`:

> Are these exact 32 bytes equal to the sole Ed25519 public-key bytes explicitly admitted by the non-caller admission authority in the code-owned immutable snapshot `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`?

The machine question has no caller-selectable snapshot, manifest, path, root, key identifier, fingerprint, issuer, role, epoch, algorithm, or admission record.

## Admission definition

Admission is the conjunction of all of the following:

1. A later Human Final authority acts explicitly in the separately named capacity `EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0`.
2. That act names this frozen scope and states that it is an admission act, not ordinary technical acceptance.
3. The act supplies exactly one exact 32-byte Ed25519 public key for exactly the immutable snapshot `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`.
4. The future implementation embeds the resulting exact decision as a code-owned constant and exposes only exact candidate-byte comparison.
5. The candidate key, its holder, an AI reviewer, the runtime caller, a signature, a repository file merely containing bytes, or an ordinary Human Final statement cannot supply or modify the admission decision.

Hardcoding, hashing, naming, fingerprinting, repository presence, successful signature verification, or self-signing is not admission by itself. The code-owned record is the mechanical preservation of the explicit admission act; implementation code does not bootstrap the act's authority.

No admission act has occurred in this D1.

## Admission authority boundary

The sole admission authority for v0 is the future human actor explicitly exercising `EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0` under a Human Design Freeze that accepts this D1 and a later, separately recorded Human Final admission act.

That authority is bounded to selecting one exact raw Ed25519 public key for one immutable snapshot. It does not gain authority to establish signer identity, role, authorization, trust, independence, provenance, freshness, revocation, anti-replay, evidence status, claim truth, or Human Final for any signed object.

Human Final technical acceptance of this D1, Exact-Bytes Witness v0, an implementation, a test run, or a review does not admit any key. Admission requires the later act to use the exact admission-capacity name and to state the exact key bytes and snapshot.

`HUMAN_FINAL_TECHNICAL_ACCEPTANCE_EQUALS_ADMISSION: NO`

## Frozen decision value

The future admitted decision is one internal immutable value with exactly these fields and no others:

| Field | Exact v0 rule |
|---|---|
| `schema_version` | Exact code-owned string `exact_public_key_admission_decision.v0` |
| `authority` | Exact boolean `false`; the value is not a general authority, execution gate, evidence authority, or authorization token |
| `algorithm` | Exact code-owned string `Ed25519` |
| `key_representation` | Exact code-owned string `RAW_32_OCTETS` |
| `public_key_bytes` | Exact built-in `bytes`, length exactly 32; supplied only by the later bounded human admission act |
| `snapshot_version` | Exact code-owned string `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` |
| `admission_effect` | Exact code-owned string `VERSION_RELATIVE_EXACT_KEY_MEMBERSHIP` |
| `admission_status` | Exact code-owned string `ADMITTED` |
| `limitations` | Exact ordered tuple defined below, with no omission, addition, replacement, or reordering |

The exact ordered `limitations` tuple is:

1. `NO_SIGNER_IDENTITY`
2. `NO_SIGNER_ROLE`
3. `NO_AUTHORIZATION`
4. `NO_TRUST_CLAIM`
5. `NO_INDEPENDENCE_CLAIM`
6. `NO_PROVENANCE_CLAIM`
7. `NO_FRESHNESS_OR_CURRENTNESS`
8. `NO_REVOCATION_OR_ANTI_REPLAY`
9. `NO_EVIDENCE_OR_CLAIM_SUPPORT`
10. `NO_HUMAN_FINAL_FOR_SIGNED_OBJECT`

The value has no generic extension map. Unknown or extra fields are rejected. It has no issuer, signer reference, key ID, fingerprint, role, identity, trust level, authorization, epoch, effective time, expiry, revocation, current-version marker, path, URI, alternate root, signature, or caller-provided digest.

If serialized for a future test fixture, serialization is not an authority source. A JSON form, if introduced later, must use a duplicate-key-rejecting parser, exact field set and types, and a separately frozen canonical encoding. This D1 does not choose JSON or authorize a persistent receipt.

## Key representation

The semantic key value is exactly one built-in `bytes` object of length 32. Byte subclasses, `bytearray`, `memoryview`, text, hexadecimal strings, Base64 strings, PEM, DER, certificates, paths, file-like objects, and iterables are not equivalent representations and must be rejected before comparison.

No operational key bytes appear in this design. Tests may use unmistakably synthetic 32-byte vectors with no admission effect.

`REAL_KEY_SELECTED: NO`

`ALGORITHM: Ed25519`

`KEY_REPRESENTATION: exact built-in bytes; length 32; singleton`

## Snapshot/version model

`EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` is a code-owned immutable historical snapshot identifier. The public predicate does not accept a version parameter. Runtime configuration, environment variables, files, paths, manifests, command-line arguments, network responses, caller records, and plugin values cannot select or replace it.

The snapshot contains exactly one admitted key. Zero, two, or more keys are invalid implementation states, not alternate v0 outcomes.

The snapshot identifier is not an epoch and does not mean current, active, fresh, unrevoked, latest, preferred, or superseded. Old code may continue to answer the historical v0 membership question. No v0 result may be presented as current admission.

## Admission effect and result vocabulary

The sole positive effect is:

`candidate exact bytes are the admitted key bytes for EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`

The sole negative effect is:

`candidate exact bytes are not the admitted key bytes for EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`

The future predicate's closed result vocabulary is:

- `EXACT_KEY_ADMITTED_FOR_SNAPSHOT_V0`
- `EXACT_KEY_NOT_ADMITTED_FOR_SNAPSHOT_V0`

Malformed or wrong-type input is a closed validation failure and is not converted to either semantic result.

Words such as `trusted`, `verified signer`, `identified`, `authorized`, `approved`, `independent`, `current`, `valid authority`, and `evidence` are forbidden in result names and positive-result explanations.

## Digest binding

No existing CLOSED digest domain safely binds this admission decision.

DSDS-v0 permits only `R4_CLAIM_BODY`, `PRESENTED_SUBJECT_BYTES`, and `CSAR_RECORD`. Reusing any of them would reinterpret a CLOSED domain. ACD-v0's digest is specific to its CLOSED association-carriage record. An untagged SHA-256, caller digest, key fingerprint, or ad hoc tag would create an unfrozen digest primitive.

Therefore v0 has no decision-digest or fingerprint field. Any supplied digest or fingerprint is rejected and has no authority. Exact in-memory field equality and exact key-byte equality are the whole v0 binding.

A persistent, digest-addressed admission record would require a later separately frozen digest-domain and canonical-encoding prerequisite. That prerequisite is not required for this memory-only, code-owned singleton predicate.

## Caller-control prevention

The future public interface accepts only `candidate_public_key: bytes`. It must not accept or discover any of the following:

- snapshot or version selector
- admission record, manifest, registry, receipt, or path
- admitted key, key ID, fingerprint, or expected digest
- algorithm or key representation selector
- authority, issuer, signer, identity, role, or authorization label
- root, anchor, epoch, current-version, environment, or configuration selector
- signature over an admission record

The predicate reads one code-owned internal decision. Dependency injection, monkey-patched alternate decisions, subclass tricks, fallback files, environment overrides, and runtime registry extension are outside the permitted production surface and must be guarded by tests appropriate to the implementation language.

A valid signature under the candidate key cannot change a negative membership result. The candidate key cannot sign itself into the snapshot. AI approval, reviewer agreement, test success, repository merge, and ordinary Human Final technical acceptance have no admission effect.

## Nonclaims

`TRUSTED_SIGNER_CLAIMED_AFTER_THIS_SCOPE: NO`

`SIGNER_IDENTITY_CLAIMED_AFTER_THIS_SCOPE: NO`

`SIGNER_ROLE_CLAIMED_AFTER_THIS_SCOPE: NO`

`AUTHORIZATION_CLAIMED_AFTER_THIS_SCOPE: NO`

`INDEPENDENCE_CLAIMED_AFTER_THIS_SCOPE: NO`

`PROVENANCE_CLAIMED_AFTER_THIS_SCOPE: NO`

`FRESHNESS_CLAIMED_AFTER_THIS_SCOPE: NO`

`REVOCATION_CLAIMED_AFTER_THIS_SCOPE: NO`

`CURRENTNESS_CLAIMED_AFTER_THIS_SCOPE: NO`

`EVIDENCE_KIND_CREATED: NO`

`CLAIM_SUPPORT_CREATED: NO`

`HUMAN_FINAL_AUTOMATED: NO`

`EXTERNAL_REAL_WORLD_TRUST_ANCHOR_PROVIDED: NO`

The non-caller admission act is a repository-governance decision only. It is not an independently authenticated real-world identity or trust anchor.

## Supersession and lifecycle

The v0 snapshot is immutable. Key replacement, addition, removal, or changed limitations requires a new additive scope, a new explicit admission act, a new snapshot identifier, and a new implementation review. The old snapshot must not be edited in place.

This D1 does not select an active snapshot and defines no supersession effect. It does not authorize a caller to request an old snapshot as though it were current. Revocation, compromise response, rollback, expiry, rotation overlap, active-version selection, and currentness remain deferred.

## Attack-test specification

The later implementation must include at least the following 24 focused negative or boundary tests. These are attack tests, not source mutants.

1. Candidate self-signature cannot create admission.
2. A signature over a purported admission record cannot create admission.
3. Caller-selected snapshot or version is unavailable or rejected.
4. Caller-selected alternate manifest is unavailable or rejected.
5. Caller-selected path is unavailable or rejected.
6. Caller-selected alternate root or registry is unavailable or rejected.
7. Algorithm substitution is unavailable or rejected.
8. Key-byte swap produces the negative membership result.
9. Non-32-byte values are rejected before comparison.
10. Non-`bytes` values are rejected before comparison.
11. `bytes` subclasses are rejected before comparison.
12. Two-key or iterable smuggling is rejected.
13. Fingerprint substitution is unavailable or rejected.
14. Caller digest substitution is unavailable or rejected.
15. Key ID or label equality cannot substitute for exact bytes.
16. Identity, role, authorization, trust, currentness, or issuer injection is rejected.
17. Unknown or extra record fields are rejected in internal construction tests.
18. Missing, added, replaced, or reordered limitations are rejected.
19. Duplicate JSON keys are rejected if JSON is ever introduced for fixtures.
20. Ordinary Human Final technical acceptance cannot create admission.
21. An unauthenticated string containing `Human Final` cannot create admission.
22. AI approval or reviewer agreement cannot create admission.
23. An old snapshot result cannot be rendered as current or unrevoked.
24. Runtime environment, configuration, network, or file content cannot replace the code-owned decision.

Positive tests are limited to exact equality against a synthetic frozen test decision and exact negative inequality. Synthetic test vectors must be visibly non-operational and must not be imported by production code.

## Future source-mutation plan

If implementation is later authorized, a separate mutation campaign should verify that tests kill at least these source changes:

1. Accepting `bytearray`, `memoryview`, or a `bytes` subclass.
2. Changing exact length from 32.
3. Replacing exact equality with prefix, suffix, textual, case-insensitive, or fingerprint comparison.
4. Adding a caller-selectable snapshot, record, algorithm, path, root, or expected digest.
5. Loading the admitted decision from environment, file, network, plugin, or runtime configuration.
6. Allowing more than one admitted key.
7. Treating signature validity as admission.
8. Dropping or reordering a limitation.
9. Adding identity, role, authorization, trust, freshness, revocation, evidence, or Human Final output.
10. Labeling the historical snapshot as current.

This mutation plan does not authorize implementation or mutation tooling.

## Material counterexamples closed by the design

- A self-signed admission record fails because signatures are not an admission source and no record is caller input.
- A key substitution fails because only exact 32-byte equality with the singleton internal value can return the positive result.
- Snapshot, manifest, path, root, algorithm, identifier, fingerprint, digest, issuer, role, and epoch substitution fail because none are public inputs or runtime selectors.
- Ordinary Human Final acceptance fails because the later act must explicitly name the admission capacity, this scope, exact bytes, and exact snapshot.
- Social or persistent laundering fails within v0 because the result vocabulary carries only historical version-relative membership and the design creates no receipt, identity, trust, evidence, or currentness claim.

The last point is a semantic boundary, not a claim that downstream humans cannot misuse text. Downstream systems must not relabel the v0 result; preventing all social misuse is outside machine enforcement.

## Closed-scope protection

This D1 does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, or Exact-Bytes Witness v0.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependencies, registry, real key, or receipt.

## Bounded later human act

After Human Design Freeze of this D1, real-key selection is safe only through one separate Human Final act containing all of the following:

1. Exact invocation of the capacity `EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0`.
2. Exact reference to the frozen D1 document and its fixed reviewed commit.
3. Exact statement `THIS IS A KEY ADMISSION ACT, NOT TECHNICAL ACCEPTANCE`.
4. Exactly one raw Ed25519 public key represented unambiguously as 32 octets, with a required exact byte transcription check before implementation.
5. Exact snapshot identifier `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`.
6. Exact admission effect `VERSION_RELATIVE_EXACT_KEY_MEMBERSHIP`.
7. The complete ordered limitations tuple from this D1.
8. Explicit statement that no signature by the candidate key, AI approval, repository presence, or ordinary Human Final acceptance supplied the admission authority.
9. Explicit authorization for a later implementation scope, if implementation is desired; the admission act itself does not implement anything.

The act must select neither an identity nor a role and must not call the key trusted, authorized, current, unrevoked, independent, or evidentiary.

## D1 conclusion

The admission semantics are coherent without an evidence-completeness authority because admission is not evidence aggregation and makes no claim about evidence. The v0 predicate asks only one closed singleton membership question.

`NON_CALLER_FROZEN_ADMISSION_ACT_PROVIDED: NO`

`EXTERNAL_REAL_WORLD_TRUST_ANCHOR_PROVIDED: NO`

`SAFE_TO_SELECT_REAL_KEY_AFTER_D1_FREEZE: YES`

The `YES` is conditional on an actual Human Design Freeze of this D1 and use of the exact bounded later human act above. This document itself is not that freeze and does not permit key selection yet.

## Push status

NO. No public or remote push is authorized by this D1.
