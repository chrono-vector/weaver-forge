# Official CPython 3.14.3 amd64 EXE Evidence Collection v0

## 1. Result

`INSTALLER_EVIDENCE_ESTABLISHED_PENDING_POST_INSTALL`

This record establishes only the bounded pre-install installer-side evidence
collected on 2026-10-05. The downloaded executable was not executed. Python was
not installed, and no account, group, ACL, environment, dependency,
implementation, key, signature, Admission, or protected future root was
created or changed.

## 2. Design Basis

- Base HEAD and accepted D0-R1:
  `964da7d1d73216c6a3d6bd3cf7aa15936a0e93ce`.
- Original D0:
  `7b77fb3454d7cc7582bfe7a7a9a692f37127c9e4`.
- Frozen interpreter-provenance amendment D1:
  `f392778c644803791310c722af373e3ec0981885`.
- Human Design Freeze save:
  `a80501f354a9766665477c74566e8ec881f9dd0a`.
- Targeted review disposition supplied to this batch:
  `ACCEPT_D0_R1_CLOSURE`; M1 closed; M2 closed; no new material finding.

The original D0, D0-R1, frozen D1, Freeze, CLOSED records, Human Final records,
and implementation source were not edited.

## 3. Evidence Session

- Session: `cpython-3.14.3-amd64-preinstall-20261005T103849Z`.
- Acquisition intervals: 2026-10-05T10:38:49.5591150Z through
  2026-10-05T10:38:51.3264654Z for the initial source/artifact set, and
  2026-10-05T11:31:33.1969762Z through 2026-10-05T11:32:29.8524061Z for the
  official read-only Downloads API records.
- Staging directory:
  `C:\Users\mine0\Downloads\weaver-evidence\cpython-3.14.3-amd64-20261005`.
- Staging-directory creation UTC: 2026-10-05T10:38:49Z.
- Staging is outside the future install root and outside Git.
- Acquisition tool: Windows `curl.exe`, HTTPS only, TLS 1.2 minimum,
  certificate verification enabled, redirects enabled with maximum 5, and
  response headers retained per object.
- Observed result for every collected URL: HTTP 200, TLS verification result 0,
  and no redirect response in the retained header chain.

The staging directory is evidence storage, not a protected install source. The
EXE must be reread and independently rehashed immediately before any later
authorized installation. Any change makes this record stale.

## 4. Authoritative Release and Artifact Identity

Official release evidence:

- Release page:
  `https://www.python.org/downloads/release/python-3143/`.
- Release identity: CPython 3.14.3, third maintenance release of Python 3.14.
- Release date stated by python.org: 2026-02-03.
- Official artifact-index page:
  `https://www.python.org/ftp/python/3.14.3/`.
- Official read-only release API:
  `https://www.python.org/api/v2/downloads/release/?slug=python-3143`.
- Release API resource: `https://www.python.org/api/v2/downloads/release/1090/`;
  published `true`; pre-release `false`; name `Python 3.14.3`.
- Official read-only release-files API:
  `https://www.python.org/api/v2/downloads/release_file/?release=1090`.
- Selected artifact API resource:
  `https://www.python.org/api/v2/downloads/release_file/5464/`.
- Selected release-page row: `Windows installer (64-bit)`, operating system
  `Windows`, description `Recommended`, displayed size `28.8 MB`.
- Exact selected artifact URL, reached from the official release material:
  `https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe`.
- Exact filename: `python-3.14.3-amd64.exe`.
- Official index byte size: 30,213,192.
- Official release-page SHA-256:
  `b68ad91421afbbd1a628105199c8c5f6179b21ba799067a8d8c0bbac3b7defb0`.
- Official Sigstore bundle URL:
  `https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe.sigstore`.
- Official SPDX URL:
  `https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe.spdx.json`.
- Official certificate and detached-signature URLs:
  `https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe.crt` and
  `https://www.python.org/ftp/python/3.14.3/python-3.14.3-amd64.exe.sig`.

The selected official release-files API object states name
`Windows installer (64-bit)`, description `Recommended`, operating-system
resource `https://www.python.org/api/v2/downloads/os/1/`, exact artifact URL,
byte size 30,213,192, the exact SHA-256 above, and the exact Sigstore,
certificate, signature, and SPDX URLs above. This raw API object removes any
dependence on search-result text or on the release page's client-side rendering.

