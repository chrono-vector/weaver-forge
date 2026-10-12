# INR-HER MinGit EOF Stdin Limited Design Candidate

Record date: 2026-10-12 (Asia/Tokyo)
Status: EOF_STDIN_LIMITED_DESIGN_CANDIDATE_RECORDED
Scope: one documentation-only design candidate for an EOF-producing anonymous-pipe stdin on the controller-to-target hop
Decision source: the Human authorization to design this candidate only

This document is a design candidate. It is not a design amendment, not a freeze, not an API or ABI specification, and not implementation authorization. It does not amend EB-5, EB-14, or F5. It does not ratify a PIN. It does not demonstrate EOF, MinGit stdin compatibility, or descendant handle containment.

Correction date: 2026-10-12 (Asia/Tokyo). This correction edits this candidate in place. It does not change the status line above. It does not approve EOF encoding.

DESIGN_AMENDMENT=NOT_APPROVED
IMPLEMENTATION=NOT_AUTHORIZED
EOF_BEHAVIOR_DEMONSTRATED=NO
MINGIT_STDIN_COMPATIBILITY=UNVERIFIED
DESCENDANT_HANDLE_CONTAINMENT=UNVERIFIED
FULL_INR_READY=NO

The candidate applies only to the designated stdin pipe of the J1 target (`git.exe`) created by the controller. It does not define Supervisor-to-controller stdin. It does not replace the frozen stdout and stderr pipe-only rule. A candidate property of that one pipe is not a property of every input source.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: ed7c8f082e3c00971ed783d280725c6c155b87d0
Cursor-verified Git HEAD before this document: ed7c8f082e3c00971ed783d280725c6c155b87d0
HEAD comparison: MATCH.

Tracked worktree before this document: no tracked path differed from HEAD. `git status --porcelain=v1` reported only the pre-existing untracked `.wacp/` tree. This document does not read, stage, edit, or delete any `.wacp/` path.

SHA-256 of the frozen and accepted documents named by this candidate, measured from current file bytes before this document was written. These are documentation-file hashes. This document does not edit those files.

- docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md: 61156b5edb2b36589b45502a3f43a16330816dc65deef05d94728b65d891191b
- docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294
- docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md: 64f45f7b55af23fe173e8ad22db4e3516e4df91d4133331c4eb9be3dbe01bc56
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md: b7215021e45d0e5b4fe41ccb34f336155d2dc0963063a36beaaaad4487735175
- docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md: b99bf685afcae6db1e17c3a3421bb4056e2b77860048ad08a955c6d0f15cf446
- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFHOST_MEASUREMENT_EVIDENCE.md: ad4aec65f7ee429ca70c52cc24e6346b1ff7edb72171a1dff357b1ec0497d594
- docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFSET_FOLLOWUP_EVIDENCE.md: 8da9b0447e90a7b8223b5d06915b7ec0c671a1f3316fb7c270fb83872feafc3e
- docs/inr_her_mingit/eb14_f5_fail_closed_mock.py: 7ef8c681a3fd5ae11d41f7053cf0e39514426b88cbecf98fdc2dca54582755b0

Accepted static evidence used only as preserved text, not as a pin and not as pipe behavior:

- `PROC_THREAD_ATTRIBUTE_HANDLE_LIST` arithmetic reading `0x00020002` is recorded under stated header guards and is explicitly not an SDK pin. Source: docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md:180. Source: docs/inr_her_mingit/INR_HER_MINGIT_SDK_STATIC_CONSTANT_EVIDENCE.md:183.
- `STARTUPINFOW` field order including `hStdInput`, `hStdOutput`, and `hStdError` is preserved. Per-field types remain UNVERIFIED in that record. Source: docs/inr_her_mingit/INR_HER_MINGIT_SDK_ABI_PRIOR_EVIDENCE_PRESERVATION.md:189.
- A transferred off-host translation recorded `sizeof(HANDLE) == 8` among other compile-time assertions. That record is not a pipe test and not an ABI pin for this candidate. Source: docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFHOST_MEASUREMENT_EVIDENCE.md:76.
- A transferred offset diagnostic recorded `STARTUPINFOW.hStdInput` offsetof 80, `hStdOutput` 88, and `hStdError` 96. That diagnostic is a failed compile used as measurement. It does not show that storing a handle at that offset changes a child stdin. Source: docs/inr_her_mingit/INR_HER_MINGIT_X64_MSVC_ABI_OFFSET_FOLLOWUP_EVIDENCE.md:99.

The existing fail-closed mock keeps `CLOSED_STDIN_WIN32_ENCODING = "UNRESOLVED"` and `HANDLE_LIST_WIN32_ENCODING = "UNRESOLVED"`. Its hypothetical closed-stdin token is not a HANDLE, and that mock does not use `HANDLE_LIST` to encode closed stdin. This candidate does not edit that mock.

## 2. Candidate architecture

The controller creates one anonymous stdin pipe and owns every handle of that pipe until a stated close point. The target, if a future amended procedure is allowed to create it, receives one inheritable duplicate of the stdin read end and does not receive a stdin write end.

Stdout and stderr remain separate anonymous pipes under the already frozen pipe-only output rule. They are listed here only so their write ends cannot be mistaken for stdin writers and cannot be omitted from the exact handle list the frozen text already requires. This candidate does not change their direction: the controller keeps the output read ends; the target is the intended holder of the output write ends.

