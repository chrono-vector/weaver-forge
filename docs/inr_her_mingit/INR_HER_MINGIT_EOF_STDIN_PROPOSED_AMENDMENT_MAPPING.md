# INR-HER MinGit EOF Stdin Proposed Amendment Mapping

Record date: 2026-10-12 (Asia/Tokyo)
Status: EOF_STDIN_PROPOSED_AMENDMENT_MAPPING_RECORDED
Scope: one documentation-only record of a Human design-direction selection and a proposed amendment mapping
Decision source: the Human handoff that selects an EOF-producing pipe as the preferred future stdin design direction

This document records a design direction and a proposed mapping. It is not a design amendment, not a freeze, not an API or ABI specification, and not implementation authorization. It does not edit the EOF candidate. It does not edit EB-5, H1, EB-14, F5, or the F5 acceptance. It does not ratify a PIN. It does not demonstrate EOF, MinGit stdin compatibility, or descendant handle containment.

DESIGN_AMENDMENT=NOT_ADOPTED
FROZEN_CONTRACTS_EDITED=NO
IMPLEMENTATION=NOT_AUTHORIZED
EOF_BEHAVIOR_DEMONSTRATED=NO
MINGIT_STDIN_COMPATIBILITY=UNVERIFIED
DESCENDANT_HANDLE_CONTAINMENT=UNVERIFIED
FULL_INR_READY=NO

Technical byte verification in section 2 and the Human direction in section 3 are separate records. A matching digest does not select a direction. A selected direction does not amend a frozen sentence.

## 1. Baseline

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: ed7c8f082e3c00971ed783d280725c6c155b87d0
Cursor-verified Git HEAD before this document: ed7c8f082e3c00971ed783d280725c6c155b87d0
HEAD comparison: MATCH.

Tracked worktree before this document: no tracked path differed from HEAD. `git status --porcelain=v1` reported two pre-existing untracked paths: the `.wacp/` tree and docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md. This document does not read, stage, edit, or delete any `.wacp/` path. It does not edit the candidate.

## 2. Technical verification of the EOF candidate

This section verifies file bytes only. It does not record a Human decision. It does not adopt the candidate. It does not close any NON-CLOSED item.

Subject: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md
Expected SHA-256: 2a955a6473e1e41fb2486489ab5c6ae11f5b60295a2e1c31b2c4c1ba153cb58c
Locally measured SHA-256 before this document: 2a955a6473e1e41fb2486489ab5c6ae11f5b60295a2e1c31b2c4c1ba153cb58c
Exact-byte comparison: MATCH.

The measured digest identifies that candidate document. It does not identify a Git executable, a runtime image, a handle value, or an operational PIN. The candidate status remains EOF_STDIN_LIMITED_DESIGN_CANDIDATE_RECORDED. Its own lines still say DESIGN_AMENDMENT=NOT_APPROVED and IMPLEMENTATION=NOT_AUTHORIZED. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:3. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:12. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:13.

## 3. Human design-direction decision

This section records the Human decision. It is not the digest comparison in section 2. It is not an amendment of any frozen contract.

The Human selects the EOF-producing anonymous pipe, as described by the verified candidate, as the preferred future stdin design direction for the controller-to-target hop.

The selection is a direction for a future amendment. It is not approval to implement, execute, amend frozen contracts, or ratify an operational PIN. Until a later Human amendment adopts operative text, EB-5 closed stdin, F5 `HANDLE_LIST` membership, and the F5 section 6 closed-stdin Win32 encoding remain the frozen sentences. The safe reading while those sentences are unamended remains refusal before launch. That refusal is not a fifth Resume condition.

The selected direction applies only to the designated stdin pipe of the J1 target (`git.exe`) created by the controller. It does not define Supervisor-to-controller stdin. It does not replace the frozen stdout and stderr pipe-only rule. A property proposed for that one pipe is not a property of every input source.

The selected direction does not select `DEVNULL`, `NUL`, a null standard-handle pointer, an invalid-handle sentinel, absence of a standard-handle slot, `Popen`, or assign-after-create. It does not add `DETACHED_PROCESS`, `CREATE_NO_WINDOW`, or any other creation flag.

