# INR-HER MinGit Windows x64 MSVC ABI Offset Follow-Up Evidence

Record date: 2026-10-12 (Asia/Tokyo)
Status: ABI_OFFSET_FOLLOWUP_FILES_REVIEWED_FULL_INR_NOT_READY
Scope: one documentation-only preservation of three transferred follow-up measurement files
Decision source: the Human explicit approval to review this follow-up evidence and to preserve the review as documentation only.
Provenance split: a separate user-run measurement produced the three files. Cursor reviewed those transferred files, computed their SHA-256 values, and compared include paths with the two earlier compile logs. Cursor did not run the compiler, did not open the SDK package, did not hash header bytes, and did not inspect the measuring PC.

This record does not copy an SDK package, an executable, or an object file into Git. It does not edit a frozen document. It does not compile, download, extract, install, or launch an SDK or a compiler. It does not grant an operational SDK pin, an operational MinGit pin, production authority, or execution authority. FULL_INR_READY=NO.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: 852975a8fd70981fae69cf1c9bd3f2cabbde724c
Cursor-verified Git HEAD before this record: 852975a8fd70981fae69cf1c9bd3f2cabbde724c
HEAD comparison: MATCH.
HEAD subject: docs: record limited human acceptance of the off-host ABI measurement evidence
Remote tracking branch origin/her/inr-her-mingit-eb0 before this record: 852975a8fd70981fae69cf1c9bd3f2cabbde724c. MATCH.

Cursor-verified tracked status before this record: no tracked path differed from HEAD. git status --porcelain=v1 reported only the pre-existing untracked .wacp/ tree. This record does not read, stage, edit, or delete any .wacp/ path.

Cursor-verified SHA-256 values of the frozen documents, measured from current file bytes before this record. Each value matches the hash already recorded in docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFHOST_MEASUREMENT_EVIDENCE_LIMITED_HUMAN_ACCEPTANCE.md. These are documentation-file hashes. They are not nupkg or header hashes. Working-tree blobs equal the HEAD blobs. This record does not edit these documents:

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
- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE_LIMITED_HUMAN_ACCEPTANCE.md: 25dbd4b0faad4209515e607a08a22e38f0c31bbd01e2821f3014d12c6b1d7322. MATCH. Working-tree blob equals HEAD blob 7d2faac4f5c39d67c0192754a670ad16545d9b05.

The two off-host evidence documents are tracked at this HEAD. Cursor remeasured them before this record and did not edit them:

- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFHOST_MEASUREMENT_EVIDENCE.md: ad4aec65f7ee429ca70c52cc24e6346b1ff7edb72171a1dff357b1ec0497d594. MATCH with the hash recorded by its limited human acceptance. Working-tree blob equals HEAD blob cbb351d41226ab7a1bfc166144f40a53ae5d9df5.
- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFHOST_MEASUREMENT_EVIDENCE_LIMITED_HUMAN_ACCEPTANCE.md: f16158a4532c52dcb7b04ba303c7a329c32a43c01b5ab26b992c74215c2c200f. Working-tree blob equals HEAD blob 1032d97c3a4893e1597d6b57c78e8c6ac1b16eba. That acceptance document does not publish its own file hash.

## 2. Transferred files

The batch named the evidence directory C:/dev/_tmp/weaver-abi-evidence-20261012/followup. That path was absent. The three files whose SHA-256 values match the expected digests are in C:/dev/_tmp/weaver-abi-evidence-20261012/abi-followup-20261012. That directory contains only these three files. The compiler log names the measuring-PC source as C:\ABI-Verification\abi-followup-20261012\abi_offsets.cpp.

Cursor computed SHA-256 independently from the bytes in that directory. Each digest matches the digest named for this batch.

| File | Size in bytes | SHA-256 |
| --- | ---: | --- |
| abi_offsets.cpp | 1390 | f1955ed33ca81eaad2cfd99fd6d50f2791ba422f165e3c4f54a799662dcfa514 |
| abi_offsets.log | 32547 | 1e5632f54348683c2b2f14733cec7ce94a60d57e1903178fa55a50f258f9f000 |
| include_hashes.txt | 23426 | 99709fd72298e4cff9a66dffd9ad5fbb98677ccd7462af95c805ce6db1c7c37e |

abi_offsets.cpp is CRLF, with no byte-order mark. abi_offsets.log is UTF-8 with a byte-order mark and CRLF, 255 lines. include_hashes.txt is CRLF, with no byte-order mark, 159 lines.

