# INR-HER MinGit EB-2 Minimum Git Scope and Static Investigation Plan

Status: DOCUMENTATION_ONLY_PROPOSAL_NOT_FROZEN
Date: 2026-10-11 (Asia/Tokyo)

## Scope and authority

EB-2 organizes existing requirements and proposes bounded future static investigations. It does not perform those investigations, execute Git, measure files, evaluate execution binding, ratify a pin, or establish a new execution profile.
Only this new report is created. Existing ZIP, inventory, EB-0/EB-1 reports, Human Finals, Design Freeze, PINs, distribution digest and implementation remain unchanged.
BASELINE_VERIFIED and ZIP_SIZE_AND_SHA256_VERIFIED remain accepted prior results, not repeated checks.

## Sources read

- docs/inr_her_mingit/INR_HER_MINGIT_EB0_HUMAN_FINAL.md: fixture-only acceptance, no real tree binding or operational pin.
- docs/inr_her_mingit/execution_binding_v0.py: existing manifest/dependency/path/environment conditions; no invocation.
- docs/inr_her_mingit/INR_HER_MINGIT_EB1_ROLE_CLASSIFICATION_INVESTIGATION.md: inventory-derived classification and bounded static observations.
- docs/inr_her_002a/INR_HER_001_PHASE2A_CLOSURE_CONTRACT.md: bounded claim, preflight, pin requirements and freshness nonclaims.
- docs/inr_her_002a/preflight_her_v1.py: read only the existing Git observation commands and launcher environment context.
- docs/inr_her_n2/INR_HER_N2_DESIGN_FREEZE_V0.md: responsibility separation only; concrete authorities and implementation remain undecided.

EB-1's 373-member inventory and static import observations are reused as reported investigation evidence. EB-2 does not remeasure or revalidate them. Its 371 unresolved classifications are not changed.

## Candidate and minimum target

Selected candidate: ucrt64/bin/git.exe.
cmd/git.exe is a shim and is not an execution target.

Initial static inspection set proposed for the next approved investigation:

1. ucrt64/bin/git.exe
2. ucrt64/bin/libiconv-2.dll
3. ucrt64/bin/libintl-8.dll
4. ucrt64/bin/libpcre2-8-0.dll
5. ucrt64/bin/zlib1.dll

EB-1 records direct normal-import requests for the four DLL names from the selected image and a libintl-8.dll -> libiconv-2.dll edge. Unique packaged basenames are not proof of Windows loader resolution.
All four remain UNRESOLVED dependency candidates; the remaining 367 files also remain UNRESOLVED. No file becomes other merely because it is absent from these imports.

## Git operations: established versus OPEN

| Item | Existing basis | Status and limit |
|---|---|---|
| Read Git version | Phase 2A collector uses git --version | Existing preflight observation, not authorized execution in EB-2 |
| Read Git exec-path | Collector uses git --exec-path | Existing preflight observation; actual helper reach is unproven |
| Read config scopes | Collector uses git config --list --show-scope -z; retained observations discard config values | Existing preflight observation; includes/ambient scope behavior still needs closure analysis |
| Selected binary invocation | EB-2 user selects ucrt64/bin/git.exe; EB-0 rejects selecting the cmd shim | Candidate only; accepted collector still invokes git by name, not a newly bound absolute path |
| INR full operation inventory | The specified sources do not enumerate all INR Git invocations and inputs | OPEN; the three preflight observations are not a complete INR operation profile |
| Local object/ref/tree lookup and historical comparisons | Possible next profile category, not established by these sources | OPEN; no specific command or argv is approved by this report |
| Archive/export or tree construction | Possible separate operation category | OPEN; not silently included |
| Network, clone/fetch/push, credential/SSH/HTTP helpers | No necessity established for this bounded scope | OPEN; excluded from the proposed next static-only scope, not proved globally unnecessary |
| Writes, hooks, filters, pager/editor, shell/helper dispatch | No exact allowed profile established | OPEN; no execution approval |

The minimum executable INR Git profile cannot be frozen from the materials read. It requires a separate explicitly authorized source-only call-site audit of named INR caller files, with each command's literal argv, bounded variable inputs, cwd, repository, read/write effects and environment recorded. EB-2 does not conduct that audit or infer the list from general Git knowledge.

## Configuration and environment conditions

Established EB-0 supplied-data constraints:

- Complete manifest and observed path/digest sets must agree.
- Dependency list must exactly equal the manifest dependency-role set and remain inside the declared tree.
- Candidate path must be inside the tree and select a non-shim execution_image.
- PATH must contain only the candidate parent directory.
- The only GIT_* item admitted in supplied environment data is GIT_NO_REPLACE_OBJECTS=1.
- source is BOUND_TREE or MINGIT_PINNED and reparse_escape is False; these are labels/claims, not live verification.
- Claims of execution/operational-pin authorization, freshness or PASS do not supply authority.
- UNRESOLVED is a research state, not an EB-0 role. A fully usable operational manifest has not been established.

Additional conditions still OPEN:

- Absolute execution tree/root and staging procedure; executable selection through all actual callers.
- Full allowlisted environment, including HOME/USERPROFILE, loader controls and config/credential/certificate influences; PATH alone is insufficient.
- System, global, local, worktree, command-line and included config scope policy; allowed keys/values and read sources.
- Working directory, repository/object/ref inputs, replace refs, alternates, templates, hooks, filters, pager/editor and subprocess routes.
- git exec-path policy, helper roots, script interpreters and direct/helper-mediated transports.
- Windows image/version/architecture, API-set resolution, forwarders, SxS/KnownDLL behavior and search-path assumptions.
- Proposed observation/output retention policy, avoiding credentials and unrelated user configuration.

The accepted Phase 2A launcher inherits os.environ and adds GIT_TERMINAL_PROMPT=0 and GIT_OPTIONAL_LOCKS=0. EB-0's supplied-data rule allows neither additional GIT_* flag. This is not resolved by deleting flags or modifying accepted code: the mapping between existing preflight and a future execution-binding profile is OPEN and requires a separately approved integration decision.
The existing launcher uses git by name with its existing cwd. Merely selecting ucrt64/bin/git.exe in a report does not bind that process or change its PATH resolution.

## Investigation plan

All following investigations are proposals, not performed here. Every approval is separate from approval of EB-2 documentation. Each step records exact source/member, method, observation, limitation and retained inventory identity without rehashing or inventing provenance.

### S1: Confirm and qualify the five-file native import graph

Target: the selected image and four DLL candidates only.
Evidence needed: exact PE normal/delay descriptor offsets and names, optional-header/section interpretation, relevant export-forwarder and dynamic-loader call-site evidence; compare EB-1 observations using a documented independent parser/method if already available without installation.
OPEN conditions: malformed/unsupported structures, delayed or computed loads, parser disagreement, and absence of an authenticated loader-resolution rule. Static paths remain hypotheses.
Stop conditions: evidence requires execution, extraction, installation, new measurements, modified bytes, or files outside the approved five-member set. Record unresolved edges rather than guessing.
Human approval: authorize nonexecuting in-memory member-content inspection and recording offsets/relationships for exactly these five members; no remeasurement or classifier invocation.

### S2: Qualify host/API-set and forwarded dependency boundaries

Target: names already reported by EB-1 (ADVAPI32, KERNEL32, USER32, WS2_32, ntdll and listed api-ms-win-crt names); initially use existing retained documentation, not a host filesystem census.
Evidence needed: approved target Windows image identity and retained loader/API-set/forwarder mapping applicable to that image; declare which host surfaces are inside T and which require explicit protection.
OPEN conditions: no target image chosen, image-specific mappings absent, dynamic resolution and host runtime identity unproved.
Stop conditions: need current host DLL reads/hashes, registry interrogation, privileged access or runtime tracing. Those require another scope and may involve remeasurement.
Human approval: name the target image and exact existing documentation/metadata permitted for reading. No operational approval follows from a documentation mapping.

### S3: Operation-specific Git helper and script reach