Proposed handle roles, all created by the controller:

| Role | Pipe | End | Inherit at birth | HANDLE_LIST |
| --- | --- | --- | --- | --- |
| STDIN_READ_PRIVATE | stdin | read | false | no |
| STDIN_WRITE_PRIVATE | stdin | write | false | no |
| STDIN_READ_INHERIT | stdin | read duplicate | true | yes, the only stdin member |
| STDOUT_READ_PRIVATE | stdout | read | false | no |
| STDOUT_WRITE_PRIVATE | stdout | write | false | no |
| STDOUT_WRITE_INHERIT | stdout | write duplicate | true | yes |
| STDERR_READ_PRIVATE | stderr | read | false | no |
| STDERR_WRITE_PRIVATE | stderr | write | false | no |
| STDERR_WRITE_INHERIT | stderr | write duplicate | true | yes |

`STDIN_WRITE_PRIVATE` is the only stdin writer the controller is allowed to create. The controller must not duplicate it, must not mark it inheritable, and must not place it in `HANDLE_LIST` or in any standard-handle slot.

The intended child stdin receipt is `STDIN_READ_INHERIT` alone. The phrase "only the explicitly intended inheritable read handle" in this candidate means only that read end of the stdin pipe. It does not remove `STDOUT_WRITE_INHERIT` or `STDERR_WRITE_INHERIT`. Removing those two output write handles would contradict the frozen handle-list membership. This candidate does not propose that removal.

No handle in this table is a `NUL` device, a `DEVNULL` device, a null pointer, or an invalid-handle sentinel. No role is supplied by parent-process standard handles, by `Popen`, or by assignment of a Job after create.

### 2.1 Phases

The phases are ordered. A later phase must not start if an earlier phase has no recorded success. Job binding is not a phase after process creation.

Phase H, handle creation, before any process creation:

1. Create the stdin pipe so both private ends are non-inheritable.
2. Create the stdout pipe the same way.
3. Create the stderr pipe the same way.
4. Duplicate `STDIN_READ_PRIVATE` once to `STDIN_READ_INHERIT` with the inheritable flag true. Do not change the private read end to inheritable.
5. Duplicate `STDOUT_WRITE_PRIVATE` once to `STDOUT_WRITE_INHERIT` with the inheritable flag true.
6. Duplicate `STDERR_WRITE_PRIVATE` once to `STDERR_WRITE_INHERIT` with the inheritable flag true.
7. Close `STDIN_READ_PRIVATE`, `STDOUT_WRITE_PRIVATE`, and `STDERR_WRITE_PRIVATE` in the controller after those duplicates exist.
8. Close `STDIN_WRITE_PRIVATE` in the controller and record that close. This close is pre-`CreateProcessW` preparation, consistent with F5 section 4 refusal rule 1 at line 83: pipe preparation failure means no create. Verification of this close is the section 4.1 preparation check. It is not a Resume condition. A recorded success is controller-local closure evidence only. It does not prove a zero kernel write-handle reference count, does not prove EOF, and does not authorize launch.

Phase A, attribute assembly, still before process creation:

- Proposed `STARTUPINFO` standard-handle slots, which are not creation flags: stdin slot = `STDIN_READ_INHERIT`; stdout slot = `STDOUT_WRITE_INHERIT`; stderr slot = `STDERR_WRITE_INHERIT`.
- The use of a standard-handle flag bit in `STARTUPINFO.dwFlags` is a proposed encoding. Section 5 records that the frozen contract leaves that bit unspecified. This candidate does not assign a numeric value to that bit. The accepted static-constant record does not pin it.
- Exact `HANDLE_LIST` members, in this order: `STDIN_READ_INHERIT`, `STDOUT_WRITE_INHERIT`, `STDERR_WRITE_INHERIT`. Count three. No other member.
- `JOB_LIST` contains J1 only and is a different attribute from `HANDLE_LIST`. The J1 handle is non-inheritable and is not a `HANDLE_LIST` member.
- `bInheritHandles=TRUE` is proposed only together with that exact list. The three frozen creation flags remain the only creation flags: `EXTENDED_STARTUPINFO_PRESENT`, `CREATE_SUSPENDED`, `CREATE_UNICODE_ENVIRONMENT`. This candidate adds no creation flag.

Phase P, process creation:

- One suspended `CreateProcessW` of the absolute IMAGE, with the attribute list from Phase A.
- Creation-time Job binding is the `JOB_LIST` attribute on this call.
- On success, the target primary thread remains suspended. The controller then closes its own copies of the three inheritable handles. The candidate's assumption, unverified, is that a successful create has already duplicated those listed handles into the suspended target. If that assumption is not proven, Phase P must not be entered.

Phase J, Job binding:

- This is not after Phase P. It is the `JOB_LIST` component of Phase P.
- `AssignProcessToJobObject` after create is not a phase and is not a repair.

Phase R, resume decision:

