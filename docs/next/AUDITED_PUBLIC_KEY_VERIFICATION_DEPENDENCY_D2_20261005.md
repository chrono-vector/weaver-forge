# Audited Public-Key Verification Dependency — D2

Date:
2026-10-05

Design status:
CANDIDATE / AWAITING HUMAN DESIGN FREEZE

DESIGN_STATUS:
READY_FOR_HUMAN_DESIGN_FREEZE

This document is a Human Design Freeze candidate. It is not a Human Design Freeze. It does not authorize implementation. It does not install a dependency. It does not modify a manifest, a lock file, or production code. It defines no record, no schema, and no digest.

Repository:
C:\dev\Weaver\weaver-forge-r4

Base HEAD:
28f2876ec597456d629ae58248f9c43ce37e4f1c

D1:
docs/next/EXACT_BYTES_WITNESS_VERIFICATION_D1_20261005.md

D0:
docs/next/EXACT_BYTES_WITNESS_VERIFICATION_PREREQUISITE_D0_20261005.md

D0 and D1 remain in force. Claim–Evidence Compatibility is not ready. SUBP-v0 is not sufficient. This D2 does not reopen those decisions.

Recommended next scope:
Human Design Freeze of this Audited Public-Key Verification Dependency candidate

## Machine question

Which one audited public-key verification dependency, and which one fixed algorithm profile, can a later exact-bytes witness predicate call?

The candidate answer is the PyPI package `cryptography` at exact version 50.0.2, using pure Ed25519 as specified in RFC 8032. The public key is 32 raw octets. The signature is 64 raw octets. The message is the supplied bytes, unchanged.

## Selection

Ed25519 is the profile. The repository and the inspection platform provide no concrete constraint against it.

The inspection interpreter is CPython 3.14.3, 64-bit Windows, MSC v.1944, `sys.abiflags` empty, and `sys._is_gil_enabled()` true. PyPI release 50.0.2 declares Python 3.14, publishes `cryptography-50.0.2-cp311-abi3-win_amd64.whl` for this ABI, and is not yanked. Tag `50.0.2` of `https://github.com/pyca/cryptography` exposes `Ed25519PublicKey.from_public_bytes` and `Ed25519PublicKey.verify`.

One verification dependency is selected. Transitive installation pins belong to that dependency. They are not alternate verifiers.

Refused for this candidate:

- The ambient interpreter package `cryptography` 50.0.1. It imports on this machine. It is not a project pin.
- HMAC and every shared-secret MAC. D1 refused them.
- Custom Ed25519, ECDSA, or RSA arithmetic.
- Ed25519ph and Ed25519ctx. RFC 8032 section 5.1 prehashes Ed25519ph with SHA-512 and gives Ed25519ctx a context. This profile has neither.
- ECDSA and RSA. A second algorithm would be agility.
- PyNaCl, the `ecdsa` package, and any WebAuthn or wallet verifier. They are not the selected dependency.
- Build logs that mention `ed25519-dalek`. Those logs are evidence artifacts. They are not this Python API.
- A caller-selected algorithm, domain, or hash.

## Pinned verify path

The future wrapper calls only this path, and only after its own type and length checks:

`cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PublicKey.from_public_bytes`

then `Ed25519PublicKey.verify(signature, data)`.

Tag 50.0.2, file `src/cryptography/hazmat/primitives/asymmetric/ed25519.py`, delegates those calls to `cryptography.hazmat.bindings._rust.openssl`. Tag 50.0.2, file `src/rust/src/backend/ed25519.rs`, loads the public key with `PKey::public_key_from_raw_bytes` and `Id::ED25519`. Verification uses `Verifier::new_without_digest` and `verify_oneshot` on the raw signature bytes and the raw data bytes. The Rust function has no prehash argument and no context argument. Failure becomes `cryptography.exceptions.InvalidSignature`. A public key that is not 32 bytes raises `ValueError` with the text "An Ed25519 public key is 32 bytes long".

The same tag's `verify` takes a bytes-like buffer. The wrapper therefore enforces exact builtin `bytes` before the library sees the arguments. Library acceptance of a `bytearray` or a `memoryview` is not the Weaver contract.

