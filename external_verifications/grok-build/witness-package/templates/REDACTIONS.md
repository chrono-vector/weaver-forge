# REDACTIONS.md — human-readable redaction explanation (RC6-R6 / R6-RD2)

Paired with machine-readable `REDACTIONS_INDEX.txt`. This file explains
redactions for human review. The index owns exact target/file/field/category/
original-value SHA-256 / replacement-marker bindings and marker reconciliation.

redaction_state is NONE or PRESENT. semantic_integrity_declaration must be
`yes`. redactions_index_ref must be `REDACTIONS_INDEX.txt`.

NEVER-REDACT integrity-critical content (commits, digests, sha256, exit codes,
outcomes, verdicts, ceilings, independence, authoritative tuple, etc.).
Integrity-critical improper redaction is a structural FAIL input to the R5
machine ceiling.

Machine-readable categories (index only; remain distinct):
FILESYSTEM_PATH | HOME_PATH_IDENTIFIER | COMMAND_TEXT | CAPTURED_COMMAND_OUTPUT

```
evidence_schema_version=1
redaction_state=NONE
semantic_integrity_declaration=yes
redactions_index_ref=REDACTIONS_INDEX.txt
```

When redaction_state=PRESENT, add human prose below explaining each redaction.
Do not place machine indexed `redaction_<n>_*` keys in this file — those belong
exclusively in REDACTIONS_INDEX.txt.
