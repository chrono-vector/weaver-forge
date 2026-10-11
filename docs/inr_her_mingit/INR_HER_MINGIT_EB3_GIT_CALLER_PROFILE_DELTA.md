# INR-HER MinGit EB-3 Git Caller Profile Delta

Status: DOCUMENTATION_ONLY_SOURCE_OBSERVATIONS_NOT_OPERATIONAL_APPROVAL
Date: 2026-10-11 (Asia/Tokyo)

## Scope and meaning of evidence states

This is an additive delta to EB-2, not a replacement, Design Freeze, Human Final, approved command allowlist, binding result or pin ratification.
Only explicitly identified caller files were inspected. No repository-wide Git-caller search was performed.

CONFIRMED (確認済み): exact behavior expressed in the inspected source or an existing contract; not an observed process/runtime fact.
UNSPECIFIED (未規定 / OPEN): a required policy or decision is not specified by these sources.
UNVERIFIED (未確認): source describes or permits behavior, but no live execution, path resolution, loader/resource verification or invocation trace was observed.

Repository-root-relative paths and one-based source line numbers below identify the inspected files. Root: C:/dev/_tmp/weaver-gzse-001. Source references are current-workspace observations, not newly authenticated hashes or Git-history evidence.

## Authorized caller identification

EB-2 explicitly identifies docs/inr_her_002a/preflight_her_v1.py at line 18 and lists its three observations at lines 43-45. The Phase 2A contract describes the same observation responsibilities at docs/inr_her_002a/INR_HER_001_PHASE2A_CLOSURE_CONTRACT.md:73-79.
Accordingly, only that file was treated as an authorized production Git caller.

EB-0's fixture evaluator and EB-1's packaged path list do not identify additional Git callers. Names of helpers or inventory resources do not authorize reading presumed INR callers. EB-2:47 and :53 explicitly leave the full INR operation inventory OPEN.
No capture/supervisor/XR/provider/ledger/test or other presumed caller was added to this investigation. This bounded result is not a claim that the repository has only one Git caller.

## Delta D1: exact Git operation candidates

All call sites belong to collect_readonly_observation in docs/inr_her_002a/preflight_her_v1.py:187-215.

| Operation candidate | Exact subprocess argv produced by source | Call-site reference | State |
|---|---|---|---|
| Version observation | ["git", "--version"] | docs/inr_her_002a/preflight_her_v1.py:193 and :463 | CONFIRMED in source; runtime UNVERIFIED |
| Exec-path observation | ["git", "--exec-path"] | docs/inr_her_002a/preflight_her_v1.py:194 and :463 | CONFIRMED in source; runtime UNVERIFIED |
| Config scope observation | ["git", "config", "--list", "--show-scope", "-z"] | docs/inr_her_002a/preflight_her_v1.py:195 and :463 | CONFIRMED in source; actual config sources/values UNVERIFIED |

Each is conditional on a truthy shutil.which("git") result (docs/inr_her_002a/preflight_her_v1.py:192-195).
The shared launcher _git_text(args) is at :460-475. There is no additional _git_text call site in this inspected file.
These are the minimum observed preflight-operation candidates only. Full INR object/ref/tree/history/export or other execution requirements remain UNSPECIFIED; none is silently added.

## Delta D2: cwd, executable resolution and environment