Target: an approved bounded Git command profile and only helper/script paths connected by concrete call-site/config evidence.
Candidate distribution groups from EB-1: ucrt64/libexec/git-core/*, ucrt64/bin Git helper/transport/credential programs, usr/bin/sh.exe, ssh/helper and related script resources. These groups are discovery candidates, not approved blanket reads or established dependencies.
Evidence needed: named INR caller files with literal argv/cwd/environment, matching Git version source/package build correspondence when already available, helper dispatch and script shebang/content edges; include conditional branches and executable search paths.
OPEN conditions: command inventory not frozen, source-to-binary correspondence missing, computed dispatch, configurable filters/hooks/credentials or interpreter selection.
Stop conditions: branch requires another member, unapproved source, network retrieval, test execution or a command outside the proposed profile. Request named targeted expansion.
Human approval: first authorize source-only audit of named INR caller files; then approve the resulting precise helper/script member list. Do not use filename similarity as reach proof.

### S4: Git configuration, transport, certificates and crypto resources

Target: exact config/resource paths justified by S3. Candidate groups: etc/gitconfig and include chains; ucrt64/etc/ssl/*; ucrt64/lib/engines-3/* and ucrt64/lib/ossl-modules/*; usr/ssl/*; SSH config; credential-manager configuration/managed components.
Evidence needed: content-derived key/include/resource references, operation-specific transport reach, compile-time defaults supported by version-matched source evidence, environment overrides and packaged resource consumers.
OPEN conditions: all transport requirements, ambient config, certificate/backend selection, OpenSSL provider/engine loads, credential helper and managed runtime reach.
Stop conditions: secret-bearing external config, remote access, credential use, certificate validation runs, out-of-scope filesystem reads or unbounded includes. Retain UNRESOLVED.
Human approval: approve named nonsecret config/resource reads and justified consumers; authorize any later transport/credential scope separately. A CA filename alone is not proof it is used or sufficient.

### S5: Dynamic and transitive edge resolution

Target: only newly evidenced members from S1-S4 after explicit targeted expansion.
Evidence needed: concrete import/forwarder/call-site/config/script references, how conditions resolve under the proposed profile, ambiguous basename/search locations and cyclic edges.
OPEN conditions: computed LoadLibrary/GetProcAddress or process invocation; managed assembly loading; locale/catalog/environment-dependent resources; unknown conditional reach.
Stop conditions: expansion cannot be enumerated or resolved statically, available tooling cannot interpret the member, or proof needs live tracing. Do not extrapolate negative reach from string absence.
Human approval: list the additional members and analysis method before reading them. If dynamic observation is ultimately necessary, propose a new controlled-execution scope; none is authorized now.

### S6: Evidence-qualified classification reconciliation

Target: existing 371 unresolved rows; annotations in a new report only.
Evidence needed: each dependency proposal cites positive reach and unresolved loader assumptions; each other proposal cites profile-specific exclusion evidence covering configurable/dynamic routes; retain original paths/digests as copied evidence.
OPEN conditions: any unresolved operation, consumer, host edge or exclusion assumption. A partial graph is not a dependency closure proof.
Stop conditions: reconciliation would drop members, replace inventory values, assign other solely by name/extension, or treat an inferred graph as a live binding.
Human approval: authorize a new classification proposal document with referenced evidence. Operational manifest adoption, binding evaluation and pin ratification require separate approval.

## OPEN decision register

- O1: Full minimal INR operation/argv inventory and allowed variable inputs.
- O2: Exact tree root, cwd, repository/objects/refs and process/executable selection.
- O3: Configuration scope/key/include policy and complete environment allowlist.
- O4: EB-0 environment constraints versus accepted preflight environment integration.
- O5: Allowed helpers, scripts, interpreters, filters/hooks, transports and credential behavior.
- O6: Target Windows image, loader/API-set/host runtime boundary and actual four-DLL resolution.
- O7: Dynamic/managed/plugin/locale/config/certificate reach and negative-exclusion evidence.
- O8: Trusted operational manifest adoption and provenance; caller-supplied matching data are not trusted tree evidence.
- O9: Distribution artifact versus extracted runtime pin target/domain and separate Human ratification procedure.
- O10: N2 issuer, verifier/trust anchor, nonce holder/state, trusted clock/expiry, key lifecycle, external environment and schema/implementation.
- O11: Any live binding/execution/measurement protocol and required explicit authorization.

None of these is made decided by this report. No existing specification is amended.

## Next executable scope and approval request

The next currently feasible action is documentation-only operation-profile discovery, not running Git:
Human should name the specific accepted INR Git caller files authorized for a source-only call-site audit and approve recording argv, bounded inputs, cwd, effects, config and environment in a new report. If the caller paths are not already known, approve a bounded path-discovery scope explicitly; do not authorize a repository-wide audit by implication.
After that profile is reviewed, separately authorize S1's five-member static evidence qualification. It can proceed without launching Git, remeasuring bytes or claiming closure.
Any S2-S5 expansion is conditional and requires its own exact target list. S6 cannot turn remaining unknowns into dependency/other by default.

## Nonclaims and preserved state

New file only; no existing document, code, ZIP, inventory, Human Final, PIN or digest changed.
No Git command or executable, binding evaluator, ratification, measurement, commit, merge, push, install, download, credential operation or privileged observation occurred.
No new static ZIP/PE inspection occurred in EB-2.
Dependency closure: UNPROVEN.
371 member classifications: UNRESOLVED (four documented dependency hypotheses only).
Execution binding real: UNEXECUTED.
Operational MinGit pin: UNRATIFIED.
Python 3.11.9 pin: PIN_PENDING.
Windows isolation: UNVERIFIED.
N2 external binding: UNEXECUTED.
Freshness: UNPROVEN.
Independent Witness: NOT_CLAIMED.
FULL_INR_READY: NO.

