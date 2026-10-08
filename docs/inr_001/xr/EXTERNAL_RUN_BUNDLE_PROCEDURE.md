# INR-XR-001 External Run Bundle Procedure v0

Status: PROCEDURE_ONLY_NOT_EXECUTED. No real external INR run has been performed.

This procedure describes how an external runner produces an evidence bundle and how
an operator classifies it with the INR-XR-001 adapter
(`docs/inr_001/xr/validate_external_run_v0.py`).

R2 (material remediation of M1-M3) separates structural validity from assurance,
adds the GitHub Actions provider trust anchor with one bundle-to-run binding, adds
the one-way XR verifier process as the integration point into INR, and binds the
protected inventory to the actual execution paths.

R3 (material remediation of M1 and M3 only) binds the submitted bundle CONTENT to the
provider-held artifact CONTENT (section 1.2), states the provenance scope honestly
(RUN-LEVEL; job-level NOT_CLAIMED), binds the actual staged execution objects (cwd,
staged validator, case inputs, interpreter, Git object store, required ancestors) to
the protected inventory, and replaces the principal-writable stage-root allowance with
a freeze model (section 6.1). Under the accepted INR supervisor's staging layout,
`all_writer_isolation_established` cannot be PASS and is reported UNCONFIRMED.

**Structural validity is not assurance.** A bundle that is internally consistent and
hash-bound gets `structural_bundle: PASS` only. External assurance additionally
needs authoritative GitHub Actions metadata, fetched by the verifier itself from
`https://api.github.com`, and the bundle-to-run binding (section 1.2). Without
trusted provider data, assurance is UNCONFIRMED or BLOCKED, never PASS. A synthetic
but fully consistent bundle (test 20 and section-12 test 1) is structural PASS with
assurance UNCONFIRMED. Nothing here is an INR PASS, IW admission, Human Final or
production permission. The accepted INR-001 local tooling (supervisor, launcher,
probe, profile, origin set) is not changed. A local supervisor run still reports
`non_origin`, `shared_state_absence` and `all_writer_isolation` as UNCONFIRMED.

## 1. Trust model

```
raw evidence (runner, untrusted claims)
  -> structural validation (STRUCTURAL_BUNDLE PASS/FAIL)
  -> adapter-owned evidence derivation (*_evidence predicates)
  -> GitHub provider verification + bundle-to-run binding (PROVIDER_PROVENANCE, BUNDLE_RUN_BINDING)
  -> assurance predicates (*_established) and EXTERNAL_ASSURANCE
  -> [XR verifier PROCESS only] INR-001 predicates for the external event
```

- **Trusted inputs (adapter side only).** These are the committed INR configuration,
  loaded through `supervisor_inr_v0.configuration()`, which checks the schema and the
  pinned digests:
  - `TARGET_SHA c5e1cfa2fb52874fe9c97e0eade6a120c12cb27b`;
  - the pinned target profile (id, digest, the 11 cases, the command inventory, the
    six PSM file digests);
  - the accepted origin reference set `INR_ORIGIN_SET_PSM_001_V0` with its digest,
    and its single authoritative repository `chrono-vector/weaver-forge`;
  - the LF-blob digests of the accepted INR tooling files: `supervisor_inr_v0.py`,
    `runtime_probe.py`, `input_cases.py`, the profile and the origin JSON.

  The adapter never takes any of these from the bundle.
- **Trusted provider data.** GitHub REST API responses fetched by the verifier from
  the fixed origin `https://api.github.com`, using the token in the environment
  variable `INR_XR_GITHUB_TOKEN` (read-only `actions:read` scope on
  `chrono-vector/weaver-forge`). The token is a credential, not evidence.
- **Operator parameters (not evidence).**
  - `--expected-event-id` is the event ID the operator issued for this run.
  - `--not-before` is the RFC 3339 UTC time the operator requested the run.
  - `--expected-head-sha` is the reviewed workflow commit the operator dispatched.

  Without them, current-event capture and provider provenance are never established.
- **Bundle (untrusted).** All files are runner-written observations and claims. The
  GitHub fields in `runner_identity.json` (repository, run ID, attempt, job ID,
  runner name, head SHA, workflow path, job start) are CLAIMS that the verifier
  compares with the provider data.

### 1.1 Result model