The official SPDX package record independently states:

- package name `CPython`;
- version `3.14.3`;
- package filename `python-3.14.3-amd64.exe`;
- the exact artifact URL above;
- originator and supplier `Organization: Python Software Foundation`;
- the same lowercase SHA-256 as the release page.

The downloaded Sigstore bundle is media type
`application/vnd.dev.sigstore.bundle.v0.3+json`. Its Rekor canonicalized body
names algorithm `sha256` and the same artifact digest. Its tlog entry reports
log index `908836872` and integrated time `1770143366`. The bundle was retained
as supplementary provenance evidence, but no Sigstore verification tool was
installed and this record does not claim independent cryptographic verification
of the bundle.

`OFFICIAL_RELEASE_IDENTITY_ESTABLISHED: YES`

`OFFICIAL_ARTIFACT_URL_ESTABLISHED: YES`

## 5. Retained Source Objects

The following non-secret objects remain outside Git in the staging directory.
Each corresponding `*.headers.txt` object retains its HTTP response headers.

| Object | Bytes | Lowercase SHA-256 |
| --- | ---: | --- |
| `release-page.html` | 11,344 | `e5ca3d1543f520e3c1ae84e933e2d0b467d7dba7c4ec3aa728f53bd693ff4890` |
| `release-page.html.headers.txt` | 1,269 | `505570e7e970ee308cb4a1fd2a60cb03dc6c55fb90397d1e3959714b649c0e66` |
| `ftp-index.html` | 9,701 | `8dd8163dee9f0834b8d4d83aa37de2a0723ddb695c4f28cf43bce2eb61846418` |
| `ftp-index.html.headers.txt` | 544 | `7a56f5158681a24be3dd4d9a54ab30d769f8d236231e370c0ff0b79221b58796` |
| `installer-doc.html` | 195,470 | `ad756d58a4bdd46a9d7b75b54ce29df82c3d1907cc5a2de4929d2870760bb2e6` |
| `installer-doc.html.headers.txt` | 558 | `2e9ffbb552c406e72e474e33aaf11fd54defb2e7f632babb91efebc2e53c3540` |
| `release-api.json` | 360 | `632a1bce1f53e5d631c209c714d77de2d95200b76774c9d337e8bb302e6d020d` |
| `release-api.json.headers.txt` | 1,161 | `b01c3f956dfc9bd546b092c741843e1632664a1ec577a5925e21b6b2ecbb261b` |
| `release-files-api.json` | 11,468 | `ef2466682f3c2f71fab43cc4108ee68420905a9a97633a8d0d968d865f0d5c82` |
| `release-files-api.json.headers.txt` | 1,162 | `b6884692e1c299761711e02f07a86d938c4b69cbd73ded2638ff68b58f5ef91a` |
| `python-3.14.3-amd64.exe.sigstore` | 5,311 | `37322efd3e2864638a3d953c9143f30b367f430d725dbecd53a2340545f66215` |
| `python-3.14.3-amd64.exe.spdx.json` | 35,157 | `0ca22587ecc26c7942124c76bbcd6b5cfc24cc425eee4eefd450347836bed9de` |
| `python-3.14.3-amd64.exe.crt` | 1,035 | `2d0baa59ade210bc0bd7d2fa32796c96e48225ff477adbe3c8618fc9044727cb` |
| `python-3.14.3-amd64.exe.sig` | 97 | `ac13e445f4c8fa4bf7e6ebab38b76bb27932c683c309e2a3a0e22d0e02974d0d` |

The four sidecar header-object digests not shown in the table are:

- Sigstore headers:
  `8faa360f96e032333f6a42ed7856d256053a0f702b29b149443546309bf1fb6d`;
- SPDX headers:
  `694ea37878c18ad34597fc8b6aa136e34974d5f8c560da3a599b1dab8747413a`;
- certificate headers:
  `299057ba17332011466f3e0c8e5b01b269793b26a23935f27ea29a500e78db38`;
- detached-signature headers:
  `9918bac358b16598c58ffc66e58eb365dd27fbe65afcdebe9adff4cd458b9c65`.

## 6. Exact Installer Artifact

