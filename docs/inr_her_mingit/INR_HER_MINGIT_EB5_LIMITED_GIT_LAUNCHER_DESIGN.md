# INR-HER MinGit EB-5 Three-Operation Limited Git Launcher Design

Status: DESIGN_DRAFT_NOT_FROZEN
Date: 2026-10-11 (Asia/Tokyo)
Design direction: EB-4 option C, additive limited launcher, existing preflight unchanged.
Revision: M1 ceiling remediation; Human H1 decision preparation. EB-4 option C remains unchanged.

## 1. Authorization and scope

The Human authorized EB-5 DESIGN-ONLY work and one new document. This authorizes preparing this draft, not acceptance/freeze of its contents, implementation, Git execution, binding evaluation, measurement, extraction, installation, operational pin ratification, integration or production permission.
All existing implementations, contracts, Human Finals, PINs, digest records, inventory and ZIP remain unchanged.
The design covers three initial observation operations only, not all INR Git requirements.

M1 boundary: launch_identity=UNBOUND_AT_LAUNCH is a code-owned mandatory ceiling, not caller-selectable. Every path/image/DLL/ancestor/config/policy inspection is check-time-only. No check result binds the bytes actually launched or loaded. Absolute-path selection, matching pre/post checks, LIVE_OBSERVATION, exit 0, valid output and any success marker cannot establish execution identity, safety, isolation or ratification.
identity_required_scope is derived only from a separately approved controller-owned scope, never a caller request, child output or self-declared flag. Missing, unknown or ambiguous scope is treated as identity-required. If that scope requires execution identity, this unproven condition blocks execution authorization and spawning: return BLOCKED / LAUNCH_IDENTITY_REQUIRED_UNPROVEN before spawn. Approval of this design or a check-time inspection cannot waive that requirement or change the ceiling. A separately approved observational scope that explicitly does not require identity is not authorized here and must not be described as a bound Git execution.

Source basis:
- INR_HER_MINGIT_EB0_HUMAN_FINAL.md: fixture-only acceptance.
- INR_HER_MINGIT_EB1_ROLE_CLASSIFICATION_INVESTIGATION.md: static dependency hypotheses and 371 unresolved roles.
- INR_HER_MINGIT_EB2_MINIMUM_GIT_SCOPE_STATIC_INVESTIGATION_PLAN.md: investigation plan and OPEN register.
- INR_HER_MINGIT_EB3_GIT_CALLER_PROFILE_DELTA.md: precise preflight source observations.
- INR_HER_MINGIT_EB4_INITIAL_PREFLIGHT_PROFILE_OPTIONS.md: A/B/C comparison and recommendation.
These five files are under docs/inr_her_mingit/.
- docs/inr_her_002a/INR_HER_001_PHASE2A_CLOSURE_CONTRACT.md: bounded preflight, pin and freshness limits.
- docs/inr_her_n2/INR_HER_N2_DESIGN_FREEZE_V0.md: responsibility separation, not concrete authority or implementation approval.

No new binary analysis, inventory measurement or current-process environment observation occurs in EB-5. Existing evidence is reused without claiming independent reproduction.

## 2. Contract identity and initial profile

Proposed profile label: HER_LIMITED_PREFLIGHT_DISTINCT_V0.
The label is descriptive, not an authority, evidence promotion or new digest domain.
Proposed policy choice: a distinct process-observation profile; do not represent it as EB-0-compatible.

Caller request can select only one of these code-owned operation identifiers:

| operation_id | Fixed argv suffix | Existing source basis |
|---|---|---|
| VERSION | ["--version"] | docs/inr_her_002a/preflight_her_v1.py:193 |
| EXEC_PATH | ["--exec-path"] | same file :194 |
| CONFIG_SCOPES | ["config", "--list", "--show-scope", "-z"] | same file :195 |

Actual proposed argv is [approved_absolute_image, *fixed_suffix], never ["git", *suffix].
No caller-supplied executable, argv, shell command, option, config value, env map, cwd or resource list is accepted.
No clone, fetch, push, archive, object/ref mutation, hook, transport, credential exchange, interpreter invocation or additional operation is authorized by this profile.
The three operations are intended observations; their apparent read-only intent and optional-lock flag do not prove absence of writes or all side effects.

## 3. Trusted policy ownership