- `ResumeThread` stays at most once, on the retained J1 target primary thread, and only when all four frozen resume conditions hold. Those four are unchanged and are restated in section 6.3. This candidate adds no fifth Resume condition. Writer closure is not a Resume condition.
- The stdin writer close is verified in Phase H, before `CreateProcessW`. If that verification fails, Phase P does not start, and the resume decision is not reached. A close after the target is running does not repair that miss and is not a Resume condition.
- Entering Phase R does not mean the pre-create close proved EOF or authorized launch.

### 2.2 Inheritance epoch

The inheritance epoch starts when the first inheritable duplicate is created and ends when every inheritable duplicate has been closed in the controller, either after a successful create or on a failure path. During the epoch the controller must not create any other process. If the controller cannot prove that it is the only process creator in that process for the whole epoch, it refuses before creating the first inheritable duplicate.

A non-inheritable flag on the private ends is not that proof. A Job DACL is not that proof. An unnamed pipe is not that proof.

## 3. Handle ownership, lifetime, close point, and failure

Owner means the component that is allowed to close the handle and the only component that may duplicate it. The target is not an owner of any controller-private handle. After a successful create, the target is the owner of whatever inherited instances the kernel placed in the target. Those inherited instances are not the same handle values as the controller copies. This ownership split is an assumption requiring host verification. It is not demonstrated.

| Role | Owner while open | Lifetime | Close point | If the step fails |
| --- | --- | --- | --- | --- |
| STDIN_READ_PRIVATE | controller | Phase H only | Immediately after `STDIN_READ_INHERIT` exists and before create | No create. Close any ends already open. Refuse before launch. |
| STDIN_WRITE_PRIVATE | controller | Phase H only | Before create, after the inheritable read duplicate exists, and before `HANDLE_LIST` is consumed by create | Close result other than recorded success: controller-local writer closure is absent. Refuse before launch. Phase P does not start. This row is not a Resume condition. Recorded local success does not prove a zero kernel write-handle reference count, does not prove EOF, and does not authorize launch. No second close is success. |
| STDIN_READ_INHERIT | controller until create returns; intended inherited instance then owned by the target | Through Phase P | Controller copy closes after successful create and before Resume. On create failure, controller copy closes on the failure path and no inherited ownership is claimed | Duplicate failure: no create. Create failure: no Resume, no re-create. Unproven duplication-into-child: do not enter Phase P. |
| STDOUT_READ_PRIVATE | controller | Through the bounded stdout reader | Reader shutdown or failure closure. Not an EOF signal for stdin | Preparation failure: no create. Reader failure after create follows the frozen pipe-failure row and is non-success. |
| STDOUT_WRITE_PRIVATE | controller | Phase H only | After `STDOUT_WRITE_INHERIT` exists and before create | No create. |
| STDOUT_WRITE_INHERIT | controller until create returns; intended inherited instance then owned by the target | Through Phase P | Controller copy closes after successful create and before Resume | Same refusal pattern as `STDIN_READ_INHERIT`. This handle is an stdout writer. It is not evidence about stdin writers. |
| STDERR_READ_PRIVATE | controller | Through the bounded stderr reader | Reader shutdown or failure closure | Same as stdout read. |
| STDERR_WRITE_PRIVATE | controller | Phase H only | After `STDERR_WRITE_INHERIT` exists and before create | No create. |
| STDERR_WRITE_INHERIT | controller until create returns; intended inherited instance then owned by the target | Through Phase P | Controller copy closes after successful create and before Resume | Same refusal pattern as the stdout inheritable write. |
| J1 | controller | Existing EB-14 lifetime | Existing single-owner closure. Not closed to produce stdin EOF | Missing or inheritable J1, or J1 placed in `HANDLE_LIST`: refuse before launch. |
| Target process and primary thread | controller | Through membership checks, the resume decision, and exit confirmation | Existing F5 retention. Not pipe ends | Create failure authorizes no Resume. |

Failure disposition for every row: fixed refusal, cleanup non-success until the frozen confirmation of process signalling and no remaining Job-associated members is present, and no success inferred from a close attempt, a terminate return, or an empty local inventory. Out-of-Job descendants and external pipe holders stay outside the cleanup claim.

A further close attempt after a failed close may be recorded only as an unverified cleanup attempt. It does not authorize create, Resume, retry, or a success claim.

## 4. EOF candidate property and closure evidence

The candidate EOF property is narrow. It is a proposed property of the designated stdin anonymous pipe only: before `CreateProcessW`, the controller records a successful close of its only stdin writer, `STDIN_WRITE_PRIVATE`. It is not a property of every input source. It is not a kernel-wide write-handle reference count. It is not a C end-of-file on the target's stdin. It does not prohibit input through any other channel. Pre-create closure, including a local record of success, does not by itself prove EOF and does not authorize launch. This document does not establish that Windows, the CRT, or MinGit implement that property.

Controller-local closure evidence and global kernel-wide reference proof are different records. Section 4.1 is the first. Section 4.2 is the second. The first can be present while the second is absent. Presence of the first does not supply the second.

### 4.1 Controller-local closure evidence, checked before CreateProcessW

The controller may record a local inventory only. The inventory is a logical record. It is not a HANDLE, not a kernel handle count, and not host evidence. It is checked as pre-`CreateProcessW` preparation. F5 section 4 refusal rule 1, at line 83, already requires that pipe preparation failure means no create. This candidate uses that existing refusal point for the local facts below. It does not add a Resume condition.

Necessary local facts, all required before Phase P:

- Stdin writer slots created = 1, and that slot is `STDIN_WRITE_PRIVATE`.
- Stdin writer duplicate count = 0.
- The stdin writer inherit flag was false at creation and was never set true.
- The stdin writer never appeared in `HANDLE_LIST`, never appeared in a standard-handle slot, and was never passed to process creation.
- The single close of `STDIN_WRITE_PRIVATE` was recorded as success and occurred in Phase H, before Phase P.
- No later slot reopened a stdin writer.
- The inventory is immutable after that close record.
- `HANDLE_LIST` is exactly the three inheritable roles in section 2, each still inheritable at assembly, each owned by the controller, with no Job handle and no private read end.
- The inheritance epoch exclusivity claim is present. If it is absent, refusal is before the first inheritable duplicate.

If any necessary local fact is missing or ambiguous, refuse before launch. Phase P does not start. That refusal is preparation failure, or, where the missing fact is ownership, duplication prevention, or inheritance boundaries, the existing launch refusal. It is not a fifth Resume condition. A complete local inventory still does not prove EOF and does not authorize launch.

Ownership, duplication prevention, inheritance boundaries, and launch refusal stay in force. A Job DACL, an unnamed handle, or a non-inheritable flag is still not proof of those boundaries. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:86.

### 4.2 Global kernel-wide reference proof this candidate does not have

The following would be required before anyone could claim that every write reference to the designated stdin pipe is closed. None of them is provided here. Their absence is not converted into a Resume condition.

- A kernel or documented host observation that the stdin pipe's write-handle reference count is zero.
- Exclusion of `DuplicateHandle` by another process, including a same-user holder with `PROCESS_DUP_HANDLE`, a debugger, or other external pipe holder. Anonymous-pipe documentation states that a process can duplicate a pipe handle with `DuplicateHandle` and send it to an unrelated process. That sentence documents an API capability. It is not a host observation that such a holder exists, and it is not a proof that no such holder exists. Source: https://learn.microsoft.com/en-us/windows/win32/ipc/anonymous-pipe-operations
- Exclusion of a writer inherited by the target or by a descendant. The pipe-inheritance page states that if the child inherits the pipe's write handle, a `ReadFile` by the child cannot return zero, because the child still has an open write end. That sentence is a documented condition. This candidate does not demonstrate that the condition is met on a host. Source: https://learn.microsoft.com/en-us/windows/win32/ipc/pipe-handle-inheritance
- A demonstrated mapping from "no writer remains" to the read result observed by `ucrt64/bin/git.exe`.

Hostile handle duplication, debugger access, inheritance races, external holders, and host-dependent MinGit/UCRT behavior remain nonclaims. They are proposed threat-model assumptions where this candidate says they are unexcluded. They are not accepted security proofs.

External pipe holders are already outside the frozen cleanup claim. Local close of `STDIN_WRITE_PRIVATE` does not bring them inside that claim. Controller-local inventory is not accepted by this document as proof that all writer handles are closed.

### 4.3 Other input channels, console inheritance, and unapproved creation flags

The candidate EOF property does not prohibit input through channels other than the designated stdin pipe.

Documented console behavior, cited here and not host-tested:

- `GetStdHandle` remarks state that if the standard handles have been redirected, `CreateFile` can be called with `CONIN$` to get a handle to a console's input buffer. Source: https://learn.microsoft.com/en-us/windows/console/getstdhandle
- The console-handles page states that `CreateFile` can get a handle to the console's input buffer even if `STDIN` has been redirected, by specifying `CONIN$`. Source: https://learn.microsoft.com/en-us/windows/console/console-handles

Those sentences support this candidate statement: closing or redirecting the designated stdin pipe does not, on that documentation, prohibit console input opened as `CONIN$` when the process has a console input buffer. They do not demonstrate that the J1 target has a console. They do not demonstrate `CreateFile` behavior when no console exists.

Documented process-creation defaults and flags, from https://learn.microsoft.com/en-us/windows/win32/procthread/process-creation-flags and the `CreateProcessW` parameter text at https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw :

- `CREATE_NEW_CONSOLE` is described as giving the new process a new console, instead of inheriting its parent's console, and that inheritance is called the default.
- `DETACHED_PROCESS` is described, for console processes, as not inheriting the parent's console, again called the default, and as allowing a later `AllocConsole`.
- `CreateProcessW` states the parent's-console inheritance sentence for `dwCreationFlags` value 0. The frozen flag set is not the value 0. This candidate does not reclassify the frozen combination as a measured console inheritance. It does record that console inheritance is the documented default when `DETACHED_PROCESS` and `CREATE_NEW_CONSOLE` are absent, so console inheritance remains possible under the frozen flags.
- `CREATE_NO_WINDOW` is described as running a console application without a console window so that the console handle is not set, and as ignored when the application is not a console application or when the flag is used with `CREATE_NEW_CONSOLE` or `DETACHED_PROCESS`. That description does not say that every later input open is prohibited.

`DETACHED_PROCESS` and `CREATE_NO_WINDOW` are unapproved options. This candidate does not add either flag. The frozen creation flags remain `EXTENDED_STARTUPINFO_PRESENT`, `CREATE_SUSPENDED`, and `CREATE_UNICODE_ENVIRONMENT`. F5 is not amended. Selecting either flag later would require the Human amendment named in section 6.5. Neither official description is treated as a complete input prohibition, and `DETACHED_PROCESS` explicitly leaves `AllocConsole` available.

