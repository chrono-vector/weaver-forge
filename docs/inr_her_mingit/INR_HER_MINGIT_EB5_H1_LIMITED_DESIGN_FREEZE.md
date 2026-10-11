# INR-HER MinGit EB-5 Human H1 Limited Design Freeze

Record date: 2026-10-11 (Asia/Tokyo)
Status: HUMAN_H1_LIMITED_DESIGN_FREEZE_RECORDED
Decision source: the Human's explicit H1 approval supplied in this conversation.

## 1. Exact design subject and prerequisite verification

Target: docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md
Approved target SHA-256: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
Locally measured target SHA-256 before recording: 42ad74d7951ccb7877eed92edda1d1428409b1f70c944ba7855b1d4893010786
Exact-byte comparison: MATCH.

The existing EB-5 draft is not edited. Its DESIGN_DRAFT_NOT_FROZEN status remains historical text in those exact bytes; this additive record captures the later, limited Human decision. It does not freeze every proposal in that draft. The file digest identifies the design document, not a Git executable, runtime image or operational PIN, and introduces no new digest domain.

## 2. Human-approved limited freeze scope

- E1: an independent profile incompatible with EB-0; no amendment or reinterpretation of EB-0's existing Human Final.
- Exactly three fixed Git observation operations: VERSION ["--version"], EXEC_PATH ["--exec-path"], and CONFIG_SCOPES ["config", "--list", "--show-scope", "-z"]. No additional operation is approved.
- Design principles of absolute execution path, limited PATH, no parent-environment inheritance, controlled cwd, and stdout/stderr through pipes only.
- check-time-only inspection and mandatory launch_identity=UNBOUND_AT_LAUNCH remain in force.

Absolute-path selection and limited environment/cwd are design requirements, not proof of actual process or loader identity. LIVE_OBSERVATION, exit 0, parsed output or a success marker cannot establish execution identity, safety, isolation or ratification.

M1 remains documentarily CLOSED according to the supplied review disposition. Actual execution identity remains unproven. identity_required_scope derives only from a separately approved controller-owned scope; missing or unknown scope is identity-required. Where execution identity is required, UNBOUND_AT_LAUNCH requires refusal before spawn. This record supplies no observational execution exception or run authorization.

## 3. Excluded scope and unresolved requirements

The following remain OPEN, not PASS, implemented, verified, approved for execution or ratified:

- N2: explicit CreateProcess application name, IMAGE double-quote rejection requirement, and unresolved command-line serialization/verification.
- N3: ancestor Git repository-discovery restriction, including any ceiling/protected-ancestor choice.
- N4: Windows loader qualification, including IFEO, AppCertDlls/AppInit_DLLs, .local, SxS, KnownDLLs, DLL-search fall-through and proposed CWD-content restrictions.
- N5: Git for Windows config sources, including ProgramData, TREE_ROOT/etc/gitconfig and prefix-relative lookup/fallback/include behavior.
- N6: approved timeout and descendant-process cleanup as prelaunch conditions; undecided conditions require DEPLOYMENT_OPEN refusal.
- Concrete deployment paths, protected controller policy/scope provenance, exact environment qualification and TEMP/TMP need/fallback.
- Config and loader/DLL/helper/resource dependency closure; the 371 existing unresolved inventory roles are not reclassified by this record.
- Cleanup implementation, output grammar/schema, retention/redaction and status/reason details.
- Operational PINs and ratification, including RATIFIED_GIT_SHA256 and RATIFIED_PYTHON_SHA256.

Reviewer N2 is a finding identifier, not the existing INR N2 freshness scope. Existing INR freshness, witness, accepted implementation and historical verdict boundaries remain unchanged.

No implementation, test execution, Git execution, measurement of distribution members, extraction, installation, real binding evaluation, live run, operational ratification, integration, commit, merge or push is authorized by this limited freeze. It establishes no production permission, independent reproduction, independent witness, verified execution identity or FULL INR PASS. FULL_INR_READY: NO.

## 4. Preservation candidate allowlist

Only these six paths are listed as preservation candidates. This list is not staging, a commit, a Git-tracking assertion or authorization to execute Git:

1. docs/inr_her_mingit/INR_HER_MINGIT_EB1_ROLE_CLASSIFICATION_INVESTIGATION.md
2. docs/inr_her_mingit/INR_HER_MINGIT_EB2_MINIMUM_GIT_SCOPE_STATIC_INVESTIGATION_PLAN.md
3. docs/inr_her_mingit/INR_HER_MINGIT_EB3_GIT_CALLER_PROFILE_DELTA.md
4. docs/inr_her_mingit/INR_HER_MINGIT_EB4_INITIAL_PREFLIGHT_PROFILE_OPTIONS.md
5. docs/inr_her_mingit/INR_HER_MINGIT_EB5_LIMITED_GIT_LAUNCHER_DESIGN.md
6. docs/inr_her_mingit/INR_HER_MINGIT_EB5_H1_LIMITED_DESIGN_FREEZE.md

Everything else is excluded, including .wacp/** and all other untracked files, EB-0, existing Human Finals, implementation code, ZIPs, inventory, PINs and ratification records. No excluded content is deleted, moved or changed. Git tracking/worktree status is not inspected because Git execution is prohibited.

## 5. Next minimum scope

Proposed next scope, requiring separate Human authorization: bounded read-only static qualification of the named N2-N6 requirements, with version-matched retained evidence and an explicit source allowlist, recording confirmed facts versus unresolved conditions in a new documentation-only report. No inventory remeasurement, executable launch, binding evaluation, code edit or ratification is implied. Missing source evidence or an unresolved control remains OPEN; it is not repaired by inferring approval from H1.

This batch adds only this record. Existing EB-0 through EB-5, Human Finals, code, ZIP, inventory, PIN and ratification records remain unchanged.
