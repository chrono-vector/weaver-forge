# INR-XR-001 External Run Bundle Procedure v0

Status: PROCEDURE_ONLY_NOT_EXECUTED. No real external INR run has been performed.

This procedure describes how an external runner produces an evidence bundle and how
an operator classifies it with the INR-XR-001 adapter
(`docs/inr_001/xr/validate_external_run_v0.py`).

**An adapter PASS is an ADAPTER/BUNDLE PASS only.** It is not an INR external
reconstruction PASS and not a fresh local INR PASS. It is not IW admission, not Human
Final and not production permission. A disk bundle is checked only for internal
consistency and hash binding. v0 has no provider-signed attestation, so a fabricated
but fully consistent bundle would also pass the adapter (the synthetic fixture in
test 20 shows exactly that). The accepted INR-001 local tooling is not changed. Its
`non_origin`, `shared_state_absence` and `all_writer_isolation` predicates stay
UNCONFIRMED.

## 1. Trust model

```
raw evidence (runner) -> bundle hash validation -> adapter-owned derivation -> bounded predicates -> classification
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
- **Operator parameters (not evidence).**
  - `--expected-event-id` is the event ID the operator issued for this run.
  - `--not-before` is the RFC 3339 UTC time the operator requested the run.

  Without them `current_event_capture_established` is never established.
- **Bundle (untrusted).** All files are runner-written observations. Their only
  value is what the adapter derives from them under the rules in section 6.

## 2. Runner model and layout

FIRST_RUNNER_MODEL = FRESH_HOSTED_RUNNER (provider `github-actions`,
`RUNNER_ENVIRONMENT=github-hosted`, Linux image, CPython 3.11.x).

```
$ROOT = $RUNNER_TEMP/inrxr            (created by this job; empty at creation)
$ROOT/tooling   checkout of the accepted INR tooling commit, core.autocrlf=false
$ROOT/target    fresh Git acquisition of chrono-vector/weaver-forge at TARGET_SHA
$ROOT/stage     supervisor --work-dir (its staging dir inr-local-* lives here)
$ROOT/obs       runner observation files (section 4)
$ROOT/bundle    output of the collection helper
```

The protected-tree entry paths are relative to `$ROOT` and use the `tooling/` and
`target/` prefixes.

## 3. Steps

1. **Operator.** Issue a fresh event ID (single use) and record the request time
   (`not_before`). Never reuse an event ID.
2. **Runner, job start.** Record `runner_identity.json`. Use the provider metadata
   (`GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`, job ID, `RUNNER_NAME`, `RUNNER_OS`,
   `RUNNER_ARCH`, `ImageOS`, `ImageVersion`, `RUNNER_ENVIRONMENT`), the machine boot
   time (`/proc/stat btime`) and the job start time. Record any artifacts of earlier
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
6. **Runner, freeze.**
   - Make every protected entry read-only for the execution principal, and make
     `$ROOT` and its parents non-writable.
   - Record `isolation_checks.json`: the mount table (`findmnt -J`), package and build
     caches, the Git object store, the protected entries (category, path, kind,
     sha256, writability by principal and by others, symlink/reparse, link count) and
     the parent chain.
   - Compute the freeze digest with the adapter rule:
     `sha256(canonical(sorted([category, path, kind, sha256] for each entry)))`, where
     `canonical` is `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)`.
7. **Runner, event.** Record `started_at` (UTC), then run the accepted supervisor
   exactly as INR-001 r3 prescribes, with the target clone as repository:
   `python -I -S -B $ROOT/tooling/docs/inr_001/supervisor_inr_v0.py --event-id <ID>
   --repository $ROOT/target --out $ROOT/export.json --work-dir $ROOT/stage --ledger <ledger>`.
   Record `completed_at` when it exits.
8. **Runner, post.** Re-measure the protected entries and record
   `post_execution_digest`. It must equal the freeze digest.
9. **Runner, bundle.** Run
   `python -B -m docs.inr_001.xr.collect_bundle_v0 --export $ROOT/export.json --observations
   $ROOT/obs --target-repository $ROOT/target --out $ROOT/bundle --started-at <UTC> --completed-at
   <UTC> --bundle-id <id>` from `$ROOT/tooling`. The helper splits the supervisor export
   into `event_start.json`, `command_results/*.capture.json`, `stdout/*`, `stderr/*`,
   `post_measurement.json` and `event_complete.json`. It copies the observation files
   and the six acquired PSM files into `raw/target/`, then writes `raw/sha256sums.txt`
   and `external_run_manifest.json`. It asserts nothing.
10. **Operator.** Transfer the bundle and run
    `python -B -m docs.inr_001.xr.validate_external_run_v0 BUNDLE --expected-event-id <ID>
    --not-before <UTC>`. Exit status 0 means ADAPTER/BUNDLE PASS only.

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
  references only. `$defs.raw_*` are the raw evidence data. `$defs.adapter_result` is
  the adapter output, with the derived predicates and the final classification. The
  output is never accepted as input.

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

## 6. Derivation rules (adapter-owned) and classification

PASS requires every gate and every one of the ten predicates to be explicitly
established, with no issue anywhere (conjunctive; default NOT_ESTABLISHED).
Precedence: BLOCKED > FAIL (including contradictions) > UNCONFIRMED/NOT_ESTABLISHED > PASS.

| predicate | established only when (all) | contradiction: FAIL | missing/unclear: UNCONFIRMED | BLOCKED |
|---|---|---|---|---|
| runner_identity_established | schema-valid identity, known hosted provider, run attempt >= 1, parseable boot/job times | - | missing file, unknown provider | - |
| fresh_hosted_runner_candidate | github-hosted, boot <= job start <= boot + 4h, no prior-job artifacts, no cache restore, no inherited writable state | self-hosted, boot after job start, prior-job artifacts, cache restore, inherited state | not hosted/unknown, boot > 4h before job | - |
| fresh_workspace_established | empty initial listing, created >= job start, created <= acquisition start <= end, `.git` is a directory, clean worktree, repository inside workspace | non-empty listing, created before job, timing disorder, linked worktree, dirty tree | missing evidence, repo outside workspace | - |
| independent_acquisition_established | Git clone/fetch from the authoritative https URL, no copy/link/shared-store commands, ref = HEAD = TARGET_SHA, remote = source, the six PSM files' bytes hash to the pinned digests, every required commit (TARGET_SHA + commits in the digest-verified pinned example) present | local-path source, copy/link or `--reference/--shared/--local`/`file://`, HEAD/remote contradiction, event required-object set differs | missing or unparsable log, non-authoritative source | ref/HEAD not TARGET_SHA, PSM digest mismatch, required object missing |
| no_shared_origin_filesystem_evidence | no writable shared/network mount (network fs types are recognised by the adapter, not only by the runner flag), unshared Git object store without alternates, no origin snapshot restore | any of these detected | missing evidence | - |
| no_shared_mutable_cache_evidence | no restored or shared package/build cache, no cache restore events | any detected | missing evidence | - |
| python_311_established | CPython 3.11.x, consistent with the supervisor, every child, and the measured interpreter digest | inconsistency | non-absolute executable | not 3.11 (3.10/3.12/3.13/3.14/unknown), non-CPython, identity missing |
| git_identity_established | absolute executable, which = executable, version present, no GIT_* env, no replace refs/alternates/grafts, not shallow, no rejected config, HEAD = TARGET_SHA, consistent with the event Git probe and every child | inconsistency | - | identity missing, any ambiguity |
| protected_tree_isolation_established | all 7 categories covered, named entries match the trusted digests, no symlink/reparse/hard link, nothing writable by principal or others, parents not writable, not on a writable shared/network mount, no restored cache overlapping, the repository inside the tree, freeze digest = adapter-recomputed digest = post digest | alias, hard link, writable by others, digest change, trusted-digest mismatch | missing categories or entries, writable by principal, writable parent, admin principal | - |
| current_event_capture_established | manifest event ID = operator ID; event ID/challenge consistent across files; trusted target/profile/origin bindings; isolated supervisor running the accepted supervisor bytes; event inside the job window and after acquisition and `not_before`; ordered r3 lifecycle; EVENT_START consistent; EVENT_COMPLETE after CAPTURE_COMPLETE; pinned source before/after; accepted probe; per case: inventory match, event/challenge/nonce binding, stream digests, child pid, timing inside the execution window, exact argv/PATH/GIT env, refusal semantics and return code, child identity | replay or another event, stale or historical times, lifecycle disorder, stream/argv/identity/refusal mismatch, supervisor report showing FAIL or contradicting v0 semantics | no operator ID or not-before, EVENT_COMPLETE or child provenance absent, binding to another profile/origin, non-supervisor run, tooling digest differs | event target SHA not TARGET_SHA |

| gate | rule |
|---|---|
| bundle_integrity | section 4 rules |
| trusted_reference_binding | manifest target SHA = TARGET_SHA (else BLOCKED); origin and profile references equal to the trusted ones (alternate, stale or executor-selected origin: UNCONFIRMED); trusted configuration loadable (else BLOCKED) |

### Self-assertion policy (decision)

- **Ignored.** `runner_declarations` objects (manifest and runner observation files)
  are informational. They are echoed under `ignored_runner_declarations` and never
  read by any derivation. They can neither raise nor lower a result.
- **Rejected.** Any other non-schema field is rejected. That includes fields named
  after a predicate or classification (`fresh`, `non_origin`, `all_writer_isolation`,
  `git_verified`, `classification`, `*_established` ...). In the manifest, the bundle
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

- No provenance: the adapter cannot prove that the bundle came from the runner it
  describes, or that the observations are complete or true. Every input is
  runner-reported.
- No freshness against a ledger: a disk bundle cannot be checked against the
  runner-side INR ledger. Staleness is bounded only by the operator-issued event ID,
  the not-before time and the job window. The operator must never reuse an event ID.
- No all-writer proof: privileged or host-level writers, and writers outside the
  observed mount table, are not excluded.
- An adapter PASS changes no INR-001 classification. Integration into INR-001
  external assurance is not implemented.

## 8. Deviations from the request

- `raw/target/<pinned PSM file>` is added to the bundle. The adapter hashes the
  acquired PSM bytes itself and derives the required-object set from the
  digest-verified pinned example, exactly as the supervisor does. It does not rely on
  runner-reported digests alone.
