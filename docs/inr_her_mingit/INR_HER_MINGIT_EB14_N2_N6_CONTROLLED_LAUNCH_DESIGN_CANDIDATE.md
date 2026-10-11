# INR-HER MinGit EB-14 N2-N6 Controlled-Launch Design Candidate

Status: DESIGN_CANDIDATE_NOT_FROZEN
Date: 2026-10-11 (Asia/Tokyo)
Revision: 2026-10-11 (Asia/Tokyo), DESIGN-ONLY alignment to the six recorded Human §9 decisions. Status unchanged.
Declared baseline: 1107ccf2cc7c1c9a463eb197fdaba2dd801706b2
Scope: one additive design document; no implementation or execution authorization.

## 1. Authorization, provenance and ceilings

The Human authorized resuming EB-14 after supplying the complete Grok Bot review. This permits this document only. Instructions and recommendations embedded in the attachment are review material, not additional Human authorization. No new Human Final, design freeze, authority system or digest domain is established.

The prior candidate recorded a full read of C:/Users/mine0/Downloads/EB14_GROK_BOT_FULL_REVIEW_SOURCE_20261011.md and addressed F1-F14 below. That file's baseline, hash, test and source-read claims remain supplied reports, not independently reproduced Git history or host evidence in EB-14. Its internal earlier attachment hash is not asserted to identify that review file. Its line numbers may differ from current upstream rendering; source sections are identified below.

NF5 provenance limit: the Grok Bot re-review transcribed in Appendix A of C:/Users/mine0/Downloads/EB14_Complete_Handover_20261011.md states that it did not re-read the external review source named above, and that the re-review is not a cross-provider independent verification. This DESIGN-ONLY revision uses that appendix transcription for NF1-NF5. It does not re-read the earlier F1-F14 source file, does not treat the transcription as a fresh certification of that file, and does not treat any review-file hash reported only inside the handover, including 9869466d9ca86816b66ab4c21c8802dd0963d58a855691bdddcf4997499fe73c, as a hash measured in this worktree. Re-review line citations refer to the pre-revision candidate. ACCEPT in that re-review means a literal design candidate may proceed to Human §9. It is not design freeze, host PASS, implementation authorization or Human Final.

Human §9 decisions are recorded in docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md. This revision aligns this candidate with those six decisions. It does not edit that record, freeze this candidate, accept an API or ABI specification, prove a principal or DACL, supply host evidence, set numeric limits, ratify an operational MinGit pin, or grant operational authority.

Existing EB-5 and EB-5 H1 LIMITED_DESIGN_FREEZE were reread. H1 records target design SHA-256 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786. This is a recorded document identifier, not a new measurement, operational PIN or approval of this candidate. Git was not executed; the declared baseline is not a newly verified HEAD claim.

EB-8 and EB-11 through EB-13 chat analyses are background, not verbatim reviewed repository artifacts. This document states the selected future design approach for a subsequent bounded review. It does not certify all prior wording (F14) and it does not freeze the candidate.

Preserved boundaries:
- E1 is independent and EB0_ENVIRONMENT_COMPATIBLE=NO; EB-0 is not amended.
- Existing preflight, H1, Human Finals, code, ZIP, inventory, PIN and ratification remain unchanged.
- launch_identity=UNBOUND_AT_LAUNCH is mandatory. Every path/config/host/image inspection is check-time-only.
- Missing or unknown controller-owned scope is identity-required; required but unproven launch identity refuses before spawn. No observational execution exception is authorized here.
- LIVE_OBSERVATION, exit 0, valid output, Job membership, cleanup or AI agreement cannot establish execution identity, safety, isolation, witness, freshness, ratification, Human Final or production permission.
- FULL_INR_READY=NO. No independent reproduction is claimed.
- OPERATIONAL_MINGIT_PIN=UNRATIFIED.
- N2-N6 remain OPEN implementation/deployment gates. Proposed labels and outcomes are not accepted output schemas.

## 2. F1 MATERIAL correction and method comparison

F1 is MATERIAL: suspended creation followed by AssignProcessToJobObject leaves a controller-death interval with a created process not associated with the intended cleanup Job. Direct CreateProcessW alone does not repair it. A PID registry/watchdog alone cannot cover death before the creating call returns its PID.

Target membership rule, inside every candidate that uses J1: creation-time J1 membership using PROC_THREAD_ATTRIBUTE_JOB_LIST. Build and configure an unnamed per-operation Job J1 before CreateProcessW; include J1 in the creation attribute list. No permitted branch creates the target first and assigns J1 later. Unsupported JOB_LIST, incompatible nesting, attribute/configuration failure or unavailable required evidence refuses without a fallback create call. This rule is not by itself a selection of J1-only lifecycle management.

