# Witness evidence validator (C2E-5 / 1.0.0-rc4 / `evidence_schema_version=1`)

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

## `key=value` parsing: no duplicate keys, no last-value-wins

`parse_kv` (the shared line parser used for every structured file) **rejects
duplicate keys** — a key declared twice anywhere in the same file is always
a structural defect, regardless of whether the repeated value is identical
to the first occurrence or conflicts with it:

- `a=1` followed later by `a=1` → rejected ("repeated with the same value")
- `a=1` followed later by `a=2` → rejected ("conflicting values")

There is **no** last-value-wins fallback: the first occurrence is retained
for downstream schema checks, but every repeat is reported as a distinct
error. Markdown headings, table rows, blank lines, and non-`key=value` lines
continue to be ignored, as before.

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

`outcome=` must also be present and **identical** in `DOCKER_EXIT_CODE.txt`,
`BUILD_TIMING.txt`, and `WITNESS_VERDICT.md`; a mismatch against
`BUILD_EXIT_CODE.txt` is a structural failure. `STATIC_ARTIFACT_INSPECTION.txt`
carries its own `outcome` field, but it is checked against a narrower rule
(see below) rather than forced to equal the run's overall outcome, because
the container script legitimately writes `NOT_APPLICABLE` there for every
outcome except `CARGO_SUCCEEDED_ARTIFACT_PRESENT`.

Validation is **outcome-sensitive**: `BUILD_EXIT_CODE.txt`
(`cargo_started`/`build_status`/`cargo_exit_code`/`status`),
`ARTIFACT_IDENTITY.txt` (`applicable`/`artifact_present`),
`STATIC_ARTIFACT_INSPECTION.txt` (`applicable`/`artifact_present`/`outcome`),
and `BUILD_TIMING.txt` (`cargo_started_utc`/`cargo_finished_utc`, required
only once cargo has started) are each checked against the outcome-specific
table encoded in the validator. A shared/generic evidence body cannot
satisfy more than one file's schema — every file has file-specific required
fields (see `FILE_REQUIRED_FIELDS` in the validator).

`cargo_exit_code` uses the literal sentinel `NOT_APPLICABLE` (exact,
case-sensitive) whenever cargo never started — there is no `N/A` alias.
This matches `container_narrow_build.sh`'s `write_outcome_evidence` exactly.

When an artifact is absent (`artifact_present=no`), `ARTIFACT_IDENTITY.txt`
and `STATIC_ARTIFACT_INSPECTION.txt` both require a non-empty `reason=`
field explaining why.

`DOCKER_EXIT_CODE.txt` must be fully labeled `key=value` fields. A bare,
unlabelled numeric-only file (e.g. a lone `0` line, as older packages used)
is explicitly rejected. `docker_exit_code` is numeric, or the sentinel
`NOT_STARTED`/`NOT_REACHED` when the container never launched (e.g. a
pre-`docker run` image-pull/inspect/digest/platform failure).

### Placeholder tolerance for container-owned files on early-failure paths

On a pre-container / pre-cargo failure path the container never overwrites the
host's initial placeholders for `BOOTSTRAP.txt`, `BUILD_COMMAND.txt`, and
`BUILD_ENVIRONMENT.txt`. When such a file is still `status=NOT_REACHED` **and**
the overall outcome is `BUILD_NOT_STARTED` or `INFRASTRUCTURE_FAILURE`, the
validator accepts the placeholder without enforcing that file's full field
schema or semantic checks (`placeholder_skip`). For any other outcome the
full schema is enforced. Likewise, `STATIC_ARTIFACT_INSPECTION.txt`'s per-tool
`*_exit_code` fields may be a `NOT_APPLICABLE`/`NOT_REACHED` sentinel (not just
empty or numeric) when `applicable=no`.

### `BUILD_EXIT_CODE.txt` `status` mirrors static-inspection completeness