| Property | Source fact | Exact reference | State / remaining gap |
|---|---|---|---|
| cwd expression | cwd=ROOT | docs/inr_her_002a/preflight_her_v1.py:464 | CONFIRMED |
| ROOT definition | Path(__file__).resolve().parents[2] | docs/inr_her_002a/preflight_her_v1.py:25 | CONFIRMED expression; for the ordinary inspected placement this denotes C:/dev/_tmp/weaver-gzse-001; actual invocation/reparse identity UNVERIFIED |
| Discovery | shutil.which("git") | docs/inr_her_002a/preflight_her_v1.py:192 | CONFIRMED; observed executable stored at :207 |
| Launch selection | ["git", *args], not [git_path, *args] | docs/inr_her_002a/preflight_her_v1.py:463 | CONFIRMED; discovery result is not passed as the executable path |
| PATH | inherited through os.environ; no PATH override or verification in launcher | docs/inr_her_002a/preflight_her_v1.py:469 | Inheritance CONFIRMED; exact PATH, Windows resolution and selected candidate UNVERIFIED |
| GIT_TERMINAL_PROMPT | explicit string "0" override | docs/inr_her_002a/preflight_her_v1.py:469 | CONFIRMED |
| GIT_OPTIONAL_LOCKS | explicit string "0" override | docs/inr_her_002a/preflight_her_v1.py:469 | CONFIRMED; does not itself prove no writes or complete isolation |
| Other GIT_* | inherited os.environ entries are retained except the two overrides | docs/inr_her_002a/preflight_her_v1.py:469 | Inheritance CONFIRMED; names/values and allowlist UNSPECIFIED/UNVERIFIED |
| GIT_NO_REPLACE_OBJECTS | not set by this launcher; may or may not be inherited | docs/inr_her_002a/preflight_her_v1.py:469 | Actual presence/value UNVERIFIED |
| HOME/USERPROFILE, PATHEXT, loader/config/certificate variables | full parent environment inheritance | docs/inr_her_002a/preflight_her_v1.py:469 | No approved values or isolation policy established here |
| Shell option | subprocess.run has no explicit shell argument | docs/inr_her_002a/preflight_her_v1.py:462-470 | Source CONFIRMED; not proof of Git-internal helper/script nonreach |
| Capture/bounds | capture_output=True, text=True, timeout=10, check=False | docs/inr_her_002a/preflight_her_v1.py:465-468 | CONFIRMED; actual output/exit not observed |
| Refusal behavior | OSError or timeout returns None; nonzero exit returns None | docs/inr_her_002a/preflight_her_v1.py:471-475 | CONFIRMED; no invocation in EB-3 |

The selected ucrt64/bin/git.exe remains an investigation candidate, not an observed target. cmd/git.exe remains excluded as the intended execution target; the existing name-based launcher has not been changed to enforce that selection.
No absolute execution-tree root was approved or supplied by this caller evidence.

## Delta D3: config and exec-path interpretation

- The collector queries scopes at docs/inr_her_002a/preflight_her_v1.py:195.
- config_scopes parses NUL-separated records, extracts the first newline-delimited token and keeps recognized scope names at :173-184.
- Recognized names are system, global, local, command and worktree at :103. This is a parser vocabulary, not an approved config-source allowlist.
- Returned data retain the recognized scope list at :213; config values are discarded by the parser, not prevented from being read/captured by Git. The full Git stdout is first returned by _git_text at :475.
- Existing logic sets git_config_closed=False when git_path and scopes are truthy, otherwise None at :196-199. An empty list or failed observation does not establish config closure.
- exec_path or git_path is stored as git_execution_path at :210. It is an observation field, not proof of the identity of the executed image, a verified dependency root or helper containment.
- git_source is marked UNEXPECTED when Git was found at :211.
- The evaluator keeps Git source and config non-PASS at :341-355, including a MINGIT_PINNED label still BLOCKED at :346-347.

Which config files and include chains are actually read, whether command/environment configuration is injected, and operation-specific resource consumption remain UNVERIFIED. Their approved policy remains UNSPECIFIED.

## Delta D4: helpers, scripts and required resources

