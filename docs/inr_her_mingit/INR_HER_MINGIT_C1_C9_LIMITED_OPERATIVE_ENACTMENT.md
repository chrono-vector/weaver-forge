# INR-HER MinGit C-1 through C-9 Limited Operative Enactment

Record date: 2026-10-13 (Asia/Tokyo)
Status: LIMITED_OPERATIVE_ENACTMENT_RECORDED
Decision source: the Human explicit approval of a limited operative enactment that gives corrected C-1 through C-9 precedence only for future launcher behavior.
Scope: this one documentation-only enactment record. It does not edit the proposal, the conditional adoption, EB-5, F5, the EB-14 freeze, H1, fixtures, mocks, or executable code.

LIMITED_OPERATIVE_PRECEDENCE=FUTURE_LAUNCHER_BEHAVIOR_ONLY
PLAN_A=NONLAUNCH
PLAN_B=UNSELECTED
PLAN_C=UNSELECTED
IMPLEMENTATION=NOT_AUTHORIZED
NATIVE_API_EXECUTION=NOT_AUTHORIZED
REAL_WINDOWS_EXECUTION=NOT_AUTHORIZED
OPERATIONAL_MINGIT_PIN=UNRATIFIED
FULL_INR_READY=NO

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: 21e60b8acb0b16628f6a7bafbaa2aef0a407681d
Locally verified HEAD before this record: 21e60b8acb0b16628f6a7bafbaa2aef0a407681d
HEAD comparison: MATCH.

Tracked worktree before this record: no tracked path differed from HEAD. `git status --porcelain=v1` reported only the pre-existing untracked `.wacp/` tree. This record does not read, stage, edit, or delete any `.wacp/` path.

This batch does not recompute documentation hashes inside accepted evidence, does not remeasure SDK or ABI bytes, does not compile, and does not re-run the accepted mock or the accepted ASCII fixture.

## 2. Sources confirmed before enactment

Conditional design adoption, read and not edited:

- Path: docs/inr_her_mingit/INR_HER_MINGIT_EB5_F5_CONDITIONAL_HUMAN_DESIGN_ADOPTION.md
- SHA-256: FEB00E76582965166D4C0064F39E9794F81E4CADE4EC897F182225B8F5C90D98
- Introducing commit: 83bf96f2deecf04af726236ce4525b6985081d65
- Recorded decisions kept: C-1 through C-9 were CONDITIONALLY_ADOPTED_DESIGN; Freeze §89 restricted ASCII/no-space/no-quote profile, C-7 uppercase-key environment ordering, and C-9 restricted argv serialization were HUMAN_DESIGN_SELECTED; C-10 through C-14 were EXISTING_FROZEN_SAFETY_UNCHANGED.

Proposal original, read and not edited:

- Path: docs/inr_her_mingit/INR_HER_MINGIT_EB5_F5_CONSOLIDATED_PROPOSED_AMENDMENT.md
- SHA-256: C53174B3374BA8C9362F51A522961DCAF306CDD9F3DC3131CB2EC5ED9A2A108D
- That digest matches the digest named by the conditional adoption. The proposed sentences in C-1 through C-9 of that file are the text this enactment names.

Frozen files, hashed before this record and not edited. Each digest matches the digest already recorded in the proposal:

- docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md: 42AD74D7951CCB7877EED92EDDA1D1428409B1F70C944BA7855B1D4893010786
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md: 254E91E4BA63B1722CD8E359A13211596CF41C8B07D5A416BC80B2AB760A453B
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md: 61156B5EDB2B36589B45502A3F43A16330816DC65DEEF05D94728B65D891191B
- docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md: AA3C3EBF1F188308367EDBD4EBD231F1357C2247EFE5DE0AF4E55428064DA294

## 3. What is enacted

This record enacts the proposed sentences in C-1 through C-9 of the named proposal as limited operative text. The enactment applies only to future launcher behavior. It does not rewrite EB-5, F5, the EB-14 freeze, or H1. Those files stay the frozen sources they already are. Approved precedence is this record. Silence elsewhere is not a further adoption.

For C-1, the existing frozen text and the enacted PA-1 sentence stay distinct. The existing frozen targets, unedited, are EB-5 line 170, F5 line 71, and EB-14 freeze line 49 together with NF4 at line 63. The enacted PA-1 sentence is the proposal's C-1 sentence: on the controller-to-target hop only, "closed stdin" means one designated anonymous stdin pipe whose only controller-owned writer, `STDIN_WRITE_PRIVATE`, is closed and recorded as success in Phase H before `CreateProcessW`, and whose only child-inherited stdin member is `STDIN_READ_INHERIT`. That encoding is not `DEVNULL` and is not absence. The inheritable stdin read duplicate is the closed-stdin encoding member and is not an extra inherited handle. The property is a property of that one pipe.

