# Exact-Bytes Witness Public-Key Admission Prerequisite - D0

Date:
2026-10-05

Design status:
PREREQUISITE_REQUIRED

This document is a D0 boundary analysis only. It is not a Human Design Freeze, does not authorize implementation, does not admit a key, does not create a trust root, and does not create an identity or authorization mapping.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Base HEAD:
`deba2ffabc1b2d40ef368adc51e2e307fbabe093`

Exact-Bytes Witness v0 fixed reviewed implementation SHA:
`9d516deb654f09f6129cadf4f036a08fd30575aa`

Exact-Bytes Witness v0 Human Final:
`docs/next/EXACT_BYTES_WITNESS_V0_HUMAN_FINAL_20261005.md`

Exact-Bytes Witness v0 is CLOSED. This D0 does not modify or reinterpret it.

## Question

What is the smallest next prerequisite that can safely move from:

`valid signature over these exact bytes under this supplied key`

toward:

`this exact public key was admitted by a non-caller authority`

without allowing the signature, key holder, or runtime caller to bootstrap the key's own trust?

## Repository finding

No adequate CLOSED trust basis exists.

The repository has no CLOSED mechanism that supplies all of the following for Exact-Bytes Witness v0:

- an admitted Ed25519 public-key set
- a non-caller-controlled key selector
- a public-key identifier bound to exact raw key bytes
- a signer identity bound to an admitted key
- a role bound to an admitted key
- an authorization bound to an admitted key
- a revocation state for an admitted key
- a trust-root version or epoch governing an admitted key

Exact-Bytes Witness v0 intentionally accepts a caller-supplied exact public key and establishes only tuple validity under that supplied key.

Existing governance authorization records authorize bounded processes or repository actions. They do not constitute a machine-readable Ed25519 key admission registry.

The external authority-evidence verifier models smart-contract authority mechanisms, holder addresses, holder identity status, and runtime authority observations. It explicitly separates holder address from holder identity and does not provide an admitted Exact-Bytes Witness public-key set. Its `SIGNATURE_GATE` classification is not a key admission or signer identity primitive.

Recovery Execution Receipt v0 can record source-local signature-check observations, but it does not select an admitted key or create a trust root. Its accepted limitations preserve that boundary.

Human Final records are authoritative decisions for their stated scopes. No current Human Final admits an Exact-Bytes Witness public key. A Human Final document cannot be treated as a generic machine key registry without a new, separately frozen scope.

Therefore:

`EXISTING_CLOSED_TRUST_BASIS_FOUND: NO`

`PREREQUISITE_REQUIRED`

## Critical separation

The following remain distinct:

1. Cryptographic key validity: whether exact bytes are a syntactically acceptable Ed25519 public key and whether a signature verifies under them.
2. Key admission: whether a non-caller authority placed that exact key in a fixed admitted-key snapshot.
3. Signer identity binding: whether an admitted key is bound to a named person, organization, service, device, or pseudonymous signer reference.
4. Role binding: whether an admitted key is assigned a defined role.
5. Authorization: whether a role or signer may perform a defined action.
6. Independence: whether the signer satisfies an independence policy.
7. Provenance: whether the signer or key establishes origin or custody of an object.
8. Freshness, revocation, and anti-replay: whether an admission or signature remains current and non-replayed.
9. Evidence semantics: whether signed bytes are evidence, and of what kind.
10. Human Final: whether the Human Final authority accepted a scope or result.

The next prerequisite must address item 2 only. It must not infer items 3 through 10.

## Recommended next scope

Recommended name:

`Immutable Singleton Public-Key Admission Registry v0 Prerequisite`

This is a recommendation for a later design scope. This D0 does not create the registry and does not select or admit a key.

### Exact machine question

For one exact 32-byte Ed25519 public key and one fixed registry version:

> Are these exact 32 key bytes identical to the sole exact public key admitted in the code-owned, Human-Final-approved immutable registry snapshot for this version?

The answer is only version-relative membership.

It is not `trusted signer`, `identified signer`, `authorized signer`, `independent signer`, `provenance`, `fresh`, or `evidence`.

### Who selects the key

The runtime caller must not select the registry member.

The exact key bytes must be selected explicitly by the Human Final authority or another separately established non-caller admission authority in a future design-freeze decision. No such selection exists today.

### Who or what admits it

Admission requires an explicit non-caller decision over the exact raw key bytes and the exact immutable registry version. The later implementation may mechanically enforce the frozen bytes, but implementation code cannot grant admission to a key that the authority did not explicitly select.

