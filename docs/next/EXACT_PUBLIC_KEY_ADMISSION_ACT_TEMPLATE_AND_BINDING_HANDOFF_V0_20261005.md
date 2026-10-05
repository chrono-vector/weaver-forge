# Exact Public-Key Admission Act Template and Binding Handoff v0

Date:
2026-10-05

Design status:
READY_FOR_HUMAN_DESIGN_FREEZE

This document is a design only. It does not perform a Human Design Freeze, select or admit a real key, create or request private material, perform an admission act, authorize implementation, or add identity, role, authorization, provenance, trust, freshness, revocation, evidence, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Base HEAD:
`8fe747acc5ea0aa93b4a6542dc27d3d8557b2476`

Frozen D1 design commit:
`7e8d499e6313d9d7aeb9e2805a3b28360f23e789`

Human Design Freeze save commit:
`8fe747acc5ea0aa93b4a6542dc27d3d8557b2476`

Frozen D1 design document:
`docs/next/EXACT_PUBLIC_KEY_ADMISSION_DECISION_SEMANTICS_V0_D1_20261005.md`

Human Design Freeze record:
`docs/next/EXACT_PUBLIC_KEY_ADMISSION_DECISION_SEMANTICS_V0_HUMAN_DESIGN_FREEZE_20261005.md`

Exact-Bytes Witness v0 and Exact Public-Key Admission Decision Semantics v0 are CLOSED. This design does not modify or reinterpret them.

## Recommended scope

`Exact Public-Key Admission Act Template and Binding Handoff v0`

The scope defines the exact two-phase shape of one later bounded Human admission act and the smallest origin-neutral value that later, separate signer-reference scopes may consume. It does not choose key material and does not define any signer reference.

## Machine question

> Can a future bounded Human admission act populate exactly one previously empty 32-byte Ed25519 public-key slot for `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` under the frozen D1 semantics, with exact transcription and confirmation checks, while exposing only a minimal origin-neutral handoff for later separate signer-reference binding scopes?

The answer at design time is structural only. There is no positive key-admission result until a later Human completes the frozen admission act with real public-key bytes.

## Why two phases are required

Two phases materially reduce wrong-key and transcription risk without adding a trust ceremony:

1. Prepare validates one exact key value and derives its lossless canonical display.
2. Confirm is a separate explicit Human act over that displayed value and the frozen admission constants.

Prepare has no admission effect. Confirm cannot silently inherit approval from an ordinary review or Human Final statement. The phases may occur in one bounded workflow, but the confirmation must be a distinct action after the prepared display is available.

`TWO_PHASE_CONFIRMATION_REQUIRED: YES`

## Exact key input rule

The semantic candidate is exactly one built-in `bytes` value of length exactly 32 representing an Ed25519 public key.

The admission mechanism rejects before preparation:

- zero, two, or more candidate keys
- lengths other than 32 bytes
- `bytes` subclasses
- `bytearray`
- `memoryview`
- strings
- lists, tuples, iterables, file-like objects, and paths
- PEM, DER, certificates, JSON objects, or wrapper records
- private keys, seeds, recovery phrases, expanded secret keys, or secret-key files

The algorithm is the code-owned exact constant `Ed25519`; it is not an input. The snapshot, admission effect, authority capacity, representation, and limitations are also code-owned constants.

## Display representation

The sole Human-readable representation is lowercase hexadecimal encoding of the exact 32 bytes:

- exactly 64 ASCII characters
- characters limited to `0-9` and `a-f`
- no `0x` prefix
- no whitespace, separators, line wrapping, comments, Unicode lookalikes, or normalization
- no uppercase acceptance or case folding

This hexadecimal text is a lossless display encoding, not a digest, fingerprint, key identifier, authority source, alternate key value, or caller-selected admission reference.

This document uses only the non-parseable placeholder:

`<64-lowercase-hex-of-future-public-key>`

It contains no operational public key and cannot pass the future parser.

## Required round-trip checks

Preparation must complete every check before presenting a candidate for confirmation:

1. Verify the candidate has exact type `bytes` and exact length 32.
2. Derive lowercase hexadecimal using a single code-owned encoder.
3. Verify the display has exact built-in `str` type, ASCII only, length 64, and only lowercase hexadecimal characters.
4. Decode the display with one strict code-owned decoder to an exact built-in `bytes` value.
5. Verify the decoded value has length 32.
6. Compare the decoded value to the original candidate using exact byte equality.
7. Re-encode the decoded value and verify exact text equality with the displayed value.
8. Fail closed before display or confirmation if any check fails.

No digest or fingerprint comparison can replace the byte and text round trips.

## Prepare phase

The future prepare operation accepts only the exact candidate bytes. It emits a non-authoritative, non-persistent prepared display with exactly these code-owned labels and one derived value:

| Item | Exact value |
|---|---|
| `act_kind` | `EXACT_PUBLIC_KEY_ADMISSION_ACT_V0` |
| `authority_capacity` | `EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0` |
| `frozen_d1_commit` | `7e8d499e6313d9d7aeb9e2805a3b28360f23e789` |
| `snapshot_version` | `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` |
| `algorithm` | `Ed25519` |
| `key_representation` | `RAW_32_OCTETS_DISPLAYED_AS_LOWERCASE_HEX` |
| `candidate_public_key_hex` | Strict lowercase hexadecimal derived from the exact candidate bytes |
| `admission_effect` | `VERSION_RELATIVE_EXACT_KEY_MEMBERSHIP` |
| `limitations` | The exact ordered frozen D1 limitations tuple |
| `prepare_effect` | `NO_ADMISSION_EFFECT` |

The prepared display must visibly state:

`PREPARE ONLY. THIS DOES NOT ADMIT A KEY.`

Preparation does not create a receipt, registry entry, authority token, evidence item, or reusable approval. Repository persistence, a commit, review approval, AI output, a candidate-key signature, or file presence cannot promote it into an admission act.

## Confirm phase

Confirmation is a separate bounded Human act after inspection of the prepared display. It must contain all of the following exact declarations with the future canonical lowercase hexadecimal value substituted once wherever the placeholder appears:

```text
I ACT IN THE CAPACITY EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0.
THIS IS A KEY ADMISSION ACT, NOT TECHNICAL ACCEPTANCE OR ORDINARY HUMAN FINAL REVIEW.
FROZEN_D1_COMMIT: 7e8d499e6313d9d7aeb9e2805a3b28360f23e789
SNAPSHOT_VERSION: EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0
ALGORITHM: Ed25519
KEY_REPRESENTATION: RAW_32_OCTETS_DISPLAYED_AS_LOWERCASE_HEX
PUBLIC_KEY_HEX: <64-lowercase-hex-of-future-public-key>
ADMISSION_EFFECT: VERSION_RELATIVE_EXACT_KEY_MEMBERSHIP
I CONFIRM THAT PUBLIC_KEY_HEX IS THE EXACT DISPLAY OF THE SINGLE 32-BYTE PUBLIC KEY I INTEND TO ADMIT FOR THIS SNAPSHOT.
I CONFIRM THAT NO CANDIDATE-KEY SIGNATURE, AI RECOMMENDATION, REPOSITORY PRESENCE, CALLER LABEL, OR ORDINARY HUMAN FINAL ACCEPTANCE SUPPLIES THIS ADMISSION AUTHORITY.
I CONFIRM THAT THIS ACT CREATES NO IDENTITY, ROLE, AUTHORIZATION, TRUST, PROVENANCE, FRESHNESS, REVOCATION, EVIDENCE, TRUTH, OR HUMAN FINAL CLAIM FOR A SIGNED OBJECT.
```

The confirmation mechanism must parse the exact snapshot, algorithm, representation, key text, effect, D1 commit, and declarations. It must strictly decode and round-trip the key text again, then compare the resulting bytes with the exact prepared candidate bytes. A mismatch, omission, duplicate field, altered constant, extra semantic field, or failed round trip rejects the act before admission.

The Human must actively submit this confirmation after the prepared display exists. Pre-approval, silence, UI defaulting, an already-checked box, inferred intent, an AI-generated statement, or reuse of unrelated Human Final text is not confirmation.

An exact duplicate confirmation for the same frozen snapshot and exact bytes has no additional effect. Use in another scope or snapshot is invalid. This rule prevents scope substitution but does not create freshness or general anti-replay semantics.

## Admission-act result boundary

