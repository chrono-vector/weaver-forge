# INR-HER MinGit Windows x64 MSVC-Compatible ABI Measurement Profile

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_LIMITED_STATIC_ABI_MEASUREMENT_PROFILE_RECORDED
Scope: one Human-approved limited verification profile for a future static ABI verification batch
Decision source: the Human explicit approval to record this limited verification profile in one documentation-only document.

This document records a measurement profile. It does not compile, run, download, extract, install, or launch an SDK or a compiler. It does not select an exact compiler, version, target configuration, calling-convention mapping, pointer width, type layout, packing value, WINAPI_FAMILY, partition, _WIN32_WINNT, or NTDDI_VERSION. It does not ratify a package, grant an operational SDK pin, grant production authority, grant runtime authority, prove a Windows host, prove Job behavior, prove execution isolation, bind execution, or declare FULL INR readiness.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: dbd6ade5556f4ccd28c3b20fb04f6dc2e601fee0
Cursor-verified Git HEAD before this record: dbd6ade5556f4ccd28c3b20fb04f6dc2e601fee0
HEAD comparison: MATCH.
HEAD subject: docs: record limited human acceptance of the provenance-labeled SDK ABI prior evidence
Remote tracking branch origin/her/inr-her-mingit-eb0 before this record: dbd6ade5556f4ccd28c3b20fb04f6dc2e601fee0.

Cursor-verified tracked status before this record: no tracked path differed from HEAD. git status --porcelain=v1 reported only the pre-existing untracked .wacp/ tree. This record does not read, stage, edit, or delete any .wacp/ path.

Cursor-verified SHA-256 values of the accepted evidence documents and the frozen documents, measured from current file bytes before this record. Each value matches the hash already recorded in docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md. These are documentation-file hashes. They are not nupkg or header hashes. Cursor did not edit these documents. Working-tree blobs equal the HEAD blobs:

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

The ABI prior-evidence acceptance document does not record its own file hash. Cursor measured its current bytes before this record and did not edit it:

- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md: a782d866319a7870e955f88e236dfd5853126811055eefc00590cee023c6be11. MATCH to current bytes. Working-tree blob equals HEAD blob 861afbc33f36e7ae5caa414f15f9deb15277d860. This batch does not treat that hash as a previously published self-digest.

## 2. Human-approved limited profile

HUMAN_APPROVED_PROFILE_RECORDED applies only to the four choices in this section.

- ABI measurement target: Windows x64.
- Compiler family: MSVC-compatible.
- Purpose: static ABI verification only.
- Production authority: NO. Runtime authority: NO.

Windows x64 names the measurement target for a future static ABI verification batch. MSVC-compatible names the compiler family for that same batch. Neither label selects a compiler product, a version, a toolset, a predefined-macro set, or a target configuration. Static ABI verification is the only purpose this profile authorizes a future batch to pursue. This profile grants no production authority and no runtime authority.

## 3. Accepted evidence referenced

The package identity below is the identity already accepted as a prior Grok Build report. Cursor did not independently remeasure the SDK package or its headers for this profile. Cursor independent nupkg or header verification: NO.

Accepted SDK static evidence:

- Document: docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md
- Document SHA-256: b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175
- Limited Human acceptance: docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE_LIMITED_HUMAN_ACCEPTANCE.md
- Acceptance document SHA-256: 097a5928f0e775d4d3343b516c7e2a1fd8fd98716972e74480dbd752f414e072
- Package reported by Grok Build and preserved there: Microsoft.Windows.SDK.CPP 10.0.28000.2705
- Package SHA-256 reported by Grok Build: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807

Accepted ABI prior evidence:

- Document: docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md
- Document SHA-256: b99bf685afcae6db1e17c3a3421bb4056e2b77860048ad08a955c6d0f15cf446
- Limited Human acceptance: docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md
- Acceptance document SHA-256 measured in section 1: a782d866319a7870e955f88e236dfd5853126811055eefc00590cee023c6be11
- Handover TXT named by that acceptance: WEAVER_FORGE_SDK_ABI_PRIOR_GROK_REPORTS_20261011.txt
- Handover TXT SHA-256 recorded by that acceptance: 5074d85b9b45cb3d7157f745a5818289858453ad660a33a7e5e2dadcaa9756f2

Grok Build is the original source of the package measurements, the header-member measurements, and the ABI findings in those accepted documents. Same-provider independence limitation: no second provider remeasured the nupkg or headers. Cursor document-byte verification is not package verification and is not independent provider verification. Agreement with the reported measurements is not evidence of header bytes, SDK identity, OS behavior, host state, or runtime isolation.

This reference grants no operational SDK pin. Package version text remains a recorded label. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. EXECUTION_BINDING_REAL remains UNEXECUTED. FULL_INR_READY=NO.

## 4. Remaining open

Selecting Windows x64 and the MSVC-compatible family does not close the items in this section. Each item stays OPEN.