Microsoft documents JOB_LIST on Windows 10 / Server 2016 and newer (S1). That source-level capability is not proof of support, membership or cleanup on the selected host. The intended invariant is creation-time membership or refusal, including controller death while CreateProcessW is in progress. The failure/partial-creation behavior and death-at-boundary cases require later host evidence; they are not assumed verified.

Comparison candidate: Supervisor-held J0, with one controller per operation. A separately trusted Supervisor prepares J0 with KILL_ON_JOB_CLOSE and no breakaway, and starts the controller with creation-time J0 association. The controller's target inherits J0 under qualified host rules. J0 does not solve F1 if the controller itself is first created unassociated and only later assigned. Supervisor death during bootstrap must not leave an unassociated controller: creation-time association or separately proven pre-existing management is required.

NF1: J0 bootstrap is the same creation-time obligation, not a lesser path. Under the selected J0+J1 design, the Supervisor must place the controller in J0 at CreateProcessW time through PROC_THREAD_ATTRIBUTE_JOB_LIST, or refuse. Assign-after-create and fallback create do not satisfy it. The historical comparison "J0 alone with standard Popen" is not a selected path and does not satisfy creation-time Job binding. That comparison covers only a controller-to-target hop and does not remove the direct-API surface. The Supervisor therefore carries the same F5 obligations as the controller: direct CreateProcessW, ABI, writable command line, environment block, HANDLE_LIST, attribute lifetime and single-owner handle closure. The design requires that creation-time binding. Its API and ABI specification remains unwritten, and implementation is not authorized here.

| Candidate | Intended death and stall management | Cost and unresolved boundary |
|---|---|---|
| JOB_LIST J1, comparison | Controller death closes its non-inherited J1 handle; last-handle rule applies. A live-but-stalled controller is not covered, because the wall-clock deadline lives inside that controller | Direct API binding, host compatibility, handle-holder protection and creation-failure behavior OPEN |
| Supervisor J0, comparison | Supervisor detects controller death and terminates J0; Supervisor death relies on last-handle close. Bootstrap still needs creation-time association | Additional trusted Supervisor, F5 direct-API obligations on the Supervisor, protected monitoring, one-operation controller, nested/host rules OPEN |
| J0 plus JOB_LIST J1, selected future design approach | Outer independent Supervisor wall-clock monitor plus per-operation creation-time membership. Supervisor terminates on its own deadline if the controller stays alive but stops | Additional ABI, hierarchy and ownership complexity. Human §9 has selected this approach. API/ABI specification, principal and DACL proof, and host evidence remain OPEN. Not a Design Freeze |

No method is runtime PASS. J0 plus creation-time J1, with an independent Supervisor wall-clock monitor, is the selected future design approach because a J1-only deadline does not cover NF2. J1-only and J0-only are not the selected approach. It is not an automatic fallback and not a Design Freeze. J0 alone with standard Popen is a historical comparison: it neither guarantees creation-time controller membership nor discharges F5 (NF1), and it is not a selected path. Independent wall-clock enforcement is required. If that monitor cannot be guaranteed, refuse before spawn. A Job CPU-time limit is only a backstop, not a wall-clock substitute. Numeric limits remain OPEN.

F1 disposition: the unsafe assign-after-create path is excluded in this literal candidate. DESIGN_REMEDIATION_PROPOSED. Human §9 has selected J0+J1 with creation-time association. Implementation and host validation remain OPEN. This document does not self-declare verified material closure.

## 3. N2: API and exact-input contract

Only code-owned operations are selectable:
- VERSION: [IMAGE, "--version"].
- EXEC_PATH: [IMAGE, "--exec-path"].
- CONFIG_SCOPES: [IMAGE, "config", "--list", "--show-scope", "-z"].

IMAGE remains TREE_ROOT/ucrt64/bin/git.exe, never cmd/git.exe or name lookup. IMAGE, cwd, environment and limits derive from separately approved controller policy, not request data or child output. Ordinary absolute drive paths only; reject relative/drive-relative, UNC/device/extended paths, traversal, ambiguous trailing dots/spaces, NUL/control characters and IMAGE double quotes under EB-5 rules. Concrete paths and alias/reparse qualification remain OPEN.

Primary API candidate: direct CreateProcessW with lpApplicationName=IMAGE, writable command-line storage, absolute cwd, explicit Unicode environment, STARTUPINFOEX and EXTENDED_STARTUPINFO_PRESENT | CREATE_SUSPENDED | CREATE_UNICODE_ENVIRONMENT. No shell, parent-process override, debugger option, caller creation flags or CREATE_BREAKAWAY_FROM_JOB. Actual ABI constants, sizes, calling convention and error handling require a dedicated implementation-gate specification and remain OPEN. Under the selected J0+J1 design, creation-time Job binding is mandatory for the applicable Supervisor bootstrap path and the controller-to-target path (NF1). There is no assign-after-create fallback. Standard Popen is not an acceptable substitute for that binding. This does not claim that every conceivable Popen use is categorically forbidden. J0-only/Popen remains a historical comparison, not a selected path.

