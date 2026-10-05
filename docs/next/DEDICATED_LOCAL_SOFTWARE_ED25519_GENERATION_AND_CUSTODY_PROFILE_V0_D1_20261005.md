# Dedicated Local Software Ed25519 Generation and Custody Profile v0 - D1

Date:
2026-10-05

Design status:
READY_FOR_INDEPENDENT_REREVIEW

Revision:
D1-R1 minimal remediation of MF-1 through MF-8 from independent review of commit `4cac108eb6a7c0454433d8a191264517c0fa29a9`.

This document remains a design-freeze candidate only. It requires independent rereview before Human Design Freeze. Human Design Freeze is not performed. It does not generate or select a real key, create private or recovery material, implement a helper, change a dependency, perform Admission PREPARE or CONFIRM, authorize signing, or add identity, role, authorization, trust, provenance, truth, evidence, currentness, revocation, or Human Final semantics.

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

The future helper environment is a dedicated virtual environment with `system-site-packages` disabled. It must use the existing hash-locked requirements file:

`requirements/exact-bytes-witness-v0.txt`

The profile permits only the recorded Windows artifacts:

- `cryptography-50.0.2-cp311-abi3-win_amd64.whl`
- `cffi-2.1.1-cp314-cp314-win_amd64.whl`
- `pycparser-3.0-py3-none-any.whl`

Installation remains outside this design and requires separate operational authorization. The only permitted installation shape is equivalent to `python -m pip --isolated install --no-deps --require-hashes --only-binary :all: -r requirements/exact-bytes-witness-v0.txt` into that empty dedicated virtual environment. Source-distribution builds, dependency resolution, system-site packages, Microsoft Store or packaged Python, editable installs, and ambient user-site packages are not permitted.

The interpreter must be an official non-Store, non-packaged CPython 3.14.3 amd64 installation. Its download source, installer filename, and artifact SHA-256 must be captured from official release evidence and frozen by the future implementation review. Those provenance facts are not currently recorded by this design and are an implementation prerequisite, not an already verified claim.

After installation, the implementation review must retain the exact selected wheel hashes and verify installed distribution `RECORD` entries and file content against the installed wheels as far as the wheel format permits. Metadata version equality alone is insufficient.

The helper runs in isolated Python mode (`-I`) if implementation validation confirms compatibility with the dedicated virtual environment. Before any secret input, runtime preflight must check exact interpreter version, executable path, provenance record, architecture, GIL state, virtual-environment identity, disabled system site packages, exact distribution versions, distribution and module file paths, no repository or current-directory import shadowing, bundled OpenSSL runtime identity, and final resolved custody paths.

The preflight must reject relevant Python and OpenSSL environment injection surfaces rather than silently inherit them, including `PYTHONPATH`, `PYTHONHOME`, `PYTHONSTARTUP`, `PYTHONINSPECT`, `PYTHONBREAKPOINT`, `PYTHONWARNINGS`, `PYTHONUSERBASE`, `PIP_CONFIG_FILE`, `OPENSSL_CONF`, `OPENSSL_MODULES`, and provider/module path overrides. This is fail-closed environmental hardening; this design does not claim a demonstrated `OPENSSL_CONF` exploit.

It must fail closed on the ambient 50.0.1 package, missing packages, free-threaded ABI, alternate or packaged interpreter, wrong interpreter origin, source builds, editable installs, path shadowing, system-site packages, unexpected module paths, mismatched `RECORD` content, unexpected OpenSSL identity, injection variables, or fallback imports.

`PINNED_VERSION: CPython 3.14.3 win_amd64 GIL; cryptography 50.0.2; cffi 2.1.1; pycparser 3.0`

`ENVIRONMENT_MANIFEST: official CPython provenance/hash prerequisite; isolated venv; binary hash-locked wheels only; installed-content, interpreter, module-path, OpenSSL-runtime, and injection-surface preflight`

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

Independent review observed that the selected 50.0.2 Windows implementation emitted an encrypted PKCS#8 construction equivalent to PBES2, PBKDF2-SHA256 with 2048 iterations, and AES-256-CBC. That is an observed implementation detail only. It is not a frozen public API guarantee and is not used as a security-strength claim. This profile deliberately does not parse or pin `AlgorithmIdentifier` at runtime because doing so would make v0 depend on private serialization details while still not turning them into a supported API contract.

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