The published docs page `https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/` was read on 2026-10-05. It describes the same shape: a 32-byte raw public key, a 64-byte signature from `sign`, `verify(signature, data)`, and `InvalidSignature` on failure. The pin's behavior is the tag 50.0.2 source above. "Latest" docs can move after this date.

The wrapper does not call `sign`, `generate`, `generate_key`, or `from_private_bytes`.

## Supply-chain pin

Observed on 2026-10-05 from `https://pypi.org/pypi/cryptography/50.0.2/json`, `https://pypi.org/pypi/cffi/2.1.1/json`, and `https://pypi.org/pypi/pycparser/3.0/json`.

| Package | Exact pin | Role |
| --- | --- | --- |
| cryptography | 50.0.2 | selected verifier |
| cffi | 2.1.1 | direct CPython requirement of cryptography 50.0.2 (`cffi>=2.0.0`) |
| pycparser | 3.0 | direct CPython requirement of cffi 2.1.1 |

`cryptography` 50.0.2 facts from that PyPI document:

- `version` is `50.0.2`, `yanked` is false, upload date of the files below is 2026-09-30.
- `license_expression` is `Apache-2.0 OR BSD-3-Clause`. License files are `LICENSE`, `LICENSE.APACHE`, and `LICENSE.BSD`.
- `requires_python` is `!=3.9.0,!=3.9.1,>=3.9`.
- Classifiers include `Development Status :: 5 - Production/Stable` and `Programming Language :: Python :: 3.14`.
- `requires_dist` is `cffi>=2.0.0` on CPython, `typing-extensions>=4.13.2` only when `python_full_version < 3.11`, and `bcrypt>=3.1.5` only for the `ssh` extra.
- Project source is `https://github.com/pyca/cryptography`. The PyPI ownership organization is `pyca`.
- The top-level `vulnerabilities` array is empty.
- `has_sig` is false on the release files. The reproducibility control is SHA-256.

`cffi` 2.1.1 is not yanked. Its `license_expression` is `MIT-0`. It requires Python `>=3.10` and, on CPython, `pycparser`. Its PyPI `vulnerabilities` array is empty. Source is `https://github.com/python-cffi/cffi`.

`pycparser` 3.0 is not yanked. Its `license_expression` is `BSD-3-Clause`. It requires Python `>=3.10` and declares no `requires_dist`. Its PyPI `vulnerabilities` array is empty.

The `ssh` extra is out of the pin, so `bcrypt` is not a requirement. On the inspection interpreter, Python 3.14, `typing-extensions` is not a requirement.

`cffi==2.1.1` and `pycparser==3.0` require Python `>=3.10`. No repository manifest requires Python 3.9. The inspected runtime is 3.14.3.

Native component:
yes. `ed25519.py` imports the Rust OpenSSL binding, and the Windows artifact is a binary wheel. OpenSSL is inside that wheel. It is not a separate pip package.

Hash locking:
feasible. A future requirements file can name exact versions and SHA-256 values with pip `--require-hashes`. This commit does not add that file.

Inspection-platform artifacts and the matching sdists, copied from the PyPI release records above:

- `cryptography-50.0.2-cp311-abi3-win_amd64.whl`, size 3824692, sha256 `7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c`
- `cryptography-50.0.2.tar.gz`, size 880623, sha256 `7b46165bb56eb4704e2eaaf86f3c940d19154535d9b0ca7d6d590b04060e00d5`
- `cffi-2.1.1-cp314-cp314-win_amd64.whl`, size 187949, sha256 `3222ba5d678f80a030e6afbcc33dc1ae5cb45facabb61cee2c7016b8432fde48`
- `cffi-2.1.1.tar.gz`, size 530807, sha256 `dd31f52ea1086513bb9df30f8fcee9b8918323ae067a3d5b78bc826a000712be`
- `pycparser-3.0-py3-none-any.whl`, size 48172, sha256 `b727414169a36b7d524c1c3e31839a521725078d7b2ff038656844266160a992`
- `pycparser-3.0.tar.gz`, size 103492, sha256 `600f49d217304a5902ac3c37e1281c9fe94e4d0489de643a9504c5cdfdfc6b29`

