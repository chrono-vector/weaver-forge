# INR-HER MinGit EB-14 Limited Human Design Freeze

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_LIMITED_DESIGN_FREEZE_APPROVED
Decision source: the Human's explicit approval for a limited design freeze of the six EB-14 section 9 design decisions only.

## 1. Exact subject and prerequisite verification

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Verified HEAD before this record: 1107ccf2cc7c1c9a463eb197fdaba2dd801706b2. MATCH.

Accepted EB-14 candidate, not edited by this record:
docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md
Accepted SHA-256: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3
Locally measured SHA-256 before recording: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3
Exact-byte comparison: MATCH.

Accepted Human design decision, not edited by this record:
docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md
Accepted SHA-256: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543
Locally measured SHA-256 before recording: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543
Exact-byte comparison: MATCH.

The Human decision document's section 1 still contains an earlier candidate digest, 23f9abeb73800b6f881dde451e0d025621f35fec4e8b493c24fdc2a7e19d8743, as historical text inside those exact bytes. This freeze does not edit that record and does not treat that earlier digest as the accepted candidate. The accepted candidate bytes are the measured digest above.

EB-5 integrity:
docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md
H1-recorded target SHA-256: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
Locally measured EB-5 SHA-256: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
Working-tree Git blob equals HEAD blob 5e6cd8fba922b58bf3cfc311debbe8253acfb8a6. MATCH. No working-tree modification.

H1 integrity:
docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md
Locally measured H1 SHA-256: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b
Working-tree Git blob equals HEAD blob 8f0be60ecfd55aa14074a0700a6553c517ea5f55. MATCH. No working-tree modification.

Existing Human Finals, including docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md, had no working-tree diff against HEAD at verification. .wacp/ remained pre-existing untracked content and is not altered by this record.

The candidate status line DESIGN_CANDIDATE_NOT_FROZEN and the Human decision line DESIGN_FREEZE: NO remain historical text in those exact bytes. This additive record captures the later, limited Human freeze. It freezes only the six approved section 9 design decisions. It does not freeze unresolved technical implementation details, and it does not replace either document. The file digests identify those documents, not a Git executable, runtime image or operational PIN, and introduce no new digest domain.

## 2. Six approved section 9 decisions under this limited freeze

HUMAN_LIMITED_DESIGN_FREEZE_APPROVED applies to these six decisions and to no other design or implementation claim:

1. J0+J1 with independent Supervisor wall-clock monitoring is the selected future design approach. J1-only and J0-only are not the selected approach. A Job CPU-time limit remains only a backstop and is not a substitute for that independent wall-clock monitor.
2. No privilege increase is approved. No operational run permission is granted. No token change is approved.
3. The cleanup claim is limited to Job-associated processes whose termination is confirmed. Out-of-Job descendants are not guaranteed. Brokered COM, service, WMI, task-scheduler work, unrelated external processes and external pipe holders are outside that claim.
4. Creation-time Job association is required for applicable bootstrap and target paths. There is no assign-after-create fallback. EB-5 closed stdin is preserved. DEVNULL is not selected and is not treated as the same handle state.
5. If target-to-controller handle duplication prevention and ownership cannot be proven, refuse launch. A Job DACL, unnamed handle or non-inheritable flag is not that proof.
6. Independent wall-clock enforcement is required. Numeric limits, evidence freshness and expiry, and host validation remain OPEN.

These remain future design decisions. They are not implementation, host validation, a live run or FULL INR readiness.

## 3. Review disposition carried with this freeze

Grok Bot NF1-NF5 review: ACCEPT. Material findings in that NF1-NF5 review: 0.

NF1 through NF5 remain the nonmaterial records already incorporated in the accepted candidate and Human decision:
- NF1: J0 bootstrap has the same creation-time JOB_LIST obligation and the same direct-API obligations as the controller-to-target hop.
- NF2: a controller that remains alive but stops is outside a controller-internal deadline; independent Supervisor wall-clock monitoring is the selected design approach.
- NF3: the target itself is a potential duplicator of the controller's existing J1 handle. Ownership is unproven unless shown.
- NF4: EB-5 closed stdin and DEVNULL are different candidates. This freeze preserves closed stdin.
- NF5: the re-review did not re-read the external F1-F14 review source, and it is not a cross-provider independent verification.