The key cannot admit itself by signing its own admission record.

### Caller self-ratification

The runtime caller may present candidate key bytes for membership comparison only.

The caller must not supply:

- the registry body
- the admitted-key list
- a registry version selector
- an admission receipt
- an authority label
- a signer identity
- a role
- an authorization
- a trust level
- a revocation state

A signature made by the candidate key cannot alter the membership result.

### Changes and revocation

The v0 snapshot should be immutable and singleton.

Changing, adding, replacing, or removing the key requires a new additive registry version and a new explicit admission decision. It must not rewrite the old snapshot.

This v0 prerequisite does not establish revocation, currentness, or freshness. Running old code against the old registry can still report historical version-relative membership. A later lifecycle scope must define active-version selection, revocation, effective time, and rollback behavior before any claim of current trust is allowed.

### What it does not prove

Registry membership alone does not prove:

- possession of the private key
- signer identity
- signer role
- authorization
- independence
- creator identity
- key custody
- provenance
- freshness
- revocation status
- anti-replay
- evidence or evidence kind
- truth, support, relevance, sufficiency, or completeness
- admission of signed bytes as evidence
- Human Final for a signed object

### Missing prerequisite

The exact key and its non-caller admission decision do not exist in the current CLOSED surface.

Before a D1 registry design can be frozen, the Human Final authority must decide whether to admit any exact public key at all and, if yes, select the exact 32 raw bytes for the singleton snapshot. That decision must not be derived from a self-signature by the same key.

## Candidate comparison

### 1. Code-owned static admitted-key registry

Machine question:
Does the supplied exact key equal a code-owned admitted key in one fixed registry snapshot?

Key selector:
The future Human Final authority selects the exact registry key; the runtime caller does not.

Admission source:
An explicit future Human Design Freeze and Human Final decision over the exact key bytes and registry version.

Self-ratification:
Preventable if neither registry contents nor registry version are caller inputs and self-signatures have no admission effect.

Change or revocation:
New additive version only. v0 itself has no revocation or freshness semantics.

Nonclaims:
No identity, role, authorization, independence, provenance, evidence semantics, or currentness.

Dependency:
Requires the unresolved exact non-caller key-admission decision.

Assessment:
Smallest mechanically checkable candidate after that decision. A singleton is safer than a caller-selectable or extensible set in v0.

### 2. Human-Final-approved key admission receipt

Machine question:
Does a presented receipt say that this key was admitted?

Key selector:
Potentially the receipt author.

Admission source:
Unsafe unless the receipt is independently authenticated by a pre-existing trust root or compiled into a code-owned snapshot.

Self-ratification:
Yes, if the candidate key signs its own receipt or the caller supplies an unauthenticated Human Final label.

Change or revocation:
Would require receipt lineage, issuer identity, active-version rules, and revocation semantics.

Nonclaims:
Receipt shape alone proves no authority.

Dependency:
Requires an already trusted receipt issuer or external anchor.

Assessment:
Not minimal. Once pinned into code, it reduces to the static-registry candidate; without that pin, it is caller-controlled.

### 3. Externally anchored key manifest

Machine question:
Does this key appear in a manifest authenticated by a recognized external anchor?

Key selector:
The external manifest authority.

Admission source:
The external anchor and its verification policy.

Self-ratification:
Preventable only if the anchor is established independently of the candidate key and caller.

Change or revocation:
Requires manifest version, anchor rotation, freshness, retrieval, rollback, and revocation rules.

Nonclaims:
Manifest membership need not establish identity, role, authorization, or evidence semantics.

Dependency:
Requires an anchor verifier, anchor identity, transport or retrieval policy, versioning, and lifecycle semantics that do not exist in the CLOSED surface.

Assessment:
Potentially stronger, but not the smallest next scope.

### 4. Key fingerprint or value-class prerequisite

Machine question:
Do supplied bytes have a specified length or fingerprint?

Key selector:
The caller supplies the key; the fingerprint may also be caller supplied unless code-owned.

Admission source:
None.

Self-ratification:
Yes if fingerprint equality is promoted to trust.

Change or revocation:
Not applicable because no admission exists.

Nonclaims:
Only byte identity or formatting.

Dependency:
None for identity, but an admission decision is still missing.

Assessment:
Not sufficient. Exact-Bytes Witness v0 already receives exact 32-byte keys; naming or hashing them does not admit them.