Command-line construction follows CPython v3.11.9 list2cmdline semantics as the proposed serialization algorithm, with IMAGE also argv[0]. No hand-added outer quoting or caller raw command line. Matching the selected MinGit CRT/wmain parser and release build remains OPEN. Human may restrict TREE_ROOT to ASCII without spaces as an interim lexical profile restriction; this reduces cases but does not prove parser/build correspondence. Spaces/non-ASCII are not silently accepted or newly forbidden by H1; the adopted profile choice needs explicit approval (F4).

Environment validation occurs before any API call: a controller-created immutable snapshot of exact str keys/values, no custom mapping or str subclass behavior, no NUL, no empty/invalid key, no case-insensitive duplicates, no unapproved keys. Reject duplicates instead of allowing CPython normalization to choose a value (F2). Build evidence from the same validated snapshot, not an earlier caller map. Direct-API environment block must be sorted according to the reviewed Windows rules, UTF-16 encoded, double-NUL terminated and lifetime-stable; surrogate/encoding and size conditions require explicit tests, not coercion.

CPython v3.11.9 _winapi.c getenvironment checks the function name normalize_environment rather than its returned normalized_environment (S2). Exact input validation does not remove allocation failures or prove the runtime cannot crash (F3). Primary direct-API block construction avoids relying on that helper, but introduces new ABI/runtime failure paths. The historical J0-only/Popen comparison retains this helper issue; it is not a selected path. The selected direct-API path still requires fail-closed startup and abnormal-termination management; no runtime patch, version change or ratification is authorized.

NF4: Human §9 preserves EB-5 closed stdin. DEVNULL is not selected and is not treated as the same handle state, the same inheritance behavior or a silent replacement of the EB-5 wording. stdout/stderr are separate binary pipes only, never console, inherited ambient handles, combined output or implicit text decoding. Child inheritance is the preserved EB-5 closed stdin together with stdout/stderr write handles. S1 requires inheritable listed handles and bInheritHandles=TRUE when HANDLE_LIST is used. Job handles, parent read ends and unrelated handles must not be in HANDLE_LIST.

Attribute-list memory and backing handle arrays must live until safe destruction. Primary thread/process handles are retained explicitly through membership checks/resume/exit confirmation. Every pipe, attribute allocation, Job and process/thread handle has a single documented owner and closure point. Concurrent process creation and temporarily inheritable handles require a reviewed race policy. Standard Popen exposes no JOB_LIST path in v3.11.9 _winapi and closes the primary thread handle, so it is not an acceptable substitute for the required creation-time Job binding. Private subclass/monkeypatch/runtime hooks are not an accepted substitute for that binding (S2, S3). This does not claim that every conceivable Popen use is categorically forbidden.

## 4. N3 plus N5: one repository/config boundary

Controller selects a non-repository cwd and approved ancestor boundary. Screen cwd for .git directories, gitfiles and bare repository structure, not merely a path label. Candidate ceiling is one immediate-parent absolute path, with no empty entry; protected-ancestor alternative requires separate selection. Windows tag PATH_SEP is ';' (S7); documentation's generic colon example must not replace it. Ceiling does not suppress cwd detection or explicit GIT_DIR. Canonicalization/reparse semantics and concrete ACLs remain OPEN.

Adding GIT_CEILING_DIRECTORIES requires an explicit E1 profile revision; it is not silently added to H1 or EB-5's environment table. Exact environment retains the EB-5 candidate PATH=IMAGE_PARENT, GIT_NO_REPLACE_OBJECTS=1, GIT_TERMINAL_PROMPT=0, GIT_OPTIONAL_LOCKS=0, GIT_CONFIG_NOSYSTEM=1, GIT_CONFIG_GLOBAL=EMPTY_GLOBAL_CONFIG, controlled HOME/USERPROFILE/XDG_CONFIG_HOME and approved SystemRoot/WINDIR. TEMP/TMP stay absent unless separately revised and qualified. This is not EB-0-compatible.

Forbid GIT_DIR/WORK_TREE/COMMON_DIR, discovery overrides, GIT_EXEC_PATH, GIT_CONFIG, GIT_CONFIG_SYSTEM, COUNT/KEY_*/VALUE_*, PARAMETERS, GIT_ASKPASS, GIT_SSH*, PAGER/GIT_PAGER/LESS and any unlisted override. Fixed argv excludes -C, -c, --git-dir, --work-tree, --file and scope-changing additions.

EMPTY_GLOBAL_CONFIG must be an approved protected empty regular file with qualified resolution; no include/includeIf directives or unapproved reference target. NOSYSTEM suppresses the ordinary system-read sequence, and explicit GLOBAL replaces normal HOME/XDG candidates in tagged source (S8). Local/worktree absence depends on discovery suppression. Prefix/TREE_ROOT/etc/gitconfig/ProgramData behavior in the actual build remains unproven. An empty output does not prove that these routes were suppressed.