A successfully completed future act authorizes only population of the one previously empty frozen public-key slot. The future implementation must still be separately authorized and reviewed before it can mechanically expose the D1 membership predicate.

The act does not establish possession of a private key. It never requests or accepts private-key, seed, recovery, or signing material. Proof of possession, if ever required, is a separate future scope and cannot create key admission retroactively.

`PRIVATE_KEY_REQUIRED: NO`

`PROOF_OF_POSSESSION_REQUIRED_NOW: NO`

`REAL_KEY_SELECTED: NO`

`ADMISSION_ACT_PERFORMED: NO`

## Origin-neutral binding handoff

The smallest permitted handoff value is the immutable typed pair:

```text
AdmissionBindingHandoffV0(
    snapshot_version = EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0,
    public_key_bytes = <the exact admitted built-in bytes value of length 32>
)
```

The snapshot member is the fixed code-owned constant, not caller text. The key member is the exact admitted value, not hexadecimal text, a digest, fingerprint, key ID, label, path, or manifest reference.

The handoff has meaning only when returned from the future code-owned admission component after exact membership succeeds. A caller-constructed, deserialized, copied, or modified lookalike has no admission authority. A later binding scope must obtain the handoff from that component or independently re-run the frozen admission predicate over the exact bytes; it must not trust a caller assertion that a handoff is admitted.

The handoff asserts only:

`these exact bytes are the admitted key bytes for EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`

It contains no actor type, signer reference, human name, AI model or provider, service name, verifier identity, role, authorization, trust, provenance, evidence, currentness, or lifecycle field.

Later separate scopes may pair this handoff with exactly one independently defined signer reference for a human signer, AI execution or service signer, or verifier service. Such pairing must define its own authority, ambiguity rules, lifecycle, and nonclaims. It must not alter Admission v0 or infer identity from a signature.

`HANDOFF_ASSERTS_IDENTITY: NO`

`HANDOFF_ASSERTS_ROLE: NO`

`HANDOFF_ASSERTS_AUTHORIZATION: NO`

`HANDOFF_ASSERTS_TRUST: NO`

`HUMAN_FUTURE_BINDING_COMPATIBLE: YES`

`AI_EXECUTION_FUTURE_BINDING_COMPATIBLE: YES`

`VERIFIER_SERVICE_FUTURE_BINDING_COMPATIBLE: YES`

## Digest boundary

The frozen D1 position remains:

`DIGEST_BINDING: NONE`

This template adds no digest or fingerprint. Lowercase hexadecimal is reversible display encoding and has no authority independent of its exact byte round trip.

If a later persistent handoff requires digest addressing, a new domain-separated digest and canonical encoding require a separate prerequisite and freeze. No existing CLOSED digest domain may be retrofitted.

`DIGEST_BINDING_ADDED: NO`

## Caller-control prevention

The runtime caller cannot select or replace:

- snapshot or version
- admission act kind or effect
- algorithm or key representation
- authority capacity
- frozen D1 commit
- limitations
- registry, manifest, path, root, or alternate admission source
- digest, fingerprint, key ID, or display encoder
- issuer, identity, signer reference, actor type, role, authorization, or trust label
- epoch, environment, currentness, revocation, or lifecycle status
- confirmation wording or confirmation target

The only future variable is the one exact key chosen by the bounded Human admission authority. The candidate key cannot self-ratify by signing its preparation, confirmation, or any other record. AI generation, repository commits, and ordinary Human Final acceptance have no admission effect.

`CALLER_SELF_RATIFICATION_PREVENTED: YES`

## Supersession model

`EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0` remains immutable and historical. The act cannot mark it current, active, latest, fresh, unrevoked, preferred, or superseded.

Replacing, adding, or removing a key requires a new additive scope, a new snapshot identifier, and a new explicit admission act. The v0 record and handoff are never edited in place. No caller may select an old or alternate snapshot and present it as current.

## Attack-test plan

The future implementation must include at least these 28 focused attack and boundary tests. They are not source mutants.