The cffi wheel is the GIL wheel `cp314-cp314`, matching the inspection interpreter. The free-threaded `cp314t` wheel is a different artifact and is not the pin for this interpreter. The cryptography wheel is the stable-ABI `cp311-abi3` Windows amd64 wheel, which PyPI publishes for this release's CPython range, including 3.14.

A later lock that adds another platform must copy more SHA-256 values from these same release records. It must not admit another version of `cryptography`, `cffi`, or `pycparser`.

Offline install expectation:
pip installs from a hash-checking requirements file that contains all three packages, with no version float and no network resolution beyond the already pinned artifacts. The `ssh` extra is absent.

License:
The repository `LICENSE` is Apache-2.0. `LICENSE_SCOPE.md` states that Public Core is Apache-2.0, and item 9 excludes content that carries another license from that grant. This candidate elects the Apache-2.0 option of `cryptography`'s `Apache-2.0 OR BSD-3-Clause` expression. `cffi` is MIT-0. `pycparser` is BSD-3-Clause. The packages stay external. They are not vendored, and their text is not absorbed into the Public Core grant.

Vulnerability status on 2026-10-05, point in time:

- PyPI `vulnerabilities` is an empty array for `cryptography` 50.0.2, `cffi` 2.1.1, and `pycparser` 3.0.
- `POST https://api.osv.dev/v1/query` with ecosystem `PyPI` returned an empty object for `cryptography` 50.0.2, `cffi` 2.1.1, and `pycparser` 3.0. The same endpoint returned `GHSA-3ww4-gg4f-jr7f` for `cryptography` 41.0.0, so the empty object is a live negative result.
- `GET https://api.github.com/advisories?ecosystem=pip&affects=cryptography&per_page=100` returned 24 advisories. The only vulnerable-range string containing `50` is `GHSA-g6cj-pr64-35w5` / `CVE-2026-69247`, range `>= 44.0.0, < 50.0.0`. That range ends before 50.0.2.

This is the advisory status on that date. It is not a continuous monitor.

Rollback:
a later implementation removes the wrapper module and the lock file. No CLOSED module imports `cryptography`. This commit adds neither the module nor the lock file.

## Wrapper

Candidate module, not created in this commit:
`exact_bytes_witness_v0`

Public function:

`verify_exact_bytes_witness(public_key: bytes, signature: bytes, message: bytes) -> str`

The function imports `cryptography` inside the call. A missing module at import of `exact_bytes_witness_v0` is not a successful verification, and it is not an import-time crash of unrelated CLOSED packages.

Order of checks:

1. The signature accepts exactly three parameters. An extra positional argument or an extra keyword, including `algorithm`, `signer`, `kind`, `domain`, or `hash`, raises `TypeError`.
2. `type(public_key) is bytes`, `type(signature) is bytes`, and `type(message) is bytes`. A subclass, `bytearray`, `memoryview`, `str`, `int`, `bool`, or `None` fails the check. Failure raises `ExactBytesWitnessError`.
3. `len(public_key) == 32` and `len(signature) == 64`. Any other length raises `ExactBytesWitnessError`. The message length may be zero.
4. Import failure, `from_public_bytes` failure, `verify` failure, and any other exception from the library raise `ExactBytesWitnessError`. `cryptography.exceptions.InvalidSignature` does not propagate.
5. The library call returns `None` on success. The wrapper then returns the success string. Any other return value raises `ExactBytesWitnessError`.

The message argument is the `data` argument of `verify`. The wrapper does not decode text, normalize newlines, normalize Unicode, strip bytes, truncate, prepend a domain, or hash the message.

Error class:
`ExactBytesWitnessError`

Its public `code` is the string `EXACT_BYTES_WITNESS_REJECTED`. Callers compare that string. The success value is a string, so a bool cannot be confused with an integer status.

## Success and failure tags

Success tag:
`EXACT_BYTES_WITNESS_VALID`

Failure tag:
`EXACT_BYTES_WITNESS_REJECTED`

`TypeError` is the Python response to a call that does not match the frozen signature. It is not a second verdict tag.

This candidate does not define `WITNESS_VERIFIED`, `SIGNATURE_VALID`, `TRUSTED_SIGNER`, `AUTHENTIC`, `PROVENANCE`, `EVIDENCE`, `LOG`, `VERIFIED`, `FRESH`, `INDEPENDENT`, or `COMPATIBLE`.