Missing source/build qualification, file protection or ancestor evidence, unapproved config reference or ambiguous resolution refuses before spawn. Unexpected output after launch is an observation refusal, not proof the unwanted read was prevented. Three suffixes remain unchanged; controlled config observations are not equivalent to accepted ambient repository-root preflight.

## 5. N4: loader, host and evidence acceptance

Required evidence categories, currently OPEN:
- Build: selected IMAGE to official release/build mapping, compiler/CRT/startup flags, manifests, direct/delay/dynamic DLL, helper, script and resource reach. Prior four DLL candidates are a lower bound; the 371 unresolved inventory roles remain unresolved.
- Host: exact Windows build/architecture, existing Job hierarchy/security constraints, loader redirection, SxS, KnownDLLs, IFEO, AppInit/AppCert applicability, DLL-search fall-through and controller/Python runtime dependencies. No assumption that suspended creation proves no loader/host activity has occurred.
- Deployment: concrete image/cwd/ancestor/home/config/runtime locations, ACL/reparse resolution, principal model, handle duplication/debugger/AV/EDR access and protection of controller policy/monitor/evidence records.

An absolute image and restricted PATH do not close dependent DLL lookup (S9). A missing route or unexplained resource is a pre-spawn refusal, not an assumed harmless item. Build/static evidence cannot establish current host state or launch-time loaded-byte identity.

Proposed evidence acceptance record requires: approved acquirer outside caller/target control, explicit collection method, source/version, target host/build/paths/principals, collection event, protected provenance/integrity, known limitations, approval context, expiry policy and invalidation triggers. Existing manifests/digests are not re-ratified here. Acquisition itself requires later explicit authorization.

Expiry is not inferred from a timestamp supplied by the target. Human must select an independently grounded recency rule or same-session acquisition rule with acknowledged time limitations; no trusted clock is created. Missing rule, expired evidence or unknown validity refuses. Host update/reboot where relevant, config/loader/ACL/runtime change, Job-chain change, principal/EDR/debugger change or evidence-protection loss invalidates applicable evidence until requalified. Exact periods and monitoring are OPEN, not a promise that all changes can be detected.

Trust boundary excludes unproven hostile administrator/kernel/host override resistance. If the requested scope needs resistance not supplied by evidence, refuse rather than redefine the scope. No host evidence can silently change UNBOUND_AT_LAUNCH. Identity-required scope remains blocked.

## 6. N6: lifecycle, death cases and refusal

Before create: validate authorized scope, fixed request/map/argv, all deployment gates, JOB_LIST support, existing Job compatibility and handle-owner assumptions; prepare J1, restrictive reviewed security descriptor, non-inheritable Job handle, KILL_ON_JOB_CLOSE, neither BREAKAWAY_OK nor SILENT_BREAKAWAY_OK. SetInformation/attribute/pipe preparation failure means no create. A capability probe requiring target execution is not authorized by this design.

Create: JOB_LIST [J1] and exact HANDLE_LIST, suspended, retained process/thread handles. No assign-after-create fallback, relaxed environment retry or invocation of accepted preflight. Unsupported/incompatible create fails closed. Creation failure must not be treated as successful isolation: absence/cleanup of any partially created process requires a qualified API/host contract and negative evidence.

Before resume: verify required membership/configuration using trusted API results, start bounded readers and deadline management, and confirm controller/monitor readiness. Verification is defense-in-depth; it is not a replacement for creation-time membership. Any failure leaves no resume and enters bounded cleanup. Do not claim creation/membership verification binds executable bytes.

Run: monotonic wall-clock deadline, concurrent bounded stdout/stderr reads and bounded transient storage; do not use uncapped communicate. Draft EB-5 numbers (10 s, stdout 65536 bytes, stderr 16384 bytes) remain proposals. Numeric limits for startup, run, cleanup and reader shutdown, including a controller-blocked-in-create case, remain OPEN. A controller-internal deadline cannot survive controller death, and it also does not run while the controller is deadlocked, blocked in a reader or deadline thread, or suspended. The selected future design approach is an independent Supervisor wall-clock monitor over J0 plus J1 (NF2). Independent wall-clock enforcement is required. J1-only and J0-only are not the selected approach. Handle-close and that external monitor have separate prerequisites, and host validation remains OPEN. A Job CPU-time limit does not replace wall-clock monitoring.

Finish or refuse: stop admitting output on cap breach, timeout, cancel, API/read/parser error or abnormal controller termination; terminate J1 where possible and confirm process signalling and no remaining associated members within a separately bounded cleanup interval. Do not equate successful TerminateJobObject return, root exit or one ActiveProcesses query with all descendants cleaned. Reader completion/cancellation is bounded independently of EOF. Never silently truncate and accept.