For outcome `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, `BUILD_EXIT_CODE.txt`'s
`status` field must be `FAILED` whenever
`STATIC_ARTIFACT_INSPECTION.txt`'s `inspection_complete=no`, and `OK`
whenever `inspection_complete=yes`. This mirrors
`container_narrow_build.sh`'s own contract: the outcome stays
`CARGO_SUCCEEDED_ARTIFACT_PRESENT` even when a required static-inspection
command failed, but `status` distinguishes the two cases, and the verdict
ceiling for an incomplete inspection is capped at `PARTIAL` (`PASS` is
prohibited).

## Machine-computed verdict ceiling (`compute_verdict_ceiling`)

The validator independently computes a verdict ceiling from the evidence
itself and **rejects any `Witness proposed verdict:` line in
`WITNESS_VERDICT.md` that exceeds it** (and, separately, rejects a verdict
that exceeds the Witness's own recorded `verdict_ceiling` field, if that is
stricter than the machine-computed value). Ceilings are ordered
`FAIL < INDETERMINATE < PARTIAL < PASS`; "ceiling" means the **best**
verdict permitted — a stricter (lower-ranked) verdict is always acceptable.

Precedence (first match governs):

| Condition | Ceiling |
|-----------|---------|
| Proven product execution, `ldd` use, or `WITNESS_STATEMENT.md` `upstream_product_commands_not_run=no` | `FAIL` |
| Canonical identity mismatch: `WEAVER_FORGE_PACKAGE_IDENTITY.txt` `tag_head_match=no` or tag ≠ canonical; `SOURCE_IDENTITY.txt` commit/`Cargo.lock` mismatch; `IMAGE_IDENTITY.txt` digest/platform mismatch; `POST_BUILD_INTEGRITY.txt` source not clean, source/lock changed, or `HEAD` changed | `FAIL` |
| Outcome is `CARGO_FAILED` or `CARGO_SUCCEEDED_ARTIFACT_MISSING` | `FAIL` |
| Outcome is `BUILD_NOT_STARTED` or `INFRASTRUCTURE_FAILURE` (or undetermined) | `INDETERMINATE` |
| Outcome is `CARGO_SUCCEEDED_ARTIFACT_PRESENT` with incomplete static inspection | `PARTIAL` (max) |
| Outcome is `CARGO_SUCCEEDED_ARTIFACT_PRESENT`, fully complete, no other condition above applies | `PASS` (eligible) |

`WITNESS_VERDICT.md` must also declare an `outcome=` field (one of the five
outcome values, checked against `BUILD_EXIT_CODE.txt`) and a
`verdict_ceiling=` field (one of `PASS|PARTIAL|FAIL|INDETERMINATE`,
representing the Witness's own alignment with
`WITNESS_CLASSIFICATION.md`'s "Machine verdict ceiling alignment" rule).

## `maintainer_intake_verdict` vocabulary (SUPERSEDED alignment)

`WITNESS_VERDICT.md`'s `maintainer_intake_verdict` field must be one of the
six lowercase lifecycle values used across
[MAINTAINER_INTAKE_POLICY.md](../MAINTAINER_INTAKE_POLICY.md) and
[CORRECTION_LEDGER.md](../CORRECTION_LEDGER.md):
`pending | accepted | rejected | correction_requested | disputed |
superseded`. A brand-new submission must record `pending` (see
[WITNESS_PACKAGE_MANIFEST.md](../WITNESS_PACKAGE_MANIFEST.md)'s
`evidence_inventory_complete` lifecycle), but the validator's vocabulary
check accepts any of the six values so that re-validating an
already-reviewed historical submission (e.g. one later annotated
`superseded` after a correction) does not spuriously fail.

## Closed auxiliary-file inventory

Only these four optional, host-only auxiliary files are permitted alongside
`REQUIRED_FILES`, and this set is **exhaustive** (`CLOSED_AUX_EVIDENCE_FILES`
in the validator):

- `HOST_RUN_METADATA.txt`
- `IMAGE_PULL_STDOUT.txt`
- `IMAGE_PULL_STDERR.txt`
- `CARGO_LOCK_INTEGRITY.txt`

They are optional in `EVIDENCE_MANIFEST.sha256` (not required entries), but
if present on disk they must not be symlinks and, if listed in the
manifest, their hash must match.

**Being listed in the manifest does not itself grant a file entry into the
evidence set.** Any manifest line for a relative path that is neither one of
`REQUIRED_FILES` nor one of the four closed auxiliary files above is
rejected outright — even if the file exists on disk and its hash matches —
because "undeclared aux" is a policy violation independent of hash
correctness (`validate_manifest`'s dedicated check).

`BOOTSTRAP_PROTOC_VERSION.txt` is **explicitly forbidden** anywhere under the
evidence directory (`check_forbidden_files`), regardless of whether it is
listed in the manifest: protoc version output belongs exclusively in
`BOOTSTRAP.txt`'s `protoc_version_output`/`protoc_version_exit_code` fields
(see `container_narrow_build.sh`'s header comment).

## `[REDACTED...]` marker scanning vs. `REDACTIONS.md`

The validator scans **every** file in the evidence directory (not just
`REQUIRED_FILES`) for the literal pattern `[REDACTED...]` and cross-checks
the result against `REDACTIONS.md`:

- `redaction_state=NONE` — no file may contain a `[REDACTED...]` marker
  anywhere; any occurrence is a structural failure.
- `redaction_state=PRESENT` — every file containing a marker must be named
  by at least one `redaction_<n>_file` entry, and every declared
  `redaction_<n>_file` entry must correspond to a file that actually
  contains a marker. An orphan marker (no declaration) or an orphan
  declaration (no marker actually present) is a structural failure.

This is independent of, and in addition to, the existing
prohibited-category check on each redaction's `_field`/`_reason` text (see
below).

## Multiline static/tool output: single-line escaping

`STATIC_ARTIFACT_INSPECTION.txt`'s per-tool `*_output` fields and
`BOOTSTRAP.txt`'s `protoc_version_output` field must be flattened to a
single `key=value` line with an embedded literal `\n` (carriage returns
stripped) before being written — see `container_narrow_build.sh`'s
`escape_oneline()`. The validator rejects a raw carriage-return byte
(`\r`) anywhere in either of these two files (`check_no_raw_carriage_returns`).
This check is scoped to only these two files: other structured files
(`ENVIRONMENT.txt` in particular) legitimately contain genuine multi-line
raw text, and human-authored markdown files
(`WITNESS_STATEMENT.md`/`WITNESS_VERDICT.md`/`DEVIATIONS.txt`/`REDACTIONS.md`)
may legitimately use CRLF line endings from a Windows editor unrelated to
this escaping convention.

## Required files

Must match [WITNESS_PACKAGE_MANIFEST.md](../WITNESS_PACKAGE_MANIFEST.md).
Field names for every structured file are **normative** in `templates/*`
and must match the validator's `FILE_REQUIRED_FIELDS` exactly.

`FILE_REQUIRED_FIELDS` for `CLEAN_TARGET_PROOF.txt`, `BUILD_ENVIRONMENT.txt`,
`BUILD_EXIT_CODE.txt`, `BUILD_TIMING.txt`, and `STATIC_ARTIFACT_INSPECTION.txt`
are reconciled field-for-field against the `BEGIN_SCHEMA_BLOCK` sections of
`container_narrow_build.sh`; `IMAGE_IDENTITY.txt` (host-owned) and the
`ENVIRONMENT.txt` union (host block + container-appended block) are reconciled
against `run_witness_narrow_build.sh`; and `POST_BUILD_INTEGRITY.txt` (host,
no schema block) against its writer. These reconciliations are **enforced by
CONTRACT TESTS** in `scripts/tests/test_validate_witness_evidence.py`, which
re-derive the schema-block key sets directly from the shell scripts and assert
they match the validator's declared schema (for `STATIC_ARTIFACT_INSPECTION.txt`
the comparison is against `FILE_REQUIRED_FIELDS` ∪
`STATIC_ARTIFACT_INSPECTION_ALWAYS_PRESENT_KEYS`, since that file's per-tool
keys are always present but only conditionally non-empty). Renames from rc3:

| File | rc3 field | rc4 field |
|------|-----------|-----------|
| `IMAGE_IDENTITY.txt` | `requested_image_string` | `requested_image` |
| `IMAGE_IDENTITY.txt` | `docker_pull_command` / `docker_pull_exit_code` | `pull_command` / `pull_exit_code` |
| `IMAGE_IDENTITY.txt` | `docker_inspect_*` | `inspect_*` |
| `IMAGE_IDENTITY.txt` | `os` / `architecture` / `platform` | `observed_os` / `observed_architecture` / `observed_platform` |
| `CLEAN_TARGET_PROOF.txt` | `cargo_target_dir_absolute` / `required_entry_count` / `observed_entry_count_host` / `observed_entry_count_container` | `target_path_host` / (dropped) / `observed_entry_count_host` (kept) / `observed_entry_count_container` (kept), plus new `target_path_container_prebootstrap`/`proof_utc_container_prebootstrap`/`observed_entry_count_container_prebootstrap`/`target_path_container_precargo`/`proof_utc_container_precargo` |
| `BUILD_ENVIRONMENT.txt` | `HOME` / `CARGO_HOME` / `CARGO_TARGET_DIR` / `CARGO_INCREMENTAL` / `DOTSLASH_CACHE` | `home` / `cargo_home` / `cargo_target_dir` / `cargo_incremental` / `dotslash_cache` (lowercase); `PROTOC` dropped from this file (it belongs to `BOOTSTRAP.txt`) |
| `STATIC_ARTIFACT_INSPECTION.txt` | `inspection_applicable` | `applicable` |
| `STATIC_ARTIFACT_INSPECTION.txt` | `readelf_h` / `readelf_n` / `readelf_d` | `readelf_h_output` / `readelf_n_output` / `readelf_d_output` (plus new `sha256sum_*`, `stat_*`, and every `*_command` field) |

## Fixed identity constants

| Constant | Value |
|----------|-------|
| `EXPECTED_GROK_COMMIT` | `98c3b2438aa922fbbe6178a5c0a4c48f85edc8ce` |
| `EXPECTED_IMAGE_DIGEST` | `6ca5ad23231207874325a751b9df584d51cd42c066c74c6963c264e3233c3e8e` |
| `EXPECTED_CARGO_LOCK_SHA256` | `1512bb4fef0c1166c6a15a3398da9593903be1759b759ce78d9958913e61b421` |
| `EXACT_BUILD_CMD` | `cargo build -p xai-grok-pager-bin --locked` |
| `PACKAGE_TAG_EXPECTED` | `grok-build-witness-v1.0.0-rc4` |
| `EXPECTED_DOTSLASH_VERSION` | `0.5.7` |

Fields recording an **expected/pinned** identity (e.g.
`grok_build_commit_expected`, `grok_build_source_commit_expected`,
`grok_build_commit_requested`, `cargo_lock_sha256_expected`,
`requested_digest`, `grok_build_commit` in `BUILD_ENVIRONMENT.txt`) are
checked for exact equality against these constants. Fields recording an
**observed/actual** value from the run (e.g. `grok_build_commit_observed`,
`cargo_lock_sha256_observed`, `weaver_forge_commit_resolved`, `image_id`)
are checked only for correct **format** (40-char hex commit, 64-char hex
sha256, etc.) — the validator checks structure, not the truth of what was
observed.

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
- A manifest entry for a file outside the closed required/optional
  inventory (see "Closed auxiliary-file inventory" above) — rejected even
  when the file exists and its hash matches
- Any regular file present on disk that is not listed (and not in the
  documented closed auxiliary set above)

Regenerate the manifest from within the evidence directory once all manual
files are finalized:

```bash
cd /path/to/evidence/run-id && find . -type f ! -name 'EVIDENCE_MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > EVIDENCE_MANIFEST.sha256
```

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
`EXPECTED_GROK_COMMIT`), `outcome` (must match `BUILD_EXIT_CODE.txt`),
`verdict_ceiling`, `product_executed=NO`, `ldd_used=NO`, and
`maintainer_intake_verdict` (see the vocabulary section above). The proposed
verdict line's value must not exceed the machine-computed verdict ceiling
(see above) or the recorded `verdict_ceiling` field, whichever is stricter.

## `WITNESS_STATEMENT.md`

Required fields (parsed as `key=value`, independent of markdown headings):
`witness_identity_or_handle` (non-empty), `not_package_owner=yes`,
`not_owner_side_reproducer=yes`, `witness_controlled_host=yes`,
`ai_assistance_used` (`yes`/`no`; `ai_assistance_detail` required and
non-empty when `yes`), `human_review_completed=yes`, `product_executed=NO`,
`ldd_used=NO`. `upstream_product_commands_not_run=no` is also fed into the
machine-computed verdict ceiling as a `FAIL` signal (see above).

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
commits, digests, exact commands, exit codes, artifact SHA-256/size,
independence statements, `outcome`, `build_status`, `failure_stage`, the
proposed verdict, the intake verdict, `canonical_run`, or `verdict_ceiling`
— is rejected. See also the `[REDACTED...]` marker-scanning section above,
which is an independent, additional cross-check.

## Tests

Run from repository root (uses temporary directories only, plus the committed
golden fixtures under `scripts/tests/fixtures/`):

```bash
python -m unittest discover -s external_verifications/grok-build/witness-package/scripts/tests -p 'test_*.py' -v
```

The suite is rc4-native. It includes: schema-block **contract tests** (see
"Required files" above); `parse_kv` duplicate-key tests; outcome-consistency
tests across `BUILD_EXIT_CODE.txt`/`DOCKER_EXIT_CODE.txt`/`BUILD_TIMING.txt`/
`WITNESS_VERDICT.md`; **golden-fixture** validation for all ten
outcomes/failure modes (`success-artifact-present`, `build-not-started`,
`cargo-failed`, `artifact-missing`, `infrastructure-failure`,
`static-inspection-incomplete`, `image-pull-failure`, `image-inspect-failure`,
`digest-mismatch`, `platform-mismatch`); manifest grammar/inventory tests;
verdict-ceiling tests; redaction tests; `upstream_product_commands_not_run`
tests; and **host-safety static assertions** (strict-mode `set -Eeuo pipefail`,
`readonly` canonical constants, the constants self-check, the
`--noncanonical-deviation` override guard, and the `WORK_ROOT` guards) read
from the shell-script text without executing it. The golden fixtures are built
by the shared `scripts/tests/fixtures_lib.py` and materialized by
`scripts/tests/_generate_fixtures.py`; the same builders are reused to
construct throw-away temp trees inside the tests, so on-disk fixtures and the
tests cannot drift.

## Known gaps / out of scope for this revision

- `witness_id` and `run_id` grammar (`is_safe_token`) rejects path
  separators, whitespace, and `..`, but does not enforce a maximum length.
- The machine-computed verdict ceiling (`compute_verdict_ceiling`) inspects
  a fixed set of fields per file; it is a structural heuristic, not a
  reimplementation of the full precedence table in
  [WITNESS_CLASSIFICATION.md](../WITNESS_CLASSIFICATION.md). A Witness must
  still independently apply that document in full — the validator's ceiling
  is a floor-level safety net, not a substitute for it.