`PINNING_LIMITATION: BestAvailableEncryption controls backend encryption details; observed PBES2/PBKDF2-SHA256-2048/AES-256-CBC is not an API guarantee; v0 pins package, wheel, container/API, and reload behavior, not exact KDF/cipher parameters or bytes`

## Passphrase and unlock channel

The passphrase must be generated by a Human-controlled password manager using a generator configuration that reports at least 128 bits of generated entropy. Human-composed passphrases and unquantified "strong password" claims are forbidden for v0. The generated secret is retained only in that password manager or a separately controlled sealed recovery record outside AI, repositories, source code, configuration, and ordinary logs.

Before reading any secret, the helper must complete a fail-closed console preflight. It must establish that the process is running under the intended standard, non-administrator Windows account; standard input and the prompt/output handle are canonical interactive Windows console character-device handles; input is not redirected; required console modes allow hidden input; and the helper can configure `getpass.GetPassWarning` as an error. Failure ends the process before `getpass` or any other secret read.

For initial serialization, restore, and later local unlock, the helper then obtains the passphrase only through `getpass.getpass()` in that preflighted console:

- standard input and standard error must be attached to an interactive console;
- terminal transcript, shell transcription, IDE capture, screen recording, and remote session recording must be disabled;
- `getpass.GetPassWarning`, echo fallback, redirected input, non-interactive input, or an exception is a hard failure;
- generation requires two separately entered values and exact equality;
- the accepted value is 24 to 128 printable ASCII characters, contains no control characters, is encoded exactly as ASCII bytes, and came from the declared password-manager generator with at least 128 bits of generated entropy;
- the helper can enforce shape but cannot prove the password manager's entropy report; the Human records that fact only as a runbook declaration without recording the secret;
- clipboard paste, command-line arguments, environment variables, files, pipes, here-strings, shell variables, prompts to AI, and source/config literals are forbidden.

The Human must declare before the run that the console is Human-controlled and has no AI, agent, IDE capture, ConPTY relay, remote-session recorder, or terminal transcript attached. Helper logic cannot cryptographically prove absence of an AI or recorder. That absence, clipboard and cloud-clipboard disablement, and no screen capture are runbook requirements rather than machine-enforced facts.

The passphrase is not stored by the helper. Python strings, encoded bytes, the private-key object, and library internals can remain in process memory until overwritten or reclaimed; CPython and `cryptography` do not give this profile a reliable whole-process zeroization guarantee. The signer host must therefore exclude untrusted same-user processes, debugging, memory capture, crash uploads, and hibernation/pagefile exposure as far as the operating environment permits. This is residual risk, not a claim of secure memory.

`UNLOCK_CHANNEL: hidden interactive Windows console via getpass.getpass; hard fail on echo fallback or non-interactive input`

`PASSPHRASE_REQUIREMENT: password-manager-generated unique printable-ASCII secret with at least 128 bits of reported generated entropy; Human-composed secrets forbidden`

`PASSPHRASE_IN_CLI: NO`

`PASSPHRASE_IN_AI_CONTEXT: NO`

`PRIVATE_KEY_IN_AI_CONTEXT: NO`

`PRIVATE_KEY_IN_REPOSITORY: NO`

## Windows-local custody directory

The working container resides in exactly one dedicated local directory for the intended Windows account:

`C:\Users\<intended-account>\AppData\Local\WeaverForge\custody-v0`

Before any secret exists, the future helper must resolve and validate the concrete absolute path. The helper must run as the intended dedicated standard, non-administrator account and reject elevated, administrator-token, service-account, or impersonated execution because those modes alter the intended ownership and access model. It rejects a path that:

- is inside or above a Git working tree;
- is inside OneDrive, Dropbox, Google Drive, another sync root, a redirected profile, or a roaming profile;
- is a UNC, network, removable, temporary, or relative path;
- contains a symbolic link, junction, mount point, or other reparse point;
- is caller-selected at runtime;
- already contains an unexpected file or an existing candidate key.

