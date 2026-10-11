# INR-HER MinGit EB-14 Human Design Decision

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_EB14_SECTION9_DESIGN_DECISIONS_RECORDED
Decision source: the Human's explicit approval for EB-14 §9 design decisions only.
DESIGN_FREEZE: NO

## 1. Exact subject and prerequisite verification

Worktree: the verified worktree whose HEAD is 1107ccf2cc7c1c9a463eb197fdaba2dd801706b2.
Branch name recorded by that worktree listing: her/inr-her-mingit-eb0.
Verified HEAD: 1107ccf2cc7c1c9a463eb197fdaba2dd801706b2. MATCH.

Subject candidate, not edited by this record:
docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md
Expected EB-14 SHA-256: 23f9abeb73800b6f881dde451e0d025621f35fec4e8b493c24fdc2a7e19d8743
Locally measured EB-14 SHA-256 before recording: 23f9abeb73800b6f881dde451e0d025621f35fec4e8b493c24fdc2a7e19d8743
Exact-byte comparison: MATCH.

EB-5 integrity:
docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md
H1-recorded target SHA-256: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
Locally measured EB-5 SHA-256: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
Working-tree Git blob equals HEAD blob 5e6cd8fba922b58bf3cfc311debbe8253acfb8a6. MATCH. No working-tree modification.

H1 integrity:
docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md
Locally measured H1 SHA-256: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b
Working-tree Git blob equals HEAD blob 8f0be60ecfd55aa14074a0700a6553c517ea5f55. MATCH. No working-tree modification.

Existing Human Finals, including docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md, had no working-tree diff against HEAD at verification. .wacp/ remained pre-existing untracked content and is not altered by this record. EB-14 itself remained the pre-existing untracked candidate identified above.

This file is an additive Human decision record. It does not edit EB-14, EB-5, H1, Human Finals, code, ZIP, inventory, PIN or ratification bytes. The EB-14 digest identifies that design-candidate document, not a Git executable, runtime image or operational PIN.

## 2. Six explicitly approved §9 decisions

These are future design decisions for the EB-14 candidate. They are not implementation, host validation, a live run, a Design Freeze or FULL INR readiness.

1. J0+J1 with independent Supervisor wall-clock monitoring is the selected future design approach. J1-only and J0-only are not the selected approach. A Job CPU-time limit remains only a backstop and is not a substitute for that independent wall-clock monitor.
2. No privilege increase is approved. No operational run permission is granted. No token change is approved.
3. The cleanup claim is limited to Job-associated processes whose termination is confirmed. Out-of-Job descendants are not guaranteed. Brokered COM, service, WMI, task-scheduler work, unrelated external processes and external pipe holders are outside that claim.
4. Creation-time Job association is required for applicable bootstrap and target paths. There is no assign-after-create fallback. EB-5 closed stdin is preserved. DEVNULL is not selected and is not treated as the same handle state.
5. If target-to-controller handle duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof.
6. Independent wall-clock enforcement is required. Numeric limits, evidence freshness and expiry, and host validation remain OPEN.

## 3. Grok Bot review disposition carried with this decision

The EB-14 candidate records the Grok Bot re-review disposition ACCEPT. In that record, ACCEPT means a literal design candidate may proceed to Human §9. It is not design freeze, host PASS, implementation authorization or a Human Final.

NF1 through NF5 are incorporated in the candidate that this decision reads:
- NF1: J0 bootstrap has the same creation-time JOB_LIST obligation and the same direct-API obligations as the controller-to-target hop.
- NF2: a controller that remains alive but stops is outside a controller-internal deadline; independent Supervisor wall-clock monitoring is the relevant recommendation, now selected as a design approach under section 2.
- NF3: the target itself is a potential duplicator of the controller's existing J1 handle. Ownership is unproven unless shown.
- NF4: EB-5 closed stdin and DEVNULL are different candidates. This decision preserves closed stdin.
- NF5: the re-review did not re-read the external F1-F14 review source, and it is not a cross-provider independent verification.

