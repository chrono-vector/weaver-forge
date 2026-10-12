# INR-HER MinGit Windows x64 MSVC ABI Off-Host Measurement Evidence

Record date: 2026-10-12 (Asia/Tokyo)
Status: OFFHOST_ABI_MEASUREMENT_FILES_REVIEWED_FULL_INR_NOT_READY
Scope: one documentation-only preservation of five transferred off-host ABI measurement files
Decision source: the Human explicit approval to preserve this completed off-host measurement as documentation only.
Provenance split: a separate user-controlled PC produced the measurement. Cursor reviewed the five transferred files and computed their SHA-256 values. Cursor did not run the compiler, did not open the SDK package, and did not inspect that PC.

This record does not copy an SDK package, an executable, or an object file into Git. It does not edit a frozen document. It does not compile, download, extract, install, or launch an SDK or a compiler. It does not grant an operational SDK pin, an operational MinGit pin, production authority, or execution authority. FULL_INR_READY=NO.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: 893a023ad8abb9db9de9a0fbd5a1c57cead20af4
Cursor-verified Git HEAD before this record: 893a023ad8abb9db9de9a0fbd5a1c57cead20af4
HEAD comparison: MATCH.
HEAD subject: docs: record limited human acceptance of the Windows x64 MSVC-compatible ABI measurement profile

Cursor-verified tracked status before this record: no tracked path differed from HEAD. git status --porcelain=v1 reported only the pre-existing untracked .wacp/ tree. This record does not read, stage, edit, or delete any .wacp/ path.

Cursor-verified SHA-256 values of the frozen documents, measured from current file bytes before this record. Each value matches the hash already recorded in docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE_LIMITED_HUMAN_ACCEPTANCE.md, or, for the profile document itself, the hash recorded in that acceptance. These are documentation-file hashes. They are not nupkg or header hashes. Working-tree blobs equal the HEAD blobs. This record does not edit these documents:

- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE.md: 5b4537bbcb416c2d23ef0a2e232ed39346ba32b18f0e05e466722248af61f12a. MATCH. Working-tree blob equals HEAD blob a353aee296be3a2c162f731188ac8aae665d8a8c.
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md: b99bf685afcae6db1e17c3a3421bb4056e2b77860048ad08a955c6d0f15cf446. MATCH. Working-tree blob equals HEAD blob d8b29a16f12251c41d390db88561bea9d1a46568.
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md: b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175. MATCH. Working-tree blob equals HEAD blob 1a4cc88533625fd697e5e079a8899b6e2dde45e1.
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE_LIMITED_HUMAN_ACCEPTANCE.md: 097a5928f0e775d4d3343b516c7e2a1fd8fd98716972e74480dbd752f414e072. MATCH. Working-tree blob equals HEAD blob b360e2f7ef52275b4f7a1f654202988ef0446bf8.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3. MATCH. Working-tree blob equals HEAD blob 65b39aaf4bf4348ab0c55bc108d80132d89a59b7.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543. MATCH. Working-tree blob equals HEAD blob 7b47048534476cadf9064b39d4001b7e4aae6422.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md: 61156b5edb2b36589b45502a3f43a16330816dc65deef05d94728b65d891191b. MATCH. Working-tree blob equals HEAD blob 40e44e61c40ad55b7510a962516f5ed36a6dd285.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786. MATCH. Working-tree blob equals HEAD blob 5e6cd8fba922b58bf3cfc311debbe8253acfb8a6.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b. MATCH. Working-tree blob equals HEAD blob 8f0be60ecfd55aa14074a0700a6553c517ea5f55.
- docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md: 5621cd7b1cf86bf4bb2b3c385237d23bb95edc99663ebb573d5a9b043bcec6fe. MATCH. Working-tree blob equals HEAD blob efa733c65c10abcae2138c6d1f16bfad0c91dbf3.
- docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294. MATCH. Working-tree blob equals HEAD blob 47d4ece6622c8968939afeda3ed091910b883446.
- docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md: 64f45f7b55af23fe173e8ad22db4e3516e4df91d4133331c4eb9be3dbe01bc56. MATCH. Working-tree blob equals HEAD blob 2f084c87686216f3c325423c5e80d41a50fafdf8.
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md: a782d866319a7870e955f88e236dfd5853126811055eefc00590cee023c6be11. MATCH. Working-tree blob equals HEAD blob 861afbc33f36e7ae5caa414f15f9deb15277d860.

