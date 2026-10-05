# Official CPython 3.14.3 amd64 EXE Evidence Preparation v0 - D0

## 1. Status

`READY_FOR_EVIDENCE_PREPARATION_REVIEW`

This document is a design and collection plan only. No installer was downloaded,
no software was installed, no machine configuration was changed, no source code
or dependency was changed, and no implementation or final pin value was
established in this batch.

## 2. Scope

This D0 defines the evidence that a later, separately authorized Evidence
Preparation operation must collect before the frozen Ed25519 custody helper
interpreter-provenance amendment can be implemented.

The machine question is:

> Do the exact official CPython 3.14.3 Windows amd64 installer bytes, their
> publisher authentication, the resulting protected installation, and the
> deterministic clean base-prefix state jointly support the interpreter facts
> that a future implementation would pin?

This D0 does not answer that question. It defines a fail-closed procedure for
answering it later.

## 3. Frozen Dependencies

This plan depends on, and does not amend or reinterpret:

- Interpreter provenance pin amendment D1 commit:
  `f392778c644803791310c722af373e3ec0981885`.
- Frozen D1 document SHA-256:
  `571acef37b2c0aae652225ee7e21242427e9b2f2997f363811b7e267bfcfb9bf`.
- Frozen D1 Git blob:
  `0bae82c83cfa846c625919f5608b6487f1c0e84d`.
- Human Design Freeze save commit:
  `a80501f354a9766665477c74566e8ec881f9dd0a`.
- Accepted artifact class: official python.org CPython 3.14.3 Windows amd64
  executable installer named `python-3.14.3-amd64.exe`.
- Planned protected base prefix:
  `C:\Program Files\WeaverForge\Python314`.
- Frozen baseline schema name: `cp314-base-prefix-manifest-v0`.

ZIP distributions, source archives, Microsoft Store packages or aliases,
PythonManager-managed content, other versions or architectures, and
caller-selected interpreters remain out of scope.

## 4. Collection Phases

A future Evidence Preparation operation must execute these phases in order:

1. Discover authoritative release and artifact references from python.org.
2. Acquire the installer as immutable bytes and record the complete acquisition
   transaction.
3. Hash the installer and validate its Authenticode evidence independently.
4. Validate the documented installer-option vocabulary and freeze the exact
   invocation record.
5. Install into the planned protected root under separately authorized machine
   administration.
6. Record root ownership, DACLs, effective access, and path topology.
7. Record installed binary and runtime identity from the absolute interpreter.
8. Capture the clean base-prefix manifest before any venv, pip, third-party
   package, custody-helper, key, or signing activity.
9. Independently recompute all then-existing candidate constants.
10. Produce a review handoff; do not implement or declare Human Final.

Failure, omission, ambiguity, or an unavailable required field stops the
operation with `NOT_ESTABLISHED`.

## 5. Authoritative Source Evidence

The future source record must contain:

- evidence schema and version;
- python.org release-page URL as discovered from official navigation;
- artifact-link URL as published on that release page;
- requested URL, every redirect status and target, and final URL;
- retrieval UTC timestamp and collector identity;
- TLS endpoint host and the collection tool/version;
- release name and version stated by the page;
- published artifact filename, platform, architecture, and artifact type;
- any official digest, signature, provenance, or SBOM references actually
  published, with their source URLs;
- raw response or page-evidence object identifiers and SHA-256 digests;
- an explicit result for official-domain and release/artifact consistency.

The release and artifact URLs are unresolved until official evidence is
collected. They must not be guessed, copied from an unofficial mirror, or
accepted from caller input. Redirects leaving the approved python.org source
boundary require review and otherwise fail closed.

## 6. Installer Artifact Record

The future artifact record must bind one exact byte sequence to:

- record schema and unique evidence-record identifier;
- source-record identifier;
- expected and observed filename;
- immutable evidence location and acquisition UTC timestamp;
- byte length;
- lowercase SHA-256;
- content type, when supplied by the source;
- requested and final source URLs plus redirect-chain identifier;
- first-computation tool, version, command, operator, and timestamp;
- independent-recomputation tool, version, command, operator, and timestamp;
- equality results for filename, byte length, and both digest computations.

The collected filename must be exactly `python-3.14.3-amd64.exe`. Filename
agreement is necessary but never sufficient.

## 7. SHA-256 Rules

Every SHA-256 value used by this scope must be exactly 64 lowercase ASCII
hexadecimal characters matching `[0-9a-f]{64}`. It is computed over the exact
raw file bytes, without newline, encoding, container, metadata, or text-mode
transformation.

