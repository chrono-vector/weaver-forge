# Witness evidence validator (C2E-4 / `evidence_schema_version=1`)

| Item | Path |
|------|------|
| Validator | `scripts/validate_witness_evidence.py` |
| Synthetic tests | `scripts/tests/test_validate_witness_evidence.py` |
| Templates (normative schema) | `templates/*` |

## Usage

```bash
python external_verifications/grok-build/witness-package/scripts/validate_witness_evidence.py \
  /path/to/evidence/run-id
```

Exit code `0` means **structural PASS** only.

## What it does not prove

- That Docker or Cargo actually ran
- Witness independence
- Truthfulness of logs or hashes
- Independent Witness (C-014) completion

## Output policy

The validator writes **only** to its own stdout/stderr. It never writes,
creates, or modifies any file inside the evidence directory it is
validating — including the manifest. Regenerating `EVIDENCE_MANIFEST.sha256`
is a separate, manual step performed by the Witness (see
[WITNESS_PACKAGE_MANIFEST.md](../WITNESS_PACKAGE_MANIFEST.md)) before the
validator is run.

## Evidence schema version

Every structured (key=value) evidence file must declare:

```text
evidence_schema_version=1
```

The four raw capture files — `BUILD_STDOUT.txt`, `BUILD_STDERR.txt`,
`CONTAINER_STDOUT.txt`, `CONTAINER_STDERR.txt` — are raw process output and
are **exempt** from the schema-version requirement (they may also be empty,
e.g. under `BUILD_NOT_STARTED`).

## Outcome model

Outcome is detected from `BUILD_EXIT_CODE.txt` field `outcome=` (preferred).
If that field is absent or not a recognized value, the validator attempts a
conservative inference from `cargo_started`/`build_status`; if inference is
still ambiguous, validation fails rather than guessing.

| Outcome | Meaning |
|---------|---------|
| `BUILD_NOT_STARTED` | Docker/bootstrap ran but cargo was never invoked |
| `CARGO_FAILED` | Cargo started and exited non-zero |
| `CARGO_SUCCEEDED_ARTIFACT_MISSING` | Cargo exited `0` but the expected artifact was not found |
| `CARGO_SUCCEEDED_ARTIFACT_PRESENT` | Cargo exited `0` and the artifact was found and inspected |
| `INFRASTRUCTURE_FAILURE` | An environment/infrastructure fault (not a cargo/bootstrap failure) prevented the build |

`outcome=` must also be present and **identical** in `DOCKER_EXIT_CODE.txt`
and `BUILD_TIMING.txt`; a mismatch against `BUILD_EXIT_CODE.txt` is a
structural failure.

Validation is **outcome-sensitive**: `BUILD_EXIT_CODE.txt`
(`cargo_started`/`build_status`/`cargo_exit_code`), `ARTIFACT_IDENTITY.txt`
(`applicable`/`artifact_present`), `STATIC_ARTIFACT_INSPECTION.txt`
(`inspection_applicable`/`artifact_present`), and `BUILD_TIMING.txt`
(`cargo_started_utc`/`cargo_finished_utc`, required only once cargo has
started) are each checked against the outcome-specific table encoded in the
validator. A shared/generic evidence body cannot satisfy more than one
file's schema — every file has file-specific required fields (see
`FILE_REQUIRED_FIELDS` in the validator).

When an artifact is absent (`artifact_present=no`), `ARTIFACT_IDENTITY.txt`
and `STATIC_ARTIFACT_INSPECTION.txt` both require a non-empty `reason=`
field explaining why.

`DOCKER_EXIT_CODE.txt` must be fully labeled `key=value` fields. A bare,
unlabelled numeric-only file (e.g. a lone `0` line, as older packages used)
is explicitly rejected.

## Required files

Must match [WITNESS_PACKAGE_MANIFEST.md](../WITNESS_PACKAGE_MANIFEST.md).
Field names for every structured file are **normative** in `templates/*`
and must match the validator's `FILE_REQUIRED_FIELDS` exactly.

## Fixed identity constants

