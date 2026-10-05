# PRE-REAL Ed25519 Custody Execution Environment v0 - D0 / Readiness Design

Date:
2026-10-05

Status:
READY_FOR_ENVIRONMENT_PREPARATION

Scope:
PRE-REAL Ed25519 Custody Execution Environment v0

This document designs the smallest prerequisite scope that can establish whether this Windows host, account, and runtime satisfy the CLOSED Dedicated Local Software Ed25519 Custody Helper and Runbook v0 PRE-REAL conditions, while stopping before any real secret is read and before any real key is generated.

It does not authorize real key generation, create a passphrase, seed, or recovery secret, perform Admission PREPARE or CONFIRM, modify the CLOSED parent, invent a new digest or admission domain, or push.

## Closed parents

- Human Final: `fde7aa54feaa59bcbd37f4911a7de88135ccd2fd` (`HUMAN_REVIEW_ACCEPTED`)
- Fixed implementation: `d0aedb62904cb39c5cafa55a4b177b3154e420c7`
- Runbook commit: `40a00d4e12a6d617a0e897eddc527c0355349fda`
- Human Design Freeze: `77100848a4485955067b8a8433b987b646f3e140`
- Frozen D1-R1: `73942f18b5089c48795039d2fe8f24bf01b0c2f7`

Core question: can the exact host/account/interpreter/dependency/filesystem/console/operational environment required by the CLOSED custody profile be independently demonstrated to satisfy PRE-REAL prerequisites, while still stopping before any real secret is read or any real key is generated?

Observed on this host during D0 (read-only): Windows 11 Home 10.0.26200 amd64; account `DESKTOP-3LUK1NO\mine0` SID `S-1-5-21-3346865571-3074713094-1920152692-1001` is a member of `BUILTIN\Administrators` (`S-1-5-32-544`) and `S-1-5-114`; process is not elevated (`TokenElevation=0`) but `TokenElevationType=Limited(3)`; `ed25519_custody_v0.winsec.evaluate_account` returns `ACCOUNT_REJECTED`; `%LOCALAPPDATA%\WeaverForge` is absent; LocalAppData is on a fixed drive and reports not-in-sync-root; CPython 3.14.3 win-amd64 GIL is present under `%LOCALAPPDATA%\Python\pythoncore-3.14-64` with PSF publisher metadata and a python.org zip URL recorded in `__install__.json`; ambient site-packages still carry cryptography 50.0.1 / cffi 2.0.0; Microsoft Store `WindowsApps\python.exe` alias exists (0-byte stub) ahead on PATH.

Production CLI `preflight` was audited as read-only (no secret read, no directory create) via `cli.py:47` -> `manifest.run_preflight`, `custody.open_session`, `custody.phase_preflight` (`custody.py:267-271`). It was not executed: the ambient interpreter is not the isolated hash-locked dedicated venv, the current account is rejected, and `_INTERPRETER_PROVENANCE` is unset so every subcommand fails closed with `ENV_PROVENANCE_NOT_RECORDED` (`manifest.py:427-428`).

## Classification vocabulary

Each prerequisite is exactly one of:

- `MACHINE_VERIFIABLE_NOW`
- `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`
- `EXTERNAL_ARTIFACT_EVIDENCE_REQUIRED`
- `NOT_YET_SATISFIED`
- `OUT_OF_SCOPE`

## 1. Windows account

Frozen / implementation basis:

- D1-R1 requires a dedicated standard non-admin account before generation (D1 L382, L217).
- Runbook Human declarations require a dedicated standard non-administrator account (runbook L76).
- `winsec.evaluate_account` accepts only SID `S-1-5-21-*`, rejects elevated tokens, requires `TokenElevationType == Default(1)`, rejects impersonation, and rejects forbidden groups including `S-1-5-32-544` (Administrators) and `S-1-5-114` (`winsec.py:77-86,342-360`).

Distinction preserved (do not weaken):

- Membership in Administrators is rejected even when the process is not currently elevated.
- `TokenElevationType Limited` (split admin token) is rejected even when `TokenElevation` is false.
- A frozen-compliant configuration therefore requires a separate local standard user that is not in Administrators / Backup Operators / Server Operators / SERVICE, running with Default elevation type, non-impersonated.