`GIT_TERMINAL_PROMPT=0` is the frozen EB-5 environment row. That row limits the value to explicit nonterminal-prompt intent and states that it does not disable every askpass/helper. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:88. This candidate states the further limit that the same value is not a complete input prohibition. It does not change the EB-5 row.

Documented pipe-read outcomes are not collapsed into one EOF result. The pipe-inheritance page says that when all write handles to the pipe are closed, `ReadFile` returns zero. Source: https://learn.microsoft.com/en-us/windows/win32/ipc/pipe-handle-inheritance . The anonymous-pipe operations page says `ReadFile` can return if all write handles have been closed, and does not state the return value. Source: https://learn.microsoft.com/en-us/windows/win32/ipc/anonymous-pipe-operations . The `ReadFile` page says that if an anonymous pipe's write handle has been closed, `ReadFile` on the corresponding read handle returns `FALSE` and `GetLastError` returns `ERROR_BROKEN_PIPE`, and, separately, that a `TRUE` return with zero bytes read means the other end called `WriteFile` with a zero byte count. Source: https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-readfile . This candidate does not choose among those documented outcomes and does not map any of them to UCRT or MinGit. The "all write handles" wording is the global condition in section 4.2, which controller-local closure does not establish.

## 5. Fail-closed rules

These rules are candidate obligations. They do not rewrite F5. Where section 6 says a rule would change a frozen clause, that change is not operative until a future Human amendment adopts it. Until that amendment, the safe reading for the unamended encoding is refusal before launch. That pre-launch refusal is not a fifth Resume condition. The four frozen Resume conditions stay the only Resume conditions.

1. If the controller-local stdin writer close in section 4.1 is missing or not recorded as success, refuse before launch. That refusal is preparation failure under the existing F5 point at line 83. It is not a fifth Resume condition. Recorded local success does not prove the section 4.2 global reference condition, does not prove EOF, and does not authorize launch. Absence of the global proof is retained as a nonclaim. It is not converted into a Resume refusal.
2. If ownership or inheritance boundaries cannot be proven, refuse before launch. A Job DACL, an unnamed handle, or a non-inheritable flag is not that proof.
3. If `HANDLE_LIST` is unsupported or ambiguous, refuse before launch. Ambiguous includes: attribute numeric value not pinned; pointer width or `sizeof(HANDLE)` not pinned for the actual build; byte length not equal to three times a pinned handle size; member set different from the three inheritable roles; any member not inheritable; any standard-handle slot absent from the list; any private end, Job handle, or unrelated handle present; the existing mock encoding `UNRESOLVED` or the hypothetical closed-stdin token used as if it were a list member.
4. No fallback. Refusal does not substitute `NUL`, `DEVNULL`, a null standard-handle pointer, an invalid-handle sentinel, `Popen`, `bInheritHandles=FALSE` without the list, or a create that omits `HANDLE_LIST`.
5. No assign-after-create. Job binding stays inside Phase P.
6. No retry, no re-create, no relaxed relaunch, and no relaxed environment. One failed close, one failed create, or one refused Resume does not start a second attempt.
7. Unverified cleanup is non-success. A successful terminate return, root exit, or one active-process query is not confirmation.
8. Pipe, attribute, or `SetInformation` preparation failure means no create.
9. A failed create authorizes no Resume.
10. The frozen four resume conditions stay the only resume conditions, unchanged. This candidate does not add a fifth condition and does not waive membership, bounded stdout and stderr readers, the controller deadline, or Supervisor-confirmed readiness. Writer-closure evidence is not a substitute for any of the four.
11. The candidate EOF property does not prohibit input through other channels, including console access such as `CONIN$`. `GIT_TERMINAL_PROMPT=0` is not a complete input prohibition. `DETACHED_PROCESS` and `CREATE_NO_WINDOW` are unapproved options and are not added as creation flags.

## 6. Comparison with frozen EB-5 closed stdin and F5 HANDLE_LIST

The freeze preserves EB-5 closed stdin and states that `DEVNULL` is a different handle state. It leaves the Win32 encoding of "closed" unspecified, including the handle value, the `STARTF` bit, and absence. This candidate is a third proposal. It is not a reading of the freeze in which EOF semantics are already authorized.

### 6.1 EB-5 closed-stdin requirement

Exact lifecycle sentence:

> If a separately approved run becomes possible, launch the absolute image with shell disabled, closed stdin, no inherited extra handles and bounded binary stdout/stderr through pipes only, never console output (N1).

Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:170.

Clause-by-clause:

- "closed stdin" names no pipe, no read handle, no write-end close, and no EOF. Mapping it to `STDIN_READ_INHERIT` plus a closed write end requires a future Human amendment.
- "no inherited extra handles" can include an inheritable stdin read handle until a Human amendment says that handle is the closed-stdin encoding and is not an extra handle. This candidate does not make that classification.
- "bounded binary stdout/stderr through pipes only" is the output rule. It authorizes stdout and stderr pipes. It does not authorize an stdin pipe. H1 freezes that output principle and does not mention stdin pipes. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md:20.

