# Real Ed25519 Key Sourcing and Custody Prerequisite v0 - D0

Date:
2026-10-05

Design status:
READY_FOR_PROFILE_SELECTION

This document is a bounded D0 analysis only. It is not a Human Design Freeze, does not select or generate a real key, does not create or request private material, does not perform an admission act, does not authorize implementation, and does not add identity, role, authorization, provenance, trust, freshness, revocation, evidence, truth, or Human Final semantics.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Base HEAD:
`17ceacdd20ad768696554a182704b61cccf2f9fc`

Frozen admission-act design commit:
`68625cee90cb322cef19b4d3927744c2177ad9dc`

Admission-act Human Design Freeze save commit:
`17ceacdd20ad768696554a182704b61cccf2f9fc`

## Recommended next scope

`Dedicated Local Software Ed25519 Generation and Custody Profile v0`

The next scope should freeze one concrete provisioning toolchain, encrypted private-key container, interactive unlock method, filesystem protections, backup procedure, raw public-key extraction procedure, and destruction checks. It must remain separate from admission, signer-reference binding, and signing-policy design.

## Core question

> What minimum key-generation, custody, backup, export, and public-key verification procedure must exist before one real Ed25519 public key may enter the frozen two-phase admission process, while ensuring that private key material never enters AI context, repository content, ordinary logs, admission records, or public artifacts?

## Required transition separation

The lifecycle contains six separate transitions:

1. **Key generation** creates an Ed25519 keypair inside a controlled signer boundary.
2. **Custody** protects private material and any encrypted backup without granting admission or signing authority.
3. **Public-key extraction** derives exactly one raw 32-byte public value and verifies its transport representation.
4. **Admission** is the separately frozen two-phase Human act over that public value.
5. **Signer-reference binding** is a later separate scope that may associate an admitted-key handoff with a human, AI execution or service, or verifier-service reference.
6. **Signing** is a later narrow operation over exact permitted bytes under a separately defined policy.

Success at one transition does not imply success, identity, role, authorization, trust, provenance, truth, or evidence at another.

`valid signature != admitted key != identity != role != authorization != truth`

## Candidate custody profiles

### 1. Dedicated local software key with encrypted controlled backup

Generate the key on a dedicated, trusted local signer host using a separately frozen and pinned Ed25519 implementation and operating-system CSPRNG. Do not generate it in chat, a repository shell transcript, a CI job, a shared development environment, a notebook, a browser console, or a remote AI execution environment.

Store the working private key only in an encrypted private-key container under a dedicated OS account with restrictive filesystem ACLs. Unlock must be interactive or mediated by a narrow local secret store; passphrases must not be command-line arguments, environment variables, source files, configuration files, clipboard content, or redirected standard input.

Permit private-key export only during controlled provisioning into the specified encrypted container and its encrypted backups. Never export raw private bytes, plaintext seed material, or an unencrypted secret backup. Routine signing must not expose or re-export the private key.

Maintain at least two verified encrypted backup copies on separately stored, access-controlled offline media. Keep the backup-unlock secret separately from those media using a Human-controlled secret manager or sealed recovery method selected by the future profile. Test restoration in the controlled boundary before relying on the backups, then securely remove temporary restored copies according to the frozen procedure.

This profile is the smallest common operational basis for a Human-controlled signer and for a future narrow service boundary. It supports recovery without silently changing the admitted public key, while limiting secret copies to named controlled locations.

### 2. OS-backed keystore

An OS-backed keystore may improve secret handling and interactive unlock, but it is not yet selected. Repository evidence does not establish that the target Windows keystore exposes the required Ed25519 generation, generic exact-byte signing, raw 32-byte public-key extraction, backup or migration behavior, and non-exportability controls as one reviewed interface.

It may become a later profile only after those exact capabilities and failure modes are demonstrated. A generic claim that a key is OS-protected is insufficient.

### 3. Hardware-backed non-exportable key

A hardware-backed non-exportable key is preferable for extraction resistance when a specific device and provider can demonstrably generate Ed25519, sign the required exact bytes without semantic transformation, export the exact raw 32-byte public key, enforce access control, and expose stable failure behavior.

No such device or provider is established by the repository or this host inspection. Hardware selection would also make device loss a mandatory replacement event unless an explicitly designed vendor recovery mechanism exists. It is therefore a future higher-assurance profile, not the smallest proven v0 baseline.

### Direction

Recommend the dedicated local software profile for v0, with encrypted exportable backup under strict custody. Keep OS-backed and hardware-backed non-exportable profiles additive. Do not pretend that an unverified hardware or OS facility is safer merely because it is labeled a keystore.

`PRIVATE_KEY_EXPORTABLE_RECOMMENDATION: CONDITIONALLY_YES_ENCRYPTED_BACKUP_ONLY`

## Local tool and dependency observation

Read-only inspection on 2026-10-05 found:

- Windows OpenSSH `ssh-keygen.exe` is installed and advertises `ed25519` and `ed25519-sk` key types.
- `openssl`, `gpg`, and `age-keygen` are not present on the command path.
- The ambient CPython is 3.14.3 with `cryptography` 50.0.1.
- The CLOSED Exact-Bytes Witness verifier instead pins `cryptography` 50.0.2 through its own reviewed dependency surface.

