# Ed25519 Custody Helper v0 Interpreter Provenance Pin Amendment - D1

Date:
2026-10-05

Design status:
READY_FOR_BOUNDED_ADVERSARIAL_REVIEW

This document is one additive design candidate only. It does not edit implementation, tests, dependencies, accounts, Python, virtual environments, CLOSED records, or Human Final records. It does not establish PRE-REAL, authorize generation, create a key or passphrase, perform Admission, or push.

Repository:
`C:\dev\Weaver\weaver-forge-r4`

Base HEAD:
`b328af3facdbd9cfb89b0685907a2e3fc80a8e97`

Design basis:
`docs/next/PRE_REAL_ED25519_CUSTODY_EXECUTION_ENVIRONMENT_V0_D0_R1_20261005.md`

Historical CLOSED implementation:
`d0aedb62904cb39c5cafa55a4b177b3154e420c7`

Historical Human Final save:
`fde7aa54feaa59bcbd37f4911a7de88135ccd2fd`

Those historical points remain immutable. This design does not amend, rebase, replace, or reinterpret them.

## Recommended scope

`Ed25519 Custody Helper v0 Interpreter Provenance Pin Amendment`

The scope is the smallest additive successor that can replace the intentionally unset interpreter provenance pin, verify a protected official-EXE interpreter baseline, and bind PRE-REAL execution to the separately reviewed successor helper bytes.

## Core machine question

> Which immutable code-owned interpreter provenance facts may the additive successor compare at runtime, which independently reviewed evidence establishes those constants, and how are both bound to the protected Human-Final-accepted successor without allowing caller-controlled self-ratification?

The runtime answer is limited to exact equality and fail-closed structural checks. It does not establish trust, identity, authority, truth, key validity, Admission, or generation authorization.

## Additive-successor rule

1. `d0aedb62904cb39c5cafa55a4b177b3154e420c7` and `fde7aa54feaa59bcbd37f4911a7de88135ccd2fd` remain historical CLOSED facts.
2. Evidence preparation occurs in a separate authorized batch before implementation.
3. A later implementation creates a new successor commit. It does not amend or rewrite the historical commit.
4. The successor receives independent implementation review and a new Human Final naming its exact commit, files, evidence record, and limitations.
5. Historical Human Final remains true only for the historical fixed implementation. It does not flow automatically to the successor.

`ADDITIVE_SUCCESSOR_REQUIRED: YES`

## Accepted interpreter path

The sole accepted acquisition path is the official python.org CPython 3.14.3 Windows amd64 EXE installer:

`python-3.14.3-amd64.exe`

Rejected as non-equivalent:

- embeddable or ordinary ZIP distributions;
- PythonManager;
- Microsoft Store packages and App Execution Aliases;
- source builds;
- package-manager or vendor repackaging;
- another version or architecture;
- another interpreter implementation;
- a caller-selected interpreter, base prefix, executable, or install root.

No final installer or installed-binary hash is selected from the current mine0/PythonManager development environment.

`FINAL_PIN_VALUES_ESTABLISHED: NO`

All production hashes, signer identifiers, manifest digest, entry count, and exact protected install-root evidence are:

`TO_BE_ESTABLISHED_BY_SEPARATE_EVIDENCE_PREPARATION`

## Protected install location

The planned accepted root is a machine-wide protected installation under:

`C:\Program Files\WeaverForge\Python314`

The exact resolved final path must be frozen in the evidence record and successor code after the official EXE installation. No environment, registry search, PATH lookup, launcher, alias, working directory, symlink, junction, or caller argument may select a different root.

The root and all descendants must satisfy this minimum model:

- owner is `NT SERVICE\TrustedInstaller`, `NT AUTHORITY\SYSTEM`, or the local `Administrators` group, as independently recorded after installation;
- the dedicated execution account is not owner;
- the dedicated execution account and ordinary `Users` receive read and execute only;
- only `TrustedInstaller`, `SYSTEM`, and local `Administrators` may have write, modify, delete, ownership, or DACL-change rights;
- no writable ACE reaches the dedicated account through direct, inherited, group, creator-owner, service, or authenticated-user membership;
- no reparse point exists in the root or relevant ancestors;
- `python.exe`, `python314.dll`, the standard library, DLLs, startup customization surfaces, and base `site-packages` are covered by the same protected model.

