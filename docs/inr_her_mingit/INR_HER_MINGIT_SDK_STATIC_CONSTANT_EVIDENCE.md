# INR-HER MinGit SDK Static Constant Evidence

Record date: 2026-10-11 (Asia/Tokyo)
Status: SDK_STATIC_CONSTANT_EVIDENCE_RECORDED
Scope: architecture-independent header expressions from one package measured by Grok Build
Decision source: the Human explicit approval to preserve this one documentation-only record.
Provenance repair: Human-approved documentation-only repair of measurement attribution. Technical values, source references, and conditional compilation guards below are unchanged.

This record preserves package identity, header-member hashes, and the cited constant expressions as reported by Grok Build. It does not compile those expressions, choose a compiler or architecture profile, measure a host, ratify an SDK, change a PIN, or bind execution. It does not edit any frozen document. Grok Build is the source of the prior SDK package measurement, the four header-member hashes, the dependency-header findings, and the derived constants. Cursor did not recover, read, or independently remeasure the original nupkg or its headers.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: debd68e5508f862108886469fdc64363681f2b9f
Cursor-verified Git HEAD at this provenance repair: debd68e5508f862108886469fdc64363681f2b9f
HEAD comparison: MATCH.

Cursor-verified tracked status at this provenance repair: this evidence document is untracked. No tracked path is modified. Untracked paths other than this evidence document are under the pre-existing .wacp/ tree. This provenance repair does not stage, commit, push, or merge.

Cursor-verified frozen-document SHA-256 values at this provenance repair. Each hash below matches the current file bytes and matches the hash already recorded in the F5 contract and the F5 acceptance. Cursor did not edit these documents:

- docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md: 61156b5edb2b36589b45502a3f43a16330816dc65deef05d94728b65d891191b. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md: 5621cd7b1cf86bf4bb2b3c385237d23bb95edc99663ebb573d5a9b043bcec6fe. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294. MATCH.
- docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md: 64f45f7b55af23fe173e8ad22db4e3516e4df91d4133331c4eb9be3dbe01bc56. MATCH.

## 1.1 Provenance separation

### Grok Build reported measurement

Grok Build is the source of the prior SDK package measurement, the four header-member hashes, the dependency-header findings, and the derived constants recorded in sections 2 and 3. Those values are preserved as reported.

### Cursor local document verification

Cursor verified this evidence document's bytes and SHA-256 before this repair: 0b476019c15653c5285941573c201a887017f2311272e0d0c296e6ee6653d934. Cursor verified Git HEAD debd68e5508f862108886469fdc64363681f2b9f, the tracked status in section 1, and the frozen-document hashes in section 1. Cursor did not recover, read, or independently remeasure the original nupkg or its headers.

### SDK static evidence recorded

Sections 2 and 3 record the Grok Build reported package identity, header-member hashes, dependency-header findings, and derived constants. That record is not an independent Cursor measurement of the package or headers.

### Operationally ratified SDK pin

NOT granted. No operational SDK pin is granted. `OPERATIONAL_MINGIT_PIN` remains `UNRATIFIED`.

### Windows host or execution proof

NOT established. This document does not establish Windows host qualification or execution proof. `EXECUTION_BINDING_REAL` remains `UNEXECUTED`.

## 2. Package identity

Package id: Microsoft.Windows.SDK.CPP
Package version: 10.0.28000.2705
Nupkg filename: Microsoft.Windows.SDK.CPP.10.0.28000.2705.nupkg
Nupkg size in bytes: 160512379
Expected SHA-256: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807
Grok Build reported SHA-256: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807
Exact comparison reported by Grok Build: MATCH.
Cursor independent package verification: NO.

Grok Build reported the measured file as the existing local nupkg at C:/Users/mine0/AppData/Local/Temp/weaver-forge-sdk-evidence/Microsoft.Windows.SDK.CPP.10.0.28000.2705.nupkg. Grok Build reported that path as the measurement location. It is not an installation, not an operational SDK pin, and not a host qualification. Cursor did not open that path and did not remeasure that file.

