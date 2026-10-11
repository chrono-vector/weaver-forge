# INR-HER MinGit Windows x64 MSVC-Compatible ABI Measurement Profile Limited Human Acceptance

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_LIMITED_ACCEPTANCE_APPROVED
Scope: the Windows x64 / MSVC-compatible static ABI measurement profile document only
Decision source: the Human explicit approval to record this limited acceptance and to preserve it with one documentation-only commit and a normal push of her/inr-her-mingit-eb0.

This acceptance applies only to docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE.md. It accepts that document as a limited measurement profile whose Human-approved choices are Windows x64, the MSVC-compatible compiler family, and static ABI verification only, with production authority NO and runtime authority NO. It does not compile, run, download, extract, install, or launch an SDK or a compiler. It does not select an exact compiler or version, an active WINAPI branch, a pointer size, or a packing value. It does not ratify a package, grant an operational SDK pin, grant production authority, grant execution authority, prove a Windows host, prove Job behavior, prove execution isolation, bind execution, or declare FULL INR readiness.

## 1. Prerequisite verification

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: dbd6ade5556f4ccd28c3b20fb04f6dc2e601fee0
Locally verified HEAD before this record: dbd6ade5556f4ccd28c3b20fb04f6dc2e601fee0
HEAD comparison: MATCH.
HEAD subject: docs: record limited human acceptance of the provenance-labeled SDK ABI prior evidence
Remote tracking branch origin/her/inr-her-mingit-eb0 before this record: dbd6ade5556f4ccd28c3b20fb04f6dc2e601fee0.

Accepted profile document, not edited by this record:
docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE.md
Expected SHA-256: 5b4537bbcb416c2d23ef0a2e232ed39346ba32b18f0e05e466722248af61f12a
Locally measured SHA-256 before recording: 5b4537bbcb416c2d23ef0a2e232ed39346ba32b18f0e05e466722248af61f12a
Exact comparison: MATCH.
Tracked status before this record: the profile document is untracked. No tracked path differed from HEAD. Untracked paths other than that profile document were under the pre-existing .wacp/ tree.

Frozen documents and the prior ABI acceptance, measured before this record and matching the hashes recorded inside the profile. Working-tree blobs equal the HEAD blobs. These are documentation-file hashes. They are not nupkg or header hashes. This record does not edit these documents:

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
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md: a782d866319a7870e955f88e236dfd5853126811055eefc00590cee023c6be11. MATCH to current bytes. Working-tree blob equals HEAD blob 861afbc33f36e7ae5caa414f15f9deb15277d860. This hash is the current-byte measurement already recorded in the accepted profile. It is not a self-digest published by that earlier acceptance.

.wacp/ remained pre-existing untracked content. This record does not add, edit, stage, or delete any .wacp/ path.

## 2. Limited acceptance

HUMAN_LIMITED_ACCEPTANCE_APPROVED applies only to the measurement profile whose SHA-256 is recorded in section 1, and only to the four Human-approved choices named in that profile's section 2.

Accepted profile path: docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE.md
Accepted profile SHA-256: 5b4537bbcb416c2d23ef0a2e232ed39346ba32b18f0e05e466722248af61f12a

Accepted choices, and only these choices:

- ABI measurement target: Windows x64.
- Compiler family: MSVC-compatible.
- Purpose: static ABI verification only.
- Production authority: NO. Runtime authority: NO.

Windows x64 names the measurement target for a future static ABI verification batch. MSVC-compatible names the compiler family for that same batch. Neither label selects a compiler product, a version, a toolset, a predefined-macro set, or a target configuration. Static ABI verification is the only purpose this acceptance authorizes a future batch to pursue under this profile.

This acceptance does not ratify any of the following:

- Exact compiler or version. No product name, version string, toolset, or predefined-macro set is selected.
- Active WINAPI branch. The three mutually exclusive branches preserved from the prior report remain unselected. The machine meaning of __stdcall, _cdecl, and an empty WINAPI stays UNVERIFIED.
- Pointer size. The Windows x64 label is not a measured width and is not a pointer-size ratification.
- Packing. Incoming pack state and resulting struct sizes and alignment stay UNVERIFIED. No packing value is ratified.

This acceptance grants no SDK operational PIN, no production authority, and no execution authority. Package version text remains a recorded label. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. EXECUTION_BINDING_REAL remains UNEXECUTED.

Grok Build is the original source of the SDK package measurements, the header-member measurements, and the ABI findings cited by the accepted profile. Cursor independent package remeasurement: NO. Cursor did not recover, open, extract, download, install, or independently remeasure the original nupkg or its headers. Cursor document-byte verification is not package verification and is not independent provider verification.

Same-provider independence limitation: the package, header, and ABI evidence comes from Grok Build. No second provider remeasured the nupkg or headers. Agreement with the reported measurements is not evidence of header bytes, SDK identity, OS behavior, host state, or runtime isolation.

Referenced prior evidence, unchanged by this acceptance:

- docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md SHA-256 b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE_LIMITED_HUMAN_ACCEPTANCE.md SHA-256 097a5928f0e775d4d3343b516c7e2a1fd8fd98716972e74480dbd752f414e072
- Package reported by Grok Build and preserved there: Microsoft.Windows.SDK.CPP 10.0.28000.2705
- Package SHA-256 reported by Grok Build: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md SHA-256 b99bf685afcae6db1e17c3a3421bb4056e2b77860048ad08a955c6d0f15cf446
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md SHA-256 a782d866319a7870e955f88e236dfd5853126811055eefc00590cee023c6be11
- Handover TXT named by that acceptance: WEAVER_FORGE_SDK_ABI_PRIOR_GROK_REPORTS_20261011.txt
- Handover TXT SHA-256 recorded by that acceptance: 5074d85b9b45cb3d7157f745a5818289858453ad660a33a7e5e2dadcaa9756f2

This acceptance establishes no Windows host qualification, no Job behavior, no execution isolation, and no FULL INR readiness. FULL_INR_READY=NO.

## 3. What remains open

The non-closed items already named by the accepted profile stay open. This acceptance does not close any of them and does not perform the static checks listed in the profile's section 5.

OPEN technical conditions named by the accepted profile:

- Exact compiler, version, and target configuration. OPEN. No product name, version string, toolset, or predefined-macro set is selected.
- WINAPI calling-convention mapping. OPEN. The three mutually exclusive branches preserved from the prior report remain unselected. The machine meaning of __stdcall, _cdecl, and an empty WINAPI stays UNVERIFIED.
- Pointer widths and concrete type layout. OPEN until verified under the still-unselected exact configuration. The Windows x64 label is not a measured width.
- Struct sizeof, alignment, and packing. OPEN. Incoming pack state and resulting struct sizes and alignment stay UNVERIFIED.
- WINAPI_FAMILY and the active partition. OPEN. No family value and no partition-macro override is selected.
- _WIN32_WINNT and NTDDI_VERSION configuration. OPEN. No value is selected for either macro. The header default expressions preserved in the accepted static evidence are not adopted as this profile's configuration.
- SDK operational PIN and compiler/header identity binding. OPEN. No operational SDK pin is granted. The exact compiler is not bound to a header-member hash set.
- Windows host qualification, Job behavior, and execution isolation. OPEN. None is established.
- Operational MinGit PIN and real execution binding. OPEN. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. EXECUTION_BINDING_REAL remains UNEXECUTED.

UNVERIFIED source-text items already named in docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md section 5 and section 6, and in docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION_LIMITED_HUMAN_ACCEPTANCE.md section 3, stay open. This acceptance does not close them:

- Archive paths and SHA-256 values of pshpack1.h, pshpack2.h, and pshpack8.h.
- Sizes and SHA-256 values of the scanned members apiset.h, specstrings.h, kernelspecs.h, sal.h, driverspecs.h, guiddef.h, minwinbase.h, ctype.h, corecrt.h, and string.h.
- Size and SHA-256 of windef.h.
- Sought archive paths for excpt.h and intrin.h.
- Which WINAPI branch is active, and the machine meaning of __stdcall, _cdecl, and an empty WINAPI.
- The NTAPI replacement text.
- The partition-macro definition text at winapifamily.h lines 149–185.
- Which HANDLE branch is active.
- Which pointer-width branch is active.
- The line-quoted INT_PTR, LONG_PTR, UINT_PTR, and _W64 spellings.
- Numeric widths of unsigned long, long, int, and unsigned short.
- The incoming pack state and the resulting struct sizes and alignment.
- The helper text inside pshpack4.h and poppack.h.
- The remaining CreateProcessW parameter names, order, and annotations.
- The CreateProcess #else mapping text.
- The full parameter lists of InitializeProcThreadAttributeList and DeleteProcThreadAttributeList, and the remaining UpdateProcThreadAttribute parameters.
- The CreateJobObjectW parameter names.
- The AssignProcessToJobObject argument text.
- The unquoted arguments of SetInformationJobObject and QueryInformationJobObject.
- The CreateJobObjectA parameter text.
- The per-field types of STARTUPINFOW.
- The other field names in JOBOBJECT_BASIC_ACCOUNTING_INFORMATION.
- Which LARGE_INTEGER and LONGLONG branch is active.
- Which names are defined before the cited headers, and which family partition is active.
- Host behavior, including Job nesting.
- SDK ratification and any operational SDK pin.
- SDK-version equivalence, including any comparison with another build such as 10.0.28000.2957.
- Same-provider verification. No second provider remeasured the nupkg or headers.
- FULL INR readiness.

## 4. Batch boundary

The documentation commit authorized with this record stages only these two paths:

1. docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE.md
2. docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_COMPATIBLE_ABI_MEASUREMENT_PROFILE_LIMITED_HUMAN_ACCEPTANCE.md

No other path is staged. .wacp/ remains untracked and excluded. No frozen document, prior SDK acceptance, F5 record, EB-14 record, code, PIN, SDK file, package, or .wacp/ bytes are changed. No executable target is compiled, installed, downloaded, or launched. No merge, pull request, or WACP generation is performed. No force push is used.

MERGED: NO
FULL_INR_READY: NO
