# Dedicated Local Software Ed25519 Custody Helper and Runbook v0 - Runbook

Date:
2026-10-05

Status:
IMPLEMENTATION_RUNBOOK_V0 - READY_FOR_INDEPENDENT_FINAL_REVIEW

This runbook accompanies the bounded helper package `ed25519_custody_v0/`. It does not authorize execution. Real key generation, a real passphrase, real backups, and Admission PREPARE or CONFIRM remain unauthorized until Human Final and a separate Human authorization.

Frozen basis:

- D1-R1 design commit: `73942f18b5089c48795039d2fe8f24bf01b0c2f7`
- D1-R1 file: `docs/next/DEDICATED_LOCAL_SOFTWARE_ED25519_GENERATION_AND_CUSTODY_PROFILE_V0_D1_20261005.md`
- D1-R1 SHA-256: `B788A240989F00A01844692C6B714E1106F936D1220C9E79AB67173DDEB01791`
- Human Design Freeze record commit: `77100848a4485955067b8a8433b987b646f3e140`

This runbook implements the frozen semantics. It does not edit or reinterpret D1-R1. Where it records an operational clarification for nonmaterial limitations N1-N8, the clarification sits inside the frozen semantics.

`REAL_KEY_GENERATION_AUTHORIZED: NO`

`ADMISSION_PERFORMED_BY_HELPER: NO`

`SIGNING_API: NONE`

## 1. What the helper is and is not

The helper is one small local Python package. It runs one bounded phase per process and terminates. It uses only `Ed25519PrivateKey.generate()`, encrypted PKCS#8 PEM through `BestAvailableEncryption`, encrypted reload, and Raw/Raw public extraction.

It has no signing API, no arbitrary-message signing, no signer service, no caller-provided message, no Admission artifact input or output, no network access, and no identity, role, authorization, or trust semantics. It does not accept a key, seed, path, snapshot, algorithm, passphrase, or message argument. ACLs do not defeat same-user compromise or an administrator.

## 2. Invocation

Only after every PRE-REAL prerequisite in section 3 is satisfied:

```text
<dedicated-venv>\Scripts\python.exe -I <helper-root>\ed25519_custody_v0\__main__.py <subcommand>
```

Each invocation takes exactly one subcommand and no other argument. Any other argument shape returns `ERROR USAGE_REJECTED` before anything else runs.

| Subcommand | Required state | Secret read | Result |
|---|---|---|---|
| `preflight` | any | no | machine preflight only; prints `PREFLIGHT_OK MACHINE_CHECKS_ONLY` |
| `init` | no active `custody-v0` or `restore-v0` | no | atomic protected `custody-v0`; `EMPTY` |
| `generate` | `EMPTY` | twice | one key; encrypted PEM; `PRIVATE_WRITTEN` |
| `derive-candidate` | `PRIVATE_WRITTEN` | once | derivation 1; protected candidate; `PUBLIC_CANDIDATE_WRITTEN DERIVATION_1` |
| `verify-candidate` | `PUBLIC_CANDIDATE_WRITTEN DERIVATION_1` | once | derivation 2; prints `DISPLAY`; `... DERIVATION_2` |
| `restore-init` | `... DERIVATION_2` or `... RESTORE_CHECK_1` | no | atomic protected empty `restore-v0` with restore marker |
| `restore-check` | same as `restore-init` | once | one backup verified; slot removed; `... RESTORE_CHECK_1` or `... RESTORE_CHECK_2` |
| `restore-clear` | any | no | removes the restore slot; unexpected content is moved to quarantine |
| `mark-backups-verified` | `... RESTORE_CHECK_2`, no slot | no | `BACKUPS_VERIFIED` |
| `mark-ready` | `BACKUPS_VERIFIED`, no slot | no | `READY_FOR_ADMISSION_HANDOFF`; prints `ADMISSION NOT_PERFORMED` |
| `pre-prepare-display` | `READY_FOR_ADMISSION_HANDOFF` | once | fresh derivation compared with the protected candidate; prints `DISPLAY` |
| `abandon` | any active generation | no | tombstone; moves active directories into quarantine |
| `status` | any | no | read-only state report |

The subcommand names follow the authorized shape. `PUBLIC_CANDIDATE_WRITTEN DERIVATION_1/DERIVATION_2/RESTORE_CHECK_1/RESTORE_CHECK_2` are non-secret progress records inside the single frozen state `PUBLIC_CANDIDATE_WRITTEN`, not additional states.

## 3. PRE-REAL prerequisites (blocking before any real execution)

These are not established by the automated tests. The test environment was a temporary venv and is explicitly not the PRE-REAL environment.