A future implementation uses a code-owned policy plus a separately Human-approved deployment selection supplied through the trusted controller, not through caller/event data.
Deployment selection fixes image/root/cwd/config/home/temp/host values. Its provenance and protection are OPEN before any live run. Naming it trusted is a design requirement, not a new authority system or proof that such a protected record exists.
The controller must not admit a policy file selected from the Git child, proposed tree, caller path or returned evidence.
The controller-selected policy/version and requested path/environment values must be faithfully represented in observation output, distinguished from any separately observed values. Their inspection is check-time-only and does not establish that the child used the same policy, bytes, paths or environment. Output cannot authenticate the policy that produced it.
Accepted preflight and EB-0 are not imported as an automatic authorization or invoked as fallback. No writes or integration edits to accepted modules are proposed in EB-5.

## 4. Absolute execution path and cwd

Logical deployment parameters (concrete values remain OPEN):
- TREE_ROOT: approved absolute local Windows drive path.
- IMAGE: exactly TREE_ROOT/ucrt64/bin/git.exe.
- IMAGE_PARENT: exactly TREE_ROOT/ucrt64/bin.
- CWD: a separately prepared, controller-owned non-repository observation directory.
- HOME_ROOT and XDG_CONFIG_ROOT: dedicated empty configuration-home directories.
- EMPTY_GLOBAL_CONFIG: one dedicated empty config file.
- TEMP_ROOT: dedicated writable scratch location only if its need/policy is separately approved.
- SYSTEM_ROOT: explicit approved host Windows directory.

All are selected outside caller input. No actual directory/file is created here.
Do not infer TREE_ROOT from PATH, cwd, discovery results, ZIP filename or event labels.
No shutil.which, name-based launch, cmd shim, shell, batch or PowerShell launcher is used.
Require absolute ordinary drive paths; reject UNC, device/extended prefixes, relative paths, drive-relative paths, traversal, NUL/control characters, ADS syntax, ambiguous trailing dots/spaces and case-fold collisions. IMAGE must also reject double-quote characters. Path validation must precede normalization; normalization must not silently repair traversal.
IMPLEMENTATION_GATE N2: explicitly supply the absolute IMAGE as the CreateProcess application name, not merely argv[0]. Windows command-line serialization and its verification remain OPEN; no current implementation or behavior is asserted.
Inspect component identities/reparse/alias conditions only with a separately approved method and label every result check-time-only. Lexical containment alone is insufficient. No path check, open/hash operation, approved pathname or equal pre/post result establishes identity at process creation or during loading. Image, DLL or ancestor substitution between observations remains unexcluded in this design.
IMAGE must be a regular approved candidate, not cmd/git.exe. Its existing recorded member digest may be cited but not treated as a live measurement or operational ratification.
CWD must not be inside a Git worktree, bare repository or a parent chain that permits repository discovery under the future approved resolution policy. Exact checks and host/ancestor boundaries remain OPEN.
IMPLEMENTATION_GATE N3: ancestor repository-discovery restrictions are not decided. Evaluate GIT_CEILING_DIRECTORIES or protected ancestor paths and their version-specific behavior; neither is silently added to the environment or treated as established protection.
Changing cwd to a controlled non-repository directory intentionally changes the observation context from accepted preflight's repo-root cwd (preflight_her_v1.py:25, :464). Results are not asserted equivalent to ambient system/global/local/worktree observations.
Failure to establish any required deployment/path/config assumption blocks a live run; do not fall back to existing preflight.

## 5. Process environment: explicit draft table

Construct a new environment map from approved policy only. Never merge os.environ and never inherit arbitrary GIT_*, PATH, HOME, USERPROFILE, XDG_*, credential, loader or certificate settings.