Cursor final consistency check: eligible.

Review independence limitation: same Grok model family. The recorded re-review is not independent verification across model families or providers. AI agreement, including ACCEPT and the consistency check, is not evidence of OS behavior, host state, execution identity or independent reproduction.

In the accepted candidate, ACCEPT means a literal design candidate may proceed to Human section 9. This freeze is the later Human approval of the six design decisions only. It is not host PASS, implementation authorization or a Human Final. F1 remains the candidate's recorded MATERIAL item, with remediation proposed in the candidate and host behavior still OPEN. This freeze does not close F1-F14 evidence.

## 4. Freeze boundary

This limited freeze applies ONLY to the six approved design decisions in section 2. It does not freeze unresolved technical implementation details. It does not accept an API or ABI specification, prove a principal or DACL, supply host evidence, set numeric limits, ratify an operational MinGit pin, or grant operational authority.

EB-14 bytes are unchanged. The Popen wording inconsistency recorded in the Human decision remains DOCUMENTED_EB14_UNCHANGED. H1's limited freeze and its exclusions remain as recorded in H1. This record does not widen H1 into implementation, execution or ratification.

## 5. Explicitly remaining OPEN

The following stay OPEN. They are not PASS, implemented, host-validated, frozen or ratified by section 2:

- API and ABI specification, including native binding sizes, calling convention, writable command line, environment-block construction, HANDLE_LIST, attribute lifetime and single-owner closure.
- Loader and config closure, including DLL search, IFEO, AppCert/AppInit, .local, SxS, KnownDLLs, ProgramData, TREE_ROOT/etc/gitconfig, prefix-relative lookup, includes and the unresolved inventory roles.
- Windows host qualification, including build, architecture, existing Job hierarchy, nesting and death-during-create behavior.
- Principal and process DACL, including controller process DACL and effective Job security.
- Handle ownership, including PROCESS_DUP_HANDLE, other same-user duplication, debugger, AV/EDR and administrator holders. Section 2 decides the refusal rule when prevention and ownership cannot be proven; it does not prove them.
- Numeric limits for startup, run, cleanup, reader shutdown and output caps. Independent wall-clock enforcement is required; the numbers are not approved. Draft EB-5 figures remain proposals.
- Evidence freshness and expiry, including invalidation, acquirer, provenance and host-validation acceptance. No trusted clock is created here.
- Command-line parser correspondence with the selected MinGit CRT/wmain and release build, and the ASCII/no-space profile choice.
- Concrete deployment paths, alias/reparse qualification, ceiling versus protected-ancestor selection, output grammar and reason vocabulary.
- Operational MinGit pin. OPERATIONAL_MINGIT_PIN=UNRATIFIED. RATIFIED_GIT_SHA256 and RATIFIED_PYTHON_SHA256 are unchanged.
- Real execution and isolation verification. No live run, process execution, Job membership proof, cleanup confirmation or isolation proof is supplied or authorized by this freeze.

## 6. Preserved boundaries

- launch_identity=UNBOUND_AT_LAUNCH. Check-time inspection does not establish execution identity. Missing or unknown controller-owned scope stays identity-required, and required but unproven launch identity refuses before spawn.
- EB0_ENVIRONMENT_COMPATIBLE=NO. EB-0 is not amended.
- OPERATIONAL_MINGIT_PIN=UNRATIFIED.
- FULL_INR_READY=NO.
- No production authority. This freeze establishes no production permission, independent reproduction, independent witness or verified execution identity.
- LIVE_OBSERVATION, exit 0, parsed output, Job membership or cleanup confirmation cannot establish execution identity, safety, isolation, witness, freshness, ratification or production permission.

No implementation, Git-target execution, PIN change, merge, push, pull request, WACP generation or FULL INR declaration is performed or authorized. No existing EB-14 candidate, Human decision, EB-5, H1, Human Final, code or .wacp/ bytes are changed by writing this record.

## 7. Batch boundary

The documentation commit authorized with this record stages only these three added paths:

1. docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md
2. docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md
3. docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md

No other path is staged. .wacp/ remains untracked and excluded.