| Constant | Value |
|----------|-------|
| `EXPECTED_GROK_COMMIT` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| `EXPECTED_IMAGE_DIGEST` | `6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| `EXPECTED_CARGO_LOCK_SHA256` | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |
| `EXACT_BUILD_CMD` | `cargo build -p xai-grok-pager-bin --locked` |
| `PACKAGE_TAG_EXPECTED` | `grok-build-witness-v1.0.0-rc3` (structural grammar check only when the tag field is non-empty; not force-equated, since rc versions evolve) |

Fields recording an **expected/pinned** identity (e.g.
`grok_build_commit_expected`, `grok_build_source_commit_expected`,
`grok_build_commit_requested`, `cargo_lock_sha256_expected`,
`requested_digest`) are checked for exact equality against these constants.
Fields recording an **observed/actual** value from the run (e.g.
`grok_build_commit_observed`, `cargo_lock_sha256_observed`,
`weaver_forge_commit_resolved`, `image_id`) are checked only for correct
**format** (40-char hex commit, 64-char hex sha256, etc.) — the validator
checks structure, not the truth of what was observed.

## `EVIDENCE_MANIFEST.sha256` grammar

Preferred line grammar:

```text
<64 lowercase hex><two spaces>./<safe-relative-path>
```

Filename grammar (applies to `<safe-relative-path>` after the `./` prefix
is stripped): `^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$`.

Rejected, with a specific error each:

- Extra tokens/whitespace embedded in the path
- Uppercase (or mixed-case) digest
- Absolute paths (Unix `/...` or Windows `C:/...`)
- Backslashes
- Parent traversal (`..` as a path segment) or empty segments
- The manifest listing itself
- Duplicate entries for the same path
- Unsafe filename characters (anything outside the grammar above)
- A listed file missing on disk
- A hash that does not match the recomputed SHA-256 of the file on disk
- Any regular file present on disk that is not listed (and not in the
  documented optional set below)

Regenerate the manifest from within the evidence directory once all manual
files are finalized:

```bash
cd /path/to/evidence/run-id && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
```

`HOST_RUN_METADATA.txt` is optional in the manifest (host-only auxiliary,
not part of the required evidence set).

### Symlink policy

Symlinks are **rejected by default** anywhere under the evidence directory
— there is no supported mechanism to mark a symlink as acceptable. This
applies regardless of whether the symlink target is listed in the manifest.

## `WITNESS_VERDICT.md`

Exactly one selection line must appear, verbatim:

```text
Witness proposed verdict: PASS
```

(or `PARTIAL`, `FAIL`, `INDETERMINATE`). Matching is **exact and
case-sensitive** — `parse_verdict_selection` never case-folds. `pass`,
`Pass`, `PASS.`, and any other variant are rejected. Explanatory uses of
those words elsewhere in the document (e.g. in a "Justification" section)
are ignored, because only a line beginning with the literal prefix
`Witness proposed verdict:` is parsed.

The file also requires (as `key=value` fields, parsed independent of
surrounding markdown): `evidence_schema_version`, `run_id`, `package_tag`,
`weaver_forge_commit`, `grok_build_commit` (must equal
`EXPECTED_GROK_COMMIT`), `product_executed=NO`, `ldd_used=NO`, and
`maintainer_intake_verdict=pending`.

## `WITNESS_STATEMENT.md`

Required fields (parsed as `key=value`, independent of markdown headings):
`witness_identity_or_handle` (non-empty), `not_package_owner=yes`,
`not_owner_side_reproducer=yes`, `witness_controlled_host=yes`,
`ai_assistance_used` (`yes`/`no`; `ai_assistance_detail` required and
non-empty when `yes`), `human_review_completed=yes`, `product_executed=NO`,
`ldd_used=NO`.

## `DEVIATIONS.txt`

`deviation_state` must be exactly `NONE` or `PRESENT`. When `PRESENT`, every
enumerated `deviation_<n>_*` entry must supply `_description`, `_severity`
(one of `NONE|NONMATERIAL_DISCLOSED|MATERIAL_NONCANONICAL|PROHIBITED`),
`_canonical_identity_impact` (`yes`/`no`), and `_verdict_ceiling` (one of
`PASS|PARTIAL|FAIL|INDETERMINATE`). Ceiling consistency is enforced:

| Severity | Ceiling constraint |
|----------|---------------------|
| `PROHIBITED` | must be exactly `FAIL` |
| `MATERIAL_NONCANONICAL` | must not be `PASS` |
| `NONMATERIAL_DISCLOSED` / `NONE` | unconstrained |

## `REDACTIONS.md`

`redaction_state` must be exactly `NONE` or `PRESENT`;
`semantic_integrity_declaration=yes` is always required. When `PRESENT`,
every enumerated `redaction_<n>_*` entry must supply `_file`, `_field`,
`_reason`, and a visible `_replacement_marker` (containing `[REDACTED`).
Any redaction whose field/reason text references a prohibited category —
commits, digests, exact commands, exit codes, artifact SHA-256/size, or
independence statements — is rejected.

## Tests

Run from repository root (uses temporary directories only):

```bash
python -m unittest discover -s external_verifications/grok-build/witness-package/scripts/tests -p 'test_*.py' -v
```

Tests use isolated `tempfile` fixtures with **file-specific** valid bodies
per evidence file — no shared generic body is reused across unrelated
schemas, so a validator regression that accepts a generic body everywhere
would be caught. Coverage includes: a fully valid package per outcome
(all five), missing required files, per-file schema isolation, every
manifest-grammar rejection case, symlink rejection (skipped automatically
in environments without symlink privilege, e.g. non-elevated Windows),
exact/duplicate/case-sensitive verdict handling, independence/AI/human-review
combinations in `WITNESS_STATEMENT.md`, deviation severity/ceiling
consistency, prohibited-redaction detection, `main()` success/failure return
codes, and report text content.

Do not commit synthetic fixture trees.

## Known gaps / out of scope for this revision

- `WITNESS_PACKAGE_MANIFEST.md`, `WITNESS_CLASSIFICATION.md`, and
  `WITNESS_REQUIREMENTS.md` have since been reconciled, at the narrative-docs
  level (RB-019/RB-021 remediation), with this validator/template revision
  and with the `evidence_schema_version=1` field names, outcome model, and
  canonical constants that `run_witness_narrow_build.sh` already declares in
  its own header. That reconciliation pass was **documentation-only**: it did
  not execute, modify, or independently verify `run_witness_narrow_build.sh`
  or `container_narrow_build.sh` against a live run, so any drift between
  what those scripts actually emit at runtime and what the templates/
  validator/narrative docs now describe has **not** been confirmed closed by
  execution. One specific, disclosed gap identified during that pass:
  the host orchestrator's own computed `verdict_ceiling` for
  `WEAVER_FORGE_TAG` identity overrides is
  looser than the authoritative ceiling defined in `WITNESS_CLASSIFICATION.md`;
  that document instructs the Witness to apply its own stricter ceiling by
  hand until the script is aligned in a future pass.
- `witness_id` and `run_id` grammar (`is_safe_token`) rejects path
  separators, whitespace, and `..`, but does not enforce a maximum length.