Host observation: current development account is `ACCOUNT_REJECTED` for both Administrators membership and Limited elevation type.

Classification: `NOT_YET_SATISFIED` (separate standard local account required; current account unsuitable). Creating that account is Human operational work outside this D0 file edit.

## 2. Host / OS

Basis:

- Manifest requires `win32`, pointer size 8, `win-amd64` (`manifest.py:330-335`).
- Paths require plain absolute `X:\...` under known-folder LocalAppData, fixed drive, non-reparse ancestors, non-roaming, non-temp, non-sync, no `.git` ancestor (`paths.py:85-135,138-151`).
- Winsec rejects UNC final paths and requires create-new + protected DACL semantics on NTFS-capable local fixed volumes (`winsec.py:527-528,575-635`).

Machine-verifiable now (partial): OS is 64-bit Windows 11; LocalAppData drive type FIXED; sync-root HRESULT equals not-in-sync for LocalAppData; WeaverForge absent.

Operational-only: trusted/patched host, no remote-session control of the generation console, physical host custody.

Classification: host platform shape is `MACHINE_VERIFIABLE_NOW` for architecture/drive/sync-root/absence of custody root; patched/trusted/non-remote operational posture is `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`. Overall item readiness for real execution remains `NOT_YET_SATISFIED` until the standard account and remaining PRE-REAL items exist.

## 3. CPython provenance

Basis:

- Frozen pin: CPython 3.14.3 win_amd64 GIL (`manifest.py:27`; D1 L34,L76,L86; runbook L64).
- Reject Store/packaged path markers (`manifest.py:344-347`).
- `_INTERPRETER_PROVENANCE` must be a reviewed tuple of `(python.exe, sha256)` and `(python314.dll, sha256)`; currently `None` fails closed (`manifest.py:66-71,427-430`).
- Runbook requires official non-Store evidence: download source, installer/artifact filename, artifact SHA-256, Authenticode signer where applicable, then installed file hashes, then a separately reviewed change that sets `_INTERPRETER_PROVENANCE` (runbook L64; Human Final L49,L80).

Host observation: Python 3.14.3 amd64 GIL exists at `%LOCALAPPDATA%\Python\pythoncore-3.14-64` with publisher Python Software Foundation. `__install__.json` records official URL `https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.zip` and zip SHA-256 `ec781bb03f9638d136b24da7c83b4db1652ce767848aa856a30bb87cfdb1abe4`. Observed installed file SHA-256 (informational only; not yet frozen into the helper): `python.exe=CCE21C0E8710E304273E98AC4B2B0F5ACEB639ACBCD2343CBAA5C4E81619C45B`, `python314.dll=1AC15E2224581FC678BBD17728B9AA538D47B891B72C76499EF07E54CD74F151`. PATH still surfaces the Store alias stub first.

Evidence rules for PRE-REAL:

- Retain external release evidence for the exact python.org artifact actually installed (zip or installer), including published SHA-256.
- Distinguish artifact hash (download) from installed `python.exe` / `python314.dll` hashes.
- Do not treat a caller-selected path as authority: only `sys.base_prefix` files of the dedicated interpreter, matched to `_INTERPRETER_PROVENANCE`, count.
- Setting `_INTERPRETER_PROVENANCE` is a separately reviewed implementation change, not a D0 edit and not a self-ratifying host note.

Classification: `EXTERNAL_ARTIFACT_EVIDENCE_REQUIRED` plus `NOT_YET_SATISFIED` until evidence is retained and `_INTERPRETER_PROVENANCE` is set by reviewed change. Zip-versus-MSI packaging is an evidence-shape detail under D1's official-artifact rule, not a design conflict with the implementation's Store/path rejection.

## 4. Python runtime isolation

Basis:

- Dedicated venv, `include-system-site-packages = false`, version 3.14.3, isolated/`-I` flags, no user site, safe path, empty warn/xoptions, no debug flags (`manifest.py:350-376`; runbook L65-L66).
- Reject injection names starting with `PYTHON`, `OPENSSL`, `PIP_`, `CRYPTOGRAPHY`, `CFFI`, `SSL_CERT`, `WEAVERFORGE`, or containing `PASSPHRASE` (`manifest.py:63-64,361-364`).
- Module paths must resolve inside the dedicated site-packages; helper root only at the end of `sys.path` (`manifest.py:377-407`).
- No caller-selected runtime root (fixed by interpreter + helper layout; CLI accepts no path args: `cli.py:38-44`).

Required recorded evidence before PRE-REAL established:

- Absolute path of the dedicated venv and its `pyvenv.cfg` contents.
- Invocation shape: `<venv>\Scripts\python.exe -I <helper-root>\ed25519_custody_v0\__main__.py <subcommand>` (runbook L36-L37).
- Confirmation that ambient/user-site/Store alias interpreters are not used.

Classification: `NOT_YET_SATISFIED` (dedicated isolated venv not yet established for PRE-REAL). Machine checks exist in `manifest.evaluate` once that venv and provenance exist (`MACHINE_VERIFIABLE_NOW` as capability; not satisfied on this host now).

## 5. Dependency artifacts

Basis:

- Lock: `requirements/exact-bytes-witness-v0.txt` pins cryptography 50.0.2, cffi 2.1.1, pycparser 3.0 with wheel SHA-256 hashes; install only via `--require-hashes --only-binary :all:` (runbook L66; lock header).
- Runtime verifies installed RECORD content and `_RECORD_PINS` origin digests (`manifest.py:37-41,156-217,423-424`); OpenSSL backend text must be `OpenSSL 4.0.3 29 Sep 2026` (`manifest.py:28,425-426`).
- No dependency upgrade, no source build, no editable/direct_url (`manifest.py:410-420`).

Required locally retained evidence:

- The frozen requirements file bytes as committed.
- Optionally retained copies of the exact wheels whose SHA-256 match the lock (recommended operational hygiene; runtime pins RECORD-origin digests derived from those wheels).

Host observation: ambient cryptography 50.0.1 / cffi 2.0.0 are unacceptable (D1 L40; manifest version pins).

Classification: lock content is `MACHINE_VERIFIABLE_NOW` in-repo; a PRE-REAL dedicated install is `NOT_YET_SATISFIED`. Wheel retention is `EXTERNAL_ARTIFACT_EVIDENCE_REQUIRED` when proving install reproducibility offline.

## 6. Console / secret-input preflight

Basis:

- All enforceable console checks run before any secret read (`console.py:1-8,123-155`; D1 L136-L148).
- Requires original stdin/stderr, character device, console modes on stdin/stderr/CONIN$/CONOUT$, empty warnoptions, and `getpass.win_getpass` (`console.py:108-120`).
- `GetPassWarning` must be configured as error before read (`console.py:145-148`).
- Absence of AI/agent/IDE capture/ConPTY/recorder/transcript is Human declaration only (console module docstring; runbook L72-L78; D1 L148).
- Clipboard/recording disablement remains runbook (`runbook L78`).

Classification: console handle/mode/getpass checks are `MACHINE_VERIFIABLE_NOW` at execution time on the intended console; AI/agent/ConPTY/clipboard/recording absence is `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`. No secret may be read to "test" this during PRE-REAL establishment beyond optional non-secret dry console probes that never call `read_secret`.

## 7. Custody root

Basis:

- Fixed root `%LOCALAPPDATA%\WeaverForge` (`paths.py:20-23,138-151`; runbook L97).
- Production must not exist before `init`; D0 must not create it (this batch constraint; runbook creation happens only in later authorized `init`).
- Creation-time protected DACL is enforced at `CreateDirectoryW` (`winsec.py:575-590`) when `init` later runs; D0 prefers non-destructive evidence: absence check + LocalAppData validation.

Host observation: WeaverForge absent (`MACHINE_VERIFIABLE_NOW`).

Classification: absence and location rules `MACHINE_VERIFIABLE_NOW`; real directory creation is `OUT_OF_SCOPE` for this D0 batch.