Zero new MATERIAL findings are introduced by this Human record. F1 remains the candidate's recorded MATERIAL item, with remediation proposed in the candidate and host behavior still OPEN. NF1-NF5 stay nonmaterial records. This decision does not close F1-F14 evidence.

Same-model-family independence limitation: the recorded re-review is not independent verification across model families or providers. AI agreement, including ACCEPT, is not evidence of OS behavior, host state, execution identity or independent reproduction.

## 4. Popen wording inconsistency, left in EB-14

EB-14 is not modified. The following two sentences remain in the candidate and do not say the same thing:

- Line 61: "Standard Popen remains an unacceptable substitute on either hop."
- Line 67: "J0/Popen alternative retains this issue."

Line 61 is broader than the decision in section 2. Line 67 still names a J0/Popen alternative while discussing the CPython v3.11.9 environment-helper defect. Those sentences are inconsistent with each other.

The selected J0+J1 design requires the specified creation-time Job binding for applicable bootstrap and target paths, with no assign-after-create fallback. Standard Popen is not adopted as that binding. This record does not claim that every conceivable Popen usage is forbidden. Aligning the two EB-14 sentences would require editing a second file, so that edit is not made. Popen consistency status: DOCUMENTED_EB14_UNCHANGED.

## 5. Explicitly remaining OPEN

The following stay OPEN. They are not PASS, implemented, host-validated, frozen or ratified by section 2:

- API and ABI specification, including native binding sizes, calling convention, writable command line, environment-block construction, HANDLE_LIST, attribute lifetime and single-owner closure.
- Loader and config closure, including DLL search, IFEO, AppCert/AppInit, .local, SxS, KnownDLLs, ProgramData, TREE_ROOT/etc/gitconfig, prefix-relative lookup, includes and the unresolved inventory roles.
- Windows host qualification, including build, architecture, existing Job hierarchy, nesting and death-during-create behavior.
- Principal and DACL model, including controller process DACL and effective Job security.
- Handle ownership, including PROCESS_DUP_HANDLE, other same-user duplication, debugger, AV/EDR and administrator holders. Section 2 decides the refusal rule when prevention and ownership cannot be proven; it does not prove them.
- Numeric limits for startup, run, cleanup, reader shutdown and output caps. Independent wall-clock enforcement is required; the numbers are not approved. Draft EB-5 figures remain proposals.
- Evidence freshness, expiry, invalidation, acquirer, provenance and host-validation acceptance. No trusted clock is created here.
- Command-line parser correspondence with the selected MinGit CRT/wmain and release build, and the ASCII/no-space profile choice.
- Concrete deployment paths, alias/reparse qualification, ceiling versus protected-ancestor selection, output grammar and reason vocabulary.
- Operational MinGit pin. It remains UNRATIFIED. RATIFIED_GIT_SHA256 and RATIFIED_PYTHON_SHA256 are unchanged.

## 6. Preserved boundaries

- EB-14 status remains DESIGN_CANDIDATE_NOT_FROZEN. This record does not freeze that candidate and does not replace its bytes.
- launch_identity remains UNBOUND_AT_LAUNCH. Check-time inspection does not establish execution identity. Missing or unknown controller-owned scope stays identity-required, and required but unproven launch identity refuses before spawn.
- EB0_ENVIRONMENT_COMPATIBLE remains NO. EB-0 is not amended.
- The operational MinGit pin remains UNRATIFIED.
- FULL_INR_READY remains NO.
- H1's limited freeze and its exclusions remain as recorded in H1. This decision does not widen H1 into implementation, execution or ratification.
- LIVE_OBSERVATION, exit 0, parsed output, Job membership or cleanup confirmation cannot establish execution identity, safety, isolation, witness, freshness, ratification or production permission.

## 7. Batch boundary

This batch adds only docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md.

No implementation, process execution, PIN change, Design Freeze, commit, merge, push or WACP generation is performed or authorized. No existing EB-14, EB-5, H1, Human Final or .wacp/ bytes are changed.