### 6.2 F5 HANDLE_LIST wording

Exact sequence sentence:

> `HANDLE_LIST` is exact. When it is used, `bInheritHandles=TRUE`, and the listed handles must be inheritable. Child inheritance is the preserved EB-5 closed stdin together with the stdout and stderr write handles. Job handles, parent read ends, and unrelated handles are excluded.

Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:70.

Clause-by-clause:

- "HANDLE_LIST is exact" is compatible with a three-member list only after a Human amendment names the members. The current exact member for stdin is the words "preserved EB-5 closed stdin", not `STDIN_READ_INHERIT`.
- "bInheritHandles=TRUE" and "listed handles must be inheritable" match the candidate's proposed flags for the three inheritable roles. Those flags are not authority to launch while the list's stdin member is still the unspecified closed-stdin encoding.
- "Child inheritance is the preserved EB-5 closed stdin together with the stdout and stderr write handles" is the membership sentence. Replacing the closed-stdin member with an inheritable pipe read handle changes that sentence and requires a future Human amendment.
- "Job handles, parent read ends, and unrelated handles are excluded" already excludes J1, `STDOUT_READ_PRIVATE`, `STDERR_READ_PRIVATE`, and every unrelated handle. "Parent read ends" can also be read as excluding every read handle, including `STDIN_READ_INHERIT`. That reading is unresolved. An ambiguous exclusion is `HANDLE_LIST` ambiguity and refuses before launch. A future amendment must say, if it adopts this candidate, that the excluded parent read ends are the controller's stdout and stderr read ends and the controller's private stdin read end, and that the listed stdin member is the inheritable stdin read duplicate.
- The candidate keeps the stdout and stderr write handles in the list. That part repeats the frozen membership and is not a new output design.

Exact preservation sentence:

> EB-5 closed stdin is preserved. DEVNULL is not selected and is not the same handle state.

Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:71. The same decision is frozen at docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md:49 and recorded as NF4 at docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md:63.

An EOF pipe is not `DEVNULL` in this candidate, and it is also not yet "closed stdin". Treating the pipe as the preserved state would amend NF4 and F5 section 3 item 11.

Exact non-closed sentence:

> Closed-stdin Win32 encoding. The preserved rule is EB-5 closed stdin, not DEVNULL. The handle value, `STARTF` bit, or absence that encodes "closed" is not specified.

Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:106.

This candidate proposes a handle identity (`STDIN_READ_INHERIT`) and proposes that a standard-handle `STARTF` bit be set. It does not propose absence, a null pointer, or an invalid-handle sentinel. Adopting the proposal would specify an encoding that F5 section 6 and the F5 acceptance both leave NON-CLOSED. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:53. That adoption requires a future Human amendment. This document does not close the item.

### 6.3 Resume gate

F5 permits one `ResumeThread` only after four conditions, and if any of the four is missing there is no resume. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:76. The F5 acceptance states the same four. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:44.

The four conditions, unchanged by this candidate, are:

1. Required membership and configuration have been verified from trusted API results. That verification is defense-in-depth and does not replace creation-time J1 membership.
2. Bounded stdout and stderr readers have been started.
3. The controller deadline has been armed. This candidate sets no numeric deadline.
4. The independent Supervisor wall-clock monitor has been armed and confirmed ready by the Supervisor itself. Controller self-report alone is insufficient.

Writer closure is none of those four. This candidate does not withhold Resume when the four hold. It does not add writer closure as a fifth condition. Moving the controller-owned stdin writer close verification to pre-`CreateProcessW` preparation uses the existing preparation-failure refusal at F5 line 83. It does not amend the resume paragraph at F5 line 76. Pre-create local closure still does not prove EOF and does not authorize launch.

### 6.4 Clauses that do not need an amendment to remain in force

The candidate relies on these frozen clauses and does not ask to weaken them:

- Creation-time `JOB_LIST`, no assign-after-create, no `Popen` substitute for that binding. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:66. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:84.
- No added creation flag, and the prohibition on `CREATE_BREAKAWAY_FROM_JOB`. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:68. `DETACHED_PROCESS` and `CREATE_NO_WINDOW` are not added. They remain unapproved options outside the frozen three flags.
- Refusal before create on preparation failure. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:83.
- Refusal before launch when handle-duplication prevention and ownership cannot be proven. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:86.
- No retry, re-create, relaxed relaunch, `Popen` fallback, or assign-after-create after failure. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:91.
- Cleanup limited to confirmed Job-associated processes; external pipe holders outside that claim. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:95.
- Single owner and one closure point for every pipe handle, plus a reviewed race policy for temporarily inheritable handles. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:73. The policy in section 2.2 is a proposal. It is not the missing reviewed proof.
- The four frozen Resume conditions. This candidate does not ask to add, remove, or restate them as a different gate. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:76.

### 6.5 Amendment list

A future Human-approved design amendment is required before any of the following becomes operative. This candidate does not adopt any of them.

