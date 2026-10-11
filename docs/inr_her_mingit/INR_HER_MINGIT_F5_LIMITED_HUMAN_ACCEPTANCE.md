# INR-HER MinGit F5 Limited Human Acceptance

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_LIMITED_ACCEPTANCE_APPROVED
Scope: the F5 static call-sequence and refusal contract only
Decision source: the Human explicit approval to record this limited acceptance and to preserve it with one documentation-only commit and a normal push of her/inr-her-mingit-eb0.

This acceptance applies only to docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md. It does not implement that contract, execute it, prove host safety, grant operational authority, bind execution, or declare FULL INR readiness.

## 1. Prerequisite verification

Worktree: C:/dev/_tmp/weaver-gzse-001
Branch: her/inr-her-mingit-eb0
Expected HEAD: c413d7d31cf539f05ca06f8b89da1ed278e9d3e0
Locally verified HEAD before this record: c413d7d31cf539f05ca06f8b89da1ed278e9d3e0
HEAD comparison: MATCH.

Accepted F5 contract, not edited by this record:
docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md
Expected SHA-256: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294
Locally measured SHA-256 before recording: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294
Exact comparison: MATCH.

Tracked worktree before this record: clean. The only untracked paths were the pre-existing .wacp/ tree and the untracked F5 contract above. No tracked path differed from HEAD.

Frozen documents, measured before this record and matching the hashes recorded inside the F5 contract:

- docs/inr_her_mingit/INR_HER_MINGIT_EB14_N2_N6_CONTROLLED_LAUNCH_DESIGN_CANDIDATE.md: 736cf16f7b08b43df808edbf9c728b82170d09fc271b07e5a389351bb3e654b3. MATCH. Working-tree blob equals HEAD blob 65b39aaf4bf4348ab0c55bc108d80132d89a59b7.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_HUMAN_DESIGN_DECISION.md: c2b14838176087bcc10ee5792846f14d0261be82ac1a5adf4d41694c42591543. MATCH. Working-tree blob equals HEAD blob 7b47048534476cadf9064b39d4001b7e4aae6422.
- docs/inr_her_mingit/INR_HER_MINGIT_EB14_LIMITED_HUMAN_DESIGN_FREEZE.md: 61156b5edb2b36589b45502a3f43a16330816dc65deef05d94728b65d891191b. MATCH. Working-tree blob equals HEAD blob 40e44e61c40ad55b7510a962516f5ed36a6dd285.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786. MATCH. Working-tree blob equals HEAD blob 5e6cd8fba922b58bf3cfc311debbe8253acfb8a6.
- docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md: 254e91e4ba63b1722cd8e359a13211596cf41c8b07d5a416bc80b2ab760a453b. MATCH. Working-tree blob equals HEAD blob 8f0be60ecfd55aa14074a0700a6553c517ea5f55.
- docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md: 5621cd7b1cf86bf4bb2b3c385237d23bb95edc99663ebb573d5a9b043bcec6fe. MATCH. Working-tree blob equals HEAD blob efa733c65c10abcae2138c6d1f16bfad0c91dbf3.

.wacp/ remained pre-existing untracked content. Before this record it contained 179 files and the sorted path-and-SHA-256 manifest digest was 9af55d593be7e1f3c6c7de75f7d8133bf9a7a002a067586400ca5037e3a01dfa. This record does not add, edit, stage, or delete any .wacp/ path.

## 2. Content confirmed inside the accepted F5 bytes

The approved NM-1 clarification is present. The contract states that standard Popen is not an acceptable substitute for the creation-time Job binding, and that the contract does not claim that every conceivable Popen use is categorically forbidden. J0-only/Popen remains a historical comparison, not a selected path. That clarification is present in the baseline Popen paragraph, call-sequence step 6, and refusal rule 9. Refusal rule 9 also states that the post-failure prohibition leaves that accepted limit in place.

M1 safety requirements remain present:

- ResumeThread on the retained J1 target primary thread is permitted at most once.
- That one ResumeThread is permitted only after all four conditions hold: required membership and configuration verified from trusted API results, with that verification treated as defense-in-depth and not a replacement for creation-time J1 membership; bounded stdout and stderr readers started; the controller deadline armed, with no numeric deadline set by the contract; and the independent Supervisor wall-clock monitor armed and confirmed ready by the Supervisor itself.
- If any of the four conditions is missing, there is no resume.
- A failed CreateProcessW authorizes no ResumeThread.
- After CreateProcessW failure there is no further execution authorization. The required disposition is TerminateJobObject on J1 where possible, bounded confirmation of process termination and no remaining Job-associated members, single-owner handle closure, and a fixed fail-closed refusal. Unconfirmed cleanup remains non-success.
- After any failure, retry, re-create, relaxed-environment relaunch, Popen fallback, and assign-after-create fallback remain prohibited.

All NON-CLOSED conditions in F5 section 6 remain NON-CLOSED. This acceptance does not freeze them, prove them, or treat them as PASS:

- Numeric SDK constants, ABI types, struct sizes, calling convention, and error mapping.
- Closed-stdin Win32 encoding.
- Environment-block sorting.
- Command-line serialization and MinGit CRT/wmain correspondence.
- Numeric time and output limits.
- Principal, DACL, and handle-ownership proof.
- Windows host qualification and Job nesting.
- Loader and config closure.
- Evidence freshness and expiry.
- Operational MinGit PIN. OPERATIONAL_MINGIT_PIN=UNRATIFIED.
- Real execution binding. EXECUTION_BINDING_REAL remains UNEXECUTED.

The EB-5 environment table remains the existing draft map. This acceptance does not revise it and does not approve TEMP, TMP, or any additional key.

## 3. Limited acceptance

HUMAN_LIMITED_ACCEPTANCE_APPROVED applies only to the static call sequence and mandatory refusal contract in the measured F5 document, including the M1 resume gate and the post-CreateProcessW failure disposition already written there.

Recorded review disposition carried with this acceptance:

- Grok Bot R1: ACCEPT.
- M1: CLOSED inside that static contract.
- Citation repairs: 7/7.
- NM-1 clarification: present, as confirmed in section 2.
- Final accepted F5 SHA-256: aa3c3ebf1f188308367edbd4ebd231f1357c2247efe5de0af4e55428064da294.

Review independence limitation: same model family. The recorded Grok Bot R1 review is not independent verification across model families or providers. AI agreement, including ACCEPT, is not evidence of OS behavior, host state, execution identity, process isolation, or independent reproduction.

This acceptance makes no implementation claim and no runtime safety claim. It supplies no host proof, no operational authority, no execution binding, and no live run. F1 host evidence remains OPEN. The F5 contract sentence that its own repair performed no commit, merge, or push remains historical text inside the accepted F5 bytes. This later additive record is the Human authorization to preserve those unchanged bytes.

FULL_INR_READY=NO.

## 4. Remaining NON-CLOSED technical gates

The technical gates listed in section 2 stay NON-CLOSED after this acceptance. In particular, API/ABI specification, closed-stdin Win32 encoding, environment-block sorting, command-line serialization, numeric limits, principal and handle-ownership proof, Windows host qualification, loader and config closure, evidence freshness and expiry, the operational MinGit PIN, and real execution binding remain open. EB0_ENVIRONMENT_COMPATIBLE=NO. launch_identity=UNBOUND_AT_LAUNCH. LIVE_OBSERVATION, exit 0, parsed output, Job membership, or cleanup confirmation cannot establish execution identity, safety, isolation, witness, freshness, ratification, or production permission.

## 5. Batch boundary

The documentation commit authorized with this record stages only these two paths:

1. docs/inr_her_mingit/INR_HER_MINGIT_F5_CALL_SEQUENCE_AND_REFUSAL_CONTRACT.md
2. docs/inr_her_mingit/INR_HER_MINGIT_F5_LIMITED_HUMAN_ACCEPTANCE.md

No other path is staged. .wacp/ remains untracked and excluded. No frozen document, code, PIN, or .wacp/ bytes are changed. No executable target is run. No merge, pull request, or WACP generation is performed. No force push is used.

MERGED: NO
FULL_INR_READY: NO
