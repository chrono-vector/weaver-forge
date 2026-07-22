# REDACTIONS.md — required fields (evidence_schema_version=1, 1.0.0-rc4)

redaction_state is NONE or PRESENT. semantic_integrity_declaration must be
`yes` (redactions never alter any structural/semantic value).

NEVER-REDACT categories (rejected if a redaction targets them): commits,
digests, sha256, exit codes, independence statements, artifact_size,
artifact_sha256, outcome, build_status, failure_stage, the Witness proposed
verdict, the maintainer intake verdict, canonical_run, and verdict_ceiling.

When redaction_state=PRESENT, enumerate each redaction with an index <n> and
place a matching visible `[REDACTED: ...]` marker in the target file:

```
redaction_<n>_file=<evidence filename>
redaction_<n>_field=<field/section redacted>
redaction_<n>_reason=<why>
redaction_<n>_replacement_marker=[REDACTED: <short label>]
```

```
evidence_schema_version=1
redaction_state=NONE
semantic_integrity_declaration=yes
```