The active directory has a closed state-dependent file set defined below. The helper creates every secret or candidate file with create-new/no-overwrite behavior inside an already protected directory and must not follow links. The profile does not permit an alternate output path argument.

### ACL rule

The custody directory must be created through a Windows-native creation operation that supplies the explicit security descriptor and protected DACL atomically at directory creation. Creating a permissive directory and tightening it afterward is forbidden. Explicit access is limited to:

- the exact intended Windows user SID: read, write, delete, and required directory traversal;
- `NT AUTHORITY\SYSTEM`: full control for operating-system operation and controlled recovery.

Broad groups such as `Users`, `Authenticated Users`, `Everyone`, and unrelated service or administrator SIDs must not have explicit or inherited access. The intended user must own the directory. The helper must inspect the owner and effective DACL immediately after directory creation, before creating any secret file. Secret files are then created new inside that directory, inherit the protected DACL, and have owner/DACL verified before content is written and again after close. Any mismatch fails before secret write or transitions the run to `ABANDONED` if secret creation already occurred.

Windows administrators can take ownership, and a compromised process running as the intended user can read the encrypted file and intercept an unlock. ACLs do not protect against same-user compromise. Full-volume encryption is recommended as defense in depth but is not claimed or configured by this profile.

`CUSTODY_DIRECTORY_RULE: fixed resolved local non-reparse AppData\\Local custody-v0 directory outside Git, sync, network, removable, and temp roots`

`WINDOWS_ACL_RULE: protected non-inherited DACL; intended user SID plus SYSTEM only; verify owner and effective entries`

`ACL_CREATION_MODEL: Windows-native atomic directory creation with explicit protected DACL; verify before any secret write; create-new files inherit and are reverified`

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

Machine-enforceable controls are: fixed resolved paths, reparse and location rejection, non-elevated intended account, owner and DACL checks, create-new/no-overwrite behavior, exact state/file-count checks, package/runtime/environment checks, exact byte comparisons, and closed transitions.

Runbook and operational controls are: absence of same-user malware, VSS/File History/indexing/sync/endpoint exfiltration, Human control of the terminal, disabled recording and cloud clipboard, host patch and physical state, and physical backup custody. The helper must not report those operational declarations as machine-proven facts.

The process may hold the private object and passphrase in memory. A crash or malicious same-user process can expose memory. The helper cannot prove absence of OS-level pagefile, dump, endpoint-security, or firmware capture; provisioning must occur on a trusted, patched, non-recorded local host.

## Custody state machine and abandonment

The helper uses one exact closed state machine:

`EMPTY -> PRIVATE_WRITTEN -> PUBLIC_CANDIDATE_WRITTEN -> BACKUPS_VERIFIED -> READY_FOR_ADMISSION_HANDOFF`

The active custody directory contains only the exact files permitted by its current state:

| State | Required active artifacts |
|---|---|
| `EMPTY` | Protected directory and atomic state marker only; no key, candidate, or backup artifact |
| `PRIVATE_WRITTEN` | `custody-v0-private-v0.pem` plus state marker |
| `PUBLIC_CANDIDATE_WRITTEN` | Private PEM, exact 32-byte `custody-v0-candidate-v0.bin`, plus state marker |
| `BACKUPS_VERIFIED` | Same two active files plus state marker recording only non-secret verification completion |
| `READY_FOR_ADMISSION_HANDOFF` | Same two active files plus final state marker; no Admission artifact |

Each transition is code-owned, monotonic, and committed only after the required file is closed, flushed, owner/DACL verified, exact file count verified, and content-specific checks pass. Restart accepts only an exact state/file combination. A partial write, crash, missing file, extra file, stale candidate, state mismatch, or failed check after secret creation transitions to terminal `ABANDONED`.

`ABANDONED` artifacts must not be repaired, overwritten, resumed, reused, backed up as valid, restored as valid, or presented to Admission. The no-argument custody-local abandon operation requires no passphrase and accepts no path. It removes `custody-v0-private-v0.pem` and `custody-v0-candidate-v0.bin` from the active directory into a fixed non-active local quarantine or deletes their directory entries according to the reviewed runbook, writes an `ABANDONED` tombstone, and leaves no active handoff. It makes no claim of physical erasure from SSDs, filesystem history, VSS, or backup media.