The successor must inspect owner/DACL facts at runtime using Windows-native security APIs and fail closed on unknown or writable state. Evidence preparation independently records the effective ACL and account-access result.

This protects against modification by the dedicated standard execution account. It does not protect against compromise of `SYSTEM`, `TrustedInstaller`, an administrator, kernel, firmware, or the installation administrator.

`PROTECTED_INSTALL_REQUIRED: YES`

`EXECUTION_ACCOUNT_CAN_MODIFY_INTERPRETER_TREE: NO`

## Evidence chain

No evidence layer substitutes for another. The separate evidence-preparation record must contain the following layers and explicit results.

### A. Installer artifact identity

- exact filename `python-3.14.3-amd64.exe`;
- exact byte size;
- official python.org release page URL and direct artifact URL;
- acquisition time and retrieval method;
- statement that ZIP, PythonManager, Store, source, and alternate artifacts were not used.

### B. Installer digest and official provenance

- independently computed lowercase SHA-256 of the exact EXE bytes;
- comparison with the official python.org-published digest or release metadata;
- identifiers and validation results for any official signature, certificate, Sigstore, SBOM, or provenance material actually published for that exact artifact;
- explicit `NOT_PUBLISHED` for an expected evidence class that the official release did not provide, never silent substitution with local metadata.

### C. Authenticode

- Windows Authenticode status from the exact EXE;
- exact signer subject, issuer, certificate thumbprint, chain result, and timestamp/countersignature facts available from the verification API;
- independent confirmation that status is valid under the evidence-preparation policy;
- no assumption that a valid Authenticode signature alone proves the release page, installed files, or invocation.

### D. Installation act and protected root

- exact absolute installer path and its verified artifact identity;
- exact invocation and unattended options, including all-users/machine-wide selection, target directory, launcher/PATH/file-association choices, and exit status;
- exact resolved installed base prefix;
- before/after directory state and installer log retained as evidence without secrets;
- owner and DACL observations proving the dedicated account has read/execute but no write/modify/delete/ownership/DACL rights.

### E. Installed `python.exe`

- exact final path under the protected root;
- lowercase SHA-256, size, file identity, version resource, owner, DACL, reparse status, and Authenticode facts if present.

### F. Installed `python314.dll`

- the same facts as E, independently measured from the installed DLL.

### G. Runtime identity

- CPython exact version tuple `(3, 14, 3, "final", 0)`;
- `win32`, 64-bit pointer size, `win-amd64`, ordinary GIL build;
- `sys.executable`, `_base_executable`, `base_prefix`, and runtime DLL identity;
- rejection of Store, WindowsApps, Packages, PythonManager, ZIP, or alternate-root indicators.

### H. Clean base-prefix baseline

- deterministic complete baseline manifest captured as specified below;
- explicit absence or reviewed expected presence of startup customization files;
- evidence that capture occurred before any third-party package installation and before custody use.

### I. PATH and alias ambiguity

- absolute accepted interpreter and venv paths;
- observed PATH, `where.exe python`, `py.exe`, WindowsApps aliases, PythonManager registrations, and relevant registry/launcher facts;
- proof that all accepted commands use absolute paths and do not resolve through those surfaces.

Installed binary hashes do not prove installer provenance. Installer provenance does not prove installation options or installed bytes. Local metadata does not prove official origin. Authenticode does not prove the baseline remained unchanged.

## Immutable pin shape

Existing `manifest.py` currently defines:

```text
_INTERPRETER_PROVENANCE = None
_PROVENANCE_FILES = ("python.exe", "python314.dll")
```

and evaluates `facts.interpreter_hashes` against `_INTERPRETER_PROVENANCE`. The additive successor retains that narrow tuple shape and replaces only the unset value with exactly:

```text
_INTERPRETER_PROVENANCE = (
    ("python.exe", "<64-lowercase-sha256-established-by-evidence>"),
    ("python314.dll", "<64-lowercase-sha256-established-by-evidence>"),
)
```

The placeholders above are design notation and cannot enter implementation. Final constants must be exact built-in strings, exactly 64 lowercase ASCII hexadecimal characters. Field order and filenames are fixed. Missing, extra, duplicate, reordered, uppercase, malformed, or mismatched values fail closed.

