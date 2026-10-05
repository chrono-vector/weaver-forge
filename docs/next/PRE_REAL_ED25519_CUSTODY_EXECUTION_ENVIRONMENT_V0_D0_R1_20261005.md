# PRE-REAL Ed25519 Custody Execution Environment v0 - D0-R1

Date:
2026-10-05

Status:
PREREQUISITE_REQUIRED

Scope:
PRE-REAL Ed25519 Custody Execution Environment v0 (D0-R1 document-only remediation)

This D0-R1 supersedes the original D0 for operational use. It does not edit, delete, or rebase that file. It does not install Python, create or change accounts, create a venv, edit CLOSED helper code, generate secrets or keys, perform Admission, invent a new digest or Admission domain, or push.

## Supersession

Original D0 (superseded for operational use; retained as historical):

- path: `docs/next/PRE_REAL_ED25519_CUSTODY_EXECUTION_ENVIRONMENT_V0_D0_20261005.md`
- commit: `ee401fe3fe9572346996ac3df03b90bc630d8fcd`
- SHA-256: `EF14F4217720A100C3C1C83D94811928D812D32A7B4FDFFABCCEABB7D7C219B3`
- prior self-assigned status `READY_FOR_ENVIRONMENT_PREPARATION` is withdrawn for operational planning

Closed parents (unchanged):

- Human Final: `fde7aa54feaa59bcbd37f4911a7de88135ccd2fd` (record SHA-256 `1FE9A304224115A64B9E6CCBE33E820EB3A61081705BABA083DC590379D7DEAB`)
- Fixed implementation (immutable historical Human Final): `d0aedb62904cb39c5cafa55a4b177b3154e420c7`
- Runbook: `40a00d4e12a6d617a0e897eddc527c0355349fda`
- Freeze: `77100848a4485955067b8a8433b987b646f3e140` (SHA-256 `E1D3CEFCCDA3D1645F9FF7BA403AF0B7304C84C17DB56A8F62189DFAC97DA1D3`)
- D1-R1: `73942f18b5089c48795039d2fe8f24bf01b0c2f7` (SHA-256 `B788A240989F00A01844692C6B714E1106F936D1220C9E79AB67173DDEB01791`)

Human direction for this batch: later interpreter acquisition must follow the official python.org CPython 3.14.3 amd64 EXE installer path (runbook L64; D1 L74-76). ZIP / PythonManager is not an accepted deviation.

## Closure map (adversarial findings -> D0-R1)

| Finding | Closed in |
|---|---|
| M1 READY derivation / self-ratification | Section B; Section K |
| M2 provenance claims exceed evidence; ZIP/PythonManager rejected | Section C; host observations corrected below |
| M3 helper root / code bytes unbound | Section E |
| M4 pin requires additive CLOSED amendment | Section F; Section A |
| N1 local non-roaming profile; MSA; domain RIDs; same SID; readable protected interpreter | Section D |
| N2 pip `--isolated --no-deps` | Section G |
| N3 staleness gaps | Section I |
| N6 lowercase hex for pin | Section C; Section F |
| N11 ordering: amendment gate, final check, init timing | Section J |

## Corrected host observations (development host only; not PRE-REAL)

Independently re-checked read-only on this machine for D0-R1 (do not treat as readiness):

