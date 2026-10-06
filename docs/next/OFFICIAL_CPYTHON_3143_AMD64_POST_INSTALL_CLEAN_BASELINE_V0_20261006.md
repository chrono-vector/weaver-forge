# Official CPython 3.14.3 amd64 Post-Install Clean Baseline v0

## Record status

- Status: `POST_INSTALL_BASELINE_CAPTURED_PENDING_ACL_GATE`
- Record date: `2026-10-06` (Asia/Tokyo)
- Base HEAD: `f2cf5f5edccc00cbc6f27aa22f47f1737c3d1dfa`
- Scope: privileged installation of the already admitted official CPython 3.14.3 amd64 EXE, followed immediately by clean base-prefix capture and a minimal isolated runtime identity check.
- This record does not establish the final interpreter-provenance pin values or the pre-real environment. The dedicated custody execution account and its effective ACL proof remain unresolved.

## Design and evidence basis

- Evidence Preparation D0 commit: `7b77fb3454d7cc7582bfe7a7a9a692f37127c9e4`
- Evidence Preparation D0-R1 commit: `964da7d1d73216c6a3d6bd3cf7aa15936a0e93ce`
- Frozen Interpreter Provenance Pin Amendment D1 commit: `f392778c644803791310c722af373e3ec0981885`
- Human Design Freeze save commit: `a80501f354a9766665477c74566e8ec881f9dd0a`
- Pre-install evidence gate commit / base HEAD: `f2cf5f5edccc00cbc6f27aa22f47f1737c3d1dfa`

## Pre-execution recheck

- Installer: `C:\Users\mine0\Downloads\weaver-evidence\cpython-3.14.3-amd64-20261005\python-3.14.3-amd64.exe`
- Filename: `python-3.14.3-amd64.exe`
- Size: `30213192` bytes
- SHA-256: `b68ad91421afbbd1a628105199c8c5f6179b21ba799067a8d8c0bbac3b7defb0`
- SHA-256 matched the pre-install evidence gate: `YES`
- Authenticode status: `Valid`
- Authenticode result matched the pre-install evidence gate: `YES`
- Target root immediately before execution: `ABSENT`

## Exact frozen invocation

The installer was launched elevated with this exact argument vector:

```text
/quiet
/log C:\ProgramData\WeaverForge\Evidence\CPython3143\install.log
InstallAllUsers=1
TargetDir=C:\Program Files\WeaverForge\Python314
AssociateFiles=0
CompileAll=0
PrependPath=0
AppendPath=0
Shortcuts=0
Include_doc=0
Include_debug=0
Include_dev=1
Include_exe=1
Include_freethreaded=0
Include_launcher=0
InstallLauncherAllUsers=0
Include_lib=1
Include_pip=1
Include_symbols=0
Include_tcltk=0
Include_test=0
Include_tools=1
LauncherOnly=0
SimpleInstall=0
```

- Elevated identity: `DESKTOP-3LUK1NO\mine0`
- Administrative token: `TRUE`
- Installer start UTC: `2026-10-06T02:18:04.1111145Z`
- Installer end UTC: `2026-10-06T02:18:21.5749631Z`
- Exit code: `0`
- Restart required: `NO`
- Installed root: `C:\Program Files\WeaverForge\Python314`
- Installer log: `C:\ProgramData\WeaverForge\Evidence\CPython3143\install.log`
- Installer log SHA-256: `6ab8cbd49a186b0bfed050d6f6e6f726fbe88cf88a95bea3af11e6a7c828a8e3`

## Immediate clean baseline

- Capture interval UTC: `2026-10-06T02:22:06.3452319Z` through `2026-10-06T02:22:13.7388679Z`
- Canonical manifest format: `cp314-base-prefix-manifest-v0`
- Entry count: `1941`
- Baseline digest: `ee89d06739fcf935ad5d2608879261971945ebbd1f379aec4dcf199457d861d4`
- Startup customization paths found (`sitecustomize.py`, `usercustomize.py`, `.pth`, `._pth`): `0`
- Reparse-point, canonical-path collision, non-ASCII path, or alternate-data-stream issue: `NONE OBSERVED`
- Full tree stable across the capture: `YES`
- Process executing from the installation root before capture: `NONE OBSERVED`

No installed interpreter was executed before this baseline was captured. Between installer completion and the successful capture, only read-only PowerShell inspection was performed. One initial capture command failed during PowerShell parsing before manifest-row generation; it performed no installation-root write. The corrected capture then completed over a stable tree.

## Installed artifacts

- `python.exe` size: `106328` bytes
- `python.exe` SHA-256: `cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b`
- `python314.dll` size: `6753112` bytes
- `python314.dll` SHA-256: `1ac15e2224581fc678bbd17728b9aa538d47b891b72c76499ef07e54cd74f151`

## Minimal isolated runtime identity check