The successor also adds the smallest baseline/root pin needed to cover the currently unpinned interpreter tree:

```text
_INTERPRETER_ROOT_PIN = (
    ("base_prefix", r"C:\Program Files\WeaverForge\Python314"),
    ("baseline_schema", "cp314-base-prefix-manifest-v0"),
    ("baseline_entry_count", <exact-positive-int-from-evidence>),
    ("baseline_manifest_sha256", "<64-lowercase-sha256-from-evidence>"),
)
```

The tuple is code-owned and immutable. It has no environment, file, registry, config, CLI, network, plugin, callback, or caller-provided override. Runtime does not accept an expected hash or expected root.

Installer URL, installer SHA-256, Authenticode signer facts, invocation evidence, and full baseline rows remain in the separately reviewed evidence record. They are evidence for selecting the code constants; they are not caller inputs to production preflight.

## Base-prefix baseline

The clean baseline is captured exactly once during separately authorized evidence preparation:

1. verify the official EXE artifact and Authenticode layers;
2. install to the protected all-users root with the recorded invocation;
3. verify root owner/DACL and that the dedicated execution account cannot modify it;
4. before creating a venv, installing third-party packages, running custody code, or allowing general use, enumerate the protected base prefix;
5. have an independent recomputer repeat the enumeration and digest.

The manifest covers every regular file under the resolved base prefix, including root executables and DLLs, `DLLs`, `Lib`, base `Lib\site-packages`, import machinery, encodings, certificates shipped by the installer, `.pth`, `._pth`, `sitecustomize.py`, `usercustomize.py`, and any bytecode or installer-created file actually present. Reparse points, alternate data streams where detectable by the selected evidence tool, unreadable entries, duplicate normalized paths, non-regular entries, or files changing during capture fail the capture.

Deterministic row construction:

- derive a path relative to the exact resolved base prefix;
- reject absolute, parent, empty, or escaping paths;
- replace `\` with `/`;
- require ASCII path bytes for this v0 or fail evidence preparation;
- lowercase with ASCII rules because the protected Windows tree is case-insensitive;
- reject duplicate normalized paths;
- record `<relative-path> NUL <decimal-size> NUL <lowercase-file-sha256> LF`;
- sort rows by their normalized ASCII path bytes;
- SHA-256 the exact concatenated UTF-8/ASCII rows;
- record exact entry count and final lowercase manifest SHA-256.

The full row manifest is retained in the reviewed evidence package for independent recomputation. Only schema, count, and digest are embedded in successor code. This avoids an enormous code constant while binding the entire clean tree.

Runtime recomputes the same full-tree manifest and compares exact count and digest. It also explicitly rejects any `sitecustomize.py`, `usercustomize.py`, `.pth`, or `._pth` startup customization not present in the reviewed baseline. A stale baseline, changed file, added file, removed file, changed path, unreadable file, reparse point, or changing tree fails closed.

`BASE_PREFIX_BASELINE_DEFINED: YES`

## Runtime comparison boundary

The additive successor may compare only code-owned expectations against directly collected facts:

- exact installed `python.exe` and `python314.dll` hashes;
- exact accepted `base_prefix` and `_base_executable` path;
- exact full-tree baseline schema, count, and digest;
- version, architecture, implementation, GIL, isolated-mode, venv, module-path, package RECORD, OpenSSL, and injection facts already frozen by the historical helper;
- protected interpreter-root owner/DACL/reparse facts;
- exact protected helper-root path and owner/DACL/reparse facts added by the successor.

It must not infer installer origin from hashes alone. The external evidence record and Human Final establish why those exact constants were selected. Runtime equality establishes only that current collected facts match those constants.

Every missing, unknown, malformed, inaccessible, noncanonical, or mismatched fact fails closed. No fallback interpreter, baseline, helper root, or relaxed mode exists.

## Helper-source binding

The helper cannot make itself authoritative merely by embedding hashes in modifiable source. PRE-REAL therefore binds it through independent evidence and filesystem protection:

1. The successor Human Final names the exact successor commit and exact SHA-256 of every production helper file, the lock file, and the additive runbook/evidence records.
2. A deployment copy is created at one fixed machine-wide protected helper root, planned as `C:\Program Files\WeaverForge\CustodyHelperV0Successor`.
3. Owner/DACL rules mirror the interpreter root: the execution account receives read/execute only and cannot own, write, modify, delete, or change DACLs; only the bounded administrative principals may modify it.
4. Independent PRE-REAL recomputation hashes every deployed file and compares it to the Human-Final file manifest. It verifies no extra file, missing file, reparse point, alternate data source, or uncommitted/development copy is executed.
5. The successor runtime requires that exact resolved helper root and checks owner/DACL/reparse facts. It rejects a caller-selected alternate root.
6. If a Git worktree is used during review, clean status and commit identity are supporting evidence only. Deployment uses independently hashed exact bytes; Git identity alone is not authority.

Self-hashing constants inside the helper are not used as sole authority because a writable attacker could change code and constants together, and a file cannot contain its own final hash without a recursive construction. Protection plus independent recomputation closes that substitution path.

`HELPER_SOURCE_BINDING_DEFINED: YES`

## Explicit invocation and venv path

No accepted command uses bare `python`, `python3`, `py`, PATH lookup, a Store alias, or PythonManager.

Evidence preparation and later PRE-REAL use the exact absolute accepted interpreter path, for example:

```text
C:\Program Files\WeaverForge\Python314\python.exe -m venv <fixed-dedicated-venv>
```

Package installation uses only the exact venv executable:

```text
<fixed-dedicated-venv>\Scripts\python.exe -I -m pip --isolated install --no-deps --require-hashes --only-binary :all: -r <fixed-protected-helper-root>\requirements\exact-bytes-witness-v0.txt
```

Helper invocation uses that same absolute venv executable and exact protected helper root. The final paths are code/runbook-owned after evidence preparation, not caller arguments.

`NM1_CLOSED_IN_DESIGN: YES`

## Operational attestation freshness

Operational attestations are evidence inputs, not machine proof or reusable authorization tokens.

Each attestation is bound to one PRE-REAL recomputation session by:

- exact successor commit and file-manifest identity;
- host identifier recorded by the evidence procedure;
- dedicated account SID;
- Windows logon session LUID and console session identifier;
- interpreter, venv, helper-root, ACL, environment, and preflight evidence identifiers;
- attestation creation timestamp and the recomputation record identifier;
- exact declared operational facts and unresolved limitations.

No universal duration is asserted. An attestation expires at the earliest of:

- end or change of the bound logon/console session;
- any staleness event listed below;
- Human withdrawal;
- completion or abandonment of the one generation-authorization decision for which it was recorded.

All operational declarations and machine checks must be re-observed in the same bound session immediately before a Human generation-authorization decision. A previous day's, previous session's, copied, or merely recent declaration is not current evidence.

`NM3_CLOSED_IN_DESIGN: YES`

## Independent recomputation record

An acceptable independent recomputer is either:

- a second Human reviewer operating a separately reviewed read-only recomputation tool against the protected host; or
- a deterministic recomputation tool run independently from the preparation workflow, with its complete output reviewed by a Human who did not merely accept the preparer's cached result.

AI agreement alone, the preparation script's own success message, Git status alone, or the custody helper's self-report alone is not independent recomputation.

The structured record contains at least:

- schema version and record identifier;
- target successor commit and per-file hashes;
- Human Final record identity;
- installer artifact filename, URL/evidence identifier, SHA-256, official provenance result, and Authenticode facts;
- exact protected install root, `python.exe` hash, `python314.dll` hash, baseline schema/count/digest, and ACL result;
- exact helper root, helper file-manifest identity, and ACL result;
- interpreter version/architecture/GIL and PATH/alias rejection results;
- dedicated account SID, groups, elevation, profile, logon LUID, and console session;
- venv, dependency RECORD, module-path, OpenSSL, and injection-preflight results;
- operational attestation record reference and creation/recheck time;
- recomputation time, tool identity, per-predicate PASS/FAIL/UNKNOWN, aggregate result, recomputer identity or bounded reviewer reference, and unresolved limitations.

Unknown or omitted predicates produce `PRE_REAL_NOT_READY`. The record is evidence only. It is not Human Final, authority, Admission, trust, identity, signer binding, or generation authorization.

`NM4_CLOSED_IN_DESIGN: YES`

## Authority boundaries

The successor and PRE-REAL process preserve all of these inequalities:

- `PRE_REAL_READY_FOR_SEPARATE_HUMAN_GENERATION_AUTHORIZATION != generation authorization`
- `Human operational attestation != machine proof`
- `Human operational attestation != Human Final`
- `valid environment != signer trust`
- `valid environment != future key validity`
- `valid environment != Admission`
- `pin match != interpreter origin by itself`
- `hash match != trust, truth, or authority`
- `reviewed successor != authorization to generate a key`
- `independent recomputation record != independent reproduction`

No AI, caller, helper, interpreter, installer, key, signature, hash, record, or successful preflight can self-ratify authority.

`NM6_CLOSED_IN_DESIGN: YES`

## Staleness and recomputation triggers

Any relevant change forces `PRE_REAL_NOT_READY`, invalidates the current recomputation/attestation session, and requires full recomputation:

- installer bytes, official evidence, Authenticode result, or evidence policy;
- installed root, path, `python.exe`, `python314.dll`, any baseline-manifest file, count, digest, owner, DACL, reparse state, or startup customization surface;
- successor commit, any helper/dependency/runbook/evidence bytes, helper root, owner, DACL, or reparse state;
- account SID, group membership, elevation, impersonation, profile, logon session, or console session;
- venv, `pyvenv.cfg`, dependency versions, wheel/RECORD content, module path, OpenSSL runtime, or environment injection state;
- PATH, Store alias, PythonManager, registry/launcher, or absolute executable resolution;
- OS build or security configuration relevant to ACLs, code loading, console, sync, VSS, File History, indexing, endpoint collection, or operational declarations;
- custody-root preconditions, backup-media readiness, password-manager readiness, or Human attestation basis;
- elapsed session boundary, logout, reboot where evidence is session-sensitive, or any failed/unknown check.

There is no permanent READY or currentness claim.

## Tests and mutations

The existing `test_x07_real_test_venv_is_not_the_prereal_environment` currently requires `_INTERPRETER_PROVENANCE is None`. The successor must change x07 so that it:

- requires the exact non-`None` canonical code-owned pin shape;
- confirms the current development/test venv remains rejected for path, provenance, ACL, baseline, helper-root, or other PRE-REAL mismatches;
- never treats a test fixture or current mine0 interpreter hash as the production pin.

Existing mutation `M15i` removes the unset-provenance fail-closed guard. That mutation is no longer semantically applicable after the pin is populated. It must be replaced by actual source mutations that remove or weaken populated-pin equality, canonicality, root/baseline checks, and helper binding.

Planned attack tests, separate from mutations, include at least these 22 cases:

1. pin missing or placeholder remains;
2. wrong `python.exe` hash;
3. wrong `python314.dll` hash;
4. uppercase or noncanonical hash;
5. missing, extra, duplicate, or reordered pin entry;
6. wrong version, implementation, architecture, or GIL;
7. ZIP, PythonManager, Store, WindowsApps, Packages, source-build, or alternate interpreter path;
8. caller-selected expected hash, root, interpreter, or baseline override;
9. writable interpreter root or file for the execution SID or one of its groups;
10. wrong owner, inherited writable ACE, reparse point, or ACL-read failure;
11. changed, missing, added, unreadable, or stale base-prefix manifest file;
12. `sitecustomize.py`, `usercustomize.py`, `.pth`, or `._pth` injection;
13. PATH, launcher, registry, or Store-alias ambiguity;
14. writable helper root;
15. alternate helper root;
16. modified or uncommitted `manifest.py` or another helper file;
17. helper file missing, extra, linked, or hash mismatched;
18. stale installer/evidence/baseline/recomputation record;
19. stale, copied, wrong-session, or basis-changed operational attestation;
20. bare-python or wrong venv executable invocation;
21. independent record with omitted/UNKNOWN predicate or mismatched account SID;
22. successful hash equality promoted to origin, trust, generation authority, or Admission.

Planned actual source mutation operators include at least these 14:

1. set `_INTERPRETER_PROVENANCE` back to `None` but return success;
2. skip `python.exe` equality;
3. skip `python314.dll` equality;
4. lowercase or normalize caller/runtime hash instead of requiring canonical facts;
5. accept any base prefix or executable path;
6. skip baseline count or digest comparison;
7. omit files or startup customization paths from baseline enumeration;
8. accept interpreter-root ACL unknown/writable state;
9. accept helper-root ACL unknown/writable state;
10. accept an alternate helper root or extra/missing helper file;
11. accept PATH/Store/PythonManager resolution;
12. accept caller/environment/file/config pin override;
13. treat stale attestation/recomputation as current;
14. return READY with a missing, FAIL, or UNKNOWN predicate.

`X07_M15I_ACCOUNTED_FOR: YES`

## Bounded later implementation plan

### Evidence required first

Implementation must not begin until a separately authorized evidence-preparation batch supplies and independently verifies:

- official EXE artifact identity, lowercase SHA-256, official provenance, and Authenticode record;
- exact install invocation and protected all-users root;
- final `python.exe` and `python314.dll` lowercase hashes;
- exact runtime identity;
- complete clean base-prefix manifest, count, and digest;
- interpreter-root owner/DACL and dedicated-account no-write result;
- final fixed helper deployment root and protection model;
- independent recomputation of every selected constant.

### Planned implementation files

Expected successor changes are bounded to:

- `ed25519_custody_v0/manifest.py` - populated interpreter tuple; root/baseline constants; runtime manifest, path, and ACL facts/checks;
- `ed25519_custody_v0/winsec.py` - only if existing Windows security helpers cannot expose the required interpreter/helper owner and effective-write facts;
- `ed25519_custody_v0/tests/conftest.py` - successor environment facts and fixtures;
- `ed25519_custody_v0/tests/test_custody_supplementary.py` - x07 replacement and source/root/evidence checks;
- `ed25519_custody_v0/tests/test_custody_checks_25_48.py` - bounded new provenance/baseline/ACL attacks if not cleanly housed in supplementary tests;
- `ed25519_custody_v0/tests/mutation_campaign_v0.py` - replace M15i and add actual successor mutations;
- one new reviewed evidence record under `docs/next` containing the full evidence chain and baseline rows or an exact referenced evidence attachment;
- one new additive successor runbook/amendment under `docs/next` using only absolute interpreter and venv commands.

No historical Human Final or CLOSED design/runbook record is edited. No dependency version or lock hash changes unless a later separately authorized scope proves such a change is required.

### Review and closure order

1. evidence preparation and independent evidence recomputation;
2. bounded implementation authorization;
3. successor implementation and focused tests/mutations;
4. independent implementation review against the exact evidence and successor bytes;
5. one bounded adversarial design/implementation review, not a broad loop;
6. new Human Final naming the successor commit and evidence record;
7. protected deployment and independent PRE-REAL recomputation;
8. only then may a separate Human consider generation authorization.

## Nonmaterial closure summary

`NM1_CLOSED_IN_DESIGN: YES` - absolute accepted interpreter and venv executable paths only.

`NM2_CLOSED_IN_DESIGN: YES` - protected all-users/equivalent root; execution account read/execute only.

`NM3_CLOSED_IN_DESIGN: YES` - session/event-bound attestations and immediate pre-authorization recheck.

`NM4_CLOSED_IN_DESIGN: YES` - structured independent recomputation evidence record.

`NM5_CLOSED_IN_DESIGN: YES` - clean post-install/pre-package full-tree baseline with deterministic digest.

`NM6_CLOSED_IN_DESIGN: YES` - explicit authority and nonpromotion boundaries.

## Current negative state

`CALLER_CONTROLLED_PIN_OVERRIDE: NO`

`PRE_REAL_ENVIRONMENT_ESTABLISHED: NO`

`REAL_KEY_GENERATION_AUTHORIZED: NO`

`REAL_KEY_GENERATED: NO`

`REAL_PASSPHRASE_CREATED: NO`

`ADMISSION_PERFORMED: NO`

`IMPLEMENTATION_EDITED: NO`

`ACCOUNT_CHANGED: NO`

`PYTHON_INSTALLED: NO`

`VENV_CREATED: NO`

## Recommended next step

Perform one bounded adversarial review of this D1 candidate. If accepted and Human Design Frozen, separately authorize official-installer evidence preparation. Do not implement the successor until final evidence constants and independent recomputation exist.

## Push status

NO. Push is forbidden for this design batch.
