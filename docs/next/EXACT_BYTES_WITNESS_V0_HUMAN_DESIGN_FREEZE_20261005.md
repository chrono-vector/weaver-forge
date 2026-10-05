# Exact-Bytes Witness v0 — Human Design Freeze

Date:
2026-10-05

HUMAN_DESIGN_FREEZE:
ACCEPTED

Design freeze:
HUMAN_DESIGN_FREEZE_ACCEPTED

This document records a Human Design Freeze decision explicitly made by the human authority. It does not record an AI acceptance decision. It is not implementation acceptance and it is not a Human Final for an implementation.

Scope:
Exact-Bytes Witness v0

Frozen scope name:
Ed25519 exact-bytes witness v0

Frozen design source:
docs/next/AUDITED_PUBLIC_KEY_VERIFICATION_DEPENDENCY_D2_20261005.md

Frozen design source commit:
0bb0303f4d026f2b83c4d19fe198fe4280c14aaf

D1:
docs/next/EXACT_BYTES_WITNESS_VERIFICATION_D1_20261005.md

D0:
docs/next/EXACT_BYTES_WITNESS_VERIFICATION_PREREQUISITE_D0_20261005.md

The semantic design remains the D2 source, unchanged by this record. D0 and D1 remain in force. Claim–Evidence Compatibility is not ready. SUBP-v0 is not sufficient. Accepting this freeze does not reopen those decisions.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD before this record:
0bb0303f4d026f2b83c4d19fe198fe4280c14aaf

Implementation:
AUTHORIZED after this freeze, for the frozen contract only.

Push:
FORBIDDEN

## Machine question

Does this exact 32-byte public key, exact 64-byte signature, and exact message form a valid pure Ed25519 tuple under the frozen profile?

D2 asked which one audited public-key verification dependency and which one fixed algorithm profile a later predicate can call. This acceptance answers that question with the profile below. The wrapper's only machine question is the tuple question above.

## Frozen profile

CRYPTO_ALGORITHM:
Ed25519 (RFC 8032 pure)

SIGNED_OBJECT:
RAW_EXACT_BYTES

Public-key encoding:
32 raw octets. PEM, DER, SubjectPublicKeyInfo, and OpenSSH encodings are outside the function.

Signature encoding:
64 raw octets, R concatenated with S. DER is outside the function.

Message:
the supplied bytes, unchanged. Length zero is in scope.

Caller algorithm selector:
NO

Caller domain selector:
NO

Caller hash selector:
NO

Ed25519ph:
NO

Ed25519ctx:
NO

Custom cryptography:
FORBIDDEN

Selected verifier:
PyPI package `cryptography` at exact version 50.0.2

Transitive pins, not alternate verifiers:

| Package | Exact pin | Role |
| --- | --- | --- |
| cryptography | 50.0.2 | selected verifier |
| cffi | 2.1.1 | direct CPython requirement of cryptography 50.0.2 |
| pycparser | 3.0 | direct CPython requirement of cffi 2.1.1 |

Verify path, after the wrapper's own type and length checks:

`cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey.from_public_bytes`

then `Ed25519PublicKey.verify(signature, data)`.

The message argument is the `data` argument. The wrapper does not decode text, normalize newlines, normalize Unicode, strip bytes, truncate, prepend a domain, or hash the message.

The wrapper does not call `sign`, `generate`, `generate_key`, or `from_private_bytes`. There is no Weaver public signing API and no Weaver public key-generation API.

An import of `cryptography`, `cffi`, or `pycparser` whose installed distribution version is not the exact pin above is a failure. It is not `EXACT_BYTES_WITNESS_VALID`. The ambient interpreter package `cryptography` 50.0.1 is not this pin.

## Dependency mechanism

This tree has no `pyproject.toml`, requirements file, `setup.py`, `setup.cfg`, or `Pipfile`. D2 named one future hash-locked requirements file as the pin mechanism. This freeze authorizes that one file and no second mechanism.

Implementation file:
`requirements/exact-bytes-witness-v0.txt`