1. One-nibble display change rejects confirmation.
2. Wrong but well-formed 64-character key transcription rejects confirmation.
3. Uppercase hexadecimal is rejected rather than normalized.
4. Mixed-case hexadecimal is rejected.
5. Odd-length hexadecimal is rejected.
6. Non-hexadecimal characters are rejected.
7. Prefixes, whitespace, separators, and trailing text are rejected.
8. A 31-byte key is rejected.
9. A 33-byte key is rejected.
10. A `bytes` subclass is rejected.
11. `bytearray`, `memoryview`, and string inputs are rejected.
12. Two keys, an iterable, or a wrapper record is rejected.
13. Candidate-key self-signature has no admission effect.
14. Ordinary Human Final text is not confirmation.
15. AI-generated approval is not confirmation.
16. Wrong snapshot or version is rejected.
17. Alternate algorithm or representation is rejected.
18. Identity, actor type, model, provider, role, authorization, trust, provenance, or evidence fields are rejected.
19. Caller-selected handoff or handoff lookalike has no admission authority.
20. Historical snapshot cannot be rendered as current, active, or unrevoked.
21. Private key, seed, recovery phrase, or secret-key file is rejected.
22. Display decode or encode round-trip mismatch rejects before confirmation.
23. Confirmation for bytes different from the prepared bytes is rejected.
24. Omitted confirmation or pre-approved confirmation is rejected.
25. Confirmation replayed in another scope or snapshot is rejected.
26. Alternate manifest, path, root, environment, or registry is rejected.
27. Missing, duplicated, reordered where order is fixed, or altered declarations and limitations are rejected.
28. Digest, fingerprint, key ID, issuer label, signature, or repository commit cannot substitute for exact byte admission.

Positive tests must use unmistakably synthetic non-operational vectors and must not admit them to the production snapshot.

## Future source-mutation plan

A separately authorized implementation campaign should verify that tests kill at least these 14 source mutations:

1. Accept a non-`bytes` exact key value.
2. Accept a `bytes` subclass.
3. Change exact key length from 32.
4. Accept uppercase, whitespace, prefixes, separators, or noncanonical display.
5. Skip display decode or either round-trip equality check.
6. Compare a prefix, suffix, text, digest, fingerprint, or key ID instead of exact bytes.
7. Allow more than one candidate key.
8. Merge prepare and confirm so preparation admits the key.
9. Accept ordinary Human Final, AI output, repository presence, or candidate signature as confirmation.
10. Add a caller-selectable snapshot, algorithm, effect, root, path, registry, or handoff.
11. Permit a caller-constructed handoff without re-running admission.
12. Add identity, actor type, role, authorization, trust, provenance, evidence, or currentness output.
13. Accept private-key or seed material.
14. Mutate the historical v0 snapshot in place.

This plan does not authorize implementation or mutation tooling.

## Exact later Human action

After Human Design Freeze of this template, selecting a real public key is safe only through this bounded sequence:

1. The Human obtains one intended Ed25519 public key through a separately controlled process outside this scope; no private material is provided to the admission mechanism.
2. A future separately authorized prepare tool receives exactly one built-in 32-byte public-key value and performs every frozen validation and round-trip check.
3. The Human inspects the complete prepared display, including the exact 64-character lowercase hexadecimal value and all frozen constants.
4. In a distinct action, the Human submits the exact confirmation block while explicitly invoking `EXACT_PUBLIC_KEY_ADMISSION_AUTHORITY_V0`.
5. The confirmation mechanism strictly parses and round-trips the display, verifies equality with the prepared exact bytes, and rejects any mismatch or semantic addition.
6. Only then may the bounded admission act identify those exact bytes for later code-owned implementation under a separately authorized implementation scope.

No key is selected by this document. Human Design Freeze of this template alone still does not admit a key.

`SAFE_TO_SELECT_REAL_KEY_AFTER_FREEZE: YES`

The `YES` is conditional on Human Design Freeze of this template and execution of the exact separate two-phase Human action above.

## Remaining prerequisites

No smaller semantic prerequisite is required before this template can be frozen.

After freeze, the unresolved prerequisite is the Human's separate real public-key sourcing and two-phase admission act. A separately authorized implementation scope remains required afterward. Proof of possession, signer-reference binding, persistent digest addressing, identity, role, authorization, revocation, and currentness remain independent future scopes.

## Closed-scope protection

This design does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, Exact-Bytes Witness v0, Exact Public-Key Admission Decision Semantics v0, or any other CLOSED scope.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependencies, registry, real key, private material, admission decision, or admission receipt.

## Push status

NO. No public or remote push is authorized by this design.