| field | values | meaning |
|---|---|---|
| `structural_bundle` | PASS / FAIL | manifest schema-valid; every raw file present, path-safe and hash-bound (`bundle_integrity` gate) |
| `evidence_predicates` (10, `*_evidence`) | PASS / FAIL / UNCONFIRMED / BLOCKED / NOT_ESTABLISHED | bundle-authored evidence present and consistent; never assurance on its own |
| `provider_provenance` | PASS / UNCONFIRMED / BLOCKED / FAIL | the claimed run, attempt, job, commit, workflow, runner and times agree with authoritative GitHub data |
| `bundle_run_binding` | PASS / UNCONFIRMED / BLOCKED / FAIL | the verified run carries exactly one artifact `inr-xr-bundle-<bundle_digest>` whose downloaded CONTENT equals the submitted bundle under the frozen content rule (section 1.2) |
| `run_level_provenance` | PASS / UNCONFIRMED / BLOCKED / FAIL | conjunction of `provider_provenance` and `bundle_run_binding`; the bundle is bound to the verified workflow RUN |
| `job_level_provenance` | NOT_CLAIMED (constant) | the producing job is not authenticated (artifacts are run-scoped) |
| `isolation_components` | PASS / UNCONFIRMED / BLOCKED / FAIL each | `inventory_binding`, `frozen_tree`, `staged_objects` (section 6.1); `staged_objects` is always UNCONFIRMED under the accepted supervisor |
| `assurance_predicates` (9, `*_established`) | PASS / UNCONFIRMED / BLOCKED / FAIL | evidence predicate(s) AND all four gates (`bundle_integrity`, `trusted_reference_binding`, `provider_provenance`, `bundle_run_binding`) |
| `external_assurance` | PASS / UNCONFIRMED / BLOCKED / FAIL | conjunction of all assurance predicates and gates; precedence BLOCKED > FAIL (including contradictions) > UNCONFIRMED > PASS |

Mapping: `runner_identity`, `fresh_hosted_runner`, `fresh_workspace`,
`independent_acquisition`, `python_311`, `git_identity` and
`current_event_capture` each come from the evidence predicate of the same name.
`no_shared_mutable_state_established` comes from
`no_shared_origin_filesystem_evidence` plus `no_shared_mutable_cache_evidence`.
`all_writer_isolation_established` comes from `protected_tree_isolation_evidence`.

### 1.2 Provider trust anchor and bundle-to-run binding (GitHub Actions only)

`provider_github_v0.py` is the only provider boundary.

- JSON endpoints (fixed set, GET only, redirects refused, final host must be
  `api.github.com`):
  `/repos/{repo}/actions/runs/{run_id}/attempts/{attempt}`,
  `/repos/{repo}/actions/jobs/{job_id}`,
  `/repos/{repo}/actions/runs/{run_id}/artifacts?name=inr-xr-bundle-<bundle_digest>`,
  `/repos/{repo}/actions/artifacts/{artifact_id}`.
  `{repo}` is the trusted repository from the committed origin set, never the bundle.
- Download endpoint (R3, the only non-JSON request):
  `GET https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip` with
  the token. `{artifact_id}` is an integer taken only from the verified listing of the
  verified run. GitHub answers 302 with a `Location` to a short-lived signed storage
  URL. Exactly one redirect is followed, and only to a target that is `https`, port
  443, without userinfo or fragment, on a host matching
  `productionresultssa<N>.blob.core.windows.net` (GitHub Actions artifact storage),
  with a path under `/actions-results/`. Any other answer (non-302, 404/410, missing
  or disallowed `Location`) is a provider failure. The redirected request carries NO
  `Authorization` header, follows no further redirect, must answer 200 from the same
  allowed host, and is capped at 64 MiB. There is no generic URL fetching, and the
  `archive_download_url` field of the metadata is not used.
- **No token: BLOCKED, and no network request is made.** No mock, offline or
  substitute mode exists in production code, and no argv, environment or file switch
  selects one. Unit tests pass a clearly labelled `UnitTestTrustSubstituteProvider`
  in-process. That object exists only in the test module.
- **Binding (the ONE mechanism: GitHub artifact CONTENT verification).**
  `bundle_digest` = SHA-256 of the exact `external_run_manifest.json` bytes. The
  manifest binds every raw file by SHA-256. The workflow uploads the bundle tree as
  the artifact named `inr-xr-bundle-<bundle_digest>` (the collection helper prints the
  name). The verifier:
  1. requires exactly one artifact of that name in the verified run's listing, with a
     positive integer ID;
  2. fetches that artifact's metadata, which must repeat the ID and name, name the
     verified run and head SHA, be unexpired with a positive size, and have been
     created inside the claimed job window (expired or empty: UNCONFIRMED; other run,
     head, ID or name: FAIL);
  3. downloads the ZIP (above); its length must equal `size_in_bytes`, and when the
     metadata carries `digest: sha256:<hex>` the ZIP SHA-256 must equal it (FAIL);
  4. applies the frozen content rule.