| Variable | Proposed value | Purpose and limit |
|---|---|---|
| PATH | IMAGE_PARENT only, no extra segment | Bound executable search hypothesis; not DLL/helper containment proof |
| GIT_NO_REPLACE_OBJECTS | "1" | Retain EB-0's supplied-data item; no freshness inference |
| GIT_TERMINAL_PROMPT | "0" | Preserve explicit nonterminal-prompt intent; does not disable every askpass/helper |
| GIT_OPTIONAL_LOCKS | "0" | Preserve optional-lock avoidance intent; not proof of zero writes |
| GIT_CONFIG_NOSYSTEM | "1" | Proposed system-config suppression control; exact selected-version semantics require static evidence |
| GIT_CONFIG_GLOBAL | EMPTY_GLOBAL_CONFIG | Proposed explicit global source; exact selected-version fallback/include behavior requires static evidence |
| HOME | HOME_ROOT | Avoid ambient home config input |
| USERPROFILE | HOME_ROOT | Avoid ambient user profile input |
| XDG_CONFIG_HOME | XDG_CONFIG_ROOT | Avoid ambient XDG config input |
| SystemRoot | SYSTEM_ROOT | Explicit host parameter, not inherited or authenticated by the child |
| WINDIR | SYSTEM_ROOT | Same approved host directory; necessity remains to be qualified |
| TEMP | UNSET | Default draft omits this key; fallback behavior and need remain OPEN |
| TMP | UNSET | Default draft omits this key; no implied scratch-write authorization |

This is a proposed exact map, not verified behavior of the selected Git/Windows image. UNSET means absent from the child map, not the literal string "UNSET". TEMP/TMP are absent by default (N7); omission does not prove that Git/Windows uses no temporary directory, makes no writes or will function. TEMP_ROOT is only a possible future parameter, not active in this default map. Any variant setting TEMP/TMP requires separately reviewed need, locations and policy; no such variant is approved here. Windows-essential variables, temporary-directory needs and config-control semantics are OPEN. If additional variables are needed, reject the run until a separately reviewed profile revision; do not inherit them to make the command work.
Reject case-insensitive duplicate environment keys. All values are exact strings without NUL. No parameter expansion or interpolation from child/caller text.
Do not add GIT_DIR, GIT_WORK_TREE, GIT_COMMON_DIR, GIT_EXEC_PATH, GIT_CONFIG_COUNT/KEY_*/VALUE_*, GIT_CONFIG_PARAMETERS, GIT_ASKPASS, GIT_SSH*, loader overrides or other keys on demand.
PAGER, GIT_PAGER and LESS are prohibited environment variables (N1), including case-insensitive spellings: they must be absent from the child map, and attempts to inject them must refuse. Their omission is not proof that every pager/helper route is blocked.
Do not claim omission of these keys blocks every helper/resource route. Compile-time defaults, config and Windows loader behavior remain separate proof obligations.
The effective map above is incompatible with EB-0's only-GIT_NO_REPLACE_OBJECTS rule. No EB-0 amendment occurs here.

## 6. Git configuration reference sources

Proposed controlled-config observation, not host config discovery:

- System config: intended excluded by the proposed GIT_CONFIG_NOSYSTEM control.
- Global config: intended only EMPTY_GLOBAL_CONFIG, with no directives or includes.
- Home/XDG defaults: dedicated empty directories; no ambient profile lookup.
- Local/worktree config: intended absent through approved non-repository cwd and absent Git repository redirection.
- Command/env config injection: no -c options and no config-injection GIT_* keys.
- Includes, includeIf, external credentials and unapproved config resources: prohibited by policy.

Each mechanism must have exact version-matched static evidence before live approval. An empty file/directory assertion, source string, empty scope result or successful exit is not closure proof. Global/system suppression and repository discovery interactions are OPEN.
IMPLEMENTATION_GATE N5: qualify Git for Windows config sources including ProgramData, TREE_ROOT/etc/gitconfig and prefix-relative paths. The controls above are intended policy, not verified suppression of those sources. Exact selected-version lookup/fallback/include behavior remains OPEN.
CONFIG_SCOPES preserves the original suffix rather than quietly adding --global, --system, --file or other options. Its controlled context intentionally differs from accepted preflight.
Expected controlled config result is no scope records. Unexpected scope/key/value/include or an ambiguous parse is a policy refusal, not an opportunity to silently sanitize and accept.
Raw config output can contain sensitive values. Do not persist raw stdout/stderr or child-controlled keys/values. Inspect only in bounded transient buffers to derive scope/policy anomalies, then discard without echoing input or exception text.
A future exact NUL/config-record grammar must be specified against the selected version; existing parser success is not used as uniqueness, closure or confidentiality proof.

## 7. DLL, helper, script and resource reach

Known prior lower bound: ucrt64/bin/git.exe imports names matching libiconv-2.dll, libintl-8.dll, libpcre2-8-0.dll and zlib1.dll. libintl-8.dll additionally imports libiconv-2.dll (EB-1).
All four remain UNRESOLVED dependency hypotheses. Static basename uniqueness does not authenticate resolution.

