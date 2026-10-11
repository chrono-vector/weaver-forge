# INR-HER MinGit SDK Static Constant Evidence Limited Human Acceptance

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_LIMITED_ACCEPTANCE_APPROVED
Scope: the provenance-labeled SDK static evidence document only
Decision source: the Human explicit approval to record this limited acceptance and to preserve it with one documentation-only commit and a normal push of her/inr-her-mingit-eb0.

This acceptance applies only to docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md. It accepts the recorded static definitions and conditional guards in that document. It does not compile those expressions, install or launch an SDK, ratify a package, grant an operational SDK pin, claim SDK-version equivalence, prove a Windows host, prove runtime isolation, bind execution, or declare FULL INR readiness.

## 1. Prerequisite verification

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: debd68e5508f862108886469fdc64363681f2b9f
Locally verified HEAD before this record: debd68e5508f862108886469fdc64363681f2b9f
HEAD comparison: MATCH.

Accepted SDK static evidence document, not edited by this record:
docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md
Expected SHA-256: b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175
Locally measured SHA-256 before recording: b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175
Exact comparison: MATCH.
Tracked status before this record: the evidence document is untracked. No tracked path differed from HEAD. Untracked paths other than that evidence document were under the pre-existing .wacp/ tree.

Frozen documents, measured before this record and matching the hashes recorded inside the SDK evidence document and the F5 contract:

- docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3. MATCH. Working-tree blob equals HEAD blob 65b39aaf4bf4348ab0c55bc108d80132d89a59b7.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543. MATCH. Working-tree blob equals HEAD blob 7b47048534476cadf9064b39d4001b7e4aae6422.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md: 61156b5edb2b36589b45502a3f43a16330816dc65deef05d94728b65d891191b. MATCH. Working-tree blob equals HEAD blob 40e44e61c40ad55b7510a962516f5ed36a6dd285.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786. MATCH. Working-tree blob equals HEAD blob 5e6cd8fba922b58bf3cfc311debbe8253acfb8a6.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b. MATCH. Working-tree blob equals HEAD blob 8f0be60ecfd55aa14074a0700a6553c517ea5f55.
- docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md: 5621cd7b1cf86bf4bb2b3c385237d23bb95edc99663ebb573d5a9b043bcec6fe. MATCH. Working-tree blob equals HEAD blob efa733c65c10abcae2138c6d1f16bfad0c91dbf3.
- docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294. MATCH. Working-tree blob equals HEAD blob 47d4ece6622c8968939afeda3ed091910b883446.
- docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md: 64f45f7b55af23fe173e8ad22db4e3516e4df91d4133331c4eb9be3dbe01bc56. MATCH. Working-tree blob equals HEAD blob 2f084c87686216f3c325423c5e80d41a50fafdf8.

.wacp/ remained pre-existing untracked content. Before this record it contained 179 files. This record does not add, edit, stage, or delete any .wacp/ path.

## 2. Limited acceptance

HUMAN_LIMITED_ACCEPTANCE_APPROVED applies only to the provenance-labeled SDK static evidence document whose SHA-256 is recorded in section 1.

Accepted package identity, as reported by Grok Build and preserved in that document:

- SDK package: Microsoft.Windows.SDK.CPP
- Package version: 10.0.28000.2705
- Package SHA-256 reported by Grok Build: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807

Grok Build is the source of the package measurement, the header-member measurements, and the derived constants in the accepted evidence document. Cursor independent nupkg/header verification: NO. Cursor did not recover, read, or independently remeasure the original nupkg or its headers.

Accepted evidence-document SHA-256: b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175.

The accepted content is static definitions and conditional guards only. The recorded integers are readings of those header expressions under the guards written in the evidence document. This acceptance does not select a compiler, architecture, pointer width, calling convention, or family partition.

Same-provider independence limitation: the package, header, and derived-constant evidence comes from Grok Build. No second provider remeasured the nupkg or headers. Cursor document-byte verification is not package verification and is not independent provider verification. Agreement with the reported measurements is not evidence of header bytes, SDK identity, OS behavior, host state, or runtime isolation.

This acceptance grants no operational SDK pin. It makes no SDK-version equivalence claim. Package version text and header path text in the evidence document are recorded labels, not a proof that another SDK build, host installation, or compiler include set is the same bytes.

This acceptance establishes no Windows host qualification, no runtime isolation, and no FULL INR readiness. EXECUTION_BINDING_REAL remains UNEXECUTED. OPERATIONAL_MINGIT_PIN remains UNRATIFIED. FULL_INR_READY=NO.

## 3. What remains open

The non-closed items already named by the accepted evidence document stay open. In particular:

- Calling convention, architecture, pointer width, and struct layout.
- Which names are defined before the cited headers, and which family partition is active.
- Host behavior, including Job nesting.
- SDK ratification and any operational SDK pin.
- The operational MinGit PIN.
- Real execution binding.

## 4. Batch boundary

The documentation commit authorized with this record stages only these two paths:

1. docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md
2. docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE_LIMITED_HUMAN_ACCEPTANCE.md

No other path is staged. .wacp/ remains untracked and excluded. No frozen document, code, PIN, SDK file, package, or .wacp/ bytes are changed. No executable target is compiled, installed, or launched. No merge, pull request, or WACP generation is performed. No force push is used.

MERGED: NO
FULL_INR_READY: NO