C-2, C-3, C-4, C-5, C-6, and C-8 are enacted only as that same future-launcher precedence, by the sentences already written in the proposal. Enactment of the name `STARTF_USESTDHANDLES` in C-3 does not pin its numeric value, the pointer width, or the byte layout. Unpinned ABI, unproven ownership, and the other evidence items named in the proposal's section 6 still refuse before launch. That refusal is the existing preparation and encoding refusal. It is not a fifth Resume condition.

The eleven environment keys in C-6 are part of this limited precedence. The stricter ASCII, no-whitespace, and no-quote value restrictions remain the Human design selection already recorded in the conditional adoption under EB-14 freeze line 89. This record does not make that choice again.

## 4. Conflicting stdin

The frozen F5 section 3 item 10, at line 70, states that child inheritance is the preserved EB-5 closed stdin together with the stdout and stderr write handles, and that parent read ends are excluded. Until a precedence is stated, that stdin member is the words "preserved EB-5 closed stdin", and "parent read ends" can be read as excluding every read handle, including `STDIN_READ_INHERIT`.

For future launcher behavior only, this record gives C-2 precedence on that conflict. When `HANDLE_LIST` is used, `bInheritHandles=TRUE`, the listed handles are inheritable, and the exact members in order are `STDIN_READ_INHERIT`, `STDOUT_WRITE_INHERIT`, and `STDERR_WRITE_INHERIT`. Count three. No other member. The stdin standard-handle slot for that future launcher is `STDIN_READ_INHERIT`. The excluded parent read ends for that future launcher are the controller's private stdout read end, the controller's private stderr read end, and `STDIN_READ_PRIVATE`.

F5 line 70 is not rewritten. The precedence lives in this record and applies only to future launcher behavior. It does not authorize that launcher to be built or started.

## 5. Selections preserved and not re-enacted

C-7 uppercase-key environment ordering and C-9 restricted argv serialization remain the Human design selections already recorded in the conditional adoption. This record does not re-enact them and does not issue a new decision on either clause.

Unproven compatibility stays OPEN. `WINDOWS_ENVIRONMENT_SORT_CLOSED` stays unclosed. `MINGIT_CRT_COMPATIBLE` stays the false fixture mark recorded by the proposal. F5 section 6 environment-block sorting and command-line serialization / MinGit CRT/`wmain` correspondence stay NON-CLOSED. Those open items still refuse before launch.

## 6. Safety that stays in force

C-10 through C-14 remain exactly the existing frozen safety. This enactment does not amend them. That includes the four Resume conditions, creation-time J0 and J1 binding, the independent Supervisor, no retry, no relaxed fallback, and fail-closed ownership. Writer closure is none of the four Resume conditions.

N4 and N5 stay implementation gates and stay OPEN. N4 is Windows loader qualification, including IFEO, AppCertDlls/AppInit_DLLs, `.local`, SxS, KnownDLLs, DLL-search fall-through, and the proposed CWD-content restriction. N5 is Git for Windows config sources, including ProgramData, `TREE_ROOT/etc/gitconfig`, and prefix-relative lookup, fallback, and include behavior. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md:33. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md:34. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:137. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:119.

While N4 or N5 is OPEN or unavailable, the pre-spawn refusal stays in force: emit BLOCKED/UNCONFIRMED and do not spawn. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:169. This record does not close either gate and does not waive that refusal.

## 7. Plans and non-authorization

Plan A remains NONLAUNCH. Plan B is unselected. Plan C is unselected. This limited precedence is not a selection of Plan B or Plan C, and it does not move Plan A off NONLAUNCH.

This enactment authorizes no implementation, no native API execution, no real Windows execution, no Windows host launch, no native binding, no compilation, no installation, no child-process launch, no host Job or EOF test, no SDK remeasurement, no numeric-limit approval, and no operational PIN ratification.

`launch_identity` stays `UNBOUND_AT_LAUNCH`. `EXECUTION_BINDING_REAL` stays `UNEXECUTED`. `REAL_WINDOWS_EXECUTION=NOT_AUTHORIZED`. `FULL_INR_READY=NO`.

## 8. Batch boundary

This batch creates only docs/inr_her_mingit/INR_HER_MINGIT_C1_C9_LIMITED_OPERATIVE_ENACTMENT.md.

FROZEN_BASELINES_UNCHANGED=YES
IMPLEMENTATION=NOT_AUTHORIZED
REAL_WINDOWS_EXECUTION=NOT_AUTHORIZED
FULL_INR_READY=NO