- Local non-executed evidence path:
  `C:\Users\mine0\Downloads\weaver-evidence\cpython-3.14.3-amd64-20261005\python-3.14.3-amd64.exe`.
- HTTP final URL: exact artifact URL in section 4.
- HTTP status: 200.
- Content-Type: `application/octet-stream`.
- Content-Length and downloaded byte count: 30,213,192.
- HTTP Last-Modified: 2026-02-03T18:02:32Z.
- EXE response-header object SHA-256:
  `d8066911e91d4cce52350922a29ea8def274ef8aef22e12ad280c41b819d3f20`.
- SHA-256 from PowerShell `Get-FileHash`:
  `b68ad91421afbbd1a628105199c8c5f6179b21ba799067a8d8c0bbac3b7defb0`.
- SHA-256 independently recomputed by Windows `certutil -hashfile ... SHA256`:
  `b68ad91421afbbd1a628105199c8c5f6179b21ba799067a8d8c0bbac3b7defb0`.
- Official release-page and SPDX digest comparison: exact match.
- Observed version-resource company: `Python Software Foundation`.
- Observed product name: `Python 3.14.3 (64-bit)`.
- Observed product/file version: `3.14.3150.0`.
- Observed original filename: `python-3.14.3-amd64.exe`.
- PE bootstrapper machine: `0x014c` and optional-header magic `0x010b`.
  This describes the signed bootstrapper executable and does not override the
  official 64-bit package identity or product metadata.

The artifact bytes were read for hashing, metadata, PE certificate-table, and
signature inspection only. They were never launched or loaded as executable
code.

`ARTIFACT_DOWNLOADED: YES`

`ARTIFACT_EXECUTED: NO`

## 7. Authenticode Evidence

Inspection method: PowerShell `Get-AuthenticodeSignature`, .NET PKCS#7
read-only parsing of the PE certificate table, and .NET `X509Chain` with online
revocation mode. Validation was performed against the exact artifact SHA-256 in
section 6.

Observed Authenticode result:

- Status: `Valid`.
- Status message: signature verified.
- Signature type: `Authenticode`.
- Authenticode digest algorithm OID: `2.16.840.1.101.3.4.2.1` (SHA-256).
- Signature algorithm OID: `1.2.840.113549.1.1.1` (RSA).
- PKCS#7 content type: `1.3.6.1.4.1.311.2.1.4`.
- Signer subject:
  `CN=Python Software Foundation, O=Python Software Foundation, L=Beaverton, S=Oregon, C=US`.
- Signer issuer:
  `CN=Microsoft ID Verified CS EOC CA 02, O=Microsoft Corporation, C=US`.
- Signer serial: `330006CB566FE0765FE940215600000006CB56`.
- Signer certificate SHA-1 thumbprint:
  `AB0D2A5429F749A63EF2197B112857BEA6767CB0`.
- Signer certificate raw-byte SHA-256:
  `90dab465b4d56846e2f0d186f5cabb3891d5b3d8ffd0d8741525b35f4b559146`.
- Signer validity UTC: 2026-02-03T08:28:47Z through
  2026-02-06T08:28:47Z.
- Signer EKU includes code signing OID `1.3.6.1.5.5.7.3.3`.

RFC 3161 timestamp evidence:

- Unsigned-attribute OID: `1.3.6.1.4.1.311.3.3.1`.
- Timestamp content type: `1.2.840.113549.1.9.16.1.4`.
- Timestamp generation time UTC: 2026-02-03T17:47:27.540Z.
- Timestamp policy OID: `1.3.6.1.4.1.601.10.3.1`.
- Timestamp message-imprint algorithm: SHA-256 OID
  `2.16.840.1.101.3.4.2.1`.
- Timestamp message imprint:
  `e0a85a86631165c1b9ab53e3bd3f477f2390b704c2569e738bfcbc991b3510c1`.
- Timestamp signer subject:
  `CN=Microsoft Public RSA Time Stamping Authority, OU=nShield TSS ESN:7800-05E0-D947, OU=Microsoft America Operations, O=Microsoft Corporation, L=Redmond, S=Washington, C=US`.
- Timestamp signer issuer:
  `CN=Microsoft Public RSA Timestamping CA 2020, O=Microsoft Corporation, C=US`.