The file names `cryptography==50.0.2`, `cffi==2.1.1`, and `pycparser==3.0` with the SHA-256 values below. Installation uses pip `--require-hashes`. The `ssh` extra is absent. `bcrypt` is not a requirement. On the inspection interpreter, Python 3.14, `typing-extensions` is not a requirement. No unrelated package is upgraded by this pin.

This freeze commit does not add the requirements file and does not install the packages.

## Supply chain and native code

Hashes below are the inspection-platform artifacts and the matching sdists recorded by D2 from the PyPI release documents on 2026-10-05. A lock that adds another platform must copy more SHA-256 values from those same release records. It must not admit another version of `cryptography`, `cffi`, or `pycparser`.

| Artifact | Size | SHA-256 |
| --- | --- | --- |
| cryptography-50.0.2-cp311-abi3-win_amd64.whl | 3824692 | 7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c |
| cryptography-50.0.2.tar.gz | 880623 | 7b46165bb56eb4704e2eaaf86f3c940d19154535d9b0ca7d6d590b04060e00d5 |
| cffi-2.1.1-cp314-cp314-win_amd64.whl | 187949 | 3222ba5d678f80a030e6afbcc33dc1ae5cb45facabb61cee2c7016b8432fde48 |
| cffi-2.1.1.tar.gz | 530807 | dd31f52ea1086513bb9df30f8fcee9b8918323ae067a3d5b78bc826a000712be |
| pycparser-3.0-py3-none-any.whl | 48172 | b727414169a36b7d524c1c3e31839a521725078d7b2ff038656844266160a992 |
| pycparser-3.0.tar.gz | 103492 | 600f49d217304a5902ac3c37e1281c9fe94e4d0489de643a9504c5cdfdfc6b29 |

The cffi wheel is the GIL wheel `cp314-cp314`. The free-threaded `cp314t` wheel is not the pin. The cryptography wheel is the stable-ABI `cp311-abi3` Windows amd64 wheel.

Native component:
yes. The selected path loads the Rust OpenSSL binding inside the binary wheel. OpenSSL is inside that wheel. It is not a separate pip package. The packages stay external. They are not vendored, and their license text is not absorbed into the Public Core grant.

License election:
`cryptography` is `Apache-2.0 OR BSD-3-Clause`. This freeze elects Apache-2.0. `cffi` is MIT-0. `pycparser` is BSD-3-Clause.

Point-in-time advisory status remains the D2 record of 2026-10-05. This freeze does not add a continuous monitor.

Rollback:
remove the wrapper package and `requirements/exact-bytes-witness-v0.txt`. No CLOSED module imports `cryptography`.

## Wrapper

Module:
`exact_bytes_witness_v0`

Public function:
`verify_exact_bytes_witness(public_key: bytes, signature: bytes, message: bytes) -> str`

Error class:
`ExactBytesWitnessError`

The function imports `cryptography` inside the call. Importing `exact_bytes_witness_v0` does not import `cryptography`. A missing verifier at import of the wrapper is not a successful verification, and it is not an import-time crash of unrelated CLOSED packages.

Order of checks:

1. The signature accepts exactly three parameters. An extra positional argument or an extra keyword, including `algorithm`, `signer`, `kind`, `domain`, or `hash`, raises `TypeError`.
2. `type(public_key) is bytes`, `type(signature) is bytes`, and `type(message) is bytes`. A subclass, `bytearray`, `memoryview`, `str`, `int`, `bool`, or `None` fails the check. Failure raises `ExactBytesWitnessError`.
3. `len(public_key) == 32` and `len(signature) == 64`. Any other length raises `ExactBytesWitnessError`. The message length may be zero.
4. A distribution version other than the frozen pins, an import failure, `from_public_bytes` failure, `verify` failure, and any other exception from the library raise `ExactBytesWitnessError`. `cryptography.exceptions.InvalidSignature` does not propagate.
5. The library call returns `None` on success. The wrapper then returns the success string. Any other return value raises `ExactBytesWitnessError`.

