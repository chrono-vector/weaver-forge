# INR-HER MinGit EB-4 Initial Preflight Profile Options

Status: DOCUMENTATION_ONLY_OPTIONS_AND_RECOMMENDATION_NOT_APPROVED_PROFILE
Date: 2026-10-11 (Asia/Tokyo)

## Scope

This new report compares three future profile directions using EB-0 through EB-3 and the Phase 2A contract. It neither changes those records nor authorizes implementation, execution, binding evaluation, pin ratification or a new authority.
Initial candidate: ucrt64/bin/git.exe. cmd/git.exe is excluded as an intended execution target.
No live PATH, parent environment, Git process, ZIP bytes or inventory was measured or inspected anew.

## Source basis

- docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md: fixture-only acceptance and explicit nonclaims.
- docs/inr_her_mingit/INR_HER_MINGIT_EB1_ROLE_CLASSIFICATION_INVESTIGATION.md: 371 UNRESOLVED members and four static dependency hypotheses; closure unproven.
- docs/inr_her_mingit/INR_HER_MINGIT_EB2_MINIMUM_GIT_SCOPE_STATIC_INVESTIGATION_PLAN.md: operation/config/environment OPEN register and static investigation plans.
- docs/inr_her_mingit/INR_HER_MINGIT_EB3_GIT_CALLER_PROFILE_DELTA.md: exact three caller operations and line-numbered source observations.
- docs/inr_her_002a/INR_HER_001_PHASE2A_CLOSURE_CONTRACT.md:73-98: existing preflight responsibilities and authenticated pin procedure.

Source facts below reuse EB-3 observations. They are not measurements of a running Git instance or independent reproduction.

## Initial verification profile candidate

The only included operation candidates are:

1. ["git", "--version"] (preflight_her_v1.py:193, common launcher :463).
2. ["git", "--exec-path"] (:194, common launcher :463).
3. ["git", "config", "--list", "--show-scope", "-z"] (:195, common launcher :463).

All references in this section are to docs/inr_her_002a/preflight_her_v1.py.
These three are source-confirmed preflight observations, not the finalized minimum operation list for the full INR workflow. No clone, fetch, push, archive, object/ref mutation, hook/helper or transport operation is added.
The config query can read configured sources and capture values before scope parsing discards them (:173-184, :475). It is not a claim of zero sensitive reads or config closure.

Future profile dimensions still requiring explicit decisions:

- Fixed candidate image and exact absolute tree root.
- Exact cwd and repository/config context.
- Operation allowlist with fixed argv and explicit bounds; nonlisted invocations rejected.
- Full process environment, config-source/include/key policy and data-retention rules.
- Dependency/resource reach and host-loader boundary.
- Failure, timeout and non-PASS evidence handling.

This candidate does not authorize a run, claim dependency closure, or promote any prior predicate.

## Existing behavior versus EB-0 conditions

| Dimension | Accepted preflight source behavior | EB-0 supplied-data condition | Consequence |
|---|---|---|---|
| Image selection | shutil.which("git") at :192; launches ["git", *args] at :463, not the discovery path | Absolute candidate_path inside tree_root; non-shim execution_image | No current process identity binding; absolute candidate data are not a launcher |
| cwd | ROOT from __file__.resolve().parents[2] at :25; cwd=ROOT at :464 | No cwd field in the EB-0 input condition | cwd/config-context compatibility remains OPEN; do not invent an EB-0 cwd guarantee |
| PATH | Inherited os.environ at :469 | PATH contains only candidate parent (execution_binding_v0.py:233-244) | Existing invocation is not shown to satisfy this |
| Parent environment | Complete inheritance plus two explicit overrides at :469 | Requires string key/value input map; narrowly restricts GIT_* and PATH | EB-0 does not prove a full environment closure or live environment equality |
| GIT_TERMINAL_PROMPT | Explicit "0" | Additional GIT_* key is not accepted | Cannot silently erase it from an evidence representation |
| GIT_OPTIONAL_LOCKS | Explicit "0" | Additional GIT_* key is not accepted | Cannot silently erase it or claim the flag proves no writes |
| GIT_NO_REPLACE_OBJECTS | May be inherited, not explicitly set | Exactly "1" and the sole GIT_* entry (execution_binding_v0.py:230-232) | Presence/value not established |
| Other GIT_* | Inherited unless one of the two overrides | Rejected by supplied-data rule | Config/exec-path/other ambient influences remain open |
| Result | Git/config/pin checks remain non-PASS | Even matching fixture yields TREE_MATCH_UNPINNED and BLOCKED | Neither path supplies isolation, freshness or operational pin approval |

EB-0 references identify docs/inr_her_mingit/execution_binding_v0.py; preflight references identify docs/inr_her_002a/preflight_her_v1.py.
The EB-0 Human Final accepts plain-data fixture decisions. It does not mandate that accepted preflight be retrofitted or supply an executable absolute-path launcher.

## Option A: preserve existing preflight; investigate a separate profile

Change size: zero accepted-code changes. A new descriptive investigation profile would document the inherited-environment, name-resolution behavior exactly.

Verification potential:
- Best for preserving the accepted observation contract and documenting what currently occurs.
- A future authorized observation could investigate the selected environment, but source description alone cannot bind the binary or exclude ambient influences.
- A profile allowing inherited values may remain difficult to bound; its evidence must stay distinct from EB-0.

Human Final impact:
- Existing acceptance and limitations remain unchanged.
- A new profile does not expand existing approval or redefine EB-0.
- A comparison result cannot be relabeled TREE_MATCH_UNPINNED, authenticated execution or isolation merely because the profiles coexist.