- **Frozen artifact content rule (`ARTIFACT_CONTENT_RULE`).** The ZIP holds exactly
  `external_run_manifest.json` plus every path bound by its `evidence_files`, as
  regular, unencrypted, stored or deflated file entries. Directory entries are
  allowed only for ancestors of those files. Every entry's bytes must equal the
  submitted bundle file byte for byte, so the manifest bytes, the raw-file inventory
  and SHA-256 values, the event ID, the target SHA and the profile/origin digests are
  all bound to provider-held content. FAIL: an unreadable archive, an extra, missing,
  duplicate (also case-folded), traversing, absolute, backslash or drive path, a
  symlink entry, an encrypted or unsupported entry, a size inconsistency, or any byte
  difference. Caps: 256 entries, 256 MiB uncompressed. No bundle-supplied artifact
  hash is trusted. A submitted bundle that fails integrity is never compared
  (UNCONFIRMED).
- Download unavailable (no token, network error, 404/410, disallowed redirect):
  BLOCKED, never PASS. `provider_run.artifact_name` is set only when the content is
  bound.
- **Provenance scope.** GitHub artifacts are run-scoped and the REST artifact
  metadata names the run, not the producing job. The binding is RUN-LEVEL
  (`run_level_provenance`). The claimed job is checked against the provider job
  record for consistency (same run, attempt and head, runner name, hosted group,
  artifact and event times in its window), but the producing job is not
  authenticated: `job_level_provenance` is the constant `NOT_CLAIMED`, and the
  claimed job fields are reported as `claimed_job_*`. The approved workflow is
  designed with a single producing job, but the verifier does not verify the
  workflow file content, so this is not used as a job binding.
- Provider checks:
  - FAIL when any of these differ: repository, run ID/attempt, job ID, the job's
    run/attempt/head, the claimed head SHA, the operator `--expected-head-sha`, the
    workflow path `.github/workflows/inr-xr-external-run.yml` (provider and claim),
    or the runner name.
  - FAIL when the runner group is not `GitHub Actions` (not a GitHub-hosted
    runner), when timestamps are out of order, when the claimed job start lies
    outside the provider job window (120 s skew), or when the event window lies
    outside the job window.
  - UNCONFIRMED when the run or job is not `completed`/`success`, when timestamps
    are missing, or when the run was created before `--not-before` (stale run).
  - BLOCKED when no provider data is available.

### 1.3 One-way integration into INR (XR verifier process)

`xr_verifier_v0.py` is a separate trusted process, started like the INR supervisor:

```
python -I -S -B <tooling>/docs/inr_001/xr/xr_verifier_v0.py --bundle DIR \
    --event-id ID --not-before UTC --expected-head-sha SHA
```

- Within one execution path, the process reads the bundle, runs structural
  validation, evidence derivation and provider verification itself (always
  `GitHubProvider.from_environment()`), and derives the 16 INR-001 predicates with
  `supervisor_inr_v0.Findings`.
- `non_origin` needs the runner-identity, fresh-hosted-runner, fresh-workspace and
  independent-acquisition assurance predicates. `shared_state_absence` needs
  `no_shared_mutable_state_established`. `all_writer_isolation` needs
  `all_writer_isolation_established`.
- Each local predicate needs the relevant XR assurance predicate AND a PASS for the
  same predicate in the provider-bound supervisor report.
- INR stays UNCONFIRMED or FAILs in any of these cases:
  - a not-provider-authenticated result (UNCONFIRMED/BLOCKED);
  - an event ID, target SHA, profile digest or origin digest mismatch (FAIL);
  - a missing or mismatched bundle digest;
  - a stale provider run (UNCONFIRMED);
  - XR external assurance that is not PASS;
  - any in-process or reconstructed result (UNCONFIRMED).
- No argv, stdin, environment or file input carries an XR result or predicate.
- The predicates count only in the report of the isolated process
  (`result_kind: XR_VERIFIER_PROCESS`). `launch()` accepts that report only if
  `verifier_pid` equals the launched child's pid, the event ID matches, and the exit
  status agrees with `pass_allowed`. An in-process call yields
  `IN_PROCESS_NOT_TRUSTED` with every predicate UNCONFIRMED.