| Failure/death | Required design disposition and unresolved condition |
|---|---|
| Controller dies before target creation | No target intended; prepared handles close. No success output; record absence only from a separately trusted monitor, if present |
| Controller dies during create or before resume | Creation-time J1 association plus last-handle closure is intended management. Actual create/death ordering, partial failures and handle-holder conditions require host tests; no inference from missing result |
| Controller dies after resume | Same J1 close prerequisite. Without trusted completion evidence result is unavailable/UNCONFIRMED, not PASS |
| Controller remains alive but stalled (NF2) | Deadlock, a blocked reader, a blocked deadline thread or suspension can leave the controller holding J1. KILL_ON_JOB_CLOSE then does not fire, and a resumed child is not bounded by the controller-internal deadline. Selected approach: independent Supervisor wall-clock monitoring of J0 plus J1, with the Supervisor terminating on its deadline. Independent wall-clock enforcement is required. If that monitor cannot be guaranteed, refuse before spawn. A Job CPU-time limit is only a backstop. Host validation of this row remains OPEN |
| Job handle copied by the target or another holder (NF3) | Last-handle guarantee unavailable. The target itself is a potential holder: with launch_identity=UNBOUND_AT_LAUNCH, a same-user substituted image may open the controller with PROCESS_DUP_HANDLE and duplicate the controller's existing J1 handle. A Job DACL does not by itself prevent that duplication. If target-to-controller handle duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof. No uniqueness assertion from non-inheritable flags or a Job DACL alone |
| Existing Job/nesting incompatible or unknown | Refuse before target create when determinable; create failure remains refusal. Never break away or relax limits to make it work |
| Membership/configuration/resume failure | No further execution authorization; bounded cleanup and fixed refusal reason, not successful-control evidence |
| Timeout/cap/pipe failure | Terminate associated Job members; bounded confirmation and reader shutdown; failure or incomplete confirmation remains non-success |
| Supervisor J0 comparison: controller dies | Supervisor terminates J0 and confirms under its approved deadline; one controller per operation prevents shared-operation ambiguity |
| Supervisor J0 comparison: Supervisor dies | Last J0 handle close is intended fail-safe, subject to no extra holders; missing evidence cannot be reconstructed as success |

The selected J0+J1 design must not give the controller or the target an inherited J0 handle. Intended J1 ownership is the controller alone. That ownership is unproven (NF3). The target itself is a potential duplicator of the controller's existing J1 handle, including through PROCESS_DUP_HANDLE while running as the same user. Unnamed and non-inheritable handles, and a restrictive Job DACL, reduce some exposure. They do not establish sole ownership against the target, other same-user duplication, privileged tools or administrator override, and a Job DACL does not prevent duplication of a handle the controller already holds. Human §9 records the refusal rule: if target-to-controller handle duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof. Principal and DACL proof, and host evidence of outstanding holders, remain OPEN. No privilege increase is approved. No operational run permission is granted. No token change is approved.

The managed cleanup claim, as recorded in Human §9, is limited to Job-associated processes whose termination is confirmed. Out-of-Job descendants are not guaranteed. Brokered COM, service, WMI, task-scheduler work, unrelated external processes and external pipe holders are outside that claim. This is the recorded bounded claim, not a silent weakening of H1's cleanup requirement and not proof that those outside categories are contained. EOF is never the sole deadline/completion criterion.

## 7. Complete F1-F14 disposition matrix

Every row is a response proposal, not a claim of implemented closure. A = pre-implementation design obligation; B = Human decision; C = host/build evidence; D = explicit deferred/nonclaim boundary.