- Exact compiler, version, and target configuration. OPEN. No product name, version string, toolset, or predefined-macro set is selected.
- WINAPI calling-convention mapping. OPEN. The three mutually exclusive branches preserved from the prior report remain unselected. The machine meaning of __stdcall, _cdecl, and an empty WINAPI stays UNVERIFIED.
- Pointer widths and concrete type layout. OPEN until verified under the still-unselected exact configuration. The Windows x64 label is not a measured width.
- Struct sizeof, alignment, and packing. OPEN. Incoming pack state and resulting struct sizes and alignment stay UNVERIFIED.
- WINAPI_FAMILY and the active partition. OPEN. No family value and no partition-macro override is selected.
- _WIN32_WINNT and NTDDI_VERSION configuration. OPEN. No value is selected for either macro. The header default expressions preserved in the accepted static evidence are not adopted as this profile's configuration.
- SDK operational PIN and compiler/header identity binding. OPEN. No operational SDK pin is granted. The exact compiler is not bound to a header-member hash set.
- Windows host qualification, Job behavior, and execution isolation. OPEN. None is established.
- Operational MinGit PIN and real execution binding. OPEN. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. EXECUTION_BINDING_REAL remains UNEXECUTED.

The UNVERIFIED source-text items already named in docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md section 5 and section 6, and in its limited Human acceptance section 3, stay open. This profile does not close them.

## 5. Static acceptance criteria for a future batch

These criteria define what a future ABI verification batch must show before this profile treats that batch's static ABI record as acceptable. This document does not perform the checks. It does not compile, run, or select the configuration values the checks require. Meeting every criterion still grants no production authority, no runtime authority, no operational SDK pin, no Windows host qualification, and no FULL INR readiness.

A future batch passes these static acceptance criteria only when every item below is true in that batch's own record:

1. Profile match. The batch states the ABI measurement target as Windows x64 and the compiler family as MSVC-compatible, and it states that its purpose is static ABI verification only.
2. Exact configuration present. The batch records the exact compiler product, version, and target configuration that section 4 leaves open, including the predefined macros that select branches. A record that stops at the family label does not pass.
3. WINAPI mapping recorded. The batch identifies exactly one active branch of the three mutually exclusive WINAPI definitions preserved in the accepted ABI prior-evidence document, quotes the resulting replacement token, and records the calling-convention mapping of that token for the exact compiler and target configuration in item 2. If more than one branch remains possible, the batch does not pass.
4. Pointer widths and concrete type layout recorded. The batch records the active pointer-width branch and the numeric widths of pointer, INT_PTR, LONG_PTR, UINT_PTR, ULONG_PTR, SIZE_T, DWORD_PTR, DWORD, BOOL, WORD, BYTE, and LONG for that same configuration, with the header text that supports each width. A width inferred from the Windows x64 label alone does not pass.
5. Struct sizeof, alignment, and packing recorded. The batch records the incoming pack state, the effect of the preserved pshpack4.h and poppack.h pairs on the job structs, and sizeof and alignment for STARTUPINFOW, STARTUPINFOEXW, JOBOBJECT_BASIC_ACCOUNTING_INFORMATION, JOBOBJECT_BASIC_LIMIT_INFORMATION, and JOBOBJECT_EXTENDED_LIMIT_INFORMATION. Any of those values left UNVERIFIED means the batch does not pass.
6. Family and partition recorded. The batch records the active WINAPI_FAMILY value and the active partition-macro definitions that guard the cited declarations. An unset family left as one of several accepted header values does not pass.
7. Version macros recorded. The batch records the effective _WIN32_WINNT and the effective NTDDI_VERSION, and it records whether each value was supplied before sdkddkver.h or came from a header conditional. An unstated effective value does not pass.
8. Evidence identity kept separate from a new package measurement. The batch cites both accepted documents by the paths and SHA-256 values in section 3. Any statement that header bytes are Microsoft.Windows.SDK.CPP 10.0.28000.2705 is labeled as the prior Grok Build report, including package SHA-256 a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807, or as a measurement by a named measurer other than a claim that Cursor already remeasured that package. A Cursor documentation-file hash is not a package remeasurement. The batch does not grant an operational SDK pin.
9. Compiler and header binding recorded. The batch binds the exact compiler and target configuration in item 2 to the header-member hashes of the members it quotes. A version string without those member hashes does not pass. This profile does not supply that binding.
10. Out-of-scope claims absent. The batch records Windows host qualification, Job behavior, execution isolation, OPERATIONAL_MINGIT_PIN, and EXECUTION_BINDING_REAL as still open. It records production authority NO, runtime authority NO, and FULL_INR_READY=NO. A batch that marks any of those closed because this profile exists does not pass.
11. Frozen baselines unchanged. The batch remeasures the document SHA-256 values in section 1, records MATCH for each, and does not edit those files or any .wacp/ path.

## 6. Batch boundary

This batch creates this one documentation file and edits nothing else. It does not stage, commit, push, merge, or open a pull request. It does not generate WACP. It does not read or modify .wacp/. It does not change a PIN. It does not edit the accepted SDK static evidence document, the accepted ABI prior-evidence document, their Human acceptances, F5, EB-14, EB-5, EB-0, or any other frozen document.

COMMITTED: NO
PUSHED: NO
FULL_INR_READY: NO