- The flow is one-way: XR feeds this report and nothing feeds XR. The accepted INR
  supervisor and launcher are not modified and accept no XR input.

## 2. Runner model and layout

FIRST_RUNNER_MODEL = FRESH_HOSTED_RUNNER (provider `github-actions`,
`RUNNER_ENVIRONMENT=github-hosted`, Linux image, CPython 3.11.x).

Workflow: `.github/workflows/inr-xr-external-run.yml` in `chrono-vector/weaver-forge`,
dispatched by the operator at the reviewed commit (`--expected-head-sha`). The
workflow file itself is not part of this commit (no GitHub configuration is changed).

```
$ROOT = $RUNNER_TEMP/inrxr            (created by this job; empty at creation; bounded workspace root)
$ROOT/tooling   checkout of the accepted INR tooling commit, core.autocrlf=false
$ROOT/target    fresh Git acquisition of chrono-vector/weaver-forge at TARGET_SHA
$ROOT/stage     supervisor --work-dir (its staging dir inr-local-* lives here)
$ROOT/obs       runner observation files (section 4)
$ROOT/bundle    output of the collection helper
```

Protected-tree entry and parent paths are ABSOLUTE and must be the exact paths the
execution used (section 6.1).

## 3. Steps

1. **Operator.** Issue a fresh event ID (single use) and record the request time
   (`not_before`). Never reuse an event ID.
2. **Runner, job start.** Record `runner_identity.json` (claims only). Use the
   provider metadata (`GITHUB_REPOSITORY`, `GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`, the
   numeric job ID, `RUNNER_NAME`, `RUNNER_OS`, `RUNNER_ARCH`, `ImageOS`,
   `ImageVersion`, `RUNNER_ENVIRONMENT`, `GITHUB_SHA` as `head_sha`, and the workflow
   path as `workflow_path`), the machine boot time (`/proc/stat btime`) and the job
   start time. How the numeric job ID is obtained inside the job has not been
   verified in this phase (not executed). Record any artifacts of earlier
   jobs found under the runner work root.
3. **Runner.** Create `$ROOT`. Record its creation time and its (empty) initial
   listing in `workspace_provenance.json`. Use no `actions/cache` or other cache
   restore. Record any restore as a `cache_restore_events` item.
4. **Runner, acquisition.** Run `git init`, `git remote add origin
   https://github.com/chrono-vector/weaver-forge.git`, `git fetch --no-tags origin
   <TARGET_SHA>` and `git checkout --detach <TARGET_SHA>`. Do not use
   `--reference`, `--shared`, `--local`, `file://`, local paths, or copy/link
   commands. Write `acquisition.log` (section 5).
5. **Runner.** Record `git_identity.json`:
   - the executable and its sha256, and `which git`;
   - `git --version` and the `GIT_*` environment;
   - the repository root and the `.git` kind (directory or file);
   - the remote URL and `rev-parse HEAD`;
   - `cat-file -e <sha>^{commit}` for TARGET_SHA and for every commit referenced by
     the pinned example;
   - `refs/replace`, `objects/info/alternates`, `info/grafts` and
     `is-shallow-repository`;
   - the `status --porcelain` output and the config keys.

   Also record `python_identity.json`: `sys.version_info`, `sys.version`,
   `platform.python_implementation()`, the resolved `sys.executable` and its sha256.