After baseline capture, the absolute installed interpreter was invoked once with `-I -S -B -c` to emit fixed identity facts. It reported:

- Version: `3.14.3 (tags/v3.14.3:323c59a, Feb  3 2026, 16:04:56) [MSC v.1944 64 bit (AMD64)]`
- `sys.version_info`: `[3, 14, 3, "final", 0]`
- Implementation / cache tag: `cpython` / `cpython-314`
- Architecture: `64-bit`, `AMD64`, `win-amd64`, little-endian
- GIL enabled: `TRUE`
- `sys.executable`: `C:\Program Files\WeaverForge\Python314\python.exe`
- `sys.prefix`, `sys.base_prefix`, `sys.exec_prefix`, and `sys.base_exec_prefix`: `C:\Program Files\WeaverForge\Python314`
- Isolation flags: `isolated=1`, `no_site=1`, `dont_write_bytecode=1`
- Import path was limited to the installed root ZIP, `DLLs`, `Lib`, and root.

An independent full-tree re-read after that invocation produced `1941` entries and the unchanged digest `ee89d06739fcf935ad5d2608879261971945ebbd1f379aec4dcf199457d861d4`. The `python.exe` and `python314.dll` hashes were also unchanged.

## ACL evidence and unresolved gate

- Root owner: `NT AUTHORITY\SYSTEM`
- Root SDDL:

```text
O:SYG:SYD:AI(A;ID;FA;;;S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464)(A;CIIOID;GA;;;S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464)(A;ID;FA;;;SY)(A;OICIIOID;GA;;;SY)(A;ID;FA;;;BA)(A;OICIIOID;GA;;;BA)(A;ID;0x1200a9;;;BU)(A;OICIIOID;GXGR;;;BU)(A;OICIIOID;GA;;;CO)(A;ID;0x1200a9;;;AC)(A;OICIIOID;GXGR;;;AC)(A;ID;0x1200a9;;;S-1-15-2-2)(A;OICIIOID;GXGR;;;S-1-15-2-2)
```

The installer-created ACL grants full control to TrustedInstaller, SYSTEM, and Administrators and read/execute access to ordinary Users and application-package principals. No dedicated standard non-admin custody execution account has yet been frozen or created, so effective-right verification for that exact account cannot be completed. ACL evidence status is therefore `PENDING_ACCOUNT_ACL_GATE`. No account or ACL was changed in this batch.

## External evidence objects

External evidence directory (not committed):
`C:\Users\mine0\Downloads\weaver-evidence\cpython-3.14.3-amd64-postinstall-20261006-v0`

| Object | Bytes | SHA-256 |
|---|---:|---|
| `install-phase.json` | not asserted here | `d3b4845865f1c37fd747c612119356b2680287376a8b18a36b96bcf20bd4804e` |
| `installer-argument-vector.txt` | not asserted here | `8e33a2192f7fecaf60dddbe001417b3a6e19941299c353690142e1031b0e59d1` |
| `baseline-summary.json` | 1505 | `fe05f8b76d01223f739c0b65308fe9cccfaf2c0ab09b54f16b3c401f680079dc` |
| `cp314-base-prefix-manifest-v0.inventory.json` | 441937 | `48b6fe85aa0ac0f01bd9ef482b6541756797483db4a63f875b3940d2951b4cbb` |
| `cp314-base-prefix-manifest-v0.rows` | 222601 | `ee89d06739fcf935ad5d2608879261971945ebbd1f379aec4dcf199457d861d4` |
| `root-acl-detail.txt` | 2116 | `7dda4ad11750da44754d635b2f5f2b9b94995ef0680cf3d310c156369889fc31` |
| `startup-customization-paths.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

The complete manifest is retained externally; it is not duplicated in Git. The downloaded installer and installed binaries are not committed.

## Execution deviations

Before the successful elevated invocation, three launch attempts caused no system change: one local `ProcessStartInfo` parameter error, one user-cancelled UAC prompt, and one elevated helper parse error. At each point the target root, install log, and post-install evidence session were absent. After successful installation, one baseline helper parse error and one post-baseline verification helper parse error occurred before their respective corrected read-only commands. These errors did not execute the installed interpreter, alter the installation root, or change the captured digest.

## Explicit negatives

- Third-party packages installed: `NO`
- `pip` invoked: `NO`
- Virtual environment created: `NO`
- Pin Amendment implemented: `NO`
- Final pin values established: `NO`
- Pre-real environment established: `NO`
- Real key generation authorized or performed: `NO`
- Real passphrase created: `NO`
- Admission performed: `NO`
- Downloaded binary committed: `NO`
- Push performed: `NO`

## Required next gate

Freeze or designate the exact standard non-admin custody execution account, then capture effective ACL evidence for that account against the installed root. Do not treat this baseline record alone as satisfaction of the Frozen D1 account/ACL gate.