These three files stay outside Git. This record quotes measurements taken from them. It does not vendor their bytes.

The two earlier logs used for the path comparison remain in the parent directory C:/dev/_tmp/weaver-abi-evidence-20261012. Cursor remeasured them before the comparison. Both digests match the hashes already recorded in the off-host measurement evidence:

| File | SHA-256 |
| --- | --- |
| abi_compile.log | 13bf90c26a5e8c9c54cdeb60bb31ae4ef96d5b4acd86035ca0a183ce9aea73fe |
| abi_layout_probe.log | 0c8853c6592bb37bbb2f70300abc9a7ba19ff2e1a7b43b4f96313060ad999e3b |

Both earlier logs are UTF-16 LE with a byte-order mark, 237 lines each. Cursor decoded them as UTF-16 for the path comparison. Their bytes were not rewritten.

## 3. User-run measurement and Cursor review

The three follow-up files are a separate user-run measurement. Cursor's role is review of the transferred files. Cursor did not re-execute the measurement.

Conclusions in sections 4 through 6 are taken from abi_offsets.cpp, abi_offsets.log, include_hashes.txt, and from the include-path text of the two earlier logs. The earlier user-run statements of Windows 11 x64, Hostx64/x64 cl.exe, the SDK package SHA-256, and process exit codes are not lines in these three files. This record does not restate them as new measurements.

## 4. Seventeen member-offset diagnostics

abi_offsets.cpp includes windows.h, jobapi2.h, and stddef.h. It prints the stringized forms of WINAPI, _MSC_VER, _MSC_FULL_VER, _WIN32_WINNT, NTDDI_VERSION, and WINAPI_FAMILY. It forward-declares template <unsigned long long Offset> struct ABI_OFFSET and does not define it. It then declares seventeen variables through a MEASURE macro whose template argument is offsetof(type, field).

abi_offsets.log line 1 is abi_offsets.cpp. Lines 2 through 232 are 231 Japanese /showIncludes notes ("メモ: インクルード ファイル:"). Lines 233 through 238 are:

```
WINAPI_EXPANSION=__stdcall
MSC_VER=1950
MSC_FULL_VER=195035739
WIN32_WINNT=0x0A00
NTDDI_VERSION=0x0A000012
WINAPI_FAMILY=100
```

The log then ends with exactly seventeen error C2079 diagnostics. It contains no warning line and no other compiler diagnostic of the form error Cxxxx. One include note names shared\winerror.h. That path text is an include note.

The seventeen diagnostics, in log order, report these offsetof values. The symbol and source line in each diagnostic match the seventeen MEASURE lines in the transferred source, in the same order.

| Type | Member | offsetof | Source line |
| --- | --- | ---: | ---: |
| STARTUPINFOW | cb | 0 | 21 |
| STARTUPINFOW | dwFlags | 60 | 22 |
| STARTUPINFOW | hStdInput | 80 | 23 |
| STARTUPINFOW | hStdOutput | 88 | 24 |
| STARTUPINFOW | hStdError | 96 | 25 |
| STARTUPINFOEXW | StartupInfo | 0 | 27 |
| STARTUPINFOEXW | lpAttributeList | 104 | 28 |
| JOBOBJECT_BASIC_ACCOUNTING_INFORMATION | TotalUserTime | 0 | 30 |
| JOBOBJECT_BASIC_ACCOUNTING_INFORMATION | TotalProcesses | 36 | 31 |
| JOBOBJECT_BASIC_ACCOUNTING_INFORMATION | ActiveProcesses | 40 | 32 |
| JOBOBJECT_BASIC_LIMIT_INFORMATION | LimitFlags | 16 | 34 |
| JOBOBJECT_BASIC_LIMIT_INFORMATION | ActiveProcessLimit | 40 | 35 |
| JOBOBJECT_BASIC_LIMIT_INFORMATION | Affinity | 48 | 36 |
| JOBOBJECT_EXTENDED_LIMIT_INFORMATION | BasicLimitInformation | 0 | 38 |
| JOBOBJECT_EXTENDED_LIMIT_INFORMATION | IoInfo | 64 | 39 |
| JOBOBJECT_EXTENDED_LIMIT_INFORMATION | ProcessMemoryLimit | 112 | 40 |
| JOBOBJECT_EXTENDED_LIMIT_INFORMATION | JobMemoryLimit | 120 | 41 |