### 5. Signer-reference binding receipt

Machine question:
Is an admitted key bound to a specific signer reference?

Key selector:
Must be an already admitted key.

Admission source:
Requires a trusted identity-binding authority.

Self-ratification:
Yes if caller-supplied signer labels or self-signed bindings are accepted.

Change or revocation:
Requires identity reassignment, supersession, and revocation rules.

Nonclaims:
A signer reference need not establish legal identity, role, authorization, or independence.

Dependency:
Depends on key admission and a separate identity-binding authority.

Assessment:
Too early. It collapses key admission with identity binding.

### 6. Trust-root or epoch prerequisite

Machine question:
Which trust-root version or epoch governs a key-admission decision?

Key selector:
The selected trust-root version would determine the eligible key set.

Admission source:
Requires an already established root and lifecycle authority.

Self-ratification:
Possible if caller selects the root or epoch.

Change or revocation:
This candidate is intended to model them, but requires rollback, expiry, overlap, and historical-verification rules.

Nonclaims:
An epoch does not itself establish identity, role, or authorization.

Dependency:
Requires a trust root that does not currently exist.

Assessment:
Not minimal for version-relative singleton membership. Required later before currentness, revocation, or freshness can be claimed.

## Why the recommendation is minimal

The static singleton registry introduces exactly one new mechanically checkable relation:

`candidate exact key bytes == frozen admitted exact key bytes`

It does not require a PKI, DID, certificate chain, online resolver, mutable database, role engine, authorization engine, identity directory, evidence-kind matrix, or revocation service.

It removes runtime caller control over the admitted key while preserving all later semantic boundaries.

A smaller key fingerprint predicate provides only identity and cannot create admission. A receipt or manifest requires an issuer or anchor that is itself missing. Identity, role, and authorization bindings all depend on key admission and are therefore later scopes.

## D1 entry conditions

A later D1 may begin only after an explicit non-caller decision supplies:

1. whether any key is admitted;
2. exactly one 32-byte raw Ed25519 public key, if admitted;
3. one immutable registry version identifier selected by design, not by runtime caller;
4. an explicit statement that membership means admission in that registry version only;
5. explicit nonclaims for identity, role, authorization, independence, provenance, freshness, revocation, anti-replay, evidence semantics, and Human Final;
6. confirmation that the candidate key's own signature is not admission evidence.

Until those conditions exist, the design status remains `PREREQUISITE_REQUIRED`.

## Required output positions

`KEY_ADMISSION_REQUIRED: YES`

`IDENTITY_BINDING_REQUIRED_NOW: NO`

`ROLE_BINDING_REQUIRED_NOW: NO`

`AUTHORIZATION_REQUIRED_NOW: NO`

`REVOCATION_REQUIRED_NOW: NO`

`EXTERNAL_ANCHOR_REQUIRED_NOW: YES`

Here, external anchor means an admission decision external to the runtime caller and candidate key. It does not require a full PKI or online certificate authority. The future Human Final authority may provide that decision for one immutable code-owned snapshot.

`CALLER_CAN_SELF_RATIFY: NO`

The `NO` position applies only to the recommended architecture, provided the registry bytes and version are code-owned and the non-caller admission decision exists. The current repository has no positive admission result.

## Nonclaims after the recommended scope

Even after a future singleton registry implementation:

`TRUSTED_SIGNER_CLAIMED_AFTER_THIS_SCOPE: NO`

`SIGNER_IDENTITY_CLAIMED_AFTER_THIS_SCOPE: NO`

`AUTHORIZATION_CLAIMED_AFTER_THIS_SCOPE: NO`

`INDEPENDENCE_CLAIMED_AFTER_THIS_SCOPE: NO`

`PROVENANCE_CLAIMED_AFTER_THIS_SCOPE: NO`

`FRESHNESS_CLAIMED_AFTER_THIS_SCOPE: NO`

`EVIDENCE_KIND_CREATED: NO`

`HUMAN_FINAL_AUTOMATED: NO`

## Closed-scope protection

This D0 does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, or Exact-Bytes Witness v0.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state.

It changes no production code, tests, requirements, or dependencies.

## Change rule

Any admitted-key registry, exact admitted key, key identifier, signer-reference mapping, role mapping, authorization, revocation, trust-root lifecycle, evidence-kind mapping, or admission effect requires a later separately authorized scope. None is created by this D0.

## Push status

NO. No public or remote push is authorized by this D0.