Grok Build reported the header member hashes below as SHA-256 of the uncompressed nupkg member bytes. Grok Build reported line numbers as 1-based lines of those member bytes. Cursor did not recompute these hashes.

| Nupkg member | Uncompressed size | SHA-256 |
| --- | ---: | --- |
| c/Include/10.0.28000.0/shared/minwindef.h | 6876 | a9cf08be8407a196104124d5ade2308e204e47d3252bcd2ad20d0f2137843d62 |
| c/Include/10.0.28000.0/shared/sdkddkver.h | 11677 | a80967a364c6c6974c4c80a7052aaa135cd3d236bf470ad038de2aaccb373cc0 |
| c/Include/10.0.28000.0/um/WinBase.h | 272941 | a7068b15a262cc2d4f0e51a1ca2f1514566d6f331562c6775235d560b3404d06 |
| c/Include/10.0.28000.0/um/winnt.h | 903556 | fb3d10c0dcc86c737c91652182b81f6bff33a189803570b8dcaa818c96c5b99a |

## 3. Header expressions reported by Grok Build

Grok Build reported these dependency-header findings as readings of the header text. They are not compiler output. Cursor did not read these headers.

### 3.1 FALSE and TRUE

Member: c/Include/10.0.28000.0/shared/minwindef.h

Open guards at the definitions:

- line 10: `#ifndef _MINWINDEF_`
- line 19: `#if WINAPI_FAMILY_PARTITION(WINAPI_PARTITION_APP | WINAPI_PARTITION_SYSTEM | WINAPI_PARTITION_GAMES)`
- line 70: `#ifndef FALSE` for the FALSE definition
- line 74: `#ifndef TRUE` for the TRUE definition

Expressions:

- line 71: `#define FALSE               0`
- line 75: `#define TRUE                1`

The family partition that contains these definitions ends at line 281. The include guard ends at line 284.

### 3.2 Version constants

Member: c/Include/10.0.28000.0/shared/sdkddkver.h

Open guard at the threshold constant:

- line 15: `#ifndef _INC_SDKDDKVER`

Expression:

- line 42: `#define _WIN32_WINNT_WINTHRESHOLD           0x0A00`

Conditional default, open guards:

- line 15: `#ifndef _INC_SDKDDKVER`
- line 229: `#if !defined(_WIN32_WINNT) && !defined(_CHICAGO_)`

Expression:

- line 230: `#define  _WIN32_WINNT   0x0A00`
- line 231: `#endif`

The include guard ends at line 321. The default is the header expression used only when `_WIN32_WINNT` and `_CHICAGO_` are both undefined at line 229. A translation unit that defines either name before this test does not receive this default from these lines.

### 3.3 Creation flags named by the accepted F5 contract

Member: c/Include/10.0.28000.0/um/WinBase.h

Open guards at each definition:

- line 12: `#ifndef _WINBASE_`
- line 669: `#if WINAPI_FAMILY_PARTITION(WINAPI_PARTITION_APP | WINAPI_PARTITION_SYSTEM | WINAPI_PARTITION_GAMES)`

Expressions:

- line 677: `#define CREATE_SUSPENDED                  0x00000004`
- line 687: `#define CREATE_UNICODE_ENVIRONMENT        0x00000400`
- line 698: `#define EXTENDED_STARTUPINFO_PRESENT      0x00080000`
- line 704: `#define CREATE_BREAKAWAY_FROM_JOB         0x01000000`

The family partition ends at line 751. Line 718 is a comment, `//#define CREATE_SUSPENDED`, and is not a second definition. These four macros have no `_WIN32_WINNT` test inside this partition. The same partition defines other `dwCreationFlag` macros. This record preserves the four flags already named by the accepted F5 contract.