6. **Runner, freeze (R3).**
   - The execution principal is a dedicated unprivileged user (for example run via
     `sudo -u inrxr`) that owns nothing under `$ROOT` except the three designated
     output directories `$ROOT/out` (export), `$ROOT/ledger` (ledger) and
     `$ROOT/stage` (supervisor work dir). The frozen tree (target clone, `.git`,
     tooling, interpreter, Git executable) and every required ancestor are owned by
     another principal and are not writable by the execution principal.
   - Record `isolation_checks.json`: the mount table (`findmnt -J`), package and build
     caches, the Git object store, the protected entries, the parent chain, the output
     directories and `freeze_completed_at`. Each protected entry records category,
     absolute path, kind, sha256, writability by the execution principal and by
     others, `owner_is_principal`, symlink/reparse, link count and device. Each parent
     record holds path, writability, `owner_is_principal`, symlink/reparse and device.
     The parent chain covers every ancestor (up to and including `$ROOT`) of every
     protected path inside `$ROOT` that is not itself a protected entry.
   - Staged entries (`stage_root`, `execution_cwd`, `staged_validator`,
     `case_inputs`) are recorded with their actual paths (the supervisor's
     `inr-local-*` directory, `validate_psm_v0.py` and `<case>.json` inside it) and
     HONEST flags: under the accepted supervisor they are created and owned by the
     execution principal, and they cannot be frozen.
   - Compute the freeze digest with the adapter rule over the FROZEN categories only:
     `sha256(canonical(sorted([category, path, kind, sha256] for each frozen entry)))`,
     where `canonical` is
     `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.
7. **Runner, event.** Record `started_at` (UTC), then run the accepted supervisor
   as the execution principal, exactly as INR-001 r3 prescribes, with the target
   clone as repository:
   `python -I -S -B $ROOT/tooling/docs/inr_001/supervisor_inr_v0.py --event-id <ID>
   --repository $ROOT/target --out $ROOT/out/export.json --work-dir $ROOT/stage
   --ledger $ROOT/ledger/<ledger>`. Record `completed_at` when it exits.
8. **Runner, post.** Re-measure every protected entry into `post_entries` (same
   fields), record `post_measured_at` and `post_execution_digest`. It must equal the
   freeze digest, and `freeze_completed_at <= started_at <= completed_at <=
   post_measured_at`.
9. **Runner, bundle.** Run
   `python -B -m docs.inr_001.xr.collect_bundle_v0 --export $ROOT/export.json --observations
   $ROOT/obs --target-repository $ROOT/target --out $ROOT/bundle --started-at <UTC> --completed-at
   <UTC> --bundle-id <id>` from `$ROOT/tooling`. The helper splits the supervisor export
   into `event_start.json`, `command_results/*.capture.json`, `stdout/*`, `stderr/*`,
   `post_measurement.json` and `event_complete.json` (`event_start.json` also records
   the absolute supervisor path). It copies the observation files and the six acquired
   PSM files into `raw/target/`, then writes `raw/sha256sums.txt` and
   `external_run_manifest.json`. It asserts nothing, and prints `bundle_digest` and
   `artifact_name`.
10. **Runner, binding.** Upload the CONTENTS of `$ROOT/bundle` (exactly the bundle
    tree, nothing else) as the artifact named exactly `inr-xr-bundle-<bundle_digest>`
    (`actions/upload-artifact`), from the same job, before the job completes.
11. **Operator, verification.** After the run completes, download the artifact,
    export `INR_XR_GITHUB_TOKEN` (read access to Actions) and run the verifier
    process (section 1.3). The verifier downloads the artifact again itself and
    compares its content with the submitted bundle. The
    adapter CLI is `python -B -m docs.inr_001.xr.validate_external_run_v0 BUNDLE
    --expected-event-id <ID> --not-before <UTC> --expected-head-sha <SHA>`. Its exit
    status 0 means external assurance PASS for the bundle only. It is never an INR
    result. Only the launcher-accepted verifier process report carries INR predicates.

## 4. Bundle layout (closed set)

```
external_run_manifest.json
raw/acquisition.log  raw/runner_identity.json  raw/workspace_provenance.json
raw/isolation_checks.json  raw/python_identity.json  raw/git_identity.json
raw/event_start.json  raw/command_results/<CASE>.capture.json  raw/stdout/<CASE>.stdout
raw/stderr/<CASE>.stderr  raw/post_measurement.json  raw/event_complete.json
raw/target/<pinned PSM file>      (extension to the request's list; see 8)
raw/sha256sums.txt
```

- `<CASE>` ranges over the 11 trusted profile cases.
- The manifest binds every raw file by role, relative path and sha256.
- `raw/sha256sums.txt` (coreutils format) must list exactly the same bindings.
- The schema is `schema/external_run_manifest_v0.schema.json` (strict,
  `additionalProperties: false`). Its top level is the manifest, which holds evidence
  references only. `$defs.raw_*` are the raw evidence data (claims).
  `$defs.adapter_result` is the adapter output (section 1.1), which is never
  accepted as input.

The bundle is rejected as FAIL in any of these cases:
- an absolute path, drive path or backslash;
- a `.`, `..` or empty component (traversal);
- a duplicate path (including case-folded duplicates);
- a role/path pair outside the closed set (unknown or substituted evidence);
- a symlink or junction anywhere in the bundle;
- a resolved path that escapes the bundle;
- an unbound extra file;
- a hash mismatch (tamper evidence);
- `sha256sums.txt` disagreeing with the manifest;
- a manifest that fails its schema.

When the bundle is rejected, no predicate is derived. A required file that is absent,
or bound but missing on disk, gives UNCONFIRMED.

## 5. `acquisition.log` format

```
# inr-xr acquisition log v0
method: git-clone | git-fetch
source: https://github.com/chrono-vector/weaver-forge.git
ref: <TARGET_SHA>
$ <each command, one per line>
> <optional output line>
head: <resulting HEAD>
```

`method`, `source`, `ref` and `head` must each appear exactly once, and at least one
`$` command must be present. Any other line makes the log unparsable (UNCONFIRMED).

## 6. Evidence derivation rules (adapter-owned)

Each evidence predicate is established only when explicitly derived with no issue
(default NOT_ESTABLISHED). An evidence PASS says only that the bundle's evidence is
consistent. Assurance follows section 1.1.

| predicate | established only when (all) | contradiction: FAIL | missing/unclear: UNCONFIRMED | BLOCKED |
|---|---|---|---|---|
| runner_identity_evidence | schema-valid identity, known hosted provider, run attempt >= 1, parseable boot/job times | - | missing file, unknown provider | - |
| fresh_hosted_runner_evidence | github-hosted, boot <= job start <= boot + 4h, no prior-job artifacts, no cache restore, no inherited writable state | self-hosted, boot after job start, prior-job artifacts, cache restore, inherited state | not hosted/unknown, boot > 4h before job | - |
| fresh_workspace_evidence | empty initial listing, created >= job start, created <= acquisition start <= end, `.git` is a directory, clean worktree, repository inside workspace | non-empty listing, created before job, timing disorder, linked worktree, dirty tree | missing evidence, repo outside workspace | - |
| independent_acquisition_evidence | Git clone/fetch from the authoritative https URL, no copy/link/shared-store commands, ref = HEAD = TARGET_SHA, remote = source, the six PSM files' bytes hash to the pinned digests, every required commit (TARGET_SHA + commits in the digest-verified pinned example) present | local-path source, copy/link or `--reference/--shared/--local`/`file://`, HEAD/remote contradiction, event required-object set differs | missing or unparsable log, non-authoritative source | ref/HEAD not TARGET_SHA, PSM digest mismatch, required object missing |
| no_shared_origin_filesystem_evidence | no writable shared/network mount (network fs types are recognised by the adapter, not only by the runner flag), unshared Git object store without alternates, no origin snapshot restore | any of these detected | missing evidence | - |
| no_shared_mutable_cache_evidence | no restored or shared package/build cache, no cache restore events | any detected | missing evidence | - |
| python_311_evidence | CPython 3.11.x, consistent with the supervisor, every child, and the measured interpreter digest | inconsistency | non-absolute executable | not 3.11 (3.10/3.12/3.13/3.14/unknown), non-CPython, identity missing |
| git_identity_evidence | absolute executable, which = executable, version present, no GIT_* env, no replace refs/alternates/grafts, not shallow, no rejected config, HEAD = TARGET_SHA, consistent with the event Git probe and every child | inconsistency | - | identity missing, any ambiguity |
| protected_tree_isolation_evidence | all 9 categories covered; the inventory equals the runtime-derived expected set (section 6.1) with trusted digests; no symlink/reparse/hard link; nothing writable by others; nothing writable by the principal except the stage root; complete parent chain, none aliased or writable; one device for root, parents and entries; not on a writable shared/network mount; no restored cache overlapping; freeze digest = adapter-recomputed digest = post digest | alias, hard link, writable by others, unrelated path substituted, inventory path not used by execution, capture path outside the inventory, Git object store or repository not the executed one, root not the workspace root, digest change, trusted-digest mismatch, unrelated parent record | missing categories or entries (partial inventory), partial parent chain, mount boundary, writable by principal, writable parent, admin principal, runtime paths not admitted | - |
| current_event_capture_evidence | manifest event ID = operator ID; event ID/challenge consistent across files; trusted target/profile/origin bindings; isolated supervisor running the accepted supervisor bytes; event inside the job window and after acquisition and `not_before`; ordered r3 lifecycle; EVENT_START consistent; EVENT_COMPLETE after CAPTURE_COMPLETE; pinned source before/after; accepted probe; per case: inventory match, event/challenge/nonce binding, stream digests, child pid, timing inside the execution window, exact argv/PATH/GIT env, refusal semantics and return code, child identity | replay or another event, stale or historical times, lifecycle disorder, stream/argv/identity/refusal mismatch, supervisor report showing FAIL or contradicting v0 semantics | no operator ID or not-before, EVENT_COMPLETE or child provenance absent, binding to another profile/origin, non-supervisor run, tooling digest differs | event target SHA not TARGET_SHA |

| gate | rule |
|---|---|
| bundle_integrity | section 4 rules (`structural_bundle`) |
| provider_provenance | section 1.2 provider checks |
| bundle_run_binding | section 1.2 binding |
| trusted_reference_binding | manifest target SHA = TARGET_SHA (else BLOCKED); origin and profile references equal to the trusted ones (alternate, stale or executor-selected origin: UNCONFIRMED); trusted configuration loadable (else BLOCKED) |

### 6.1 Protected execution objects and the freeze model (M3, R3)

The adapter derives the REQUIRED protected set from the actual runtime/capture data,
the trusted frozen configuration and the Git/runtime measurements. The inventory
never defines what was executed.

Derivation:

- tooling root = `event_start.supervisor_path` without
  `/docs/inr_001/supervisor_inr_v0.py` (any other shape: UNCONFIRMED);
- repository, common Git dir and Git executable (with its digest) = the supervisor's
  post-measurement `git_probe`;
- execution cwd = the children's single `cwd`, which must be an `inr-local-*`
  directory; stage root = its parent;
- each capture record: `argv` must have the accepted 8-element shape with absolute
  paths; `argv[4]` must be `<tooling root>/docs/inr_001/runtime_probe.py`, `argv[5]`
  `<cwd>/validate_psm_v0.py` (the executed staged validator), `argv[6]`
  `<cwd>/<case_id>.json` (the executed case input), and `argv[7]` the repository.
  Otherwise FAIL. `argv[0]` is the interpreter; all children must use the same one;
- Git object directories = `<common Git dir>/objects` plus every absolute alternate
  reported by `git_identity` or `isolation_checks` (a non-absolute alternate:
  UNCONFIRMED).

Required entries (exact path, kind and digest):

- FROZEN categories: `target_tree` (repository), `target_files` (pinned PSM files),
  `git_directory` (common Git dir), `git_objects` (object store and alternates),
  `profile_origin_binding`, `command_inventory`, `inputs`, `capture_configuration`
  (supervisor and probe) under the tooling root with the accepted digests, and
  `runtime_executables` (interpreter with the measured Python executable digest, and
  the Git executable with the probe digest);
- STAGED categories: `stage_root`, `execution_cwd`, `staged_validator` (digest = the
  capture record's staged source digest) and `case_inputs` (digest = the input
  digest).

The result reports three components in `isolation_components`; the predicate
`protected_tree_isolation_evidence` (and so `all_writer_isolation_established`) is
their conjunction:

1. `inventory_binding`
   - FAIL: an expected path missing while its category lists another path
     (substitution); an extra inventory path; a kind or digest mismatch; a path
     outside the bounded root (`workspace_provenance.workspace_path`) other than
     runtime executables; a root mismatch; `git_identity.repository_root` or
     `git_object_store.path` not the executed repository or object store; an alias
     (symlink, junction/reparse point, hard link) on an entry or parent; a parent
     record not required by any protected path; the declared supervisor work dir not
     equal to the actual stage root; children executed outside the root.
   - UNCONFIRMED: a missing entry with no substitute; a missing required ancestor; a
     device differing from the root (mount boundary); a missing digest.
2. `frozen_tree`
   - FAIL: writable by others; a post entry changed, extra or aliased; a freeze or
     post digest not equal to the recomputed digest, or post not equal to freeze; an
     output dir that is relative or overlaps a frozen entry; a shared/network mount or
     restored cache overlap.
   - UNCONFIRMED: any frozen entry or required parent writable by, or owned by, the
     execution principal (parent replacement risk); an elevated principal; a missing
     post entry; the freeze/post times not enclosing the event window; designated
     output directories not exactly `export`, `ledger` and `work_dir`.
   - Equal pre/post digests alone never establish this component (TOCTOU boundary);
     non-writability during the window is required as well.
3. `staged_objects`
   - With the accepted supervisor (`ACCEPTED_SUPERVISOR_STAGES_AS_PRINCIPAL = True`, a
     code constant, not a switch): always UNCONFIRMED. The accepted supervisor
     creates its `inr-local-*` staging directory with `tempfile` under the work dir,
     writes the validator and case JSON there, and runs the children in it as the
     same principal. The executed objects are therefore principal-owned and
     replaceable during the window, and freezing them would need a change to the
     accepted INR tooling, which is out of scope. A bundle that claims a
     non-writable stage root, or staged objects not owned by the execution principal,
     contradicts that supervisor: FAIL.
   - The unit tests also exercise a hypothetical staging substitute (constant patched
     in-process) to show that the conjunction can PASS when every object is frozen.
     That path is not reachable from production.

Consequence: in production, `all_writer_isolation_established` is at best
UNCONFIRMED. No hostile-host claim is made: privileged or host-level writers are not
excluded, and the observations remain runner-reported.

### Self-assertion policy (decision)

- **Ignored.** `runner_declarations` objects (manifest and runner observation files)
  are informational. They are echoed under `ignored_runner_declarations` and never
  read by any derivation. They can neither raise nor lower a result.
- **Rejected.** Any other non-schema field is rejected. That includes fields named
  after a predicate or classification (`fresh`, `non_origin`, `all_writer_isolation`,
  `git_verified`, `classification`, `*_established`, `*_evidence` ...). In the manifest, the bundle
  is rejected (FAIL). In a raw file, the file is inadmissible, so the dependent
  predicates are not established: UNCONFIRMED, or BLOCKED for Python/Git identity.
- **Negative-only.** The INR-001 r3 supervisor report inside `event_complete.json`
  is checked against the INR event schema. It can only lower the result: a local
  predicate FAIL gives FAIL; a non-PASS, a non-supervisor run or a mismatched event
  gives UNCONFIRMED or FAIL; `pass_allowed: true` or a non-UNCONFIRMED external
  predicate gives FAIL. It never raises the result.

### EVENT_COMPLETE mapping

The r3 supervisor lifecycle ends at `CAPTURE_COMPLETE`. `raw/event_complete.json` is
the bundle-level completion marker. The collection helper writes it after the
supervisor exited, and it carries the supervisor report. The adapter requires
`event_complete_ns >= CAPTURE_COMPLETE` and `completed_at >= started_at`.

## 7. What this does not establish

- Provider trust is bounded. Provenance rests on GitHub Actions, on the token's view
  of the API, and on the reviewed workflow code at `--expected-head-sha` computing
  the artifact name from the bundle it uploads. A compromised workflow commit or
  runner could still upload a fabricated bundle under the right name. That is
  outside v0 (no hostile-host resistance).
- Real provider verification has NOT been executed. In this phase every provider
  path was exercised only with unit-test trust substitutes, and no network call was
  made. Real provider verification stays UNCONFIRMED until a real run.
- No freshness against a ledger: a disk bundle cannot be checked against the
  runner-side INR ledger. Staleness is bounded by the operator-issued event ID, the
  not-before time, the provider run creation time and the job window. The operator
  must never reuse an event ID.
- No all-writer proof: privileged or host-level writers, and writers outside the
  observed mount table, are not excluded. Under the accepted supervisor the staged
  execution objects are principal-writable, so all-writer isolation is UNCONFIRMED.
- Real artifact download has NOT been executed; the content binding was exercised
  only with unit-test archives (MOCK_ONLY). The storage host allowlist follows
  GitHub's documented behaviour at the time of writing and may need revision.
- No job-level provenance: the binding authenticates the run, not the job.
- Observations inside the bundle (mount table, writability, parent chain) remain
  runner-reported. The provider anchors their origin (which run produced them), not
  their truth.

## 8. Deviations from the request

- R3: the R2 principal-writable stage-root allowance is removed. Because the
  accepted supervisor stages the executed validator and case JSON as the execution
  principal, `staged_objects` (and so all-writer isolation) stays UNCONFIRMED; the
  accepted INR tooling is not changed to avoid this.
- R3: runtime executables (interpreter, Git) are bound by path and digest but lie
  outside the bounded workspace root; their parent chains are not required.
- R3: job-level provenance is NOT_CLAIMED (artifacts are run-scoped).
- R2/R3: OIDC/attestations are not used. The single binding mechanism is GitHub
  artifact content verification (R3), keyed by the artifact name.

- `raw/target/<pinned PSM file>` is added to the bundle. The adapter hashes the
  acquired PSM bytes itself and derives the required-object set from the
  digest-verified pinned example, exactly as the supervisor does. It does not rely on
  runner-reported digests alone.
