# Exact-Bytes Witness Verification — D1

Date:
2026-10-05

Design status:
CANDIDATE / NOT A HUMAN DESIGN FREEZE

DESIGN_STATUS:
PREREQUISITE_REQUIRED

This document is not a Human Design Freeze. It does not authorize implementation. It does not add a dependency. It does not choose a signature algorithm. It defines no producer, no record, no schema, no digest, and no success tag.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD:
939f71c31147cbf8617b5ba6b3f38b677dcc9d27

D0:
docs/next/EXACT_BYTES_WITNESS_VERIFICATION_PREREQUISITE_D0_20261005.md

D0 remains in force. Claim–Evidence Compatibility is not ready. SUBP-v0 is not sufficient. This D1 does not reopen that decision.

Recommended next scope:
Audited Public-Key Verification Dependency Prerequisite

## Machine question

Does this repository already expose one stable, explicit public-key verification dependency that a witness predicate can call without adding a dependency or implementing cryptography?

The answer on this tree is no.

## What a valid signature would still not tell us

No signature result exists in this scope. A later valid signature, if a reviewed verifier is frozen, would still not tell us who trusts the key, who the signer is, whether the signer is authorized or independent, who created the bytes, whether the bytes are evidence, whether they are true, whether they support a claim, whether the witness is fresh, whether the tuple may be replayed, or whether anyone admitted it. It would mean only that the supplied signature checks for the supplied bytes under the supplied public key and one frozen algorithm.

Key trust, witness identity, and authorization stay unresolved after that future check. They are not this D1.

## Repository inspection

The epistemic packages on this branch call SHA-256 through `hashlib`. They do not verify a public-key signature.

Searched project source and dependency manifests:

- No `pyproject.toml`, `requirements` file, `setup.py`, `setup.cfg`, or `Pipfile` declares a cryptographic library.
- No Python module imports `cryptography`, `nacl`, `ecdsa`, `hmac`, or a WebAuthn, passkey, or wallet verifier.
- No `Cargo.toml` in this repository declares `ed25519`, `ed25519-dalek`, or `ecdsa`.
- Build logs under `external_verifications/grok-build/evidence/` mention compiling `ed25519-dalek` 2.2.0, `ed25519` 2.2.3, and `ecdsa` 0.16.9. Those logs are evidence artifacts. They are not a Python API and they are not a CLOSED verifier this layer may call.
- No repository policy document was found that either adopts or forbids a new crypto dependency. Absence of a prohibition is not an adoption.

The inspection interpreter, Python 3.14.3, can import `cryptography` 50.0.1, including `cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey`. `nacl`, `ecdsa`, and `webauthn` do not import. That interpreter fact is not a project pin. An ambient import would hide a supply-chain choice.

The standard library on this tree can hash and can compute HMAC. It does not provide an audited Ed25519, ECDSA, or RSA verification API that this scope can call. Implementing that arithmetic here would be custom cryptography. This document forbids that.

HMAC is rejected as the witness primitive. A MAC shows that a party with the shared secret could produce it. The verifier and the producer share that secret. That symmetry is a poor external-witness boundary.

Public-key verification remains the preferred shape for a later scope. It is not frozen here, because the library that would perform it is not a repository dependency.

## Decision

### Not frozen

Exact-Bytes Signature Verification Predicate v0 is not frozen.

A freeze would have to fix the algorithm, the public-key encoding, the signature encoding, the lengths, and the failure behavior. Those choices bind the project to a verifier. The only audited verifier observed here is an undeclared interpreter package. Binding the contract to it now would add a dependency by implication.

No envelope, domain string, or digest wrapper is defined. If a later scope signs anything, the smaller contract is the raw exact subject bytes, with no Unicode, newline, JSON, whitespace, BOM, or encoding normalization. A domain label on top of those bytes would be decorative until a separate collision or value-class problem is shown. This note is guidance for that later scope. It is not a record format.

A persistent receipt is not useful before a verifier exists. Structural consistency must not be asked to stand in for a signature check. This D1 creates neither a predicate function nor a receipt.