These seventeen C2079 lines are a failed compile used as a diagnostic measurement. They are not a passing compile. No object file for abi_offsets.cpp is in the transferred set. The log contains no process exit code.

The same log prints WINAPI_EXPANSION=__stdcall. That line is the preprocessor stringization of the WINAPI macro in this translation. The active replacement text of WINAPI in this translation is __stdcall. The log does not show the machine calling convention of a call. MSC_VER=1950, MSC_FULL_VER=195035739, WIN32_WINNT=0x0A00, NTDDI_VERSION=0x0A000012, and WINAPI_FAMILY=100 are the same configuration values previously printed by abi_compile.log. The log contains no compiler command line, no cl.exe path, and no Hostx64 text.

Each measured offsetof is below the sizeof previously recorded for that same type in abi_layout_probe.log. This batch did not remeasure those five sizeof or alignof values. Members other than the seventeen named fields remain unmeasured.

## 5. Include-hash file and path comparison

include_hashes.txt has 159 records. Every record is an uppercase 64-digit hexadecimal digest, two spaces, and one path. The file has 159 unique paths and 159 unique digests. No path is repeated. No digest is shared by two paths. The records are sorted by full path. That order is not the /showIncludes order.

Every path is under one of the two roots already permitted by the earlier logs:

- SDK include root, 151 unique paths: C:\ABI-Verification\SDK-10.0.28000.2705\c\Include\10.0.28000.0\
- MSVC toolset include root, 8 unique paths: C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Tools\MSVC\14.50.35717\include\

The 151 SDK paths divide into shared 38, ucrt 13, and um 100. The eight MSVC basenames are concurrencysal.h, excpt.h, limits.h, sal.h, stdarg.h, vadefs.h, vcruntime.h, and vcruntime_string.h. The file does not name intrin.h. No path falls outside those two roots.

abi_offsets.log has 231 /showIncludes notes: 223 under the SDK include root and 8 under the MSVC include root. Those 231 notes name 159 unique paths. The unique-path set equals the 159 paths in include_hashes.txt.

Cursor compared that set with the two earlier logs in the parent evidence directory. abi_compile.log and abi_layout_probe.log each contain 231 /showIncludes notes. The three note sequences are identical, line for line, after decoding the earlier logs as UTF-16 LE and the follow-up log as UTF-8. The unique-path set of each earlier log is the same 159 paths. No path in include_hashes.txt is absent from those logs, and no unique path in those logs is absent from include_hashes.txt.

The path comparison identifies the files named by the earlier translations and by this translation. It does not recompute the digest of any header. Cursor did not hash the SDK package in this batch. Package-byte equality of the 159 header digests remains UNVERIFIED. This record does not claim that those header hashes match the original package.

A /showIncludes path shows where the compiler opened a file during that translation. Directory tokens 10.0.28000.2705, 10.0.28000.0, and 14.50.35717 remain path text.

## 6. What remains unverified

The following stay OPEN. This record does not close them.

- Header digest bytes against the original package: UNVERIFIED. Section 5 records path identity with the two earlier logs and records the digests as transferred text. Cursor did not hash the headers or the nupkg.
- Struct members outside the seventeen named fields: NOT MEASURED. The five earlier sizeof and alignof pairs were not remeasured in this log.
- Machine meaning of WINAPI=__stdcall: NOT SHOWN. The replacement text is measured. The log does not show a call sequence or a disassembly.
- Compiler command line, Hostx64/x64 cl.exe, and the process exit code of this translation: NOT IN THE THREE FILES.
- Windows 11 x64 and the stated SDK package SHA-256: NOT REMEASURED. No transferred follow-up file contains an OS version string or a package digest.
- Object code for abi_offsets.cpp: NOT TRANSFERRED.
- Host Job behavior, runtime isolation, operational MinGit PIN, SDK operational PIN, and real execution binding: OPEN. Nothing in the three files runs a Job, launches MinGit, or binds execution. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. EXECUTION_BINDING_REAL remains UNEXECUTED.
- Third-party independent verification: NONE. No second provider remeasured the compiler, the headers, or the package.
- Full ABI ratification: not granted.
- Production authority: not granted. Runtime authority: not granted.
- FULL INR readiness: NO. FULL_INR_READY=NO.

## 7. Batch boundary

This batch adds one documentation path and edits nothing else. It does not stage, commit, or push. .wacp/ remains untracked and excluded. No frozen document is edited. No SDK package, executable, or object file is added to Git.

COMMITTED: NO
PUSHED: NO
FULL_INR_READY: NO