## Success and failure tags

Success tag:
`EXACT_BYTES_WITNESS_VALID`

Failure tag:
`EXACT_BYTES_WITNESS_REJECTED`

The success value is a `str`. `TypeError` is the Python response to a call that does not match the frozen signature. It is not a second verdict tag.

The public `code` of `ExactBytesWitnessError` is `EXACT_BYTES_WITNESS_REJECTED`.

This freeze does not define `WITNESS_VERIFIED`, `SIGNATURE_VALID`, `TRUSTED_SIGNER`, `AUTHENTIC`, `PROVENANCE`, `EVIDENCE`, `LOG`, `VERIFIED`, `FRESH`, `INDEPENDENT`, or `COMPATIBLE`.

## Known-answer vectors

Source remains RFC 8032 section 7.1 TEST 1 and TEST 2, as copied into D2. Section 7.3 Ed25519ph vectors are not inputs. The RFC secret keys are not inputs and are not a license to call a signing API.

TEST 1. Message length 0.

Public key:
`d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a`

Signature:
`e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b`

TEST 2. Message is the single octet hex `72`.

Public key:
`3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c`

Signature:
`92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00`

## Semantic nonclaims

`EXACT_BYTES_WITNESS_VALID` means the pinned verifier accepted this 64-byte signature as a pure Ed25519 signature over these exact message bytes under this exact 32-byte public key.

Trusted signer or trusted key:
NO

Signer identity:
NO

Signer authorization:
NO

Signer independence:
NO

Creator:
NO

Strong provenance:
NO

Timestamp:
NO

Freshness:
NO

Anti-replay:
NO

Evidence:
NO

Evidence kind:
NO

Truth:
NO

Support:
NO

Relevance:
NO

Sufficiency:
NO

Completeness:
NO

Admission:
NO

Authority:
NO

Real-world correspondence:
NO

Human Final:
NO

The same three byte strings may verify again on a later call. That replay is not anti-replay. No CLOSED surface binds a public key to an identity. Independent-evidence admission remains `NOT_CONFIGURED`.

A caller algorithm string, signer string, kind string, schema name, SUBP success token, or ambient import of `cryptography` 50.0.1 is not `EXACT_BYTES_WITNESS_VALID`.

## Planned attack tests

These tests are part of the frozen contract. They are not source mutations. The expected rejection is `ExactBytesWitnessError` with `code == "EXACT_BYTES_WITNESS_REJECTED"` unless a row says `TypeError`. The expected success is the exact string `EXACT_BYTES_WITNESS_VALID`, and its type is `str`.