These facts do not select a generator.

OpenSSH uses SSH private/public container formats; a safe, frozen conversion from its public form to Admission's exact raw 32 bytes is not present. Its `ed25519-sk` option also requires a specific security-key provider and capability review.

The ambient `cryptography` 50.0.1 must not be used merely because it imports. Reusing the CLOSED verifier's 50.0.2 package for key generation would add a new secret-bearing API and operational purpose that its freeze did not authorize.

The next profile-selection scope must choose and pin the exact generator and serialization APIs, confirm their random-source behavior, define the private container and encryption/KDF settings, and verify raw public-key extraction. No dependency installation or change is authorized here.

## Signing and custody boundary

For v0, the signing/custody boundary consists only of:

- the dedicated signer host and dedicated OS account;
- the reviewed key-generation and signing process;
- the encrypted working private-key container or future non-exportable provider;
- the separately stored encrypted backup media and their controlled restoration environment;
- the separate Human-controlled unlock-secret custody mechanism.

The following may leave that boundary after exact validation:

- the raw 32-byte public key;
- its canonical 64-character lowercase hexadecimal display;
- signatures created by a later separately frozen signing protocol;
- signed exact public bytes or public decision records when a later scope authorizes their release.

A digest or hash may leave only if a later separately frozen protocol defines its domain, preimage, and meaning. No digest is a substitute for the exact public key or signed exact bytes in this D0.

The following must never leave the signing/custody boundary:

- private-key bytes;
- seed or expanded secret material;
- passphrases, recovery secrets, unlock tokens, or PINs;
- plaintext or raw secret backups;
- decrypted temporary private-key files;
- memory dumps, debug output, stack traces, telemetry, or logs containing secret material;
- screenshots, clipboard entries, shell history, command-line arguments, environment variables, AI prompts, or support bundles containing any secret.

`PUBLIC_KEY_ALLOWED_OUTSIDE_SIGNING_BOUNDARY: YES`

`SIGNATURE_ALLOWED_OUTSIDE_SIGNING_BOUNDARY: YES`

## Secret-handling minimums

The future profile must enforce all of the following:

1. Generate directly into the controlled destination; never print private material to a terminal.
2. Disable command echo, transcript capture, debug logging, crash upload, clipboard use, and screen capture for provisioning.
3. Use an interactive secret entry path that does not expose the unlock secret in process arguments or environment variables.
4. Create private containers and temporary files with restrictive access before writing content.
5. Never place secret-bearing files under the repository, its parent export trees, cloud-sync folders, CI workspaces, or ordinary backup agents.
6. Scan the intended public export and repository status for secret formats before admission, without copying secrets into the scanner's logs.
7. Record only non-secret procedural outcomes. Do not record passphrases, seeds, private serialization, or raw backup content.
8. Minimize controlled private copies and maintain an explicit inventory of the working container and encrypted backups.
9. Verify each encrypted backup by controlled restoration before deleting any prior known-good backup.
10. Destroy temporary plaintext material and abandoned candidate keys according to the future profile before ending provisioning.

No procedure can prove that a compromised host kept a secret. Host integrity and malware exposure must be assessed before generation; uncertainty requires abandoning that candidate and generating a replacement in a clean boundary before admission.

## Public-key extraction and comparison

The only value entering Admission `PREPARE` is exactly one built-in `bytes` value of length 32 produced by the frozen extraction path.

The future profile must:

1. Derive the public key from the protected private-key object using the selected tool's reviewed API; never accept a manually paired public-key file as authoritative.
2. Export only the raw 32 public octets through a dedicated public-only path.
3. Extract the public key twice in separate clean invocations after reopening the same protected private-key object.
4. Compare both raw outputs by exact byte equality inside the controlled workflow.
5. Derive canonical lowercase hexadecimal independently from each raw output and require identical 64-character text.
6. Transfer only the public bytes or canonical public display to the Admission preparation boundary.
7. Have Admission `PREPARE` perform its own strict display round trip and compare the prepared display against both extraction displays before Human confirmation.
8. Reject any mismatch, format conversion ambiguity, unexpected metadata, extra key, changed container, or silent signer-key change.

This double extraction and independent Admission round trip address public-key transport and transcription risk. They are not proof of possession and do not authorize signing.

`INDEPENDENT_COMPARISON_REQUIRED: YES`

## Backup, loss, and compromise

### Backup loss

Loss of one backup requires controlled replacement of that backup from a verified remaining private-key container, without printing or exporting plaintext secret material. Loss of all private instances makes the key unusable; it does not revoke the immutable admission snapshot.

### Device or key loss

If the private key cannot be recovered, stop using it. Do not label the historical admission revoked, inactive, or superseded under Admission v0. Any replacement key requires a new additive snapshot, a new two-phase admission act, and separately authorized downstream binding and signing changes.

### Suspected compromise

Immediately stop signing with the suspect key, isolate the signer boundary, preserve only non-secret incident evidence, and treat every copy and backup as suspect until assessed. Admission v0 remains a historical fact and supplies no revocation semantics. A replacement requires a new additive snapshot and admission act. Any currentness, revocation, denylist, or compromise-notice mechanism requires a separate scope.