Before a live controlled-observation scope, identify the approved host/loader boundary and sufficient operation-specific reach evidence. Explicitly record unresolved host API-set/forwarders, dynamic loads, managed assemblies, plugins, locale/catalogs, configuration resources and helpers. Do not classify unproved routes as other.
The selected three argv do not directly name a helper/script/transport/certificate. This does not prove their nonreach.
Proposed policy allows no intentional helper/script/network/credential dispatch. Enforceability and detection method are OPEN: an environment table or observed absence in one run is not a process-containment mechanism.
If static evidence requires a helper, interpreter, CA bundle, OpenSSL module or other resource, stop and request a named investigation/profile revision. Never admit arbitrary resource paths from observed exec-path or child output.
EXEC_PATH output is informational. It must not become a trusted helper root, executable override or next subprocess command. Proposed comparison to an approved exec-path value remains OPEN until selected-tree static evidence defines it.
No capability to guarantee zero network/extra child processes is established here. A future execution scope needs explicit controls or accurately bounded trust assumptions; if neither is approved, do not launch.
PATH restriction does not imply Windows DLL resolution isolation. Existing hosted administrator and unprotected-writer limitations remain unchanged.
IMPLEMENTATION_GATE N4: additional Windows loader qualification remains OPEN for IFEO, AppCertDlls/AppInit_DLLs, .local, SxS, KnownDLLs and DLL-search fall-through. A requirement that CWD contain no DLL/executable files is a consideration to resolve, not an implemented control or sufficient closure proof. No unverified Windows mechanism is reported PASS.

## 8. Input validation and rejection

Proposed public request shape: an exact built-in dict with exactly schema_version and operation_id.
schema_version is an exact built-in string equal to the proposed label her.limited_git.request.v0; operation_id is an exact string equal to one of VERSION, EXEC_PATH, CONFIG_SCOPES.
The label is a proposed future format, not an implemented or approved persistent receipt schema.

Reject subclasses, unexpected/missing keys, arbitrary nested objects, booleans/integers as strings, list/dict schema versions, custom hash/equality/stringification, NUL/control characters and extra authorization/status/env/path/argv fields.
If JSON input is supported later, cap encoded request size at a proposed 4096 bytes; require UTF-8, unique object keys, finite JSON values and exact shape. Do not coerce invalid values with str(), bool() or int().
Perform safe exact-type checks before set membership, dictionary operations involving untrusted keys or delegation. No call to Phase 1 evaluate_event or existing collectors is needed for request validation.
Return constant structured refusal reason codes with no reflection of malformed input, repr, path, child text or exception message. KeyboardInterrupt/SystemExit and cancellation are not successful completion.
Proposed ordinary exception handling must be bounded to input parse/probe/process/output-validation stages, with fixed stage-specific reasons; no blanket that disguises unrelated implementation errors as successful safety controls.

Prelaunch refusal categories:
- INPUT_REJECTED: malformed request or unsupported operation.
- POLICY_UNAPPROVED: missing/invalid trusted deployment selection or required separate Human authorization.
- DEPLOYMENT_OPEN: concrete root/cwd/env/config/host assumptions, approved timeout or descendant-cleanup prerequisites not resolved.
- IMAGE_UNBOUND: candidate identity/provenance/runtime relationship not established for the requested scope.
- LAUNCH_IDENTITY_REQUIRED_UNPROVEN: the separately approved controller-owned scope requires identity of the actual launched/loaded bytes, or scope is missing/unknown/ambiguous, while launch_identity remains UNBOUND_AT_LAUNCH; refuse before spawning, with no authorization inferred from check-time results.
- RESOURCE_REACH_OPEN: helper/DLL/config/resource route not sufficiently qualified for the proposed bounded run.
- EB0_COMPATIBILITY_NOT_SELECTED: attempted EB-0 promotion/mapping without a specific approved option.
- AUTHORITY_CLAIM_REJECTED: caller attempts to supply approval/PASS/freshness/pin declarations.

The current design has unresolved prelaunch conditions; actual execution remains UNEXECUTED. No existing pin or approval is inferred.

## 9. Proposed execution and refusal lifecycle (not implemented)