At least two independent computations must read the retained artifact bytes.
They must use independently invoked implementations or tools, not two renderings
of one cached result. Any disagreement, uppercase-only unnormalized input,
truncation, missing artifact, or inability to reread the bytes yields
`NOT_ESTABLISHED`. Normalization is allowed only for display after the original
result and validation behavior have been retained in evidence.

## 8. Authenticode Evidence and Acceptance

The future Authenticode record must be bound to the installer SHA-256 and
contain:

- validation host, OS build, policy/tool name and version, and UTC time;
- signature status and full status message;
- signature type and digest algorithm;
- signer certificate subject, issuer, serial number, SHA-256 thumbprint,
  validity interval, and enhanced key usage;
- chain elements, trust statuses, revocation result, and policy errors;
- timestamp/countersignature presence, timestamp time, timestamp authority
  identity, and timestamp-chain result;
- the exact publisher identity asserted by the official source evidence;
- a structured comparison of observed signer identity to that asserted
  publisher identity;
- raw validation output or an evidence-object digest.

Acceptance is fail closed. It requires a valid signature over the retained
installer bytes, an acceptable chain under the recorded policy, successful
publisher-identity comparison to independently reviewed official evidence, and
an acceptable timestamp/countersignature result when certificate validity at
execution time depends on signing time. `UnknownError`, `NotSigned`, hash or
publisher mismatch, untrusted or revoked chain state, indeterminate revocation,
unreviewed certificate substitution, or missing required timestamp evidence is
`NOT_ESTABLISHED`.

No signer subject, issuer, thumbprint, or trust-root value is predeclared by this
D0. Those values must come from collected evidence and review, not self-attested
installer metadata alone.

## 9. Exact Planned Install-Options Record

Before execution, the future operation must verify the exact silent-install
option names and semantics against official CPython 3.14.3 Windows installer
documentation. Unsupported, renamed, ignored, or undocumented options stop the
operation. No installer default may remain implicit.

The planned option manifest must explicitly record and validate these intended
values, subject to that official vocabulary check:

| Intent | Planned value |
| --- | --- |
| all-users installation | enabled |
| target directory | `C:\Program Files\WeaverForge\Python314` |
| add or prepend to `PATH` | disabled |
| Python launcher installation | disabled |
| file associations | disabled |
| Start-menu/desktop shortcuts | disabled |
| interpreter executables and standard library | enabled |
| `venv` support | enabled |
| `pip` bootstrap payload | enabled |
| test suite | disabled |
| documentation | disabled |
| Tcl/Tk and IDLE | disabled |
| debug binaries | disabled |
| symbols | disabled |
| compile-all behavior | explicitly recorded after documentation review |
| every remaining documented selectable feature | explicitly enabled or disabled |

The invocation record must contain the installer SHA-256, absolute installer
path, elevation context, exact ordered argument vector, working directory,
environment delta, start/end UTC timestamps, exit code, installer log path and
log SHA-256, reboot indication, and an option-manifest digest. A shell-rendered
command is supplementary; the ordered argument vector is authoritative.

## 10. Protected-Root and ACL Evidence

The future protected-root record must cover the resolved base prefix and at
least `python.exe`, `python314.dll`, the standard-library tree, and every file
included in the baseline manifest. It must record:

- lexical and resolved absolute path;
- volume identity and file/directory identity where available;
- owner SID and resolved owner name;
- protected/inherited DACL state, SDDL, and canonical ACE list;
- effective rights for the dedicated execution identity and all relevant group
  memberships;
- effective rights for TrustedInstaller, SYSTEM, and local Administrators;
- reparse-point, junction, symlink, hard-link, mount-point, and alternate-data-
  stream scan results;
- collection tools, versions, operators, and UTC timestamps;
- before/after evidence references for ACL establishment.

Acceptance requires that the execution identity have read/execute access but no
write, append, create, delete, delete-child, modify, ownership, or DACL-changing
right anywhere in the protected base tree. Only TrustedInstaller, SYSTEM, and
local Administrators may have modification authority under the frozen design.
Unexpected inheritance, unresolved identities, path redirection, writable
ancestors that can substitute the resolved tree, or incomplete effective-access
analysis is `NOT_ESTABLISHED`.

This does not claim resistance to compromise of Administrators, SYSTEM,
TrustedInstaller, the kernel, firmware, or the physical host.

## 11. Installed Interpreter Evidence

The future installed-file record must bind both
`C:\Program Files\WeaverForge\Python314\python.exe` and
`C:\Program Files\WeaverForge\Python314\python314.dll` to:

- resolved path, size, lowercase SHA-256, file identity, and timestamps;
- version-resource product/file version, original filename, architecture, and
  machine type;
- Authenticode status and signer linkage where present;
- owner/DACL evidence and baseline-manifest row;
- equality or explained relationship to installer payload evidence.

The runtime record must be obtained only by an explicit absolute invocation of
the installed `python.exe` in isolated mode and must record:

- exact ordered invocation and evidence-script SHA-256;
- `sys.version`, `sys.version_info`, implementation name/version and cache tag;
- pointer width, machine/architecture, byte order, and GIL/build facts exposed
  by the interpreter;
- `sys.executable`, `sys.prefix`, `sys.base_prefix`, `sys.exec_prefix`, and
  `sys.base_exec_prefix`;
- module search path, user-site enablement, environment variables considered,
  and site initialization state;
- `python.exe` and loaded `python314.dll` resolved identities;
- invocation UTC timestamp, exit code, stdout/stderr byte digests, and parsed
  record digest.

Bare `python`, `py`, PATH lookup, Store aliases, and caller-selected executable
paths are forbidden. Any path, version, architecture, or loaded-library
disagreement is `NOT_ESTABLISHED`.

## 12. Clean Base-Prefix Manifest

The baseline must be captured immediately after installation and ACL validation,
before any venv, pip invocation, third-party package, custody-helper content,
key, passphrase, or signing operation.

`cp314-base-prefix-manifest-v0` covers every regular file under the resolved
base prefix. For each file:

1. Compute a path relative to the resolved base prefix and reject empty or
   escaping paths.