1. **Official CPython provenance.** Obtain the official non-Store, non-packaged CPython 3.14.3 amd64 installer from python.org release evidence. Record the download source, installer filename, installer SHA-256, and Authenticode signer. Install it. Record the SHA-256 of `python.exe` and `python314.dll`. A separately reviewed change must then set `_INTERPRETER_PROVENANCE` in `ed25519_custody_v0/manifest.py`. Until then every subcommand fails closed with `ERROR ENV_PROVENANCE_NOT_RECORDED`.
2. **Dedicated virtual environment** with `include-system-site-packages = false`, created from that interpreter.
3. **Binary hash-locked installation only:** `python -m pip --isolated install --no-deps --require-hashes --only-binary :all: -r requirements/exact-bytes-witness-v0.txt`. No other package, `.pth` file, editable install, or source build may be added to that venv.
4. **Installed content verification.** The helper verifies, at runtime, every installed `RECORD` row against file content and checks a pinned digest of the wheel-origin `RECORD` rows of `cryptography 50.0.2`, `cffi 2.1.1`, and `pycparser 3.0`. These pins were computed from the hash-locked wheels installed by the frozen command (pip verified the wheel SHA-256 values from the requirements file). The independent final review should re-derive them directly from the reviewed wheel artifacts.
5. **Isolated mode** `-I`, no `-X` options, no `-W` options, no debug/inspect/verbose/dev-mode flags.
6. **No injection variables.** Clear every variable whose name starts with `PYTHON`, `OPENSSL`, `PIP_`, `CRYPTOGRAPHY`, `CFFI`, `SSL_CERT`, or `WEAVERFORGE`, or contains `PASSPHRASE`. The helper rejects them rather than inheriting them.
7. **Bundled OpenSSL identity.** The helper requires the backend version text `OpenSSL 4.0.3 29 Sep 2026` reported by the reviewed `cryptography 50.0.2` Windows wheel.

## 4. Human declarations (runbook only; not machine-proven)

The helper cannot prove these facts. The Human records each as a declaration before the run, without recording any secret:

- trusted, patched local Windows host; dedicated standard, non-administrator account;
- no AI, agent, IDE capture, ConPTY relay, remote-session recorder, terminal transcript, or screen recording attached to the console;
- clipboard history and cloud clipboard disabled; no paste of the passphrase;
- no untrusted same-user process, debugger, memory capture, crash upload, hibernation or pagefile exposure as far as the host permits;
- VSS, File History, indexing, sync, and endpoint upload excluded for `%LOCALAPPDATA%\WeaverForge`;
- physical custody of backup media.

The helper machine-enforces only: fixed resolved paths; Git, sync, roaming, temp, network, removable, relative, and reparse rejection; non-elevated, non-admin, non-service, non-impersonated account; atomic protected DACL at directory creation; owner and DACL checks through handles; create-new files; exact state and file sets; environment manifest; console handle and mode preflight; exact byte comparisons; closed transitions.

## 5. Passphrase

- Generated by a Human-controlled password manager whose generator configuration reports at least 128 bits of generated entropy. Human-composed, reused, or unquantified passphrases are forbidden. This is a Human declaration; the helper only enforces shape.
- Shape enforced by the helper: 24 to 128 printable ASCII characters (0x20-0x7E), encoded as ASCII.
- Entered only by typing into the hidden prompt of the preflighted console. Never via argument, environment variable, file, pipe, here-string, shell variable, clipboard, chat, or AI.
- Fail-closed warning (frozen L239 and L263): after the private container exists and before READY, a wrong passphrase, warning, or reload failure in `derive-candidate`, `verify-candidate`, or `restore-check` terminally abandons the generation. Type carefully. After READY, a failure never abandons (N2).

## 6. Procedure (maps D1-R1 L380-L395)

1. Satisfy section 3 and record section 4.
2. Pre-test both new backup media (N8): format, write and read back a non-secret test file, confirm the media are not cloud-synced or auto-backed-up, then remove the test file. This reduces the chance that a defective medium forces abandonment of a good generation.
3. `preflight`.
4. `init`. The helper creates `%LOCALAPPDATA%\WeaverForge` (if absent) and `custody-v0` with the protected DACL supplied atomically at creation (no create-then-tighten), verifies owner and DACL, and writes `EMPTY`.
5. `generate`. Enter the passphrase twice.
6. `derive-candidate` in a fresh process. Enter the passphrase.
7. `verify-candidate` in another fresh process. Enter the passphrase. Note the `DISPLAY` line.
8. For each of the two backups in turn:
   1. Copy only `custody-v0\custody-v0-private-v0.pem` to the medium.
   2. Confirm byte equality between the medium copy and the working container, for example `fc.exe /b <working> <medium-copy>` reporting no differences (N4: medium equality is a runbook step).
   3. `restore-init`.
   4. Copy only that medium copy into `restore-v0\restore-v0-artifact-v0.pem` (for example `copy /b`). Never link, never copy from the working directory.
   5. `restore-check`. Enter the passphrase. On success the helper deletes the restored copy and the slot.