1. Validate the small request without reflecting it.
2. Obtain independently protected controller policy and verify separately authorized controller-owned scope; derive identity_required_scope there only. Missing/unknown/ambiguous scope is identity-required, never a caller-selected observational exception.
3. Derive fixed image, argv, cwd and exact environment.
4. Inspect deployment and resource conditions using only methods authorized for that later scope; retain check-time-only provenance. Do not promote those observations to launch identity. If the requested scope requires execution identity, refuse before spawning with LAUNCH_IDENTITY_REQUIRED_UNPROVEN.
5. If any required condition is OPEN or unavailable, emit BLOCKED/UNCONFIRMED and do not spawn.
6. If a separately approved run becomes possible, launch the absolute image with shell disabled, closed stdin, no inherited extra handles and bounded binary stdout/stderr through pipes only, never console output (N1). Explicit CreateProcess application-name binding and command-line serialization remain subject to N2, not assumed from absolute argv.
7. Proposed per-operation wall-clock limit: 10 seconds. Proposed stdout cap: 65536 bytes; stderr cap: 16384 bytes. Caps are hard limits, not silent truncation. Supervisor/parser failure or cap breach refuses the operation.
8. Timeout/cancellation cleanup must be independently specified and tested, including any descendants. Killing only the direct process does not establish child cleanup or containment. No privileged Job/token implementation is authorized in EB-5.
   IMPLEMENTATION_GATE N6: an approved timeout and descendant-process cleanup policy are prelaunch conditions, not post-launch TODOs. If either is undecided or unavailable, refuse with DEPLOYMENT_OPEN before spawning. The proposed numeric limit alone does not satisfy this gate.
9. Capture process return/exit status and parse according to a fixed operation-specific grammar. Nonzero exit, spawn error, ambiguous/malformed output, unexpected config scope or exec-path mismatch is a refusal, not evidence that an isolation control worked.
10. Emit a bounded observation with fixed nonclaims and launch_identity=UNBOUND_AT_LAUNCH, including when exit status or parsing appears successful. Never execute a child-supplied path or retry under relaxed environment/policy.

VERSION grammar and selected expected version string, EXEC_PATH canonical target, CONFIG_SCOPES full grammar, Windows command-line serialization and cleanup guarantees remain OPEN before implementation freeze/live runs.
Numeric limits are design proposals requiring approval, not assumed guarantees of existing subprocess.run.
Tests of mocked process behavior can validate only control flow; they cannot establish that physical controls operated.

## 10. Evidence output and ceilings

Proposed structured local observation fields:
- format/profile/policy revision identifiers;
- operation identifier and controller-derived literal argv;
- controller-derived requested absolute image/tree/cwd and exact environment supplied to the spawn API, distinguished from any check-time or child-reported observations; these are not authenticated execution/loader identity;
- launch_identity fixed to UNBOUND_AT_LAUNCH and identity_required_scope refusal when applicable;
- check_time_only fixed to true for deployment/image/DLL/ancestor/config/policy inspection results, with the observation stage retained;
- provenance references to prior inventory/distribution evidence, clearly marked retained/copied/not remeasured;
- deployment/resource checks with status, constant reason and evidence source (STATIC, SYNTHETIC or LIVE_OBSERVATION), never inferred from caller labels; LIVE_OBSERVATION identifies an observation method only, not trusted identity, safety, freshness, Windows control verification or ratification;
- attempted/not-attempted, bounded process/exit/timeout/output-limit observations when actually executed;
- parsed version/exec-path or recognized scope categories only after strict grammar validation; no raw config values, unvalidated path or exception text;
- actual output-retention/redaction policy and any incomplete checks;
- explicit EB-0 compatibility selection and mismatch reasons;
- explicit nonclaims and non-PASS conclusion.

An observation is not an authoritative receipt, a Human Final, a trusted nonce ledger, a new digest domain, operational pin approval or an external witness. Persistent recording, output schema and integration destinations require separate design approval.
Controller/child self-reports must be distinguished from authenticated evidence. Event/run correlation labels may be controller-local and must be labelled UNAUTHENTICATED; no N2 freshness is implied.
A process exit 0 or success marker reports only that the observed process/output met the specified completion/parsing conditions, if actually observed. It does not identify the launched bytes as the approved image or authenticate loaded DLLs, ancestors or policy. Overall assurance remains UNCONFIRMED, not PASS, and launch_identity remains UNBOUND_AT_LAUNCH. Invalid request/process/policy conditions are BLOCKED or FAIL according to their fixed stage; no success is inferred from any refusal. Unconfirmed Windows mechanisms never become PASS from expected output, self-report, missing anomaly or a synthetic test.
Missing checks remain visible, not removed to reach a favorable result.