OPEN:
Actual image, full inherited environment, config sources, resource/loader reach, separate profile schema/evaluator and mapping to INR.
Human approval needed:
A separately bounded observation/static investigation scope with named inputs and output limits. Any real Git execution requires explicit approval beyond this report.

Assessment:
Smallest immediate change, but does not resolve the intended bounded-candidate execution question. Acceptable as descriptive baseline preservation, not sufficient as a future execution-binding profile.

## Option B: adapt accepted preflight to EB-0 conditions in a future scope

Change size: direct changes to accepted invocation/environment behavior. Fewer new launcher artifacts than C may be possible, but smaller line count is not smaller semantic impact.

Verification potential:
- Absolute image and limited PATH could improve reproducibility.
- Full environment/config/loader closure would still need design and evidence.
- Removing GIT_TERMINAL_PROMPT/GIT_OPTIONAL_LOCKS to satisfy the existing rule changes behavior. Neither safe prompting nor no-write behavior can be assumed after removal.
- Keeping those flags would remain outside current EB-0 input conditions; modifying EB-0 itself would require another separately authorized amendment.

Human Final impact:
- Historical accepted bytes and verdicts must remain identifiable.
- Existing Human Final does not automatically accept the changed preflight or a changed EB-0 contract.
- Requires explicit authorization for accepted-source evolution, review and a new acceptance decision for the new candidate; does not rewrite historical approval.

OPEN:
Compatibility, exact env/config policy, prompt/write-control substitutes, caller migration, error semantics, dependency closure and test plan.
Human approval needed:
Before any implementation, approve the behavior change and its precise owned files; independently review the new candidate and separately decide acceptance.

Assessment:
Not preferred for this stage. It couples unresolved integration decisions to accepted code and makes preservation more difficult.

## Option C: design a new limited launcher in a separate scope

Change size: no accepted preflight or EB-0 changes. New design first; possible additive implementation only after distinct authorization. More new artifacts than A, but isolates behavioral change from accepted code.

Verification potential:
- A design could specify a fixed absolute image, exactly three fixed argv, exact cwd, bounded outputs/timeouts and a complete explicit environment/config policy.
- A future implementation must reject arbitrary executable/argv/environment overrides and evidence representations that omit effective variables.
- Static and synthetic tests could check launcher policy, but must not establish actual loader identity, privileged isolation, freshness or FULL INR PASS.
- Any EB-0-compatible profile must actually satisfy its existing input conditions. If the chosen process policy needs the two additional GIT_* flags, identify it as a distinct profile, not an EB-0 match. An EB-0 amendment is not part of C by implication.

Human Final impact:
- Existing preflight, EB-0 and all accepted records remain unchanged.
- A new launcher is not automatically admitted into INR and cannot borrow existing Human Final approval.
- Production integration, invoking the launcher, operational pin adoption and any new acceptance each require separate decisions.

OPEN:
Exact root/cwd; required environment including Windows essentials; config/include containment; prompt/write-control policy; distinction between process data and fixture representation; caller/output integration; dependency/loader/resource closure.
Human approval needed:
Approve a DESIGN-ONLY limited-launcher scope for these three operations and explicitly preserve existing sources. Approving design is not approving implementation, execution or pin ratification.

Assessment:
Best future direction for isolating the new verification surface while preserving accepted semantics. This is a proposed design scope, not a new implemented subsystem.

## Comparative summary

| Criterion | A | B | C |
|---|---|---|---|
| Immediate accepted-code edits | None | Required in future | None |
| New artifact burden | Lowest descriptive burden | Changed implementation/contract tests | Additive design, later code/tests if approved |
| Historical Human Final preservation | Strong | Must separate changed candidate from history | Strong |
| Candidate-path/environment verification potential | Limited by ambient behavior | Potentially improved; compatibility changes | Potentially most explicit and separately testable |
| EB-0 mismatch resolved automatically | No | No | No |
| Dependency/loader/config closure established | No | No | No |
| Execution or operational pin approved | No | No | No |

## Recommendation (proposal only)

Recommend C for the next design direction, while leaving the accepted preflight untouched.
Reason: it separates bounded-candidate verification from inherited ambient observation without modifying accepted bytes or reinterpreting fixture-only EB-0 acceptance. This does not mean C is the smallest artifact count; A is smaller but does not resolve bounded execution selection, and B changes accepted behavior.
Do not implement or invoke a launcher from this recommendation. Do not treat the user's authorization to write EB-4 as approval of C.

## Required next minimum Human decision

Approve or reject a separate DESIGN-ONLY scope for C, limited to the three operation candidates. Its deliverable should define:
- fixed image/root/cwd and argv;
- complete environment/config policy and output retention;
- a resolved proposal for the two flags versus EB-0, without changing accepted contracts implicitly;
- failure/timeout/input controls and synthetic-test expectations;
- exact exclusions and unresolved dependency/loader/resource assumptions;
- later approval gates for implementation, integration, live observation and operational pin adoption.

Until approved, these remain OPEN. If compatibility cannot be designed under existing EB-0 conditions, explicitly present a distinct-profile proposal or request a separately bounded amendment; never silently widen EB-0.
The broader INR operation inventory and N2 issuer/verifier/nonce-holder/clock remain OPEN and outside this three-operation profile.

## Preserved state and nonclaims

Only this new report is saved.
No existing document/code/PIN/digest/inventory/ZIP/Human Final was changed.
No Git execution, collector invocation, test run, binding evaluation, measurement, ratification, commit, merge, push, install or download occurred.
371 file classifications remain UNRESOLVED, including four static dependency hypotheses.
Execution binding: UNEXECUTED.
Operational MinGit pin: UNRATIFIED.
Freshness and dependency closure: UNPROVEN.
Windows isolation: UNVERIFIED.
Independent Witness: NOT_CLAIMED.
FULL_INR_READY: NO.