1. Declare the EOF pipe to be the EB-5 "closed stdin" encoding, or declare it a rejected alternative. The EB-5 lifecycle sentence at line 170 does not name a pipe, a read handle, a write-end close, or EOF.
2. Replace the F5 `HANDLE_LIST` stdin member "preserved EB-5 closed stdin" with `STDIN_READ_INHERIT`. That member is F5 section 3 item 10, at line 70.
3. Resolve the "parent read ends" exclusion so the inheritable stdin read duplicate is either listed or forbidden. The exclusion is in the same F5 sentence at line 70.
4. Specify the handle value and the `STARTF` bit that F5 section 6 leaves unspecified, and close that NON-CLOSED item only by that amendment. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:106. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:53.
5. Define the proof standard that can satisfy "all writer handles closed" without shrinking the external-pipe-holder nonclaim. F5 section 5 already places external pipe holders outside the cleanup claim, at line 95. This candidate does not ask to shrink that sentence.
6. Accept or reject controller-local inventory as evidence. This candidate rejects it as sufficient for EOF and as launch authority. A future amendment would still be required before any acceptance of that inventory as encoding evidence.
7. Add `DETACHED_PROCESS` or `CREATE_NO_WINDOW`, or any other creation flag. F5 section 3 item 8, at line 68, names only `EXTENDED_STARTUPINFO_PRESENT`, `CREATE_SUSPENDED`, and `CREATE_UNICODE_ENVIRONMENT`, and adds no creation flag. This candidate does not request that amendment.
8. Treat `GIT_TERMINAL_PROMPT=0` as a complete input prohibition, or as disabling every askpass/helper. That would change the EB-5 environment row at line 88. This candidate does not request that amendment.
9. Authorize any future implementation, host test, or PIN. This list does not authorize them.

This candidate does not request an amendment of the four Resume conditions. A fifth Resume condition is not proposed. Pre-`CreateProcessW` verification of the controller-owned stdin writer close is the existing preparation-failure refusal at F5 line 83, not a new resume clause.

## 7. Host verification still required

The 2026-10-12 correction consulted only the Microsoft Learn pages cited in sections 4.2 and 4.3, and only for the sentences recorded there. It did not compile, did not call Win32, and did not launch a process. A cited sentence is documented Win32 text. It is not host evidence and not an accepted security proof. Behavior those sentences do not settle stays an assumption or a gap. None of the items below is a demonstrated host result.

- Whether pipe creation with a non-inheritable security attribute yields two non-inheritable ends, and whether one creation call can set different inherit flags on the two ends.
- Whether one inheritable `DuplicateHandle` of the read end leaves the source write end non-inheritable.
- Whether `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`, when `bInheritHandles=TRUE`, inherits only the listed handles on the host that would run the controller. Header presence under `_WIN32_WINNT >= 0x0600` is not that host fact. The arithmetic value `0x00020002` is not a pin.
- Whether every standard-handle value must also be a list member, and whether a non-inheritable list member fails process creation. Error mapping remains NON-CLOSED.
- Handle size, attribute-list layout, `STARTUPINFOEX` size, and calling convention for the actual controller build. Preserved offsetof and `sizeof(HANDLE) == 8` measurements are not that pin and are not stdin behavior.
- The numeric value and effect of the standard-handle flag in `STARTUPINFO.dwFlags`. Not pinned by the accepted static-constant record.
- Whether a successful suspended create duplicates listed inheritable handles into the target before return, so the controller may close its copies without closing the target's copies.
- Whether a non-inheritable write end that is absent from `HANDLE_LIST` is absent from the target handle table.
- Which documented pipe-read outcome occurs after write handles close. Section 4.3 records separate Microsoft sentences for `ReadFile` returning zero when all write handles are closed, for `FALSE` with `ERROR_BROKEN_PIPE`, and for a successful zero-byte read after a zero-byte `WriteFile`. Those sentences are not one outcome. Which one the selected host returns, and whether the UCRT linked by the selected MinGit maps any of them to a C end-of-file on stdin, is unverified. MinGit stdin compatibility is not demonstrated. Controller-local close does not establish the documented "all write handles" condition.
- Whether the J1 target has a console under the frozen creation flags. The documented default is not a measurement of this host. `CONIN$` after a redirected standard input is documented where a console input buffer exists. Behavior with no console is not settled by the cited `GetStdHandle` sentence.
- Whether `git.exe` or a descendant blocks, reopens stdin, or duplicates a handle the target did not receive.
- Descendant handle containment. Job membership is not a handle-table proof. Out-of-Job descendants remain outside the frozen cleanup claim. Descendant handle containment is not demonstrated.
- Whether `CloseHandle` success equals a zero kernel reference count in the presence of other duplicators.
- The inheritance-epoch claim against concurrent creates in the same process.
- Death during create, existing Job nesting, and partial process cleanup. Already OPEN in F5. This candidate adds no host evidence.

## 8. Non-executing test plan

This section proposes future fixture tests. It does not add a test file, does not modify `eb14_f5_fail_closed_mock.py`, and does not run tests. A future batch must be separately authorized before any fixture module exists.

The fixtures are logical tokens. They must not be numeric HANDLE values, must not call Win32, and must not import or name a process-creation port. Suggested forbidden port names remain those already listed by the existing mock, including `CreateProcessW`, `Popen`, and `AssignProcessToJobObject`. Suggested dispositions remain only `REFUSED`, `UNEXECUTED`, and `UNCONFIRMED`. No fixture result is PASS, host evidence, or execution identity.

Proposed cases:

1. Local inventory complete, frozen four resume conditions true, Human encoding amendment absent. Expect refuse before launch and `EOF_STDIN_ENCODING_UNAMENDED`. Do not add a Resume condition. A complete inventory must not become success, EOF proof, or launch authority.
2. Local inventory complete and a fixture flag `kernel_writer_proof=ABSENT`. Expect no EOF claim and no launch authorization from that inventory. Do not refuse Resume because of that flag. `STDIN_WRITERS_UNPROVEN` records the missing global proof. It is not a fifth Resume condition. If the encoding amendment is also absent, the launch refusal remains the unamended-encoding refusal before launch.
3. Writer close result anything other than recorded success, including a second close token. Expect refuse before launch, no create, cleanup `UNCONFIRMED`, reason not success. Resume is not reached. This is not a Resume condition.
4. Stdin writer inherit flag true at any recorded instant. Expect refuse before launch, `STDIN_WRITER_INHERITABLE`.
5. Stdin writer duplicate count greater than zero, or writer present in `HANDLE_LIST`. Expect refuse before launch.
6. `HANDLE_LIST` equal to `UNRESOLVED`, equal to the hypothetical closed-stdin token, equal to a non-list scalar, or missing. Expect refuse before launch, `HANDLE_LIST_REJECTED` or `HANDLE_LIST_AMBIGUOUS`.
7. List members other than the three inheritable roles, including a Job handle, either private read end, `NUL`, `DEVNULL`, `NULL`, or `INVALID`. Expect refuse before launch, `STDIN_FALLBACK_FORBIDDEN` or `HANDLE_LIST_REJECTED`. No create token.
8. Attribute id, handle size, or list byte length unpinned. Expect `HANDLE_LIST_AMBIGUOUS` and refuse before launch.
9. Ownership evidence limited to `DACL`, `UNNAMED_HANDLE`, or `NON_INHERITABLE`. Expect refuse before launch.
10. Inheritance-epoch exclusivity absent. Expect refuse before the first inheritable duplicate.
11. `Popen` or post-create Job assignment present. Expect refuse, no create, no Resume.
12. Create token failed. Expect no Resume and no second create.
13. Retry or relaxed relaunch token present. Expect refusal of the retry. Attempt count stays one.
14. Stdout and stderr readers started while the controller-local writer close is absent. Expect refuse before launch and no create. Readers do not satisfy the pre-create writer-close check and do not add a Resume condition.
15. Cleanup confirmation absent after refusal. Expect `UNCONFIRMED`, including when a terminate-return token is true.
16. A fixture treats `CONIN$` or another non-pipe channel as still available, or proposes `DETACHED_PROCESS` or `CREATE_NO_WINDOW`. Expect no claim that designated-stdin-pipe closure prohibits other input. Expect those two flags absent from the creation-flag set. Expect no F5 amendment token. `GIT_TERMINAL_PROMPT=0` present in the environment token is not a complete input prohibition.

The existing mock's hypothetical closed-stdin token stays unresolved encoding. These cases must not be implemented by editing that mock in a later batch unless a Human amendment says so. A new fixture module, if ever authorized, has to treat EOF-pipe tokens as candidate tokens that still refuse while the amendment is absent.

## 9. Remaining open decisions

1. Whether a Human amendment adopts the EOF pipe as EB-5 closed stdin, rejects it, or leaves the encoding NON-CLOSED.
2. The proof standard for "all writer handles closed", given that local inventory is necessary and not sufficient and that external pipe holders stay outside the cleanup claim.
3. Whether the J1 target has a console under the frozen creation flags, and what `CONIN$` does when no console input buffer exists. The documented default and the redirected-stdin `CONIN$` sentence are not that host measurement. A fifth Resume condition is not an open proposal of this candidate.
4. Whether the standard-handle `STARTF` bit is the encoding to specify, if any encoding is ever specified. No numeric value is chosen here.
5. Which documented `ReadFile` outcome occurs, and whether UCRT or MinGit maps it to C end-of-file. Inside this candidate the controller-owned stdin writer close point is before `CreateProcessW`. Moving that check to Resume is not proposed.
6. What evidence, if any, can prove inheritance-epoch exclusivity.
7. Supervisor-to-controller stdin. Out of scope. No inference.
8. UCRT and MinGit behavior on a writerless stdin pipe. Unverified.
9. ABI pin for handle size, attribute identifiers, and `STARTUPINFOEX`. Still absent.
10. Whether the controller close of `STDIN_READ_INHERIT` after a successful suspended create preserves a target read end.
11. Whether an inherited read handle remains inheritable inside `git.exe`, and whether descendants may hold it. Unverified, and not a writer-closure proof.
12. Fixed reason vocabulary. The reason labels in section 8 are proposals for a future fixture, not a frozen vocabulary.

## 10. Batch boundary

The creating batch created only docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md. The 2026-10-12 correction edits only that same file.

The correction does not stage, commit, push, merge, or modify any other file. It does not read or modify `.wacp/`. It does not edit EB-5, H1, EB-14, F5, EB-0, SDK evidence, the fail-closed mock, or any test. It does not implement, compile, execute a process, or ratify a PIN. EOF encoding stays unapproved.

EOF behavior is not demonstrated. MinGit stdin compatibility is not demonstrated. Descendant handle containment is not demonstrated. FULL_INR_READY=NO.