## 4. Proposed amendment mapping

Each row below is a proposed future amendment. OPERATIVE=NO on every row. None of these rows rewrites EB-5, H1, EB-14, F5, or the F5 acceptance. A later Human amendment would have to adopt a row before that row's proposed text replaces the frozen sentence it names.

### 4.1 PA-1 — EB-5 closed stdin semantics

Frozen sentence:

> If a separately approved run becomes possible, launch the absolute image with shell disabled, closed stdin, no inherited extra handles and bounded binary stdout/stderr through pipes only, never console output (N1).

Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:170.

H1 freezes stdout/stderr through pipes only and does not mention an stdin pipe. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md:20. The EB-14 limited freeze preserves EB-5 closed stdin and states that DEVNULL is not the same handle state. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md:49. NF4 records the same preservation. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md:63. F5 section 3 item 11 preserves the same rule. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:71.

The phrase "closed stdin" names no pipe, no read handle, no write-end close, and no EOF. "No inherited extra handles" does not yet classify an inheritable stdin read duplicate as the closed-stdin encoding. The output-pipe sentence authorizes stdout and stderr pipes. It does not authorize an stdin pipe.

Proposed future text, not adopted: on the controller-to-target hop only, "closed stdin" would mean one designated anonymous stdin pipe whose only controller-owned writer, `STDIN_WRITE_PRIVATE`, is closed and recorded as success in Phase H before `CreateProcessW`, and whose only child-inherited stdin member is `STDIN_READ_INHERIT`. That encoding would not be `DEVNULL` and would not be absence. The inheritable stdin read duplicate would be the closed-stdin encoding member and would not be an extra inherited handle. The stdout and stderr pipe-only rule, the prohibition on console output for those streams, and the EB-5 environment row for `GIT_TERMINAL_PROMPT=0` would stay as frozen. That environment row would remain explicit nonterminal-prompt intent and would remain not a complete input prohibition and not a disablement of every askpass/helper. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md:88.

OPERATIVE=NO. Adopting PA-1 would be required before the candidate pipe could be read as EB-5 closed stdin. This document does not adopt it.

### 4.2 PA-2 — F5 HANDLE_LIST stdin member and parent read ends

Frozen sentence:

> `HANDLE_LIST` is exact. When it is used, `bInheritHandles=TRUE`, and the listed handles must be inheritable. Child inheritance is the preserved EB-5 closed stdin together with the stdout and stderr write handles. Job handles, parent read ends, and unrelated handles are excluded.

Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:70.

The current stdin member is the words "preserved EB-5 closed stdin", not `STDIN_READ_INHERIT`. "Parent read ends" can be read as excluding every read handle, including an inheritable stdin read duplicate. That reading is unresolved. An ambiguous exclusion remains `HANDLE_LIST` ambiguity and, under the candidate's fail-closed rule, refuses before launch. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:259.

Proposed future text, not adopted: when `HANDLE_LIST` is used, `bInheritHandles=TRUE`, the listed handles are inheritable, and the exact members in order are `STDIN_READ_INHERIT`, `STDOUT_WRITE_INHERIT`, and `STDERR_WRITE_INHERIT`. Count three. No other member. The excluded parent read ends would be the controller's private stdout read end, the controller's private stderr read end, and the controller's private stdin read end `STDIN_READ_PRIVATE`. The listed stdin member would be the inheritable stdin read duplicate. Job handles, `STDIN_WRITE_PRIVATE`, and unrelated handles would remain excluded. `STDIN_WRITE_PRIVATE` would also remain absent from every standard-handle slot. The stdout and stderr write-handle membership would repeat the frozen output membership and would not be a new output design.

OPERATIVE=NO. Until PA-2 is adopted, the exact stdin member remains the unspecified preserved closed-stdin encoding, and the parent-read-end exclusion stays ambiguous. Ambiguity refuses before launch. That refusal is not a fifth Resume condition.

### 4.3 PA-3 — STARTF_USESTDHANDLES and stdin encoding

Frozen non-closed sentence:

> Closed-stdin Win32 encoding. The preserved rule is EB-5 closed stdin, not DEVNULL. The handle value, `STARTF` bit, or absence that encodes "closed" is not specified.

Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:106.

The F5 acceptance leaves that item NON-CLOSED. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:53. The candidate proposes a standard-handle flag bit in `STARTUPINFO.dwFlags` and proposes the three standard-handle slots. It assigns no numeric value to that bit. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:98. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:99.

Proposed future text, not adopted: the encoding of closed stdin would be presence of the standard-handle flag whose documented name is `STARTF_USESTDHANDLES`, together with these slots and no other stdin slot: stdin = `STDIN_READ_INHERIT`; stdout = `STDOUT_WRITE_INHERIT`; stderr = `STDERR_WRITE_INHERIT`. The proposed encoding would not be absence, a null pointer, or an invalid-handle sentinel. The three frozen creation flags would remain the only creation flags. `STARTF_USESTDHANDLES` is a `STARTUPINFO.dwFlags` bit in this proposal. It is not a creation flag.

This mapping does not assign a numeric value to `STARTF_USESTDHANDLES`. The accepted static-constant record does not pin that bit. A later amendment that adopted the name would still leave the NON-CLOSED item open until a separate Human pin of the numeric value, the pointer width, and the byte layout for the actual controller build. Until both the name and that pin are adopted, the safe reading is refusal before launch. That refusal is the existing preparation and encoding refusal. It is not a fifth Resume condition. This document does not close F5 section 6 or the F5 acceptance NON-CLOSED list.

OPERATIVE=NO.

### 4.4 PA-4 — Writer ownership, close-before-create, and duplication prevention

Frozen obligations this mapping does not weaken:

- Every pipe handle has one documented owner and one closure point. Concurrent process creation and temporarily inheritable handles require a reviewed race policy. The API and ABI specification of those obligations remains unwritten. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:73.
- Preparation failure refuses before create. Pipe preparation failure means no create. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:83.
- If target-to-controller handle-duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, an unnamed handle, or a non-inheritable flag is not that proof. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:86. Source: docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md:50.
- External pipe holders stay outside the cleanup claim. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:95.
- The refusal rule for ownership is closed. The proof is not. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:110.

Proposed future obligations, not adopted, and only as additional preparation facts under the existing refusal points:

- The controller creates exactly one stdin writer, `STDIN_WRITE_PRIVATE`. That writer is non-inheritable at creation and is never marked inheritable. The controller does not duplicate it. It never appears in `HANDLE_LIST` or in a standard-handle slot.
- The controller closes `STDIN_WRITE_PRIVATE` in Phase H, after `STDIN_READ_INHERIT` exists and before `CreateProcessW`. A recorded local success of that single close is a necessary preparation fact. A result other than recorded success, including a second close treated as success, refuses before create. Phase P does not start. Resume is not reached.
- Controller-local closure evidence is not a kernel write-handle reference count. Recorded local success does not prove EOF, does not prove that every write reference is closed, and does not authorize launch.
- If ownership, duplication prevention, or inheritance boundaries cannot be proven, refuse before launch under the existing F5 rule at line 86. The proposed inventory does not replace that proof. A Job DACL, an unnamed handle, or a non-inheritable flag remains not that proof.
- The candidate inheritance-epoch rule remains a proposal. It is not the missing reviewed race policy required by F5 section 3 item 13.
- External pipe holders, including a same-user `DuplicateHandle` holder, remain outside the cleanup claim. PA-4 does not shrink that sentence.
- The target is not an owner of any controller-private handle. After a successful create, ownership of inherited instances is an assumption requiring host verification. It is not demonstrated.

OPERATIVE=NO. If a later amendment adopts PA-4, the writer-close check stays a pre-create preparation refusal under F5 line 83. It does not become a Resume condition.

### 4.5 PA-5 — Console and CONIN$ nonclaims

No frozen sentence currently states a `CONIN$` prohibition or a console-absence measurement. The candidate records documented console and pipe-read sentences and states that they are not host evidence. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:190. Source: docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_LIMITED_DESIGN_CANDIDATE.md:210.

Proposed future nonclaims, not adopted, which an encoding amendment must preserve rather than erase:

- Closing or redirecting the designated stdin pipe does not, on the cited documentation, prohibit console input opened as `CONIN$` when the process has a console input buffer. Those sentences do not demonstrate that the J1 target has a console, and they do not demonstrate `CreateFile` behavior when no console exists.
- Console inheritance remains possible under the frozen creation flags because `DETACHED_PROCESS` and `CREATE_NEW_CONSOLE` are absent. That statement records a documented default. It is not a measurement that this host inherits a console.
- `DETACHED_PROCESS` and `CREATE_NO_WINDOW` stay unapproved. PA-5 does not add either flag. The frozen creation flags remain `EXTENDED_STARTUPINFO_PRESENT`, `CREATE_SUSPENDED`, and `CREATE_UNICODE_ENVIRONMENT`.
- `GIT_TERMINAL_PROMPT=0` is not a complete input prohibition.
- The candidate EOF property does not prohibit input through channels other than the designated stdin pipe.
- Documented `ReadFile` outcomes are not collapsed into one EOF result. Which outcome a selected host returns, and whether UCRT or MinGit maps any of them to a C end-of-file, stays unverified.

OPERATIVE=NO. PA-5 proposes text that would keep these limits visible. It does not authorize a console flag, a host test, or an input-prohibition claim.

## 5. Preserved safety conditions

This mapping preserves the frozen Resume gate exactly. It adds no fifth condition. It does not withhold Resume when the four conditions hold, and it does not waive any of the four because a writer close was recorded.

F5 permits one `ResumeThread` on the retained J1 target primary thread only after all four conditions hold, and if any of the four is missing there is no resume. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:74. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:76. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md:78. The F5 acceptance states the same four. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:43. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:44. Source: docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md:45.

The four conditions, unchanged:

1. Required membership and configuration have been verified from trusted API results. That verification is defense-in-depth and does not replace creation-time J1 membership.
2. Bounded stdout and stderr readers have been started.
3. The controller deadline has been armed. This mapping sets no numeric deadline.
4. The independent Supervisor wall-clock monitor has been armed and confirmed ready by the Supervisor itself. Controller self-report alone is insufficient.

Writer closure is none of those four. A missing controller-local writer close refuses before `CreateProcessW` under the existing preparation-failure rule. It does not amend the resume paragraph. A failed `CreateProcessW` authorizes no `ResumeThread`. A second `ResumeThread` remains prohibited.

Ownership and refusal conditions that stay in force, and that this mapping does not weaken:

- Creation-time `JOB_LIST`, no assign-after-create, and no `Popen` substitute for that binding.
- No added creation flag, and the prohibition on `CREATE_BREAKAWAY_FROM_JOB`.
- Refusal before create on preparation failure.
- Refusal before launch when handle-duplication prevention and ownership cannot be proven. A Job DACL, an unnamed handle, or a non-inheritable flag is not that proof.
- No retry, re-create, relaxed relaunch, `Popen` fallback, or assign-after-create after failure.
- Cleanup limited to confirmed Job-associated processes. External pipe holders stay outside that claim.
- Single owner and one closure point for every pipe handle, plus the still-unwritten reviewed race policy for temporarily inheritable handles.
- No fallback to `NUL`, `DEVNULL`, a null standard-handle pointer, an invalid-handle sentinel, or a create that omits `HANDLE_LIST`.
- Unverified cleanup is non-success. A successful terminate return, root exit, or one active-process query is not confirmation.

## 6. Host-dependent assumptions

None of the following is a demonstrated host result. The 2026-10-12 candidate correction cited Microsoft Learn sentences and did not compile, call Win32, or launch a process. A cited sentence is documented text. It is not host evidence and not an accepted security proof. This mapping adds no host evidence.