2. Replace `\` with `/`.
3. Require ASCII bytes and lowercase ASCII letters.
4. Reject duplicate normalized paths and case-colliding source paths.
5. Compute raw-file byte length and lowercase SHA-256.
6. Serialize exactly:
   `<normalized-relative-path> NUL <decimal-size> NUL <lowercase-sha256> LF`.
7. Sort rows by normalized ASCII path bytes.
8. SHA-256 the exact concatenation of all sorted rows.

The record retains the complete ordered row set, entry count, manifest digest,
resolved root identity, collection tool/version, and UTC timestamp. It includes
all import-affecting files and locations, including any `sitecustomize`,
`usercustomize`, `.pth`, and `._pth` files. Symlinks, junctions, reparse points,
unexpected hard links, unreadable entries, alternate data streams, concurrent
tree mutation, path encoding failure, or traversal instability fail closed.

Future code may embed only the schema name, entry count, and manifest digest,
but the complete rows remain external evidence.

## 13. Freshness and Replay Rules

Every record belongs to one named evidence session and identifies its immediate
predecessor inputs. The handoff is stale and must be recollected or revalidated
after any of the following:

- installer bytes, source references, or retained evidence objects change;
- trust policy, certificate status, validation host, or relevant OS trust state
  changes materially;
- installation, repair, upgrade, ACL change, ownership change, or protected-root
  topology change occurs;
- any base-prefix file content, path, count, metadata relevant to identity, or
  effective access changes;
- runtime identity no longer matches the captured absolute installation;
- evidence records are detached from their session, artifact digests, or
  predecessor references.

An old but byte-identical installer digest does not by itself refresh signer,
trust-policy, installed-state, ACL, runtime, or baseline evidence. Replay across
machines, roots, sessions, or installation events is forbidden.

## 14. Independent Recomputation

The recomputation record must identify a second operator or review role, tools
and versions, UTC times, exact input evidence-object digests, and separate
results for:

- installer byte length and SHA-256;
- source/artifact linkage;
- Authenticode and publisher-identity decision;
- installed `python.exe` and `python314.dll` hashes and identities;
- protected-root resolution and effective-access result;
- runtime identity facts;
- baseline entry count and manifest SHA-256.

It must report `PASS`, `FAIL`, or `NOT_ESTABLISHED` per layer and preserve
disagreements. It must reread source bytes and records rather than consume a
single preparation script's final assertion. Independent recomputation is
evidence, not an authority, admission decision, or Human Final.

Pi N1 is preserved as follows: pre-implementation independent recomputation
applies to the installer, interpreter, protected-root, runtime, and baseline
constants that exist at that stage. Successor helper source hashes, successor
commit identity, helper-root facts, and their bindings arise only after an
authorized implementation; they must be independently recomputed and bound
before any successor Human Final or deployment. They must not be fabricated or
declared missing from this pre-implementation D0.

## 15. Future Implementation Handoff

The reviewed Evidence Preparation handoff must provide, without caller
override:

- evidence-session and schema identifiers;
- source record and raw-evidence digests;
- installer filename, byte length, lowercase SHA-256, and immutable artifact
  reference;
- Authenticode signer, chain, timestamp, and publisher-comparison results;
- exact installer option manifest, invocation record, log digest, and outcome;
- resolved base prefix and root identity;
- installed `python.exe` and `python314.dll` paths, sizes, lowercase SHA-256
  values, and file identities;
- runtime identity record and evidence-script digest;
- ACL/ownership/effective-access result and evidence references;
- baseline schema, entry count, manifest SHA-256, and complete-row evidence
  reference;
- independent-recomputation results and record digest;
- freshness boundary, unresolved limitations, reviewer disposition, and explicit
  `SUPPORTED_FOR_PIN_REVIEW` or `NOT_ESTABLISHED` outcome.

These are candidate inputs to a later authorized implementation. They are not
final code pins until reviewed, implemented as code-owned constants, tested,
and separately frozen.

## 16. Adversarial Checks

The future collection and review must reject at least:

1. unofficial or look-alike domains;
2. unrecorded or cross-boundary redirects;
3. correct filename with substituted bytes;
4. alternate version, architecture, package type, Store alias, or PythonManager
   content;
5. one-byte installer mutation;
6. disagreeing digest computations;
7. unsigned, invalid, revoked, untrusted, indeterminate, or wrong-publisher
   Authenticode state;
8. signer-certificate substitution or self-attested publisher identity;
9. stale trust or timestamp evidence;
10. undocumented, ignored, duplicated, or implicit installer options;
11. installation outside the exact protected root;
12. PATH, `py`, alias, or caller-selected interpreter substitution;
13. writable root, writable ancestor substitution, unexpected inheritance, or
    incomplete group/effective-right analysis;
14. symlink, junction, reparse, hard-link, mount-point, or ADS ambiguity;
15. installed binary or DLL mismatch;
16. wrong runtime version, architecture, base prefix, or loaded DLL;
17. baseline capture after venv, pip, package, helper, or key activity;
18. omitted import-affecting files or nondeterministic manifest ordering;
19. stale or replayed evidence from another machine, root, session, or install;
20. one script certifying its own cached outputs as independent recomputation;
21. missing evidence layer treated as a pass;
22. current-machine or PythonManager values promoted without this procedure;
23. pre-implementation fabrication of successor helper or commit hashes;
24. evidence outcome treated as authority, admission, deployment approval, or
    Human Final.

## 17. Unresolved Values

The following intentionally remain unresolved:

- official release-page and artifact URLs;
- redirect chain, content length, installer SHA-256, and raw evidence digests;
- signer, issuer, certificate, chain, timestamp, and trust-policy facts;
- official installer-option spellings and the complete explicit argument vector;
- installation log digest and machine-specific file identities;
- owner/DACL/SDDL/effective-access evidence;
- installed executable and DLL hashes and version-resource facts;
- runtime identity outputs;
- baseline entry count, complete rows, and manifest SHA-256;
- independent-recomputation record and reviewer disposition;
- all post-implementation helper source, helper-root, commit, test, and Human
  Final bindings.

No values observed from the current machine, PythonManager, a pre-existing
interpreter, or an unrelated installation are promoted by this D0.

## 18. Nonclaims and Authority Boundaries

This D0 does not:

- download, validate, install, execute, or endorse an installer;
- establish official-source, publisher, binary, ACL, runtime, or baseline facts;
- establish final interpreter or helper pin values;
- authorize implementation, dependency change, key generation, signing,
  Admission, deployment, or push;
- create authority, independent reproduction, Human Final, or execution
  permission;
- prove security against privileged host compromise;
- amend CLOSED scopes or the frozen D1 semantics.

## 19. Stop/Go Gates

- **D0 review gate:** GO only for review of this collection plan. Current status:
  `READY_FOR_EVIDENCE_PREPARATION_REVIEW`.
- **Evidence execution gate:** STOP until a separate human authorization approves
  network acquisition, machine changes, exact tools, official-source policy,
  and the fully explicit installer option vocabulary.
- **Evidence acceptance gate:** GO only if every required layer is complete,
  fresh, internally bound, independently recomputed, and reviewed as
  `SUPPORTED_FOR_PIN_REVIEW`; otherwise `NOT_ESTABLISHED`.
- **Implementation gate:** STOP until accepted evidence and a separate explicit
  implementation authorization exist.
- **Successor freeze/deployment gate:** STOP until implementation-specific
  hashes, helper-root evidence, tests, independent recomputation, and separate
  Human Final requirements are completed.