| Id | Case | Expected |
| --- | --- | --- |
| APKD2-A01 | RFC 8032 section 7.1 TEST 1 | success token |
| APKD2-A02 | RFC 8032 section 7.1 TEST 2 | success token |
| APKD2-A03 | TEST 2 message byte changed from `0x72` to `0x73` | rejected |
| APKD2-A04 | TEST 2 message and signature with the TEST 1 public key | rejected |
| APKD2-A05 | TEST 2 public key with one byte flipped | rejected |
| APKD2-A06 | TEST 2 signature with first byte changed from `0x92` to `0x93` | rejected |
| APKD2-A07 | TEST 2 public key and signature with the empty message | rejected |
| APKD2-A08 | public key length 31 | rejected |
| APKD2-A09 | public key length 33 | rejected |
| APKD2-A10 | signature length 63 | rejected |
| APKD2-A11 | signature length 65 | rejected |
| APKD2-A12 | public key whose type is a `bytes` subclass | rejected |
| APKD2-A13 | signature whose type is a `bytes` subclass | rejected |
| APKD2-A14 | message whose type is a `bytes` subclass | rejected |
| APKD2-A15 | message is a `bytearray` | rejected |
| APKD2-A16 | message is a `memoryview` | rejected |
| APKD2-A17 | message is a `str` | rejected |
| APKD2-A18 | public key is a `str` | rejected |
| APKD2-A19 | signature is a `str` | rejected |
| APKD2-A20 | TEST 2 message plus a trailing `0x0A` | rejected |
| APKD2-A21 | a leading `0x0A` before the TEST 2 message | rejected |
| APKD2-A22 | a leading `0x0D` before the TEST 2 message | rejected |
| APKD2-A23 | `b"\n"` and `b"\r\n"` under the TEST 2 key and signature, each | rejected |
| APKD2-A24 | octets `c3 a9` and octets `65 cc 81` under the TEST 2 key and signature, each | rejected |
| APKD2-A25 | TEST 2 message plus a trailing `0x00` | rejected |
| APKD2-A26 | a leading `0x00` before the TEST 2 message | rejected |
| APKD2-A27 | TEST 1 invoked twice in sequence | success token both times |
| APKD2-A28 | keyword `algorithm` added to a TEST 2 call | `TypeError` |
| APKD2-A29 | keyword `signer` added to a TEST 2 call | `TypeError` |
| APKD2-A30 | keyword `kind` added to a TEST 2 call | `TypeError` |
| APKD2-A31 | 32 zero public-key bytes, 64 zero signature bytes, TEST 2 message | rejected |
| APKD2-A32 | 32 `0xFF` public-key bytes with the TEST 2 signature and message | rejected |
| APKD2-A33 | A06's exception type is `ExactBytesWitnessError`, not `InvalidSignature` | rejected |
| APKD2-A34 | `cryptography` cannot be imported | rejected |
| APKD2-A35 | public surface omits `sign`, `generate`, `generate_key`, `from_private_bytes`, and `Ed25519PrivateKey` | surface holds |
| APKD2-A36 | `int`, `bool`, and `None` in any of the three positions | rejected |

Planned attack tests:
36

## Planned actual source mutations

These mutations are applied to actual production source in isolated temporary copies. They are not attack tests. A mutant that still returns the success token, or that fails to raise the expected exception, on a killing test is killed. A mutant that preserves the frozen verdicts is equivalent. A non-equivalent mutant that the tests do not kill remains material.

| Id | Mutation | Killing tests |
| --- | --- | --- |
| APKD2-S01 | skip the library verify and return the success token | A03, A06, A31 |
| APKD2-S02 | invert the result | A01, A03 |
| APKD2-S03 | verify a message other than the supplied message | A01, A02 |
| APKD2-S04 | normalize or truncate the message before verify | A20, A22, A25, A26 |
| APKD2-S05 | ignore the supplied public key | A04, A05 |
| APKD2-S06 | ignore the supplied signature | A06 |
| APKD2-S07 | accept a `bytes` subclass or a `bytearray` | A12, A15 |
| APKD2-S08 | accept a public key whose length is not 32 | A08, A09 |
| APKD2-S09 | accept a signature whose length is not 64 | A10, A11 |
| APKD2-S10 | treat a library exception as success | A03, A33 |
| APKD2-S11 | accept a caller algorithm argument | A28 |
| APKD2-S12 | verify with another primitive or profile | A01, A02 |
| APKD2-S13 | publish signing or key generation | A35 |
| APKD2-S14 | prehash the message before verify | A01, A02 |

Planned actual source-code mutations:
14

S03 is killed because one constant stand-in message cannot satisfy both the empty TEST 1 message and the one-byte TEST 2 message. S12 and S14 are killed because those two RFC 8032 pure-Ed25519 vectors fail under another primitive and under a local SHA-512 prehash. S04 is killed because stripping a trailing newline, deleting a leading CR, keeping only a one-byte prefix, or keeping only a one-byte suffix turns at least one of A20, A22, A25, and A26 into the TEST 2 message.

## Next unresolved prerequisite

Public-key trust, signer identity, and authorization.

D2's paragraph of the same boundary remains unchanged and says public-key trust, witness identity, and authorization remain unresolved. This freeze does not resolve that boundary and names no accepted key.

## Closed scopes

This freeze does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, or SUBP-v0. It does not alter VECTOR, EIG, Canonical, Published, or Deployed state.