The profile acceptance document does not record its own file hash. Cursor measured its current bytes before this record and did not edit it:

- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE_LIMITED_HUMAN_ACCEPTANCE.md: 25dbd4b0faad4209515e607a08a22e38f0c31bbd01e2821f3014d12c6b1d7322. Working-tree blob equals HEAD blob 7d2faac4f5c39d67c0192754a670ad16545d9b05. This batch does not treat that hash as a previously published self-digest.

## 2. Transferred files

External evidence directory, outside this Git worktree: C:/dev/_tmp/weaver-abi-evidence-20261012

Cursor computed SHA-256 independently from the bytes in that directory. Each digest matches the digest named by the Human approval for this batch. No file was missing.

| File | Size in bytes | SHA-256 |
| --- | ---: | --- |
| abi_compile.log | 47358 | 13bf90c26a5e8c9c54cdeb60bb31ae4ef96d5b4acd86035ca0a183ce9aea73fe |
| abi_layout_probe.cpp | 750 | 67c954b325a7c45b80f7c6d42bf2f961b93ddd1316a056d69dff60094c4e8472 |
| abi_layout_probe.log | 48442 | 0c8853c6592bb37bbb2f70300abc9a7ba19ff2e1a7b43b4f96313060ad999e3b |
| abi_probe.c | 1647 | 4c8e892ab782769703050546077fbf327628d402a2a24fcdcccf92f2a6cf1c69 |
| abi_probe.obj | 657 | fd631425d7054a2b7b682ce8c1fb315f4490f532283572f6a0ad1fab5c268b92 |

These five files stay outside Git. This record quotes measurements taken from them. It does not vendor their bytes.

## 3. User-run statement and Cursor review

The Human approval for this batch states the measurement environment:

- Host: Windows 11 x64, on a separate user-controlled PC.
- Compiler invocation stated by that approval: MSVC 14.50.35717, Hostx64/x64 cl.exe.
- SDK package stated by that approval: Microsoft.Windows.SDK.CPP 10.0.28000.2705.
- Separate SDK package SHA-256 stated by that approval: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807.

Cursor did not re-execute the measurement. Cursor did not hash that SDK package in this batch. The stated package SHA-256 is numerically equal to the package SHA-256 already preserved as a prior Grok Build report in the frozen static-evidence documents. Numerical equality is not a new package measurement and is not third-party verification.

Conclusions in sections 4 through 6 are taken from the five transferred files. Where a fact is only the user-run statement above, this record says so.

## 4. Initial C translation

Transferred source abi_probe.c includes windows.h and jobapi2.h. It rejects the translation unless _WIN64, _M_X64, and _MSC_VER are defined, by #error with the texts "Expected _WIN64", "Expected _M_X64", and "Expected MSVC-compatible compiler". It emits #pragma message lines for _MSC_VER, _MSC_FULL_VER, and, when defined, _WIN32_WINNT, NTDDI_VERSION, and WINAPI_FAMILY. It contains these compile-time assertions, each as a typedef char array of length 1 or -1:

- sizeof(void*) == 8
- sizeof(HANDLE) == 8
- sizeof(SIZE_T) == 8
- sizeof(int) == 4
- sizeof(long) == 4
- sizeof(short) == 2

It also names typedefs of STARTUPINFOW, STARTUPINFOEXW, JOBOBJECT_BASIC_ACCOUNTING_INFORMATION, JOBOBJECT_BASIC_LIMIT_INFORMATION, and JOBOBJECT_EXTENDED_LIMIT_INFORMATION, and defines abi_probe to return the sum of their sizeof results cast to int.

