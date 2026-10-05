# Dedicated Local Software Ed25519 Generation and Custody Profile v0 - D1

Date:
2026-10-05

Design status:
READY_FOR_HUMAN_DESIGN_FREEZE

This document is a design-freeze candidate only. Human Design Freeze is not performed. It does not generate or select a real key, create private or recovery material, implement a helper, change a dependency, perform Admission PREPARE or CONFIRM, authorize signing, or add identity, role, authorization, trust, provenance, truth, evidence, currentness, revocation, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Base HEAD:
`345a98bf091420725f00ab1ee6da8ea2899aabd7`

D0:
`docs/next/REAL_ED25519_KEY_SOURCING_AND_CUSTODY_PREREQUISITE_V0_D0_20261005.md`

D0 commit:
`345a98bf091420725f00ab1ee6da8ea2899aabd7`

Frozen Admission Act Template and Binding Handoff v0 remains unchanged.

## Recommended profile

`Dedicated Local Software Ed25519 Generation and Custody Profile v0`

The profile uses one small, later-reviewed local Python helper on 64-bit Windows under a dedicated Human-controlled Windows account. The helper uses the already hash-locked Python dependency set and no second cryptographic implementation:

- CPython 3.14.3, 64-bit Windows, GIL build
- `cryptography==50.0.2`
- `cffi==2.1.1`
- `pycparser==3.0`
- the exact Windows wheel hashes already recorded by the CLOSED Exact-Bytes Witness dependency profile

The helper must reject any runtime, ABI, package version, or package source outside the selected profile before touching key material. The ambient `cryptography` 50.0.1 observed during design is not acceptable. OpenSSH, OpenSSL command-line tools, GPG, PyNaCl, custom Ed25519, and fallback implementations are not part of this profile.

Selection of the same package set does not modify or broaden Exact-Bytes Witness v0. This profile separately selects additional secret-bearing APIs for a future helper. It does not reinterpret the verifier's CLOSED API surface.

## Machine question

> Can one concrete, pinned, reproducible Windows-local software profile generate, encrypt at rest, unlock interactively, back up, recover, and extract one raw 32-byte Ed25519 public key without exposing private material to AI, repository content, ordinary logs, shell history, clipboard, screenshots, or Admission artifacts?

The design answer is yes within the explicit pinning and residual-risk limits below.

## Exact generator path

The only key-generation call is:

`cryptography.hazmat.primitives.asymmetric.ed25519.Ed25519PrivateKey.generate()`

The helper must not accept a seed, private bytes, deterministic test value, algorithm selector, backend selector, key count, output format selector, caller RNG, or alternate generator. Exactly one invocation produces exactly one candidate key object per authorized provisioning run.

The helper must not expose `sign`, `private_bytes_raw`, `from_private_bytes`, `NoEncryption`, or a generic cryptographic command surface. Signing is outside this profile.

`CUSTOM_CRYPTO: NO`

## Version and artifact pin

The future helper environment must use the existing hash-locked requirements file:

`requirements/exact-bytes-witness-v0.txt`

The profile permits only the recorded Windows artifacts:

- `cryptography-50.0.2-cp311-abi3-win_amd64.whl`
- `cffi-2.1.1-cp314-cp314-win_amd64.whl`
- `pycparser-3.0-py3-none-any.whl`

Installation remains outside this design and requires separate operational authorization. Source-distribution builds are not permitted for provisioning because they would introduce an unreviewed compiler and native dependency path.

Runtime preflight must check exact Python version and architecture, exact distribution versions, ordinary GIL build, and successful import from the dedicated environment. It must fail closed on the ambient 50.0.1 package, missing packages, free-threaded ABI, alternate platform, editable installs, path shadowing, or fallback imports.

`PINNED_VERSION: CPython 3.14.3 win_amd64 GIL; cryptography 50.0.2; cffi 2.1.1; pycparser 3.0`

## Private-key serialization

The only permitted private serialization call is equivalent to:

```text
private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(passphrase_bytes),
)
```

The output must begin with the encrypted PKCS#8 PEM label `-----BEGIN ENCRYPTED PRIVATE KEY-----`. An unencrypted `PRIVATE KEY`, OpenSSH private key, Raw serialization, TraditionalOpenSSL format, DER file, PKCS#12 container, custom envelope, or `NoEncryption` is rejected.