- Whether pipe creation with a non-inheritable security attribute yields two non-inheritable ends, and whether one creation call can set different inherit flags on the two ends.
- Whether one inheritable `DuplicateHandle` of the read end leaves the source write end non-inheritable.
- Whether `PROC_THREAD_ATTRIBUTE_HANDLE_LIST`, when `bInheritHandles=TRUE`, inherits only the listed handles on the host that would run the controller. Header presence and the arithmetic value `0x00020002` are not that host fact and are not a pin.
- Whether every standard-handle value must also be a list member, and whether a non-inheritable list member fails process creation. Error mapping remains NON-CLOSED.
- Handle size, attribute-list layout, `STARTUPINFOEX` size, and calling convention for the actual controller build. Preserved offsetof and `sizeof(HANDLE) == 8` measurements are not that pin and are not stdin behavior.
- The numeric value and effect of `STARTF_USESTDHANDLES` in `STARTUPINFO.dwFlags`. Not pinned here.
- Whether a successful suspended create duplicates listed inheritable handles into the target before return, so the controller may close its copies without closing the target's copies.
- Whether a non-inheritable write end that is absent from `HANDLE_LIST` is absent from the target handle table.
- Which documented pipe-read outcome occurs after write handles close, and whether the UCRT linked by the selected MinGit maps any of them to a C end-of-file on stdin. Controller-local close does not establish the documented "all write handles" condition.
- Whether the J1 target has a console under the frozen creation flags. `CONIN$` after redirected standard input is documented where a console input buffer exists. Behavior with no console is not settled.
- Whether `git.exe` or a descendant blocks, reopens stdin, or duplicates a handle the target did not receive.
- Descendant handle containment. Job membership is not a handle-table proof. Out-of-Job descendants remain outside the frozen cleanup claim.
- Whether `CloseHandle` success equals a zero kernel reference count in the presence of other duplicators.
- The inheritance-epoch claim against concurrent creates in the same process.
- The ownership split between controller handle values and inherited instances in the target. The candidate states this split as an assumption requiring host verification.
- Death during create, existing Job nesting, and partial process cleanup. Already OPEN in F5.

## 7. Remaining Human decisions

The direction in section 3 does not decide the items below. They stay open. They are not PASS, implemented, host-validated, frozen, or ratified by this record.

1. Whether a later Human amendment adopts PA-1 through PA-5, adopts a subset, rejects the EOF pipe, or leaves the encoding NON-CLOSED. Section 3 selects a preferred direction. It does not adopt the mapping.
2. The proof standard for "all writer handles closed", given that local inventory is necessary and not sufficient and that external pipe holders stay outside the cleanup claim.
3. Whether controller-local inventory may ever be accepted as encoding evidence. This mapping does not accept it as EOF proof or as launch authority.
4. Whether the J1 target has a console under the frozen creation flags, and what `CONIN$` does when no console input buffer exists.
5. Whether `STARTF_USESTDHANDLES` is the bit to specify, and the separate numeric pin of that bit for the actual build. No numeric value is chosen here.
6. Which documented `ReadFile` outcome occurs, and whether UCRT or MinGit maps it to C end-of-file.
7. What evidence, if any, can prove inheritance-epoch exclusivity and can satisfy the still-unwritten reviewed race policy.
8. Supervisor-to-controller stdin. Out of scope. No inference.
9. ABI pin for handle size, attribute identifiers, and `STARTUPINFOEX`. Still absent.
10. Whether the controller close of `STDIN_READ_INHERIT` after a successful suspended create preserves a target read end.
11. Whether an inherited read handle remains inheritable inside `git.exe`, and whether descendants may hold it.
12. Whether any future fixture module, reason vocabulary, implementation, host test, or operational PIN is authorized. This record authorizes none of them.
13. Fixed reason vocabulary. Labels in the candidate's non-executing test plan remain proposals. They are not frozen by this mapping.

## 8. Batch boundary

This batch creates only docs/inr_her_mingit/INR_HER_MINGIT_EOF_STDIN_PROPOSED_AMENDMENT_MAPPING.md.

It does not stage, commit, push, merge, or modify any other file. It does not read or modify `.wacp/`. It does not edit the EOF candidate, EB-5, H1, EB-14, F5, the F5 acceptance, EB-0, SDK evidence, the fail-closed mock, or any test. It does not implement, compile, execute a process, or ratify a PIN.

EOF behavior is not demonstrated. MinGit stdin compatibility is not demonstrated. Descendant handle containment is not demonstrated. FULL_INR_READY=NO.
