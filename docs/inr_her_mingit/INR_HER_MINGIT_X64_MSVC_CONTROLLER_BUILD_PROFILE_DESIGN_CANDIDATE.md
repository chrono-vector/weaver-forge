# INR-HER MinGit Windows x64 MSVC Controller Build Profile Design Candidate

Record date: 2026-10-13 (Asia/Tokyo)
Status: DESIGN_CANDIDATE_SELECTED
Scope: one documentation-only development-candidate record for a future INR-HER-MINGIT controller build profile
Decision source: the Human authorization to select the existing measured Windows x64 MSVC configuration as that development candidate

This record selects a development candidate. It is not an operational ABI pin and not execution authorization.

BUILD_PROFILE=DESIGN_CANDIDATE_SELECTED
CONTROLLER_ABI_PIN=NOT_RATIFIED
launch_identity=UNBOUND_AT_LAUNCH
REAL_WINDOWS_EXECUTION=NOT_AUTHORIZED
FULL_INR_READY=NO

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: 83bf96f2deecf04af726236ce4525b6985081d65
Cursor-verified Git HEAD before this record: 83bf96f2deecf04af726236ce4525b6985081d65
HEAD comparison: MATCH.
HEAD subject: docs(inr): adopt conditional EB5 F5 design amendment

Tracked worktree before this record: no tracked path differed from HEAD. `git status --porcelain=v1` reported only the pre-existing untracked `.wacp/` tree. This record does not read, stage, edit, or delete any `.wacp/` path.

Conditional Human adoption present at that HEAD, and not edited by this record:

- docs/inr_her_mingit/INR_HER_MINGIT_EB5_F5_CONDITIONAL_HUMAN_DESIGN_ADOPTION.md
- Introducing commit: 83bf96f2deecf04af726236ce4525b6985081d65

This batch does not repeat SDK measurement, ZIP rehash, compilation, or preprocessing.

## 2. Measured evidence reused

These values are copied from existing accepted records. This batch did not remeasure them.

Off-host layout and width record, docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFHOST_MEASUREMENT_EVIDENCE.md, commit 852975a:

- Target label in that record: Windows x64, as the user-run host statement Windows 11 x64.
- Toolchain family: MSVC. Toolset directory token: 14.50.35717. Hostx64/x64 cl.exe remains the user-run invocation statement. The transferred logs do not contain that invocation text.
- Printed `_MSC_VER`: 1950. Printed `_MSC_FULL_VER`: 195035739.
- Printed `WINAPI_FAMILY`: 100. Printed `_WIN32_WINNT`: 0x0A00. Printed `NTDDI_VERSION`: 0x0A000012.
- Compile-time assertions recorded there: `sizeof(void*) == 8` and `sizeof(HANDLE) == 8`.
- Diagnostic layout: `STARTUPINFOW` size 104, alignment 8. `STARTUPINFOEXW` size 112, alignment 8.
- SDK include path token: 10.0.28000.0, under a directory token 10.0.28000.2705. Those tokens are path text.
- The same record states that include order is not a measurement of which pack is in force at a particular struct definition.

Offset follow-up, docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFSET_FOLLOWUP_EVIDENCE.md, commit 470c0ba, reprints the same five configuration values and records `WINAPI_EXPANSION=__stdcall` as preprocessor stringization. That line does not show the machine calling convention of a call. It also records `STARTUPINFOW.cb` offsetof 0 and `STARTUPINFOEXW.lpAttributeList` offsetof 104. Those offsets are not a stored `cb` value and not an attribute-list allocation size.

Package label carried by the off-host user-run statement and by the accepted static evidence: Microsoft.Windows.SDK.CPP 10.0.28000.2705. Package SHA-256 carried as prior text: a74ca8f9af98bd61925d9e2932ad98f746306123167b8f0bba99cd9ea9f03807. Header rehash v2 is commit 45855b0. Nupkg internal header comparison is commit 5f9d423. This batch does not rehash the package or the headers.

Grok Build is the original source of the earlier package and header-member reports preserved in docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md (commit 8470ee2) and docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md (commit dbd6ade). Grok Build review is not independent cross-provider verification. No second provider remeasured the nupkg or the headers. Cursor document review is not that verification.

The reused off-host and offset logs do not print `_USE_FULL_PROC_THREAD_ATTRIBUTE`. The accepted static-constant record leaves whether that macro is defined OPEN. This record does not convert that open item into a new measurement.

## 3. Proposed development choices

The Human selects the measured Windows x64 MSVC configuration in section 2 as the development candidate for a future controller build.

- Proposed packing choice: no additional packing override. Preserve the measured configuration that produced the sizes in section 2. This sentence does not select a new pack value.
- Proposed macro choice: leave `_USE_FULL_PROC_THREAD_ATTRIBUTE` undefined for that candidate. This is a proposed build choice. It is not a printed measurement from the reused logs and not a pin.
- This selection does not ratify an SDK pin, a compiler pin, or a controller ABI pin.

## 4. Source observations, not pins

This Human authorization identifies a prior source inspection of the ten `CreateProcessW` parameters and of the source token `STARTF_USESTDHANDLES` with the observed value `0x00000100`. This batch does not repeat that inspection.

Those items are source observations. They are not operational pins. The accepted prior-evidence preservation still records the remaining `CreateProcessW` parameter names, order, and annotations as UNVERIFIED in the Grok Build quotation. This record does not close that mark.

## 5. Remaining ABI gates

`STARTF_USESTDHANDLES`, the active attribute guards, `cb`, the calling convention, and the attribute-list size still require appropriate controller-build evidence or approval. Section 2 does not close them.

`CONTROLLER_ABI_PIN=NOT_RATIFIED`.

## 6. Frozen safety preserved

This record does not edit EB-5, H1, EB-14, F5, the conditional adoption, fixtures, mocks, or executable code.

Preserved conditions:

- EB-5 limited launcher design and the H1 limited design freeze, commit 1107ccf, including `launch_identity=UNBOUND_AT_LAUNCH`.
- EB-14 limited freeze of the six section 9 decisions, commit c413d7d.
- F5 call sequence, refusal contract, and limited Human acceptance, commit debd68e, including the four Resume gates.
- Conditional adoption of corrected C-1 through C-9 at HEAD 83bf96f. C-10 through C-14 remain existing frozen safety. That adoption does not replace EB-5, F5, the EB-14 freeze, or H1.

## 7. Boundary

This batch creates this one documentation file and edits nothing else. It does not stage, commit, push, merge, or force-push. GitHub save requires a separate Human authorization.

COMMITTED: NO
PUSHED: NO
REAL_WINDOWS_EXECUTION: NOT_AUTHORIZED
FULL_INR_READY: NO