The encrypted PEM is the working private container and the only byte-for-byte backup object. The helper writes it directly from memory to a newly created protected destination. It never writes a plaintext private-key serialization, seed, raw private bytes, or intermediate unencrypted file.

### Pinning limitation

`BestAvailableEncryption` is a curated `cryptography` API whose underlying algorithm may change over time and may depend on the compiled backend. Its public contract does not freeze exact PBES, KDF, cipher, iteration, salt, IV, or ASN.1 output bytes.

This profile therefore pins:

- `cryptography` version 50.0.2;
- the reviewed Windows binary wheel;
- its bundled OpenSSL 4.0.3 observation recorded for that release;
- PEM encoding;
- PKCS#8 private format;
- use of `BestAvailableEncryption` with a non-empty passphrase;
- successful encrypted reload and exact public-key recovery.

It does not claim bit-for-bit reproducible encrypted serialization or independently frozen KDF/cipher parameters. A future dependency or wheel change requires a new profile review before key generation or migration. This limitation is preferable to inventing a home-grown KDF, cipher, ASN.1 writer, or undocumented parameter override.

`PRIVATE_KEY_SERIALIZATION: encrypted PKCS#8 PEM`

`PRIVATE_KEY_ENCRYPTION: cryptography.serialization.BestAvailableEncryption`

`KDF_CIPHER_EXACTLY_PINNED: NO`

`PINNING_LIMITATION: BestAvailableEncryption controls backend encryption details; v0 pins package, wheel, container/API, and reload behavior, not exact KDF/cipher parameters or bytes`

## Passphrase and unlock channel

The passphrase is created and retained by the Human in a separate Human-controlled password manager or sealed recovery record outside AI, repositories, source code, configuration, and ordinary logs.

For initial serialization, restore, and later local unlock, the helper obtains the passphrase only through `getpass.getpass()` in an interactive Windows console:

- standard input and standard error must be attached to an interactive console;
- terminal transcript, shell transcription, IDE capture, screen recording, and remote session recording must be disabled;
- `getpass.GetPassWarning`, echo fallback, redirected input, non-interactive input, or an exception is a hard failure;
- generation requires two separately entered values and exact equality;
- the accepted value is 24 to 128 printable ASCII characters, contains no control characters, and is encoded exactly as ASCII bytes;
- the helper makes no entropy claim merely from length; the Human must use a password-manager-generated unique value or an equivalently controlled method;
- clipboard paste, command-line arguments, environment variables, files, pipes, here-strings, shell variables, prompts to AI, and source/config literals are forbidden.

The passphrase is not stored by the helper. Python strings, encoded bytes, the private-key object, and library internals can remain in process memory until overwritten or reclaimed; CPython and `cryptography` do not give this profile a reliable whole-process zeroization guarantee. The signer host must therefore exclude untrusted same-user processes, debugging, memory capture, crash uploads, and hibernation/pagefile exposure as far as the operating environment permits. This is residual risk, not a claim of secure memory.

`UNLOCK_CHANNEL: hidden interactive Windows console via getpass.getpass; hard fail on echo fallback or non-interactive input`

`PASSPHRASE_IN_CLI: NO`

`PASSPHRASE_IN_AI_CONTEXT: NO`

`PRIVATE_KEY_IN_AI_CONTEXT: NO`

`PRIVATE_KEY_IN_REPOSITORY: NO`

## Windows-local custody directory

The working container resides in exactly one dedicated local directory for the intended Windows account:

`C:\Users\<intended-account>\AppData\Local\WeaverForge\custody-v0`

Before any secret exists, the future helper must resolve and validate the concrete absolute path. It rejects a path that:

- is inside or above a Git working tree;
- is inside OneDrive, Dropbox, Google Drive, another sync root, a redirected profile, or a roaming profile;
- is a UNC, network, removable, temporary, or relative path;
- contains a symbolic link, junction, mount point, or other reparse point;
- is caller-selected at runtime;
- already contains an unexpected file or an existing candidate key.

The helper must create one new container with create-new/no-overwrite behavior and must not follow links. The profile does not permit an alternate output path argument.

### ACL rule