- Timestamp signer serial:
  `330000005724D395E0A2E9C931000000000057`.
- Timestamp certificate SHA-1 thumbprint:
  `FD2F31399C42510141364ACDF168A28F5C79CBC3`.
- Timestamp certificate raw-byte SHA-256:
  `f53c9f64b5056e4c65886ca2cee1fd5550e954536f404421290d99854c78db52`.
- Timestamp certificate validity UTC: 2025-10-23T20:46:53Z through
  2026-10-22T20:46:53Z.
- Timestamp EKU: time stamping OID `1.3.6.1.5.5.7.3.8`.

Chain disposition:

- Signer chain evaluated at the RFC 3161 timestamp: `True`, no chain status
  error. Elements: Python Software Foundation signer; Microsoft ID Verified CS
  EOC CA 02; Microsoft ID Verified Code Signing PCA 2021; Microsoft Identity
  Verification Root Certificate Authority 2020.
- Timestamp chain evaluated at collection time: `True`, no chain status error.
  Elements: Microsoft Public RSA Time Stamping Authority; Microsoft Public RSA
  Timestamping CA 2020; Microsoft Identity Verification Root Certificate
  Authority 2020.
- Signer chain evaluated naively at collection time: `False`, `NotTimeValid`,
  because the short-lived signer certificate had expired. This is retained as a
  non-substitutable observation. It does not negate the recorded Windows
  Authenticode `Valid` result because the RFC 3161 time is within signer
  validity and both signing-time and timestamp chains validated.

Publisher comparison: the signer subject is Python Software Foundation and
matches the official SPDX originator/supplier and official python.org release
context. This establishes artifact publisher/source compatibility for this
bounded record. It does not establish truth, authority, Admission, or a future
key identity.

`AUTHENTICODE_ACCEPTED: YES`

## 8. Future Root Observation

- Intended exact future root:
  `C:\Program Files\WeaverForge\Python314`.
- Observation UTC: 2026-10-05T10:39:16.9855449Z.
- Exact target exists: `False`.
- Parent `C:\Program Files\WeaverForge` exists: `False`.
- `C:\Program Files` existed and was observed as an ordinary directory with no
  PowerShell-reported link type or target.
- No directory was created, deleted, cleaned, resolved through a new link, or
  ACL-modified.

This observation supports the D0-R1 `absent` branch only at the stated instant.
It is not reusable as the installation-time pristine-root record. A later
privileged installation session must repeat and independently bind the full M1
pre-install observation immediately before execution. If the root or relevant
path topology then exists unexpectedly, the result is
`BLOCKED_PRISTINE_ROOT` and nothing may be cleaned or overwritten under this
record.

`FUTURE_ROOT_OBSERVATION: ABSENT_AT_OBSERVATION_TIME`

## 9. Frozen Future Install Invocation

The command below is a record for a later separately authorized privileged
installation. It was not executed. The argument vector is authoritative; line
breaks are presentation only.

```text
C:\Users\mine0\Downloads\weaver-evidence\cpython-3.14.3-amd64-20261005\python-3.14.3-amd64.exe
/quiet
/log
C:\ProgramData\WeaverForge\Evidence\CPython3143\install.log
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

The option names are grounded in the retained official Python 3.14 Windows
installer documentation at
`https://docs.python.org/3.14/using/windows.html`. `Include_freethreaded=0` is
explicit because official 3.14 documentation identifies it as the option for
additional free-threaded binaries.

Explicit non-options and rationale:

- `/passive`, `/simple`, `/uninstall`, and `/layout` are not passed; this is a
  quiet install, not progress UI, simplified UI, uninstall, or layout mode.
- `DefaultAllUsersTargetDir`, `DefaultJustForMeTargetDir`, and
  `DefaultCustomTargetDir` are not passed because exact `TargetDir` is supplied;
  the latter two also do not select this all-users non-UI target.
- `SimpleInstallDescription` is not passed because `SimpleInstall=0`.
- No option is supplied through an adjacent `unattend.xml` file. The later
  session must prove no such file can influence invocation.

Before later execution, the privileged session must:

1. independently rehash the exact EXE and require the section 6 digest;
2. repeat Authenticode validation and freshness checks;
3. repeat the D0-R1 pristine-root observation;
4. create and bind the log parent under the separately authorized operation;
5. record the exact ordered process argument vector, elevation context,
   environment delta, start/end times, exit code, reboot indication, and log
   SHA-256;