### Backup theft

An encrypted-backup theft is a compromise event even if encryption is believed intact. Rotate operational use through the additive replacement process after risk assessment; do not silently rewrite v0 or claim revocation from this D0.

## AI-triggered signing boundary

An AI model must never receive, reconstruct, decrypt, transmit, or directly access private-key, seed, recovery, PIN, passphrase, or raw backup material.

A future AI-triggered workflow may request signing only through a narrow signer service or keystore operation outside model context. That later interface must:

- accept only a separately frozen exact decision-record type or domain;
- prevent arbitrary-byte signing by the AI;
- enforce code-owned scope and policy rather than caller labels;
- show or log only public request identifiers and non-secret outcomes;
- return only the signature and permitted public metadata;
- bind each operation to the configured public key and fail if the signer silently changes key;
- define Human approval, service policy, rate limits, replay handling, and audit behavior in its own scope.

This D0 neither implements nor authorizes that service and does not bind the admitted key to an AI identity, model, provider, role, or authorization.

`AI_DIRECT_PRIVATE_KEY_ACCESS: NO`

`AI_FUTURE_SIGNING_MODEL: narrow non-AI signer boundary over separately frozen decision-record inputs`

## Proof-of-possession boundary

Proof of possession is not required for admission and cannot be smuggled into the frozen prepare or confirm phases.

A future operational profile may need a local keypair-consistency or signer-health check before deployment. If that check uses a signature, its challenge, domain, result vocabulary, storage, replay behavior, and nonclaims require a separate scope. It must not become admission authority or signer identity.

`PROOF_OF_POSSESSION_REQUIRED_FOR_ADMISSION: NO`

## Threat coverage

| Threat | Required treatment |
|---|---|
| Accidental secret commit | Generate and store outside repositories; restrictive paths; public-only export; non-secret repository scan |
| Secret in shell history | No secret arguments, command substitution, pasted secret, or echoed input |
| Secret in AI prompt or log | AI has no secret access; disable secret-bearing logs and transcripts |
| Clipboard or screenshot leakage | No clipboard or screen capture during generation, unlock, backup, or recovery |
| Wrong public key admitted | Double extraction, exact raw equality, independent canonical display comparison, frozen PREPARE round trip |
| Public/private mismatch | Derive public bytes from the protected private object twice; reject manual pairing |
| Backup loss | Two verified encrypted copies on separately stored controlled media |
| Backup theft | Separate unlock-secret custody; treat theft as compromise |
| Machine compromise | Pre-generation host assessment; abandon affected candidate; isolate suspect signer |
| Copies on uncontrolled machines | Explicit inventory; working copy and encrypted backups only; no sync or ordinary backups |
| Signing API too broad | Future allowlisted decision-record interface; no arbitrary-byte endpoint |
| AI requests arbitrary signatures | Code-owned request domain and policy gate outside model context |
| Signer silently changes key | Exact public-key check before each future signer activation or operation, defined later |
| Lost key treated as revoked | Loss stops use but creates no Admission-v0 revocation claim |
| Replacement reuses historical snapshot | New additive snapshot and admission act are mandatory |
| Public-key encoding error | Raw 32-byte extraction plus strict lowercase-hex round trips and exact comparison |

`THREAT_MODEL_STATUS: COVERED_FOR_D0`

## D0 conclusion

The D0 is sufficient to choose a concrete generation and custody profile next. No smaller semantic prerequisite is required.

The next unresolved prerequisite is exact profile selection and freeze, including:

- the exact pinned generator and serialization implementation;
- entropy and CSPRNG behavior;
- encrypted private-container format;
- encryption, KDF, and parameter choices;
- interactive unlock channel;
- filesystem and account protections;
- exact backup media, count, verification, and recovery procedure;
- raw 32-byte public extraction and conversion rules;
- public-only transfer and comparison procedure;
- cleanup and secret-leak checks;
- capability evidence if OS-backed or hardware-backed custody is proposed.

Only after that profile is frozen and separately authorized may a real key be generated. The generated public key must still pass the already frozen two-phase admission act. Generation itself is not admission.

`REAL_KEY_SELECTED: NO`

`PRIVATE_KEY_CREATED: NO`

`ADMISSION_ACT_PERFORMED: NO`

`IMPLEMENTATION_AUTHORIZED: NO`

## Closed-scope protection

This D0 does not modify or reinterpret R3, R4, WVMA-V1, TE, RP, IVP, CR, RER, EBD, DSDS-v0, ACD-v0, CSAR-v0, ACR-v0, PSRD-v0, SUBP-v0, Exact-Bytes Witness v0, Exact Public-Key Admission Decision Semantics v0, Exact Public-Key Admission Act Template and Binding Handoff v0, or any other CLOSED scope.

It does not alter VECTOR, EIG, Canonical, Published, or Deployed state. It changes no production code, tests, requirements, dependencies, registry, key material, admission record, signer-reference binding, or signing service.

## Push status

NO. No public or remote push is authorized by this D0.