Before writing the encrypted container, the directory and file must have a protected DACL with inheritance disabled. Explicit access is limited to:

- the exact intended Windows user SID: read, write, delete, and required directory traversal;
- `NT AUTHORITY\SYSTEM`: full control for operating-system operation and controlled recovery.

Broad groups such as `Users`, `Authenticated Users`, `Everyone`, and unrelated service or administrator SIDs must not have explicit or inherited access. The intended user must own the directory. The helper must inspect the effective DACL after creation and after each backup restore, and fail closed on unexpected principals or inheritance.

Windows administrators can take ownership, and a compromised process running as the intended user can read the encrypted file and intercept an unlock. ACLs do not protect against same-user compromise. Full-volume encryption is recommended as defense in depth but is not claimed or configured by this profile.

`CUSTODY_DIRECTORY_RULE: fixed resolved local non-reparse AppData\\Local custody-v0 directory outside Git, sync, network, removable, and temp roots`

`WINDOWS_ACL_RULE: protected non-inherited DACL; intended user SID plus SYSTEM only; verify owner and effective entries`

`CLOUD_SYNC_ALLOWED: NO`

`PLAINTEXT_PRIVATE_FILE_ALLOWED: NO`

## File and process behavior

The future helper must:

1. Disable its own debug and traceback output for all secret-bearing operations.
2. Return fixed public error codes without values, paths containing usernames, passphrase lengths, private serialization, or exception reprs.
3. Never print private bytes, encrypted PEM, passphrase, key object repr, or backup content to stdout or stderr.
4. Print only the canonical public-key display after both public derivations agree.
5. Avoid temporary private files. The encrypted serialization moves from memory directly to the create-new destination.
6. Flush and close the encrypted file before reload; request durable filesystem flush before reporting success.
7. Reject existing destinations rather than overwrite or rotate them.
8. Avoid shelling out to cryptographic commands.
9. Avoid generic eval, plugins, callbacks, hooks, telemetry, crash reporters, and network access.
10. Terminate after each bounded phase so a second public derivation occurs in a fresh process.

The process may hold the private object and passphrase in memory. A crash or malicious same-user process can expose memory. The helper cannot prove absence of OS-level pagefile, dump, endpoint-security, or firmware capture; provisioning must occur on a trusted, patched, non-recorded local host.

## Backup model

The minimum backup set is two byte-for-byte copies of the encrypted PKCS#8 PEM on two separately stored, Human-controlled offline removable media. The working container is not counted as a backup.

Requirements:

1. Copy only the closed encrypted PEM file; never export plaintext, Raw private bytes, or seed material.
2. Use media not mounted during routine signing and not managed by cloud sync or ordinary online backup software.
3. Store the two media in separate physical locations with controlled access.
4. Keep the passphrase record separately from both media and the signer host.
5. Re-read each copy and require exact byte equality with the closed working container.
6. In a clean local restore test, copy each encrypted backup to a newly protected temporary custody directory, verify ACLs, load it with hidden interactive passphrase entry, require an Ed25519 private-key object, derive Raw public bytes, and require equality with both independently derived public outputs.
7. Remove the restored encrypted test copy after the check without claiming guaranteed physical erasure on flash storage. Never create a plaintext restored file.
8. Record only backup location labels, completion status, date, and the canonical public-key display. Do not record secret bytes, passphrase, PEM content, or private metadata.
9. A failed copy, exact-byte comparison, reload, ACL check, or public-key comparison invalidates that backup.

The encrypted backups remain private material and stay within the custody boundary. Encryption reduces consequences of media theft but does not make the file public.

`BACKUP_MODEL: two exact encrypted-PKCS8-PEM copies on separately stored offline controlled media; passphrase held separately`

`BACKUP_RESTORE_TEST_REQUIRED: YES`

## Public-key extraction

The only permitted extraction is:

```text
loaded_private_key.public_key().public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)
```

The helper requires the result to have exact built-in `bytes` type and length exactly 32. It derives the display with the built-in byte-to-hex operation and requires an exact built-in `str` of exactly 64 lowercase ASCII hexadecimal characters.

Two derivations are mandatory:

1. After generation and encrypted serialization, close the first process.
2. In a fresh process, reload the encrypted working container through hidden interactive unlock and derive Raw public bytes.
3. In another fresh process, repeat the reload and Raw derivation.
4. Compare the two exact byte values and their independently derived lowercase hexadecimal displays.
5. Require the backup restore tests to derive the same exact public bytes.
6. Supply exactly one of those identical raw 32-byte values to the separately frozen Admission PREPARE operation.
7. Admission PREPARE performs its own strict raw/hex round trip before Human inspection.

No OpenSSH text, PEM public key, DER, certificate, fingerprint, digest, key ID, filename, backup label, or caller string can substitute for Raw public bytes. The public hexadecimal display is reversible encoding, not authority.

`PUBLIC_KEY_EXTRACTION: Ed25519PublicKey.public_bytes(Encoding.Raw, PublicFormat.Raw) after encrypted reload`

`PUBLIC_KEY_LENGTH: 32`

`DISPLAY_REPRESENTATION: 64 lowercase ASCII hex`

`INDEPENDENT_PUBLIC_COMPARISON: YES`

## RNG assurance

`Ed25519PrivateKey.generate()` takes no seed or randomness parameter. In the selected `cryptography` 50.0.2 Windows wheel it delegates generation to the bundled OpenSSL backend recorded as OpenSSL 4.0.3 by the existing dependency review.

This profile asserts only that the pinned library/backend performs generation and no application-supplied seed, deterministic source, or custom RNG is permitted. The public Python API does not expose a per-key entropy-source attestation, entropy estimate, or reproducible random transcript. This design therefore does not claim a particular Windows entropy call, quantified entropy, hardware RNG use, or proof that the host was uncompromised.

Runtime health is limited to successful exact-version preflight and successful key generation, encrypted reload, and public extraction. A backend RNG failure must fail closed. Host integrity and OS RNG assurance remain operational assumptions of the trusted local Windows boundary.

`RNG_ASSURANCE: pinned cryptography 50.0.2 bundled-OpenSSL generation with no caller seed; exact OS entropy source and entropy quantity are not attested by this profile`

## AI and signing boundary

No AI model, prompt, agent workspace, connector, chat attachment, tool output, log, telemetry stream, or model-accessible environment may receive:

- the private-key object or bytes;
- seed or recovery material;
- encrypted private PEM or backup bytes;
- passphrase, PIN, unlock token, or password-manager entry;
- memory dump or secret-bearing exception output.

This profile exposes no signing API. A later AI-triggered signing design must use a separately reviewed local signer boundary that accepts only a closed exact decision-record type, enforces code-owned policy, verifies the configured admitted public key, and returns only a signature and permitted public metadata. A generic `sign(bytes)` or arbitrary-message endpoint is forbidden unless a later scope explicitly designs and authorizes it.

`AI_FUTURE_SIGNING_BOUNDARY: separate narrow local signer interface over a frozen decision-record type; no model access to secrets`

`ARBITRARY_MESSAGE_SIGNING_AUTHORIZED: NO`

## Loss, compromise, and replacement

### Loss

Loss of one backup requires creation and verification of a replacement encrypted backup from a verified remaining controlled copy. Loss of all private copies makes the key unusable. It does not change, revoke, deactivate, or supersede historical Admission v0.

### Suspected compromise

Stop signing, isolate the signer host and all backup media, preserve only non-secret incident information, and treat every private copy as suspect. Do not continue merely because the encrypted container still reloads. This profile creates no revocation or currentness result.

### Replacement

A replacement requires a newly generated key under a separately current profile, a new additive admission snapshot, a new two-phase admission act, and separately authorized signer-reference and signing-boundary changes. The replacement must not reuse or mutate `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`.

`LOSS_HANDLING: stop use if no verified private copy remains; historical admission is unchanged`

`COMPROMISE_HANDLING: stop signing, isolate all copies, assess outside Admission v0, and replace additively`

`REPLACEMENT_MODEL: new key plus new additive snapshot and admission act; no in-place mutation or revocation claim`

## Semantic boundary

The profile creates cryptographic key material only. Generation, custody, public extraction, admission, signer-reference binding, and signing remain separate transitions.

It does not establish or add:

- human, AI, verifier, service, model, provider, organization, or device identity;
- role or authorization;
- trust or independence;
- provenance or custody truth beyond the bounded local procedure;
- claim truth, evidence kind, support, sufficiency, or Human Final;
- currentness, freshness, revocation, active status, or anti-replay.