Mandatory ceilings:
- launch_identity UNBOUND_AT_LAUNCH; no inspection, LIVE_OBSERVATION, exit 0 or success marker may override it;
- execution_binding_real UNEXECUTED unless a separately scoped real binding is actually established; launcher completion alone cannot change it;
- operational_mingit_pin UNRATIFIED;
- Python pin remains PIN_PENDING;
- dependency/loader/config closure UNPROVEN unless separately evidenced under an explicit scope;
- Windows isolation UNVERIFIED;
- writers outside T UNCONFIRMED;
- N2 external binding UNEXECUTED and freshness UNPROVEN;
- independent witness NOT_CLAIMED;
- FULL_INR_READY NO;
- production authorization UNCHANGED.

## 11. EB-0 compatibility options and required Human decisions

EB-0 is a pure supplied-fixture decision. It checks absolute candidate/tree lexical conditions, limited PATH and an environment whose only GIT_* item is GIT_NO_REPLACE_OBJECTS=1. It does not launch a process or establish loader/config/isolation/freshness.

E1: Distinct profile (recommended draft).
Keep the explicit two existing intent flags plus proposed config controls in the new profile. Label EB0_ENVIRONMENT_COMPATIBLE=NO. Do not call EB-0 automatically or produce TREE_MATCH_UNPINNED for this real environment. Matching tree/path facts may be cited as separate observations only.
Human decision: accept a separate process profile and its exact controls/limitations. This preserves accepted EB-0 and preflight unchanged.

E2: Strict EB-0-shaped environment in a separate future design.
Use only GIT_NO_REPLACE_OBJECTS=1 among GIT_* keys and the exact limited PATH. The two flags and proposed config controls cannot remain in the child environment.
Human decision: explicitly approve alternate prompt/write/config protections, prove relevant version-specific config/resource assumptions and accept semantic differences before a run. Removing flags alone does not establish safety. No such alternative has been designed or verified here.

E3: Explicit EB-0 amendment in another scope.
Propose a versioned change to EB-0's accepted environment conditions, independently review it and seek a new Human decision for that candidate. Do not overwrite historical bytes/verdicts or retroactively expand them.
Human decision: authorize that amendment as a separate scope first. EB-5 neither requests nor performs it as an implicit dependency.

Never strip extra variables from the evidence map while leaving them in the actual process. Never manufacture an EB-0-compatible fixture from a distinct environment and imply it describes the process. Case normalization or filtering is not compatibility.
No option is frozen by authorization to prepare EB-5. E1 is the recommended design choice awaiting acceptance.

## 12. Design-only verification plan for a later implementation scope

Required future negative/unit coverage:
- every wrong input type including unhashable schema versions, subclasses/custom objects, duplicate JSON keys and unauthorized fields;
- exactly the three argv, no shell/path/argv/env fallback or child-selected command;
- environmental poisoning does not appear in the child map; case-fold duplicate keys and unapproved config variables refuse;
- PAGER/GIT_PAGER/LESS injection, including case variants, refuses; ambient pager variables are not inherited, stdout/stderr use pipes only, and any console-output configuration is rejected;
- TEMP/TMP remain absent in the default map; ambient values do not leak in, and an unapproved scratch variant cannot be selected by input;
- caller-supplied identity_required_scope or scope downgrade refuses; missing/unknown controller scope remains identity-required and blocks spawn under UNBOUND_AT_LAUNCH;
- missing approved timeout or descendant-cleanup policy refuses before spawn with DEPLOYMENT_OPEN; a timeout or cleanup failure is not a successful isolation test;
- cmd shim, alternate Git, path traversal, reparse/alias ambiguity, policy substitution and missing deployment evidence refuse;
- image swap after the last image check but before process creation: a substituted image may emit expected output/exit 0; check-time agreement must not promote launch identity or assurance, and an identity-required scope must refuse before spawning;
- DLL swap after inspection but before/during loading: unchanged image output or restored post-check bytes must not establish loaded-DLL identity, safety or ratification;
- ancestor swap between path inspection and process creation/loading: the same pathname and matching restored pre/post observations must not establish resolved-object identity;
- simulate swapped objects, restored objects and forged LIVE_OBSERVATION/success claims through unit-only substitutes; assert the fixed UNBOUND_AT_LAUNCH ceiling, non-PASS assurance and identity-required prelaunch refusal. These are proposed negative tests, not executed Windows swap experiments or proof of physical prevention;
- missing/repeated/reordered/malformed checks and forged PASS cannot become an assurance result;
- timeout/output overflow/nonzero exit/parser error retain correct stage reasons and do not count as successful isolation;
- sensitive config/raw errors are not reflected or persisted;
- extra helper/resource/exec-path routes remain unavailable absent approval;
- EB-0 mismatch is retained, including the two flags and proposed config controls; no selective environment serialization;
- existing Phase 1/2A/r3/AWI/EB-0 code and historical verdicts remain untouched.