abi_compile.log has 237 lines. Line 1 is abi_probe.c. Lines 2 through 232 are 231 Japanese /showIncludes notes ("メモ: インクルード ファイル:"). Lines 233 through 237 are:

```
ABI _MSC_VER=1950
ABI _MSC_FULL_VER=195035739
ABI _WIN32_WINNT=0x0A00
ABI NTDDI_VERSION=0x0A000012
ABI WINAPI_FAMILY=100
```

The log contains no line with "error" and no line with "warning". It does not contain the three #error texts. It does not contain a compiler command line, a cl.exe path, the text Hostx64, or a process exit code.

The user-run statement records the initial C compile exit code as 0. That numeral is not a line in the five files. The transferred log is consistent with a diagnostic-free completion of the messages above. The transferred object is the generated object for that translation, as follows.

abi_probe.obj is 657 bytes. Its first two bytes are 64 86, the little-endian COFF machine field 0x8664. ASCII strings in the object include "Microsoft (R) Optimizing Compiler", "abi_probe", "C:\ABI-Verification\abi_probe.obj", ".text$mn", ".drectve", and the directive text /DEFAULTLIB:"uuid.lib" /DEFAULTLIB:"uuid.lib" /DEFAULTLIB:"LIBCMT" /DEFAULTLIB:"OLDNAMES". The object does not contain the text Hostx64 or cl.exe. Cursor did not link or execute it.

## 5. Diagnostic layout translation

Transferred source abi_layout_probe.cpp includes windows.h and jobapi2.h. It forward-declares template <unsigned long long Size, unsigned long long Alignment> struct ABI_MEASUREMENT and does not define it. It then declares five variables whose template arguments are sizeof and alignof of STARTUPINFOW, STARTUPINFOEXW, JOBOBJECT_BASIC_ACCOUNTING_INFORMATION, JOBOBJECT_BASIC_LIMIT_INFORMATION, and JOBOBJECT_EXTENDED_LIMIT_INFORMATION.

abi_layout_probe.log has 237 lines. Line 1 is abi_layout_probe.cpp. Its 231 /showIncludes notes are identical, line for line, to the 231 notes in abi_compile.log. The log then ends with exactly five diagnostics and no warning line:

```
C:\ABI-Verification\abi_layout_probe.cpp(10): error C2079: 'measure_startupinfow' が 未定義の struct 'ABI_MEASUREMENT<104,8>' で使用しています。
C:\ABI-Verification\abi_layout_probe.cpp(15): error C2079: 'measure_startupinfoexw' が 未定義の struct 'ABI_MEASUREMENT<112,8>' で使用しています。
C:\ABI-Verification\abi_layout_probe.cpp(20): error C2079: 'measure_job_accounting' が 未定義の struct 'ABI_MEASUREMENT<48,8>' で使用しています。
C:\ABI-Verification\abi_layout_probe.cpp(25): error C2079: 'measure_job_limit' が 未定義の struct 'ABI_MEASUREMENT<64,8>' で使用しています。
C:\ABI-Verification\abi_layout_probe.cpp(30): error C2079: 'measure_job_extended' が 未定義の struct 'ABI_MEASUREMENT<144,8>' で使用しています。
```

The template arguments reported by those C2079 diagnostics are the measured size and alignment:

| Type | sizeof | alignof |
| --- | ---: | ---: |
| STARTUPINFOW | 104 | 8 |
| STARTUPINFOEXW | 112 | 8 |
| JOBOBJECT_BASIC_ACCOUNTING_INFORMATION | 48 | 8 |
| JOBOBJECT_BASIC_LIMIT_INFORMATION | 64 | 8 |
| JOBOBJECT_EXTENDED_LIMIT_INFORMATION | 144 | 8 |

The user-run statement records this layout compile exit code as 2 and states that exit code 2 is intentional. That numeral is not a line in the five files. The five C2079 lines are a failed compile. They are not a passing compile. No object file for abi_layout_probe.cpp is in the transferred set.