### 3.4 Attribute component macros and enumerator anchors

Member: c/Include/10.0.28000.0/um/WinBase.h

Open guards at the component macros, lines 3507-3510:

- line 12: `#ifndef _WINBASE_`
- line 3499: `#if WINAPI_FAMILY_PARTITION(WINAPI_PARTITION_DESKTOP | WINAPI_PARTITION_SYSTEM | WINAPI_PARTITION_GAMES)`
- line 3501: `#if (_WIN32_WINNT >= 0x0600)`

Expressions:

- line 3507: `#define PROC_THREAD_ATTRIBUTE_NUMBER    0x0000FFFF`
- line 3508: `#define PROC_THREAD_ATTRIBUTE_THREAD    0x00010000`
- line 3509: `#define PROC_THREAD_ATTRIBUTE_INPUT     0x00020000`
- line 3510: `#define PROC_THREAD_ATTRIBUTE_ADDITIVE  0x00040000`

Enumerator anchors inside the additional guard at line 3513, `#ifndef _USE_FULL_PROC_THREAD_ATTRIBUTE`:

- line 3516: `ProcThreadAttributeHandleList                   = 2`
- line 3530 opens `#if (_WIN32_WINNT >= _WIN32_WINNT_WINTHRESHOLD)`
- line 3531: `ProcThreadAttributeJobList                      = 13`

The enum closes at line 3567. The `#endif` for `_USE_FULL_PROC_THREAD_ATTRIBUTE` is line 3568. The `#endif` for `(_WIN32_WINNT >= 0x0600)` that covers `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` is line 3581.

Substitution macro, under the same family partition and `(_WIN32_WINNT >= 0x0600)` guards:

- lines 3570-3574: `ProcThreadAttributeValue(Number, Thread, Input, Additive)` is `(((Number) & PROC_THREAD_ATTRIBUTE_NUMBER) | ((Thread != FALSE) ? PROC_THREAD_ATTRIBUTE_THREAD : 0) | ((Input != FALSE) ? PROC_THREAD_ATTRIBUTE_INPUT : 0) | ((Additive != FALSE) ? PROC_THREAD_ATTRIBUTE_ADDITIVE : 0))`
- lines 3578-3579: `#define PROC_THREAD_ATTRIBUTE_HANDLE_LIST ProcThreadAttributeValue (ProcThreadAttributeHandleList, FALSE, TRUE, FALSE)`

`PROC_THREAD_ATTRIBUTE_JOB_LIST` is under a later guard in the same family partition:

- line 3990: `#if (_WIN32_WINNT >= _WIN32_WINNT_WINTHRESHOLD)`
- lines 3992-3993: `#define PROC_THREAD_ATTRIBUTE_JOB_LIST ProcThreadAttributeValue (ProcThreadAttributeJobList, FALSE, TRUE, FALSE)`
- line 4018: `#endif // _WIN32_WINNT_WINTHRESHOLD`

### 3.5 Header-expression substitution for the two attribute integers

Grok Build reported the following derived constants by substituting the expressions in section 3.4, using FALSE as 0 and TRUE as 1 from section 3.1:

- `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` = `((2) & 0x0000FFFF) | 0 | 0x00020000 | 0` = `0x00020002`
- `PROC_THREAD_ATTRIBUTE_JOB_LIST` = `((13) & 0x0000FFFF) | 0 | 0x00020000 | 0` = `0x0002000D`

Grok Build reported this substitution as an arithmetic reading of those header expressions. It is reached only when all of the following hold: the cited family partition is active; `_WIN32_WINNT >= 0x0600` for `HANDLE_LIST`; `_WIN32_WINNT >= _WIN32_WINNT_WINTHRESHOLD` for `JOB_LIST` and for enumerator 13; `_USE_FULL_PROC_THREAD_ATTRIBUTE` is undefined so enumerators 2 and 13 are the ones in this enum; and FALSE and TRUE still expand to 0 and 1. These integers are not an SDK pin.