Caller-supplied public keys and signatures are acceptable only in that later predicate, and only as “valid under this supplied key.” They are not inputs of this D1. Algorithm choice stays out of the caller’s hands. Evidence kind, witness role, signer name, trust level, authority, independence, and provenance labels are excluded.

### The missing prerequisite

The next scope is adoption of one audited public-key verification library as an explicit project dependency, with the version, license, and the exact verify API reviewed by a human before any signature predicate is designed for freeze.

The inspection candidate is pyca/cryptography Ed25519, `Ed25519PublicKey.verify`, observed as version 50.0.1 on this interpreter. This document does not pin that version, does not vendor the library, and does not authorize `pip install`.

Until that dependency decision exists:

- no algorithm is code-owned
- no public-key encoding is frozen
- no signature encoding is frozen
- no success tag exists
- replay, freshness, and key trust are not handled, because there is no verification result to qualify

## Exact inputs

None.

## Exact record keys

None.

## Success and failure tags

Success tags:
none

Failure tags:
none

`PREREQUISITE_REQUIRED` is the design status of this document. It is not a runtime tag.

This candidate does not define `WITNESS_VERIFIED`, `SIGNATURE_VALID`, `TRUSTED_SIGNER`, `AUTHENTIC`, `PROVENANCE`, `EVIDENCE`, `LOG`, `VERIFIED`, `FRESH`, `INDEPENDENT`, or `COMPATIBLE`.

## Nonclaims

This candidate does not verify a signature, choose an algorithm, trust a key, name a signer, authorize a signer, create an evidence kind, or establish provenance, freshness, anti-replay, truth, support, relevance, admission, authority, independence, or Human Final.

A hash is not a signature. An HMAC is not a public-key witness. An ambient library import is not a project dependency. A build log is not an API. SUBP-v0 success is not a witness. A schema name is not a signer.

## Semantic self-ratification

The forbidden pattern remains a caller label, a schema name, a digest, or an unreviewed crypto call being reported as a verified witness. This candidate has no function that can return that report.

## Attack and mutation spec

Two lists are specified. They are not the same list.

Planned attack tests are behavior specifications for this refusal. Count: 12. Identifiers: `EWVD1-A01` through `EWVD1-A12`.

Planned source-code mutation operators are edits that would violate this refusal if a package or dependency were added. Count: 12. Identifiers: `EWVD1-S01` through `EWVD1-S12`.

This design batch does not implement a package, does not add a dependency, does not run the attack tests, and does not apply the source mutations. These tests are not a license to implement a verifier in order to watch them fail.

### Planned attack tests

### EWVD1-A01

Attack: import `cryptography` from the ambient interpreter and treat a successful import as a project verifier.
Expected: no verifier is exported and no tag is returned.
Invariant: an interpreter package is not a repository dependency.
Boundary control: no dependency manifest is added.

### EWVD1-A02

Attack: add a hand-rolled Ed25519, ECDSA, or RSA check.
Expected: the check is outside this scope. No success tag exists.
Invariant: custom cryptography is forbidden.
Boundary control: SHA-256 in CLOSED digest code is not extended into signature arithmetic.

### EWVD1-A03

Attack: accept `hmac.new` over the subject and a shared key as the witness.
Expected: no MAC success tag.
Invariant: a shared secret is not the external-witness boundary.
Boundary control: the standard library HMAC API is not wrapped.

### EWVD1-A04

Attack: pass `algorithm=ed25519` or `algorithm=hmac-sha256`.
Expected: no parameter accepts the algorithm.
Invariant: the caller does not select an algorithm, because this scope selects none.
Boundary control: the string is not hashed and not stored.

### EWVD1-A05

Attack: pass `signer=alice`, `kind=LOG`, or `trust=high` with a subject.
Expected: no record retains the metadata.
Invariant: declared identity and trust do not control a check that does not exist.
Boundary control: the words are not verification inputs.

### EWVD1-A06