`IDENTITY_SEMANTICS_ADDED: NO`

`ROLE_SEMANTICS_ADDED: NO`

`AUTHORIZATION_SEMANTICS_ADDED: NO`

`TRUST_SEMANTICS_ADDED: NO`

## Later bounded Human execution procedure

After Human Design Freeze and separate authorization of the reviewed helper implementation, the bounded Human run is:

1. Prepare a trusted, patched local Windows host and dedicated account; disable sync, recording, transcript, debugging, crash upload, clipboard use, and untrusted same-user processes.
2. Verify the fixed custody path, no-reparse/no-Git/no-sync constraints, owner, protected DACL, and empty destination.
3. Activate the dedicated CPython 3.14.3 environment and verify every exact distribution and ABI pin; abort on ambient 50.0.1 or any mismatch.
4. Retrieve the unique passphrase from its separate Human-controlled custody without AI, clipboard, file, environment variable, or command-line exposure.
5. Enter it twice through hidden interactive `getpass`; abort on mismatch, echo fallback, recording risk, or invalid input.
6. Generate exactly one key with `Ed25519PrivateKey.generate()` in memory.
7. Serialize directly to encrypted PKCS#8 PEM with `BestAvailableEncryption`; create the protected file without overwrite; reject any unencrypted or unexpected label.
8. Flush, close, terminate, and restart in a fresh process without printing secret material.
9. Reload through hidden interactive entry and derive the first Raw 32-byte public value and canonical lowercase display; terminate.
10. Repeat reload and derivation in another fresh process; require exact byte and display equality.
11. Create two exact encrypted backups on separate offline controlled media; verify exact copy equality, ACL/custody conditions, independent restore, Ed25519 type, and public-key equality for each.
12. End provisioning if any check fails. Do not continue with a partially verified key.
13. Transfer only the single agreed raw 32-byte public value to Admission PREPARE and compare its display with both derivations.
14. The Human performs the separately frozen Admission CONFIRM as a distinct later act. Generation, backup success, or PREPARE does not imply confirmation.

No real execution is authorized by this document.

## Negative and failure checks

The future implementation and runbook must plan at least these 32 behavioral checks:

1. Reject `NoEncryption` and any plaintext private serialization.
2. Reject Raw private serialization and `private_bytes_raw` use.
3. Reject passphrases in command-line arguments.
4. Reject passphrases in environment variables, files, pipes, or shell variables.
5. Reject non-interactive input, echo fallback, and `GetPassWarning`.
6. Reject empty, mismatched, control-character, non-ASCII, too-short, or too-long passphrases.
7. Reject a destination inside or above a Git working tree.
8. Reject cloud-sync, roaming, network, removable, temp, relative, or alternate working paths.
9. Reject symlink, junction, mount point, and other reparse paths.
10. Reject inherited or broad ACLs, wrong owner, and unexpected principals.
11. Reject existing destinations and overwrite attempts.
12. Reject encrypted output without the expected encrypted PKCS#8 PEM label.
13. Reject wrong public encoding or format.
14. Reject public output whose exact type is not built-in `bytes`.
15. Reject public output whose length is not 32.
16. Reject noncanonical, uppercase, malformed, or non-64-character public display.
17. Reject mismatch between the two clean public derivations.
18. Reject a manually paired or caller-supplied public key.
19. Reject altered or truncated encrypted backup bytes.
20. Reject backup restore failure or wrong loaded key type.
21. Reject backup-derived public mismatch.
22. Fail if private, encrypted PEM, or passphrase content reaches stdout or stderr.
23. Fail if secret-bearing values reach logs, traceback, telemetry, crash reports, clipboard, or screenshots.
24. Reject introduction of a generic or arbitrary-message signing operation.
25. Reject zero, two, or multiple candidate keys.
26. Reject wrong Python, `cryptography`, `cffi`, or `pycparser` version or ABI.
27. Reject source builds, editable installs, path-shadowed modules, and fallback crypto implementations.
28. Reject OpenSSH, command-line OpenSSL, GPG, PyNaCl, or custom cryptography fallback.
29. Reject a replacement key under the historical snapshot.
30. Reject AI, agent, plugin, or remote-service access to private or unlock material.
31. Reject Admission PREPARE before both derivations and both backup restore tests pass.
32. Reject treating generation, backup, extraction, or PREPARE as Admission CONFIRM.