## 8. Windows ACL / security identity

Basis:

- Protected SDDL: owner = intended user SID; DACL protected; SYSTEM + user FA with OICI (`winsec.py:433-453,575-590`).
- Files inherit only (`evaluate_file_acl`, `winsec.py:456-463`); verify before secret write (`winsec.py:606-635`).
- Elevation/impersonation rejection as in item 1.
- ACLs do not defeat same-user compromise (package docstring; D1 L190).

Safe pre-creation evidence: token SID, elevation facts, group SIDs of the intended standard account; SDDL string template with that SID. Do not create WeaverForge in D0.

Classification: identity/elevation checks `MACHINE_VERIFIABLE_NOW` on the intended account once it exists; directory ACL proof after creation is deferred to later authorized `init` (`OUT_OF_SCOPE` for destructive proof in D0). Currently `NOT_YET_SATISFIED` because the intended standard account does not exist.

## 9. Sync / indexing / VSS / File History / endpoint

Basis:

- Helper machine-rejects known sync roots/components and cloud-files sync API results (`paths.py:26-28,111-117,134-135`).
- Runbook requires Human declaration that VSS, File History, indexing, sync, and endpoint upload are excluded for WeaverForge (runbook L80; D1 L219).
- Helper must not claim those operational absences as machine-proven (runbook L83; D1 L219).

Classification: path/sync-root API subset `MACHINE_VERIFIABLE_NOW`; VSS/File History/indexing/endpoint exfiltration absence `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`.

## 10. Backup media preconditions

Basis:

- Two offline controlled media; pretest format/write/read non-secret file; no cloud sync; byte equality with working container is a runbook step (runbook L94-L105; D1 L254-L267).
- No backup or private artifact creation in this D0.

Classification: media selection/pretest readiness `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`; physical custody `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`; artifact creation `OUT_OF_SCOPE` now. Overall `NOT_YET_SATISFIED` until Human media pretest is recorded for the later generation authorization.

## 11. Password manager / passphrase precondition

Basis:

- Password-manager-generated unique secret with >=128 bits reported entropy; Human-composed forbidden (D1 L134,L154,L449; runbook L87,L135).
- Helper enforces shape only: 24..128 printable ASCII (`console.py:22-23,158-168`); length alone does not prove entropy (Human Final / review nonmaterial honesty; runbook L87).

Classification: password-manager readiness and entropy declaration `HUMAN_OPERATIONAL_ATTESTATION_REQUIRED`. Real passphrase creation `OUT_OF_SCOPE` / forbidden now (`NOT_YET_SATISFIED` as a later-generation precondition, not as a D0 deliverable).

## 12. Test versus PRE-REAL separation

Basis:

- Runbook L62: automated tests and temporary test venv are not the PRE-REAL environment.
- Human Final explicit boundary: `TEST SUCCESS != PRE-REAL ENVIRONMENT ESTABLISHED`.
- Manifest docstring: passing tests does not establish PRE-REAL (`manifest.py:1-9`).
- Test harness replaces `_location_context`, stubs `run_preflight`, and uses tmp paths (`ed25519_custody_v0/tests/conftest.py`).

Classification: separation rule is closed and `MACHINE_VERIFIABLE_NOW` as a documentation/process invariant. No test artifact may satisfy real-key prerequisites (`OUT_OF_SCOPE` to promote tests).

## 13. Evidence record (origin-neutral proposal)

Propose the smallest PRE-REAL readiness evidence as a future documentation-only checklist (not created by this D0 as an authority object), recording only non-secret facts:

1. Host identifiers sufficient for staleness (OS build, machine name) without identity/role claims.
2. Intended standard-account SID and confirmation it passes `evaluate_account`.
3. External python.org artifact URL, filename, published SHA-256 (and Authenticode evidence if an installer EXE is used).
4. Installed `python.exe` and `python314.dll` SHA-256 values intended for `_INTERPRETER_PROVENANCE`.
5. Dedicated venv path, `pyvenv.cfg` digest or exact text, and lock-file commit hash used for `--require-hashes` install.
6. Wheel SHA-256 list matching `requirements/exact-bytes-witness-v0.txt` (or retained wheel files).
7. Human operational attestation list (AI/agent/ConPTY/clipboard/VSS/File History/indexing/sync/endpoint; password-manager readiness; backup media pretest labels).