| Category | Caller evidence | State |
|---|---|---|
| External helper/script directly launched by the Python caller | This inspected Git launcher has only the three explicit argv above; no direct named helper/script subprocess call is present | CONFIRMED absence of such a direct call in this file only |
| Git-internal dispatch, hooks, filters, transport, pager/editor, credential manager, shell interpreters | No operation-specific static dispatch or negative-reach evidence established by the caller | UNVERIFIED; allowed policy UNSPECIFIED |
| Git exec-path directory | Queried at :194, stored at :210 | Source CONFIRMED; actual directory/member mapping UNVERIFIED |
| Four DLL candidates | Prior EB-1 native import evidence for libiconv-2.dll, libintl-8.dll, libpcre2-8-0.dll and zlib1.dll | Prior static hypotheses reused; loader resolution and closure UNVERIFIED |
| Git config, includes and repository/config inputs | :195, :464, :469 allow observations in inherited context | Exact resource paths/read set UNVERIFIED; bounded policy UNSPECIFIED |
| Certificate bundles, OpenSSL modules, SSH config, locale/catalogs, managed runtime resources | No positive required-resource or exclusion evidence in this caller | UNVERIFIED; do not mark other or infer dependency from names |
| Host Windows/API-set/forwarded imports | No live host identity or loader mapping inspected | UNVERIFIED; target-image policy remains OPEN |

The three argv do not explicitly request a network operation. This is not proof that arbitrary inherited configuration or Git-internal behavior cannot cause additional activity.
The caller alone cannot establish a complete required-resource set. All 371 EB-1 unresolved roles remain unchanged.

## Delta D5: EB-0 integration remains OPEN

EB-0 requires the supplied environment's only GIT_* entry to be GIT_NO_REPLACE_OBJECTS=1 at docs/inr_her_mingit/execution_binding_v0.py:227-232, and PATH to contain just the candidate parent at :233-244.
The existing Phase 2A launcher explicitly adds two different GIT_* entries and inherits all remaining environment at docs/inr_her_002a/preflight_her_v1.py:469. Its executable selection is name-based at :463.

These facts confirm EB-2 O4's integration question, not an authorization to edit either accepted implementation. EB-0 fixture input and the real preflight environment have not been linked by an approved mapping. Matching fixture labels do not repair that gap.

## EB-2 OPEN-item delta

- O1 PARTIALLY DOCUMENTED: three preflight argv established; complete INR operation inventory still OPEN.
- O2 PARTIALLY DOCUMENTED: this caller's cwd expression and name-based executable selection established; real tree/process identity and other callers remain OPEN.
- O3 PARTIALLY DOCUMENTED: inherited environment, two overrides and scope parser identified; config sources/allowed values and closure remain OPEN.
- O4 CONFIRMED OPEN: exact EB-0 versus Phase 2A environment/path difference now has line references.
- O5 OPEN: direct caller has no additional helper launch; Git-internal helper/script/resource reach unverified.
- O6-O11 UNCHANGED OPEN: loader/host boundaries, dynamic resources, manifest provenance, pin target, N2 responsibilities and real binding/measurement authorization.
No EB-2 item is declared globally closed.

## Next minimum scope and necessary approval

Propose a documentation-only decision record selecting whether the intended operational profile includes only these three preflight observations or also other INR callers.
For any other caller, Human must name an existing contract/code reference that identifies its exact file, or explicitly approve a bounded path-discovery scope. Do not infer targets from filenames or expand to full repository history.
For a preflight-only profile, separately approve source/static investigation of exact candidate members needed for the existing five-file PE graph and named config/resource consumers. Read-only ZIP member inspection, no remeasurement or execution, must be explicit.
Decide how a future bound absolute image, cwd, environment/config allowlist and EB-0 fixture representation coexist without changing accepted code implicitly. Any implementation, live binding evaluation, measurement or pin ratification remains a separately authorized stage.
Without these decisions, do not claim a finalized minimum INR command profile, dependency closure, candidate process identity, freshness or isolation.

## Preserved scope

Only this new report is saved. Existing EB-0/EB-1/EB-2, Phase 2A contract/code, ZIP, inventory, Human Final, PIN and digest remain unchanged.
No Git command or executable, observation collector, binding evaluator, test suite, remeasurement, ratification, commit, merge or push was run.
No current process environment, user config or system runtime was inspected.
Execution binding: UNEXECUTED.
Operational pin: UNRATIFIED.
Freshness and dependency closure: UNPROVEN.
Independent Witness: NOT_CLAIMED.
FULL_INR_READY: NO.