### 3.6 Job limit flags named by the accepted F5 contract

Member: c/Include/10.0.28000.0/um/winnt.h

Open guard at each definition:

- line 18: `#ifndef _WINNT_`

No `_WIN32_WINNT` test and no `WINAPI_FAMILY_PARTITION` test are open at these lines.

Expressions:

- line 14093: `#define JOB_OBJECT_LIMIT_BREAKAWAY_OK               0x00000800`
- line 14094: `#define JOB_OBJECT_LIMIT_SILENT_BREAKAWAY_OK        0x00001000`
- line 14095: `#define JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE          0x00002000`

The same include guard contains other `JOB_OBJECT_LIMIT_*` macros. This record preserves the three flags already named by the accepted F5 contract.

### 3.7 Job information class enumerator sequence

Member: c/Include/10.0.28000.0/um/winnt.h

Open guard:

- line 18: `#ifndef _WINNT_`

The typedef enum `_JOBOBJECTINFOCLASS` occupies lines 14180-14238. Explicit anchors in that text are `JobObjectBasicAccountingInformation = 1`, `JobObjectReserved1Information = 18`, `JobObjectReserved14Information = 31`, `JobObjectReserved15Information = 37`, `JobObjectReserved16Information = 38`, `JobObjectReserved17Information = 39`, `JobObjectReserved18Information = 40`, `JobObjectReserved19Information = 41`, `JobObjectReserved20Information = 42`, `JobObjectReserved21Information = 43`, `JobObjectReserved22Information = 44`, `JobObjectReserved23Information = 45`, `JobObjectReserved24Information = 46`, `JobObjectReserved25Information = 47`, `JobObjectReserved26Information = 48`, `JobObjectReserved27Information = 49`, and `JobObjectReserved28Information = 50`.

Grok Build reported C and C++ enumerator succession from those anchors, which is a language-rule reading of the header text and not a compiled object, as this derived sequence:

| Value | Enumerator | Source line |
| ---: | --- | ---: |
| 1 | JobObjectBasicAccountingInformation | 14181 |
| 2 | JobObjectBasicLimitInformation | 14182 |
| 3 | JobObjectBasicProcessIdList | 14183 |
| 4 | JobObjectBasicUIRestrictions | 14184 |
| 5 | JobObjectSecurityLimitInformation | 14185 |
| 6 | JobObjectEndOfJobTimeInformation | 14186 |
| 7 | JobObjectAssociateCompletionPortInformation | 14187 |
| 8 | JobObjectBasicAndIoAccountingInformation | 14188 |
| 9 | JobObjectExtendedLimitInformation | 14189 |
| 10 | JobObjectJobSetInformation | 14190 |
| 11 | JobObjectGroupInformation | 14191 |
| 12 | JobObjectNotificationLimitInformation | 14192 |
| 13 | JobObjectLimitViolationInformation | 14193 |
| 14 | JobObjectGroupInformationEx | 14194 |
| 15 | JobObjectCpuRateControlInformation | 14195 |
| 16 | JobObjectCompletionFilter | 14196 |
| 17 | JobObjectCompletionCounter | 14197 |
| 18 | JobObjectReserved1Information | 14202 |
| 19 | JobObjectReserved2Information | 14203 |
| 20 | JobObjectReserved3Information | 14204 |
| 21 | JobObjectReserved4Information | 14205 |
| 22 | JobObjectReserved5Information | 14206 |
| 23 | JobObjectReserved6Information | 14207 |
| 24 | JobObjectReserved7Information | 14208 |
| 25 | JobObjectReserved8Information | 14209 |
| 26 | JobObjectReserved9Information | 14210 |
| 27 | JobObjectReserved10Information | 14211 |
| 28 | JobObjectReserved11Information | 14212 |
| 29 | JobObjectReserved12Information | 14213 |
| 30 | JobObjectReserved13Information | 14214 |
| 31 | JobObjectReserved14Information | 14215 |
| 32 | JobObjectNetRateControlInformation | 14216 |
| 33 | JobObjectNotificationLimitInformation2 | 14217 |
| 34 | JobObjectLimitViolationInformation2 | 14218 |
| 35 | JobObjectCreateSilo | 14219 |
| 36 | JobObjectSiloBasicInformation | 14220 |
| 37 | JobObjectReserved15Information | 14221 |
| 38 | JobObjectReserved16Information | 14222 |
| 39 | JobObjectReserved17Information | 14223 |
| 40 | JobObjectReserved18Information | 14224 |
| 41 | JobObjectReserved19Information | 14225 |
| 42 | JobObjectReserved20Information | 14226 |
| 43 | JobObjectReserved21Information | 14227 |
| 44 | JobObjectReserved22Information | 14228 |
| 45 | JobObjectReserved23Information | 14229 |
| 46 | JobObjectReserved24Information | 14230 |
| 47 | JobObjectReserved25Information | 14231 |
| 48 | JobObjectReserved26Information | 14232 |
| 49 | JobObjectReserved27Information | 14233 |
| 50 | JobObjectReserved28Information | 14234 |
| 51 | JobObjectNetworkAccountingInformation | 14235 |
| 52 | JobObjectCpuPartition | 14236 |
| 53 | MaxJobObjectInfoClass | 14237 |