## Signed object and encodings

Signed object:
`RAW_EXACT_BYTES`

Public-key encoding:
32 raw octets, the RFC 8032 Ed25519 public key. PEM, DER, SubjectPublicKeyInfo, and OpenSSH encodings are outside this function.

Signature encoding:
64 raw octets, R concatenated with S, as RFC 8032 section 7 describes for Ed25519. DER is outside this function.

Algorithm selectable by the caller:
no

The empty message is in scope because RFC 8032 section 7.1 TEST 1 uses a message of length 0.

## Known-answer vectors

Source:
RFC 8032, `https://www.rfc-editor.org/rfc/rfc8032.txt`, section 7.1, retrieved 2026-10-05. The vectors below are TEST 1 and TEST 2 of pure Ed25519. Section 7.3 Ed25519ph vectors are not inputs.

The RFC also prints a secret key for each test. The secret key is not an input, not a test fixture for this wrapper, and not a license to call a signing API.

Whitespace in the RFC is readability only. The octet strings below are the hex of those fields with that whitespace removed.

TEST 1. Message length 0. Public key and signature:

```
d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a
e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b
```

TEST 2. Message is the single octet hex `72`. Public key and signature:

```
3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c
92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00
```

These vectors are specified. They were not executed against the pin. The ambient 50.0.1 install is not a run of this pin.

## What a valid result proves

`EXACT_BYTES_WITNESS_VALID` means the pinned verifier accepted this 64-byte signature as a pure Ed25519 signature over these exact message bytes under this exact 32-byte public key.

A valid result does not establish a trusted key, signer identity, signer authorization, signer independence, creator, strong provenance, freshness, timestamp, anti-replay, evidence, evidence kind, truth, support, relevance, sufficiency, completeness, admission, authority, real-world correspondence, or Human Final.

The same three byte strings may verify again on a later call. Anti-replay is not provided.

No CLOSED surface binds a public key to an identity. Independent-evidence admission remains `NOT_CONFIGURED`. This candidate does not change that.

## Next unresolved prerequisite

Public-key trust, witness identity, and authorization remain unresolved. A later boundary has to say which supplied public keys, if any, may be treated as accepted witnesses. This candidate names no accepted key.

## Semantic self-ratification

A caller algorithm string, signer string, kind string, schema name, SUBP success token, or ambient import of `cryptography` 50.0.1 is not `EXACT_BYTES_WITNESS_VALID`.

## Attack test plan

These are planned tests. They were not run. They are not source mutations.

The expected rejection is `ExactBytesWitnessError` with `code == "EXACT_BYTES_WITNESS_REJECTED"` unless a row says `TypeError`. The expected success is the exact string `EXACT_BYTES_WITNESS_VALID`, and its type is `str`.

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

Planned attack test count:
36

A27 records that replay of an identical tuple still verifies. A24 uses two different raw messages so a composed UTF-8 sequence and a decomposed UTF-8 sequence are each refused against the TEST 2 signature. No signature was invented for those messages. A20 through A26 are the normalization, newline, and leading or trailing byte cases, and they likewise invent no signature.

## Source mutation plan

These are planned production mutations. They were not applied. Each row names the tests that kill that mutant. A mutant that still returns the success token, or that fails to raise the expected exception, on a killing test is killed.

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

Planned source mutation count:
14

S03 is killed because one constant stand-in message cannot satisfy both the empty TEST 1 message and the one-byte TEST 2 message. S12 and S14 are killed because those two RFC 8032 pure-Ed25519 vectors fail under Ed25519ph and under a local SHA-512 prehash. S04 is killed because stripping a trailing newline, deleting a leading CR, keeping only a one-byte prefix, or keeping only a one-byte suffix turns at least one of A20, A22, A25, and A26 into the TEST 2 message.

## Closed scopes

This candidate does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, or SUBP-v0. It does not alter VECTOR, EIG, Canonical, Published, or Deployed state.

## Human Design Freeze

HUMAN_DESIGN_FREEZE:
NOT_PERFORMED

Implementation remains unauthorized after this commit. Installing `cryptography`, `cffi`, or `pycparser` remains unauthorized. A later Human Design Freeze is a separate documentation save.