The diagnostics report aggregate size and alignment only. They do not report member offsets.

## 6. Include paths and provenance boundaries

Both logs report 231 includes and no path outside these two roots:

- SDK directory root, 223 includes: C:\ABI-Verification\SDK-10.0.28000.2705\c\Include\10.0.28000.0\
- MSVC toolset include root, 8 includes: C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717\include\

The eight MSVC includes, by basename, are excpt.h, vcruntime.h, sal.h, concurrencysal.h, vadefs.h, stdarg.h, vcruntime_string.h, and limits.h. excpt.h is reached from that MSVC include root. The logs do not list intrin.h.

SDK paths present in the same closure include, among others, um\windows.h, shared\winapifamily.h, shared\winpackagefamily.h, shared\sdkddkver.h, shared\windef.h, shared\minwindef.h, um\winnt.h, um\processthreadsapi.h, um\winbase.h, and um\jobapi2.h. The closure also includes shared\pshpack1.h, shared\pshpack2.h, shared\pshpack4.h, shared\pshpack8.h, and shared\poppack.h. The leaf count of unique included basenames is 159. A /showIncludes path shows where the compiler opened a file during that translation. It is not a content hash, and the order of the closure is not a measurement of which pack is in force at a particular struct definition.

Provenance boundaries supported by the transferred files:

- Probe sources and the generated object path are under C:\ABI-Verification\ on the measuring PC. The copies Cursor hashed are the five files in C:/dev/_tmp/weaver-abi-evidence-20261012.
- Headers under the SDK-10.0.28000.2705 directory are a directory tree named in the logs. The directory tokens 10.0.28000.2705 and 10.0.28000.0 are path text. They do not, by themselves, establish the nupkg bytes or the user-stated package SHA-256.
- Headers under VC\Tools\MSVC\14.50.35717\include are outside that SDK directory. The toolset directory name 14.50.35717 is path text in the logs. Together with the pragma values _MSC_VER=1950 and _MSC_FULL_VER=195035739, and the object string "Microsoft (R) Optimizing Compiler", that is the compiler identity the files support. The files do not contain the text Hostx64/x64 cl.exe. That invocation form remains the user-run statement.
- Windows 11 x64 remains the user-run host statement. No transferred file contains an OS version string.

## 7. What remains open

The following stay OPEN. This record does not close them.

- Full header closure and content hashes: NOT MEASURED. The logs name paths. They do not hash header bytes. Cursor did not hash the SDK package.
- Active WINAPI calling convention: NOT FULLY PROVEN. The files show WINAPI_FAMILY=100 and do not show which WINAPI replacement was active or its machine meaning.
- Struct member offsets: NOT MEASURED. Section 5 records sizeof and alignof only.
- Compiler flags and macro selection beyond the observed configuration: NOT RATIFIED. The observed printed configuration is _MSC_VER=1950, _MSC_FULL_VER=195035739, _WIN32_WINNT=0x0A00, NTDDI_VERSION=0x0A000012, and WINAPI_FAMILY=100, plus the assertion and #error results in section 4. No command line is in the logs.
- Host Job behavior, runtime isolation, operational MinGit PIN, SDK operational PIN, and real execution binding: OPEN. Nothing in the five files runs a Job, launches MinGit, or binds execution. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. EXECUTION_BINDING_REAL remains UNEXECUTED.
- Third-party independent verification: NONE. The measurement is a user-run on a separate PC. Cursor's role is review of the transferred files. No second provider remeasured the compiler, the headers, or the package.
- FULL INR readiness: NO. FULL_INR_READY=NO.

## 8. Batch boundary

This batch adds one documentation path and edits nothing else. It does not stage, commit, or push. .wacp/ remains untracked and excluded. No frozen document is edited. No SDK package, executable, or object file is added to Git.

COMMITTED: NO
PUSHED: NO
FULL_INR_READY: NO