## 4. Compile-profile-dependent conclusions left open

The header text does not select a compiler, an architecture, a pointer width, or a calling convention. Whether a later translation unit actually sees each guarded expression depends on names defined before the header and on the active family partition. This record does not choose those names.

Left as compile-profile-dependent, and not concluded here:

- A pre-existing definition of `FALSE` or `TRUE` before minwindef.h.
- A pre-existing definition of `_WIN32_WINNT` or `_CHICAGO_` before the default at sdkddkver.h:229.
- Whether `WINAPI_FAMILY_PARTITION` includes `WINAPI_PARTITION_APP`, `WINAPI_PARTITION_SYSTEM`, or `WINAPI_PARTITION_GAMES` for FALSE, TRUE, and the creation flags.
- Whether `WINAPI_FAMILY_PARTITION` includes `WINAPI_PARTITION_DESKTOP`, `WINAPI_PARTITION_SYSTEM`, or `WINAPI_PARTITION_GAMES` for the attribute macros.
- Whether `_WIN32_WINNT` satisfies `>= 0x0600` and `>= _WIN32_WINNT_WINTHRESHOLD`.
- Whether `_USE_FULL_PROC_THREAD_ATTRIBUTE` is defined. When it is defined, the enum that states enumerators 2 and 13 is skipped by line 3513.
- The value of `NTDDI_VERSION` after sdkddkver.h:233. When `_WIN32_WINNT >= _WIN32_WINNT_WIN10`, line 240 sets `NTDDI_VERSION` from `WDK_NTDDI_VERSION`. That value is not recorded here.
- Calling convention, architecture, pointer width, and struct layout.
- Host behavior, including Job nesting and death-during-create behavior.
- SDK ratification and any operational SDK pin.
- The operational MinGit PIN. `OPERATIONAL_MINGIT_PIN` remains `UNRATIFIED`.

## 5. What this record does not close

This record does not implement, compile, execute, download, install, or change a PIN. It does not authorize CreateProcessW, assign a process to a Job, or treat the recorded integers as permission to launch. It does not amend the F5 contract. Numeric ABI types, struct sizes, calling convention, and error mapping remain non-closed there.

Remaining open:

- Calling convention.
- Architecture and pointer width.
- Struct layout.
- Host behavior.
- SDK ratification.
- Operational MinGit PIN and operational SDK pin.
- Real execution binding. `EXECUTION_BINDING_REAL` remains `UNEXECUTED`.

FULL_INR_READY: NO