9. `mark-backups-verified`.
10. `mark-ready`.
11. Later, immediately before a separately authorized Admission PREPARE: `pre-prepare-display`. Only that fresh verified display, compared with the protected candidate, may be carried to PREPARE. Admission CONFIRM is a distinct later Human act; the helper never performs PREPARE or CONFIRM.

Record only backup location labels, completion status, date, and the canonical display. Never record passphrase, PEM content, or private metadata.

## 7. Restore slot (N4)

`restore-v0` is created only by `restore-init`, with the same atomic protected DACL. It holds exactly `restore-v0-state-v0` (content `RESTORE_EMPTY FOR_CHECK 1` or `2`, bound to the expected check) and one copied `restore-v0-artifact-v0.pem`. `restore-check` rejects extra, stale, linked, substituted, or wrong-check artifacts, compares the artifact bytes exactly with the working container, loads only the artifact bytes, requires `Ed25519PrivateKey`, and compares Raw bytes and display with the protected candidate. A missing artifact is rejected without transition; every other failure abandons the generation before READY. `restore-clear` removes a known-content slot, or moves a slot with unexpected content into quarantine.

## 8. Abandon and quarantine (N3)

`abandon` takes no argument and no passphrase. It writes the `ABANDONED` tombstone into the active directory when possible, moves `custody-v0` and any `restore-v0` as whole directories into the fixed `%LOCALAPPDATA%\WeaverForge\abandoned-v0` (created with the same atomic protected DACL, name never caller-selected), writes a `generation-<UTC>.abandoned` tombstone there, and leaves no active handoff. It makes no physical-erasure claim. The helper never reads quarantine contents. A new attempt starts only with `init`. Backup media of an abandoned generation stay secret-bearing until the Human reinitializes or destroys them with a media-appropriate procedure; they must never be reused as valid backups.

After READY (N2), ordinary failures abort without transition. The Human may still explicitly `abandon` a READY generation.

## 9. Loss and compromise

A backup known to have been intentionally destroyed may be replaced from a verified remaining copy under a later reviewed procedure. Any unknown-location, stolen, unexpectedly missing, or unaccounted backup medium is `SUSPECTED_COMPROMISE`, not ordinary loss: stop signing, isolate the signer host and all media, preserve only non-secret incident facts, and replace additively with a new key, a new additive admission snapshot, and a new two-phase admission act. A replacement never reuses or mutates the historical snapshot. The helper has no loss, replace, or recover command.

## 10. Check classification (N5)

| Checks | Classification |
|---|---|
| 1-29, 31, 33-40, 42, 44-46 | Machine-enforced by the helper and exercised by automated tests |
| 30 | Runbook declaration (no AI/agent/plugin/remote access); helper exposes no such surface (structural test) |
| 41 | Runbook rule `SUSPECTED_COMPROMISE`; helper exposes no loss/replace surface (structural test) |
| 43 | Structural: directories are created only by the helper with the SDDL at `CreateDirectoryW`; pre-existing directories are refused |
| 47 | Runbook declaration (password-manager entropy); helper enforces shape only |
| 48 | Documentation: observed encryption details are not an API guarantee (structural test) |
| 32 | Machine: no CONFIRM surface; outputs state `ADMISSION NOT_PERFORMED` |

## 11. Wording clarifications (N6, N7)

- The PBES2 / PBKDF2-SHA256 with 2048 iterations / AES-256-CBC construction is a source-observed detail of `BestAvailableEncryption` in `cryptography 50.0.2`. It is not an API guarantee, not a security-strength claim, and not an admission claim. The helper neither parses nor pins it.
- The OpenSSL 4.0.3 identity is the runtime backend version text of the reviewed wheel and is asserted by the helper; it is not taken from dependency-review prose.
- `RECORD` verification is against content derived from the reviewed hash-locked wheel artifacts, not merely against whatever is installed.
- N7 (rereview ordering wording in D1-R1) needs no action; the order was satisfied before the Freeze.

## 12. Residual limitations

- ACLs do not protect against same-user malware or administrators.
- Process memory holds the passphrase and key object; no zeroization guarantee.
- `.pyc` files listed in `RECORD` without hashes cannot be content-verified; a same-user attacker able to plant bytecode is outside the ACL boundary.
- The helper cannot distinguish the two physical backup media; the Human attests them.
- A wrong passphrase before READY abandons the generation (frozen fail-closed behavior).
- Interpreter provenance is unset by design until the PRE-REAL evidence is recorded and reviewed.

## Push status

NO. No public or remote push is authorized.