| Finding / supplied classification | Response and invariant | Human decision | Required real evidence / remaining OPEN |
|---|---|---|---|
| F1 MATERIAL (A+B) | JOB_LIST membership at creation for the target; exclude post-create assignment and fallback. J0 bootstrap has the same creation-time rule (NF1). J0+J1 with independent Supervisor wall-clock monitoring is the selected future design approach. J1-only and J0-only are not selected | Recorded: J0+J1 with independent Supervisor wall-clock monitoring. Bounded cleanup scope is the §9 associated-member claim. Not a Design Freeze | Windows support, hierarchy, death during create, partial failure, final-handle behavior; MATERIAL remediation proposed, not verified CLOSED |
| F2 NONMATERIAL (A) | Reject case duplicates and non-exact types before API; evidence from same validated snapshot | Approve exact map/validation contract | Production negative tests incl PATH/Path, encoding, mutation; no reliance on silent dedup |
| F3 NONMATERIAL (A) | Record v3.11.9 null-check defect; validation is insufficient for OOM; main route avoids helper, all routes manage abnormal termination | Accept runtime risk boundaries or choose separately reviewed alternative; no runtime change here | Allocation/crash cases, controller death and monitor behavior; runtime authenticity OPEN |
| F4 OPEN (B+C) | list2cmdline-compatible candidate only; no claimed MinGit parser/build match | ASCII/no-space restriction or broader tested path class | Exact CRT/build provenance and actual argv receipt cases; restriction alone not closure |
| F5 NONMATERIAL (A) | Dedicated direct-API ABI/lifetime/handle/environment specification gate. NF1: the same gate applies to Supervisor J0 bootstrap and the controller-to-target hop under the selected J0+J1 design | Creation-time Job binding is required for applicable bootstrap and target paths. API and ABI specification remains OPEN. Not implementation approval | Native binding sizes/calling convention, writable buffers, HANDLE_LIST, Unicode block, resource-failure/race tests. Spec still unwritten |
| F6 OPEN (C+D) | Claim only confirmed associated Job members; bound readers without EOF; no brokered containment claim | Recorded: cleanup is limited to Job-associated processes whose termination is confirmed. Out-of-Job descendants are not guaranteed. Brokered COM, service, WMI, task-scheduler work, unrelated external processes and external pipe holders are outside that claim | Permitted launch routes, external pipe holders and brokered process relevance remain host-evidence items. The nonclaim is decided, and those categories stay outside the claim |
| F7 OPEN (C) | Unnamed non-inherited Job handle; restrictive Job security; no assumed holder uniqueness. NF3: the target itself is a potential J1-handle duplicator. Job DACL alone is not sufficient | Recorded refusal rule: if target-to-controller handle duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof. No token change. Principal and DACL model remains OPEN | PROCESS_DUP_HANDLE, debugger/EDR/admin access, effective process and Job DACLs, outstanding holders; hostile host resistance unproven |
| F8 NONMATERIAL (A) | Monotonic timeout, hard concurrent byte caps, Job termination plus bounded confirmation. NF2: an internal deadline does not cover a controller that stays alive but stops | Independent wall-clock enforcement is required. Numeric limits for startup, run, cleanup, reader shutdown and output caps remain OPEN. A Job CPU-time limit is only a backstop | Cap floods, pipe stall, live-controller stall, cancellation and cleanup failure tests; no uncapped communicate, root-only kill or CPU-time substitute for wall-clock |
| F9 NONMATERIAL (B+C) | No own breakaway flags or CREATE_BREAKAWAY_FROM_JOB; incompatible nesting refuses | Approve supported Job hierarchy/platform | Existing host chain/UI/security constraints and effective membership; no name-only capability claim |
| F10 NONMATERIAL/OPEN (B+C) | One nonempty ceiling candidate plus cwd/gitfile/bare screening; explicit profile revision | Ceiling or protected ancestors, concrete boundary | Windows ';', canonical/reparse/ancestor behavior, ACLs; ceiling never covers explicit GIT_DIR/cwd by itself |
| F11 NONMATERIAL/OPEN (C) | Existing NOSYSTEM/GLOBAL rows retained; prohibit injection/includes through qualified source closure | Approve config resource/protection acceptance criteria | Selected-build ProgramData/prefix/tree paths, empty-file protection; empty output not PASS |
| F12 NONMATERIAL/OPEN (C+D) | Evidence acquirer/target/method/validity/invalidation required; missing route refuses | Approve recency/expiry/trust boundary; mandatory gates cannot be deferred for a live run | Loader/build/host evidence and monitoring; UNBOUND_AT_LAUNCH unchanged |
| F13 NONMATERIAL (B) | Ordinary Job and Supervisor elements are the selected future J0+J1 design approach only as unprivileged design elements; no privilege or token implementation and no frozen wording edit | Recorded: no privilege increase, no operational run permission, no token change. Design selection is not deployment permission | Required API rights and host policy remain OPEN. Design permission is not deployment permission |
| F14 NONMATERIAL (B) | This literal document contains the integrated design candidate and source limits. NF5: the later re-review did not re-read the external F1-F14 source file | Human §9 design decisions are recorded. This is not design freeze, host PASS or implementation authorization. No H3 inferred | Prior chat not verbatim reconstructed; unread review source not treated as reconfirmed; review of this actual document before implementation authorization |

NF1-NF5 are nonmaterial records from that re-review. Human §9 has selected the J0+J1 future design approach. That selection does not freeze this candidate and does not close F1-F14 host evidence.