Source/static checks and mocked subprocess tests are not privileged Windows observation, authenticated current-event capture or independent reproduction. Actual process policy enforcement, physical writer protections and host loader behavior require a different approved evidence scope.

## 13. OPEN decisions and approval gates

OPEN:
1. Concrete trusted deployment selection/protection and absolute image/tree/cwd/config/home/temp/host locations.
2. E1/E2/E3 choice and exact environment keys, config suppression semantics and Windows-essential variables.
3. Version-specific expected output/config grammar and exec-path root. Bytes-to-runtime identity remains unproven under mandatory launch_identity=UNBOUND_AT_LAUNCH; any scope requiring it is blocked before execution authorization.
4. Reachable DLL/helper/resource/config/host boundaries; all 371 existing roles still unresolved.
5. Enforceable process/network/write limits and descendant cleanup method; no privileged design assumed.
6. Output schema, safe retention, redaction and exact status/reason ranking.
7. Operational pin targets/evidence/ratification; no changes to RATIFIED_GIT_SHA256 or RATIFIED_PYTHON_SHA256.
8. Full INR operation list/integration and N2 concrete authorities remain outside this initial profile.

Separate Human gates:
- H1: Review this design, choose compatibility/config/cwd policy and decide whether/when to freeze it; no automatic freeze.
- H2: Approve a bounded static qualification of named members and retained version-matched config/loader evidence, with no remeasurement/execution.
- H3: Authorize additive implementation and synthetic tests only after the relevant design questions are resolved; no edits to accepted preflight/EB-0.
- H4: Independently review the new implementation; separately approve concrete deployment, observations/measurement methods and a bounded live-run scope if appropriate.
- H4 limitation: check-time-only results cannot justify an execution-identity-required run. Any future identity-binding mechanism requires a separately authorized design/evidence scope; this revision supplies none and grants no run approval.
- H5: Separately decide any real execution-binding, operational pin ratification, INR integration and acceptance. Do not infer any of them from H1-H4 or exit 0.
- N2: Independent future authority/key/nonce-holder/clock decisions remain governed by its existing Freeze, not this launcher.

Next minimum scope: bounded read-only design review of EB-5 and Human choice of E1 versus alternatives, including the controlled non-repository config-observation context. If accepted as the direction, authorize the named static config/loader/resource qualification to resolve H2 prerequisites. No implementation or run is the next automatic step.

## 14. Review classification and prospective Human H1 boundary

The Human reports Grok Bot final review ACCEPT and M1 documentarily CLOSED. This records the supplied review disposition, not independent reproduction, Human acceptance of this design, or Design Freeze. Actual execution identity remains UNBOUND_AT_LAUNCH and every relevant inspection remains check-time-only.

