# WACP-001 — Weaver AI Context Pack v0

WACP-v0 is deterministic, bounded repository-context extraction tooling. It
accepts an explicit scope manifest and writes six review artifacts. It does not
infer semantic scope, invoke an AI provider, run tests by default, use a network,
or create authority, evidence, Human Final, merge, or production semantics.

Core boundary: context selection is not verification completeness. A WACP pack
does not reduce reviewer responsibility.

## Scope manifest

Required fields:

```json
{
  "scope_id": "SCOPE-001",
  "base": "<git revision>",
  "head": "<git revision>",
  "review_mode": "implementation",
  "include": ["path/**"],
  "max_bytes": 100000
}
```

`review_mode` is exactly `implementation`, `independent_review`, or
`remediation`. Optional fields are `schema_version`, `exclude`,
`required_status_files`, `finding_sources`, `test_status`, and
`clean_worktree_required` (default `true`). Unknown fields are invalid.

Paths and patterns use normalized, repository-relative POSIX syntax. Include
patterns expand against the union of the base and head Git trees. Every include
must match. Excludes are applied afterward; an unmatched exclude is harmless.
Selected paths are bytewise ordered. Absolute paths, traversal, duplicate
normalized patterns, and selected symlinks are invalid.

Changed files not selected by the manifest, including excluded changed files,
produce `PACK_INCOMPLETE`; they are never silently hidden. Non-ancestor commits
are allowed and their relationship is recorded.

## Statuses

- `PACK_READY`: all changed paths and required sources are selected and the
  generated pack fits the budget.
- `PACK_INCOMPLETE`: changed paths or declared required sources are outside the
  selected context.
- `PACK_TOO_LARGE`: the complete pack exceeds `max_bytes`; nothing is truncated.
- `INVALID`: manifest, revision, path, symlink, clean-worktree, artifact hash, or
  claim-boundary validation failed.

## Output

Every generated pack contains exactly:

- `PACK_MANIFEST.json`
- `CONTEXT_SUMMARY.md`
- `DIFF.patch`
- `OPEN_FINDINGS.md`
- `CLAIM_BOUNDARY.md`
- `TEST_STATUS.md`

The selected diff is base-to-head, no-renames, no-color, no-textconv, and
no-external-diff. Large source bodies are not copied into the pack; selected
files are identified by path and exact base/head SHA-256 values.

If no finding source is declared, `OPEN_FINDINGS.md` says
`NO_FINDING_SOURCE_SUPPLIED`, not `NO_OPEN_FINDINGS`. Supplied test status is
reported as supplied and is not independently verified by WACP.

`CLAIM_BOUNDARY.md` is mandatory and non-authoritative. Its absence or mutation
makes verification fail.

## Determinism and identity

Core artifacts use LF, deterministic ordering, canonical indented JSON, and no
timestamps, user names, machine paths, or temporary paths. The manifest records
the Git version, relevant diff configuration, generator version, and fixed
no-renames/no-external-diff/no-textconv policy.

`pack_id` is ordinary SHA-256 over canonical identity inputs: repository remote
identity, full base/head SHAs and relationship, scope/review mode, exact source
manifest SHA-256, generator identity, Git context, and budget. It is integrity
identity only and introduces no digest domain or authority.

The generated artifact inventory covers the five non-manifest artifacts. The
manifest cannot hash itself; it records its fixed-point total byte size instead.
Post-write verification checks every recorded artifact and the exact claim
boundary.

Expected external reviewer metadata may state `review_context_basis` as
`PACK_ONLY` or `PACK_PLUS_TARGETED_REPO`; WACP does not enforce that field.

## Usage

```powershell
python -m tools.wacp.cli docs/wacp_001/SCOPE_MANIFEST_EXAMPLE.json output/wacp-pack --repository .
python -m unittest tools.wacp.test_wacp -v
```

The output directory must be absent or empty. WACP never deletes or overwrites
an existing pack.

## Assurance and limitations

Focused tests cover the closed status model, explicit selection, exact commit
binding, path and symlink rejection, changed-file completeness, budget handling,
determinism, inventories, all review modes, claim enforcement, no network use,
and repeat-byte comparison. Mutation controls cover all six required weakened
behaviors.

WACP does not prove selected context sufficient, excluded context irrelevant,
tests valid, changes correct or safe, or review complete. Git object availability
and local Git correctness remain environmental assumptions. Third-party or
non-Python semantics are not interpreted because WACP performs no semantic
discovery at all.