- Store-signed `PythonSoftwareFoundation.PythonManager` 26.3.240.0 is installed under `C:\Program Files\WindowsApps\...`. The `WindowsApps\python.exe` entry is an App Execution Alias surface for that manager, not merely a "0-byte Store stub" as original D0 L26/L81 described.
- The observed interpreter under `%LOCALAPPDATA%\Python\pythoncore-3.14-64` was acquired via that manager / ZIP channel (`__install__.json` records `python-3.14.3-amd64.zip`). That channel is rejected for PRE-REAL under Human direction and runbook L64.
- That tree is a modified development interpreter: independently counted 251 entries under base `Lib\site-packages` and 29 under `Scripts`. ACL allows only `SYSTEM`, `Administrators`, and `mine0` (a dedicated standard account cannot read it).
- Current account `mine0` remains `ACCOUNT_REJECTED` (Administrators / S-1-5-114; Limited elevation) and carries Microsoft Account SIDs `S-1-11-96-*` and cloud-account authentication `S-1-5-64-36`.
- `%LOCALAPPDATA%\WeaverForge` remains absent.
- `C:\dev` and inherited `ed25519_custody_v0\` grant `Authenticated Users` Modify, so any local authenticated account can edit helper sources including a future pin.

These facts motivate remediation. They do not satisfy PRE-REAL.

## A. Status

Narrowest honest status: `PREREQUISITE_REQUIRED`.

Reasons:

1. Production preflight cannot succeed until `_INTERPRETER_PROVENANCE` is set (`cli.py:47` -> `manifest.run_preflight` -> `manifest.py:427-428` `ENV_PROVENANCE_NOT_RECORDED`).
2. Setting that pin is a separately authorized additive amendment with its own Human Final (Section F), not ordinary "environment preparation".
3. Until that amendment Human Final exists, the Section B READY derivation is unreachable, so `READY_FOR_ENVIRONMENT_PREPARATION` was premature.

Limited planning allowed by D0-R1: account policy, official EXE evidence plan, amendment-scope definition, ordering, and attestation/staleness rules. No preparation step that installs Python, creates accounts, creates venvs, or edits CLOSED code is authorized by this document.

## B. READY derivation (no caller boolean)

`PRE_REAL_READY_FOR_SEPARATE_HUMAN_GENERATION_AUTHORIZATION` is DERIVED only. It is never accepted from a checklist checkbox, caller field, chat claim, or D0 narrative.

Derivation rule: EVERY predicate below must be independently established as PASS at recomputation time. Any missing, unknown, stale, or FAIL predicate yields `PRE_REAL_NOT_READY`. No missing/unknown predicate may be treated as PASS.

### B1. Binding predicates

1. Authoritative helper bytes equal the reviewed additive successor commit that includes the accepted interpreter-provenance pin amendment (not `d0aedb6` in-place; not an uncommitted tree).
2. Authoritative helper working copy is clean relative to that commit, or an independently verified read-only/protected copy of those exact bytes is used.
3. Helper-root ACL/protection prevents the execution account from modifying helper sources beyond frozen policy (addresses observed `Authenticated Users:(M)` on `C:\dev` / package).
4. Execution uses that bound helper root; no alternate caller-selected root.

### B2. Account / profile predicates

5. Dedicated local standard non-admin account; SID matches frozen `evaluate_account` acceptance (`winsec.py:342-360`).
6. Not a member of forbidden groups including Administrators / S-1-5-114 / Backup Operators / Server Operators / SERVICE; domain RIDs 512/518/519 rejected (`winsec.py:77-86,358`).
7. Non-elevated; `TokenElevationType == Default(1)`; non-impersonated (`winsec.py:349-354`).
8. Local non-roaming, non-redirected profile: known-folder LocalAppData equals `Profile\AppData\Local` (`paths.py:94-98`; D1 redirected/roaming rejection).
9. Same account SID is used for every custody phase of the generation.

### B3. Interpreter / provenance predicates

10. Interpreter acquired only via official python.org `python-3.14.3-amd64.exe` (Section C). ZIP/PythonManager/Store packaged channels FAIL.
11. External installer evidence retained and independently verified (artifact SHA-256, available official provenance such as sigstore/sig/crt as published, Authenticode signer).
12. Installed `python.exe` / `python314.dll` lowercase SHA-256 match the Human-Final-accepted `_INTERPRETER_PROVENANCE` pin values.
13. Base_prefix content manifest shows no unexpected `Lib\sitecustomize.py` / customization / unexpected site-packages pollution relative to a clean official EXE install.
14. Exact version/architecture/GIL match frozen pins (`manifest.py:27,330-342`).
15. PATH / Store alias ambiguity rejected: the dedicated interpreter is selected by absolute path, not via WindowsApps alias.

### B4. Amendment / runtime / dependency predicates

16. Pin-amendment Human Final accepted; successor commit fixed (Section F).
17. Dedicated venv created FROM THAT ACCOUNT'S OWN verified interpreter (not mine0's private tree); `include-system-site-packages=false`; isolated invocation `-I`.
18. Dependencies installed only with runbook command shape including `--isolated --no-deps --require-hashes --only-binary :all:` (runbook L66); wheel artifact hashes verified; installed RECORD/content and `_RECORD_PINS` match (`manifest.py:156-217,423-424`).
19. OpenSSL backend text matches frozen expectation (`manifest.py:28,425-426`).
20. Injection variable rejection and module-path checks pass (`manifest.py:361-407`).

### B5. Preflight / custody / operational predicates

21. Actual production `preflight` executed as the intended account, using the bound helper, dedicated venv `-I` interpreter, and intended console, returning the exact success lines from `custody.phase_preflight` after `manifest.run_preflight` and `open_session` succeed (`cli.py:47-49`; `custody.py:267-271`).
22. Custody-root preconditions: WeaverForge absent before authorized `init`; LocalAppData location rules pass; DACL template/account SID ready. `init` itself is NOT part of PRE-REAL establishment and must not run until after separate Human real-key-generation authorization (Section J).
23. Current Human operational attestations within expiry (Section H/I).
24. Backup-media pretest readiness and password-manager readiness attested (no real secret created).
25. Independent recomputation of all predicates immediately before any later generation-authorization decision.

Checklist items may assist Humans in gathering evidence. They never set READY.

## C. Interpreter path (official EXE only)

Accepted later-preparation direction (Human-authorized for planning only):

- Artifact: official python.org CPython 3.14.3 Windows amd64 EXE installer `python-3.14.3-amd64.exe` (runbook L64; D1 L74-76).
- Rejected for PRE-REAL: Microsoft Store packaging, `PythonSoftwareFoundation.PythonManager`, ZIP embeds such as `python-3.14.3-amd64.zip`, and any `__install__.json` / install-manager local metadata presented as provenance.

Evidence model (each layer distinct; none alone suffices):

1. Installer artifact identity (filename, download URL from python.org release evidence).
2. Independent SHA-256 of the EXE bytes; plus available official provenance files published beside it (for example `.sigstore` / `.sig` / `.crt` / `.spdx` as published for that release).
3. Authenticode signer verification of the EXE.
4. After clean install into a location readable by the dedicated standard account: SHA-256 of installed `python.exe` and `python314.dll` as lowercase hex (Python `hashlib.sha256(...).hexdigest()` form). Uppercase hex MUST NOT be written into `_INTERPRETER_PROVENANCE` or comparison will `ENV_PROVENANCE_MISMATCH` (`manifest.py:133-138,429-430`).
5. Base_prefix content manifest sufficient to detect unexpected `Lib\sitecustomize.py`, unexpected site-packages, or other customization. Note: runtime pin covers only `python.exe` and `python314.dll` (`manifest.py:71,269-274`); `site` may still import `sitecustomize` under `-I` if present. Clean-install hygiene and manifest inspection are therefore mandatory operational controls complementary to the pin.
6. Exact version/architecture/GIL.
7. Rejection of PATH/Store alias ambiguity.

Do not claim that hashing currently installed files under the PythonManager/ZIP tree proves EXE installer provenance. Do not use mine0-only ACL trees as the dedicated account's interpreter.

## D. Standard account

Required for PRE-REAL and later generation:

- Dedicated local standard user (non-Administrators), preferably a local non-Microsoft-Account principal (avoid MSA SID families such as `S-1-11-96-*` / cloud authentication `S-1-5-64-36` observed on mine0).
- Stable SID recorded; same SID for all custody phases.
- Local, non-roaming, non-redirected profile so `LocalAppData == Profile\AppData\Local` (`paths.py:94-98`).
- Passes `evaluate_account` including Default elevation type and forbidden group/RID checks (`winsec.py:342-360,86`).
- Can read its own official-EXE interpreter, dedicated venv, and protected authoritative helper copy; those trees must not depend on mine0-only ACLs.

Current mine0 observations are development-host facts only and cannot satisfy PRE-REAL.

## E. Helper root / code binding

Problem confirmed:

- Helper root is whatever directory contains the executed `ed25519_custody_v0` package. `__main__.py` appends its parent onto `sys.path` (`ed25519_custody_v0/__main__.py:12-17`).
- `manifest.py:304,387-395` only checks self-consistency of that loaded helper against `sys.path`; it does not verify helper bytes against a reviewed commit.
- Therefore original D0 L99 "no caller-selected runtime root" was incorrect: choosing which tree to invoke selects the root.
- Observed ACL: `Authenticated Users` Modify on `C:\dev` inherited into `ed25519_custody_v0\`, so an uncommitted edit (including a forged pin) can pass its own preflight.

PRE-REAL requirements:

1. Bind execution to exact reviewed additive successor commit/file hashes after pin-amendment Human Final.
2. Use a clean worktree of that commit or an independently verified read-only/protected copy of those bytes.
3. Helper-root ACL/protection: the execution account must not be able to modify helper sources (remove inherited Authenticated Users Modify from the authoritative copy; prefer read/execute for the execution account).
4. No uncommitted edits in the authoritative copy.
5. No caller-selected alternate root: invocation documentation must name the bound path; verification must re-hash helper files against the reviewed commit, not trust Git status alone as authority.

Git is evidence of intended bytes when the object store and clean tree are independently verified; Git alone does not create trust.

## F. Pin amendment (CLOSED boundary)

Explicit statements:

1. CLOSED implementation `d0aedb62904cb39c5cafa55a4b177b3154e420c7` remains immutable historical Human Final ("accepted as-is": Human Final L16-17). It must NOT be edited, rebased, or reinterpreted in place.
2. A separate additive bounded scope is required, tentatively named: `Ed25519 Custody Helper v0 Interpreter Provenance Pin Amendment`.
3. That amendment must have its own design/fixed evidence, implementation and test changes, independent review, Human Final, and new fixed successor commit.
4. Likely touched semantics: `manifest.py` `_INTERPRETER_PROVENANCE` (and only as needed for lowercase pin tuple of `python.exe` / `python314.dll`); tests such as `test_x07` which currently asserts `_INTERPRETER_PROVENANCE is None` (`test_custody_supplementary.py:242`); mutation `M15i` which removes the unset-provenance fail-closed (`mutation_campaign_v0.py:210-212`).
5. No environment variable, config file, or CLI override may supply the pin.
6. PRE-REAL completion (Section B predicate 16 and production preflight success) depends on that amendment Human Final. Until then, status remains `PREREQUISITE_REQUIRED` / `PRE_REAL_NOT_READY`.

## G. Venv / dependencies

Later venv creation only after: dedicated account exists, official EXE interpreter is installed for that account/environment, and pin-amendment Human Final exists (so production preflight can possibly succeed).

Rules:

- Create the venv from the dedicated account's own verified interpreter absolute path.
- `include-system-site-packages = false`.
- Install only: `python -m pip --isolated install --no-deps --require-hashes --only-binary :all: -r requirements/exact-bytes-witness-v0.txt` (runbook L66; D1 L74).
- Distinguish wheel artifact SHA-256 verification (lock file) from installed RECORD/content and `_RECORD_PINS` verification (`manifest.py:156-217`).
- No source builds, editable installs, extra packages, or `.pth` additions.
- No test venv or review temp venv may be promoted to PRE-REAL.

## H. Operational attestations

Human declarations cover operational facts the helper cannot prove (AI/agent/IDE/ConPTY/recorder absence; clipboard; VSS/File History/indexing/sync/endpoint exclusion; password-manager readiness; backup media pretest; trusted/patched host).

They are inputs only. They are NOT machine proof, NOT Human Final, NOT authority/trust/identity/role, NOT Admission, and NOT sufficient alone for READY.

Attestations must be session-scoped and time-bounded with explicit expiry (Section I). Expired or basis-changed attestations force `PRE_REAL_NOT_READY` until renewed.

## I. Staleness

Any material change forces `PRE_REAL_NOT_READY` until full recomputation, including at least:

- Helper amendment commit / package bytes; runbook / D1 / Freeze / Human Final / lock-file bytes
- Helper-root ACL/protection state
- Interpreter installer artifact evidence; installed `python.exe`/`python314.dll` hashes; full base_prefix manifest (stdlib/DLLs/sitecustomize/site-packages)
- PythonManager or other auto-update channels if present on the host (must not regain control of the PRE-REAL interpreter)
- Venv/`pyvenv.cfg`/site-packages/RECORD/OpenSSL backend text
- Account SID/groups/elevation/impersonation/profile redirection
- OS build/security configuration; LocalAppData; custody-root existence/reparse/sync-root state
- Per-session console conditions (handles/modes/attachment model)
- Operational attestations age/expiry and their factual basis
- Backup media status; password-manager readiness
- Time-bounded reconfirmation immediately before generation-authorization

Do not claim permanent currentness.

## J. Safe order

Document-only sequence (no step authorizes the next's irreversible actions without its own Human gate):

1. D0-R1 document-only remediation (this file).
2. Separate Human authorization for account and official-EXE evidence preparation planning.
3. Create dedicated local standard account (local/non-roaming profile).
4. Obtain official `python-3.14.3-amd64.exe` evidence; clean-install for that account/environment into an ACL-readable location; reject ZIP/PythonManager.
5. Pin amendment design -> implementation/tests -> independent review -> Human Final -> fixed successor commit (additive; do not edit `d0aedb6`).
6. Place protected authoritative helper successor (clean tree or verified copy; fix helper-root ACL).
7. From THAT account's verified interpreter: dedicated venv; `--isolated --no-deps --require-hashes --only-binary :all:` install; wheel and RECORD verification.
8. Injection/path/module checks.
9. Current operational attestations (within expiry).
10. Custody path/DACL readiness checks without creating secrets; WeaverForge must still be absent.
11. Backup media pretest readiness; password-manager readiness (no real secret).
12. Actual production `preflight` in intended account/runtime/console (must succeed only after amendment).
13. Independent final PRE-REAL recomputation of Section B predicates.
14. Separate Human real-key-generation authorization.
15. Only then: real passphrase handling, `init`/`generate`, backups, and later Admission acts under their own frozen procedures.

`init` and any secret-reading phase are after step 14, not part of PRE-REAL establishment.

## K. Result vocabulary

- `PRE_REAL_READY_FOR_SEPARATE_HUMAN_GENERATION_AUTHORIZATION` - only if Section B derivation passes at recomputation time.
- `PRE_REAL_NOT_READY` - default whenever any predicate is missing, unknown, stale, or failed.

READY does not authorize generation.

Until pin-amendment Human Final and the rest of Section B: treat the environment as `PRE_REAL_NOT_READY` and this scope status as `PREREQUISITE_REQUIRED`.

Closed negatives remain:

- `PRE_REAL_ENVIRONMENT_ESTABLISHED: NO`
- `REAL_KEY_GENERATION_AUTHORIZED: NO`
- `REAL_KEY_GENERATED: NO`
- `REAL_PASSPHRASE_CREATED: NO`
- `ADMISSION_PERFORMED: NO`

## Recommended next scope

`Ed25519 Custody Helper v0 Interpreter Provenance Pin Amendment` (design first; then implementation only after its own authorization). Parallel Human planning for the dedicated standard account and official EXE evidence may proceed only under separate Human authorization and must not edit CLOSED code or claim PRE-REAL.

## Explicit non-authorization

This D0-R1 does not authorize Python installation, account changes, venv creation, CLOSED edits, WeaverForge creation, real secrets/keys, Admission, identity/role/trust semantics, or push.