Backup copies associated with an abandoned generation are removed from active use. Their media remain secret-bearing until the Human-controlled runbook reinitializes or destroys them using the media-appropriate procedure. A new generation attempt starts only after the old active directory is retired and a fresh empty custody directory is atomically created with the required DACL. No abandoned key or candidate value may cross into the new attempt.

`ABANDON_STATE_MODEL: any post-secret failure before READY is terminal ABANDONED; no repair/reuse/admission; no-argument local abandon removes artifacts from active use without claiming physical erasure`

## Backup model

The minimum backup set is two byte-for-byte copies of the encrypted PKCS#8 PEM on two separately stored, Human-controlled offline removable media. The working container is not counted as a backup.

Requirements:

1. Copy only the closed encrypted PEM file; never export plaintext, Raw private bytes, or seed material.
2. Use media not mounted during routine signing and not managed by cloud sync or ordinary online backup software.
3. Store the two media in separate physical locations with controlled access.
4. Keep the passphrase record separately from both media and the signer host.
5. Re-read each copy and require exact byte equality with the closed working container.
6. Run the no-argument restore-check operation against the second fixed protected custody-local path `C:\Users\<intended-account>\AppData\Local\WeaverForge\restore-v0`. It accepts no caller path and must never read the working original as its restore input.
7. Create `restore-v0` with the same atomic Windows-native protected-DACL creation rule as the active custody directory. Require exactly one create-new encrypted restore artifact and the expected restore state marker; reject extra, stale, linked, substituted, or working-directory artifacts.
8. For each backup in turn, copy only that backup into the empty `restore-v0` slot, require exact byte equality with the intended backup and the closed working encrypted serialization, load it with hidden interactive passphrase entry, require the loaded object to be an `Ed25519PrivateKey`, derive Raw public bytes, and require exact equality with protected `custody-v0-candidate-v0.bin` and exact canonical-display equality.
9. Remove the restored encrypted test copy from active restore use after each check without claiming guaranteed physical erasure on flash storage. Never create a plaintext restored file. Recreate an empty protected `restore-v0` before testing the next backup.
10. Record only backup location labels, completion status, date, and the canonical public-key display. Do not record secret bytes, passphrase, PEM content, or private metadata.
11. A failed copy, exact-byte comparison, reload, type check, ACL check, candidate comparison, or display comparison invalidates that backup and transitions the generation to `ABANDONED` before readiness.

The encrypted backups remain private material and stay within the custody boundary. Encryption reduces consequences of media theft but does not make the file public. Security of arbitrary removable media is physical Human custody plus encryption, not an assertion that the media preserves the Windows custody DACL. Periodic backup re-verification is a runbook recommendation and has no Admission meaning.

`BACKUP_MODEL: two exact encrypted-PKCS8-PEM copies on separately stored offline controlled media; passphrase held separately`

`BACKUP_RESTORE_TEST_REQUIRED: YES`

`RESTORE_CHECK_MODEL: no-argument fixed protected restore-v0 slot; exact artifact set and encrypted bytes; Ed25519 type; Raw candidate and canonical-display equality; never reads working original as restore input`

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
2. In a fresh process, reload the encrypted working container through hidden interactive unlock, require the loaded object to be an `Ed25519PrivateKey`, and derive public value 1 as Raw bytes.
3. Require exact built-in `bytes` type and length 32, then write only those 32 bytes to the fixed protected active path `custody-v0-candidate-v0.bin` with create-new/no-overwrite behavior under the custody DACL. Derive canonical display 1 only from the exact bytes read back from that protected file.
4. Terminate. In another fresh process, reload the encrypted private key, require `Ed25519PrivateKey`, and derive public value 2 as Raw bytes.
5. Read `custody-v0-candidate-v0.bin` from its fixed protected path, require exact type/length/file count/owner/DACL/state, and compare public value 2 against it by exact byte equality. Independently derive canonical display 2 and compare it exactly with display 1 derived from the protected candidate.
6. Require each fixed `restore-v0` backup check to derive the same exact protected candidate bytes and display.
7. Immediately before a later Admission PREPARE, the Human runs a fresh custody-host derivation/display operation. It reloads the encrypted private key, requires `Ed25519PrivateKey`, derives Raw public bytes, compares them exactly with the protected candidate, and displays canonical hex derived from that fresh value.
8. Only that fresh verified Raw value may enter Admission PREPARE. The Human compares PREPARE's display exactly with the fresh custody-host display and the display derived from the protected candidate before any separate CONFIRM.