| Review item | Classification and documentary treatment | Remaining limit |
|---|---|---|
| M1 | CLOSED, documentation only: fixed ceiling, non-inference and prelaunch identity-required refusal | Actual launch/loader identity remains unproven |
| N1 | DOCUMENTATION_NONBLOCKER: pipes only, prohibited PAGER/GIT_PAGER/LESS, negative-test proposals | No process or pager behavior verified |
| N7 | DOCUMENTATION_NONBLOCKER: default TEMP/TMP absent; any set variant separately reviewed | Temporary-directory fallback/need OPEN |
| N8 | DOCUMENTATION_NONBLOCKER: DESIGN_DRAFT_NOT_FROZEN | Work authorization is not freeze |
| R1 | DOCUMENTATION_NONBLOCKER: scope controller-owned only; missing/unknown scope identity-required | Protected scope provenance/deployment OPEN |
| R2 | DOCUMENTATION_NONBLOCKER: terminology changed to M1 ceiling remediation | EB-4 option C unchanged |
| N2 | IMPLEMENTATION_GATE, OPEN: explicit CreateProcess application name and IMAGE quote rejection | Command-line serialization/verification OPEN |
| N3 | IMPLEMENTATION_GATE, OPEN: ancestor repository discovery policy | Ceiling/protected-ancestor option not selected |
| N4 | IMPLEMENTATION_GATE, OPEN: additional Windows loader routes and CWD contents | No loader isolation PASS |
| N5 | IMPLEMENTATION_GATE, OPEN: ProgramData/tree/prefix config sources | No config closure PASS |
| N6 | IMPLEMENTATION_GATE, OPEN: approved timeout and descendant cleanup before launch | Undecided conditions refuse DEPLOYMENT_OPEN |

Reviewer N2 above is a finding identifier, distinct from the existing INR N2 freshness design/scope. None of N2-N6 or any other OPEN item becomes PASS, implemented, ratified or authorized by this documentation update.

Prospective H1 freeze inclusion, only if the Human expressly decides: the additive three-operation design direction; E1 as an EB-0-incompatible independent profile candidate; fixed argv and controller-only policy/scope requirements; default environment proposal with TEMP/TMP absent and pager variables prohibited; pipe-only output; fail-closed requirements, fixed identity/evidence ceilings, refusal categories, negative-test plan and explicit unresolved implementation gates. Freezing these requirements would not assert they are realizable or verified.

Prospective H1 freeze exclusions: implementation, tests executed, Windows loader/process-control correctness, finalized command-line serialization, selected ancestor-discovery control, proven config/resource/dependency closure, concrete deployment/cleanup mechanism, launch identity, live execution, binding evaluation, freshness/witness evidence, operational PIN or ratification, integration and production permission. Existing EB-0 Human Final, EB-0 through EB-4, accepted preflight and all existing evidence/digests remain unchanged.

Human H1 decisions required: explicitly choose or decline E1; accept or revise the proposed default environment/cwd/config intent and pipe-only contract without declaring their behavior verified; decide whether to freeze only the bounded requirements above while retaining N2-N6 and section 13 OPEN items; identify excluded actions and the next separately authorized static-qualification scope. If unresolved requirements prevent that bounded freeze, retain DESIGN_DRAFT_NOT_FROZEN. No H1 decision is supplied or inferred by this document.

Remaining OPEN includes all section 13 items and N2-N6, TEMP/TMP need/fallback, version-specific output grammar, protected controller scope, concrete paths/policy and output/status schema. E1 remains a candidate, not accepted by the reported reviewer verdict. No approved timeout/cleanup, operational execution permission or launch binding is created here.

## 15. Actions in this batch

Original EB-5 batch created this design document. This revision modifies only this same document for M1 ceiling remediation and Human H1 preparation; EB-4 option C and accepted preflight remain unchanged.
M1 documentation rationale: earlier wording could join check-time inspection to successful launch observation without an explicit identity boundary. The fixed UNBOUND_AT_LAUNCH ceiling, check-time-only labels, refusal for identity-required scopes, non-inference rules and proposed swap negative tests remove that documentary inference. They do not prevent swaps, implement launch binding or prove Windows behavior. The Human-supplied final review reports M1 documentarily CLOSED; no new independent confirmation is claimed here.
The Human supplied the specific N1-N8/R1/R2 content for this revision. N1/N7/N8/R1/R2 receive documentary corrections only; N2-N6 remain explicitly OPEN IMPLEMENTATION_GATE requirements. No implementation feasibility, Windows behavior, ratification or completed test is asserted.
No EB-0 through EB-4, other existing document/code/ZIP/inventory/Human Final/PIN/digest changed.
No Git execution, binding evaluation, ratification, measurement, test execution, extraction, installation, commit, merge or push occurred.
Human-approved DESIGN-ONLY work completed; design acceptance/freeze and later actions remain separate.
FULL_INR_READY: NO.