| Added record | Disposition kept OPEN or limited |
|---|---|
| NF1, A+B, related to F1/F5 | J0 bootstrap requires creation-time JOB_LIST association and the same F5 direct-API and handle obligations. Standard Popen is not an acceptable substitute for that binding. J0-only/Popen is a historical comparison, not a selected path. This does not claim that every conceivable Popen use is categorically forbidden. Not an implementation approval. API and ABI specification remains OPEN |
| NF2, B | Failure table includes controller alive but stalled. Selected approach is independent Supervisor wall-clock monitoring with J0+J1. Independent wall-clock enforcement is required. If that monitor cannot be guaranteed, refuse before spawn. CPU-time limit is only a backstop. Numeric limits and host validation remain OPEN |
| NF3, C+B, related to F7 | Target itself is a potential J1 handle duplicator via PROCESS_DUP_HANDLE. If prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof. Principal and DACL proof remains OPEN. No token change |
| NF4, B | EB-5 closed stdin is preserved. DEVNULL is not selected and is not the same handle state |
| NF5, D | Re-review source limit is recorded in §1. The unread external review file is not marked confirmed |

## 8. Prospective negative-test and acceptance specification

No tests are run here. Mock/unit tests may establish control flow only; later separately authorized host tests are required for OS behavior. Wrong-reason failure is not a successful isolation test: each case must identify the exercised boundary, creation/resume count, membership/cleanup evidence and expected fixed non-success disposition, without raw untrusted output reflection.

- F1/F9: unsupported JOB_LIST and configuration failure produce no target create; membership failure produces no resume; inject controller death at pre-create/in-create/post-create/pre-resume/run boundaries; incompatible existing Job and breakaway attempts remain non-success. A death-test that cannot establish process absence/termination is UNCONFIRMED, not a killed mutation.
- F2/F3/F5: duplicate-case keys, NUL/non-str/custom mappings, encoding/allocation failure, attribute-list lifetime and wrong handle list; controller crash must not leave an unassociated runnable target. No deliberate invocation of a known crash path is authorized now.
- F4: approved path classes, spaces/non-ASCII/trailing-backslash serialization, IMAGE quote/relative/NUL rejection and argv mismatch; actual receiving tokens required to qualify parser match later.
- F6/F7/F8: leaked Job handle prevents assuming last-close cleanup; a same-user target that duplicates the controller J1 handle is an outstanding-holder case, not proof of sole ownership (NF3); external pipe holder never permits indefinite wait; stdout/stderr floods independently exceed hard caps; timeout, controller-alive stall (NF2) and root-exit-with-live-members; termination/query/reader failure remains non-success. A Job CPU-time limit is not a passing substitute for an independent wall-clock monitor.
- F10/F11: cwd .git/gitfile/bare, ancestor repository, malformed/empty ceiling, reparse escape, injected GIT_DIR/config parameters, include/includeIf, nonempty/replaced config, inaccessible system-route evidence. Pre-spawn refusal must be distinguished from post-spawn detection.
- F12: missing/expired/wrong-target evidence, changed loader/ACL/Job/runtime configuration and unknown validity refuse; equal pre/post digest never asserts execution identity.
- All: caller tries to select API, environment, Job handles, scope exception, approval or PASS; reject. Exit 0 and syntactically valid three-operation output do not elevate evidence or authority.

Output grammar/schema, operation-specific version/exec-path expectations, CONFIG_SCOPES exact NUL parsing, approved limits and constant reason vocabulary remain OPEN before implementation. No persistent authoritative receipt or new source of truth is created. Raw child config/exception data must not be reflected or persisted; use bounded transient inspection only under a later approved policy.

## 9. Human decisions and next minimum scope

The six Human §9 design decisions are already recorded in docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md. This section repeats them and does not replace that record. They are future design decisions. They are not implementation, host validation, a live run, a Design Freeze or FULL INR readiness.

1. J0+J1 with independent Supervisor wall-clock monitoring is the selected future design approach. J1-only and J0-only are not the selected approach. A Job CPU-time limit remains only a backstop and is not a substitute for that independent wall-clock monitor.
2. No privilege increase is approved. No operational run permission is granted. No token change is approved.
3. The cleanup claim is limited to Job-associated processes whose termination is confirmed. Out-of-Job descendants are not guaranteed. Brokered COM, service, WMI, task-scheduler work, unrelated external processes and external pipe holders are outside that claim.
4. Creation-time Job association is required for applicable bootstrap and target paths. There is no assign-after-create fallback. EB-5 closed stdin is preserved. DEVNULL is not selected and is not treated as the same handle state.
5. If target-to-controller handle duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof.
6. Independent wall-clock enforcement is required. Numeric limits, evidence freshness and expiry, and host validation remain OPEN.

Creation-time Job binding is mandatory for applicable paths under that selected J0+J1 design. Standard Popen is not an acceptable substitute for that binding. This candidate does not claim that every conceivable Popen use is categorically forbidden. J0-only/Popen remains a historical comparison, not a selected path. No assumption that EB-8 Popen supports JOB_LIST.

The following technical prerequisites remain OPEN. They are not PASS, implemented, host-validated, frozen or ratified by the six decisions:

- API and ABI specification, including native binding sizes, calling convention, writable command line, environment-block construction, HANDLE_LIST, attribute lifetime and single-owner closure.
- Loader and config closure, including DLL search, IFEO, AppCert/AppInit, .local, SxS, KnownDLLs, ProgramData, TREE_ROOT/etc/gitconfig, prefix-relative lookup, includes and the unresolved inventory roles.
- Windows host qualification, including build, architecture, existing Job hierarchy, nesting and death-during-create behavior.
- Principal and DACL model, including controller process DACL and effective Job security.
- Handle ownership, including PROCESS_DUP_HANDLE, other same-user duplication, debugger, AV/EDR and administrator holders. Decision 5 is the refusal rule when prevention and ownership cannot be proven; it does not prove them.
- Numeric limits for startup, run, cleanup, reader shutdown and output caps. Independent wall-clock enforcement is required; the numbers are not approved. Draft EB-5 figures remain proposals.
- Evidence freshness, expiry, invalidation, acquirer, provenance and host-validation acceptance. No trusted clock is created here.
- Command-line parser correspondence with the selected MinGit CRT/wmain and release build, and the ASCII/no-space profile choice.
- Concrete deployment paths, alias/reparse qualification, ceiling versus protected-ancestor selection, output grammar and reason vocabulary.
- Operational MinGit pin. OPERATIONAL_MINGIT_PIN=UNRATIFIED. RATIFIED_GIT_SHA256 and RATIFIED_PYTHON_SHA256 are unchanged.

Section 5 of this candidate, N4 loader, host and evidence acceptance, stays OPEN on build, host and deployment evidence. Bootstrap death, host compatibility and the unwritten F5 specification on the selected J0 hop remain OPEN (NF1).

Next minimum scope: the six decisions above are recorded. This revision does not freeze the candidate and does not authorize implementation. A later bounded read-only review of this literal candidate may check F1 creation-time membership, J0 bootstrap F5 obligations, the live-but-stalled row, target handle duplication, closed-stdin preservation, the NF5 unread-source limit, all F2-F14 obligations and H1 nonclaims. AI agreement is not evidence of OS behavior or independent reproduction. Any subsequent static evidence collection, host tests, implementation, execution, Design Freeze or ratification requires separate authorization.

No existing H1 or Human Final bytes are changed. This note does not supersede a CLOSED scope, revise accepted preflight semantics or authorize a live observational run. Deployment, build linkage, loader closure, runtime authenticity, operational PINs and ratification remain OPEN. DESIGN_CANDIDATE_NOT_FROZEN. launch_identity=UNBOUND_AT_LAUNCH. EB0_ENVIRONMENT_COMPATIBLE=NO. OPERATIONAL_MINGIT_PIN=UNRATIFIED. FULL_INR_READY=NO.

## 10. Official reference index and evidence classification

SOURCE_CONFIRMED here means a documentary/API/source fact only. It is not BUILD_LINK_CONFIRMED or HOST_CONFIRMED. Sources read or carried as prior bounded official analysis are distinguished below.

- S1 (reread): Microsoft UpdateProcThreadAttribute, HANDLE_LIST requirements, JOB_LIST Windows support and attribute backing-value lifetime: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute
- S2 (reread): CPython v3.11.9 Modules/_winapi.c, normalize_environment/getenvironment defect and getattributelist handle_list-only path: https://github.com/python/cpython/blob/v3.11.9/Modules/_winapi.c
- S3 (EB-13 source basis): CPython v3.11.9 Lib/subprocess.py, Windows _execute_child primary-thread close, uncapped reader and direct-process terminate: https://github.com/python/cpython/blob/v3.11.9/Lib/subprocess.py
- S4 (reread): Microsoft Job Objects, ordinary inheritance, breakaway/nested conditions and associated-process termination: https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects
- S5 (reread): Microsoft JOBOBJECT_BASIC_LIMIT_INFORMATION, last-handle KILL_ON_JOB_CLOSE and CPU-time limits: https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information
- S6 (reread): Microsoft AssignProcessToJobObject, rights and existing/nested Job restrictions: https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject
- S7 (EB-12 source basis): Git for Windows v2.56.0.windows.2 compat/mingw.h PATH_SEP and setup.c discovery: https://github.com/git-for-windows/git/blob/v2.56.0.windows.2/compat/mingw.h and https://github.com/git-for-windows/git/blob/v2.56.0.windows.2/setup.c
- S8 (EB-12 source basis): same tag config.c system/global/local/worktree sequence and Git 2.56.0 config injection/include specification: https://github.com/git-for-windows/git/blob/v2.56.0.windows.2/config.c and https://git-scm.com/docs/git-config/2.56.0
- S9 (reread): Microsoft Dynamic-link library search order, dependent DLL/name and host-dependent search factors: https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order

Microsoft pages describe supported APIs across Windows versions, not the measured deployment host. Git tag/source and CPython source do not authenticate selected local executables. No ZIP extraction, binary remeasurement, host query or Git-history verification was performed in this batch.