Repository files, chat text, agent output, clipboard content, logs, screenshots, prior displays, backup labels, and caller-provided copies are never authoritative comparison sources. An abandoned, stale, unprotected, mismatched, or non-current-state candidate or display must never enter PREPARE. The custody helper never reads or writes Admission artifacts; it outputs only the fresh verified public bytes/display for the separate Admission boundary.

No OpenSSH text, PEM public key, DER, certificate, fingerprint, digest, key ID, filename, backup label, or caller string can substitute for the protected exact Raw public bytes. The public hexadecimal display is reversible encoding, not authority.

`PUBLIC_KEY_EXTRACTION: Ed25519PublicKey.public_bytes(Encoding.Raw, PublicFormat.Raw) after encrypted reload`

`PUBLIC_KEY_LENGTH: 32`

`DISPLAY_REPRESENTATION: 64 lowercase ASCII hex`

`INDEPENDENT_PUBLIC_COMPARISON: YES`

`PUBLIC_HANDOFF_MODEL: fixed protected custody-v0-candidate-v0.bin is exact-byte authority; fresh pre-PREPARE derivation must match it; only fresh verified Raw bytes cross to separate PREPARE`

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

A backup known to have been intentionally destroyed under the runbook may be replaced from a verified remaining controlled copy. Any backup medium whose location is unknown, that is stolen, unexpectedly missing, or otherwise unaccounted for creates a `SUSPECTED_COMPROMISE` operational condition, not ordinary backup loss. Stop signing, isolate the remaining signer and media, and use the separately defined additive replacement process as applicable. Loss of all private copies makes the key unusable. None of these events changes, revokes, deactivates, or supersedes historical Admission v0.

### Suspected compromise

Stop signing, isolate the signer host and all backup media, preserve only non-secret incident information, and treat every private copy as suspect. Do not continue merely because the encrypted container still reloads. This profile creates no revocation or currentness result.

### Replacement

A replacement requires a newly generated key under a separately current profile, a new additive admission snapshot, a new two-phase admission act, and separately authorized signer-reference and signing-boundary changes. The replacement must not reuse or mutate `EXACT_PUBLIC_KEY_ADMISSION_SNAPSHOT_V0`.

`LOSS_HANDLING: known destroyed copy may be replaced; unknown-location, stolen, unexpectedly missing, or unaccounted backup is SUSPECTED_COMPROMISE; historical admission is unchanged`

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

After Human Design Freeze, independent rereview acceptance, and separate authorization of the reviewed helper implementation, the bounded Human run is:

1. Prepare a trusted, patched local Windows host and dedicated standard non-admin account. Make the operational declaration that sync, recording, transcript, debugging, crash upload, clipboard/cloud clipboard, untrusted same-user processes, VSS/File History/indexing exfiltration, and AI/agent/IDE attachment are absent or disabled.
2. Verify official CPython provenance and artifact hash, create the isolated virtual environment with the frozen binary-wheel command, verify installed content, and pass every interpreter/module/OpenSSL/environment-injection preflight before reading a secret.
3. Atomically create the fresh fixed custody directory with its explicit protected DACL. Verify path, no-reparse/no-Git/no-sync rules, non-elevated account, owner, DACL, exact `EMPTY` state, and file count before any secret exists.
4. Only after console-handle and mode preflight succeeds, retrieve the password-manager-generated secret from separate Human custody without AI, clipboard, file, environment variable, or command-line exposure.
5. Enter it twice through hidden interactive `getpass`; abort before generation on mismatch, echo fallback, warning, redirection, invalid shape, or failed runbook declaration.
6. Generate exactly one key with `Ed25519PrivateKey.generate()` in memory.
7. Serialize directly to encrypted PKCS#8 PEM with `BestAvailableEncryption`; create `custody-v0-private-v0.pem` new inside the already protected directory; verify inherited owner/DACL and encrypted label; close and commit `PRIVATE_WRITTEN`.
8. In a fresh process, reload, require `Ed25519PrivateKey`, derive Raw public value 1, create-new `custody-v0-candidate-v0.bin` with only the exact 32 bytes, verify it, derive display 1 from its read-back bytes, and commit `PUBLIC_CANDIDATE_WRITTEN`.
9. In another fresh process, reload, require `Ed25519PrivateKey`, derive Raw public value 2, and require exact byte equality with the protected candidate and exact display equality.
10. Create two exact encrypted backups on separate offline controlled media. Use the no-argument fixed `restore-v0` check for each; verify exact encrypted bytes, loaded Ed25519 type, protected candidate equality, and canonical display. Commit `BACKUPS_VERIFIED` only after both pass.
11. Verify the exact final state and artifact set, then commit `READY_FOR_ADMISSION_HANDOFF`. Any crash, partial write, restart mismatch, or failure after secret creation invokes no-argument abandon and permanently excludes that generation from admission.
12. Immediately before PREPARE, run a fresh custody-host derivation/display and compare it with protected `custody-v0-candidate-v0.bin`. Only those freshly verified Raw bytes cross the boundary.
13. Admission PREPARE independently validates the public value. The Human compares its display with the fresh custody display and protected-candidate-derived display. Repository, chat, agent, clipboard, log, screenshot, stale, or abandoned copies are not comparison sources.
14. The Human performs the separately frozen Admission CONFIRM as a distinct later act. Generation, backup success, readiness, or PREPARE does not imply confirmation.

No real execution is authorized by this document. After Freeze and implementation review, the profile is eligible for separately authorized execution; this document does not call an unimplemented procedure safe to run.

## Negative and failure checks

The future implementation and runbook must plan at least these 48 behavioral checks:

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
33. Inject a crash or partial write at every state transition and require restart to accept only the exact prior committed state or enter `ABANDONED`.
34. Reject partial, duplicated, skipped, reordered, rolled-back, or file-inconsistent state markers.
35. Reject an abandoned candidate or display presented to PREPARE.
36. Reject substitution, truncation, extension, linking, or overwrite of protected `custody-v0-candidate-v0.bin`.
37. Reject comparison against repository, chat, agent, clipboard, log, screenshot, or prior-display copies.
38. Reject each relevant Python or OpenSSL environment injection variable and unexpected provider/module path.
39. Reject Microsoft Store or packaged Python, wrong interpreter provenance/hash, system-site packages, user-site packages, source builds, and wrong virtual environment.
40. Reject redirected or noncanonical stdin, missing console handles, wrong console modes, warning suppression, echo fallback, ConPTY/IDE declaration failure, and any secret read before preflight.
41. Treat unknown-location, stolen, unexpectedly missing, or unaccounted backup media as `SUSPECTED_COMPROMISE`, not routine replacement.
42. Reject a restore check that reads, links, or falls back to the working original instead of the fixed `restore-v0` artifact.
43. Reject custody or restore directories whose protected DACL was applied only after creation or after secret write.
44. Reject a loaded non-Ed25519 key, including X25519 or another raw-32-byte key type.
45. Reject multiple, stale, extra, or wrong-state public candidate files.
46. Reject abandon with caller arguments, repair/resume of `ABANDONED`, or reuse of abandoned artifacts or media.
47. Reject Human-composed, reused, unquantified, or password-manager-reported-under-128-bit secrets.
48. Reject treating observed PBES2/PBKDF2-SHA256-2048/AES-256-CBC details as a stable API guarantee or admission claim.

`NEGATIVE_CHECKS_PLANNED: 48`

## Future source-mutation plan

Behavioral checks above are not source mutants. A separately authorized implementation should verify that tests kill at least these 30 mutations:

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
19. Write the public candidate anywhere except the fixed protected candidate path.
20. Compare derivation 2 or PREPARE against text, repository, chat, agent, clipboard, log, or stale display instead of protected exact bytes.
21. Remove a custody state, allow a backward/skip transition, or accept a mismatched state/file set after restart.
22. Repair, overwrite, resume, back up, restore, or admit an `ABANDONED` generation.
23. Make abandon accept a caller path or leave an active handoff.
24. Treat a missing, stolen, unknown-location, or unaccounted backup as ordinary loss instead of suspected compromise.
25. Accept a Human-composed or under-128-bit-reported passphrase source.
26. Read a secret before console-handle/mode and warning preflight or suppress `GetPassWarning`.
27. Inherit Python/OpenSSL injection variables, system site packages, or unverified interpreter/module paths.
28. Create a custody or restore directory permissively and tighten the DACL after creation or secret write.
29. Make restore caller-selectable, allow it to read the working original, skip exact encrypted-byte comparison, or skip exact `Ed25519PrivateKey` type.
30. Allow the future signer scope to accept a free-form record or expose generic arbitrary-message signing.

