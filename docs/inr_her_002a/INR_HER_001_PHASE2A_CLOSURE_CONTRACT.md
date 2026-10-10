# INR-HER-001 Phase 2A Closure Contract

Status: PHASE2A_WORKING_CONTRACT

This document is the working contract for the local preflight gate. It is not a Human Final, not production authority, and not an external-run admission.

FULL_INR_READY: NO

Accepted Phase 1 Human Final: `fccd128ec37a8cfb940c572a1bf566449abddb25`

Phase 1 implementation: `2357aceee154eaba16ef9bc5411f2363f5d71585`

Base under that implementation: `38131191710aad087c274fc3ffc95e80f1c140cf`

## Bounded claim

Phase 2A remains inside the Phase 1 question: protection of P from the restricted child principal U. This phase does not establish that claim. `all_writer_isolation_bounded_v1` stays non-PASS. `HASH_AGREEMENT_ONLY` remains hash agreement only.

## WACP selected context

Scope: `INR-HER-001-PHASE2A-CONTEXT-FCCD128`

Review mode: `implementation`

Base and head are the accepted Human Final, relationship `EQUAL`.

Selected files:

- `docs/inr_001/schema_check.py`
- `docs/inr_her_001/INR_HER_001_PHASE1_HUMAN_FINAL.md`
- `docs/inr_her_001/INR_HER_001_PROCEDURE.md`
- `docs/inr_her_001/__init__.py`
- `docs/inr_her_001/collect_bundle_her_v1.py`
- `docs/inr_her_001/schema/inr_event_v0_r4.schema.json`
- `docs/inr_her_001/schema/inr_her_predicate_result_v0.schema.json`
- `docs/inr_her_001/schema/inr_her_surface_record_v0.schema.json`
- `docs/inr_her_001/schema/inr_supervisor_result_v0_r4.schema.json`
- `docs/inr_her_001/supervisor_her_v1.py`
- `docs/inr_her_001/validate_her_v1.py`

`docs/inr_her_001/__init__.py` and `collect_bundle_her_v1.py` are selected because importing the Phase 1 package loads them. No further INR source is selected.

## N1 unhashable schema_version

Phase 2A entry `evaluate_phase2a` scans `schema_version` on the event, the supervisor result, and each surface record. A value that raises TypeError from `hash`, including `[]` and `{}`, returns BLOCKED `HER_SCHEMA_VERSION`. The overall result is a schema-checked object whose status is FAIL, BLOCKED, or UNCONFIRMED. Phase 1 `evaluate_event` is not called on that input.

The accepted Phase 1 function still raises TypeError at `supervisor_her_v1.py` `_version_reason` when it evaluates the same input. Correcting that line requires an edit to accepted Phase 1 code. That portion is STOPPED.

Exact minimal change, not applied:

```python
for item in versions:
    try:
        hash(item)
    except TypeError:
        return "HER_SCHEMA_VERSION"
```

Insert that loop in `_version_reason` immediately above `if any(item in R3_SCHEMA_VERSIONS for item in versions):`. No other Phase 1 line changes.

## N2 freshness and replay

Freshness is verified only by an external binding that this phase does not execute (`N2_EXTERNAL_BINDING_UNEXECUTED`):

1. An issuer outside the HER supervisor signs one binding of a new nonce, the issue time, the event_id, the source head, and each surface freeze hash.
2. The verifier checks that signature with a key the supervisor does not hold.
3. A repeated nonce, an event_id that differs from the binding, and a head string that differs from the bound head are failures.
4. Uniform relabeling of every event_id is a failure when it is declared or bound. Consistent identifiers alone do not prove the event is fresh.
5. Hash agreement without the binding remains BLOCKED `HER_FRESHNESS_UNPROVEN`.

A runner flag, a relabeled event_id, or `HASH_AGREEMENT_ONLY` does not authenticate freshness.

## Read-only preflight

The gate reads the platform, the running CPython version and executable path, the Git executable and exec-path, Git config scope names, and the current process token's enabled privilege names. It does not elevate, install, download, or write Git config. Config values are discarded.

Missing runtimes, a platform other than observed Windows x64, an unverified pin, an unexpected Git executable, and a permission observation of ABSENT are BLOCKED. A privilege query that cannot be completed is UNCONFIRMED `HER_PRIVILEGE_OBSERVATION_UNAVAILABLE`. Enabled privileges remain BLOCKED `HER_PRIVILEGED_OBSERVATION_UNVERIFIED` because this phase does not create a restricted token or a Job.

Python identity must be CPython 3.11.9 before a pin can be discussed. Any other version is BLOCKED `HER_PYTHON_IDENTITY_MISMATCH`. The pin reason stays `HER_PYTHON_PIN_PENDING` and outranks an unratified MinGit result when both are open. A Git-path failure stays on the `git_execution_path` check as `HER_GIT_SOURCE_NOT_SNAPSHOT` or `HER_GIT_PIN_UNRATIFIED`. It is not reported as hash agreement.

## Authenticated SHA-256 pins

Python 3.11.9:

1. Obtain the exact official Windows x86-64 artifact over authenticated HTTPS from python.org.
2. Verify the publisher signature and the SHA-256 published for that exact filename in the same authenticated session.
3. Compute SHA-256 over those bytes locally.
4. Ratify only when the local digest equals that published digest.

MinGit:

1. Name the exact MinGit version and filename.
2. Obtain those bytes over authenticated HTTPS from the Git for Windows release.
3. Verify the publisher-attested SHA-256 for that exact asset.
4. Compute SHA-256 locally and ratify only on equality.
5. Bind later Git execution to that pinned tree. Any other `git.exe` remains an unexpected source.

This phase does not download those bytes. No digest is stored. Python remains `PIN_PENDING`. MinGit remains `UNRATIFIED`. A hash of the installed `python.exe`, an MD5, or a previously circulated digest is not a ratification.

## Withheld claims

- Phase 1 source remains unedited
- Restricted-token isolation remains unproven
- Job containment remains unproven
- Event freshness remains unproven
- Independent external witness remains unclaimed
- FULL INR PASS remains unclaimed
- This document is not a Human Final
- Production authority remains unclaimed
- No external run is performed
- Python 3.11.9 SHA-256 remains unratified
- MinGit digest remains unratified
- Privileged Windows tests remain unexecuted

Accepted r3/AWI files and the Phase 1 Human Final stay byte-for-byte with `fccd128ec37a8cfb940c572a1bf566449abddb25`.