6. establish that no adjacent configuration or caller-supplied value changes
   these options.

No installer defaults are silently relied upon for selected installation
features. The exact argument vector is frozen for later review and separate
authorization, not authorized for execution by this record.

`INSTALL_INVOCATION_FROZEN_FOR_LATER: YES`

## 10. Post-install Fields

No value in this section may be populated from the current machine,
PythonManager, PATH, Store aliases, or any pre-existing Python.

| Field | Status |
| --- | --- |
| installed `python.exe` path, size, hash, identity, version, and signature | `PENDING_POST_INSTALL` |
| installed `python314.dll` path, size, hash, identity, version, and signature | `PENDING_POST_INSTALL` |
| installed interpreter version, architecture, implementation, GIL, and build facts | `PENDING_POST_INSTALL` |
| `sys.executable`, `sys.prefix`, `sys.base_prefix`, `sys.exec_prefix`, and `sys.base_exec_prefix` | `PENDING_POST_INSTALL` |
| protected-root owner, DACL, effective non-write result, and path topology | `PENDING_POST_INSTALL` |
| installer completion and closed installer-to-baseline interval | `PENDING_POST_INSTALL` |
| startup/import customization inspection and provenance classification | `PENDING_POST_INSTALL` |
| complete `cp314-base-prefix-manifest-v0` rows, count, and digest | `PENDING_POST_INSTALL` |
| independent post-install recomputation | `PENDING_POST_INSTALL` |
| successor helper source, helper root, commit, test, and deployment bindings | `PENDING_POST_IMPLEMENTATION` |

`POST_INSTALL_FIELDS: PENDING_POST_INSTALL`

## 11. Independent Recomputation and Limitations

Completed pre-install recomputation:

- EXE size matched the official index and HTTP Content-Length.
- PowerShell and `certutil` independently produced the same SHA-256.
- The digest matched the official release-page value, official SPDX package
  value, and the retained Sigstore bundle's canonicalized Rekor body value.
- Filename, URL, version, and PSF originator/supplier matched across the release
  page, index, SPDX, EXE version resource, and Authenticode signer.
- Authenticode, RFC 3161, signing-time chain, and timestamp chain predicates were
  separately recorded rather than collapsed into a single `Valid` label.

Limitations and freshness:

- The downloaded Sigstore bundle was parsed and retained but not independently
  cryptographically verified because no preinstalled verifier was available and
  dependency changes were prohibited.
- The staging directory is not asserted immutable or protected.
- Root absence is point-in-time evidence, not installation authorization.
- All installed-state, ACL, runtime, baseline, and post-install recomputation
  facts do not yet exist.
- A separate reviewer must recompute this record from retained bytes; AI
  agreement is not evidence and this batch is not independent reproduction.
- Any artifact, trust-store, revocation, source, staging-path, invocation,
  machine, or future-root change makes the affected predicate stale.

These limitations do not substitute current-machine values and do not convert
the bounded installer evidence into post-install evidence.

## 12. Authority Boundaries and Negative State

`FINAL_PIN_VALUES_ESTABLISHED: NO`

`PYTHON_INSTALLED: NO`

`ACCOUNT_OR_ACL_CHANGED: NO`

`VENV_CREATED: NO`

`IMPLEMENTATION_PERFORMED: NO`

`PRE_REAL_ENVIRONMENT_ESTABLISHED: NO`

`REAL_KEY_GENERATION_AUTHORIZED: NO`

`REAL_KEY_GENERATED: NO`

`REAL_PASSPHRASE_CREATED: NO`

`ADMISSION_PERFORMED: NO`

`DOWNLOADED_BINARY_COMMITTED: NO`

Evidence is not authority. A valid signature is not truth or authorization.
This record is not Human Final, PRE_REAL readiness, implementation approval,
installation approval, key-generation authorization, signer trust, identity,
role, Admission, or deployment permission.

## 13. Stop and Recommended Next Step

STOP before installation. The next permissible step is one bounded independent
review of this pre-install evidence record and retained bytes. Only after that
review may a Human separately decide whether to authorize the privileged
installation and post-install evidence session defined by D0-R1.