`NEGATIVE_CHECKS_PLANNED: 32`

## Future source-mutation plan

Behavioral checks above are not source mutants. A separately authorized implementation should verify that tests kill at least these 18 mutations:

1. Replace `BestAvailableEncryption` with `NoEncryption`.
2. Change PKCS8 or PEM to Raw, DER, OpenSSH, or another format.
3. Add `private_bytes_raw` or private stdout output.
4. Accept a passphrase from argv, environment, file, pipe, or config.
5. Ignore `GetPassWarning`, non-interactive input, or mismatched confirmation.
6. Permit a caller-selected output path.
7. Skip Git, sync, reparse, network, temp, or roaming path rejection.
8. Leave ACL inheritance or broad principals enabled.
9. Overwrite an existing private container.
10. Skip encrypted-label or reload validation.
11. Change Raw public encoding or format.
12. Skip exact type, length, or canonical-display validation.
13. Remove the second clean public derivation or equality comparison.
14. Skip backup exact-byte, reload, or public-key verification.
15. Permit wrong package versions, source builds, module shadowing, or fallback crypto.
16. Add signing, arbitrary-message, plugin, callback, or network capability.
17. Send private or unlock material to logs, telemetry, exception text, or AI context.
18. Reuse the historical snapshot for a replacement key.

`SOURCE_MUTATIONS_PLANNED: 18`

## Design honesty and next prerequisite

The design is coherent without exact KDF/cipher pinning because it narrows its guarantee to the exact package/wheel, encrypted PKCS#8 API, and verified reload behavior. It does not claim cryptographic serialization reproducibility across upgrades.

Before any real key generation, the Human must:

1. accept this candidate as Human Design Freeze;
2. separately authorize implementation of the bounded helper and runbook;
3. review that implementation against the 32 negative checks and 18 source mutations;
4. provision and verify the exact hash-locked environment rather than the ambient 50.0.1 installation.

After those conditions, the later Human procedure is safe to run within the documented operational assumptions.

`SAFE_TO_GENERATE_REAL_KEY_AFTER_HUMAN_FREEZE: YES, only after separately authorized helper implementation and environment verification`

`NEXT_UNRESOLVED_PREREQUISITE: Human Design Freeze, then separately authorized implementation and review of the bounded helper/runbook in the exact hash-locked environment`

`REAL_KEY_GENERATED: NO`

`PRIVATE_KEY_CREATED: NO`

`ADMISSION_PREPARE_PERFORMED: NO`

`ADMISSION_CONFIRM_PERFORMED: NO`

`IMPLEMENTATION_AUTHORIZED: NO`

`HUMAN_DESIGN_FREEZE: NOT_PERFORMED`

## Sources and observed facts

Repository sources:

- `docs/next/AUDITED_PUBLIC_KEY_VERIFICATION_DEPENDENCY_D2_20261005.md`
- `docs/next/EXACT_BYTES_WITNESS_V0_HUMAN_DESIGN_FREEZE_20261005.md`
- `requirements/exact-bytes-witness-v0.txt`

Official package documentation consulted on 2026-10-05:

- `https://cryptography.io/en/50.0.2/genindex/`
- `https://cryptography.io/en/stable/hazmat/primitives/asymmetric/ed25519/`
- `https://cryptography.io/en/stable/hazmat/primitives/asymmetric/serialization/`

The documentation exposes `Ed25519PrivateKey.generate`, PKCS8/PEM private serialization, `BestAvailableEncryption`, encrypted private-key loading, and Raw public serialization. It describes `BestAvailableEncryption` as a curated choice that may change, which is why exact KDF/cipher parameters are not claimed here.

## Closed-scope protection

This D1 does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, Exact-Bytes Witness v0, Exact Public-Key Admission Decision Semantics v0, Exact Public-Key Admission Act Template and Binding Handoff v0, or any other CLOSED scope.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependency pins, installed packages, key material, admission state, signer-reference binding, or signing service.

## Push status

NO. No public or remote push is authorized by this design.