Attack: supply a 32-byte public key and a 64-byte signature beside subject byte `0x61`.
Expected: this scope does not verify them and does not return a validity tag.
Invariant: key and signature bytes are not checked before a reviewed dependency exists.
Boundary control: lengths that look like Ed25519 do not select Ed25519.

### EWVD1-A07

Attack: present SHA-256 of the subject, or a digest of a normalized copy, as the signature result.
Expected: the digest is not a signature verdict.
Invariant: hashing is not verification.
Boundary control: DSDS-v0 and SUBP-v0 digests stay inside those CLOSED scopes.

### EWVD1-A08

Attack: take SUBP-v0 success or a closed schema parse and ask for a witness.
Expected: no witness label is added. SUBP-v0 and the receipt parsers are not reinterpreted.
Invariant: grammar and schema match are not signatures.
Boundary control: this scope does not call those parsers to mint a signer.

### EWVD1-A09

Attack: ask for `WITNESS_VERIFIED`, `SIGNATURE_VALID`, `TRUSTED_SIGNER`, or `AUTHENTIC`.
Expected: none of those words is a success tag.
Invariant: a missing verifier is not a positive conclusion.
Boundary control: `PREREQUISITE_REQUIRED` is not a runtime tag.

### EWVD1-A10

Attack: ask for a structural record that stores the key and signature without a cryptographic check.
Expected: no record and no structural tag.
Invariant: structural consistency must not imply verification.
Boundary control: no field list is defined.

### EWVD1-A11

Attack: add `cryptography` to a new or existing dependency manifest inside this scope.
Expected: this document’s commit does not do that. A later dependency adoption is a separate human decision.
Invariant: D1 does not smuggle the library in.
Boundary control: version 50.0.1 is an inspection observation, not a pin.

### EWVD1-A12

Attack: report that a repeated subject, key, and signature tuple is fresh, independent, or authorized.
Expected: no such report exists.
Invariant: anti-replay, freshness, identity, and authorization are later prerequisites.
Boundary control: even a future identical tuple that verifies would still not be those facts. This scope does not verify the tuple.

Planned attack-test count:
12

### Planned source-code mutation operators

These operators would violate this refusal. They are not the 12 attack tests. This batch does not apply them.

### EWVD1-S01

Operator: import ambient `cryptography` and return success when the import works.
Killing test: `EWVD1-A01`.

### EWVD1-S02

Operator: implement signature arithmetic in this repository.
Killing test: `EWVD1-A02`.

### EWVD1-S03

Operator: verify with `hmac.new` and a shared key.
Killing test: `EWVD1-A03`.

### EWVD1-S04

Operator: add a caller `algorithm` parameter and branch on it.
Killing test: `EWVD1-A04`.

### EWVD1-S05

Operator: store `signer`, `kind`, or `trust` and treat it as part of the check.
Killing test: `EWVD1-A05`.

### EWVD1-S06

Operator: accept 32-byte and 64-byte inputs as an Ed25519 success without calling a reviewed verifier.
Killing test: `EWVD1-A06`.

### EWVD1-S07

Operator: compare a stored SHA-256 digest and call that comparison a signature check.
Killing test: `EWVD1-A07`.

### EWVD1-S08

Operator: map SUBP success or a schema parse onto a witness tag.
Killing test: `EWVD1-A08`.

### EWVD1-S09

Operator: return `TRUSTED_SIGNER` or `WITNESS_VERIFIED`.
Killing test: `EWVD1-A09`.

### EWVD1-S10

Operator: emit a structural record of key and signature without a cryptographic verification step.
Killing test: `EWVD1-A10`.

### EWVD1-S11

Operator: add a dependency pin for `cryptography` inside this D1 scope.
Killing test: `EWVD1-A11`.

### EWVD1-S12

Operator: treat a repeated tuple as fresh, independent, or authorized.
Killing test: `EWVD1-A12`.

Planned source-mutation count:
12

## Change rule

Adopting a verification library, freezing Ed25519 or another algorithm, and any signature predicate are later scopes. They must not be folded into this refusal or into SUBP-v0.

## Push status

NO. This candidate authorizes no public or private push.