Constraints:

- The checklist must not grant authority, trust, identity, role, Admission, or key-generation permission.
- Caller-controlled free text must not self-ratify readiness: machine gates remain `manifest.evaluate`, `winsec.check_account`, `paths.resolve`, and `console.console_preflight`.
- Setting `_INTERPRETER_PROVENANCE` requires a separately reviewed code change; this D0 does not invent a new digest domain or admission snapshot. If an additive cryptographic domain were demanded beyond that reviewed pin, STOP as prerequisite rather than inventing one.

Classification of the proposal itself: `NOT_YET_SATISFIED` until filled; mechanism is documentation + reviewed provenance pin, not a new trust object.

## 14. Failure / staleness

PRE-REAL evidence MUST be considered stale and re-established when any of the following change:

- Interpreter install path, `python.exe` / `python314.dll` hashes, or CPython version/build.
- Dedicated venv recreation, `pyvenv.cfg`, site-packages contents, RECORD pins, wheel hashes, or OpenSSL backend text.
- Intended account SID, group membership, elevation type, or impersonation state.
- OS build/security configuration material to local fixed-disk custody, or LocalAppData relocation/redirection.
- Custody-path state (unexpected creation/population of WeaverForge before authorized `init`, sync-root changes, reparse introduction).
- Helper package bytes or lock-file bytes used for the PRE-REAL install.
- Console host topology if the Human attestation basis changed (new remote/IDE/agent attachment model).

Do not claim permanent currentness. Helper runtime re-checks machine gates on every process; Human attestations must be reaffirmed when stale.

## 15. Final gate vocabulary

Exact results for a later PRE-REAL establishment attempt:

- `PRE_REAL_READY_FOR_SEPARATE_HUMAN_GENERATION_AUTHORIZATION`
- `PRE_REAL_NOT_READY`

Binding rule: READY does not authorize generation. Real key generation still requires a separate Human authorization after PRE-REAL is established (Human Final L80; runbook L9-L10,L20).

Also keep closed negatives true until that later authorization:

- `PRE_REAL_ENVIRONMENT_ESTABLISHED: NO` (this D0)
- `REAL_KEY_GENERATION_AUTHORIZED: NO`
- `REAL_KEY_GENERATED: NO`
- `REAL_PASSPHRASE_CREATED: NO`
- `ADMISSION_PERFORMED: NO`

## Design conflict check

No material conflict found between frozen D1-R1 / Freeze / runbook / Human Final and implementation `ed25519_custody_v0` that would require broadening or weakening. Account rejection of Administrators and Limited elevation type matches the dedicated standard-account rule. Provenance unset matches fail-closed PRE-REAL. Zip-based official python.org install is an evidence packaging detail under the official-artifact rule, not an implementation contradiction.

## Next minimal actions (Human / later reviewed work)

1. Create or designate a dedicated local standard (non-Administrators) account and verify `evaluate_account` accepts it.
2. Retain python.org artifact evidence; confirm installed interpreter file hashes; prepare a separately reviewed change to set `_INTERPRETER_PROVENANCE` (do not set it in this D0).
3. From that interpreter, create a dedicated venv with `include-system-site-packages=false`; install only the frozen lock with `--require-hashes --only-binary :all:`; keep wheels as needed.
4. Clear injection environment variables; plan `-I` invocation; ensure Store alias is not the selected interpreter.
5. Record Human operational attestations (console/AI/clipboard/VSS/File History/indexing/sync/endpoint; password-manager readiness; backup media pretest) without creating secrets or WeaverForge.
6. Only after the above: a separate Human generation authorization may be considered. Not authorized now.

## Explicit non-authorization

This D0 does not authorize PRE-REAL establishment completion, real key generation, Admission, signing, identity/role/trust semantics, or push.