`SOURCE_MUTATIONS_PLANNED: 30`

## Design honesty and next prerequisite

The design is coherent without exact KDF/cipher pinning because it narrows its guarantee to the exact package/wheel, encrypted PKCS#8 API, and verified reload behavior. It does not claim cryptographic serialization reproducibility across upgrades.

Before any real key generation, the Human must:

1. accept this candidate as Human Design Freeze;
2. separately authorize implementation of the bounded helper and runbook;
3. independently rereview D1-R1 and review the implementation against the 48 negative checks and 30 source mutations;
4. provision and verify the exact hash-locked environment rather than the ambient 50.0.1 installation.

After those conditions, the later Human procedure is eligible for separately authorized execution within the documented operational assumptions. Neither this candidate nor its future Freeze alone authorizes execution.

`SAFE_TO_GENERATE_REAL_KEY_AFTER_HUMAN_FREEZE: NO; Freeze alone is insufficient; execution becomes eligible only after independent rereview, separate helper/runbook authorization, implementation review, and exact environment verification`

`NEXT_UNRESOLVED_PREREQUISITE: Human Design Freeze, then separately authorized implementation and review of the bounded helper/runbook in the exact hash-locked environment`

`REAL_KEY_GENERATED: NO`

`PRIVATE_KEY_CREATED: NO`

`ADMISSION_PREPARE_PERFORMED: NO`

`ADMISSION_CONFIRM_PERFORMED: NO`

`IMPLEMENTATION_AUTHORIZED: NO`

`HUMAN_DESIGN_FREEZE: NOT_PERFORMED`

## D1-R1 material-finding closure map

`MF-1: CLOSED_BY_D1_R1`

Derivation 1 now writes the sole protected exact-byte candidate; derivation 2, restore checks, and fresh pre-PREPARE derivation compare against it. External copies and stale or abandoned displays have no authority.

`MF-2: CLOSED_BY_D1_R1`

The closed monotonic state machine, terminal `ABANDONED` state, no-argument abandon operation, artifact exclusion, media handling, and fresh-directory restart rule are explicit.

`MF-3: CLOSED_BY_D1_R1`

Unknown-location, stolen, unexpectedly missing, or unaccounted backup media now creates `SUSPECTED_COMPROMISE`; historical Admission remains unchanged.

`MF-4: CLOSED_BY_D1_R1`

Observed encryption parameters are labeled implementation detail rather than API guarantee, and v0 requires a password-manager-generated secret with at least 128 bits of reported generated entropy.

`MF-5: CLOSED_BY_D1_R1`

Console handles, modes, redirection, warning behavior, account, and interactivity are checked before secret read; absence of AI, ConPTY, IDE capture, and recording is accurately classified as a runbook declaration.

`MF-6: CLOSED_BY_D1_R1`

The environment manifest now requires official CPython provenance/hash evidence, isolated venv, binary hash-locked installation, installed-content checks, isolated mode where compatible, resolved-path/runtime checks, and fail-closed Python/OpenSSL injection handling. Missing CPython artifact evidence is explicitly an implementation prerequisite.

`MF-7: CLOSED_BY_D1_R1`

Custody and restore directories receive explicit protected DACLs atomically at creation before secret write; non-admin execution, inherited file ACL verification, and machine-versus-runbook controls are explicit.

`MF-8: CLOSED_BY_D1_R1`

The no-argument fixed protected `restore-v0` slot verifies exact artifacts and bytes, encrypted reload, exact Ed25519 type, protected candidate bytes, and canonical display without reading the working original as restore input.

`MATERIAL_FINDINGS_OPEN: NONE`

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
